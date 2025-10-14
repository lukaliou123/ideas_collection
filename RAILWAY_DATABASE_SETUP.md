# Railway 数据库配置紧急指南

## ⚠️ 当前问题

你看到的错误：
```
sqlite3.OperationalError: unable to open database file
```

**原因**：应用在 Railway 上仍然使用 SQLite，但没有添加 PostgreSQL 数据库。

## ✅ 立即解决（3步）

### 步骤 1: 提交代码修复

首先提交刚才修复的调度器代码：

```bash
git add .
git commit -m "fix: 修复调度器在无数据库时的启动问题"
git push origin main
```

### 步骤 2: 在 Railway 添加 PostgreSQL（必须）

#### 方法 A: 通过 Railway Dashboard（推荐）

1. **打开你的 Railway 项目**
   - 访问 https://railway.app/dashboard
   - 选择你的项目

2. **添加 PostgreSQL 数据库**
   - 点击 "New" 按钮
   - 选择 "Database"
   - 选择 "Add PostgreSQL"
   - 等待 1-2 分钟初始化完成

3. **验证 DATABASE_URL**
   - 点击 PostgreSQL 服务
   - 切换到 "Variables" 标签
   - 确认看到 `DATABASE_URL` 已自动生成
   - 这个变量会自动传递给你的应用

#### 方法 B: 使用 Railway CLI

```bash
# 登录 Railway
railway login

# 连接到你的项目
railway link

# 添加 PostgreSQL
railway add --plugin postgresql

# 查看环境变量
railway variables
```

### 步骤 3: 重新部署应用

#### Railway 会自动检测到数据库并重新部署

等待部署完成后，查看日志应该看到：
- ✅ `"调度器使用 PostgreSQL 存储任务"` 或 `"调度器使用内存存储任务（非持久化）"`
- ✅ 应用成功启动
- ✅ 定时任务已注册

### 步骤 4: 初始化数据库（首次部署需要）

使用 Railway CLI 运行初始化脚本：

```bash
# 初始化数据库表
railway run python scripts/init_db.py

# 添加数据源
railway run python scripts/add_sources.py
```

## 📋 验证部署成功

### 1. 检查环境变量

在 Railway Dashboard 中：
- Settings → Variables
- 确认看到 `DATABASE_URL` 以 `postgresql://` 开头

### 2. 查看应用日志

应该看到类似这样的日志：
```
INFO: Uvicorn running on http://0.0.0.0:8000
调度器使用 PostgreSQL 存储任务
任务调度器已启动
已注册HackerNews数据收集任务
```

### 3. 访问应用

- 在 Railway Dashboard 点击 "Generate Domain"（如果还没有）
- 访问生成的 URL
- 应该能看到应用正常运行

## 🔧 刚才的代码修复说明

我修复了两个问题：

### 1. Langfuse 导入错误
- ✅ 更新了导入路径兼容新版本
- ✅ 添加了优雅降级：导入失败也不会崩溃

### 2. 调度器数据库问题
- ✅ PostgreSQL：使用数据库持久化存储任务
- ✅ SQLite：使用内存存储（避免文件权限问题）
- ✅ 启动失败时自动降级到内存存储

## 🎯 为什么必须使用 PostgreSQL？

### ❌ SQLite + Railway = 不可行
- Railway 容器是临时的
- 每次重启/重新部署会丢失所有数据
- 容器文件系统可能没有写权限

### ✅ PostgreSQL + Railway = 完美
- 独立的数据库服务
- 数据永久保存
- 自动备份
- 高性能

## 📊 成本说明

添加 PostgreSQL 后的费用（Hobby Plan）：
- **应用服务**: ~$2-3/月
- **PostgreSQL**: ~$1-2/月
- **总计**: 约 $3-5/月

Railway 提供 $5/月 的使用额度，足够运行这个项目。

## 🐛 常见问题

### Q: 我添加了 PostgreSQL，但应用还是报错？
**A**: 等待 1-2 分钟让 Railway 重新部署。或者手动触发重新部署：
```
Settings → Redeploy
```

### Q: DATABASE_URL 没有自动设置？
**A**: PostgreSQL 插件添加后，Railway 会自动注入环境变量。确认：
1. PostgreSQL 服务显示为 "Active"
2. 应用已重新部署
3. 查看应用的 Variables 标签

### Q: 调度器使用内存存储有什么影响？
**A**: 
- 内存存储：任务配置在应用重启时会丢失，但会自动重新注册
- PostgreSQL：任务配置持久化，重启后保留
- **对本项目影响不大**：因为任务在启动时都会重新注册

### Q: 如何查看数据库内容？
**A**: 使用 Railway CLI：
```bash
# 连接到数据库
railway connect postgres

# 或使用 psql
railway run psql $DATABASE_URL
```

### Q: 数据库初始化失败？
**A**: 检查是否有表创建权限：
```bash
# 使用 Python 脚本初始化
railway run python scripts/init_db.py

# 如果失败，查看详细错误
railway logs
```

## 🆘 还是无法解决？

### 1. 检查完整日志
```bash
railway logs --follow
```

### 2. 验证环境变量
```bash
railway variables
```

应该至少看到：
- `DATABASE_URL` (自动)
- `OPENAI_API_KEY` (手动设置)

### 3. 尝试本地测试
```bash
# 设置临时 PostgreSQL URL（使用 Railway 的）
export DATABASE_URL="postgresql://..."

# 运行应用
python main.py
```

## 📚 相关文档

- [Railway 部署详细指南](./RAILWAY_DEPLOYMENT.md)
- [通用部署指南](./DEPLOYMENT.md)
- [快速修复指南](./RAILWAY_QUICKFIX.md)

---

**重要提示**：
- ✅ 必须添加 PostgreSQL 数据库
- ✅ 必须设置 OPENAI_API_KEY
- ✅ 其他环境变量可选
- ✅ 提交代码后 Railway 会自动重新部署

