"""Pydantic schemas for saved artifact persistence."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ArtifactCreate(BaseModel):
    account_id: Optional[UUID] = None
    artifact_type: str
    artifact_subtype: Optional[str] = None
    title: str = ""
    content_json: dict
    rendered_text: Optional[str] = None
    status: str = "ready"
    confidence: Optional[float] = None
    model_name: Optional[str] = None
    created_by_user_id: Optional[str] = None


class ArtifactResponse(BaseModel):
    id: UUID
    account_id: Optional[UUID] = None
    artifact_type: str
    artifact_subtype: Optional[str] = None
    title: Optional[str] = None
    content_json: dict
    rendered_text: Optional[str] = None
    status: str = "ready"
    confidence: Optional[float] = None
    model_name: Optional[str] = None
    created_by_user_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ArtifactListResponse(BaseModel):
    artifacts: list[ArtifactResponse] = []
    total: int = 0
