"""Add accounts table and link existing reviews

Revision ID: 004
Revises: 003
Create Date: 2026-03-06
"""
from alembic import op
import sqlalchemy as sa

revision = "004"
down_revision = "003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "accounts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("name", sa.String(255), nullable=False, unique=True),
        sa.Column("industry", sa.String(200), nullable=True),
        sa.Column("location", sa.String(255), nullable=True),
        sa.Column("employee_count", sa.Integer(), nullable=True),
        sa.Column("current_mod", sa.Float(), nullable=True),
        sa.Column("vehicle_exposure", sa.String(255), nullable=True),
        sa.Column("policy_expiration", sa.String(20), nullable=True),
        sa.Column("renewal_status", sa.String(50), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add account_id FK to existing tables
    op.add_column("loss_run_reviews", sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True))
    op.add_column("experience_mod_reviews", sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True))
    op.add_column("query_logs", sa.Column("account_id", sa.Integer(), sa.ForeignKey("accounts.id"), nullable=True))


def downgrade() -> None:
    op.drop_column("query_logs", "account_id")
    op.drop_column("experience_mod_reviews", "account_id")
    op.drop_column("loss_run_reviews", "account_id")
    op.drop_table("accounts")
