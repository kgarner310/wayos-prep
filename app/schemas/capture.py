"""Pydantic schemas for capture / ingestion flow."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class CaptureResponse(BaseModel):
    ingestion_event_id: UUID
    source_type: str
    extracted_text: str = ""
    signals: dict = {}


class ManualAccountCreate(BaseModel):
    account_name: str
    named_insured: Optional[str] = None
    industry: str = ""
    state: str = ""
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    payroll_estimate: Optional[float] = None
    workers_comp_mod: Optional[float] = None
    current_coverages: list[str] = []
    current_carriers: list[str] = []
    claims_summary: Optional[dict] = None
    vehicle_count: Optional[int] = None
    uses_subcontractors: bool = False
    website_url: Optional[str] = None
    notes: str = ""


class AccountFromCaptureRequest(BaseModel):
    ingestion_event_id: Optional[UUID] = None
    account_name: Optional[str] = None
    named_insured: Optional[str] = None
    industry: Optional[str] = None
    state: Optional[str] = None
    signals: Optional[dict] = None
