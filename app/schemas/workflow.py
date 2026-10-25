from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict, Field


class ApplicationCreate(BaseModel):
    """Payload for registering a new application."""
    institution_id: str = Field(..., description="Target Institution identifier (e.g. INST001)")
    application_type: str = Field(..., description="e.g. Extension of Approval, New Programme, Increase in Intake")
    academic_year: Optional[str] = Field("2026-2027", description="Target academic year")
    contact_email: Optional[str] = Field(None, description="Official contact email")
    contact_phone: Optional[str] = Field(None, description="Official contact phone number")
    programme_name: Optional[str] = Field(None, description="Programme title (if applicable)")
    intake_approved: Optional[int] = Field(None, description="Proposed or existing intake capacity")
    due_date: Optional[str] = Field(None, description="Custom due date YYYY-MM-DD")


class ApplicationUpdate(BaseModel):
    """
    Permitted fields that can be updated by Institution Admin.
    Protected fields (stage, status, role, deficiency_flag) CANNOT be updated here.
    """
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    programme_name: Optional[str] = None
    intake_approved: Optional[int] = None
    academic_year: Optional[str] = None


class WorkflowHistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: str
    from_stage: str
    to_stage: str
    from_status: str
    to_status: str
    action: str
    actor_id: str
    actor_role: str
    timestamp: datetime
    remarks: Optional[str] = None


class ScrutinyRecordItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: str
    scrutiny_type: str
    outcome: str
    remarks: str
    deficiency_summary: Optional[str] = None
    scrutinizer_id: str
    scrutinizer_role: str
    created_at: datetime


class DeficiencyRecordItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: str
    scrutiny_id: Optional[int] = None
    deficiency_text: str
    status: str
    institution_response: Optional[str] = None
    raised_at: datetime
    resolved_at: Optional[datetime] = None


class DecisionRecordItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    application_id: str
    decision: str
    reasons: str
    conditions: Optional[str] = None
    authority_id: str
    authority_role: str
    decided_at: datetime


class ApplicationResponse(BaseModel):
    """Shared representation of an application matching Dataset 2 fields."""
    model_config = ConfigDict(from_attributes=True)

    application_id: str
    institution_id: str
    application_type: str
    current_stage: str
    application_status: str
    submitted_date: str
    stage_entered_date: str
    due_date: Optional[str] = None
    assigned_role: str
    deficiency_flag: str
    last_updated: str
    data_type: str
    deadline_condition: str
    reference_date: str
    demo_notes: Optional[str] = None
    academic_year: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    programme_name: Optional[str] = None
    intake_approved: Optional[int] = None


class ApplicationDetailResponse(ApplicationResponse):
    """Detailed view including active scrutiny, deficiencies, decision, and history."""
    history: List[WorkflowHistoryItem] = []
    scrutiny_records: List[ScrutinyRecordItem] = []
    deficiency_records: List[DeficiencyRecordItem] = []
    decision_record: Optional[DecisionRecordItem] = None


class ApplicationListResponse(BaseModel):
    items: List[ApplicationResponse]
    total: int
    limit: int
    offset: int


class DashboardSummaryRow(BaseModel):
    """Aggregate row matching Dataset 2 Sheet 3 schema."""
    current_stage: str
    application_status: str
    deadline_condition: str
    record_count: int


class DashboardSummaryResponse(BaseModel):
    """Overall dashboard KPI and matrix breakdown response."""
    total_applications: int
    action_required_count: int
    overdue_count: int
    by_stage: Dict[str, int]
    by_status: Dict[str, int]
    by_deadline_condition: Dict[str, int]
    summary_matrix: List[DashboardSummaryRow]


class TransitionRequest(BaseModel):
    """Payload for invoking a generic workflow transition."""
    action: str = Field(..., description="Action to trigger (e.g. ASSIGN_SCRUTINY, SCRUTINY_PASS)")
    to_stage: Optional[str] = Field(None, description="Optional target stage; derived automatically from rule if omitted")
    remarks: Optional[str] = Field(None, description="Optional transition notes")


class ScrutinySubmitRequest(BaseModel):
    """Payload for submitting a scrutiny evaluation."""
    scrutiny_type: str = Field("INITIAL", description="INITIAL or RE_SCRUTINY")
    outcome: str = Field(..., description="PASSED or DEFICIENT")
    remarks: str = Field(..., min_length=3, description="Evaluator remarks")
    deficiencies: List[str] = Field(default_factory=list, description="List of deficiency notes if DEFICIENT")


class DeficiencyItemResponse(BaseModel):
    deficiency_id: int = Field(..., description="ID of the deficiency record")
    institution_response: str = Field(..., min_length=3, description="Explanation or compliance statement")


class DeficiencyResponseRequest(BaseModel):
    """Payload for Institution Admin resubmitting deficiency clarifications."""
    responses: List[DeficiencyItemResponse]
    remarks: Optional[str] = Field(None, description="General resubmission notes")


class DecisionSubmitRequest(BaseModel):
    """Payload for recording authorized human decision."""
    decision: str = Field(..., description="APPROVED | REJECTED | APPROVED_WITH_CONDITIONS")
    reasons: str = Field(..., min_length=10, description="Mandatory detailed justification")
    conditions: Optional[str] = Field(None, description="Required if decision is APPROVED_WITH_CONDITIONS")
