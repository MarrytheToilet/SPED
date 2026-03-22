#!/usr/bin/env python3
"""
使用新解耦架构的提取示例

展示如何使用：
1. ExtractionService - 高层API
2. 自定义 LLMClient + PromptAssembler 组合
"""
import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.extractors import ExtractionService, extract_paper
from src.llm import create_llm_client
from src.prompts import PromptAssembler
from src.agents.chunk_filter_agent import ChunkFilterAgent

from settings import PARSED_DIR, EXTRACTED_DIR
import json


def example_simple():
    """
    示例1: 最简单的使用方式
    """
    print("=" * 60)
    print("示例1: 简单使用 ExtractionService")
    print("=" * 60)
    
    # 一行代码创建服务
    service = ExtractionService(mode="skeleton_fill")
    
    print(f"模式: {service.mode}")
    print(f"模型: {service.llm_client.config.model}")
    print(f"供应商: {service.llm_client.config.provider}")


def example_custom_client():
    """
    示例2: 自定义LLM客户端
    """
    print("\n" + "=" * 60)
    print("示例2: 自定义 LLM 客户端")
    print("=" * 60)
    
    # 创建智谱客户端（需要配置 ZHIPU_API_KEY）
    # client = create_llm_client(model="glm-5", provider="zhipu")
    
    # 或使用SiliconFlow
    client = create_llm_client(model="Pro/moonshotai/Kimi-K2.5")
    
    print(f"客户端: {client.config.model}")
    
    # 使用自定义客户端创建服务
    service = ExtractionService(
        mode="full",
        llm_client=client,
    )
    
    print(f"服务模式: {service.mode}")


def example_full_extraction():
    """
    示例3: 完整的提取流程
    """
    print("\n" + "=" * 60)
    print("示例3: 完整提取流程")
    print("=" * 60)
    
    # 查找论文
    papers = list(PARSED_DIR.iterdir())
    if not papers:
        print("❌ 没有可用论文")
        return
    
    paper_dir = papers[0]
    paper_id = paper_dir.name
    paper_path = paper_dir / "full.md"
    
    if not paper_path.exists():
        print(f"❌ 论文文件不存在: {paper_path}")
        return
    
    print(f"论文: {paper_id}")
    
    # 读取内容
    content = paper_path.read_text(encoding="utf-8")
    print(f"内容长度: {len(content)} 字符")
    
    # 分块
    chunk_filter = ChunkFilterAgent()
    filter_result = chunk_filter.process({
        "paper_id": paper_id,
        "file_path": paper_path
    })
    
    if not filter_result.success:
        print(f"❌ 分块失败: {filter_result.error}")
        return
    
    filtered_doc = filter_result.data
    chunks = [c.content for c in filtered_doc.chunks if not c.is_filtered]
    print(f"分块数: {len(chunks)}")
    
    # 提取
    service = ExtractionService(mode="skeleton_fill")
    result = service.extract(
        paper_id=paper_id,
        content=content,
        chunks=chunks,
    )
    
    print(f"\n提取结果:")
    print(f"  成功: {result.success}")
    print(f"  记录数: {result.count}")
    print(f"  模式: {result.mode}")
    print(f"  模型: {result.model}")
    
    if result.success and result.records:
        print(f"\n第一条记录的表:")
        for key in list(result.records[0].keys())[:5]:
            print(f"    - {key}")


def example_convenient_function():
    """
    示例4: 便捷函数
    """
    print("\n" + "=" * 60)
    print("示例4: 使用便捷函数 extract_paper()")
    print("=" * 60)
    
    # extract_paper 是最简单的调用方式
    # result = extract_paper(
    #     paper_id="test",
    #     content="论文内容...",
    #     mode="full",
    # )
    
    print("便捷函数签名:")
    print("  extract_paper(paper_id, content, chunks=None, mode='skeleton_fill', model=None)")


if __name__ == "__main__":
    example_simple()
    example_custom_client()
    # example_full_extraction()  # 需要较长时间，取消注释运行
    example_convenient_function()
    
    print("\n" + "=" * 60)
    print("✅ 示例完成")
    print("=" * 60)
