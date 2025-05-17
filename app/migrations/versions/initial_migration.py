"""initial migration

Revision ID: 001
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'users',
        sa.Column('username', sa.String(50), primary_key=True),
        sa.Column('full_name', sa.String(100)),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('disabled', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    op.create_table(
        'services',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    op.create_table(
        'orders',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('user_id', sa.String(50), sa.ForeignKey('users.username')),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'))
    )

    op.create_table(
        'order_services',
        sa.Column('order_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('orders.id'), primary_key=True),
        sa.Column('service_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('services.id'), primary_key=True)
    )

    op.create_index('idx_users_username', 'users', ['username'])
    op.create_index('idx_users_full_name', 'users', ['full_name'])
    op.create_index('idx_services_name', 'services', ['name'])
    op.create_index('idx_orders_user_id', 'orders', ['user_id'])
    op.create_index('idx_orders_created_at', 'orders', ['created_at'])
    op.create_index('idx_order_services_order_id', 'order_services', ['order_id'])
    op.create_index('idx_order_services_service_id', 'order_services', ['service_id'])

def downgrade():
    op.drop_index('idx_order_services_service_id')
    op.drop_index('idx_order_services_order_id')
    op.drop_index('idx_orders_created_at')
    op.drop_index('idx_orders_user_id')
    op.drop_index('idx_services_name')
    op.drop_index('idx_users_full_name')
    op.drop_index('idx_users_username')

    op.drop_table('order_services')
    op.drop_table('orders')
    op.drop_table('services')
    op.drop_table('users')