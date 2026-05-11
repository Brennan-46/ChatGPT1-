"""initial tables

Revision ID: 0001_initial
Revises:
Create Date: 2026-05-11
"""

from alembic import op
import sqlalchemy as sa


revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'agent_runs',
        sa.Column('run_id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=128), nullable=False, server_default='default'),
        sa.Column('status', sa.String(length=64), nullable=False),
        sa.Column('stop_reason', sa.String(length=128), nullable=False),
        sa.Column('trace', sa.Text(), nullable=False, server_default=''),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_table(
        'pending_actions',
        sa.Column('run_id', sa.String(length=64), primary_key=True),
        sa.Column('tenant_id', sa.String(length=128), nullable=False, server_default='default'),
        sa.Column('step_id', sa.String(length=32), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False, server_default='pending'),
    )
    op.create_table(
        'audit_events',
        sa.Column('id', sa.String(length=128), primary_key=True),
        sa.Column('run_id', sa.String(length=64), nullable=False),
        sa.Column('tenant_id', sa.String(length=128), nullable=False, server_default='default'),
        sa.Column('event', sa.String(length=128), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table('audit_events')
    op.drop_table('pending_actions')
    op.drop_table('agent_runs')
