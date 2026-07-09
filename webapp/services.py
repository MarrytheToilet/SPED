"""
Web 后端业务逻辑：把解析 / 设计schema / 提取 / 数据查看封装成可被任务管理器调用的函数。
"""
from __future__ import annotations

import json
import os
import random
import shutil
import sqlite3
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import settings
from src.database.catalog import (
    PaperCatalog, PARSE_PARSED, PARSE_FAILED,
    configure_connection,
)
from src.pdfs.pdf_processor import PDFProcessor
from src.schema import SchemaDiscovery, SchemaStore, GeneratedSchema, slugify, validate_schema
from src.schema.sampling import list_parsed_papers, load_paper_text
from src.extractors import ExtractionService
from webapp.jobs import JobHandle

def _safe_collection(collection: Optional[str]) -> str:
    return settings.safe_collection_name(collection or getattr(settings, "DEFAULT_COLLECTION", ""))


def _pdf_root(collection: Optional[str] = None) -> Path:
    return settings.collection_pdf_dir(_safe_collection(collection))


def _parsed_root(collection: Optional[str] = None) -> Path:
    return settings.collection_parsed_dir(_safe_collection(collection))


def _extracted_root(collection: Optional[str] = None, slug: str = "") -> Path:
    return settings.collection_extracted_dir(_safe_collection(collection), slug)


def list_collections() -> List[Dict[str, Any]]:
    """List canonical PDF collections."""
    default = getattr(settings, "DEFAULT_COLLECTION", "")
    out = [{"name": default, "label": default, "pdf_count": len(list(_pdf_root(default).rglob("*.pdf"))) if default else 0}]
    if settings.COLLECTIONS_DIR.exists():
        for d in sorted(p for p in settings.COLLECTIONS_DIR.iterdir() if p.is_dir()):
            if d.name == default:
                out[0]["pdf_count"] = len(list((d / "pdfs").rglob("*.pdf")))
                continue
            out.append({
                "name": d.name,
                "label": d.name,
                "pdf_count": len(list((d / "pdfs").rglob("*.pdf"))),
            })
    return out


def _collection_of_relpath(rel: str) -> str:
    parts = Path(str(rel).replace("\\", "/")).parts
    return _safe_collection(parts[0] if parts else "")


def _pdf_logical_name(path: Path, collection: Optional[str] = None) -> str:
    return settings.logical_pdf_name(path, _safe_collection(collection))


def _pdf_path(name: str) -> Path:
    return settings.pdf_path_from_logical(name)


def _max_pdf_bytes() -> int:
    return int(getattr(settings, "MAX_PDF_SIZE_MB", 20)) * 1024 * 1024


def _connect_state_db(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path, timeout=30)
    conn.row_factory = sqlite3.Row
    configure_connection(conn)
    return conn


def _processing_stale_hours() -> int:
    try:
        return max(1, int(getattr(settings, "PROCESSING_STALE_HOURS", 12)))
    except (TypeError, ValueError):
        return 12

# 同一时刻只允许一个解析任务，避免重复上传浪费 MinerU 付费额度
_PARSE_LOCK = threading.Lock()
_EXTRACT_FILE_LOCKS: Dict[str, threading.Lock] = {}
_EXTRACT_FILE_LOCKS_GUARD = threading.Lock()


def parse_in_progress() -> bool:
    return _PARSE_LOCK.locked()


def _lock_for_extract(collection: str, slug: str, paper_id: str) -> threading.Lock:
    key = f"{collection}:{slug}:{paper_id}"
    with _EXTRACT_FILE_LOCKS_GUARD:
        lock = _EXTRACT_FILE_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _EXTRACT_FILE_LOCKS[key] = lock
        return lock


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}.{threading.get_ident()}")
    tmp.write_text(text, encoding="utf-8")
    os.replace(tmp, path)


def _parsed_stems(collection: Optional[str] = None) -> set:
    """磁盘上已解析（含有效 full.md）的论文目录名集合——解析状态的**真相来源**。

    即使 pdf_files / papers 跟踪库被外部流程破坏，也能据此正确识别已解析 PDF，
    避免重复上传浪费 MinerU 额度、避免界面误报为未解析。
    """
    out = set()
    collection = _safe_collection(collection)
    root = _parsed_root(collection)
    try:
        for d in root.iterdir():
            if d.is_dir():
                md = d / "full.md"
                if md.exists() and md.stat().st_size > 0:
                    out.add(d.name)
    except FileNotFoundError:
        pass
    return out


# ----------------------------------------------------------------------
# PDF 总览 / 分类
# ----------------------------------------------------------------------
def _pdf_files_status() -> Dict[str, Dict[str, Any]]:
    proc = PDFProcessor()
    out: Dict[str, Dict[str, Any]] = {}
    conn = _connect_state_db(proc.db_path)
    try:
        for r in conn.execute("SELECT filename, status, batch_id, updated_at FROM pdf_files"):
            out[r["filename"]] = {
                "status": r["status"],
                "batch_id": r["batch_id"],
                "updated_at": r["updated_at"],
            }
    finally:
        conn.close()
    return out


def _is_stale_processing(rec: Dict[str, Any], hours: Optional[int] = None) -> bool:
    if rec.get("status") != "uploaded":
        return False
    raw = rec.get("updated_at")
    if not raw:
        return False
    try:
        updated = datetime.fromisoformat(str(raw).replace("Z", "+00:00").split("+", 1)[0])
    except ValueError:
        return False
    return datetime.now() - updated > timedelta(hours=hours or _processing_stale_hours())


def mark_stale_processing_failed(collection: Optional[str] = None,
                                 hours: Optional[int] = None) -> int:
    """把长时间停留在 uploaded 的 PDF 标记为 failed，避免界面永久显示处理中。"""
    collection = _safe_collection(collection)
    cutoff = datetime.now() - timedelta(hours=hours or _processing_stale_hours())
    proc = PDFProcessor()
    conn = _connect_state_db(proc.db_path)
    try:
        rows = conn.execute(
            "SELECT filename, updated_at FROM pdf_files WHERE status='uploaded'"
        ).fetchall()
        stale = []
        for name, updated_at in rows:
            if _collection_of_relpath(name) != collection:
                continue
            try:
                updated = datetime.fromisoformat(str(updated_at).split("+", 1)[0])
            except ValueError:
                continue
            if updated < cutoff:
                stale.append((name,))
        if stale:
            conn.executemany(
                "UPDATE pdf_files SET status='failed', updated_at=CURRENT_TIMESTAMP WHERE filename=?",
                stale,
            )
            conn.commit()
        return len(stale)
    finally:
        conn.close()


