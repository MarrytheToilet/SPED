# 数据库管理使用指南

## 🎯 功能概述

数据库管理系统提供完整的数据导入、导出和管理功能。

### 主要特性
- ✅ 从JSON文件导入数据到SQLite数据库
- ✅ 批量导入extracted目录的所有提取结果
- ✅ 导出多种格式的CSV文件
- ✅ 查询、删除、统计功能
- ✅ 自动处理重复数据（更新已有记录）
- ✅ 支持中文字段名

## 🚀 快速开始

### 1. 启动数据库管理工具
```bash
python database.py
```

### 2. 查看数据库统计
选择菜单选项 `1`，查看：
- 总记录数
- 有应用部位的记录数
- 不同论文数
- 最近更新时间
- 数据库大小

### 3. 导入数据

#### 方法A：导入单个JSON文件
```bash
# 选择菜单选项 2
# 输入JSON文件路径，例如:
test_real_extraction.json
```

#### 方法B：批量导入extracted目录
```bash
# 选择菜单选项 3
# 自动导入 data/processed/extracted/ 下的所有JSON文件
```

### 4. 导出CSV

#### 导出完整数据（展平JSON）
```bash
# 选择菜单选项 4
# 输出: data/exports/full_data_flat_TIMESTAMP.csv
# 特点: JSON字段被展平为可读格式
```

#### 导出完整数据（保留JSON）
```bash
# 选择菜单选项 5
# 输出: data/exports/full_data_raw_TIMESTAMP.csv
# 特点: 保留原始JSON格式
```

#### 导出数据摘要
```bash
# 选择菜单选项 6
# 输出: data/exports/summary_TIMESTAMP.csv
# 包含: dataid, paper_id, 数据标识, 应用部位, 非空字段数, 时间戳
```

#### 导出关键字段
```bash
# 选择菜单选项 7
# 输出: data/exports/key_fields_TIMESTAMP.csv
# 只包含最重要的16个字段
```

#### 一次导出所有格式
```bash
# 选择菜单选项 8
# 自动导出上述4种格式
```

## 📊 导出文件说明

### 1. full_data_flat_TIMESTAMP.csv
**完整数据（展平JSON）**

```csv
数据id,paper_id,数据标识,应用部位,球头信息_球头基本信息,...
AJ_001,paper1,CoCrMo实验,髋关节,"材料类别: CoCrMo合金; 直径: 28 mm",...
```

- 所有30个字段
- JSON字符串被展平为 `key: value; key: value` 格式
- 适合Excel查看和分析

### 2. full_data_raw_TIMESTAMP.csv
**完整数据（保留JSON）**

```csv
数据id,paper_id,数据标识,应用部位,球头信息_球头基本信息,...
AJ_001,paper1,CoCrMo实验,髋关节,"{\"材料类别\": \"CoCrMo合金\", \"直径\": \"28 mm\"}",...
```

- 所有30个字段
- 保留原始JSON格式
- 适合程序化处理

### 3. summary_TIMESTAMP.csv
**数据摘要**

```csv
dataid,paper_id,数据标识,应用部位,非空字段数,创建时间,更新时间
AJ_001,paper1,CoCrMo实验,髋关节,15,2025-11-03 11:00:00,2025-11-03 11:00:00
```

- 每条记录一行
- 快速了解数据质量
- 适合数据清洗和统计

### 4. key_fields_TIMESTAMP.csv
**关键字段**

包含16个最重要的字段：
- 基本信息：数据id, paper_id, 数据标识, 应用部位, 文献
- 球头信息：基本信息, 成分, 物理性能
- 内衬信息：基本信息, 物理性能
- 实验：设置, 润滑液, 磨损结果（球头和内衬）, 腐蚀结果（球头和内衬）

适合快速分析主要实验数据。

## 🔍 高级功能

### 查询特定论文的数据
```bash
# 选择菜单选项 9
# 输入 paper_id，例如: b3_5_人工关节金属假体材料界面间的摩擦腐蚀行为_张鑫
# 显示该论文的所有记录
```

### 删除特定论文的数据
```bash
# 选择菜单选项 10
# 输入 paper_id
# 确认后删除该论文的所有记录
```

### 清空所有数据
```bash
# 选择菜单选项 11
# 需要输入 "DELETE ALL" 确认
# 清空数据库（保留表结构）
```

## 💻 编程接口

### Python API使用示例

#### 导入数据
```python
from src.database.db_manager import DatabaseManager

db = DatabaseManager()

# 从JSON文件导入
result = db.insert_from_json("test_extraction.json")
print(f"成功: {result['success']}, 失败: {result['failed']}")

# 单条记录导入
record = {
    "dataid": "AJ_001",
    "paper_id": "test_paper",
    "数据标识": "测试实验",
    "应用部位": "髋关节"
}
db.insert_record(record)
```

