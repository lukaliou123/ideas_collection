"""add concept_image_url to products table

Revision ID: bbef0ff57489
Revises: 6a9e1e8203d0
Create Date: 2025-05-12 17:55:12.726268

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'bbef0ff57489'
down_revision = '6a9e1e8203d0'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('products', sa.Column('concept_image_url', sa.String(1000), nullable=True))


def downgrade():
    op.drop_column('products', 'concept_image_url') 