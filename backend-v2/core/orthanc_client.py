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
    def find_study_by_uid(cls, study_instance_uid: str) -> str | None:
        """Tìm Orthanc study ID bằng DICOM StudyInstanceUID
        Dùng Orthanc Tools/Find API — reliable hơn dùng ParentStudy ID
        Returns: Orthanc study ID string hoặc None nếu không tìm thấy
        """
        try:
            response = requests.post(
                f"{ORTHANC_URL}/tools/find",
                json={
                    "Level": "Study",
                    "Query": {"StudyInstanceUID": study_instance_uid},
                    "Limit": 1
                },
                timeout=10
            )
            response.raise_for_status()
            results = response.json()
            return results[0] if results else None
        except Exception as e:
            print(f"[WARN] Orthanc find_study_by_uid failed: {e}")
            return None

    @classmethod
    def get_instance_file(cls, instance_id: str) -> bytes:
        """Download 1 file DICOM binary từ Orthanc"""
        response = requests.get(
            f"{ORTHANC_URL}/instances/{instance_id}/file",
            timeout=30
        )
        response.raise_for_status()
        return response.content
