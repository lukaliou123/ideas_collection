# Railway 部署指南

本指南将帮助你将项目部署到 Railway 平台，使用 PostgreSQL 数据库实现数据持久化。

## 📋 前置准备

### 1. 注册 Railway 账号
访问 [Railway.app](https://railway.app/) 并注册账号（支持 GitHub 登录）。

### 2. 安装 Railway CLI（可选）
```bash
npm i -g @railway/cli
# 或使用 brew
brew install railway
```

### 3. 准备 API 密钥
- OpenAI API Key（必需）
- Langfuse 配置（可选，用于 AI 监控）

## 🚀 部署步骤

### 方法一：通过 GitHub 自动部署（推荐）

#### 1. 推送代码到 GitHub
```bash
git add .
git commit -m "feat: 准备部署到 Railway"
git push origin main
```

#### 2. 在 Railway 创建新项目
1. 登录 [Railway Dashboard](https://railway.app/dashboard)
2. 点击 "New Project"
3. 选择 "Deploy from GitHub repo"
4. 选择你的仓库
5. Railway 会自动检测 Dockerfile 并开始构建

#### 3. 添加 PostgreSQL 数据库
1. 在项目中点击 "New" → "Database" → "Add PostgreSQL"
2. Railway 会自动创建数据库并设置 `DATABASE_URL` 环境变量
3. 等待数据库初始化完成（通常 1-2 分钟）

#### 4. 配置环境变量
在 Railway Dashboard 中设置以下环境变量：

**必需变量：**
- `OPENAI_API_KEY`: 你的 OpenAI API 密钥
- `DATABASE_URL`: 已自动设置（PostgreSQL 插件）

**可选变量：**
- `OPENAI_MODEL`: 使用的模型（默认: gpt-4.1-nano）
- `ENABLE_SCHEDULER`: 是否启用定时任务（建议: True）
- `ENABLE_AI_ANALYSIS`: 是否启用 AI 分析（建议: True）
- `SCRAPER_INTERVAL`: 爬虫运行间隔秒数（默认: 3600）
- `AI_ANALYSIS_MIN_POINTS`: AI 分析最低分数（默认: 10）
- `LANGFUSE_PUBLIC_KEY`: Langfuse 公钥
- `LANGFUSE_SECRET_KEY`: Langfuse 密钥
- `LANGFUSE_HOST`: Langfuse 服务器地址
- `DEBUG`: 调试模式（建议: False）
- `LOG_LEVEL`: 日志级别（默认: INFO）

#### 5. 部署应用
1. 环境变量配置完成后，Railway 会自动重新部署
2. 等待构建和部署完成
3. 点击 "View Logs" 查看部署日志

#### 6. 获取应用 URL
1. 在项目设置中点击 "Generate Domain"
2. Railway 会生成一个公开的 URL（如：your-app.railway.app）
3. 访问该 URL 确认应用正常运行

### 方法二：使用 Railway CLI 部署

#### 1. 登录 Railway CLI
```bash
railway login
```

#### 2. 初始化项目
```bash
# 在项目根目录执行
railway init
```

#### 3. 添加 PostgreSQL
```bash
railway add --plugin postgresql
```

#### 4. 设置环境变量
```bash
railway variables set OPENAI_API_KEY=sk-xxx
railway variables set ENABLE_SCHEDULER=True
railway variables set ENABLE_AI_ANALYSIS=True
# ... 其他变量
```

#### 5. 部署
```bash
railway up
```

#### 6. 查看日志
```bash
railway logs
```

## 📊 数据迁移

如果你有现有的 SQLite 数据需要迁移到 PostgreSQL：

### 1. 本地迁移（推荐）

```bash
# 1. 获取 Railway PostgreSQL 连接字符串
# 在 Railway Dashboard → PostgreSQL → Variables → DATABASE_URL
# 复制完整的连接字符串

# 2. 运行迁移脚本
python scripts/migrate_to_postgresql.py \
  --source sqlite:///./data/app.db \
  --target "postgresql://user:pass@host:5432/railway"

# 3. 验证迁移结果
# 脚本会自动验证数据完整性
```

### 2. 使用 Railway CLI 迁移

```bash
# 1. 连接到 Railway 项目
railway link

# 2. 获取数据库连接信息
railway variables

# 3. 运行迁移脚本（使用上面的命令）
```

## 🔧 初始化数据库

如果是全新部署（没有现有数据），需要初始化数据库：

### 通过 Railway Shell 初始化

```bash
# 打开 Railway Shell
railway run bash

# 运行初始化脚本
python scripts/init_db.py

# 添加数据源
python scripts/add_sources.py

# 退出
exit
```

### 或者在本地初始化后迁移

```bash
# 本地初始化
python scripts/init_db.py
python scripts/add_sources.py

# 然后迁移数据（参考上面的数据迁移步骤）
```

## 📈 监控和维护

### 查看日志
```bash
# 使用 CLI
railway logs

# 或在 Railway Dashboard 中点击 "View Logs"
```

### 查看资源使用
在 Railway Dashboard 中可以看到：
- CPU 使用率
- 内存使用
- 网络流量
- 数据库大小

### 定时任务监控
应用会自动运行定时任务（如果 `ENABLE_SCHEDULER=True`）：
- 每小时抓取 HackerNews 数据
- 自动进行 AI 分析
- 查看日志确认任务正常运行

### 数据库备份
Railway PostgreSQL 自动提供：
- 每日自动备份
- 在 Railway Dashboard → PostgreSQL → Backups 查看

## 🐛 常见问题

### 1. 部署失败：构建超时
**解决方案**：
- 确保 requirements.txt 中的依赖版本正确
- 检查 Dockerfile 是否正确
- 查看构建日志找到具体错误

### 2. 应用启动后立即崩溃
**解决方案**：
- 检查环境变量是否正确设置
- 查看应用日志找到错误信息
- 确认 DATABASE_URL 已正确设置

### 3. 数据库连接失败
**解决方案**：
- 确认 PostgreSQL 插件已添加
- 检查 DATABASE_URL 环境变量
- 确认数据库已初始化完成

### 4. 定时任务不运行
**解决方案**：
- 确认 `ENABLE_SCHEDULER=True`
- 查看日志确认调度器已启动
- 检查 SCRAPER_INTERVAL 设置

### 5. OpenAI API 调用失败
**解决方案**：
- 检查 OPENAI_API_KEY 是否正确
- 确认 API 密钥有足够的配额
- 查看日志中的具体错误信息

### 6. 内存不足
**解决方案**：
- Railway 提供 8GB RAM（免费版：512MB）
- 考虑升级到 Hobby 或 Pro 计划
- 优化代码减少内存使用

## 💰 费用说明

Railway 定价模式：
- **Hobby Plan**: $5/月
  - $5 的使用额度
  - 按实际使用计费
  - 适合小型项目
  
- **Pro Plan**: $20/月
  - $20 的使用额度
  - 更高的资源配额
  - 优先支持

**本项目预估费用**（Hobby Plan）：
- 应用运行：~$2-3/月
- PostgreSQL 数据库：~$1-2/月
- 总计：约 $3-5/月

**节省成本建议**：
- 调整 SCRAPER_INTERVAL 减少运行频率
- 合理设置 AI_ANALYSIS_MIN_POINTS 减少 AI 调用
- 监控资源使用，优化代码性能

## 🔒 安全建议

1. **API 密钥管理**
   - 不要在代码中硬编码 API 密钥
   - 使用 Railway 的环境变量功能
   - 定期轮换 API 密钥

2. **数据库安全**
   - Railway 自动管理数据库凭证
   - 定期检查数据库备份
   - 避免暴露数据库连接字符串

3. **应用安全**
   - 生产环境设置 `DEBUG=False`
   - 定期更新依赖包
   - 监控异常日志

## 📚 相关资源

- [Railway 官方文档](https://docs.railway.app/)
- [Railway CLI 文档](https://docs.railway.app/develop/cli)
- [PostgreSQL 使用指南](https://docs.railway.app/databases/postgresql)
- [Railway 定价](https://railway.app/pricing)

## 🆘 获取帮助

- Railway Discord: https://discord.gg/railway
- Railway 支持: help@railway.app
- 项目 Issues: 在 GitHub 仓库提交问题

---

部署愉快！🎉

