"""
Schema 自动设计引擎（多agent协作）。

流程：
  1. 选取多样化样本论文（按体量分层）。
  2. 提议阶段(proposers)：把样本论文轮转分配给多个「提议者」角色
     （可配置为不同家族的模型，观点更多样），每个提议者读单篇论文+图注，
     提出候选字段；按规范化名统计 coverage(被多少篇独立提出)。
  3. 整合阶段(consolidator)：把候选字段合并为一张统一单表 schema 草稿。
  4. 评审阶段(critic)：审查草稿(查漏/去冗/控字段数/保留图表派生字段)，定稿。

各角色端点由 settings.get_agent_config(role) 决定，默认全部回退到基础 DeepSeek。
"""
from __future__ import annotations

import datetime
import json as _json
from typing import Dict, List, Optional

from loguru import logger

from ..llm.base import LLMClient, LLMMessage
from ..llm.factory import create_llm_client_for_agent
from ._json import parse_json_loose
from .models import GeneratedSchema, SchemaField, normalize_field_name, validate_schema
from .sampling import build_excerpt, collect_figures, load_paper_text, select_sample
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
        proposer_roles: List[str] = None,
        consolidator_role: str = "consolidator",
        critic_role: str = "critic",
    ):
        import settings
        self.domain = domain
        self.description = description or domain
        self.sample_size = sample_size or getattr(settings, "SCHEMA_SAMPLE_SIZE", 8)
        self.excerpt_budget = excerpt_budget or getattr(settings, "SCHEMA_EXCERPT_BUDGET", 16000)
        self.target_min = target_min or getattr(settings, "SCHEMA_MIN_FIELDS", 20)
        self.target_max = target_max or getattr(settings, "SCHEMA_MAX_FIELDS", 80)
        self.proposer_roles = proposer_roles or getattr(
            settings, "SCHEMA_PROPOSER_ROLES", ["proposer_a", "proposer_b", "proposer_c"]
        )
        self.consolidator_role = consolidator_role
        self.critic_role = critic_role
        self.logger = logger.bind(module="SchemaDiscovery")
        self._clients: Dict[str, LLMClient] = {}

    def _client(self, role: str) -> LLMClient:
        if role not in self._clients:
            self._clients[role] = create_llm_client_for_agent(role)
        return self._clients[role]

    # ---- 提议 ----
    def _propose_for_paper(self, paper_id: str, text: str, role: str) -> List[Dict]:
        excerpt = build_excerpt(text, self.excerpt_budget)
        figures = collect_figures(text) or "（未识别到图/表标题）"
        user = P.PROPOSER_USER.format(
            description=self.description, paper_id=paper_id, excerpt=excerpt, figures=figures
        )
        messages = [
            LLMMessage(role="system", content=P.PROPOSER_SYSTEM),
            LLMMessage(role="user", content=user),
        ]
        resp = self._client(role).call(messages, call_id=f"propose_{role}_{paper_id}")
        if not resp.success:
            self.logger.warning(f"[{role}] 候选字段失败 {paper_id}: {resp.error}")
            return []
        try:
            data = parse_json_loose(resp.content)
        except ValueError as e:
            self.logger.warning(f"[{role}] 候选解析失败 {paper_id}: {e}")
            return []
        fields = data.get("fields") if isinstance(data, dict) else data
        return fields if isinstance(fields, list) else []

    def _merge_candidates(self, per_paper: List[List[Dict]]) -> List[Dict]:
        merged: Dict[str, Dict] = {}
        for fields in per_paper:
            seen = set()
            for f in fields:
                if not isinstance(f, dict):
                    continue
                name = str(f.get("name", "")).strip()
                key = normalize_field_name(name)
                if not name or not key:
                    continue
                if key not in merged:
                    merged[key] = {
                        "name": name,
                        "type": f.get("type", "string"),
                        "unit": f.get("unit"),
                        "enum_values": f.get("enum_values"),
                        "description": f.get("description", ""),
                        "extraction_hint": f.get("extraction_hint", ""),
                        "from_figure": bool(f.get("from_figure", False)),
                        "coverage": 0,
                    }
                if key not in seen:
                    merged[key]["coverage"] += 1
                    seen.add(key)
                if not merged[key].get("description") and f.get("description"):
                    merged[key]["description"] = f.get("description")
                if f.get("from_figure"):
                    merged[key]["from_figure"] = True
        return sorted(merged.values(), key=lambda x: x["coverage"], reverse=True)

    # ---- 整合 + 评审 ----
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
            generated_at=datetime.datetime.now().isoformat(timespec="seconds"),
        )

    def _consolidate(self, candidates: List[Dict]) -> GeneratedSchema:
        system = P.CONSOLIDATOR_SYSTEM.format(min=self.target_min, max=self.target_max)
        user = P.CONSOLIDATOR_USER.format(
            description=self.description,
            candidates=_json.dumps(candidates, ensure_ascii=False),
            min=self.target_min, max=self.target_max,
        )
        messages = [LLMMessage(role="system", content=system),
                    LLMMessage(role="user", content=user)]
        resp = self._client(self.consolidator_role).call(messages, call_id="schema_consolidate")
        if not resp.success:
            raise RuntimeError(f"整合 schema 失败: {resp.error}")
        data = parse_json_loose(resp.content)
        if not isinstance(data, dict):
            raise RuntimeError("整合返回非对象")
        return self._schema_from_json(data, candidates)

    def _critique(self, draft: GeneratedSchema, candidates: List[Dict]) -> GeneratedSchema:
        system = P.CRITIC_SYSTEM.format(min=self.target_min, max=self.target_max)
        draft_json = _json.dumps(
            {"record_definition": draft.record_definition,
             "fields": [f.to_dict() for f in draft.fields]},
            ensure_ascii=False,
        )
        user = P.CRITIC_USER.format(
            description=self.description, draft=draft_json,
            candidates=_json.dumps(candidates, ensure_ascii=False),
            min=self.target_min, max=self.target_max,
        )
        messages = [LLMMessage(role="system", content=system),
                    LLMMessage(role="user", content=user)]
        resp = self._client(self.critic_role).call(messages, call_id="schema_critique")
        if not resp.success:
            self.logger.warning(f"评审失败，沿用草稿: {resp.error}")
            return draft
        try:
            data = parse_json_loose(resp.content)
        except ValueError as e:
            self.logger.warning(f"评审解析失败，沿用草稿: {e}")
            return draft
        if not isinstance(data, dict) or not data.get("fields"):
            return draft
        final = self._schema_from_json(data, candidates)
        # 评审若把字段删空/过少，回退草稿
        if len(final.fields) < max(self.target_min // 2, 5):
            self.logger.warning("评审结果字段过少，沿用草稿")
            return draft
        return final

    # ---- 入口 ----
    def discover(self, paper_ids: List[str]) -> GeneratedSchema:
        sample = select_sample(paper_ids, self.sample_size)
        self.logger.info(f"schema 设计样本 {len(sample)} 篇；提议角色={self.proposer_roles}")

        per_paper: List[List[Dict]] = []
        used: List[str] = []
        for i, pid in enumerate(sample):
            text = load_paper_text(pid)
            if not text:
                self.logger.warning(f"跳过无正文论文: {pid}")
                continue
            role = self.proposer_roles[i % len(self.proposer_roles)]
            fields = self._propose_for_paper(pid, text, role)
            if fields:
                per_paper.append(fields)
                used.append(pid)
            self.logger.info(f"  [{role}] {pid}: 候选字段 {len(fields)}")

        if not per_paper:
            raise RuntimeError("没有任何论文产出候选字段，无法设计 schema")

        candidates = self._merge_candidates(per_paper)
        self.logger.info(f"合并后候选字段 {len(candidates)} 个")

        draft = self._consolidate(candidates)
        self.logger.info(f"整合草稿: {len(draft.fields)} 字段，开始评审...")

        final = self._critique(draft, candidates)
        final.source_papers = used
        final.model = self._client(self.critic_role).config.model

        errors = validate_schema(final, min_fields=self.target_min, max_fields=self.target_max)
        if errors:
            self.logger.warning(f"schema 校验警告: {errors}")
        figs = sum(1 for f in final.fields if f.from_figure)
        self.logger.info(f"最终 schema: {len(final.fields)} 字段(其中图表派生 {figs} 个)")
        return final
