"""添加标签系统相关表

Revision ID: xxx
Revises: 
Create Date: 2023-10-25

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "6a9e1e8203d0"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # 创建标签分类表
    op.create_table(
        'tag_categories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )
    op.create_index(op.f('ix_tag_categories_id'), 'tag_categories', ['id'], unique=False)
    op.create_index(op.f('ix_tag_categories_name'), 'tag_categories', ['name'], unique=True)

    # 创建标签表
    op.create_table(
        'tags',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('normalized_name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('aliases', sa.JSON(), nullable=True),
        sa.Column('category_id', sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(['category_id'], ['tag_categories.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('normalized_name')
    )
    op.create_index(op.f('ix_tags_id'), 'tags', ['id'], unique=False)
    op.create_index(op.f('ix_tags_name'), 'tags', ['name'], unique=False)
    op.create_index(op.f('ix_tags_normalized_name'), 'tags', ['normalized_name'], unique=True)

    # 创建产品-标签关联表
    op.create_table(
        'product_tag',
        sa.Column('product_id', sa.Integer(), nullable=False),
        sa.Column('tag_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['product_id'], ['products.id'], ),
        sa.ForeignKeyConstraint(['tag_id'], ['tags.id'], ),
        sa.PrimaryKeyConstraint('product_id', 'tag_id')
    )

    # 为产品表添加image_url字段
    op.add_column('products', sa.Column('image_url', sa.String(), nullable=True))


def downgrade():
    # 删除产品表的image_url字段
    op.drop_column('products', 'image_url')
    
    # 删除产品-标签关联表
    op.drop_table('product_tag')
    
    # 删除标签表
    op.drop_index(op.f('ix_tags_normalized_name'), table_name='tags')
    op.drop_index(op.f('ix_tags_name'), table_name='tags')
    op.drop_index(op.f('ix_tags_id'), table_name='tags')
    op.drop_table('tags')
    
    # 删除标签分类表
    op.drop_index(op.f('ix_tag_categories_name'), table_name='tag_categories')
    op.drop_index(op.f('ix_tag_categories_id'), table_name='tag_categories')
    op.drop_table('tag_categories') 