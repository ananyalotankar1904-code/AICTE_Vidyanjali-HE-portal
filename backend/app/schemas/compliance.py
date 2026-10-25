from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from backend.app.enums import ObligationStatus


class ObligationCreateRequest(BaseModel):
    institution_id: str
    application_id: Optional[str] = None
    title: str
    obligation_type: str
    description: str
    source_reference: Optional[str] = "Illustrative Demo Configuration"
    is_illustrative_demo_rule: bool = True
    due_date: Optional[datetime] = None
    responsible_owner: Optional[str] = None


class ObligationSubmitEvidenceRequest(BaseModel):
    evidence_document_id: str
    submission_notes: Optional[str] = None


class ObligationVerifyRequest(BaseModel):
    verification_notes: Optional[str] = None


class ObligationCorrectionRequest(BaseModel):
    reason: str
    guidance: Optional[str] = None


class ObligationResponse(BaseModel):
    id: str
    application_id: Optional[str] = None
    institution_id: str
    title: str
    obligation_type: str
    description: str
    source_reference: str
    is_illustrative_demo_rule: bool
    due_date: Optional[datetime] = None
    responsible_owner: Optional[str] = None
    status: ObligationStatus
    evidence_document_id: Optional[str] = None
    submission_notes: Optional[str] = None
    submitted_at: Optional[datetime] = None
    submitted_by: Optional[str] = None
    verification_result: Optional[str] = None
    verification_notes: Optional[str] = None
    correction_reason: Optional[str] = None
    verified_at: Optional[datetime] = None
    verified_by: Optional[str] = None
    correction_history: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
