"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


# --- Source Schemas ---

class SourceIngestText(BaseModel):
    title: str
    raw_text: str
    source_type: str = "article"
    authority_level: str = "trade"
    jurisdiction_state: Optional[str] = None
    published_at: Optional[datetime] = None
    publisher: Optional[str] = None
    author: Optional[str] = None

class SourceIngestURL(BaseModel):
    url: str
    source_type: str = "article"
    authority_level: str = "trade"
    jurisdiction_state: Optional[str] = None

class SourceResponse(BaseModel):
    id: UUID
    source_type: str
    title: str
    publisher: Optional[str] = None
    author: Optional[str] = None
    url: Optional[str] = None
    jurisdiction_state: Optional[str] = None
    authority_level: str
    authority_score: float
    freshness_score: float
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class SourceDetailResponse(SourceResponse):
    raw_text: Optional[str] = None
    document_hash: Optional[str] = None
    tags: list = []
    chunks: list = []

class TagResponse(BaseModel):
    id: UUID
    tag_type: str
    tag_value: str
    confidence: float

    model_config = ConfigDict(from_attributes=True)

class ChunkResponse(BaseModel):
    id: UUID
    chunk_index: int
    heading: Optional[str] = None
    text_content: str
    token_count: Optional[int] = None
    char_count: Optional[int] = None
    has_embedding: bool = False
    tags: list[TagResponse] = []

    model_config = ConfigDict(from_attributes=True)


# --- Query / Prep Schemas ---

class PrepQueryRequest(BaseModel):
    industry: str
    state: str
    employee_count: int = 10
    current_mod: Optional[float] = None
    raw_query: Optional[str] = None

class PrepQueryResponse(BaseModel):
    query_id: UUID
    brief_id: UUID
    brief: dict
    rendered_markdown: str


# --- Brief Schema ---

class LossDriver(BaseModel):
    title: str
    why_it_matters: str
    confidence: str = "medium"
    source_ids: list[str] = []

class CoverageBlindSpot(BaseModel):
    title: str
    why_it_matters: str
    source_ids: list[str] = []

class QuestionToAsk(BaseModel):
    question: str
    purpose: str
    source_ids: list[str] = []

class Watchout(BaseModel):
    note: str
    source_ids: list[str] = []

class ConfidenceNote(BaseModel):
    note: str
    severity: str = "info"

class CitationMapEntry(BaseModel):
    source_id: str
    title: str
    url: Optional[str] = None

class BriefOutput(BaseModel):
    industry: str
    state: str
    employee_count: int = 0
    current_mod: Optional[float] = None
    top_loss_drivers: list[LossDriver] = []
    coverage_blind_spots: list[CoverageBlindSpot] = []
    questions_to_ask: list[QuestionToAsk] = []
    watchouts: list[Watchout] = []
    confidence_notes: list[ConfidenceNote] = []
    citation_map: list[CitationMapEntry] = []


# --- Feedback ---

class FeedbackRequest(BaseModel):
    brief_id: UUID
    query_id: UUID
    event_type: str
    event_value: Optional[str] = None
    event_json: Optional[dict] = None
    user_id: Optional[str] = None

class FeedbackResponse(BaseModel):
    id: UUID
    event_type: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# --- Retrieval Debug ---

class RetrievalDebugResult(BaseModel):
    chunk_id: UUID
    rank_position: int
    similarity_score: Optional[float] = None
    rerank_score: Optional[float] = None
    selected: bool
    text_preview: str = ""
    source_title: str = ""

class RetrievalDebugResponse(BaseModel):
    query_id: UUID
    retrieval_run_id: Optional[UUID] = None
    embedding_model: Optional[str] = None
    filters: Optional[dict] = None
    candidate_count: int = 0
    selected_count: int = 0
    results: list[RetrievalDebugResult] = []
