"""共享的宽松 JSON 解析（兼容 LLM 偶尔包裹的代码块/前后缀）。"""
from __future__ import annotations

import json
import re
from typing import Any


def parse_json_loose(content: str) -> Any:
    """尽力把 LLM 返回解析为 JSON 对象/数组。失败抛 ValueError。"""
    if content is None:
        raise ValueError("空内容")
    content = content.strip()
    if not content:
        raise ValueError("空内容")

    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    patterns = [
        r"```json\s*([\s\S]*?)\s*```",
        r"```\s*([\s\S]*?)\s*```",
        r"(\{[\s\S]*\})",
        r"(\[[\s\S]*\])",
    ]
    for pat in patterns:
        m = re.search(pat, content)
        if m:
            snippet = m.group(1)
            try:
                return json.loads(snippet)
            except (json.JSONDecodeError, IndexError):
                continue

    # 最后兜底：用 json_repair 修复模型偶发的非法 JSON（如括号不匹配、尾逗号）
    try:
        import json_repair
        repaired = json_repair.loads(content)
        if repaired not in (None, "", [], {}):
            return repaired
    except Exception:
        pass

    raise ValueError(f"无法解析 JSON: {content[:200]}...")
