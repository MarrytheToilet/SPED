#!/usr/bin/env python3
"""
人工关节材料数据提取系统 - 统一命令行工具

这是系统的主要命令行入口，整合了所有核心功能。
"""
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """主入口"""
    parser = argparse.ArgumentParser(
        description="人工关节材料数据提取系统 - 命令行工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # PDF处理
  %(prog)s pdf upload                    # 上传PDF到MinerU
  %(prog)s pdf status BATCH_ID           # 查询处理状态
  %(prog)s pdf download BATCH_ID         # 下载解析结果
  
  # 数据提取
  %(prog)s extract single PAPER_ID       # 提取单个论文
  %(prog)s extract batch                 # 批量提取所有论文
  %(prog)s extract test                  # 测试系统配置
  
  # 数据库操作
  %(prog)s db import                     # 导入JSON到数据库
  %(prog)s db export                     # 导出数据
  %(prog)s db stats                      # 查看统计信息
  
  # 完整工作流
  %(prog)s workflow run PAPER_ID         # 完整提取流程（推荐）
  
更多信息请访问: README_AGENTS.md
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # ========================================
    # PDF 处理命令
    # ========================================
    pdf_parser = subparsers.add_parser('pdf', help='PDF处理（上传/查询/下载）')
    pdf_subparsers = pdf_parser.add_subparsers(dest='pdf_action', help='PDF操作')
    
    # pdf upload
    pdf_upload = pdf_subparsers.add_parser('upload', help='上传PDF到MinerU')
    pdf_upload.add_argument('--dir', type=Path, help='PDF目录（默认: data/raw/pdfs）')
    
    # pdf status
    pdf_status = pdf_subparsers.add_parser('status', help='查询批次状态')
    pdf_status.add_argument('batch_id', help='批次ID')
    
    # pdf download
    pdf_download = pdf_subparsers.add_parser('download', help='下载解析结果')
    pdf_download.add_argument('batch_id', help='批次ID')
    pdf_download.add_argument('--output', type=Path, help='输出目录（默认: data/processed/parsed）')
    
    # pdf list
    pdf_list = pdf_subparsers.add_parser('list', help='列出所有批次')
    
    # ========================================
    # 数据提取命令
    # ========================================
    extract_parser = subparsers.add_parser('extract', help='数据提取')
    extract_subparsers = extract_parser.add_subparsers(dest='extract_action', help='提取操作')
    
    # extract test
    extract_test = extract_subparsers.add_parser('test', help='测试系统配置')
    
    # extract single
    extract_single = extract_subparsers.add_parser('single', help='提取单个论文')
    extract_single.add_argument('paper_id', nargs='?', help='论文ID（可选，不提供则交互式选择）')
    extract_single.add_argument('--mode', choices=['full', 'chunk', 'global_first'], 
                               default='full', help='提取模式（默认: full）')
    extract_single.add_argument('--model', help='LLM模型名称')
    
    # extract batch
    extract_batch = extract_subparsers.add_parser('batch', help='批量提取所有论文')
    extract_batch.add_argument('--mode', choices=['full', 'chunk', 'global_first'], 
                              default='full', help='提取模式（默认: full）')
    extract_batch.add_argument('--model', help='LLM模型名称')
    extract_batch.add_argument('--workers', type=int, help='并行worker数量')
    extract_batch.add_argument('--force', action='store_true', help='强制重跑所有论文（默认仅处理新增）')
    
    # ========================================
    # 数据库操作命令
    # ========================================
    db_parser = subparsers.add_parser('db', help='数据库操作')
    db_subparsers = db_parser.add_subparsers(dest='db_action', help='数据库操作')
    
    # db import
    db_import = db_subparsers.add_parser('import', help='导入JSON到数据库')
    db_import.add_argument('--dir', type=Path, help='JSON目录（默认: data/processed/extracted）')
    
    # db export
    db_export = db_subparsers.add_parser('export', help='导出数据')
    db_export.add_argument('--format', choices=['excel', 'csv'], default='excel', 
                          help='导出格式（默认: excel）')
    db_export.add_argument('--output', type=Path, help='输出文件路径')
    
    # db stats
    db_stats = db_subparsers.add_parser('stats', help='查看数据库统计')
    
    # db query
    db_query = db_subparsers.add_parser('query', help='查询数据')
    db_query.add_argument('--limit', type=int, default=10, help='返回记录数（默认: 10）')
    
    # ========================================
    # 完整工作流命令
    # ========================================
    workflow_parser = subparsers.add_parser('workflow', help='完整工作流')
    workflow_subparsers = workflow_parser.add_subparsers(dest='workflow_action', help='工作流操作')
    
    # workflow run
    workflow_run = workflow_subparsers.add_parser('run', help='运行完整提取流程')
    workflow_run.add_argument('paper_id', help='论文ID')
    workflow_run.add_argument('--mode', choices=['full', 'chunk', 'global_first'], 
                             default='full', help='提取模式（默认: full）')
    workflow_run.add_argument('--model', help='LLM模型名称')
    workflow_run.add_argument('--no-import', action='store_true', help='不自动导入数据库')
    
    # workflow batch
    workflow_batch = workflow_subparsers.add_parser('batch', help='批量运行完整流程')
    workflow_batch.add_argument('--mode', choices=['full', 'chunk', 'global_first'], 
                               default='full', help='提取模式（默认: full）')
    workflow_batch.add_argument('--model', help='LLM模型名称')
    workflow_batch.add_argument('--no-import', action='store_true', help='不自动导入数据库')
    
    # 解析参数
    args = parser.parse_args()
    
    # 如果没有提供命令，显示帮助
    if not args.command:
        parser.print_help()
        return 0
    
    # 执行相应的命令
    try:
        if args.command == 'pdf':
            return handle_pdf_command(args)
        elif args.command == 'extract':
            return handle_extract_command(args)
        elif args.command == 'db':
            return handle_db_command(args)
        elif args.command == 'workflow':
            return handle_workflow_command(args)
        else:
            parser.print_help()
            return 1
    except KeyboardInterrupt:
        print("\n\n操作已取消")
        return 130
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return 1


def handle_pdf_command(args):
    """处理PDF命令"""
    from src.pdfs.pdf_processor import PDFProcessor, quick_upload, quick_status, quick_download, show_stats
    
    processor = PDFProcessor()
    
    if args.pdf_action == 'upload':
        pdf_dir = args.dir
        batch_ids = quick_upload(pdf_dir)
        
        if batch_ids:
            print(f"\n💡 下一步:")
            print(f"   python scripts/cli.py pdf status {batch_ids[0]}")
        
        return 0 if batch_ids else 1
    
    elif args.pdf_action == 'status':
        quick_status(args.batch_id)
        return 0
    
    elif args.pdf_action == 'download':
        output_dir = args.output
        success = quick_download(args.batch_id, output_dir)
        
        if success:
            print(f"\n💡 下一步:")
            print(f"   python scripts/cli.py extract single")
        
        return 0 if success else 1
    
    elif args.pdf_action == 'list':
        quick_status(None)  # 查询所有批次
        return 0
    
    return 0


def handle_extract_command(args):
    """处理提取命令"""
    if args.extract_action == 'test':
        from scripts.full_extraction_pipeline import FullExtractionPipeline
        print("🧪 测试系统配置...")
        # 只初始化，不实际提取
        try:
            pipeline = FullExtractionPipeline()
            print("\n✅ 系统配置正确！")
            print(f"   模型: {pipeline.model}")
            print(f"   输出目录: {pipeline.output_dir}")
            return 0
        except Exception as e:
            print(f"\n❌ 配置错误: {e}")
            return 1
    
    elif args.extract_action == 'single':
        from scripts.full_extraction_pipeline import FullExtractionPipeline
        
        pipeline = FullExtractionPipeline(
            mode=args.mode,
            model=args.model
        )
        
        # 如果没有提供paper_id，交互式选择
        if not args.paper_id:
            from settings import PARSED_DIR
            papers = [d.name for d in PARSED_DIR.iterdir() 
                     if d.is_dir() and (d / "full.md").exists()]
            
            if not papers:
                print("❌ 未找到已解析的论文")
                return 1
            
            print("\n可用论文:")
            for i, paper in enumerate(papers[:20], 1):
                print(f"{i}. {paper}")
            
            if len(papers) > 20:
                print(f"... 还有 {len(papers) - 20} 篇")
            
            try:
                choice = int(input("\n请选择论文编号: ")) - 1
                paper_id = papers[choice]
            except (ValueError, IndexError):
                print("❌ 无效的选择")
                return 1
        else:
            paper_id = args.paper_id
        
        print(f"\n📝 提取论文: {paper_id}")
        print(f"   模式: {args.mode}")
        
        result = pipeline.process_single_paper(paper_id)
        
        if result.get('success'):
            print(f"\n✅ 提取成功！")
            print(f"   记录数: {result['count']}")
            print(f"   保存路径: data/processed/extracted/{paper_id}.json")
            return 0
        else:
            print(f"\n❌ 提取失败: {result.get('error')}")
            return 1
    
    elif args.extract_action == 'batch':
        from scripts.full_extraction_pipeline import FullExtractionPipeline
        
        pipeline = FullExtractionPipeline(
            mode=args.mode,
            model=args.model
        )
        
        print(f"\n🚀 批量提取")
        print(f"   模式: {args.mode}")
        print(f"   增量模式: {'关闭（全量重跑）' if args.force else '开启（跳过已提取）'}")
        
        stats = pipeline.process_batch_papers(skip_existing=not args.force)
        
        print(f"\n📊 提取完成:")
        print(f"   总论文: {stats['total']}")
        print(f"   跳过已提取: {stats['skipped_existing']}")
        print(f"   本次处理: {stats['to_process']}")
        print(f"   成功: {stats['success']}")
        print(f"   失败: {stats['failed']}")
        
        if stats['errors']:
            print(f"\n失败的论文:")
            for error in stats['errors'][:5]:
                print(f"   - {error['paper_id']}: {error['error']}")
        
        return 0 if stats['failed'] == 0 else 1
    
    return 0


def handle_db_command(args):
    """处理数据库命令"""
    from src.database.db_manager import DatabaseManager
    from settings import DB_PATH, EXTRACTED_DIR
    
    db = DatabaseManager(DB_PATH)
    
    if args.db_action == 'import':
        json_dir = args.dir or EXTRACTED_DIR
        print(f"📥 导入JSON: {json_dir}")
        
        json_files = list(json_dir.glob("*.json"))
        print(f"找到 {len(json_files)} 个JSON文件")
        
        success_count = 0
        for json_file in json_files:
            try:
                db.insert_from_json(json_file)
                success_count += 1
                print(f"✅ {json_file.name}")
            except Exception as e:
                print(f"❌ {json_file.name}: {e}")
        
        print(f"\n导入完成: {success_count}/{len(json_files)}")
        return 0
    
    elif args.db_action == 'export':
        output = args.output or f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        print(f"📤 导出数据: {output}")
        
        if args.format == 'excel':
            from src.database.excel_exporter import ExcelExporter
            from pathlib import Path
            exporter = ExcelExporter()
            output_path = Path("data/exports") / output
            output_path.parent.mkdir(parents=True, exist_ok=True)
            exporter.export_by_schema(output_path, filter_empty_sheets=True)
        else:
            from src.database.csv_exporter import CSVExporter
            exporter = CSVExporter(DB_PATH)
            exporter.export_expanded_csv(output)
        
        print(f"✅ 导出成功: {output}")
        return 0
    
    elif args.db_action == 'stats':
        stats = db.get_statistics()
        print(f"\n📊 数据库统计:")
        print(f"   总记录数: {stats.get('total_records', 0)}")
        print(f"   论文数: {stats.get('paper_count', 0)}")
        
        # 应用部位分布
        if 'application_distribution' in stats:
            print(f"\n   应用部位分布:")
            for part, count in list(stats['application_distribution'].items())[:5]:
                print(f"      {part}: {count}")
        
        return 0
    
    elif args.db_action == 'query':
        records = db.query_records(limit=args.limit)
        print(f"\n📋 最近 {len(records)} 条记录:")
        
        for i, record in enumerate(records, 1):
            print(f"\n{i}. {record.get('数据标识', 'N/A')}")
            print(f"   应用部位: {record.get('应用部位', 'N/A')}")
            print(f"   论文: {record.get('paper_id', 'N/A')}")
        
        return 0
    
    return 0


def handle_workflow_command(args):
    """处理工作流命令"""
    from scripts.full_extraction_pipeline import FullExtractionPipeline
    from src.database.db_manager import DatabaseManager
    from settings import DB_PATH, EXTRACTED_DIR
    from datetime import datetime
    
    if args.workflow_action == 'run':
        print(f"\n🔄 运行完整工作流: {args.paper_id}")
        
        # 步骤1: 提取数据
        print(f"\n[1/2] 提取数据...")
        pipeline = FullExtractionPipeline(
            mode=args.mode,
            model=args.model
        )
        
        result = pipeline.process_single_paper(args.paper_id)
        
        if not result.get('success'):
            print(f"❌ 提取失败: {result.get('error')}")
            return 1
        
        print(f"✅ 提取成功: {result['count']} 条记录")
        
        # 步骤2: 导入数据库（如果需要）
        if not args.no_import:
            print(f"\n[2/2] 导入数据库...")
            json_file = EXTRACTED_DIR / f"{args.paper_id}.json"
            
            try:
                db = DatabaseManager(DB_PATH)
                db.insert_from_json(json_file)
                print(f"✅ 导入成功")
            except Exception as e:
                print(f"❌ 导入失败: {e}")
                return 1
        
        print(f"\n🎉 工作流完成！")
        return 0
    
    elif args.workflow_action == 'batch':
        print(f"\n🔄 批量运行完整工作流")
        
        # 步骤1: 批量提取
        print(f"\n[1/2] 批量提取数据...")
        pipeline = FullExtractionPipeline(
            mode=args.mode,
            model=args.model
        )
        
        stats = pipeline.process_batch_papers()
        print(f"✅ 提取完成: {stats['success']}/{stats['total']}")
        
        # 步骤2: 批量导入（如果需要）
        if not args.no_import:
            print(f"\n[2/2] 批量导入数据库...")
            
            db = DatabaseManager(DB_PATH)
            json_files = list(EXTRACTED_DIR.glob("*.json"))
            
            success_count = 0
            for json_file in json_files:
                try:
                    db.insert_from_json(json_file)
                    success_count += 1
                except:
                    pass
            
            print(f"✅ 导入完成: {success_count}/{len(json_files)}")
        
        print(f"\n🎉 批量工作流完成！")
        return 0
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
