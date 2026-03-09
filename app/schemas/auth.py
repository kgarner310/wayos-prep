"""Pydantic schemas for authentication and authorization."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr


# --- Request ---

class RegisterRequest(BaseModel):
    email: str
    password: str
    full_name: str
    agency_name: str
    agency_slug: Optional[str] = None


class LoginRequest(BaseModel):
    email: str
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


# --- Response ---

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    agency_id: UUID
    agency_name: str
    is_active: bool
