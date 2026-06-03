"""
提取模式策略。

- ExtractionMode: 基类，定义流程接口
- GenericFlatMode: 基于生成schema的扁平提取（内联 value+evidence）
- MultiAgentFlatMode: 多 extractor 候选抽取 + merger 仲裁合并
"""
from .base import ExtractionMode
from .flat_mode import GenericFlatMode, MultiAgentFlatMode

__all__ = ["ExtractionMode", "GenericFlatMode", "MultiAgentFlatMode"]
