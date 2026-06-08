# SPED - 科研论文结构化数据提取系统

SPED 用来把一批领域 PDF 论文转换成可导出的结构化数据。核心流程是：

1. PDF 通过 MinerU 解析成 Markdown。
2. 多个 schema agent 阅读样本论文，各自提出 schema。
3. merger/reviewer 合并并审阅 schema。
4. 多个 extractor 按 schema 提取全文数据。
5. merger/reviewer 合并和审阅提取结果。
6. 在网页中查看 evidence，或导出 CSV/JSON。

当前默认主题 collection 是 `人工关节材料摩擦学`，但目录结构和 schema 逻辑支持按主题扩展。

---

## 1. 环境准备

建议使用已有 conda 环境或 Python 3.10+ 环境：

```bash
pip install -r requirements.txt
```

复制并填写本地配置：

```bash
cp .env.example .env
```

最少需要配置：

```ini
LLM_MODEL=deepseek-v4-flash
LLM_API_BASE=https://api.deepseek.com/v1
LLM_API_KEY=sk-...

MINERU_TOKEN=...
DEFAULT_COLLECTION=人工关节材料摩擦学
WEB_PORT=8000
```

不要提交 `.env`。仓库已经通过 `.gitignore` 忽略本地密钥、PDF、解析结果、提取结果、SQLite 状态库和日志。

---

## 2. 推荐入口：`menu.py`

启动交互式菜单：

```bash
python menu.py
```

菜单是日常使用的主入口，包含：

- 上传 PDF 到 MinerU
- 查询批次状态
- 下载解析结果
- 查看 agent 端点和运行配置
- 自动设计 schema
- 查看已有 schema
- 单篇或批量提取
- 导出提取数据
- 启动 Web 界面
- 查看数据目录概览

推荐运行顺序：

1. 把 PDF 放入：
   ```text
   data/collections/<collection>/pdfs/
   ```
2. 在菜单中选择 `1. 上传PDF到MinerU`。
3. 上传后选择 `2. 查询批次状态`。
4. 解析完成后选择 `3. 下载解析结果`。
5. 选择 `6. 自动设计schema（多agent）`，生成 schema。
6. 选择 `9. 用schema批量提取全部`。
7. 选择 `10. 导出提取数据`，导出 CSV 或 JSON。
8. 需要人工查看 evidence 时，选择 `12. 启动网页`。

### WSL 下访问网页

如果在 WSL 里运行，`menu.py` 会默认监听 `0.0.0.0`，并优先提示 WSL IP，例如：

```text
http://172.x.x.x:8000
```

在 Windows 浏览器中优先打开菜单提示的 WSL IP 地址。某些 WSL 环境下 `http://localhost:8000` 会被 Windows 重置连接，不一定可用。

---

## 3. Web 界面

也可以直接启动 Web：

```bash
python -m uvicorn webapp.app:app --host 0.0.0.0 --port 8000
```

如果只想在 Linux/WSL 内部访问，也可以绑定本机：

```bash
python -m uvicorn webapp.app:app --host 127.0.0.1 --port 8000
```

Web 页面包含以下板块：

- `解析 PDF`：选择 PDF，提交 MinerU 解析任务，查看处理状态。
- `Schema`：自动设计 schema，也可以上传、修改、克隆或删除 schema。
- `提取数据`：选择 schema 和论文，启动批量提取任务。
- `数据表`：查看提取结果，悬浮单元格查看 evidence。
- `设置`：修改 collection、并发数、LLM/MinerU 端点和 agent 角色。
- `任务`：查看后台任务进度、日志和状态。

导出接口：

```text
/api/data/export?slug=<schema_slug>&collection=<collection>&fmt=csv
/api/data/export?slug=<schema_slug>&collection=<collection>&fmt=json
```

CSV 只导出字段值，适合 Excel/表格分析。JSON 保留完整 `{value, evidence, verified}`。

---

## 4. 命令行脚本

不使用菜单时，也可以直接调用脚本。

### PDF 处理

```bash
python scripts/pdf.py upload --collection 人工关节材料摩擦学
python scripts/pdf.py status
python scripts/pdf.py download <batch_id> --collection 人工关节材料摩擦学
python scripts/pdf.py stats
```

### Schema 自动发现

```bash
python scripts/schema_pipeline.py design \
  --collection 人工关节材料摩擦学 \
  --domain 人工关节材料摩擦学 \
  --samples 16 \
  --min-fields 25 \
  --max-fields 70
```

查看 schema：

```bash
python scripts/schema_pipeline.py list --collection 人工关节材料摩擦学
```

### 数据提取

单篇：

