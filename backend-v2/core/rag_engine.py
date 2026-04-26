"""
core/rag_engine.py — RAG Search Engine cho PACS++
UC12: Keyword search (ILIKE)
UC13: Dense search (pgvector cosine)
UC14: Hybrid search (Dense + BM25 + RRF)

Pattern adapted from 6803_rag/core/rag/hybrid_retriever.py
"""

import logging
import re
import numpy as np
from typing import List, Dict, Optional

from core.embeddings import EmbeddingModel, tokenize_vietnamese, BM25_AVAILABLE
from database.connection import get_connection, release_connection
from psycopg2.extras import RealDictCursor

if BM25_AVAILABLE:
    from rank_bm25 import BM25Okapi

logger = logging.getLogger(__name__)

# Threshold: score < 70% → không trùng, loại khỏi kết quả
MIN_SIMILARITY_THRESHOLD = 0.70


# ============================================================
# UC12: Keyword Search (ILIKE)
# ============================================================

def keyword_search(query: str, limit: int = 10) -> List[Dict]:
    """
    Tìm kiếm từ khóa đơn giản bằng ILIKE.
    Spec UC12: WHERE findings ILIKE '%...%' OR conclusion ILIKE '%...%'
    """
    if not query or not query.strip():
        return []

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        pattern = f"%{query.strip()}%"
        cursor.execute("""
            SELECT r.id AS report_id, r.study_id, r.findings, r.conclusion,
                   r.recommendation, r.report_date,
                   s.modality, s.study_date, s.description AS study_description,
                   s.orthanc_id,
                   p.full_name AS patient_name, p.patient_id AS patient_code
            FROM diagnostic_reports r
            JOIN studies s ON r.study_id = s.id
            JOIN patients p ON s.patient_id = p.id
            WHERE r.findings ILIKE %s
               OR r.conclusion ILIKE %s
               OR p.full_name ILIKE %s
               OR p.patient_id ILIKE %s
            ORDER BY r.report_date DESC
            LIMIT %s
        """, (pattern, pattern, pattern, pattern, limit))

        results = []
        for row in cursor.fetchall():
            results.append({**dict(row), "score": 1.0, "method": "keyword"})

        logger.info(f"[Keyword] query='{query[:30]}' → {len(results)} results")
        return results

    finally:
        cursor.close()
        release_connection(conn)


# ============================================================
# Patient Name Search (ILIKE on full_name + patient_id ONLY)
# ============================================================

def patient_search(name: str, limit: int = 20) -> List[Dict]:
    """
    Tìm kiếm theo TÊN bệnh nhân hoặc MÃ bệnh nhân.
    Chỉ match trên p.full_name và p.patient_id — KHÔNG tìm trong nội dung báo cáo.
    """
    if not name or not name.strip():
        return []

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        pattern = f"%{name.strip()}%"
        cursor.execute("""
            SELECT r.id AS report_id, r.study_id, r.findings, r.conclusion,
                   r.recommendation, r.report_date,
                   s.modality, s.study_date, s.description AS study_description,
                   s.orthanc_id,
                   p.full_name AS patient_name, p.patient_id AS patient_code
            FROM diagnostic_reports r
            JOIN studies s ON r.study_id = s.id
            JOIN patients p ON s.patient_id = p.id
            WHERE p.full_name ILIKE %s
               OR p.patient_id ILIKE %s
            ORDER BY p.full_name, r.report_date DESC
            LIMIT %s
        """, (pattern, pattern, limit))

        results = []
        for row in cursor.fetchall():
            results.append({**dict(row), "score": 1.0, "method": "patient_lookup"})

        logger.info(f"[Patient] name='{name[:30]}' → {len(results)} results")
        return results

    finally:
        cursor.close()
        release_connection(conn)


# ============================================================
# UC13: Dense Search (pgvector cosine similarity)
# ============================================================

