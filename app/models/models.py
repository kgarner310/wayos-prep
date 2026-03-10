"""SQLAlchemy models for WAYOS PREP."""

import uuid
from datetime import datetime, timezone

from sqlalchemy import (
    Column, Text, Integer, Boolean, Numeric, ForeignKey,
    DateTime, Index, UniqueConstraint, func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import relationship

from app.db.session import Base


def utcnow():
    return datetime.now(timezone.utc)


class Source(Base):
    __tablename__ = "sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    source_type = Column(Text, nullable=False)
    title = Column(Text, nullable=False)
    publisher = Column(Text)
    author = Column(Text)
    url = Column(Text)
    canonical_url = Column(Text)
    published_at = Column(DateTime(timezone=True))
    retrieved_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    jurisdiction = Column(Text)
    jurisdiction_state = Column(Text)
    country_code = Column(Text, default="US")
    license_type = Column(Text, nullable=False, default="public")
    authority_level = Column(Text, nullable=False, default="trade")
    authority_score = Column(Numeric(4, 2), nullable=False, default=5.00)
    freshness_score = Column(Numeric(4, 2), nullable=False, default=5.00)
    document_hash = Column(Text)
    raw_text = Column(Text)
    raw_text_path = Column(Text)
    status = Column(Text, nullable=False, default="new")
    language_code = Column(Text, default="en")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow)

    tags = relationship("SourceTag", back_populates="source", cascade="all, delete-orphan")
    chunks = relationship("SourceChunk", back_populates="source", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_sources_source_type", "source_type"),
        Index("ix_sources_jurisdiction_state", "jurisdiction_state"),
        Index("ix_sources_authority_level", "authority_level"),
        Index("ix_sources_published_at", "published_at"),
        Index("ix_sources_status", "status"),
    )


class SourceTag(Base):
    __tablename__ = "source_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    tag_type = Column(Text, nullable=False)
    tag_value = Column(Text, nullable=False)
    confidence = Column(Numeric(4, 2), nullable=False, default=1.00)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    source = relationship("Source", back_populates="tags")

    __table_args__ = (
        Index("ix_source_tags_source_id", "source_id"),
        Index("ix_source_tags_tag_type_value", "tag_type", "tag_value"),
    )


class SourceChunk(Base):
    __tablename__ = "source_chunks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    heading = Column(Text)
    text_content = Column(Text, nullable=False)
    text_summary = Column(Text)
    token_count = Column(Integer)
    char_count = Column(Integer)
    chunk_hash = Column(Text)
    jurisdiction = Column(Text)
    jurisdiction_state = Column(Text)
    authority_score = Column(Numeric(4, 2), nullable=False, default=5.00)
    freshness_score = Column(Numeric(4, 2), nullable=False, default=5.00)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow)

    source = relationship("Source", back_populates="chunks")
    tags = relationship("ChunkTag", back_populates="chunk", cascade="all, delete-orphan")
    embedding = relationship("ChunkEmbedding", back_populates="chunk", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("source_id", "chunk_index", name="uq_source_chunk_index"),
        Index("ix_source_chunks_source_id", "source_id"),
        Index("ix_source_chunks_jurisdiction_state", "jurisdiction_state"),
    )


class ChunkTag(Base):
    __tablename__ = "chunk_tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("source_chunks.id", ondelete="CASCADE"), nullable=False)
    tag_type = Column(Text, nullable=False)
    tag_value = Column(Text, nullable=False)
    confidence = Column(Numeric(4, 2), nullable=False, default=1.00)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    chunk = relationship("SourceChunk", back_populates="tags")

    __table_args__ = (
        Index("ix_chunk_tags_chunk_id", "chunk_id"),
        Index("ix_chunk_tags_tag_type_value", "tag_type", "tag_value"),
    )


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    chunk_id = Column(UUID(as_uuid=True), ForeignKey("source_chunks.id", ondelete="CASCADE"), primary_key=True)
    embedding = Column(Vector(1536))
    embedding_model = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    chunk = relationship("SourceChunk", back_populates="embedding")


