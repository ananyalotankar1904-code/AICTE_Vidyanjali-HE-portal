from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import DocumentReviewStatus, UserRole
from app.schemas.document import (
    DocumentRegisterRequest,
    DocumentRenewRequest,
    DocumentReviewRequest,
    DocumentResponse,
)
from app.services.document import (
    register_document,
    get_document_by_id,
    list_documents,
    renew_document,
    review_document,
    get_expiring_soon_documents,
    get_expired_documents,
)

router = APIRouter(prefix="/documents", tags=["Documents & Expiry Lifecycle"])


@router.get("", response_model=List[DocumentResponse])
def get_documents(
    institution_id: Optional[str] = Query(None, description="Filter by institution ID"),
    application_id: Optional[str] = Query(None, description="Filter by application ID"),
    obligation_id: Optional[str] = Query(None, description="Filter by obligation ID"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    is_latest: Optional[bool] = Query(None, description="Filter by latest version only"),
    review_status: Optional[DocumentReviewStatus] = Query(None, description="Filter by review status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists registered document records with version and review filters."""
    return list_documents(
        db=db,
        institution_id=institution_id,
        application_id=application_id,
        obligation_id=obligation_id,
        document_type=document_type,
        is_latest=is_latest,
        review_status=review_status,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def register_new_document(
    payload: DocumentRegisterRequest,
    x_user_id: Optional[str] = Header("APPLICANT_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.APPLICANT.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Registers metadata for a new regulatory document (Version 1)."""
    return register_document(
        db=db,
        institution_id=payload.institution_id,
        document_type=payload.document_type,
        title=payload.title,
        file_name=payload.file_name,
        storage_path=payload.storage_path,
        file_size_bytes=payload.file_size_bytes,
        file_mime_type=payload.file_mime_type or "application/pdf",
        application_id=payload.application_id,
        obligation_id=payload.obligation_id,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        is_expiry_tracked=payload.is_expiry_tracked,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.get("/status/expiring-soon", response_model=List[DocumentResponse])
def get_expiring_documents(
    reference_time: Optional[datetime] = Query(None, description="Reference time for evaluation"),
    threshold_days: int = Query(30, ge=1, le=365, description="Days threshold to check"),
    db: Session = Depends(get_db)
):
    """Returns active documents approaching expiry within the threshold period."""
    return get_expiring_soon_documents(db=db, reference_time=reference_time, threshold_days=threshold_days)


@router.get("/status/expired", response_model=List[DocumentResponse])
def get_already_expired_documents(
    reference_time: Optional[datetime] = Query(None, description="Reference time for evaluation"),
    db: Session = Depends(get_db)
):
    """Returns active documents whose expiry date has passed."""
    return get_expired_documents(db=db, reference_time=reference_time)


@router.get("/{document_id}", response_model=DocumentResponse)
def get_document_detail(
    document_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves single document metadata and version relationship."""
    return get_document_by_id(db, document_id)


@router.post("/{document_id}/renew", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def renew_document_version(
    document_id: str,
    payload: DocumentRenewRequest,
    x_user_id: Optional[str] = Header("APPLICANT_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.APPLICANT.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """
    Uploads a renewal or replacement document.
    Creates a new version linked to the prior version without overwriting the old record.
    """
    return renew_document(
        db=db,
        document_id=document_id,
        file_name=payload.file_name,
        storage_path=payload.storage_path,
        file_size_bytes=payload.file_size_bytes,
        file_mime_type=payload.file_mime_type or "application/pdf",
        title=payload.title,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        renewal_reason=payload.renewal_reason,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.post("/{document_id}/review", response_model=DocumentResponse)
def review_document_status(
    document_id: str,
    payload: DocumentReviewRequest,
    x_user_id: Optional[str] = Header("COMPLIANCE_OFFICER_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.COMPLIANCE_OFFICER.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Authorized reviewer updates the verification status of a document."""
    return review_document(
        db=db,
        document_id=document_id,
        status_update=payload.status,
        review_notes=payload.review_notes,
        actor_id=x_user_id,
        actor_role=x_user_role
    )
