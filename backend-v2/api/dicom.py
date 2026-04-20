# api/dicom.py
import os
import sys
import requests

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Request
from fastapi.responses import StreamingResponse
from io import BytesIO
from psycopg2.extras import RealDictCursor

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from core.dicom_parser import DicomParser
from core.orthanc_client import OrthancClient
from database.connection import get_connection, release_connection
from models.user import User
from config import ORTHANC_URL

router = APIRouter(prefix="/api/dicom", tags=["DICOM"])


# ====================== POST /api/dicom/upload ======================
@router.post("/upload")
async def upload_dicom(
    file: UploadFile = File(...),
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """POST /api/dicom/upload — Upload file .dcm → Orthanc + DB (Tech/Admin only)
    Spec US3: auto-parse metadata, tạo patient nếu chưa có, sync DB, upload Orthanc
    """
    # Spec: chỉ technician/admin được upload (role matrix)
    if current_user.role not in ("technician", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ technician/admin được upload DICOM")

    # Spec edge case: chỉ nhận file .dcm
    if not file.filename.endswith(".dcm"):
        raise HTTPException(status_code=400, detail="Chỉ chấp nhận file .dcm")

    file_bytes = await file.read()

    # Parse DICOM metadata
    metadata = DicomParser.parse(file_bytes)

    if not metadata.get("patient_id") or not metadata.get("study_uid"):
        raise HTTPException(status_code=400, detail="File DICOM thiếu PatientID hoặc StudyUID")

    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        # 1. Upsert patient
        cursor.execute("""
            INSERT INTO patients (patient_id, full_name, gender)
            VALUES (%s, %s, %s)
            ON CONFLICT (patient_id) DO NOTHING
            RETURNING id
        """, (
            metadata["patient_id"],
            metadata.get("patient_name") or metadata["patient_id"],
            metadata.get("patient_sex") if metadata.get("patient_sex") in ("M", "F") else None
        ))
        result = cursor.fetchone()
        if result:
            patient_db_id = result["id"]
        else:
            cursor.execute("SELECT id FROM patients WHERE patient_id = %s", (metadata["patient_id"],))
            patient_db_id = cursor.fetchone()["id"]

        # 2. Upload lên Orthanc
        try:
            orthanc_result = OrthancClient.upload_dicom(file_bytes)
            orthanc_study_id = orthanc_result.get("ParentStudy", "")
        except Exception as e:
            # Orthanc có thể chưa chạy — ghi log nhưng không crash
            orthanc_study_id = ""
            print(f"[WARN] Orthanc upload failed: {e}")

        # 3. Upsert study (spec edge: trùng StudyUID → update, không duplicate)
        cursor.execute("""
            INSERT INTO studies (study_uid, patient_id, study_date, modality,
                                 body_part, description, technician_id, orthanc_id, num_instances)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
            ON CONFLICT (study_uid) DO UPDATE SET
                orthanc_id     = EXCLUDED.orthanc_id,
                num_instances  = studies.num_instances + 1
            RETURNING id
        """, (
            metadata["study_uid"],
            patient_db_id,
            metadata.get("study_date"),
            metadata.get("modality") if metadata.get("modality") in ("CR", "CT", "MR", "US", "DX", "MG") else None,
            metadata.get("body_part"),
            metadata.get("study_description"),
            current_user.id,          # ← FIX: User object, không phải dict
            orthanc_study_id
        ))

        # 4. Auto-tạo tài khoản patient (spec Q1: auto-create khi upload)
        cursor.execute("SELECT id FROM users WHERE username = %s", (metadata["patient_id"],))
        if not cursor.fetchone():
            password_hash = AuthUtils.hash_password(metadata["patient_id"] + "@")
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, linked_patient_id)
                VALUES (%s, %s, %s, 'patient', %s)
            """, (
                metadata["patient_id"],
                password_hash,
                metadata.get("patient_name") or metadata["patient_id"],
                patient_db_id
            ))

        conn.commit()
        return {
            "status": "success",
            "message": f"Uploaded {file.filename}",
            "patient_id": metadata["patient_id"],
            "study_uid": metadata["study_uid"],
            "orthanc_id": orthanc_study_id
        }

    except HTTPException:
        raise
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        release_connection(conn)


# ====================== GET /api/dicom/instances/{study_id} ======================
@router.get("/instances/{study_id}")
def get_study_instances(
    study_id: int,
    current_user: User = Depends(AuthUtils.get_current_user),
):
    """GET /api/dicom/instances/{study_id} — Lấy danh sách instance IDs từ Orthanc
    Spec plan.md line 306 — dùng cho Cornerstone.js Viewer (spec US4)
    """
    conn = get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    try:
        cursor.execute("""
            SELECT s.orthanc_id, s.study_uid, s.num_instances,
                   p.full_name AS patient_name, p.patient_id AS patient_code,
                   s.study_date, s.modality, s.description
            FROM studies s
            JOIN patients p ON s.patient_id = p.id
            WHERE s.id = %s
        """, (study_id,))
        study = cursor.fetchone()

        if not study:
            raise HTTPException(status_code=404, detail="Study not found")

        # Patient isolation (spec FR-009)
        if current_user.role == "patient":
            cursor.execute("SELECT id FROM patients WHERE patient_id = %s",
                           (study["patient_code"],))
            pt = cursor.fetchone()
            if not pt or pt["id"] != current_user.linked_patient_id:
                raise HTTPException(status_code=403, detail="Không có quyền xem ca này")

        # Lấy instances từ Orthanc — dùng StudyInstanceUID để tìm (reliable)
        orthanc_id   = study["orthanc_id"]
        study_uid    = study.get("study_uid")
        raw_instances = []
        real_orthanc_study_id = orthanc_id

        try:
            # Ưu tiên: tìm bằng StudyInstanceUID (luôn khớp)
            if study_uid:
                result = OrthancClient.find_study_by_uid(study_uid)
                if result:
                    real_orthanc_study_id = result
                    raw_instances = OrthancClient.get_study_instances(real_orthanc_study_id)
            # Fallback: dùng orthanc_id lưu trong DB
            elif orthanc_id:
                raw_instances = OrthancClient.get_study_instances(orthanc_id)
        except Exception as e:
            print(f"[WARN] Cannot fetch instances from Orthanc: {e}")

        # Orthanc trả về list of objects: [{"ID": "abc123", "Type": "Instance", ...}, ...]
        # Frontend cần list of ID strings: ["abc123", "def456", ...]
        instance_ids = []
        for inst in raw_instances:
            if isinstance(inst, dict) and "ID" in inst:
                instance_ids.append(inst["ID"])
            elif isinstance(inst, str):
                instance_ids.append(inst)

        return {
            "study_id":         study_id,
            "orthanc_study_id": real_orthanc_study_id,
            "study_info":       dict(study),
            "instances":        instance_ids,
            "total":            len(instance_ids)
        }
    finally:
        cursor.close()
        release_connection(conn)


# ====================== GET /api/dicom/wado ======================
@router.get("/wado")
def get_wado(
    objectId: str,
    token: str = None,          # Cornerstone.js gửi token qua ?token=
    request: Request = None,    # Đọc Authorization header thủ công
):
    """GET /api/dicom/wado?objectId=xxx&token=xxx — Stream DICOM từ Orthanc
    
    Cornerstone.js không thể thêm Authorization header vào XHR image request
    → Chấp nhận token từ query param HOẶC Authorization header
    """
    from jose import jwt as _jwt, JWTError
    from config import JWT_SECRET, JWT_ALGORITHM

    # 1. Lấy raw token — ưu tiên query param (Cornerstone), fallback header
    raw_token = token
    if not raw_token and request:
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            raw_token = auth_header[7:]

    if not raw_token:
        raise HTTPException(status_code=401, detail="Token bắt buộc")

    # 2. Validate token
    try:
        payload = _jwt.decode(raw_token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "access":
            raise HTTPException(status_code=401, detail="Token không hợp lệ")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token không hợp lệ hoặc hết hạn")

    # 3. Stream DICOM từ Orthanc — TRUE streaming (không buffer toàn bộ file)
    try:
        orthanc_response = requests.get(
            f"{ORTHANC_URL}/instances/{objectId}/file",
            stream=True,   # ← Stream chunks, không load hết vào RAM
            timeout=60,
        )
        orthanc_response.raise_for_status()

        content_length = orthanc_response.headers.get("Content-Length")
        headers = {"Content-Disposition": f"inline; filename={objectId}.dcm"}
        if content_length:
            headers["Content-Length"] = content_length

        return StreamingResponse(
            orthanc_response.iter_content(chunk_size=256 * 1024),  # 256KB chunks
            media_type="application/dicom",
            headers=headers,
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Instance not found in Orthanc: {e}")