def pdf_overview(collection: Optional[str] = None) -> Dict[str, Any]:
    """把 collection/pdfs 下的 PDF 分为：未解析 / 处理中 / 解析成功 / 解析失败。"""
    collection = _safe_collection(collection)
    stale_marked = mark_stale_processing_failed(collection)
    cat = PaperCatalog()
    pf = _pdf_files_status()

    failed_src = {
        (p.get("source_pdf") or "").strip(): p
        for p in cat.list_papers(parse_status=PARSE_FAILED)
        if p.get("source_pdf")
    }

    root = _pdf_root(collection)
    files = sorted(root.rglob("*.pdf"))
    items = []
    counts = {"unparsed": 0, "processing": 0, "parsed": 0, "failed": 0, "too_large": 0}
    max_bytes = _max_pdf_bytes()
    parsed_stems = _parsed_stems(collection)
    for f in files:
        try:
            name = _pdf_logical_name(f, collection)
        except ValueError:
            name = str(Path(collection) / f.name).replace("\\", "/")
        if collection and _collection_of_relpath(name) != collection:
            continue
        size = f.stat().st_size
        rec = pf.get(name, {})
        status = rec.get("status")
        stale_processing = _is_stale_processing(rec)
        oversized = size > max_bytes
        if f.stem in parsed_stems or status == "downloaded":
            cat_ = "parsed"          # 磁盘已有解析结果即视为已解析（真相来源）
        elif oversized:
            cat_ = "too_large"        # 超过体积上限，不可上传
        elif name in failed_src or status == "failed" or stale_processing:
            cat_ = "failed"
        elif status == "uploaded":
            cat_ = "processing"
        else:
            cat_ = "unparsed"
        counts[cat_] += 1
        items.append({
            "filename": name,
            "basename": f.name,
            "collection": _collection_of_relpath(name),
            "size": size,
            "size_mb": round(size / 1024 / 1024, 2),
            "category": cat_,
            "oversized": oversized,
            "stale_processing": stale_processing,
            "batch_id": rec.get("batch_id"),
            "updated_at": rec.get("updated_at"),
        })
    return {"counts": counts, "items": items, "total": len(files),
            "max_pdf_size_mb": int(getattr(settings, "MAX_PDF_SIZE_MB", 20)),
            "processing_stale_hours": _processing_stale_hours(),
            "stale_marked": stale_marked}


def delete_pdfs(filenames: Optional[List[str]] = None,
                categories: Optional[List[str]] = None,
                collection: Optional[str] = None,
                delete_files: bool = True,
                force: bool = False,
                confirm_text: str = "") -> Dict[str, Any]:
    """删除异常 PDF 及其状态记录。

    force=True 时连同 parsed 目录、各 schema 下的 extracted JSON 和 papers 状态一起清理。
    """
    collection = _safe_collection(collection)
    if (confirm_text or "").strip() != collection:
        raise ValueError(f"清理前需要输入当前主题名确认：{collection}")
    overview = pdf_overview(collection)
    items = overview["items"]
    by_name = {it["filename"]: it for it in items}
    allowed_categories = set(categories or [])
    if filenames:
        targets = [by_name[n] for n in filenames if n in by_name]
    elif allowed_categories:
        targets = [it for it in items if it["category"] in allowed_categories]
    else:
        targets = []

    deleted_files: List[str] = []
    deleted_state: List[str] = []
    deleted_parsed: List[str] = []
    deleted_extracted: List[str] = []
    skipped: List[Dict[str, str]] = []
    proc = PDFProcessor()
    parsed_root = _parsed_root(collection).resolve()

    conn = _connect_state_db(proc.db_path)
    conn.row_factory = sqlite3.Row
    try:
        for it in targets:
            name = it["filename"]
            if _collection_of_relpath(name) != collection:
                skipped.append({"filename": name, "reason": "不属于当前主题"})
                continue
            basename = Path(name).name
            safe_stem = PDFProcessor._safe_stem(basename)
            candidate_dirs = {_parsed_root(collection) / safe_stem}
            paper_ids = {safe_stem}

            for row in conn.execute(
                "SELECT paper_id, parsed_dir, extract_json FROM papers "
                "WHERE source_pdf IN (?, ?) OR paper_id IN (?, ?)",
                (name, basename, Path(name).stem, safe_stem),
            ):
                if row["paper_id"]:
                    paper_ids.add(row["paper_id"])
                if row["parsed_dir"]:
                    candidate_dirs.add(Path(row["parsed_dir"]))

            for row in conn.execute(
                "SELECT output_path FROM download_records WHERE filename IN (?, ?)",
                (name, basename),
            ):
                if row["output_path"]:
                    candidate_dirs.add(Path(row["output_path"]))

            path = _pdf_path(name)
            if delete_files and path.exists():
                path.unlink()
                deleted_files.append(name)

            if force:
                for d in sorted(candidate_dirs):
                    try:
                        d_resolved = d.resolve()
                        if d_resolved.exists() and d_resolved.is_dir() and parsed_root in d_resolved.parents:
                            shutil.rmtree(d_resolved)
                            deleted_parsed.append(str(d_resolved))
                            paper_ids.add(d_resolved.name)
                    except FileNotFoundError:
                        pass
                extracted_root = _extracted_root(collection)
                for pid in sorted(paper_ids):
                    for jf in sorted(extracted_root.rglob(f"{pid}.json")) if extracted_root.exists() else []:
                        jf.unlink()
                        deleted_extracted.append(str(jf))

            conn.execute("DELETE FROM pdf_files WHERE filename=?", (name,))
            conn.execute("DELETE FROM download_records WHERE filename IN (?, ?)", (name, basename))
            if force:
                conn.executemany(
                    "DELETE FROM papers WHERE paper_id=?",
                    [(pid,) for pid in paper_ids],
                )
            else:
                conn.execute(
                    "UPDATE papers SET source_pdf=NULL, error=NULL, updated_at=CURRENT_TIMESTAMP "
                    "WHERE source_pdf IN (?, ?) AND parse_status!='parsed'",
                    (name, basename),
                )
            deleted_state.append(name)
        conn.commit()
    finally:
        conn.close()
    with _DATA_LOCK:
        _DATA_CACHE.clear()

    return {
        "requested": len(targets),
        "deleted_files": len(deleted_files),
        "deleted_state": len(deleted_state),
        "deleted_parsed": len(deleted_parsed),
        "deleted_extracted": len(deleted_extracted),
        "skipped": skipped,
        "filenames": deleted_files,
    }


