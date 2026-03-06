"""API key authentication dependency.

Usage:
    Add `api_key_auth` as a route dependency for protected endpoints.
    Set WAYOS_API_KEY in environment. If unset, auth is disabled (dev mode).
"""
import secrets

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader

from app.config import settings

_header_scheme = APIKeyHeader(name="X-API-Key", auto_error=False)


async def api_key_auth(api_key: str | None = Security(_header_scheme)) -> str | None:
    """Validate the API key from the X-API-Key header.

    Returns the key on success. If WAYOS_API_KEY is not configured, auth is
    bypassed (development mode).
    """
    expected = settings.wayos_api_key

    # Dev mode: no key configured → skip auth
    if not expected:
        return None

    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key. Provide X-API-Key header.",
        )

    # Constant-time comparison to prevent timing attacks
    if not secrets.compare_digest(api_key, expected):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key.",
        )

    return api_key
