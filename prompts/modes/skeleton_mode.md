# 骨架识别模式 - 记录识别与元信息提取

## 🎯 任务目标

快速扫描论文全文，识别所有**独立材料/样品记录**，输出简洁的骨架JSON。

> ⚠️ **重要**：仔细识别所有不同的材料、处理方式、添加剂配比，确保不遗漏任何独立记录！

---

## 📖 论文内容

{PAPER_CONTENT}

---

## ❓ 什么是"独立记录"？

### ✅ 需要分开为独立记录的情况

| 情况 | 示例 | 记录数 |
|------|------|--------|
| **不同基体材料** | CoCrMo球头 vs Ti6Al4V球头 | 2条 |
| **不同表面处理** | 抛光 vs 氮化 vs DLC涂层 vs TiN涂层 | 每种1条 |
| **不同添加剂配比** | 纯PEEK vs PEEK+10%CF vs PEEK+30%CF | 3条 |
| **不同配合副组合** | CoCrMo-UHMWPE vs Al₂O₃-Al₂O₃ | 2条 |
| **对照组 vs 实验组** | 未处理样品 vs 处理后样品 | 2条 |
| **不同尺寸规格** | 28mm球头 vs 32mm球头（分别测试时）| 2条 |
| **不同辐照剂量** | 未辐照 vs 50kGy vs 100kGy | 3条 |
| **不同制造工艺** | 铸造 vs 锻造 vs 3D打印 | 3条 |

### ❌ 不需要分开的情况（合并为一条记录）

| 情况 | 说明 |
|------|------|
| 同一样品的多个测试指标 | 硬度、粗糙度、摩擦系数都属于同一记录 |
| 同一实验的不同时间点 | 磨损100万次、200万次、300万次的数据 |
| 同一材料的重复测试 | 3个平行样的平均值 |
| 同一配合副的不同载荷测试 | 5N, 10N, 20N载荷下的摩擦系数 |

### 🤔 判断原则

**核心问题**：这两组数据的材料/处理是否相同？

- 材料成分相同 + 处理相同 → **同一记录**
- 材料不同 或 处理不同 → **不同记录**

---

## 🔍 关键词识别指南

### 材料名称识别

| 论文中的表达 | 识别为 |
|-------------|--------|
| CoCrMo, Co-Cr-Mo, cobalt-chromium, cobalt chrome | CoCrMo合金 |
| Ti6Al4V, Ti-6Al-4V, titanium alloy | Ti6Al4V钛合金 |
| 316L, 316L SS, stainless steel | 316L不锈钢 |
| UHMWPE, ultra-high molecular weight polyethylene | UHMWPE |
| HXLPE, highly crosslinked polyethylene | HXLPE |
| PEEK, polyetheretherketone | PEEK |
| PEEK-CF, CFR-PEEK, carbon fiber reinforced PEEK | PEEK-CF复合材料 |
| Al₂O₃, alumina, aluminum oxide | Al₂O₃陶瓷 |
| ZrO₂, zirconia, Y-TZP | ZrO₂陶瓷 |
| BIOLOX delta, BIOLOX forte | 对应陶瓷品牌 |

### 表面处理识别

| 论文中的表达 | 识别为 |
|-------------|--------|
| polished, mirror polish, polishing | 抛光 |
| nitriding, plasma nitriding, ion nitriding | 氮化 |
| DLC coating, diamond-like carbon | DLC涂层 |
| TiN coating, titanium nitride | TiN涂层 |
| CrN coating | CrN涂层 |
| HA coating, hydroxyapatite | HA涂层 |
| PVD, physical vapor deposition | PVD涂层 |
| gamma irradiation, γ-irradiation, 50kGy, 100kGy | γ辐照+剂量 |
| e-beam irradiation, electron beam | 电子束辐照 |
| annealing, remelting | 退火/重熔 |
| grit blasting, sand blasting | 喷砂 |
| 3D printing, SLM, EBM, additive manufacturing | 3D打印 |

### 应用部位识别

| 论文中的表达 | 识别为 |
|-------------|--------|
| hip, total hip arthroplasty (THA), hip replacement | 髋关节 |
| knee, total knee arthroplasty (TKA), knee replacement | 膝关节 |
| shoulder, total shoulder arthroplasty | 肩关节 |
| ankle, total ankle replacement | 踝关节 |
| general, tribological study | 通用 |

