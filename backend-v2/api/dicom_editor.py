import os
import sys
import pydicom
from io import BytesIO
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/editor", tags=["DICOM Editor"])

DICOM_DIR = r"E:\HoangDucLong_javisai\pacs_rag_system\dataset\dicom"


@router.get("/scan")
def scan_patients():
    """Quét folder DICOM → trả danh sách bệnh nhân (unique)"""
    patients = {}

    for root, dirs, files in os.walk(DICOM_DIR):
        for filename in files:
            if not filename.endswith(".dcm"):
                continue

            filepath = os.path.join(root, filename)
            try:
                ds = pydicom.dcmread(filepath, stop_before_pixels=True, force=True)
                pid = str(getattr(ds, "PatientID", ""))
                pname = str(getattr(ds, "PatientName", ""))
                modality = str(getattr(ds, "Modality", ""))
                study_desc = str(getattr(ds, "StudyDescription", ""))

                if pid and pid not in patients:
                    # Đếm số file của patient này
                    patients[pid] = {
                        "patient_id": pid,
                        "current_name": pname,
                        "new_name": "",
                        "modality": modality,
                        "study_description": study_desc,
                        "file_count": 0,
                        "sample_file": filepath
                    }
                if pid:
                    patients[pid]["file_count"] += 1

            except Exception:
                continue

    result = sorted(patients.values(), key=lambda x: x["patient_id"])
    return {"patients": result, "total": len(result)}


class EditRequest(BaseModel):
    patient_id: str
    new_name: str
    institution: Optional[str] = "Bệnh viện PACS++"


@router.post("/edit")
def edit_patient_name(body: EditRequest):
    """Sửa tên bệnh nhân trong tất cả file DICOM có cùng PatientID"""
    count = 0
    errors = 0

    for root, dirs, files in os.walk(DICOM_DIR):
        for filename in files:
            if not filename.endswith(".dcm"):
                continue

            filepath = os.path.join(root, filename)
            try:
                ds = pydicom.dcmread(filepath)
                pid = str(getattr(ds, "PatientID", ""))

                if pid == body.patient_id:
                    ds.PatientName = body.new_name
                    if body.institution:
                        ds.InstitutionName = body.institution
                    ds.save_as(filepath)
                    count += 1

            except Exception as e:
                errors += 1

    return {
        "status": "success",
        "patient_id": body.patient_id,
        "new_name": body.new_name,
        "files_edited": count,
        "errors": errors
    }


class BulkEditRequest(BaseModel):
    edits: list  # [{"patient_id": "A000801", "new_name": "Nguyễn Văn Tuấn"}, ...]
    institution: Optional[str] = "Bệnh viện PACS++"


@router.post("/edit-bulk")
def edit_bulk(body: BulkEditRequest):
    """Sửa tên nhiều bệnh nhân cùng lúc"""
    name_map = {e["patient_id"]: e["new_name"] for e in body.edits}
    counts = {pid: 0 for pid in name_map}
    total = 0

    for root, dirs, files in os.walk(DICOM_DIR):
        for filename in files:
            if not filename.endswith(".dcm"):
                continue

            filepath = os.path.join(root, filename)
            try:
                ds = pydicom.dcmread(filepath)
                pid = str(getattr(ds, "PatientID", ""))

                if pid in name_map:
                    ds.PatientName = name_map[pid]
                    if body.institution:
                        ds.InstitutionName = body.institution
                    ds.save_as(filepath)
                    counts[pid] += 1
                    total += 1

            except Exception:
                continue

    return {"status": "success", "total_files": total, "per_patient": counts}
