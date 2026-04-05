import pydicom
from io import BytesIO


class DicomParser:
    """Đọc metadata từ file .dcm"""

    @classmethod
    def parse(cls, file_bytes: bytes) -> dict:
        """Đọc file DICOM binary → trả dict metadata"""
        ds = pydicom.dcmread(BytesIO(file_bytes), stop_before_pixels=True)

        # Hàm helper — lấy giá trị, trả '' nếu tag không tồn tại
        def get(tag, default=""):
            value = getattr(ds, tag, default)
            return str(value).strip() if value else default

        # Chuyển ngày DICOM "20260301" → "2026-03-01"
        def parse_date(tag):
            raw = get(tag)
            if raw and len(raw) == 8:
                return f"{raw[:4]}-{raw[4:6]}-{raw[6:8]}"
            return None

        return {
            "patient_id": get("PatientID"),
            "patient_name": get("PatientName"),
            "patient_sex": get("PatientSex"),
            "patient_age": get("PatientAge"),
            "patient_birth_date": parse_date("PatientBirthDate"),
            "study_uid": get("StudyInstanceUID"),
            "study_date": parse_date("StudyDate"),
            "study_description": get("StudyDescription"),
            "modality": get("Modality"),
            "body_part": get("BodyPartExamined"),
            "series_uid": get("SeriesInstanceUID"),
        }
