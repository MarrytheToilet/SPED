"""
Prompt组装层 - 与模型调用解耦的Prompt构建

设计原则：
1. 不关心具体模型，只负责组装prompt
2. 支持多种组装模式（全量/分块）
3. 模板可配置
4. Schema驱动的prompt生成
"""

from .assembler import PromptAssembler, AssembledPrompt
from .modes import ExtractionMode, FullMode, SkeletonFillMode
from .schema_generator import SchemaPromptGenerator, GeneratedPromptParts

__all__ = [
    "PromptAssembler",
    "AssembledPrompt",
    "ExtractionMode",
    "FullMode",
    "SkeletonFillMode",
    "SchemaPromptGenerator",
    "GeneratedPromptParts",
]
