"""Add risk scoring tables

Revision ID: 004
Revises: 003
Create Date: 2026-03-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'risk_score_runs',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('query_id', UUID(as_uuid=True), sa.ForeignKey('queries.id', ondelete='CASCADE'), nullable=True),
        sa.Column('brief_id', UUID(as_uuid=True), sa.ForeignKey('generated_briefs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('scoring_version', sa.Text(), nullable=False),
        sa.Column('overall_risk_score', sa.Numeric(6, 2), nullable=False),
        sa.Column('risk_band', sa.Text(), nullable=False),
        sa.Column('confidence_score', sa.Numeric(6, 2), nullable=False),
        sa.Column('score_json', JSONB, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_risk_score_runs_query_id', 'risk_score_runs', ['query_id'])
    op.create_index('ix_risk_score_runs_brief_id', 'risk_score_runs', ['brief_id'])

    op.create_table(
        'risk_score_components',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('risk_score_run_id', UUID(as_uuid=True), sa.ForeignKey('risk_score_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('component_type', sa.Text(), nullable=False),
        sa.Column('component_key', sa.Text(), nullable=False),
        sa.Column('component_label', sa.Text(), nullable=True),
        sa.Column('raw_value', sa.Numeric(8, 3), nullable=True),
        sa.Column('weighted_value', sa.Numeric(8, 3), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_risk_score_components_run_id', 'risk_score_components', ['risk_score_run_id'])
    op.create_index('ix_risk_score_components_type', 'risk_score_components', ['component_type'])

    op.create_table(
        'coverage_gap_alerts',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('risk_score_run_id', UUID(as_uuid=True), sa.ForeignKey('risk_score_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('risk_theme', sa.Text(), nullable=False),
        sa.Column('suggested_coverage', sa.Text(), nullable=False),
        sa.Column('alert_severity', sa.Text(), nullable=False),
        sa.Column('alert_reason', sa.Text(), nullable=False),
        sa.Column('supporting_node_json', JSONB, nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_coverage_gap_alerts_run_id', 'coverage_gap_alerts', ['risk_score_run_id'])

    op.create_table(
        'missing_information_alerts',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('risk_score_run_id', UUID(as_uuid=True), sa.ForeignKey('risk_score_runs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('missing_field', sa.Text(), nullable=False),
        sa.Column('alert_severity', sa.Text(), nullable=False),
        sa.Column('alert_reason', sa.Text(), nullable=False),
        sa.Column('recommended_question', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_missing_information_alerts_run_id', 'missing_information_alerts', ['risk_score_run_id'])


def downgrade() -> None:
    op.drop_table('missing_information_alerts')
    op.drop_table('coverage_gap_alerts')
    op.drop_table('risk_score_components')
    op.drop_table('risk_score_runs')
