"""Add state_profiles table

Revision ID: 002
Revises: 001
Create Date: 2026-03-06
"""
from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "state_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("state_code", sa.String(2), nullable=False),
        sa.Column("state_name", sa.String(100), nullable=False),
        sa.Column("wc_monopolistic", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("wc_competitive", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("wc_notes", sa.Text(), nullable=True),
        sa.Column("regulatory_notes", sa.Text(), nullable=True),
        sa.Column("tort_environment", sa.String(50), nullable=True),
        sa.Column("cat_exposures", sa.JSON(), nullable=True),
        sa.Column("compliance_items", sa.JSON(), nullable=True),
        sa.Column("market_notes", sa.Text(), nullable=True),
        sa.Column("top_industries", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_state_code", "state_profiles", ["state_code"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_state_code", table_name="state_profiles")
    op.drop_table("state_profiles")
