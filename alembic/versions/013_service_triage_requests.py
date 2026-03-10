"""Add service_triage_requests table for the Service Triage Inbox feature.

Revision ID: 013
Revises: 012
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "013"
down_revision = "012"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "service_triage_requests",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agency_id", UUID(as_uuid=True), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=True),
        sa.Column("created_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # Input
        sa.Column("input_type", sa.Text(), nullable=False, server_default="text"),
        sa.Column("input_text", sa.Text(), nullable=False),
        sa.Column("input_filename", sa.Text(), nullable=True),
        sa.Column("input_extracted_text", sa.Text(), nullable=True),
        # Triage results
        sa.Column("status", sa.Text(), nullable=False, server_default="pending"),
        sa.Column("request_type", sa.Text(), nullable=True),
        sa.Column("urgency", sa.Text(), nullable=True),
        sa.Column("summary", sa.Text(), nullable=True),
        # Drafted messages
        sa.Column("draft_insured", JSONB(), nullable=True),
        sa.Column("draft_carrier", JSONB(), nullable=True),
        sa.Column("draft_ams_note", JSONB(), nullable=True),
        # Approval
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("approved_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        # AI metadata
        sa.Column("confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("model_name", sa.Text(), nullable=True),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_service_triage_account_id", "service_triage_requests", ["account_id"])
    op.create_index("ix_service_triage_agency_id", "service_triage_requests", ["agency_id"])
    op.create_index("ix_service_triage_status", "service_triage_requests", ["status"])
    op.create_index("ix_service_triage_created_at", "service_triage_requests", ["created_at"])
    op.create_index("ix_service_triage_urgency", "service_triage_requests", ["urgency"])


def downgrade():
    op.drop_table("service_triage_requests")
