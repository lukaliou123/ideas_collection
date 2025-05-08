#!/usr/bin/env python
"""
批量分析帖子生成产品信息的脚本
"""
import asyncio
import sys
import os
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.database import SessionLocal
from app.services.product_service import ProductService
from app.utils.logger import logger
from sqlalchemy import text

async def get_unprocessed_posts_count(db):
    """获取未处理帖子数量"""
    result = db.execute(text("SELECT COUNT(*) FROM posts WHERE processed = 0"))
    return result.scalar()

async def main():
    """脚本主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='批量分析帖子生成产品信息')
    parser.add_argument('--min-points', type=int, default=5, 
                        help='分析帖子的最低点赞数要求 (默认: 5)')
    parser.add_argument('--limit', type=int, default=0,
                        help='处理的最大帖子数量，0表示不限制 (默认: 0)')
    args = parser.parse_args()

    logger.info(f"开始批量分析帖子，最低点赞数要求: {args.min_points}")
    
    # 创建数据库会话
    db = SessionLocal()
    
    try:
        # 获取未处理帖子总数
        unprocessed_count = await get_unprocessed_posts_count(db)
        print(f"发现 {unprocessed_count} 条未处理的帖子")
        
        if unprocessed_count == 0:
            print("没有需要处理的帖子，退出程序")
            return
        
        # 调用ProductService执行批量处理
        service = ProductService(db)
        
        # 处理帖子
        if args.limit > 0:
            print(f"将处理最多 {args.limit} 条帖子...")
        else:
            print("将处理所有符合条件的帖子...")
            
        processed_count = await service.process_unprocessed_posts(
            min_points=args.min_points,
            limit=args.limit if args.limit > 0 else None
        )
        
        # 输出结果
        logger.info(f"处理完成，成功分析了 {processed_count} 条帖子")
        print(f"成功分析了 {processed_count} 条帖子并生成产品信息")
        
        # 查询剩余未处理数量
        remaining = await get_unprocessed_posts_count(db)
        if remaining > 0:
            print(f"还有 {remaining} 条帖子未处理")
        
    except Exception as e:
        logger.error(f"处理过程中出错: {e}")
        print(f"错误: {e}")
        # 详细错误信息
        import traceback
        traceback.print_exc()
    finally:
        # 关闭数据库会话
        db.close()

if __name__ == "__main__":
    # 运行异步主函数
    asyncio.run(main()) 