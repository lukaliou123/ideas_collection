"""add tag system

Revision ID: a1b2c3d4e5f6
Revises: 
Create Date: 2024-03-21 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # 为已存在的 tags 表添加新列
    op.add_column('tags', sa.Column('normalized_name', sa.String(), nullable=True))
    op.add_column('tags', sa.Column('category_id', sa.Integer(), nullable=True))
    op.add_column('tags', sa.Column('aliases', sa.JSON(), nullable=True))
    
    # 创建索引
    op.create_index(op.f('ix_tags_normalized_name'), 'tags', ['normalized_name'], unique=True)
    
    # 更新现有标签的normalized_name
    op.execute("""
        UPDATE tags 
        SET normalized_name = LOWER(REPLACE(name, ' ', '_'))
    """)
    
    # 将normalized_name设为非空
    op.alter_column('tags', 'normalized_name',
               existing_type=sa.String(),
               nullable=False)
    
    # 注意：product_tags 表已经存在，不需要创建

def downgrade():
    # 删除索引
    op.drop_index(op.f('ix_tags_normalized_name'), table_name='tags')
    
    # 删除添加的列
    op.drop_column('tags', 'aliases')
    op.drop_column('tags', 'category_id')
    op.drop_column('tags', 'normalized_name')
    
    # 删除标签分类表
    op.drop_index(op.f('ix_tag_categories_name'), table_name='tag_categories')
    op.drop_index(op.f('ix_tag_categories_id'), table_name='tag_categories')
    op.drop_table('tag_categories') 