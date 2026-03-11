# 用户操作手册

> 人工关节材料数据提取系统 - 常用操作指南

---

## 📋 完整工作流程

### 1. 解析PDF
```bash
python3 scripts/parse.py
# 输出: data/processed/parsed/output/batch_X/论文名/full.md
```

### 2. 添加DOI（推荐）
```bash
python3 scripts/add_doi_to_md.py
# 提高DOI提取成功率
```

### 3. 数据提取
```bash
python3 scripts/extract.py
# 输出: data/processed/extracted/论文名.json
```

### 4. 导出Excel
```bash
python3 -c "from src.database.json_to_excel import export_json_to_excel; from pathlib import Path; export_json_to_excel(Path('data/exports'))"
# 输出: data/exports/人工关节数据_YYYYMMDD_HHMMSS.xlsx
```

---

## 🔧 常用命令

### 查看状态
```bash
# 已解析论文数
ls -1d data/processed/parsed/output/batch_*/*/ | wc -l

# 已提取数据数
ls -1 data/processed/extracted/*.json | wc -l

# 导出的Excel
ls -lh data/exports/*.xlsx
```

### 重新处理
```bash
# 重新提取
rm data/processed/extracted/论文名.json
python3 scripts/extract.py

# 重新导出Excel
python3 -c "from src.database.json_to_excel import export_json_to_excel; from pathlib import Path; export_json_to_excel(Path('data/exports'))"
```

---

## ❓ 常见问题

### Q1: DOI提取失败？
```bash
# 运行DOI添加工具
python3 scripts/add_doi_to_md.py

# 验证
head -5 data/processed/parsed/output/batch_1/论文名/full.md
# 应看到: **DOI**: 10.xxxx/xxxxx

# 重新提取
python3 scripts/extract.py
```

### Q2: 数据字段包含图片引用？
系统已在v3.1.4修复，重新提取即可获得纯净数据。

### Q3: Excel Sheet名或字段重复？
系统已在v3.1.3修复，重新导出即可。

### Q4: API调用失败？
```bash
# 检查API密钥
grep "API_KEY" settings.py

# 查看日志
tail -100 logs/extract.log

# 尝试其他模型（编辑settings.py）
```

---

## 📖 更多信息

- 系统介绍: [../README.md](../README.md)
- 版本历史: [../CHANGELOG.md](../CHANGELOG.md)
- 项目结构: [../PROJECT_STRUCTURE.md](../PROJECT_STRUCTURE.md)

---

**最后更新**: 2026-03-11
