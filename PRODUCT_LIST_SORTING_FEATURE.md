## 产品列表排序功能实现方案

### 1. 背景与目标

当前产品列表页面和API仅支持按最新添加排序。本次迭代的目标是实现多种排序方式，包括按热门程度和产品名称排序，以提升用户体验。

### 2. 相关文件分析

- **API 端点 (`app/api/endpoints.py`)**: 产品列表接口需添加排序参数。
- **产品服务 (`app/services/product_service.py`)**: 需封装获取和排序产品列表的逻辑。
- **产品模型 (`app/models/products.py`)**: 包含可用于排序的字段（`name`, `created_at`）。通过关联的 `Post` 模型，可以获取 `points` 和 `comments_count` 用于热门排序。
- **前端模板 (`templates/products.html`)**: 需更新排序选项的链接以传递排序参数。

### 3. 实现方案

#### a. 定义排序枚举

在 `app/api/endpoints.py` (或单独的 `schemas.py` 文件) 中定义排序方式的枚举类：

```python
from enum import Enum

class ProductSortBy(str, Enum):
    latest = "latest"  # 最新添加
    popular = "popular" # 热门程度
    name = "name"     # 名称
```

#### b. 修改 API 端点

在 `app/api/endpoints.py` 中的 `/products` (页面) 和 `/api/products` (API) 路由：

- 添加 `sort_by: Optional[ProductSortBy] = Query(ProductSortBy.latest, description="排序方式")` 查询参数。
- 调用新的 `ProductService.get_products_with_pagination()` 方法获取数据。
- 将当前的排序方式 (`current_sort`) 传递给模板或API响应。

**示例 (`/products` 页面路由修改):**
```python
from app.services.product_service import ProductService # 确保导入
# ...

@router.get("/products")
async def products_page(
    request: Request, 
    page: int = Query(1, ge=1),
    tag: Optional[str] = None,
    source: Optional[str] = None,
    sort_by: Optional[ProductSortBy] = Query(ProductSortBy.latest, description="排序方式"), # 新增
    db: Session = Depends(get_db)
):
    per_page = 12
    product_service = ProductService(db) # 初始化服务
    
    products_data = await product_service.get_products_with_pagination(
        page=page,
        per_page=per_page,
        tag_name=tag,
        source_name=source,
        sort_by_value=sort_by.value if sort_by else ProductSortBy.latest.value
    )
    
    # 获取所有标签供过滤使用
    tags_list = db.query(Tag).all() # 避免变量名冲突
    
    # 获取数据源列表供过滤使用
    sources_list = db.query(Source).filter(Source.active == True).all()
    
    return templates.TemplateResponse(
        "products.html",
        {
            "request": request, 
            "products": products_data["products"],
            "tags": tags_list,
            "sources": sources_list,
            "current_page": page,
            "total_pages": products_data["pages"],
            "total_products": products_data["total"],
            "filter_tag": tag,
            "filter_source": source,
            "current_sort": products_data["sort_by"] # 新增
        }
    )
```

**示例 (`/api/products` API路由修改):**
```python
@router.get("/api/products", response_model=dict)
async def api_products(
    page: int = Query(1, ge=1),
    per_page: int = Query(10, ge=1, le=100),
    tag: Optional[str] = None,
    source: Optional[str] = None,
    sort_by: Optional[ProductSortBy] = Query(ProductSortBy.latest, description="排序方式"), # 新增
    db: Session = Depends(get_db)
):
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
```

#### c. 更新产品服务 (`app/services/product_service.py`)

- 创建 `get_products_with_pagination` 方法处理产品列表的获取、过滤、排序和分页逻辑。

