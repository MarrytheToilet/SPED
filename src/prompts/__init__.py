"""
Prompt层 - 提取模式与prompt构建。

新架构只保留：基于「生成schema」的扁平提取模式 GenericFlatMode。
（旧的12表 PromptAssembler / SchemaPromptGenerator / FullMode 已移除）
"""
from .modes import ExtractionMode, GenericFlatMode

__all__ = ["ExtractionMode", "GenericFlatMode"]