def _register_pdfs(filenames: List[str], force_reparse: bool = False,
                   collection: Optional[str] = None) -> tuple[List[Path], List[str]]:
    """把选中的 PDF 登记进 pdf_files（按 hash 去重），返回 (有效路径列表, 超限文件名列表)。

    默认跳过已成功解析(downloaded)的 PDF，避免重复消耗 MinerU 额度；
    force_reparse=True 时才会重置它们重新解析。失败(failed)的总是允许重试。
    """
    import hashlib
    proc = PDFProcessor()
    paths: List[Path] = []
    skipped_large: List[str] = []
    max_bytes = _max_pdf_bytes()
    collection = _safe_collection(collection)
    parsed_stems = _parsed_stems(collection)
    conn = _connect_state_db(proc.db_path)
    cur = conn.cursor()
    try:
        for name in filenames:
            p = _pdf_path(name)
            if not p.exists():
                continue
            if p.stat().st_size > max_bytes:
                skipped_large.append(name)   # 体积超限，拒绝上传
                continue
            if p.stem in parsed_stems and not force_reparse:
                continue  # 磁盘已有解析结果，跳过（真相来源，省额度）
            row = cur.execute(
                "SELECT status FROM pdf_files WHERE filename = ?", (name,)
            ).fetchone()
            status = row[0] if row else None
            if status == "downloaded" and not force_reparse:
                continue  # 已解析，跳过（省额度）
            if status == "uploaded" and not force_reparse:
                continue  # 正在处理中，避免重复上传
            paths.append(p)
            md5 = hashlib.md5()
            with open(p, "rb") as fh:
                for chunk in iter(lambda: fh.read(8192), b""):
                    md5.update(chunk)
            h = md5.hexdigest()
            if row is None:
                cur.execute(
                    "INSERT OR IGNORE INTO pdf_files (filename, file_hash, file_size, status) "
                    "VALUES (?, ?, ?, 'pending')",
                    (name, h, p.stat().st_size),
                )
            else:
                cur.execute(
                    "UPDATE pdf_files SET status='pending', batch_id=NULL, updated_at=CURRENT_TIMESTAMP "
                    "WHERE filename = ?",
                    (name,),
                )
        conn.commit()
    finally:
        conn.close()
    return paths, skipped_large


def run_parse_job(handle: JobHandle, filenames: List[str], force_reparse: bool = False,
                  collection: Optional[str] = None,
                  poll_interval: int = 30, max_wait_min: int = 240) -> Dict[str, Any]:
    """完整解析流水线：登记 → 上传分批 → 轮询 MinerU → 下载落盘。"""
    if not _PARSE_LOCK.acquire(blocking=False):
        raise RuntimeError("已有解析任务在运行，请等待其完成后再试")
    try:
        return _run_parse_job_locked(handle, filenames, force_reparse, collection, poll_interval, max_wait_min)
    finally:
        _PARSE_LOCK.release()


