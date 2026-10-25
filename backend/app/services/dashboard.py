from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from backend.app.models.evc import EVCRecord
from backend.app.models.compliance import ComplianceObligation
from backend.app.models.document import Document
from backend.app.models.deadline import DeadlineRecord
from backend.app.models.notification import Notification
from backend.app.models.audit import AuditEvent
from backend.app.enums import EVCStatus, ObligationStatus, DeadlineStatus
from backend.app.utils.datetime_utils import utc_now, ensure_naive_utc


def get_compliance_dashboard_metrics(
    db: Session,
    reference_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Computes real, persistent database-derived metrics for Member 4 compliance modules.
    No hard-coded values; every metric maps directly to SQL filters.
    """
    ref = ensure_naive_utc(reference_time) or utc_now()
    doc_expiry_threshold = ref + timedelta(days=30)

    # 1. EVC Metrics
    evcs_pending_scheduling = db.query(EVCRecord).filter(
        EVCRecord.status == EVCStatus.PENDING_SCHEDULING
    ).count()

    evcs_scheduled = db.query(EVCRecord).filter(
        EVCRecord.status == EVCStatus.SCHEDULED
    ).count()

    evcs_completed_pending_report = db.query(EVCRecord).filter(
        EVCRecord.status == EVCStatus.VISIT_COMPLETED
    ).count()

    evcs_reports_pending_review = db.query(EVCRecord).filter(
        EVCRecord.status == EVCStatus.REPORT_SUBMITTED
    ).count()

    # 2. Compliance Obligations Metrics
    open_obligations = db.query(ComplianceObligation).filter(
        ComplianceObligation.status.in_([
            ObligationStatus.PENDING,
            ObligationStatus.SUBMITTED,
            ObligationStatus.NEEDS_CORRECTION
        ])
    ).count()

    obligations_awaiting_verification = db.query(ComplianceObligation).filter(
        ComplianceObligation.status == ObligationStatus.SUBMITTED
    ).count()

    obligations_overdue = db.query(ComplianceObligation).filter(
        ComplianceObligation.status != ObligationStatus.VERIFIED,
        ComplianceObligation.due_date.isnot(None),
        ComplianceObligation.due_date < ref
    ).count()

    # 3. Documents & Expiry Metrics (latest version only)
    documents_nearing_expiry = db.query(Document).filter(
        Document.is_latest.is_(True),
        Document.expiry_date.isnot(None),
        Document.expiry_date >= ref,
        Document.expiry_date <= doc_expiry_threshold
    ).count()

    documents_past_expiry = db.query(Document).filter(
        Document.is_latest.is_(True),
        Document.expiry_date.isnot(None),
        Document.expiry_date < ref
    ).count()

    # 4. Deadlines & Escalations
    deadlines_upcoming = db.query(DeadlineRecord).filter(
        DeadlineRecord.status == DeadlineStatus.ACTIVE,
        DeadlineRecord.due_date >= ref
    ).count()

    deadlines_overdue = db.query(DeadlineRecord).filter(
        DeadlineRecord.status.in_([DeadlineStatus.ACTIVE, DeadlineStatus.OVERDUE]),
        DeadlineRecord.due_date < ref
    ).count()

    escalations_generated = db.query(DeadlineRecord).filter(
        DeadlineRecord.escalation_triggered.is_(True)
    ).count()

    # 5. Notifications & Audit
    unread_notifications = db.query(Notification).filter(
        Notification.is_read.is_(False)
    ).count()

    total_audit_events = db.query(AuditEvent).count()

    return {
        "computed_at": ref.isoformat(),
        "evc": {
            "pending_scheduling": evcs_pending_scheduling,
            "scheduled": evcs_scheduled,
            "completed_pending_report": evcs_completed_pending_report,
            "reports_pending_review": evcs_reports_pending_review,
        },
        "compliance": {
            "open_obligations": open_obligations,
            "awaiting_verification": obligations_awaiting_verification,
            "overdue_obligations": obligations_overdue,
        },
        "documents": {
            "nearing_expiry_30_days": documents_nearing_expiry,
            "past_expiry": documents_past_expiry,
        },
        "deadlines": {
            "upcoming_active": deadlines_upcoming,
            "overdue": deadlines_overdue,
            "escalations_generated": escalations_generated,
        },
        "notifications": {
            "unread_count": unread_notifications,
        },
        "audit": {
            "total_events_logged": total_audit_events,
        }
    }
