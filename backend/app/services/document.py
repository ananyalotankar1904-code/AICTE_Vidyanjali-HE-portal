import uuid
from datetime import datetime, timedelta
from typing import Optional, List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.document import Document
from app.models.application import Application
from app.models.compliance import ComplianceObligation
from app.enums import DocumentReviewStatus, EntityType, UserRole
from app.services.audit import record_audit_event
from app.utils.datetime_utils import utc_now, ensure_naive_utc


def get_document_by_id(db: Session, document_id: str) -> Document:
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with id '{document_id}' not found."
        )
    return doc


def list_documents(
    db: Session,
    institution_id: Optional[str] = None,
    application_id: Optional[str] = None,
    obligation_id: Optional[str] = None,
    document_type: Optional[str] = None,
    is_latest: Optional[bool] = None,
    review_status: Optional[DocumentReviewStatus] = None,
    skip: int = 0,
    limit: int = 50
) -> List[Document]:
    query = db.query(Document)
    if institution_id:
        query = query.filter(Document.institution_id == institution_id)
    if application_id:
        query = query.filter(Document.application_id == application_id)
    if obligation_id:
        query = query.filter(Document.obligation_id == obligation_id)
    if document_type:
        query = query.filter(Document.document_type == document_type)
    if is_latest is not None:
        query = query.filter(Document.is_latest == is_latest)
    if review_status:
        query = query.filter(Document.review_status == review_status)
    return query.order_by(Document.created_at.desc()).offset(skip).limit(limit).all()


def register_document(
    db: Session,
    institution_id: str,
    document_type: str,
    title: str,
    file_name: str,
    storage_path: Optional[str] = None,
    file_size_bytes: int = 0,
    file_mime_type: str = "application/pdf",
    application_id: Optional[str] = None,
    obligation_id: Optional[str] = None,
    issue_date: Optional[datetime] = None,
    expiry_date: Optional[datetime] = None,
    is_expiry_tracked: bool = False,
    actor_id: str = "APPLICANT_1",
    actor_role: str = UserRole.APPLICANT.value
) -> Document:
    if application_id:
        app = db.query(Application).filter(Application.id == application_id).first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Linked application '{application_id}' not found."
            )

    if obligation_id:
        ob = db.query(ComplianceObligation).filter(ComplianceObligation.id == obligation_id).first()
        if not ob:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Linked compliance obligation '{obligation_id}' not found."
            )

    safe_path = storage_path or f"/vault/docs/{institution_id}/{uuid.uuid4().hex[:12]}_{file_name}"

    norm_issue = ensure_naive_utc(issue_date)
    norm_expiry = ensure_naive_utc(expiry_date)

    doc = Document(
        institution_id=institution_id,
        application_id=application_id,
        obligation_id=obligation_id,
        document_type=document_type,
        title=title,
        file_name=file_name,
        storage_path=safe_path,
        file_size_bytes=file_size_bytes,
        file_mime_type=file_mime_type,
        version=1,
        is_latest=True,
        previous_version_id=None,
        issue_date=norm_issue,
        expiry_date=norm_expiry,
        is_expiry_tracked=is_expiry_tracked or (norm_expiry is not None),
        review_status=DocumentReviewStatus.PENDING_REVIEW,
        created_by=actor_id
    )
    db.add(doc)
    db.flush()

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="REGISTER_DOCUMENT",
        entity_type=EntityType.DOCUMENT.value,
        entity_id=doc.id,
        after_state={"title": title, "version": 1, "document_type": document_type},
        reason=f"Registered document {title} v1"
    )

    db.commit()
    db.refresh(doc)
    return doc


