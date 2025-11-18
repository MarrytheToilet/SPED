#!/usr/bin/env python3
"""
批量处理脚本 - 处理指定文件夹中的所有PDF解析结果

功能：
1. 自动扫描指定文件夹下的所有论文
2. 逐一提取信息并插入数据库
3. 生成处理报告
4. 支持断点续传（跳过已处理的论文）

用法：
    python scripts/batch_process.py --folder batch_1           # 处理指定batch
    python scripts/batch_process.py --folder batch_1 --skip-db  # 只提取，不写数据库
    python scripts/batch_process.py --folder batch_1 --resume   # 续传模式（跳过已处理）
"""

import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger
from typing import List, Dict, Any

# 添加项目根目录到path
sys.path.insert(0, str(Path(__file__).parent.parent))

from settings import PARSED_DIR, ANALYZED_DIR
from scripts.process_pipeline import ProcessingPipeline


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, use_database: bool = True, resume: bool = False):
        """
        初始化批量处理器
        
        Args:
            use_database: 是否写入数据库
            resume: 是否续传模式（跳过已处理的论文）
        """
        self.pipeline = ProcessingPipeline(use_database=use_database)
        self.use_database = use_database
        self.resume = resume
        self.results = []
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
    
    def is_already_processed(self, paper_id: str) -> bool:
        """检查论文是否已经处理过"""
        output_dir = ANALYZED_DIR / paper_id
        result_file = output_dir / "extraction_results.json"
        return result_file.exists()
    
    def process_folder(self, folder_name: str) -> Dict[str, Any]:
        """
        处理指定文件夹中的所有论文
        
        Args:
            folder_name: 文件夹名称（例如：batch_1）
        
        Returns:
            处理报告
        """
        folder_path = PARSED_DIR / folder_name
        
        if not folder_path.exists():
            logger.error(f"❌ 文件夹不存在: {folder_path}")
            return {"error": "文件夹不存在"}
        
        # 获取所有论文目录
        paper_dirs = sorted([d for d in folder_path.iterdir() if d.is_dir()])
        
        if not paper_dirs:
            logger.warning(f"⚠️  文件夹中没有找到论文目录: {folder_path}")
            return {"error": "没有找到论文"}
        
        self.stats['total'] = len(paper_dirs)
        
        logger.info("=" * 80)
        logger.info(f"📂 批量处理文件夹: {folder_name}")
        logger.info(f"📄 找到论文数量: {len(paper_dirs)}")
        logger.info(f"💾 数据库模式: {'开启' if self.use_database else '关闭'}")
        logger.info(f"🔄 续传模式: {'开启' if self.resume else '关闭'}")
        logger.info("=" * 80)
        
        # 开始处理
        start_time = datetime.now()
        
        for i, paper_dir in enumerate(paper_dirs, 1):
            paper_id = paper_dir.name
            
            logger.info(f"\n{'='*80}")
            logger.info(f"📄 [{i}/{len(paper_dirs)}] 处理论文: {paper_id}")
            logger.info(f"{'='*80}")
            
            # 检查是否已处理（续传模式）
            if self.resume and self.is_already_processed(paper_id):
                logger.info(f"⏭️  论文已处理，跳过: {paper_id}")
                self.stats['skipped'] += 1
                self.results.append({
                    'paper_id': paper_id,
                    'status': 'skipped',
                    'message': '已处理'
                })
                continue
            
            # 处理论文
            try:
                result = self.pipeline.process_paper(str(paper_dir), paper_id)
                
                if "error" in result:
                    logger.error(f"❌ 处理失败: {result['error']}")
                    self.stats['failed'] += 1
                    self.results.append({
                        'paper_id': paper_id,
                        'status': 'failed',
                        'error': result['error']
                    })
                else:
                    logger.success(f"✅ 处理成功: {paper_id}")
                    self.stats['success'] += 1
                    
                    # 统计提取的数据
                    extraction_info = self._get_extraction_info(result)
                    
                    self.results.append({
                        'paper_id': paper_id,
                        'status': 'success',
                        'extraction_info': extraction_info
                    })
                    
            except Exception as e:
                logger.error(f"❌ 处理异常: {str(e)}")
                logger.exception(e)
                self.stats['failed'] += 1
                self.results.append({
                    'paper_id': paper_id,
                    'status': 'failed',
                    'error': str(e)
                })
        
        # 处理完成
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # 生成报告
        report = self._generate_report(folder_name, duration)
        
        # 保存报告
        self._save_report(report, folder_name)
        
        return report
    
    def _get_extraction_info(self, result: Dict) -> Dict:
        """获取提取信息摘要"""
        info = {
            'extraction_type': result.get('extraction_type', 'unknown'),
            'data_count': 0,
            'field_count': 0
        }
        
        # 统计提取的数据
        if result.get('extraction_type') == 'multi_experiment':
            experiments = result.get('llm_extraction', {}).get('experiments', [])
            info['data_count'] = len(experiments)
            if experiments:
                # 统计第一个实验的字段数
                first_exp = experiments[0]
                info['field_count'] = len([v for v in first_exp.values() if v])
        else:
            llm_result = result.get('llm_extraction', {})
            info['data_count'] = 1
            info['field_count'] = len([v for v in llm_result.values() if v])
        
        # 数据库插入信息
        if 'database_insertion' in result:
            db_info = result['database_insertion']
            info['db_success'] = db_info.get('success', False)
            if db_info.get('extraction_type') == 'multi_experiment':
                info['db_inserted'] = db_info.get('success_count', 0)
        
        return info
    
    def _generate_report(self, folder_name: str, duration: float) -> Dict:
        """生成处理报告"""
        report = {
            'folder': folder_name,
            'timestamp': datetime.now().isoformat(),
            'duration_seconds': round(duration, 2),
            'statistics': self.stats.copy(),
            'success_rate': round(self.stats['success'] / self.stats['total'] * 100, 2) if self.stats['total'] > 0 else 0,
            'results': self.results
        }
        
        # 打印摘要
        logger.info("\n" + "=" * 80)
        logger.info("📊 处理报告摘要")
        logger.info("=" * 80)
        logger.info(f"文件夹: {folder_name}")
        logger.info(f"总数: {self.stats['total']}")
        logger.info(f"成功: {self.stats['success']} ✅")
        logger.info(f"失败: {self.stats['failed']} ❌")
        logger.info(f"跳过: {self.stats['skipped']} ⏭️")
        logger.info(f"成功率: {report['success_rate']}%")
        logger.info(f"耗时: {duration:.2f} 秒")
        logger.info(f"平均速度: {duration/self.stats['total']:.2f} 秒/篇" if self.stats['total'] > 0 else "N/A")
        logger.info("=" * 80)
        
        return report
    
    def _save_report(self, report: Dict, folder_name: str):
        """保存处理报告"""
        report_dir = Path("logs/batch_reports")
        report_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = report_dir / f"batch_report_{folder_name}_{timestamp}.json"
        
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📄 报告已保存: {report_file}")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="批量处理PDF解析结果",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python scripts/batch_process.py --folder batch_1
  python scripts/batch_process.py --folder batch_1 --skip-db
  python scripts/batch_process.py --folder batch_1 --resume
        """
    )
    
    parser.add_argument(
        "--folder",
        type=str,
        required=True,
        help="要处理的文件夹名称（例如：batch_1）"
    )
    
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="跳过数据库插入（只提取信息）"
    )
    
    parser.add_argument(
        "--resume",
        action="store_true",
        help="续传模式（跳过已处理的论文）"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="详细输出模式"
    )
    
    args = parser.parse_args()
    
    # 配置日志
    logger.remove()
    
    if args.verbose:
        log_format = "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        logger.add(sys.stdout, level="DEBUG", format=log_format)
    else:
        log_format = "<level>{level: <8}</level> | <level>{message}</level>"
        logger.add(sys.stdout, level="INFO", format=log_format)
    
    # 文件日志
    log_file = f"logs/batch_process_{args.folder}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logger.add(
        log_file,
        rotation="100 MB",
        retention="30 days",
        level="DEBUG",
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )
    
    # 创建批量处理器
    processor = BatchProcessor(
        use_database=not args.skip_db,
        resume=args.resume
    )
    
    # 处理文件夹
    try:
        report = processor.process_folder(args.folder)
        
        if "error" not in report:
            logger.success("✅ 批量处理完成！")
            sys.exit(0)
        else:
            logger.error(f"❌ 批量处理失败: {report['error']}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.warning("\n⚠️  用户中断处理")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ 批量处理异常: {str(e)}")
        logger.exception(e)
        sys.exit(1)


if __name__ == "__main__":
    main()
