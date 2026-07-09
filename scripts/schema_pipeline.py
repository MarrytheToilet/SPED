#!/usr/bin/env python3
"""
新架构提取流程：LLM 自动设计 schema + 扁平提取(内联 evidence)。

用法：
    # 1) 设计 schema（读领域简介 + 若干论文，自动产出单表字段）
    python scripts/schema_pipeline.py design --domain "人工关节材料摩擦学" \
        --desc "髋/膝关节内衬/球头/股骨柄的材料成分、几何尺寸、物理性能、摩擦磨损实验参数与结果、计算模拟" \
        --samples 8

    # 2) 列出已生成的 schema
    python scripts/schema_pipeline.py list

    # 3) 用 schema 提取单篇 / 批量
    python scripts/schema_pipeline.py extract --slug <slug> --paper PAPER_ID
    python scripts/schema_pipeline.py extract --slug <slug> --all
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import settings
from src.schema import SchemaDiscovery, SchemaStore
from src.schema.sampling import list_parsed_papers, load_paper_text
from src.extractors import ExtractionService


DEFAULT_DOMAIN = "人工关节材料摩擦学"
DEFAULT_DESC = (
    "髋/膝关节的内衬、球头、股骨柄的材料成分、几何尺寸、物理性能、"
    "摩擦磨损实验参数与结果、计算模拟"
)


def cmd_design(args):
    domain = args.domain or DEFAULT_DOMAIN
    desc = args.desc or DEFAULT_DESC
    collection = args.collection or settings.DEFAULT_COLLECTION
    papers = list_parsed_papers(collection=collection)
    if not papers:
        print(f"❌ 没有已解析论文 ({settings.collection_parsed_dir(collection)}/*/full.md)")
        return 1

    disc = SchemaDiscovery(
        domain=domain, description=desc,
        sample_size=args.samples,
        target_min=args.min_fields, target_max=args.max_fields,
        collection=collection,
    )
    print(f"🧠 设计 schema（多agent）：领域={domain}，样本≤{args.samples} 篇 ...")
    schema = disc.discover(papers)

    store = SchemaStore(collection=collection)
    path = store.save(schema)
    print(f"\n✅ schema 已生成：{path}")
    print(f"   slug: {schema.slug}")
    print(f"   字段数: {len(schema.fields)}")
    print(f"   记录定义: {schema.record_definition}")
    print(f"   样本论文: {schema.source_papers}")
    print("\n字段预览：")
    for f in schema.fields:
        unit = f" [{f.unit}]" if f.unit else ""
        print(f"  - {f.name} ({f.type}{unit}) cov={f.coverage} imp={f.importance}: {f.description}")
    return 0


def cmd_list(args):
    collection = args.collection or settings.DEFAULT_COLLECTION
    store = SchemaStore(collection=collection)
    schemas = store.list_schemas()
    if not schemas:
        print("（暂无生成的 schema，先运行 design）")
        return 0
    for s in schemas:
        print(f"- {s.slug}  字段{len(s.fields)}  领域={s.domain}  model={s.model}  生成于{s.generated_at}")
    return 0


def _extract_one(service, paper_id, output_dir, collection):
    content = load_paper_text(paper_id, collection=collection)
    if not content:
        print(f"  ❌ {paper_id}: 无 full.md")
        return False
    out = service.extract(paper_id=paper_id, content=content)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{paper_id}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(out.to_dict(), f, ensure_ascii=False, indent=2)
    if out.success:
        meta = out.metadata or {}
        print(f"  ✅ {paper_id}: {out.count} 条记录, "
              f"evidence 校验 {meta.get('evidence_verified',0)}/{meta.get('evidence_total',0)} → {output_file}")
        return True
    print(f"  ❌ {paper_id}: {out.error}")
    return False


def cmd_extract(args):
    collection = args.collection or settings.DEFAULT_COLLECTION
    store = SchemaStore(collection=collection)
    try:
        schema = store.load(args.slug)
    except FileNotFoundError:
        print(f"❌ 找不到 schema: {args.slug}（先 design 或 list 查看）")
        return 1

    service = ExtractionService(schema=schema, model=args.model)
    output_dir = Path(args.out) if args.out else settings.collection_extracted_dir(collection, args.slug)

    if args.all:
        papers = list_parsed_papers(collection=collection)
    elif args.paper:
        papers = [args.paper]
    else:
        print("❌ 需指定 --paper PAPER_ID 或 --all")
        return 1

    print(f"🚀 用 schema='{args.slug}' 提取 {len(papers)} 篇 ...")
    ok = 0
    for pid in papers:
        if _extract_one(service, pid, output_dir, collection):
            ok += 1
    print(f"\n📊 完成：成功 {ok}/{len(papers)}，输出目录 {output_dir}")
    return 0 if ok == len(papers) else 1


def main():
    parser = argparse.ArgumentParser(description="LLM自动设计schema + 扁平提取")
    sub = parser.add_subparsers(dest="command")

    p_design = sub.add_parser("design", help="设计 schema")
    p_design.add_argument("--domain", help="领域名称")
    p_design.add_argument("--desc", help="领域简介")
    p_design.add_argument("--samples", type=int, default=8, help="采样论文数")
    p_design.add_argument("--min-fields", type=int, default=18, dest="min_fields")
    p_design.add_argument("--max-fields", type=int, default=40, dest="max_fields")
    p_design.add_argument("--model", help="LLM模型")
    p_design.add_argument("--collection", default=None, help="主题 collection")

    p_list = sub.add_parser("list", help="列出已生成 schema")
    p_list.add_argument("--collection", default=None, help="主题 collection")

    p_ext = sub.add_parser("extract", help="用 schema 提取")
    p_ext.add_argument("--slug", required=True, help="schema slug")
    p_ext.add_argument("--paper", help="单篇 paper_id")
    p_ext.add_argument("--all", action="store_true", help="提取全部已解析论文")
    p_ext.add_argument("--out", help="输出目录")
    p_ext.add_argument("--model", help="LLM模型")
    p_ext.add_argument("--collection", default=None, help="主题 collection")

    args = parser.parse_args()
    if args.command == "design":
        return cmd_design(args)
    if args.command == "list":
        return cmd_list(args)
    if args.command == "extract":
        return cmd_extract(args)
    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
