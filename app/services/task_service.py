"""
任务服务模块 - 管理系统所有数据收集任务
"""
import asyncio
import sys
import functools
from typing import Dict, Any, Callable, Coroutine
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.core.scheduler import scheduler
from app.core.config import settings
from app.services.hackernews_service import HackerNewsService
from app.services.product_service import ProductService
from app.utils.logger import logger

class TaskService:
    """任务服务，负责注册和管理所有数据收集任务"""
    
    @staticmethod
    def register_tasks():
        """注册所有定时任务"""
        TaskService.register_hackernews_task()
        
        # 如果启用了AI分析，注册产品处理任务
        if settings.ENABLE_AI_ANALYSIS:
            TaskService.register_product_processing_task()
        
        # 未来添加更多任务
        # TaskService.register_indiehackers_task()
        
        logger.info("所有定时任务已注册")
    
    @staticmethod
    def register_hackernews_task():
        """注册HackerNews数据收集任务"""
        # 使用cron触发器，设置为每天早上10点执行
        scheduler.add_job(
            func=TaskService.run_hackernews_collection,
            job_id="collect_hackernews",
            cron_expression="0 10 * * *", 
            job_name="HackerNews每日收集"
        )
        
        logger.info("已注册HackerNews数据收集任务，将在每天上午10:00执行")
    
    @staticmethod
    def register_product_processing_task():
        """注册产品处理任务"""
        # 设置为每天执行一次
        interval = 24 * 60 * 60  # 24小时
        
        scheduler.add_job(
            func=TaskService.run_product_processing,
            job_id="process_products",
            interval_seconds=interval
        )
    
    @staticmethod
    def run_hackernews_collection():
        """执行HackerNews数据收集任务的包装函数"""
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 创建事件循环并执行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 运行异步任务并获取结果
            result = loop.run_until_complete(HackerNewsService.run_collection(db))
            
            # 关闭事件循环
            loop.close()
            
            logger.info(f"HackerNews数据收集任务执行完成，保存了 {result} 条新帖子")
            return result
            
        except Exception as e:
            logger.error(f"执行HackerNews数据收集任务时出错: {e}")
            # 打印完整的异常堆栈
            import traceback
            logger.error(traceback.format_exc())
            return 0
            
        finally:
            db.close()
    
    @staticmethod
    def run_product_processing():
        """执行产品处理任务的包装函数"""
        # 创建数据库会话
        db = SessionLocal()
        
        try:
            # 创建事件循环并执行异步任务
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # 创建产品服务
            service = ProductService(db)
            
            # 运行异步任务并获取结果
            min_points = settings.AI_ANALYSIS_MIN_POINTS
            result = loop.run_until_complete(service.process_unprocessed_posts(min_points))
            
            # 关闭事件循环
            loop.close()
            
            logger.info(f"产品处理任务执行完成，处理了 {result} 条帖子")
            return result
            
        except Exception as e:
            logger.error(f"执行产品处理任务时出错: {e}")
            # 打印完整的异常堆栈
            import traceback
            logger.error(traceback.format_exc())
            return 0
            
        finally:
            db.close()
    
    @staticmethod
    def start_scheduler():
        """启动调度器"""
        scheduler.start()
    
    @staticmethod
    def shutdown_scheduler():
        """关闭调度器"""
        scheduler.shutdown()
    
    @staticmethod
    def get_all_jobs():
        """获取所有任务信息"""
        jobs = scheduler.get_jobs()
        job_info = []
        
        for job in jobs:
            next_run = job.next_run_time.strftime("%Y-%m-%d %H:%M:%S") if job.next_run_time else "未排定"
            job_info.append({
                "id": job.id,
                "name": job.name or job.id,
                "next_run": next_run
            })
            
        return job_info 