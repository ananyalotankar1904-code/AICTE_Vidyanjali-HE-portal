from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, ConfigDict
from backend.app.enums import DeadlineStatus


class DeadlineCreateRequest(BaseModel):
    entity_type: str
    entity_id: str
    deadline_type: str
    title: str
    due_date: datetime
    owner_role: str
    owner_id: Optional[str] = None
    source_reference: Optional[str] = "Illustrative Demo Policy"
    is_statutory: bool = False
    warning_threshold_hours: int = 48
    escalation_policy: Optional[str] = "NOTIFY_REGIONAL_OFFICER_ON_OVERDUE"


class DeadlineEvaluateRequest(BaseModel):
    reference_time: Optional[datetime] = None  # If null, uses utc_now()


class DeadlineEvaluationSummary(BaseModel):
    evaluated_at: datetime
    reference_time: datetime
    total_active_evaluated: int
    upcoming_warnings_issued: int
    overdue_escalations_issued: int
    deadlines_marked_overdue: int


class DeadlineResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    deadline_type: str
    title: str
    due_date: datetime
    owner_role: str
    owner_id: Optional[str] = None
    source_reference: str
    is_statutory: bool
    status: DeadlineStatus
    warning_threshold_hours: int
    last_evaluated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    escalation_policy: str
    escalation_triggered: bool
    escalation_history: List[Dict[str, Any]] = []
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
