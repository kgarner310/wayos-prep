"""Add session_id to event_log and demo_feedback table.

Revision ID: 009
Revises: 008
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "009"
down_revision = "008"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- add session_id to event_log ---
    op.add_column("event_log", sa.Column("session_id", sa.Text(), nullable=True))
    op.create_index("ix_event_log_session_id", "event_log", ["session_id"])

    # --- demo_feedback ---
    op.create_table(
        "demo_feedback",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("agency_id", UUID(as_uuid=True), nullable=True),
        sa.Column("session_id", sa.Text(), nullable=True),
        sa.Column("account_id", UUID(as_uuid=True), nullable=True),
        sa.Column("would_use_before_meeting", sa.Text(), nullable=True),
        sa.Column("most_useful_part", sa.Text(), nullable=True),
        sa.Column("unclear_or_untrustworthy", sa.Text(), nullable=True),
        sa.Column("what_next", sa.Text(), nullable=True),
        sa.Column("overall_rating", sa.Integer(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_demo_feedback_user_id", "demo_feedback", ["user_id"])
    op.create_index("ix_demo_feedback_created_at", "demo_feedback", ["created_at"])


def downgrade() -> None:
    op.drop_table("demo_feedback")
    op.drop_index("ix_event_log_session_id", "event_log")
    op.drop_column("event_log", "session_id")
