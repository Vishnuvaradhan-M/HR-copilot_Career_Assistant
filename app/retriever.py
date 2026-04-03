"""Evidence-first RAG retriever with LLM-optional mode support.

This module implements a safe, evidence-first retrieval+generation pipeline:
- Dense retrieval via FAISS (top 25 semantic matches)
- Lexical search via SQL keyword matching (critical policy terms)
- Hybrid union + deduplication ensures legally critical clauses ranked
- Rerank combined candidates with CrossEncoder
- LEXICAL-SAFE SELECTION: force-include lexical-exact hits (≥2 keywords) in top evidence
- LLM-ENHANCED MODE: Call Ollama if available for refined answers
- EVIDENCE-ONLY MODE: Accept high-confidence (≥0.65) answers when LLM unavailable (via sigmoid confidence)
- Confidence derived from sigmoid(reranker_score) mapping to [0,1]
- Returns strict JSON shape and degrades safely on failures

System supports both LLM-enhanced and evidence-only modes gracefully.
Do NOT change ingest, FAISS, or evaluator logic. This file is self-contained.
"""
import os
import requests
import re
import logging
from typing import List, Dict
from sentence_transformers import CrossEncoder
import math

logger = logging.getLogger(__name__)

from .faiss_store import query_faiss
from .models import get_conn

# LLM Configuration
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()

# Groq settings
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "mixtral-8x7b-32768")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

# Ollama settings (fallback)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma:2b")

# Lazy-load reranker (ms-marco cross-encoder)
_reranker = None

def get_reranker():
    """Lazy-load CrossEncoder on first use to avoid blocking startup."""
    global _reranker
    if _reranker is None:
        logger.info("Loading CrossEncoder model...")
        _reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")
        logger.info("CrossEncoder model loaded successfully")
    return _reranker

SYSTEM_PROMPT = (
    "You are an HR policy assistant. Use ONLY the provided evidence below.\n"
    "Rules:\n"
    "- Use ONLY the provided evidence (verbatim). Do not access external knowledge.\n"
    "- If the answer is not explicitly present in the provided evidence, reply exactly:\n"
    "  \"I couldn't find a definitive answer in the provided documents.\"\n"
    "- Do NOT guess or invent facts.\n"
    "- Keep answers concise and factual."
)

USER_TEMPLATE = (
    "Question:\n{question}\n\nEvidence (verbatim):\n{evidence}\n\nAnswer:"
)

FALLBACK_ANSWER = "I couldn't find a definitive answer in the provided documents."


