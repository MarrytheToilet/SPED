"""
生成 schema 的存储：保存/加载/列出 data_schema/generated/<slug>.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import List, Optional

from loguru import logger

from .models import GeneratedSchema


def _generated_dir() -> Path:
    try:
        import settings
        base = Path(settings.SCHEMA_DIR)
    except Exception:
        base = Path(__file__).parent.parent.parent / "data_schema"
    d = base / "generated"
    d.mkdir(parents=True, exist_ok=True)
    return d


class SchemaStore:
    """生成 schema 的文件存储。"""

    def __init__(self, directory: Optional[Path] = None):
        self.dir = Path(directory) if directory else _generated_dir()
        self.dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(module="SchemaStore")

    def path_for(self, slug: str) -> Path:
        return self.dir / f"{slug}.json"

    def save(self, schema: GeneratedSchema) -> Path:
        path = self.path_for(schema.slug)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(schema.to_dict(), f, ensure_ascii=False, indent=2)
        self.logger.info(f"已保存 schema: {path} ({len(schema.fields)} 字段)")
        return path

    def load(self, slug: str) -> GeneratedSchema:
        path = self.path_for(slug)
        if not path.exists():
            raise FileNotFoundError(f"schema 不存在: {path}")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GeneratedSchema.from_dict(data)

    def load_path(self, path: Path) -> GeneratedSchema:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return GeneratedSchema.from_dict(data)

    def list_slugs(self) -> List[str]:
        return sorted(p.stem for p in self.dir.glob("*.json"))

    def list_schemas(self) -> List[GeneratedSchema]:
        out = []
        for p in sorted(self.dir.glob("*.json")):
            try:
                out.append(self.load_path(p))
            except Exception as e:
                self.logger.warning(f"加载 schema 失败 {p}: {e}")
        return out
