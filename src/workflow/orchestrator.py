"""
工作流编排器 - 协调多个Agent的执行
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger
import uuid

import sys
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.agents.base import BaseAgent, AgentResult
from .state_manager import StateManager


class WorkflowOrchestrator:
    """
    工作流编排器
    
    负责:
    1. Agent注册和管理
    2. 执行流程定义
    3. 状态持久化
    4. 错误处理和重试
    5. 并行执行控制
    """
    
    def __init__(
        self,
        workflow_name: str = "default",
        state_manager: Optional[StateManager] = None
    ):
        self.workflow_name = workflow_name
        self.agents: Dict[str, BaseAgent] = {}
        self.pipeline: List[str] = []
        self.state_manager = state_manager or StateManager()
        self.run_id = None
        
        logger.info(f"工作流编排器已初始化: {workflow_name}")
    
    def register_agent(self, agent_id: str, agent: BaseAgent):
        """注册Agent"""
        if agent_id in self.agents:
            logger.warning(f"Agent ID已存在，将被覆盖: {agent_id}")
        
        self.agents[agent_id] = agent
        logger.info(f"Agent已注册: {agent_id} ({agent.name})")
    
    def set_pipeline(self, agent_ids: List[str]):
        """设置执行流程"""
        for agent_id in agent_ids:
            if agent_id not in self.agents:
                raise ValueError(f"Agent未注册: {agent_id}")
        
        self.pipeline = agent_ids
        logger.info(f"执行流程已设置: {' → '.join(agent_ids)}")
    
    def run_pipeline(
        self,
        initial_data: Any,
        skip_agents: Optional[List[str]] = None,
        stop_on_error: bool = False
    ) -> Dict[str, Any]:
        """运行完整流程"""
        self.run_id = str(uuid.uuid4())
        skip_agents = skip_agents or []
        
        self.state_manager.start_run(
            run_id=self.run_id,
            workflow_name=self.workflow_name,
            pipeline=self.pipeline
        )
        
        logger.info(f"开始执行工作流: {self.workflow_name} (run_id={self.run_id})")
        
        current_data = initial_data
        results = {}
        
        for i, agent_id in enumerate(self.pipeline):
            if agent_id in skip_agents:
                continue
            
            agent = self.agents[agent_id]
            logger.info(f"[{i+1}/{len(self.pipeline)}] 执行Agent: {agent_id}")
            
            try:
                result = agent.process(current_data)
                results[agent_id] = result
                
                if result.success:
                    current_data = result.data
                else:
                    logger.error(f"Agent执行失败: {agent_id} - {result.error}")
                    if stop_on_error:
                        break
                        
            except Exception as e:
                logger.exception(f"Agent执行异常: {agent_id}")
                results[agent_id] = AgentResult(success=False, error=str(e))
                if stop_on_error:
                    break
        
        success = all(r.success for r in results.values() if isinstance(r, AgentResult))
        self.state_manager.complete_run(self.run_id, success)
        
        return {
            "run_id": self.run_id,
            "success": success,
            "results": results,
            "final_data": current_data
        }
    
    def run_single_agent(self, agent_id: str, input_data: Any) -> AgentResult:
        """运行单个Agent"""
        if agent_id not in self.agents:
            raise ValueError(f"Agent未注册: {agent_id}")
        
        return self.agents[agent_id].process(input_data)
    
    def get_status(self) -> Dict[str, Any]:
        """获取工作流状态"""
        return {
            "workflow_name": self.workflow_name,
            "registered_agents": list(self.agents.keys()),
            "pipeline": self.pipeline,
            "current_run_id": self.run_id
        }
