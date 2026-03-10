"""Pydantic schemas for Service Triage Inbox."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class DraftMessage(BaseModel):
    subject: str = ""
    body: str = ""


class DraftAmsNote(BaseModel):
    summary: str = ""
    action_items: list[str] = []
    category: str = ""


class TriageRequestCreate(BaseModel):
    account_id: Optional[UUID] = None
    input_type: str = "text"  # text | voice_transcript | file
    input_text: str
    input_filename: Optional[str] = None
    input_extracted_text: Optional[str] = None


class TriageRequestUpdate(BaseModel):
    summary: Optional[str] = None
    request_type: Optional[str] = None
    urgency: Optional[str] = None
    draft_insured: Optional[dict] = None
    draft_carrier: Optional[dict] = None
    draft_ams_note: Optional[dict] = None


class TriageRequestResponse(BaseModel):
    id: UUID
    account_id: Optional[UUID] = None
    agency_id: Optional[UUID] = None
    created_by_user_id: Optional[UUID] = None
    input_type: str
    input_text: str
    input_filename: Optional[str] = None
    input_extracted_text: Optional[str] = None
    status: str
    request_type: Optional[str] = None
    urgency: Optional[str] = None
    summary: Optional[str] = None
    draft_insured: Optional[dict] = None
    draft_carrier: Optional[dict] = None
    draft_ams_note: Optional[dict] = None
    approved_at: Optional[datetime] = None
    approved_by_user_id: Optional[UUID] = None
    confidence: Optional[float] = None
    model_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TriageRequestListResponse(BaseModel):
    requests: list[TriageRequestResponse] = []
    total: int = 0
