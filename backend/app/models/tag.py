from sqlalchemy import Column, Integer, String, ForeignKey, JSON
from sqlalchemy.orm import relationship
from backend.app.db.base_class import Base
from backend.app.models.associations import product_tags

class TagCategory(Base):
    __tablename__ = "tag_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String)
    
    # Relationships
    tags = relationship("Tag", back_populates="category")

class Tag(Base):
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    normalized_name = Column(String, unique=True, nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("tag_categories.id"))
    aliases = Column(JSON, default=lambda: [], nullable=False)  # 存储相似标签的别名
    
    # Relationships
    category = relationship("TagCategory", back_populates="tags")
    products = relationship("Product", secondary=product_tags, back_populates="tags") 