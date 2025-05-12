# 首页精选产品展示功能实现方案

## 1. 概述

根据需求，我们需要在首页展示当日更新中点赞数最高的三个产品，并为其生成产品概念图，以增强视觉吸引力。这些精选产品需要每日定时更新。

## 2. 数据模型调整

首先，需要为产品模型新增一个字段，用于存储AI生成的概念图URL：

```python
# app/models/products.py
concept_image_url = Column(String(1000), nullable=True)  # 产品概念图URL
```

## 3. AI图像生成服务

我们需要增强现有AI服务，添加使用DALL-E 2生成产品概念图的功能：

```python
# app/services/ai_service.py 或 app/services/ai_service_langchain.py 中添加

async def generate_product_image(self, product_name: str, product_description: str) -> Optional[str]:
    """
    为产品生成概念图
    
    Args:
        product_name: 产品名称
        product_description: 产品描述
        
    Returns:
        生成的图片URL
    """
    try:
        prompt = f"A clean, modern product concept image for '{product_name}': {product_description[:200]}. Minimal, professional design."
        
        response = await self.openai_client.images.generate(
            model="dall-e-2",
            prompt=prompt,
            size="512x512",
            quality="standard",
            n=1
        )
        
        image_url = response.data[0].url
        return image_url
    except Exception as e:
        logger.error(f"生成产品概念图失败: {e}")
        return None
```

## 4. 产品服务增强

在ProductService中添加获取精选产品的方法：

```python
# app/services/product_service.py

async def get_featured_products(self, limit: int = 3) -> List[Dict[str, Any]]:
    """
    获取精选产品（当日更新中点赞数最高的产品）
    
    Args:
        limit: 要获取的产品数量
        
    Returns:
        精选产品列表
    """
    # 获取今天的日期（0点0分0秒）
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # 查询今天创建或更新的产品，按点赞数排序
    query = self.db.query(Product)\
        .join(Product.post)\
        .filter(Product.created_at >= today)\
        .order_by(desc(Post.points + Post.comments_count))\
        .limit(limit)
    
    featured_products = query.all()
    
    # 如果今天没有足够的新产品，则获取历史数据补充
    if len(featured_products) < limit:
        remaining = limit - len(featured_products)
        existing_ids = [p.id for p in featured_products]
        
        backup_products = self.db.query(Product)\
            .join(Product.post)\
            .filter(Product.id.notin_(existing_ids))\
            .order_by(desc(Post.points + Post.comments_count))\
            .limit(remaining)\
            .all()
            
        featured_products.extend(backup_products)
    
    return featured_products
    
async def generate_images_for_featured_products(self) -> int:
    """
    为精选产品生成概念图
    
    Returns:
        成功生成图片的产品数量
    """
    # 获取精选产品
    featured_products = await self.get_featured_products()
    success_count = 0
    
    for product in featured_products:
        # 如果已有图片且不是默认图片，则跳过
        if product.concept_image_url and not product.concept_image_url.endswith('default.png'):
            continue
            
        # 使用AI服务生成图片
        image_url = await self.ai_service.generate_product_image(
            product_name=product.name,
            product_description=product.description or ""
        )
        
        if image_url:
            # 更新产品信息
            product.concept_image_url = image_url
            self.db.commit()
            success_count += 1
    
    return success_count
```

## 5. 定时任务设置

在调度器中添加每日更新精选产品的任务：

```python
# app/core/scheduler.py 的初始化部分或应用启动时

async def update_featured_products():
    """更新精选产品及其概念图"""
    from app.services.product_service import ProductService
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        service = ProductService(db)
        await service.generate_images_for_featured_products()
        logger.info("已更新首页精选产品")
    finally:
        db.close()

# 添加任务，每天上午10点执行
scheduler.add_job(
    func=update_featured_products,
    job_id="update_featured_products",
    cron_expression="0 10 * * *",
    job_name="更新首页精选产品"
)
```

## 6. 接口和页面更新

更新首页路由和模板，以展示精选产品：

```python
# app/api/endpoints.py

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
```

## 7. 首页模板优化

更新首页模板以适应新的设计：

```html
<!-- templates/index.html -->
<div class="row mt-5">
    <div class="col-12 mb-4">
        <h2>精选产品</h2>
    </div>
    
    {% if products %}
        {% for product in products %}
        <div class="col-md-4">
            <div class="featured-product-card">
                <div class="product-image">
                    {% if product.concept_image_url %}
                    <img src="{{ product.concept_image_url }}" alt="{{ product.name }}" class="img-fluid rounded">
                    {% else %}
                    <div class="placeholder-image">
                        <i class="bi bi-image"></i>
                    </div>
                    {% endif %}
                </div>
                <h3 class="product-title">
                    <a href="/products/{{ product.id }}">{{ product.name }}</a>
                </h3>
                <p class="product-description">{{ product.description|truncate(120) }}</p>
                <div class="mb-2">
                    {% for tag in product.tags[:3] %}
                    <a href="/products?tag={{ tag.name }}" class="tag">{{ tag.name }}</a>
                    {% endfor %}
                </div>
                <div class="product-meta">
                    {% if product.post and product.post.source %}
                    <span class="source-badge source-{{ product.post.source.name|lower }}">{{ product.post.source.name }}</span>
                    {% endif %}
                    <span class="ms-2">{{ product.created_at.strftime('%Y-%m-%d') }}</span>
                    <span class="ms-2">
                        <i class="bi bi-hand-thumbs-up"></i> {{ product.post.points }}
                    </span>
                </div>
            </div>
        </div>
        {% endfor %}
    {% else %}
        <div class="col-12">
            <p>暂无精选产品</p>
        </div>
    {% endif %}
    
    <div class="col-12 mt-4 text-center">
        <a href="/products" class="btn btn-outline-primary">查看更多产品</a>
    </div>
</div>
```

## 8. CSS 样式调整

为精选产品卡片添加特殊样式，以突出显示：

```css
.featured-product-card {
    background-color: #fff;
    border-radius: 12px;
    box-shadow: 0 8px 16px rgba(0,0,0,0.1);
    padding: 20px;
    height: 100%;
    transition: transform 0.3s, box-shadow 0.3s;
    position: relative;
    overflow: hidden;
}

.featured-product-card:hover {
    transform: translateY(-10px);
    box-shadow: 0 12px 20px rgba(0,0,0,0.15);
}

.product-image {
    height: 180px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin-bottom: 15px;
    overflow: hidden;
    border-radius: 8px;
    background-color: #f8f9fa;
}

.product-image img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.placeholder-image {
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 3rem;
    color: #dee2e6;
}
```

## 9. 实现步骤

1. 添加产品概念图字段（需要数据库迁移）
2. 实现AI图像生成服务
3. 扩展ProductService以支持精选产品功能
4. 设置定时任务执行精选产品更新
5. 更新首页路由和模板
6. 测试并部署

## 10. 技术考量

### 图片存储
为了避免依赖OpenAI的临时URLs，我们应考虑将生成的图片下载并存储到本地或云存储服务。

### 性能优化
为了提高页面加载速度，我们可以考虑使用缓存机制缓存精选产品列表，每天更新一次。

### 成本控制
使用DALL-E 2的512×512尺寸可以平衡图片质量和API成本，每次生成的费用约为0.016美元，对于每天更新3张图片，月成本大约为1.44美元。 