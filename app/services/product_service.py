"""
产品服务模块 - 负责处理产品信息和标签
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime

from app.models.posts import Post
from app.models.products import Product
from app.models.tags import Tag
from app.services.ai_service import AIService, AIAnalysisResult
from app.utils.logger import logger

class ProductService:
    """产品服务类，负责处理产品信息和标签"""
    
    def __init__(self, db: Session):
        """初始化服务"""
        self.db = db
        self.ai_service = AIService()
    
    async def process_post(self, post_id: int) -> Optional[Product]:
        """
        处理帖子，提取产品信息并创建产品记录
        
        Args:
            post_id: 要处理的帖子ID
            
        Returns:
            创建的产品对象，如果处理失败则返回None
        """
        try:
            # 获取帖子
            post = self.db.query(Post).filter(Post.id == post_id).first()
            if not post:
                logger.warning(f"未找到ID为 {post_id} 的帖子")
                return None
                
            # 如果帖子已处理，则返回关联的产品（如果有）
            if post.processed and post.product:
                logger.info(f"帖子 {post_id} 已处理，跳过")
                return post.product
            
            # 使用AI分析帖子
            analysis_result = await self.ai_service.analyze_product(
                title=post.title,
                content=post.content or "",
                url=post.url or ""
            )
            
            if not analysis_result:
                logger.warning(f"帖子 {post_id} 的AI分析结果为空")
                # 标记为已处理，但不创建产品
                post.processed = True
                self.db.commit()
                return None
            
            # 创建产品
            product = self._create_product_from_analysis(post, analysis_result)
            
            # 处理标签
            if analysis_result.tags:
                await self._process_tags(product, analysis_result.tags)
            
            # 标记帖子为已处理
            post.processed = True
            self.db.commit()
            
            logger.info(f"成功处理帖子 {post_id}，创建产品记录 {product.id}")
            return product
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"处理帖子 {post_id} 时出错: {e}")
            # 记录详细的错误信息
            import traceback
            logger.error(traceback.format_exc())
            return None
    
    def _create_product_from_analysis(self, post: Post, analysis: AIAnalysisResult) -> Product:
        """
        从AI分析结果创建产品记录
        
        Args:
            post: 关联的帖子
            analysis: AI分析结果
            
        Returns:
            创建的产品对象
        """
        # 检查是否已有关联产品
        if post.product:
            # 更新现有产品
            product = post.product
            product.name = analysis.name or post.title
            product.description = analysis.description
            product.problem_solved = analysis.problem_solved
            product.target_audience = analysis.target_audience
            product.competitive_advantage = analysis.competitive_advantage
            product.potential_competitors = analysis.potential_competitors
            product.business_model = analysis.business_model
            
        else:
            # 创建新产品
            product = Product(
                post_id=post.id,
                name=analysis.name or post.title,
                description=analysis.description,
                problem_solved=analysis.problem_solved,
                target_audience=analysis.target_audience,
                competitive_advantage=analysis.competitive_advantage,
                potential_competitors=analysis.potential_competitors,
                business_model=analysis.business_model
            )
            self.db.add(product)
            
        # 保存更改
        self.db.commit()
        self.db.refresh(product)
        
        return product
    
    async def _process_tags(self, product: Product, tag_names: List[str]) -> None:
        """
        处理产品标签
        
        Args:
            product: 产品对象
            tag_names: 标签名称列表
        """
        # 清除现有标签关联
        product.tags = []
        
        # 处理每个标签
        for tag_name in tag_names:
            if not tag_name or len(tag_name.strip()) == 0:
                continue
                
            # 规范化标签名称
            normalized_name = tag_name.strip().lower()
            
            # 查找或创建标签
            tag = self.db.query(Tag).filter(Tag.name == normalized_name).first()
            if not tag:
                tag = Tag(name=normalized_name)
                self.db.add(tag)
                self.db.commit()
                self.db.refresh(tag)
            
            # 添加标签关联
            product.tags.append(tag)
        
        # 保存更改
        self.db.commit()
    
    async def process_unprocessed_posts(self, min_points: int = 5, limit: Optional[int] = None) -> int:
        """
        处理所有未处理且符合条件的帖子
        
        Args:
            min_points: 最低点赞数要求
            limit: 最大处理数量，None表示处理所有符合条件的帖子
            
        Returns:
            成功处理的帖子数量
        """
        # 获取未处理且符合点赞数要求的帖子
        query = self.db.query(Post).filter(
            Post.processed == False,
            Post.points >= min_points
        )
        
        # 如果设置了limit，则限制数量
        if limit:
            posts = query.limit(limit).all()
        else:
            posts = query.all()
        
        logger.info(f"找到 {len(posts)} 条符合条件的未处理帖子")
        processed_count = 0
        
        # 处理每个帖子
        for post in posts:
            logger.info(f"正在处理帖子 {post.id}: {post.title}")
            product = await self.process_post(post.id)
            if product:
                processed_count += 1
                logger.info(f"成功处理帖子 {post.id}，当前进度: {processed_count}/{len(posts)}")
        
        return processed_count 