## 文档：标签系统优化与脚本使用指南

### 1. 背景与目标

本次迭代主要目标是优化标签系统，解决现有标签数量过多、无组织、难以维护等问题，提升用户体验和搜索效率。

主要改进点：
- 创建预定义标签集合和分类体系
- 实现标签标准化与自动合并机制
- 确保AI生成的标签与预定义集合对齐

### 2. 数据库结构变更

为了支持新功能，我们对数据库结构做了如下调整：

- **`tag_categories` 表 (新建)**：
    - `id`: 主键
    - `name`: 分类名称 (唯一)
    - `description`: 分类描述
- **`tags` 表 (修改)**：
    - `id`: 主键
    - `name`: 原始标签名
    - `normalized_name`: 标准化后的标签名 (唯一，用于去重和合并)
    - `category_id`: 外键，关联到 `tag_categories` 表
    - `aliases`: JSON 字段，存储相似标签的别名列表
    - `description`: (可选) 标签描述
- **`product_tag_association` 表 (新建)**：
    - `product_id`: 外键，关联到 `products` 表
    - `tag_id`: 外键，关联到 `tags` 表
- **`products` 表 (修改)**：
    - 关系：与 `tags` 表建立多对多关系

### 3. 核心代码实现

#### a. 标签工具 (`backend/app/core/tag_utils.py`)
- **`TagNormalizer` 类**：
    - `normalize_tag_name()`: 标签名标准化（小写、去特殊字符、去多余空格等）
    - `calculate_similarity()`: 计算两个标签的相似度
    - `find_similar_tags()`: 查找与目标标签相似的标签列表

#### b. 标签模型 (`backend/app/models/tag.py`)
- **`TagCategory` 模型**：定义了标签分类的结构
- **`Tag` 模型**：定义了标签的结构，包含 `normalized_name`、`category_id`、`aliases` 等字段
- **`product_tag_association` 表**：定义了产品与标签的多对多关联

#### c. 标签服务 (`backend/app/services/tag_service.py`)
- **`TagService` 类**：
    - 标签创建、查询、标准化、合并等核心逻辑
    - 标签分类的创建和查询

#### d. AI 服务 (`backend/app/services/langchain_service.py`)
- **`LangChainService` 类** (假设已重构完成)：
    - `generate_product_tags()`: 使用 LangChain 为产品生成标签，确保标签来自预定义集合，并进行标准化处理

### 4. 脚本使用指南 (`backend/app/scripts/README.md`)

#### a. 数据库迁移
- **目的**：确保数据库结构与代码模型一致。
- **命令**：
    ```bash
    cd backend
    alembic upgrade head 
    ```
- **原理**：Alembic 会比较当前数据库结构与模型定义，生成并应用必要的迁移脚本，创建新表、添加新字段等。

#### b. 标签初始化 (`init_tags.py`)
- **目的**：创建预定义的标签分类和标签。
- **命令**：
    ```bash
    python -m backend.app.scripts.init_tags
    ```
- **原理**：脚本会读取预定义的分类和标签列表，通过 `TagService` 批量创建，并自动归类。

#### c. 标签标准化与合并 (`normalize_tags.py`)
- **目的**：处理现有标签，标准化名称并合并相似标签。
- **功能**：
    - 标准化所有标签名称
    - 查找相似标签
    - 交互式或自动合并相似标签
- **命令**：
    ```bash
    # 标准化所有标签
    python -m backend.app.scripts.normalize_tags --normalize

    # 查找相似标签 (可调整相似度阈值)
    python -m backend.app.scripts.normalize_tags --find-similar --threshold 0.8

    # 交互式合并
    python -m backend.app.scripts.normalize_tags --find-similar --merge-interactive

    # 自动合并 (高相似度)
    python -m backend.app.scripts.normalize_tags --auto-merge --auto-threshold 0.95
    ```
- **原理**：
    - 标准化：调用 `TagNormalizer.normalize_tag_name()` 处理每个标签。
    - 查找相似：使用 `TagNormalizer.calculate_similarity()` 计算相似度。
    - 合并：将次要标签的产品关联转移到主标签，次要标签名存入主标签的 `aliases` 字段，然后删除次要标签。

#### d. 自动归类现有标签 (`auto_assign_tag_categories.py`)
- **目的**：将数据库中未分类的标签，根据预设规则自动归入合适的分类。
- **命令**：
    ```bash
    python -m backend.app.scripts.auto_assign_tag_categories
    ```
- **原理**：脚本内定义了一个 `CATEGORY_MAP` 字典，根据这个映射关系，将未分类标签批量更新 `category_id`。

### 5. 总结

通过以上修改，我们建立了一个更健壮、易于管理的标签系统：
- **标准化**：所有标签都有统一的规范化名称
- **去重**：通过标准化名称和别名机制，有效避免重复标签
- **分类**：标签按类别组织，便于维护和使用
- **AI友好**：AI生成的标签可以与预定义集合对齐，保证质量 