# 项目更新日志

> 早于 v4.0 的历史（v2.0–v3.1.5，12 表硬编码 + 分块提取时代）随 v4.0 重构一起废弃，
> 不再记录；当前架构自 v4.0.0 起。

## [v4.2.0] - 完整流程核对 + 并行提取 + Schema 上传

### ✨ 新增
- **并行提取**：`run_extract_job` 改用线程池并发（每 worker 独立 LLM 客户端与统计），整库 1384 篇提取从串行改并行。新增 `EXTRACT_CONCURRENCY`（默认 8，范围 1–32），可在网页「设置 → 性能/限额」配置并写入 `.env`。
- **直接上传 Schema**：设计页新增「方式 B」，可上传符合规范的 schema JSON（`POST /api/schema/upload`）；`slugify` 防路径穿越，语义不同时需 `overwrite=True`。

### 🐛 修复
- **随机采样失效**：设计 schema 的「随机抽取论文」此前被 `select_sample` 的尺寸分层覆盖；改为 `random.sample` 取 k 篇并以 k 作 sample_size，确保真正随机。
- **`select_sample` 在 size=1 时除零**：增加守护，返回中位长度论文。
- **串行提取卡死**：单个慢 LLM 调用会阻塞全部；并行化 + `LLM_CALL_TIMEOUT` 默认 1200→600s。

### ✅ 核对
- design→extract→data 全链路验证可用；证据核验（截断+NFKC+子串/窗口匹配→`evidence_verified`）与单篇多材料样本展平（`records[]`→多行 `_paper_id`）实测正确。

## [v4.1.0] - Web 界面 + 解析稳健性 + 网页设置

### ✨ 新增
- **FastAPI 单页 Web 界面**（`webapp/`）：解析 PDF / 设计 schema / 提取 / 查看数据（悬浮看证据来源）/ 任务 / 设置 六个页签，后台任务实时进度。
- **网页 API 设置页**：在线配置 MinerU(token/base) 与各 LLM 角色 model/base/key，写入 `.env` 并热重载（`settings.reload_config()`），API Key 脱敏；有任务运行时禁止修改。
- **全局进度横幅**：顶部跨页签显示当前活动任务进度。
- **浅色（白色系）主题**。
- 菜单新增「启动网页」入口。

### 🛡️ 稳健性
- **PDF 体积上限**：`MAX_PDF_SIZE_MB`（默认 20MB），超限标记 `too_large` 且拒绝上传。
- **MinerU 限速**：`MINERU_UPLOAD_RATE_PER_MIN`（默认 50），解析任务按滚动 60s 窗口限速上传，`upload_batch` 429-aware 退避（尊重 `Retry-After`），修复批量上传被 429 刷屏的问题。
- **配置快照**：`PDFProcessor` 构造时快照 MinerU 配置，设置热重载不打断进行中的解析。
- **安全**：`.env` 从 git 取消跟踪并加入 `.gitignore`。

## [v4.0.0] - 重构：多智能体自动 schema + 内联证据

### 🔥 重大重构
- **移除分块再合并**：现代长上下文 LLM 整篇处理，删除全部 chunk 逻辑。
- **移除硬编码多表/旧数据库导入**：改为 LLM 自动设计**单一大表** schema，领域可迁移。
- **清理历史数据与代码**：删除旧 db、旧提取 JSON、旧 agents/workflow/多 provider 客户端等；仅保留已解析 markdown 与图片。

### ✨ 新增
- **多智能体 schema 设计**（`src/schema/`）：schema_agent_a/b/c 各自读同一批样本产出完整 schema → schema_merger 合并 → schema_reviewer 定稿，各角色可配不同模型家族（`AGENT_<ROLE>_*`），默认全部 DeepSeek。
- **逐字段原文证据**：提取输出 `{value, evidence, evidence_verified}`，自动核验。
- **图/表派生字段**：图注/表标题进入设计与抽取上下文，`SchemaField.from_figure` 标记。
- **自适应字段数**：默认 20–80；推理模型给足 `LLM_MAX_OUTPUT_TOKENS=65536`。
- **极简配置**：`.env` 仅需 `LLM_MODEL / LLM_API_BASE / LLM_API_KEY`。

### 🧰 文档与目录
- 重写 `README.md`、`docs/ARCHITECTURE.md`；删除过时文档。
- 数据按 collection 组织：`data/collections/<collection>/{pdfs,parsed,schemas,extracted}`，状态库在 `data/state/`。
