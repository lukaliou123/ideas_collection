"""
自动归类未分类标签脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.tags import Tag
from app.models.tag_category import TagCategory

# 分类映射（可根据实际需求补充/调整）
CATEGORY_MAP = {
    "产品类型": [
        "SaaS", "工具", "API", "移动应用", "桌面应用", "网站", "浏览器扩展", "开源项目"
    ],
    "技术": [
        "人工智能", "机器学习", "数据分析", "区块链", "云计算", "安全", "开发工具"
    ],
    "目标市场": [
        "B2B", "B2C", "企业级", "个人用户", "开发者"
    ],
    "产品状态": [
        "原型", "测试版", "正式版"
    ],
    "商业模式": [
        "免费", "订阅制", "一次性付费", "开源"
    ],
    # 可继续补充其它分类
}

def auto_assign_tag_categories():
    db = SessionLocal()
    try:
        # 获取所有分类名到id的映射
        categories = {c.name: c.id for c in db.query(TagCategory).all()}
        updated = 0
        for cat_name, tag_names in CATEGORY_MAP.items():
            cat_id = categories.get(cat_name)
            if not cat_id:
                print(f"分类 {cat_name} 不存在，跳过。")
                continue
            for tag_name in tag_names:
                # 只归类未归类的标签
                count = db.query(Tag).filter(Tag.name == tag_name, Tag.category_id == None).update({"category_id": cat_id})
                if count:
                    print(f"标签 {tag_name} 归类到 {cat_name}")
                    updated += count
        db.commit()
        print(f"自动归类完成，共更新 {updated} 个标签。")
    finally:
        db.close()

if __name__ == "__main__":
    auto_assign_tag_categories() 