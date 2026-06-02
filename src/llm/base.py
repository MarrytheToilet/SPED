"""
LLM基础类 - 定义统一的LLM调用接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import time
from pathlib import Path
from loguru import logger


@dataclass
class LLMMessage:
    """LLM消息"""
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class LLMResponse:
    """LLM响应"""
    success: bool
    content: str = ""
    error: str = ""
    model: str = ""
    provider: str = ""
    usage: Dict[str, int] = field(default_factory=dict)
    latency_ms: int = 0
    finish_reason: str = ""
    truncated: bool = False  # 因 max_tokens 截断或正文为空（reasoning 吃光预算）
    raw_response: Any = None
    
    def to_json(self) -> Dict[str, Any]:
        """转换为可JSON序列化的字典"""
        return {
            "success": self.success,
            "content": self.content,
            "error": self.error,
            "model": self.model,
            "provider": self.provider,
            "usage": self.usage,
            "latency_ms": self.latency_ms,
            "finish_reason": self.finish_reason,
            "truncated": self.truncated,
        }


@dataclass
class LLMConfig:
    """LLM配置"""
    model: str
    provider: str
    api_key: str
    api_base: str
    temperature: float = 0.1
    max_tokens: int = 16000
    timeout: float = 600.0
    max_retries: int = 3
    retry_delay: float = 2.0
    
    # 供应商特定配置
    extra_params: Dict[str, Any] = field(default_factory=dict)


class LLMClient(ABC):
    """
    LLM客户端基类
    
    职责：
    1. 调用模型API
    2. 处理重试和超时
    3. 记录调用日志
    4. 报告结果给Key轮询器（用于负载均衡健康检测）
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.logger = logger.bind(module="LLMClient")
        
        # 调用统计
        self.stats = {
            "total_calls": 0,
            "success_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0,
        }
        
        # 调试日志目录
        self.debug_dir = Path("logs/llm_debug")
        self.debug_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def _do_call(
        self,
        messages: List[LLMMessage],
        **kwargs
    ) -> LLMResponse:
        """
        实际的API调用（由子类实现）
        """
        pass
    
    def _report_to_rotator(self, success: bool, error: str = ""):
        """保留占位（多Key负载均衡已移除，单端点无需上报）。"""
        return
    
    def call(
        self,
        messages: List[LLMMessage],
        call_id: str = "unknown",
        **kwargs
    ) -> LLMResponse:
        """
        调用LLM（带重试和日志）
        
        Args:
            messages: 消息列表
            call_id: 调用标识（用于日志）
            **kwargs: 额外参数
        
        Returns:
            LLMResponse
        """
        self.stats["total_calls"] += 1
        
        # 保存输入
        self._save_input(call_id, messages)
        
        # 当前调用使用的输出 token 上限（截断/空正文时逐次抬高）
        cur_max_tokens = int(kwargs.get("max_tokens", self.config.max_tokens) or self.config.max_tokens)
        token_cap = int(getattr(self.config, "max_tokens_cap", 0) or 65536)

        # 重试循环
        last_error = ""
        for attempt in range(self.config.max_retries):
            if attempt > 0:
                delay = self.config.retry_delay * (2 ** (attempt - 1))
                self.logger.info(f"重试 {attempt + 1}/{self.config.max_retries}，等待 {delay:.1f}s")
                time.sleep(delay)
            
            try:
                self.logger.debug(
                    f"调用LLM [{call_id}] 尝试 {attempt + 1}: "
                    f"model={self.config.model}, provider={self.config.provider}, "
                    f"max_tokens={cur_max_tokens}"
                )
                
                call_kwargs = dict(kwargs)
                call_kwargs["max_tokens"] = cur_max_tokens

                start_time = time.time()
                response = self._do_call(messages, **call_kwargs)
                response.latency_ms = int((time.time() - start_time) * 1000)
                
                if response.success:
                    self.stats["success_calls"] += 1
                    self.stats["total_tokens"] += response.usage.get("total_tokens", 0)
                    self._save_output(call_id, response)
                    # 报告成功
                    self._report_to_rotator(True)
                    return response
                else:
                    last_error = response.error
                    self.logger.warning(f"调用失败: {response.error}")
                    # 截断或正文为空：下次抬高 max_tokens 重试（reasoning 模型常见）
                    if getattr(response, "truncated", False) and cur_max_tokens < token_cap:
                        cur_max_tokens = min(int(cur_max_tokens * 2), token_cap)
                        self.logger.info(f"检测到截断/空正文，提升 max_tokens 至 {cur_max_tokens} 后重试")
                    
            except Exception as e:
                last_error = str(e)
                self.logger.error(f"调用异常: {e}")
        
        # 全部重试失败
        self.stats["failed_calls"] += 1
        # 报告失败
        self._report_to_rotator(False, last_error)
        return LLMResponse(
            success=False,
            error=f"重试{self.config.max_retries}次后仍失败: {last_error}",
            model=self.config.model,
            provider=self.config.provider,
        )
    
    def _save_input(self, call_id: str, messages: List[LLMMessage]):
        """保存输入到文件"""
        try:
            filepath = self.debug_dir / f"{call_id}_input.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== LLM Input [{call_id}] ===\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
                f.write(f"Model: {self.config.model}\n")
                f.write(f"Provider: {self.config.provider}\n")
                f.write(f"\n{'='*60}\n\n")
                for msg in messages:
                    f.write(f"[{msg.role.upper()}]\n{msg.content}\n\n")
        except Exception as e:
            self.logger.error(f"保存输入失败: {e}")
    
    def _save_output(self, call_id: str, response: LLMResponse):
        """保存输出到文件"""
        try:
            filepath = self.debug_dir / f"{call_id}_output.txt"
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(f"=== LLM Output [{call_id}] ===\n")
                f.write(f"Time: {datetime.now().isoformat()}\n")
                f.write(f"Model: {response.model}\n")
                f.write(f"Latency: {response.latency_ms}ms\n")
                f.write(f"Usage: {response.usage}\n")
                f.write(f"\n{'='*60}\n\n")
                f.write(response.content)
        except Exception as e:
            self.logger.error(f"保存输出失败: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            **self.stats,
            "model": self.config.model,
            "provider": self.config.provider,
        }
