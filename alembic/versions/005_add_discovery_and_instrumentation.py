"""Add discovery outcomes and event log tables

Revision ID: 005
Revises: 004
Create Date: 2026-03-06
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'discovery_outcomes',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('industry', sa.Text(), nullable=False),
        sa.Column('state', sa.Text(), nullable=False),
        sa.Column('account_stage', sa.Text(), nullable=True),
        sa.Column('source_type', sa.Text(), nullable=False),
        sa.Column('source_key', sa.Text(), nullable=False),
        sa.Column('exposure_found', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('exposure_type', sa.Text(), nullable=True),
        sa.Column('coverage_added', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_discovery_outcomes_industry', 'discovery_outcomes', ['industry'])
    op.create_index('ix_discovery_outcomes_state', 'discovery_outcomes', ['state'])
    op.create_index('ix_discovery_outcomes_source_type', 'discovery_outcomes', ['source_type'])
    op.create_index('ix_discovery_outcomes_created_at', 'discovery_outcomes', ['created_at'])

    op.create_table(
        'event_log',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('event_type', sa.Text(), nullable=False),
        sa.Column('event_payload', JSONB, nullable=True),
        sa.Column('user_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_event_log_event_type', 'event_log', ['event_type'])
    op.create_index('ix_event_log_created_at', 'event_log', ['created_at'])


def downgrade() -> None:
    op.drop_table('event_log')
    op.drop_table('discovery_outcomes')
