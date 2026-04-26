# models/report.py
from sqlalchemy import Column, Integer, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from database.base import Base


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(Integer, primary_key=True, index=True)
    study_id = Column(Integer, ForeignKey("studies.id"), unique=True)
    doctor_id = Column(Integer, ForeignKey("users.id"))
    findings = Column(Text, nullable=False)
    conclusion = Column(Text, nullable=False)
    recommendation = Column(Text)
    report_date = Column(DateTime(timezone=True), server_default=func.now())
    # embedding = vector(1024) — handled by pgvector, not SQLAlchemy

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<DiagnosticReport study_id={self.study_id}>"
