# SPED · 科研论文结构化数据提取系统

SPED 把一批领域 PDF 论文转换成可导出的结构化数据表。核心流程：

```
PDF ──MinerU──▶ Markdown ──多agent设计──▶ schema ──多agent提取──▶ 带原文证据的记录 ──▶ CSV / JSON
      解析              (schema_a/b/c→合并→审阅)     (extractor_a/b→合并→审阅)          导出
```

每个提取值都附带一段**原文证据引文**并自动核验，可在网页里悬浮查看来源，或导出为 CSV/JSON。
数据按「主题 collection」组织，默认主题是 `人工关节材料摩擦学`，可扩展到任意领域。

---

## 目录

- [1. 环境与安装](#1-环境与安装)
- [2. 配置 .env](#2-配置-env)
- [3. 三种使用方式](#3-三种使用方式)
  - [A. 交互菜单 `menu.py`（推荐入门）](#a-交互菜单-menupy推荐入门)
  - [B. Web 界面（推荐日常）](#b-web-界面推荐日常)
  - [C. 命令行脚本（自动化 / 批处理）](#c-命令行脚本自动化--批处理)
- [4. 完整工作流](#4-完整工作流)
- [5. 部署](#5-部署)
- [6. 数据目录](#6-数据目录)
- [7. 多 agent 与模型配置](#7-多-agent-与模型配置)
- [8. Web API 一览](#8-web-api-一览)
- [9. 测试](#9-测试)
- [10. 常见问题](#10-常见问题)

---

## 1. 环境与安装

要求 **Python 3.10+**（推荐用现成的 conda 环境）。

```bash
git clone https://github.com/MarrytheToilet/SPED.git
cd SPED
pip install -r requirements.txt
```

外部依赖：
- **MinerU**：把 PDF 解析成 Markdown，需要 API token（https://mineru.net）。
- **一个 OpenAI 兼容的 LLM 端点**：DeepSeek / Qwen / GLM / Kimi / OpenAI / SiliconFlow 等均可。

---

## 2. 配置 .env

复制模板并填写：

```bash
cp .env.example .env
```

最少需要这几项就能跑通：

```ini
# LLM（OpenAI 兼容端点）
LLM_MODEL=deepseek-v4-flash
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=sk-...

# PDF 解析
MINERU_TOKEN=...

# 默认主题与网页端口
DEFAULT_COLLECTION=人工关节材料摩擦学
WEB_PORT=8000
```

常用可选项（都有默认值，详见 `.env.example`）：

| 变量 | 默认 | 说明 |
|---|---|---|
| `EXTRACT_CONCURRENCY` | 8 | 提取阶段同时处理多少篇论文（1–32） |
| `LLM_MAX_INFLIGHT` | 8 | 进程内 LLM 并发上限，务必 ≤ 供应商限额 |
| `MAX_PDF_SIZE_MB` | 20 | 超过体积的 PDF 拒绝上传（MinerU 大文件易超时） |
| `MINERU_UPLOAD_RATE_PER_MIN` | 50 | MinerU 上传限速（文件/分钟） |
| `SCHEMA_AGENT_ROLES` | schema_agent_a,b,c | 设计 schema 的多个 agent 角色 |
| `EXTRACTOR_ROLES` | extractor_a,b | 提取的多个 extractor 角色 |

> `.env` 已被 `.gitignore` 忽略，不要提交密钥。

---

## 3. 三种使用方式

三种方式操作的是**同一份数据**（`data/` 下），可以混用：例如命令行批量提取、网页里查看证据。

### A. 交互菜单 `menu.py`（推荐入门）

```bash
python menu.py
```

菜单把常用操作串成编号选项，底层调用的就是下面的脚本 / Web：

```
【PDF 处理】
  1. 上传 PDF 到 MinerU     2. 查询批次状态
  3. 下载解析结果           4. PDF 处理统计
【Schema 设计 + 数据提取】
  5. 查看各 agent 端点/配置  6. 自动设计 schema（多agent）
  7. 查看已生成 schema       8. 用 schema 提取单篇
  9. 用 schema 批量提取全部  10. 导出提取数据
  11. 列出已解析论文
【Web】
  12. 启动网页（解析/设计/提取/数据/设置一站式）
【数据 / 配置】
  13. 数据目录概览           14. 运行配置摘要
```

### B. Web 界面（推荐日常）

从菜单选 `12`，或直接启动：

```bash
# 仅本机访问
python -m uvicorn webapp.app:app --host 127.0.0.1 --port 8000
# 局域网 / 远程访问（配合防火墙）
python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
```

浏览器打开 `http://<host>:8000`。页面板块：

- **解析 PDF**：选文件、提交 MinerU 解析、看进度
- **Schema**：自动设计，或上传 / 修改 / 克隆 / 删除 schema
- **提取数据**：选 schema 和论文，启动批量提取任务
- **数据表**：查看结果，悬浮单元格看原文证据
- **设置**：在线改 collection、并发数、LLM/MinerU 端点和 agent 角色（写回 `.env` 并热重载）
- **任务**：后台任务的进度、日志、取消

> ⚠️ 网页用**进程内**的任务管理器和 SQLite 状态库，因此必须**单 worker**运行（不要加 `--workers >1`，否则任务状态和进度不共享）。见[部署](#5-部署)。

### C. 命令行脚本（自动化 / 批处理）

**PDF 处理** `scripts/pdf.py`：

```bash
python scripts/pdf.py upload --collection 人工关节材料摩擦学 [--dir <PDF目录>]
python scripts/pdf.py status [<batch_id>]          # 不带 id 查全部批次
python scripts/pdf.py download <batch_id> --collection 人工关节材料摩擦学
python scripts/pdf.py stats
```

**Schema 设计 / 列出 / 提取** `scripts/schema_pipeline.py`：

```bash
# 设计 schema（读若干已解析论文，自动产出单表字段）
python scripts/schema_pipeline.py design \
  --collection 人工关节材料摩擦学 \
  --domain 人工关节材料摩擦学 \
  --desc "材料成分/几何/性能/摩擦磨损参数与结果/计算模拟" \
  --samples 16 --min-fields 25 --max-fields 70

# 列出已生成 schema
python scripts/schema_pipeline.py list --collection 人工关节材料摩擦学

# 提取：单篇
python scripts/schema_pipeline.py extract --collection 人工关节材料摩擦学 \
  --slug <schema_slug> --paper <paper_id>
# 提取：全部已解析论文
python scripts/schema_pipeline.py extract --collection 人工关节材料摩擦学 \
  --slug <schema_slug> --all
```

**带文件锁的全量提取** `scripts/run_full_extract.py`（长任务推荐，避免同一 schema 被重复启动）：

```bash
EXTRACT_CONCURRENCY=4 python scripts/run_full_extract.py \
  --collection 人工关节材料摩擦学 --slug <schema_slug>
```

**导出**（命令行没有单独的导出脚本，走 Web API 或菜单第 10 项）：

```bash
curl "http://127.0.0.1:8000/api/data/export?slug=<schema_slug>&collection=<collection>&fmt=csv" -o data.csv
curl "http://127.0.0.1:8000/api/data/export?slug=<schema_slug>&collection=<collection>&fmt=json" -o data.json
```

CSV 只导字段值（Excel 友好，带 UTF-8 BOM）；JSON 保留完整 `{value, evidence, evidence_verified}`。

---

## 4. 完整工作流

```
1) 把 PDF 放进 data/collections/<collection>/pdfs/
2) 上传解析     menu 1  |  scripts/pdf.py upload      |  Web「解析 PDF」
3) 查询/下载    menu 2,3|  scripts/pdf.py status/download
4) 设计 schema  menu 6  |  schema_pipeline.py design  |  Web「Schema」
5) 批量提取     menu 9  |  schema_pipeline.py extract --all  |  Web「提取数据」
6) 查看证据                                              Web「数据表」（悬浮看来源）
7) 导出         menu 10 |  /api/data/export           |  Web 导出按钮
```

三段产物（parsed / schemas / extracted）都落盘、彼此解耦，任一段可单独重跑，不影响其它段。

---

## 5. 部署

### 本机 / WSL

WSL 里推荐监听 `0.0.0.0`，然后在 Windows 浏览器用 WSL 的 IP 访问（`localhost` 转发有时会被重置）：

```bash
hostname -I                       # 取 WSL IP，例如 172.x.x.x
python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
# Windows 浏览器打开 http://172.x.x.x:8000
```

`menu.py` 的选项 12 会自动检测 WSL 并提示可用地址与可用端口。

### 远程服务器

方式一，SSH 端口转发（最省心，不暴露端口）：

```bash
# 服务器上（仅监听本机）
python -m uvicorn webapp.app:app --host 127.0.0.1 --port 8000
# 自己电脑上
ssh -L 8000:127.0.0.1:8000 <user>@<server>
# 然后本机浏览器打开 http://127.0.0.1:8000
```

方式二，直接对外（注意防火墙 / 安全组放行端口）：

```bash
python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
```

### 后台常驻

```bash
# 简单方式
nohup python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000 > logs/web.log 2>&1 &
# 或用 tmux / screen 保活
```

systemd 服务示例（`/etc/systemd/system/sped.service`）：

```ini
[Unit]
Description=SPED web
After=network.target

[Service]
WorkingDirectory=/path/to/SPED
ExecStart=/path/to/python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
Restart=on-failure
User=youruser

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now sped
```

### 部署注意事项

- **必须单进程（单 worker）**：任务管理器（`webapp/jobs.py::JOBS`）是进程内单例，状态存在内存；SQLite 状态库也不适合多进程写。**不要**用 `--workers >1` 或 gunicorn 多 worker，否则进度/任务会错乱。要扩并发请调 `EXTRACT_CONCURRENCY` 和 `LLM_MAX_INFLIGHT`，而不是加 worker。
- **并发匹配 API 限额**：`LLM_MAX_INFLIGHT` 要 ≤ LLM 供应商的并发上限，`MINERU_UPLOAD_RATE_PER_MIN` 要 ≤ MinerU 限速，否则会 429。
- **长任务**：整库提取用 `scripts/run_full_extract.py`（带文件锁），或网页任务页；中断后重跑会跳过已成功的论文。
- **反向代理**：如需 Nginx，转发到 `127.0.0.1:8000` 即可，注意放开较长的读超时（提取任务耗时）。

---

## 6. 数据目录

```
data/
├── collections/
│   └── <collection>/
│       ├── pdfs/                # 原始 PDF
│       ├── parsed/<paper_id>/   # MinerU 解析结果，含 full.md 与 images/
│       ├── schemas/             # schema JSON（+ archive/ 存归档）
│       ├── extracted/<slug>/    # 按 schema_slug 存的提取结果 JSON
│       └── exports/             # 菜单导出的 CSV/JSON
└── state/
    ├── pdf_state.db             # PDF / 解析 / 提取状态库（SQLite）
    ├── backups/                 # 状态库迁移备份
    └── jobs/                    # 长任务 lock 文件
```

`data/**`、`logs/**`、`.env`、SQLite、缓存都在 `.gitignore` 里，不进仓库。

---

## 7. 多 agent 与模型配置

所有角色都走 OpenAI 兼容协议，默认全部回退到基础 `LLM_*` 端点；可用
`AGENT_<ROLE>_MODEL / _API_BASE / _API_KEY` 单独覆盖某个角色，实现「不同模型家族分工协作」。

```ini
# 设计 schema：多个 agent 各自读同一批样本 → 合并 → 审阅
SCHEMA_AGENT_ROLES=schema_agent_a,schema_agent_b,schema_agent_c
SCHEMA_MERGER_ROLE=schema_merger
SCHEMA_REVIEWER_ROLE=schema_reviewer

# 提取：多个 extractor 独立抽取 → 合并 → 审阅
EXTRACTOR_ROLES=extractor_a,extractor_b
EXTRACT_MERGER_ROLE=extract_merger
EXTRACT_REVIEWER_ROLE=extract_reviewer
EXTRACT_REVIEW_ENABLED=true

# 例：给某个 schema agent 换成 Qwen
# AGENT_SCHEMA_AGENT_B_MODEL=qwen-max
# AGENT_SCHEMA_AGENT_B_API_BASE=https://dashscope.aliyuncs.com/compatible-mode/v1
# AGENT_SCHEMA_AGENT_B_API_KEY=sk-...
```

菜单第 5 项、网页「设置」页可查看每个角色实际生效的端点。架构细节见 `docs/ARCHITECTURE.md`。

---

## 8. Web API 一览

| 方法 | 路径 | 作用 |
|---|---|---|
| GET | `/api/collections` | 列出主题及 PDF 数 |
| GET/POST | `/api/pdfs` · `/api/pdfs/delete` | PDF 总览 / 清理 |
| POST | `/api/parse` | 提交解析任务 |
| GET | `/api/parsed` | 已解析论文 |
| POST | `/api/schema/design` | 多agent 设计 schema |
| GET/PUT/DELETE | `/api/schemas` · `/api/schemas/{slug}` | 列出 / 改 / 删 schema |
| POST | `/api/schemas/{slug}/clone` · `/api/schema/upload` | 克隆 / 上传 schema |
| POST | `/api/extract` | 提交提取任务 |
| GET | `/api/data` · `/api/data/export` | 查看数据 / 导出 CSV·JSON |
| GET/POST | `/api/jobs` · `/api/jobs/{id}` · `/api/jobs/{id}/cancel` | 任务进度 / 取消 |
| GET/POST | `/api/settings` | 读取 / 更新运行配置 |

---

## 9. 测试

```bash
python -m pytest tests -q
```

覆盖：schema 扁平模型与校验、多 agent 提取合并、后台任务去重与状态管理。

---

## 10. 常见问题

**Windows 浏览器打不开 WSL 里的 `localhost:8000`** — WSL 的 localhost 转发偶发异常。用 `hostname -I` 取 WSL IP，改用 `http://<WSL_IP>:8000`；`menu.py` 会自动提示该地址。

**端口被占用** — `menu.py` 会从 `WEB_PORT` 起找可用端口并提示；也可手动改 `--port`。

**提取任务大量失败、报 429 / 限速** — 调低 `LLM_MAX_INFLIGHT` 和 `EXTRACT_CONCURRENCY`；确认没有用多 worker 启动。

**`'GeneratedSchema' object has no attribute ...'` 之类属性报错** — 代码版本不一致：`git pull` 到最新、清 `__pycache__`、重启网页服务。

**导出中文文件名乱码 / 报错** — 已用 `filename*=` UTF-8 编码，中文文件名可正常下载。

**数据要不要提交 Git** — 不需要。只提交代码、`.env.example`、文档和测试。
