"""
HackerNews API 客户端
"""
import httpx
import asyncio
from datetime import datetime
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.sources import Source
from app.utils.logger import logger

class HackerNewsClient:
    """HackerNews API 客户端，用于获取HN上的创业产品信息"""
    
    # HackerNews API基础URL
    BASE_URL = "https://hacker-news.firebaseio.com/v0"
    
    # 获取的最大帖子数量
    MAX_POSTS = 500
    
    # 最小点赞数
    MIN_POINTS = 5
    
    def __init__(self, db: Session):
        """初始化客户端"""
        self.db = db
        self.source = self._get_or_create_source()
        self.client = httpx.AsyncClient(
            timeout=settings.REQUEST_TIMEOUT,
            headers={"User-Agent": settings.USER_AGENT}
        )
    
    def _get_or_create_source(self) -> Source:
        """获取或创建HackerNews数据源"""
        source = self.db.query(Source).filter(Source.name == "HackerNews").first()
        if not source:
            source = Source(
                name="HackerNews",
                url="https://news.ycombinator.com/",
                active=True
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        return source
    
    async def close(self):
        """关闭HTTP客户端"""
        await self.client.aclose()
    
    async def get_show_stories(self) -> List[int]:
        """获取Show HN类型帖子的ID列表"""
        try:
            response = await self.client.get(f"{self.BASE_URL}/showstories.json")
            response.raise_for_status()
            story_ids = response.json()
            return story_ids[:self.MAX_POSTS]  # 只获取最新的N个帖子
        except Exception as e:
            logger.error(f"获取Show HN帖子列表失败: {e}")
            return []
    
    async def get_story_details(self, story_id: int) -> Optional[Dict[str, Any]]:
        """获取帖子详情"""
        try:
            response = await self.client.get(f"{self.BASE_URL}/item/{story_id}.json")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"获取帖子 {story_id} 详情失败: {e}")
            return None
    
    async def get_show_hn_posts(self) -> List[Dict[str, Any]]:
        """获取'Show HN'类型的帖子"""
        story_ids = await self.get_show_stories()
        show_hn_posts = []
        
        # 同时获取多个帖子详情
        tasks = [self.get_story_details(story_id) for story_id in story_ids]
        stories = await asyncio.gather(*tasks)
        
        for story in stories:
            if not story or not isinstance(story, dict):
                continue
                
            # 只检查是否符合最低点赞数要求
            if 'score' in story and story['score'] >= self.MIN_POINTS:
                show_hn_posts.append(story)
        
        logger.info(f"获取到 {len(show_hn_posts)} 个符合条件的'Show HN'帖子")
        return show_hn_posts
    
    def format_post_data(self, post: Dict[str, Any]) -> Dict[str, Any]:
        """格式化帖子数据，用于存储到数据库"""
        return {
            'original_id': str(post.get('id')),
            'title': post.get('title', ''),
            'url': post.get('url', f"https://news.ycombinator.com/item?id={post.get('id')}"),
            'content': post.get('text', ''),
            'author': post.get('by', ''),
            'published_at': datetime.fromtimestamp(post.get('time', 0)),
            'points': post.get('score', 0),
            'comments_count': post.get('descendants', 0),
            'source_id': self.source.id
        }
    
    async def collect_show_hn_posts(self) -> List[Dict[str, Any]]:
        """收集Show HN帖子数据"""
        posts = await self.get_show_hn_posts()
        formatted_posts = [self.format_post_data(post) for post in posts]
        return formatted_posts 