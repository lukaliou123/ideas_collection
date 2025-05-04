"""
标签模型模块
"""
from sqlalchemy import Column, String, Table, ForeignKey, Integer
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import BaseModel

# 产品与标签的多对多关系表
product_tags = Table(
    "product_tags",
    Base.metadata,
    Column("product_id", Integer, ForeignKey("products.id"), primary_key=True),
    Column("tag_id", Integer, ForeignKey("tags.id"), primary_key=True)
)

class Tag(Base, BaseModel):
    """标签模型，用于对产品进行分类"""
    
    __tablename__ = "tags"
    
    name = Column(String(100), nullable=False, unique=True, index=True)
    
    # 关联关系
    products = relationship("Product", secondary=product_tags, back_populates="tags")
    
    def __repr__(self):
        return f"<Tag {self.name}>" 