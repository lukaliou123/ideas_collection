"""
列出所有标签脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.tags import Tag

def list_tags():
    """列出所有标签"""
    db = SessionLocal()
    try:
        tags = db.query(Tag).order_by(Tag.name).all()
        
        print(f"\n共有 {len(tags)} 个标签:\n")
        
        for tag in tags:
            print(f"- {tag.name} (ID: {tag.id})")
                    
    finally:
        db.close()

if __name__ == "__main__":
    list_tags() 