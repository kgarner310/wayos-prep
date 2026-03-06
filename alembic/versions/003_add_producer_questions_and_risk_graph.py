"""Add producer_questions, risk_themes, and risk_theme_edges tables

Revision ID: 003
Revises: 002
Create Date: 2026-03-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Producer questions table
    op.create_table(
        'producer_questions',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('category', sa.Text(), nullable=False),
        sa.Column('industry', sa.Text(), nullable=True),
        sa.Column('entity_type', sa.Text(), nullable=False, server_default='public_entity'),
        sa.Column('public_entity_type', sa.Text(), nullable=True),
        sa.Column('department', sa.Text(), nullable=True),
        sa.Column('risk_theme', sa.Text(), nullable=True),
        sa.Column('coverage', JSONB, nullable=True),  # Array of coverage strings
        sa.Column('purpose', sa.Text(), nullable=True),
        sa.Column('follow_up_questions', JSONB, nullable=True),
        sa.Column('importance_score', sa.Numeric(3, 1), server_default='5.0'),
        sa.Column('difficulty_score', sa.Numeric(3, 1), server_default='5.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_producer_questions_category', 'producer_questions', ['category'])
    op.create_index('ix_producer_questions_industry', 'producer_questions', ['industry'])
    op.create_index('ix_producer_questions_department', 'producer_questions', ['department'])
    op.create_index('ix_producer_questions_risk_theme', 'producer_questions', ['risk_theme'])
    op.create_index('ix_producer_questions_entity_type', 'producer_questions', ['entity_type'])
    op.create_index('ix_producer_questions_public_entity_type', 'producer_questions', ['public_entity_type'])

    # Risk themes table (graph nodes)
    op.create_table(
        'risk_themes',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('name', sa.Text(), nullable=False, unique=True),
        sa.Column('node_type', sa.Text(), nullable=False),
        sa.Column('display_label', sa.Text(), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('entity_scope', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_risk_themes_node_type', 'risk_themes', ['node_type'])
    op.create_index('ix_risk_themes_name', 'risk_themes', ['name'])

    # Risk theme edges table (denormalized graph edges)
    op.create_table(
        'risk_theme_edges',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('from_node_type', sa.Text(), nullable=False),
        sa.Column('from_node_value', sa.Text(), nullable=False),
        sa.Column('edge_type', sa.Text(), nullable=False),
        sa.Column('to_node_type', sa.Text(), nullable=False),
        sa.Column('to_node_value', sa.Text(), nullable=False),
        sa.Column('weight', sa.Numeric(5, 2), nullable=False, server_default='1.00'),
        sa.Column('evidence_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint('from_node_type', 'from_node_value', 'edge_type',
                            'to_node_type', 'to_node_value', name='uq_risk_theme_edge'),
    )
    op.create_index('ix_risk_theme_edges_from', 'risk_theme_edges', ['from_node_type', 'from_node_value'])
    op.create_index('ix_risk_theme_edges_to', 'risk_theme_edges', ['to_node_type', 'to_node_value'])
    op.create_index('ix_risk_theme_edges_type', 'risk_theme_edges', ['edge_type'])


def downgrade() -> None:
    op.drop_table('risk_theme_edges')
    op.drop_table('risk_themes')
    op.drop_table('producer_questions')
