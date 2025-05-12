"""
初始化标签和标签分类脚本
用于创建基本的标签分类和默认标签
"""
import os
import sys
import logging

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
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

from sqlalchemy import Column, String, Integer, ForeignKey, JSON
from sqlalchemy.orm import relationship

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
        # 移除特殊字符
        import re
        normalized = re.sub(r'[^\w\s\-]', ' ', normalized)
        # 将连字符替换为空格
        normalized = normalized.replace('-', ' ')
        # 将多个空格替换为单个空格
        normalized = re.sub(r'\s+', ' ', normalized)
        # 移除首尾空格
        normalized = normalized.strip()
        return normalized

# 预定义的标签分类
PREDEFINED_CATEGORIES = [
    {
        "name": "技术领域",
        "description": "技术相关的标签，如编程语言、框架、平台等"
    },
    {
        "name": "行业领域",
        "description": "各种行业分类标签，如金融、教育、医疗等"
    },
    {
        "name": "用户类型",
        "description": "目标用户类型的标签，如个人用户、企业用户、开发者等"
    },
    {
        "name": "问题领域",
        "description": "产品解决的问题类型标签"
    },
    {
        "name": "产品属性",
        "description": "产品特点和属性相关的标签，如免费、开源、AI驱动等"
    }
]

# 预定义的标签
PREDEFINED_TAGS = {
    "技术领域": [
        "Python", "JavaScript", "React", "Vue", "Angular", "Node.js",
        "Django", "Flask", "FastAPI", "Spring", "Java", "Go", "Rust",
        "TensorFlow", "PyTorch", "人工智能", "机器学习", "深度学习",
        "区块链", "微服务", "容器化", "云计算", "边缘计算"
    ],
    "行业领域": [
        "电子商务", "金融科技", "教育科技", "医疗健康", "房地产", "物流",
        "旅游", "餐饮", "娱乐", "社交媒体", "企业服务", "农业", "能源",
        "制造业", "零售", "传媒", "广告营销"
    ],
    "用户类型": [
        "个人用户", "企业用户", "开发者", "设计师", "学生", "教师",
        "医生", "患者", "投资者", "创业者", "自由职业者"
    ],
    "问题领域": [
        "效率提升", "成本降低", "用户体验", "数据分析", "安全防护",
        "自动化", "流程优化", "内容创作", "资源管理", "社交连接",
        "学习辅助", "健康监测"
    ],
    "产品属性": [
        "免费", "开源", "付费", "订阅制", "一次性付费", "移动应用",
        "网页应用", "桌面应用", "多平台", "云服务", "AI驱动", "实时",
        "离线使用", "高安全性", "高隐私性"
    ]
}


def create_categories(db):
    """创建预定义的标签分类"""
    logger.info("开始创建标签分类")
    categories = {}
    
    for category_data in PREDEFINED_CATEGORIES:
        name = category_data["name"]
        description = category_data["description"]
        
        # 查询是否已存在
        existing = db.query(TagCategory).filter(TagCategory.name == name).first()
        if existing:
            logger.info(f"分类 '{name}' 已存在，跳过")
            categories[name] = existing
            continue
            
        # 创建新分类
        try:
            category = TagCategory(
                name=name,
                description=description
            )
            db.add(category)
            db.commit()
            db.refresh(category)
            logger.info(f"创建分类: {name}")
            categories[name] = category
        except Exception as e:
            logger.error(f"创建分类 '{name}' 失败: {str(e)}")
    
    return categories


def create_tags(db, categories):
    """创建预定义的标签"""
    logger.info("开始创建预定义标签")
    created_count = 0
    skipped_count = 0
    
    for category_name, tags in PREDEFINED_TAGS.items():
        if category_name not in categories:
            logger.warning(f"分类 '{category_name}' 不存在，跳过相关标签")
            continue
            
        category = categories[category_name]
        
        for tag_name in tags:
            # 查询是否已存在
            normalized_name = TagNormalizer.normalize_tag_name(tag_name)
            existing = db.query(Tag).filter(Tag.normalized_name == normalized_name).first()
            if existing:
                logger.debug(f"标签 '{tag_name}' 已存在，跳过")
                skipped_count += 1
                continue
                
            # 创建新标签
            try:
                tag = Tag(
                    name=tag_name,
                    normalized_name=normalized_name,
                    category_id=category.id,
                    aliases=[]
                )
                db.add(tag)
                db.commit()
                db.refresh(tag)
                logger.info(f"创建标签: {tag_name} (分类: {category_name})")
                created_count += 1
            except Exception as e:
                logger.error(f"创建标签 '{tag_name}' 失败: {str(e)}")
    
    logger.info(f"标签创建完成: 新建 {created_count} 个，跳过 {skipped_count} 个")


def main():
    """主函数"""
    db = SessionLocal()
    try:
        # 创建标签分类
        categories = create_categories(db)
        
        # 创建预定义标签
        create_tags(db, categories)
        
        logger.info("标签初始化完成")
    except Exception as e:
        logger.error(f"标签初始化失败: {str(e)}")
    finally:
        db.close()


if __name__ == "__main__":
    main() 