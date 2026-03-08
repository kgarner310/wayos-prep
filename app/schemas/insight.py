"""Pydantic schemas for the insight feed."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class InsightItem(BaseModel):
    insight_type: str  # coverage_alert|duty_to_advise|workers_comp_signal|market_signal|opportunity
    title: str
    subtitle: str = ""
    suggested_action: str = ""
    severity: str = "info"  # info|low|medium|high|critical
    timestamp: Optional[datetime] = None


class InsightFeedResponse(BaseModel):
    account_id: str
    insights: list[InsightItem] = []
    total: int = 0
