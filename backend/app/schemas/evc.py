from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from backend.app.enums import EVCStatus, EVCRecommendation, EVCReportReviewOutcome


class EVCCreateRequest(BaseModel):
    application_id: str
    assigned_team_id: Optional[str] = None
    assigned_members: Optional[List[str]] = None
    venue_address: Optional[str] = None
    scheduling_notes: Optional[str] = None


class EVCScheduleRequest(BaseModel):
    planned_visit_date: datetime
    venue_address: Optional[str] = None
    assigned_team_id: Optional[str] = None
    assigned_members: Optional[List[str]] = None
    notes: Optional[str] = None


class EVCRescheduleRequest(BaseModel):
    new_planned_visit_date: datetime
    reason: str
    notes: Optional[str] = None


class EVCCompleteVisitRequest(BaseModel):
    actual_visit_date: datetime
    visit_notes: Optional[str] = None


class EVCSubmitReportRequest(BaseModel):
    findings_summary: str
    recommendation: EVCRecommendation
    report_document_id: Optional[str] = None


class EVCReviewReportRequest(BaseModel):
    outcome: EVCReportReviewOutcome
    review_notes: Optional[str] = None


class EVCUpdateRequest(BaseModel):
    assigned_team_id: Optional[str] = None
    assigned_members: Optional[List[str]] = None
    venue_address: Optional[str] = None
    scheduling_notes: Optional[str] = None


class EVCResponse(BaseModel):
    id: str
    application_id: str
    status: EVCStatus
    assigned_team_id: Optional[str] = None
    assigned_members: Optional[List[str]] = None
    planned_visit_date: Optional[datetime] = None
    actual_visit_date: Optional[datetime] = None
    venue_address: Optional[str] = None
    scheduling_notes: Optional[str] = None
    reschedule_history: List[Dict[str, Any]] = []
    visit_notes: Optional[str] = None
    findings_summary: Optional[str] = None
    recommendation: Optional[EVCRecommendation] = None
    report_document_id: Optional[str] = None
    report_submitted_at: Optional[datetime] = None
    report_submitted_by: Optional[str] = None
    report_reviewed_at: Optional[datetime] = None
    report_reviewed_by: Optional[str] = None
    report_review_outcome: Optional[EVCReportReviewOutcome] = None
    report_review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
