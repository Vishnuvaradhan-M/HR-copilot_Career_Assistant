# app/main.py
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Path
from fastapi.responses import JSONResponse, FileResponse
from dotenv import load_dotenv
import os, shutil, uuid, traceback
import logging

load_dotenv()

from .models import init_sqlite, insert_document, insert_feedback, get_conn
from .ingest import extract_and_chunk
from .faiss_store import upsert_chunks_to_faiss, query_faiss
from .retriever import rag_answer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="HR Copilot (MVP) - Groq/Ollama backend")

init_sqlite()

# Pre-warm lazy-loaded models on startup
logger.info("Pre-warming models for first request...")
try:
    from .retriever import get_reranker
    from .faiss_store import get_embedder
    logger.info("Loading embedder...")
    embedder = get_embedder()
    logger.info("✅ Embedder loaded")
    logger.info("Loading reranker...")
    reranker = get_reranker()
    logger.info("✅ Reranker loaded")
    logger.info("All models pre-warmed successfully")
except Exception as e:
    logger.warning(f"Model pre-warming failed: {e}")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/upload")
async def upload(file: UploadFile = File(...), uploader: str = Form(...), role_tag: str = Form(...)):
    filename = file.filename
    if not filename:
        raise HTTPException(status_code=400, detail="No filename provided.")
    doc_id = str(uuid.uuid4())
    dest_path = os.path.join(UPLOAD_DIR, f"{doc_id}_{filename}")
    try:
        with open(dest_path, "wb") as out:
            shutil.copyfileobj(file.file, out)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save upload: {str(e)}")
    try:
        chunks = extract_and_chunk(dest_path)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Extraction failed: {str(e)}")
    if not chunks:
        try:
            insert_document(doc_id, filename, uploader, role_tag,
                            "pdf" if filename.lower().endswith(".pdf") else "docx", dest_path)
        except Exception:
            pass
        return JSONResponse(status_code=200, content={"doc_id": doc_id, "chunks": 0, "warning": "No text extracted from document."})
    try:
        upsert_chunks_to_faiss(doc_id, filename, role_tag, chunks)
        insert_document(doc_id, filename, uploader, role_tag,
                        "pdf" if filename.lower().endswith(".pdf") else "docx", dest_path)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Upsert failed: {str(e)}")
    return {"doc_id": doc_id, "chunks": len(chunks)}

@app.post("/test_retrieve")
def test_retrieve(payload: dict):
    query = payload.get("query")
    role_tag = payload.get("role_tag")
    top_k = int(payload.get("top_k", 5))
    if not query:
        raise HTTPException(status_code=400, detail="Missing 'query' in payload.")
    try:
        hits = query_faiss(query, top_k=top_k, role_tag=role_tag)
        return {"hits": hits}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Retrieval error: {str(e)}")

@app.post("/query")
def query_endpoint(payload: dict):
    user_id = payload.get("user_id")
    role_tag = payload.get("role_tag")
    goal = payload.get("goal")
    query = payload.get("query")
    top_k = int(payload.get("top_k", 6))
    if not user_id or not query:
        raise HTTPException(status_code=400, detail="Missing user_id or query")
    try:
        result = rag_answer(query=query, role_tag=role_tag, goal=goal, top_k=top_k)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@app.post("/feedback")
def feedback(payload: dict):
    query_id = payload.get("query_id")
    user_id = payload.get("user_id")
    rating = payload.get("rating")
    comment = payload.get("comment", "")
    if not query_id or not user_id or rating is None:
        raise HTTPException(status_code=400, detail="Missing required fields: query_id, user_id, rating")
    try:
        insert_feedback(query_id, user_id, int(rating), comment or "")
        return {"ok": True}
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to store feedback: {str(e)}")

@app.get("/docs/{doc_id}")
def get_doc(doc_id: str = Path(..., description="Document ID to fetch metadata and download")):
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT doc_id, title, uploader, role_tag, source_type, upload_ts, file_path, version FROM documents WHERE doc_id=?", (doc_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            raise HTTPException(status_code=404, detail="Document not found.")
        doc = {
            "doc_id": row[0],
            "title": row[1],
            "uploader": row[2],
            "role_tag": row[3],
            "source_type": row[4],
            "upload_ts": row[5],
            "file_path": row[6],
            "version": row[7]
        }
        file_path = doc["file_path"]
        if file_path and os.path.exists(file_path):
            return FileResponse(path=file_path, filename=os.path.basename(file_path), media_type="application/octet-stream")
        return {"metadata": doc, "file_exists": False}
    except HTTPException:
        raise
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")
