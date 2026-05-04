"""
api/ask.py — NL2SQL + RAG Hỏi đáp API
UC15: POST /api/ask

Tách riêng theo kiến trúc README:
  /api/search → RAG search (UC12-14)
  /api/ask    → NL2SQL + RAG routing (UC15)
"""

import os
import sys

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from slowapi import Limiter
from slowapi.util import get_remote_address

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from models.user import User

router = APIRouter(prefix="/api", tags=["Ask"])
limiter = Limiter(key_func=get_remote_address)


class AskRequest(BaseModel):
    """Câu hỏi tự nhiên"""
    question: str = Field(..., min_length=1, description="Câu hỏi (VD: 'Bao nhiêu ca CT hôm nay?')")


@router.post("/ask")
@limiter.limit("10/minute")  # Giới hạn 10 câu hỏi/phút/IP (tốn tài nguyên LLM)
def ask_endpoint(
    request: Request,
    body: AskRequest,
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """POST /api/ask — Hỏi đáp tự nhiên (UC15)

    Pipeline:
      1. query_router.classify() → STRUCTURED / SEMANTIC / HYBRID
      2. STRUCTURED → rule NL2SQL → Ollama → Gemini
      3. SEMANTIC → hybrid_search (dense + BM25)
      4. HYBRID → cả SQL + RAG

    Rate limit: 10 requests/minute/IP

    Returns:
      intent, confidence, sql, source, data[], rag_results[], answer, router_debug
    """
    from core.nl2sql_engine import ask
    return ask(body.question)

