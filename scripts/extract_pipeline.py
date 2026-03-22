#!/usr/bin/env python3
"""
完整的数据提取工作流 v2

使用新解耦架构：
- ExtractionService 作为主入口
- PromptAssembler 组装提示
- LLMClient 调用模型

使用方式：
    python scripts/extract_pipeline.py single --paper-id "论文名称"
    python scripts/extract_pipeline.py batch
"""
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any
from loguru import logger
import sys

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.extractors import ExtractionService
from src.agents.chunk_filter_agent import ChunkFilterAgent
from settings import PARSED_DIR, EXTRACTED_DIR


def load_paper(paper_id: str) -> Optional[str]:
    """加载论文内容"""
    paper_dir = PARSED_DIR / paper_id
    full_md = paper_dir / "full.md"
    
    if not full_md.exists():
        logger.error(f"找不到论文: {full_md}")
        return None
    
    return full_md.read_text(encoding="utf-8")


def extract_single(
    paper_id: str,
    mode: str = "skeleton_fill",
    model: str = None,
    output_dir: Path = None,
    force: bool = False
) -> bool:
    """
    提取单篇论文
    
    Args:
        paper_id: 论文ID（目录名）
        mode: 提取模式 - skeleton_fill（推荐）或 full
        model: LLM模型名称
        output_dir: 输出目录
        force: 是否强制重新提取
    
    Returns:
        是否成功
    """
    output_dir = output_dir or EXTRACTED_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / f"{paper_id}.json"
    
    # 检查是否已提取
    if output_file.exists() and not force:
        logger.info(f"已存在提取结果: {output_file}")
        return True
    
    # 加载论文
    logger.info(f"加载论文: {paper_id}")
    content = load_paper(paper_id)
    if not content:
        return False
    
    logger.info(f"论文长度: {len(content)} 字符")
    
    # 分块过滤
    logger.info("步骤1: 文档分块过滤")
    filter_agent = ChunkFilterAgent()
    filter_result = filter_agent.process({
        "paper_id": paper_id,
        "content": content
    })
    
    if not filter_result.success:
        logger.error(f"分块失败: {filter_result.error}")
        return False
    
    chunks = filter_result.data.chunks
    logger.info(f"分块完成: {len(chunks)} 个chunks")
    
    # 数据提取
    logger.info(f"步骤2: 数据提取 (mode={mode})")
    service = ExtractionService(mode=mode, model=model)
    
    result = service.extract(
        paper_id=paper_id,
        content=content,
        chunks=chunks
    )
    
    if not result.success:
        logger.error(f"提取失败: {result.error}")
        return False
    
    logger.info(f"提取完成: {result.count} 条记录")
    
    # 保存结果
    output_data = {
        "paper_id": paper_id,
        "records": result.records,
        "count": result.count,
        "mode": result.mode,
        "model": result.model,
        "metadata": result.metadata
    }
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"结果已保存: {output_file}")
    
    # 显示提取摘要
    print(f"\n✅ 提取成功: {result.count} 条记录")
    for i, rec in enumerate(result.records[:3]):  # 只显示前3条
        print(f"  {i+1}. {rec.get('material_name', '?')} ({rec.get('treatment', '?')})")
        tables = [k for k in rec.keys() if k.startswith('Sheet')]
        filled = sum(1 for t in tables if isinstance(rec.get(t), dict) and 
                    any(v and v != '${DATA_ID}' for v in rec[t].values()))
        print(f"     填充表数: {filled}/12")
    
    if result.count > 3:
        print(f"  ... 还有 {result.count - 3} 条记录")
    
    return True


def extract_batch(
    mode: str = "skeleton_fill",
    model: str = None,
    output_dir: Path = None,
    force: bool = False
) -> Dict[str, bool]:
    """
    批量提取所有论文
    
    Returns:
        {paper_id: success} 字典
    """
    # 查找所有已解析的论文
    papers = [d.name for d in PARSED_DIR.iterdir() if d.is_dir() and (d / "full.md").exists()]
    
    if not papers:
        logger.warning("没有找到已解析的论文")
        return {}
    
    logger.info(f"找到 {len(papers)} 篇论文待提取")
    
    results = {}
    for i, paper_id in enumerate(papers):
        print(f"\n{'='*60}")
        print(f"[{i+1}/{len(papers)}] {paper_id}")
        print('='*60)
        
        try:
            results[paper_id] = extract_single(
                paper_id=paper_id,
                mode=mode,
                model=model,
                output_dir=output_dir,
                force=force
            )
        except Exception as e:
            logger.exception(f"提取失败: {paper_id}")
            results[paper_id] = False
    
    # 统计结果
    success = sum(1 for v in results.values() if v)
    failed = len(results) - success
    
    print(f"\n{'='*60}")
    print(f"批量提取完成: 成功 {success}, 失败 {failed}")
    print('='*60)
    
    return results


def main():
    parser = argparse.ArgumentParser(description="人工关节材料数据提取流程")
    parser.add_argument("command", choices=["single", "batch"], help="执行模式")
    parser.add_argument("--paper-id", help="论文ID（single模式必需）")
    parser.add_argument("--mode", default="skeleton_fill", 
                       choices=["skeleton_fill", "full"],
                       help="提取模式（默认: skeleton_fill）")
    parser.add_argument("--model", help="LLM模型名称")
    parser.add_argument("--output-dir", type=Path, help="输出目录")
    parser.add_argument("--force", action="store_true", help="强制重新提取")
    
    args = parser.parse_args()
    
    if args.command == "single":
        if not args.paper_id:
            # 列出可用论文
            papers = [d.name for d in PARSED_DIR.iterdir() if d.is_dir()]
            print("可用论文:")
            for p in papers:
                print(f"  - {p}")
            parser.error("请指定 --paper-id")
        
        success = extract_single(
            paper_id=args.paper_id,
            mode=args.mode,
            model=args.model,
            output_dir=args.output_dir,
            force=args.force
        )
        sys.exit(0 if success else 1)
    
    elif args.command == "batch":
        results = extract_batch(
            mode=args.mode,
            model=args.model,
            output_dir=args.output_dir,
            force=args.force
        )
        failed = sum(1 for v in results.values() if not v)
        sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
