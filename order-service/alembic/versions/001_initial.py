"""Create orders tables

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('total_amount', sa.Numeric(10, 2), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PROCESSING', 'PAID', 'FAILED', 'CANCELED', 'SHIPPED', 'DELIVERED', name='orderstatus'), nullable=False),
        sa.Column('payment_id', sa.String(255), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_orders_id', 'orders', ['id'])
    op.create_index('ix_orders_user_id', 'orders', ['user_id'])
    
    # Create order_items table
    op.create_table(
        'order_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('product_id', sa.String(255), nullable=False),
        sa.Column('product_name', sa.String(255), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('unit_price', sa.Numeric(10, 2), nullable=False),
        sa.Column('subtotal', sa.Numeric(10, 2), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_order_items_id', 'order_items', ['id'])


def downgrade() -> None:
    op.drop_index('ix_order_items_id', table_name='order_items')
    op.drop_table('order_items')
    op.drop_index('ix_orders_user_id', table_name='orders')
    op.drop_index('ix_orders_id', table_name='orders')
    op.drop_table('orders')
    op.execute('DROP TYPE orderstatus')
