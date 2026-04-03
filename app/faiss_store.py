# app/faiss_store.py
import os
import sqlite3
import threading
import numpy as np
from sentence_transformers import SentenceTransformer
import faiss

DB_PATH = os.getenv("SQLITE_DB", "./app/db.sqlite")
INDEX_PATH = os.getenv("FAISS_INDEX_PATH", "./faiss_index.index")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")

_lock = threading.Lock()
_embedder = None

def get_embedder():
    """Lazy-load SentenceTransformer on first use."""
    global _embedder
    if _embedder is None:
        print("Loading SentenceTransformer embedder...")
        _embedder = SentenceTransformer(EMBED_MODEL)
        print("Embedder loaded successfully")
    return _embedder

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def load_or_create_index(dim):
    if os.path.exists(INDEX_PATH):
        index = faiss.read_index(INDEX_PATH)
        if index.d != dim:
            raise ValueError("Embedding dimension mismatch. Delete FAISS index.")
    else:
        index = faiss.IndexFlatIP(dim)
    return index

def save_index(index):
    faiss.write_index(index, INDEX_PATH)

def upsert_chunks_to_faiss(doc_id, title, role_tag, chunks):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()

        texts = [c["text"] for c in chunks]
        embedder = get_embedder()
        vecs = embedder.encode(texts, normalize_embeddings=True)
        vecs = np.array(vecs, dtype="float32")

        index = load_or_create_index(vecs.shape[1])

        cur.execute("SELECT v FROM meta WHERE k='next_faiss_idx'")
        row = cur.fetchone()
        next_idx = int(row[0]) if row else 0

        for i, c in enumerate(chunks):
            fid = next_idx + i
            cur.execute("""
                INSERT INTO chunks (chunk_id, doc_id, chunk_idx, page, snippet, text, faiss_idx)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                c["chunk_id"],
                doc_id,
                c["index"],
                c["page"],
                c["text"][:300],
                c["text"],
                fid
            ))

        index.add(vecs)
        save_index(index)

        cur.execute("UPDATE meta SET v=? WHERE k='next_faiss_idx'", (str(next_idx + len(chunks)),))
        conn.commit()
        conn.close()

def query_faiss(query, top_k=6, role_tag=None):
    with _lock:
        conn = get_conn()
        cur = conn.cursor()

        if not os.path.exists(INDEX_PATH):
            return []

        embedder = get_embedder()
        q_emb = embedder.encode([query], normalize_embeddings=True).astype("float32")
        index = faiss.read_index(INDEX_PATH)

        D, I = index.search(q_emb, min(top_k, index.ntotal))

        hits = []
        for score, idx in zip(D[0], I[0]):
            cur.execute("""
                SELECT chunks.chunk_id, chunks.doc_id, chunks.snippet, chunks.text
                FROM chunks
                WHERE chunks.faiss_idx=?
            """, (int(idx),))
            row = cur.fetchone()
            if not row:
                continue
            hits.append({
                "chunk_id": row[0],
                "doc_id": row[1],
                "snippet": row[2],
                "text": row[3],
                "score": float(score)
            })

        conn.close()
        return hits
