"""
SPED Web 后端（FastAPI）。

把「解析 → 设计schema → 提取 → 数据查看」整套流程暴露为 REST 接口，
配合 webapp/static/index.html 单页前端使用。耗时操作走后台任务（webapp/jobs.py）。

启动：
    python -m webapp.app           # 或 uvicorn webapp.app:app --port 8000
"""
from __future__ import annotations

from pathlib import Path
from typing import List, Optional
import hashlib
import json

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from webapp import services
from webapp.jobs import JOBS

app = FastAPI(title="SPED", version="1.0")
STATIC_DIR = Path(__file__).parent / "static"


def _fingerprint(prefix: str, payload: dict) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.sha256(raw.encode('utf-8')).hexdigest()[:24]}"


# ---------------- 请求模型 ----------------
class ParseReq(BaseModel):
    filenames: Optional[List[str]] = None
    all_unparsed: bool = False
    all_failed: bool = False
    force_reparse: bool = False
    collection: Optional[str] = None


class DeletePdfsReq(BaseModel):
    filenames: Optional[List[str]] = None
    categories: Optional[List[str]] = None
    collection: Optional[str] = None
    delete_files: bool = True
    force: bool = False
    confirm_text: str = ""


class DesignReq(BaseModel):
    domain: str
    description: str = ""
    paper_ids: Optional[List[str]] = None
    sample_size: Optional[int] = None
    random_pick: bool = False
    min_fields: Optional[int] = None
    max_fields: Optional[int] = None
    collection: Optional[str] = None


class ExtractReq(BaseModel):
    slug: str
    paper_ids: Optional[List[str]] = None
    all_parsed: bool = False
    collection: Optional[str] = None


class UploadSchemaReq(BaseModel):
    schema_def: dict
    overwrite: bool = False
    collection: Optional[str] = None


class UpdateSchemaReq(BaseModel):
    schema_def: dict
    collection: Optional[str] = None


class CloneSchemaReq(BaseModel):
    new_slug: str
    collection: Optional[str] = None


class SettingsReq(BaseModel):
    mineru: Optional[dict] = None
    llm: Optional[dict] = None
    agents: Optional[List[dict]] = None
    limits: Optional[dict] = None


# ---------------- PDF / 解析 ----------------
@app.get("/api/collections")
def api_collections():
    return {"collections": services.list_collections()}


@app.get("/api/pdfs")
def api_pdfs(collection: Optional[str] = None):
    return services.pdf_overview(collection)


@app.post("/api/pdfs/delete")
def api_pdfs_delete(req: DeletePdfsReq):
    try:
        return services.delete_pdfs(
            filenames=req.filenames,
            categories=req.categories,
            collection=req.collection,
            delete_files=req.delete_files,
            force=req.force,
            confirm_text=req.confirm_text,
        )
    except ValueError as e:
        raise HTTPException(400, str(e))
    except FileNotFoundError as e:
        raise HTTPException(404, str(e))


@app.post("/api/parse")
def api_parse(req: ParseReq):
    if services.parse_in_progress():
        raise HTTPException(409, "已有解析任务在运行，请等待其完成")
    overview = services.pdf_overview(req.collection)
    names = list(req.filenames or [])
    if req.all_unparsed:
        names += [it["filename"] for it in overview["items"] if it["category"] == "unparsed"]
    if req.all_failed:
        names += [it["filename"] for it in overview["items"] if it["category"] == "failed"]
    names = sorted(set(names))
    if not names:
        raise HTTPException(400, "未选择任何 PDF")
    force = req.force_reparse
    fp = _fingerprint("parse", {"collection": req.collection, "filenames": names, "force_reparse": force})
    job = JOBS.submit("parse", f"解析 {len(names)} 个 PDF",
                      lambda h: services.run_parse_job(h, names, force_reparse=force, collection=req.collection),
                      fingerprint=fp)
    return {"job_id": job.id, "count": len(names)}


# ---------------- 已解析论文 ----------------
@app.get("/api/parsed")
def api_parsed(collection: Optional[str] = None):
    return {"papers": services.parsed_papers(collection)}


@app.get("/api/parsed/by_collection")
def api_parsed_by_collection(collection: Optional[str] = None):
    return {"papers": services.parsed_papers(collection)}


# ---------------- Schema 设计 ----------------
@app.post("/api/schema/design")
def api_design(req: DesignReq):
    fp = _fingerprint("design", {
        "domain": req.domain,
        "description": req.description,
        "paper_ids": sorted(req.paper_ids or []),
        "collection": req.collection,
        "sample_size": req.sample_size,
        "random_pick": req.random_pick,
        "min_fields": req.min_fields,
        "max_fields": req.max_fields,
    })
    job = JOBS.submit("design", f"设计 schema：{req.domain}",
                      lambda h: services.run_design_job(
                          h, req.domain, req.description, req.paper_ids,
                          req.sample_size, req.random_pick,
                          req.min_fields, req.max_fields,
                          req.collection),
                      fingerprint=fp)
    return {"job_id": job.id}


