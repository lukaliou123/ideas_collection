"""
HackerNews数据服务
"""
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from app.models.posts import Post
from app.scrapers.hackernews import HackerNewsClient
from app.services.content_service import ContentService
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
            duplicate_count = 0
            
            for post_data in posts_data:
                # 规范化帖子数据
                normalized_data = ContentService.normalize_post_data("HackerNews", post_data)
                
                # 检查直接匹配的帖子是否已存在（原始ID匹配）
                existing_post = self.db.query(Post).filter(
                    Post.source_id == normalized_data['source_id'],
                    Post.original_id == normalized_data['original_id']
                ).first()
                
                if existing_post:
                    logger.debug(f"跳过已存在的帖子: {normalized_data['title']} (ID: {normalized_data['original_id']})")
                    continue
                
                # 检查URL是否重复
                if normalized_data['url']:
                    is_duplicate_url = await ContentService.is_duplicate_url(self.db, normalized_data['url'])
                    if is_duplicate_url:
                        logger.debug(f"跳过URL重复的帖子: {normalized_data['title']} (URL: {normalized_data['url']})")
                        duplicate_count += 1
                        continue
                
                # 检查内容是否重复
                duplicate_post = await ContentService.is_duplicate_content(
                    self.db, 
                    normalized_data['title'], 
                    normalized_data.get('content', '')
                )
                
                if duplicate_post:
                    logger.debug(f"跳过内容相似的帖子: {normalized_data['title']} (与ID: {duplicate_post.id} 相似)")
                    duplicate_count += 1
                    continue
                
                # 创建新帖子
                new_post = Post(**normalized_data)
                self.db.add(new_post)
                saved_count += 1
            
            # 提交所有更改
            if saved_count > 0:
                self.db.commit()
                logger.info(f"已保存 {saved_count} 条新HackerNews帖子，跳过 {duplicate_count} 条重复帖子")
            else:
                logger.info(f"没有新的HackerNews帖子需要保存，跳过 {duplicate_count} 条重复帖子")
            
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