#### 查询数据
```python
# 查询所有
all_records = db.query_all(limit=10)

# 根据论文ID查询
paper_records = db.query_by_paper_id("test_paper")

# 获取统计
stats = db.get_statistics()
print(f"总记录数: {stats['total_records']}")
```

#### 导出CSV
```python
from src.database.csv_exporter import CSVExporter, export_all_formats
from pathlib import Path

# 方法1: 使用高级API
export_all_formats(Path("data/exports"))

# 方法2: 自定义导出
exporter = CSVExporter()

# 导出所有数据
exporter.export_all(Path("data/output.csv"), flatten_json=True)

# 导出特定字段
fields = ['数据id', '数据标识', '应用部位', '球头信息_球头基本信息']
exporter.export_custom_fields(Path("data/custom.csv"), fields)

# 导出特定论文
exporter.export_by_paper("paper_id", Path("data/paper.csv"))
```

## 📁 文件结构

```
sped/
├── database.py                      # 命令行工具
├── data/
│   ├── artificial_joint.db          # SQLite数据库
│   ├── exports/                     # CSV导出目录
│   │   ├── full_data_flat_*.csv
│   │   ├── full_data_raw_*.csv
│   │   ├── summary_*.csv
│   │   └── key_fields_*.csv
│   └── processed/
│       └── extracted/               # 提取的JSON文件
└── src/
    └── database/
        ├── db_manager.py            # 数据库管理器
        ├── csv_exporter.py          # CSV导出器
        └── __init__.py
```

## 🎯 数据库Schema

### 主表 sheet_1

| 字段名 | 类型 | 说明 |
|--------|------|------|
| 数据id | TEXT | 主键，唯一标识 |
| paper_id | TEXT | 论文ID |
| 数据标识 | TEXT | 实验描述 |
| 应用部位 | TEXT | 髋关节/膝关节等 |
| 产品所属专利号或文献 | TEXT | 文献信息 |
| 球头信息_* | TEXT | 球头相关信息（JSON） |
| 内衬信息_* | TEXT | 内衬相关信息（JSON） |
| 股骨柄信息_* | TEXT | 股骨柄相关信息（JSON） |
| 体外实验_* | TEXT | 实验数据（JSON） |
| created_at | TEXT | 创建时间 |
| updated_at | TEXT | 更新时间 |

共30个字段（28个数据字段 + 2个时间戳）

## ⚠️ 注意事项

### 1. 数据去重
- 系统自动处理重复数据
- 相同dataid的记录会被更新，不会重复插入
- 保证数据库的一致性

### 2. JSON字段处理
- 复杂字段（如"球头信息.球头基本信息"）存储为JSON字符串
- 导出时可选择展平或保留JSON格式
- 展平格式更易读，JSON格式更精确

### 3. 中文字段名
- 数据库支持中文字段名
- CSV导出使用UTF-8编码（带BOM）
- Excel可以正确打开

### 4. 数据库备份
```bash
# 备份数据库
cp data/artificial_joint.db data/artificial_joint_backup.db

# 或使用SQLite命令
sqlite3 data/artificial_joint.db ".backup data/backup.db"
```

## 🔧 故障排除

### Q: 导入失败？
A: 
1. 检查JSON文件格式是否正确
2. 确保dataid字段存在
3. 查看错误日志

### Q: CSV中文乱码？
A: 
- 使用Excel打开CSV时选择UTF-8编码
- 或使用记事本打开，另存为时选择UTF-8

### Q: 数据库损坏？
A: 
1. 使用备份恢复
2. 或清空数据重新导入
3. 极端情况删除.db文件重建

### Q: 内存不足？
A: 
- 大量数据时分批导入
- 导出时使用filter_empty=True过滤空记录

## 📈 性能建议

1. **批量导入**: 使用选项3批量导入比逐个文件快
2. **索引优化**: 数据库已建立paper_id和created_at索引
3. **定期备份**: 导出CSV作为备份
4. **数据清理**: 定期删除测试数据

## 🎉 示例工作流

### 完整的数据处理流程

```bash
# 1. 提取数据
python extract.py batch

# 2. 导入数据库
python database.py
选择 3 (批量导入extracted目录)

# 3. 查看统计
选择 1 (查看数据库统计)

# 4. 导出CSV
选择 8 (导出所有格式)

# 5. 使用Excel分析
打开 data/exports/full_data_flat_*.csv
```

就是这么简单！🎊
