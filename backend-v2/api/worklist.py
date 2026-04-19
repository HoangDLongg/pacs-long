# api/worklist.py
import os
import sys
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from psycopg2.extras import RealDictCursor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from database.connection import get_connection, release_connection
from models.user import User

router = APIRouter(prefix="/api/worklist", tags=["Worklist"])

# ====================== Helper ======================
def _require_worklist_roles(current_user: User):
    """Chỉ admin, doctor, technician mới được xem Worklist"""
    if current_user.role not in ("admin", "doctor", "technician"):
        raise HTTPException(status_code=403, detail="Không có quyền truy cập Worklist")


# ====================== GET /api/worklist ======================
@router.get("")
def get_worklist(
    date: Optional[str] = Query(None),
    modality: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """GET /api/worklist — Danh sách ca chụp + filter (Admin/Doctor/Tech)"""
    _require_worklist_roles(current_user)

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        sql = """
            SELECT s.*,
                   p.full_name  AS patient_name,
                   p.patient_id AS patient_code,
                   p.gender,
                   u.full_name  AS technician_name
            FROM studies s
            JOIN patients p ON s.patient_id = p.id
            LEFT JOIN users u ON s.technician_id = u.id
            WHERE 1=1
        """
        params = []

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
        return {"studies": [dict(r) for r in studies], "total": len(studies)}
    finally:
        cursor.close()
        release_connection(conn)


# ====================== GET /api/worklist/stats/dashboard ======================
# PHẢI đứng trước /{study_id} để FastAPI không nhầm "stats" là study_id
@router.get("/stats/dashboard")
def get_dashboard_stats(
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """GET /api/worklist/stats/dashboard — 4 con số thống kê (Admin/Doctor/Tech)"""
    _require_worklist_roles(current_user)

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT
                COUNT(*)                                         AS total,
                COUNT(*) FILTER (WHERE status = 'PENDING')      AS pending,
                COUNT(*) FILTER (WHERE status = 'REPORTED')     AS reported,
                COUNT(*) FILTER (WHERE status = 'VERIFIED')     AS verified
            FROM studies
        """)
        stats = cursor.fetchone()
        return dict(stats)
    finally:
        cursor.close()
        release_connection(conn)


# ====================== GET /api/worklist/my-studies ======================
# PHẢI đứng trước /{study_id}
@router.get("/my-studies")
def get_my_studies(
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """GET /api/worklist/my-studies — Ca chụp của bệnh nhân đang login (Patient only)
    Spec US8: patient chỉ thấy ca của chính mình (FR-009)
    """
    if current_user.role != "patient":
        raise HTTPException(status_code=403, detail="Chỉ bệnh nhân mới truy cập được trang này")

    if not current_user.linked_patient_id:
        return {"studies": [], "total": 0, "message": "Tài khoản chưa được liên kết với bệnh nhân"}

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT s.*,
                   p.full_name  AS patient_name,
                   p.patient_id AS patient_code,
                   p.gender,
                   p.birth_date
            FROM studies s
            JOIN patients p ON s.patient_id = p.id
            WHERE s.patient_id = %s
            ORDER BY s.study_date DESC, s.created_at DESC
        """, (current_user.linked_patient_id,))
        studies = cursor.fetchall()
        return {"studies": [dict(r) for r in studies], "total": len(studies)}
    finally:
        cursor.close()
        release_connection(conn)


# ====================== GET /api/worklist/{study_id} ======================
@router.get("/{study_id}")
def get_study_detail(
    study_id: int,
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """GET /api/worklist/{id} — Chi tiết 1 ca chụp"""
    # Patient chỉ xem được ca của mình (FR-009)
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT s.*,
                   p.full_name  AS patient_name,
                   p.patient_id AS patient_code,
                   p.gender, p.birth_date, p.phone,
                   u.full_name  AS technician_name
            FROM studies s
            JOIN patients p ON s.patient_id = p.id
            LEFT JOIN users u ON s.technician_id = u.id
            WHERE s.id = %s
        """, (study_id,))
        study = cursor.fetchone()

        if not study:
            raise HTTPException(status_code=404, detail="Study not found")

        # Patient isolation check (spec FR-009, SC-007)
        if current_user.role == "patient":
            if study["patient_id"] != current_user.linked_patient_id:
                raise HTTPException(status_code=403, detail="Không có quyền xem ca này")

        return dict(study)
    finally:
        cursor.close()
        release_connection(conn)
