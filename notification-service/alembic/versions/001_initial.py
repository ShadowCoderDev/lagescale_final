"""Create notification_logs table

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
        'notification_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('notification_type', sa.Enum('email', 'sms', 'push', name='notificationtype'), nullable=False),
        sa.Column('recipient', sa.String(255), nullable=False),
        sa.Column('subject', sa.String(255), nullable=True),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('event_type', sa.String(50), nullable=True),
        sa.Column('order_id', sa.Integer(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('status', sa.Enum('pending', 'sent', 'failed', name='notificationstatus'), nullable=True),
        sa.Column('error_message', sa.String(500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_notification_logs_order_id', 'notification_logs', ['order_id'])
    op.create_index('ix_notification_logs_user_id', 'notification_logs', ['user_id'])


def downgrade() -> None:
    op.drop_index('ix_notification_logs_user_id', table_name='notification_logs')
    op.drop_index('ix_notification_logs_order_id', table_name='notification_logs')
    op.drop_table('notification_logs')
    op.execute('DROP TYPE notificationtype')
    op.execute('DROP TYPE notificationstatus')
