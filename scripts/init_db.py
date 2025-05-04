"""
数据库初始化脚本
"""
import sys
import os

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import Base, engine
from app.core.config import settings
from app.models import *  # 导入所有模型以确保它们被注册

def init_db():
    """初始化数据库"""
    print(f"正在使用数据库: {settings.DATABASE_URL}")
    print("创建数据库表...")
    Base.metadata.create_all(bind=engine)
    print("数据库初始化完成!")

if __name__ == "__main__":
    init_db() 