"""
帖子模型模块
"""
from sqlalchemy import Column, String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.base import BaseModel

class Post(Base, BaseModel):
    """帖子模型，用于存储从各数据源获取的原始信息"""
    
    __tablename__ = "posts"
    
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False, index=True)
    original_id = Column(String(100), nullable=False)  # 源站上的原始ID
    title = Column(String(500), nullable=False)
    url = Column(String(2000), nullable=True)  # 可能有些帖子没有URL
    content = Column(Text, nullable=True)  # 帖子内容，如果有
    author = Column(String(100), nullable=True)
    published_at = Column(DateTime, nullable=True)
    points = Column(Integer, default=0)
    comments_count = Column(Integer, default=0)
    collected_at = Column(DateTime, nullable=False)
    processed = Column(Integer, default=0)  # 0-未处理, 1-已处理, 2-处理失败
    
    # 关联关系
    source = relationship("Source", back_populates="posts")
    product = relationship("Product", back_populates="post", uselist=False)
    
    def __repr__(self):
        return f"<Post {self.title}>" 