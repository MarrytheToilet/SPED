"""
提取模式策略 - 不同的提取流程策略

设计：
- ExtractionMode: 基类，定义流程接口
- FullMode: 全量提取
- SkeletonFillMode: 两阶段骨架填充
"""

from .base import ExtractionMode
from .full_mode import FullMode
from .skeleton_fill_mode import SkeletonFillMode

__all__ = ["ExtractionMode", "FullMode", "SkeletonFillMode"]
