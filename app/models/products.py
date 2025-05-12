"""
产品模型模块
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import BaseModel
from app.models.associations import product_tag_association

class Product(Base, BaseModel):
    """产品模型，存储从帖子中提取的结构化产品信息"""
    
    __tablename__ = "products"
    
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, unique=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    problem_solved = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    competitive_advantage = Column(Text, nullable=True)
    potential_competitors = Column(Text, nullable=True)
    business_model = Column(Text, nullable=True)
    concept_image_url = Column(String(1000), nullable=True)  # 产品概念图URL
    
    # 关联关系
    post = relationship("Post", back_populates="product")
    tags = relationship("Tag", secondary=product_tag_association, back_populates="products")
    
    def __repr__(self):
        return f"<Product {self.name}>" 