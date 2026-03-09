"""Pydantic schemas for deal outcomes and market signals."""

from typing import Optional

from pydantic import BaseModel


class OutcomeCreate(BaseModel):
    account_id: str
    outcome: str  # won|lost|renewed|pending|declined|no_quote
    outcome_reason: Optional[str] = None
    industry: Optional[str] = None
    state: Optional[str] = None
    carrier: Optional[str] = None
    premium: Optional[float] = None
    competitor: Optional[str] = None
    notes: Optional[str] = None

    class Config:
        str_max_length = 500


class OutcomeResponse(BaseModel):
    status: str = "ok"
    outcome_id: str
    account_id: str
    outcome: str


class MarketSignalResponse(BaseModel):
    carrier_win_rates: dict = {}
    loss_reasons: dict = {}
    total_outcomes: int = 0
    win_rate_overall: float = 0.0
    top_carrier: Optional[str] = None
