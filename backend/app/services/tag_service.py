from typing import List, Dict, Optional, Union, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from ..models.tag import Tag, TagCategory
from ..core.tag_utils import TagNormalizer


class TagService:
    """标签服务，用于管理标签的创建、查询和合并"""

    @staticmethod
    def create_tag(
        db: Session, 
        name: str, 
        category_id: Optional[int] = None,
        description: Optional[str] = None,
        aliases: Optional[List[str]] = None
    ) -> Tag:
        """
        创建一个新的标签
        如果标签已存在（根据normalized_name判断），返回已存在的标签
        """
        normalized_name = TagNormalizer.normalize_tag_name(name)
        
        # 检查标签是否已存在
        existing_tag = db.query(Tag).filter(Tag.normalized_name == normalized_name).first()
        if existing_tag:
            return existing_tag
            
        # 创建新标签
        tag = Tag(
            name=name,
            normalized_name=normalized_name,
            category_id=category_id,
            description=description,
            aliases=aliases or []
        )
        
        db.add(tag)
        db.commit()
        db.refresh(tag)
        return tag
    
    @staticmethod
    def get_tag_by_id(db: Session, tag_id: int) -> Optional[Tag]:
        """根据ID获取标签"""
        return db.query(Tag).filter(Tag.id == tag_id).first()
    
    @staticmethod
    def get_tag_by_name(db: Session, name: str) -> Optional[Tag]:
        """根据标签名称获取标签（使用标准化名称进行查询）"""
        normalized_name = TagNormalizer.normalize_tag_name(name)
        return db.query(Tag).filter(Tag.normalized_name == normalized_name).first()
    
    @staticmethod
    def get_all_tags(db: Session, skip: int = 0, limit: int = 100) -> List[Tag]:
        """获取所有标签"""
        return db.query(Tag).offset(skip).limit(limit).all()
    
    @staticmethod
    def get_tags_by_category(
        db: Session, 
        category_id: int,
        skip: int = 0, 
        limit: int = 100
    ) -> List[Tag]:
        """获取指定分类下的标签"""
        return db.query(Tag).filter(Tag.category_id == category_id).offset(skip).limit(limit).all()
        
    @staticmethod
    def find_similar_tags(db: Session, tag_name: str, threshold: float = 0.85) -> List[Tag]:
        """
        查找与给定标签名称相似的标签
        返回相似度高于阈值的标签列表
        """
        normalized_name = TagNormalizer.normalize_tag_name(tag_name)
        all_tags = db.query(Tag).all()
        
        similar_tags = []
        for tag in all_tags:
            if tag.normalized_name == normalized_name:
                continue
                
            similarity = TagNormalizer.calculate_similarity(normalized_name, tag.normalized_name)
            if similarity >= threshold:
                similar_tags.append(tag)
                
        return similar_tags
    
    @staticmethod
    def merge_tags(db: Session, primary_tag_id: int, secondary_tag_ids: List[int]) -> Tag:
        """
        合并标签：将次要标签合并到主要标签中
        - 将次要标签的产品关联转移到主要标签
        - 将次要标签的别名添加到主要标签
        - 删除次要标签
        """
        primary_tag = TagService.get_tag_by_id(db, primary_tag_id)
        if not primary_tag:
            raise ValueError(f"Primary tag with ID {primary_tag_id} not found")
            
        # 获取主标签的现有别名列表，确保它是一个列表
        primary_aliases = primary_tag.aliases or []
        
        for secondary_id in secondary_tag_ids:
            secondary_tag = TagService.get_tag_by_id(db, secondary_id)
            if not secondary_tag:
                continue
                
            # 将次要标签名称添加为主标签的别名
            if secondary_tag.name != primary_tag.name and secondary_tag.name not in primary_aliases:
                primary_aliases.append(secondary_tag.name)
                
            # 添加次要标签的别名到主标签
            secondary_aliases = secondary_tag.aliases or []
            for alias in secondary_aliases:
                if alias not in primary_aliases and alias != primary_tag.name:
                    primary_aliases.append(alias)
                    
            # 将次要标签的产品关联转移到主标签
            for product in secondary_tag.products:
                if primary_tag not in product.tags:
                    product.tags.append(primary_tag)
                    
            # 删除次要标签
            db.delete(secondary_tag)
            
        # 更新主标签的别名
        primary_tag.aliases = primary_aliases
        
        db.commit()
        db.refresh(primary_tag)
        return primary_tag
        
    @staticmethod
    def create_category(db: Session, name: str, description: Optional[str] = None) -> TagCategory:
        """创建标签分类"""
        category = TagCategory(
            name=name,
            description=description
        )
        
        db.add(category)
        db.commit()
        db.refresh(category)
        return category
    
    @staticmethod
    def get_all_categories(db: Session, skip: int = 0, limit: int = 100) -> List[TagCategory]:
        """获取所有标签分类"""
        return db.query(TagCategory).offset(skip).limit(limit).all()
        
    @staticmethod
    def get_category_by_id(db: Session, category_id: int) -> Optional[TagCategory]:
        """根据ID获取标签分类"""
        return db.query(TagCategory).filter(TagCategory.id == category_id).first()
    
    @staticmethod
    def get_category_by_name(db: Session, name: str) -> Optional[TagCategory]:
        """根据名称获取标签分类"""
        return db.query(TagCategory).filter(func.lower(TagCategory.name) == name.lower()).first() 