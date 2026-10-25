import os
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db import init_db
from app.api import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize database tables on startup
    init_db()
    yield


app = FastAPI(
    title="AICTE Approval Workflow & Regulatory Compliance Platform API",
    description="Backend API for Smart India Hackathon (SIH26262) prototype. "
                "Covers EVC lifecycle, compliance obligations, document renewals, "
                "deadline escalation, and in-app notifications.",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS configuration for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits localhost dev frontend clients
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all /api routers
app.include_router(api_router)


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "healthy",
        "service": "AICTE Approval & Compliance Management System",
        "version": "1.0.0"
    }


@app.get("/", tags=["Root"])
def root():
    return {
        "message": "AICTE Approval Workflow Automation and Regulatory Compliance Platform Backend is active.",
        "documentation": "/docs",
        "health": "/health"
    }


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8005))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"Starting server on http://{host}:{port} (docs: http://{host}:{port}/docs)...")
    uvicorn.run("app.main:app", host=host, port=port, reload=True)
