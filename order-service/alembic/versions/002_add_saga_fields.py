"""Add saga fields to order models

Revision ID: 002_saga_fields
Revises: 001
Create Date: 2026-02-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '002_saga_fields'
down_revision = None  # Update this to your last migration
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add failure_reason to orders
    op.add_column('orders', sa.Column('failure_reason', sa.Text(), nullable=True))
    
    # Add reservation_id to order_items
    op.add_column('order_items', sa.Column('reservation_id', sa.String(64), nullable=True))
    
    # Add RESERVED to OrderStatus enum (for PostgreSQL native enum)
    # op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'RESERVED' AFTER 'PENDING'")


def downgrade() -> None:
    op.drop_column('order_items', 'reservation_id')
    op.drop_column('orders', 'failure_reason')
