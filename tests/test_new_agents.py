#!/usr/bin/env python3
"""
测试新Agent系统

测试内容:
1. ChunkFilterAgent - 文档切分和过滤
2. PromptBuilderAgent - Prompt组装
3. ExtractionAgent - 数据提取
4. 完整流程测试
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.agents.chunk_filter_agent import ChunkFilterAgent
from src.agents.prompt_builder_agent import PromptBuilderAgent, PromptMode
from src.agents.extraction_agent import ExtractionAgent
from workflows.full_extraction_pipeline import FullExtractionPipeline
from settings import PARSED_DIR
from loguru import logger


def test_chunk_filter_agent():
    """测试ChunkFilterAgent"""
    print("\n" + "="*70)
    print("测试1: ChunkFilterAgent - 文档切分和过滤")
    print("="*70)
    
    # 查找一个测试论文
    test_papers = list(PARSED_DIR.glob("*/full.md"))
    if not test_papers:
        print("❌ 未找到测试论文")
        return False
    
    test_paper = test_papers[0]
    paper_id = test_paper.parent.name
    
    print(f"测试论文: {paper_id}")
    print(f"文件路径: {test_paper}")
    
    # 初始化Agent
    agent = ChunkFilterAgent(chunk_size=5000, chunk_overlap=200)
    
    # 处理
    result = agent.process({
        "paper_id": paper_id,
        "file_path": test_paper
    })
    
    if not result.success:
        print(f"❌ 处理失败: {result.error}")
        return False
    
    doc = result.data
    
    print(f"\n✅ 处理成功:")
    print(f"   论文ID: {doc.paper_id}")
    print(f"   标题: {doc.metadata.title or 'N/A'}")
    print(f"   DOI: {doc.metadata.doi or 'N/A'}")
    print(f"   摘要: {'是' if doc.metadata.abstract else '否'}")
    print(f"   原始字符数: {doc.total_chars:,}")
    print(f"   有效字符数: {doc.effective_chars:,}")
    print(f"   过滤率: {(1 - doc.effective_chars/doc.total_chars)*100:.1f}%")
    print(f"   分块数: {len(doc.chunks)}")
    print(f"   过滤章节: {doc.filtered_sections}")
    
    # 显示前3个chunks
    print(f"\n前3个chunks:")
    for i, chunk in enumerate(doc.chunks[:3]):
        print(f"\n  Chunk {i}:")
        print(f"    ID: {chunk.chunk_id}")
        print(f"    章节: {chunk.section}")
        print(f"    字符数: {chunk.char_count}")
        print(f"    内容预览: {chunk.content[:100]}...")
    
    return True


def test_prompt_builder_agent():
    """测试PromptBuilderAgent"""
    print("\n" + "="*70)
    print("测试2: PromptBuilderAgent - Prompt组装")
    print("="*70)
    
    agent = PromptBuilderAgent()
    
    # 测试FULL模式
    print("\n测试FULL模式:")
    result = agent.process({
        "mode": "full",
        "paper_text": "这是一个测试论文内容..."
    })
    
    if not result.success:
        print(f"❌ FULL模式失败: {result.error}")
        return False
    
    prompt = result.data
    print(f"✅ FULL模式成功:")
    print(f"   模式: {prompt.mode}")
    print(f"   总长度: {len(prompt.full_prompt):,} 字符")
    print(f"   系统Prompt长度: {len(prompt.system_prompt):,}")
    print(f"   用户Prompt长度: {len(prompt.user_prompt):,}")
    
    # 测试CHUNK模式
    print("\n测试CHUNK模式:")
    result = agent.process({
        "mode": "chunk",
        "chunk_text": "这是一个chunk...",
        "chunk_index": 0,
        "total_chunks": 5
    })
    
    if not result.success:
        print(f"❌ CHUNK模式失败: {result.error}")
        return False
    
    print(f"✅ CHUNK模式成功:")
    print(f"   总长度: {len(result.data.full_prompt):,} 字符")
    
    # 测试GLOBAL_FIRST模式
    print("\n测试GLOBAL_FIRST模式:")
    result = agent.process({
        "mode": "global_first",
        "paper_text": "测试论文..."
    })
    
    if not result.success:
        print(f"❌ GLOBAL_FIRST模式失败: {result.error}")
        return False
    
    print(f"✅ GLOBAL_FIRST模式成功:")
    print(f"   总长度: {len(result.data.full_prompt):,} 字符")
    
    return True


def test_extraction_agent():
    """测试ExtractionAgent（不实际调用LLM）"""
    print("\n" + "="*70)
    print("测试3: ExtractionAgent - 初始化和配置")
    print("="*70)
    
    try:
        # 测试不同模式的初始化
        agent_full = ExtractionAgent(mode="full")
        print(f"✅ FULL模式Agent初始化成功")
        print(f"   模型: {agent_full.model}")
        print(f"   API Base: {agent_full.api_base}")
        
        agent_chunk = ExtractionAgent(mode="chunk")
        print(f"✅ CHUNK模式Agent初始化成功")
        
        agent_global = ExtractionAgent(mode="global_first")
        print(f"✅ GLOBAL_FIRST模式Agent初始化成功")
        
        return True
    
    except Exception as e:
        print(f"❌ 初始化失败: {e}")
        return False


def test_full_pipeline():
    """测试完整流程（不实际调用LLM）"""
    print("\n" + "="*70)
    print("测试4: 完整流程 - 流程集成")
    print("="*70)
    
    try:
        # 初始化流程
        pipeline = FullExtractionPipeline(mode="full")
        
        print(f"✅ 流程初始化成功")
        print(f"   模式: {pipeline.mode}")
        print(f"   模型: {pipeline.model}")
        print(f"   输出目录: {pipeline.output_dir}")
        
        # 检查组件
        print(f"\n组件检查:")
        print(f"   ChunkFilterAgent: {'✅' if pipeline.chunk_filter else '❌'}")
        print(f"   PromptBuilderAgent: {'✅' if pipeline.prompt_builder else '❌'}")
        print(f"   ExtractionAgent: {'✅' if pipeline.extraction_agent else '❌'}")
        
        return True
    
    except Exception as e:
        print(f"❌ 流程初始化失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("\n" + "="*70)
    print("🚀 新Agent系统测试")
    print("="*70)
    
    results = {}
    
    # 测试1: ChunkFilterAgent
    try:
        results["chunk_filter"] = test_chunk_filter_agent()
    except Exception as e:
        print(f"❌ ChunkFilterAgent测试异常: {e}")
        results["chunk_filter"] = False
    
    # 测试2: PromptBuilderAgent
    try:
        results["prompt_builder"] = test_prompt_builder_agent()
    except Exception as e:
        print(f"❌ PromptBuilderAgent测试异常: {e}")
        results["prompt_builder"] = False
    
    # 测试3: ExtractionAgent
    try:
        results["extraction"] = test_extraction_agent()
    except Exception as e:
        print(f"❌ ExtractionAgent测试异常: {e}")
        results["extraction"] = False
    
    # 测试4: 完整流程
    try:
        results["full_pipeline"] = test_full_pipeline()
    except Exception as e:
        print(f"❌ 完整流程测试异常: {e}")
        results["full_pipeline"] = False
    
    # 汇总结果
    print("\n" + "="*70)
    print("📊 测试结果汇总")
    print("="*70)
    
    total = len(results)
    passed = sum(1 for r in results.values() if r)
    
    for name, passed_test in results.items():
        status = "✅ 通过" if passed_test else "❌ 失败"
        print(f"{status}  {name}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    if passed == total:
        print("\n🎉 所有测试通过！新Agent系统工作正常。")
        return 0
    else:
        print(f"\n⚠️  {total - passed} 个测试失败，请检查错误信息。")
        return 1


if __name__ == "__main__":
    exit(main())
