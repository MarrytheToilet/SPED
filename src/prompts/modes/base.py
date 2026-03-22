"""
提取模式基类 - 定义提取流程的接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from loguru import logger


@dataclass
class ExtractionResult:
    """提取结果"""
    success: bool
    records: List[Dict[str, Any]] = field(default_factory=list)
    count: int = 0
    error: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "records": self.records,
            "count": self.count,
            "error": self.error,
            "metadata": self.metadata,
        }


class ExtractionMode(ABC):
    """
    提取模式基类
    
    定义提取流程的接口，不同模式实现不同策略
    """
    
    def __init__(self, llm_client, prompt_assembler):
        """
        初始化
        
        Args:
            llm_client: LLM客户端
            prompt_assembler: Prompt组装器
        """
        self.llm_client = llm_client
        self.prompt_assembler = prompt_assembler
        self.logger = logger.bind(module=self.__class__.__name__)
    
    @property
    @abstractmethod
    def mode_name(self) -> str:
        """模式名称"""
        pass
    
    @abstractmethod
    def extract(
        self,
        paper_id: str,
        content: str,
        chunks: List[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """
        执行提取
        
        Args:
            paper_id: 论文ID
            content: 论文全文
            chunks: 分块后的文本列表（可选）
            **kwargs: 其他参数
        
        Returns:
            ExtractionResult
        """
        pass
    
    def _call_llm(
        self,
        system_prompt: str,
        user_prompt: str,
        call_id: str,
        **kwargs
    ) -> Dict[str, Any]:
        """
        调用LLM并解析JSON
        
        Returns:
            {"success": bool, "data": dict, "error": str}
        """
        from src.llm import LLMMessage
        
        messages = [
            LLMMessage(role="system", content=system_prompt),
            LLMMessage(role="user", content=user_prompt),
        ]
        
        response = self.llm_client.call(messages, call_id=call_id, **kwargs)
        
        if not response.success:
            return {"success": False, "data": {}, "error": response.error}
        
        # 解析JSON
        try:
            data = self._parse_json(response.content)
            return {"success": True, "data": data, "error": ""}
        except Exception as e:
            return {"success": False, "data": {}, "error": f"JSON解析失败: {e}"}
    
    def _parse_json(self, content: str) -> Dict[str, Any]:
        """解析LLM返回的JSON"""
        import json
        import re
        
        # 尝试直接解析
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass
        
        # 尝试提取代码块
        patterns = [
            r'```json\s*([\s\S]*?)\s*```',
            r'```\s*([\s\S]*?)\s*```',
            r'\{[\s\S]*\}',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                try:
                    json_str = match.group(1) if '```' in pattern else match.group(0)
                    return json.loads(json_str)
                except (json.JSONDecodeError, IndexError):
                    continue
        
        raise ValueError(f"无法解析JSON: {content[:200]}...")
