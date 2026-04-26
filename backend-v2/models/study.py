# models/study.py
from sqlalchemy import Column, Integer, String, Date, DateTime, Text, ForeignKey
from sqlalchemy.sql import func
from database.base import Base


class Study(Base):
    __tablename__ = "studies"

    id = Column(Integer, primary_key=True, index=True)
    study_uid = Column(String(200), unique=True, nullable=False)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    study_date = Column(Date, nullable=False)
    modality = Column(String(10))         # CR, CT, MR, US, DX, MG
    body_part = Column(String(50))
    description = Column(Text)
    status = Column(String(20), default="PENDING")   # PENDING, REPORTED, VERIFIED
    technician_id = Column(Integer, ForeignKey("users.id"))
    orthanc_id = Column(String(200))
    num_instances = Column(Integer, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<Study {self.study_uid} [{self.modality}]>"
