import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.config import settings
from app.middleware.errors import ErrorHandlingMiddleware
from app.middleware.logging import RequestLoggingMiddleware
from app.middleware.rate_limit import RateLimitMiddleware

# --- Structured logging setup ---
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
    stream=sys.stdout,
)

app = FastAPI(
    title="WAYOS PREP",
    description="Meeting preparation engine for commercial insurance producers",
    version="1.0.0",
)

# --- Middleware (order matters: outermost first) ---

# 1. Error handling — catches everything
app.add_middleware(ErrorHandlingMiddleware)

# 2. Request logging — logs every request with request ID
app.add_middleware(RequestLoggingMiddleware)

# 3. Rate limiting
app.add_middleware(RateLimitMiddleware)

# 4. CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-API-Key", "X-Request-ID"],
)

# --- Routes ---
# Mount under /api/v1 for versioning, keep /health at root for load balancers
app.include_router(router, prefix="/api/v1")


# Backward-compat: also mount health at root
@app.get("/health")
def root_health():
    return {"status": "ok", "service": "wayos-prep"}
