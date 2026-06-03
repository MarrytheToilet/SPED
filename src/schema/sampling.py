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


def build_schema_context_for_papers(paper_ids: List[str], budget_per_paper: int = 16000,
                                    parsed_dir: Optional[Path] = None,
                                    collection: str = "") -> str:
    """
    为“完整 schema agent”构造同一批样本论文上下文。

    优先保留每篇论文的摘要/引言/实验或方法相关部分；若 MinerU 的标题结构不稳定，
    回退到 build_excerpt 的分节感知摘录。每篇论文单独限长，避免某篇长文挤掉其它样本。
    """
    parts: List[str] = []
    for pid in paper_ids:
        text = load_paper_text(pid, parsed_dir=parsed_dir, collection=collection) or ""
        if not text:
            continue
        excerpt = _abstract_intro_methods_excerpt(text, budget_per_paper)
        figures = collect_figures(text, max_items=24, max_chars=1600)
        parts.append(
            f"===== PAPER {pid} =====\n"
            f"【正文摘录：摘要 / 引言 / 实验或方法优先】\n{excerpt}\n\n"
            f"【图/表标题】\n{figures or '（未识别到图/表标题）'}"
        )
    return "\n\n".join(parts)


def _abstract_intro_methods_excerpt(text: str, budget: int) -> str:
    """抽摘要、引言、实验/方法优先；不足或失败时回退 build_excerpt。"""
    if len(text) <= budget:
        return text

    lines = text.splitlines()
    section_patterns = [
        r"abstract|摘要",
        r"introduction|引言|绪论",
        r"experiment|experimental|materials?\s+and\s+methods?|methodology|methods?|实验|材料与方法|方法",
    ]
    wanted = [re.compile(p, re.I) for p in section_patterns]

    blocks: List[str] = []
    n = len(lines)
    i = 0
    while i < n:
        line = lines[i]
        clean = line.strip().lstrip("#").strip()
        is_heading = line.lstrip().startswith("#") or (len(clean) < 120 and any(p.search(clean) for p in wanted))
        if is_heading and any(p.search(clean) for p in wanted):
            block = [line]
            j = i + 1
            while j < n:
                nxt = lines[j]
                nxt_clean = nxt.strip().lstrip("#").strip()
                if j > i + 3 and nxt.lstrip().startswith("#"):
                    break
                if j > i + 8 and len(nxt_clean) < 120 and re.match(r"^\d+(\.\d+)*\s+\S+", nxt_clean):
                    break
                block.append(nxt)
                if sum(len(x) for x in block) >= budget // 2:
                    break
                j += 1
            blocks.append("\n".join(block))
            i = j
        else:
            i += 1

    joined = "\n\n...\n\n".join(blocks)
    if len(joined) >= max(1000, budget // 4):
        return joined[:budget]
    return build_excerpt(text, budget=budget)


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


def _safe_collection(collection: str = "") -> str:
    raw = (collection or "").strip().replace("\\", "/").strip("/")
    parts = [p for p in raw.split("/") if p and p not in (".", "..")]
    return "/".join(parts)


def load_paper_text(paper_id: str, parsed_dir: Optional[Path] = None,
                    collection: str = "") -> Optional[str]:
    """读取某篇已解析论文的 full.md。"""
    if parsed_dir is None:
        import settings
        collection = collection or getattr(settings, "DEFAULT_COLLECTION", "")
        parsed_dir = settings.collection_parsed_dir(collection)
    collection = _safe_collection(collection)
    path = Path(parsed_dir) / paper_id / "full.md"
    if not path.exists():
        return None
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def list_parsed_papers(parsed_dir: Optional[Path] = None,
                       collection: str = "") -> List[str]:
    """列出有 full.md 的已解析论文 id。"""
    if parsed_dir is None:
        import settings
        collection = collection or getattr(settings, "DEFAULT_COLLECTION", "")
        parsed_dir = settings.collection_parsed_dir(collection)
    collection = _safe_collection(collection)
    parsed_dir = Path(parsed_dir)
    if not parsed_dir.exists():
        return []
    out = []
    for d in sorted(parsed_dir.iterdir()):
        if d.is_dir() and (d / "full.md").exists():
            out.append(d.name)
    return out


def select_sample(paper_ids: List[str], sample_size: int, parsed_dir: Optional[Path] = None,
                  collection: str = "") -> List[str]:
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
            collection = collection or getattr(settings, "DEFAULT_COLLECTION", "")
            parsed_dir = settings.collection_parsed_dir(collection)
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
        collection = collection or getattr(settings, "DEFAULT_COLLECTION", "")
        parsed_dir = settings.collection_parsed_dir(collection)
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
