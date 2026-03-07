"""Pydantic schemas for producer style preferences."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class ProducerStyleCreate(BaseModel):
    producer_id: str
    audience: str = "underwriter"
    default_posture: str = "balanced"
    directness: Optional[str] = None
    verbosity: Optional[str] = None
    warmth: Optional[str] = None
    confidence_style: Optional[str] = None


class ProducerStyleUpdate(BaseModel):
    audience: Optional[str] = None
    default_posture: Optional[str] = None
    directness: Optional[str] = None
    verbosity: Optional[str] = None
    warmth: Optional[str] = None
    confidence_style: Optional[str] = None


class ProducerStyleResponse(BaseModel):
    id: UUID
    producer_id: str
    audience: Optional[str] = "underwriter"
    default_posture: Optional[str] = "balanced"
    directness: Optional[str] = None
    verbosity: Optional[str] = None
    warmth: Optional[str] = None
    confidence_style: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
