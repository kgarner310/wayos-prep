"""MVP: extend accounts/artifacts/outcomes, add account_health and ingestion_events.

Revision ID: 012
Revises: 011
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "012"
down_revision = "011"
branch_labels = None
depends_on = None


def upgrade():
    # --- Extend accounts table ---
    op.add_column("accounts", sa.Column("named_insured", sa.Text(), nullable=True))
    op.add_column("accounts", sa.Column("payroll_estimate", sa.Numeric(14, 2), nullable=True))
    op.add_column("accounts", sa.Column("workers_comp_mod", sa.Numeric(5, 3), nullable=True))
    op.add_column("accounts", sa.Column("current_carriers", JSONB(), nullable=True))
    op.add_column("accounts", sa.Column("claims_summary", JSONB(), nullable=True))
    op.add_column("accounts", sa.Column("extracted_text", sa.Text(), nullable=True))
    op.create_index("ix_accounts_named_insured", "accounts", ["named_insured"])

    # --- Extend saved_artifacts table ---
    op.add_column("saved_artifacts", sa.Column("status", sa.Text(), server_default="ready", nullable=False))
    op.add_column("saved_artifacts", sa.Column("confidence", sa.Numeric(4, 3), nullable=True))
    op.add_column("saved_artifacts", sa.Column("model_name", sa.Text(), nullable=True))
    op.create_index("ix_saved_artifacts_status", "saved_artifacts", ["status"])

    # --- Extend deal_outcomes table ---
    op.add_column("deal_outcomes", sa.Column("competitor", sa.Text(), nullable=True))
    op.add_column("deal_outcomes", sa.Column("notes", sa.Text(), nullable=True))

    # --- Create account_health table ---
    op.create_table(
        "account_health",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("overall_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("coverage_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("workers_comp_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("carrier_fit_score", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0.0"),
        sa.Column("top_issues_json", JSONB(), nullable=True),
        sa.Column("duty_to_advise_alert_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_account_health_account_id", "account_health", ["account_id"])

    # --- Create ingestion_events table ---
    op.create_table(
        "ingestion_events",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("account_id", UUID(as_uuid=True), sa.ForeignKey("accounts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("source_type", sa.Text(), nullable=False),
        sa.Column("filename", sa.Text(), nullable=True),
        sa.Column("raw_text", sa.Text(), nullable=True),
        sa.Column("extraction_json", JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_ingestion_events_account_id", "ingestion_events", ["account_id"])
    op.create_index("ix_ingestion_events_source_type", "ingestion_events", ["source_type"])


def downgrade():
    op.drop_table("ingestion_events")
    op.drop_table("account_health")

    op.drop_column("deal_outcomes", "notes")
    op.drop_column("deal_outcomes", "competitor")

    op.drop_index("ix_saved_artifacts_status", table_name="saved_artifacts")
    op.drop_column("saved_artifacts", "model_name")
    op.drop_column("saved_artifacts", "confidence")
    op.drop_column("saved_artifacts", "status")

    op.drop_index("ix_accounts_named_insured", table_name="accounts")
    op.drop_column("accounts", "extracted_text")
    op.drop_column("accounts", "claims_summary")
    op.drop_column("accounts", "current_carriers")
    op.drop_column("accounts", "workers_comp_mod")
    op.drop_column("accounts", "payroll_estimate")
    op.drop_column("accounts", "named_insured")
