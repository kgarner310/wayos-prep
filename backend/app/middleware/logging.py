"""Structured request logging middleware with request ID propagation."""
import logging
import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger("wayos.access")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Attach a unique request ID to every request and log access info."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex[:16]
        request.state.request_id = request_id

        start = time.perf_counter()
        response: Response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - start) * 1000, 1)

        response.headers["X-Request-ID"] = request_id

        logger.info(
            "method=%s path=%s status=%d duration_ms=%.1f request_id=%s client=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            request_id,
            request.client.host if request.client else "unknown",
        )

        return response
