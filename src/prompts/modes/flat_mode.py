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
import json
from concurrent.futures import ThreadPoolExecutor, as_completed

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
            f"【提取输出格式】\n{self.schema.extraction_format or '输出 JSON：{\"records\":[{字段名:{\"value\":...,\"evidence\":...}}]}。'}\n\n"
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


class MultiAgentFlatMode(GenericFlatMode):
    """多 extractor 候选抽取 + merger 仲裁合并。

    每个 extractor 使用同一份 schema 独立抽取，merger 只看到候选输出，
    不直接读取全文，以降低合并阶段引入新事实的风险。
    """

    def __init__(
        self,
        extractor_clients: Dict[str, Any],
        merger_client,
        schema,
        merger_role: str = "extract_merger",
        reviewer_client=None,
        reviewer_role: str = "extract_reviewer",
        review_enabled: bool = True,
        keep_candidates: bool = False,
    ):
        # GenericFlatMode needs one llm_client for base initialization; use merger as the owner client.
        super().__init__(merger_client, schema)
        self.extractor_clients = extractor_clients
        self.merger_client = merger_client
        self.merger_role = merger_role
        self.reviewer_client = reviewer_client
        self.reviewer_role = reviewer_role
        self.review_enabled = review_enabled
        # 溯源开关：在 metadata 中保留每个 extractor 的候选 records，
        # 供消融实验/置信度特征（agent 一致性）使用；默认关闭避免结果文件膨胀。
        self.keep_candidates = keep_candidates

    @property
    def mode_name(self) -> str:
        return "flat_multi_agent"

    def _build_merger_user_prompt(self, candidate_outputs: List[Dict[str, Any]]) -> str:
        from src.schema import prompts as P
        record_def = self.schema.record_definition or "论文中一组可独立成行的结构化数据"
        return P.EXTRACT_MERGER_USER.format(
            domain=self.schema.domain,
            record_definition=record_def,
            schema_block=self._build_schema_block(),
            candidate_outputs=json.dumps(candidate_outputs, ensure_ascii=False),
        )

    def _review_records(self, paper_id: str, content: str, records: List[Dict[str, Any]]) -> ExtractionResult:
        from src.llm import LLMMessage
        from src.schema import prompts as P

        if not self.reviewer_client or not self.review_enabled:
            cleaned, stats = self._postprocess(records, content)
            return ExtractionResult(
                success=True,
                records=cleaned,
                count=len(cleaned),
                metadata={
                    "review_used": False,
                    "evidence_verified": stats["verified"],
                    "evidence_unverified": stats["unverified"],
                    "evidence_total": stats["total"],
                },
            )

        record_def = self.schema.record_definition or "论文中一组可独立成行的结构化数据"
        user = P.EXTRACT_REVIEWER_USER.format(
            domain=self.schema.domain,
            record_definition=record_def,
            schema_block=self._build_schema_block(),
            content=content,
            records=json.dumps(records, ensure_ascii=False),
        )
        resp = self.reviewer_client.call(
            [LLMMessage(role="system", content=P.EXTRACT_REVIEWER_SYSTEM), LLMMessage(role="user", content=user)],
            call_id=f"flat_review_{paper_id}",
        )
        if not resp.success:
            cleaned, stats = self._postprocess(records, content)
            return ExtractionResult(
                success=True,
                records=cleaned,
                count=len(cleaned),
                metadata={
                    "review_used": False,
                    "review_error": resp.error,
                    "evidence_verified": stats["verified"],
                    "evidence_unverified": stats["unverified"],
                    "evidence_total": stats["total"],
                },
            )
        try:
            data = self._parse_json(resp.content)
        except Exception as e:
            cleaned, stats = self._postprocess(records, content)
            return ExtractionResult(
                success=True,
                records=cleaned,
                count=len(cleaned),
                metadata={
                    "review_used": False,
                    "review_error": f"审阅 JSON 解析失败: {e}",
                    "evidence_verified": stats["verified"],
                    "evidence_unverified": stats["unverified"],
                    "evidence_total": stats["total"],
                },
            )
        reviewed_records = data.get("records", []) if isinstance(data, dict) else []
        if not isinstance(reviewed_records, list):
            reviewed_records = []
        cleaned, stats = self._postprocess(reviewed_records, content)
        return ExtractionResult(
            success=True,
            records=cleaned,
            count=len(cleaned),
            metadata={
                "review_used": True,
                "reviewer_role": self.reviewer_role,
                "reviewer_model": self.reviewer_client.config.model,
                "review": data.get("review", {}) if isinstance(data, dict) else {},
                "evidence_verified": stats["verified"],
                "evidence_unverified": stats["unverified"],
                "evidence_total": stats["total"],
            },
        )

    def _merge_records(
        self,
        paper_id: str,
        content: str,
        candidate_outputs: List[Dict[str, Any]],
    ) -> ExtractionResult:
        from src.llm import LLMMessage
        from src.schema import prompts as P

        messages = [
            LLMMessage(role="system", content=P.EXTRACT_MERGER_SYSTEM),
            LLMMessage(role="user", content=self._build_merger_user_prompt(candidate_outputs)),
        ]
        resp = self.merger_client.call(messages, call_id=f"flat_merge_{paper_id}")
        if not resp.success:
            return ExtractionResult(success=False, error=f"合并失败: {resp.error}")
        try:
            data = self._parse_json(resp.content)
        except Exception as e:
            return ExtractionResult(success=False, error=f"合并 JSON 解析失败: {e}")
        records = data.get("records", []) if isinstance(data, dict) else []
        if not isinstance(records, list):
            records = []
        reviewed = self._review_records(paper_id, content, records)
        reviewed.metadata.update({
            "schema_slug": self.schema.slug,
            "field_count": len(self.schema.fields),
            "merger_role": self.merger_role,
            "merger_model": self.merger_client.config.model,
        })
        return reviewed

    def extract(self, paper_id: str, content: str, chunks: List[str] = None, **kwargs) -> ExtractionResult:
        candidate_outputs: List[Dict[str, Any]] = []
        errors: Dict[str, str] = {}

        def _run_one(role: str, client: Any):
            mode = GenericFlatMode(client, self.schema)
            result = mode.extract(paper_id=paper_id, content=content, chunks=chunks, **kwargs)
            return role, client, result

        workers = max(1, min(len(self.extractor_clients), 8))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {
                ex.submit(_run_one, role, client): role
                for role, client in self.extractor_clients.items()
            }
            for fut in as_completed(futures):
                role = futures[fut]
                try:
                    role, client, result = fut.result()
                except Exception as e:  # noqa: BLE001
                    errors[role] = str(e)
                    continue
                if result.success:
                    candidate_outputs.append({
                        "role": role,
                        "model": client.config.model,
                        "records": result.records,
                        "count": result.count,
                        "metadata": result.metadata,
                    })
                else:
                    errors[role] = result.error

        if not candidate_outputs:
            return ExtractionResult(
                success=False,
                error="所有 extractor 均失败: " + json.dumps(errors, ensure_ascii=False),
                metadata={
                    "extractor_roles": list(self.extractor_clients.keys()),
                    "agent_errors": errors,
                },
            )

        role_order = {role: i for i, role in enumerate(self.extractor_clients.keys())}
        candidate_outputs.sort(key=lambda x: role_order.get(x["role"], len(role_order)))

        if len(candidate_outputs) == 1:
            only = candidate_outputs[0]
            reviewed = self._review_records(paper_id, content, only.get("records", []))
            reviewed.metadata.update({
                "schema_slug": self.schema.slug,
                "field_count": len(self.schema.fields),
                "multi_agent": True,
                "merge_used": False,
                "extractor_roles": list(self.extractor_clients.keys()),
                "successful_agents": [only["role"]],
                "agent_errors": errors,
            })
            if self.keep_candidates:
                reviewed.metadata["candidates"] = [
                    {"role": x["role"], "model": x["model"], "records": x["records"]}
                    for x in candidate_outputs
                ]
            return reviewed

        merged = self._merge_records(paper_id, content, candidate_outputs)
        merged.metadata.update({
            "multi_agent": True,
            "merge_used": True,
            "extractor_roles": list(self.extractor_clients.keys()),
            "successful_agents": [x["role"] for x in candidate_outputs],
            "agent_errors": errors,
            "candidate_counts": {x["role"]: x["count"] for x in candidate_outputs},
        })
        if self.keep_candidates:
            merged.metadata["candidates"] = [
                {"role": x["role"], "model": x["model"], "records": x["records"]}
                for x in candidate_outputs
            ]
        return merged
