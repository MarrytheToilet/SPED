"""
Schema 自动设计引擎（多agent协作）。

流程：
  1. 选取多样化样本论文（按体量分层）。
  2. Schema agent 阶段：默认 3 个 agent 独立阅读同一批样本论文上下文，
     各自产出一份完整 schema。
  3. 合并阶段(schema_merger)：合并多份完整 schema 草稿。
  4. 审阅阶段(schema_reviewer)：审阅合并结果，定稿。

各角色端点由 settings.get_agent_config(role) 决定，默认全部回退到基础 DeepSeek。
"""
from __future__ import annotations

import datetime
import json as _json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from ..llm.base import LLMClient, LLMMessage
from ..llm.factory import create_llm_client_for_agent
from ._json import parse_json_loose
from .models import GeneratedSchema, SchemaField, normalize_field_name, validate_schema
from .sampling import build_schema_context_for_papers, load_paper_text, select_sample
from . import prompts as P


class SchemaDiscovery:
    """根据领域简介 + 论文样本，多agent协作设计单表 schema。"""

    def __init__(
        self,
        domain: str,
        description: str = "",
        sample_size: int = None,
        excerpt_budget: int = None,
        target_min: int = None,
        target_max: int = None,
        schema_agent_roles: List[str] = None,
        schema_merger_role: str = None,
        schema_reviewer_role: str = None,
        collection: str = "",
    ):
        import settings
        self.domain = domain
        self.description = description or domain
        self.collection = collection or getattr(settings, "DEFAULT_COLLECTION", "")
        self.sample_size = sample_size or getattr(settings, "SCHEMA_SAMPLE_SIZE", 8)
        self.excerpt_budget = excerpt_budget or getattr(settings, "SCHEMA_EXCERPT_BUDGET", 16000)
        self.target_min = target_min or getattr(settings, "SCHEMA_MIN_FIELDS", 20)
        self.target_max = target_max or getattr(settings, "SCHEMA_MAX_FIELDS", 80)
        self.schema_agent_roles = schema_agent_roles or getattr(
            settings, "SCHEMA_AGENT_ROLES", ["schema_agent_a", "schema_agent_b", "schema_agent_c"]
        )
        self.schema_merger_role = schema_merger_role or getattr(settings, "SCHEMA_MERGER_ROLE", "schema_merger")
        self.schema_reviewer_role = schema_reviewer_role or getattr(settings, "SCHEMA_REVIEWER_ROLE", "schema_reviewer")
        self.logger = logger.bind(module="SchemaDiscovery")
        self._clients: Dict[str, LLMClient] = {}

    def _client(self, role: str) -> LLMClient:
        if role not in self._clients:
            self._clients[role] = create_llm_client_for_agent(role)
        return self._clients[role]

    # ---- 完整 schema 草案 ----
    def _draft_schema_with_agent(self, role: str, paper_context: str) -> Optional[GeneratedSchema]:
        user = P.SCHEMA_AGENT_USER.format(
            description=self.description,
            paper_context=paper_context,
            min=self.target_min,
            max=self.target_max,
        )
        messages = [
            LLMMessage(role="system", content=P.SCHEMA_AGENT_SYSTEM),
            LLMMessage(role="user", content=user),
        ]
        resp = self._client(role).call(messages, call_id=f"schema_draft_{role}")
        if not resp.success:
            self.logger.warning(f"[{role}] schema 草案失败: {resp.error}")
            return None
        try:
            data = parse_json_loose(resp.content)
        except ValueError as e:
            self.logger.warning(f"[{role}] schema 草案解析失败: {e}")
            return None
        if not isinstance(data, dict) or not data.get("fields"):
            self.logger.warning(f"[{role}] schema 草案为空")
            return None
        schema = self._schema_from_json(data, [])
        schema.model = self._client(role).config.model
        return schema

    def _merge_schema_drafts(self, drafts: List[GeneratedSchema]) -> GeneratedSchema:
        payload = [
            {
                "role": getattr(d, "agent_role", ""),
                "record_definition": d.record_definition,
                "fields": [f.to_dict() for f in d.fields],
                "extraction_format": d.extraction_format,
            }
            for d in drafts
        ]
        system = P.SCHEMA_MERGER_SYSTEM.format(min=self.target_min, max=self.target_max)
        user = P.SCHEMA_MERGER_USER.format(
            description=self.description,
            schema_drafts=_json.dumps(payload, ensure_ascii=False),
            min=self.target_min,
            max=self.target_max,
        )
        resp = self._client(self.schema_merger_role).call(
            [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)],
            call_id="schema_merge",
        )
        if not resp.success:
            raise RuntimeError(f"合并 schema 草案失败: {resp.error}")
        data = parse_json_loose(resp.content)
        if not isinstance(data, dict):
            raise RuntimeError("schema 合并返回非对象")
        return self._schema_from_json(data, [])

    def _review_schema(self, draft: GeneratedSchema) -> GeneratedSchema:
        system = P.SCHEMA_REVIEWER_SYSTEM.format(min=self.target_min, max=self.target_max)
        draft_json = _json.dumps(
            {
                "record_definition": draft.record_definition,
                "fields": [f.to_dict() for f in draft.fields],
                "extraction_format": draft.extraction_format,
            },
            ensure_ascii=False,
        )
        user = P.SCHEMA_REVIEWER_USER.format(
            description=self.description,
            draft_schema=draft_json,
            min=self.target_min,
            max=self.target_max,
        )
        resp = self._client(self.schema_reviewer_role).call(
            [LLMMessage(role="system", content=system), LLMMessage(role="user", content=user)],
            call_id="schema_review",
        )
        if not resp.success:
            self.logger.warning(f"schema 审阅失败，沿用合并草稿: {resp.error}")
            return draft
        try:
            data = parse_json_loose(resp.content)
        except ValueError as e:
            self.logger.warning(f"schema 审阅解析失败，沿用合并草稿: {e}")
            return draft
        if not isinstance(data, dict) or not data.get("fields"):
            return draft
        reviewed = self._schema_from_json(data, [])
        if len(reviewed.fields) < max(self.target_min // 2, 5):
            self.logger.warning("schema 审阅结果字段过少，沿用合并草稿")
            return draft
        return reviewed

    # ---- schema 组装 + 修复 ----
    def _schema_from_json(self, data: Dict, candidates: List[Dict]) -> GeneratedSchema:
        cov_map = {normalize_field_name(c["name"]): c.get("coverage", 0) for c in candidates}
        fig_map = {normalize_field_name(c["name"]): bool(c.get("from_figure")) for c in candidates}
        fields = []
        for fd in data.get("fields", []):
            if not isinstance(fd, dict):
                continue
            sf = SchemaField.from_dict(fd)
            if not sf.name:
                continue
            if not sf.coverage:
                sf.coverage = cov_map.get(sf.normalized_key(), 0)
            if not sf.from_figure and fig_map.get(sf.normalized_key()):
                sf.from_figure = True
            fields.append(sf)
        return GeneratedSchema(
            domain=self.domain,
            description=self.description,
            fields=fields,
            record_definition=str(data.get("record_definition", "")).strip(),
            extraction_format=str(data.get("extraction_format", "")).strip(),
            generated_at=datetime.datetime.now().isoformat(timespec="seconds"),
        )

    def _repair_schema(self, schema: GeneratedSchema, candidates: List[Dict]) -> Tuple[GeneratedSchema, List[str]]:
        """Deterministic cleanup after LLM review.

        This does not invent domain knowledge. It only enforces basic schema hygiene so
        downstream extraction gets a stable field list even when the LLM returns
        duplicates, too many fields, or too few fields.
        """
        notes: List[str] = []

        if not schema.record_definition:
            schema.record_definition = "论文中一个可独立比较的研究对象、方法/条件与结果组合"
            notes.append("补充默认 record_definition")
        if not schema.extraction_format:
            schema.extraction_format = (
                '输出 JSON：{"records":[{字段名:{"value":..., "evidence":"原文片段或null"}}]}。'
                "无法确定时 value=null 且 evidence=null。"
            )
            notes.append("补充默认 extraction_format")

        # 1) Deduplicate by normalized name, keeping the more informative field.
        by_key: Dict[str, SchemaField] = {}

        def score_field(f: SchemaField) -> tuple:
            importance_rank = {"core": 3, "rare_important": 2, "common": 1}.get(f.importance, 0)
            info = len(f.description or "") + len(f.extraction_hint or "")
            return (importance_rank, int(f.coverage or 0), bool(f.from_figure), info)

        for field in schema.fields:
            if not field.name:
                continue
            key = field.normalized_key()
            old = by_key.get(key)
            if old is None:
                by_key[key] = field
                continue
            keep, drop = (field, old) if score_field(field) > score_field(old) else (old, field)
            if not keep.description and drop.description:
                keep.description = drop.description
            if not keep.extraction_hint and drop.extraction_hint:
                keep.extraction_hint = drop.extraction_hint
            if not keep.unit and drop.unit:
                keep.unit = drop.unit
            if not keep.enum_values and drop.enum_values:
                keep.enum_values = drop.enum_values
            keep.coverage = max(int(keep.coverage or 0), int(drop.coverage or 0))
            keep.from_figure = bool(keep.from_figure or drop.from_figure)
            by_key[key] = keep
            notes.append(f"合并重复字段: {drop.name} -> {keep.name}")

        fields = list(by_key.values())

        # 2) Repair enum fields that have no enum list.
        for field in fields:
            if field.type == "enum" and not field.enum_values:
                field.type = "string"
                notes.append(f"枚举字段缺少取值，降级为 string: {field.name}")

        # 3) If the final schema is too small, fill from candidate pool by coverage.
        if len(fields) < self.target_min:
            existing = {f.normalized_key() for f in fields}
            for cand in candidates:
                if len(fields) >= self.target_min:
                    break
                key = normalize_field_name(str(cand.get("name", "")))
                if not key or key in existing:
                    continue
                new_field = SchemaField.from_dict({
                    "name": cand.get("name", ""),
                    "type": cand.get("type", "string"),
                    "unit": cand.get("unit"),
                    "enum_values": cand.get("enum_values"),
                    "description": cand.get("description", ""),
                    "extraction_hint": cand.get("extraction_hint", ""),
                    "importance": "common",
                    "coverage": cand.get("coverage", 0),
                    "from_figure": cand.get("from_figure", False),
                })
                if new_field.name:
                    fields.append(new_field)
                    existing.add(new_field.normalized_key())
                    notes.append(f"字段数不足，从候选池补入: {new_field.name}")

        # 4) If too large, keep high-coverage/core fields and a small number of figure-derived fields.
        if len(fields) > self.target_max:
            before = len(fields)
            fields.sort(
                key=lambda f: (
                    {"core": 4, "rare_important": 3, "common": 2}.get(f.importance, 1),
                    int(f.coverage or 0),
                    bool(f.from_figure),
                    len(f.description or "") + len(f.extraction_hint or ""),
                ),
                reverse=True,
            )
            kept = fields[:self.target_max]

            # Preserve at least a few figure/table-derived fields when available.
            fig_fields = [f for f in fields if f.from_figure]
            min_fig = min(3, len(fig_fields), self.target_max)
            if min_fig:
                kept_keys = {f.normalized_key() for f in kept}
                missing_figs = [f for f in fig_fields if f.normalized_key() not in kept_keys]
                for fig in missing_figs[:min_fig]:
                    non_fig_idx = next((i for i in range(len(kept) - 1, -1, -1) if not kept[i].from_figure), None)
                    if non_fig_idx is not None:
                        kept[non_fig_idx] = fig
                        kept_keys.add(fig.normalized_key())
            fields = kept
            notes.append(f"字段数过多，按 importance/coverage/from_figure 裁剪: {before} -> {len(fields)}")

        schema.fields = fields
        return schema, notes

    # ---- 入口 ----
    def discover(self, paper_ids: List[str]) -> GeneratedSchema:
        sample = select_sample(paper_ids, self.sample_size, collection=self.collection)
        used = [pid for pid in sample if load_paper_text(pid, collection=self.collection)]
        if not used:
            raise RuntimeError("没有可读取正文的样本论文，无法设计 schema")
        paper_context = build_schema_context_for_papers(
            used, budget_per_paper=self.excerpt_budget, collection=self.collection
        )
        self.logger.info(
            f"schema 设计样本 {len(used)} 篇；schema agents={self.schema_agent_roles}；"
            f"context_chars={len(paper_context)}"
        )

        drafts: List[GeneratedSchema] = []
        trace_drafts: List[Dict[str, Any]] = []
        workers = max(1, min(len(self.schema_agent_roles), 8))
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {
                ex.submit(self._draft_schema_with_agent, role, paper_context): role
                for role in self.schema_agent_roles
            }
            for fut in as_completed(futures):
                role = futures[fut]
                try:
                    draft = fut.result()
                except Exception as e:  # noqa: BLE001
                    self.logger.warning(f"[{role}] schema 草案异常: {e}")
                    draft = None
                if not draft:
                    continue
                setattr(draft, "agent_role", role)
                drafts.append(draft)
                trace_drafts.append({
                    "role": role,
                    "model": self._client(role).config.model,
                    "field_count": len(draft.fields),
                    "record_definition": draft.record_definition,
                })
                self.logger.info(f"  [{role}] schema 草案字段 {len(draft.fields)}")

        if not drafts:
            raise RuntimeError("没有任何 schema agent 产出完整 schema")

        merged = self._merge_schema_drafts(drafts)
        self.logger.info(f"schema 合并草稿: {len(merged.fields)} 字段，开始审阅...")

        final = self._review_schema(merged)
        final_before_repair = final.to_dict()
        # 完整 schema 流程没有候选池，用各草案字段展平作为 deterministic repair 的补充来源。
        repair_candidates = []
        for d in drafts:
            for f in d.fields:
                repair_candidates.append(f.to_dict())
        final, repair_notes = self._repair_schema(final, repair_candidates)
        final.source_papers = used
        final.model = self._client(self.schema_reviewer_role).config.model
        final.discovery_trace = {
            "pipeline": "schema_draft_merge_review",
            "collection": self.collection,
            "sample_size_requested": self.sample_size,
            "sample_papers_selected": sample,
            "source_papers_used": used,
            "paper_context_chars": len(paper_context),
            "schema_agent_roles": self.schema_agent_roles,
            "schema_merger_role": self.schema_merger_role,
            "schema_reviewer_role": self.schema_reviewer_role,
            "schema_drafts": trace_drafts,
            "merged_schema": merged.to_dict(),
            "final_before_repair": final_before_repair,
            "repair_notes": repair_notes,
        }

        errors = validate_schema(final, min_fields=self.target_min, max_fields=self.target_max)
        if errors:
            self.logger.warning(f"schema 校验警告: {errors}")
        if repair_notes:
            self.logger.info(f"schema 自动修复: {repair_notes}")
        figs = sum(1 for f in final.fields if f.from_figure)
        self.logger.info(f"最终 schema: {len(final.fields)} 字段(其中图表派生 {figs} 个)")
        return final
