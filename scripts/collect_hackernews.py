"""
HackerNews帖子收集脚本
"""
import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.services.hackernews_service import HackerNewsService
from app.utils.logger import logger

async def collect_hackernews_posts():
    """从HackerNews收集帖子"""
    db = SessionLocal()
    try:
        logger.info("开始从HackerNews收集帖子...")
        saved_count = await HackerNewsService.run_collection(db)
        logger.info(f"收集完成，共保存 {saved_count} 条新帖子。")
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(collect_hackernews_posts()) 