"""
数据库模块 - 管理数据库连接
"""
import os
from sqlalchemy import create_engine, pool
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# 根据数据库类型配置不同的连接参数
def get_engine_config():
    """获取数据库引擎配置"""
    config = {
        "echo": settings.DEBUG,
    }
    
    if settings.is_sqlite:
        # SQLite 特定配置
        config["connect_args"] = {"check_same_thread": False}
    elif settings.is_postgresql:
        # PostgreSQL 特定配置
        config["pool_pre_ping"] = True  # 自动检测连接是否有效
        config["pool_size"] = 5  # 连接池大小
        config["max_overflow"] = 10  # 最大溢出连接数
        config["pool_recycle"] = 3600  # 连接回收时间（秒）
    
    return config

# 创建数据库引擎
engine = create_engine(
    settings.DATABASE_URL,
    **get_engine_config()
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 声明基础模型类
Base = declarative_base()

def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """初始化数据库（创建所有表）"""
    # 确保数据目录存在（仅对 SQLite）
    if settings.is_sqlite:
        db_path = settings.DATABASE_URL.replace("sqlite:///", "")
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
    
    # 导入所有模型以确保它们被注册
    from app.models import base, sources, posts, products, tag, associations
    
    # 创建所有表
    Base.metadata.create_all(bind=engine) 