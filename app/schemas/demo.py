"""Pydantic schemas for demo feedback and session summaries."""

from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DemoFeedbackRequest(BaseModel):
    session_id: Optional[str] = None
    account_id: Optional[str] = None
    would_use_before_meeting: Optional[str] = None
    most_useful_part: Optional[str] = None
    unclear_or_untrustworthy: Optional[str] = None
    what_next: Optional[str] = None
    overall_rating: Optional[int] = None
    notes: Optional[str] = None


class DemoFeedbackResponse(BaseModel):
    id: UUID
    session_id: Optional[str] = None
    overall_rating: Optional[int] = None
    created_at: str


class DemoSessionSummaryResponse(BaseModel):
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    event_count: int = 0
    actions_completed: list[str] = []
    time_to_first_workspace_seconds: Optional[float] = None
    time_to_first_packet_seconds: Optional[float] = None
    copy_actions: int = 0
    sections_expanded: int = 0
    errors_encountered: int = 0
    public_intel_refreshed_before_packet: bool = False
    feedback_count: int = 0
    timeline: list[dict] = []


class InstrumentEventRequest(BaseModel):
    event_type: str
    session_id: Optional[str] = None
    payload: Optional[dict] = None
