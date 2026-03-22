#!/usr/bin/env python3
"""
人工关节材料数据提取系统 - 数据提取脚本

功能:
1. test   - 测试系统配置和API连接
2. single - 单个论文数据提取（交互式选择）
3. batch  - 批量提取所有论文
4. add-doi - 为所有论文添加DOI信息

使用:
    python scripts/extract.py test              # 测试系统
    python scripts/extract.py single            # 单个提取
    python scripts/extract.py batch             # 批量提取
    python scripts/extract.py batch --force     # 强制重新提取所有
    python scripts/extract.py add-doi           # 添加DOI到所有论文
    python scripts/extract.py --list-models     # 列出所有模型
"""

import sys
import argparse
import json
import time
from pathlib import Path
from collections import defaultdict
from datetime import datetime

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extractors import PaperScanner, InteractiveUI, ExtractionService
from src.agents.chunk_filter_agent import ChunkFilterAgent
from src.utils.doi_extractor import DOIExtractor
from src.utils.concurrency import ConcurrencyController, BatchStats
from loguru import logger
import settings


# ==================== 常量 ====================
DIVIDER = "=" * 80


# ==================== 系统测试 ====================

def test_system() -> bool:
    """测试系统配置和API连接"""
    print(f"\n{DIVIDER}")
    print("系统配置测试")
    print(f"{DIVIDER}\n")
    
    all_passed = True
    
    # 1. 检查LLM配置
    print("1. LLM配置")
    print(f"   默认模型: {settings.DEFAULT_MODEL}")
    print(f"   API Base: {settings.OPENAI_API_BASE}")
    print(f"   API Key: {settings.OPENAI_API_KEY[:20]}..." if settings.OPENAI_API_KEY else "   ❌ 未配置")
    
    if not settings.OPENAI_API_KEY:
        print("   ❌ API密钥未配置")
        all_passed = False
    else:
        print("   ✅ 已配置")
    
    # 2. 检查目录结构
    print("\n2. 目录结构")
    required_dirs = {
        "数据目录": settings.DATA_DIR,
        "解析目录": settings.PARSED_DIR,
        "提取目录": settings.EXTRACTED_DIR,
    }
    
    for name, path in required_dirs.items():
        exists = path.exists()
        status = "✅" if exists else "❌"
        print(f"   {status} {name}: {path}")
        if not exists:
            all_passed = False
    
    # 3. 扫描论文
    print("\n3. 已解析论文")
    scanner = PaperScanner(settings.PARSED_DIR)
    papers = scanner.scan()
    print(f"   找到 {len(papers)} 篇论文")
    
    if papers:
        print("   前5篇:")
        for paper in papers[:5]:
            print(f"     • {paper['name']}")
        if len(papers) > 5:
            print(f"     ... 还有 {len(papers)-5} 篇")
    
    # 4. 测试API连接
    print("\n4. API连接测试")
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.OPENAI_API_BASE
        )
        
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": "Hi"}],
            max_tokens=10,
            timeout=30
        )
        print(f"   ✅ API连接正常 (模型: {settings.OPENAI_MODEL})")
        
    except Exception as e:
        print(f"   ❌ API连接失败: {e}")
        all_passed = False
    
    # 总结
    print(f"\n{DIVIDER}")
    if all_passed:
        print("✅ 所有测试通过")
    else:
        print("❌ 部分测试失败，请检查配置")
    print(f"{DIVIDER}\n")
    
    return all_passed


# ==================== 单论文提取 ====================

