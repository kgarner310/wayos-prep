"""Pydantic schemas for account health card."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class AccountHealthResponse(BaseModel):
    id: UUID
    account_id: UUID
    overall_score: int = 0
    coverage_score: int = 0
    workers_comp_score: int = 0
    carrier_fit_score: int = 0
    confidence: float = 0.0
    top_issues: list[str] = []
    duty_to_advise_alert_count: int = 0
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_model(cls, obj):
        """Build from AccountHealth ORM model, unpacking top_issues_json."""
        return cls(
            id=obj.id,
            account_id=obj.account_id,
            overall_score=obj.overall_score,
            coverage_score=obj.coverage_score,
            workers_comp_score=obj.workers_comp_score,
            carrier_fit_score=obj.carrier_fit_score,
            confidence=float(obj.confidence) if obj.confidence else 0.0,
            top_issues=obj.top_issues_json or [],
            duty_to_advise_alert_count=obj.duty_to_advise_alert_count,
            updated_at=obj.updated_at,
        )
