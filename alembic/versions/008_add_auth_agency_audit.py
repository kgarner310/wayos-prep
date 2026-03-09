"""Add agencies, users, audit_events tables and agency_id columns.

Revision ID: 008
Revises: 007
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB


revision = "008"
down_revision = "007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- agencies ---
    op.create_table(
        "agencies",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("agency_name", sa.Text(), nullable=False),
        sa.Column("slug", sa.Text(), nullable=False, unique=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_agencies_slug", "agencies", ["slug"])

    # --- users ---
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("email", sa.Text(), nullable=False, unique=True),
        sa.Column("hashed_password", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("role", sa.Text(), nullable=False, server_default=sa.text("'producer'")),
        sa.Column("agency_id", UUID(as_uuid=True), sa.ForeignKey("agencies.id", ondelete="CASCADE"), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
    op.create_index("ix_users_agency_id", "users", ["agency_id"])

    # --- audit_events ---
    op.create_table(
        "audit_events",
        sa.Column("id", UUID(as_uuid=True), server_default=sa.text("gen_random_uuid()"), primary_key=True),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("user_id", UUID(as_uuid=True), nullable=True),
        sa.Column("agency_id", UUID(as_uuid=True), nullable=True),
        sa.Column("resource_type", sa.Text(), nullable=True),
        sa.Column("resource_id", sa.Text(), nullable=True),
        sa.Column("detail", JSONB(), nullable=True),
        sa.Column("ip_address", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )
    op.create_index("ix_audit_events_event_type", "audit_events", ["event_type"])
    op.create_index("ix_audit_events_user_id", "audit_events", ["user_id"])
    op.create_index("ix_audit_events_agency_id", "audit_events", ["agency_id"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])

    # --- add agency_id to accounts ---
    op.add_column("accounts", sa.Column("agency_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_accounts_agency_id", "accounts", "agencies", ["agency_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_accounts_agency_id", "accounts", ["agency_id"])

    # --- add agency_id to saved_artifacts ---
    op.add_column("saved_artifacts", sa.Column("agency_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_saved_artifacts_agency_id", "saved_artifacts", "agencies", ["agency_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_saved_artifacts_agency_id", "saved_artifacts", ["agency_id"])

    # --- add agency_id to producer_style_preferences ---
    op.add_column("producer_style_preferences", sa.Column("agency_id", UUID(as_uuid=True), nullable=True))
    op.create_foreign_key("fk_producer_style_preferences_agency_id", "producer_style_preferences", "agencies", ["agency_id"], ["id"], ondelete="CASCADE")
    op.create_index("ix_producer_style_preferences_agency_id", "producer_style_preferences", ["agency_id"])


def downgrade() -> None:
    op.drop_index("ix_producer_style_preferences_agency_id", "producer_style_preferences")
    op.drop_constraint("fk_producer_style_preferences_agency_id", "producer_style_preferences", type_="foreignkey")
    op.drop_column("producer_style_preferences", "agency_id")

    op.drop_index("ix_saved_artifacts_agency_id", "saved_artifacts")
    op.drop_constraint("fk_saved_artifacts_agency_id", "saved_artifacts", type_="foreignkey")
    op.drop_column("saved_artifacts", "agency_id")

    op.drop_index("ix_accounts_agency_id", "accounts")
    op.drop_constraint("fk_accounts_agency_id", "accounts", type_="foreignkey")
    op.drop_column("accounts", "agency_id")

    op.drop_table("audit_events")
    op.drop_table("users")
    op.drop_table("agencies")
