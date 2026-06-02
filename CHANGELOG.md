# 项目更新日志

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
- 菜单新增「启动网页」入口（`menu.py` 选项 11）。

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
- **多智能体 schema 设计**（`src/schema/`）：proposer_a/b/c 提议 → consolidator 合并 → critic 定稿，各角色可配不同模型家族（`AGENT_<ROLE>_*`），默认全部 DeepSeek。
- **逐字段原文证据**：提取输出 `{value, evidence, evidence_verified}`，自动核验。
- **图/表派生字段**：图注/表标题进入设计与抽取上下文，`SchemaField.from_figure` 标记。
- **自适应字段数**：默认 20–80；推理模型给足 `LLM_MAX_OUTPUT_TOKENS=65536`。
- **极简配置**：`.env` 仅需 `LLM_MODEL / LLM_API_BASE / LLM_API_KEY`。

### 🧰 文档与目录
- 重写 `README.md`、`docs/ARCHITECTURE.md`；删除过时文档。
- `data/processed/extracted/` 存提取结果，`data_schema/generated/` 存自动 schema。

---

## [v3.1.5] - 2026-03-11

### 📚 文档整理

**大幅精简文档结构**
- **删除冗余文档**: 11个临时/重复文档
- **合并核心文档**: 4个bugfix文档合并为1个
- **保留核心文档**: 只保留6个核心文档
- **精简率**: 65%（17个→6个）

**保留的核心文档**：
1. `README.md` - 系统完整介绍
2. `CHANGELOG.md` - 版本更新历史
3. `PROJECT_STRUCTURE.md` - 项目结构
4. `docs/README.md` - 文档索引
5. `docs/USAGE_GUIDE.md` - 用户操作手册 ⭐
6. `docs/BUGFIX_HISTORY.md` - 历史问题记录 ⭐

**详细说明**: `docs/CLEANUP_DONE.md`

---

## [v3.1.4] - 2026-03-11

### 🔧 Prompt改进

**修复数据字段中的图片引用问题**
- **问题**: 所有数据字段都包含图片路径，如`"摩擦系数": "0.16 (Figure 3d: images/xxx.jpg)"`
- **原因**: Prompt规则不明确，导致LLM在所有字段中添加图片引用
- **修复**: `prompts/prompt.md`
  - 明确区分数据字段（只填数值）和图片字段（填路径）
  - 更新图片提取规则、黄金规则、JSON示例
  - 新增特别提醒第4条
- **结果**: 
  - 数据字段: `"摩擦系数": "0.16 (Figure 3d: images/xxx.jpg)"` → `"摩擦系数": "0.16"` ✅
  - 图片字段: `"计算建模模拟结构图": "images/xxx.jpg"` 保持不变 ✅
- **建议**: 重新提取已有数据以获得纯净数值

**详细文档**: `docs/BUGFIX_IMAGE_REFERENCE.md`

---

## [v3.1.3] - 2026-03-11

### 🐛 Bug修复

**修复Excel导出重复问题**
- **问题1**: Sheet名重复（如Sheet1_Sheet1_基本信息表）
- **问题2**: 字段重复（来源文件和论文ID出现两次）
- **原因**: 
  - Sheet名: 代码在已包含Sheet前缀的table_name前又加了sheet_name
  - 字段重复: 代码额外添加了schema中已有的字段
- **修复**: `src/database/json_to_excel.py`
  - 行154: 移除重复的Sheet前缀
  - 行189-194: 移除额外添加的字段
- **结果**: 
  - Sheet名: Sheet1_Sheet1_基本信息表 → Sheet1_基本信息表 ✅
  - 字段数: 9个（含重复） → 7个（无重复） ✅

---

## [v3.1.2] - 2026-03-10

### 🎉 新增功能

**DOI自动提取工具**
- **问题**: DOI存在于MinerU的JSON文件中，但不在Markdown中
- **解决**: 创建`scripts/add_doi_to_md.py`脚本
- **功能**: 
  - 从`layout.json`/`content_list.json`提取DOI
  - 自动添加到`full.md`开头
  - 支持批量处理
- **结果**: 成功为53/97个论文添加DOI

**使用方法**:
```bash
python3 scripts/add_doi_to_md.py        # 处理所有批次
python3 scripts/add_doi_to_md.py batch_1  # 处理单个批次
```

---

## [v3.1.1] - 2026-03-10

### 🐛 Bug修复

**修复记录计数显示问题**
- **问题**: 单条记录提取显示"0 条记录"
- **原因**: 单条记录格式缺少count字段
- **修复**: 
  - `src/agents/llm_agent.py`: 确保单条记录返回时添加count=1
  - `src/extractors/extractor.py`: 正确处理count为None的情况
- **影响**: 单条记录现在显示"1 条记录"而不是"0 条记录"

---

## [v3.1] - 2026-03-10

### 🎉 Prompt系统改进

#### ✨ 新增
- **DOI提取增强**: 详细说明位置、格式、示例
- **图片路径提取**: 三步法、保留完整路径（images/hash.jpg）
- **Schema示例**: 为所有12张表添加完整示例

#### 📝 文档
- `docs/EXTRACTION_RULES.md` - 提取规则精简说明
- `prompts/prompt.md` - 改进的prompt v3.1

#### 🗑️ 清理
- 删除冗余prompt备份文件
- 删除临时改进说明文档
- 精简文档结构

---

## [v2.0] - 2026-03-10

### 🎉 PDF处理系统全面升级

#### ✨ 新增
- **核心代码**
  - `src/pdfs/pdf_manager.py` - PDF状态管理器（SQLite）
  - `scripts/pdf_manager.py` - 新版PDF处理工具
  
- **功能**
  - 智能去重（MD5哈希）
  - 一键自动化（auto --wait）
  - 状态追踪（SQLite数据库）
  - 待处理列表（list-pending）
  - 统计信息（stats）

- **文档**
  - `PDF_GUIDE.md` - PDF快速参考
  - `docs/PDF_GUIDE.md` - 完整使用指南
  - `PDF_UPGRADE_SUMMARY.md` - 升级总结

#### 🔄 修改
- **menu.py**
  - 更新PDF菜单（智能版选项）
  - 新增8个函数支持新工具
  - 保留旧版工具兼容
  
- **PROJECT_STRUCTURE.md**
  - 更新目录结构说明
  - 反映新的文件组织

#### 🗑️ 删除
- **冗余文档（14个）**
  - PDF相关临时文档（7个）
  - 历史改进文档（7个）
  
- **多余脚本（2个）**
  - import_json.py（功能已整合）
  - check_null_quality.py（临时脚本）

#### ✅ 改进
- 告别CSV手动管理
- 无需记录batch_id
- 目录结构更清晰
- 支持断点续传
- 文档精简易读

---

## 使用方法

### 处理新PDF
```bash
python scripts/pdf_manager.py auto --wait
```

### 查看状态
```bash
python scripts/pdf_manager.py stats
```

### 使用菜单
```bash
python menu.py  # P → 1 → y
```

---

## 兼容性

- ✅ 完全向后兼容
- ✅ 旧工具仍可用
- ✅ 旧数据完整保留

---

**升级者**: GitHub Copilot  
**测试**: ✅ 基础功能已验证