class Query(Base):
    __tablename__ = "queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    user_id = Column(Text)
    session_id = Column(Text)
    product_surface = Column(Text, nullable=False, default="prep")
    raw_query = Column(Text, nullable=False)
    normalized_query = Column(Text)
    requested_industry = Column(Text)
    requested_state = Column(Text)
    employee_count = Column(Integer)
    current_mod = Column(Numeric(6, 3))
    entity_type = Column(Text)
    public_entity_type = Column(Text)
    department = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    retrieval_runs = relationship("RetrievalRun", back_populates="query", cascade="all, delete-orphan")
    briefs = relationship("GeneratedBrief", back_populates="query", cascade="all, delete-orphan")
    feedback_events = relationship("FeedbackEvent", back_populates="query", cascade="all, delete-orphan")


class RetrievalRun(Base):
    __tablename__ = "retrieval_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False)
    embedding_model = Column(Text)
    reranker_name = Column(Text)
    filters_json = Column(JSONB)
    candidate_count = Column(Integer, nullable=False, default=0)
    selected_count = Column(Integer, nullable=False, default=0)
    status = Column(Text, nullable=False, default="complete")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    query = relationship("Query", back_populates="retrieval_runs")
    results = relationship("RetrievalResult", back_populates="retrieval_run", cascade="all, delete-orphan")


class RetrievalResult(Base):
    __tablename__ = "retrieval_results"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    retrieval_run_id = Column(UUID(as_uuid=True), ForeignKey("retrieval_runs.id", ondelete="CASCADE"), nullable=False)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("source_chunks.id", ondelete="CASCADE"), nullable=False)
    rank_position = Column(Integer, nullable=False)
    similarity_score = Column(Numeric(8, 6))
    rerank_score = Column(Numeric(8, 6))
    selected = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    retrieval_run = relationship("RetrievalRun", back_populates="results")
    chunk = relationship("SourceChunk")

    __table_args__ = (
        Index("ix_retrieval_results_run_id", "retrieval_run_id"),
        Index("ix_retrieval_results_chunk_id", "chunk_id"),
    )


class GeneratedBrief(Base):
    __tablename__ = "generated_briefs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False)
    retrieval_run_id = Column(UUID(as_uuid=True), ForeignKey("retrieval_runs.id", ondelete="SET NULL"))
    model_name = Column(Text, nullable=False)
    brief_json = Column(JSONB, nullable=False)
    rendered_markdown = Column(Text)
    quality_status = Column(Text, nullable=False, default="unreviewed")
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    query = relationship("Query", back_populates="briefs")
    brief_sources = relationship("BriefSource", back_populates="brief", cascade="all, delete-orphan")


class BriefSource(Base):
    __tablename__ = "brief_sources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    brief_id = Column(UUID(as_uuid=True), ForeignKey("generated_briefs.id", ondelete="CASCADE"), nullable=False)
    source_id = Column(UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"), nullable=False)
    chunk_id = Column(UUID(as_uuid=True), ForeignKey("source_chunks.id", ondelete="SET NULL"))
    citation_label = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    brief = relationship("GeneratedBrief", back_populates="brief_sources")
    source = relationship("Source")
    chunk = relationship("SourceChunk")


class ProducerQuestion(Base):
    __tablename__ = "producer_questions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    question_text = Column(Text, nullable=False)
    category = Column(Text, nullable=False)
    industry = Column(Text)
    entity_type = Column(Text, nullable=False, default="public_entity")
    public_entity_type = Column(Text)
    department = Column(Text)
    risk_theme = Column(Text)
    coverage = Column(JSONB)  # Array of coverage strings, e.g. ["law_enforcement_liability", "epli"]
    purpose = Column(Text)
    follow_up_questions = Column(JSONB)
    importance_score = Column(Numeric(3, 1), default=5.0)
    difficulty_score = Column(Numeric(3, 1), default=5.0)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_producer_questions_category", "category"),
        Index("ix_producer_questions_industry", "industry"),
        Index("ix_producer_questions_department", "department"),
        Index("ix_producer_questions_risk_theme", "risk_theme"),
        Index("ix_producer_questions_entity_type", "entity_type"),
        Index("ix_producer_questions_public_entity_type", "public_entity_type"),
    )


