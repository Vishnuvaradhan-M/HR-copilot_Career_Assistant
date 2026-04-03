from sentence_transformers import CrossEncoder

reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

def rerank(query, hits, top_k=5):
    pairs = [(query, h["text"]) for h in hits]
    scores = reranker.predict(pairs)

    for h, s in zip(hits, scores):
        h["rerank_score"] = float(s)

    hits.sort(key=lambda x: x["rerank_score"], reverse=True)
    return hits[:top_k]
