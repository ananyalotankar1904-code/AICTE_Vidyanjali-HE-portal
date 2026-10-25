from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.audit import AuditEvent


class AuditLogResponse(BaseModel):
    id: str
    actor_id: str
    actor_role: str
    action: str
    entity_type: str
    entity_id: str
    timestamp: datetime
    before_state: Optional[dict] = None
    after_state: Optional[dict] = None
    reason: Optional[str] = None
    details: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


router = APIRouter(prefix="/audit-logs", tags=["Audit History"])


@router.get("", response_model=List[AuditLogResponse])
def get_audit_logs(
    entity_type: Optional[str] = Query(None, description="Filter by entity type (EVC, UNDERTAKING, DOCUMENT, DEADLINE)"),
    entity_id: Optional[str] = Query(None, description="Filter by entity ID"),
    actor_id: Optional[str] = Query(None, description="Filter by actor ID"),
    action: Optional[str] = Query(None, description="Filter by action name"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Retrieves immutable audit trail events.
    Audit entries cannot be created, modified, or deleted through application endpoints.
    """
    query = db.query(AuditEvent)
    if entity_type:
        query = query.filter(AuditEvent.entity_type == entity_type)
    if entity_id:
        query = query.filter(AuditEvent.entity_id == entity_id)
    if actor_id:
        query = query.filter(AuditEvent.actor_id == actor_id)
    if action:
        query = query.filter(AuditEvent.action == action)
    return query.order_by(AuditEvent.timestamp.desc()).offset(skip).limit(limit).all()