def extract_single_paper(
    paper: dict, 
    mode: str = "skeleton_fill", 
    model: str = None, 
    output_dir: Path = None,
    worker_id: int = None,
) -> dict:
    """
    提取单个论文（使用新的ExtractionService）
    
    Args:
        paper: 论文信息 {name, path, full_md}
        mode: 提取模式
        model: 模型名称
        output_dir: 输出目录
        worker_id: 并发worker编号（用于负载均衡）
    
    Returns:
        dict: {"status": "success"/"failed", "count": int, "error": str}
    """
    paper_id = paper["name"]
    output_dir = output_dir or settings.EXTRACTED_DIR
    output_file = output_dir / f"{paper_id}.json"
    
    try:
        # 1. 读取论文内容
        full_md_path = paper.get("full_md") or (Path(paper["path"]) / "full.md")
        with open(full_md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 2. 分块过滤
        filter_agent = ChunkFilterAgent()
        filter_result = filter_agent.process({
            "paper_id": paper_id,
            "content": content
        })
        
        if not filter_result.success:
            return {"status": "failed", "error": f"分块失败: {filter_result.error}"}
        
        chunks = filter_result.data.chunks
        
        # 3. 数据提取（支持负载均衡）
        service = ExtractionService(mode=mode, model=model, worker_id=worker_id)
        result = service.extract(
            paper_id=paper_id,
            content=content,
            chunks=chunks
        )
        
        if not result.success:
            return {"status": "failed", "error": result.error}
        
        # 4. 保存结果
        output_data = {
            "paper_id": paper_id,
            "records": result.records,
            "count": result.count,
            "mode": result.mode,
            "model": result.model,
            "metadata": result.metadata,
            "extracted_at": datetime.now().isoformat()
        }
        
        output_dir.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        return {"status": "success", "count": result.count, "result": result}
    
    except Exception as e:
        logger.error(f"提取失败: {paper_id} - {e}")
        return {"status": "failed", "error": str(e)}


def extract_single_interactive(mode: str = None, model: str = None):
    """交互式单个论文提取"""
    print(f"\n{DIVIDER}")
    print("单个论文数据提取")
    print(f"{DIVIDER}\n")
    
    # 1. 扫描论文
    scanner = PaperScanner(settings.PARSED_DIR)
    papers = scanner.scan()
    
    if not papers:
        print("❌ 未找到已解析论文")
        return
    
    # 2. 选择论文
    paper = InteractiveUI.select_paper(papers)
    if not paper:
        return
    
    # 3. 选择模式
    if mode is None:
        print(f"\n📄 论文: {paper['name']}")
        print(f"📂 路径: {paper['path']}\n")
        mode = InteractiveUI.select_mode()
    else:
        print(f"\n📄 论文: {paper['name']}")
        print(f"📂 路径: {paper['path']}")
        print(f"🔧 模式: {mode}\n")
    
    print(f"开始提取数据...\n")
    
    # 4. 配置日志
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # 5. 提取数据
    result = extract_single_paper(paper, mode=mode, model=model)
    
    # 6. 显示结果
    print(f"\n{DIVIDER}")
    print("📊 提取结果")
    print(f"{DIVIDER}\n")
    
    if result["status"] == "success":
        print(f"✅ 提取到 {result.get('count', 0)} 条记录")
    else:
        print(f"❌ 提取失败: {result.get('error', '未知错误')}")
    
    print(f"\n{DIVIDER}")
    print("✅ 提取完成！")
    print(f"📁 结果已保存: {settings.EXTRACTED_DIR / paper['name']}.json")
    print(f"{DIVIDER}\n")


# ==================== 批量提取 ====================

def extract_batch_interactive(
    mode: str = None, 
    model: str = None, 
    parallel: bool = True, 
    workers: int = None,
    skip_existing: bool = True,
    rate_limit: float = None,
    auto_confirm: bool = False,
):
    """
    批量提取所有论文
    
    Args:
        mode: 提取模式
        model: 模型名称
        parallel: 是否并行处理
        workers: 并行worker数量
        skip_existing: 是否跳过已提取的论文
        rate_limit: 每秒最大请求数
        auto_confirm: 是否自动确认（跳过交互确认）
    """
    print(f"\n{DIVIDER}")
    print("批量数据提取")
    print(f"{DIVIDER}\n")
    
    # 1. 扫描论文
    scanner = PaperScanner(settings.PARSED_DIR)
    papers = scanner.scan()
    
    if not papers:
        print("❌ 未找到已解析论文")
        print("   请先使用 PDF处理 功能解析PDF文件")
        return
    
    print(f"📚 找到 {len(papers)} 篇论文")
    
    # 2. 过滤已提取的（智能过滤：失败或空记录的论文仍可重新提取）
    if skip_existing:
        papers_to_process = []
        skipped_count = 0
        retry_count = 0
        
        for p in papers:
            json_file = settings.EXTRACTED_DIR / f"{p['name']}.json"
            if json_file.exists():
                # 检查JSON内容，判断是否需要重新提取
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    
                    # 判断是否是有效提取（有记录且无错误）
                    has_records = data.get("count", 0) > 0 or len(data.get("records", [])) > 0
                    has_error = "error" in data or data.get("success") == False
                    
                    if has_records and not has_error:
                        # 成功提取且有数据，跳过
                        skipped_count += 1
                    else:
                        # 失败或空记录，加入重试队列
                        papers_to_process.append(p)
                        retry_count += 1
                except (json.JSONDecodeError, Exception):
                    # JSON损坏，需要重新提取
                    papers_to_process.append(p)
                    retry_count += 1
            else:
                # 文件不存在，需要提取
                papers_to_process.append(p)
        
        print(f"   跳过已成功提取: {skipped_count} 篇")
        if retry_count > 0:
            print(f"   重试（失败/空记录）: {retry_count} 篇")
        print(f"   待处理: {len(papers_to_process)} 篇")
    else:
        papers_to_process = papers
        skipped_count = 0
        print(f"   强制模式: 全部重新提取")
    
    if not papers_to_process:
        print("\n✅ 没有需要处理的论文")
        return
    
    # 3. 选择模式
    if mode is None:
        mode = InteractiveUI.select_mode()
    else:
        print(f"\n🔧 模式: {mode}")
    
    # 4. 确认操作
    if not auto_confirm and not InteractiveUI.confirm_batch(len(papers_to_process)):
        print("取消操作")
        return
    
    # 5. 配置worker数量
    import multiprocessing
    if workers is None:
        if settings.DEFAULT_WORKERS is not None:
            workers = settings.DEFAULT_WORKERS
        else:
            workers = min(multiprocessing.cpu_count(), settings.MAX_WORKERS)
    
    # 6. 使用并发控制器执行提取
    print(f"\n开始批量提取...")
    
    if parallel and len(papers_to_process) > 1:
        print(f"⚡ 并行处理: {workers} workers")
        if rate_limit:
            print(f"🚦 速率限制: {rate_limit} 请求/秒")
        print()
        
        # 进度显示回调
        def on_progress(completed: int, total: int, result):
            status = "✓" if result.success else "✗"
            count = result.result.get("count", 0) if result.result and result.success else 0
            if result.success:
                print(f"[{completed}/{total}] {status} {result.task_id} - {count} 条记录 ({result.duration:.1f}s)")
            else:
                print(f"[{completed}/{total}] {status} {result.task_id} - {result.error[:50]}")
        
        # 获取最小间隔配置
        min_interval = getattr(settings, 'LLM_MIN_INTERVAL', 3.0)
        
        # 创建并发控制器
        controller = ConcurrencyController(
            max_workers=workers,
            rate_limit=rate_limit,
            min_interval=min_interval,  # 从配置读取请求间隔
            retry_count=1,
            retry_delay=10.0,  # 重试延迟增加到10秒
            on_progress=on_progress,
        )
        
        # 显示API Key轮询状态
        from src.llm import get_key_rotator
        provider = getattr(settings, 'LLM_PROVIDER', 'siliconflow')
        rotator = get_key_rotator(provider)
        if rotator.key_count > 1:
            print(f"🔄 API Key轮询: {rotator.key_count} 个Key可用")
        print(f"⏱️  请求间隔: {min_interval}秒")
        
        # 使用线程局部变量传递worker_id
        import threading
        _worker_counter = {"value": 0}
        _counter_lock = threading.Lock()
        
        def extract_wrapper(paper):
            # 为每个worker分配一个ID
            with _counter_lock:
                worker_id = _worker_counter["value"]
                _worker_counter["value"] = (worker_id + 1) % workers
            return extract_single_paper(paper, mode=mode, model=model, worker_id=worker_id)
        
        # 执行批量提取
        batch_stats = controller.execute_batch(
            papers_to_process,
            extract_wrapper,
            id_func=lambda p: p["name"]
        )
        
        # 转换统计格式
        stats = {
            "success": batch_stats.success,
            "failed": batch_stats.failed,
            "total_records": sum(
                r.result.get("count", 0) 
                for r in batch_stats.results 
                if r.success and r.result
            ),
            "errors": [
                {"paper_id": r.task_id, "error": r.error}
                for r in batch_stats.results
                if not r.success
            ],
            "duration": batch_stats.total_duration
        }
    else:
        print(f"🔄 串行处理\n")
        stats = _extract_batch_sequential(papers_to_process, mode, model)
    
    # 7. 显示总结
    stats["skipped_existing"] = skipped_count
    _print_summary(stats)


def _extract_batch_sequential(papers: list, mode: str, model: str) -> dict:
    """串行批量提取"""
    stats = {"success": 0, "failed": 0, "total_records": 0, "errors": [], "duration": 0}
    start_time = time.time()
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{'─'*60}")
        print(f"[{i}/{len(papers)}] {paper['name']}")
        print(f"{'─'*60}")
        
        result = extract_single_paper(paper, mode=mode, model=model)
        
        if result["status"] == "success":
            stats["success"] += 1
            stats["total_records"] += result.get("count", 0)
            print(f"✅ 成功: {result.get('count', 0)} 条记录")
        else:
            stats["failed"] += 1
            stats["errors"].append({"paper_id": paper["name"], "error": result.get("error")})
            print(f"❌ 失败: {result.get('error')}")
        
        # 避免API限流
        if i < len(papers):
            time.sleep(2)
    
    stats["duration"] = time.time() - start_time
    return stats


def _print_summary(stats: dict):
    """打印总结"""
    print(f"\n{DIVIDER}")
    print("📊 批量提取完成")
    print(f"{DIVIDER}")
    print(f"✅ 成功: {stats['success']} 篇")
    print(f"❌ 失败: {stats['failed']} 篇")
    print(f"⏭️  跳过: {stats.get('skipped_existing', 0)} 篇")
    print(f"📝 总记录数: {stats['total_records']} 条")
    print(f"⏱️  耗时: {stats.get('duration', 0):.1f} 秒")
    print(f"📂 保存位置: {settings.EXTRACTED_DIR}")
    
    if stats["errors"]:
        print(f"\n失败的论文:")
        for err in stats["errors"][:10]:
            print(f"  • {err['paper_id']}: {err['error'][:50] if err['error'] else '未知错误'}")
        if len(stats["errors"]) > 10:
            print(f"  ... 还有 {len(stats['errors']) - 10} 个失败")
    
    print(f"{DIVIDER}\n")


# ==================== DOI提取 ====================

def add_doi_to_all():
    """为所有论文添加DOI信息"""
    print(f"\n{DIVIDER}")
    print("DOI提取与添加")
    print(f"{DIVIDER}\n")
    
    stats = DOIExtractor.process_all_papers(settings.PARSED_DIR)
    
    print(f"\n处理完成:")
    print(f"  总数: {stats['total']}")
    print(f"  成功添加: {stats['success']}")
    print(f"  已有DOI: {stats['already_has_doi']}")
    print(f"  未找到DOI: {stats['no_doi_found']}")
    print(f"  失败: {stats['failed']}")
    
    print(f"\n{DIVIDER}\n")


# ==================== 辅助功能 ====================

def list_models():
    """列出所有可用模型"""
    print(f"\n{DIVIDER}")
    print("可用的模型")
    print(f"{DIVIDER}\n")
    
    models = settings.list_available_models()
    
    # 按provider分组显示
    by_provider = defaultdict(list)
    for model, info in models.items():
        by_provider[info['provider']].append((model, info))
    
    for provider in sorted(by_provider.keys()):
        print(f"\n【{provider.upper()}】")
        for model, info in by_provider[provider]:
            status = "✅" if info['has_key'] else "❌"
            default_mark = " (默认)" if model == settings.DEFAULT_MODEL else ""
            print(f"  {status} {model}{default_mark}")
        
    print(f"\n{DIVIDER}")
    print("💡 提示:")
    print(f"  使用 --model 参数指定模型")
    print(f"  示例: python scripts/extract.py single --model gpt-4o")
    print(f"{DIVIDER}\n")


# ==================== 主函数 ====================

def main():
    """主函数 - 命令行入口"""
    # 检查是否需要列出模型
    if '--list-models' in sys.argv:
        list_models()
        return
    
    parser = argparse.ArgumentParser(
        description='人工关节材料数据提取系统',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
示例:
  # 测试系统
  python scripts/extract.py test
  
  # 提取单篇论文
  python scripts/extract.py single
  
  # 批量提取（增量模式，跳过已提取）
  python scripts/extract.py batch
  
  # 批量提取（强制全部重新提取）
  python scripts/extract.py batch --force
  
  # 使用指定模型和并行数
  python scripts/extract.py batch --model gpt-4o --workers 4
  
  # 设置速率限制（每秒最多2个请求）
  python scripts/extract.py batch --rate-limit 2
  
  # 禁用并行处理
  python scripts/extract.py batch --no-parallel
  
  # 为所有论文添加DOI信息
  python scripts/extract.py add-doi
  
  # 列出所有可用模型
  python scripts/extract.py --list-models
        '''
    )
    
    parser.add_argument('command', 
                       choices=['test', 'single', 'batch', 'add-doi'],
                       help='要执行的命令')
    parser.add_argument('--mode', '-M',
                       choices=['skeleton_fill', 'full', 'chunk'],
                       default='skeleton_fill',
                       help='提取模式（默认: skeleton_fill）: skeleton_fill=两阶段骨架填充（推荐）, full=一次性提取, chunk=分块提取')
    parser.add_argument('--model', '-m',
                       help='模型名称')
    parser.add_argument('--force', '-f',
                       action='store_true',
                       help='强制重新提取所有论文（默认跳过已提取）')
    parser.add_argument('--no-parallel',
                       action='store_true',
                       help='禁用并行处理')
    parser.add_argument('--workers', '-w',
                       type=int,
                       default=None,
                       help='并行worker数量（默认=CPU核心数，最大4）')
    parser.add_argument('--rate-limit', '-r',
                       type=float,
                       default=None,
                       help='每秒最大请求数（速率限制）')
    parser.add_argument('--yes', '-y',
                       action='store_true',
                       help='跳过确认提示，自动开始')
    
    args = parser.parse_args()
    
    # 配置日志
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # 路由到对应功能
    if args.command == 'test':
        test_system()
    
    elif args.command == 'single':
        extract_single_interactive(mode=args.mode, model=args.model)
    
    elif args.command == 'batch':
        extract_batch_interactive(
            mode=args.mode, 
            model=args.model,
            parallel=not args.no_parallel,
            workers=args.workers,
            skip_existing=not args.force,
            rate_limit=args.rate_limit,
            auto_confirm=args.yes,
        )
    
    elif args.command == 'add-doi':
        add_doi_to_all()


if __name__ == "__main__":
    main()
