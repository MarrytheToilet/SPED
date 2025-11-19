"""
主处理Pipeline - 协调整个信息提取和入库流程
"""
import sys
from pathlib import Path
from loguru import logger
from typing import List, Dict, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import multiprocessing

# 添加项目根目录到path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from settings import PARSED_DIR, EXTRACTED_DIR, ANALYZED_DIR, SCHEMA_DIR
from src.extractors.text_extractor import TextExtractor
from src.agents.base_agent import AgentOrchestrator
from src.agents.llm_agent import LLMExtractionAgent
from src.agents.database_agent import DatabaseInsertionAgent


class ProcessingPipeline:
    """完整的处理流程"""
    
    def __init__(self, use_database: bool = True, max_workers: int = None):
        """
        初始化处理流程
        
        Args:
            use_database: 是否使用数据库插入Agent
            max_workers: 并行处理的最大worker数量，None则使用配置文件设置
        """
        self.text_extractor = TextExtractor()
        self.orchestrator = AgentOrchestrator()
        self.use_database = use_database
        
        # 设置并行worker数量
        if max_workers is None:
            # 从配置文件读取
            from settings import DEFAULT_WORKERS, MAX_WORKERS
            if DEFAULT_WORKERS is not None:
                self.max_workers = DEFAULT_WORKERS
            else:
                # 自动选择：CPU核心数，但不超过MAX_WORKERS
                cpu_count = multiprocessing.cpu_count()
                self.max_workers = min(cpu_count, MAX_WORKERS)
        else:
            self.max_workers = max_workers
        
        logger.info(f"Pipeline初始化: 并行worker数={self.max_workers}")
        
        # 注册Agents
        self._setup_agents()
    
    def _setup_agents(self):
        """设置Agents"""
        # LLM提取Agent
        schema_file = SCHEMA_DIR / "inferred_schema.json"
        llm_agent = LLMExtractionAgent(schema_path=str(schema_file))
        self.orchestrator.register_agent("llm_extraction", llm_agent)
        
        # 数据库插入Agent（可选）
        if self.use_database:
            db_agent = DatabaseInsertionAgent()
            self.orchestrator.register_agent("database_insertion", db_agent)
            self.orchestrator.set_pipeline(["llm_extraction", "database_insertion"])
        else:
            self.orchestrator.set_pipeline(["llm_extraction"])
    
    def process_paper(self, paper_dir: str, paper_id: str = None) -> Dict[str, Any]:
        """
        处理单篇论文
        
        Args:
            paper_dir: 论文解析结果目录
            paper_id: 论文ID（可选，默认使用目录名）
        
        Returns:
            处理结果
        """
        paper_path = Path(paper_dir)
        if paper_id is None:
            paper_id = paper_path.name
        
        logger.info(f"="*60)
        logger.info(f"开始处理论文: {paper_id}")
        logger.info(f"="*60)
        
        # Step 1: 提取文本
        logger.info("Step 1: 提取文本...")
        extracted_data = self.text_extractor.extract_from_parsed(str(paper_path))
        
        if not extracted_data.get('text'):
            logger.error(f"无法提取文本: {paper_id}")
            return {"error": "文本提取失败"}
        
        logger.info(f"文本提取成功: {len(extracted_data['text'])} 字符")
        logger.info(f"章节数: {len(extracted_data['sections'])}")
        logger.info(f"章节列表: {list(extracted_data['sections'].keys())}")
        
        # Step 2: 使用Agent按section提取结构化信息
        logger.info("\nStep 2: 使用LLM按section提取结构化信息...")
        
        # 准备输入数据 - 传入所有sections
        input_data = {
            "sections": extracted_data['sections'],
            "paper_id": paper_id
        }
        
        # 运行Agent流程（LLM Agent会自动按section处理）
        agent_results = self.orchestrator.run_pipeline(input_data)
        
        # Step 3: 保存结果
        logger.info("\nStep 3: 保存结果...")
        self._save_results(agent_results, paper_id)
        
        logger.info(f"\n{'='*60}")
        logger.info(f"论文处理完成: {paper_id}")
        logger.info(f"{'='*60}\n")
        
        return agent_results
    
    def process_batch(self, batch_name: str = "batch_1", parallel: bool = True) -> List[Dict]:
        """
        批量处理论文
        
        Args:
            batch_name: 批次名称
            parallel: 是否并行处理（默认True）
        
        Returns:
            所有论文的处理结果
        """
        batch_dir = PARSED_DIR / batch_name
        
        if not batch_dir.exists():
            logger.error(f"批次目录不存在: {batch_dir}")
            return []
        
        # 获取所有论文目录
        paper_dirs = [d for d in batch_dir.iterdir() if d.is_dir()]
        logger.info(f"发现 {len(paper_dirs)} 篇论文")
        
        if parallel and len(paper_dirs) > 1:
            logger.info(f"启动并行处理模式: {self.max_workers} workers")
            results = self._process_batch_parallel(paper_dirs)
        else:
            logger.info(f"使用串行处理模式")
            results = self._process_batch_sequential(paper_dirs)
        
        # 统计
        success_count = sum(1 for r in results if r["status"] == "success")
        logger.info(f"\n批量处理完成:")
        logger.info(f"  成功: {success_count}/{len(results)}")
        logger.info(f"  失败: {len(results) - success_count}/{len(results)}")
        
        return results
    
    def _process_batch_sequential(self, paper_dirs: List[Path]) -> List[Dict]:
        """串行处理（原有逻辑）"""
        results = []
        for i, paper_dir in enumerate(paper_dirs, 1):
            logger.info(f"\n处理进度: {i}/{len(paper_dirs)}")
            
            try:
                result = self.process_paper(str(paper_dir))
                results.append({
                    "paper_id": paper_dir.name,
                    "status": "success",
                    "result": result
                })
            except Exception as e:
                logger.error(f"处理失败 [{paper_dir.name}]: {str(e)}")
                results.append({
                    "paper_id": paper_dir.name,
                    "status": "failed",
                    "error": str(e)
                })
        
        return results
    
    def _process_batch_parallel(self, paper_dirs: List[Path]) -> List[Dict]:
        """并行处理"""
        results = []
        completed_count = 0
        total_count = len(paper_dirs)
        
        # 使用ThreadPoolExecutor进行并行处理
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_paper = {
                executor.submit(self._process_single_paper_safe, str(paper_dir)): paper_dir
                for paper_dir in paper_dirs
            }
            
            # 处理完成的任务
            for future in as_completed(future_to_paper):
                paper_dir = future_to_paper[future]
                completed_count += 1
                
                try:
                    result = future.result()
                    results.append(result)
                    
                    status_icon = "✓" if result["status"] == "success" else "✗"
                    logger.info(f"[{completed_count}/{total_count}] {status_icon} {result['paper_id']}")
                    
                except Exception as e:
                    logger.error(f"[{completed_count}/{total_count}] ✗ {paper_dir.name}: {str(e)}")
                    results.append({
                        "paper_id": paper_dir.name,
                        "status": "failed",
                        "error": str(e)
                    })
        
        return results
    
    def _process_single_paper_safe(self, paper_dir: str) -> Dict:
        """安全的单论文处理（用于并行）"""
        paper_path = Path(paper_dir)
        try:
            result = self.process_paper(paper_dir)
            return {
                "paper_id": paper_path.name,
                "status": "success",
                "result": result
            }
        except Exception as e:
            return {
                "paper_id": paper_path.name,
                "status": "failed",
                "error": str(e)
            }
    
    def _save_results(self, results: Dict, paper_id: str):
        """保存处理结果"""
        import json
        
        output_dir = ANALYZED_DIR / paper_id
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / "extraction_results.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"结果已保存到: {output_file}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="人工关节信息提取Pipeline")
    parser.add_argument("--paper-dir", type=str, help="单篇论文目录")
    parser.add_argument("--paper-id", type=str, help="论文ID")
    parser.add_argument("--batch", type=str, default="batch_1", help="批次名称")
    parser.add_argument("--no-db", action="store_true", help="不使用数据库")
    parser.add_argument("--test", action="store_true", help="测试模式（只处理1篇）")
    parser.add_argument("--no-parallel", action="store_true", help="禁用并行处理")
    parser.add_argument("--workers", type=int, default=None, help="并行worker数量（默认=CPU核心数，最大4）")
    
    args = parser.parse_args()
    
    # 配置日志
    logger.add(
        "logs/pipeline_{time}.log",
        rotation="100 MB",
        retention="10 days",
        level="INFO"
    )
    
    # 创建Pipeline
    pipeline = ProcessingPipeline(
        use_database=not args.no_db,
        max_workers=args.workers
    )
    
    if args.paper_dir:
        # 处理单篇论文
        pipeline.process_paper(args.paper_dir, args.paper_id)
    else:
        # 批量处理
        if args.test:
            # 测试模式：只处理第一篇
            batch_dir = PARSED_DIR / args.batch
            paper_dirs = [d for d in batch_dir.iterdir() if d.is_dir()]
            if paper_dirs:
                logger.info("测试模式：只处理第一篇论文")
                pipeline.process_paper(str(paper_dirs[0]))
        else:
            pipeline.process_batch(args.batch, parallel=not args.no_parallel)


if __name__ == "__main__":
    main()
