import sqlite3
import os
from datetime import datetime
from typing import List, Tuple

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
DB_PATH = os.path.join(ROOT, "app_analytics.sqlite")

_SCHEMA = [
    "CREATE TABLE IF NOT EXISTS unanswered_queries (id INTEGER PRIMARY KEY AUTOINCREMENT, query TEXT UNIQUE, count INTEGER, last_seen TEXT)",
    "CREATE TABLE IF NOT EXISTS query_confidences (id INTEGER PRIMARY KEY AUTOINCREMENT, ts TEXT, query TEXT, confidence REAL)",
]


def init_db(path: str = DB_PATH):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    for s in _SCHEMA:
        cur.execute(s)
    conn.commit()
    conn.close()


def log_query_result(query: str, is_fallback: bool, confidence: float = None, path: str = DB_PATH):
    """Log a query result. If it's a fallback, increment unanswered_queries; always insert confidence row."""
    init_db(path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    ts = datetime.utcnow().isoformat() + "Z"

    # Insert confidence
    try:
        cur.execute("INSERT INTO query_confidences (ts, query, confidence) VALUES (?, ?, ?)", (ts, query, confidence if confidence is not None else -1.0))
    except Exception:
        pass

    if is_fallback:
        # upsert unanswered_queries
        cur.execute("SELECT id, count FROM unanswered_queries WHERE query = ?", (query,))
        r = cur.fetchone()
        if r:
            cur.execute("UPDATE unanswered_queries SET count = ?, last_seen = ? WHERE id = ?", (r[1] + 1, ts, r[0]))
        else:
            cur.execute("INSERT INTO unanswered_queries (query, count, last_seen) VALUES (?, ?, ?)", (query, 1, ts))

    conn.commit()
    conn.close()


def get_top_unanswered(limit: int = 20, path: str = DB_PATH) -> List[Tuple[str, int, str]]:
    init_db(path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("SELECT query, count, last_seen FROM unanswered_queries ORDER BY count DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows


def get_confidence_distribution(path: str = DB_PATH) -> List[Tuple[float, int]]:
    init_db(path)
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    # group confidences into buckets (0.0-0.1, 0.1-0.2, ... 0.9-1.0)
    buckets = []
    for i in range(10):
        lo = i / 10.0
        hi = (i + 1) / 10.0
        cur.execute("SELECT COUNT(*) FROM query_confidences WHERE confidence >= ? AND confidence < ?", (lo, hi))
        c = cur.fetchone()[0]
        buckets.append(((lo, hi), c))
    conn.close()
    return buckets


if __name__ == "__main__":
    init_db()
    print(get_top_unanswered())
    print(get_confidence_distribution())
