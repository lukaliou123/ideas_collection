"""
HackerNews数据服务
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.posts import Post
from app.scrapers.hackernews import HackerNewsClient
from app.utils.logger import logger

class HackerNewsService:
    """HackerNews数据服务类，负责从HackerNews获取并存储数据"""
    
    def __init__(self, db: Session):
        """初始化服务"""
        self.db = db
        self.client = HackerNewsClient(db)
    
    async def collect_posts(self) -> int:
        """收集并存储Show HN帖子"""
        try:
            # 获取帖子数据
            posts_data = await self.client.collect_show_hn_posts()
            saved_count = 0
            
            for post_data in posts_data:
                # 检查帖子是否已存在
                existing_post = self.db.query(Post).filter(
                    Post.source_id == post_data['source_id'],
                    Post.original_id == post_data['original_id']
                ).first()
                
                if not existing_post:
                    # 添加收集时间
                    post_data['collected_at'] = datetime.now()
                    
                    # 创建新帖子
                    new_post = Post(**post_data)
                    self.db.add(new_post)
                    saved_count += 1
            
            # 提交所有更改
            if saved_count > 0:
                self.db.commit()
                logger.info(f"已保存 {saved_count} 条新HackerNews帖子")
            else:
                logger.info("没有新的HackerNews帖子需要保存")
            
            return saved_count
        
        except Exception as e:
            self.db.rollback()
            logger.error(f"保存HackerNews帖子时出错: {e}")
            return 0
        
        finally:
            # 关闭HTTP客户端
            await self.client.close()
    
    @classmethod
    async def run_collection(cls, db: Session) -> int:
        """运行数据收集，可作为定时任务调用"""
        service = cls(db)
        return await service.collect_posts() 