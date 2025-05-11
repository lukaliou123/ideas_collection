from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from backend.app.db.base_class import Base
from backend.app.models.associations import product_tags

class Product(Base):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    url = Column(String, unique=True, nullable=False)
    source = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)
    updated_at = Column(DateTime, nullable=False)
    
    # 添加标签关系
    tags = relationship("Tag", secondary=product_tags, back_populates="products") 