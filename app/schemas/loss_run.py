"""Pydantic schemas for loss run analysis."""

from typing import Optional

from pydantic import BaseModel


# --- Request ---

class LossRunClaim(BaseModel):
    date_of_loss: Optional[str] = None
    line_of_business: str = "Unknown"
    cause_of_loss: Optional[str] = None
    paid_amount: float = 0.0
    reserve_amount: float = 0.0
    claim_status: str = "Closed"
    claimant_description: Optional[str] = None


class LossRunRequest(BaseModel):
    policy_period: Optional[str] = None
    industry: Optional[str] = None
    state: Optional[str] = None
    claims: list[LossRunClaim] = []


# --- Response ---

class LossRunSummary(BaseModel):
    total_claims: int
    open_claims: int
    total_incurred: float
    total_paid: float
    total_reserves: float
    loss_ratio: Optional[float] = None


class LossRunLineDetail(BaseModel):
    line: str
    claim_count: int
    total_incurred: float
    total_paid: float
    open_reserves: float
    causes: list[str]


class LossRunAnalysisResponse(BaseModel):
    summary: LossRunSummary
    by_line: list[LossRunLineDetail]
    patterns: list[str]
    underwriting_flags: list[str]
    producer_talking_points: list[str]
