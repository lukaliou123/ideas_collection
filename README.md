# 创业产品信息收集系统

自动化收集、分析和存储来自HackerNews、Indie Hackers等网站的创业产品信息与讨论的系统。

## 1. 项目概述

### 目标
构建一个自动化系统，从多个网络来源收集应用开发和创业相关的产品信息，使用AI进行分析和总结，并存储到数据库中供后续查询和分析。

### 核心功能
- 自动爬取多个信息源的创业和产品相关内容
- 按特定条件(如点赞数、评论数)过滤内容
- 使用LLM进行内容总结和分类
- 结构化存储数据
- 提供简单的查询和展示界面

## 2. 系统架构

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│  数据源模块  │────▶│  处理模块   │────▶│  存储模块   │
└─────────────┘     └─────────────┘     └─────────────┘
       ▲                   │                   │
       └───────────────────┘                   ▼
                                        ┌─────────────┐
                                        │  展示模块   │
                                        └─────────────┘
```

## 3. 技术栈

- **后端**: Python 3.9+
- **Web框架**: FastAPI
- **数据库**: SQLite + SQLAlchemy ORM
- **定时任务**: APScheduler
- **爬虫工具**: Requests, BeautifulSoup4, HTTPX
- **AI接口**: OpenAI API (GPT模型)
- **前端**: HTML, CSS, JavaScript (简单UI框架如Bootstrap)
- **部署**: Docker (可选)
- **LLM可观测性**: Langfuse (可选)

## 3.1. Langfuse 集成说明

Langfuse 提供了一个监控和分析 LLM API 调用的平台，集成了以下功能：

- **追踪 LLM 调用**：记录所有 LangChain 框架的 LLM 调用
- **成本监控**：跟踪 API 调用的花费和使用量
- **性能分析**：查看延迟、成功率和错误统计
- **调试**：通过可视化界面检查 LLM 调用链的每个步骤
- **比较模型和提示**：对比不同的提示和模型的效果

主要应用场景包括：
- 产品分析（`analyze_product`）
- 标签生成（`generate_tags`）
- 概念图片提示词生成（`generate_product_image`）

## 4. 数据模型

```
Sources
- id: Integer (PK)
- name: String (如"HackerNews", "IndieHackers")
- url: String
- active: Boolean

Posts
- id: Integer (PK)
- source_id: Integer (FK -> Sources)
- original_id: String (源站上的ID)
- title: String
- url: String
- content: Text
- author: String
- published_at: DateTime
- points: Integer
- comments_count: Integer
- collected_at: DateTime
- processed: Integer (0:未处理, 1:已处理, 2:处理失败)

Products
- id: Integer (PK)
- post_id: Integer (FK -> Posts)
- name: String
- description: Text
- problem_solved: Text
- target_audience: Text
- competitive_advantage: Text
- potential_competitors: Text
- business_model: Text

Tags
- id: Integer (PK)
- name: String

product_tags
- product_id: Integer (FK -> Products)
- tag_id: Integer (FK -> Tags)
```

## 5. 开发步骤

### 阶段1: 基础架构和数据获取 (估计2天)

1. **项目设置**
   - 创建项目目录结构
   - 设置虚拟环境和依赖管理
   - 创建基础配置文件

2. **数据库模型实现**
   - 使用SQLAlchemy实现数据模型
   - 创建数据库迁移脚本
   - 实现基础CRUD操作

3. **HackerNews API集成**
   - 实现HN API客户端
   - 获取和过滤"Show HN"帖子
   - 存储到数据库

### 阶段2: 爬虫和内容处理 (估计3天)

4. **Indie Hackers爬虫**
   - 实现网页爬取逻辑
   - 提取帖子和相关元数据
   - 实现爬虫限速和错误处理

5. **定时任务系统**
   - 设置APScheduler
   - 实现各数据源的定时抓取任务
   - 添加日志和监控

6. **内容去重和规范化**
   - 实现URL和内容去重机制
   - 标准化不同来源的数据格式

### 阶段3: AI集成和内容分析 (估计2天)

7. **OpenAI API集成**
   - 设置API访问
   - 创建提示模板
   - 实现错误处理和重试机制

8. **内容分析模块**
   - 实现内容摘要生成
   - 提取产品信息(问题、解决方案、目标受众等)
   - 自动标签生成

### 阶段4: Web界面和部署 (估计3天)

9. **FastAPI后端**
   - 实现REST API端点
   - 添加过滤和分页功能
   - 实现简单认证(可选)

10. **简易前端**
    - 实现基本列表和详情页面
    - 添加过滤和搜索功能
    - 响应式设计

11. **部署准备**
    - 创建Docker配置(可选)
    - 编写部署文档
    - 实现基本监控

## 6. 潜在挑战和解决方案

1. **爬虫限制**
   - 问题: 网站可能有反爬虫措施
   - 解决: 实现请求间隔、随机UA、代理IP池

2. **AI成本控制**
   - 问题: 大量内容处理可能导致API成本过高
   - 解决: 批量处理、缓存相似结果、使用更经济的模型

3. **数据质量**
   - 问题: 低质量或不相关的信息
   - 解决: 多层次过滤、人工反馈机制

4. **系统可扩展性**
   - 问题: 随着数据源增加，系统复杂度上升
   - 解决: 模块化设计、适配器模式、异步处理

## 7. 未来扩展计划

1. 添加更多数据源(Product Hunt, Reddit等)
2. 实现更复杂的分析和推荐系统
3. 添加用户反馈和标注功能
4. 开发邮件通知或者RSS订阅功能
5. 提供API接口供第三方应用使用

## 8. 如何开始

1. 克隆项目仓库
2. 安装依赖: `pip install -r requirements.txt`
3. 配置环境变量 (API密钥等)
   - 创建一个 `.env` 文件，并参考 `.env.example` (如果项目中有的话) 或以下内容进行配置:
     ```
     OPENAI_API_KEY="your_openai_api_key"
     # ... 其他已有的环境变量 ...

     # Langfuse (可选, 用于LLM可观测性)
     LANGFUSE_PUBLIC_KEY="your_langfuse_public_key"
     LANGFUSE_SECRET_KEY="your_langfuse_secret_key"
     LANGFUSE_HOST="https://cloud.langfuse.com" # 如果使用自托管 Langfuse，请修改此地址
     ```
4. 初始化数据库: `python scripts/init_db.py`
5. 运行开发服务器: `python main.py`

## 9. 项目结构

```
project/
├── app/
│   ├── api/             # FastAPI 路由和端点
│   ├── core/            # 配置和共享组件
│   ├── models/          # 数据库模型
│   ├── scrapers/        # 各网站爬虫
│   ├── services/        # 业务逻辑
│   └── utils/           # 工具函数
├── scripts/             # 脚本工具
├── static/              # 静态文件
├── templates/           # HTML模板
├── tests/               # 测试文件
├── .env                 # 环境变量
├── main.py              # 应用入口
└── requirements.txt     # 依赖清单
``` 