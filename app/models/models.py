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
