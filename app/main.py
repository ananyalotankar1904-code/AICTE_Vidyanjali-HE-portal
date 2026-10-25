from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import engine, Base
from app.api.applications import router as applications_router
from app.api.unified_dashboard import router as unified_dashboard_router
import app.models  # ensure Member 3 models are registered

# Import Member 4 compliance gateway components
from app.core.gateway import (
    init_compliance_db,
    compliance_api_router,
    register_compliance_bridges,
    unregister_compliance_bridges,
)

# Create SQLite tables for both engines on startup safely
Base.metadata.create_all(bind=engine)
init_compliance_db()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Register decoupled event bridges on application startup
    register_compliance_bridges()
    yield
    # Clean up on shutdown
    unregister_compliance_bridges()


app = FastAPI(
    title="AICTE Approval & Regulatory Compliance Platform API",
    description="Unified Gateway Prototype (SIH26262 Integration). "
                "Serves Member 3 Workflow Engine alongside Member 4 Regulatory Compliance Engine.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Enable CORS for local dashboards and frontend prototypes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. Mount Unified Dashboard Router (first priority for /api/dashboard/summary)
app.include_router(unified_dashboard_router)

# 2. Mount Member 3 Workflow Engine Router (/api/applications)
app.include_router(
    applications_router,
    prefix="/api/applications",
    tags=["Applications & Workflow"]
)

# 3. Mount Member 4 Compliance Routers (/api/evcs, /api/undertakings, /api/documents, etc.)
app.include_router(compliance_api_router)


@app.get("/", tags=["System"])
def root():
    return {
        "service": "AICTE Approval & Regulatory Compliance Platform",
        "gateway": "Unified Member 3 + Member 4 FastAPI Gateway",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs",
        "health_url": "/health"
    }


@app.get("/health", tags=["System"])
def health_check():
    return {
        "status": "healthy",
        "service": "AICTE Approval & Regulatory Compliance Platform",
        "workflow_engine": "operational",
        "compliance_engine": "operational"
    }

