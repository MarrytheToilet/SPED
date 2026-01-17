# Data Schema 说明文档

## 📋 概述

这是人工关节材料数据提取系统的数据架构，采用**规范化多表结构**设计，具有良好的数据组织性和查询效率。

---

## 🏗️ 数据库架构

### ER关系图

```
┌─────────────────┐
│  basic_info     │ ◄─────┐
│  (主表)         │       │
│  - data_id (PK) │       │
│  - 应用部位      │       │
│  - 文献来源      │       │
└─────────────────┘       │
                          │ 1:1
    ┌─────────────────────┼─────────────────────┐
    │                     │                     │
    ▼                     ▼                     ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│liner_    │      │head_     │      │stem_     │
│basic     │      │basic     │      │basic     │
│(内衬基本) │      │(球头基本) │      │(股骨柄基本)│
└──────────┘      └──────────┘      └──────────┘

    ▼                     ▼                     ▼
┌──────────┐      ┌──────────┐      ┌──────────┐
│liner_    │      │head_     │      │stem_     │
│properties│      │properties│      │properties│
│(内衬性能) │      │(球头性能) │      │(股骨柄性能)│
└──────────┘      └──────────┘      └──────────┘

    ┌─────────────┬─────────────┬─────────────┐
    ▼             ▼             ▼             ▼
┌──────────┐┌──────────┐┌──────────┐┌──────────┐
│fitting_  ││test_     ││simulation││simulation│
│info      ││results   ││_params   ││_images   │
│(配合信息) ││(测试结果) ││(模拟参数) ││(模拟图像) │
└──────────┘└──────────┘└──────────┘└──────────┘
```

---

## 📊 表结构详细说明

### 1. basic_info (基本信息表) - 主表

**用途**: 记录的基本标识和文献来源

| 字段 | 类型 | 约束 | 说明 |
|------|------|------|------|
| data_id | TEXT | PRIMARY KEY | 唯一标识符，格式：AJ_YYYYMMDD_xxx |
| application_site | TEXT | - | 应用部位（髋关节、膝关节等） |
| patent_or_literature | TEXT | - | 专利号或文献DOI |
| created_at | TIMESTAMP | DEFAULT NOW | 创建时间 |
| updated_at | TIMESTAMP | DEFAULT NOW | 更新时间 |

**索引**: `idx_basic_info_site` on `application_site`

---

### 2. liner_basic (内衬基本信息表)

**用途**: 内衬材料的基本属性和加工工艺

关键字段：材料类别、材料名称、厚度、偏移、锁定机制、加工工艺、后处理

---

### 3. head_basic (球头基本信息表)

**用途**: 球头材料的基本属性和加工工艺

关键字段：材料类别、材料名称、直径、纹理、加工工艺、后处理

---

### 4. fitting_info (配合信息表)

**用途**: 内衬与球头的配合参数

关键字段：径向间隙

---

### 5. stem_basic (股骨柄基本信息表)

**用途**: 股骨柄的几何参数和材料信息（16个字段）

关键字段：材料类别、材料名称、锥度、颈长、偏心距、孔隙率、加工工艺等

---

### 6-8. 物理性能表

- **liner_properties**: 内衬物理性能（硬度、粗糙度、模量、强度、密度、泊松比）
- **head_properties**: 球头物理性能（同上，注意粗糙度单位是nm）
- **stem_properties**: 股骨柄物理性能（同上）

---

### 9. test_results (性能测试结果表)

**用途**: 摩擦磨损和力学性能测试结果

关键字段：相含量变化、累计磨损量、磨损率、抗疲劳性、接触应力、Von Mises应力

---

### 10-11. 计算模拟表

- **simulation_params**: 软件、输入参数(JSON)、输出参数(JSON)
- **simulation_images**: 结构图、图说明

---

## 📁 文件清单

### 核心文件

```
data_schema/
├── schema.xlsx                    # Excel格式schema（手工维护）
├── schema_mapping.json            # 字段映射和说明
├── schema.sql                     # SQL建表语句
└── README.md                      # 本说明文档

prompts/
└── prompt.md                      # LLM提取指令

scripts/
└── import_json.py                 # 数据导入工具
```

---

## 🔄 数据导入导出流程

### 1. LLM提取阶段

**Prompt**: 使用 `prompts/prompt.md`

**输出格式**: 多表JSON
```json
{
  "records": [
    {
      "基本信息表": {...},
      "内衬基本信息表": {...},
      "球头基本信息表": {...},
      ...其他表
    }
  ]
}
```

### 2. 数据库导入

```bash
# 导入单个文件
python scripts/import_json.py data/processed/extracted/paper1.json

# 导入整个目录
python scripts/import_json.py data/processed/extracted/
```

### 3. 数据查询

**使用视图**（推荐）:
```sql
-- 使用预定义的完整数据视图
SELECT * FROM full_data_view WHERE application_site = '髋关节';
```

**多表JOIN**:
```sql
SELECT 
    bi.application_site,
    lb.material_name as liner_material,
    hb.material_name as head_material,
    tr.wear_rate
FROM basic_info bi
LEFT JOIN liner_basic lb ON bi.data_id = lb.data_id
LEFT JOIN head_basic hb ON bi.data_id = hb.data_id
LEFT JOIN test_results tr ON bi.data_id = tr.data_id
WHERE bi.application_site = '髋关节';
```

---

## 🎯 核心特性

### 1. 规范化设计
- **1个主表** + **10个从表**
- 通过 `data_id` 外键关联
- 减少数据冗余，提高查询效率

### 2. 清晰的表分类

| 分类 | 表 | 数量 |
|------|---|------|
| **基本信息** | basic_info | 1 |
| **内衬** | liner_basic, liner_properties | 2 |
| **球头** | head_basic, head_properties | 2 |
| **股骨柄** | stem_basic, stem_properties | 2 |
| **配合** | fitting_info | 1 |
| **测试** | test_results | 1 |
| **模拟** | simulation_params, simulation_images | 2 |

### 3. 完整的字段定义
- 每个字段都有明确的类型、说明、示例
- 单位规范（mm、GPa、HV等）
- NULL值处理规则

### 4. 优化的查询
- 索引优化（应用部位、材料名称）
- 预定义视图 `full_data_view`
- 支持复杂JOIN查询

---

## 📚 参考资料

- **Excel Schema**: `data_schema/schema.xlsx` - 权威数据源
- **SQL Schema**: `data_schema/schema.sql` - 数据库定义
- **Field Mapping**: `data_schema/schema_mapping.json` - 字段映射
- **Extraction Prompt**: `prompts/prompt.md` - LLM提取指令

---

**维护者**: SPED Team  
**最后更新**: 2026-01-17
