#!/usr/bin/env python3
"""
LLM客户端完整测试 - 测试所有供应商的连接

测试项目：
1. SiliconFlow 客户端
2. 智谱AI 客户端
3. 完整提取流程
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.llm import (
    create_llm_client,
    SiliconFlowClient,
    ZhipuClient,
    LLMMessage,
)
import settings


def test_siliconflow():
    """测试SiliconFlow客户端"""
    print("\n" + "=" * 60)
    print("测试 SiliconFlow 客户端")
    print("=" * 60)
    
    try:
        client = create_llm_client(
            model="Pro/moonshotai/Kimi-K2.5",
            provider="siliconflow"
        )
        
        print(f"✅ 客户端创建成功")
        print(f"   类型: {type(client).__name__}")
        print(f"   模型: {client.config.model}")
        print(f"   API: {client.config.api_base}")
        
        # 简单测试
        messages = [
            LLMMessage(role="user", content="请用一句话回答：1+1等于几？")
        ]
        
        print("\n正在测试API连接...")
        response = client.call(messages, call_id="test_siliconflow")
        
        if response.success:
            print(f"✅ API调用成功")
            print(f"   响应: {response.content[:100]}...")
            print(f"   延迟: {response.latency_ms}ms")
            print(f"   Token: {response.usage}")
            return True
        else:
            print(f"❌ API调用失败: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_zhipu():
    """测试智谱AI客户端"""
    print("\n" + "=" * 60)
    print("测试 智谱AI 客户端")
    print("=" * 60)
    
    # 检查API Key
    api_key = settings.AVAILABLE_MODELS.get("glm-4-flash", {}).get("api_key", "")
    if not api_key:
        print("❌ 未配置 ZHIPU_API_KEY")
        return False
    
    try:
        client = create_llm_client(
            model="glm-4-flash",  # 使用flash版本测试（更快更便宜）
            provider="zhipu"
        )
        
        print(f"✅ 客户端创建成功")
        print(f"   类型: {type(client).__name__}")
        print(f"   模型: {client.config.model}")
        print(f"   API: {client.config.api_base}")
        
        # 简单测试
        messages = [
            LLMMessage(role="user", content="请用一句话回答：1+1等于几？")
        ]
        
        print("\n正在测试API连接...")
        response = client.call(messages, call_id="test_zhipu")
        
        if response.success:
            print(f"✅ API调用成功")
            print(f"   响应: {response.content[:100]}...")
            print(f"   延迟: {response.latency_ms}ms")
            print(f"   Token: {response.usage}")
            return True
        else:
            print(f"❌ API调用失败: {response.error}")
            return False
            
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False


def test_extraction_service():
    """测试完整提取服务"""
    print("\n" + "=" * 60)
    print("测试 ExtractionService（完整提取流程）")
    print("=" * 60)
    
    from src.extractors import ExtractionService
    from src.agents.chunk_filter_agent import ChunkFilterAgent
    
    # 查找论文
    parsed_dir = settings.PARSED_DIR
    papers = list(parsed_dir.iterdir()) if parsed_dir.exists() else []
    
    if not papers:
        print("❌ 没有可用论文")
        return False
    
    paper_dir = papers[0]
    paper_id = paper_dir.name
    paper_path = paper_dir / "full.md"
    
    if not paper_path.exists():
        print(f"❌ 论文文件不存在: {paper_path}")
        return False
    
    print(f"论文: {paper_id}")
    
    # 读取和分块
    content = paper_path.read_text(encoding="utf-8")
    print(f"内容长度: {len(content)} 字符")
    
    chunk_filter = ChunkFilterAgent()
    filter_result = chunk_filter.process({
        "paper_id": paper_id,
        "file_path": paper_path
    })
    
    if not filter_result.success:
        print(f"❌ 分块失败: {filter_result.error}")
        return False
    
    filtered_doc = filter_result.data
    chunks = [c.content for c in filtered_doc.chunks if not c.is_filtered]
    print(f"分块数: {len(chunks)}")
    
    # 使用新架构提取
    print("\n开始提取（使用 skeleton_fill 模式）...")
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
        print(f"\n记录示例（第1条）:")
        first_record = result.records[0]
        for key in list(first_record.keys())[:8]:
            value = first_record[key]
            if isinstance(value, dict):
                print(f"  {key}: {list(value.keys())[:3]}...")
            else:
                print(f"  {key}: {str(value)[:50]}")
        return True
    else:
        print(f"  错误: {result.error}")
        return False


def main():
    """运行所有测试"""
    print("=" * 60)
    print("LLM 客户端完整测试")
    print("=" * 60)
    
    results = {}
    
    # 测试SiliconFlow
    results["SiliconFlow"] = test_siliconflow()
    
    # 测试智谱
    results["智谱AI"] = test_zhipu()
    
    # 测试完整提取（可选，耗时较长）
    import sys
    if "--full" in sys.argv:
        results["完整提取"] = test_extraction_service()
    else:
        print("\n提示: 运行 --full 参数测试完整提取流程")
    
    # 总结
    print("\n" + "=" * 60)
    print("测试结果汇总")
    print("=" * 60)
    
    all_passed = True
    for name, passed in results.items():
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"  {name}: {status}")
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("🎉 所有测试通过！")
    else:
        print("⚠️ 部分测试失败")
    
    return all_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
