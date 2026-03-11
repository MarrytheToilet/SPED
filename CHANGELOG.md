# 项目更新日志

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
