# 项目结构说明

## 📁 目录结构

```
sped/
├── menu.py                      # 🎯 统一菜单入口（唯一根目录脚本）
├── settings.py                  # ⚙️ 全局配置文件
│
├── scripts/                     # 📜 所有功能脚本
│   ├── extract.py              # 📝 数据提取脚本
│   ├── database.py             # 💾 数据库管理脚本
│   ├── pdf_process.py          # 📄 PDF处理脚本（上传/下载/解析）
│   ├── batch_process.py        # 🔄 批量处理工具
│   ├── export_to_excel.py      # 📊 Excel导出工具
│   └── ...                     # 其他工具脚本
│
├── src/                        # 🔧 核心代码库
│   ├── agents/                 # 🤖 智能代理
│   │   ├── llm_agent.py       # LLM提取逻辑
│   │   └── base_agent.py      # 基础Agent类
│   ├── database/              # 💾 数据库模块
│   │   ├── db_manager.py      # 数据库管理器
│   │   ├── csv_exporter.py    # CSV导出器
│   │   └── excel_exporter.py  # Excel导出器
│   └── pdfs/                  # 📄 PDF工具
│       ├── upload.py
│       ├── download.py
│       └── request.py
│
├── data/                       # 📊 数据目录
│   ├── raw/pdfs/              # 待处理PDF
│   ├── raw/pdfs_processed/    # 已处理PDF
│   ├── processed/parsed/      # 解析后的论文
│   ├── processed/extracted/   # 提取的JSON
│   ├── exports/               # CSV导出
│   └── artificial_joint.db    # SQLite数据库
│
├── prompts/                    # 💬 提示词模板
│   └── prompt.md              # 数据提取Prompt
│
└── docs/                       # 📚 文档
    ├── QUICK_USAGE_GUIDE.md
    ├── DATABASE_GUIDE.md
    └── ...
```

## 🚀 使用方式

### 主入口
```bash
python menu.py                  # 启动统一菜单
```

### 直接调用脚本
```bash
# 数据提取
python scripts/extract.py test           # 测试系统
python scripts/extract.py single         # 单个提取
python scripts/extract.py batch          # 批量提取

# 数据库管理
python scripts/database.py               # 交互式菜单

# PDF处理
python scripts/pdf_process.py upload     # 上传PDF
python scripts/pdf_process.py status     # 查询状态
python scripts/pdf_process.py download   # 下载结果
```

## 📋 核心脚本说明

### scripts/extract.py
- 功能：从解析后的论文中提取结构化数据
- 输入：`data/processed/parsed/*/full.md`
- 输出：`data/processed/extracted/*.json`
- 使用：通过菜单或命令行调用

### scripts/database.py
- 功能：数据库管理（导入/导出/查询/统计）
- 数据库：`data/artificial_joint.db`
- 支持：JSON导入、多格式CSV导出、Excel导出

### scripts/pdf_process.py
- 功能：PDF上传到MinerU、查询处理状态、下载解析结果
- 输入：`data/raw/pdfs/*.pdf`
- 输出：`data/processed/parsed/`
- 特性：自动去重、智能状态管理

## 🎯 设计原则

1. **清晰分离**：入口(menu.py) + 脚本(scripts/) + 核心代码(src/)
2. **统一管理**：所有功能脚本集中在 scripts/ 目录
3. **独立运行**：每个脚本都可独立运行
4. **模块化**：核心功能封装在 src/ 中复用

## 📝 配置文件

- `.env` - 环境变量（API密钥等）
- `settings.py` - Python配置（路径、参数等）

## 🔄 典型工作流

```
1. PDF处理
   python scripts/pdf_process.py upload    # 上传PDF
   python scripts/pdf_process.py download  # 下载解析结果

2. 数据提取
   python menu.py → 选择批量提取         # 提取数据

3. 数据管理
   python menu.py → 数据库管理           # 导入/导出
```

---
更新日期: 2025-11-18
