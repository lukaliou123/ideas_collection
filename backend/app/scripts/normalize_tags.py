"""
标签标准化和合并脚本
用于处理现有标签，标准化名称并合并相似标签
"""
import os
import sys
import argparse
import logging
import re
from collections import defaultdict
from difflib import SequenceMatcher

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 创建数据库会话
from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.ext.declarative import declarative_base

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建数据库会话
DATABASE_URL = "sqlite:///app.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 简化的模型定义，避免循环引用
Base = declarative_base()

class TagCategory(Base):
    """标签分类模型"""
    __tablename__ = "tag_categories"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    
    # 反向关系
    tags = relationship("Tag", back_populates="category")
    
    def __repr__(self):
        return f"<TagCategory {self.name}>"

class Tag(Base):
    """标签模型"""
    __tablename__ = "tags"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    normalized_name = Column(String, unique=True, index=True, nullable=False)
    description = Column(String, nullable=True)
    aliases = Column(JSON, nullable=True, default=list)
    
    # 外键
    category_id = Column(Integer, ForeignKey("tag_categories.id"), nullable=True)
    
    # 关系
    category = relationship("TagCategory", back_populates="tags")
    
    def __repr__(self):
        return f"<Tag {self.name}>"

# 标签规范化工具类
class TagNormalizer:
    @staticmethod
    def normalize_tag_name(tag_name: str) -> str:
        """
        标准化标签名称：
        1. 转换为小写
        2. 移除特殊字符
        3. 将多个空格替换为单个空格
        4. 移除首尾空格
        """
        # 转换为小写
        normalized = tag_name.lower()
        # 将特殊字符替换为空格
        normalized = re.sub(r'[^\w\s\-]', ' ', normalized)
        # 将连字符替换为空格
        normalized = normalized.replace('-', ' ')
        # 将多个空格替换为单个空格
        normalized = re.sub(r'\s+', ' ', normalized)
        # 移除首尾空格
        normalized = normalized.strip()
        return normalized

    @staticmethod
    def calculate_similarity(tag1: str, tag2: str) -> float:
        """
        计算两个标签名称的相似度
        返回0-1之间的相似度分数
        """
        return SequenceMatcher(None, tag1, tag2).ratio()