```python
from sqlalchemy import desc, asc # 导入 asc
from app.models.posts import Post # 确保 Post 模型已导入
from app.models.tags import Tag # 确保 Tag 模型已导入
from app.models.sources import Source # 确保 Source 模型已导入
import math # 导入 math

class ProductService:
    def __init__(self, db: Session):
        self.db = db
        # ... (其他现有方法) ...

    async def get_products_with_pagination(
        self,
        page: int = 1,
        per_page: int = 12,
        tag_name: Optional[str] = None,
        source_name: Optional[str] = None,
        sort_by_value: str = "latest"
    ) -> Dict[str, Any]:
        query = self.db.query(Product)

        if tag_name:
            query = query.join(Product.tags).filter(Tag.name == tag_name)
        
        if source_name:
            # 确保 Product 和 Post 之间有正确的关联，并且 Post 和 Source 之间有关联
            query = query.join(Product.post).join(Post.source).filter(Source.name == source_name)

        # 应用排序
        if sort_by_value == "popular":
            # 确保 Product 和 Post 之间有正确的关联 'post'
            query = query.join(Product.post).order_by(desc(Post.points + Post.comments_count))
        elif sort_by_value == "name":
            query = query.order_by(asc(Product.name))
        else: # "latest" or default
            query = query.order_by(desc(Product.created_at))

        total = query.count()
        pages = math.ceil(total / per_page)
        offset = (page - 1) * per_page
        products_result = query.offset(offset).limit(per_page).all()
        
        products_api_format = [
            {
                "id": p.id,
                "name": p.name,
                "description": p.description,
                "problem_solved": p.problem_solved,
                "target_audience": p.target_audience,
                "tags": [t.name for t in p.tags],
                "source": p.post.source.name if p.post and p.post.source else None,
                "created_at": p.created_at.isoformat() if p.created_at else None,
                "points": p.post.points if p.post else 0
            }
            for p in products_result
        ]

        return {
            "products": products_result, # 用于模板渲染
            "products_api_format": products_api_format, # 用于API响应
            "total": total,
            "pages": pages,
            "page": page,
            "sort_by": sort_by_value
        }
    # ... (其他现有方法) ...
```

#### d. 更新前端模板 (`templates/products.html`)

- 修改排序下拉菜单的链接，通过 URL 参数传递 `sort_by` 的值。
- 更新分页链接，确保在翻页时保留当前的排序方式和过滤条件。

```html
<!-- templates/products.html -->
<div class="dropdown">
    <button class="btn btn-outline-secondary btn-sm dropdown-toggle" type="button" id="sortDropdown" data-bs-toggle="dropdown">
        排序方式: 
        {% if current_sort == "latest" %}最新添加
        {% elif current_sort == "popular" %}热门程度
        {% elif current_sort == "name" %}名称
        {% else %}最新添加
        {% endif %}
    </button>
    <ul class="dropdown-menu" aria-labelledby="sortDropdown">
        <li><a class="dropdown-item {% if current_sort == 'latest' %}active{% endif %}" href="?sort_by=latest{% if filter_tag %}&tag={{ filter_tag }}{% endif %}{% if filter_source %}&source={{ filter_source }}{% endif %}">最新添加</a></li>
        <li><a class="dropdown-item {% if current_sort == 'popular' %}active{% endif %}" href="?sort_by=popular{% if filter_tag %}&tag={{ filter_tag }}{% endif %}{% if filter_source %}&source={{ filter_source }}{% endif %}">热门程度</a></li>
        <li><a class="dropdown-item {% if current_sort == 'name' %}active{% endif %}" href="?sort_by=name{% if filter_tag %}&tag={{ filter_tag }}{% endif %}{% if filter_source %}&source={{ filter_source }}{% endif %}">名称</a></li>
    </ul>
</div>

<!-- 分页链接示例修改 -->
<a class="page-link" href="/products?page={{ current_page - 1 }}{% if filter_tag %}&tag={{ filter_tag }}{% endif %}{% if filter_source %}&source={{ filter_source }}{% endif %}{% if current_sort %}&sort_by={{ current_sort }}{% endif %}" aria-label="上一页">
    <span aria-hidden="true">&laquo;</span>
</a>
```

### 4. 讨论点与优化

- **热门程度定义**: 当前使用 `Post.points + Post.comments_count`。可以根据实际效果调整，例如引入时间衰减因素。
- **性能**: 对于大量数据，`join` 操作和动态排序可能会影响性能。后期可以考虑添加数据库索引（例如在 `products.name`, `posts.points`, `posts.comments_count` 等字段上）。
- **代码复用**: `ProductService` 中的 `get_products_with_pagination` 方法可以被 `/products` 页面路由和 `/api/products` API 路由共用，提高了代码的复用性。

这个方案为产品列表增加了灵活的排序功能，并对代码结构进行了一定的优化。 