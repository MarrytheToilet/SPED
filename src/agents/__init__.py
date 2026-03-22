"""
Agents模块 - 智能代理系统

保留的Agent:
- PDFProcessAgent: PDF处理
- ChunkFilterAgent: 文档分块过滤
- DatabaseInsertionAgent: 数据库写入

已迁移到新架构（src/extractors/）:
- ExtractionAgent → ExtractionService
- PromptBuilderAgent → PromptAssembler
"""

# 核心Agent基类
from .base import (
    BaseAgent,
    AgentResult,
    StatefulAgent,
    BatchAgent
)

# 保留的Agent实现
from .pdf_process_agent import PDFProcessAgent
from .chunk_filter_agent import ChunkFilterAgent
from .database_agent import DatabaseInsertionAgent

__all__ = [
    # 基类
    "BaseAgent",
    "AgentResult",
    "StatefulAgent",
    "BatchAgent",
    # Agent实现
    "PDFProcessAgent",
    "ChunkFilterAgent",
    "DatabaseInsertionAgent",
]
