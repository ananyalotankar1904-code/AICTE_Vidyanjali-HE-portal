from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.enums import DocumentReviewStatus


class DocumentRegisterRequest(BaseModel):
    institution_id: str
    document_type: str
    title: str
    file_name: str
    storage_path: Optional[str] = None
    file_size_bytes: int = 0
    file_mime_type: Optional[str] = "application/pdf"
    application_id: Optional[str] = None
    obligation_id: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_expiry_tracked: bool = False


class DocumentRenewRequest(BaseModel):
    title: Optional[str] = None
    file_name: str
    storage_path: Optional[str] = None
    file_size_bytes: int = 0
    file_mime_type: Optional[str] = "application/pdf"
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    renewal_reason: Optional[str] = None


class DocumentReviewRequest(BaseModel):
    status: DocumentReviewStatus
    review_notes: Optional[str] = None


class DocumentResponse(BaseModel):
    id: str
    application_id: Optional[str] = None
    obligation_id: Optional[str] = None
    institution_id: str
    document_type: str
    title: str
    file_name: str
    storage_path: str
    file_size_bytes: int
    file_mime_type: str
    version: int
    is_latest: bool
    previous_version_id: Optional[str] = None
    issue_date: Optional[datetime] = None
    expiry_date: Optional[datetime] = None
    is_expiry_tracked: bool
    review_status: DocumentReviewStatus
    reviewed_at: Optional[datetime] = None
    reviewed_by: Optional[str] = None
    review_notes: Optional[str] = None
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
