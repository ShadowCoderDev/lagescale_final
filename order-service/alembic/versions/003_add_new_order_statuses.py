"""Add RESERVED and REFUNDED order statuses

Revision ID: 003_add_new_order_statuses
Revises: 002_saga_and_idempotency
Create Date: 2026-02-06

This migration adds the RESERVED and REFUNDED values to the PostgreSQL
orderstatus enum type. These are needed for the Saga pattern:
  - RESERVED: Stock reserved, awaiting payment
  - REFUNDED: Order cancelled after payment, money returned
"""
from typing import Sequence, Union
from alembic import op

revision: str = '003_add_new_order_statuses'
down_revision: str = '002_saga_and_idempotency'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new enum values to the existing orderstatus type
    # PostgreSQL requires ALTER TYPE ... ADD VALUE for enum modifications
    # These cannot run inside a transaction, so we use autocommit
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'RESERVED' AFTER 'PENDING'")
    op.execute("ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS 'REFUNDED' AFTER 'CANCELED'")


def downgrade() -> None:
    # PostgreSQL does not support removing enum values directly.
    # To rollback, you would need to:
    # 1. Create a new enum type without RESERVED/REFUNDED
    # 2. Update the column to use the new type
    # 3. Drop the old type
    # This is intentionally left as a no-op to avoid data loss.
    pass
