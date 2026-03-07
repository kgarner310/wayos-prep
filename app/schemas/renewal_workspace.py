"""Pydantic schemas for the Renewal Workspace."""

from typing import Optional

from pydantic import BaseModel


class RenewalWorkspaceRequest(BaseModel):
    account_stage: str = "renewal"
    narrative_type: str = "renewal"
    producer_id: Optional[str] = None
    experience_mod: Optional[float] = None
    loss_run_data: Optional[dict] = None
    experience_mod_data: Optional[dict] = None


class CompanyIdentitySummary(BaseModel):
    company_name: str = ""
    founded_year: Optional[int] = None
    service_area: list[str] = []


class OperationsSignals(BaseModel):
    company_identity: CompanyIdentitySummary = CompanyIdentitySummary()
    operations_signals: list[str] = []
    safety_signals: list[str] = []
    scale_signals: list[str] = []
    carrier_relevant_signals: list[str] = []


class AccountSummary(BaseModel):
    account_name: str = ""
    industry: str = ""
    state: str = ""
    account_stage: str = "renewal"
    key_facts: list[str] = []


class RiskOverview(BaseModel):
    risk_level: str = "low"
    confidence: float = 0.4
    headline: str = ""


class CoverageGap(BaseModel):
    coverage: str = ""
    reason: str = ""
    risk_level: str = "medium"
    confidence: float = 0.5
    applied_rules: list[str] = []


class NarrativeSection(BaseModel):
    email_version: str = ""
    memo_version: str = ""
    style_applied: dict = {}


class RenewalWorkspaceResponse(BaseModel):
    account_id: str
    account_summary: AccountSummary = AccountSummary()
    operations_signals: OperationsSignals = OperationsSignals()
    risk_overview: RiskOverview = RiskOverview()
    coverage_gaps: list[CoverageGap] = []
    producer_questions: list[str] = []
    underwriter_narrative: NarrativeSection = NarrativeSection()
    recommended_actions: list[str] = []
    sections_available: list[str] = []
    error: Optional[str] = None
