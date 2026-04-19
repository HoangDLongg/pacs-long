# api/report.py
import os
import sys
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from psycopg2.extras import RealDictCursor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from database.connection import get_connection, release_connection
from models.user import User

router = APIRouter(prefix="/api/report", tags=["Report"])


# ====================== Schemas ======================
class ReportRequest(BaseModel):
    study_id: int
    findings: str
    conclusion: str
    recommendation: Optional[str] = None


# ====================== GET /api/report/{study_id} ======================
@router.get("/{study_id}")
def get_report(
    study_id: int,
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """GET /api/report/{study_id} — Xem báo cáo (All roles, patient chỉ của mình)
    Spec UC10: xem báo cáo readonly cho Tech + Patient
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Patient isolation: verify ca chụp thuộc patient này
        if current_user.role == "patient":
            cursor.execute("""
                SELECT s.patient_id FROM studies s WHERE s.id = %s
            """, (study_id,))
            study_row = cursor.fetchone()
            if not study_row or study_row["patient_id"] != current_user.linked_patient_id:
                raise HTTPException(status_code=403, detail="Không có quyền xem báo cáo này")

        cursor.execute("""
            SELECT r.*,
                   u.full_name  AS doctor_name,
                   s.modality, s.study_date, s.description AS study_description,
                   p.full_name  AS patient_name, p.patient_id AS patient_code
            FROM diagnostic_reports r
            JOIN users    u ON r.doctor_id = u.id
            JOIN studies  s ON r.study_id  = s.id
            JOIN patients p ON s.patient_id = p.id
            WHERE r.study_id = %s
        """, (study_id,))
        report = cursor.fetchone()

        if not report:
            return {"report": None, "message": "Chưa có báo cáo"}

        # Loại bỏ embedding khỏi response (vector 1024d — không cần gửi FE)
        row = dict(report)
        row.pop("embedding", None)
        return {"report": row}
    finally:
        cursor.close()
        release_connection(conn)


# ====================== POST /api/report ======================
@router.post("")
def create_report(
    body: ReportRequest,
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """POST /api/report — Tạo báo cáo (Doctor/Admin only)
    Spec UC08: tạo report + update status PENDING → REPORTED
    Spec FR-005: tạo embedding vector 1024d khi lưu (TODO: dùng BGE-M3 sau)
    """
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ/admin được viết báo cáo")

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            INSERT INTO diagnostic_reports (study_id, doctor_id, findings, conclusion, recommendation)
            VALUES (%s, %s, %s, %s, %s)
            RETURNING id
        """, (
            body.study_id,
            current_user.id,          # ← FIX: User object
            body.findings,
            body.conclusion,
            body.recommendation
        ))
        report_id = cursor.fetchone()["id"]

        # Spec US5 acceptance: status PENDING → REPORTED sau khi lưu
        cursor.execute(
            "UPDATE studies SET status = 'REPORTED' WHERE id = %s",
            (body.study_id,)
        )
        conn.commit()
        return {"id": report_id, "message": "Tạo báo cáo thành công"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        release_connection(conn)


# ====================== PUT /api/report/{report_id} ======================
@router.put("/{report_id}")
def update_report(
    report_id: int,
    body: ReportRequest,
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """PUT /api/report/{id} — Cập nhật báo cáo (Doctor/Admin only)
    Spec UC09: update report + tính lại embedding (TODO: BGE-M3)
    """
    if current_user.role not in ("doctor", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ bác sĩ/admin được sửa báo cáo")

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            UPDATE diagnostic_reports
            SET findings = %s, conclusion = %s, recommendation = %s, updated_at = NOW()
            WHERE id = %s
            RETURNING id
        """, (body.findings, body.conclusion, body.recommendation, report_id))

        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Báo cáo không tồn tại")

        conn.commit()
        return {"message": "Cập nhật báo cáo thành công"}

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        release_connection(conn)


# ====================== GET /api/report/{study_id}/pdf ======================
@router.get("/{study_id}/pdf")
def export_pdf(
    study_id: int,
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """GET /api/report/{study_id}/pdf — Xuất PDF báo cáo
    Spec UC11 + FR-010: PDF có header bệnh viện + thông tin đầy đủ
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # Patient isolation
        if current_user.role == "patient":
            cursor.execute("SELECT patient_id FROM studies WHERE id = %s", (study_id,))
            s = cursor.fetchone()
            if not s or s["patient_id"] != current_user.linked_patient_id:
                raise HTTPException(status_code=403, detail="Không có quyền xuất PDF này")

        cursor.execute("""
            SELECT r.findings, r.conclusion, r.recommendation, r.report_date,
                   u.full_name  AS doctor_name,
                   s.study_date, s.modality, s.description AS study_description,
                   p.full_name  AS patient_name, p.patient_id AS patient_code,
                   p.birth_date, p.gender
            FROM diagnostic_reports r
            JOIN users    u ON r.doctor_id  = u.id
            JOIN studies  s ON r.study_id   = s.id
            JOIN patients p ON s.patient_id = p.id
            WHERE r.study_id = %s
        """, (study_id,))
        data = cursor.fetchone()

        if not data:
            raise HTTPException(status_code=404, detail="Không tìm thấy báo cáo để xuất PDF")

        data = dict(data)
    finally:
        cursor.close()
        release_connection(conn)

    # Build PDF với ReportLab (spec FR-010: header bệnh viện)
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.lib import colors
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)

        styles = getSampleStyleSheet()
        story = []

        # Header bệnh viện (spec FR-010)
        story.append(Paragraph("<b>BỆNH VIỆN PACS++</b>", styles["Title"]))
        story.append(Paragraph("Khoa Chẩn đoán hình ảnh", styles["Normal"]))
        story.append(HRFlowable(width="100%", thickness=1, color=colors.gray))
        story.append(Spacer(1, 0.3*cm))

        # Tiêu đề báo cáo
        story.append(Paragraph("<b>PHIẾU KẾT QUẢ CHẨN ĐOÁN HÌNH ẢNH</b>", styles["Heading1"]))
        story.append(Spacer(1, 0.3*cm))

        # Thông tin bệnh nhân
        patient_info = [
            ["Họ tên BN:", data.get("patient_name", "")],
            ["Mã BN:",     data.get("patient_code", "")],
            ["Ngày sinh:", str(data.get("birth_date", ""))],
            ["Giới tính:", "Nam" if data.get("gender") == "M" else "Nữ" if data.get("gender") == "F" else ""],
            ["Ngày chụp:", str(data.get("study_date", ""))],
            ["Modality:",  data.get("modality", "")],
            ["Mô tả ca:",  data.get("study_description", "")],
        ]
        t = Table(patient_info, colWidths=[4*cm, 13*cm])
        t.setStyle(TableStyle([
            ("FONTNAME",  (0, 0), (-1, -1), "Helvetica"),
            ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
            ("FONTSIZE",  (0, 0), (-1, -1), 10),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(t)
        story.append(Spacer(1, 0.5*cm))

        # Nội dung báo cáo
        story.append(Paragraph("<b>KẾT QUẢ:</b>", styles["Heading2"]))
        story.append(Paragraph(data.get("findings", ""), styles["Normal"]))
        story.append(Spacer(1, 0.3*cm))

        story.append(Paragraph("<b>KẾT LUẬN:</b>", styles["Heading2"]))
        story.append(Paragraph(data.get("conclusion", ""), styles["Normal"]))
        story.append(Spacer(1, 0.3*cm))

        if data.get("recommendation"):
            story.append(Paragraph("<b>ĐỀ NGHỊ:</b>", styles["Heading2"]))
            story.append(Paragraph(data["recommendation"], styles["Normal"]))
            story.append(Spacer(1, 0.3*cm))

        # Chữ ký bác sĩ
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(
            f"Bác sĩ đọc phim: <b>{data.get('doctor_name', '')}</b>",
            styles["Normal"]
        ))
        story.append(Paragraph(
            f"Ngày báo cáo: {str(data.get('report_date', ''))[:10]}",
            styles["Normal"]
        ))

        doc.build(story)
        buffer.seek(0)

        filename = f"report_study_{study_id}.pdf"
        return StreamingResponse(
            buffer,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )

    except ImportError:
        raise HTTPException(status_code=500, detail="ReportLab chưa được cài. Chạy: pip install reportlab")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xuất PDF: {e}")
