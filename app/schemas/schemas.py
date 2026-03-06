"""Pydantic schemas for request/response validation."""

from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


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
    entity_type: Optional[str] = None
    public_entity_type: Optional[str] = None
    department: Optional[str] = None

class PrepQueryResponse(BaseModel):
    query_id: UUID
    brief_id: UUID
    brief: dict
    rendered_markdown: str
    risk_score: Optional[dict] = None


# --- Brief Schema ---

class LossDriver(BaseModel):
    title: str
    why_it_matters: str
    confidence: Literal["high", "medium", "low"] = "medium"
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
    severity: Literal["info", "warning", "critical"] = "info"

class CitationMapEntry(BaseModel):
    source_id: str
    title: str
    url: Optional[str] = None

class CoverageGapItem(BaseModel):
    title: str
    severity: Literal["high", "medium", "low"] = "medium"
    reason: str
    why_now: str = ""
    suggested_question: str = ""
    suggested_coverage_or_action: str = ""
    evidence_source: str = "industry"

class ProducerAmmo(BaseModel):
    renewal_pressure_points: list[str] = []
    underwriting_hot_buttons: list[str] = []
    cross_sell_openings: list[str] = []
    hard_questions_to_ask: list[str] = []

class BriefOutput(BaseModel):
    industry: str
    state: str
    employee_count: int = 0
    current_mod: Optional[float] = None
    entity_type: Optional[str] = None
    public_entity_type: Optional[str] = None
    department: Optional[str] = None
    top_loss_drivers: list[LossDriver] = []
    coverage_blind_spots: list[CoverageBlindSpot] = []
    questions_to_ask: list[QuestionToAsk] = []
    watchouts: list[Watchout] = []
    confidence_notes: list[ConfidenceNote] = []
    citation_map: list[CitationMapEntry] = []
    coverage_gap_detector: list[CoverageGapItem] = []
    producer_ammo: Optional[ProducerAmmo] = None


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

# --- Risk Scoring Schemas ---

class RiskThemeInput(BaseModel):
    slug: str
    strength: float = 0.5

class QuestionSignal(BaseModel):
    category: str
    weight: float = 0.5

class RiskScoreRequest(BaseModel):
    industry: str
    state: str
    employee_count: int = 10
    current_mod: Optional[float] = None
    entity_type: str = "private_business"
    public_entity_type: Optional[str] = None
    department: Optional[str] = None
    account_traits: list[str] = []
    retrieved_risk_themes: list[RiskThemeInput] = []
    known_coverages: list[str] = []
    question_signals: list[QuestionSignal] = []
    source_confidence: float = 0.5

class ScoreComponent(BaseModel):
    component_type: str
    component_key: str
    component_label: Optional[str] = None
    raw_value: Optional[float] = None
    weighted_value: Optional[float] = None
    explanation: Optional[str] = None

class TopRiskTheme(BaseModel):
    risk_theme: str
    score_contribution: float
    reason: str

class CoverageGapAlert(BaseModel):
    risk_theme: str
    suggested_coverage: str
    alert_severity: str
    alert_reason: str

class MissingInfoAlert(BaseModel):
    missing_field: str
    alert_severity: str
    alert_reason: str
    recommended_question: Optional[str] = None

class ScoreExplanation(BaseModel):
    base_exposure_score: float
    trait_amplifier_score: float
    account_detail_modifier_score: float
    final_adjusted_score: float
    confidence_notes: list[str] = []

class RiskScoreOutput(BaseModel):
    overall_risk_score: float
    risk_band: str
    confidence_score: float
    top_risk_themes: list[TopRiskTheme] = []
    coverage_gap_alerts: list[CoverageGapAlert] = []
    missing_information_alerts: list[MissingInfoAlert] = []
    score_explanation: ScoreExplanation
    components: list[ScoreComponent] = []

class RiskScoreResponse(BaseModel):
    risk_score_run_id: UUID
    query_id: Optional[UUID] = None
    brief_id: Optional[UUID] = None
    score: RiskScoreOutput
    created_at: Optional[datetime] = None


# --- Retrieval Debug ---

# --- Coverage Gap Insight Engine ---

class CoverageGapInsightRequest(BaseModel):
    industry: str
    state: str
    employees: Optional[int] = None
    employee_count: Optional[int] = None
    vehicles: Optional[int] = None
    vehicle_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    experience_mod: Optional[float] = None
    current_mod: Optional[float] = None
    uses_subcontractors: Optional[bool] = False
    current_coverages: list[str] = []

class CoverageGapDetail(BaseModel):
    coverage: str
    reason: str
    risk_level: Literal["high", "medium", "low"]

class CoverageGapInsightResponse(BaseModel):
    coverage_gaps: list[CoverageGapDetail] = []
    suggested_questions: list[str] = []


# --- Producer Ammo Questions Engine ---

class ProducerAmmoRequest(BaseModel):
    industry: str
    state: str
    employee_count: Optional[int] = None
    annual_revenue: Optional[float] = None
    vehicle_count: Optional[int] = None
    experience_mod: Optional[float] = None
    uses_subcontractors: Optional[bool] = False
    current_coverages: list[str] = []
    claims_summary: Optional[str] = None
    account_stage: Optional[str] = "renewal"
    notes: Optional[str] = None

class AmmoQuestions(BaseModel):
    top_questions: list[str] = []
    coverage_traps: list[str] = []
    operational_change_questions: list[str] = []
    underwriting_flags: list[str] = []

class ProducerAmmoResponse(BaseModel):
    industry: str
    account_stage: str
    ammo_questions: AmmoQuestions


# --- Agency Ammo Feed ---

class AgencyAmmoFeedSummary(BaseModel):
    top_question_themes: list[str] = []
    rising_risk_topics: list[str] = []
    common_coverage_gaps: list[str] = []
    suggested_openers: list[str] = []

class AgencyAmmoFeedResponse(BaseModel):
    industry: str
    state: str
    date_range_days: int
    summary: AgencyAmmoFeedSummary


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