class RiskTheme(Base):
    __tablename__ = "risk_themes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    name = Column(Text, nullable=False, unique=True)
    node_type = Column(Text, nullable=False)  # industry, risk_theme, coverage, department, entity_type
    display_label = Column(Text)
    description = Column(Text)
    entity_scope = Column(Text)  # private, public, both — scopes which entity types this node applies to
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_risk_themes_node_type", "node_type"),
        Index("ix_risk_themes_name", "name"),
    )


class RiskThemeEdge(Base):
    __tablename__ = "risk_theme_edges"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    from_node_type = Column(Text, nullable=False)
    from_node_value = Column(Text, nullable=False)
    edge_type = Column(Text, nullable=False)
    to_node_type = Column(Text, nullable=False)
    to_node_value = Column(Text, nullable=False)
    weight = Column(Numeric(5, 2), nullable=False, default=1.00)
    evidence_note = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_risk_theme_edges_from", "from_node_type", "from_node_value"),
        Index("ix_risk_theme_edges_to", "to_node_type", "to_node_value"),
        Index("ix_risk_theme_edges_type", "edge_type"),
        UniqueConstraint("from_node_type", "from_node_value", "edge_type",
                         "to_node_type", "to_node_value", name="uq_risk_theme_edge"),
    )


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    brief_id = Column(UUID(as_uuid=True), ForeignKey("generated_briefs.id", ondelete="CASCADE"), nullable=False)
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id", ondelete="CASCADE"), nullable=False)
    event_type = Column(Text, nullable=False)
    event_value = Column(Text)
    event_json = Column(JSONB)
    user_id = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    brief = relationship("GeneratedBrief")
    query = relationship("Query", back_populates="feedback_events")


class RiskScoreRun(Base):
    __tablename__ = "risk_score_runs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    query_id = Column(UUID(as_uuid=True), ForeignKey("queries.id", ondelete="CASCADE"))
    brief_id = Column(UUID(as_uuid=True), ForeignKey("generated_briefs.id", ondelete="SET NULL"))
    scoring_version = Column(Text, nullable=False)
    overall_risk_score = Column(Numeric(6, 2), nullable=False)
    risk_band = Column(Text, nullable=False)
    confidence_score = Column(Numeric(6, 2), nullable=False)
    score_json = Column(JSONB, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    components = relationship("RiskScoreComponent", back_populates="risk_score_run", cascade="all, delete-orphan")
    coverage_gaps = relationship("CoverageGapAlert", back_populates="risk_score_run", cascade="all, delete-orphan")
    missing_info = relationship("MissingInformationAlert", back_populates="risk_score_run", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_risk_score_runs_query_id", "query_id"),
        Index("ix_risk_score_runs_brief_id", "brief_id"),
    )


class RiskScoreComponent(Base):
    __tablename__ = "risk_score_components"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    risk_score_run_id = Column(UUID(as_uuid=True), ForeignKey("risk_score_runs.id", ondelete="CASCADE"), nullable=False)
    component_type = Column(Text, nullable=False)
    component_key = Column(Text, nullable=False)
    component_label = Column(Text)
    raw_value = Column(Numeric(8, 3))
    weighted_value = Column(Numeric(8, 3))
    explanation = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    risk_score_run = relationship("RiskScoreRun", back_populates="components")

    __table_args__ = (
        Index("ix_risk_score_components_run_id", "risk_score_run_id"),
        Index("ix_risk_score_components_type", "component_type"),
    )


class CoverageGapAlert(Base):
    __tablename__ = "coverage_gap_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    risk_score_run_id = Column(UUID(as_uuid=True), ForeignKey("risk_score_runs.id", ondelete="CASCADE"), nullable=False)
    risk_theme = Column(Text, nullable=False)
    suggested_coverage = Column(Text, nullable=False)
    alert_severity = Column(Text, nullable=False)
    alert_reason = Column(Text, nullable=False)
    supporting_node_json = Column(JSONB)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    risk_score_run = relationship("RiskScoreRun", back_populates="coverage_gaps")

    __table_args__ = (
        Index("ix_coverage_gap_alerts_run_id", "risk_score_run_id"),
    )


class MissingInformationAlert(Base):
    __tablename__ = "missing_information_alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    risk_score_run_id = Column(UUID(as_uuid=True), ForeignKey("risk_score_runs.id", ondelete="CASCADE"), nullable=False)
    missing_field = Column(Text, nullable=False)
    alert_severity = Column(Text, nullable=False)
    alert_reason = Column(Text, nullable=False)
    recommended_question = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    risk_score_run = relationship("RiskScoreRun", back_populates="missing_info")

    __table_args__ = (
        Index("ix_missing_information_alerts_run_id", "risk_score_run_id"),
    )


class DiscoveryOutcome(Base):
    __tablename__ = "discovery_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    industry = Column(Text, nullable=False)
    state = Column(Text, nullable=False)
    account_stage = Column(Text)
    source_type = Column(Text, nullable=False)
    source_key = Column(Text, nullable=False)
    exposure_found = Column(Boolean, nullable=False, default=False)
    exposure_type = Column(Text)
    coverage_added = Column(Text)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_discovery_outcomes_industry", "industry"),
        Index("ix_discovery_outcomes_state", "state"),
        Index("ix_discovery_outcomes_source_type", "source_type"),
        Index("ix_discovery_outcomes_created_at", "created_at"),
    )


