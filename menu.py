#!/usr/bin/env python3
"""
人工关节材料数据提取系统 - 交互式菜单

新架构流程：
  PDF → MinerU解析(markdown) → LLM自动设计schema(多agent) → 按schema扁平提取(带原文evidence)

入口脚本：
  - scripts/pdf.py            PDF 上传/查询/下载/统计
  - scripts/schema_pipeline.py  设计schema / 列出 / 提取
"""
import os
import sys
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

BLUE = '\033[94m'; GREEN = '\033[92m'; YELLOW = '\033[93m'
RED = '\033[91m'; CYAN = '\033[96m'; BOLD = '\033[1m'; END = '\033[0m'


def clear():
    os.system('clear' if os.name != 'nt' else 'cls')


def header():
    try:
        import settings
        coll = settings.DEFAULT_COLLECTION
    except Exception:
        coll = "unknown"
    print(f"\n{BLUE}{BOLD}{'='*78}{END}")
    print(f"{BLUE}{BOLD}    人工关节材料数据提取系统  (多agent · 自动schema · 原文证据){END}")
    print(f"{BLUE}    当前主题 collection: {coll}{END}")
    print(f"{BLUE}{BOLD}{'='*78}{END}\n")


def pause():
    input(f"\n{GREEN}按回车继续...{END}")


def run(cmd):
    """运行子命令（列表形式）。"""
    print(f"{CYAN}$ {' '.join(cmd)}{END}\n")
    return subprocess.run(cmd)


def py(*args):
    return [sys.executable, *args]


def current_collection() -> str:
    try:
        import settings
        return settings.DEFAULT_COLLECTION
    except Exception:
        return "人工关节材料摩擦学"


def ask_collection() -> str:
    default = current_collection()
    val = input(f"{GREEN}主题 collection（回车用 {default}）: {END}").strip()
    return val or default


# ============ PDF 处理 ============
def pdf_upload():
    clear(); header()
    print(f"{BOLD}上传 PDF 到 MinerU{END}\n")
    collection = ask_collection()
    try:
        import settings
        default_dir = settings.collection_pdf_dir(collection)
    except Exception:
        default_dir = ROOT / "data" / "collections" / collection / "pdfs"
    d = input(f"{GREEN}PDF 目录（回车用 {default_dir}）: {END}").strip()
    cmd = py("scripts/pdf.py", "upload")
    cmd += ["--collection", collection]
    if d:
        cmd += ["--dir", d]
    run(cmd); pause()


def pdf_status():
    clear(); header()
    print(f"{BOLD}查询批次状态{END}\n")
    bid = input(f"{GREEN}批次ID（回车查询全部）: {END}").strip()
    cmd = py("scripts/pdf.py", "status")
    if bid:
        cmd.append(bid)
    run(cmd); pause()


def pdf_download():
    clear(); header()
    print(f"{BOLD}下载解析结果{END}\n")
    collection = ask_collection()
    bid = input(f"{GREEN}批次ID: {END}").strip()
    if not bid:
        print(f"{RED}需要批次ID{END}"); pause(); return
    run(py("scripts/pdf.py", "download", bid, "--collection", collection)); pause()


def pdf_stats():
    clear(); header()
    run(py("scripts/pdf.py", "stats")); pause()


# ============ Schema + 提取 ============
def show_endpoints():
    clear(); header()
    print(f"{BOLD}各 agent 角色的模型端点{END}\n")
    try:
        import settings
        eps = settings.list_agent_endpoints()
        for role, info in eps.items():
            key = "✓key" if info["has_key"] else f"{RED}缺key{END}"
            print(f"  {CYAN}{role:14}{END} model={info['model']:24} base={info['api_base']}  {key}")
        print(f"\n  Schema agents: {settings.SCHEMA_AGENT_ROLES}")
        print(f"  Schema merger/reviewer: {settings.SCHEMA_MERGER_ROLE} / {settings.SCHEMA_REVIEWER_ROLE}")
        print(f"  Extractors: {settings.EXTRACTOR_ROLES}")
        print(f"  Extract merger/reviewer: {settings.EXTRACT_MERGER_ROLE} / {settings.EXTRACT_REVIEWER_ROLE}")
        print(f"  字段数范围: {settings.SCHEMA_MIN_FIELDS}~{settings.SCHEMA_MAX_FIELDS}")
        print(f"  输出token上限: {settings.LLM_MAX_OUTPUT_TOKENS}")
    except Exception as e:
        print(f"{RED}读取配置失败: {e}{END}")
    pause()


