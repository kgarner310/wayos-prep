"""Add accounts, saved artifacts, and producer style preferences

Revision ID: 006
Revises: 005
Create Date: 2026-03-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'accounts',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('account_name', sa.Text(), nullable=False),
        sa.Column('industry', sa.Text(), nullable=True),
        sa.Column('state', sa.Text(), nullable=True),
        sa.Column('employee_count', sa.Integer(), nullable=True),
        sa.Column('annual_revenue', sa.Numeric(14, 2), nullable=True),
        sa.Column('vehicle_count', sa.Integer(), nullable=True),
        sa.Column('uses_subcontractors', sa.Boolean(), server_default=sa.text('false'), nullable=True),
        sa.Column('current_coverages', JSONB, nullable=True),
        sa.Column('website_url', sa.Text(), nullable=True),
        sa.Column('social_urls', JSONB, nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_accounts_account_name', 'accounts', ['account_name'])
    op.create_index('ix_accounts_industry', 'accounts', ['industry'])
    op.create_index('ix_accounts_state', 'accounts', ['state'])
    op.create_index('ix_accounts_created_at', 'accounts', ['created_at'])

    op.create_table(
        'saved_artifacts',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('account_id', UUID(as_uuid=True), sa.ForeignKey('accounts.id', ondelete='CASCADE'), nullable=True),
        sa.Column('artifact_type', sa.Text(), nullable=False),
        sa.Column('artifact_subtype', sa.Text(), nullable=True),
        sa.Column('title', sa.Text(), nullable=True),
        sa.Column('content_json', JSONB, nullable=False),
        sa.Column('rendered_text', sa.Text(), nullable=True),
        sa.Column('created_by_user_id', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_saved_artifacts_account_id', 'saved_artifacts', ['account_id'])
    op.create_index('ix_saved_artifacts_artifact_type', 'saved_artifacts', ['artifact_type'])
    op.create_index('ix_saved_artifacts_created_at', 'saved_artifacts', ['created_at'])

    op.create_table(
        'producer_style_preferences',
        sa.Column('id', UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), primary_key=True),
        sa.Column('producer_id', sa.Text(), nullable=False, unique=True),
        sa.Column('audience', sa.Text(), server_default='underwriter', nullable=True),
        sa.Column('default_posture', sa.Text(), server_default='balanced', nullable=True),
        sa.Column('directness', sa.Text(), nullable=True),
        sa.Column('verbosity', sa.Text(), nullable=True),
        sa.Column('warmth', sa.Text(), nullable=True),
        sa.Column('confidence_style', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index('ix_producer_style_preferences_producer_id', 'producer_style_preferences', ['producer_id'])


def downgrade() -> None:
    op.drop_table('producer_style_preferences')
    op.drop_table('saved_artifacts')
    op.drop_table('accounts')
