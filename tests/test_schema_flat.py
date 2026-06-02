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
from src.prompts.modes.flat_mode import GenericFlatMode


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


def test_discovery_coverage_and_consolidation():
    cand = {"fields": [
        {"name": "material", "type": "string", "description": "材料"},
        {"name": "hardness", "type": "number", "unit": "HV", "description": "硬度"},
    ]}
    consolidated = {"record_definition": "一种材料一次实验",
                    "fields": [
                        {"name": "material", "type": "string", "importance": "core", "description": "材料"},
                        {"name": "hardness", "type": "number", "unit": "HV", "importance": "common", "description": "硬度"},
                        {"name": "wear_rate", "type": "number", "unit": "mm3/Nm", "importance": "common", "description": "磨损率"},
                    ]}
    fake = FakeLLM({"schema_candidate": cand, "schema_consolidate": consolidated})

    disc = SchemaDiscovery(domain="人工关节", description="摩擦学", sample_size=3, target_min=1, target_max=10)
    disc._clients["consolidator"] = fake  # 注入假整合client，绕过真实端点
    # 直接喂候选，绕过文件读取
    per_paper = [cand["fields"], cand["fields"]]
    merged = disc._merge_candidates(per_paper)
    cov = {m["name"]: m["coverage"] for m in merged}
    assert cov["material"] == 2 and cov["hardness"] == 2

    schema = disc._consolidate(merged)
    assert len(schema.fields) == 3
    assert schema.record_definition
    # coverage 回填
    mat = next(f for f in schema.fields if f.name == "material")
    assert mat.coverage == 2


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


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-q"]))
