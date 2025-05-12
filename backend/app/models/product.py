"""
产品模型模块
"""
from sqlalchemy import Column, String, Integer, Text, ForeignKey
from sqlalchemy.orm import relationship, declared_attr

from ..db.base_class import Base
from .associations import product_tag_association

class Product(Base):
    """产品模型，存储结构化产品信息"""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False, unique=True)
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text, nullable=True)
    problem_solved = Column(Text, nullable=True)
    target_audience = Column(Text, nullable=True)
    competitive_advantage = Column(Text, nullable=True)
    potential_competitors = Column(Text, nullable=True)
    business_model = Column(Text, nullable=True)
    image_url = Column(String, nullable=True)
    
    # 关联关系
    post = relationship("Post", back_populates="product")
    
    @declared_attr
    def tags(cls):
        return relationship(
            "Tag",
            secondary=product_tag_association,
            back_populates="products"
        )
    
    def __repr__(self):
        return f"<Product {self.name}>" 