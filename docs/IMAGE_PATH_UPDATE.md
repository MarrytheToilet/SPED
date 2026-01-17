# 图片路径字段更新说明

## 更新时间
2026-01-17

## 问题描述

用户发现表11"计算模拟图像表"中缺少图片路径字段。虽然论文Markdown中有图片引用（如`![](images/xxx.jpg)`），但schema中只有"图片描述"字段，没有存储图片的实际路径。

## 解决方案

### 1. 更新Schema

**旧字段名**：
- `计算建模模拟结构图` - 只能存描述

**新字段名**：
- `计算建模模拟结构图路径` - 存储图片相对路径
- `计算建模模拟结构图说明` - 存储完整说明

### 2. 图片路径格式

**标准格式**：
```
images/f8090ed526fd65d67d46a0523bc23574f9532403cc5c36853d43d48599d61844.jpg
```

**来源**：
- MinerU解析后的`content_list.json`中的`img_path`字段
- 相对于论文目录的路径

### 3. 多图片处理

**关键改进**：表11现在支持数组格式，一个论文可以有多条图片记录

**示例**：
```json
{
  "计算模拟图像表": [
    {
      "数据ID": "AJ_20260117_001",
      "计算建模模拟结构图路径": "images/fig1.jpg",
      "计算建模模拟结构图说明": "Fig. 1. 有限元模型网格划分"
    },
    {
      "数据ID": "AJ_20260117_001",
      "计算建模模拟结构图路径": "images/fig2.jpg",
      "计算建模模拟结构图说明": "Fig. 2. Von Mises应力分布云图，最大应力85 MPa"
    },
    {
      "数据ID": "AJ_20260117_001",
      "计算建模模拟结构图路径": "images/fig3.jpg",
      "计算建模模拟结构图说明": "Fig. 3. 接触压力分布"
    }
  ]
}
```

## 图片信息的获取

### MinerU解析结果结构

```
论文目录/
├── full.md                 # Markdown文件（可能不包含图片引用）
├── content_list.json       # 完整的内容列表（包含图片信息）
├── images/                 # 图片目录
│   ├── xxx.jpg
│   └── yyy.jpg
└── layout.json            # 布局信息
```

### content_list.json中的图片信息

```json
{
  "type": "image",
  "img_path": "images/dc438782d496736534ae3770289b29d1003dacbe1489619b8a25b71ce4244ce8.jpg",
  "image_caption": [
    "图 1-1 功能梯度材料成分结构变化示意图[58]"
  ],
  "image_footnote": [],
  "bbox": [326, 165, 618, 329],
  "page_idx": 14
}
```

**关键字段**：
- `img_path` - 图片相对路径（直接使用）
- `image_caption` - 图片说明（用于"计算建模模拟结构图说明"字段）
- `page_idx` - 页码（可选，用于验证）

## 提取指导

### 提取规则

1. **识别模拟图片**（重要⚠️）
   
   **必须提取的图片**：
   - ✅ 有限元分析（FEA）结果图
   - ✅ 应力分布云图（Von Mises应力、主应力等）
   - ✅ 位移/变形分布图
   - ✅ 接触压力分布图
   - ✅ 应变分布图
   - ✅ 有限元模型网格图
   - ✅ 温度场分布（如果有热分析）
   - ✅ 磨损深度预测图（模拟预测）
   
   **不要提取的图片**：
   - ❌ 材料微观结构照片（SEM、金相等）
   - ❌ 实验装置照片
   - ❌ 产品实物照片
   - ❌ X光片、CT扫描图
   - ❌ 磨损形貌照片（实验结果，非模拟）
   - ❌ 材料表面形貌图
   - ❌ 流程图、示意图
   - ❌ 普通的几何模型图（没有分析结果的）
   
   **判断标准**：
   - 图片是**计算机模拟/仿真的结果**（有云图、网格、应力值等） → ✅ 提取
   - 图片是**实验拍摄/观察的照片** → ❌ 不提取
   - 不确定 → 留空（null）

2. **提取路径**
   - 直接使用`content_list.json`中的`img_path`值
   - 保持相对路径格式：`images/xxx.jpg`
   - **只对筛选出的模拟图片提取路径**

3. **提取说明（使用中文）**
   - 图片编号（保留原文：Fig. 1 或 图3-2）
   - 图片类型（用中文：有限元应力分布云图、位移分布图等）
   - 关键发现（用中文描述，保留数值和单位）
   - 来自`image_caption`或论文正文
   - 专业术语英文缩写可保留（如Von Mises、FEA等）

### 提取示例

**场景1：论文有单个模拟图**

```json
{
  "计算模拟图像表": {
    "数据ID": "AJ_20260117_001",
    "计算建模模拟结构图路径": "images/abc123.jpg",
    "计算建模模拟结构图说明": "图3 Von Mises应力分布，最大值85 MPa"
  }
}
```

**场景2：论文有多个模拟图（推荐格式）**

论文中共有6张图：
- Fig. 1 产品照片 → ❌ 不提取
- Fig. 2 有限元模型 → ✅ 提取
- Fig. 3 应力分布 → ✅ 提取
- Fig. 4 SEM照片 → ❌ 不提取
- Fig. 5 磨损形貌 → ❌ 不提取
- Fig. 6 接触压力 → ✅ 提取

