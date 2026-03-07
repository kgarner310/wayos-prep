"""Pydantic schemas for underwriter narrative generation."""

from typing import Optional

from pydantic import BaseModel


# --- Request ---

class UnderwriterNarrativeRequest(BaseModel):
    account_name: str = ""
    industry: str = ""
    state: str = ""
    employee_count: int = 0
    annual_revenue: float = 0.0
    vehicle_count: int = 0
    uses_subcontractors: bool = False
    current_coverages: list[str] = []
    experience_mod: Optional[float] = None
    account_stage: str = "renewal"
    claims_summary: str = ""
    notes: str = ""
    loss_run_data: Optional[dict] = None
    experience_mod_data: Optional[dict] = None
    narrative_type: str = "renewal"
    intended_market_positioning: str = "standard"
    renewal_brief: Optional[dict] = None
    public_web_intel: Optional[dict] = None
    producer_id: Optional[str] = None


# --- Response sub-models ---

class NarrativeVersion(BaseModel):
    subject: str = ""
    title: str = ""
    body: str = ""


class FactSources(BaseModel):
    account_profile_used: bool = False
    renewal_brief_used: bool = False
    public_web_intel_used: bool = False


# --- Response ---

class UnderwriterNarrativeResponse(BaseModel):
    account_name: str = ""
    narrative_type: str = "renewal"
    email_version: NarrativeVersion
    memo_version: NarrativeVersion
    supporting_points: list[str] = []
    fact_sources: FactSources
    source_signals: list[str] = []
    cautions: list[str] = []
    style_applied: Optional[dict] = None
