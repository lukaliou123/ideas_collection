"""
API端点
"""
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.sources import Source

router = APIRouter()

# 配置模板
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    """首页视图"""
    # 获取数据源列表
    sources = db.query(Source).filter(Source.active == True).all()
    
    # 在实际应用中，这里还会获取最新的产品列表
    
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "sources": sources}
    ) 