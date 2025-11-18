"""
基础Agent - 所有Agent的基类
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from loguru import logger
import json


class BaseAgent(ABC):
    """Agent基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.memory = []  # 对话历史
        
    @abstractmethod
    def process(self, input_data: Any) -> Dict[str, Any]:
        """
        处理输入数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果字典
        """
        pass
    
    def add_to_memory(self, role: str, content: str):
        """添加到记忆"""
        self.memory.append({"role": role, "content": content})
    
    def clear_memory(self):
        """清空记忆"""
        self.memory = []
    
    def log_info(self, message: str):
        """记录信息日志"""
        logger.info(f"[{self.name}] {message}")
    
    def log_warning(self, message: str):
        """记录警告日志"""
        logger.warning(f"[{self.name}] {message}")
    
    def log_error(self, message: str):
        """记录错误日志"""
        logger.error(f"[{self.name}] {message}")
    
    def log_debug(self, message: str):
        """记录调试日志"""
        logger.debug(f"[{self.name}] {message}")
    
    def save_result(self, result: Dict[str, Any], output_path: str):
        """保存结果到JSON文件"""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        self.log_info(f"结果已保存到: {output_path}")


class AgentOrchestrator:
    """Agent编排器 - 协调多个Agent的工作"""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.pipeline: List[str] = []
    
    def register_agent(self, agent_name: str, agent: BaseAgent):
        """注册Agent"""
        self.agents[agent_name] = agent
        logger.info(f"Agent已注册: {agent_name} - {agent.description}")
    
    def set_pipeline(self, agent_names: List[str]):
        """设置处理流程"""
        self.pipeline = agent_names
        logger.info(f"处理流程: {' → '.join(agent_names)}")
    
    def run_pipeline(self, initial_data: Any) -> Dict[str, Any]:
        """
        运行完整的处理流程
        
        Args:
            initial_data: 初始输入数据
            
        Returns:
            最终处理结果
        """
        current_data = initial_data
        results = {}
        
        for agent_name in self.pipeline:
            if agent_name not in self.agents:
                logger.error(f"Agent不存在: {agent_name}")
                continue
            
            agent = self.agents[agent_name]
            logger.info(f"执行Agent: {agent_name}")
            
            try:
                result = agent.process(current_data)
                results[agent_name] = result
                current_data = result  # 将结果传递给下一个Agent
            except Exception as e:
                logger.error(f"Agent执行失败 [{agent_name}]: {str(e)}")
                results[agent_name] = {"error": str(e)}
        
        return results
