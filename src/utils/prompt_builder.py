#!/usr/bin/env python3
"""
Prompt构建器 - 动态组装prompt和schema
"""
from pathlib import Path


def build_prompt(mode: str = "full") -> str:
    """
    构建完整的prompt
    
    Args:
        mode: 提取模式（暂未使用，保留用于future扩展）
    
    Returns:
        str: 组装好的prompt模板（不含论文文本）
    """
    # 读取prompt模板
    prompt_file = Path(__file__).parent.parent.parent / "prompts" / "prompt.md"
    
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt文件不存在: {prompt_file}")
    
    with open(prompt_file, 'r', encoding='utf-8') as f:
        prompt_template = f.read()
    
    return prompt_template

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
