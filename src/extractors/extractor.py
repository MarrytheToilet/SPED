#!/usr/bin/env python3
"""
提取器 - 协调数据提取流程
"""
import json
import time
from pathlib import Path
from typing import Dict, Optional, List
from loguru import logger
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

from ..agents.llm_agent import LLMExtractionAgent


class Extractor:
    """数据提取器"""
    
    def __init__(self, output_dir: Path, mode: str = "full", model: str = None, max_workers: int = None):
        """
        初始化提取器
        
        Args:
            output_dir: 输出目录
            mode: 提取模式 (full/chunk)
            model: 模型名称
            max_workers: 并行worker数量，None则使用配置文件设置
        """
        self.output_dir = output_dir
        self.mode = mode
        self.model = model
        self.agent = None
        
        # 设置并行worker数量
        if max_workers is None:
            # 从配置文件读取
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent.parent))
            import settings
            
            if settings.DEFAULT_WORKERS is not None:
                self.max_workers = settings.DEFAULT_WORKERS
            else:
                # 自动选择：CPU核心数，但不超过MAX_WORKERS
                cpu_count = multiprocessing.cpu_count()
                self.max_workers = min(cpu_count, settings.MAX_WORKERS)
        else:
            self.max_workers = max_workers
        
        logger.info(f"Extractor初始化: 并行worker数={self.max_workers}")
    
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
    
    def extract_batch(self, papers: list, parallel: bool = True) -> Dict:
        """
        批量提取
        
        Args:
            papers: 论文列表
            parallel: 是否使用并行处理（默认True）
        
        Returns:
            Dict: 统计信息
        """
        # 确保输出目录存在
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        if parallel and len(papers) > 1:
            logger.info(f"启动并行提取模式: {self.max_workers} workers")
            return self._extract_batch_parallel(papers)
        else:
            logger.info(f"使用串行提取模式")
            return self._extract_batch_sequential(papers)
    
    def _extract_batch_sequential(self, papers: list) -> Dict:
        """串行批量提取（原有逻辑）"""
        self._init_agent()
        
        stats = {
            "success": 0,
            "failed": 0,
            "total_records": 0
        }
        failed_papers = []
        
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
    
    def _extract_batch_parallel(self, papers: list) -> Dict:
        """并行批量提取"""
        stats = {
            "success": 0,
            "failed": 0,
            "total_records": 0
        }
        failed_papers = []
        completed_count = 0
        total_count = len(papers)
        
        # 使用ThreadPoolExecutor进行并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_paper = {
                executor.submit(self._extract_single_safe, paper): paper
                for paper in papers
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_paper):
                paper = future_to_paper[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    
                    if result["status"] == "success":
                        stats["success"] += 1
                        stats["total_records"] += result.get("count", 0)
                        status_icon = "✓"
                    else:
                        stats["failed"] += 1
                        failed_papers.append(paper["name"])
                        status_icon = "✗"
                    
                    print(f"[{completed_count}/{total_count}] {status_icon} {paper['name']} - {result.get('count', 0)} 条记录")
                    
                except Exception as e:
                    stats["failed"] += 1
                    failed_papers.append(paper["name"])
                    print(f"[{completed_count}/{total_count}] ✗ {paper['name']} - 错误: {e}")
        
        # 显示总结
        self._print_summary(stats, failed_papers)
        
        return stats
    
    def _extract_single_safe(self, paper: Dict) -> Dict:
        """安全的单论文提取（用于并行，每个worker独立创建Agent）"""
        # 每个worker独立创建Agent实例（线程安全）
        agent = LLMExtractionAgent(mode=self.mode, model=self.model)
        
        paper_id = paper["name"]
        full_md = paper["full_md"]
        
        try:
            result = agent.process({
                "paper_id": paper_id,
                "full_text_path": str(full_md)
            })
            
            # 保存结果
            self.save_result(paper_id, result)
            
            # 统计
            count = result.get("count", 0)
            
            return {
                "status": "success",
                "count": count,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"提取失败: {paper_id} - {e}")
            
            return {
                "status": "failed",
                "error": str(e)
            }
    
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
