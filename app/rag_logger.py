import os
import sys
import json
from datetime import datetime

# Ensure repo root on path when run as script
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

try:
    from app.retriever import rag_answer
except Exception:
    # defer import errors to runtime usage
    rag_answer = None


LOG_DIR = os.path.join(ROOT, "logs")
os.makedirs(LOG_DIR, exist_ok=True)
DEFAULT_LOG_PATH = os.path.join(LOG_DIR, "rag_queries.jsonl")


def logged_rag_answer(query: str, *, log_path: str = DEFAULT_LOG_PATH, **kwargs):
    """Call the frozen `rag_answer()` and append a structured JSON log line.

    Returns the original rag_answer() result.
    """
    if rag_answer is None:
        # import late to surface import errors at call time
        from app.retriever import rag_answer as _ra
        globals()["rag_answer"] = _ra

    ts = datetime.utcnow().isoformat() + "Z"
    result = rag_answer(query, **kwargs)

    # Normalize hits to chunk ids list
    hits = result.get("hits") or []
    chunk_ids = [h.get("chunk_id") or h.get("id") or None for h in hits]

    answer = result.get("answer") or ""
    confidence = result.get("confidence")
    fallback = False
    a_low = (answer or "").lower()
    # simple fallback detection (matches retriever harness rules)
    fb_phrases = ["couldn't find", "could not find", "i couldn't", "i could not", "i cannot", "cannot", "does not explicitly state", "i cannot answer"]
    for ph in fb_phrases:
        if ph in a_low:
            fallback = True
            break

    log_entry = {
        "ts": ts,
        "query": query,
        "chunk_ids": chunk_ids,
        "confidence": confidence,
        "fallback": fallback,
        "answer_snippet": (answer or "").strip()[:400],
    }

    # append as jsonl
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    return result


if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("query")
    p.add_argument("--log", help="override log path", default=DEFAULT_LOG_PATH)
    args = p.parse_args()

    res = logged_rag_answer(args.query, log_path=args.log)
    print(json.dumps(res, indent=2, ensure_ascii=False))
