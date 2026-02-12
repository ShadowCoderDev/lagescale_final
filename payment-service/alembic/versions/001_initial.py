"""Create payments table

Revision ID: 001_initial
Revises:
Create Date: 2026-02-05
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('transaction_id', sa.String(36), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', sa.Enum('success', 'failed', 'pending', 'refunded', name='paymentstatus'), nullable=False),
        sa.Column('message', sa.String(255), nullable=True),
        sa.Column('idempotency_key', sa.String(64), nullable=True),
        sa.Column('original_transaction_id', sa.String(36), nullable=True),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_payments_id', 'payments', ['id'])
    op.create_index('ix_payments_transaction_id', 'payments', ['transaction_id'], unique=True)
    op.create_index('ix_payments_order_id', 'payments', ['order_id'])
    op.create_index('ix_payments_user_id', 'payments', ['user_id'])
    op.create_index('ix_payments_idempotency_key', 'payments', ['idempotency_key'], unique=True)
    op.create_index('ix_payments_original_transaction_id', 'payments', ['original_transaction_id'])


def downgrade() -> None:
    op.drop_index('ix_payments_original_transaction_id', table_name='payments')
    op.drop_index('ix_payments_idempotency_key', table_name='payments')
    op.drop_index('ix_payments_user_id', table_name='payments')
    op.drop_index('ix_payments_order_id', table_name='payments')
    op.drop_index('ix_payments_transaction_id', table_name='payments')
    op.drop_index('ix_payments_id', table_name='payments')
    op.drop_table('payments')
    op.execute('DROP TYPE paymentstatus')
