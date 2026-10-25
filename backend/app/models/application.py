import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text
from sqlalchemy.orm import relationship

from app.db import Base
from app.enums import ApplicationStatus, WorkflowStage


def utc_now():
    return datetime.now(timezone.utc)


class Application(Base):
    __tablename__ = "applications"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_number = Column(String(50), unique=True, nullable=False, index=True)
    institution_id = Column(String(50), nullable=False, index=True)
    institution_name = Column(String(200), nullable=False)
    application_type = Column(String(100), nullable=False)  # e.g. EXTENSION_OF_APPROVAL, NEW_INSTITUTION
    route_id = Column(String(100), nullable=False, default="ROUTE_FULL_SCRUTINY_EVC")
    status = Column(SQLEnum(ApplicationStatus), nullable=False, default=ApplicationStatus.SUBMITTED, index=True)
    current_stage = Column(SQLEnum(WorkflowStage), nullable=False, default=WorkflowStage.SCRUTINY, index=True)
    assigned_to = Column(String(100), nullable=True)
    description = Column(Text, nullable=True)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    submitted_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    # Relationships to compliance modules
    evc_records = relationship("EVCRecord", back_populates="application", cascade="all, delete-orphan")
    compliance_obligations = relationship("ComplianceObligation", back_populates="application")
    documents = relationship("Document", back_populates="application")
