"""Authentication service — JWT tokens, password hashing, user management."""

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import Agency, User

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# --- Password ---

def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


# --- JWT ---

def create_access_token(user_id: str, agency_id: str, role: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": user_id,
        "agency_id": agency_id,
        "role": role,
        "type": "access",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(user_id: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "type": "refresh",
        "exp": expire,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError:
        logger.debug("Invalid token")
        return None


# --- Slug ---

def _make_slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug or "agency"


# --- Registration ---

def register_user(db: Session, email: str, password: str, full_name: str,
                   agency_name: str, agency_slug: Optional[str] = None) -> dict:
    email = email.lower().strip()
    existing = db.query(User).filter(User.email == email).first()
    if existing:
        return {"error": "Email already registered"}

    slug = agency_slug or _make_slug(agency_name)
    agency = db.query(Agency).filter(Agency.slug == slug).first()
    if not agency:
        agency = Agency(agency_name=agency_name, slug=slug)
        db.add(agency)
        db.flush()

    user = User(
        email=email,
        hashed_password=hash_password(password),
        full_name=full_name,
        role="admin",
        agency_id=agency.id,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    db.refresh(agency)

    logger.info("User registered: %s (agency: %s)", email, agency.slug)

    access_token = create_access_token(str(user.id), str(agency.id), user.role)
    refresh_token = create_refresh_token(str(user.id))

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "agency_id": agency.id,
            "agency_name": agency.agency_name,
            "is_active": user.is_active,
        },
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
    }


# --- Login ---

def login_user(db: Session, email: str, password: str) -> dict:
    email = email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user:
        return {"error": "Invalid email or password"}
    if not user.is_active:
        return {"error": "Account is disabled"}
    if not verify_password(password, user.hashed_password):
        return {"error": "Invalid email or password"}

    agency = db.query(Agency).filter(Agency.id == user.agency_id).first()

    access_token = create_access_token(str(user.id), str(user.agency_id), user.role)
    refresh_token = create_refresh_token(str(user.id))

    logger.info("User logged in: %s", email)

    return {
        "user": {
            "id": user.id,
            "email": user.email,
            "full_name": user.full_name,
            "role": user.role,
            "agency_id": user.agency_id,
            "agency_name": agency.agency_name if agency else "",
            "is_active": user.is_active,
        },
        "tokens": {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        },
    }


# --- Refresh ---

def refresh_tokens(db: Session, refresh_token: str) -> dict:
    payload = decode_token(refresh_token)
    if not payload or payload.get("type") != "refresh":
        return {"error": "Invalid or expired refresh token"}

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return {"error": "User not found or disabled"}

    access_token = create_access_token(str(user.id), str(user.agency_id), user.role)
    new_refresh = create_refresh_token(str(user.id))

    return {
        "access_token": access_token,
        "refresh_token": new_refresh,
        "token_type": "bearer",
        "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    }


# --- Get current user ---

def get_user_from_token(db: Session, token: str) -> Optional[dict]:
    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        return None

    user_id = payload["sub"]
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        return None

    agency = db.query(Agency).filter(Agency.id == user.agency_id).first()
    return {
        "id": user.id,
        "email": user.email,
        "full_name": user.full_name,
        "role": user.role,
        "agency_id": user.agency_id,
        "agency_name": agency.agency_name if agency else "",
        "is_active": user.is_active,
    }
