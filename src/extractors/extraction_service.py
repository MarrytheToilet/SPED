"""
提取服务 - 高层API。基于「生成schema」的扁平提取（每字段内联 value+evidence）。
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from loguru import logger

from src.llm import create_llm_client, create_llm_client_for_agent, LLMClient
from src.prompts.modes import GenericFlatMode, MultiAgentFlatMode


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
        extractor_roles: List[str] = None,
        merger_role: str = None,
        reviewer_role: str = None,
        review_enabled: bool = None,
    ):
        self.logger = logger.bind(module="ExtractionService")
        if schema is None:
            raise ValueError("ExtractionService 需要提供 schema")
        self.schema = schema
        if extractor_roles is None:
            try:
                import settings
                extractor_roles = list(getattr(settings, "EXTRACTOR_ROLES", ["extractor_a", "extractor_b"]) or ["extractor_a", "extractor_b"])
                merger_role = merger_role or getattr(settings, "EXTRACT_MERGER_ROLE", "extract_merger")
                reviewer_role = reviewer_role or getattr(settings, "EXTRACT_REVIEWER_ROLE", "extract_reviewer")
                if review_enabled is None:
                    review_enabled = bool(getattr(settings, "EXTRACT_REVIEW_ENABLED", True))
            except Exception:
                extractor_roles = ["extractor"]
                merger_role = merger_role or "extract_merger"
                reviewer_role = reviewer_role or "extract_reviewer"
                if review_enabled is None:
                    review_enabled = True
        extractor_roles = [r for r in extractor_roles if r]
        if not extractor_roles:
            extractor_roles = [agent_role]

        if llm_client:
            self.llm_client = llm_client
        elif model:
            self.llm_client = create_llm_client(model=model)
        else:
            self.llm_client = create_llm_client_for_agent(agent_role)

        if (len(extractor_roles) > 1 or review_enabled) and llm_client is None and model is None:
            extractor_clients = {role: create_llm_client_for_agent(role) for role in extractor_roles}
            merger_client = create_llm_client_for_agent(merger_role or "extract_merger")
            reviewer_client = create_llm_client_for_agent(reviewer_role or "extract_reviewer") if review_enabled else None
            self._mode_strategy = MultiAgentFlatMode(
                extractor_clients=extractor_clients,
                merger_client=merger_client,
                schema=self.schema,
                merger_role=merger_role or "extract_merger",
                reviewer_client=reviewer_client,
                reviewer_role=reviewer_role or "extract_reviewer",
                review_enabled=bool(review_enabled),
            )
            self.mode = "flat_multi_agent"
            self.llm_client = merger_client
        else:
            self._mode_strategy = GenericFlatMode(self.llm_client, self.schema)
            self.mode = "flat"
        self.logger.info(
            f"初始化完成: mode={self.mode}, model={self.llm_client.config.model}, "
            f"schema={getattr(self.schema, 'slug', '?')} ({len(self.schema.fields)}字段)"
        )

    def extract(self, paper_id: str, content: str, **kwargs) -> ExtractionOutput:
        self.logger.info(f"开始提取: {paper_id} ({self.mode})")
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
