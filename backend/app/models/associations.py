"""
关联表定义模块
用于定义多对多关系表，避免循环引用
"""
from sqlalchemy import Column, Integer, ForeignKey, Table

from ..db.base_class import Base

# 产品-标签的多对多关系表
product_tag_association = Table(
    "product_tag",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
) 