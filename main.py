"""
创业产品信息收集系统 - 主应用入口
"""
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import os
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

@app.get("/api")
async def api_root():
    """API根路由，返回API基本信息"""
    return {
        "message": "欢迎使用创业产品信息收集系统API",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    # 从环境变量获取调试模式设置，默认为False
    debug = os.getenv("DEBUG", "False").lower() == "true"
    # 启动服务器
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=debug) 