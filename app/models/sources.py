"""
数据源模型
"""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import BaseModel

class Source(Base, BaseModel):
    """数据源模型，如HackerNews, IndieHackers等"""
    
    __tablename__ = "sources"
    
    name = Column(String(100), nullable=False, index=True)
    url = Column(String(255), nullable=False)
    active = Column(Boolean, default=True)
    
    # 关联关系
    posts = relationship("Post", back_populates="source")
    
    def __repr__(self):
        return f"<Source {self.name}>" 