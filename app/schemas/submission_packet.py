"""Pydantic schemas for the Submission Packet."""

from typing import Optional

from pydantic import BaseModel

from app.schemas.renewal_workspace import (
    AccountSummary, OperationsSignals, RiskOverview,
    CoverageGap, NarrativeSection,
)


class SubmissionPacketRequest(BaseModel):
    narrative_type: str = "renewal"
    include_public_intel: bool = True
    include_questions: bool = True
    include_gaps: bool = True
    use_latest_saved_artifacts: bool = True
    producer_id: Optional[str] = None
    account_stage: str = "renewal"


class PacketSection(BaseModel):
    title: str
    content_type: str  # "text", "list", "gaps", "kv"
    body: str = ""
    items: list[str] = []


class SubmissionPacketResponse(BaseModel):
    account_id: str
    packet_title: str
    account_summary: AccountSummary = AccountSummary()
    operations_signals: Optional[OperationsSignals] = None
    risk_overview: RiskOverview = RiskOverview()
    coverage_gaps: list[CoverageGap] = []
    producer_questions: list[str] = []
    underwriter_narrative: NarrativeSection = NarrativeSection()
    recommended_actions: list[str] = []
    sections: list[PacketSection] = []
    rendered_text: str = ""
    rendered_markdown: str = ""
    sections_available: list[str] = []
    error: Optional[str] = None
