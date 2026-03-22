"""
模型请求配置 - 将不同供应商/模型的请求头与额外参数解耦。
"""
from typing import Dict, Any


# SiliconFlow 支持 thinking 参数的模型
SILICONFLOW_THINKING_MODELS = {
    "Pro/zai-org/GLM-5",
    "Pro/zai-org/GLM-4.7",
    "deepseek-ai/DeepSeek-V3.2",
    "Pro/deepseek-ai/DeepSeek-V3.2",
    "zai-org/GLM-4.6",
    "Qwen/Qwen3-8B",
    "Qwen/Qwen3-14B",
    "Qwen/Qwen3-32B",
    "Qwen/Qwen3-30B-A3B",
    "tencent/Hunyuan-A13B-Instruct",
    "zai-org/GLM-4.5V",
    "deepseek-ai/DeepSeek-V3.1-Terminus",
    "Pro/deepseek-ai/DeepSeek-V3.1-Terminus",
    "Qwen/Qwen3.5-397B-A17B",
    "Qwen/Qwen3.5-122B-A10B",
    "Qwen/Qwen3.5-35B-A3B",
    "Qwen/Qwen3.5-27B",
    "Qwen/Qwen3.5-9B",
    "Qwen/Qwen3.5-4B",
}

# 智谱支持思考模式的模型
ZHIPU_THINKING_MODELS = {
    "glm-5",
    "glm-4.7",
    "glm-4.6",
}


def build_provider_headers(provider_name: str, model: str) -> Dict[str, str]:
    """
    构建供应商/模型相关的默认请求头。
    """
    provider = (provider_name or "").lower()

    if provider == "siliconflow":
        # 显式关闭长连接，避免连接复用导致的偶发断连/超时。
        return {
            "Connection": "close",
            "Accept": "application/json",
        }
    
    if provider == "zhipu":
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    return {}


def supports_siliconflow_thinking_toggle(model: str) -> bool:
    """判断模型是否支持 SiliconFlow thinking 参数。"""
    return model in SILICONFLOW_THINKING_MODELS


def supports_zhipu_thinking(model: str) -> bool:
    """判断模型是否支持智谱思考模式。"""
    return model in ZHIPU_THINKING_MODELS


def build_provider_extra_body(
    provider_name: str,
    model: str,
    enable_thinking: bool,
    thinking_budget: int,
) -> Dict[str, Any]:
    """
    构建请求体附加参数（extra_body）。
    """
    provider = (provider_name or "").lower()

    if provider == "siliconflow":
        if not supports_siliconflow_thinking_toggle(model):
            return {}
        extra_body: Dict[str, Any] = {"enable_thinking": bool(enable_thinking)}
        if enable_thinking:
            extra_body["thinking_budget"] = max(128, int(thinking_budget))
        return extra_body
    
    if provider == "zhipu":
        # 智谱支持 response_format 参数
        return {
            "response_format": {"type": "json_object"}
        }

    return {}


def get_provider_specific_params(
    provider_name: str,
    model: str,
    temperature: float = 0.1,
    max_tokens: int = 16000,
) -> Dict[str, Any]:
    """
    获取供应商特定的请求参数。
    
    用于需要不同参数格式的供应商（如智谱）。
    """
    provider = (provider_name or "").lower()
    
    params = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }
    
    if provider == "zhipu":
        # 智谱API使用不同的参数名
        # 注意：智谱通过 OpenAI 兼容接口，参数名相同
        pass
    
    return params
