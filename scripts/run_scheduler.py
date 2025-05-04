"""
启动定时任务调度器脚本
"""
import sys
import os
import time
import signal
import argparse
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import settings
from app.core.scheduler import scheduler
from app.services.task_service import TaskService
from app.utils.logger import logger

# 全局运行标志
running = True

def handle_signal(signum, frame):
    """处理信号，优雅关闭"""
    global running
    print(f"\n接收到信号 {signum}，准备停止调度器...")
    running = False

def setup_signal_handlers():
    """设置信号处理器"""
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

def run_scheduler(is_daemon=False):
    """运行任务调度器"""
    try:
        # 注册所有任务
        logger.info("正在注册定时任务...")
        TaskService.register_tasks()
        
        # 启动调度器
        logger.info("正在启动任务调度器...")
        TaskService.start_scheduler()
        
        # 显示所有已注册的任务
        jobs = TaskService.get_all_jobs()
        if jobs:
            logger.info(f"已注册 {len(jobs)} 个任务:")
            for job in jobs:
                logger.info(f"  - {job['id']}: 下次执行时间 {job['next_run']}")
        else:
            logger.warning("没有注册任何任务")
        
        # 如果是守护模式，保持运行
        if is_daemon:
            logger.info(f"调度器已启动，按 Ctrl+C 停止")
            while running:
                time.sleep(1)
        
    except Exception as e:
        logger.error(f"运行调度器时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())
        
    finally:
        if is_daemon:
            # 关闭调度器
            logger.info("正在关闭调度器...")
            TaskService.shutdown_scheduler()
            logger.info("调度器已关闭")

def run_once(task_id=None):
    """立即运行指定任务一次"""
    try:
        if task_id == "hackernews" or task_id is None:
            logger.info("开始执行HackerNews数据收集任务...")
            result = TaskService.run_hackernews_collection()
            logger.info(f"任务执行完成，收集了 {result} 条新帖子")
        else:
            logger.error(f"未知任务ID: {task_id}")
            
    except Exception as e:
        logger.error(f"运行任务时出错: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="运行任务调度器")
    
    # 添加命令行参数
    parser.add_argument(
        "--daemon", 
        action="store_true", 
        help="以守护进程模式运行调度器"
    )
    
    parser.add_argument(
        "--run-once", 
        action="store_true", 
        help="立即运行任务一次，而不是启动调度器"
    )
    
    parser.add_argument(
        "--task", 
        type=str, 
        help="指定要运行的任务ID，仅在--run-once时有效"
    )
    
    # 解析命令行参数
    args = parser.parse_args()
    
    # 设置信号处理器
    setup_signal_handlers()
    
    if args.run_once:
        run_once(args.task)
    else:
        run_scheduler(args.daemon) 