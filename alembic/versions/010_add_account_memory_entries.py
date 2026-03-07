"""Add account_memory_entries table.

Revision ID: 010
Revises: 009
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "010"
down_revision = "009"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "account_memory_entries",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id", sa.Text(), nullable=False),
        sa.Column("agency_id", sa.Text(), nullable=True),
        sa.Column("session_id", sa.Text(), nullable=True),
        sa.Column("industry", sa.Text(), nullable=True),
        sa.Column("entry_type", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("payload_json", JSONB, nullable=True),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_account_memory_account_id", "account_memory_entries", ["account_id"])
    op.create_index("ix_account_memory_agency_id", "account_memory_entries", ["agency_id"])
    op.create_index("ix_account_memory_industry", "account_memory_entries", ["industry"])
    op.create_index("ix_account_memory_entry_type", "account_memory_entries", ["entry_type"])
    op.create_index("ix_account_memory_account_created", "account_memory_entries", ["account_id", "created_at"])
    op.create_index("ix_account_memory_agency_created", "account_memory_entries", ["agency_id", "created_at"])
    op.create_index("ix_account_memory_industry_type", "account_memory_entries", ["industry", "entry_type"])


def downgrade() -> None:
    op.drop_table("account_memory_entries")
