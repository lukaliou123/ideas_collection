from sqlalchemy import Column, Integer, ForeignKey, Table
from backend.app.db.base_class import Base

# 产品-标签关联表
product_tags = Table(
    'product_tags',
    Base.metadata,
    Column('product_id', Integer, ForeignKey('products.id')),
    Column('tag_id', Integer, ForeignKey('tags.id'))
) 