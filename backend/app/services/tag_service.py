from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from backend.app.models.tag import Tag, TagCategory
import re
from difflib import SequenceMatcher

class TagService:
    def __init__(self, db: Session):
        self.db = db
        self.similarity_threshold = 0.8

    def _normalize_tag_string(self, tag: str) -> str:
        """标准化标签字符串"""
        # 转换为小写
        tag = tag.lower()
        # 移除多余空格
        tag = " ".join(tag.split())
        # 移除特殊字符
        tag = re.sub(r'[^a-z0-9\s-]', '', tag)
        return tag

    def get_all_tags(self) -> List[Dict[str, Any]]:
        """获取所有预定义标签，按分类组织"""
        tags = self.db.query(Tag).all()
        return [
            {
                "id": tag.id,
                "name": tag.name,
                "category": tag.category.name if tag.category else None
            }
            for tag in tags
        ]

    def normalize_tag(self, tag: str) -> Optional[str]:
        """标准化标签，如果标签不在预定义列表中返回None"""
        normalized = self._normalize_tag_string(tag)
        existing_tag = self.db.query(Tag).filter(
            Tag.normalized_name == normalized
        ).first()
        return existing_tag.name if existing_tag else None

    def find_similar_tags(self, tag: str) -> List[Tag]:
        """查找相似标签"""
        normalized_input = self._normalize_tag_string(tag)
        all_tags = self.db.query(Tag).all()
        
        similar_tags = []
        for existing_tag in all_tags:
            similarity = SequenceMatcher(None, normalized_input, existing_tag.normalized_name).ratio()
            if similarity >= self.similarity_threshold:
                similar_tags.append(existing_tag)
        
        return similar_tags

    def merge_similar_tags(self, tag: str) -> Optional[Tag]:
        """合并相似标签"""
        similar_tags = self.find_similar_tags(tag)
        if not similar_tags:
            return None
            
        # 选择最相似的标签作为主标签
        main_tag = max(similar_tags, 
                      key=lambda x: SequenceMatcher(None, 
                                                  self._normalize_tag_string(tag), 
                                                  x.normalized_name).ratio())
        
        # 更新别名列表
        if main_tag.aliases is None:
            main_tag.aliases = []
            
        if tag not in main_tag.aliases:
            main_tag.aliases.append(tag)
            self.db.commit()
            
        return main_tag

    def create_tag(self, name: str, category_id: Optional[int] = None) -> Tag:
        """创建新标签"""
        normalized_name = self._normalize_tag_string(name)
        
        # 检查是否已存在
        existing_tag = self.db.query(Tag).filter(
            Tag.normalized_name == normalized_name
        ).first()
        if existing_tag:
            return existing_tag
            
        # 创建新标签
        tag = Tag(
            name=name,
            normalized_name=normalized_name,
            category_id=category_id,
            aliases=[]
        )
        self.db.add(tag)
        self.db.commit()
        self.db.refresh(tag)
        return tag

    def get_tags_by_category(self, category_id: int) -> List[Tag]:
        """获取特定分类的标签"""
        return self.db.query(Tag).filter(Tag.category_id == category_id).all()

    def create_category(self, name: str, description: Optional[str] = None) -> TagCategory:
        """创建标签分类"""
        category = TagCategory(name=name, description=description)
        self.db.add(category)
        self.db.commit()
        self.db.refresh(category)
        return category 