"""
LLM客户端工厂 - 根据配置创建合适的LLM客户端
"""
from typing import Optional
import os
from loguru import logger

from .base import LLMClient, LLMConfig
from .openai_client import OpenAICompatibleClient
from .siliconflow_client import SiliconFlowClient
from .zhipu_client import ZhipuClient


def create_llm_client(
    model: str = None,
    provider: str = None,
    api_key: str = None,
    api_base: str = None,
    use_load_balancer: bool = False,
    **kwargs
) -> LLMClient:
    """
    创建LLM客户端
    
    Args:
        model: 模型名称，如 "glm-5", "Pro/moonshotai/Kimi-K2.5"
        provider: 供应商，如 "zhipu", "siliconflow", "openai"
        api_key: API密钥（可选，默认从环境变量读取）
        api_base: API地址（可选，默认从环境变量读取）
        use_load_balancer: 是否使用负载均衡（从备用API列表中选择）
        **kwargs: 其他配置
    
    Returns:
        LLMClient实例
    """
    # 如果使用负载均衡器，从中获取端点配置
    if use_load_balancer:
        from .load_balancer import get_load_balancer
        balancer = get_load_balancer()
        endpoint = balancer.get_endpoint()
        if endpoint:
            model = endpoint.model
            provider = endpoint.provider
            api_key = endpoint.api_key
            api_base = endpoint.api_base
    
    # 如果未指定，从settings获取默认配置
    if model is None:
        try:
            import settings
            model = settings.DEFAULT_MODEL
        except ImportError:
            model = os.getenv("LLM_MODEL", "gpt-4o")
    
    # 自动检测provider
    if provider is None:
        provider = _detect_provider(model)
    
    # 获取API配置
    api_key, api_base = _get_api_config(model, provider, api_key, api_base)
    
    # 获取模型特定配置
    max_tokens = _get_max_tokens(model)
    timeout = float(os.getenv("LLM_CALL_TIMEOUT", "600"))
    max_retries = int(os.getenv("LLM_MAX_RETRIES", "3"))
    temperature = float(os.getenv("LLM_TEMPERATURE", "0.1"))
    
    # 构建配置
    config = LLMConfig(
        model=model,
        provider=provider,
        api_key=api_key,
        api_base=api_base,
        temperature=temperature,
        max_tokens=max_tokens,
        timeout=timeout,
        max_retries=max_retries,
        extra_params=kwargs,
    )
    
    # 根据provider创建专用客户端
    if provider == "zhipu":
        return ZhipuClient(config)
    elif provider == "siliconflow":
        return SiliconFlowClient(config)
    else:
        # OpenAI兼容客户端（openai/deepseek等）
        return OpenAICompatibleClient(config)


def create_llm_client_for_worker(worker_id: int = 0) -> LLMClient:
    """
    为并发worker创建LLM客户端（按worker固定分配API Key）
    
    按worker_id分配固定的API Key：
    - worker_id % key_count 决定使用哪个Key
    - 如果分配的Key不健康，自动切换到其他健康Key
    - 无可用Key时回退到主Key
    
    Args:
        worker_id: worker编号（用于Key分配）
    
    Returns:
        LLMClient实例
    """
    from .load_balancer import get_key_rotator
    
    # 获取默认配置
    try:
        import settings
        model = settings.DEFAULT_MODEL
        provider = _detect_provider(model)
    except ImportError:
        model = os.getenv("LLM_MODEL", "gpt-4o")
        provider = _detect_provider(model)
    
    # 获取Key轮询器
    rotator = get_key_rotator(provider)
    
    # 按worker_id获取固定分配的Key
    api_key = rotator.get_key_for_worker(worker_id)
    
    # 记录分配信息
    key_info = rotator.get_worker_key_info(worker_id)
    logger.debug(f"Worker-{worker_id} 分配Key: {key_info['key_name']} ({key_info['key_short']})")
    
    # 获取api_base
    _, api_base = _get_api_config(model, provider, api_key, None)
    
    # 创建客户端
    return create_llm_client(
        model=model,
        provider=provider,
        api_key=api_key,
        api_base=api_base,
    )


def report_api_result(provider: str, api_key: str, success: bool, error: str = ""):
    """
    报告API调用结果（用于负载均衡的健康检测）
    
    Args:
        provider: 供应商名称
        api_key: 使用的API Key
        success: 是否成功
        error: 错误信息（失败时）
    """
    from .load_balancer import get_key_rotator
    
    rotator = get_key_rotator(provider)
    if success:
        rotator.report_success(api_key)
    else:
        rotator.report_failure(api_key, error)


def _detect_provider(model: str) -> str:
    """根据模型名自动检测provider"""
    model_lower = model.lower()
    
    if model.startswith("glm-") or "zhipu" in model_lower:
        return "zhipu"
    elif "deepseek" in model_lower:
        if "Pro/" in model or model.startswith("deepseek-ai/"):
            return "siliconflow"  # SiliconFlow上的DeepSeek
        return "deepseek"
    elif model.startswith("Pro/") or "siliconflow" in model_lower:
        return "siliconflow"
    elif model.startswith("gpt-"):
        return "openai"
    else:
        return "siliconflow"  # 默认使用SiliconFlow


def _get_api_config(
    model: str,
    provider: str,
    api_key: Optional[str],
    api_base: Optional[str]
) -> tuple:
    """获取API配置"""
    # 尝试从settings获取
    try:
        import settings
        if model in settings.AVAILABLE_MODELS:
            model_config = settings.AVAILABLE_MODELS[model]
            if api_key is None:
                api_key = model_config.get("api_key", "")
            if api_base is None:
                api_base = model_config.get("api_base", "")
    except ImportError:
        pass
    
    # 回退到环境变量
    if not api_key:
        env_map = {
            "zhipu": "ZHIPU_API_KEY",
            "siliconflow": "SILICONFLOW_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
            "openai": "OPENAI_API_KEY",
        }
        api_key = os.getenv(env_map.get(provider, "OPENAI_API_KEY"), "")
    
    if not api_base:
        base_map = {
            "zhipu": "https://open.bigmodel.cn/api/paas/v4",
            "siliconflow": "https://api.siliconflow.cn/v1",
            "deepseek": "https://api.deepseek.com/v1",
            "openai": "https://api.openai.com/v1",
        }
        api_base = os.getenv(f"{provider.upper()}_API_BASE", base_map.get(provider, ""))
    
    return api_key, api_base


def _get_max_tokens(model: str) -> int:
    """获取模型的max_tokens限制"""
    try:
        import settings
        return settings.MODEL_MAX_TOKENS.get(model, 16000)
    except ImportError:
        # 默认配置
        defaults = {
            "glm-5": 128000,
            "glm-4.7": 32000,
            "glm-4.6": 32000,
            "gpt-4o": 16000,
        }
        return defaults.get(model, 16000)
