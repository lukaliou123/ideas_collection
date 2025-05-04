"""
内容处理服务模块 - 负责内容去重和规范化
"""
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.posts import Post
from app.models.sources import Source
from app.utils.logger import logger
from app.utils.text import normalize_text, calculate_similarity

class ContentService:
    """内容处理服务，负责内容去重和规范化"""
    
    @staticmethod
    async def is_duplicate_url(db: Session, url: str) -> bool:
        """
        检查URL是否已存在于数据库中
        
        Args:
            db: 数据库会话
            url: 待检查的URL
            
        Returns:
            是否为重复URL
        """
        # 规范化URL（移除追踪参数、统一格式等）
        normalized_url = ContentService.normalize_url(url)
        
        # 检查数据库中是否存在相同URL
        existing_post = db.query(Post).filter(
            func.lower(Post.url) == func.lower(normalized_url)
        ).first()
        
        return existing_post is not None
    
    @staticmethod
    async def is_duplicate_content(db: Session, title: str, content: str, 
                                  similarity_threshold: float = 0.85) -> Optional[Post]:
        """
        检查内容是否与现有内容重复
        
        Args:
            db: 数据库会话
            title: 内容标题
            content: 内容正文
            similarity_threshold: 相似度阈值，超过此值视为重复
            
        Returns:
            若重复则返回重复的帖子对象，否则返回None
        """
        # 规范化文本
        normalized_title = normalize_text(title)
        
        # 首先根据标题进行初筛
        # 获取最近的100篇帖子进行比较（完整比较所有帖子会很耗性能）
        recent_posts = db.query(Post).order_by(
            Post.collected_at.desc()
        ).limit(100).all()
        
        # 对每篇帖子计算相似度
        for post in recent_posts:
            post_title = normalize_text(post.title)
            
            # 如果标题非常相似，进一步比较内容
            title_similarity = calculate_similarity(normalized_title, post_title)
            
            if title_similarity > similarity_threshold:
                # 如果标题高度相似且有内容，则进一步比较内容
                if content and post.content:
                    content_similarity = calculate_similarity(
                        normalize_text(content), 
                        normalize_text(post.content)
                    )
                    
                    # 综合标题和内容的相似度
                    overall_similarity = (title_similarity * 0.6) + (content_similarity * 0.4)
                    
                    if overall_similarity > similarity_threshold:
                        return post
                else:
                    # 如果没有内容或其中一个内容为空，仅靠标题判断
                    if title_similarity > 0.95:  # 标题几乎完全一致
                        return post
        
        return None
    
    @staticmethod
    def normalize_url(url: str) -> str:
        """
        规范化URL，移除跟踪参数，统一格式
        
        Args:
            url: 原始URL
            
        Returns:
            规范化后的URL
        """
        # 移除常见的跟踪参数
        import re
        from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
        
        # 解析URL
        parsed_url = urlparse(url)
        
        # 解析查询参数
        query_params = parse_qs(parsed_url.query)
        
        # 移除常见的跟踪参数
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'ref', 'source', 'ref_src', 'ref_url', 'cmpid', 'cid'
        ]
        
        for param in tracking_params:
            if param in query_params:
                del query_params[param]
        
        # 重新构建查询字符串
        new_query = urlencode(query_params, doseq=True) if query_params else ''
        
        # 重新组装URL
        normalized_url = urlunparse((
            parsed_url.scheme,
            parsed_url.netloc,
            parsed_url.path,
            parsed_url.params,
            new_query,
            ''  # 移除fragment
        ))
        
        # 移除URL末尾的斜杠
        if normalized_url.endswith('/'):
            normalized_url = normalized_url[:-1]
        
        return normalized_url
    
    @staticmethod
    def normalize_post_data(source_name: str, post_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据来源规范化帖子数据
        
        Args:
            source_name: 来源名称，如"HackerNews"、"IndieHackers"
            post_data: 原始帖子数据
            
        Returns:
            规范化后的帖子数据
        """
        normalized_data = post_data.copy()
        
        # 根据不同来源进行不同的处理
        if source_name.lower() == "hackernews":
            # HackerNews特定的数据规范化逻辑
            if 'points' in normalized_data and normalized_data['points'] is None:
                normalized_data['points'] = 0
                
            if 'comments_count' in normalized_data and normalized_data['comments_count'] is None:
                normalized_data['comments_count'] = 0
                
            # 确保URL格式正确
            if 'url' in normalized_data and normalized_data['url']:
                normalized_data['url'] = ContentService.normalize_url(normalized_data['url'])
                
        elif source_name.lower() == "indiehackers":
            # Indie Hackers特定的数据规范化逻辑
            # 将会在实现Indie Hackers爬虫后添加
            pass
        
        # 通用处理：去除标题和内容中的多余空白
        if 'title' in normalized_data and normalized_data['title']:
            normalized_data['title'] = ' '.join(normalized_data['title'].split())
            
        if 'content' in normalized_data and normalized_data['content']:
            normalized_data['content'] = normalized_data['content'].strip()
        
        # 添加标准化的收集时间
        normalized_data['collected_at'] = datetime.utcnow()
        
        return normalized_data 