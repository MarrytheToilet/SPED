# 项目结构说明

## 📁 目录结构

```
sped/
├── menu.py                      # 🎯 统一菜单入口
├── settings.py                  # ⚙️ 全局配置
├── requirements.txt             # 📦 依赖列表
├── .env                         # 🔐 环境变量
│
├── scripts/                     # 📜 功能脚本
│   ├── pdf_manager.py          # 📄 新版PDF工具（推荐）
│   ├── pdf_process.py          # 📄 旧版PDF工具（兼容）
│   ├── extract.py              # 📝 数据提取
│   └── database.py             # 💾 数据库管理
│
├── src/                        # 🔧 核心代码
│   ├── pdfs/
│   │   ├── pdf_manager.py     # PDF状态管理器（新）
│   │   ├── upload.py
│   │   ├── download.py
│   │   └── request.py
│   ├── agents/                # 🤖 LLM代理
│   ├── database/              # 💾 数据库模块
│   ├── extractors/            # 🔍 提取器
│   └── utils/                 # 🛠️ 工具函数
│
├── data/                       # 📊 数据目录
│   ├── raw/
│   │   └── pdfs/              # PDF输入目录
│   ├── processed/
│   │   ├── pdfs_uploaded/     # 已上传PDF
│   │   ├── parsed/            # 解析结果
│   │   └── extracted/         # 提取JSON
│   ├── uploads/
│   │   └── pdf_manager.db     # PDF状态数据库
│   ├── exports/               # 导出文件
│   └── artificial_joint.db    # 主数据库
│
├── docs/                       # 📚 文档
│   ├── PDF_GUIDE.md           # PDF完整指南
│   ├── USAGE.md               # 系统使用文档
│   └── DATABASE.md            # 数据库管理
│
├── prompts/                    # 💬 提示词
│   └── prompt.md
│
├── data_schema/                # 📋 数据Schema
│   └── schema.json
│
└── logs/                       # 📝 日志
    └── *.log
```

---

## 🎯 核心文件说明

### 入口文件
- **menu.py** - 统一菜单系统（推荐使用）
- **settings.py** - 全局配置管理

### 核心脚本
- **scripts/pdf_manager.py** - 新版PDF工具（推荐）⭐
- **scripts/pdf_process.py** - 旧版PDF工具（兼容）
- **scripts/extract.py** - 数据提取工具
- **scripts/database.py** - 数据库管理工具

### 核心代码
- **src/pdfs/pdf_manager.py** - PDF状态管理器（新）⭐
- **src/agents/** - LLM智能代理
- **src/database/** - 数据库操作模块
- **src/extractors/** - 数据提取器

### 文档
- **PDF_GUIDE.md** - PDF系统快速参考
- **docs/PDF_GUIDE.md** - PDF完整使用指南
- **docs/USAGE.md** - 系统使用文档
- **docs/DATABASE.md** - 数据库管理指南
- **README.md** - 项目总览文档

---

## 🔄 数据流向

```
PDF文件 (raw/pdfs/)
    ↓ scan + upload
MinerU处理
    ↓ download
解析结果 (processed/parsed/)
    ↓ extract
JSON数据 (processed/extracted/)
    ↓ import
SQLite数据库 (artificial_joint.db)
    ↓ export
Excel/CSV (exports/)
```

---

## 🚀 典型工作流

### 完整流程
```bash
# 1. PDF处理
python scripts/pdf_manager.py auto --wait

# 2. 数据提取
python menu.py  # 选择 2 或 3

# 3. 数据库管理
python menu.py  # 选择 6, 8, 9
```

### 快速测试
```bash
python menu.py
# 1: 测试系统
# 4: 测试提取
```

---

**更新日期**: 2026-03-10
