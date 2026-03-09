"""Pydantic schemas for renewal brief request/response."""

from typing import Optional

from pydantic import BaseModel


# --- Request ---

class RenewalBriefRequest(BaseModel):
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


# --- Response sub-models ---

class AccountSummary(BaseModel):
    account_name: str = ""
    industry: str = ""
    state: str = ""
    account_stage: str = "renewal"
    key_facts: list[str] = []


class RiskOverview(BaseModel):
    risk_level: str = "moderate"
    confidence: float = 0.5
    headline: str = ""


class CoverageGapItem(BaseModel):
    coverage: str
    reason: str
    risk_level: str
    confidence: float = 0.0
    applied_rules: list[dict] = []


# --- Response ---

class RenewalBriefResponse(BaseModel):
    account_summary: AccountSummary
    risk_overview: RiskOverview
    underwriter_concerns: list[str] = []
    coverage_gaps: list[CoverageGapItem] = []
    loss_patterns: list[str] = []
    mod_trends: list[str] = []
    producer_questions: list[str] = []
    defense_strategy: list[str] = []
    peer_insights: list[str] = []
    recommended_actions: list[str] = []
