"""
FastAPI application entry point — complete version.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# pyrefly: ignore [missing-import]
from slowapi import Limiter, _rate_limit_exceeded_handler
# pyrefly: ignore [missing-import]
from slowapi.errors import RateLimitExceeded
# pyrefly: ignore [missing-import]
from slowapi.util import get_remote_address

from app.config import get_settings
from app.database import create_tables
from app.routers.auth import router as auth_router
from app.routers.cameras import live_router, router as cameras_router
from app.routers.parking import router as parking_router
from app.routers.violations import router as violations_router
from app.routers.analytics import router as analytics_router
from app.routers.users import router as users_router
from app.routers.ai_detection import router as ai_router
from app.utils.logging import get_logger, setup_logging

settings = get_settings()
setup_logging(log_level=settings.log_level, log_file=settings.log_file)
log = get_logger(__name__)

limiter = Limiter(key_func=get_remote_address, default_limits=[f"{settings.api_rate_limit}/minute"])


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    log.info("startup", version="1.0.0")
    # Create tables on startup (dev mode); use Alembic in production
    if settings.debug:
        await create_tables()
    yield
    log.info("shutdown")


app = FastAPI(
    title="Smart Curb & Parking Intelligence Platform",
    description="AI-powered real-time parking monitoring and violation enforcement API.",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS — allow configured origins and all local development ports
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:\d+)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth_router)
app.include_router(cameras_router)
app.include_router(parking_router)
app.include_router(violations_router)
app.include_router(analytics_router)
app.include_router(users_router)
app.include_router(live_router)
app.include_router(ai_router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "ok", "version": "1.0.0"}


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    log.error("unhandled_exception", error=str(exc), path=request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
    )
