"""
schema 设计 + 扁平提取的确定性单元测试（不依赖真实 LLM）。
运行: python -m pytest tests/test_schema_flat.py -q
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.llm.base import LLMClient, LLMConfig, LLMResponse
from src.schema.models import GeneratedSchema, SchemaField, validate_schema
from src.schema.discovery import SchemaDiscovery
from src.schema.sampling import build_excerpt
from src.prompts.modes.flat_mode import GenericFlatMode, MultiAgentFlatMode


class FakeLLM(LLMClient):
    """按 call_id 前缀返回预置 JSON 的假客户端。"""

    def __init__(self, responses):
        cfg = LLMConfig(model="fake", provider="fake", api_key="x", api_base="x")
        super().__init__(cfg)
        self.responses = responses
        self.calls = []

    def _do_call(self, messages, **kwargs):
        return LLMResponse(success=True, content="{}")

    def call(self, messages, call_id="unknown", **kwargs):
        self.calls.append(call_id)
        for prefix, payload in self.responses.items():
            if call_id.startswith(prefix):
                content = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
                return LLMResponse(success=True, content=content, finish_reason="stop")
        return LLMResponse(success=True, content="{}", finish_reason="stop")


def test_build_excerpt_budget():
    text = "A" * 50000
    out = build_excerpt(text, budget=5000)
    assert len(out) <= 5200  # 含分隔符的小冗余
    short = "hello"
    assert build_excerpt(short, 5000) == short


def test_validate_schema_field_count():
    schema = GeneratedSchema(domain="d", description="x", fields=[
        SchemaField(name="a"), SchemaField(name="b"),
    ])
    errs = validate_schema(schema, min_fields=5)
    assert any("过少" in e for e in errs)


def test_validate_schema_duplicate_and_enum():
    schema = GeneratedSchema(domain="d", description="x", fields=[
        SchemaField(name="mat"), SchemaField(name="MAT"),
        SchemaField(name="kind", type="enum", enum_values=None),
    ])
    errs = validate_schema(schema, min_fields=1)
    assert any("重复" in e for e in errs)
    assert any("枚举" in e for e in errs)


def test_generated_schema_keeps_discovery_trace():
    schema = GeneratedSchema(
        domain="d",
        description="x",
        fields=[SchemaField(name="a")],
        discovery_trace={"source_papers_used": ["p1"], "repair_notes": ["ok"]},
    )
    loaded = GeneratedSchema.from_dict(schema.to_dict())
    assert loaded.discovery_trace["source_papers_used"] == ["p1"]
    assert loaded.discovery_trace["repair_notes"] == ["ok"]


def test_generated_schema_keeps_extraction_format():
    schema = GeneratedSchema(
        domain="d",
        description="x",
        fields=[SchemaField(name="a")],
        extraction_format='{"records":[...]}',
    )
    loaded = GeneratedSchema.from_dict(schema.to_dict())
    assert loaded.extraction_format == '{"records":[...]}'


def test_repair_schema_dedup_enum_and_fill_candidates():
    disc = SchemaDiscovery(domain="d", description="x", target_min=3, target_max=5)
    schema = GeneratedSchema(domain="d", description="x", fields=[
        SchemaField(name="metric", type="enum", enum_values=None, description="short"),
        SchemaField(name="Metric", type="number", coverage=2, description="better"),
    ])
    candidates = [
        {"name": "object_name", "type": "string", "coverage": 3, "description": "研究对象"},
        {"name": "condition", "type": "string", "coverage": 2, "description": "实验条件"},
    ]
    repaired, notes = disc._repair_schema(schema, candidates)
    assert repaired.record_definition
    assert len(repaired.fields) == 3
    assert len({f.normalized_key() for f in repaired.fields}) == 3
    assert any("合并重复字段" in n for n in notes)
    assert any(f.name == "object_name" for f in repaired.fields)


def test_schema_discovery_full_schema_agents(monkeypatch, tmp_path):
    paper_dir = tmp_path / "p1"
    paper_dir.mkdir()
    (paper_dir / "full.md").write_text(
        "# Abstract\nMaterial A was tested.\n# Introduction\nStudy intro.\n# Experimental\nLoad was 1 N.",
        encoding="utf-8",
    )
    agent_schema = {
        "record_definition": "一种材料一次实验",
        "fields": [
            {"name": "material", "type": "string", "importance": "core", "description": "材料"},
            {"name": "load", "type": "number", "unit": "N", "importance": "core", "description": "载荷"},
        ],
        "extraction_format": "records with value/evidence",
    }
    merged_schema = {
        "record_definition": "一种材料在一组条件下的一次实验",
        "fields": [
            {"name": "material", "type": "string", "importance": "core", "description": "材料"},
            {"name": "load", "type": "number", "unit": "N", "importance": "core", "description": "载荷"},
            {"name": "result", "type": "string", "importance": "common", "description": "结果"},
        ],
        "extraction_format": "records array; each field has value/evidence",
    }
    reviewed_schema = {
        "record_definition": "一种材料在一组条件下的一次实验",
        "fields": merged_schema["fields"],
        "extraction_format": "records array; each field has value/evidence",
    }
    fake = FakeLLM({
        "schema_draft": agent_schema,
        "schema_merge": merged_schema,
        "schema_review": reviewed_schema,
    })
    disc = SchemaDiscovery(
        domain="d",
        description="x",
        sample_size=1,
        target_min=1,
        target_max=5,
        schema_agent_roles=["schema_agent_a", "schema_agent_b", "schema_agent_c"],
    )
    disc._clients = {
        "schema_agent_a": fake,
        "schema_agent_b": fake,
        "schema_agent_c": fake,
        "schema_merger": fake,
        "schema_reviewer": fake,
    }
    monkeypatch.setattr(
        "src.schema.discovery.load_paper_text",
        lambda pid, collection=None: (paper_dir / "full.md").read_text(encoding="utf-8"),
    )
    monkeypatch.setattr(
        "src.schema.discovery.build_schema_context_for_papers",
        lambda paper_ids, budget_per_paper, collection=None: (paper_dir / "full.md").read_text(encoding="utf-8"),
    )
    schema = disc.discover(["p1"])
    assert len(schema.fields) == 3
    assert schema.extraction_format
    assert schema.discovery_trace["pipeline"] == "schema_draft_merge_review"
    assert len(schema.discovery_trace["schema_drafts"]) == 3


def test_flat_extract_evidence_rules():
    source = "The UHMWPE liner showed a wear rate of 5.2 mm3/Nm under 1 MPa contact pressure."
    schema = GeneratedSchema(domain="人工关节", description="摩擦学", fields=[
        SchemaField(name="material", type="string"),
        SchemaField(name="wear_rate", type="number", unit="mm3/Nm"),
        SchemaField(name="missing_field", type="string"),
    ])
    llm_out = {"records": [{
        "material": {"value": "UHMWPE", "evidence": "The UHMWPE liner showed"},
        "wear_rate": {"value": 5.2, "evidence": "wear rate of 5.2 mm3/Nm"},
        "missing_field": {"value": None, "evidence": None},
        "fabricated": {"value": "X", "evidence": "not in source at all zzz"},
    }]}
    fake = FakeLLM({"flat_extract": llm_out})
    mode = GenericFlatMode(fake, schema)
    res = mode.extract("p1", source)
    assert res.success and res.count == 1
    rec = res.records[0]
    # 非空字段带 evidence 与校验标记
    assert rec["material"]["evidence_verified"] is True
    assert rec["wear_rate"]["evidence_verified"] is True
    # 空字段 evidence=None
    assert rec["missing_field"]["value"] is None
    assert rec["missing_field"]["evidence"] is None
    # 编造 evidence 被标记 unverified
    assert rec["fabricated"]["evidence_verified"] is False
    assert res.metadata["evidence_unverified"] >= 1


def test_flat_extract_scalar_cells():
    source = "Material is Ti6Al4V."
    schema = GeneratedSchema(domain="d", description="x", fields=[SchemaField(name="material")])
    llm_out = {"records": [{"material": "Ti6Al4V"}]}
    fake = FakeLLM({"flat_extract": llm_out})
    mode = GenericFlatMode(fake, schema)
    res = mode.extract("p1", source)
    assert res.records[0]["material"]["value"] == "Ti6Al4V"


def test_multi_agent_flat_extract_merges_candidates():
    source = "Material is Ti6Al4V. Wear rate was 1.2 mm3/Nm."
    schema = GeneratedSchema(domain="d", description="x", fields=[
        SchemaField(name="material", type="string"),
        SchemaField(name="wear_rate", type="number", unit="mm3/Nm"),
    ])
    a = FakeLLM({"flat_extract": {"records": [{
        "material": {"value": "Ti6Al4V", "evidence": "Material is Ti6Al4V"}
    }]}})
    b = FakeLLM({"flat_extract": {"records": [{
        "wear_rate": {"value": 1.2, "evidence": "Wear rate was 1.2 mm3/Nm"}
    }]}})
    merger = FakeLLM({"flat_merge": {"records": [{
        "material": {"value": "Ti6Al4V", "evidence": "Material is Ti6Al4V"},
        "wear_rate": {"value": 1.2, "evidence": "Wear rate was 1.2 mm3/Nm"},
    }]}})
    mode = MultiAgentFlatMode({"extractor_a": a, "extractor_b": b}, merger, schema)
    res = mode.extract("p1", source)
    assert res.success
    assert res.count == 1
    assert res.records[0]["material"]["value"] == "Ti6Al4V"
    assert res.records[0]["wear_rate"]["value"] == 1.2
    assert res.metadata["merge_used"] is True
    assert res.metadata["successful_agents"] == ["extractor_a", "extractor_b"]


def test_multi_agent_flat_extract_reviews_merged_records():
    source = "Material is Ti6Al4V. Wear rate was 1.2 mm3/Nm."
    schema = GeneratedSchema(domain="d", description="x", fields=[
        SchemaField(name="material", type="string"),
        SchemaField(name="wear_rate", type="number", unit="mm3/Nm"),
    ])
    a = FakeLLM({"flat_extract": {"records": [{
        "material": {"value": "Ti6Al4V", "evidence": "Material is Ti6Al4V"}
    }]}})
    b = FakeLLM({"flat_extract": {"records": [{
        "wear_rate": {"value": 1.2, "evidence": "Wear rate was 1.2 mm3/Nm"}
    }]}})
    merger = FakeLLM({"flat_merge": {"records": [{
        "material": {"value": "Ti6Al4V", "evidence": "Material is Ti6Al4V"},
        "wear_rate": {"value": 1.2, "evidence": "Wear rate was 1.2 mm3/Nm"},
    }]}})
    reviewer = FakeLLM({"flat_review": {
        "records": [{
            "material": {"value": "Ti6Al4V", "evidence": "Material is Ti6Al4V"},
            "wear_rate": {"value": 1.2, "evidence": "Wear rate was 1.2 mm3/Nm"},
        }],
        "review": {"passed": True, "issues": []},
    }})
    mode = MultiAgentFlatMode(
        {"extractor_a": a, "extractor_b": b},
        merger,
        schema,
        reviewer_client=reviewer,
    )
    res = mode.extract("p1", source)
    assert res.success
    assert res.metadata["review_used"] is True
    assert res.metadata["review"]["passed"] is True
    assert res.metadata["evidence_verified"] == 2


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
