# Scripts 目录说明

## 📁 目录结构

```
scripts/
├── cli.py                  # ⭐ 统一命令行入口（推荐使用）
├── legacy/                 # 旧脚本归档（仅供参考）
│   ├── extract_old.py     # 旧版数据提取脚本
│   ├── database_old.py    # 旧版数据库脚本
│   ├── pdf_process.py     # 旧版PDF处理
│   ├── pdf_manager.py     # 旧版PDF管理器
│   ├── add_doi_to_md.py   # DOI提取工具（一次性）
│   ├── fix_duplicate_dataids.py  # 修复重复ID（一次性）
│   └── fix_json_dataids.py       # 修复JSON ID（一次性）
└── maintenance/            # 维护工具（预留）
```

---

## 🚀 使用新的CLI工具

### 为什么使用cli.py？

✅ **统一入口** - 一个命令搞定所有操作  
✅ **清晰的子命令** - pdf/extract/db/workflow 分类明确  
✅ **完整的帮助** - `--help` 查看详细说明  
✅ **与新Agent系统集成** - 使用最新的Agent架构  

---

## 📝 快速开始

### 1. 查看帮助

```bash
python scripts/cli.py --help
python scripts/cli.py pdf --help
python scripts/cli.py extract --help
python scripts/cli.py db --help
python scripts/cli.py workflow --help
```

### 2. PDF处理

```bash
# 上传PDF
python scripts/cli.py pdf upload

# 查询状态
python scripts/cli.py pdf status BATCH_ID

# 下载结果
python scripts/cli.py pdf download BATCH_ID

# 列出所有批次
python scripts/cli.py pdf list
```

### 3. 数据提取

```bash
# 测试配置
python scripts/cli.py extract test

# 提取单个论文（交互式）
python scripts/cli.py extract single

# 提取指定论文
python scripts/cli.py extract single PAPER_ID --mode chunk

# 批量提取
python scripts/cli.py extract batch --mode full
```

### 4. 数据库操作

```bash
# 导入JSON
python scripts/cli.py db import

# 查看统计
python scripts/cli.py db stats

# 导出数据
python scripts/cli.py db export --format excel

# 查询记录
python scripts/cli.py db query --limit 20
```

### 5. 完整工作流（推荐）

```bash
# 单个论文完整流程（提取 + 导入）
python scripts/cli.py workflow run PAPER_ID --mode full

# 批量完整流程
python scripts/cli.py workflow batch --mode chunk
```

---

## 🔄 迁移指南

### 从旧脚本迁移到新CLI

| 旧命令 | 新命令 |
|--------|--------|
| `python scripts/extract.py single` | `python scripts/cli.py extract single` |
| `python scripts/extract.py batch` | `python scripts/cli.py extract batch` |
| `python scripts/extract.py test` | `python scripts/cli.py extract test` |
| `python scripts/database.py` | `python scripts/cli.py db [action]` |
| `python scripts/pdf_process.py` | `python scripts/cli.py pdf [action]` |
| `python workflows/full_extraction_pipeline.py` | `python scripts/cli.py workflow run` |

---

## 📚 命令参考

### PDF命令

```bash
# 上传
python scripts/cli.py pdf upload [--dir PATH]

# 查询
python scripts/cli.py pdf status BATCH_ID

# 下载
python scripts/cli.py pdf download BATCH_ID [--output PATH]

# 列表
python scripts/cli.py pdf list
```

### 提取命令

```bash
# 测试
python scripts/cli.py extract test

# 单个
python scripts/cli.py extract single [PAPER_ID] \
    [--mode {full,chunk,global_first}] \
    [--model MODEL_NAME]

# 批量
python scripts/cli.py extract batch \
    [--mode {full,chunk,global_first}] \
    [--model MODEL_NAME] \
    [--workers N]
```

### 数据库命令

```bash
# 导入
python scripts/cli.py db import [--dir PATH]

# 导出
python scripts/cli.py db export \
    [--format {excel,csv}] \
    [--output PATH]

# 统计
python scripts/cli.py db stats

# 查询
python scripts/cli.py db query [--limit N]
```

