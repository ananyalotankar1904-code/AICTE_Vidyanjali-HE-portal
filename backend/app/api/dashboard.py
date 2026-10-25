from typing import Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.application import Application
from app.services.dashboard import get_compliance_dashboard_metrics
from app.utils.datetime_utils import utc_now

router = APIRouter(prefix="/dashboard", tags=["Dashboard & Metrics"])


@router.get("/compliance-summary", response_model=Dict[str, Any])
def get_compliance_summary(
    reference_time: Optional[datetime] = Query(None, description="Optional reference time for deadline and expiry evaluation"),
    db: Session = Depends(get_db)
):
    """
    Returns live aggregated metrics for EVCs, undertakings, document renewals,
    deadlines, notifications, and audit volume.
    """
    return get_compliance_dashboard_metrics(db=db, reference_time=reference_time)


@router.get("/summary", response_model=Dict[str, Any])
def get_unified_dashboard_summary(
    reference_time: Optional[datetime] = Query(None, description="Optional reference time"),
    db: Session = Depends(get_db)
):
    """
    Shared dashboard endpoint incorporating overall application counts alongside compliance metrics.
    Coordinated with Member 3 and Member 5 standards.
    """
    total_apps = db.query(Application).count()
    compliance_metrics = get_compliance_dashboard_metrics(db=db, reference_time=reference_time)
    
    return {
        "total_applications": total_apps,
        "compliance_summary": compliance_metrics,
        "status": "operational",
        "timestamp": utc_now().isoformat()
    }