def _run_parse_job_locked(handle: JobHandle, filenames: List[str], force_reparse: bool,
                          collection: Optional[str],
                          poll_interval: int, max_wait_min: int) -> Dict[str, Any]:
    proc = PDFProcessor()
    collection = _safe_collection(collection)
    paths, skipped_large = _register_pdfs(filenames, force_reparse=force_reparse, collection=collection)
    if skipped_large:
        handle.log(f"⚠️ 跳过 {len(skipped_large)} 个超过 {settings.MAX_PDF_SIZE_MB}MB 的 PDF（不予上传）")
    if not paths:
        handle.log("所选 PDF 均已解析 / 正在处理 / 超过体积上限，无需上传")
        return {"skipped": True, "downloaded": 0, "failed": 0, "too_large": len(skipped_large)}
    handle.log(f"待解析 {len(paths)} 个 PDF")
    handle.set_progress(0, len(paths))

    # 分批上传（单批受 50 文件/分钟速率上限约束）
    rate = proc.upload_rate_per_min
    batches = proc.build_upload_batches(paths, max_files=rate)
    handle.log(f"划分为 {len(batches)} 个上传批次（限速 {rate} 文件/分钟）")
    batch_ids: List[str] = []
    conn = _connect_state_db(proc.db_path)
    try:
        row = conn.execute("SELECT MAX(batch_index) FROM batches").fetchone()
        base_index = (row[0] or 0) + 1 if row and row[0] is not None else 0
    finally:
        conn.close()
    # 滚动窗口限速：保证任意 60 秒内上传文件数不超过 rate
    from collections import deque
    window: "deque[tuple[float, int]]" = deque()
    for i, bp in enumerate(batches):
        if handle.cancelled:
            return {"cancelled": True}
        n = len(bp)
        now = time.time()
        while window and now - window[0][0] >= 60:
            window.popleft()
        used = sum(c for _, c in window)
        if used + n > rate and window:
            wait = 60 - (now - window[0][0]) + 1
            if wait > 0:
                handle.log(f"⏳ 限速：等待 {wait:.0f}s 后上传批次 {i+1}")
                time.sleep(wait)
            window.clear()
        bid = proc.upload_batch(bp, base_index + i)
        window.append((time.time(), n))
        if bid:
            batch_ids.append(bid)
            handle.log(f"批次 {i+1}/{len(batches)} 上传完成: {bid}")
        else:
            handle.log(f"批次 {i+1}/{len(batches)} 上传失败")
    if not batch_ids:
        raise RuntimeError("所有批次上传失败")

    # 轮询直到全部批次终态（done+failed==total）
    handle.log("开始轮询 MinerU 解析进度 ...")
    deadline = time.time() + max_wait_min * 60
    failed_files: List[str] = []
    timed_out = True
    while time.time() < deadline:
        if handle.cancelled:
            return {"cancelled": True, "batch_ids": batch_ids}
        total = done = failed = processing = 0
        failed_files = []
        all_terminal = True
        for bid in batch_ids:
            st = proc.check_batch_status(bid)
            if not st:
                all_terminal = False  # 查询失败按未完成处理
                continue
            total += st["total"]; done += st["done"]
            failed += st["failed"]; processing += st["processing"]
            if st["done"] + st["failed"] < st["total"]:
                all_terminal = False
            for it in st.get("results", []):
                if it.get("state") == "failed":
                    failed_files.append(it.get("file_name", ""))
        handle.set_progress(done + failed, max(total, 1))
        handle.set_meta(done=done, failed=failed, processing=processing, total=total)
        handle.log(f"解析进度: 完成 {done} / 失败 {failed} / 处理中 {processing} / 共 {total}")
        if all_terminal and total > 0:
            timed_out = False
            break
        time.sleep(poll_interval)
    if timed_out:
        handle.log("⚠️ 轮询超时，仅下载已完成部分；未完成的 PDF 仍为处理中，可稍后再次提交解析")

    # 标记 MinerU 端解析失败的文件（可在前端重新解析）
    failed_files = [f for f in failed_files if f]
    if failed_files:
        conn = _connect_state_db(proc.db_path)
        try:
            conn.executemany(
                "UPDATE pdf_files SET status='failed', updated_at=CURRENT_TIMESTAMP WHERE filename=?",
                [(f,) for f in failed_files],
            )
            conn.commit()
        finally:
            conn.close()
        handle.log(f"标记 {len(failed_files)} 个 MinerU 解析失败文件")

    # 下载落盘
    handle.log("解析完成，开始下载结果 ...")
    total_ok = total_fail = 0
    for bid in batch_ids:
        if handle.cancelled:
            break
        res = proc.download_batch_parallel(bid, _parsed_root(collection), max_workers=4)
        total_ok += res.get("success_count", 0)
        total_fail += res.get("failed_count", 0)
        handle.log(f"批次 {bid} 下载: 成功 {res.get('success_count',0)} 失败 {res.get('failed_count',0)}")

    handle.set_progress(total_ok + total_fail, total_ok + total_fail or 1)
    return {"batch_ids": batch_ids, "downloaded": total_ok, "failed": total_fail}


# ----------------------------------------------------------------------
# 已解析论文
# ----------------------------------------------------------------------
def parsed_papers(collection: Optional[str] = None) -> List[Dict[str, Any]]:
    collection = _safe_collection(collection)
    cat = PaperCatalog()
    rows = cat.list_papers(parse_status=PARSE_PARSED)
    by_id = {r["paper_id"]: r for r in rows}
    # 兜底：直接扫描 parsed 目录，补齐未入库的
    out = []
    for pid in list_parsed_papers(collection=collection):
        r = by_id.get(pid, {})
        source_pdf = r.get("source_pdf")
        item_collection = _collection_of_relpath(source_pdf or "") if source_pdf else collection
        item = {
            "paper_id": pid,
            "char_count": r.get("char_count", 0),
            "extract_status": r.get("extract_status", "none"),
            "extract_count": r.get("extract_count", 0),
            "source_pdf": source_pdf,
            "collection": item_collection,
        }
        if item["collection"] != collection:
            continue
        out.append(item)
    return out


# ----------------------------------------------------------------------
# Schema 设计
# ----------------------------------------------------------------------
def _resolve_sample_size(sample_size: Optional[int]) -> int:
    if sample_size is None:
        sample_size = getattr(settings, "SCHEMA_SAMPLE_SIZE", 8)
    try:
        return max(1, int(sample_size))
    except (TypeError, ValueError):
        return getattr(settings, "SCHEMA_SAMPLE_SIZE", 8)


def run_design_job(handle: JobHandle, domain: str, description: str,
                   paper_ids: Optional[List[str]] = None,
                   sample_size: int = None, random_pick: bool = False,
                   min_fields: int = None, max_fields: int = None,
                   collection: Optional[str] = None) -> Dict[str, Any]:
    pool = paper_ids or [p["paper_id"] for p in parsed_papers(collection)]
    if not pool:
        raise RuntimeError("没有已解析论文可供设计 schema")
    k = _resolve_sample_size(sample_size)
    if random_pick:
        # 真·随机：从候选池里随机抽 k 篇作为样本（在所选论文/全部已解析论文范围内）。
        # 抽完后 len(pool)==k，select_sample 会原样返回，避免被体量分层覆盖掉随机性。
        pool = random.sample(list(pool), min(k, len(pool)))
        handle.log(f"随机抽样 {len(pool)} 篇用于设计 schema")
    handle.log(f"设计 schema：领域={domain}，候选论文 {len(pool)} 篇，采样 {k} 篇")
    disc = SchemaDiscovery(
        domain=domain, description=description or domain,
        sample_size=k, target_min=min_fields, target_max=max_fields,
        collection=_safe_collection(collection),
    )
    handle.set_meta(stage="多agent设计中")
    schema = disc.discover(pool)
    collection = _safe_collection(collection)
    store = SchemaStore(collection=collection)
    path = store.save(schema)
    handle.log(f"schema 已生成: {schema.slug}（{len(schema.fields)} 字段）")
    return {
        "slug": schema.slug, "fields": len(schema.fields),
        "from_figure": sum(1 for f in schema.fields if f.from_figure),
        "path": str(path), "source_papers": schema.source_papers,
    }


