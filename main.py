"""
创业产品信息收集系统 - 主应用入口
"""
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
import argparse
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建FastAPI应用
app = FastAPI(
    title="创业产品信息收集系统",
    description="自动化收集、分析和存储来自HackerNews、Indie Hackers等网站的创业产品信息与讨论的系统。",
    version="0.1.0"
)

# 配置静态文件
app.mount("/static", StaticFiles(directory="static"), name="static")

# 配置模板
templates = Jinja2Templates(directory="templates")

# 导入路由
from app.api.endpoints import router as api_router
app.include_router(api_router)

# 导入任务服务
from app.services.task_service import TaskService
from app.core.config import settings

@app.get("/api")
async def api_root():
    """API根路由，返回API基本信息"""
    return {
        "message": "欢迎使用创业产品信息收集系统API",
        "docs_url": "/docs"
    }

@app.on_event("startup")
async def startup_event():
    """应用启动时的事件处理"""
    import logging
    logger = logging.getLogger("app")
    
    try:
        logger.info("=" * 60)
        logger.info("应用启动中...")
        logger.info(f"数据库 URL: {settings.DATABASE_URL[:20]}...")
        logger.info(f"启用调度器: {settings.ENABLE_SCHEDULER}")
        
        # 自动初始化数据库（如果表不存在）
        try:
            from app.core.database import init_db
            logger.info("检查数据库表...")
            init_db()
            logger.info("数据库表检查/初始化完成")
        except Exception as db_error:
            logger.warning(f"数据库初始化出现问题（可能已存在）: {db_error}")
        
        # 如果启用了定时任务，则启动调度器
        if settings.ENABLE_SCHEDULER:
            logger.info("开始注册定时任务...")
            # 注册所有任务
            TaskService.register_tasks()
            logger.info("开始启动调度器...")
            # 启动调度器
            TaskService.start_scheduler()
            logger.info("调度器启动成功")
        
        logger.info("应用启动完成")
        logger.info("=" * 60)
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"❌ 应用启动失败: {e}")
        logger.error("=" * 60)
        import traceback
        traceback.print_exc()
        # 不要抛出异常，让应用继续运行（但调度器可能不可用）
        logger.warning("应用将在没有调度器的情况下继续运行")

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的事件处理"""
    import logging
    logger = logging.getLogger("app")
    
    try:
        logger.info("应用关闭中...")
        # 关闭调度器
        TaskService.shutdown_scheduler()
        logger.info("应用关闭完成")
    except Exception as e:
        logger.error(f"应用关闭时出错: {e}")

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="运行创业产品信息收集系统")
    parser.add_argument(
        "--no-scheduler",
        action="store_true",
        help="禁用定时任务调度器"
    )
    args = parser.parse_args()
    
    # 设置是否启用定时任务
    if args.no_scheduler:
        os.environ["ENABLE_SCHEDULER"] = "False"
    
    # 从环境变量获取调试模式设置，默认为False
    debug = os.getenv("DEBUG", "False").lower() == "true"
    
    # 从环境变量获取端口设置，默认为8000
    port = int(os.getenv("PORT", "8000"))
    
    # 启动服务器
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=debug) 