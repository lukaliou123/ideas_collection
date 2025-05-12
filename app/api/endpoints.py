"""
API端点
"""
from fastapi import APIRouter, Depends, Request, HTTPException, Query
from fastapi.templating import Jinja2Templates
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
import math
from enum import Enum

from app.core.database import get_db
from app.models.sources import Source
from app.models.posts import Post
from app.models.products import Product
from app.models.tags import Tag
from app.services.product_service import ProductService

# 定义排序方式的枚举类
class ProductSortBy(str, Enum):
    latest = "latest"  # 最新添加
    popular = "popular" # 热门程度
    name = "name"     # 名称

router = APIRouter()

# 配置模板
templates = Jinja2Templates(directory="templates")

@router.get("/")
async def home(request: Request, db: Session = Depends(get_db)):
    """首页视图"""
    # 获取数据源列表
    sources = db.query(Source).filter(Source.active == True).all()
    
    # 获取精选产品
    product_service = ProductService(db)
    featured_products = await product_service.get_featured_products(limit=3)
    
    return templates.TemplateResponse(
        "index.html",
        {
            "request": request, 
            "sources": sources, 
            "products": featured_products,
            "is_featured": True
        }
    )

@router.get("/products")
async def products_page(
    request: Request, 
    page: int = Query(1, ge=1),
    tag: Optional[str] = None,
    source: Optional[str] = None,
    sort_by: Optional[ProductSortBy] = Query(ProductSortBy.latest, description="排序方式"),
    db: Session = Depends(get_db)
):
    """产品列表页"""
    per_page = 12
    product_service = ProductService(db)
    
    products_data = await product_service.get_products_with_pagination(
        page=page,
        per_page=per_page,
        tag_name=tag,
        source_name=source,
        sort_by_value=sort_by.value if sort_by else ProductSortBy.latest.value
    )
    
    # 获取所有标签供过滤使用
    tags = db.query(Tag).all()
    
    # 获取数据源列表供过滤使用
    sources = db.query(Source).filter(Source.active == True).all()
    
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request, 
            "products": products_data["products"],
            "tags": tags,
            "sources": sources,
            "current_page": page,
            "total_pages": products_data["pages"],
            "total_products": products_data["total"],
            "filter_tag": tag,
            "filter_source": source,
            "current_sort": products_data["sort_by"]
        }
    )

@router.get("/products/{product_id}")
async def product_detail(request: Request, product_id: int, db: Session = Depends(get_db)):
    """产品详情页"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="产品不存在")
    
    return templates.TemplateResponse(
        "product_detail.html",
        {"request": request, "product": product}
    )

@router.get("/sources")
async def sources_page(request: Request, db: Session = Depends(get_db)):
    """数据源页面"""
    sources = db.query(Source).all()
    
    # 获取每个来源的帖子数量
    sources_with_counts = []
    for source in sources:
        post_count = db.query(Post).filter(Post.source_id == source.id).count()
        product_count = db.query(Product).join(Post).filter(Post.source_id == source.id).count()
        sources_with_counts.append({
            "source": source,
            "post_count": post_count,
            "product_count": product_count
        })
    
    return templates.TemplateResponse(
        "sources.html",
        {"request": request, "sources_data": sources_with_counts}
    )

# API端点
@router.get("/api/products", response_model=dict)
async def api_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    tag: Optional[str] = None,
    source: Optional[str] = None,
    sort_by: Optional[ProductSortBy] = Query(ProductSortBy.latest, description="排序方式"),
    db: Session = Depends(get_db)
):
    """获取产品列表API"""
    product_service = ProductService(db)
    products_data = await product_service.get_products_with_pagination(
        page=page,
        per_page=per_page,
        tag_name=tag,
        source_name=source,
        sort_by_value=sort_by.value if sort_by else ProductSortBy.latest.value
    )
    
    return {
        "total": products_data["total"],
        "pages": products_data["pages"],
        "page": products_data["page"],
        "per_page": per_page,
        "sort_by": products_data["sort_by"],
        "products": products_data["products_api_format"]
    }

@router.get("/api/products/{product_id}")
async def api_product_detail(product_id: int, db: Session = Depends(get_db)):
    """获取产品详情API"""
    product = db.query(Product).filter(Product.id == product_id).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    result = {
        "id": product.id,
        "name": product.name,
        "description": product.description,
        "problem_solved": product.problem_solved,
        "target_audience": product.target_audience,
        "competitive_advantage": product.competitive_advantage,
        "potential_competitors": product.potential_competitors,
        "business_model": product.business_model,
        "tags": [tag.name for tag in product.tags],
        "post": {
            "id": product.post.id,
            "title": product.post.title,
            "url": product.post.url,
            "author": product.post.author,
            "published_at": product.post.published_at.isoformat() if product.post.published_at else None,
            "points": product.post.points,
            "comments_count": product.post.comments_count,
            "source": product.post.source.name if product.post.source else None
        } if product.post else None,
        "created_at": product.created_at.isoformat() if product.created_at else None
    }
    
    return result

@router.get("/api/tags")
async def api_tags(db: Session = Depends(get_db)):
    """获取所有标签API"""
    tags = db.query(Tag).all()
    
    # 计算每个标签关联的产品数量
    tags_with_counts = []
    for tag in tags:
        product_count = db.query(Product).join(Product.tags).filter(Tag.id == tag.id).count()
        tags_with_counts.append({
            "id": tag.id,
            "name": tag.name,
            "product_count": product_count
        })
    
    return {"tags": tags_with_counts}

@router.get("/api/sources")
async def api_sources(db: Session = Depends(get_db)):
    """获取所有数据源API"""
    sources = db.query(Source).all()
    
    # 计算每个来源的帖子和产品数量
    sources_with_counts = []
    for source in sources:
        post_count = db.query(Post).filter(Post.source_id == source.id).count()
        product_count = db.query(Product).join(Post).filter(Post.source_id == source.id).count()
        sources_with_counts.append({
            "id": source.id,
            "name": source.name,
            "url": source.url,
            "active": source.active,
            "post_count": post_count,
            "product_count": product_count
        })
    
    return {"sources": sources_with_counts}

@router.post("/api/process/{post_id}")
async def api_process_post(post_id: int, db: Session = Depends(get_db)):
    """处理指定帖子API"""
    post = db.query(Post).filter(Post.id == post_id).first()
    
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    service = ProductService(db)
    product = await service.process_post(post_id)
    
    if not product:
        raise HTTPException(status_code=500, detail="Failed to process post")
    
    return {"success": True, "product_id": product.id} 