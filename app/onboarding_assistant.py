import os
import sys
from datetime import datetime

# Make sure repo root is importable
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app.rag_logger import logged_rag_answer


DEFAULT_CONF_THRESHOLD = 0.7

# Minimal canned guidance for onboarding (non-policy guidance)
ONBOARDING_GUIDANCE = {
    "first_week": (
        "Welcome! In your first week: meet your team, complete HR paperwork, set up your workstation, "
        "and review mandatory training modules. For policy specifics, ask the policy FAQ."
    ),
    "faq_fallback": (
        "I couldn't find a policy-backed answer for that. For practical guidance, contact your HR representative "
        "or consult the employee handbook under 'Onboarding' section."
    ),
}


class OnboardingAssistant:
    """Lightweight wrapper that uses `rag_answer()` (via `logged_rag_answer`) and
    distinguishes policy-backed answers from general guidance.

    This module does not alter RAG behavior; it only classifies responses and
    returns a combined result for UI layers or chatbots.
    """

    def __init__(self, confidence_threshold: float = DEFAULT_CONF_THRESHOLD, logger_path: str = None):
        self.confidence_threshold = confidence_threshold
        self.logger_path = logger_path

    def answer(self, query: str):
        """Return a dict with `type` ("policy-backed" or "general-guidance"), answer, hits, confidence."""
        res = logged_rag_answer(query, log_path=self.logger_path) if self.logger_path is not None else logged_rag_answer(query)
        answer = res.get("answer", "")
        confidence = res.get("confidence")

        # classify
        is_policy = False
        if answer:
            # consider non-fallback and confidence threshold
            low = (answer or "").lower()
            fallback_tokens = ["couldn't find", "could not find", "i cannot", "cannot", "do not have"]
            if not any(t in low for t in fallback_tokens):
                try:
                    if float(confidence) >= self.confidence_threshold:
                        is_policy = True
                except Exception:
                    # if confidence missing, be conservative and treat as policy-backed only if not fallback
                    is_policy = True

        if is_policy:
            return {
                "type": "policy-backed",
                "answer": answer,
                "confidence": confidence,
                "hits": res.get("hits", []),
            }
        else:
            # Provide general onboarding guidance as fallback (non-policy)
            # Keep it explicit that this is not policy-backed
            guidance = ONBOARDING_GUIDANCE.get("faq_fallback")
            return {
                "type": "general-guidance",
                "answer": guidance,
                "policy_answer": answer,
                "confidence": confidence,
                "hits": res.get("hits", []),
            }


if __name__ == "__main__":
    # quick manual test
    oa = OnboardingAssistant()
    q = "What is the ceiling on accumulation of Earned Leave?"
    print(oa.answer(q))