# 标签服务类
class TagService:
    @staticmethod
    def get_tag_by_id(db, tag_id: int):
        """根据ID获取标签"""
        return db.query(Tag).filter(Tag.id == tag_id).first()
    
    @staticmethod
    def merge_tags(db, primary_tag_id: int, secondary_tag_ids: list) -> Tag:
        """
        合并标签：将次要标签合并到主要标签中
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
            
            # 删除次要标签
            db.delete(secondary_tag)
            
        # 更新主标签的别名
        primary_tag.aliases = primary_aliases
        
        db.commit()
        db.refresh(primary_tag)
        return primary_tag


def normalize_existing_tags():
    """标准化所有现有标签的名称"""
    db = SessionLocal()
    try:
        tags = db.query(Tag).all()
        logger.info(f"开始标准化 {len(tags)} 个标签")
        
        for tag in tags:
            normalized_name = TagNormalizer.normalize_tag_name(tag.name)
            if tag.normalized_name != normalized_name:
                logger.info(f"标准化标签: {tag.name} -> {normalized_name}")
                tag.normalized_name = normalized_name
        
        db.commit()
        logger.info("标签标准化完成")
    except Exception as e:
        db.rollback()
        logger.error(f"标签标准化失败: {str(e)}")
    finally:
        db.close()


def find_similar_tags(threshold=0.85, interactive=False):
    """
    查找相似标签并打印结果
    如果interactive=True，允许用户选择是否合并
    """
    db = SessionLocal()
    try:
        tags = db.query(Tag).all()
        logger.info(f"分析 {len(tags)} 个标签以查找相似项")
        
        # 用于保存已处理的标签对，避免重复检查
        processed_pairs = set()
        # 用于保存相似标签的分组
        similar_groups = []
        
        for i, tag1 in enumerate(tags):
            current_group = [tag1]
            
            for j, tag2 in enumerate(tags):
                if i == j:
                    continue
                    
                pair_key = tuple(sorted([tag1.id, tag2.id]))
                if pair_key in processed_pairs:
                    continue
                    
                processed_pairs.add(pair_key)
                
                similarity = TagNormalizer.calculate_similarity(
                    tag1.normalized_name, tag2.normalized_name
                )
                
                if similarity >= threshold:
                    logger.info(f"相似标签: '{tag1.name}' 和 '{tag2.name}' (相似度: {similarity:.2f})")
                    current_group.append(tag2)
            
            if len(current_group) > 1:
                similar_groups.append(current_group)
        
        logger.info(f"找到 {len(similar_groups)} 组相似标签")
        
        if interactive and similar_groups:
            merge_interactively(db, similar_groups)
            
        return similar_groups
    except Exception as e:
        logger.error(f"查找相似标签失败: {str(e)}")
        return []
    finally:
        db.close()


def merge_interactively(db, similar_groups):
    """交互式合并标签组"""
    for i, group in enumerate(similar_groups):
        print(f"\n组 {i+1}/{len(similar_groups)}:")
        for j, tag in enumerate(group):
            print(f"  {j+1}. {tag.name} (ID: {tag.id})")
        
        merge_choice = input("是否合并这组标签? (y/n): ").strip().lower()
        if merge_choice != 'y':
            continue
            
        primary_idx = int(input(f"选择主标签 (1-{len(group)}): ").strip()) - 1
        primary_tag = group[primary_idx]
        secondary_tags = [tag for j, tag in enumerate(group) if j != primary_idx]
        
        if not secondary_tags:
            print("没有次要标签可合并")
            continue
            
        print(f"将标签 {', '.join(t.name for t in secondary_tags)} 合并到 {primary_tag.name}")
        confirm = input("确认? (y/n): ").strip().lower()
        if confirm == 'y':
            try:
                TagService.merge_tags(db, primary_tag.id, [t.id for t in secondary_tags])
                print("合并成功")
            except Exception as e:
                print(f"合并失败: {str(e)}")


def auto_merge_tags(threshold=0.95):
    """
    自动合并相似度高于阈值的标签
    """
    db = SessionLocal()
    try:
        tags = db.query(Tag).all()
        logger.info(f"分析 {len(tags)} 个标签以自动合并相似项 (阈值: {threshold})")
        
        # 建立标签名称查找字典
        tag_dict = {tag.normalized_name: tag for tag in tags}
        normalized_names = list(tag_dict.keys())
        
        # 跟踪已处理的标签
        processed_tags = set()
        merge_count = 0
        
        for name1 in normalized_names:
            if name1 in processed_tags:
                continue
                
            tag1 = tag_dict[name1]
            similar_names = []
            
            for name2 in normalized_names:
                if name1 == name2 or name2 in processed_tags:
                    continue
                    
                similarity = TagNormalizer.calculate_similarity(name1, name2)
                if similarity >= threshold:
                    similar_names.append(name2)
            
            if similar_names:
                # 找出相似标签
                similar_tags = [tag_dict[name] for name in similar_names]
                # 将主标签也加入列表
                all_tags = [tag1] + similar_tags
                
                # 第一个作为主标签(由于没有产品关联数据，无法按产品数量排序)
                primary_tag = all_tags[0]
                secondary_tags = all_tags[1:]
                
                if secondary_tags:
                    try:
                        logger.info(f"自动合并: 以 '{primary_tag.name}' 为主标签，合并 {len(secondary_tags)} 个次要标签")
                        TagService.merge_tags(db, primary_tag.id, [t.id for t in secondary_tags])
                        merge_count += 1
                        
                        # 标记已处理的标签
                        processed_tags.update([t.normalized_name for t in secondary_tags])
                    except Exception as e:
                        logger.error(f"合并失败: {str(e)}")
        
        logger.info(f"自动合并完成，共合并 {merge_count} 组标签")
    except Exception as e:
        db.rollback()
        logger.error(f"自动合并标签失败: {str(e)}")
    finally:
        db.close()


def main():
    parser = argparse.ArgumentParser(description="标签标准化和合并工具")
    parser.add_argument("--normalize", action="store_true", help="标准化所有标签名称")
    parser.add_argument("--find-similar", action="store_true", help="查找相似标签")
    parser.add_argument("--merge-interactive", action="store_true", help="交互式合并相似标签")
    parser.add_argument("--auto-merge", action="store_true", help="自动合并高度相似的标签")
    parser.add_argument("--threshold", type=float, default=0.85, help="相似度阈值 (0-1)")
    parser.add_argument("--auto-threshold", type=float, default=0.95, help="自动合并的相似度阈值 (0-1)")
    
    args = parser.parse_args()
    
    if args.normalize:
        normalize_existing_tags()
        
    if args.find_similar:
        find_similar_tags(threshold=args.threshold, interactive=args.merge_interactive)
        
    if args.auto_merge:
        auto_merge_tags(threshold=args.auto_threshold)
        
    if not any([args.normalize, args.find_similar, args.auto_merge]):
        parser.print_help()


if __name__ == "__main__":
    main() 