def list_schemas(collection: Optional[str] = None) -> List[Dict[str, Any]]:
    store = SchemaStore(collection=_safe_collection(collection))
    out = []
    for s in store.list_schemas():
        out.append({
            "slug": s.slug, "domain": s.domain, "description": s.description,
            "fields": len(s.fields), "model": s.model,
            "generated_at": s.generated_at, "record_definition": s.record_definition,
            "field_list": [
                {"name": f.name, "type": f.type, "unit": f.unit,
                 "description": f.description, "importance": f.importance,
                 "coverage": f.coverage, "from_figure": f.from_figure}
                for f in s.fields
            ],
        })
    return out


def get_schema(slug: str, collection: Optional[str] = None) -> Dict[str, Any]:
    store = SchemaStore(collection=_safe_collection(collection))
    schema = store.load(slug)
    return schema.to_dict()


def schema_usage_count(slug: str, collection: Optional[str] = None) -> int:
    count = 0
    for jf in _iter_extracted_json(collection):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if data.get("schema_slug") == slug:
            count += 1
    return count


def update_schema(slug: str, payload: Dict[str, Any], collection: Optional[str] = None) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise SchemaUploadError("schema 必须是 JSON 对象")
    payload = dict(payload)
    payload["slug"] = slug
    return upload_schema(payload, overwrite=True, collection=collection)


def delete_schema(slug: str, force: bool = False,
                  collection: Optional[str] = None) -> Dict[str, Any]:
    store = SchemaStore(collection=_safe_collection(collection))
    path = store.path_for(slug)
    if not path.exists():
        raise FileNotFoundError(f"schema 不存在: {slug}")
    usage = schema_usage_count(slug, collection)
    if usage and not force:
        raise SchemaExistsError(f"schema「{slug}」已有 {usage} 个提取结果引用；如需删除请 force=true")
    coll = _safe_collection(collection)
    archive = settings.collection_schema_dir(coll) / "archive"
    archive.mkdir(parents=True, exist_ok=True)
    target = archive / f"{slug}.{int(time.time())}.json"
    os.replace(path, target)
    return {"slug": slug, "archived_to": str(target), "usage": usage}


def clone_schema(slug: str, new_slug: str, collection: Optional[str] = None) -> Dict[str, Any]:
    store = SchemaStore(collection=_safe_collection(collection))
    schema = store.load(slug)
    schema.slug = slugify(new_slug)
    if store.path_for(schema.slug).exists():
        raise SchemaExistsError(f"目标 schema 已存在: {schema.slug}")
    path = store.save(schema)
    return {"slug": schema.slug, "path": str(path), "fields": len(schema.fields)}


# ----------------------------------------------------------------------
# 直接上传 schema（用户给定符合规范的 schema+prompt，跳过自动设计）
# ----------------------------------------------------------------------
class SchemaUploadError(Exception):
    """上传 schema 不合规（对应 HTTP 400）。"""


class SchemaExistsError(Exception):
    """同名 schema 已存在且内容不同（对应 HTTP 409）。"""


def _schema_semantic(schema: GeneratedSchema) -> Dict[str, Any]:
    """取 schema 的语义部分用于「是否相同」比较（忽略生成元数据）。"""
    return {
        "domain": schema.domain,
        "description": schema.description,
        "record_definition": schema.record_definition,
        "fields": [f.to_dict() for f in schema.fields],
    }


def upload_schema(payload: Dict[str, Any], overwrite: bool = False,
                  collection: Optional[str] = None) -> Dict[str, Any]:
    """保存用户直接上传的 schema（含 domain/description/record_definition/fields）。

    - slug 始终经 slugify 净化（防止路径穿越），用户给的 slug 仅作建议名。
    - 宽松校验：至少 1 个字段、有 domain 或 description；缺 record_definition / 字段说明
      仅作 warning，不拒绝。
    - 同名 schema 已存在且语义不同：除非 overwrite=True，否则拒绝（409）。
    """
    if not isinstance(payload, dict):
        raise SchemaUploadError("schema 必须是 JSON 对象")
    schema = GeneratedSchema.from_dict(payload)

    if not schema.fields:
        raise SchemaUploadError("schema 至少需要 1 个字段（fields 不能为空）")
    if not (schema.domain or schema.description):
        raise SchemaUploadError("需要提供 domain 或 description")

    # slug 净化：优先用户建议名，否则由 domain 生成；统一过 slugify 防穿越
    suggested = str(payload.get("slug") or "").strip()
    schema.slug = slugify(suggested or schema.domain or schema.description)
    schema.schema_version = payload.get("schema_version") or "user-1"
    if not schema.model:
        schema.model = "user-uploaded"

    warnings = validate_schema(schema, min_fields=1,
                               max_fields=getattr(settings, "SCHEMA_MAX_FIELDS", 80))
    if not schema.record_definition:
        warnings.append("缺少 record_definition：建议补充「一条记录代表什么」，否则提取分行可能不稳定")
    missing_desc = [f.name for f in schema.fields if not (f.description or f.extraction_hint)]
    if missing_desc:
        warnings.append(f"{len(missing_desc)} 个字段缺少 description/extraction_hint，可能影响抽取质量")

    store = SchemaStore(collection=_safe_collection(collection))
    existing_path = store.path_for(schema.slug)
    if existing_path.exists() and not overwrite:
        try:
            old = store.load(schema.slug)
            if _schema_semantic(old) != _schema_semantic(schema):
                raise SchemaExistsError(
                    f"已存在同名 schema「{schema.slug}」且内容不同；如需覆盖请设置 overwrite=true")
        except SchemaExistsError:
            raise
        except Exception:
            pass  # 旧文件损坏则直接覆盖

    path = store.save(schema)
    return {
        "slug": schema.slug,
        "fields": len(schema.fields),
        "from_figure": sum(1 for f in schema.fields if f.from_figure),
        "path": str(path),
        "warnings": warnings,
    }


# ----------------------------------------------------------------------
# 提取
# ----------------------------------------------------------------------
def _extract_concurrency() -> int:
    try:
        n = int(getattr(settings, "EXTRACT_CONCURRENCY", 8))
    except (TypeError, ValueError):
        n = 8
    return max(1, min(32, n))


