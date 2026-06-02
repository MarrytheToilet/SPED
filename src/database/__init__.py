"""
数据库/目录模块。

旧的固定12表数据库已移除；保留 PaperCatalog（追踪PDF解析/提取状态）。
"""
from .catalog import PaperCatalog

__all__ = ['PaperCatalog']
