"""
自动生成 schema 的数据模型与校验。

新架构：不再使用固定的12表结构，而是由 LLM 依据「领域简介」+ 若干论文
自动设计出**单一大表**的字段集合。一个 schema = 一组扁平字段 + 记录定义。
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import re


VALID_TYPES = {"string", "number", "boolean", "enum", "list"}
VALID_IMPORTANCE = {"core", "common", "rare_important"}


def slugify(text: str) -> str:
    """把领域名/描述转成文件名安全的 slug。"""
    text = (text or "").strip().lower()
    # 保留中英文与数字，其余转连字符
    text = re.sub(r"[^\w\u4e00-\u9fff]+", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:60] or "schema"


def normalize_field_name(name: str) -> str:
    """字段名归一化键（用于跨论文去重）。"""
    n = (name or "").strip().lower()
    n = re.sub(r"[\s\-/]+", "_", n)
    n = re.sub(r"[^\w\u4e00-\u9fff]+", "", n)
    return n


@dataclass
class SchemaField:
    """单个字段定义。"""
    name: str
    type: str = "string"
    description: str = ""
    extraction_hint: str = ""
    unit: Optional[str] = None
    enum_values: Optional[List[str]] = None
    importance: str = "common"
    coverage: int = 0  # 多少篇样本论文独立提到该字段
    from_figure: bool = False  # 该字段是否主要来自图/表征（图注作为证据来源）

    def normalized_key(self) -> str:
        return normalize_field_name(self.name)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        # 清理空 enum
        if not d.get("enum_values"):
            d["enum_values"] = None
        return d

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "SchemaField":
        ftype = str(d.get("type", "string")).strip().lower()
        if ftype not in VALID_TYPES:
            ftype = "string"
        importance = str(d.get("importance", "common")).strip().lower()
        if importance not in VALID_IMPORTANCE:
            importance = "common"
        enum_values = d.get("enum_values") or None
        if enum_values and not isinstance(enum_values, list):
            enum_values = None
        unit = d.get("unit")
        if unit in ("", "null", "none", "N/A"):
            unit = None
        return cls(
            name=str(d.get("name", "")).strip(),
            type=ftype,
            description=str(d.get("description", "")).strip(),
            extraction_hint=str(d.get("extraction_hint", "")).strip(),
            unit=unit,
            enum_values=enum_values,
            importance=importance,
            coverage=int(d.get("coverage", 0) or 0),
            from_figure=bool(d.get("from_figure", False)),
        )


@dataclass
class GeneratedSchema:
    """一份自动生成的 schema（单一大表）。"""
    domain: str
    description: str
    fields: List[SchemaField] = field(default_factory=list)
    record_definition: str = ""
    slug: str = ""
    schema_version: str = "auto-1"
    model: str = ""
    source_papers: List[str] = field(default_factory=list)
    generated_at: str = ""

    def __post_init__(self):
        if not self.slug:
            self.slug = slugify(self.domain or self.description)

    def field_names(self) -> List[str]:
        return [f.name for f in self.fields]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schema_version": self.schema_version,
            "slug": self.slug,
            "domain": self.domain,
            "description": self.description,
            "record_definition": self.record_definition,
            "model": self.model,
            "generated_at": self.generated_at,
            "source_papers": self.source_papers,
            "field_count": len(self.fields),
            "fields": [f.to_dict() for f in self.fields],
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GeneratedSchema":
        fields = [SchemaField.from_dict(x) for x in d.get("fields", [])]
        return cls(
            domain=d.get("domain", ""),
            description=d.get("description", ""),
            fields=fields,
            record_definition=d.get("record_definition", ""),
            slug=d.get("slug", ""),
            schema_version=d.get("schema_version", "auto-1"),
            model=d.get("model", ""),
            source_papers=d.get("source_papers", []),
            generated_at=d.get("generated_at", ""),
        )


def validate_schema(schema: GeneratedSchema, min_fields: int = 5, max_fields: int = 80) -> List[str]:
    """
    校验生成的 schema，返回错误列表（空列表表示通过）。
    """
    errors: List[str] = []
    if not schema.domain and not schema.description:
        errors.append("domain/description 均为空")
    if not schema.fields:
        errors.append("fields 为空")
    if len(schema.fields) < min_fields:
        errors.append(f"字段数过少: {len(schema.fields)} < {min_fields}")
    if len(schema.fields) > max_fields:
        errors.append(f"字段数过多: {len(schema.fields)} > {max_fields}")

    seen = set()
    for f in schema.fields:
        if not f.name:
            errors.append("存在空字段名")
            continue
        key = f.normalized_key()
        if key in seen:
            errors.append(f"重复字段: {f.name}")
        seen.add(key)
        if f.type not in VALID_TYPES:
            errors.append(f"字段 {f.name} 类型非法: {f.type}")
        if f.type == "enum" and not f.enum_values:
            errors.append(f"枚举字段 {f.name} 缺少 enum_values")
    return errors
