import os
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, Query

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from database.connection import DatabaseConnection
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/api/worklist", tags=["Worklist"])


@router.get("")
def get_worklist(
    request: Request,
    date: Optional[str] = Query(None),
    modality: Optional[str] = Query(None),
    status: Optional[str] = Query(None)
):
    """GET /api/worklist — Danh sách ca chụp + filter"""
    # Kiểm tra đăng nhập
    user = AuthUtils.get_current_user(request)

    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # Query cơ bản — JOIN 3 bảng
        sql = """
            SELECT s.*, 
                   p.full_name as patient_name,
                   p.patient_id as patient_code,
                   p.gender,
                   u.full_name as technician_name
            FROM studies s
            JOIN patients p ON s.patient_id = p.id
            LEFT JOIN users u ON s.technician_id = u.id
            WHERE 1=1
        """
        params = []

        # Thêm filter nếu có
        if date:
            sql += " AND s.study_date = %s"
            params.append(date)
        if modality:
            sql += " AND s.modality = %s"
            params.append(modality)
        if status:
            sql += " AND s.status = %s"
            params.append(status)

        sql += " ORDER BY s.study_date DESC, s.created_at DESC"

        cursor.execute(sql, params)
        studies = cursor.fetchall()

        return {"studies": studies, "total": len(studies)}
    finally:
        cursor.close()
        DatabaseConnection.release_connection(conn)


@router.get("/stats/dashboard")
def get_dashboard_stats(request: Request):
    """GET /api/worklist/stats/dashboard — 4 con số thống kê"""
    user = AuthUtils.get_current_user(request)

    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT 
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE status = 'PENDING') as pending,
                COUNT(*) FILTER (WHERE status = 'REPORTED') as reported,
                COUNT(*) FILTER (WHERE status = 'VERIFIED') as verified
            FROM studies
        """)
        stats = cursor.fetchone()
        return stats
    finally:
        cursor.close()
        DatabaseConnection.release_connection(conn)


@router.get("/{study_id}")
def get_study_detail(study_id: int, request: Request):
    """GET /api/worklist/{id} — Chi tiết 1 ca chụp"""
    user = AuthUtils.get_current_user(request)

    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT s.*, 
                   p.full_name as patient_name,
                   p.patient_id as patient_code,
                   p.gender, p.birth_date, p.phone,
                   u.full_name as technician_name
            FROM studies s
            JOIN patients p ON s.patient_id = p.id
            LEFT JOIN users u ON s.technician_id = u.id
            WHERE s.id = %s
        """, (study_id,))
        study = cursor.fetchone()

        if not study:
            raise HTTPException(status_code=404, detail="Study not found")

        return study
    finally:
        cursor.close()
        DatabaseConnection.release_connection(conn)
