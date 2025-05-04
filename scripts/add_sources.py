"""
添加初始数据源脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.models.sources import Source

def add_initial_sources():
    """添加初始数据源"""
    db = SessionLocal()
    
    # 检查是否已存在数据源
    if db.query(Source).count() > 0:
        print("数据源已存在，跳过添加。")
        db.close()
        return
    
    # 创建初始数据源
    sources = [
        Source(
            name="HackerNews",
            url="https://news.ycombinator.com/",
            active=True
        ),
        Source(
            name="IndieHackers",
            url="https://www.indiehackers.com/",
            active=True
        )
    ]
    
    # 添加到数据库
    db.add_all(sources)
    db.commit()
    
    print(f"成功添加 {len(sources)} 个数据源。")
    db.close()

if __name__ == "__main__":
    add_initial_sources() 