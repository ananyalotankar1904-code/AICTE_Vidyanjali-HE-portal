import logging
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Callable
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.application import (
    Application,
    WorkflowHistory,
    ScrutinyRecord,
    DeficiencyRecord,
    DecisionRecord,
)

logger = logging.getLogger("aicte.workflow")

# Pluggable listeners for shared audit and notification services
_audit_listeners: List[Callable[[Dict[str, Any]], None]] = []
_notification_listeners: List[Callable[[Dict[str, Any]], None]] = []


def register_audit_listener(callback: Callable[[Dict[str, Any]], None]) -> None:
    """Registers an external audit sink listener (e.g. Member 4 central audit service)."""
    _audit_listeners.append(callback)


def register_notification_listener(callback: Callable[[Dict[str, Any]], None]) -> None:
    """Registers an external notification engine listener (e.g. Member 4 notification service)."""
    _notification_listeners.append(callback)


def clear_service_listeners() -> None:
    """Clears registered listeners (primarily for test cleanup)."""
    _audit_listeners.clear()
    _notification_listeners.clear()


def emit_audit_event(
    event_type: str,
    actor_id: str,
    actor_role: str,
    target_id: str,
    details: Optional[Dict[str, Any]] = None
) -> None:
    """
    Decoupled audit event hook.
    Logs structured event locally and invokes any registered shared audit listeners.
    """
    payload = {
        "event_type": event_type,
        "actor_id": actor_id,
        "actor_role": actor_role,
        "target_id": target_id,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details or {},
    }
    logger.info(f"[SECURITY_AUDIT] {payload}")
    for listener in _audit_listeners:
        try:
            listener(payload)
        except Exception as e:
            logger.error(f"Error invoking audit listener: {e}")


