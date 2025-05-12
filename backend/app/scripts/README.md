# 标签系统工具

本目录包含与标签系统相关的多个实用工具脚本。

## 标签初始化

通过以下命令初始化预定义的标签分类和标签：

```bash
python -m backend.app.scripts.init_tags
```

该脚本会创建5个标签分类（技术领域、行业领域、用户类型、问题领域、产品属性）和大量预定义标签。

## 标签标准化和合并

标签标准化和合并工具可以帮助清理现有标签数据，标准化标签名称并合并相似标签。

### 功能

- **标准化标签名称**：将所有标签名称标准化（小写、移除特殊字符等）
- **查找相似标签**：识别系统中相似的标签
- **交互式合并**：通过命令行交互合并标签
- **自动合并**：根据相似度自动合并高相似度标签

### 使用方法

1. **标准化所有标签**：

```bash
python -m backend.app.scripts.normalize_tags --normalize
```

2. **查找相似标签**：

```bash
python -m backend.app.scripts.normalize_tags --find-similar
```

3. **交互式合并标签**：

```bash
python -m backend.app.scripts.normalize_tags --find-similar --merge-interactive
```

4. **自动合并高相似度标签**：

```bash
python -m backend.app.scripts.normalize_tags --auto-merge
```

5. **设置相似度阈值**：

```bash
python -m backend.app.scripts.normalize_tags --find-similar --threshold 0.8
python -m backend.app.scripts.normalize_tags --auto-merge --auto-threshold 0.95
```

## 注意事项

- 标签合并操作不可撤销，建议在操作前备份数据库
- 自动合并会选择关联产品数量最多的标签作为主标签
- 交互式合并允许手动选择主标签 