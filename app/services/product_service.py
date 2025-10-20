"""
产品服务模块 - 负责处理产品信息和标签
"""
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from datetime import datetime
from sqlalchemy import desc, asc
import math

from app.models.posts import Post
from app.models.products import Product
from app.models.tag import Tag
from app.models.sources import Source
from app.services.ai_service import AIService, AIAnalysisResult
from app.services.ai_service_langchain import LangChainAIService
from app.utils.logger import logger
from app.core.database import SessionLocal, get_db
from app.core.config import settings

class ProductService:
    """产品服务类，负责处理产品信息和标签"""
    
    def __init__(self, db: Session):
        """初始化服务"""
        self.db = db
        self.ai_service = AIService()
        # 初始化 LangChain AI服务
        self.langchain_ai_service = LangChainAIService(db)
    
    async def get_products_with_pagination(
        self,
        page: int = 1,
        per_page: int = 12,
        tag_name: Optional[str] = None,
        source_name: Optional[str] = None,
        sort_by_value: str = "latest"
    ) -> Dict[str, Any]:
        """
        获取产品列表并应用分页、过滤和排序
        
        Args:
            page: 页码
            per_page: 每页数量
            tag_name: 按标签名称过滤
            source_name: 按来源名称过滤
            sort_by_value: 排序方式
            
        Returns:
            包含产品列表和分页信息的字典
        """
        query = self.db.query(Product)

        # 应用过滤条件
        if tag_name:
            query = query.join(Product.tags).filter(Tag.name == tag_name)
        
        if source_name:
            query = query.join(Product.post).join(Post.source).filter(Source.name == source_name)

        # 应用排序
        if sort_by_value == "popular":
            query = query.join(Product.post).order_by(desc(Post.points + Post.comments_count))
        elif sort_by_value == "name":
            query = query.order_by(asc(Product.name))
        else:  # "latest" 或默认
            query = query.order_by(desc(Product.created_at))

        # 计算总数和页数
        total = query.count()
        pages = math.ceil(total / per_page)
        offset = (page - 1) * per_page
        products_result = query.offset(offset).limit(per_page).all()
        
        # 为API准备格式化的数据
        products_api_format = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "problem_solved": p.problem_solved,
                "target_audience": p.target_audience,
                "tags": [t.name for t in p.tags],
                "source": p.post.source.name if p.post and p.post.source else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "points": p.post.points if p.post else 0
            }
            for p in products_result
        ]

        return {
            "products": products_result,  # 用于模板渲染
            "products_api_format": products_api_format,  # 用于API响应
            "total": total,
            "pages": pages,
            "page": page,
            "sort_by": sort_by_value
        }
    
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
        logger.info(f"Processing tags for product {product.id}. Received tags from AI: {tag_names}")
        
        # 清除现有标签关联
        product.tags = []
        
        # 处理每个标签
        for tag_name in tag_names:
            if not tag_name or len(tag_name.strip()) == 0:
                logger.debug(f"Skipping empty or whitespace tag: '{tag_name}'")
                continue
                
            # 规范化标签名称
            normalized_name = tag_name.strip().lower()
            logger.debug(f"Normalized tag name: '{normalized_name}'")
            
            # 查找或创建标签 (基于规范化名称的唯一性)
            tag = self.db.query(Tag).filter(Tag.normalized_name == normalized_name).first()
            if not tag:
                logger.info(f"Tag '{normalized_name}' not found, creating new tag.")
                # 确保原始名称也被存储，如果需要的话，或者只存储规范化名称并用于显示
                tag = Tag(name=tag_name.strip(), normalized_name=normalized_name) 
                self.db.add(tag)
                # No need for new_tags_added_to_session, commit handles all pending changes.
            else:
                logger.debug(f"Found existing tag: '{normalized_name}' (ID: {tag.id})")

            # 添加标签关联
            if tag not in product.tags:
                product.tags.append(tag)
            else:
                logger.debug(f"Tag '{normalized_name}' already associated with product {product.id}, skipping duplicate append.")

        logger.info(f"Final tag list for product {product.id} before commit: {[t.name for t in product.tags]}")
        # 事务将在调用此方法的地方（例如 process_post）的末尾统一提交，或者根据需要单独提交
        # self.db.commit() # Commit is usually handled by the calling method or at the end of the request.

        # Refresh the product to load the tags correctly after commit
        try:
            self.db.refresh(product)
            logger.info(f"Product {product.id} tags refreshed after commit.")
        except Exception as e:
            logger.error(f"Failed to refresh product {product.id} after tag processing: {e}")
    
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
        # 注意：processed 是 Integer 类型，0=未处理，1=已处理
        query = self.db.query(Post).filter(
            Post.processed == 0,
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
    
    async def get_featured_products(self, limit: int = 3) -> List[Product]:
        """
        获取精选产品（当日更新中点赞数最高的产品）
        
        Args:
            limit: 要获取的产品数量
            
        Returns:
            精选产品列表
        """
        # 获取今天的日期（0点0分0秒）
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # 查询今天创建或更新的产品，按点赞数排序
        query = self.db.query(Product)\
            .join(Product.post)\
            .filter(Product.created_at >= today)\
            .order_by(desc(Post.points + Post.comments_count))\
            .limit(limit)
        
        featured_products = query.all()
        
        # 如果今天没有足够的新产品，则获取历史数据补充
        if len(featured_products) < limit:
            remaining = limit - len(featured_products)
            existing_ids = [p.id for p in featured_products]
            
            backup_products = self.db.query(Product)\
                .join(Product.post)\
                .filter(Product.id.notin_(existing_ids) if existing_ids else True)\
                .order_by(desc(Post.points + Post.comments_count))\
                .limit(remaining)\
                .all()
                
            featured_products.extend(backup_products)
        
        return featured_products
    
    async def generate_images_for_featured_products(self) -> int:
        """
        为精选产品生成概念图
        
        Returns:
            成功生成图片的产品数量
        """
        # 获取精选产品
        featured_products = await self.get_featured_products()
        success_count = 0
        
        for product in featured_products:
            # 如果已有图片且不是默认图片，则跳过
            if product.concept_image_url and not product.concept_image_url.endswith('default.png'):
                continue
                
            # 使用LangChain AI服务生成图片
            try:
                image_url = await self.langchain_ai_service.generate_product_image(
                    product_name=product.name,
                    product_description=product.description or ""
                )
                
                if image_url:
                    # 更新产品信息
                    product.concept_image_url = image_url
                    self.db.commit()
                    success_count += 1
                    logger.info(f"为产品 '{product.name}' (ID:{product.id}) 生成了概念图")
            except Exception as e:
                logger.error(f"为产品 '{product.name}' (ID:{product.id}) 生成概念图时出错: {e}")
                # 如果LangChain服务失败，尝试使用原始服务作为后备
                try:
                    image_url = await self.ai_service.generate_product_image(
                        product_name=product.name,
                        product_description=product.description or ""
                    )
                    
                    if image_url:
                        product.concept_image_url = image_url
                        self.db.commit()
                        success_count += 1
                        logger.info(f"使用备用方法为产品 '{product.name}' (ID:{product.id}) 生成了概念图")
                except Exception as inner_e:
                    logger.error(f"备用方法也无法为产品 '{product.name}' 生成图片: {inner_e}")
        
        return success_count 