import os
import sys

from fastapi import APIRouter, HTTPException, Request, UploadFile, File
from fastapi.responses import StreamingResponse
from io import BytesIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.auth_utils import AuthUtils
from core.dicom_parser import DicomParser
from core.orthanc_client import OrthancClient
from database.connection import DatabaseConnection
from psycopg2.extras import RealDictCursor

router = APIRouter(prefix="/api/dicom", tags=["DICOM"])


@router.post("/upload")
async def upload_dicom(request: Request, file: UploadFile = File(...)):
    """POST /api/dicom/upload — Upload file .dcm → Orthanc + DB"""
    user = AuthUtils.get_current_user(request)

    # Chỉ tech và admin được upload
    if user["role"] not in ("technician", "admin"):
        raise HTTPException(status_code=403, detail="Chỉ technician/admin được upload")

    # 1. Đọc file bytes
    file_bytes = await file.read()

    # 2. Parse metadata từ DICOM
    metadata = DicomParser.parse(file_bytes)

    if not metadata["patient_id"] or not metadata["study_uid"]:
        raise HTTPException(status_code=400, detail="File DICOM thiếu PatientID hoặc StudyUID")

    conn = DatabaseConnection.get_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)

    try:
        # 3. Upsert patient (tạo mới nếu chưa có)
        cursor.execute("""
            INSERT INTO patients (patient_id, full_name, gender)
            VALUES (%s, %s, %s)
            ON CONFLICT (patient_id) DO NOTHING
            RETURNING id
        """, (
            metadata["patient_id"],
            metadata["patient_name"] or metadata["patient_id"],
            metadata["patient_sex"] if metadata["patient_sex"] in ("M", "F") else None
        ))

        result = cursor.fetchone()
        if result:
            patient_db_id = result["id"]
        else:
            cursor.execute("SELECT id FROM patients WHERE patient_id = %s", (metadata["patient_id"],))
            patient_db_id = cursor.fetchone()["id"]

        # 4. Upload lên Orthanc
        orthanc_result = OrthancClient.upload_dicom(file_bytes)
        orthanc_study_id = orthanc_result.get("ParentStudy", "")

        # 5. Upsert study
        cursor.execute("""
            INSERT INTO studies (study_uid, patient_id, study_date, modality, body_part, 
                               description, technician_id, orthanc_id, num_instances)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 1)
            ON CONFLICT (study_uid) DO UPDATE SET
                orthanc_id = EXCLUDED.orthanc_id,
                num_instances = studies.num_instances + 1
            RETURNING id
        """, (
            metadata["study_uid"],
            patient_db_id,
            metadata["study_date"],
            metadata["modality"] if metadata["modality"] in ("CR","CT","MR","US","DX","MG") else None,
            metadata["body_part"],
            metadata["study_description"],
            user["sub"],
            orthanc_study_id
        ))

        # 6. Auto tạo tài khoản patient
        cursor.execute("SELECT id FROM users WHERE username = %s", (metadata["patient_id"],))
        existing_user = cursor.fetchone()

        if not existing_user:
            password_hash = AuthUtils.hash_password(metadata["patient_id"] + "@")
            cursor.execute("""
                INSERT INTO users (username, password_hash, full_name, role, linked_patient_id)
                VALUES (%s, %s, %s, 'patient', %s)
            """, (
                metadata["patient_id"],
                password_hash,
                metadata["patient_name"] or metadata["patient_id"],
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

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        DatabaseConnection.release_connection(conn)


@router.get("/wado")
def get_wado(request: Request, objectId: str):
    """GET /api/dicom/wado?objectId=xxx — Stream ảnh DICOM"""
    AuthUtils.get_current_user(request)

    try:
        dicom_bytes = OrthancClient.get_instance_file(objectId)
        return StreamingResponse(
            BytesIO(dicom_bytes),
            media_type="application/dicom"
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Instance not found: {e}")
