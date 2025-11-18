# 人工关节材料数据提取系统

基于LLM的智能数据提取系统，从学术论文中自动提取人工关节材料的实验数据，并提供完整的数据库管理和导出功能。

## 🎯 系统概述

```
论文PDF → MinerU解析 → 数据提取 → 数据库存储 → CSV导出 → 数据分析
```

### 核心功能

- ✅ **智能数据提取**: 使用LLM从论文中提取28个字段的结构化数据
- ✅ **数据库管理**: SQLite数据库存储，自动去重
- ✅ **CSV导出**: 多种格式导出，Excel兼容
- ✅ **批量处理**: 支持批量提取和导入
- ✅ **交互式工具**: 命令行界面，操作简单

## 🚀 快速开始

### 1. 环境配置

创建 `.env` 文件：

```bash
# OpenAI API配置
OPENAI_API_KEY=sk-your-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 分块配置（可选）
CHUNK_SIZE=10000
CHUNK_OVERLAP=300
```

### 2. 测试系统

```bash
python extract.py test
```

检查：
- ✅ API配置
- ✅ 目录结构
- ✅ 已解析论文数量
- ✅ API连接状态

### 3. 提取数据

**单个论文提取**：
```bash
python extract.py single
# 从列表中选择论文编号
```

**批量提取**：
```bash
python extract.py batch
```

### 4. 数据库管理

```bash
python database.py
```

菜单选项：
- 1 - 查看数据库统计
- 3 - 批量导入extracted目录
- 8 - 导出所有CSV格式
- 其他功能见DATABASE_GUIDE.md

### 5. 查看结果

提取结果：`data/processed/extracted/`  
CSV导出：`data/exports/`

## 📊 数据Schema

系统提取28个字段的数据：

### 基本信息 (3个)
- 数据标识、应用部位、产品所属专利号或文献

### 球头信息 (4个)
- 球头基本信息、成分组成、物理性能、微观组织

### 内衬信息 (6个)
- 基本信息、改性填料、成分组成、物理性能、复合材料性能、材料表征

### 股骨柄信息 (4个)
- 基本信息、成分组成、物理性能、微观组织

### 体外实验 - 内衬与球头摩擦腐蚀 (7个)
- 实验设置、润滑液组成、球头磨损结果、内衬磨损结果、球头腐蚀结果、内衬腐蚀结果、球头表面成分分析

### 体外实验 - 球头与锥颈界面微动腐蚀 (3个)
- 实验设置、润滑液组成、腐蚀与磨损实验结果

### 元数据 (2个)
- dataid (自动生成), paper_id (论文标识)

## 📁 项目结构

```
sped/
├── extract.py                  # 数据提取主程序
├── database.py                 # 数据库管理工具
├── settings.py                 # 配置文件
├── requirements.txt            # 依赖包
│
├── prompts/
│   └── prompt.md              # 提取Prompt（570行，含4个完整示例）
│
├── src/
│   ├── agents/
│   │   ├── llm_agent.py      # LLM提取逻辑
│   │   └── base_agent.py     # 基础Agent类
│   └── database/
│       ├── db_manager.py     # 数据库管理器
│       └── csv_exporter.py   # CSV导出器
│
├── data/
│   ├── artificial_joint.db   # SQLite数据库
│   ├── processed/
│   │   ├── parsed/           # 输入：解析后的论文（full.md）
│   │   └── extracted/        # 输出：提取的JSON
│   └── exports/              # CSV导出目录
│
└── docs/
    ├── QUICK_USAGE_GUIDE.md      # 快速使用指南
    ├── DATABASE_GUIDE.md         # 数据库详细指南
    └── EXTRACTION_SUCCESS_REPORT.md  # 提取测试报告
```

## 🎯 完整工作流程

### 方案A：PDF处理 + 数据提取 + 数据库管理

```bash
# 1. 使用MinerU解析PDF（在scripts/pdf_pipeline.py中）
#    输出：data/processed/parsed/*/full.md

# 2. 提取数据
python extract.py batch

# 3. 导入数据库
python database.py
# 选择 3 - 批量导入

# 4. 导出CSV
# 选择 8 - 导出所有格式

# 5. 分析数据
# Excel打开 data/exports/*.csv
```

### 方案B：已有parsed论文

