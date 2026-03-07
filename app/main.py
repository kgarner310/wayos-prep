"""WAYOS PREP - Main FastAPI application."""

import logging
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

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("WAYOS PREP starting up")
    # Load industry knowledge profiles at startup
    from app.knowledge.industry_profiles import INDUSTRY_PROFILES
    logger.info("Industry profiles loaded: %d industries", len(INDUSTRY_PROFILES))
    yield
    logger.info("WAYOS PREP shutting down")


app = FastAPI(
    title="WAYOS PREP",
    description="Insurance meeting-brief engine for commercial producers",
    version="0.1.0",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(api_router, prefix="/api/v1")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(admin_router, prefix="/admin")


@app.get("/health")
def health():
    return {"status": "ok", "service": "wayos-prep"}
