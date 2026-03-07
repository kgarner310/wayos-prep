"""Add deal_outcomes and account_events tables.

Revision ID: 011
Revises: 010
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID


revision = "011"
down_revision = "010"
branch_labels = None
depends_on = None


def upgrade():
    # --- deal_outcomes ---
    op.create_table(
        "deal_outcomes",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id", sa.Text(), nullable=False),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("state", sa.Text(), nullable=True),
        sa.Column("carrier", sa.Text(), nullable=True),
        sa.Column("premium", sa.Numeric(14, 2), nullable=True),
        sa.Column("outcome", sa.Text(), nullable=False),
        sa.Column("outcome_reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_deal_outcomes_account_id", "deal_outcomes", ["account_id"])
    op.create_index("ix_deal_outcomes_industry", "deal_outcomes", ["industry"])
    op.create_index("ix_deal_outcomes_state", "deal_outcomes", ["state"])
    op.create_index("ix_deal_outcomes_carrier", "deal_outcomes", ["carrier"])
    op.create_index("ix_deal_outcomes_outcome", "deal_outcomes", ["outcome"])
    op.create_index("ix_deal_outcomes_industry_carrier", "deal_outcomes", ["industry", "carrier"])
    op.create_index("ix_deal_outcomes_industry_outcome", "deal_outcomes", ["industry", "outcome"])

    # --- account_events ---
    op.create_table(
        "account_events",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_account_events_account_id", "account_events", ["account_id"])
    op.create_index("ix_account_events_event_type", "account_events", ["event_type"])
    op.create_index("ix_account_events_account_created", "account_events", ["account_id", "created_at"])


def downgrade():
    op.drop_table("account_events")
    op.drop_table("deal_outcomes")
