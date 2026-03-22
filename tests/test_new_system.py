#!/usr/bin/env python3
"""
测试新的多Agent系统
"""
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent))

from loguru import logger
from src.agents.base import BaseAgent, AgentResult
from src.workflow import WorkflowOrchestrator
from src.agents.pdf_process_agent import PDFProcessAgent


def test_base_agent():
    """测试基础Agent"""
    print("\n" + "="*60)
    print("测试 1: 基础Agent")
    print("="*60)
    
    class TestAgent(BaseAgent[str, str]):
        def process(self, input_data):
            result = input_data.upper()
            return AgentResult(success=True, data=result)
    
    agent = TestAgent("TestAgent", "测试用Agent")
    result = agent.process("hello world")
    
    print(f"✓ 输入: 'hello world'")
    print(f"✓ 输出: '{result.data}'")
    print(f"✓ 成功: {result.success}")
    assert result.success
    assert result.data == "HELLO WORLD"
    print("✓ 基础Agent测试通过")


def test_pdf_agent():
    """测试PDF Agent"""
    print("\n" + "="*60)
    print("测试 2: PDF Agent")
    print("="*60)
    
    agent = PDFProcessAgent(batch_size=200)
    
    # 获取统计信息
    stats = agent.get_statistics()
    print(f"✓ PDF统计: {stats.get('pdf_files', {})}")
    print(f"✓ 批次统计: {stats.get('batches', {})}")
    
    # 扫描PDF目录
    pdf_dir = Path("data/raw/pdfs")
    if pdf_dir.exists():
        new_pdfs = agent.scan_pdfs(pdf_dir)
        print(f"✓ 扫描PDF: 找到 {len(new_pdfs)} 个新文件")
    else:
        print(f"⚠ PDF目录不存在: {pdf_dir}")
    
    print("✓ PDF Agent测试通过")


def test_workflow():
    """测试工作流编排"""
    print("\n" + "="*60)
    print("测试 3: 工作流编排")
    print("="*60)
    
    # 创建简单的测试Agents
    class Agent1(BaseAgent[int, int]):
        def process(self, data):
            result = data + 1
            self.log_info(f"Agent1: {data} -> {result}")
            return AgentResult(success=True, data=result)
    
    class Agent2(BaseAgent[int, int]):
        def process(self, data):
            result = data * 2
            self.log_info(f"Agent2: {data} -> {result}")
            return AgentResult(success=True, data=result)
    
    class Agent3(BaseAgent[int, str]):
        def process(self, data):
            result = f"Final: {data}"
            self.log_info(f"Agent3: {data} -> {result}")
            return AgentResult(success=True, data=result)
    
    # 创建编排器
    orchestrator = WorkflowOrchestrator("test_workflow")
    
    # 注册Agents
    orchestrator.register_agent("agent1", Agent1("Agent1", "加1"))
    orchestrator.register_agent("agent2", Agent2("Agent2", "乘2"))
    orchestrator.register_agent("agent3", Agent3("Agent3", "转字符串"))
    
    # 设置流程
    orchestrator.set_pipeline(["agent1", "agent2", "agent3"])
    
    # 运行: 10 -> +1=11 -> *2=22 -> "Final: 22"
    result = orchestrator.run_pipeline(initial_data=10)
    
    print(f"✓ 输入: 10")
    print(f"✓ 输出: {result['final_data']}")
    print(f"✓ 成功: {result['success']}")
    print(f"✓ Run ID: {result['run_id']}")
    
    assert result['success']
    assert result['final_data'] == "Final: 22"
    print("✓ 工作流编排测试通过")


def test_state_manager():
    """测试状态管理"""
    print("\n" + "="*60)
    print("测试 4: 状态管理")
    print("="*60)
    
    from src.workflow.state_manager import StateManager
    
    state_manager = StateManager()
    stats = state_manager.get_statistics()
    
    print(f"✓ 总运行次数: {stats['total_runs']}")
    print(f"✓ 总任务数: {stats['total_tasks']}")
    print(f"✓ 状态分布: {stats.get('status_counts', {})}")
    print("✓ 状态管理测试通过")


def main():
    """运行所有测试"""
    logger.remove()  # 移除默认handler
    logger.add(sys.stderr, level="INFO", format="<level>{message}</level>")
    
    print("\n" + "="*60)
    print("   新版多Agent系统 - 功能测试")
    print("="*60)
    
    try:
        test_base_agent()
        test_pdf_agent()
        test_workflow()
        test_state_manager()
        
        print("\n" + "="*60)
        print("   所有测试通过! ✓")
        print("="*60)
        print("\n下一步:")
        print("1. 运行 python workflows/full_pipeline.py 测试完整流程")
        print("2. 查看 REFACTOR_README.md 了解使用方法")
        print("3. 开始实现其他Agent (ChunkFilterAgent, ExtractionAgent等)")
        print()
        
    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
