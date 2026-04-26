"""
api/ask.py — NL2SQL + RAG Hỏi đáp API
UC15: POST /api/ask

Tách riêng theo kiến trúc README:
  /api/search → RAG search (UC12-14)
  /api/ask    → NL2SQL + RAG routing (UC15)
"""

import os
import sys

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from models.user import User

router = APIRouter(prefix="/api", tags=["Ask"])


class AskRequest(BaseModel):
    """Câu hỏi tự nhiên"""
    question: str = Field(..., min_length=1, description="Câu hỏi (VD: 'Bao nhiêu ca CT hôm nay?')")


@router.post("/ask")
def ask_endpoint(
    body: AskRequest,
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """POST /api/ask — Hỏi đáp tự nhiên (UC15)

    Pipeline:
      1. query_router.classify() → STRUCTURED / SEMANTIC / HYBRID
      2. STRUCTURED → rule NL2SQL → Ollama → Gemini
      3. SEMANTIC → hybrid_search (dense + BM25)
      4. HYBRID → cả SQL + RAG

    Returns:
      intent, confidence, sql, source, data[], rag_results[], answer, router_debug
    """
    from core.nl2sql_engine import ask
    return ask(body.question)