def schema_design():
    clear(); header()
    print(f"{BOLD}自动设计提取 schema（多agent协作）{END}\n")
    print(f"{YELLOW}模型会阅读若干已解析论文，自动设计「单一大表」字段集合。{END}\n")
    domain = input(f"{GREEN}领域名称（回车用默认）: {END}").strip()
    collection = ask_collection()
    desc = input(f"{GREEN}领域简介（回车用默认）: {END}").strip()
    samples = input(f"{GREEN}采样论文数（回车用默认）: {END}").strip()
    cmd = py("scripts/schema_pipeline.py", "design")
    cmd += ["--collection", collection]
    if domain: cmd += ["--domain", domain]
    if desc: cmd += ["--desc", desc]
    if samples.isdigit(): cmd += ["--samples", samples]
    print()
    run(cmd); pause()


def schema_list():
    clear(); header()
    collection = ask_collection()
    run(py("scripts/schema_pipeline.py", "list", "--collection", collection)); pause()


def schema_extract_single():
    clear(); header()
    print(f"{BOLD}用 schema 提取单篇{END}\n")
    collection = ask_collection()
    run(py("scripts/schema_pipeline.py", "list", "--collection", collection))
    slug = input(f"\n{GREEN}schema slug: {END}").strip()
    if not slug:
        return
    pid = input(f"{GREEN}论文 paper_id: {END}").strip()
    if not pid:
        print(f"{RED}需要 paper_id{END}"); pause(); return
    run(py("scripts/schema_pipeline.py", "extract", "--collection", collection, "--slug", slug, "--paper", pid)); pause()


def schema_extract_all():
    clear(); header()
    print(f"{BOLD}用 schema 批量提取全部已解析论文{END}\n")
    collection = ask_collection()
    run(py("scripts/schema_pipeline.py", "list", "--collection", collection))
    slug = input(f"\n{GREEN}schema slug: {END}").strip()
    if not slug:
        return
    confirm = input(f"{GREEN}确认对所有已解析论文提取？(y/n): {END}").strip().lower()
    if confirm != 'y':
        return
    run(py("scripts/schema_pipeline.py", "extract", "--collection", collection, "--slug", slug, "--all")); pause()


def list_parsed():
    clear(); header()
    collection = ask_collection()
    print(f"{BOLD}已解析论文（collection={collection}）{END}\n")
    try:
        from src.schema.sampling import list_parsed_papers
        papers = list_parsed_papers(collection=collection)
        for i, p in enumerate(papers, 1):
            print(f"  {i:3}. {p}")
        print(f"\n{GREEN}共 {len(papers)} 篇{END}")
    except Exception as e:
        print(f"{RED}读取失败: {e}{END}")
    pause()


def data_layout():
    clear(); header()
    print(f"{BOLD}数据目录概览{END}\n")
    try:
        import settings
        coll = ask_collection()
        paths = [
            ("collection root", settings.collection_root(coll)),
            ("pdfs", settings.collection_pdf_dir(coll)),
            ("parsed", settings.collection_parsed_dir(coll)),
            ("schemas", settings.collection_schema_dir(coll)),
            ("extracted", settings.collection_extracted_dir(coll)),
            ("state db", Path(settings.UPLOADS_DIR) / "pdf_state.db"),
        ]
        for label, path in paths:
            print(f"  {CYAN}{label:16}{END} {path}")
        print("\n计数:")
        print(f"  PDFs:      {len(list(settings.collection_pdf_dir(coll).rglob('*.pdf')))}")
        print(f"  parsed:    {len([p for p in settings.collection_parsed_dir(coll).iterdir() if p.is_dir()]) if settings.collection_parsed_dir(coll).exists() else 0}")
        print(f"  schemas:   {len(list(settings.collection_schema_dir(coll).glob('*.json')))}")
        print(f"  extracted: {len(list(settings.collection_extracted_dir(coll).rglob('*.json')))}")
    except Exception as e:
        print(f"{RED}读取失败: {e}{END}")
    pause()


