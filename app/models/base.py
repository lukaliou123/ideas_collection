"""
基础模型类模块
"""
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.sql import func

from app.core.database import Base

class BaseModel(object):
    """所有模型的基类"""
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False) 