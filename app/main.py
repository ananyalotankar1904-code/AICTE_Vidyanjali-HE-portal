from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.api.applications import router as applications_router
import app.models  # ensure models are registered

# Create SQLite tables on startup
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="AICTE Approval & Compliance Platform API",
    description="Backend Workflow & Application Management Prototype (Member 3)",
    version="1.0.0",
)

# Enable CORS for local dashboards and frontend prototypes
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Member 3 Router
app.include_router(
    applications_router,
    prefix="/api/applications",
    tags=["Applications & Workflow"]
)


@app.get("/", tags=["System"])
def root():
    return {
        "service": "AICTE Approval & Compliance Platform",
        "module": "Member 3 - Backend Workflow Engine",
        "version": "1.0.0",
        "status": "online",
        "docs_url": "/docs"
    }


@app.get("/health", tags=["System"])
def health_check():
    return {"status": "healthy"}