def runtime_config():
    clear(); header()
    print(f"{BOLD}运行配置摘要{END}\n")
    try:
        import settings
        print(f"  DEFAULT_COLLECTION       {settings.DEFAULT_COLLECTION}")
        print(f"  WEB_PORT                 {settings.WEB_PORT}")
        print(f"  MAX_PDF_SIZE_MB          {settings.MAX_PDF_SIZE_MB}")
        print(f"  PROCESSING_STALE_HOURS   {settings.PROCESSING_STALE_HOURS}")
        print(f"  MINERU_UPLOAD_RATE/MIN   {settings.MINERU_UPLOAD_RATE_PER_MIN}")
        print(f"  LLM_MODEL                {settings.LLM_MODEL}")
        print(f"  LLM_API_BASE             {settings.LLM_API_BASE}")
        print(f"  LLM_MAX_INFLIGHT         {settings.LLM_MAX_INFLIGHT}")
        print(f"  SCHEMA_AGENT_ROLES       {settings.SCHEMA_AGENT_ROLES}")
        print(f"  EXTRACTOR_ROLES          {settings.EXTRACTOR_ROLES}")
        print(f"  EXTRACT_CONCURRENCY      {settings.EXTRACT_CONCURRENCY}")
        print(f"  EXTRACT_REVIEW_ENABLED   {settings.EXTRACT_REVIEW_ENABLED}")
    except Exception as e:
        print(f"{RED}读取配置失败: {e}{END}")
    pause()


def launch_web():
    clear()
    print(f"{BOLD}启动 Web 界面{END}\n")
    try:
        import settings
        port = getattr(settings, "WEB_PORT", 8000)
    except Exception:
        port = 8000
    print(f"{YELLOW}将在 http://localhost:{port} 启动单页应用（解析 / 设计 / 提取 / 数据 / 设置）。{END}")
    print(f"{YELLOW}按 Ctrl+C 可停止服务并返回菜单。{END}\n")
    try:
        run([sys.executable, "-m", "webapp.app"])
    except KeyboardInterrupt:
        print(f"\n{BLUE}已停止 Web 服务{END}")
    pause()


def main_menu():
    while True:
        try:
            clear(); header()
            print(f"{CYAN}【PDF 处理】{END}")
            print(f"  {BOLD}1.{END} 📤 上传PDF到MinerU")
            print(f"  {BOLD}2.{END} 🔍 查询批次状态")
            print(f"  {BOLD}3.{END} 📥 下载解析结果")
            print(f"  {BOLD}4.{END} 📊 PDF处理统计\n")

            print(f"{CYAN}【Schema 设计 + 数据提取】{END}")
            print(f"  {BOLD}5.{END} 🧭 查看各agent端点/配置")
            print(f"  {BOLD}6.{END} 🪄 自动设计schema（多agent）")
            print(f"  {BOLD}7.{END} 📜 查看已生成schema")
            print(f"  {BOLD}8.{END} 🧬 用schema提取单篇")
            print(f"  {BOLD}9.{END} 🚀 用schema批量提取全部")
            print(f"  {BOLD}10.{END} 📄 列出已解析论文\n")

            print(f"{CYAN}【Web 界面】{END}")
            print(f"  {BOLD}11.{END} 🌐 启动网页（推荐：解析/设计/提取/数据/设置一站式）\n")

            print(f"{CYAN}【数据 / 配置】{END}")
            print(f"  {BOLD}12.{END} 🗂  数据目录概览")
            print(f"  {BOLD}13.{END} 🧩 运行配置摘要\n")

            print(f"  {BOLD}0.{END} 🚪 退出\n")

            choice = input(f"{GREEN}请选择 (0-13): {END}").strip()
            actions = {
                '1': pdf_upload, '2': pdf_status, '3': pdf_download, '4': pdf_stats,
                '5': show_endpoints, '6': schema_design, '7': schema_list,
                '8': schema_extract_single, '9': schema_extract_all, '10': list_parsed,
                '11': launch_web,
                '12': data_layout, '13': runtime_config,
            }
            if choice == '0':
                print(f"\n{BLUE}再见！{END}\n"); sys.exit(0)
            elif choice in actions:
                actions[choice]()
            else:
                print(f"\n{RED}无效选项{END}"); pause()
        except KeyboardInterrupt:
            print(f"\n\n{BLUE}再见！{END}\n"); sys.exit(0)
        except Exception as e:
            print(f"\n{RED}错误: {e}{END}"); pause()


if __name__ == "__main__":
    main_menu()
