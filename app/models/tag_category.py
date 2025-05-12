from sqlalchemy import Column, Integer, String
from app.core.database import Base

class TagCategory(Base):
    __tablename__ = 'tag_categories'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)
    description = Column(String) 