def run_extract_job(handle: JobHandle, slug: str,
                    paper_ids: Optional[List[str]] = None,
                    collection: Optional[str] = None) -> Dict[str, Any]:
    collection = _safe_collection(collection)
    store = SchemaStore(collection=collection)
    schema = store.load(slug)
    papers = paper_ids or [p["paper_id"] for p in parsed_papers(collection)]
    if not papers:
        raise RuntimeError("没有论文可提取")
    _extracted_root(collection).mkdir(parents=True, exist_ok=True)
    cat = PaperCatalog()
    total = len(papers)
    workers = min(_extract_concurrency(), total)
    handle.set_progress(0, total)
    handle.log(f"并行提取启动：{total} 篇，并发 {workers}（schema={slug}）")

    # 每个工作线程独立一个 ExtractionService（各自的 LLM 客户端 + 统计），
    # 避免共享可变状态竞争；schema 只读，可安全共享。
    _tls = threading.local()

    def _service() -> ExtractionService:
        svc = getattr(_tls, "svc", None)
        if svc is None:
            svc = ExtractionService(schema=schema)
            _tls.svc = svc
        return svc

    cat_lock = threading.Lock()      # SQLite 写串行化（upsert 每次新开连接）
    stat_lock = threading.Lock()
    counter = {"done": 0, "ok": 0, "failed": 0, "skipped": 0, "records": 0}

    def _work(pid: str) -> Dict[str, Any]:
        if handle.cancelled:
            return {"status": "cancelled", "pid": pid}
        out_file = _extracted_root(collection, slug) / f"{pid}.json"
        if out_file.exists():
            try:
                existing = json.loads(out_file.read_text(encoding="utf-8"))
                if existing.get("schema_slug") == slug and existing.get("success") is True:
                    return {
                        "status": "skip",
                        "pid": pid,
                        "error": "已有成功提取结果",
                        "count": int(existing.get("count") or 0),
                    }
            except Exception:
                pass
        content = load_paper_text(pid, collection=collection)
        if not content:
            return {"status": "skip", "pid": pid}
        lock = _lock_for_extract(collection, slug, pid)
        if not lock.acquire(blocking=False):
            return {"status": "skip", "pid": pid, "error": "同一 schema/paper 正在提取"}
        try:
            out = _service().extract(paper_id=pid, content=content)
            d = out.to_dict()
            d["schema_slug"] = slug
            _atomic_write_text(out_file, json.dumps(d, ensure_ascii=False, indent=2))
            with cat_lock:
                if out.success:
                    cat.mark_extracted(pid, extract_json=str(out_file), extract_count=out.count)
                else:
                    cat.mark_extract_failed(pid, error=out.error or "提取失败")
        finally:
            lock.release()
        return {"status": "ok" if out.success else "fail", "pid": pid,
                "count": out.count, "error": out.error, "meta": out.metadata or {}}

    from concurrent.futures import ThreadPoolExecutor, as_completed
    cancelled = False
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(_work, pid): pid for pid in papers}
        for fut in as_completed(futures):
            pid = futures[fut]
            try:
                res = fut.result()
            except Exception as e:  # noqa: BLE001
                res = {"status": "fail", "pid": pid, "error": str(e), "count": 0, "meta": {}}
            with stat_lock:
                counter["done"] += 1
                st = res["status"]
                if st == "ok":
                    counter["ok"] += 1
                    counter["records"] += res.get("count", 0)
                elif st == "fail":
                    counter["failed"] += 1
                elif st == "skip":
                    counter["skipped"] += 1
                elif st == "cancelled":
                    cancelled = True
                done = counter["done"]
            handle.set_progress(done, total)
            handle.set_meta(ok=counter["ok"], records=counter["records"],
                            failed=counter["failed"], skipped=counter["skipped"])
            if res["status"] == "ok":
                m = res["meta"]
                handle.log(f"✅ [{done}/{total}] {pid}: {res['count']} 条, 证据 {m.get('evidence_verified',0)}/{m.get('evidence_total',0)}")
            elif res["status"] == "fail":
                handle.log(f"❌ [{done}/{total}] {pid}: {res.get('error')}")
            elif res["status"] == "skip":
                reason = res.get("error") or "无正文"
                handle.log(f"⏭ [{done}/{total}] 跳过（{reason}）: {pid}")

    result = {"slug": slug, "ok": counter["ok"], "failed": counter["failed"],
              "skipped": counter["skipped"], "total": total, "records": counter["records"]}
    if cancelled or handle.cancelled:
        result["cancelled"] = True
    handle.log(f"提取完成：成功 {counter['ok']}，失败 {counter['failed']}，跳过 {counter['skipped']}，共 {counter['records']} 条记录")
    return result


# ----------------------------------------------------------------------
# 数据查看（含证据与来源）
# ----------------------------------------------------------------------
# 数据集缓存：避免每次查看/翻页都重新读取上千个 JSON 文件
_DATA_CACHE: Dict[str, Any] = {}
_DATA_LOCK = threading.Lock()


def _iter_extracted_json(collection: Optional[str] = None):
    collection = _safe_collection(collection)
    root = _extracted_root(collection)
    yield from sorted(root.rglob("*.json")) if root.exists() else []


def _dataset_signature(collection: Optional[str] = None) -> tuple:
    """目录指纹（文件数 + 最新 mtime），用于缓存失效判断。"""
    files = list(_iter_extracted_json(collection))
    mtime = max((f.stat().st_mtime for f in files), default=0.0)
    return (len(files), round(mtime, 3))


