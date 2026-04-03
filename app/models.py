# app/models.py
import sqlite3
import os
import datetime
import uuid

DB_PATH = os.getenv("SQLITE_DB", "./app/db.sqlite")

def init_sqlite():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    c = conn.cursor()
    c.execute("""
      CREATE TABLE IF NOT EXISTS documents (
        doc_id TEXT PRIMARY KEY,
        title TEXT,
        uploader TEXT,
        role_tag TEXT,
        source_type TEXT,
        upload_ts TEXT,
        file_path TEXT,
        version INTEGER
      );
    """)
    c.execute("""
      CREATE TABLE IF NOT EXISTS chunks (
        chunk_id TEXT PRIMARY KEY,
        doc_id TEXT,
        chunk_idx INTEGER,
        page INTEGER,
        snippet TEXT,
        text TEXT,
        faiss_idx INTEGER
      );
    """)
    c.execute("""
      CREATE TABLE IF NOT EXISTS meta (k TEXT PRIMARY KEY, v TEXT);
    """)
    c.execute("""
      CREATE TABLE IF NOT EXISTS feedback (
        id TEXT PRIMARY KEY,
        query_id TEXT,
        user_id TEXT,
        rating INTEGER,
        comment TEXT,
        ts TEXT
      );
    """)
    # initialize next_faiss_idx if missing
    c.execute("INSERT OR IGNORE INTO meta (k,v) VALUES ('next_faiss_idx','0')")
    conn.commit()
    conn.close()

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def insert_document(doc_id, title, uploader, role_tag, source_type, file_path, version=1):
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        INSERT INTO documents (doc_id, title, uploader, role_tag, source_type, upload_ts, file_path, version)
        VALUES (?,?,?,?,?,?,?,?)
    """, (doc_id, title, uploader, role_tag, source_type, datetime.datetime.utcnow().isoformat(), file_path, version))
    conn.commit()
    conn.close()

def insert_feedback(query_id, user_id, rating, comment=""):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO feedback (id, query_id, user_id, rating, comment, ts) VALUES (?,?,?,?,?,?)",
              (str(uuid.uuid4()), query_id, user_id, rating, comment, datetime.datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
