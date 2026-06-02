"""
提取模式策略。

- ExtractionMode: 基类，定义流程接口
- GenericFlatMode: 基于生成schema的扁平提取（内联 value+evidence）
"""
from .base import ExtractionMode
from .flat_mode import GenericFlatMode

__all__ = ["ExtractionMode", "GenericFlatMode"]
