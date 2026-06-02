#!/usr/bin/env python3
"""
论文目录（Paper Catalog）- 全流程统一事实来源

把「PDF 上传 → MinerU 解析 → 数据提取 → 入库」四个阶段的状态汇总到一张
`papers` 表，方便统一查看「哪些 PDF 已经解析过、解析/提取/入库到了哪一步」。

设计要点：
- 表存放在与 PDFProcessor 共用的 `data/uploads/pdf_state.db` 中，避免多库之间
  的非原子双重记账。旧表（pdf_files/batches/download_records）保持不变。
- paper_id 沿用「解析目录名 / 提取 JSON 文件名（stem）」，与已有的 ~1700 份
  提取结果及入库 `论文ID` 保持兼容；另用 file_hash 作为稳定身份标识。
- 提供 backfill：从现有 parsed/ 与 extracted/ 目录回填，兼容仅解析、仅提取、
  两者皆有等多种情况。
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from loguru import logger

import settings


# 解析阶段状态
PARSE_PENDING = "pending"
PARSE_UPLOADED = "uploaded"
PARSE_PROCESSING = "processing"
PARSE_PARSED = "parsed"
PARSE_FAILED = "failed"

# 提取阶段状态
EXTRACT_NONE = "none"
EXTRACT_DONE = "done"
EXTRACT_FAILED = "failed"
EXTRACT_TOO_LARGE = "too_large"


class PaperCatalog:
    """论文目录管理器 - 统一查看与更新全流程状态"""

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            db_path = Path(settings.UPLOADS_DIR) / "pdf_state.db"
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(module="PaperCatalog")
        self._init_db()

    # ------------------------------------------------------------------
    # 初始化
    # ------------------------------------------------------------------
    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        conn = self._connect()
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS papers (
                    paper_id        TEXT PRIMARY KEY,
                    source_pdf      TEXT,
                    file_hash       TEXT,
                    file_size       INTEGER,
                    batch_id        TEXT,
                    mineru_data_id  TEXT,
                    parse_status    TEXT DEFAULT 'pending',
                    parsed_dir      TEXT,
                    has_full_md     INTEGER DEFAULT 0,
                    char_count      INTEGER DEFAULT 0,
                    extract_status  TEXT DEFAULT 'none',
                    extract_json    TEXT,
                    extract_count   INTEGER DEFAULT 0,
                    imported        INTEGER DEFAULT 0,
                    error           TEXT,
                    created_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at      TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_papers_parse ON papers(parse_status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_papers_extract ON papers(extract_status)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_papers_hash ON papers(file_hash)"
            )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 基础读写
    # ------------------------------------------------------------------
    def get(self, paper_id: str) -> Optional[Dict[str, Any]]:
        conn = self._connect()
        try:
            row = conn.execute(
                "SELECT * FROM papers WHERE paper_id = ?", (paper_id,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def upsert(self, paper_id: str, **fields) -> None:
        """插入或更新一条论文记录（仅更新提供的字段）"""
        if not paper_id:
            raise ValueError("paper_id 不能为空")

        allowed = {
            "source_pdf", "file_hash", "file_size", "batch_id", "mineru_data_id",
            "parse_status", "parsed_dir", "has_full_md", "char_count",
            "extract_status", "extract_json", "extract_count", "imported", "error",
        }
        fields = {k: v for k, v in fields.items() if k in allowed and v is not None}

        conn = self._connect()
        try:
            exists = conn.execute(
                "SELECT 1 FROM papers WHERE paper_id = ?", (paper_id,)
            ).fetchone()

            if exists:
                if fields:
                    sets = ", ".join(f"{k} = ?" for k in fields)
                    params = list(fields.values()) + [paper_id]
                    conn.execute(
                        f"UPDATE papers SET {sets}, updated_at = CURRENT_TIMESTAMP "
                        f"WHERE paper_id = ?",
                        params,
                    )
            else:
                cols = ["paper_id"] + list(fields.keys())
                placeholders = ", ".join("?" for _ in cols)
                params = [paper_id] + list(fields.values())
                conn.execute(
                    f"INSERT INTO papers ({', '.join(cols)}) VALUES ({placeholders})",
                    params,
                )
            conn.commit()
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 阶段状态更新（语义化封装）
    # ------------------------------------------------------------------
    def mark_uploaded(self, paper_id: str, batch_id: str = None,
                      mineru_data_id: str = None, source_pdf: str = None,
                      file_hash: str = None, file_size: int = None) -> None:
        self.upsert(
            paper_id,
            parse_status=PARSE_UPLOADED,
            batch_id=batch_id,
            mineru_data_id=mineru_data_id,
            source_pdf=source_pdf,
            file_hash=file_hash,
            file_size=file_size,
        )

    def mark_parsed(self, paper_id: str, parsed_dir: str, char_count: int,
                    batch_id: str = None, mineru_data_id: str = None,
                    source_pdf: str = None) -> None:
        self.upsert(
            paper_id,
            parse_status=PARSE_PARSED,
            parsed_dir=str(parsed_dir),
            has_full_md=1,
            char_count=char_count,
            batch_id=batch_id,
            mineru_data_id=mineru_data_id,
            source_pdf=source_pdf,
        )

    def mark_parse_failed(self, paper_id: str, error: str,
                          batch_id: str = None, mineru_data_id: str = None,
                          source_pdf: str = None) -> None:
        self.upsert(
            paper_id,
            parse_status=PARSE_FAILED,
            error=error,
            batch_id=batch_id,
            mineru_data_id=mineru_data_id,
            source_pdf=source_pdf,
        )

    def mark_extracted(self, paper_id: str, extract_json: str,
                       extract_count: int) -> None:
        self.upsert(
            paper_id,
            extract_status=EXTRACT_DONE,
            extract_json=str(extract_json),
            extract_count=extract_count,
        )

    def mark_extract_failed(self, paper_id: str, error: str,
                            status: str = EXTRACT_FAILED) -> None:
        self.upsert(paper_id, extract_status=status, error=error)

    def mark_imported(self, paper_id: str, imported: bool = True) -> None:
        self.upsert(paper_id, imported=1 if imported else 0)

    # ------------------------------------------------------------------
    # 查询
    # ------------------------------------------------------------------
    def list_papers(
        self,
        parse_status: Optional[str] = None,
        extract_status: Optional[str] = None,
        imported: Optional[bool] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        clauses = []
        params: List[Any] = []
        if parse_status is not None:
            clauses.append("parse_status = ?")
            params.append(parse_status)
        if extract_status is not None:
            clauses.append("extract_status = ?")
            params.append(extract_status)
        if imported is not None:
            clauses.append("imported = ?")
            params.append(1 if imported else 0)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        sql = f"SELECT * FROM papers {where} ORDER BY updated_at DESC"
        if limit:
            sql += f" LIMIT {int(limit)}"

        conn = self._connect()
        try:
            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def stats(self) -> Dict[str, Any]:
        conn = self._connect()
        try:
            def scalar(sql, params=()):
                return conn.execute(sql, params).fetchone()[0]

            total = scalar("SELECT COUNT(*) FROM papers")
            parsed = scalar(
                "SELECT COUNT(*) FROM papers WHERE parse_status = ?", (PARSE_PARSED,)
            )
            parse_failed = scalar(
                "SELECT COUNT(*) FROM papers WHERE parse_status = ?", (PARSE_FAILED,)
            )
            extracted = scalar(
                "SELECT COUNT(*) FROM papers WHERE extract_status = ?", (EXTRACT_DONE,)
            )
            extract_failed = scalar(
                "SELECT COUNT(*) FROM papers WHERE extract_status IN (?, ?)",
                (EXTRACT_FAILED, EXTRACT_TOO_LARGE),
            )
            imported = scalar("SELECT COUNT(*) FROM papers WHERE imported = 1")
            pending_extract = scalar(
                "SELECT COUNT(*) FROM papers WHERE parse_status = ? "
                "AND extract_status != ?",
                (PARSE_PARSED, EXTRACT_DONE),
            )
            return {
                "total": total,
                "parsed": parsed,
                "parse_failed": parse_failed,
                "extracted": extracted,
                "extract_failed": extract_failed,
                "imported": imported,
                "pending_extract": pending_extract,
            }
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # 回填（从现有目录重建目录表）
    # ------------------------------------------------------------------
    def _download_record_index(self) -> Dict[str, Dict[str, Any]]:
        """读取 download_records，建立 parsed_dir(basename) -> 来源信息 的索引"""
        index: Dict[str, Dict[str, Any]] = {}
        conn = self._connect()
        try:
            # download_records 与 papers 共库，但表可能不存在（独立使用 catalog 时）
            try:
                rows = conn.execute(
                    "SELECT batch_id, data_id, filename, output_path "
                    "FROM download_records WHERE download_status = 'completed'"
                ).fetchall()
            except sqlite3.OperationalError:
                return index

            for r in rows:
                output_path = r["output_path"] or ""
                key = Path(output_path).name
                if key:
                    index[key] = {
                        "batch_id": r["batch_id"],
                        "mineru_data_id": r["data_id"],
                        "source_pdf": r["filename"],
                    }
            return index
        finally:
            conn.close()

    def backfill(
        self,
        parsed_dir: Optional[Path] = None,
        extracted_dir: Optional[Path] = None,
    ) -> Dict[str, int]:
        """
        从现有 parsed/ 和 extracted/ 目录回填 papers 表。

        覆盖以下情况：仅解析、仅提取、两者皆有。
        """
        parsed_root = Path(parsed_dir or settings.PARSED_DIR)
        extracted_root = Path(extracted_dir or settings.EXTRACTED_DIR)

        dl_index = self._download_record_index()
        stats = {"parsed": 0, "extracted": 0}

        # 1. 解析目录
        if parsed_root.exists():
            for d in sorted(parsed_root.iterdir()):
                if not d.is_dir():
                    continue
                paper_id = d.name
                full_md = d / "full.md"
                has_md = full_md.exists() and full_md.stat().st_size > 0
                char_count = 0
                if has_md:
                    try:
                        char_count = len(full_md.read_text(encoding="utf-8"))
                    except Exception:
                        char_count = full_md.stat().st_size

                src = dl_index.get(paper_id, {})
                if has_md:
                    self.mark_parsed(
                        paper_id,
                        parsed_dir=str(d),
                        char_count=char_count,
                        batch_id=src.get("batch_id"),
                        mineru_data_id=src.get("mineru_data_id"),
                        source_pdf=src.get("source_pdf"),
                    )
                else:
                    self.mark_parse_failed(
                        paper_id,
                        error="解析目录缺少有效的 full.md",
                        batch_id=src.get("batch_id"),
                        mineru_data_id=src.get("mineru_data_id"),
                        source_pdf=src.get("source_pdf"),
                    )
                stats["parsed"] += 1

        # 2. 提取结果
        if extracted_root.exists():
            for jf in sorted(extracted_root.glob("*.json")):
                paper_id = jf.stem
                count = 0
                try:
                    data = json.loads(jf.read_text(encoding="utf-8"))
                    count = int(data.get("count", len(data.get("records", []))))
                except Exception as e:
                    self.logger.warning(f"读取提取结果失败 {jf.name}: {e}")
                self.mark_extracted(paper_id, extract_json=str(jf), extract_count=count)
                stats["extracted"] += 1

        self.logger.info(
            f"回填完成: 解析目录 {stats['parsed']} 个, 提取结果 {stats['extracted']} 个"
        )
        return stats