def emit_notification_hook(
    event_type: str,
    application_id: str,
    recipient_role: str,
    message: str
) -> None:
    """
    Decoupled notification event hook.
    Logs alert locally and invokes any registered shared notification listeners.
    """
    payload = {
        "event_type": event_type,
        "application_id": application_id,
        "recipient_role": recipient_role,
        "message": message,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    logger.info(f"[NOTIFICATION_ALERT] {payload}")
    for listener in _notification_listeners:
        try:
            listener(payload)
        except Exception as e:
            logger.error(f"Error invoking notification listener: {e}")


# Permitted Workflow Transition Rules
# Maps (current_stage, action, to_stage) -> rule definition
TRANSITION_RULES: Dict[tuple, Dict[str, Any]] = {
    # 1. From SUBMITTED
    ("SUBMITTED", "ASSIGN_SCRUTINY", "INITIAL_SCRUTINY"): {
        "allowed_roles": ["Intake Officer", "Admin", "Scrutiny Officer"],
        "next_status": "IN_PROGRESS",
        "next_role": "Scrutiny Officer",
        "deficiency_flag": "No",
    },

    # 2. From INITIAL_SCRUTINY
    ("INITIAL_SCRUTINY", "SCRUTINY_PASS", "COMMITTEE_REVIEW"): {
        "allowed_roles": ["Scrutiny Officer", "Admin"],
        "next_status": "IN_PROGRESS",
        "next_role": "Committee Secretariat",
        "deficiency_flag": "No",
    },
    ("INITIAL_SCRUTINY", "SCRUTINY_PASS", "EVC_SCHEDULED"): {
        "allowed_roles": ["Scrutiny Officer", "Admin"],
        "next_status": "IN_PROGRESS",
        "next_role": "EVC Coordinator",
        "deficiency_flag": "No",
    },
    ("INITIAL_SCRUTINY", "SCRUTINY_DEFICIENT", "DEFICIENCY_RAISED"): {
        "allowed_roles": ["Scrutiny Officer", "Admin"],
        "next_status": "ACTION_REQUIRED",
        "next_role": "Institution Admin",
        "deficiency_flag": "Yes",
    },

    # 3. From DEFICIENCY_RAISED (Resubmission loop)
    ("DEFICIENCY_RAISED", "SUBMIT_RESPONSE", "RE_SCRUTINY"): {
        "allowed_roles": ["Institution Admin", "Admin"],
        "next_status": "IN_PROGRESS",
        "next_role": "Scrutiny Officer",
        "deficiency_flag": "Yes",
    },

    # 4. From RE_SCRUTINY
    ("RE_SCRUTINY", "RE_SCRUTINY_PASS", "COMMITTEE_REVIEW"): {
        "allowed_roles": ["Scrutiny Officer", "Admin"],
        "next_status": "IN_PROGRESS",
        "next_role": "Committee Secretariat",
        "deficiency_flag": "No",
    },
    ("RE_SCRUTINY", "RE_SCRUTINY_PASS", "EVC_SCHEDULED"): {
        "allowed_roles": ["Scrutiny Officer", "Admin"],
        "next_status": "IN_PROGRESS",
        "next_role": "EVC Coordinator",
        "deficiency_flag": "No",
    },
    ("RE_SCRUTINY", "RE_SCRUTINY_FAIL", "COMMITTEE_REVIEW"): {
        "allowed_roles": ["Scrutiny Officer", "Admin"],
        "next_status": "IN_PROGRESS",
        "next_role": "Committee Secretariat",
        "deficiency_flag": "Yes",
    },

    # 5. From EVC_SCHEDULED
    ("EVC_SCHEDULED", "COMPLETE_EVC", "EVC_COMPLETED"): {
        "allowed_roles": ["EVC Coordinator", "Admin"],
        "next_status": "IN_PROGRESS",
        "next_role": "EVC Coordinator",
        "deficiency_flag": "No",
    },

    # 6. From EVC_COMPLETED
    ("EVC_COMPLETED", "SUBMIT_TO_COMMITTEE", "COMMITTEE_REVIEW"): {
        "allowed_roles": ["EVC Coordinator", "Admin", "Committee Secretariat"],
        "next_status": "IN_PROGRESS",
        "next_role": "Committee Secretariat",
        "deficiency_flag": "No",
    },

    # 7. From COMMITTEE_REVIEW
    ("COMMITTEE_REVIEW", "SUBMIT_TO_AUTHORITY", "DECISION_PENDING"): {
        "allowed_roles": ["Committee Secretariat", "Admin"],
        "next_status": "IN_PROGRESS",
        "next_role": "Competent Authority Secretariat",
        "deficiency_flag": "No",
    },

    # 8. From DECISION_PENDING
    ("DECISION_PENDING", "RECORD_DECISION", "COMPLETED"): {
        "allowed_roles": ["Competent Authority Secretariat", "Admin"],
        "next_status": "COMPLETED",
        "next_role": "Records Officer",
        "deficiency_flag": "No",
    },
}


class WorkflowService:
    """
    Centralized Workflow Service.
    Enforces current-stage validation, transition rule matrix, role authorization,
    prerequisite verification, atomic database commits, and audit/notification hooks.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_application_or_404(self, application_id: str) -> Application:
        """Retrieves an application by ID or raises 404."""
        app = self.db.query(Application).filter(Application.application_id == application_id).first()
        if not app:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Application '{application_id}' not found."
            )
        return app

    def derive_destination_stage(self, application: Application, action: str, requested_to_stage: Optional[str] = None) -> str:
        """
        Derives the destination stage based on application stage, action, and application type.
        If the caller requested a destination stage, validates that it matches the permitted rule.
        """
        current_stage = application.current_stage

        # Find matching rules from current stage with action
        matching_rules = [
            (stg, act, to_stg)
            for (stg, act, to_stg) in TRANSITION_RULES.keys()
            if stg == current_stage and act == action
        ]

        if not matching_rules:
            permitted = [act for (stg, act, _) in TRANSITION_RULES.keys() if stg == current_stage]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_WORKFLOW_TRANSITION",
                    "message": (
                        f"Action '{action}' is not permitted from current stage '{current_stage}'."
                    ),
                    "current_stage": current_stage,
                    "permitted_actions": list(set(permitted)),
                }
            )

        # If multiple targets exist (e.g. SCRUTINY_PASS -> EVC_SCHEDULED vs COMMITTEE_REVIEW)
        if len(matching_rules) > 1:
            if requested_to_stage:
                target = requested_to_stage
            elif application.application_type in ["New Programme", "Increase in Intake"]:
                target = "EVC_SCHEDULED"
            else:
                target = "COMMITTEE_REVIEW"
        else:
            target = matching_rules[0][2]

        # Verify that (current_stage, action, target) exists in rules
        if (current_stage, action, target) not in TRANSITION_RULES:
            allowed_targets = [r[2] for r in matching_rules]
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_WORKFLOW_TRANSITION",
                    "message": (
                        f"Destination stage '{target}' is not permitted for action '{action}' "
                        f"from stage '{current_stage}'. Permitted targets: {allowed_targets}"
                    ),
                    "current_stage": current_stage,
                    "permitted_target_stages": allowed_targets,
                }
            )

        return target

    def validate_transition_permissions(
        self,
        application: Application,
        action: str,
        to_stage: str,
        actor_role: str
    ) -> Dict[str, Any]:
        """Validates that the acting user has permission to trigger the transition."""
        key = (application.current_stage, action, to_stage)
        if key not in TRANSITION_RULES:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error_code": "INVALID_WORKFLOW_TRANSITION",
                    "message": f"Transition '{action}' -> '{to_stage}' is not permitted from '{application.current_stage}'.",
                    "current_stage": application.current_stage
                }
            )

        rule = TRANSITION_RULES[key]
        if actor_role not in rule["allowed_roles"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error_code": "UNAUTHORIZED_WORKFLOW_ACTION",
                    "message": (
                        f"User role '{actor_role}' is not authorized to execute '{action}' "
                        f"from stage '{application.current_stage}'."
                    ),
                    "required_roles": rule["allowed_roles"],
                }
            )
        return rule

    def validate_prerequisites(
        self,
        application: Application,
        action: str,
        **context
    ) -> None:
        """
        Validates agreed prerequisites using existing application data and models.
        Rejects transition if prerequisites are not satisfied.
        """
        if action == "SUBMIT_RESPONSE":
            # Prerequisite: All open deficiency records must have non-empty responses
            open_defs = self.db.query(DeficiencyRecord).filter(
                DeficiencyRecord.application_id == application.application_id,
                DeficiencyRecord.status != "RESOLVED"
            ).all()

            if not open_defs:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "MISSING_PREREQUISITE",
                        "message": "No open deficiencies exist for this application to resubmit."
                    }
                )

            unresponded = [d for d in open_defs if not d.institution_response or d.status == "OPEN"]
            if unresponded:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "MISSING_PREREQUISITE",
                        "message": f"All open deficiencies must be addressed before resubmission. {len(unresponded)} deficiency item(s) remain unaddressed.",
                        "unaddressed_count": len(unresponded)
                    }
                )

        elif action == "RECORD_DECISION":
            decision = context.get("decision")
            reasons = context.get("reasons")
            conditions = context.get("conditions")

            if not decision or decision not in ["APPROVED", "REJECTED", "APPROVED_WITH_CONDITIONS"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "MISSING_PREREQUISITE",
                        "message": "Valid decision ('APPROVED', 'REJECTED', 'APPROVED_WITH_CONDITIONS') is required."
                    }
                )
            if not reasons or len(reasons.strip()) < 10:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "MISSING_PREREQUISITE",
                        "message": "Mandatory statutory reasons (minimum 10 characters) must be recorded."
                    }
                )
            if decision == "APPROVED_WITH_CONDITIONS" and (not conditions or not conditions.strip()):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "MISSING_PREREQUISITE",
                        "message": "Compliance conditions must be specified for conditional approval."
                    }
                )

        elif action == "SCRUTINY_DEFICIENT":
            deficiencies = context.get("deficiencies")
            if deficiencies is not None:
                if not deficiencies:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error_code": "MISSING_PREREQUISITE",
                            "message": "At least one deficiency item must be provided when outcome is DEFICIENT."
                        }
                    )
            else:
                open_defs = self.db.query(DeficiencyRecord).filter(
                    DeficiencyRecord.application_id == application.application_id
                ).all()
                if not open_defs:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail={
                            "error_code": "MISSING_PREREQUISITE",
                            "message": "At least one deficiency item must be provided when outcome is DEFICIENT."
                        }
                    )

    def execute_transition(
        self,
        application_id: str,
        action: str,
        actor_id: str,
        actor_role: str,
        to_stage: Optional[str] = None,
        remarks: Optional[str] = None,
        **context
    ) -> Application:
        """
        Executes a transition atomically with rollback on any failure.
        """
        app = self.get_application_or_404(application_id)

        # 1. Derive destination stage
        derived_to_stage = self.derive_destination_stage(app, action, to_stage)

        # 2. Validate role & permissions
        rule = self.validate_transition_permissions(app, action, derived_to_stage, actor_role)

        # 3. Validate prerequisites
        self.validate_prerequisites(app, action, **context)

        # 4. Perform atomic update
        from_stage = app.current_stage
        from_status = app.application_status
        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")

        try:
            # Update application
            app.current_stage = derived_to_stage
            app.application_status = rule["next_status"]
            app.assigned_role = rule["next_role"]
            if "deficiency_flag" in rule:
                app.deficiency_flag = rule["deficiency_flag"]
            app.stage_entered_date = today_str
            app.last_updated = today_str

            if derived_to_stage == "COMPLETED":
                app.deadline_condition = "COMPLETED"

            # Create history record
            history_entry = WorkflowHistory(
                application_id=app.application_id,
                from_stage=from_stage,
                to_stage=derived_to_stage,
                from_status=from_status,
                to_status=rule["next_status"],
                action=action,
                actor_id=actor_id,
                actor_role=actor_role,
                timestamp=datetime.now(timezone.utc),
                remarks=remarks,
            )
            self.db.add(history_entry)

            # Commit transaction atomically
            self.db.commit()
            self.db.refresh(app)

            # 5. Emit shared integration hooks
            emit_audit_event(
                event_type="WORKFLOW_TRANSITION",
                actor_id=actor_id,
                actor_role=actor_role,
                target_id=app.application_id,
                details={
                    "from_stage": from_stage,
                    "to_stage": derived_to_stage,
                    "action": action,
                    "remarks": remarks
                }
            )

            emit_notification_hook(
                event_type="STAGE_CHANGED",
                application_id=app.application_id,
                recipient_role=rule["next_role"],
                message=f"Application {app.application_id} transitioned to {derived_to_stage} ({rule['next_status']})"
            )

            return app

        except Exception as e:
            self.db.rollback()
            if isinstance(e, HTTPException):
                raise e
            logger.error(f"Transaction failed during transition: {e}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Database transaction failed during workflow transition: {str(e)}"
            )

    def record_scrutiny(
        self,
        application_id: str,
        scrutiny_type: str,
        outcome: str,
        remarks: str,
        deficiencies: List[str],
        actor_id: str,
        actor_role: str,
    ) -> Application:
        """
        Records scrutiny outcome, maintains history, manages open deficiencies,
        and transitions the application. Preserves previous scrutiny records.
        """
        app = self.get_application_or_404(application_id)

        # Validate stage
        if app.current_stage not in ["INITIAL_SCRUTINY", "RE_SCRUTINY"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Application is in '{app.current_stage}'. Scrutiny can only be performed in 'INITIAL_SCRUTINY' or 'RE_SCRUTINY'."
            )

        # Role permission check
        if actor_role not in ["Scrutiny Officer", "Admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role '{actor_role}'. Action requires 'Scrutiny Officer' or 'Admin'."
            )

        stype = scrutiny_type.upper()
        soutcome = outcome.upper()

        if soutcome not in ["PASSED", "DEFICIENT"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid outcome. Must be 'PASSED' or 'DEFICIENT'."
            )

        if soutcome == "DEFICIENT":
            if not deficiencies:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "error_code": "MISSING_PREREQUISITE",
                        "message": "At least one deficiency item must be provided when outcome is DEFICIENT."
                    }
                )

            # Create Scrutiny Record (preserves previous records)
            scrutiny = ScrutinyRecord(
                application_id=app.application_id,
                scrutiny_type=stype,
                outcome="DEFICIENT",
                remarks=remarks,
                deficiency_summary="; ".join(deficiencies),
                scrutinizer_id=actor_id,
                scrutinizer_role=actor_role,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(scrutiny)
            self.db.flush()

            # Create individual deficiency records
            for text in deficiencies:
                def_record = DeficiencyRecord(
                    application_id=app.application_id,
                    scrutiny_id=scrutiny.id,
                    deficiency_text=text,
                    status="OPEN",
                    raised_at=datetime.now(timezone.utc),
                )
                self.db.add(def_record)
            self.db.flush()

            # Transition application
            if app.current_stage == "INITIAL_SCRUTINY":
                res = self.execute_transition(
                    application_id=app.application_id,
                    action="SCRUTINY_DEFICIENT",
                    actor_id=actor_id,
                    actor_role=actor_role,
                    remarks=f"Deficiencies recorded: {remarks}",
                    deficiencies=deficiencies
                )
                emit_notification_hook(
                    event_type="DEFICIENCY_RAISED",
                    application_id=app.application_id,
                    recipient_role="Institution Admin",
                    message=f"Deficiencies raised for application {app.application_id}: {remarks}"
                )
                return res
            else:
                res = self.execute_transition(
                    application_id=app.application_id,
                    action="RE_SCRUTINY_FAIL",
                    actor_id=actor_id,
                    actor_role=actor_role,
                    remarks=f"Re-scrutiny failed. Escalated with deficiencies: {remarks}",
                )
                emit_notification_hook(
                    event_type="DEFICIENCY_RAISED",
                    application_id=app.application_id,
                    recipient_role="Institution Admin",
                    message=f"Re-scrutiny deficiencies recorded for application {app.application_id}: {remarks}"
                )
                return res

        else:  # PASSED
            # If in RE_SCRUTINY, mark open/responded deficiencies as RESOLVED
            if app.current_stage == "RE_SCRUTINY":
                open_defs = self.db.query(DeficiencyRecord).filter(
                    DeficiencyRecord.application_id == app.application_id,
                    DeficiencyRecord.status != "RESOLVED"
                ).all()
                for od in open_defs:
                    od.status = "RESOLVED"
                    od.resolved_at = datetime.now(timezone.utc)
                self.db.flush()

            # Create Scrutiny Record (preserves previous records)
            scrutiny = ScrutinyRecord(
                application_id=app.application_id,
                scrutiny_type=stype,
                outcome="PASSED",
                remarks=remarks,
                deficiency_summary=None,
                scrutinizer_id=actor_id,
                scrutinizer_role=actor_role,
                created_at=datetime.now(timezone.utc),
            )
            self.db.add(scrutiny)
            self.db.flush()

            action = "SCRUTINY_PASS" if app.current_stage == "INITIAL_SCRUTINY" else "RE_SCRUTINY_PASS"
            return self.execute_transition(
                application_id=app.application_id,
                action=action,
                actor_id=actor_id,
                actor_role=actor_role,
                remarks=f"Scrutiny passed: {remarks}",
            )

    def record_deficiency_responses(
        self,
        application_id: str,
        responses: List[Any],
        actor_id: str,
        actor_role: str,
        remarks: Optional[str] = None
    ) -> Application:
        """
        Records institution responses to deficiencies and transitions to RE_SCRUTINY.
        """
        app = self.get_application_or_404(application_id)

        if app.current_stage != "DEFICIENCY_RAISED":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Application is in stage '{app.current_stage}'. Deficiencies can only be answered in 'DEFICIENCY_RAISED'."
            )

        if actor_role not in ["Institution Admin", "Admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role '{actor_role}'. Action requires 'Institution Admin' or 'Admin'."
            )

        # Update deficiency records
        for item in responses:
            def_id = item.deficiency_id if hasattr(item, "deficiency_id") else item["deficiency_id"]
            resp_text = item.institution_response if hasattr(item, "institution_response") else item["institution_response"]

            d_record = self.db.query(DeficiencyRecord).filter(
                DeficiencyRecord.id == def_id,
                DeficiencyRecord.application_id == application_id
            ).first()
            if d_record:
                d_record.institution_response = resp_text
                d_record.status = "RESPONDED"
        self.db.flush()

        # Execute transition to RE_SCRUTINY
        return self.execute_transition(
            application_id=application_id,
            action="SUBMIT_RESPONSE",
            actor_id=actor_id,
            actor_role=actor_role,
            remarks=remarks or "Institution resubmitted compliance response.",
        )

    def record_official_decision(
        self,
        application_id: str,
        decision: str,
        reasons: str,
        conditions: Optional[str],
        actor_id: str,
        actor_role: str
    ) -> Application:
        """
        Records authorized human decision by Competent Authority and transitions to COMPLETED.
        """
        app = self.get_application_or_404(application_id)

        if app.current_stage != "DECISION_PENDING":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Application is in stage '{app.current_stage}'. Official decision can only be recorded in 'DECISION_PENDING'."
            )

        if actor_role not in ["Competent Authority Secretariat", "Admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access denied for role '{actor_role}'. Action requires 'Competent Authority Secretariat' or 'Admin'."
            )

        d_val = decision.upper()

        # Validate prerequisites
        self.validate_prerequisites(
            application=app,
            action="RECORD_DECISION",
            decision=d_val,
            reasons=reasons,
            conditions=conditions
        )

        # Create or update DecisionRecord
        existing_rec = self.db.query(DecisionRecord).filter(DecisionRecord.application_id == app.application_id).first()
        if existing_rec:
            existing_rec.decision = d_val
            existing_rec.reasons = reasons
            existing_rec.conditions = conditions
            existing_rec.authority_id = actor_id
            existing_rec.authority_role = actor_role
            existing_rec.decided_at = datetime.now(timezone.utc)
        else:
            decision_rec = DecisionRecord(
                application_id=app.application_id,
                decision=d_val,
                reasons=reasons,
                conditions=conditions,
                authority_id=actor_id,
                authority_role=actor_role,
                decided_at=datetime.now(timezone.utc),
            )
            self.db.add(decision_rec)
        self.db.flush()

        # Execute transition to COMPLETED
        res = self.execute_transition(
            application_id=application_id,
            action="RECORD_DECISION",
            actor_id=actor_id,
            actor_role=actor_role,
            remarks=f"Final Decision: {d_val}. Reasons: {reasons}",
            decision=d_val,
            reasons=reasons,
            conditions=conditions
        )
        emit_notification_hook(
            event_type="DECISION_RECORDED",
            application_id=application_id,
            recipient_role="Institution Admin",
            message=f"Official decision '{d_val}' recorded for application {application_id}."
        )
        return res

    def get_scrutiny_records(self, application_id: str) -> List[ScrutinyRecord]:
        self.get_application_or_404(application_id)
        return self.db.query(ScrutinyRecord).filter(
            ScrutinyRecord.application_id == application_id
        ).order_by(ScrutinyRecord.id.asc()).all()

    def get_deficiency_records(self, application_id: str, status_filter: Optional[str] = None) -> List[DeficiencyRecord]:
        self.get_application_or_404(application_id)
        query = self.db.query(DeficiencyRecord).filter(
            DeficiencyRecord.application_id == application_id
        )
        if status_filter:
            query = query.filter(DeficiencyRecord.status == status_filter)
        return query.order_by(DeficiencyRecord.id.asc()).all()

    def get_decision_record(self, application_id: str) -> DecisionRecord:
        self.get_application_or_404(application_id)
        rec = self.db.query(DecisionRecord).filter(
            DecisionRecord.application_id == application_id
        ).first()
        if not rec:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"No official decision has been recorded yet for application '{application_id}'."
            )
        return rec


# Backward-compatible functional wrappers
def validate_transition(application: Application, action: str, to_stage: str, actor_role: str) -> Dict[str, Any]:
    key = (application.current_stage, action, to_stage)
    if key not in TRANSITION_RULES:
        permitted = [act for (stg, act, _) in TRANSITION_RULES.keys() if stg == application.current_stage]
        allowed_targets = [to for (stg, act, to) in TRANSITION_RULES.keys() if stg == application.current_stage and act == action]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error_code": "INVALID_WORKFLOW_TRANSITION",
                "message": f"Transition '{action}' to stage '{to_stage}' is not permitted from '{application.current_stage}'.",
                "current_stage": application.current_stage,
                "permitted_actions": list(set(permitted)),
                "permitted_target_stages": allowed_targets,
            }
        )
    rule = TRANSITION_RULES[key]
    if actor_role not in rule["allowed_roles"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error_code": "UNAUTHORIZED_WORKFLOW_ACTION",
                "message": f"User role '{actor_role}' is not authorized to execute '{action}' from '{application.current_stage}'.",
                "required_roles": rule["allowed_roles"],
            }
        )
    return rule


def execute_workflow_transition(
    db: Session,
    application: Application,
    action: str,
    to_stage: str,
    actor_id: str,
    actor_role: str,
    remarks: Optional[str] = None
) -> Application:
    service = WorkflowService(db)
    return service.execute_transition(
        application_id=application.application_id,
        action=action,
        actor_id=actor_id,
        actor_role=actor_role,
        to_stage=to_stage,
        remarks=remarks,
    )
