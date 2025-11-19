# 人工关节材料数据提取系统

> 基于LLM的智能数据提取系统，自动从学术论文PDF中提取人工关节材料的实验数据，支持全流程自动化处理。

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Active-success.svg)]()

[快速开始](#-快速开始) •
[功能特点](#-核心功能) •
[使用文档](#-详细文档) •
[常见问题](#-常见问题)

</div>

---

## 📖 目录

- [系统概述](#系统概述)
- [核心功能](#-核心功能)
- [完整工作流程](#-完整工作流程)
- [快速开始](#-快速开始)
- [系统架构](#-系统架构)
- [LLM模型支持](#-llm模型支持)
- [典型使用场景](#-典型使用场景)
- [项目结构](#-项目结构)
- [配置说明](#️-配置说明)
- [详细文档](#-详细文档)
- [常见问题](#-常见问题)
- [更新日志](#-更新日志)
- [贡献指南](#-贡献指南)
- [许可证](#-许可证)

---

## 系统概述

本系统是一个端到端的学术论文数据提取解决方案，专门用于从人工关节材料相关的学术论文中自动提取结构化的实验数据。

### 主要特点

- 🤖 **智能提取**：基于大语言模型（LLM）的智能数据提取
- 📄 **PDF支持**：集成MinerU进行高质量PDF解析
- 🔄 **全流程自动化**：从PDF到数据库的一站式处理
- 💾 **数据管理**：完整的数据库导入/导出功能
- 🎯 **高准确度**：支持多种主流LLM模型，确保提取质量
- 🌐 **多供应商支持**：OpenAI、硅基流动、DeepSeek、智谱AI等
- 📊 **丰富导出**：支持Excel多表、CSV等多种格式
- 🎨 **友好界面**：统一菜单界面，操作简单直观

### 应用场景

- ✅ 学术论文数据整理与分析
- ✅ 材料科学数据库构建
- ✅ 实验数据自动化提取
- ✅ 科研数据管理与共享

---

## ✨ 核心功能

### 1. PDF智能解析
- 📥 批量上传PDF到MinerU云服务
- 🔍 实时查询处理状态
- 📦 自动下载解析结果
- 📝 高质量Markdown格式输出

### 2. LLM数据提取
- 🧠 支持10+主流LLM模型
- 🎯 28个字段的结构化提取
- 🔄 支持chunk和full两种模式
- ✅ JSON格式输出，格式统一

### 3. 数据库管理
- 💾 SQLite轻量级数据库
- 📥 批量导入JSON数据
- 🔍 强大的查询统计功能
- 📤 多格式数据导出

### 4. 数据导出
- 📊 **Excel多表**：按schema组织，多个sheet
- 📋 **CSV格式**：展开JSON，适合数据分析
- 🎨 **自动美化**：表头样式、列宽自适应
- 🗑️ **智能过滤**：自动过滤空数据

### 5. 统一菜单系统
- 🎯 完整工作流程引导
- 📖 内置流程指南
- 🔄 三步走操作模式
- 💡 智能错误提示

---

## 🔄 完整工作流程

### 流程概览图

```
┌─────────────┐      ┌──────────────┐      ┌─────────────┐      ┌──────────────┐      ┌─────────────┐
│  原始PDF    │ ---> │ MinerU解析   │ ---> │  LLM提取    │ ---> │  数据库存储  │ ---> │ 导出分析    │
│  论文文件   │      │  Markdown    │      │   JSON      │      │   SQLite     │      │ Excel/CSV   │
└─────────────┘      └──────────────┘      └─────────────┘      └──────────────┘      └─────────────┘
       │                    │                     │                     │                      │
    上传PDF              下载结果              提取JSON              导入DB              导出文件
```

### 详细步骤说明

<details>
<summary><b>🔹 第一步：PDF处理（点击展开）</b></summary>

#### 操作流程

1. **准备PDF文件**
   ```bash
   # 将PDF文件放入指定目录
   cp your_papers/*.pdf data/raw/pdfs/
   ```

2. **上传到MinerU**
   ```bash
   python menu.py
   # 选择：P → 1. 上传PDF文件
   ```
   - ✅ 自动扫描 `data/raw/pdfs/` 目录
   - ✅ 批量上传所有PDF
   - ✅ 获取 `batch_id`（重要！）

3. **查询处理状态**
   ```bash
   python menu.py
   # 选择：P → 2. 查询批次状态
   # 输入：上一步的 batch_id
   ```
   - 查看处理进度（处理中/已完成）
   - 等待状态变为"完成"（通常需要几分钟）

4. **下载解析结果**
   ```bash
   python menu.py
   # 选择：P → 3. 下载解析结果
   # 输入：batch_id
   ```
   - 结果保存到：`data/processed/parsed/[paper_name]/`
   - 主要文件：`full.md`（完整文本）

#### 输出示例
```
data/processed/parsed/
├── paper1/
│   ├── full.md          # 完整文本
│   ├── images/          # 提取的图片
│   └── tables/          # 提取的表格
└── paper2/
    └── full.md
```

</details>

<details>
<summary><b>🔹 第二步：数据提取（点击展开）</b></summary>

#### 操作流程

1. **测试系统配置**（首次使用推荐）
   ```bash
   python menu.py
   # 选择：1 - 测试系统配置
   ```
   - ✅ 验证LLM API配置
   - ✅ 检查论文文件
   - ✅ 测试API连接

2. **提取单个论文**（交互式）
   ```bash
   python menu.py
   # 选择：2 - 提取单个论文
   ```
   - 📋 显示所有可用论文列表
   - 🎯 选择要提取的论文
   - 👀 实时查看提取进度
   - 💾 自动保存JSON结果

3. **批量提取所有论文**
   ```bash
   python menu.py
   # 选择：3 - 批量提取所有论文
   ```
   - 🚀 自动处理所有未提取论文
   - 📊 显示处理进度
   - ⏱️ 适合大量论文处理

4. **测试单条数据**（可选）
   ```bash
   python menu.py
   # 选择：4 - 测试单条数据提取
   ```
   - 🧪 快速验证提取效果
   - 🔍 查看提取字段详情

#### 提取结果格式
```json
{
  "dataid": "AJ_20251119_abc123",
  "paper_id": "paper_name",
  "records": [
    {
      "数据标识": "CoCrMo-UHMWPE髋关节实验",
      "应用部位": "髋关节",
      "球头信息.球头基本信息": "{\"材料类别\":\"CoCrMo合金\",\"直径\":\"28 mm\"}",
      "球头信息.球头-成分组成": "{\"Co\":\"60.5 wt%\",\"Cr\":\"28.0 wt%\"}",
      "体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置": "{\"载荷\":\"50 N\",\"频率\":\"1 Hz\"}",
      ...
    }
  ],
  "count": 9
}
```

#### 提取质量指标
- ✅ **准确性**：基于prompt严格提取，不编造数据
- ✅ **完整性**：覆盖全部28个字段
- ✅ **格式统一**：100%符合JSON schema
- ✅ **平均字段数**：8-10个非空字段/记录

</details>

<details>
<summary><b>🔹 第三步：数据库管理（点击展开）</b></summary>

#### 操作流程

1. **批量导入数据**
   ```bash
   python menu.py
   # 选择：6 - 批量导入JSON到数据库
   ```
   - 📂 扫描 `data/processed/extracted/` 目录
   - 📥 批量导入所有JSON文件
   - 🔄 自动去重（基于dataid）
   - 📊 显示导入统计

2. **查看数据统计**
   ```bash
   python menu.py
   # 选择：8 - 查看数据库统计
   ```
   - 📈 总记录数
   - 📊 应用部位分布
   - 🔬 材料类型统计
   - 📉 数据质量分析

3. **导出Excel多表**（推荐）
   ```bash
   python menu.py
   # 选择：9 - 导出Excel多表
   ```
   - 📊 多个sheet，按schema组织
   - 🎨 表头样式美化
   - 📏 列宽自动调整
   - 🗑️ 过滤空表

4. **导出CSV格式**（可选）
   ```bash
   python menu.py
   # 选择：7 - 导出CSV格式
   ```
   - 📋 单表格式
   - 🔓 JSON字段展开
   - 📊 适合数据分析

#### 导出文件示例
```
data/exports/
├── artificial_joint_materials_20251119_143025.xlsx
│   ├── 基本信息
│   ├── 球头基本信息
│   ├── 球头成分
│   ├── 实验设置
│   └── ...
└── full_data_expanded_20251119_143025.csv
```

</details>

### 快速工作流（5分钟上手）

```bash
# 1️⃣ 启动系统
python menu.py

# 2️⃣ 查看流程指南（首次使用推荐）
选择: W

# 3️⃣ 处理PDF
选择: P → 上传 → 查询 → 下载

# 4️⃣ 提取数据
选择: 2 (单个) 或 3 (批量)

# 5️⃣ 管理数据
选择: 6 (导入) → 8 (统计) → 9 (导出)
```

---

## 🚀 快速开始

### 系统要求

- **Python**：3.8 或更高版本
- **操作系统**：Linux / macOS / Windows
- **依赖管理**：pip
- **必需API**：至少一个LLM API密钥

### 安装步骤

#### 1. 克隆或下载项目

```bash
# 如果使用git
git clone <repository_url>
cd sped

# 或直接下载ZIP并解压
```

#### 2. 安装Python依赖

```bash
pip install -r requirements.txt
```

主要依赖包：
- `openai` - LLM API调用
- `requests` - HTTP请求
- `python-dotenv` - 环境变量管理
- `loguru` - 日志系统
- `pandas` - 数据处理
- `openpyxl` - Excel操作

#### 3. 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑配置文件
nano .env  # 或使用你喜欢的编辑器
```

**最小配置**（必需）：

```bash
# MinerU API（用于PDF解析）
MINERU_TOKEN=your_mineru_token_here

# LLM API（至少配置一个）
SILICONFLOW_API_KEY=sk-your-key-here
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct
```

**完整配置示例**：

```bash
# ==========================
# MinerU API配置
# ==========================
MINERU_TOKEN=your_token_here
MINERU_API_BASE=https://mineru.net/api/v4

# ==========================
# LLM配置（推荐：硅基流动）
# ==========================
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=sk-your-key-here
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct

# 或使用其他供应商
# OPENAI_API_KEY=sk-your-openai-key
# DEEPSEEK_API_KEY=sk-your-deepseek-key
# ZHIPU_API_KEY=your-zhipu-key

# ==========================
# LLM参数（可选）
# ==========================
LLM_TEMPERATURE=0.1
CHUNK_SIZE=10000
CHUNK_OVERLAP=300

# ==========================
# 数据库配置（可选）
# ==========================
DB_PATH=data/artificial_joint.db
```

#### 4. 测试系统

```bash
# 方式一：使用菜单测试
python menu.py
# 选择：1 - 测试系统配置

# 方式二：直接运行测试
python scripts/extract.py test
```

预期输出：
```
✅ LLM配置正确
✅ 找到 125 篇已解析论文
✅ API连接成功
✅ 系统测试通过！
```

#### 5. 开始使用

```bash
python menu.py
```

**首次使用建议**：
1. 按 `W` 查看完整流程指南
2. 按 `1` 测试系统配置
3. 按 `4` 测试单条数据提取
4. 熟悉后开始正式处理

---

## 🏗️ 系统架构

### 技术栈

```
┌─────────────────────────────────────────────────┐
│                   用户界面层                     │
│         menu.py (统一菜单) + 命令行脚本          │
└─────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────┐
│                   业务逻辑层                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ PDF处理  │  │ LLM提取  │  │ 数据库   │     │
│  │  模块    │  │   模块   │  │  模块    │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────┐
│                   数据访问层                     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │ MinerU   │  │ OpenAI   │  │ SQLite   │     │
│  │   API    │  │Compatible│  │ Database │     │
│  └──────────┘  └──────────┘  └──────────┘     │
└─────────────────────────────────────────────────┘
                        │
┌─────────────────────────────────────────────────┐
│                   数据存储层                     │
│     文件系统 + SQLite数据库 + JSON文件          │
└─────────────────────────────────────────────────┘
```

### 核心模块

| 模块 | 功能 | 技术 |
|------|------|------|
| **PDF处理** | PDF上传、解析、下载 | MinerU API, requests |
| **LLM提取** | 智能数据提取 | OpenAI SDK, 多LLM支持 |
| **数据库管理** | 数据存储、查询 | SQLite, pandas |
| **数据导出** | Excel/CSV导出 | openpyxl, pandas |
| **菜单系统** | 交互式界面 | Python标准库 |

### 数据流向

```
PDF文件 → MinerU解析 → LLM提取 → 数据库存储 → 导出分析
   ↓           ↓          ↓          ↓           ↓
 上传PDF    下载结果   提取JSON    导入DB    导出Excel/CSV
```

### 流程详解

#### 第一步：PDF处理（MinerU）
1. **上传PDF**：将原始PDF上传到MinerU进行解析
   - 放置PDF到 `data/raw/pdfs/`
   - 运行 `python scripts/pdf_process.py` → 选择"上传"
   - 记录返回的 batch_id

2. **查询状态**：等待MinerU处理完成
   - 运行 `python scripts/pdf_process.py` → 选择"查询"
   - 输入batch_id查看处理进度

3. **下载结果**：获取解析后的文档
   - 运行 `python scripts/pdf_process.py` → 选择"下载"
   - 结果保存到 `data/processed/parsed/`

#### 第二步：数据提取（LLM）
1. **测试系统**：验证配置正确
   ```bash
   python scripts/extract.py test
   ```

2. **提取数据**：使用LLM从解析后的论文中提取结构化数据
   ```bash
   # 单个提取（交互式选择）
   python scripts/extract.py single
   
   # 批量提取所有论文
   python scripts/extract.py batch
   ```

3. **查看结果**：提取的JSON保存到 `data/processed/extracted/`

#### 第三步：数据库管理
1. **导入数据**：将JSON导入SQLite数据库
   ```bash
   python scripts/database.py
   # 选择：批量导入JSON文件
   ```

2. **查看统计**：了解数据概况
   ```bash
   python scripts/database.py
   # 选择：查看数据库统计
   ```

3. **导出数据**：导出为Excel或CSV格式
   ```bash
   python scripts/database.py
   # 选择：导出Excel多表
   # 或：导出CSV格式
   ### 数据流向

```mermaid
graph LR
    A[PDF文件] -->|上传| B[MinerU云服务]
    B -->|解析| C[Markdown文本]
    C -->|下载| D[本地存储]
    D -->|LLM处理| E[JSON数据]
    E -->|导入| F[SQLite数据库]
    F -->|导出| G[Excel/CSV]
```

**文本描述**：
```
PDF文件 (data/raw/pdfs/)
    ↓ MinerU上传
云端处理 (batch_id)
    ↓ 等待完成
Markdown (data/processed/parsed/)
    ↓ LLM提取
JSON数据 (data/processed/extracted/)
    ↓ 数据库导入
SQLite (data/artificial_joint.db)
    ↓ 数据导出
Excel/CSV (data/exports/)
```

---

## 🤖 LLM模型支持

### 支持的供应商

| 供应商 | 推荐模型 | Max Tokens | 价格/性能 | 推荐场景 |
|--------|---------|------------|-----------|----------|
| **硅基流动** ⭐ | Qwen/Qwen2.5-72B-Instruct | 30000 | 💰💰 高性价比 | 推荐，国内访问快 |
| 硅基流动 | moonshotai/Kimi-K2-Instruct-0905 | 16000 | 💰💰💰 中等 | 高质量提取 |
| 硅基流动 | Qwen/Qwen2.5-7B-Instruct | 30000 | 💰 便宜 | 快速测试 |
| OpenAI | gpt-4o | 16000 | 💰💰💰💰 昂贵 | 最高准确度 |
| OpenAI | gpt-4o-mini | 16000 | 💰💰 适中 | 平衡选择 |
| DeepSeek | deepseek-chat | 8000 | 💰 便宜 | 性价比高 |
| 智谱AI | glm-4-plus | 16000 | 💰💰 适中 | 国产优质 |

### 模型选择建议

**🎯 推荐配置**：
```bash
# 日常使用（推荐）
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct

# 高质量要求
OPENAI_MODEL=gpt-4o

# 快速测试
SILICONFLOW_MODEL=Qwen/Qwen2.5-7B-Instruct

# 成本优化
DEEPSEEK_MODEL=deepseek-chat
```

**查看所有支持的模型**：
```bash
python scripts/extract.py --list-models
```

### 模型切换方法

**方式一**：修改 `.env` 文件
```bash
# 编辑 .env
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct
```

**方式二**：命令行参数
```bash
python scripts/extract.py single --model "gpt-4o"
```

---

## 🎯 典型使用场景

### 场景1：处理新的PDF论文（完整流程）

**目标**：从零开始处理一批新的PDF论文

```bash
# 步骤1：准备PDF文件
cp ~/Downloads/papers/*.pdf data/raw/pdfs/

# 步骤2：启动系统
python menu.py

# 步骤3：按顺序操作
选择 W  # 首次使用，查看流程指南
选择 P  # 进入PDF处理
  → 1. 上传PDF文件
  → 记录batch_id: batch_xxx
  
# 等待5-10分钟后
选择 P  # 再次进入PDF处理
  → 2. 查询批次状态
  → 输入batch_id
  → 确认状态为"已完成"
  
选择 P  # 下载结果
  → 3. 下载解析结果
  → 输入batch_id
  
# 提取数据
选择 3  # 批量提取所有论文
# 或
选择 2  # 提取单个论文（逐个检查）

# 导入数据库
选择 6  # 批量导入JSON

# 查看和导出
选择 8  # 查看统计
选择 9  # 导出Excel
```

**预期时间**：
- PDF上传：1-2分钟
- MinerU处理：5-10分钟
- 数据提取：每篇2-3分钟
- 数据导入：<1分钟
- 数据导出：<1分钟

---

### 场景2：快速测试系统（新用户）

**目标**：验证系统配置，测试提取效果

```bash
python menu.py

# 快速测试流程
选择 1  # 测试系统配置
选择 4  # 测试单条数据提取
选择 8  # 查看数据库统计
```

**检查清单**：
- ✅ API配置正确
- ✅ 论文文件存在
- ✅ API连接成功
- ✅ 提取结果符合预期

---

### 场景3：批量处理已有数据（高效模式）

**目标**：已有解析好的论文，快速批量提取

```bash
# 假设已有论文在 data/processed/parsed/

# 方式一：使用菜单
python menu.py
选择 3  # 批量提取
选择 6  # 批量导入
选择 9  # 导出Excel

# 方式二：直接使用脚本（更快）
python scripts/extract.py batch
python menu.py
选择 6  # 批量导入
选择 9  # 导出Excel
```

---

### 场景4：更换LLM模型对比（质量测试）

**目标**：对比不同模型的提取质量

```bash
# 测试1：使用Qwen模型
python scripts/extract.py single --model "Qwen/Qwen2.5-72B-Instruct"

# 测试2：使用GPT-4o模型
python scripts/extract.py single --model "gpt-4o"

# 对比JSON结果
diff data/processed/extracted/paper1_qwen.json \
     data/processed/extracted/paper1_gpt4o.json
```

---

### 场景5：定期数据更新（自动化）

**目标**：每周处理新论文并更新数据库

```bash
#!/bin/bash
# weekly_update.sh

# 1. 处理新PDF（假设已上传到MinerU）
cd /path/to/sped

# 2. 下载最新结果
python scripts/pdf_process.py  # 选择下载

# 3. 批量提取
python scripts/extract.py batch

# 4. 导入数据库
python menu.py <<EOF
6
y
0
EOF

# 5. 导出最新数据
python menu.py <<EOF
9
0
EOF

# 6. 备份数据库
cp data/artificial_joint.db backups/artificial_joint_$(date +%Y%m%d).db

echo "✅ 数据更新完成！"
```

---

## 📁 项目结构

```
sped/                           # 项目根目录
│
├── menu.py                     # 🎯 统一菜单入口（推荐使用）
├── settings.py                 # ⚙️ 全局配置管理
├── requirements.txt            # 📦 Python依赖列表
├── .env                        # 🔐 环境变量配置（需创建）
├── .env.example                # 📝 环境变量模板
├── README.md                   # 📖 本文档
│
├── scripts/                    # 📜 功能脚本
│   ├── pdf_process.py          # 📄 PDF处理（上传/查询/下载）
│   ├── extract.py              # 📝 数据提取（单个/批量）
│   └── database.py             # 💾 数据库管理（导入/导出）
│
├── src/                        # 🔧 核心源代码
│   ├── agents/                 # 🤖 智能代理
│   │   ├── llm_agent.py        # LLM提取逻辑
│   │   ├── base_agent.py       # 基础Agent类
│   │   └── database_agent.py   # 数据库Agent
│   │
│   ├── database/               # 💾 数据库模块
│   │   ├── db_manager.py       # 数据库管理器
│   │   ├── csv_exporter.py     # CSV导出器
│   │   └── excel_exporter.py   # Excel导出器
│   │
│   ├── pdfs/                   # 📄 PDF处理工具
│   │   ├── upload.py           # PDF上传
│   │   ├── download.py         # 结果下载
│   │   └── request.py          # 状态查询
│   │
│   ├── extractors/             # 🔍 提取器
│   │   ├── extractor.py        # 主提取器
│   │   ├── paper_scanner.py    # 论文扫描器
│   │   └── interactive_ui.py   # 交互界面
│   │
│   ├── pipeline/               # 🔄 数据管道
│   │   └── processor.py        # 数据处理器
│   │
│   └── utils/                  # 🛠️ 工具函数
│       └── prompt_builder.py   # Prompt构建器
│
├── data/                       # 📊 数据目录
│   ├── raw/                    # 原始数据
│   │   └── pdfs/               # 📄 第1步：待处理PDF
│   │
│   ├── processed/              # 处理结果
│   │   ├── parsed/             # 📝 第2步：MinerU解析结果
│   │   │   └── [paper_name]/
│   │   │       ├── full.md     # 完整Markdown文本
│   │   │       ├── images/     # 提取的图片
│   │   │       └── tables/     # 提取的表格
│   │   │
│   │   └── extracted/          # 📋 第3步：LLM提取JSON
│   │       └── [paper_name].json
│   │
│   ├── exports/                # 📤 第4步：导出文件
│   │   ├── *.xlsx              # Excel多表格式
│   │   └── *.csv               # CSV格式
│   │
│   ├── uploads/                # 📤 上传记录
│   │   └── upload_batches.csv  # 批次记录
│   │
│   └── artificial_joint.db     # 💾 SQLite数据库
│
├── prompts/                    # 💬 提示词模板
│   └── prompt.md               # LLM提取使用的提示词
│
├── data_schema/                # 📋 数据Schema
│   ├── schema.xlsx             # Excel格式Schema
│   ├── inferred_schema.json    # JSON格式Schema
│   └── inferred_schema.sql     # SQL格式Schema
│
├── docs/                       # 📚 详细文档
│   ├── USAGE.md                # 使用指南
│   └── DATABASE.md             # 数据库管理指南
│
└── logs/                       # 📝 日志文件
    └── *.log                   # 系统运行日志
```

### 关键文件说明

| 文件/目录 | 说明 | 重要性 |
|----------|------|--------|
| `menu.py` | 统一菜单入口 | ⭐⭐⭐⭐⭐ |
| `.env` | 环境变量配置 | ⭐⭐⭐⭐⭐ |
| `settings.py` | 全局配置 | ⭐⭐⭐⭐ |
| `prompts/prompt.md` | LLM提示词 | ⭐⭐⭐⭐ |
| `data/artificial_joint.db` | 主数据库 | ⭐⭐⭐⭐⭐ |
| `data_schema/` | 数据结构定义 | ⭐⭐⭐ |
| `docs/` | 详细文档 | ⭐⭐⭐⭐ |

---

## ⚙️ 配置说明

### 环境变量配置

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 环境变量配置

完整的 `.env` 配置文件结构：

```bash
# ==========================
# MinerU API配置
# ==========================
MINERU_TOKEN=your_token_here
MINERU_API_BASE=https://mineru.net/api/v4
BATCH_SIZE=200
UPLOAD_ENABLE_FORMULA=True
UPLOAD_LANGUAGE=en

# ==========================
# 数据库配置
# ==========================
DB_PATH=data/artificial_joint.db

# ==========================
# LLM API配置
# ==========================
LLM_PROVIDER=siliconflow                        # 使用的供应商

# OpenAI配置
OPENAI_API_KEY=sk-your-key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# 硅基流动配置（推荐）
SILICONFLOW_API_KEY=sk-your-key
SILICONFLOW_API_BASE=https://api.siliconflow.cn/v1
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct

# DeepSeek配置
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_API_BASE=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-chat

# 智谱AI配置
ZHIPU_API_KEY=your-key
ZHIPU_API_BASE=https://open.bigmodel.cn/api/paas/v4
ZHIPU_MODEL=glm-4-plus

# ==========================
# LLM调用参数
# ==========================
LLM_TEMPERATURE=0.1                             # 温度参数（0-2，越低越确定）
LLM_TOP_P=0.95                                  # Top-p采样（0-1）
CHUNK_MODE_MAX_TOKENS=4096                      # chunk模式token限制
CHUNK_SIZE=10000                                # 文本分块大小
CHUNK_OVERLAP=300                               # 分块重叠大小

# ==========================
# 网络配置
# ==========================
HTTP_REQUEST_TIMEOUT=30                         # HTTP请求超时（秒）
DOWNLOAD_TIMEOUT=300                            # 下载超时（秒）
DOWNLOAD_RETRY=3                                # 下载重试次数
DOWNLOAD_CHUNK_SIZE=8192                        # 下载分块大小

# ==========================
# 日志配置
# ==========================
LOG_LEVEL=INFO                                  # 日志级别：DEBUG/INFO/WARNING/ERROR
```

### 配置项详解

<details>
<summary><b>🔹 MinerU配置</b></summary>

| 参数 | 说明 | 默认值 | 必需 |
|------|------|--------|------|
| `MINERU_TOKEN` | MinerU API token | - | ✅ |
| `MINERU_API_BASE` | API基础URL | https://mineru.net/api/v4 | ❌ |
| `BATCH_SIZE` | 批量上传大小 | 200 | ❌ |
| `UPLOAD_ENABLE_FORMULA` | 启用公式识别 | True | ❌ |
| `UPLOAD_LANGUAGE` | 文档语言 | en | ❌ |

</details>

<details>
<summary><b>🔹 LLM配置</b></summary>

| 参数 | 说明 | 推荐值 | 调优建议 |
|------|------|--------|----------|
| `LLM_TEMPERATURE` | 控制输出随机性 | 0.1 | 提取任务保持低值（0-0.2） |
| `LLM_TOP_P` | 控制输出多样性 | 0.95 | 一般不需要调整 |
| `CHUNK_SIZE` | 文本分块大小 | 10000 | 长文档增大到15000 |
| `CHUNK_OVERLAP` | 分块重叠 | 300 | 需要更多上下文时增大到500 |
| `CHUNK_MODE_MAX_TOKENS` | chunk模式token | 4096 | 根据模型调整 |

</details>

<details>
<summary><b>🔹 网络配置</b></summary>

| 参数 | 说明 | 默认值 | 场景 |
|------|------|--------|------|
| `HTTP_REQUEST_TIMEOUT` | HTTP超时 | 30秒 | 网络慢时增大 |
| `DOWNLOAD_TIMEOUT` | 下载超时 | 300秒 | 大文件时增大 |
| `DOWNLOAD_RETRY` | 下载重试次数 | 3次 | 网络不稳定时增大 |

</details>

---

## 📚 详细文档

### 核心文档

| 文档 | 内容 | 适合人群 |
|------|------|----------|
| **[USAGE.md](docs/USAGE.md)** | 完整使用指南 | 所有用户 ⭐⭐⭐⭐⭐ |
| **[DATABASE.md](docs/DATABASE.md)** | 数据库管理指南 | 数据管理员 ⭐⭐⭐⭐ |
| **[README.md](README.md)** | 项目概览（本文档） | 快速了解 ⭐⭐⭐⭐⭐ |

### 文档导航

**🔰 新手入门**
1. 阅读本 README 的"快速开始"
2. 配置 `.env` 文件
3. 运行 `python menu.py`，选择 `W` 查看流程指南
4. 按照流程一步步操作

**🔧 进阶使用**
1. 阅读 [USAGE.md](docs/USAGE.md) 了解所有功能
2. 根据需求调整配置参数
3. 探索不同的LLM模型
4. 优化提取效果

**💾 数据管理**
1. 阅读 [DATABASE.md](docs/DATABASE.md)
2. 了解数据库结构
3. 学习数据导入导出
4. 掌握数据维护技巧

**🎓 高级定制**
1. 研究 `prompts/prompt.md` 提示词
2. 修改提示词以适应特定需求
3. 调整LLM参数获得最佳效果
4. 开发自定义功能模块

---

## 💡 常见问题

### 安装与配置

<details>
<summary><b>Q: 首次使用需要做什么？</b></summary>

**A**: 按照以下步骤：

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境**
   ```bash
   cp .env.example .env
   nano .env  # 编辑配置
   ```

3. **测试系统**
   ```bash
   python scripts/extract.py test
   ```

4. **查看指南**
   ```bash
   python menu.py
   # 选择 W
   ```

</details>

<details>
<summary><b>Q: 如何获取API密钥？</b></summary>

**A**: 

**MinerU**：
1. 访问 https://mineru.net
2. 注册账号
3. 获取API token

**硅基流动**（推荐）：
1. 访问 https://siliconflow.cn
2. 注册账号
3. 创建API密钥

**OpenAI**：
1. 访问 https://platform.openai.com
2. 注册账号
3. 创建API密钥

**DeepSeek**：
1. 访问 https://platform.deepseek.com
2. 注册账号
3. 获取API密钥

</details>

<details>
<summary><b>Q: 支持Windows系统吗？</b></summary>

**A**: 是的，完全支持Windows系统。

**注意事项**：
- 使用 PowerShell 或 CMD
- 路径分隔符会自动处理
- 部分shell脚本需要使用Git Bash

</details>

---

### PDF处理

<details>
<summary><b>Q: PDF如何解析？</b></summary>

**A**: 使用MinerU云服务进行解析。

**流程**：
1. 上传PDF到MinerU
2. 等待云端处理（5-10分钟）
3. 下载解析后的Markdown

**支持的PDF类型**：
- ✅ 学术论文
- ✅ 扫描版PDF（OCR）
- ✅ 含公式和表格的PDF
- ❌ 加密PDF
- ❌ 损坏的PDF

</details>

<details>
<summary><b>Q: MinerU处理失败怎么办？</b></summary>

**A**: 

1. **检查PDF质量**
   - 确保PDF未加密
   - 确保PDF未损坏
   - 文件大小<100MB

2. **重新上传**
   - 删除失败的批次
   - 重新上传PDF

3. **联系支持**
   - 如果持续失败，联系MinerU技术支持

</details>

---

### 数据提取

<details>
<summary><b>Q: 支持哪些LLM？</b></summary>

**A**: 支持所有OpenAI兼容API的模型。

**已测试的模型**：
- ✅ OpenAI: gpt-4o, gpt-4o-mini, gpt-4-turbo
- ✅ 硅基流动: Qwen系列, Kimi, DeepSeek-V2.5
- ✅ DeepSeek: deepseek-chat
- ✅ 智谱AI: glm-4-plus, glm-4-flash

**推荐模型**：
- 🥇 **Qwen/Qwen2.5-72B-Instruct**（性价比最高）
- 🥈 **gpt-4o**（质量最好）
- 🥉 **moonshotai/Kimi-K2-Instruct-0905**（平衡选择）

</details>

<details>
<summary><b>Q: 如何提高提取质量？</b></summary>

**A**: 多个优化策略：

**1. 选择更强的模型**
```bash
# 从这个
SILICONFLOW_MODEL=Qwen/Qwen2.5-7B-Instruct

# 改为这个
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct
# 或
OPENAI_MODEL=gpt-4o
```

**2. 调整chunk参数**
```bash
# 增大chunk以获得更多上下文
CHUNK_SIZE=15000       # 从10000增大到15000
CHUNK_OVERLAP=500      # 从300增大到500
```

**3. 降低温度参数**
```bash
# 减少随机性
LLM_TEMPERATURE=0.05   # 从0.1降低到0.05
```

**4. 优化prompt**
- 编辑 `prompts/prompt.md`
- 添加更多示例
- 明确字段定义

**5. 使用full模式**
```bash
# 对于短文档，使用full模式而非chunk
python scripts/extract.py single --mode full
```

</details>

<details>
<summary><b>Q: 提取速度慢怎么办？</b></summary>

**A**: 

**1. 使用更快的模型**
```bash
SILICONFLOW_MODEL=Qwen/Qwen2.5-7B-Instruct
```

**2. 减小chunk大小**
```bash
CHUNK_SIZE=8000
```

**3. 批量处理**
```bash
python scripts/extract.py batch
```

**4. 并行处理**（高级）
- 修改代码支持多线程
- 使用多个API密钥

</details>

---

### 数据库管理

<details>
<summary><b>Q: 数据存储在哪里？</b></summary>

**A**: 

```
data/
├── raw/pdfs/                   # 原始PDF
├── processed/parsed/           # 解析结果
├── processed/extracted/        # 提取JSON
├── artificial_joint.db         # 主数据库
└── exports/                    # 导出文件
```

**推荐备份**：
- `data/artificial_joint.db` - 数据库
- `data/processed/extracted/` - JSON文件
- `.env` - 配置文件

</details>

<details>
<summary><b>Q: 如何备份数据？</b></summary>

**A**: 

**方式一：手动备份**
```bash
# 备份数据库
cp data/artificial_joint.db backups/db_$(date +%Y%m%d).db

# 备份JSON文件
tar -czf backups/extracted_$(date +%Y%m%d).tar.gz \
    data/processed/extracted/
```

**方式二：使用Git**
```bash
git add data/artificial_joint.db
git commit -m "Backup database"
```

**方式三：导出Excel**
```bash
python menu.py
# 选择：9 - 导出Excel
# Excel文件自带时间戳
```

</details>

<details>
<summary><b>Q: 导入时出现重复记录？</b></summary>

**A**: 

系统会自动去重（基于`dataid`）。

**如果仍有重复**：
1. 检查JSON文件的dataid是否唯一
2. 手动删除重复记录：
   ```bash
   python scripts/database.py
   # 选择：删除重复记录
   ```

</details>

---

### 错误处理

<details>
<summary><b>Q: 遇到 "API密钥未配置" 错误？</b></summary>

**A**: 

1. 检查 `.env` 文件是否存在
2. 确认API密钥已正确填写
3. 重启程序使配置生效

```bash
# 检查配置
cat .env | grep API_KEY

# 测试API
python scripts/extract.py test
```

</details>

<details>
<summary><b>Q: 遇到 "连接超时" 错误？</b></summary>

**A**: 

**可能原因**：
1. 网络问题
2. API服务不可用
3. 超时时间设置过短

**解决方案**：
```bash
# 增大超时时间
HTTP_REQUEST_TIMEOUT=60
DOWNLOAD_TIMEOUT=600

# 检查网络
ping api.siliconflow.cn

# 尝试其他API
LLM_PROVIDER=openai
```

</details>

<details>
<summary><b>Q: 遇到 "JSON解析错误"？</b></summary>

**A**: 

**原因**：LLM返回的不是有效JSON

**解决方案**：
1. 降低temperature参数
2. 使用更好的模型
3. 检查prompt模板

```bash
# 1. 降低temperature
LLM_TEMPERATURE=0.05

# 2. 使用更好的模型
OPENAI_MODEL=gpt-4o

# 3. 查看错误日志
cat logs/latest.log | grep ERROR
```

</details>

---

## 🔄 更新日志

### v1.0.0 (2025-01-19)

**🎉 首次发布**

**核心功能**：
- ✅ PDF上传、解析、下载
- ✅ LLM智能数据提取
- ✅ 数据库管理
- ✅ Excel/CSV导出
- ✅ 统一菜单系统

**支持的模型**：
- OpenAI: gpt-4o, gpt-4o-mini, gpt-4-turbo
- 硅基流动: Qwen, Kimi, DeepSeek
- DeepSeek: deepseek-chat
- 智谱AI: glm-4-plus, glm-4-flash

**文档**：
- 完整README
- 使用指南
- 数据库管理指南

---

## 🤝 贡献指南

欢迎贡献！以下是参与项目的方式：

### 报告问题

在GitHub Issues中报告：
- 🐛 Bug报告
- 💡 功能建议
- 📝 文档改进
- ❓ 使用问题

### 贡献代码

1. Fork本项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启Pull Request

### 贡献文档

- 改进README
- 添加使用示例
- 翻译文档
- 修复错误

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## 👥 作者与致谢

**开发团队**: [Your Team Name]

**特别感谢**:
- MinerU - PDF解析服务
- OpenAI - LLM API
- 硅基流动 - 高性价比LLM服务
- 所有贡献者

---

## 📞 联系方式

- 📧 Email: your.email@example.com
- 💬 Issues: [GitHub Issues](https://github.com/your/repo/issues)
- 📖 文档: [Documentation](docs/)

---

## 🌟 Star History

如果这个项目对你有帮助，请给个⭐️支持一下！

---

<div align="center">

**[⬆ 回到顶部](#人工关节材料数据提取系统)**

Made with ❤️ by [Your Team]

</div>
