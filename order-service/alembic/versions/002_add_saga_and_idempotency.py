"""Add saga fields and idempotency_key to order models

Revision ID: 002_saga_and_idempotency
Revises: 001_initial
Create Date: 2026-02-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_saga_and_idempotency'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add idempotency_key column to orders table
    op.add_column('orders', sa.Column('idempotency_key', sa.String(64), nullable=True))
    op.create_index('ix_orders_idempotency_key', 'orders', ['idempotency_key'], unique=True)
    
    # Add failure_reason to orders (for Saga pattern)
    op.add_column('orders', sa.Column('failure_reason', sa.Text(), nullable=True))
    
    # Add reservation_id to order_items (for Saga pattern)
    op.add_column('order_items', sa.Column('reservation_id', sa.String(64), nullable=True))


def downgrade() -> None:
    op.drop_column('order_items', 'reservation_id')
    op.drop_column('orders', 'failure_reason')
    op.drop_index('ix_orders_idempotency_key', table_name='orders')
    op.drop_column('orders', 'idempotency_key')
