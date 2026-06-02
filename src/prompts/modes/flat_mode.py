"""
通用扁平提取模式 (GenericFlatMode)

依据 LLM 自动设计的单表 schema，对整篇论文做一次性提取，
输出扁平记录，每个字段内联 {value, evidence}：
  records: [ { "field_a": {"value": ..., "evidence": "原文片段"}, ... }, ... ]
规则：
  - 字段无值时 value=null 且 evidence=null（不臆造）。
  - evidence 必须是论文原文中的一段引文（用于人工/自动核验）。
  - 提取后对 evidence 做长度截断与「是否近似为原文子串」校验（仅标记，不丢弃）。
"""
from __future__ import annotations

import re
import unicodedata
from typing import Any, Dict, List, Optional

from .base import ExtractionMode, ExtractionResult

EVIDENCE_MAX_CHARS = 240
EVIDENCE_MATCH_WINDOW = 16


def _normalize_text(s: str) -> str:
    """NFKC + 去除 LaTeX/markdown 数学标记 + 仅保留字母数字与中文，用于 evidence 核验。"""
    if not s:
        return ""
    s = unicodedata.normalize("NFKC", s)
    s = re.sub(r"\\[a-zA-Z]+", " ", s)  # 去 \mathrm \times 等 LaTeX 命令
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", s.lower())


def _evidence_in_source(evidence: str, norm_source: str) -> bool:
    """
    判断 evidence 是否源自原文。容忍模型添加的前后缀与 OCR/markdown 差异：
    完整子串命中，或存在一段足够长(>=window)的连续片段命中即视为通过。
    """
    n = _normalize_text(evidence)
    if not n:
        return False
    if n in norm_source:
        return True
    w = EVIDENCE_MATCH_WINDOW
    if len(n) <= w:
        return n in norm_source
    for i in range(0, len(n) - w + 1):
        if n[i:i + w] in norm_source:
            return True
    return False


class GenericFlatMode(ExtractionMode):
    """基于生成 schema 的扁平 + evidence 提取。"""

    def __init__(self, llm_client, schema, prompt_assembler=None):
        super().__init__(llm_client, prompt_assembler)
        self.schema = schema

    @property
    def mode_name(self) -> str:
        return "flat"

    def _parse_json(self, content: str):
        """用带 json_repair 兜底的宽松解析（应对 reasoning 模型偶发非法 JSON）。"""
        from src.schema._json import parse_json_loose
        return parse_json_loose(content)

    # ---- prompt ----
    def _build_system_prompt(self) -> str:
        from src.schema import prompts as P
        return P.EXTRACTOR_SYSTEM

    def _build_schema_block(self) -> str:
        lines = []
        for f in self.schema.fields:
            parts = [f"- {f.name} ({f.type}"]
            if f.unit:
                parts[0] += f", 单位:{f.unit}"
            if f.enum_values:
                parts[0] += f", 取值:{f.enum_values}"
            parts[0] += ")"
            desc = f.description or ""
            hint = f" 提示:{f.extraction_hint}" if f.extraction_hint else ""
            fig = " [图/表征字段：证据可用图注/表标题]" if getattr(f, "from_figure", False) else ""
            lines.append(f"{parts[0]}: {desc}{hint}{fig}")
        return "\n".join(lines)

    def _build_user_prompt(self, paper_id: str, content: str) -> str:
        record_def = self.schema.record_definition or "论文中一组可独立成行的结构化数据"
        return (
            f"【领域】{self.schema.domain}\n"
            f"【一条记录代表】{record_def}\n\n"
            f"【字段表 schema】\n{self._build_schema_block()}\n\n"
            f"【论文全文 (paper_id={paper_id})】\n{content}\n\n"
            f"请按 schema 抽取所有记录，输出 JSON（含 records，每字段 value+evidence）。"
        )

    # ---- 提取 ----
    def extract(self, paper_id: str, content: str, chunks: List[str] = None, **kwargs) -> ExtractionResult:
        try:
            import settings
            max_chars = int(getattr(settings, "EXTRACT_MAX_INPUT_CHARS", 0) or 0)
        except Exception:
            max_chars = 0
        truncated_input = False
        if max_chars and len(content) > max_chars:
            content = content[:max_chars]
            truncated_input = True
            self.logger.warning(f"[{paper_id}] 输入超长，截断至 {max_chars} 字符")

        result = self._call_llm(
            system_prompt=self._build_system_prompt(),
            user_prompt=self._build_user_prompt(paper_id, content),
            call_id=f"flat_extract_{paper_id}",
        )
        if not result["success"]:
            return ExtractionResult(success=False, error=result["error"])

        data = result["data"]
        records = data.get("records", []) if isinstance(data, dict) else []
        if not isinstance(records, list):
            records = []

        cleaned, stats = self._postprocess(records, content)
        meta = {
            "schema_slug": self.schema.slug,
            "field_count": len(self.schema.fields),
            "input_truncated": truncated_input,
            "evidence_verified": stats["verified"],
            "evidence_unverified": stats["unverified"],
            "evidence_total": stats["total"],
        }
        return ExtractionResult(
            success=True,
            records=cleaned,
            count=len(cleaned),
            metadata=meta,
        )

    def _postprocess(self, records: List[Any], source: str) -> (List[Dict], Dict[str, int]):
        field_names = {f.normalized_key(): f.name for f in self.schema.fields}
        norm_source = _normalize_text(source)
        verified = unverified = total = 0
        out: List[Dict] = []

        for rec in records:
            if not isinstance(rec, dict):
                continue
            new_rec: Dict[str, Any] = {}
            for raw_name, cell in rec.items():
                # 规范化字段名映射回 schema 字段
                key = re.sub(r"[\s\-/]+", "_", str(raw_name).strip().lower())
                key = re.sub(r"[^\w\u4e00-\u9fff]+", "", key)
                fname = field_names.get(key, str(raw_name))

                value, evidence = self._normalize_cell(cell)
                if value is None:
                    new_rec[fname] = {"value": None, "evidence": None}
                    continue

                if evidence:
                    evidence = evidence[:EVIDENCE_MAX_CHARS]
                    total += 1
                    ok = _evidence_in_source(evidence, norm_source)
                    if ok:
                        verified += 1
                    else:
                        unverified += 1
                    new_rec[fname] = {"value": value, "evidence": evidence, "evidence_verified": ok}
                else:
                    new_rec[fname] = {"value": value, "evidence": None}
            if new_rec:
                out.append(new_rec)

        return out, {"verified": verified, "unverified": unverified, "total": total}

    @staticmethod
    def _normalize_cell(cell: Any) -> (Any, Optional[str]):
        """把单元格归一为 (value, evidence)。兼容模型直接给标量的情况。"""
        if isinstance(cell, dict):
            value = cell.get("value", None)
            evidence = cell.get("evidence", None)
            if isinstance(evidence, (int, float)):
                evidence = str(evidence)
            if isinstance(value, str) and value.strip().lower() in ("", "null", "n/a", "na", "none", "未提及", "未提供"):
                value = None
            return value, (evidence if isinstance(evidence, str) and evidence.strip() else None)
        # 标量
        if isinstance(cell, str) and cell.strip().lower() in ("", "null", "n/a", "na", "none"):
            return None, None
        return cell, None
