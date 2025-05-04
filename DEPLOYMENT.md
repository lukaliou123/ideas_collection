# 部署指南 - 创业产品信息收集系统

本文档提供了部署创业产品信息收集系统的详细步骤，包括本地部署和Docker容器化部署。

## 目录
1. [环境要求](#环境要求)
2. [本地部署](#本地部署)
3. [Docker部署](#docker部署)
4. [环境变量配置](#环境变量配置)
5. [系统监控](#系统监控)
6. [常见问题](#常见问题)

## 环境要求

- Python 3.9+
- SQLite 3
- pip 包管理工具

## 本地部署

### 1. 克隆代码仓库

```bash
git clone <仓库地址>
cd 创业产品信息收集系统
```

### 2. 创建并激活虚拟环境

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 配置环境变量

创建 `.env` 文件或修改现有的 `.env` 文件，设置必要的环境变量（参见[环境变量配置](#环境变量配置)部分）。

### 5. 初始化数据库

```bash
python scripts/init_db.py
```

### 6. 启动应用

```bash
python main.py
```

应用将在 [http://localhost:8000](http://localhost:8000) 上运行。

### 7. 生产环境部署 (使用 Gunicorn, 仅限 Linux/Mac)

在生产环境中，建议使用 Gunicorn 作为 WSGI 服务器：

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app
```

## Docker部署

### 1. 使用Docker Compose (推荐)

确保安装了 Docker 和 Docker Compose，然后执行：

```bash
# 构建并启动容器
docker-compose up -d

# 查看日志
docker-compose logs -f
```

### 2. 使用Dockerfile手动构建

```bash
# 构建Docker镜像
docker build -t startup-product-collector .

# 运行容器
docker run -d -p 8000:8000 --env-file .env --name product-collector startup-product-collector
```

### 3. 使用预构建镜像 (如果已发布到Docker Hub)

```bash
docker pull <your-username>/startup-product-collector
docker run -d -p 8000:8000 --env-file .env --name product-collector <your-username>/startup-product-collector
```

## 环境变量配置

以下是应用使用的主要环境变量：

| 变量名 | 描述 | 默认值 | 是否必需 |
|-------|------|-------|---------|
| DATABASE_URL | 数据库连接URL | sqlite:///./app.db | 是 |
| OPENAI_API_KEY | OpenAI API密钥 | - | 是 |
| OPENAI_MODEL | 使用的OpenAI模型 | gpt-3.5-turbo | 否 |
| SCRAPER_INTERVAL | 爬虫运行间隔(秒) | 3600 | 否 |
| REQUEST_TIMEOUT | HTTP请求超时(秒) | 30 | 否 |
| USER_AGENT | 爬虫使用的User-Agent | Mozilla/5.0... | 否 |
| ENABLE_SCHEDULER | 是否启用定时任务 | True | 否 |
| ENABLE_AI_ANALYSIS | 是否启用AI分析 | True | 否 |
| AI_ANALYSIS_MIN_POINTS | 分析帖子的最低点赞数 | 5 | 否 |
| DEBUG | 是否启用调试模式 | False | 否 |
| LOG_LEVEL | 日志级别 | INFO | 否 |

## 系统监控

### 健康检查

Docker容器配置了健康检查，可以通过以下命令查看容器状态：

```bash
docker ps
# 或
docker-compose ps
```

### 日志监控

```bash
# Docker部署
docker logs -f product-collector
# 或
docker-compose logs -f

# 本地部署
# 日志默认输出到控制台
```

## 常见问题

### 数据库迁移

如果数据模型发生变化，需要执行数据库迁移：

```bash
# 使用Alembic进行迁移
alembic revision --autogenerate -m "migration message"
alembic upgrade head
```

### API访问限制

如果遇到OpenAI API限制，可以尝试：

1. 减少并发请求数量
2. 增加请求间隔时间
3. 使用多个API密钥轮换使用

### 内存使用优化

对于内存较小的服务器，可以调整worker数量和工作模式：

```bash
# 减少worker数量
gunicorn -w 2 -k uvicorn.workers.UvicornWorker main:app

# 或在docker-compose.yml中添加资源限制
services:
  app:
    # ...其他配置
    deploy:
      resources:
        limits:
          memory: 512M
```

---

如有其他部署问题，请提交Issue或查阅项目文档。 