"""Initial schema for WAYOS PREP

Revision ID: 001
Revises:
Create Date: 2026-03-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Enable extensions
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    # sources
    op.create_table(
        'sources',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('title', sa.Text(), nullable=False),
        sa.Column('publisher', sa.Text()),
        sa.Column('author', sa.Text()),
        sa.Column('url', sa.Text()),
        sa.Column('canonical_url', sa.Text()),
        sa.Column('published_at', sa.DateTime(timezone=True)),
        sa.Column('retrieved_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('jurisdiction', sa.Text()),
        sa.Column('jurisdiction_state', sa.Text()),
        sa.Column('country_code', sa.Text(), server_default='US'),
        sa.Column('license_type', sa.Text(), nullable=False, server_default='public'),
        sa.Column('authority_level', sa.Text(), nullable=False, server_default='trade'),
        sa.Column('authority_score', sa.Numeric(4, 2), nullable=False, server_default='5.00'),
        sa.Column('freshness_score', sa.Numeric(4, 2), nullable=False, server_default='5.00'),
        sa.Column('document_hash', sa.Text()),
        sa.Column('raw_text', sa.Text()),
        sa.Column('raw_text_path', sa.Text()),
        sa.Column('status', sa.Text(), nullable=False, server_default='new'),
        sa.Column('language_code', sa.Text(), server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_sources_source_type', 'sources', ['source_type'])
    op.create_index('ix_sources_jurisdiction_state', 'sources', ['jurisdiction_state'])
    op.create_index('ix_sources_authority_level', 'sources', ['authority_level'])
    op.create_index('ix_sources_published_at', 'sources', ['published_at'])
    op.create_index('ix_sources_status', 'sources', ['status'])

    # source_tags
    op.create_table(
        'source_tags',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag_type', sa.Text(), nullable=False),
        sa.Column('tag_value', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Numeric(4, 2), nullable=False, server_default='1.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_source_tags_source_id', 'source_tags', ['source_id'])
    op.create_index('ix_source_tags_tag_type_value', 'source_tags', ['tag_type', 'tag_value'])

    # source_chunks
    op.create_table(
        'source_chunks',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('heading', sa.Text()),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('text_summary', sa.Text()),
        sa.Column('token_count', sa.Integer()),
        sa.Column('char_count', sa.Integer()),
        sa.Column('chunk_hash', sa.Text()),
        sa.Column('jurisdiction', sa.Text()),
        sa.Column('jurisdiction_state', sa.Text()),
        sa.Column('authority_score', sa.Numeric(4, 2), nullable=False, server_default='5.00'),
        sa.Column('freshness_score', sa.Numeric(4, 2), nullable=False, server_default='5.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('source_id', 'chunk_index', name='uq_source_chunk_index'),
    )
    op.create_index('ix_source_chunks_source_id', 'source_chunks', ['source_id'])
    op.create_index('ix_source_chunks_jurisdiction_state', 'source_chunks', ['jurisdiction_state'])

    # chunk_tags
    op.create_table(
        'chunk_tags',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('chunk_id', UUID(as_uuid=True), sa.ForeignKey('source_chunks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tag_type', sa.Text(), nullable=False),
        sa.Column('tag_value', sa.Text(), nullable=False),
        sa.Column('confidence', sa.Numeric(4, 2), nullable=False, server_default='1.00'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_chunk_tags_chunk_id', 'chunk_tags', ['chunk_id'])
    op.create_index('ix_chunk_tags_tag_type_value', 'chunk_tags', ['tag_type', 'tag_value'])

    # chunk_embeddings
    op.create_table(
        'chunk_embeddings',
        sa.Column('chunk_id', UUID(as_uuid=True), sa.ForeignKey('source_chunks.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('embedding_model', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    # Add vector column separately (alembic doesn't handle custom types well)
    op.execute("ALTER TABLE chunk_embeddings ADD COLUMN embedding vector(1536)")
    op.execute("CREATE INDEX ix_chunk_embeddings_cosine ON chunk_embeddings USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)")

    # queries
    op.create_table(
        'queries',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('user_id', sa.Text()),
        sa.Column('session_id', sa.Text()),
        sa.Column('product_surface', sa.Text(), nullable=False, server_default='prep'),
        sa.Column('raw_query', sa.Text(), nullable=False),
        sa.Column('normalized_query', sa.Text()),
        sa.Column('requested_industry', sa.Text()),
        sa.Column('requested_state', sa.Text()),
        sa.Column('employee_count', sa.Integer()),
        sa.Column('current_mod', sa.Numeric(6, 3)),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # retrieval_runs
    op.create_table(
        'retrieval_runs',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('query_id', UUID(as_uuid=True), sa.ForeignKey('queries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('embedding_model', sa.Text()),
        sa.Column('reranker_name', sa.Text()),
        sa.Column('filters_json', JSONB()),
        sa.Column('candidate_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('selected_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('status', sa.Text(), nullable=False, server_default='complete'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # retrieval_results
    op.create_table(
        'retrieval_results',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('retrieval_run_id', UUID(as_uuid=True), sa.ForeignKey('retrieval_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', UUID(as_uuid=True), sa.ForeignKey('source_chunks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rank_position', sa.Integer(), nullable=False),
        sa.Column('similarity_score', sa.Numeric(8, 6)),
        sa.Column('rerank_score', sa.Numeric(8, 6)),
        sa.Column('selected', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_retrieval_results_run_id', 'retrieval_results', ['retrieval_run_id'])
    op.create_index('ix_retrieval_results_chunk_id', 'retrieval_results', ['chunk_id'])

    # generated_briefs
    op.create_table(
        'generated_briefs',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('query_id', UUID(as_uuid=True), sa.ForeignKey('queries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('retrieval_run_id', UUID(as_uuid=True), sa.ForeignKey('retrieval_runs.id', ondelete='SET NULL')),
        sa.Column('model_name', sa.Text(), nullable=False),
        sa.Column('brief_json', JSONB(), nullable=False),
        sa.Column('rendered_markdown', sa.Text()),
        sa.Column('quality_status', sa.Text(), nullable=False, server_default='unreviewed'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # brief_sources
    op.create_table(
        'brief_sources',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('brief_id', UUID(as_uuid=True), sa.ForeignKey('generated_briefs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_id', UUID(as_uuid=True), sa.ForeignKey('sources.id', ondelete='CASCADE'), nullable=False),
        sa.Column('chunk_id', UUID(as_uuid=True), sa.ForeignKey('source_chunks.id', ondelete='SET NULL')),
        sa.Column('citation_label', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    # feedback_events
    op.create_table(
        'feedback_events',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('brief_id', UUID(as_uuid=True), sa.ForeignKey('generated_briefs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('query_id', UUID(as_uuid=True), sa.ForeignKey('queries.id', ondelete='CASCADE'), nullable=False),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('event_value', sa.Text()),
        sa.Column('event_json', JSONB()),
        sa.Column('user_id', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table('feedback_events')
    op.drop_table('brief_sources')
    op.drop_table('generated_briefs')
    op.drop_table('retrieval_results')
    op.drop_table('retrieval_runs')
    op.drop_table('queries')
    op.drop_table('chunk_embeddings')
    op.drop_table('chunk_tags')
    op.drop_table('source_chunks')
    op.drop_table('source_tags')
    op.drop_table('sources')
