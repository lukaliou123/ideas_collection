"""
产品处理脚本 - 使用AI分析帖子并提取产品信息
"""
import sys
import os
import asyncio
import argparse

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.database import SessionLocal
from app.core.config import settings
from app.services.product_service import ProductService
from app.models.posts import Post
from app.utils.logger import logger

async def process_post(post_id: int = None):
    """处理指定ID的帖子，如果没有指定ID则处理所有未处理的帖子"""
    db = SessionLocal()
    try:
        service = ProductService(db)
        
        if post_id:
            # 处理指定帖子
            logger.info(f"开始处理帖子 ID: {post_id}")
            post = db.query(Post).filter(Post.id == post_id).first()
            
            if not post:
                logger.error(f"未找到ID为 {post_id} 的帖子")
                return
                
            product = await service.process_post(post_id)
            if product:
                logger.info(f"帖子处理成功! 产品: {product.name}")
            else:
                logger.warning(f"帖子处理失败")
                
        else:
            # 处理所有未处理的帖子
            min_points = settings.AI_ANALYSIS_MIN_POINTS
            logger.info(f"开始处理所有未处理的帖子 (最低 {min_points} 点赞)")
            
            processed_count = await service.process_unprocessed_posts(min_points)
            logger.info(f"处理完成，共处理 {processed_count} 篇帖子")
            
    except Exception as e:
        logger.error(f"处理产品时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="使用AI处理帖子并提取产品信息")
    
    parser.add_argument(
        "--post-id", 
        type=int,
        help="指定要处理的帖子ID，如果不指定则处理所有未处理的帖子"
    )
    
    args = parser.parse_args()
    
    asyncio.run(process_post(args.post_id)) 