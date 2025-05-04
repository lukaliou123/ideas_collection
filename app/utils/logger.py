"""
日志工具模块
"""
import logging
import sys
from app.core.config import settings

# 配置根日志记录器
def setup_logger():
    """设置应用程序日志记录器"""
    # 获取日志级别
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # 配置根记录器
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # 设置一些库的日志级别
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy").setLevel(logging.WARNING if not settings.DEBUG else logging.INFO)
    
    return logging.getLogger("app")

# 创建应用logger实例
logger = setup_logger() 