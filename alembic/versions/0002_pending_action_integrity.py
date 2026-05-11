"""add pending action integrity and tenant fields

Revision ID: 0002_pending_action_integrity
Revises: 0001_initial
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa


revision = '0002_pending_action_integrity'
down_revision = '0001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('pending_actions', sa.Column('action_hash', sa.String(length=128), nullable=False, server_default=''))
    op.add_column('pending_actions', sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column('pending_actions', 'expires_at')
    op.drop_column('pending_actions', 'action_hash')
