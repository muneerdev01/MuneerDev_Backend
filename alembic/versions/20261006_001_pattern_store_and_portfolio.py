"""create pattern store and portfolio tables

Revision ID: 20261006_001
Revises: (articles_table_revision_id)
Create Date: 2026-10-06 00:20:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '20261006_001'
down_revision: Union[str, None] = '001_initial_articles'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# Define PostgreSQL Native ENUM types
product_category_enum = postgresql.ENUM(
    'PATTERNS', 'TEMPLATES', 'EBOOKS', 
    name='product_category_enum', 
    create_type=False
)
order_status_enum = postgresql.ENUM(
    'PENDING', 'PAID', 'FAILED', 
    name='order_status_enum', 
    create_type=False
)

def upgrade() -> None:
    # 1. Create native ENUM types in PostgreSQL
    op.execute("CREATE TYPE product_category_enum AS ENUM ('PATTERNS', 'TEMPLATES', 'EBOOKS')")
    op.execute("CREATE TYPE order_status_enum AS ENUM ('PENDING', 'PAID', 'FAILED')")

    # 2. Create projects table
    op.create_table(
        'projects',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=250), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('tech_stack', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('images', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('github_url', sa.String(length=500), nullable=True),
        sa.Column('live_url', sa.String(length=500), nullable=True),
        sa.Column('featured', sa.Boolean(), nullable=False, server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_projects')),
        sa.UniqueConstraint('slug', name=op.f('uq_projects_slug'))
    )
    op.create_index(op.f('ix_projects_slug'), 'projects', ['slug'], unique=True)

    # 3. Create products table
    op.create_table(
        'products',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('slug', sa.String(length=250), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('category', product_category_enum, nullable=False),
        sa.Column('preview_images', sa.JSON(), nullable=False, server_default='[]'),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('sales_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_products')),
        sa.UniqueConstraint('slug', name=op.f('uq_products_slug'))
    )
    op.create_index(op.f('ix_products_slug'), 'products', ['slug'], unique=True)
    op.create_index(op.f('ix_products_is_active'), 'products', ['is_active'])
    op.create_index(op.f('ix_products_category'), 'products', ['category'])

    # 4. Create orders table
    op.create_table(
        'orders',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('buyer_email', sa.String(length=255), nullable=False),
        sa.Column('stripe_session_id', sa.String(length=255), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('status', order_status_enum, nullable=False, server_default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ondelete='CASCADE', name=op.f('fk_orders_product_id_products')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_orders')),
        sa.UniqueConstraint('stripe_session_id', name=op.f('uq_orders_stripe_session_id'))
    )
    op.create_index(op.f('ix_orders_product_id'), 'orders', ['product_id'])
    op.create_index(op.f('ix_orders_buyer_email'), 'orders', ['buyer_email'])
    op.create_index(op.f('ix_orders_stripe_session_id'), 'orders', ['stripe_session_id'], unique=True)
    op.create_index(op.f('ix_orders_status'), 'orders', ['status'])

    # 5. Create download_tokens table
    op.create_table(
        'download_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('order_id', sa.Integer(), nullable=False),
        sa.Column('token', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['order_id'], ['orders.id'], ondelete='CASCADE', name=op.f('fk_download_tokens_order_id_orders')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_download_tokens')),
        sa.UniqueConstraint('order_id', name=op.f('uq_download_tokens_order_id')),
        sa.UniqueConstraint('token', name=op.f('uq_download_tokens_token'))
    )
    op.create_index(op.f('ix_download_tokens_order_id'), 'download_tokens', ['order_id'], unique=True)
    op.create_index(op.f('ix_download_tokens_token'), 'download_tokens', ['token'], unique=True)

def downgrade() -> None:
    op.drop_table('download_tokens')
    op.drop_table('orders')
    op.drop_table('products')
    op.drop_table('projects')
    op.execute("DROP TYPE IF EXISTS order_status_enum")
    op.execute("DROP TYPE IF EXISTS product_category_enum")
