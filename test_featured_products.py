"""
测试精选产品功能
"""
import asyncio
import traceback
from app.services.product_service import ProductService
from app.core.database import SessionLocal
from app.utils.logger import logger

async def main():
    db = SessionLocal()
    try:
        logger.info("初始化ProductService...")
        service = ProductService(db)
        
        # 获取精选产品
        logger.info("获取精选产品...")
        featured_products = await service.get_featured_products()
        logger.info(f"找到 {len(featured_products)} 个精选产品:")
        for i, product in enumerate(featured_products, 1):
            logger.info(f"{i}. {product.name} (ID: {product.id}) - 概念图URL: {product.concept_image_url or '无'}")
        
        # 生成产品概念图
        logger.info("\n生成产品概念图...")
        logger.info("使用LangChain API进行图片生成...")
        count = await service.generate_images_for_featured_products()
        logger.info(f"为 {count} 个产品生成了概念图")
        
        # 再次获取精选产品，查看更新后的图片URL
        if count > 0:
            logger.info("\n更新后的产品概念图:")
            featured_products = await service.get_featured_products()
            for i, product in enumerate(featured_products, 1):
                logger.info(f"{i}. {product.name} (ID: {product.id}) - 概念图URL: {product.concept_image_url or '无'}")
    
    except Exception as e:
        logger.error(f"测试过程中发生错误: {e}")
        logger.error(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(main()) 