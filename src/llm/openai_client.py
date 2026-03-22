"""
OpenAI兼容客户端 - 支持OpenAI/SiliconFlow/DeepSeek等兼容API
"""
from typing import Dict, List, Any, Optional
import httpx

from .base import LLMClient, LLMConfig, LLMMessage, LLMResponse

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class OpenAICompatibleClient(LLMClient):
    """
    OpenAI兼容客户端
    
    支持：
    - OpenAI
    - SiliconFlow
    - DeepSeek
    - 其他OpenAI兼容API
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if OpenAI is None:
            raise ImportError("请安装 openai: pip install openai")
        
        # 创建客户端
        self.client = self._create_client()
    
    def _create_client(self) -> OpenAI:
        """创建OpenAI客户端"""
        # 配置超时
        timeout_config = httpx.Timeout(
            connect=60.0,
            read=self.config.timeout,
            write=120.0,
            pool=60.0,
        )
        
        # 供应商特定配置
        http_client_kwargs = {}
        if self.config.provider == "siliconflow":
            # SiliconFlow需要关闭长连接
            http_client_kwargs["headers"] = {
                "Connection": "close",
                "Accept": "application/json",
            }
        
        http_client = httpx.Client(
            timeout=timeout_config,
            **http_client_kwargs
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
            
            # 添加超时
            request_kwargs["timeout"] = self.config.timeout
            
            # 供应商特定参数
            extra_body = self._build_extra_body()
            if extra_body:
                request_kwargs["extra_body"] = extra_body
            
            self.logger.debug(f"请求参数: max_tokens={request_kwargs['max_tokens']}")
            
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
                provider=self.config.provider,
                usage=usage,
                raw_response=response,
            )
            
        except Exception as e:
            error_msg = str(e)
            # 解析常见错误
            if "timeout" in error_msg.lower():
                error_msg = f"请求超时 ({self.config.timeout}s)"
            elif "connection" in error_msg.lower():
                error_msg = f"连接错误: {error_msg}"
            
            return LLMResponse(
                success=False,
                error=error_msg,
                model=self.config.model,
                provider=self.config.provider,
            )
    
    def _build_extra_body(self) -> Dict[str, Any]:
        """构建供应商特定的extra_body"""
        extra = {}
        
        if self.config.provider == "siliconflow":
            # SiliconFlow的thinking参数
            enable_thinking = self.config.extra_params.get("enable_thinking", False)
            if self._supports_thinking():
                extra["enable_thinking"] = enable_thinking
                if enable_thinking:
                    extra["thinking_budget"] = self.config.extra_params.get("thinking_budget", 1024)
        
        return extra
    
    def _supports_thinking(self) -> bool:
        """判断模型是否支持thinking参数"""
        thinking_models = {
            "Pro/zai-org/GLM-5", "Pro/zai-org/GLM-4.7",
            "deepseek-ai/DeepSeek-V3.2", "Pro/deepseek-ai/DeepSeek-V3.2",
        }
        return self.config.model in thinking_models
