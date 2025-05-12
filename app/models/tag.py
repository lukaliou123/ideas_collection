from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship, declared_attr

from ..core.database import Base
from .associations import product_tag_association
from .base import BaseModel


class TagCategory(Base, BaseModel):
    """标签分类模型"""
    __tablename__ = "tag_categories"
    
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # 反向关系
    tags = relationship("Tag", back_populates="category")
    
    def __repr__(self):
        return f"<TagCategory {self.name}>"


class Tag(Base, BaseModel):
    """标签模型"""
    __tablename__ = "tags"
    
    name = Column(String, index=True, nullable=False)
    normalized_name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    aliases = Column(JSON, nullable=True, default=list)
    
    # 外键
    category_id = Column(Integer, ForeignKey("tag_categories.id"), nullable=True)
    
    # 关系
    category = relationship("TagCategory", back_populates="tags")
    
    # 仅定义关系名称，实际关系在_decl_class_registry中设置后定义
    @declared_attr
    def products(cls):
        return relationship(
            "Product",
            secondary=product_tag_association,
            back_populates="tags"
        )
    
    def __repr__(self):
        return f"<Tag {self.name}>" 