def _build_dataset(slug: Optional[str], collection: Optional[str] = None) -> Dict[str, Any]:
    """读取全部提取结果，组装成 columns + rows；带缓存。"""
    collection = _safe_collection(collection)
    key = f"{collection or '__all_collections__'}:{slug or '__all__'}"
    sig = _dataset_signature(collection)
    with _DATA_LOCK:
        cached = _DATA_CACHE.get(key)
        if cached and cached[0] == sig:
            return cached[1]

    store = SchemaStore(collection=collection)
    field_names: List[str] = []
    schema_info = None
    if slug:
        try:
            schema = store.load(slug)
            field_names = [f.name for f in schema.fields]
            schema_info = {
                "slug": schema.slug, "domain": schema.domain,
                "record_definition": schema.record_definition,
                "fields": [{"name": f.name, "type": f.type, "unit": f.unit,
                            "from_figure": f.from_figure} for f in schema.fields],
            }
        except FileNotFoundError:
            pass

    rows: List[Dict[str, Any]] = []
    for jf in _iter_extracted_json(collection):
        try:
            data = json.loads(jf.read_text(encoding="utf-8"))
        except Exception:
            continue
        if slug and data.get("schema_slug") and data.get("schema_slug") != slug:
            continue
        paper_id = data.get("paper_id", jf.stem)
        for rec in data.get("records", []):
            row = {"_paper_id": paper_id, "fields": {}}
            for k, v in rec.items():
                if isinstance(v, dict):
                    row["fields"][k] = {
                        "value": v.get("value"),
                        "evidence": v.get("evidence"),
                        "verified": v.get("evidence_verified"),
                    }
                else:
                    row["fields"][k] = {"value": v, "evidence": None, "verified": None}
            rows.append(row)

    if not field_names:
        seen = []
        for r in rows:
            for k in r["fields"]:
                if k not in seen:
                    seen.append(k)
        field_names = seen

    payload = {"schema": schema_info, "columns": field_names, "rows": rows}
    with _DATA_LOCK:
        _DATA_CACHE[key] = (sig, payload)
    return payload


def get_data(slug: Optional[str] = None, offset: int = 0,
             collection: Optional[str] = None,
             limit: int = 100) -> Dict[str, Any]:
    """分页返回数据：count=总记录数，rows=当前页。"""
    ds = _build_dataset(slug, collection)
    all_rows = ds["rows"]
    total = len(all_rows)
    offset = max(0, int(offset))
    limit = int(limit)
    page = all_rows[offset:offset + limit] if limit > 0 else all_rows
    return {"schema": ds["schema"], "columns": ds["columns"],
            "rows": page, "count": total, "offset": offset,
            "limit": limit, "returned": len(page)}


def _cell_value(f: Dict[str, Any]) -> str:
    v = f.get("value")
    if v is None or v == "":
        return ""
    if isinstance(v, (dict, list)):
        return json.dumps(v, ensure_ascii=False)
    return str(v)


def export_csv(slug: Optional[str] = None, collection: Optional[str] = None) -> str:
    """导出数值表为 CSV（带 UTF-8 BOM，Excel 友好）。"""
    import csv
    import io
    ds = _build_dataset(slug, collection)
    cols = ds["columns"]
    buf = io.StringIO()
    buf.write("\ufeff")  # BOM，避免 Excel 中文乱码
    w = csv.writer(buf)
    w.writerow(["来源论文"] + cols)
    for r in ds["rows"]:
        w.writerow([r["_paper_id"]] + [_cell_value(r["fields"].get(c, {})) for c in cols])
    return buf.getvalue()


def export_json(slug: Optional[str] = None, collection: Optional[str] = None) -> str:
    """导出完整记录（含 value/evidence/verified）为 JSON。"""
    ds = _build_dataset(slug, collection)
    out = {"schema": ds["schema"], "columns": ds["columns"],
           "count": len(ds["rows"]), "rows": ds["rows"]}
    return json.dumps(out, ensure_ascii=False, indent=2)


# ----------------------------------------------------------------------
# 运行时设置（API 端点配置，写入 .env 并热重载）
# ----------------------------------------------------------------------
import os as _os

ENV_PATH = Path(settings.BASE_DIR) / ".env"


def _mask_key(val: str) -> str:
    if not val:
        return ""
    if len(val) <= 8:
        return "****"
    return f"{val[:4]}…{val[-4:]}"


def get_settings() -> Dict[str, Any]:
    """返回当前生效的端点配置（API Key 脱敏）。"""
    roles = []
    for r in settings.AGENT_ROLE_NAMES:
        up = r.upper()
        roles.append({
            "role": r,
            "model": _os.getenv(f"AGENT_{up}_MODEL", ""),
            "api_base": _os.getenv(f"AGENT_{up}_API_BASE", ""),
            "api_key_set": bool(_os.getenv(f"AGENT_{up}_API_KEY", "")),
            "api_key_masked": _mask_key(_os.getenv(f"AGENT_{up}_API_KEY", "")),
        })
    return {
        "mineru": {
            "token_set": bool(settings.MINERU_TOKEN),
            "token_masked": _mask_key(settings.MINERU_TOKEN),
            "api_base": settings.MINERU_API_BASE,
        },
        "llm": {
            "model": settings.LLM_MODEL,
            "api_base": settings.LLM_API_BASE,
            "api_key_set": bool(settings.LLM_API_KEY),
            "api_key_masked": _mask_key(settings.LLM_API_KEY),
        },
        "agents": roles,
        "roles": settings.AGENT_ROLE_NAMES,
        "data": {
            "default_collection": getattr(settings, "DEFAULT_COLLECTION", ""),
            "collections_dir": str(settings.COLLECTIONS_DIR),
            "state_db": str(Path(settings.UPLOADS_DIR) / "pdf_state.db"),
        },
        "limits": {
            "max_pdf_size_mb": settings.MAX_PDF_SIZE_MB,
            "processing_stale_hours": getattr(settings, "PROCESSING_STALE_HOURS", 12),
            "upload_rate_per_min": settings.MINERU_UPLOAD_RATE_PER_MIN,
            "llm_max_inflight": getattr(settings, "LLM_MAX_INFLIGHT", 8),
            "extract_concurrency": getattr(settings, "EXTRACT_CONCURRENCY", 8),
            "schema_agent_roles": ",".join(getattr(settings, "SCHEMA_AGENT_ROLES", ["schema_agent_a", "schema_agent_b", "schema_agent_c"])),
            "schema_merger_role": getattr(settings, "SCHEMA_MERGER_ROLE", "schema_merger"),
            "schema_reviewer_role": getattr(settings, "SCHEMA_REVIEWER_ROLE", "schema_reviewer"),
            "extractor_roles": ",".join(getattr(settings, "EXTRACTOR_ROLES", ["extractor_a", "extractor_b"])),
            "extract_merger_role": getattr(settings, "EXTRACT_MERGER_ROLE", "extract_merger"),
            "extract_reviewer_role": getattr(settings, "EXTRACT_REVIEWER_ROLE", "extract_reviewer"),
            "extract_review_enabled": getattr(settings, "EXTRACT_REVIEW_ENABLED", True),
        },
    }


