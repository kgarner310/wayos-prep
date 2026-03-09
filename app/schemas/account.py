"""Pydantic schemas for account persistence."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AccountCreate(BaseModel):
    account_name: str
    named_insured: Optional[str] = None
    industry: str = ""
    state: str = ""
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    vehicle_count: Optional[int] = None
    uses_subcontractors: bool = False
    current_coverages: list[str] = []
    payroll_estimate: Optional[float] = None
    workers_comp_mod: Optional[float] = None
    current_carriers: Optional[list[str]] = None
    claims_summary: Optional[dict] = None
    extracted_text: Optional[str] = None
    website_url: Optional[str] = None
    social_urls: list[str] = []
    notes: str = ""


class AccountUpdate(BaseModel):
    account_name: Optional[str] = None
    named_insured: Optional[str] = None
    industry: Optional[str] = None
    state: Optional[str] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    vehicle_count: Optional[int] = None
    uses_subcontractors: Optional[bool] = None
    current_coverages: Optional[list[str]] = None
    payroll_estimate: Optional[float] = None
    workers_comp_mod: Optional[float] = None
    current_carriers: Optional[list[str]] = None
    claims_summary: Optional[dict] = None
    extracted_text: Optional[str] = None
    website_url: Optional[str] = None
    social_urls: Optional[list[str]] = None
    notes: Optional[str] = None


class AccountResponse(BaseModel):
    id: UUID
    account_name: str
    named_insured: Optional[str] = None
    industry: Optional[str] = None
    state: Optional[str] = None
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    vehicle_count: Optional[int] = None
    uses_subcontractors: bool = False
    current_coverages: Optional[list] = None
    payroll_estimate: Optional[float] = None
    workers_comp_mod: Optional[float] = None
    current_carriers: Optional[list] = None
    claims_summary: Optional[dict] = None
    website_url: Optional[str] = None
    social_urls: Optional[list] = None
    notes: Optional[str] = None
    last_public_intel_refresh_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class AccountListResponse(BaseModel):
    accounts: list[AccountResponse] = []
    total: int = 0
