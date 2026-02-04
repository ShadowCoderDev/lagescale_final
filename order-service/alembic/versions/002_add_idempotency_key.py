"""Add idempotency_key to orders table

Revision ID: 002_add_idempotency_key
Revises: 001_initial
Create Date: 2024-01-02
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '002_add_idempotency_key'
down_revision: Union[str, None] = '001_initial'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add idempotency_key column to orders table
    op.add_column('orders', sa.Column('idempotency_key', sa.String(64), nullable=True))
    # Create unique index for idempotency_key
    op.create_index('ix_orders_idempotency_key', 'orders', ['idempotency_key'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_orders_idempotency_key', table_name='orders')
    op.drop_column('orders', 'idempotency_key')

