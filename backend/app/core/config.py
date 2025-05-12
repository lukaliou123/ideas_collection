import os
from pathlib import Path
from typing import Any, Dict, Optional

from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "Product Collection System"
    
    # 基础路径
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    
    # 数据库配置
    DATABASE_URL: str = f"sqlite:///{BASE_DIR}/app.db"
    
    # 跨域配置
    BACKEND_CORS_ORIGINS: list = ["*"]
    
    # OpenAI配置
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    
    # 爬虫配置
    SCRAPER_INTERVAL: int = 3600
    REQUEST_TIMEOUT: int = 30
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36"
    
    # 功能开关
    ENABLE_SCHEDULER: bool = True
    ENABLE_AI_ANALYSIS: bool = True
    AI_ANALYSIS_MIN_POINTS: int = 5
    
    # 调试配置
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Any) -> list:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        return v
    
    class Config:
        case_sensitive = True
        env_file = ".env"
        extra = "ignore"  # 忽略额外的配置项


settings = Settings() 