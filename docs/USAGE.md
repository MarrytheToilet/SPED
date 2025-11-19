# 使用指南

## 📖 目录

1. [完整工作流程](#完整工作流程)
2. [快速开始](#快速开始)
3. [数据提取](#数据提取)
4. [数据库管理](#数据库管理)
5. [PDF处理](#pdf处理)
6. [LLM模型配置](#llm模型配置)
7. [高级配置](#高级配置)

---

## 完整工作流程

### 流程概览

```
PDF文件 → MinerU解析 → LLM提取 → 数据库存储 → 导出分析
   ↓           ↓          ↓          ↓           ↓
 上传PDF    下载结果   提取JSON    导入DB    导出Excel/CSV
```

### 详细步骤

#### 阶段一：PDF处理（MinerU解析）

**目标**：将原始PDF转换为结构化的Markdown文本

1. **准备PDF文件**
   ```bash
   # 将PDF文件放入指定目录
   cp your_paper.pdf data/raw/pdfs/
   ```

2. **上传到MinerU**
   ```bash
   python menu.py
   # 选择 P → 1. 上传PDF文件
   ```
   - 系统会扫描 `data/raw/pdfs/` 目录
   - 批量上传所有PDF
   - 记录返回的 `batch_id`

3. **查询处理状态**
   ```bash
   python menu.py
   # 选择 P → 2. 查询批次状态
   # 输入上一步获得的 batch_id
   ```
   - 查看处理进度
   - 等待状态变为"完成"

4. **下载解析结果**
   ```bash
   python menu.py
   # 选择 P → 3. 下载解析结果
   # 输入 batch_id
   ```
   - 结果保存到 `data/processed/parsed/[paper_name]/`
   - 主要文件：`full.md`（完整文本）

#### 阶段二：数据提取（LLM智能提取）

**目标**：从Markdown文本中提取结构化的实验数据

1. **测试系统配置**（首次使用）
   ```bash
   python menu.py
   # 选择 1 - 测试系统配置
   ```
   - 验证LLM API配置正确
   - 检查论文文件是否存在
   - 测试API连接

2. **提取单个论文**
   ```bash
   python menu.py
   # 选择 2 - 提取单个论文
   ```
   - 交互式选择要提取的论文
   - 实时查看提取进度
   - 结果保存为JSON

3. **批量提取所有论文**
   ```bash
   python menu.py
   # 选择 3 - 批量提取所有论文
   ```
   - 自动处理所有未提取的论文
   - 适合大量论文处理
   - 提取结果保存到 `data/processed/extracted/`

4. **查看提取结果**
   ```bash
   # JSON文件保存在
   ls data/processed/extracted/*.json
   ```
   - 每个论文对应一个JSON文件
   - 包含所有提取的实验记录

#### 阶段三：数据库管理（存储与查询）

**目标**：将JSON数据导入数据库，便于查询和分析

1. **批量导入数据**
   ```bash
   python menu.py
   # 选择 6 - 批量导入JSON到数据库
   ```
   - 扫描 `data/processed/extracted/` 目录
   - 批量导入所有JSON文件
   - 自动去重（基于dataid）

2. **查看数据统计**
   ```bash
   python menu.py
   # 选择 8 - 查看数据库统计
   ```
   - 查看总记录数
   - 应用部位分布
   - 材料类型统计

3. **导出数据**
   ```bash
   python menu.py
   # 选择 9 - 导出Excel多表
   # 或选择 7 - 导出CSV格式
   ```
   - Excel：多个sheet，结构化清晰
   - CSV：单表，便于数据分析
   - 导出到 `data/exports/`

### 快速工作流（完整示例）

假设你有新的PDF论文需要处理，完整流程：

```bash
# 启动系统
python menu.py

# 依次选择：
W  → 查看流程指南（首次使用）
P  → 上传PDF
P  → 查询状态（等待完成）
P  → 下载结果
2  → 提取单个论文（或 3 批量提取）
6  → 导入数据库
8  → 查看统计
9  → 导出Excel
```

### 数据流向图

```
data/raw/pdfs/your_paper.pdf
    ↓
[MinerU上传] → batch_id
    ↓
[MinerU处理] → 等待完成
    ↓
[下载结果]
    ↓
data/processed/parsed/your_paper/full.md
    ↓
[LLM提取]
    ↓
data/processed/extracted/your_paper.json
    {
      "dataid": "AJ_20251119_abc123",
      "paper_id": "your_paper",
      "records": [
        {
          "数据标识": "实验1",
          "应用部位": "髋关节",
          ...
        }
      ]
    }
    ↓
[导入数据库]
    ↓
data/artificial_joint.db
    ↓
[导出数据]
    ↓
data/exports/artificial_joint_materials_20251119.xlsx
```

---

## 快速开始

### 1. 测试系统

```bash
python scripts/extract.py test
```

输出示例：
```
✅ LLM配置正确
✅ 找到 125 篇已解析论文
✅ API连接成功
✅ 系统测试通过！
```

### 2. 提取单篇论文

```bash
# 使用菜单
python menu.py

# 或直接运行
python scripts/extract.py single
```

然后从列表中选择论文编号。

### 3. 批量提取

```bash
python scripts/extract.py batch
```

---

## 数据提取

### 提取模式

系统支持两种提取模式：

1. **full模式**（默认）：一次性处理整篇论文
   - 适合：短篇论文（<10000字符）
   - 优点：速度快，上下文完整
   
2. **chunk模式**：分块迭代处理
   - 适合：长篇论文
   - 优点：处理超长文本，避免token限制

### 提取结果

提取结果保存为JSON格式：

```json
{
  "dataid": "AJ_20251103_4026ca86",
  "paper_id": "论文标题",
  "records": [
    {
      "数据标识": "实验描述",
      "应用部位": "髋关节",
      "球头信息.球头基本信息": "{\"材料类别\": \"CoCrMo\", \"直径\": \"28 mm\"}",
      ...
    }
  ],
  "count": 9
}
```

**输出路径**：`data/processed/extracted/`

### 指定模型提取

```bash
# 使用特定模型
python scripts/extract.py single --model "gpt-4o"

# 查看所有可用模型
python scripts/extract.py --list-models
```

### 查看提取日志

提取过程会显示详细日志：
- 使用的模型和配置
- Chunk信息（chunk模式）
- 提取的记录数
- 错误信息（如有）

---

## 数据库管理

### 启动数据库管理工具

```bash
python scripts/database.py
```

### 主要功能

1. **导入数据**
   - 批量导入JSON文件到数据库
   - 自动去重（基于dataid）
   
2. **导出数据**
   - 导出为CSV格式
   - 导出为Excel（多表格式）
   
3. **查看统计**
   - 总记录数
   - 各应用部位统计
   - 各材料类型统计
   
4. **数据清理**
   - 删除重复记录
   - 删除特定记录

### 快速命令

```bash
# 批量导入
python menu.py  # 选择选项6

# 导出CSV
python menu.py  # 选择选项7

# 导出Excel
python menu.py  # 选择选项9
```

---

## PDF处理

### 上传PDF到MinerU

```bash
python scripts/pdf_process.py
# 选择：1 - 上传PDF文件
```

步骤：
1. 将PDF放入 `data/raw/pdfs/`
2. 运行上传脚本
3. 记录返回的batch_id

### 查询处理状态

```bash
python scripts/pdf_process.py
# 选择：2 - 查询批次状态
# 输入batch_id
```

### 下载解析结果

```bash
python scripts/pdf_process.py
# 选择：3 - 下载解析结果
# 输入batch_id
```

结果保存在：`data/processed/parsed/output/`

---

## LLM模型配置

### 支持的供应商

| 供应商 | 配置前缀 | API Base |
|--------|---------|----------|
| 硅基流动 | SILICONFLOW | https://api.siliconflow.cn/v1 |
| OpenAI | OPENAI | https://api.openai.com/v1 |
| DeepSeek | DEEPSEEK | https://api.deepseek.com/v1 |
| 智谱AI | ZHIPU | https://open.bigmodel.cn/api/paas/v4 |

### 配置示例

#### 硅基流动（推荐）

```bash
# .env
SILICONFLOW_API_KEY=sk-your-key
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct
```

优势：
- 国内访问快
- 支持多种开源模型
- 性价比高

#### OpenAI

```bash
# .env
OPENAI_API_KEY=sk-your-key
OPENAI_MODEL=gpt-4o
```

优势：
- 质量最高
- 稳定可靠

#### DeepSeek

```bash
# .env
DEEPSEEK_API_KEY=sk-your-key
DEEPSEEK_MODEL=deepseek-chat
```

优势：
- 国产优质
- 性价比高

### 模型选择建议

| 场景 | 推荐模型 | 原因 |
|------|---------|------|
| 高准确度 | gpt-4o | 最强理解能力 |
| 平衡性能 | Qwen/Qwen2.5-72B-Instruct | 质量好，速度快 |
| 快速测试 | Qwen/Qwen2.5-7B-Instruct | 快速响应 |
| 成本优化 | deepseek-chat | 性价比最高 |

---

## 高级配置

### LLM参数调优

```bash
# .env

# 温度（0-2）：控制随机性，越低越确定
LLM_TEMPERATURE=0.1

# Top-p采样（0-1）：控制多样性
LLM_TOP_P=0.95

# 频率惩罚（-2.0到2.0）：减少重复
LLM_FREQUENCY_PENALTY=0.0

# 存在惩罚（-2.0到2.0）：鼓励新话题
LLM_PRESENCE_PENALTY=0.0
```

### 文本分块配置

```bash
# .env

# 每个chunk的字符数
CHUNK_SIZE=10000

# chunk之间的重叠字符数
CHUNK_OVERLAP=300
```

调优建议：
- 长文档：增大 CHUNK_SIZE 到 15000
- 需要更多上下文：增大 CHUNK_OVERLAP 到 500
- 加速处理：减小 CHUNK_SIZE 到 8000

### 网络配置

```bash
# .env

# HTTP请求超时（秒）
HTTP_REQUEST_TIMEOUT=30

# 下载超时（秒）
DOWNLOAD_TIMEOUT=300

# 下载重试次数
DOWNLOAD_RETRY=3

# 下载分块大小（字节）
DOWNLOAD_CHUNK_SIZE=8192
```

### 模型Token限制配置

如需调整特定模型的token限制：

```bash
# .env
GPT4O_MAX_TOKENS=16000
QWEN_72B_MAX_TOKENS=30000
KIMI_MAX_TOKENS=16000
DEEPSEEK_CHAT_MAX_TOKENS=8000
```

### 目录结构说明

```
data/
├── raw/
│   └── pdfs/                    # 待上传的PDF
├── processed/
│   ├── parsed/                  # MinerU解析结果
│   │   └── output/              # 下载的解析文件
│   └── extracted/               # LLM提取的JSON
└── artificial_joint.db          # SQLite数据库
```

---

## 常见问题

### Q: 提取失败怎么办？

1. 检查API配置是否正确
2. 查看日志文件了解错误详情
3. 尝试更换模型
4. 检查论文是否已正确解析

### Q: 如何提高提取质量？

1. 使用更强大的模型（如gpt-4o）
2. 增大CHUNK_SIZE以保留更多上下文
3. 降低TEMPERATURE以减少随机性
4. 优化prompt模板（在 `prompts/prompt.md`）

### Q: 批量提取太慢？

1. 使用更快的模型（如Qwen-7B）
2. 减小CHUNK_SIZE
3. 考虑并发处理（需要代码修改）

### Q: 数据库导入报错？

1. 检查JSON文件格式是否正确
2. 确认dataid字段存在且唯一
3. 查看数据库日志了解详情

---

## 获取帮助

- 查看系统状态：`python menu.py` → 选项11
- 查看提取日志：`python menu.py` → 选项12
- 查看使用指南：`python menu.py` → 选项10
