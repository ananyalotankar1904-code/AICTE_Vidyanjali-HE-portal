import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, DateTime, Enum as SQLEnum, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base
from app.enums import DocumentReviewStatus


def utc_now():
    return datetime.now(timezone.utc)


class Document(Base):
    """Represents institutional regulatory document metadata, version history, and expiry lifecycle."""
    __tablename__ = "documents"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    application_id = Column(String(36), ForeignKey("applications.id"), nullable=True, index=True)
    obligation_id = Column(String(36), ForeignKey("compliance_obligations.id"), nullable=True, index=True)
    institution_id = Column(String(50), nullable=False, index=True)
    
    document_type = Column(String(100), nullable=False, index=True)  # e.g. FIRE_SAFETY_NOC, LAND_TITLE_DEED
    title = Column(String(200), nullable=False)
    file_name = Column(String(255), nullable=False)
    storage_path = Column(String(500), nullable=False)  # Safe abstract identifier, e.g. /vault/docs/doc-123.pdf
    file_size_bytes = Column(Integer, default=0, nullable=False)
    file_mime_type = Column(String(100), default="application/pdf", nullable=False)
    
    # Versioning
    version = Column(Integer, default=1, nullable=False)
    is_latest = Column(Boolean, default=True, nullable=False, index=True)
    previous_version_id = Column(String(36), ForeignKey("documents.id"), nullable=True)
    
    # Expiry tracking
    issue_date = Column(DateTime, nullable=True)
    expiry_date = Column(DateTime, nullable=True, index=True)
    is_expiry_tracked = Column(Boolean, default=False, nullable=False)
    
    # Review status
    review_status = Column(SQLEnum(DocumentReviewStatus), default=DocumentReviewStatus.PENDING_REVIEW, nullable=False, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(String(100), nullable=True)
    review_notes = Column(String(500), nullable=True)
    
    created_by = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=utc_now, nullable=False)
    updated_at = Column(DateTime, default=utc_now, onupdate=utc_now, nullable=False)

    # Relationships
    application = relationship("Application", back_populates="documents")
    obligation = relationship("ComplianceObligation", back_populates="documents")
    previous_version = relationship("Document", remote_side=[id], backref="next_versions")
