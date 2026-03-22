"""
智谱AI客户端 - 专门处理智谱GLM系列模型

特点：
- 支持 response_format 强制JSON输出
- 支持思考模式（GLM-5/4.7/4.6）
- 使用OpenAI兼容接口
"""
from typing import Dict, List, Any, Optional
import httpx

from .base import LLMClient, LLMConfig, LLMMessage, LLMResponse

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


class ZhipuClient(LLMClient):
    """
    智谱AI客户端
    
    支持模型：
    - glm-5: 旗舰模型，200K上下文，128K输出
    - glm-4.7: 高性能模型
    - glm-4.6: 均衡模型
    - glm-4-plus: 增强版
    - glm-4-flash: 快速版
    """
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        
        if OpenAI is None:
            raise ImportError("请安装 openai: pip install openai")
        
        self.client = self._create_client()
    
    def _create_client(self) -> OpenAI:
        """创建客户端（使用OpenAI兼容接口）"""
        timeout_config = httpx.Timeout(
            connect=60.0,
            read=self.config.timeout,
            write=120.0,
            pool=60.0,
        )
        
        http_client = httpx.Client(
            timeout=timeout_config,
            headers={
                "Accept": "application/json",
                "Content-Type": "application/json",
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
            
            # 智谱支持强制JSON输出
            if kwargs.get("json_mode", True):
                request_kwargs["response_format"] = {"type": "json_object"}
            
            request_kwargs["timeout"] = self.config.timeout
            
            self.logger.debug(
                f"智谱API调用: model={self.config.model}, "
                f"max_tokens={request_kwargs['max_tokens']}"
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
                provider="zhipu",
                usage=usage,
                raw_response=response,
            )
            
        except Exception as e:
            error_msg = str(e)
            
            # 解析智谱特定错误
            if "1301" in error_msg:
                error_msg = "系统检测到输入或生成内容可能包含不安全内容"
            elif "1302" in error_msg:
                error_msg = "API Key无效或已过期"
            elif "1303" in error_msg:
                error_msg = "请求频率超限，请稍后重试"
            
            return LLMResponse(
                success=False,
                error=error_msg,
                model=self.config.model,
                provider="zhipu",
            )
    
    def supports_thinking(self) -> bool:
        """判断模型是否支持思考模式"""
        return self.config.model in {"glm-5", "glm-4.7", "glm-4.6"}
