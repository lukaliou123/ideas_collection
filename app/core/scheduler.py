"""
调度器模块 - 管理系统定时任务
"""
import asyncio
import logging
import os
from typing import Dict, Any, Callable, Optional, Coroutine
from datetime import datetime

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.jobstores.memory import MemoryJobStore
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.triggers.cron import CronTrigger
from apscheduler.executors.pool import ThreadPoolExecutor

from app.core.config import settings
from app.utils.logger import logger

class TaskScheduler:
    """任务调度器，负责管理系统内的定时任务"""
    
    def __init__(self):
        """初始化调度器"""
        # 配置任务存储
        # 对于 PostgreSQL 使用数据库存储，对于 SQLite 使用内存存储（避免文件权限问题）
        try:
            if settings.is_postgresql:
                # PostgreSQL：使用数据库持久化存储
                jobstores = {
                    'default': SQLAlchemyJobStore(url=settings.DATABASE_URL)
                }
                logger.info("调度器使用 PostgreSQL 存储任务")
            else:
                # SQLite 或其他：使用内存存储（重启后任务会重新注册）
                jobstores = {
                    'default': MemoryJobStore()
                }
                logger.info("调度器使用内存存储任务（非持久化）")
        except Exception as e:
            logger.warning(f"初始化调度器存储失败，使用内存存储: {e}")
            jobstores = {
                'default': MemoryJobStore()
            }
        
        # 配置执行器
        executors = {
            'default': ThreadPoolExecutor(max_workers=5)
        }
        
        # 配置作业默认值
        job_defaults = {
            'coalesce': True,       # 合并执行错过的任务
            'max_instances': 3,     # 同一个任务的最大实例数
            'misfire_grace_time': 60 * 60  # 任务错过执行时间的宽限期（秒）
        }
        
        # 创建调度器
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone='Asia/Shanghai'
        )
        
        # 设置日志级别
        logging.getLogger('apscheduler').setLevel(logging.WARNING)
    
    def start(self):
        """启动调度器"""
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("任务调度器已启动")
    
    def shutdown(self):
        """关闭调度器"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("任务调度器已关闭")
    
    def add_job(self, 
                func: Callable, 
                job_id: str, 
                interval_seconds: Optional[int] = None,
                cron_expression: Optional[str] = None,
                job_name: Optional[str] = None, 
                replace_existing: bool = True,
                **kwargs) -> str:
        """
        添加定时任务
        
        Args:
            func: 要执行的函数
            job_id: 任务ID
            interval_seconds: 任务执行间隔（秒）
            cron_expression: Cron表达式 (例如 "0 10 * * *" 表示每天上午10点)
            job_name: 任务名称
            replace_existing: 是否替换同ID的现有任务
            **kwargs: 传递给任务函数的参数
            
        Returns:
            任务ID
        """
        if cron_expression:
            # 使用Cron触发器
            trigger = CronTrigger.from_crontab(cron_expression)
            schedule_desc = f"cron表达式: {cron_expression}"
        elif interval_seconds:
            # 使用间隔触发器
            trigger = IntervalTrigger(seconds=interval_seconds)
            schedule_desc = f"执行间隔: {interval_seconds}秒"
        else:
            # 默认使用间隔触发器，每小时执行一次
            trigger = IntervalTrigger(seconds=3600)
            schedule_desc = "执行间隔: 3600秒（默认）"
        
        job = self.scheduler.add_job(
            func=func,
            trigger=trigger,
            id=job_id,
            name=job_name or job_id,
            replace_existing=replace_existing,
            kwargs=kwargs
        )
        
        logger.info(f"已添加定时任务: {job_id}, {schedule_desc}")
        return job.id
    
    def remove_job(self, job_id: str) -> bool:
        """
        移除定时任务
        
        Args:
            job_id: 任务ID
            
        Returns:
            是否成功移除
        """
        try:
            self.scheduler.remove_job(job_id)
            logger.info(f"已移除定时任务: {job_id}")
            return True
        except Exception as e:
            logger.error(f"移除任务 {job_id} 失败: {e}")
            return False
    
    def get_jobs(self) -> list:
        """获取所有任务信息"""
        return self.scheduler.get_jobs()

# 创建全局调度器实例
scheduler = TaskScheduler() 