import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Enum as SQLEnum, Text, JSON, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base
from app.enums import ObligationStatus


def utc_now():
    return datetime.now(timezone.utc)


class ComplianceObligation(Base):
    """Represents a regulatory undertaking or ongoing institutional compliance obligation."""
    __tablename__ = "compliance_obligations"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=True, index=True)
    institution_id = Column(String(50), nullable=False, index=True)
    
    title = Column(String(200), nullable=False)
    obligation_type = Column(String(100), nullable=False)  # e.g. FACULTY_CADRE_RATIO, LAND_SAFETY_AFFIDAVIT
    description = Column(Text, nullable=False)
    
    # Source discipline: citing handbook or marked as illustrative demo configuration
    source_reference = Column(String(200), nullable=False, default="Illustrative Demo Configuration")
    is_illustrative_demo_rule = Column(Boolean, default=True, nullable=False)
    
    due_date = Column(DateTime, nullable=True, index=True)
    responsible_owner = Column(String(100), nullable=True)
    
    # Lifecycle status: PENDING -> SUBMITTED -> VERIFIED (or NEEDS_CORRECTION)
    status = Column(SQLEnum(ObligationStatus), default=ObligationStatus.PENDING, nullable=False, index=True)
    
    # Evidence submission
    evidence_document_id = Column(String(100), nullable=True)
    submission_notes = Column(Text, nullable=True)
    submitted_at = Column(DateTime, nullable=True)
    submitted_by = Column(String(100), nullable=True)
    
    # Verification & correction loop
    verification_result = Column(String(50), nullable=True)
    verification_notes = Column(Text, nullable=True)
    correction_reason = Column(Text, nullable=True)
    verified_at = Column(DateTime, nullable=True)
    verified_by = Column(String(100), nullable=True)
    
    # Correction and resubmission history: list of {requested_at, requested_by, reason, resubmitted_at, notes}
    correction_history = Column(JSON, default=list, nullable=False)

    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="compliance_obligations")
    documents = relationship("Document", back_populates="obligation")
