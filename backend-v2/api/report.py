import os
import sys

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional
from io import BytesIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from database.connection import DatabaseConnection
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/api/report", tags=["Report"])


class ReportRequest(BaseModel):
    study_id: int
    findings: str
    conclusion: str
    recommendation: Optional[str] = None


@router.get("/{study_id}")
def get_report(study_id: int, request: Request):
    """GET /api/report/{study_id} — Xem báo cáo của 1 ca chụp"""
    AuthUtils.get_current_user(request)

    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            SELECT r.*, u.full_name as doctor_name
            FROM diagnostic_reports r
            JOIN users u ON r.doctor_id = u.id
            WHERE r.study_id = %s
        """, (study_id,))
        report = cursor.fetchone()

        if not report:
            return {"report": None, "message": "Chưa có báo cáo"}

        return {"report": report}
    finally:
        cursor.close()
        DatabaseConnection.release_connection(conn)


@router.post("")
def create_report(body: ReportRequest, request: Request):
    """POST /api/report — Tạo báo cáo mới (doctor/admin only)"""
    user = AuthUtils.get_current_user(request)

    if user["role"] not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ được viết báo cáo")

    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            INSERT INTO diagnostic_reports (study_id, doctor_id, findings, conclusion, recommendation)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (body.study_id, user["sub"], body.findings, body.conclusion, body.recommendation))

        report_id = cursor.fetchone()["id"]

        # Cập nhật status study → REPORTED
        cursor.execute("UPDATE studies SET status = 'REPORTED' WHERE id = %s", (body.study_id,))

        conn.commit()
        return {"id": report_id, "message": "Tạo báo cáo thành công"}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        DatabaseConnection.release_connection(conn)


@router.put("/{report_id}")
def update_report(report_id: int, body: ReportRequest, request: Request):
    """PUT /api/report/{id} — Cập nhật báo cáo"""
    user = AuthUtils.get_current_user(request)

    if user["role"] not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ được sửa báo cáo")

    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cursor.execute("""
            UPDATE diagnostic_reports 
            SET findings = %s, conclusion = %s, recommendation = %s, updated_at = NOW()
            WHERE id = %s
        """, (body.findings, body.conclusion, body.recommendation, report_id))

        conn.commit()
        return {"message": "Cập nhật báo cáo thành công"}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        DatabaseConnection.release_connection(conn)
