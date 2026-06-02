"""
提取服务 - 高层API。基于「生成schema」的扁平提取（每字段内联 value+evidence）。
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger

from src.llm import create_llm_client, create_llm_client_for_agent, LLMClient
from src.prompts.modes import GenericFlatMode


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
    提取服务（扁平模式）。

    必须提供一个生成的 schema（src.schema.GeneratedSchema）。
    使用 extractor 角色的模型（settings.get_agent_config('extractor')）。
    """

    def __init__(
        self,
        schema,
        model: str = None,
        llm_client: LLMClient = None,
        agent_role: str = "extractor",
    ):
        self.logger = logger.bind(module="ExtractionService")
        if schema is None:
            raise ValueError("ExtractionService 需要提供 schema")
        self.schema = schema
        self.mode = "flat"

        if llm_client:
            self.llm_client = llm_client
        elif model:
            self.llm_client = create_llm_client(model=model)
        else:
            self.llm_client = create_llm_client_for_agent(agent_role)

        self._mode_strategy = GenericFlatMode(self.llm_client, self.schema)
        self.logger.info(
            f"初始化完成: mode=flat, model={self.llm_client.config.model}, "
            f"schema={getattr(self.schema, 'slug', '?')} ({len(self.schema.fields)}字段)"
        )

    def extract(self, paper_id: str, content: str, **kwargs) -> ExtractionOutput:
        self.logger.info(f"开始提取: {paper_id} (flat)")
        try:
            result = self._mode_strategy.extract(paper_id=paper_id, content=content, **kwargs)
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
                success=False, paper_id=paper_id, records=[], count=0,
                mode=self.mode, model=self.llm_client.config.model, error=str(e),
            )

    def get_stats(self) -> Dict[str, Any]:
        return {"mode": self.mode, "llm_stats": self.llm_client.get_stats()}


def extract_paper(paper_id: str, content: str, schema, model: str = None) -> ExtractionOutput:
    """便捷函数：用 schema 提取单篇论文。"""
    service = ExtractionService(schema=schema, model=model)
    return service.extract(paper_id, content)
