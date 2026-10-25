import logging
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

logger = logging.getLogger("aicte.dashboard")

from app.database import get_db as get_m3_db
from app.models.application import Application as M3Application
from app.core.gateway import get_compliance_db
from backend.app.services.dashboard import get_compliance_dashboard_metrics

router = APIRouter(prefix="/api/dashboard", tags=["Unified Dashboard & Metrics"])

# Map Member 3 stages to the 6 high-level Frontend WorkflowStages
STAGE_MAPPING = {
    "SUBMITTED": "Submitted",
    "INITIAL_SCRUTINY": "Scrutiny",
    "DEFICIENCY_RAISED": "Scrutiny",
    "RE_SCRUTINY": "Re-scrutiny",
    "EVC_SCHEDULED": "EVC",
    "EVC_COMPLETED": "EVC",
    "COMMITTEE_REVIEW": "Executive Decision",
    "DECISION_PENDING": "Executive Decision",
    "COMPLETED": "Appeal/Post-approval",
}

FRONTEND_STAGES = [
    "Submitted",
    "Scrutiny",
    "Re-scrutiny",
    "EVC",
    "Executive Decision",
    "Appeal/Post-approval",
]


def _compute_age_days(submitted_date_str: str) -> int:
    try:
        dt = datetime.strptime(submitted_date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        return max(0, (now - dt).days)
    except Exception:
        return 0


@router.get("/summary", response_model=Dict[str, Any])
def get_unified_dashboard_summary(
    reference_time: Optional[datetime] = Query(None, description="Optional reference time for deterministic deadline checks"),
    m3_db: Session = Depends(get_m3_db),
    m4_db: Session = Depends(get_compliance_db),
) -> Dict[str, Any]:
    """
    Unified Dashboard Endpoint (SIH26262 Integration).
    Aggregates live workflow pipeline data from Member 3 (aicte_platform.db)
    alongside live regulatory compliance & EVC metrics from Member 4 (aicte.db).
    """
    # 1. Fetch all workflow applications from Member 3
    apps = m3_db.query(M3Application).all()
    total_applications = len(apps)

    # 2. Compute Member 3 pipeline breakdowns
    pending_scrutiny = sum(1 for a in apps if a.current_stage == "INITIAL_SCRUTINY")
    deficiency_cases = sum(1 for a in apps if a.deficiency_flag == "Yes")
    overdue_apps = sum(1 for a in apps if a.deadline_condition == "OVERDUE")
    action_required_apps = sum(1 for a in apps if a.application_status == "ACTION_REQUIRED")

    by_stage: Dict[str, int] = {}
    by_status: Dict[str, int] = {}
    by_deadline_condition: Dict[str, int] = {}

    for a in apps:
        by_stage[a.current_stage] = by_stage.get(a.current_stage, 0) + 1
        by_status[a.application_status] = by_status.get(a.application_status, 0) + 1
        by_deadline_condition[a.deadline_condition] = by_deadline_condition.get(a.deadline_condition, 0) + 1

    # Stage distribution for frontend UI chart
    stage_counts = {stg: 0 for stg in FRONTEND_STAGES}
    for a in apps:
        ui_stg = STAGE_MAPPING.get(a.current_stage, "Submitted")
        stage_counts[ui_stg] = stage_counts.get(ui_stg, 0) + 1

    stage_distribution = [{"stage": stg, "count": stage_counts[stg]} for stg in FRONTEND_STAGES]

    # Ageing buckets
    age_0_15 = sum(1 for a in apps if _compute_age_days(a.submitted_date) <= 15)
    age_16_30 = sum(1 for a in apps if 15 < _compute_age_days(a.submitted_date) <= 30)
    age_31_45 = sum(1 for a in apps if 30 < _compute_age_days(a.submitted_date) <= 45)
    age_46_60 = sum(1 for a in apps if 45 < _compute_age_days(a.submitted_date) <= 60)
    age_60_plus = sum(1 for a in apps if _compute_age_days(a.submitted_date) > 60)

    ageing_buckets = [
        {"bucket": "0–15 days", "count": age_0_15},
        {"bucket": "16–30 days", "count": age_16_30},
        {"bucket": "31–45 days", "count": age_31_45},
        {"bucket": "46–60 days", "count": age_46_60},
        {"bucket": "60+ days", "count": age_60_plus},
    ]

    # 3. Fetch live compliance metrics from Member 4 with graceful degradation
    compliance_available = True
    compliance_metrics = None
    compliance_error = None

    try:
        compliance_metrics = get_compliance_dashboard_metrics(db=m4_db, reference_time=reference_time)
    except Exception as exc:
        compliance_available = False
        compliance_error = "Compliance metrics subsystem temporarily unavailable"
        logger.error(f"[UNIFIED_DASHBOARD_COMPLIANCE_ERROR] Failed to query compliance metrics: {str(exc)}", exc_info=True)

    if compliance_available and compliance_metrics:
        evc_data = compliance_metrics.get("evc", {})
        doc_data = compliance_metrics.get("documents", {})
        ddl_data = compliance_metrics.get("deadlines", {})

        evcs_scheduled = evc_data.get("scheduled", 0)
        expiring_docs = (
            doc_data.get("nearing_expiry_30_days", 0)
            + doc_data.get("past_expiry", 0)
        )
        upcoming_deadlines = (
            ddl_data.get("upcoming_active", 0)
            + ddl_data.get("overdue", 0)
        )
        status_label = "operational"
        subsystem_status = {
            "workflow_engine": "operational",
            "compliance_engine": "operational",
        }
    else:
        # Graceful degradation: do NOT report genuine zeroes for unmeasured compliance
        evcs_scheduled = None
        expiring_docs = None
        upcoming_deadlines = None
        compliance_metrics = {
            "status": "unavailable",
            "message": compliance_error or "Service unavailable",
        }
        status_label = "degraded"
        subsystem_status = {
            "workflow_engine": "operational",
            "compliance_engine": "unavailable",
        }

    # 4. Construct unified dual-contract response (compatible with frontend & backend schemas)
    return {
        # CamelCase contract for Frontend React (src/types/index.ts)
        "totalApplications": total_applications,
        "pendingScrutiny": pending_scrutiny,
        "deficiencyCases": deficiency_cases,
        "evcsScheduled": evcs_scheduled,
        "expiringDocuments": expiring_docs,
        "upcomingDeadlines": upcoming_deadlines,
        "stageDistribution": stage_distribution,
        "ageingBuckets": ageing_buckets,
        # Snake_case contract for Backend API & Dataset 2 Sheet 3
        "total_applications": total_applications,
        "action_required_count": action_required_apps,
        "overdue_count": overdue_apps,
        "by_stage": by_stage,
        "by_status": by_status,
        "by_deadline_condition": by_deadline_condition,
        "compliance_summary": compliance_metrics,
        "status": status_label,
        "subsystem_status": subsystem_status,
        "degraded": not compliance_available,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