只提取Fig. 2、3、6：

```json
{
  "计算模拟图像表": [
    {
      "数据ID": "AJ_20260117_001",
      "计算建模模拟结构图路径": "images/model.jpg",
      "计算建模模拟结构图说明": "图2 有限元模型网格划分，采用C3D8R单元"
    },
    {
      "数据ID": "AJ_20260117_001",
      "计算建模模拟结构图路径": "images/stress.jpg",
      "计算建模模拟结构图说明": "Fig. 3 Von Mises应力分布云图，最大应力85 MPa"
    },
    {
      "数据ID": "AJ_20260117_001",
      "计算建模模拟结构图路径": "images/contact.jpg",
      "计算建模模拟结构图说明": "图6 接触压力分布，峰值压力50 MPa"
    }
  ]
}
```

**场景3：论文无模拟图（只有实验照片）**

```json
{
  "计算模拟图像表": null
}
```

## 数据库存储

### 表结构

```sql
CREATE TABLE simulation_images (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_id TEXT NOT NULL,
    image_path TEXT,
    image_description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (data_id) REFERENCES basic_info(data_id)
);
```

**注意**：
- 一个`data_id`可以对应多条图片记录
- `image_path`存储相对路径
- 实际使用时需要拼接完整路径：`论文目录 + image_path`

## 图片访问

### 完整路径构建

```python
import os
from pathlib import Path

def get_full_image_path(paper_dir, img_path):
    """
    获取图片的完整路径
    
    Args:
        paper_dir: 论文目录，如 "data/processed/parsed/output/batch_10/b10_10_xxx"
        img_path: 相对路径，如 "images/abc123.jpg"
    
    Returns:
        完整路径: "data/processed/parsed/output/batch_10/b10_10_xxx/images/abc123.jpg"
    """
    return os.path.join(paper_dir, img_path)

# 使用示例
paper_dir = "data/processed/parsed/output/batch_10/b10_10_基于功能梯度材料胫骨假体的有限元分析_李志"
img_path = "images/dc438782d496736534ae3770289b29d1003dacbe1489619b8a25b71ce4244ce8.jpg"
full_path = get_full_image_path(paper_dir, img_path)
# full_path = "data/processed/parsed/output/batch_10/b10_10_基于功能梯度材料胫骨假体的有限元分析_李志/images/dc438782d496736534ae3770289b29d1003dacbe1489619b8a25b71ce4244ce8.jpg"
```

### 图片验证

```python
def verify_image_exists(full_path):
    """验证图片是否存在"""
    return Path(full_path).exists()

# 验证
if verify_image_exists(full_path):
    print(f"✅ 图片存在：{full_path}")
else:
    print(f"❌ 图片不存在：{full_path}")
```

## 更新的文件

1. **data_schema/schema.json**
   - 更新了表11的字段定义
   - 字段名：`计算建模模拟结构图` → `计算建模模拟结构图路径`
   - 添加了详细的description

2. **prompts/prompt.md**
   - 更新了表11的字段说明
   - 添加了多图片处理示例
   - 添加了图片路径格式说明

## 使用建议

### 对于提取脚本

1. 解析`content_list.json`获取图片信息
2. 筛选type="image"的记录
3. 识别计算模拟相关的图片（通过caption关键词）
4. 提取`img_path`和`image_caption`
5. 如果有多个图片，创建数组

### 对于人工检查

1. 查看论文目录下的`images/`文件夹
2. 打开`content_list.json`查找图片信息
3. 验证提取的路径是否正确
4. 确认图片说明是否完整

## 注意事项

1. **路径格式统一**
   - 使用相对路径，不要使用绝对路径
   - 格式：`images/xxx.jpg`
   - 不要包含前导`./`

2. **多图片场景**
   - 优先使用数组格式
   - 每个图片一条记录
   - 共享同一个data_id

3. **图片说明完整性**
   - 包含图片编号
   - 包含图片类型
   - 包含关键数值（如果有）

4. **图片筛选**
   - 只提取计算模拟相关的图片
   - 实验照片、材料照片等不需要提取到此表

## 测试验证

```python
# 测试代码
import json
from pathlib import Path

def test_image_extraction():
    # 读取content_list.json
    content_file = "data/processed/parsed/output/batch_10/b10_10_xxx/c8787aa9_content_list.json"
    with open(content_file) as f:
        content_list = json.load(f)
    
    # 筛选图片
    images = [item for item in content_list if item.get('type') == 'image']
    
    print(f"找到 {len(images)} 个图片")
    for img in images[:3]:  # 显示前3个
        print(f"路径: {img.get('img_path')}")
        print(f"说明: {img.get('image_caption')}")
        print()

# 运行测试
test_image_extraction()
```

## 总结

这次更新解决了图片路径缺失的问题，让系统能够：
1. ✅ 保存图片的相对路径
2. ✅ 支持多图片场景
3. ✅ 完整保存图片说明
4. ✅ 便于后续图片访问和展示

**核心改进**：
- 字段名更明确（"路径"而不是"结构图"）
- 支持数组格式（多图片）
- 详细的使用说明

---

**更新时间**: 2026-01-17  
**影响范围**: Schema、Prompt、提取逻辑  
**向后兼容**: 是（旧数据可以保留，新数据使用新格式）
