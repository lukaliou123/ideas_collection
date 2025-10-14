# Railway 部署快速修复指南

## 问题：Langfuse 导入错误

如果你在 Railway 部署时遇到 `ModuleNotFoundError: No module named 'langfuse.callback'` 错误，已经修复！

### 已修复内容

1. ✅ **更新了 langfuse 导入方式**
   - 使用新版本 API: `from langfuse.langchain import CallbackHandler`
   - 添加了旧版本兼容性支持
   - 添加了优雅降级：如果 langfuse 不可用，应用仍然可以运行

2. ✅ **更新了 requirements.txt**
   - 指定 langfuse>=2.6.0（使用最新版本）

3. ✅ **Langfuse 现在是可选功能**
   - 即使没有配置 Langfuse 密钥，应用也能正常运行
   - 只会在日志中显示警告信息

### 部署步骤

#### 1. 提交更新的代码

```bash
git add .
git commit -m "fix: 修复 langfuse 导入错误，支持 Railway 部署"
git push origin main
```

#### 2. Railway 会自动重新部署

- Railway 检测到代码更新会自动触发新的部署
- 等待构建完成（约 2-5 分钟）

#### 3. 检查部署日志

在 Railway Dashboard 中查看日志，应该会看到：
- ✅ 成功安装所有依赖
- ✅ 应用启动成功
- ℹ️ 如果没有配置 Langfuse 密钥，会看到 "Manual tracing will be disabled" 的提示（这是正常的）

### 关于 Langfuse

**Langfuse 是什么？**
- AI 应用的监控和追踪工具
- 用于记录和分析 OpenAI API 调用
- 完全可选，不影响核心功能

**是否需要配置 Langfuse？**

❌ **不是必需的**
- 应用的核心功能（爬虫、AI 分析）不依赖 Langfuse
- 只是少了监控和追踪功能

✅ **如果你想使用 Langfuse 监控**
1. 注册 [Langfuse Cloud](https://cloud.langfuse.com/)（免费）
2. 获取 Public Key 和 Secret Key
3. 在 Railway Dashboard 设置环境变量：
   - `LANGFUSE_PUBLIC_KEY=pk-lf-xxx`
   - `LANGFUSE_SECRET_KEY=sk-lf-xxx`
   - `LANGFUSE_HOST=https://cloud.langfuse.com`

### 验证部署成功

访问你的 Railway 应用 URL，应该能看到：
- ✅ 应用正常运行
- ✅ API 文档可访问（`/docs`）
- ✅ 定时任务正在运行（查看日志）

### 如果还有问题

1. **检查环境变量**
   - 确认 `DATABASE_URL` 已自动设置（PostgreSQL 插件）
   - 确认 `OPENAI_API_KEY` 已正确设置
   
2. **查看完整日志**
   ```bash
   # 使用 Railway CLI
   railway logs
   ```

3. **重新构建**
   - 在 Railway Dashboard → Settings → Redeploy

4. **检查数据库**
   ```bash
   # 连接到 Railway
   railway run bash
   
   # 初始化数据库
   python scripts/init_db.py
   python scripts/add_sources.py
   ```

---

## 其他可能的问题

### 问题 1: DATABASE_URL 未设置
**解决方案**：确保已添加 PostgreSQL 插件
```
Railway Dashboard → New → Database → Add PostgreSQL
```

### 问题 2: 应用启动后立即崩溃
**解决方案**：检查环境变量
```bash
railway variables
```
确认至少设置了：
- `DATABASE_URL`（自动）
- `OPENAI_API_KEY`（手动）

### 问题 3: 定时任务不运行
**解决方案**：设置调度器环境变量
```
ENABLE_SCHEDULER=True
```

---

## 本地测试（可选）

在提交到 Railway 前，可以在本地测试：

```bash
# 1. 安装更新的依赖
pip install -r requirements.txt

# 2. 运行应用
python main.py

# 3. 检查日志
# 应该看到 "Langfuse package not available" 或成功初始化的消息
```

---

需要帮助？查看完整部署指南：
- [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md) - 详细部署教程
- [DEPLOYMENT.md](./DEPLOYMENT.md) - 通用部署指南

