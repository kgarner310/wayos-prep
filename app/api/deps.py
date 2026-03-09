"""FastAPI dependencies for authentication and agency scoping."""

import logging
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.auth_service import decode_token
from app.models.models import User, Agency

logger = logging.getLogger(__name__)
security = HTTPBearer(auto_error=False)


class CurrentUser:
    """Authenticated user context available to route handlers."""

    def __init__(self, user_id: UUID, agency_id: UUID, role: str, email: str, full_name: str):
        self.user_id = user_id
        self.agency_id = agency_id
        self.role = role
        self.email = email
        self.full_name = full_name


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> CurrentUser:
    """Require a valid JWT access token. Returns CurrentUser."""
    if not credentials:
        raise HTTPException(401, "Not authenticated", headers={"WWW-Authenticate": "Bearer"})

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        raise HTTPException(401, "Invalid or expired token", headers={"WWW-Authenticate": "Bearer"})

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(401, "User not found or disabled")

    return CurrentUser(
        user_id=user.id,
        agency_id=user.agency_id,
        role=user.role,
        email=user.email,
        full_name=user.full_name,
    )


def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
) -> Optional[CurrentUser]:
    """Optional auth — returns CurrentUser if token present, None otherwise."""
    if not credentials:
        return None

    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None

    return CurrentUser(
        user_id=user.id,
        agency_id=user.agency_id,
        role=user.role,
        email=user.email,
        full_name=user.full_name,
    )


def require_role(allowed_roles: list[str]):
    """Dependency factory that checks user has one of the allowed roles."""
    def _check(user: CurrentUser = Depends(get_current_user)):
        if user.role not in allowed_roles:
            raise HTTPException(403, "Insufficient permissions")
        return user
    return _check
