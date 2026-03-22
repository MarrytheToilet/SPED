"""
提取服务 - 高层API，编排LLM和Prompt组件

这是解耦后的新接口，推荐使用。
旧的 extraction_agent.py 保留向后兼容。
"""
from typing import Dict, List, Any, Optional
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
from loguru import logger

from src.llm import create_llm_client, create_llm_client_for_worker, LLMClient
from src.prompts import PromptAssembler
from src.prompts.modes import ExtractionMode, FullMode, SkeletonFillMode


@dataclass
class ExtractionOutput:
    """提取输出"""
    success: bool
    paper_id: str
    records: List[Dict[str, Any]]
    count: int
    mode: str
    model: str
    error: str = ""
    metadata: Dict[str, Any] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "paper_id": self.paper_id,
            "records": self.records,
            "count": self.count,
            "mode": self.mode,
            "model": self.model,
            "error": self.error,
            "metadata": self.metadata or {},
        }


class ExtractionService:
    """
    提取服务
    
    职责：
    1. 管理LLM客户端和Prompt组装器
    2. 根据模式选择合适的提取策略
    3. 提供统一的提取接口
    
    使用示例：
    ```python
    service = ExtractionService(mode="skeleton_fill")
    result = service.extract(
        paper_id="论文ID",
        content="论文全文",
        chunks=["chunk1", "chunk2", ...]
    )
    ```
    """
    
    SUPPORTED_MODES = ["full", "skeleton_fill", "chunk"]
    
    def __init__(
        self,
        mode: str = "skeleton_fill",
        model: str = None,
        llm_client: LLMClient = None,
        prompt_assembler: PromptAssembler = None,
        worker_id: int = None,
    ):
        """
        初始化提取服务
        
        Args:
            mode: 提取模式 ("full", "skeleton_fill", "chunk")
            model: LLM模型名称
            llm_client: 可选，自定义LLM客户端
            prompt_assembler: 可选，自定义Prompt组装器
            worker_id: 可选，并发worker编号（用于负载均衡分配不同API）
        """
        self.logger = logger.bind(module="ExtractionService")
        
        # 验证模式
        if mode not in self.SUPPORTED_MODES:
            raise ValueError(f"不支持的模式: {mode}，可选: {self.SUPPORTED_MODES}")
        
        self.mode = mode
        self.model = model
        self.worker_id = worker_id
        
        # 初始化组件（支持负载均衡）
        if llm_client:
            self.llm_client = llm_client
        elif worker_id is not None:
            # 并发模式：使用负载均衡分配API
            self.llm_client = create_llm_client_for_worker(worker_id)
        else:
            self.llm_client = create_llm_client(model=model)
        
        self.prompt_assembler = prompt_assembler or PromptAssembler()
        
        # 创建模式策略
        self._mode_strategy = self._create_mode_strategy()
        
        self.logger.info(
            f"初始化完成: mode={mode}, model={self.llm_client.config.model}, "
            f"provider={self.llm_client.config.provider}"
            f"{f', worker={worker_id}' if worker_id is not None else ''}"
        )
    
    def _create_mode_strategy(self) -> ExtractionMode:
        """创建模式策略"""
        if self.mode == "full":
            return FullMode(self.llm_client, self.prompt_assembler)
        elif self.mode == "skeleton_fill":
            return SkeletonFillMode(self.llm_client, self.prompt_assembler)
        elif self.mode == "chunk":
            # chunk模式暂时使用skeleton_fill的变体
            return SkeletonFillMode(self.llm_client, self.prompt_assembler)
        else:
            raise ValueError(f"未实现的模式: {self.mode}")
    
    def extract(
        self,
        paper_id: str,
        content: str,
        chunks: List[str] = None,
        **kwargs
    ) -> ExtractionOutput:
        """
        执行提取
        
        Args:
            paper_id: 论文ID
            content: 论文全文
            chunks: 分块后的文本列表（skeleton_fill模式需要）
            **kwargs: 其他参数
        
        Returns:
            ExtractionOutput
        """
        self.logger.info(f"开始提取: {paper_id}, mode={self.mode}")
        
        try:
            result = self._mode_strategy.extract(
                paper_id=paper_id,
                content=content,
                chunks=chunks,
                **kwargs
            )
            
            if result.success:
                self.logger.info(f"提取完成: {paper_id}, 记录数={result.count}")
            else:
                self.logger.error(f"提取失败: {paper_id}, 错误={result.error}")
            
            return ExtractionOutput(
                success=result.success,
                paper_id=paper_id,
                records=result.records,
                count=result.count,
                mode=self.mode,
                model=self.llm_client.config.model,
                error=result.error,
                metadata=result.metadata,
            )
            
        except Exception as e:
            self.logger.error(f"提取异常: {paper_id}, 错误={e}")
            return ExtractionOutput(
                success=False,
                paper_id=paper_id,
                records=[],
                count=0,
                mode=self.mode,
                model=self.llm_client.config.model,
                error=str(e),
            )
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            "mode": self.mode,
            "llm_stats": self.llm_client.get_stats(),
        }


# 便捷函数
def extract_paper(
    paper_id: str,
    content: str,
    chunks: List[str] = None,
    mode: str = "skeleton_fill",
    model: str = None,
) -> ExtractionOutput:
    """
    便捷函数：提取单篇论文
    
    Args:
        paper_id: 论文ID
        content: 论文全文
        chunks: 分块列表（可选）
        mode: 提取模式
        model: 模型名称
    
    Returns:
        ExtractionOutput
    """
    service = ExtractionService(mode=mode, model=model)
    return service.extract(paper_id, content, chunks)
