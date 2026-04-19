# api/admin.py
from fastapi import APIRouter, HTTPException, Depends
from psycopg2.extras import RealDictCursor

from core.auth_utils import AuthUtils
from database.connection import get_connection, release_connection
from models.user import User

router = APIRouter(prefix="/api/admin", tags=["Admin"])


def _require_admin(current_user: User):
    """Chỉ admin mới truy cập được"""
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Chỉ admin mới có quyền")


# ====================== GET /api/admin/users ======================
@router.get("/users")
def get_users(current_user: User = Depends(AuthUtils.get_current_user)):
    """GET /api/admin/users — Danh sách tất cả users (Admin only)"""
    _require_admin(current_user)

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT id, username, full_name, role, is_active, created_at
            FROM users
            ORDER BY id
        """)
        users = cursor.fetchall()
        return {"users": [dict(u) for u in users], "total": len(users)}
    finally:
        cursor.close()
        release_connection(conn)


# ====================== GET /api/admin/system ======================
@router.get("/system")
def get_system_info(current_user: User = Depends(AuthUtils.get_current_user)):
    """GET /api/admin/system — Thông tin hệ thống (Admin only)"""
    _require_admin(current_user)

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("SELECT COUNT(*) AS total FROM users")
        user_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM patients")
        patient_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM studies")
        study_count = cursor.fetchone()["total"]

        cursor.execute("SELECT COUNT(*) AS total FROM diagnostic_reports")
        report_count = cursor.fetchone()["total"]

        cursor.execute("""
            SELECT COUNT(*) FILTER (WHERE role = 'admin') AS admins,
                   COUNT(*) FILTER (WHERE role = 'doctor') AS doctors,
                   COUNT(*) FILTER (WHERE role = 'technician') AS technicians,
                   COUNT(*) FILTER (WHERE role = 'patient') AS patients
            FROM users
        """)
        role_counts = dict(cursor.fetchone())

        return {
            "users": user_count,
            "patients": patient_count,
            "studies": study_count,
            "reports": report_count,
            "roles": role_counts,
        }
    finally:
        cursor.close()
        release_connection(conn)