def dense_search(query: str, top_k: int = 10) -> List[Dict]:
    """
    Tìm kiếm ngữ nghĩa bằng e5-large + pgvector.
    Spec UC13: encode query → cosine similarity → top-K
    """
    if not query or not query.strip():
        return []

    # Encode query (prefix "query: " cho e5-large)
    query_vector = EmbeddingModel.encode_query(query)
    if not query_vector:
        return []

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # pgvector: <=> = cosine distance, 1 - distance = similarity
        cursor.execute("""
            SELECT r.id AS report_id, r.study_id, r.findings, r.conclusion,
                   r.recommendation, r.report_date,
                   s.modality, s.study_date, s.description AS study_description,
                   s.orthanc_id,
                   p.full_name AS patient_name, p.patient_id AS patient_code,
                   1 - (r.embedding <=> %s::vector) AS similarity_score
            FROM diagnostic_reports r
            JOIN studies s ON r.study_id = s.id
            JOIN patients p ON s.patient_id = p.id
            WHERE r.embedding IS NOT NULL
            ORDER BY r.embedding <=> %s::vector
            LIMIT %s
        """, (str(query_vector), str(query_vector), top_k))

        results = []
        for row in cursor.fetchall():
            d = dict(row)
            score = round(float(d.pop("similarity_score", 0)), 4)
            # Threshold: < 70% coi như không trùng
            if score < MIN_SIMILARITY_THRESHOLD:
                continue
            d["score"] = score
            d["method"] = "dense"
            results.append(d)

        logger.info(f"[Dense] query='{query[:30]}' → {len(results)} results (>={MIN_SIMILARITY_THRESHOLD}), top_score={results[0]['score'] if results else 0}")
        return results

    finally:
        cursor.close()
        release_connection(conn)


# ============================================================
# UC14: Hybrid Search (Dense + BM25 + RRF)
# Pattern from 6803_rag/core/rag/hybrid_retriever.py
# ============================================================