### 工作流命令

```bash
# 单个
python scripts/cli.py workflow run PAPER_ID \
    [--mode {full,chunk,global_first}] \
    [--model MODEL_NAME] \
    [--no-import]

# 批量
python scripts/cli.py workflow batch \
    [--mode {full,chunk,global_first}] \
    [--model MODEL_NAME] \
    [--no-import]
```

---

## 💡 常见用法

### 场景1: 处理新的PDF论文

```bash
# 1. 上传PDF
python scripts/cli.py pdf upload

# 2. 记录batch_id，等待5-10分钟

# 3. 查询状态
python scripts/cli.py pdf status batch_xxx

# 4. 下载结果
python scripts/cli.py pdf download batch_xxx

# 5. 提取数据
python scripts/cli.py extract single PAPER_ID

# 6. 导入数据库
python scripts/cli.py db import
```

### 场景2: 快速提取并导入（推荐）

```bash
# 一条命令完成提取+导入
python scripts/cli.py workflow run PAPER_ID --mode full
```

### 场景3: 批量处理所有论文

```bash
# 批量提取并导入
python scripts/cli.py workflow batch --mode chunk
```

### 场景4: 导出数据分析

```bash
# 查看统计
python scripts/cli.py db stats

# 导出Excel
python scripts/cli.py db export --format excel
```

---

## 🔧 高级用法

### 使用不同的LLM模型

```bash
# 使用GPT-4o
python scripts/cli.py extract single PAPER_ID --model gpt-4o

# 使用Qwen
python scripts/cli.py extract batch --model "Qwen/Qwen2.5-72B-Instruct"
```

### 自定义输出路径

```bash
# 自定义PDF下载路径
python scripts/cli.py pdf download batch_xxx --output /custom/path

# 自定义导出路径
python scripts/cli.py db export --output /custom/export.xlsx
```

### 提取但不导入数据库

```bash
# 只提取，不导入
python scripts/cli.py workflow run PAPER_ID --no-import
```

---

## 📖 Legacy脚本说明

`legacy/` 目录中的脚本**仅供参考**，不推荐使用：

### 为什么不推荐？

1. **功能重复** - extract_old.py, pdf_process.py, pdf_manager.py 功能重叠
2. **代码老旧** - 没有使用新的Agent架构
3. **维护困难** - 代码分散，难以维护
4. **一次性工具** - add_doi_to_md.py 等是临时修复脚本

### 何时可以查看？

- 📚 学习旧实现方式
- 🔍 查找特定功能的实现
- 🐛 调试历史问题

### ⚠️ 注意

这些脚本**不再维护**，可能与当前系统不兼容。

---

## 🎯 最佳实践

### 推荐工作流

```bash
# 日常使用
python scripts/cli.py workflow run PAPER_ID

# 大批量处理
python scripts/cli.py workflow batch

# 快速测试
python scripts/cli.py extract test
```

### 避免的做法

❌ 不要同时使用新CLI和旧脚本  
❌ 不要手动修改legacy中的脚本  
❌ 不要在新功能中引用legacy代码  

---

## 🐛 故障排除

### Q: cli.py找不到模块？

```bash
# 确保从项目根目录运行
cd /path/to/sped
python scripts/cli.py --help
```

### Q: 想使用旧脚本怎么办？

```bash
# 可以运行，但不推荐
python scripts/legacy/extract_old.py
```

### Q: 如何查看详细错误？

CLI会自动打印详细错误信息和堆栈跟踪。

---

## 📞 获取帮助

1. **查看命令帮助**: `python scripts/cli.py [command] --help`
2. **查看文档**: [README_AGENTS.md](../README_AGENTS.md)
3. **运行测试**: `python test_new_agents.py`

---

**更新日期**: 2026-03-15  
**状态**: ✅ 新CLI已就绪，旧脚本已归档