```bash
# 1. 提取数据
python extract.py batch

# 2. 管理数据库
python database.py
```

## ✨ 核心特性

### 1. 智能数据提取

#### 高质量Prompt
- 570行详细prompt
- 4个完整真实示例
- 明确的字段格式要求
- 严格的JSON输出规范

#### 智能分块策略
```python
# 自动过滤参考文献
# 按自然边界分块（段落→换行→句子）
# Overlap机制避免信息丢失
CHUNK_SIZE=10000      # 可调节
CHUNK_OVERLAP=300     # 可调节
```

#### 自动判断逻辑
- LLM自动决定创建新记录还是完善已有记录
- JSON字段智能合并
- 详细的处理日志

### 2. 数据库管理

#### 功能完整
- ✅ 自动去重（相同dataid更新而非重复）
- ✅ 支持中文字段名
- ✅ 批量导入JSON
- ✅ 查询、删除、统计
- ✅ 自动升级schema

#### 交互式工具
```bash
python database.py

菜单：
1. 📊 查看数据库统计
2. 📥 从JSON文件导入数据
3. 📥 批量导入extracted目录的所有JSON
4. 📤 导出CSV（完整数据-展平JSON）
5. 📤 导出CSV（完整数据-保留JSON）
6. 📤 导出CSV（数据摘要）
7. 📤 导出CSV（关键字段）
8. 📤 导出所有格式
9. 🔍 查询论文数据
10. 🗑️  删除论文数据
11. ⚠️  清空所有数据
```

### 3. CSV导出

#### 4种预设格式

| 格式 | 特点 | 适用场景 |
|------|------|----------|
| **full_data_flat** | JSON展平为可读格式 | Excel分析 |
| **full_data_raw** | 保留原始JSON | 程序处理 |
| **summary** | 数据摘要（7个关键列） | 快速预览 |
| **key_fields** | 16个核心字段 | 重点数据分析 |

#### Excel兼容
- UTF-8编码（带BOM）
- 中文字段名正常显示
- JSON字段展平为易读格式

## 💻 编程接口

### 数据提取API

```python
from src.agents.llm_agent import LLMExtractionAgent

agent = LLMExtractionAgent()

# 提取单篇论文
result = agent.process({
    "paper_id": "paper_name",
    "full_text_path": "path/to/full.md"
})

# 结果格式
{
    "dataid": "AJ_20251103_xxx",
    "paper_id": "paper_name",
    "records": [...],
    "count": 9
}
```

### 数据库API

```python
from src.database import DatabaseManager, CSVExporter

# 数据库操作
db = DatabaseManager()

# 导入JSON
db.insert_from_json("test.json")

# 查询
records = db.query_all(limit=10)
paper_records = db.query_by_paper_id("paper_name")

# 统计
stats = db.get_statistics()
```

### CSV导出API

```python
from src.database import CSVExporter
from pathlib import Path

exporter = CSVExporter()

# 导出所有数据
exporter.export_all(Path("output.csv"), flatten_json=True)

# 自定义字段
fields = ['数据标识', '应用部位', '球头信息_球头基本信息']
exporter.export_custom_fields(Path("custom.csv"), fields)

# 导出指定论文
exporter.export_by_paper("paper_id", Path("paper.csv"))
```

## 📈 提取质量

基于真实论文测试（详见 EXTRACTION_SUCCESS_REPORT.md）：

### 测试结果
- ✅ 提取记录数: 9条独立实验记录
- ✅ 平均字段数: 8.1/28 (29%填充率)
- ✅ 输出格式: 100%符合JSON schema
- ✅ 数值单位: 100%包含单位
- ✅ 智能合并: LLM正确使用new和enrich

### 提取示例

**输入论文片段**：
```
The femoral head was made of CoCrMo alloy (ASTM F75, Ø28mm), 
manufactured by forging process. The surface was polished to Ra<0.05 μm. 
Hardness measured 450 HV.
```

**提取结果**：
```json
{
  "数据标识": "CoCrMo-UHMWPE摩擦磨损实验",
  "应用部位": "髋关节",
  "球头信息.球头基本信息": "{\"材料类别\": \"CoCrMo合金\", \"材料编号\": \"ASTM F75\", \"直径\": \"28 mm\", \"加工工艺\": \"锻造\", \"表面处理\": \"抛光\", \"表面粗糙度\": \"Ra<0.05 μm\"}",
  "球头信息.球头-物理性能": "{\"硬度\": \"450 HV\"}"
}
```

