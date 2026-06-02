"""
论文采样与摘录工具。

schema 设计阶段不需要整篇，只需有代表性的片段。对于超长论文（学位论文等）
做「分节感知」摘录：保留开头(标题/摘要/引言) + 结果/性能/讨论等关键小节 +
表格密集块 + 结尾，控制在 token/字符预算内，避免遗漏只出现在表格/后段的字段。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional


# 命中这些关键词的小节标题更可能含有可提取字段
_SECTION_KEYWORDS = [
    "result", "discussion", "experiment", "method", "material",
    "property", "properties", "mechanical", "wear", "friction",
    "tribolog", "test", "measure", "parameter", "fabricat", "process",
    "结果", "讨论", "实验", "方法", "材料", "性能", "力学", "磨损", "摩擦", "参数", "制备",
]


def _is_table_line(line: str) -> bool:
    return line.count("|") >= 2 or "\t" in line


def build_excerpt(text: str, budget: int = 12000) -> str:
    """
    构造分节感知摘录，控制在 budget 字符内。

    策略：head 段 + 命中关键词的小节/表格块 + tail 段，去重拼接。
    """
    if text is None:
        return ""
    if len(text) <= budget:
        return text

    head_chars = min(budget // 2, 6000)
    tail_chars = min(budget // 6, 2000)
    head = text[:head_chars]
    tail = text[-tail_chars:]

    remaining = budget - len(head) - len(tail)
    middle_parts: List[str] = []

    if remaining > 500:
        lines = text[head_chars:-tail_chars].split("\n")
        i = 0
        used = 0
        n = len(lines)
        while i < n and used < remaining:
            line = lines[i]
            low = line.lower()
            is_heading = line.lstrip().startswith("#")
            hit = any(k in low for k in _SECTION_KEYWORDS)
            if _is_table_line(line) or (is_heading and hit) or (hit and len(line) < 200):
                # 收集这一块（含其后若干行）
                block = [line]
                used += len(line)
                j = i + 1
                while j < n and used < remaining and (j - i) < 25:
                    nxt = lines[j]
                    if nxt.lstrip().startswith("#") and not _is_table_line(nxt):
                        break
                    block.append(nxt)
                    used += len(nxt)
                    j += 1
                middle_parts.append("\n".join(block))
                i = j
            else:
                i += 1

    middle = "\n...\n".join(middle_parts)
    if len(middle) > remaining:
        middle = middle[:remaining]

    return f"{head}\n\n...\n\n{middle}\n\n...\n\n{tail}"


def collect_figures(text: str, max_items: int = 40, max_chars: int = 2500) -> str:
    """
    抽取图/表标题行（Fig./Figure/Table/图/表 开头的说明），供 schema 设计参考。
    这些图注常含「只在图里出现」的可结构化信息（形貌、相、峰位等）。
    """
    if not text:
        return ""
    pat = re.compile(r"^\s*(?:!\[[^\]]*\]\([^)]*\)\s*)?((?:fig(?:ure)?\.?|table|图|表)\s*[\.:]?\s*\d+[^\n]{0,180})",
                     re.IGNORECASE)
    out = []
    seen = set()
    for line in text.split("\n"):
        m = pat.match(line)
        if m:
            cap = m.group(1).strip()
            key = cap[:40].lower()
            if key in seen:
                continue
            seen.add(key)
            out.append(cap)
            if len(out) >= max_items:
                break
    joined = "\n".join(out)
    return joined[:max_chars]


def load_paper_text(paper_id: str, parsed_dir: Optional[Path] = None) -> Optional[str]:
    """读取某篇已解析论文的 full.md。"""
    if parsed_dir is None:
        import settings
        parsed_dir = settings.PARSED_DIR
    path = Path(parsed_dir) / paper_id / "full.md"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def list_parsed_papers(parsed_dir: Optional[Path] = None) -> List[str]:
    """列出有 full.md 的已解析论文 id。"""
    if parsed_dir is None:
        import settings
        parsed_dir = settings.PARSED_DIR
    parsed_dir = Path(parsed_dir)
    if not parsed_dir.exists():
        return []
    out = []
    for d in sorted(parsed_dir.iterdir()):
        if d.is_dir() and (d / "full.md").exists():
            out.append(d.name)
    return out


def select_sample(paper_ids: List[str], sample_size: int, parsed_dir: Optional[Path] = None) -> List[str]:
    """
    从论文中选出多样化样本：按 full.md 体量分层（大/中/小都覆盖），
    以便 schema 同时见到期刊短文与学位长文。
    """
    if len(paper_ids) <= sample_size:
        return list(paper_ids)
    if sample_size <= 1:
        # 仅取一篇代表：选体量居中的一篇，避免过短/过长极端
        if parsed_dir is None:
            import settings
            parsed_dir = settings.PARSED_DIR
        parsed_dir = Path(parsed_dir)
        sized = []
        for pid in paper_ids:
            p = parsed_dir / pid / "full.md"
            try:
                sized.append((pid, p.stat().st_size))
            except Exception:
                sized.append((pid, 0))
        sized.sort(key=lambda x: x[1])
        return [sized[len(sized) // 2][0]]

    if parsed_dir is None:
        import settings
        parsed_dir = settings.PARSED_DIR
    parsed_dir = Path(parsed_dir)

    sized = []
    for pid in paper_ids:
        p = parsed_dir / pid / "full.md"
        try:
            sized.append((pid, p.stat().st_size))
        except Exception:
            sized.append((pid, 0))
    sized.sort(key=lambda x: x[1])

    # 等距取样，保证大小分布均匀
    n = len(sized)
    idxs = [round(i * (n - 1) / (sample_size - 1)) for i in range(sample_size)]
    seen = set()
    out = []
    for i in idxs:
        pid = sized[i][0]
        if pid not in seen:
            seen.add(pid)
            out.append(pid)
    # 不足则补齐
    for pid, _ in sized:
        if len(out) >= sample_size:
            break
        if pid not in seen:
            seen.add(pid)
            out.append(pid)
    return out
