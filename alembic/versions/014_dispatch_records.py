"""Add dispatch_records table for PIT dispatch tracking.

Revision ID: 014
Revises: 013
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "014"
down_revision = "013"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "dispatch_records",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("triage_request_id", UUID(as_uuid=True), sa.ForeignKey("service_triage_requests.id", ondelete="SET NULL"), nullable=True),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("agency_id", UUID(as_uuid=True), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=True),
        # What was sent
        sa.Column("recipient_type", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text(), nullable=False),
        sa.Column("subject", sa.Text(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        # Who dispatched it
        sa.Column("dispatched_by_user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # Status
        sa.Column("status", sa.Text(), nullable=False, server_default="logged"),
        # Timestamps
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_dispatch_records_triage_request_id", "dispatch_records", ["triage_request_id"])
    op.create_index("ix_dispatch_records_account_id", "dispatch_records", ["account_id"])
    op.create_index("ix_dispatch_records_agency_id", "dispatch_records", ["agency_id"])
    op.create_index("ix_dispatch_records_dispatched_at", "dispatch_records", ["dispatched_at"])
    op.create_index("ix_dispatch_records_recipient_type", "dispatch_records", ["recipient_type"])


def downgrade():
    op.drop_table("dispatch_records")
