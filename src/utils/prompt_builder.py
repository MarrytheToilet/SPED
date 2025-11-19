#!/usr/bin/env python3
"""
Prompt构建器 - 动态组装prompt和schema
"""
from pathlib import Path


def build_prompt(mode: str = "full") -> str:
    """
    构建完整的prompt（包含schema）
    
    Args:
        mode: 提取模式（暂未使用，保留用于future扩展）
    
    Returns:
        str: 组装好的prompt模板（不含论文文本）
    """
    # 读取prompt模板（现在只有一个版本）
    prompt_file = Path(__file__).parent.parent.parent / "prompts" / "prompt.md"
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    # 生成schema文本
    schema_text = generate_schema_text()
    
    # 替换占位符
    prompt = prompt_template.replace("{SCHEMA}", schema_text)
    
    return prompt


def generate_schema_text() -> str:
    """
    生成schema文本描述
    
    Returns:
        str: schema的markdown格式文本
    """
    schema_text = """
### 主表字段（28个必填）

**基本信息（3个）**
- `数据标识` - string - 实验简短描述
- `应用部位` - string - 髋关节/膝关节/其他  
- `产品所属专利号或文献` - string

**球头信息（4个）**
- `球头信息.球头基本信息` - JSON字符串 - `{材料类别, 材料编号, 直径, 加工工艺, 表面处理, 表面粗糙度}`
- `球头信息.球头-成分组成` - JSON字符串 - 化学成分及百分比
- `球头信息.球头-物理性能` - JSON字符串 - `{硬度, 弹性模量, 密度, ...}`
- `球头信息.球头-微观组织` - JSON字符串 - `{晶粒大小, 晶粒取向, ...}`

**内衬信息（6个）**
- `内衬信息.内衬-基本信息` - JSON字符串 - `{材料类别, 材料编号, 分子量, ...}`
- `内衬信息.内衬-改性填料` - JSON字符串 - `{填料类型, 添加量}`
- `内衬信息.内衬-成分组成` - JSON字符串
- `内衬信息.内衬-物理性能` - JSON字符串
- `内衬信息.复合材料性能` - JSON字符串
- `内衬信息.内衬-材料表征` - JSON字符串 - `{表征方法, 分析结果}`

**股骨柄信息（4个）**
- `股骨柄信息.股骨柄基本信息` - JSON字符串
- `股骨柄信息.股骨柄-成分组成` - JSON字符串
- `股骨柄信息.股骨柄-物理性能` - JSON字符串
- `股骨柄信息.股骨柄-微观组织` - JSON字符串

**内衬与球头摩擦腐蚀实验（7个）**
- `体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置` - JSON字符串
- `体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验环境-润滑液组成` - JSON字符串
- `体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果` - JSON字符串
- `体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果` - JSON字符串
- `体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果` - JSON字符串
- `体外实验-内衬与球头摩擦腐蚀实验.内衬腐蚀实验结果` - JSON字符串
- `体外实验-内衬与球头摩擦腐蚀实验.球头表面成分分析` - JSON字符串

**球头与锥颈微动腐蚀实验（3个）**
- `体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置` - JSON字符串
- `体外实验-球头与锥颈界面微动腐蚀实验.锥颈与球头-实验环境-润滑液组成` - JSON字符串
- `体外实验-球头与锥颈界面微动腐蚀实验.腐蚀与磨损实验结果` - JSON字符串
"""
    return schema_text.strip()


def add_paper_text(prompt_template: str, paper_text: str, mode: str = "full") -> str:
    """
    将论文文本添加到prompt中
    
    Args:
        prompt_template: prompt模板
        paper_text: 论文文本
        mode: 提取模式（full/chunk）
    
    Returns:
        str: 完整的prompt
    """
    if mode == "full":
        task = f"""

---

## 当前任务

从以下完整论文中提取**所有**实验数据。

### 论文文本：
```
{paper_text}
```

请提取所有独立实验，每个实验创建一条记录。
返回格式：{{"records": [record1, record2, ...]}}
返回纯JSON，不要markdown代码块包裹。
"""
    else:  # chunk模式
        task = f"""

---

## 当前任务

从以下论文片段中提取实验数据。

### 论文片段：
```
{paper_text}
```

根据内容自主判断：
- 发现新实验 → `{{"records": [{{"action": "new", "data": {{...全部28个字段}}}}]}}`
- 补充已有实验 → `{{"records": [{{"action": "enrich", "record_index": N, "data": {{...更新字段}}}}]}}`

返回纯JSON，不要markdown代码块包裹。
"""
    
    return prompt_template + task
