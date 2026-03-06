"""Simple in-memory rate limiting middleware.

Uses a sliding window counter per client IP. For production at scale,
swap the in-memory store for Redis (the interface stays the same).
"""
import time
from collections import defaultdict

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from app.config import settings


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Token-bucket-style rate limiter per client IP."""

    def __init__(self, app, requests_per_minute: int | None = None):
        super().__init__(app)
        self.rpm = requests_per_minute or settings.rate_limit_rpm
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        # Skip rate limiting for health checks
        if request.url.path == "/health" or request.url.path == "/api/v1/health":
            return await call_next(request)

        if self.rpm <= 0:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        window_start = now - 60.0

        # Prune old entries
        timestamps = self._buckets[client_ip]
        self._buckets[client_ip] = [t for t in timestamps if t > window_start]

        if len(self._buckets[client_ip]) >= self.rpm:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded. Try again shortly."},
                headers={"Retry-After": "60"},
            )

        self._buckets[client_ip].append(now)
        return await call_next(request)
