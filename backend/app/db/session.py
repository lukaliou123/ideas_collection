import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..core.config import settings

# 根据环境配置数据库URL
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", settings.DATABASE_URL)

# 创建SQLite数据库引擎
# 对于SQLite，需要配置check_same_thread=False和连接池
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=connect_args,
        poolclass=StaticPool,
        # 启用SQLite外键支持
        pool_pre_ping=True
    )
    # 启用SQLite外键约束
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
else:
    # 对于其他数据库类型
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

# 创建会话类
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine) 