import os
import sys
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import ORTHANC_URL


class OrthancClient:
    """Gọi Orthanc REST API — upload/download ảnh DICOM"""

    @classmethod
    def upload_dicom(cls, file_bytes: bytes) -> dict:
        """Upload file .dcm lên Orthanc → trả thông tin study"""
        response = requests.post(
            f"{ORTHANC_URL}/instances",
            data=file_bytes,
            headers={"Content-Type": "application/dicom"}
        )
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_study(cls, orthanc_id: str) -> dict:
        """Lấy thông tin 1 study từ Orthanc"""
        response = requests.get(f"{ORTHANC_URL}/studies/{orthanc_id}")
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_study_instances(cls, orthanc_id: str) -> list:
        """Lấy danh sách instances (ảnh) của 1 study"""
        response = requests.get(f"{ORTHANC_URL}/studies/{orthanc_id}/instances")
        response.raise_for_status()
        return response.json()

    @classmethod
    def get_instance_file(cls, instance_id: str) -> bytes:
        """Download 1 file DICOM binary từ Orthanc"""
        response = requests.get(f"{ORTHANC_URL}/instances/{instance_id}/file")
        response.raise_for_status()
        return response.content