def renew_document(
    db: Session,
    document_id: str,
    file_name: str,
    storage_path: Optional[str] = None,
    file_size_bytes: int = 0,
    file_mime_type: str = "application/pdf",
    title: Optional[str] = None,
    issue_date: Optional[datetime] = None,
    expiry_date: Optional[datetime] = None,
    renewal_reason: Optional[str] = None,
    actor_id: str = "APPLICANT_1",
    actor_role: str = UserRole.APPLICANT.value
) -> Document:
    """
    Creates a replacement/renewal document version while strictly retaining the prior version intact.
    Links the new version to previous_version_id and marks previous version as is_latest=False.
    """
    prev_doc = get_document_by_id(db, document_id)
    if not prev_doc.is_latest:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document '{document_id}' is version {prev_doc.version} and not the latest version. Renewal must target the latest version."
        )

    prev_doc.is_latest = False
    new_version_num = prev_doc.version + 1

    safe_path = storage_path or f"/vault/docs/{prev_doc.institution_id}/{uuid.uuid4().hex[:12]}_{file_name}"
    norm_issue = ensure_naive_utc(issue_date) or prev_doc.issue_date
    norm_expiry = ensure_naive_utc(expiry_date)

    new_doc = Document(
        institution_id=prev_doc.institution_id,
        application_id=prev_doc.application_id,
        obligation_id=prev_doc.obligation_id,
        document_type=prev_doc.document_type,
        title=title or prev_doc.title,
        file_name=file_name,
        storage_path=safe_path,
        file_size_bytes=file_size_bytes,
        file_mime_type=file_mime_type,
        version=new_version_num,
        is_latest=True,
        previous_version_id=prev_doc.id,
        issue_date=norm_issue,
        expiry_date=norm_expiry,
        is_expiry_tracked=True if norm_expiry else prev_doc.is_expiry_tracked,
        review_status=DocumentReviewStatus.PENDING_REVIEW,
        created_by=actor_id
    )
    db.add(new_doc)
    db.flush()

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="RENEW_DOCUMENT",
        entity_type=EntityType.DOCUMENT.value,
        entity_id=new_doc.id,
        before_state={"previous_document_id": prev_doc.id, "previous_version": prev_doc.version},
        after_state={"new_document_id": new_doc.id, "version": new_version_num},
        reason=renewal_reason or f"Renewed/replaced document from v{prev_doc.version} to v{new_version_num}"
    )

    db.commit()
    db.refresh(new_doc)
    return new_doc


def review_document(
    db: Session,
    document_id: str,
    status_update: DocumentReviewStatus,
    review_notes: Optional[str] = None,
    actor_id: str = "COMPLIANCE_OFFICER_1",
    actor_role: str = UserRole.COMPLIANCE_OFFICER.value
) -> Document:
    doc = get_document_by_id(db, document_id)
    
    permitted_roles = [UserRole.COMPLIANCE_OFFICER.value, UserRole.SCRUTINY_OFFICER.value, UserRole.ADMIN.value]
    if actor_role not in permitted_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Role '{actor_role}' is not authorized to review documents."
        )

    before_state = {"review_status": doc.review_status.value}
    doc.review_status = status_update
    doc.reviewed_at = utc_now()
    doc.reviewed_by = actor_id
    doc.review_notes = review_notes

    record_audit_event(
        db=db,
        actor_id=actor_id,
        actor_role=actor_role,
        action="REVIEW_DOCUMENT",
        entity_type=EntityType.DOCUMENT.value,
        entity_id=doc.id,
        before_state=before_state,
        after_state={"review_status": status_update.value},
        reason=review_notes or f"Document reviewed with status {status_update.value}"
    )

    db.commit()
    db.refresh(doc)
    return doc


def get_expiring_soon_documents(
    db: Session,
    reference_time: Optional[datetime] = None,
    threshold_days: int = 30
) -> List[Document]:
    """Retrieves active (latest version) documents whose expiry date is within threshold_days."""
    ref = ensure_naive_utc(reference_time) or utc_now()
    window_end = ref + timedelta(days=threshold_days)
    return db.query(Document).filter(
        Document.is_latest.is_(True),
        Document.expiry_date.isnot(None),
        Document.expiry_date >= ref,
        Document.expiry_date <= window_end
    ).order_by(Document.expiry_date.asc()).all()


def get_expired_documents(
    db: Session,
    reference_time: Optional[datetime] = None
) -> List[Document]:
    """Retrieves active (latest version) documents whose expiry date has passed."""
    ref = ensure_naive_utc(reference_time) or utc_now()
    return db.query(Document).filter(
        Document.is_latest.is_(True),
        Document.expiry_date.isnot(None),
        Document.expiry_date < ref
    ).order_by(Document.expiry_date.asc()).all()
