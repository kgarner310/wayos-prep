"""Pydantic schemas for PIT Dispatch Records."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DispatchRecordResponse(BaseModel):
    id: UUID
    triage_request_id: Optional[UUID] = None
    account_id: Optional[UUID] = None
    agency_id: Optional[UUID] = None
    recipient_type: str
    channel: str
    subject: Optional[str] = None
    body: str
    dispatched_by_user_id: Optional[UUID] = None
    dispatched_at: datetime
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class DispatchListResponse(BaseModel):
    dispatches: list[DispatchRecordResponse] = []
    total: int = 0


class PITFeedItem(BaseModel):
    item_type: str  # "triage" | "dispatch"
    item_id: str
    timestamp: datetime
    summary: str
    urgency: Optional[str] = None
    status: str
    recipient_type: Optional[str] = None
    request_type: Optional[str] = None


class PITFeedResponse(BaseModel):
    items: list[PITFeedItem] = []
    total: int = 0


class PITStatsResponse(BaseModel):
    pending_triage: int = 0
    urgent_count: int = 0
    dispatches_today: int = 0
    accounts_touched: int = 0
