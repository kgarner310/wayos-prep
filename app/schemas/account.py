"""Pydantic schemas for account persistence."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AccountCreate(BaseModel):
    account_name: str
    industry: str = ""
    state: str = ""
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    vehicle_count: Optional[int] = None
    uses_subcontractors: bool = False
    current_coverages: list[str] = []
    website_url: Optional[str] = None
    social_urls: list[str] = []
    notes: str = ""


class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    industry: Optional[str] = None
    state: Optional[str] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    vehicle_count: Optional[int] = None
    uses_subcontractors: Optional[bool] = None
    current_coverages: Optional[list[str]] = None
    website_url: Optional[str] = None
    social_urls: Optional[list[str]] = None
    notes: Optional[str] = None


class AccountResponse(BaseModel):
    id: UUID
    account_name: str
    industry: Optional[str] = None
    state: Optional[str] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    vehicle_count: Optional[int] = None
    uses_subcontractors: bool = False
    current_coverages: Optional[list] = None
    website_url: Optional[str] = None
    social_urls: Optional[list] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountListResponse(BaseModel):
    accounts: list[AccountResponse] = []
    total: int = 0
