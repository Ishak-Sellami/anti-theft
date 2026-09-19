from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.config import settings
from app.db.base import Base
from app.db.session import engine, AsyncSessionLocal
from app.db.models import *  # Ensure all models are registered
from app.api.v1.api_router import api_v1_router
from app.core.exceptions import AntiSarikaException
from app.services.policy_service import PolicyService
from app.services.device_service import get_master_backend_keys


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize backend master keys
    get_master_backend_keys()

    # Create tables if using SQLite / development mode
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize default recovery policies
    async with AsyncSessionLocal() as session:
        await PolicyService.initialize_default_policies(session)
        await session.commit()

    yield

    # Cleanup resources on shutdown
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description="Anti-Sarika Device Recovery & Anti-Theft Platform Control Plane API",
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AntiSarikaException)
async def antisarika_exception_handler(request: Request, exc: AntiSarikaException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": exc.error_code,
            "detail": exc.detail,
        },
        headers=exc.headers,
    )


# Mount v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_STR)


@app.get("/health", tags=["Health"])
async def health_check():
    """System health check endpoint."""
    return {
        "status": "HEALTHY",
        "service": settings.APP_NAME,
        "version": "0.1.0"
    }
