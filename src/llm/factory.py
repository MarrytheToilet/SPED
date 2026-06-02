"""
LLM客户端工厂 - 统一创建 OpenAI 兼容客户端（支持多agent分角色端点）。

所有家族（DeepSeek / Qwen / GLM / Kimi / OpenAI / SiliconFlow ...）均通过
OpenAI 兼容协议接入，只需各自的 base_url + api_key + model。
"""
from typing import Optional
import os
from loguru import logger

from .base import LLMClient, LLMConfig
from .openai_client import OpenAICompatibleClient


def _base_defaults() -> dict:
    try:
        import settings
        return {
            "model": settings.LLM_MODEL,
            "api_base": settings.LLM_API_BASE,
            "api_key": settings.LLM_API_KEY,
            "provider": settings.LLM_PROVIDER,
            "max_tokens": settings.LLM_MAX_OUTPUT_TOKENS,
            "temperature": settings.LLM_TEMPERATURE,
        }
    except Exception:
        return {
            "model": os.getenv("LLM_MODEL", "deepseek-v4-flash"),
            "api_base": os.getenv("LLM_API_BASE", "https://api.deepseek.com/v1"),
            "api_key": os.getenv("LLM_API_KEY", ""),
            "provider": os.getenv("LLM_PROVIDER", "openai"),
            "max_tokens": int(os.getenv("LLM_MAX_OUTPUT_TOKENS", "65536")),
            "temperature": float(os.getenv("LLM_TEMPERATURE", "0.1")),
        }


def create_llm_client(
    model: str = None,
    provider: str = None,
    api_key: str = None,
    api_base: str = None,
    max_tokens: int = None,
    **kwargs,
) -> LLMClient:
    """创建一个 OpenAI 兼容 LLM 客户端。未指定的参数回退到基础 LLM_* 配置。"""
    d = _base_defaults()
    model = model or d["model"]
    provider = provider or d["provider"]
    api_key = api_key if api_key is not None else d["api_key"]
    api_base = api_base or d["api_base"]
    max_tokens = max_tokens or d["max_tokens"]

    timeout = float(os.getenv("LLM_CALL_TIMEOUT", "600"))
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))

    config = LLMConfig(
        model=model,
        provider=provider,
        api_key=api_key,
        api_base=api_base,
        temperature=d["temperature"],
        max_tokens=max_tokens,
        timeout=timeout,
        max_retries=max_retries,
        extra_params=kwargs,
    )
    return OpenAICompatibleClient(config)


def create_llm_client_for_agent(role: str) -> LLMClient:
    """
    为某个agent角色创建客户端。

    角色端点来自 settings.get_agent_config(role)（AGENT_<ROLE>_* 环境变量，
    缺省回退基础端点）。用于多agent（不同家族）协作。
    """
    try:
        import settings
        cfg = settings.get_agent_config(role)
    except Exception:
        cfg = {"model": None, "api_base": None, "api_key": None, "provider": None}

    client = create_llm_client(
        model=cfg.get("model"),
        provider=cfg.get("provider"),
        api_key=cfg.get("api_key"),
        api_base=cfg.get("api_base"),
    )
    logger.debug(f"[agent:{role}] model={client.config.model} base={client.config.api_base}")
    return client


# 向后兼容：旧调用 create_llm_client_for_worker(worker_id)
def create_llm_client_for_worker(worker_id: int = 0) -> LLMClient:
    return create_llm_client()
