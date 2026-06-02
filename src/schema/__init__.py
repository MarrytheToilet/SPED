"""
src.schema — LLM 自动设计的单表 schema：发现、存储、数据模型。
"""
from .models import GeneratedSchema, SchemaField, validate_schema, slugify
from .store import SchemaStore
from .discovery import SchemaDiscovery

__all__ = [
    "GeneratedSchema",
    "SchemaField",
    "validate_schema",
    "slugify",
    "SchemaStore",
    "SchemaDiscovery",
]