class EventLog(Base):
    __tablename__ = "event_log"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    event_type = Column(Text, nullable=False)
    event_payload = Column(JSONB)
    user_id = Column(Text)
    session_id = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_event_log_event_type", "event_type"),
        Index("ix_event_log_created_at", "created_at"),
        Index("ix_event_log_session_id", "session_id"),
    )


class Agency(Base):
    __tablename__ = "agencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    agency_name = Column(Text, nullable=False)
    slug = Column(Text, nullable=False, unique=True)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow)

    users = relationship("User", back_populates="agency", cascade="all, delete-orphan")
    accounts = relationship("Account", back_populates="agency", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_agencies_slug", "slug"),
    )


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    email = Column(Text, nullable=False, unique=True)
    hashed_password = Column(Text, nullable=False)
    full_name = Column(Text, nullable=False)
    role = Column(Text, nullable=False, default="producer")
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow)

    agency = relationship("Agency", back_populates="users")

    __table_args__ = (
        Index("ix_users_email", "email"),
        Index("ix_users_agency_id", "agency_id"),
    )


class Account(Base):
    __tablename__ = "accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    account_name = Column(Text, nullable=False)
    named_insured = Column(Text, nullable=True)
    industry = Column(Text)
    state = Column(Text)
    employee_count = Column(Integer)
    annual_revenue = Column(Numeric(14, 2))
    vehicle_count = Column(Integer)
    uses_subcontractors = Column(Boolean, default=False)
    current_coverages = Column(JSONB)
    payroll_estimate = Column(Numeric(14, 2), nullable=True)
    workers_comp_mod = Column(Numeric(5, 3), nullable=True)
    current_carriers = Column(JSONB, nullable=True)
    claims_summary = Column(JSONB, nullable=True)
    extracted_text = Column(Text, nullable=True)
    website_url = Column(Text)
    social_urls = Column(JSONB)
    notes = Column(Text)
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=True)
    last_public_intel_refresh_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow)

    agency = relationship("Agency", back_populates="accounts")
    artifacts = relationship("SavedArtifact", back_populates="account", cascade="all, delete-orphan")
    health = relationship("AccountHealth", back_populates="account", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_accounts_account_name", "account_name"),
        Index("ix_accounts_named_insured", "named_insured"),
        Index("ix_accounts_industry", "industry"),
        Index("ix_accounts_state", "state"),
        Index("ix_accounts_created_at", "created_at"),
        Index("ix_accounts_agency_id", "agency_id"),
    )


