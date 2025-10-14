# 部署指南 - 创业产品信息收集系统

本文档提供了部署创业产品信息收集系统的详细步骤，包括本地部署、Docker容器化部署和Railway云部署。

## 目录
1. [环境要求](#环境要求)
2. [本地部署](#本地部署)
3. [Docker部署](#docker部署)
4. [Railway云部署](#railway云部署-推荐)
5. [数据库迁移](#数据库迁移-sqlite-to-postgresql)
6. [环境变量配置](#环境变量配置)
7. [系统监控](#系统监控)
8. [常见问题](#常见问题)

## 环境要求

- Python 3.9+
- 数据库：SQLite 3（本地开发）或 PostgreSQL 12+（生产环境）
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

## Railway云部署 (推荐)

Railway 是最适合本项目的云平台，提供：
- ✅ PostgreSQL 托管数据库（数据持久化）
- ✅ 自动部署和 CI/CD
- ✅ 免费额度（Hobby Plan $5/月起）
- ✅ 自动 HTTPS 和域名

### 快速部署步骤

1. **推送代码到 GitHub**
   ```bash
   git add .
   git commit -m "feat: 准备部署到 Railway"
   git push origin main
   ```

2. **在 Railway 创建项目**
   - 访问 [Railway.app](https://railway.app/)
   - 点击 "New Project" → "Deploy from GitHub repo"
   - 选择你的仓库

3. **添加 PostgreSQL 数据库**
   - 点击 "New" → "Database" → "Add PostgreSQL"
   - Railway 会自动设置 `DATABASE_URL` 环境变量

4. **配置环境变量**
   在 Railway Dashboard 设置：
   - `OPENAI_API_KEY`: 你的 OpenAI API 密钥（必需）
   - `ENABLE_SCHEDULER`: True（启用定时任务）
   - `ENABLE_AI_ANALYSIS`: True（启用 AI 分析）
   - 其他变量参考 `.env.example`

5. **初始化数据库**
   ```bash
   # 使用 Railway CLI
   railway run python scripts/init_db.py
   railway run python scripts/add_sources.py
   ```

6. **生成域名**
   - 在项目设置中点击 "Generate Domain"
   - 访问生成的 URL 确认部署成功

📖 **详细部署指南**: 查看 [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)

### 为什么选择 Railway？

❌ **SQLite + Railway 不合适**：
- Railway 容器是临时的，重启会丢失数据
- 每次部署都会清空 SQLite 数据库
- 无法保证数据持久化

✅ **PostgreSQL + Railway 完美组合**：
- 独立的数据库服务，数据永久保存
- 自动备份和恢复
- 适合生产环境
- Railway 原生支持，配置简单

## 数据库迁移 (SQLite to PostgreSQL)

如果你有现有的 SQLite 数据需要迁移到 PostgreSQL：

### 迁移步骤

```bash
# 1. 确保已安装 PostgreSQL 驱动
pip install psycopg2-binary

# 2. 获取目标数据库连接字符串
# 从 Railway Dashboard → PostgreSQL → Variables → DATABASE_URL

# 3. 运行迁移脚本
python scripts/migrate_to_postgresql.py \
  --source sqlite:///./data/app.db \
  --target "postgresql://user:pass@host:5432/railway"

# 4. 验证迁移结果
# 脚本会自动验证数据完整性并显示统计信息
```

### 迁移功能
- ✅ 自动迁移所有表和数据
- ✅ 保持数据完整性和关系
- ✅ 批量处理，高效快速
- ✅ 自动验证迁移结果
- ✅ 详细的进度显示和错误处理

详细说明请参考脚本中的帮助信息：
```bash
python scripts/migrate_to_postgresql.py --help
```

## 环境变量配置

以下是应用使用的主要环境变量：

| 变量名 | 描述 | 默认值 | 是否必需 |
|-------|------|-------|---------|
| DATABASE_URL | 数据库连接URL | sqlite:///./data/app.db | 是 |
| OPENAI_API_KEY | OpenAI API密钥 | - | 是 |
| OPENAI_MODEL | 使用的OpenAI模型 | gpt-4.1-nano | 否 |
| SCRAPER_INTERVAL | 爬虫运行间隔(秒) | 3600 | 否 |
| REQUEST_TIMEOUT | HTTP请求超时(秒) | 30 | 否 |
| USER_AGENT | 爬虫使用的User-Agent | Mozilla/5.0... | 否 |
| ENABLE_SCHEDULER | 是否启用定时任务 | True | 否 |
| ENABLE_AI_ANALYSIS | 是否启用AI分析 | True | 否 |
| AI_ANALYSIS_MIN_POINTS | 分析帖子的最低点赞数 | 10 | 否 |
| DEBUG | 是否启用调试模式 | False | 否 |
| LOG_LEVEL | 日志级别 | INFO | 否 |
| LANGFUSE_PUBLIC_KEY | Langfuse公钥（AI监控） | - | 否 |
| LANGFUSE_SECRET_KEY | Langfuse密钥（AI监控） | - | 否 |
| LANGFUSE_HOST | Langfuse服务器地址 | https://cloud.langfuse.com | 否 |

### 数据库配置说明

**本地开发（SQLite）：**
```bash
DATABASE_URL=sqlite:///./data/app.db
```

**生产环境（PostgreSQL）：**
```bash
# Railway 会自动设置，格式如下：
DATABASE_URL=postgresql://user:password@host:5432/database
```

### 配置文件

复制 `.env.example` 为 `.env` 并填入实际值：
```bash
cp .env.example .env
```

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

### 数据库切换

应用自动检测数据库类型，无需额外配置：
- SQLite：用于本地开发和测试
- PostgreSQL：用于生产环境（Railway、Docker等）

切换数据库只需修改 `DATABASE_URL` 环境变量即可。

---

## 相关文档

- [Railway 部署详细指南](./RAILWAY_DEPLOYMENT.md) - Railway 平台完整部署教程
- [README.md](./README.md) - 项目介绍和功能说明
- [.env.example](./.env.example) - 环境变量配置示例

如有其他部署问题，请提交Issue或查阅项目文档。 