"""Add loss_run_reviews and experience_mod_reviews tables

Revision ID: 003
Revises: 002
Create Date: 2026-03-06
"""
from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "loss_run_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("policy_period_start", sa.String(20), nullable=True),
        sa.Column("policy_period_end", sa.String(20), nullable=True),
        sa.Column("industry_id", sa.Integer(), sa.ForeignKey("industry_risk_profiles.id"), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("line_entries", sa.JSON(), nullable=True),
        sa.Column("analysis_json", sa.JSON(), nullable=True),
        sa.Column("analysis_text", sa.Text(), nullable=True),
        sa.Column("talking_points", sa.Text(), nullable=True),
        sa.Column("total_incurred", sa.Float(), nullable=True),
        sa.Column("total_claims", sa.Integer(), nullable=True),
        sa.Column("loss_ratio", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "experience_mod_reviews",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("account_name", sa.String(255), nullable=False),
        sa.Column("state_code", sa.String(2), nullable=True),
        sa.Column("effective_date", sa.String(20), nullable=True),
        sa.Column("current_mod", sa.Float(), nullable=True),
        sa.Column("prior_mod", sa.Float(), nullable=True),
        sa.Column("expected_losses", sa.Float(), nullable=True),
        sa.Column("actual_primary_losses", sa.Float(), nullable=True),
        sa.Column("actual_excess_losses", sa.Float(), nullable=True),
        sa.Column("total_payroll", sa.Float(), nullable=True),
        sa.Column("class_code_entries", sa.JSON(), nullable=True),
        sa.Column("mod_claims", sa.JSON(), nullable=True),
        sa.Column("analysis_json", sa.JSON(), nullable=True),
        sa.Column("analysis_text", sa.Text(), nullable=True),
        sa.Column("talking_points", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("experience_mod_reviews")
    op.drop_table("loss_run_reviews")