class SavedArtifact(Base):
    __tablename__ = "saved_artifacts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True)
    artifact_type = Column(Text, nullable=False)
    artifact_subtype = Column(Text)
    title = Column(Text)
    content_json = Column(JSONB, nullable=False)
    rendered_text = Column(Text)
    status = Column(Text, nullable=False, default="ready", server_default="ready")
    confidence = Column(Numeric(4, 3), nullable=True)
    model_name = Column(Text, nullable=True)
    created_by_user_id = Column(Text)
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow)

    account = relationship("Account", back_populates="artifacts")

    __table_args__ = (
        Index("ix_saved_artifacts_account_id", "account_id"),
        Index("ix_saved_artifacts_artifact_type", "artifact_type"),
        Index("ix_saved_artifacts_status", "status"),
        Index("ix_saved_artifacts_created_at", "created_at"),
        Index("ix_saved_artifacts_agency_id", "agency_id"),
    )


class ProducerStylePreference(Base):
    __tablename__ = "producer_style_preferences"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    producer_id = Column(Text, nullable=False, unique=True)
    audience = Column(Text, default="underwriter")
    default_posture = Column(Text, default="balanced")
    directness = Column(Text)
    verbosity = Column(Text)
    warmth = Column(Text)
    confidence_style = Column(Text)
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow)

    __table_args__ = (
        Index("ix_producer_style_preferences_producer_id", "producer_id"),
        Index("ix_producer_style_preferences_agency_id", "agency_id"),
    )


class AuditEvent(Base):
    __tablename__ = "audit_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    event_type = Column(Text, nullable=False)
    user_id = Column(UUID(as_uuid=True), nullable=True)
    agency_id = Column(UUID(as_uuid=True), nullable=True)
    resource_type = Column(Text)
    resource_id = Column(Text)
    detail = Column(JSONB)
    ip_address = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_audit_events_event_type", "event_type"),
        Index("ix_audit_events_user_id", "user_id"),
        Index("ix_audit_events_agency_id", "agency_id"),
        Index("ix_audit_events_created_at", "created_at"),
    )


class DemoFeedback(Base):
    __tablename__ = "demo_feedback"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    user_id = Column(UUID(as_uuid=True), nullable=True)
    agency_id = Column(UUID(as_uuid=True), nullable=True)
    session_id = Column(Text)
    account_id = Column(UUID(as_uuid=True), nullable=True)
    would_use_before_meeting = Column(Text)
    most_useful_part = Column(Text)
    unclear_or_untrustworthy = Column(Text)
    what_next = Column(Text)
    overall_rating = Column(Integer)
    notes = Column(Text)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_demo_feedback_user_id", "user_id"),
        Index("ix_demo_feedback_created_at", "created_at"),
    )


# ============================================================
# ACCOUNT MEMORY LEDGER
# ============================================================


class AccountMemoryEntry(Base):
    """Persistent ledger of what was known, recommended, changed, and what happened next."""

    __tablename__ = "account_memory_entries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    account_id = Column(Text, nullable=False, index=True)
    agency_id = Column(Text, nullable=True, index=True)
    session_id = Column(Text, nullable=True)
    industry = Column(Text, nullable=True, index=True)
    entry_type = Column(Text, nullable=False, index=True)
    summary = Column(Text, nullable=False)
    payload_json = Column(JSONB, nullable=True)
    created_by = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_account_memory_account_created", "account_id", "created_at"),
        Index("ix_account_memory_agency_created", "agency_id", "created_at"),
        Index("ix_account_memory_industry_type", "industry", "entry_type"),
    )


# ============================================================
# DEAL OUTCOMES
# ============================================================


