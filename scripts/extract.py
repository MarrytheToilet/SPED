#!/usr/bin/env python3
"""
人工关节材料数据提取系统 - 数据提取脚本

功能:
1. test   - 测试系统配置和API连接
2. single - 单个论文数据提取（交互式选择）
3. batch  - 批量提取所有论文
4. prompt - 查看当前使用的Prompt

使用:
    python scripts/extract.py test              # 测试系统
    python scripts/extract.py single            # 单个提取
    python scripts/extract.py batch             # 批量提取
    python scripts/extract.py --list-models     # 列出所有模型
"""

import sys
import argparse
from pathlib import Path
from collections import defaultdict

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extractors import PaperScanner, Extractor, InteractiveUI
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
            timeout=10
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


# ==================== 数据提取 ====================

def extract_single_interactive(mode: str = None, model: str = None):
    """交互式单个论文提取"""
    print(f"\n{DIVIDER}")
    print("单个论文数据提取")
    print(f"{DIVIDER}\n")
    
    # 1. 扫描论文
    scanner = PaperScanner(settings.PARSED_DIR)
    papers = scanner.scan()
    
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
    extractor = Extractor(
        output_dir=settings.EXTRACTED_DIR,
        mode=mode,
        model=model
    )
    
    result = extractor.extract_single(paper)
    
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


def extract_batch_interactive(mode: str = None, model: str = None, parallel: bool = True, workers: int = None):
    """交互式批量提取"""
    print(f"\n{DIVIDER}")
    print("批量数据提取")
    print(f"{DIVIDER}\n")
    
    # 1. 扫描论文
    scanner = PaperScanner(settings.PARSED_DIR)
    papers = scanner.scan()
    
    if not papers:
        print("❌ 未找到已解析论文")
        print("   请先使用 scripts/pdf_process.py 解析PDF文件")
        return
    
    print(f"📚 找到 {len(papers)} 篇论文\n")
    
    # 2. 选择模式
    if mode is None:
        mode = InteractiveUI.select_mode()
    else:
        print(f"🔧 模式: {mode}")
    
    # 3. 确认操作
    if not InteractiveUI.confirm_batch(len(papers)):
        print("取消操作")
        return
    
    # 显示并行配置
    if parallel:
        import multiprocessing
        default_workers = min(multiprocessing.cpu_count(), 4)
        actual_workers = workers if workers else default_workers
        print(f"\n⚡ 并行处理: {actual_workers} workers")
    else:
        print(f"\n🔄 串行处理模式")
    
    print(f"\n开始批量提取...\n")
    
    # 4. 配置日志
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    # 5. 批量提取
    extractor = Extractor(
        output_dir=settings.EXTRACTED_DIR,
        mode=mode,
        model=model,
        max_workers=workers
    )
    
    stats = extractor.extract_batch(papers, parallel=parallel)


# ==================== 辅助功能 ====================

def show_prompt():
    """显示Prompt内容预览"""
    prompt_path = project_root / "prompts" / "prompt.md"
    
    if not prompt_path.exists():
        print(f"❌ 未找到Prompt文件: {prompt_path}")
        return
    
    print(f"\n{DIVIDER}")
    print("当前Prompt内容")
    print(f"{DIVIDER}\n")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 显示前2000字符
    preview_length = 2000
    print(content[:preview_length])
    
    if len(content) > preview_length:
        print("\n...")
        print(f"\n(仅显示前 {preview_length} 字符)")
    
    print(f"\n{DIVIDER}")
    print(f"📝 总长度: {len(content):,} 字符")
    print(f"📄 总行数: {len(content.splitlines()):,} 行")
    print(f"📂 文件路径: {prompt_path}")
    print(f"{DIVIDER}\n")


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
            print(f"  {status} {model}")
        
    print(f"\n{DIVIDER}")
    print("💡 提示:")
    print(f"  使用 --model 参数指定模型")
    print(f"  示例: python scripts/extract.py single --model \"Qwen/Qwen2.5-7B-Instruct\"")
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
  
  # 提取单篇论文，使用默认配置
  python scripts/extract.py single
  
  # 提取单篇论文，指定模型
  python scripts/extract.py single --model "Qwen/Qwen2.5-7B-Instruct"
  
  # 批量提取，使用gpt-4o-mini，并行4个worker
  python scripts/extract.py batch --model gpt-4o-mini --workers 4
  
  # 批量提取，使用full模式和特定模型
  python scripts/extract.py batch full --model "Qwen/Qwen2.5-72B-Instruct"
  
  # 批量提取，禁用并行（串行模式）
  python scripts/extract.py batch --no-parallel
  
  # 列出所有可用模型
  python scripts/extract.py --list-models
        '''
    )
    
    parser.add_argument('command', 
                       choices=['test', 'single', 'batch', 'prompt', 'help'],
                       help='要执行的命令')
    parser.add_argument('mode', 
                       nargs='?',
                       choices=['chunk', 'full'],
                       help='提取模式（可选）')
    parser.add_argument('--model', '-m',
                       help='模型名称')
    parser.add_argument('--no-parallel',
                       action='store_true',
                       help='禁用并行处理（仅batch模式）')
    parser.add_argument('--workers', '-w',
                       type=int,
                       default=None,
                       help='并行worker数量（默认=CPU核心数，最大4）')
    
    args = parser.parse_args()
    
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
            workers=args.workers
        )
    
    elif args.command == 'prompt':
        show_prompt()
    
    elif args.command == 'help':
        parser.print_help()
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
