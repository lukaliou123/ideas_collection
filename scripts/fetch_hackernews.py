#!/usr/bin/env python
"""
手动拉取HackerNews数据的脚本
"""
import asyncio
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.hackernews_service import HackerNewsService
from app.utils.logger import logger

async def main():
    """脚本主函数"""
    logger.info("开始手动拉取HackerNews数据...")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 调用HackerNewsService执行数据拉取
        service = HackerNewsService(db)
        saved_count = await service.collect_posts()
        
        logger.info(f"数据拉取完成，成功保存了 {saved_count} 条新帖子")
        print(f"成功保存了 {saved_count} 条新HackerNews帖子")
    except Exception as e:
        logger.error(f"数据拉取过程中出错: {e}")
        print(f"错误: {e}")
    finally:
        # 关闭数据库会话
        db.close()

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main()) 