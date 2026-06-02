"""
LLM调用层 - 与业务逻辑解耦的模型调用接口

所有家族通过 OpenAI 兼容协议接入（DeepSeek/Qwen/GLM/Kimi/OpenAI/SiliconFlow ...）。
支持按 agent 角色使用不同端点（见 settings.get_agent_config / factory.create_llm_client_for_agent）。
"""

from .base import LLMClient, LLMResponse, LLMConfig, LLMMessage
from .factory import (
    create_llm_client,
    create_llm_client_for_agent,
    create_llm_client_for_worker,
)
from .openai_client import OpenAICompatibleClient

__all__ = [
    "LLMClient",
    "LLMResponse",
    "LLMConfig",
    "LLMMessage",
    "create_llm_client",
    "create_llm_client_for_agent",
    "create_llm_client_for_worker",
    "OpenAICompatibleClient",
]