class DealOutcome(Base):
    """Records the outcome of a deal for market intelligence."""

    __tablename__ = "deal_outcomes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    account_id = Column(Text, nullable=False, index=True)
    industry = Column(Text, nullable=True, index=True)
    state = Column(Text, nullable=True, index=True)
    carrier = Column(Text, nullable=True, index=True)
    premium = Column(Numeric(14, 2), nullable=True)
    outcome = Column(Text, nullable=False, index=True)
    outcome_reason = Column(Text, nullable=True)
    competitor = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_deal_outcomes_industry_carrier", "industry", "carrier"),
        Index("ix_deal_outcomes_industry_outcome", "industry", "outcome"),
    )


# ============================================================
# ACCOUNT EVENTS (TIMELINE)
# ============================================================


class AccountEvent(Base):
    """Timeline events for an account lifecycle."""

    __tablename__ = "account_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    account_id = Column(Text, nullable=False, index=True)
    event_type = Column(Text, nullable=False, index=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_account_events_account_created", "account_id", "created_at"),
    )


# ============================================================
# ACCOUNT HEALTH
# ============================================================


class AccountHealth(Base):
    """Fast deterministic health card for an account."""

    __tablename__ = "account_health"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, unique=True)
    overall_score = Column(Integer, nullable=False, default=0, server_default="0")
    coverage_score = Column(Integer, nullable=False, default=0, server_default="0")
    workers_comp_score = Column(Integer, nullable=False, default=0, server_default="0")
    carrier_fit_score = Column(Integer, nullable=False, default=0, server_default="0")
    confidence = Column(Numeric(4, 3), nullable=False, default=0.0, server_default="0.0")
    top_issues_json = Column(JSONB, nullable=True)
    duty_to_advise_alert_count = Column(Integer, nullable=False, default=0, server_default="0")
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow)

    account = relationship("Account", back_populates="health")

    __table_args__ = (
        Index("ix_account_health_account_id", "account_id"),
    )


# ============================================================
# INGESTION EVENTS
# ============================================================


# ============================================================
# SERVICE TRIAGE INBOX
# ============================================================


class ServiceTriageRequest(Base):
    """Incoming service request with AI-generated triage and draft messages."""

    __tablename__ = "service_triage_requests"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    agency_id = Column(UUID(as_uuid=True), ForeignKey("agencies.id", ondelete="CASCADE"), nullable=True)
    created_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # Input
    input_type = Column(Text, nullable=False, default="text", server_default="text")
    input_text = Column(Text, nullable=False)
    input_filename = Column(Text, nullable=True)
    input_extracted_text = Column(Text, nullable=True)

    # Triage results
    status = Column(Text, nullable=False, default="pending", server_default="pending")
    request_type = Column(Text, nullable=True)
    urgency = Column(Text, nullable=True)
    summary = Column(Text, nullable=True)

    # Drafted messages
    draft_insured = Column(JSONB, nullable=True)
    draft_carrier = Column(JSONB, nullable=True)
    draft_ams_note = Column(JSONB, nullable=True)

    # Approval
    approved_at = Column(DateTime(timezone=True), nullable=True)
    approved_by_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    # AI metadata
    confidence = Column(Numeric(4, 3), nullable=True)
    model_name = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now(), onupdate=utcnow)

    __table_args__ = (
        Index("ix_service_triage_account_id", "account_id"),
        Index("ix_service_triage_agency_id", "agency_id"),
        Index("ix_service_triage_status", "status"),
        Index("ix_service_triage_created_at", "created_at"),
        Index("ix_service_triage_urgency", "urgency"),
    )


class IngestionEvent(Base):
    """Tracks file/text ingestion into the system."""

    __tablename__ = "ingestion_events"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, server_default=func.gen_random_uuid())
    account_id = Column(UUID(as_uuid=True), ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True)
    source_type = Column(Text, nullable=False)
    filename = Column(Text, nullable=True)
    raw_text = Column(Text, nullable=True)
    extraction_json = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow, server_default=func.now())

    __table_args__ = (
        Index("ix_ingestion_events_account_id", "account_id"),
        Index("ix_ingestion_events_source_type", "source_type"),
    )