## 🔧 配置选项

### 提取参数

```bash
# .env 文件

# 模型选择
OPENAI_MODEL=gpt-4o          # 推荐：最佳质量
# OPENAI_MODEL=gpt-4o-mini   # 备选：更快但略少准确

# 分块参数
CHUNK_SIZE=10000             # 增大提高上下文，减小提高速度
CHUNK_OVERLAP=300            # 增大减少边界遗漏

# API配置
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_API_KEY=sk-your-key
```

### 优化建议

**追求质量**：
```bash
OPENAI_MODEL=gpt-4o
CHUNK_SIZE=15000
CHUNK_OVERLAP=500
```

**追求速度**：
```bash
OPENAI_MODEL=gpt-4o-mini
CHUNK_SIZE=8000
CHUNK_OVERLAP=200
```

**平衡方案**：
```bash
OPENAI_MODEL=gpt-4o
CHUNK_SIZE=10000
CHUNK_OVERLAP=300
```

## 📚 详细文档

- **[QUICK_USAGE_GUIDE.md](QUICK_USAGE_GUIDE.md)** - 快速使用指南
- **[DATABASE_GUIDE.md](DATABASE_GUIDE.md)** - 数据库管理完整指南
- **[EXTRACTION_SUCCESS_REPORT.md](EXTRACTION_SUCCESS_REPORT.md)** - 提取测试报告

## ❓ 常见问题

### Q: 提取结果不准确？

A: 
1. 使用 `gpt-4o` 模型（最佳质量）
2. 增大 `CHUNK_SIZE` 到15000包含更多上下文
3. 查看DEBUG日志：`python extract.py single`

### Q: 部分数据遗漏？

A:
1. 增大 `CHUNK_OVERLAP` 到500避免边界遗漏
2. 检查论文是否确实包含相关实验数据
3. 查看日志确认chunk划分情况

### Q: 提取速度慢？

A:
1. 使用 `gpt-4o-mini` 模型
2. 减小 `CHUNK_SIZE` 到8000
3. 大论文需要更长时间（每chunk约5-10秒）

### Q: CSV中文乱码？

A:
- 系统导出的CSV使用UTF-8编码（带BOM）
- Excel应该能正确打开
- 如有问题，记事本打开后另存为UTF-8

### Q: 数据库导入失败？

A:
1. 检查JSON文件格式是否正确
2. 确保dataid字段存在
3. 查看错误日志定位问题

### Q: 字段填充率低？

A:
- 这是正常的，很多论文不包含所有字段
- 平均8-10个非空字段是合理的
- 不同论文侧重点不同（如股骨柄、内衬等）

## 🎉 版本历史

### v1.2 (2025-11-03)
- ✅ 完整的数据库管理系统
- ✅ 多格式CSV导出功能
- ✅ 交互式命令行工具
- ✅ 完整的文档体系

### v1.1 (2024-11-02)
- ✅ Prompt大幅优化（570行，4个完整示例）
- ✅ 智能分块策略
- ✅ LLM自动判断new/enrich
- ✅ JSON字段智能合并

### v1.0 (2024-11-01)
- 初始版本

## 📝 系统要求

- Python 3.8+
- OpenAI API（或兼容接口）
- 已通过MinerU解析的论文（full.md格式）

## 🔄 依赖安装

```bash
pip install -r requirements.txt
```

主要依赖：
- openai
- loguru  
- python-dotenv
- tqdm

## 📞 技术支持

遇到问题？

1. 查看文档：[QUICK_USAGE_GUIDE.md](QUICK_USAGE_GUIDE.md)
2. 查看测试报告：[EXTRACTION_SUCCESS_REPORT.md](EXTRACTION_SUCCESS_REPORT.md)
3. 查看数据库指南：[DATABASE_GUIDE.md](DATABASE_GUIDE.md)

## 📄 License

MIT

---

**开始使用**: `python extract.py test` 🚀

**管理数据**: `python database.py` 💾

**查看文档**: [QUICK_USAGE_GUIDE.md](QUICK_USAGE_GUIDE.md) 📖