```bash
python scripts/schema_pipeline.py extract \
  --collection 人工关节材料摩擦学 \
  --slug 人工关节摩擦磨损_clean_v1 \
  --paper <paper_id>
```

全部：

```bash
python scripts/schema_pipeline.py extract \
  --collection 人工关节材料摩擦学 \
  --slug 人工关节摩擦磨损_clean_v1 \
  --all
```

长时间全量提取推荐用带锁的脚本，避免重复启动同一 schema：

```bash
EXTRACT_CONCURRENCY=4 python scripts/run_full_extract.py \
  --collection 人工关节材料摩擦学 \
  --slug 人工关节摩擦磨损_clean_v1
```

---

## 5. 数据目录

当前数据按 collection 组织：

```text
data/
├── collections/
│   └── <collection>/
│       ├── pdfs/                 # 原始 PDF
│       ├── parsed/               # MinerU 解析结果，包含 full.md
│       ├── schemas/              # schema JSON
│       ├── extracted/            # 按 schema_slug 存放提取结果
│       └── exports/              # 菜单导出的 CSV/JSON
└── state/
    ├── pdf_state.db              # PDF/解析/提取状态库
    ├── backups/                  # 状态库迁移备份
    └── jobs/                     # 长任务 lock 文件
```

这些数据默认不提交到 Git。代码、配置样例、文档和测试才应该进入仓库。

---

## 6. 多 agent 逻辑

### Schema 自动发现

默认：

```ini
SCHEMA_AGENT_ROLES=schema_agent_a,schema_agent_b,schema_agent_c
SCHEMA_MERGER_ROLE=schema_merger
SCHEMA_REVIEWER_ROLE=schema_reviewer
```

流程：

1. 多个 schema agent 阅读同一批样本论文。
2. 每个 agent 独立提出完整 schema。
3. `schema_merger` 合并同义字段、单位、枚举和描述。
4. `schema_reviewer` 检查字段是否可抽取、是否过细/过粗、输出格式是否明确。

### 提取阶段

默认：

```ini
EXTRACTOR_ROLES=extractor_a,extractor_b
EXTRACT_MERGER_ROLE=extract_merger
EXTRACT_REVIEWER_ROLE=extract_reviewer
EXTRACT_REVIEW_ENABLED=true
```

流程：

1. 多个 extractor 独立按同一个 schema 抽取同一篇论文。
2. `extract_merger` 合并候选记录，处理冲突。
3. `extract_reviewer` 对 value/evidence 做审阅，不支持的值会置空或删除。
4. 输出 JSON 保存到：
   ```text
   data/collections/<collection>/extracted/<schema_slug>/<paper_id>.json
   ```

每个字段格式为：

```json
{
  "field_name": {
    "value": "...",
    "evidence": "论文中的短证据",
    "evidence_verified": true
  }
}
```

---

## 7. 常见问题

### Windows 浏览器打不开 WSL 里的 `localhost:8000`

这通常是 WSL localhost 自动转发异常。解决方式：

1. Web 监听 `0.0.0.0`。
2. 在 WSL 中查看 IP：
   ```bash
   hostname -I
   ```
3. 在 Windows 浏览器打开：
   ```text
   http://<WSL_IP>:8000
   ```

本项目的 `menu.py` 会自动检测 WSL，并优先提示这个地址。

### 导出 CSV 出现 Internal Server Error

旧版本曾因中文 schema slug 写入 `Content-Disposition` header 触发编码错误。现在已使用 `filename*=` UTF-8 编码，中文文件名可以正常下载。

### 端口被占用

`menu.py` 会从 `WEB_PORT` 开始查找可用端口，并提示建议端口。也可以手动输入端口。

### 数据很多，是否需要提交到 Git

不需要。`data/**`、`logs/**`、`.env`、SQLite 数据库和缓存都已忽略。只提交代码、文档、测试和 `.env.example`。

---

## 8. 测试

运行测试：

```bash
python -m pytest tests -q
```

当前测试覆盖：

- schema 扁平模型与校验
- 多 agent 提取合并逻辑
- 后台任务去重和状态管理
- Web/service 层关键流程

---

## 9. 当前人工关节数据集示例

当前已整理的 schema：

```text
人工关节摩擦磨损_clean_v1
```

它聚焦：

- 人工关节材料
- 组件类型
- 摩擦副
- 表面处理/涂层
- 润滑介质
- 载荷、速度、循环数
- 摩擦系数
- 磨损率/磨损体积/线性磨损
- 表面损伤、磨屑和取出物分析
- 模拟结果

一次全量验证结果：

```text
total papers: 1371
success: 1365
skipped: 6
records: 5310
```