@app.get("/api/schemas")
def api_schemas(collection: Optional[str] = None):
    return {"schemas": services.list_schemas(collection)}


@app.get("/api/schemas/{slug}")
def api_schema_get(slug: str, collection: Optional[str] = None):
    try:
        return services.get_schema(slug, collection)
    except FileNotFoundError:
        raise HTTPException(404, "schema 不存在")


@app.put("/api/schemas/{slug}")
def api_schema_update(slug: str, req: UpdateSchemaReq):
    try:
        return services.update_schema(slug, req.schema_def, collection=req.collection)
    except services.SchemaUploadError as e:
        raise HTTPException(400, str(e))


@app.delete("/api/schemas/{slug}")
def api_schema_delete(slug: str, force: bool = False, collection: Optional[str] = None):
    try:
        return services.delete_schema(slug, force=force, collection=collection)
    except FileNotFoundError:
        raise HTTPException(404, "schema 不存在")
    except services.SchemaExistsError as e:
        raise HTTPException(409, str(e))


@app.post("/api/schemas/{slug}/clone")
def api_schema_clone(slug: str, req: CloneSchemaReq):
    try:
        return services.clone_schema(slug, req.new_slug, collection=req.collection)
    except FileNotFoundError:
        raise HTTPException(404, "schema 不存在")
    except services.SchemaExistsError as e:
        raise HTTPException(409, str(e))


@app.post("/api/schema/upload")
def api_schema_upload(req: UploadSchemaReq):
    try:
        return services.upload_schema(req.schema_def, overwrite=req.overwrite, collection=req.collection)
    except services.SchemaUploadError as e:
        raise HTTPException(400, str(e))
    except services.SchemaExistsError as e:
        raise HTTPException(409, str(e))


# ---------------- 提取 ----------------
@app.post("/api/extract")
def api_extract(req: ExtractReq):
    paper_ids = req.paper_ids
    if req.all_parsed:
        paper_ids = [p["paper_id"] for p in services.parsed_papers(req.collection)]
    if not paper_ids:
        raise HTTPException(400, "未选择任何论文")
    fp = _fingerprint("extract", {"collection": req.collection, "slug": req.slug, "paper_ids": sorted(paper_ids)})
    job = JOBS.submit("extract", f"提取 {len(paper_ids)} 篇（{req.slug}）",
                      lambda h: services.run_extract_job(h, req.slug, paper_ids, req.collection),
                      fingerprint=fp)
    return {"job_id": job.id, "count": len(paper_ids)}


# ---------------- 数据查看 ----------------
@app.get("/api/data")
def api_data(slug: Optional[str] = None, collection: Optional[str] = None, offset: int = 0, limit: int = 100):
    return services.get_data(slug, offset, collection, limit)


@app.get("/api/data/export")
def api_data_export(slug: Optional[str] = None, collection: Optional[str] = None, fmt: str = "csv"):
    from fastapi.responses import Response
    tag = slug or "all"
    if fmt == "json":
        content = services.export_json(slug, collection)
        return Response(
            content, media_type="application/json; charset=utf-8",
            headers={"Content-Disposition": f'attachment; filename="data_{tag}.json"'})
    content = services.export_csv(slug, collection)
    return Response(
        content, media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="data_{tag}.csv"'})


# ---------------- 任务 ----------------
@app.get("/api/jobs")
def api_jobs():
    return {"jobs": JOBS.list(), "active": [j.to_dict() for j in JOBS.active()]}


@app.get("/api/jobs/{job_id}")
def api_job(job_id: str):
    job = JOBS.get(job_id)
    if not job:
        raise HTTPException(404, "任务不存在")
    return job.to_dict(with_logs=True)


@app.post("/api/jobs/{job_id}/cancel")
def api_job_cancel(job_id: str):
    return {"cancelled": JOBS.cancel(job_id)}


# ---------------- 设置 ----------------
@app.get("/api/settings")
def api_get_settings():
    return services.get_settings()


@app.post("/api/settings")
def api_set_settings(req: SettingsReq):
    # 有任务运行时禁止改端点配置，避免热重载影响进行中的解析/提取
    if JOBS.has_active():
        raise HTTPException(409, "有任务正在运行，请等待其完成后再修改设置")
    return services.update_settings(req.dict(exclude_none=True))


# ---------------- 前端 ----------------
@app.get("/")
def index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main():
    import uvicorn
    import settings
    port = int(getattr(settings, "WEB_PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
