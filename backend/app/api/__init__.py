from fastapi import APIRouter
from app.api.evc import router as evc_router
from app.api.compliance import router as compliance_router
from app.api.documents import router as documents_router
from app.api.deadlines import router as deadlines_router
from app.api.notifications import router as notifications_router
from app.api.dashboard import router as dashboard_router
from app.api.audit import router as audit_router

api_router = APIRouter(prefix="/api")

api_router.include_router(evc_router)
api_router.include_router(compliance_router)
api_router.include_router(documents_router)
api_router.include_router(deadlines_router)
api_router.include_router(notifications_router)
api_router.include_router(dashboard_router)
api_router.include_router(audit_router)