def _load_all_reports() -> List[Dict]:
    """Load tất cả reports cho BM25 indexing."""
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT r.id AS report_id, r.study_id, r.findings, r.conclusion,
                   r.recommendation, r.report_date,
                   s.modality, s.study_date, s.description AS study_description,
                   s.orthanc_id,
                   p.full_name AS patient_name, p.patient_id AS patient_code
            FROM diagnostic_reports r
            JOIN studies s ON r.study_id = s.id
            JOIN patients p ON s.patient_id = p.id
            ORDER BY r.id
        """)
        return [dict(row) for row in cursor.fetchall()]
    finally:
        cursor.close()
        release_connection(conn)


# BM25 cache (rebuild khi cần)
_bm25_cache = {"bm25": None, "reports": None, "count": 0}


def _get_bm25():
    """Get or build BM25 index. Cache in memory."""
    global _bm25_cache

    if not BM25_AVAILABLE:
        return None, []

    reports = _load_all_reports()

    # Rebuild if report count changed
    if _bm25_cache["count"] != len(reports):
        logger.info(f"[BM25] Building index for {len(reports)} reports...")
        texts = [f"{r.get('findings', '')} {r.get('conclusion', '')}" for r in reports]
        tokenized = [tokenize_vietnamese(t) for t in texts]
        _bm25_cache["bm25"] = BM25Okapi(tokenized)
        _bm25_cache["reports"] = reports
        _bm25_cache["count"] = len(reports)
        logger.info(f"[BM25] Index built OK")

    return _bm25_cache["bm25"], _bm25_cache["reports"]


def sparse_search(query: str, top_k: int = 10) -> List[Dict]:
    """
    BM25 sparse keyword search.
    Copy from 6803_rag/core/rag/hybrid_retriever.py
    """
    if not BM25_AVAILABLE:
        logger.warning("[Sparse] BM25 not available, falling back to keyword search")
        return keyword_search(query, top_k)

    bm25, reports = _get_bm25()
    if not bm25 or not reports:
        return []

    query_tokens = tokenize_vietnamese(query)
    scores = bm25.get_scores(query_tokens)

    # Get top-k indices
    top_indices = np.argsort(scores)[::-1][:top_k]
    max_score = max(scores) if max(scores) > 0 else 1

    results = []
    for idx in top_indices:
        if scores[idx] > 0:
            doc = reports[idx].copy()
            doc["score"] = round(float(scores[idx] / max_score), 4)
            doc["method"] = "sparse"
            results.append(doc)

    logger.info(f"[Sparse] query='{query[:30]}' → {len(results)} results")
    return results


def hybrid_search(
    query: str,
    top_k: int = 10,
    dense_weight: float = 0.6,
    sparse_weight: float = 0.4
) -> List[Dict]:
    """
    Hybrid search: Dense (pgvector) + Sparse (BM25) + RRF fusion.
    Copy RRF pattern from 6803_rag/core/rag/hybrid_retriever.py
    
    Spec UC14:
        score = dense_weight/(k + rank_dense) + sparse_weight/(k + rank_bm25)
        k = 60 (RRF constant)
    """
    if not query or not query.strip():
        return []

    # 1. Dense search (pgvector)
    dense_results = dense_search(query, top_k=top_k * 2)

    # 2. Sparse search (BM25)
    sparse_results = sparse_search(query, top_k=top_k * 2)

    # 3. RRF fusion (from 6803_rag)
    rrf_scores = {}
    doc_map = {}
    k_rrf = 60  # RRF constant (same as 6803)

    # Dense rank scores
    for rank, doc in enumerate(dense_results):
        doc_id = doc["report_id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + dense_weight / (k_rrf + rank + 1)
        doc_map[doc_id] = doc

    # Sparse rank scores
    for rank, doc in enumerate(sparse_results):
        doc_id = doc["report_id"]
        rrf_scores[doc_id] = rrf_scores.get(doc_id, 0) + sparse_weight / (k_rrf + rank + 1)
        if doc_id not in doc_map:
            doc_map[doc_id] = doc

    # Sort by RRF score
    ranked = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)[:top_k]

    results = []
    for doc_id, rrf_score in ranked:
        doc = doc_map[doc_id].copy()
        dense_score = next((d["score"] for d in dense_results if d["report_id"] == doc_id), 0)
        sparse_score = next((d["score"] for d in sparse_results if d["report_id"] == doc_id), 0)

        # Weighted score (pattern 6805) — normalize khi 1 component rỗng
        # Nếu sparse=0 → dùng dense_score trực tiếp (không bị phạt)
        has_dense = dense_score > 0
        has_sparse = sparse_score > 0
        if has_dense and has_sparse:
            # Cả 2 có kết quả → weighted trung bình
            weighted_score = round(dense_score * dense_weight + sparse_score * sparse_weight, 4)
        elif has_dense:
            # Chỉ dense → dùng dense score
            weighted_score = round(dense_score, 4)
        elif has_sparse:
            # Chỉ sparse → dùng sparse score
            weighted_score = round(sparse_score, 4)
        else:
            weighted_score = 0

        # Threshold: dense < 70% → loại (không đủ liên quan về ngữ nghĩa)
        if dense_score < MIN_SIMILARITY_THRESHOLD and sparse_score < 0.3:
            continue

        doc["score"] = weighted_score
        doc["method"] = "hybrid"
        doc["dense_score"] = dense_score
        doc["sparse_score"] = sparse_score
        results.append(doc)

    # Re-sort by weighted score
    results.sort(key=lambda x: x["score"], reverse=True)

    logger.info(
        f"[Hybrid] query='{query[:30]}' → {len(results)} results (>={MIN_SIMILARITY_THRESHOLD}) "
        f"(dense={len(dense_results)}, sparse={len(sparse_results)})"
    )
    return results
