#!/usr/bin/env python3
"""
论文扫描器 - 扫描和管理已解析的论文
"""
from pathlib import Path
from typing import List, Dict


class PaperScanner:
    """扫描已解析的论文"""
    
    def __init__(self, parsed_dir: Path):
        self.parsed_dir = parsed_dir
    
    def scan(self) -> List[Dict]:
        """
        扫描所有已解析的论文
        
        Returns:
            List[Dict]: 论文列表，每项包含 name, path, full_md
        """
        papers = []
        
        if not self.parsed_dir.exists():
            return papers
        
        # 递归查找所有包含full.md的目录
        for full_md in self.parsed_dir.rglob("full.md"):
            paper_dir = full_md.parent
            papers.append({
                "name": paper_dir.name,
                "path": paper_dir,
                "full_md": full_md
            })
        
        # 按名称排序
        papers.sort(key=lambda x: x["name"])
        
        return papers
    
    def find_by_index(self, papers: List[Dict], index: int) -> Dict:
        """根据索引查找论文"""
        if 0 <= index < len(papers):
            return papers[index]
        raise IndexError(f"论文索引 {index} 超出范围 (0-{len(papers)-1})")
    
    def find_by_name(self, papers: List[Dict], name: str) -> Dict:
        """根据名称查找论文"""
        for paper in papers:
            if paper["name"] == name:
                return paper
        raise ValueError(f"未找到论文: {name}")
