# 精选产品概念图生成功能实现文档

## 功能概述

实现了首页精选产品展示功能，并为精选产品生成专业的概念图片。系统会自动选择当日更新中点赞数最高的产品展示在首页，并通过AI生成对应的产品概念图来增强用户视觉体验。

## 架构设计

该功能涉及以下主要组件：

1. **ProductService** - 产品服务，负责获取精选产品和触发图片生成
2. **AIService** - 原始AI服务，提供OpenAI API调用功能
3. **LangChainAIService** - 基于LangChain框架的增强AI服务，提供更稳定的图片生成功能
4. **定时任务** - 每日自动更新精选产品和生成图片

## 实现细节

### 1. 产品模型扩展

在`app/models/products.py`中增加了`concept_image_url`字段，用于存储产品概念图的URL。

### 2. 图片生成服务

实现了两套图片生成服务，相互备份：

- **LangChainAIService.generate_product_image**
  - 使用LangChain框架生成优化的图片描述提示词
  - 直接通过httpx调用OpenAI DALL-E 2 API
  - 包含每日限额控制和详细日志记录

- **AIService.generate_product_image**
  - 作为备用方案，确保系统稳定性
  - 同样使用httpx直接调用API，避免了之前的异步问题

### 3. 精选产品服务

`ProductService.generate_images_for_featured_products`方法负责：
- 获取精选产品列表
- 优先尝试使用LangChain服务生成图片
- 如果失败，尝试使用传统AI服务作为备份
- 更新产品记录中的概念图URL

### 4. 任务调度

在`task_service.py`中注册了精选产品更新任务，每天上午10:30自动执行，确保首页始终展示最新最热的产品及其概念图。

## 技术特点

1. **双重实现保障可靠性**：使用两种不同实现方式确保即使一种方式失败，系统仍能生成图片

2. **错误处理机制**：完善的错误捕获和日志记录，方便调试和监控

3. **成本控制**：
   - 每日图片生成限额设置
   - 使用较小尺寸的图片(512x512)
   - 使用DALL-E 2而非更昂贵的DALL-E 3

4. **提示词优化**：通过LangChain生成高质量的图片描述提示词，确保生成的概念图专业且相关

5. **解决异步问题**：使用httpx直接调用API解决了OpenAI库中`await`关键字的兼容性问题

## 使用方法

### 手动测试

可使用`test_featured_products.py`测试脚本验证功能：

```bash
./venv/bin/python test_featured_products.py
```

### 自动执行

系统会在每天上午10:30自动执行更新任务，无需手动干预。

## 未来改进方向

1. 增加图片缓存机制，避免重复生成
2. 实现图片生成质量评估
3. 考虑集成更先进的模型如DALL-E 3或Midjourney
4. 添加更多样式选项，适应不同类型的产品

## 故障排除

### 常见问题

1. **图片生成失败**
   - 检查OpenAI API密钥是否有效
   - 检查API调用限额是否已达上限
   - 检查日志中的详细错误信息

2. **异步调用问题**
   - 如果遇到"can't be used in 'await' expression"错误，确保使用了正确的httpx实现

3. **图片未显示在首页**
   - 检查数据库中concept_image_url字段是否已更新
   - 确认定时任务是否正常运行
   - 检查模板中图片显示逻辑

### 日志查看

系统会记录详细的图片生成日志，可通过以下方式查看：

```bash
grep "生成概念图" logs/app.log
``` 