---

## 📤 输出格式

```json
{
  "paper_info": {
    "title": "Tribological behavior of CoCrMo alloy with different surface treatments for hip joint application",
    "doi": "10.1016/j.wear.2023.204896",
    "application": "髋关节"
  },
  "record_count": 4,
  "records": [
    {
      "id": 0,
      "name": "CoCrMo-抛光",
      "component": "球头",
      "category": "金属",
      "material": "CoCrMo合金",
      "treatment": null,
      "description": "对照组，镜面抛光"
    },
    {
      "id": 1,
      "name": "CoCrMo-氮化",
      "component": "球头",
      "category": "金属",
      "material": "CoCrMo合金",
      "treatment": "等离子氮化",
      "description": "表面硬化处理"
    },
    {
      "id": 2,
      "name": "CoCrMo-DLC",
      "component": "球头",
      "category": "金属",
      "material": "CoCrMo合金",
      "treatment": "DLC涂层",
      "description": "类金刚石碳涂层"
    },
    {
      "id": 3,
      "name": "UHMWPE-内衬",
      "component": "内衬",
      "category": "聚合物",
      "material": "UHMWPE",
      "treatment": "γ辐照75kGy",
      "description": "配合球头测试"
    }
  ]
}
```

---

## 📋 字段说明

### paper_info 论文信息

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| title | ✅ | 论文完整标题，优先英文 | `Tribological behavior of...` |
| doi | ⚠️ | 格式 `10.xxxx/xxxxx`，找不到填 `null` | `10.1016/j.wear.2023.204896` |
| application | ✅ | 应用部位 | `髋关节`/`膝关节`/`肩关节`/`通用` |

### records[] 记录数组

| 字段 | 必填 | 说明 | 示例 |
|------|------|------|------|
| id | ✅ | 从0开始的连续序号 | 0, 1, 2 |
| name | ✅ | 简短唯一标识（材料-特征） | `CoCrMo-抛光`、`PEEK-30CF` |
| component | ✅ | 部件类型 | `球头`/`内衬`/`股骨柄`/`配合副` |
| category | ✅ | 材料大类 | `金属`/`陶瓷`/`聚合物`/`复合材料` |
| material | ✅ | 具体材料名 | `CoCrMo合金`、`UHMWPE` |
| treatment | ⚠️ | 表面处理/后处理，无则 `null` | `等离子氮化`、`γ辐照100kGy` |
| description | ✅ | 关键特征描述（≤20字） | `对照组`、`30%碳纤维增强` |

---

## ⚠️ 特殊情况

### 1. 非人工关节论文
```json
{
  "paper_info": {"title": "...", "doi": "...", "application": "非人工关节"},
  "record_count": 0,
  "records": []
}
```

### 2. 配合副研究（同时涉及球头和内衬）
为每个独特组件创建记录：
```json
{
  "records": [
    {"id": 0, "name": "CoCrMo-球头", "component": "球头", "category": "金属", "material": "CoCrMo合金", ...},
    {"id": 1, "name": "UHMWPE-内衬", "component": "内衬", "category": "聚合物", "material": "UHMWPE", ...}
  ]
}
```

### 3. 多种添加剂配比
```json
{
  "records": [
    {"id": 0, "name": "PEEK-纯", "material": "PEEK", "treatment": null, "description": "纯PEEK对照组"},
    {"id": 1, "name": "PEEK-10CF", "material": "PEEK-CF", "treatment": null, "description": "10%碳纤维"},
    {"id": 2, "name": "PEEK-30CF", "material": "PEEK-CF", "treatment": null, "description": "30%碳纤维"}
  ]
}
```

---

## ✅ 自检清单

1. [ ] 是否识别了所有不同的材料？
2. [ ] 是否识别了所有不同的表面处理？
3. [ ] 是否识别了所有不同的添加剂配比？
4. [ ] `record_count` 是否等于 `records` 数组长度？
5. [ ] 每个 `name` 是否唯一？
6. [ ] DOI格式是否正确（以10.开头）？

**直接输出JSON，不要markdown代码块：**
