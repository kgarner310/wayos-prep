"""Initial migration

Revision ID: 001
Revises:
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "industry_risk_profiles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("industry_name", sa.String(255), nullable=False),
        sa.Column("synonyms", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("top_workers_comp_claims", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("commercial_auto_claims", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("general_liability_exposures", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("conversation_prompts", postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column("regional_risk_notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_industry_name", "industry_risk_profiles", ["industry_name"], unique=True)

    op.create_table(
        "query_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("query_type", sa.String(20), nullable=False),
        sa.Column("raw_question", sa.Text(), nullable=True),
        sa.Column("industry_id", sa.Integer(), sa.ForeignKey("industry_risk_profiles.id"), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("mod", sa.Float(), nullable=True),
        sa.Column("vehicle_exposure", sa.String(255), nullable=True),
        sa.Column("brief_json", sa.JSON(), nullable=True),
        sa.Column("brief_text", sa.Text(), nullable=True),
        sa.Column("underwriter_email_text", sa.Text(), nullable=True),
        sa.Column("internal_note_text", sa.Text(), nullable=True),
        sa.Column("llm_used", sa.String(50), nullable=True),
        sa.Column("latency_ms", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "feedbacks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("query_log_id", sa.Integer(), sa.ForeignKey("query_logs.id"), nullable=False),
        sa.Column("helpful_bool", sa.Boolean(), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("feedbacks")
    op.drop_table("query_logs")
    op.drop_index("ix_industry_name", table_name="industry_risk_profiles")
    op.drop_table("industry_risk_profiles")
