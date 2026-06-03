# SPED — 科研论文结构化数据提取系统

> Scientific Paper Extraction & Discovery
> 把一批领域论文（PDF）解析为 Markdown，再由「多智能体」自动设计字段表(schema)，
> 最后整篇抽取为带**原文证据**的结构化数据。换个领域只需改一句领域简介。

---

## 它解决什么问题

传统做法需要人工为每个领域硬编码一张表（字段、单位、枚举…），换领域就推倒重来。
SPED 把这一步交给 LLM：

1. **PDF → Markdown**：用 [MinerU](https://github.com/opendatalab/MinerU) 解析 PDF，得到带图表的 `full.md`。
2. **自动设计 schema（多智能体）**：给一句领域简介 + 若干已解析论文，默认 3 个 schema agent 独立阅读同一批样本论文（摘要/引言/实验或方法部分 + 图/表标题），各自产出一份完整 schema；`schema_merger` 合并多份 schema，`schema_reviewer` 审阅字段描述、格式、单位和可抽取性后定稿。
3. **整篇提取 + 证据**：用该 schema 对每篇论文整篇抽取，输出扁平记录，**每个字段都带 `{value, evidence}`**——evidence 是论文原文中的原句/原短语（图表派生字段可用图注作证据），系统会逐条核验。

---

## 核心特性

- 🧠 **LLM 自动设计 schema**：领域可迁移，无需手工建表。字段数量自适应（默认 20–80）。
- 🤝 **多智能体协作**：提议者 / 整合者 / 评审者可分别配置为**不同家族的模型**（默认全部 DeepSeek，可按角色用环境变量替换）。
- 🧾 **逐字段原文证据**：每个值都附 evidence 并自动核验，便于人工复核与去幻觉。
- 🖼 **图/表派生字段**：图注与表标题进入设计与抽取上下文，捕捉「只在图里出现」的信息。
- 🪶 **扁平单表输出**：一篇论文可含多条记录（不同材料/不同实验条件各一行）。
- ⚙️ **极简配置**：`.env` 只需 `LLM_MODEL / LLM_API_BASE / LLM_API_KEY`。

---

## 安装

```bash
# Python 3.10+，建议 conda 环境
pip install -r requirements.txt
```

配置 `.env`（参考 `.env.example`）：

```ini
# LLM（OpenAI 兼容即可）
LLM_MODEL=deepseek-v4-flash
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=sk-xxxx

# 可选：按角色覆盖某个智能体的端点（不填则全部回退到上面的基础配置）
# AGENT_PROPOSER_B_MODEL=...
# AGENT_PROPOSER_B_API_BASE=...
# AGENT_PROPOSER_B_API_KEY=...

# Schema 自动发现阶段默认 3 个 agent 独立阅读同一批样本，各自产出完整 schema
# SCHEMA_AGENT_ROLES=schema_agent_a,schema_agent_b,schema_agent_c
# SCHEMA_MERGER_ROLE=schema_merger
# SCHEMA_REVIEWER_ROLE=schema_reviewer

# 提取阶段默认 2 个 extractor + 合并 + 审阅
# EXTRACTOR_ROLES=extractor_a,extractor_b
# EXTRACT_MERGER_ROLE=extract_merger
# EXTRACT_REVIEWER_ROLE=extract_reviewer
# EXTRACT_REVIEW_ENABLED=true

# 可选调参
# LLM_MAX_OUTPUT_TOKENS=65536   # 推理模型给足额度，避免截断
# SCHEMA_MIN_FIELDS=20
# SCHEMA_MAX_FIELDS=80
# SCHEMA_SAMPLE_SIZE=8
```

> ⚠️ 切勿把真实 API Key 提交进仓库。若曾在聊天中暴露，请尽快在服务商处轮换。

---

## 快速开始

### Web 界面（推荐）

```bash
python -m webapp.app            # 启动后访问 http://localhost:8000
# 可选: WEB_PORT=8077 python -m webapp.app
```

四个步骤一站式完成：

1. **① 解析 PDF**：从 `data/collections/<collection>/pdfs` 选取（可全选/筛选）→ 一键解析。PDF 自动归类为
   **未解析 / 处理中 / 解析成功 / 解析失败 / 超大(不可解析)**；失败的可重新解析。
   超过 `MAX_PDF_SIZE_MB`（默认 20MB）的 PDF 不可上传；上传自动限速到 50 文件/分钟，规避
   MinerU 速率限制。后台任务实时显示进度。
2. **② 设计 Schema**：两种方式——(A) 填领域名 + 引导 prompt，挑选（或随机抽取）几篇解析好的论文
   → 多 schema agent 独立设计完整 schema，再合并和审阅；(B) 直接上传符合规范的 schema JSON。
3. **③ 提取数据**：选 schema + 论文（可全选）→ 整篇并行提取（并行度可在「设置」里配 `EXTRACT_CONCURRENCY`，默认 8）。
   默认每篇论文由 `extractor_a` / `extractor_b` 独立抽取，`extract_merger` 合并，`extract_reviewer` 审阅 value/evidence。
4. **④ 查看数据**：表格展示所有记录，**悬浮单元格即可看到原文证据与来源论文**，✓ 表示证据已核验。
5. **⚙ 任务**：所有解析/设计/提取均为后台任务，顶部全局进度条 + 任务卡片实时显示进度、日志、取消。
6. **🔧 设置**：网页内配置默认 collection、MinerU(token/base)、基础 LLM、各 agent 角色端点、
   schema/extraction 角色、并发与限额，写入 `.env` 并对新任务即时生效（API Key 脱敏显示，留空表示不修改；有任务运行时禁止修改）。

> 同一时刻只允许一个解析任务，避免重复上传浪费 MinerU 额度。界面为浅色（白色系）主题。

### 交互式菜单

```bash
python menu.py
```

### 命令行

```bash
# 1) PDF → Markdown（MinerU）
python scripts/pdf.py upload  <pdf或目录>
python scripts/pdf.py download           # 解析
python scripts/pdf.py stats

# 2) 多智能体设计 schema（领域简介可在 scripts 内/交互中指定）
python scripts/schema_pipeline.py design --samples 6 --min-fields 20 --max-fields 80

# 3) 查看已生成的 schema
python scripts/schema_pipeline.py list

# 4) 用 schema 提取某篇论文
python scripts/schema_pipeline.py extract --slug <领域slug> --paper <paper_id>
```

提取结果写入 `data/collections/<collection>/extracted/<schema_slug>/<paper_id>.json`，每条记录的每个字段含 `{value, evidence}` 与证据核验统计。

---

## 流程概览

```
PDF ──MinerU──▶ data/collections/<collection>/parsed/<id>/full.md (+images)
                       │
                       ▼
        ┌──────── 多智能体 schema 设计 ────────┐
        │ schema_agent_a/b/c → 各自完整 schema 草案 │
        │ schema_merger      → 合并相近字段/描述    │
        │ schema_reviewer    → 审阅可抽取性与格式   │
        └──────────────────┬───────────────────┘
                           ▼
            data/collections/<collection>/schemas/<slug>.json
                           │
                           ▼
        extractor_a/b → merger → reviewer → {value, evidence}
                           ▼
            data/collections/<collection>/extracted/<slug>/<id>.json
```

---

## 目录结构

```
sped/
├── menu.py                  # 交互式菜单入口
├── settings.py              # 全局配置（目录、LLM、多智能体角色、字段数等）
├── .env / .env.example      # 凭据与可选调参
├── webapp/                  # ⭐ Web 界面（FastAPI）
│   ├── app.py               # REST 接口入口（python -m webapp.app）
│   ├── services.py          # 解析/设计/提取/数据查看 业务逻辑
│   ├── jobs.py              # 后台任务管理器（线程 + 进度/日志）
│   └── static/index.html    # 单页前端（四步流程 + 证据悬浮）
├── scripts/
│   ├── pdf.py               # PDF 上传/解析/下载/统计（MinerU）
│   └── schema_pipeline.py   # design / list / extract
├── src/
│   ├── pdfs/                # MinerU 解析与 PDF 状态库
│   ├── database/            # 已解析论文目录(catalog)
│   ├── schema/              # ⭐ 多智能体 schema 设计
│   │   ├── prompts.py       # 提议/整合/评审/抽取 元prompt
│   │   ├── discovery.py     # 多智能体编排
│   │   ├── sampling.py      # 采样/截断/图注抽取
│   │   ├── models.py        # GeneratedSchema / SchemaField
│   │   ├── store.py         # 生成 schema 的存取
│   │   └── _json.py         # 宽松 JSON 解析(json_repair)
│   ├── prompts/modes/       # GenericFlatMode：扁平提取 + 证据核验
│   ├── extractors/          # ExtractionService 提取服务
│   ├── llm/                 # OpenAI 兼容客户端 + 按角色工厂
│   └── utils/
├── data/
│   ├── collections/<name>/
│   │   ├── pdfs/            # 原始 PDF
│   │   ├── parsed/          # MinerU 输出(full.md/images/tables)
│   │   ├── schemas/         # collection-local schema
│   │   └── extracted/       # 按 schema_slug 存结构化提取结果
│   └── state/pdf_state.db   # 上传/解析/提取运行状态
├── docs/ARCHITECTURE.md     # 架构细节
└── tests/                   # 单元测试
```

---

## 多智能体配置

各角色默认回退到基础 `LLM_*`，可单独用 `AGENT_<ROLE>_MODEL/_API_BASE/_API_KEY` 覆盖：

| 角色 | 作用 |
|------|------|
| `schema_agent_a` / `schema_agent_b` / `schema_agent_c` | 独立阅读同一批样本论文，各自产出完整 schema |
| `schema_merger` | 合并多份 schema 草案，统一相近字段、描述、单位和提取格式 |
| `schema_reviewer` | 审阅合并后的 schema，检查可抽取性、字段格式和记录定义 |
| `extractor_a` / `extractor_b` / `extractor_c` | 多路提取角色，独立按 schema 抽取同一篇论文 |
| `extract_merger` | 可选合并角色，合并多个 extractor 的候选记录并保留 evidence |
| `extract_reviewer` | 审阅合并后的 records 与 evidence，删除或置空不被证据支持的值 |

> 想让不同角色用不同模型家族，只需为对应 `AGENT_<ROLE>_*` 配上各自的 base/key/model。

Schema 自动发现阶段默认：

```ini
SCHEMA_AGENT_ROLES=schema_agent_a,schema_agent_b,schema_agent_c
SCHEMA_MERGER_ROLE=schema_merger
SCHEMA_REVIEWER_ROLE=schema_reviewer
```

每个 schema agent 读取的是同一批样本论文上下文，优先包含摘要、引言、实验/方法部分和图表标题。

提取阶段默认：

```ini
EXTRACTOR_ROLES=extractor_a,extractor_b
EXTRACT_MERGER_ROLE=extract_merger
EXTRACT_REVIEWER_ROLE=extract_reviewer
EXTRACT_REVIEW_ENABLED=true
```

---

## 测试

```bash
python -m pytest tests/test_schema_flat.py -q
```

不依赖真实 LLM（使用按 `call_id` 返回预置 JSON 的 FakeLLM），校验：摘要截断、schema 校验、候选合并/整合、扁平提取的证据规则。

---

## 设计取舍

- **不再分块再合并**：现代长上下文 LLM 可整篇处理，旧的「分块→合并」逻辑已移除。
- **不再硬编码多表**：单一大表 + 自动 schema，迁移成本最低。
- **证据优先**：宁可 `null` 也不臆造；证据逐条核验，表格线性化导致的少量数值未命中会被如实标记。
- **图像处理**：当前以「图注/表标题文本」进入上下文（务实、零额外依赖）；完整视觉理解暂不在范围内。
