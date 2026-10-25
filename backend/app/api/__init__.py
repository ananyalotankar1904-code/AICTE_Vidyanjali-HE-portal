from fastapi import APIRouter
from backend.app.api.evc import router as evc_router
from backend.app.api.compliance import router as compliance_router
from backend.app.api.documents import router as documents_router
from backend.app.api.deadlines import router as deadlines_router
from backend.app.api.notifications import router as notifications_router
from backend.app.api.dashboard import router as dashboard_router, compliance_dashboard_router
from backend.app.api.audit import router as audit_router

# 1. Full API router for Member 4 standalone application (includes standalone /summary)
api_router = APIRouter(prefix="/api")
api_router.include_router(evc_router)
api_router.include_router(compliance_router)
api_router.include_router(documents_router)
api_router.include_router(deadlines_router)
api_router.include_router(notifications_router)
api_router.include_router(dashboard_router)
api_router.include_router(audit_router)

# 2. Compliance API router for Unified Gateway mount (contains /compliance-summary but NO duplicate /summary)
gateway_compliance_router = APIRouter(prefix="/api")
gateway_compliance_router.include_router(evc_router)
gateway_compliance_router.include_router(compliance_router)
gateway_compliance_router.include_router(documents_router)
gateway_compliance_router.include_router(deadlines_router)
gateway_compliance_router.include_router(notifications_router)
gateway_compliance_router.include_router(compliance_dashboard_router)
gateway_compliance_router.include_router(audit_router)
