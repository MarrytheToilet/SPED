"""
SiliconFlow客户端 - 专门处理SiliconFlow API的特殊需求

特点：
- 关闭长连接避免连接超时
- 支持 thinking 参数（部分模型）
- 处理SiliconFlow特定错误
"""
from typing import Dict, List, Any, Optional
import httpx

from .base import LLMClient, LLMConfig, LLMMessage, LLMResponse

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# 支持 thinking 参数的模型
THINKING_MODELS = {
    "Pro/zai-org/GLM-5",
    "Pro/zai-org/GLM-4.7",
    "deepseek-ai/DeepSeek-V3.2",
    "Pro/deepseek-ai/DeepSeek-V3.2",
    "zai-org/GLM-4.6",
    "Qwen/Qwen3-8B",
    "Qwen/Qwen3-14B",
    "Qwen/Qwen3-32B",
    "Pro/moonshotai/Kimi-K2.5",
    "moonshotai/Kimi-K2-Instruct-0905",
}


class SiliconFlowClient(LLMClient):
    """
    SiliconFlow客户端
    
    支持模型：
    - Pro/moonshotai/Kimi-K2.5
    - Pro/zai-org/GLM-5
    - deepseek-ai/DeepSeek-V2.5
    - Qwen/Qwen2.5-72B-Instruct
    - 等等
    
    特殊处理：
    - 关闭HTTP长连接（避免连接超时）
    - enable_thinking 参数
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if OpenAI is None:
            raise ImportError("请安装 openai: pip install openai")
        
        self.client = self._create_client()
    
    def _create_client(self) -> OpenAI:
        """创建客户端（特殊配置）"""
        timeout_config = httpx.Timeout(
            connect=60.0,
            read=self.config.timeout,
            write=120.0,
            pool=60.0,
        )
        
        # SiliconFlow关键配置：关闭长连接
        http_client = httpx.Client(
            timeout=timeout_config,
            headers={
                "Connection": "close",  # 关键！避免连接复用导致超时
                "Accept": "application/json",
            }
        )
        
        return OpenAI(
            api_key=self.config.api_key,
            base_url=self.config.api_base,
            http_client=http_client,
        )
    
    def _do_call(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """执行API调用"""
        try:
            # 构建请求参数
            request_kwargs: Dict[str, Any] = {
                "model": self.config.model,
                "messages": [{"role": m.role, "content": m.content} for m in messages],
                "temperature": self.config.temperature,
                "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            }
            
            request_kwargs["timeout"] = self.config.timeout
            
            # SiliconFlow 特有参数
            extra_body = self._build_extra_body()
            if extra_body:
                request_kwargs["extra_body"] = extra_body
            
            self.logger.debug(
                f"SiliconFlow API调用: model={self.config.model}, "
                f"max_tokens={request_kwargs['max_tokens']}, "
                f"extra_body={extra_body}"
            )
            
            # 调用API
            response = self.client.chat.completions.create(**request_kwargs)
            
            # 解析响应
            content = response.choices[0].message.content
            usage = {
                "prompt_tokens": getattr(response.usage, "prompt_tokens", 0),
                "completion_tokens": getattr(response.usage, "completion_tokens", 0),
                "total_tokens": getattr(response.usage, "total_tokens", 0),
            }
            
            return LLMResponse(
                success=True,
                content=content,
                model=self.config.model,
                provider="siliconflow",
                usage=usage,
                raw_response=response,
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # 解析SiliconFlow特定错误
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                error_msg = f"请求超时 ({self.config.timeout}s) - 建议使用skeleton_fill模式分块处理"
            elif "connection" in error_msg.lower():
                error_msg = f"连接错误 - 可能是请求过长导致: {error_msg[:100]}"
            elif "rate limit" in error_msg.lower():
                error_msg = "请求频率超限，请稍后重试"
            elif "invalid api key" in error_msg.lower():
                error_msg = "API Key无效"
            
            return LLMResponse(
                success=False,
                error=error_msg,
                model=self.config.model,
                provider="siliconflow",
            )
    
    def _build_extra_body(self) -> Dict[str, Any]:
        """构建SiliconFlow特有的extra_body"""
        extra = {}
        
        # thinking 参数（部分模型支持）
        if self.supports_thinking():
            enable_thinking = self.config.extra_params.get("enable_thinking", False)
            extra["enable_thinking"] = enable_thinking
            if enable_thinking:
                extra["thinking_budget"] = self.config.extra_params.get("thinking_budget", 1024)
        
        return extra
    
    def supports_thinking(self) -> bool:
        """判断模型是否支持thinking参数"""
        return self.config.model in THINKING_MODELS
