#!/usr/bin/env python3
"""
提取器 - 协调数据提取流程
"""
import json
import time
from pathlib import Path
from typing import Dict, Optional
from loguru import logger

from ..agents.llm_agent import LLMExtractionAgent


class Extractor:
    """数据提取器"""
    
    def __init__(self, output_dir: Path, mode: str = "full", model: str = None):
        """
        初始化提取器
        
        Args:
            output_dir: 输出目录
            mode: 提取模式 (full/chunk)
            model: 模型名称
        """
        self.output_dir = output_dir
        self.mode = mode
        self.model = model
        self.agent = None
    
    def _init_agent(self):
        """延迟初始化Agent"""
        if self.agent is None:
            self.agent = LLMExtractionAgent(mode=self.mode, model=self.model)
    
    def extract_single(self, paper: Dict) -> Dict:
        """
        提取单个论文
        
        Args:
            paper: 论文信息 {name, path, full_md}
        
        Returns:
            Dict: 提取结果
        """
        self._init_agent()
        
        paper_id = paper["name"]
        full_md = paper["full_md"]
        
        print(f"\n{'='*80}")
        print(f"提取论文: {paper_id}")
        print(f"{'='*80}\n")
        
        try:
            result = self.agent.process({
                "paper_id": paper_id,
                "full_text_path": str(full_md)
            })
            
            # 保存结果
            self.save_result(paper_id, result)
            
            # 统计
            count = result.get("count", 0)
            print(f"\n✅ 成功: 提取 {count} 条记录")
            
            return {
                "status": "success",
                "count": count,
                "result": result
            }
            
        except Exception as e:
            print(f"\n❌ 失败: {e}")
            logger.error(f"提取失败: {paper_id} - {e}")
            
            return {
                "status": "failed",
                "error": str(e)
            }
    
    def extract_batch(self, papers: list) -> Dict:
        """
        批量提取
        
        Args:
            papers: 论文列表
        
        Returns:
            Dict: 统计信息
        """
        self._init_agent()
        
        stats = {
            "success": 0,
            "failed": 0,
            "total_records": 0
        }
        failed_papers = []
        
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        for i, paper in enumerate(papers, 1):
            print(f"\n{'='*80}")
            print(f"[{i}/{len(papers)}] {paper['name']}")
            print(f"{'='*80}\n")
            
            result = self.extract_single(paper)
            
            if result["status"] == "success":
                stats["success"] += 1
                stats["total_records"] += result.get("count", 0)
            else:
                stats["failed"] += 1
                failed_papers.append(paper["name"])
            
            # 避免API限流
            if i < len(papers):
                time.sleep(2)
        
        # 显示总结
        self._print_summary(stats, failed_papers)
        
        return stats
    
    def save_result(self, paper_id: str, result: Dict):
        """保存提取结果"""
        output_file = self.output_dir / f"{paper_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    
    def _print_summary(self, stats: Dict, failed_papers: list):
        """打印总结"""
        print(f"\n{'='*80}")
        print("📊 批量提取完成")
        print(f"{'='*80}")
        print(f"✅ 成功: {stats['success']} 篇")
        print(f"❌ 失败: {stats['failed']} 篇")
        print(f"📝 总记录数: {stats['total_records']} 条")
        print(f"📂 保存位置: {self.output_dir}")
        
        if failed_papers:
            print(f"\n失败的论文:")
            for paper_name in failed_papers:
                print(f"  • {paper_name}")
        
        print(f"{'='*80}\n")