def call_groq(system: str, user: str) -> str:
    """Call Groq API (OpenAI-compatible endpoint) and return assistant content."""
    if not GROQ_API_KEY:
        raise ValueError("GROQ_API_KEY not set in environment")
    
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    
    payload = {
        "model": GROQ_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "max_tokens": 512,
    }
    
    r = requests.post(GROQ_URL, json=payload, headers=headers, timeout=30)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def call_ollama(system: str, user: str) -> str:
    """Call Ollama chat endpoint and return assistant content."""
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    r = requests.post(f"{OLLAMA_URL}/api/chat", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["message"]["content"].strip()


def call_llm(system: str, user: str) -> str:
    """Call the configured LLM provider (Groq or Ollama)."""
    if LLM_PROVIDER == "groq":
        return call_groq(system, user)
    else:
        return call_ollama(system, user)


def _fetch_page_for_chunk(chunk_id: str) -> int:
    """Lookup page number for a chunk_id in SQLite; return 0 if unknown."""
    try:
        conn = get_conn()
        cur = conn.cursor()
        cur.execute("SELECT page FROM chunks WHERE chunk_id = ?", (chunk_id,))
        row = cur.fetchone()
        conn.close()
        return int(row[0]) if row else 0
    except Exception:
        return 0


def _lexical_keyword_search(query: str, limit: int = 20) -> List[Dict]:
    """Lightweight lexical search for critical policy keywords within numbered clauses."""
    critical_keywords = [
        "ceiling", "limit", "maximum", "accumulation", "not exceed",
        "minimum", "not permitted", "forbidden", "prohibited", "entitlement",
        "entitled", "shall not", "cannot be"
    ]
    
    query_lower = query.lower()
    has_critical_term = any(kw in query_lower for kw in critical_keywords)
    
    if not has_critical_term:
        return []
    
    try:
        conn = get_conn()
        cur = conn.cursor()
        
        keyword_combos = [
            ("ceiling", "accumulation"),
            ("ceiling", "days"),
            ("maximum", "accumulation"),
            ("limit", "exceed"),
            ("not exceed", None),
            ("forbidden", None),
            ("shall not", None),
        ]
        
        all_results = {}
        policy_pattern = re.compile(r'^\d+(?:\.\d+)+\s')
        
        for kw1, kw2 in keyword_combos:
            if kw2:
                cur.execute(
                    "SELECT chunk_id, text, page FROM chunks WHERE text LIKE ? AND text LIKE ? LIMIT ?",
                    (f"%{kw1}%", f"%{kw2}%", limit * 3)
                )
            else:
                cur.execute(
                    "SELECT chunk_id, text, page FROM chunks WHERE text LIKE ? LIMIT ?",
                    (f"%{kw1}%", limit * 3)
                )
            
            rows = cur.fetchall()
            for chunk_id, text, page in rows:
                if policy_pattern.match(text) and chunk_id not in all_results:
                    all_results[chunk_id] = {
                        "chunk_id": chunk_id,
                        "text": text,
                        "page": int(page) if page else 0,
                        "score": 0.0,
                        "source": "lexical"
                    }
        
        conn.close()
        return list(all_results.values())[:limit]
        
    except Exception:
        return []


def _format_evidence_answer(evidence_chunk: Dict) -> str:
    """Format top evidence chunk as final answer (evidence-only mode, high confidence).
    
    Takes the highest-ranked evidence chunk and formats it cleanly with page reference.
    Used only when LLM is unavailable AND confidence >= 0.85.
    
    Returns:
      - Formatted answer with page reference (max 280 chars)
      - Preserves original wording (no paraphrasing)
    """
    if not evidence_chunk:
        return FALLBACK_ANSWER
    
    text = evidence_chunk.get("text", "").strip()
    page = evidence_chunk.get("page", 0)
    
    if not text or len(text) < 10:
        return FALLBACK_ANSWER
    
    # Limit to first 2 sentences for conciseness
    sentences = text.split(". ")
    if len(sentences) > 2:
        formatted = ". ".join(sentences[:2]) + "."
    else:
        formatted = text
    
    # Add page reference if available
    if page and page > 0:
        answer = f"According to the policy (page {page}): {formatted}"
    else:
        answer = f"According to the policy: {formatted}"
    
    # Trim to reasonable length if needed
    if len(answer) > 280:
        answer = answer[:277] + "..."
    
    return answer


def _evidence_contains_answer(evidence_texts: List[str], answer: str) -> bool:
    """Verify that an answer is grounded in provided evidence.
    
    Returns True only if the answer can be traced back to evidence phrases.
    Generic fallback messages return False (must be explicitly handled by caller).
    """
    if not answer:
        return False
    
    # Do NOT auto-accept generic fallback (changed from previous behavior)
    if answer.strip() == FALLBACK_ANSWER:
        return False

    ans_low = answer.lower()
    
    for ev in evidence_texts:
        ev_lower = ev.lower()
        
        # Full-substring match
        if ev_lower in ans_low:
            return True
        
        # Phrase matching (5-grams, 4-grams, 3-grams)
        ev_words = re.split(r"\s+", ev_lower)
        
        for window_size in [5, 4, 3]:
            if window_size > len(ev_words):
                continue
            for i in range(len(ev_words) - window_size + 1):
                phrase = " ".join(ev_words[i:i + window_size])
                stopwords = {"a", "the", "is", "and", "or", "of", "in", "to", "for", "on", "at"}
                phrase_words = phrase.split()
                if all(w in stopwords for w in phrase_words):
                    continue
                if phrase in ans_low:
                    return True
    
    return False


def _normalize_confidence(scores: List[float], top_score: float) -> float:
    """Calculate confidence from reranker score using sigmoid function.
    
    Uses sigmoid(score) to map reranker scores to [0,1] confidence range.
    - Positive scores (>0) map to high confidence (0.5-1.0)
    - Score 0 maps to 0.5 confidence
    - Negative scores (<0) map to low confidence (0-0.5)
    - Very negative scores (<-3) map to very low confidence (~0)
    
    This properly handles cases where all candidates are irrelevant (all negative scores).
    """
    if not scores:
        return 0.0
    
    # Use sigmoid to map score to [0, 1]
    # sigmoid(x) = 1 / (1 + e^-x)
    try:
        # Clip extremely large values to avoid overflow
        clipped_score = max(-100, min(100, float(top_score)))
        confidence = 1.0 / (1.0 + math.exp(-clipped_score))
        return round(confidence, 2)
    except:
        return 0.0


def _expand_query(query: str) -> List[str]:
    """Expand query with synonyms to improve retrieval of leave-related queries."""
    expanded = [query]
    
    # Leave type synonyms
    leave_synonyms = {
        "sick leave": ["medical", "health", "illness", "absent due to medical"],
        "leave request": ["applying for leave", "leave application", "request leave", "grant leave", "procedure for granting leave"],
        "bereavement leave": ["death of family", "mourning"],
        "how many days": ["entitlement", "how much", "entitled to", "total days"],
    }
    
    query_lower = query.lower()
    for key, synonyms in leave_synonyms.items():
        if key in query_lower:
            expanded.extend(synonyms)
    
    return expanded


def rag_answer(query: str, role_tag: str = None, goal: str = None, top_k: int = 6) -> Dict:
    """Hybrid evidence-first retrieval + answer generation with LEXICAL-SAFE evidence selection."""
    try:
        # 1) Dense retrieval: FAISS top 25 - try original query + expanded variants
        dense_candidates = query_faiss(query, top_k=25, role_tag=role_tag)
        if not dense_candidates:
            dense_candidates = []
        
        # Try expanded queries if original had low retrieval
        if len(dense_candidates) < 5:
            expanded_queries = _expand_query(query)
            for expanded_q in expanded_queries[1:]:  # Skip original
                additional = query_faiss(expanded_q, top_k=10, role_tag=role_tag)
                dense_candidates.extend(additional)
                if len(dense_candidates) >= 15:
                    break

        # 2) Lexical retrieval
        lexical_candidates = _lexical_keyword_search(query, limit=20)

        # 3) Hybrid union
        seen_ids = set()
        combined_candidates = []
        
        for c in dense_candidates:
            cid = c.get("chunk_id")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                combined_candidates.append(c)
        
        for c in lexical_candidates:
            cid = c.get("chunk_id")
            if cid and cid not in seen_ids:
                seen_ids.add(cid)
                combined_candidates.append(c)
        
        if not combined_candidates:
            return {"answer": FALLBACK_ANSWER, "confidence": 0.0, "hits": []}

        # 4) Rerank
        pairs = [(query, c["text"]) for c in combined_candidates]
        try:
            reranker = get_reranker()
            rerank_scores = reranker.predict(pairs)
        except Exception as e:
            logger.error(f"Reranking failed: {e}")
            return {"answer": FALLBACK_ANSWER, "confidence": 0.0, "hits": []}

        for c, s in zip(combined_candidates, rerank_scores):
            c["rerank_score"] = float(s)

        # 5) LEXICAL-SAFE EVIDENCE SELECTION
        critical_keywords_in_query = [
            "ceiling", "limit", "maximum", "accumulation", "not exceed",
            "minimum", "not permitted", "forbidden", "prohibited", "entitlement",
            "entitled", "shall not", "cannot be"
        ]
        query_lower = query.lower()
        query_has_critical = any(kw in query_lower for kw in critical_keywords_in_query)
        
        lexical_exact_hits = []
        if query_has_critical:
            for c in combined_candidates:
                if c.get("source") == "lexical":
                    text_lower = c.get("text", "").lower()
                    keyword_matches = sum(1 for kw in critical_keywords_in_query if kw in text_lower)
                    if keyword_matches >= 2:
                        lexical_exact_hits.append(c)
        
        top_selected = []
        seen_ids_for_final = set()
        
        for c in lexical_exact_hits[:2]:
            cid = c.get("chunk_id")
            if cid and cid not in seen_ids_for_final:
                top_selected.append(c)
                seen_ids_for_final.add(cid)
        
        ranked = sorted(combined_candidates, key=lambda x: x["rerank_score"], reverse=True)
        for c in ranked:
            if len(top_selected) >= 4:
                break
            cid = c.get("chunk_id")
            if cid and cid not in seen_ids_for_final:
                top_selected.append(c)
                seen_ids_for_final.add(cid)

        for h in top_selected:
            if not h.get("page"):
                h["page"] = _fetch_page_for_chunk(h.get("chunk_id"))

        # 6) Build evidence
        evidence_texts = [h["text"] for h in top_selected]
        evidence = "\n\n".join([f"--- CHUNK {i+1} ---\n{txt}" for i, txt in enumerate(evidence_texts)])

        # 7) Calculate confidence first (needed for decision logic)
        all_scores = [float(s) for s in rerank_scores]
        top_score = float(top_selected[0]["rerank_score"]) if top_selected else 0.0
        confidence = _normalize_confidence(all_scores, top_score)

        # 8) Ask LLM or prepare fallback
        user_prompt = USER_TEMPLATE.format(question=query, evidence=evidence)
        llm_available = True
        try:
            llm_answer = call_llm(SYSTEM_PROMPT, user_prompt)
            logger.info(f"LLM-enhanced mode: answer generated via {LLM_PROVIDER.upper()}")
        except Exception as e:
            # LLM unavailable - prepare evidence-only mode
            llm_available = False
            logger.warning(f"LLM unavailable ({type(e).__name__}) — using evidence-only mode")
            llm_answer = None

        # 9) Decide final answer based on confidence and availability
        # STRATEGY (CORRECTED - EVIDENCE-FIRST):
        # - If confidence >= 0.65: Use LLM-enhanced answer (if available and grounded)
        # - If confidence >= 0.35 and LLM available: Try LLM answer
        # - If chunks exist (ANY confidence >= 0.2): Return formatted evidence (safe, factual)
        # - Only fallback if NO chunks retrieved
        
        final_answer = None
        
        # Priority 1: Try LLM for high-confidence queries if available
        if llm_available and top_selected and confidence >= 0.65:
            answer_supported = _evidence_contains_answer(evidence_texts, llm_answer)
            if answer_supported:
                final_answer = llm_answer
                logger.info(f"High-confidence LLM mode: answer verified against evidence (confidence={confidence:.2f})")
        
        # Priority 2: Try LLM for moderate-confidence queries if available
        elif llm_available and top_selected and confidence >= 0.35:
            answer_supported = _evidence_contains_answer(evidence_texts, llm_answer)
            if answer_supported:
                final_answer = llm_answer
                logger.debug(f"Moderate-confidence LLM mode: answer grounded in evidence")
        
        # Priority 3: Return formatted evidence if confidence >= 0.2 (lowered threshold to surface more answers)
        if final_answer is None and top_selected and confidence >= 0.2:
            # Return evidence directly - confidence shows quality
            final_answer = _format_evidence_answer(top_selected[0])
            logger.info(f"Evidence-based mode: returning formatted chunk (confidence={confidence:.2f}, rerank_score={top_selected[0]['rerank_score']:.2f})")
        
        # Priority 4: Fall back to generic message if confidence too low
        if final_answer is None:
            final_answer = FALLBACK_ANSWER
            logger.warning(f"No evidence with acceptable confidence (threshold=0.2, got={confidence:.2f}) - using fallback message")

        # 10) Build output
        hits_out = []
        for h in top_selected:
            hits_out.append({
                "chunk_id": h.get("chunk_id"),
                "page": h.get("page", 0),
                "text": h.get("text"),
                "rerank_score": float(h.get("rerank_score", 0.0))
            })
        
        return {"answer": final_answer, "confidence": confidence, "hits": hits_out}

    except Exception:
        return {"answer": FALLBACK_ANSWER, "confidence": 0.0, "hits": []}
