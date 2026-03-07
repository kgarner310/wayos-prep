"""Authentication endpoints — register, login, refresh, me."""

import logging

from fastapi import APIRouter, Depends, HTTPException, Request
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.auth import (
    RegisterRequest, LoginRequest, RefreshRequest,
    TokenResponse, UserResponse,
)
from app.services.auth_service import register_user, login_user, refresh_tokens
from app.services.audit_service import log_audit_event
from app.api.deps import get_current_user, CurrentUser

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/auth", tags=["auth"])
limiter = Limiter(key_func=get_remote_address)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, db: Session = Depends(get_db)):
    """Register a new user and agency."""
    result = register_user(
        db,
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        agency_name=payload.agency_name,
        agency_slug=payload.agency_slug,
    )
    if result.get("error"):
        raise HTTPException(400, result["error"])

    log_audit_event(
        db,
        event_type="user_registered",
        user_id=result["user"]["id"],
        agency_id=result["user"]["agency_id"],
        resource_type="user",
        resource_id=str(result["user"]["id"]),
        ip_address=_client_ip(request),
    )

    return TokenResponse(**result["tokens"])


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, db: Session = Depends(get_db)):
    """Authenticate and receive tokens."""
    result = login_user(db, email=payload.email, password=payload.password)
    if result.get("error"):
        log_audit_event(
            db,
            event_type="login_failed",
            detail={"email": payload.email, "reason": result["error"]},
            ip_address=_client_ip(request),
        )
        raise HTTPException(401, result["error"])

    log_audit_event(
        db,
        event_type="login_success",
        user_id=result["user"]["id"],
        agency_id=result["user"]["agency_id"],
        ip_address=_client_ip(request),
    )

    return TokenResponse(**result["tokens"])


@router.post("/refresh", response_model=TokenResponse)
@limiter.limit("20/minute")
def refresh(request: Request, payload: RefreshRequest, db: Session = Depends(get_db)):
    """Refresh access token using a refresh token."""
    result = refresh_tokens(db, payload.refresh_token)
    if result.get("error"):
        raise HTTPException(401, result["error"])
    return TokenResponse(**result)


@router.get("/me", response_model=UserResponse)
def get_me(user: CurrentUser = Depends(get_current_user), db: Session = Depends(get_db)):
    """Get the current authenticated user profile."""
    from app.models.models import Agency
    agency = db.query(Agency).filter(Agency.id == user.agency_id).first()
    return UserResponse(
        id=user.user_id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        agency_id=user.agency_id,
        agency_name=agency.agency_name if agency else "",
        is_active=True,
    )
