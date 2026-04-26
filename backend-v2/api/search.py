"""
api/search.py — Search API endpoints cho PACS++
UC12: GET  /api/search/keyword?q=...
UC13: POST /api/search (method: "dense")
UC14: POST /api/search (method: "hybrid")
"""

import os
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from models.user import User

router = APIRouter(prefix="/api/search", tags=["Search"])


# ====================== Schemas ======================

class SearchRequest(BaseModel):
    """Request body cho Dense/Hybrid search"""
    query: str = Field(..., min_length=1, description="Câu truy vấn")
    method: str = Field(default="hybrid", description="keyword | dense | hybrid")
    top_k: int = Field(default=10, ge=1, le=50, description="Số kết quả")
    dense_weight: float = Field(default=0.6, ge=0.0, le=1.0, description="Trọng số dense (hybrid)")
    sparse_weight: float = Field(default=0.4, ge=0.0, le=1.0, description="Trọng số sparse (hybrid)")


# ====================== UC12: Keyword Search ======================

@router.get("/keyword")
def search_keyword(
    q: str = Query(..., min_length=1, description="Từ khóa tìm kiếm"),
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """GET /api/search/keyword?q=tổn+thương+phổi
    Spec UC12: tìm kiếm từ khóa bằng ILIKE
    """
    from core.rag_engine import keyword_search
    results = keyword_search(q, limit=limit)
    return {
        "results": results,
        "total": len(results),
        "method": "keyword",
        "query": q,
    }


# ====================== UC13 + UC14: Dense / Hybrid Search ======================

@router.post("")
def search_reports(
    body: SearchRequest,
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """POST /api/search — Tìm kiếm báo cáo
    method: "keyword" | "dense" | "hybrid" (default)

    Spec UC13: Dense search (pgvector cosine similarity)
    Spec UC14: Hybrid search (Dense + BM25 + RRF)
    """
    from core.rag_engine import keyword_search, dense_search, hybrid_search

    query = body.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query không được rỗng")

    if body.method == "keyword":
        results = keyword_search(query, limit=body.top_k)

    elif body.method == "dense":
        results = dense_search(query, top_k=body.top_k)

    elif body.method == "hybrid":
        results = hybrid_search(
            query,
            top_k=body.top_k,
            dense_weight=body.dense_weight,
            sparse_weight=body.sparse_weight,
        )

    else:
        raise HTTPException(status_code=400, detail=f"method '{body.method}' không hợp lệ. Dùng: keyword, dense, hybrid")

    return {
        "results": results,
        "total": len(results),
        "method": body.method,
        "query": query,
    }

