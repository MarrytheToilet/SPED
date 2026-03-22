"""
LLM调用层 - 与业务逻辑解耦的模型调用接口

设计原则：
1. 不关心业务逻辑，只负责调用模型
2. 统一的接口，屏蔽不同供应商差异
3. 内置重试、超时、日志功能
4. 支持多API Key负载均衡

支持的供应商：
- SiliconFlow (SiliconFlowClient)
- 智谱AI (ZhipuClient)
- OpenAI及兼容API (OpenAICompatibleClient)
"""

from .base import LLMClient, LLMResponse, LLMConfig, LLMMessage
from .factory import create_llm_client, create_llm_client_for_worker, report_api_result
from .siliconflow_client import SiliconFlowClient
from .zhipu_client import ZhipuClient
from .openai_client import OpenAICompatibleClient
from .load_balancer import (
    APIKeyRotator,
    APIKey,
    get_key_rotator,
    reset_rotators,
)

__all__ = [
    "LLMClient",
    "LLMResponse",
    "LLMConfig",
    "LLMMessage",
    "create_llm_client",
    "create_llm_client_for_worker",
    "report_api_result",
    "SiliconFlowClient",
    "ZhipuClient",
    "OpenAICompatibleClient",
    "APIKeyRotator",
    "APIKey",
    "get_key_rotator",
    "reset_rotators",
]
