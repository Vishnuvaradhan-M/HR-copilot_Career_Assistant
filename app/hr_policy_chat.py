"""
HR Policy Assistant - Chat Component for Streamlit

Integrates with FastAPI /query endpoint to provide policy-backed Q&A.
Non-invasive wrapper around frozen RAG backend.

Features:
- Chat-style UI with history
- Answer + confidence display
- Expandable evidence snippets
- Graceful error handling
- Real-time session state management
"""

import streamlit as st
import requests
import json
from typing import Optional, Dict, List, Any
from datetime import datetime


# Constants
API_BASE_URL = "http://127.0.0.1:8001"  # Update if FastAPI runs on different host/port
DEFAULT_USER_ID = "streamlit_user"  # For demo; can be connected to actual user session
DEFAULT_ROLE_TAG = None  # Optional: can filter by role
DEFAULT_TOP_K = 6


# ============================================================================
# HELPERS: API Communication
# ============================================================================

def query_hr_policy(query: str, user_id: str = DEFAULT_USER_ID, role_tag: Optional[str] = DEFAULT_ROLE_TAG, top_k: int = DEFAULT_TOP_K) -> Optional[Dict[str, Any]]:
    """
    Send query to FastAPI /query endpoint.
    
    Args:
        query: User's question
        user_id: Session user identifier
        role_tag: Optional role filter
        top_k: Number of evidence chunks to retrieve
    
    Returns:
        Raw response dict or None on failure
    """
    try:
        payload = {
            "user_id": user_id,
            "query": query,
            "top_k": top_k,
        }
        if role_tag:
            payload["role_tag"] = role_tag
        
        response = requests.post(
            f"{API_BASE_URL}/query",
            json=payload,
            timeout=15
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return None  # Backend unavailable
    except requests.exceptions.Timeout:
        return None  # Request timeout
    except Exception as e:
        st.error(f"API error: {str(e)}")
        return None


def format_confidence(confidence: Optional[float]) -> str:
    """Convert confidence (0-1) to emoji + percentage."""
    if confidence is None:
        return "❓ Unknown"
    
    if confidence >= 0.8:
        return f"✅ {confidence*100:.0f}% Very High"
    elif confidence >= 0.6:
        return f"🟢 {confidence*100:.0f}% High"
    elif confidence >= 0.4:
        return f"🟡 {confidence*100:.0f}% Medium"
    else:
        return f"🟠 {confidence*100:.0f}% Low"


def format_evidence_chunk(hit: Dict[str, Any], index: int) -> str:
    """Format a single evidence chunk for display."""
    chunk_id = hit.get("chunk_id") or hit.get("id") or f"Chunk {index+1}"
    text = hit.get("text") or hit.get("content") or ""
    
    # Truncate if too long
    if len(text) > 300:
        text = text[:297] + "..."
    
    return f"**{chunk_id}**\n{text}"


# ============================================================================
# STREAMLIT SESSION STATE
# ============================================================================

def init_chat_session():
    """Initialize chat history in session state."""
    if "hr_chat_history" not in st.session_state:
        st.session_state.hr_chat_history = []


# ============================================================================
# UI COMPONENT: HR Policy Chat
# ============================================================================

def render_hr_policy_chat():
    """
    Render the complete HR Policy Assistant chat interface.
    
    Includes:
    - Chat history display
    - Input box + submit button
    - Error/success messages
    - Evidence expansion
    """
    
    init_chat_session()
    
    st.markdown("---")
    st.subheader("💼 HR Policy Assistant")
    st.markdown(
        "Ask any HR-related policy questions. I'll search our knowledge base and provide evidence-backed answers."
    )
    
    # ========================================================================
    # CHAT HISTORY DISPLAY
    # ========================================================================
    
    if st.session_state.hr_chat_history:
        st.markdown("**Chat History**")
        
        for i, msg in enumerate(st.session_state.hr_chat_history):
            if msg["role"] == "user":
                # User message (right-aligned, blue bubble)
                st.markdown(
                    f"""
                    <div style="text-align: right; margin-bottom: 12px;">
                        <div style="
                            display: inline-block;
                            background: #E3F2FD;
                            color: #1565C0;
                            padding: 12px 16px;
                            border-radius: 18px;
                            max-width: 70%;
                            word-wrap: break-word;
                            font-size: 14px;
                        ">
                            {msg['content']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
            else:
                # Assistant message (left-aligned, gray bubble)
                st.markdown(
                    f"""
                    <div style="text-align: left; margin-bottom: 12px;">
                        <div style="
                            display: inline-block;
                            background: #F5F5F5;
                            color: #424242;
                            padding: 12px 16px;
                            border-radius: 18px;
                            max-width: 70%;
                            word-wrap: break-word;
                            font-size: 14px;
                        ">
                            {msg['content']}
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                
                # Show confidence badge + evidence for assistant messages
                if "confidence" in msg:
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.caption(f"Confidence: {format_confidence(msg['confidence'])}")
                    with col2:
                        if msg.get("hits"):
                            if st.button("📎 View Evidence", key=f"evidence_{i}"):
                                st.session_state[f"show_evidence_{i}"] = not st.session_state.get(f"show_evidence_{i}", False)
                
                # Expandable evidence
                if st.session_state.get(f"show_evidence_{i}", False) and msg.get("hits"):
                    with st.expander("📄 Evidence Chunks", expanded=True):
                        for j, hit in enumerate(msg["hits"][:5]):  # Show top 5 chunks
                            st.markdown(format_evidence_chunk(hit, j))
                            if j < len(msg["hits"]) - 1:
                                st.markdown("---")
    
    # ========================================================================
    # INPUT SECTION
    # ========================================================================
    
    st.markdown("---")
    st.markdown("**Ask a Question**")
    
    col1, col2 = st.columns([4, 1])
    
    with col1:
        user_input = st.text_input(
            "Your question:",
            placeholder="e.g., What is the maternity leave policy?",
            label_visibility="collapsed",
        )
    
    with col2:
        submit_button = st.button("Send", use_container_width=True)
    
    # ========================================================================
    # SUBMIT LOGIC
    # ========================================================================
    
    if submit_button and user_input.strip():
        # Add user message to history
        st.session_state.hr_chat_history.append({
            "role": "user",
            "content": user_input,
            "timestamp": datetime.now().isoformat(),
        })
        
        # Query backend
        with st.spinner("🔍 Searching policy documents..."):
            result = query_hr_policy(user_input)
        
        if result is None:
            # Backend unavailable
            st.session_state.hr_chat_history.append({
                "role": "assistant",
                "content": "❌ **Oops!** I couldn't connect to the HR policy database. Please check if the service is running or try again in a moment.",
                "confidence": 0,
                "hits": [],
            })
            st.error("❌ Backend service unavailable. Is the FastAPI server running on http://localhost:8000?")
        
        elif not result.get("answer"):
            # Empty response
            st.session_state.hr_chat_history.append({
                "role": "assistant",
                "content": "❓ I couldn't find an answer to your question in the policy documents. Please rephrase or contact HR directly.",
                "confidence": result.get("confidence", 0),
                "hits": result.get("hits", []),
            })
        
        else:
            # Success
            answer = result.get("answer", "No answer found")
            confidence = result.get("confidence", 0)
            hits = result.get("hits", [])
            
            st.session_state.hr_chat_history.append({
                "role": "assistant",
                "content": answer,
                "confidence": confidence,
                "hits": hits,
            })
        
        # Rerun to refresh display
        st.rerun()


# ============================================================================
# TEST
# ============================================================================

if __name__ == "__main__":
    st.set_page_config(page_title="HR Policy Chat Test", layout="wide")
    st.title("HR Policy Chat - Standalone Test")
    render_hr_policy_chat()
