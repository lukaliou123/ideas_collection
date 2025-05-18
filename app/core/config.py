"""
配置模块 - 管理应用程序配置
"""
import os
from typing import Optional, Dict, Any
from pydantic_settings import BaseSettings
from pydantic import Field, field_validator

class Settings(BaseSettings):
    """应用配置设置"""
    
    # 数据库配置
    DATABASE_URL: str = Field(default="sqlite:///./app.db")
    
    # API密钥
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: Optional[str] = "gpt-4.1-nano"
    
    # Langfuse 配置
    LANGFUSE_PUBLIC_KEY: Optional[str] = None
    LANGFUSE_SECRET_KEY: Optional[str] = None
    LANGFUSE_HOST: Optional[str] = "https://cloud.langfuse.com" # 默认指向 Langfuse Cloud
    
    # 爬虫配置
    SCRAPER_INTERVAL: int = 3600  # 默认每小时运行一次
    REQUEST_TIMEOUT: int = 30  # 请求超时时间（秒）
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    # 调度器配置
    ENABLE_SCHEDULER: bool = True  # 是否启用定时任务调度器
    
    # AI设置
    ENABLE_AI_ANALYSIS: bool = True  # 是否启用AI分析
    AI_ANALYSIS_MIN_POINTS: int = 10  # 启用AI分析的最低分数要求
    
    # 应用设置
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # 验证器和其他设置
    @field_validator("DATABASE_URL")
    def validate_database_url(cls, v: Optional[str]) -> str:
        """验证数据库URL"""
        if not v:
            # 如果未设置，默认使用SQLite
            return "sqlite:///./app.db"
        return v
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": True
    }

# 创建设置实例
settings = Settings() 