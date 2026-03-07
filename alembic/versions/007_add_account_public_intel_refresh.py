"""Add last_public_intel_refresh_at to accounts

Revision ID: 007
Revises: 006
Create Date: 2026-03-07
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('accounts', sa.Column(
        'last_public_intel_refresh_at',
        sa.DateTime(timezone=True),
        nullable=True,
    ))


def downgrade() -> None:
    op.drop_column('accounts', 'last_public_intel_refresh_at')
