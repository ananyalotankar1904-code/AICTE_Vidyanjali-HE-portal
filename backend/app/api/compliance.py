from typing import List, Optional
from fastapi import APIRouter, Depends, Header, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.enums import ObligationStatus, UserRole
from app.schemas.compliance import (
    ObligationCreateRequest,
    ObligationSubmitEvidenceRequest,
    ObligationVerifyRequest,
    ObligationCorrectionRequest,
    ObligationResponse,
)
from app.services.compliance import (
    create_compliance_obligation,
    get_obligation_by_id,
    list_obligations,
    submit_obligation_evidence,
    verify_compliance_obligation,
    request_obligation_correction,
)

router = APIRouter(prefix="/undertakings", tags=["Compliance Obligations & Undertakings"])


@router.get("", response_model=List[ObligationResponse])
def get_obligations(
    institution_id: Optional[str] = Query(None, description="Filter by institution ID"),
    application_id: Optional[str] = Query(None, description="Filter by application ID"),
    status: Optional[ObligationStatus] = Query(None, description="Filter by obligation status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Lists compliance undertakings with optional filters."""
    return list_obligations(
        db=db,
        institution_id=institution_id,
        application_id=application_id,
        status_filter=status,
        skip=skip,
        limit=limit
    )


@router.post("", response_model=ObligationResponse, status_code=status.HTTP_201_CREATED)
def create_obligation(
    payload: ObligationCreateRequest,
    x_user_id: Optional[str] = Header("OFFICER_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.COMPLIANCE_OFFICER.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Registers a new statutory undertaking or compliance obligation."""
    return create_compliance_obligation(
        db=db,
        institution_id=payload.institution_id,
        title=payload.title,
        obligation_type=payload.obligation_type,
        description=payload.description,
        application_id=payload.application_id,
        source_reference=payload.source_reference or "Illustrative Demo Configuration",
        is_illustrative_demo_rule=payload.is_illustrative_demo_rule,
        due_date=payload.due_date,
        responsible_owner=payload.responsible_owner,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.get("/{obligation_id}", response_model=ObligationResponse)
def get_obligation_detail(
    obligation_id: str,
    db: Session = Depends(get_db)
):
    """Retrieves full details of an obligation including correction and submission history."""
    return get_obligation_by_id(db, obligation_id)


@router.post("/{obligation_id}/submit", response_model=ObligationResponse)
def submit_evidence(
    obligation_id: str,
    payload: ObligationSubmitEvidenceRequest,
    x_user_id: Optional[str] = Header("INSTITUTION_REP", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.APPLICANT.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Institution submits evidence for the obligation, transitioning it to SUBMITTED state."""
    return submit_obligation_evidence(
        db=db,
        obligation_id=obligation_id,
        evidence_document_id=payload.evidence_document_id,
        submission_notes=payload.submission_notes,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.post("/{obligation_id}/verify", response_model=ObligationResponse)
def verify_obligation(
    obligation_id: str,
    payload: ObligationVerifyRequest,
    x_user_id: Optional[str] = Header("COMPLIANCE_OFFICER_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.COMPLIANCE_OFFICER.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Authorized compliance officer officially verifies the submitted obligation evidence."""
    return verify_compliance_obligation(
        db=db,
        obligation_id=obligation_id,
        verification_notes=payload.verification_notes,
        actor_id=x_user_id,
        actor_role=x_user_role
    )


@router.post("/{obligation_id}/request-correction", response_model=ObligationResponse)
def request_correction(
    obligation_id: str,
    payload: ObligationCorrectionRequest,
    x_user_id: Optional[str] = Header("COMPLIANCE_OFFICER_1", alias="X-User-Id"),
    x_user_role: Optional[str] = Header(UserRole.COMPLIANCE_OFFICER.value, alias="X-User-Role"),
    db: Session = Depends(get_db)
):
    """Requests corrections for deficient evidence, returning the obligation to NEEDS_CORRECTION."""
    return request_obligation_correction(
        db=db,
        obligation_id=obligation_id,
        reason=payload.reason,
        guidance=payload.guidance,
        actor_id=x_user_id,
        actor_role=x_user_role
    )