def _write_env(updates: Dict[str, str]) -> None:
    """把 updates 合并进 .env（保留其它行/注释/顺序），原子替换。

    值为 ""（空串）表示删除该键（回退到继承/默认）。
    """
    lines: List[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()
    keys = set(updates.keys())
    seen = set()
    out: List[str] = []
    for ln in lines:
        s = ln.strip()
        if not s or s.startswith("#") or "=" not in s:
            out.append(ln)
            continue
        k = s.split("=", 1)[0].strip()
        if k in keys:
            seen.add(k)
            v = updates[k]
            if v == "":
                continue  # 删除该键
            out.append(f"{k}={v}")
        else:
            out.append(ln)
    # 追加新增键
    appended = [k for k in updates if k not in seen and updates[k] != ""]
    if appended:
        out.append("")
        out.append("# ---- 由 Web 设置页写入 ----")
        for k in appended:
            out.append(f"{k}={updates[k]}")
    tmp = ENV_PATH.with_suffix(".env.tmp")
    tmp.write_text("\n".join(out) + "\n", encoding="utf-8")
    _os.replace(tmp, ENV_PATH)


def update_settings(payload: Dict[str, Any]) -> Dict[str, Any]:
    """根据前端提交更新 .env + os.environ + 热重载 settings。

    只接受空串=保持/清除以外的非空写入；API Key 留空表示「不修改」。
    """
    updates: Dict[str, str] = {}

    def _set(envkey: str, value, allow_clear: bool = True):
        if value is None:
            return
        value = str(value).strip()
        # 对 key 字段：空串表示不修改（不写入）
        updates[envkey] = value
        if value == "":
            _os.environ.pop(envkey, None)
        else:
            _os.environ[envkey] = value

    mineru = payload.get("mineru") or {}
    if "api_base" in mineru:
        _set("MINERU_API_BASE", mineru.get("api_base"))
    if mineru.get("token"):  # 仅在提供新 token 时更新
        _set("MINERU_TOKEN", mineru.get("token"))

    llm = payload.get("llm") or {}
    if "model" in llm:
        _set("LLM_MODEL", llm.get("model"))
    if "api_base" in llm:
        _set("LLM_API_BASE", llm.get("api_base"))
    if llm.get("api_key"):
        _set("LLM_API_KEY", llm.get("api_key"))

    for a in payload.get("agents") or []:
        r = (a.get("role") or "").strip().upper()
        if not r:
            continue
        if "model" in a:
            _set(f"AGENT_{r}_MODEL", a.get("model"))
        if "api_base" in a:
            _set(f"AGENT_{r}_API_BASE", a.get("api_base"))
        if a.get("api_key"):
            _set(f"AGENT_{r}_API_KEY", a.get("api_key"))

    limits = payload.get("limits") or {}
    if limits.get("default_collection") not in (None, ""):
        _set("DEFAULT_COLLECTION", limits.get("default_collection"))
    if limits.get("max_pdf_size_mb") not in (None, ""):
        try:
            n = max(1, min(200, int(limits["max_pdf_size_mb"])))
            _set("MAX_PDF_SIZE_MB", n)
        except (TypeError, ValueError):
            pass
    if limits.get("upload_rate_per_min") not in (None, ""):
        try:
            n = max(1, min(50, int(limits["upload_rate_per_min"])))
            _set("MINERU_UPLOAD_RATE_PER_MIN", n)
        except (TypeError, ValueError):
            pass
    if limits.get("llm_max_inflight") not in (None, ""):
        try:
            n = max(1, min(64, int(limits["llm_max_inflight"])))
            _set("LLM_MAX_INFLIGHT", n)
        except (TypeError, ValueError):
            pass
    if limits.get("extract_concurrency") not in (None, ""):
        try:
            n = max(1, min(32, int(limits["extract_concurrency"])))
            _set("EXTRACT_CONCURRENCY", n)
        except (TypeError, ValueError):
            pass
    if limits.get("processing_stale_hours") not in (None, ""):
        try:
            n = max(1, min(24 * 30, int(limits["processing_stale_hours"])))
            _set("PROCESSING_STALE_HOURS", n)
        except (TypeError, ValueError):
            pass
    if "extractor_roles" in limits:
        roles = ",".join(
            r.strip() for r in str(limits.get("extractor_roles") or "").split(",") if r.strip()
        )
        _set("EXTRACTOR_ROLES", roles or "extractor")
    if "extract_merger_role" in limits:
        role = str(limits.get("extract_merger_role") or "").strip()
        _set("EXTRACT_MERGER_ROLE", role or "extract_merger")
    if "extract_reviewer_role" in limits:
        role = str(limits.get("extract_reviewer_role") or "").strip()
        _set("EXTRACT_REVIEWER_ROLE", role or "extract_reviewer")
    if "extract_review_enabled" in limits:
        enabled = str(limits.get("extract_review_enabled")).strip().lower()
        _set("EXTRACT_REVIEW_ENABLED", "false" if enabled in {"0", "false", "no", "off"} else "true")
    if "schema_agent_roles" in limits:
        roles = ",".join(
            r.strip() for r in str(limits.get("schema_agent_roles") or "").split(",") if r.strip()
        )
        _set("SCHEMA_AGENT_ROLES", roles or "schema_agent_a,schema_agent_b,schema_agent_c")
    if "schema_merger_role" in limits:
        role = str(limits.get("schema_merger_role") or "").strip()
        _set("SCHEMA_MERGER_ROLE", role or "schema_merger")
    if "schema_reviewer_role" in limits:
        role = str(limits.get("schema_reviewer_role") or "").strip()
        _set("SCHEMA_REVIEWER_ROLE", role or "schema_reviewer")

    if updates:
        _write_env(updates)
        settings.reload_config()
    return get_settings()
