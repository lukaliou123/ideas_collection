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
    # 如果启用了定时任务，则启动调度器
    if settings.ENABLE_SCHEDULER:
        # 注册所有任务
        TaskService.register_tasks()
        # 启动调度器
        TaskService.start_scheduler()

@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时的事件处理"""
    # 关闭调度器
    TaskService.shutdown_scheduler()

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
    
    # 启动服务器
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=debug) 