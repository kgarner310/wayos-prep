"""WAYOS PREP - Main FastAPI application."""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api.routes import router as api_router
from app.api.admin import router as admin_router
from app.api.auth_routes import router as auth_router
from app.security.headers import SecurityHeadersMiddleware

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("WAYOS PREP starting up (env=%s)", settings.APP_ENV)
    # Log connection targets (mask passwords)
    import re
    safe_db = re.sub(r"://[^@]+@", "://***@", settings.DATABASE_URL)
    safe_redis = re.sub(r"://[^@]+@", "://***@", settings.REDIS_URL)
    logger.info("DATABASE_URL target: %s", safe_db)
    logger.info("REDIS_URL target: %s", safe_redis)
    logger.info("CORS_ORIGINS: %s", settings.CORS_ORIGINS)
    if settings.is_production and "unsafe" in settings.JWT_SECRET_KEY:
        logger.warning("JWT_SECRET_KEY appears to be the dev default — set a secure key for production!")
    # Test database connectivity at startup
    try:
        from sqlalchemy import text
        from app.db.session import get_engine
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection verified OK")
    except Exception as e:
        logger.error("DATABASE CONNECTION FAILED at startup: %s", e)
    # Load industry knowledge profiles at startup
    from app.knowledge.industry_profiles import INDUSTRY_PROFILES
    logger.info("Industry profiles loaded: %d industries", len(INDUSTRY_PROFILES))
    # Initialize Redis cache (non-blocking — app works without Redis)
    from app.core.cache import get_redis
    get_redis()
    yield
    logger.info("WAYOS PREP shutting down")
    from app.core.cache import reset_redis
    reset_redis()


app = FastAPI(
    title="WAYOS PREP",
    description="Account-centric insurance intelligence for commercial P&C producers",
    version="0.3.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Security headers (outermost middleware — runs on every response)
app.add_middleware(SecurityHeadersMiddleware)

# CORS — use configured origins, not wildcard
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    allow_credentials=True,
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(api_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/admin")

# Serve React frontend from /app if built
_frontend_dist = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend", "dist")
if os.path.isdir(_frontend_dist):
    app.mount("/app", StaticFiles(directory=_frontend_dist, html=True), name="frontend")


@app.get("/health")
def health():
    """Health check that verifies DB and Redis connectivity."""
    from sqlalchemy import text
    from app.db.session import get_engine
    from app.core.cache import get_redis

    checks = {"service": "wayos-prep"}

    # Database check
    try:
        with get_engine().connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as e:
        checks["database"] = f"error: {e}"
        logger.error("Health check — database unreachable: %s", e)

    # Redis check
    try:
        r = get_redis()
        if r:
            r.ping()
            checks["redis"] = "ok"
        else:
            checks["redis"] = "unavailable"
    except Exception as e:
        checks["redis"] = f"error: {e}"

    all_ok = checks.get("database") == "ok"
    checks["status"] = "ok" if all_ok else "degraded"

    return checks
