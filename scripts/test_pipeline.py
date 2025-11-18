#!/usr/bin/env python3
"""
完整的数据处理Pipeline测试工具

功能：
1. 测试PDF信息提取（不需要数据库）
2. 测试数据库插入（需要SQLite）
3. 支持详细/简洁两种输出模式
4. 提供交互式选择

用法：
    python scripts/test_pipeline.py              # 交互式模式
    python scripts/test_pipeline.py --extract    # 只测试提取
    python scripts/test_pipeline.py --database   # 完整测试（含数据库）
    python scripts/test_pipeline.py --simple     # 简洁输出模式
"""
import sys
import json
import argparse
from pathlib import Path
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent))

from src.agents.llm_agent import LLMExtractionAgent
from src.extractors.text_extractor import TextExtractor
from scripts.process_pipeline import ProcessingPipeline
from settings import PARSED_DIR, SCHEMA_DIR


def setup_logger(verbose=True):
    """配置日志输出"""
    logger.remove()
    
    if verbose:
        # 详细模式
        logger.add(
            sys.stdout,
            level="INFO",
            format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
        )
    else:
        # 简洁模式
        logger.add(
            sys.stdout,
            level="INFO",
            format="<level>{message}</level>"
        )
    
    # 文件日志（总是详细）
    logger.add(
        "logs/test_pipeline_{time}.log",
        rotation="10 MB",
        level="DEBUG",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}"
    )


def select_test_paper():
    """选择一篇测试论文"""
    batch_dir = PARSED_DIR / "output" / "batch_1"
    
    if not batch_dir.exists():
        batch_dir = PARSED_DIR / "batch_1"  # 备用路径
    
    if not batch_dir.exists():
        logger.error(f"批次目录不存在: {batch_dir}")
        return None
    
    paper_dirs = [d for d in batch_dir.iterdir() if d.is_dir()]
    
    if not paper_dirs:
        logger.error("未找到解析的论文")
        return None
    
    return paper_dirs[0]


def test_extraction_only(paper_dir: Path, verbose: bool = True):
    """测试提取功能（不需要数据库）"""
    
    if verbose:
        logger.info("=" * 80)
        logger.info("测试模式: 仅提取（无数据库）")
        logger.info("=" * 80)
    
    logger.info(f"\n📄 测试论文: {paper_dir.name}")
    
    # 1. 提取文本
    if verbose:
        logger.info("\n🔍 步骤1: 从解析结果中提取文本...")
    
    extractor = TextExtractor()
    data = extractor.extract_from_parsed(str(paper_dir))
    
    title = data.get('metadata', {}).get('title', '未提取到标题')
    sections = data.get('sections', {})
    
    if verbose:
        logger.info(f"   ✓ 论文标题: {title}")
        logger.info(f"   ✓ 章节数: {len(sections)}")
        logger.info(f"   ✓ 总字数: {sum(len(content) for content in sections.values())}")
        
        if sections:
            logger.info(f"\n   章节列表:")
            for i, (sec_name, content) in enumerate(list(sections.items())[:10], 1):
                logger.info(f"      {i}. {sec_name} ({len(content)} 字符)")
            if len(sections) > 10:
                logger.info(f"      ... 还有 {len(sections) - 10} 个章节")
    else:
        logger.info(f"章节数: {len(sections)}, 总字数: {sum(len(content) for content in sections.values())}")
    
    # 2. 使用LLM Agent提取结构化信息
    if verbose:
        logger.info("\n🤖 步骤2: 使用 AI 提取结构化信息...")
        logger.info("   提示: 这一步会调用 OpenAI API，可能需要1-2分钟")
    else:
        logger.info("\n开始AI提取...")
    
    schema_file = SCHEMA_DIR / "inferred_schema.json"
    if not schema_file.exists():
        logger.error(f"Schema 文件不存在: {schema_file}")
        return None
    
    agent = LLMExtractionAgent(schema_path=str(schema_file))
    
    input_data = {
        "sections": sections,
        "paper_id": paper_dir.name
    }
    
    try:
        result = agent.process(input_data)
        
        # 3. 保存结果
        output_file = Path("logs") / f"extraction_{paper_dir.name}.json"
        output_file.parent.mkdir(exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        if verbose:
            logger.info(f"\n✅ 提取成功！结果已保存到: {output_file}")
        else:
            logger.info(f"结果已保存: {output_file}")
        
        # 4. 分析提取结果
        analyze_extraction_result(result, verbose)
        
        return result
        
    except Exception as e:
        logger.error(f"\n✗ 提取失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return None


def analyze_extraction_result(result: dict, verbose: bool = True):
    """分析并显示提取结果"""
    
    if verbose:
        logger.info("\n📊 提取结果分析:")
        logger.info("=" * 80)
    else:
        logger.info("\n提取结果:")
    
    if result.get("extraction_type") == "multi_experiment":
        # 多组实验
        total = result.get("total_experiments", 0)
        experiments = result.get("experiments", [])
        
        logger.info(f"   检测到多组实验: {total} 组")
        
        if verbose:
            logger.info("")
            for idx, exp in enumerate(experiments, 1):
                logger.info(f"   实验组 {idx}:")
                logger.info(f"      ID: {exp.get('exp_id')}")
                logger.info(f"      DataID: {exp.get('dataid')}")
                
                non_null_fields = {k: v for k, v in exp.items() 
                                  if v is not None and v != "" 
                                  and k not in ["exp_id", "dataid"]}
                
                logger.info(f"      提取字段数: {len(non_null_fields)}")
                
                # 显示关键字段
                key_fields = ["数据标识", "应用部位", "球头基本信息", "内衬基本信息"]
                for field in key_fields:
                    if field in exp and exp[field]:
                        value = str(exp[field])[:50] + "..." if len(str(exp[field])) > 50 else exp[field]
                        logger.info(f"         ✓ {field}: {value}")
                
                logger.info("")
        else:
            for idx, exp in enumerate(experiments, 1):
                non_null = sum(1 for v in exp.values() if v is not None and v != "")
                logger.info(f"  实验 {idx}: {exp.get('exp_id')} | dataid={exp.get('dataid')} | {non_null}个字段")
    
    else:
        # 单组实验
        logger.info(f"   检测到单组实验")
        logger.info(f"   DataID: {result.get('dataid')}")
        
        non_null_fields = {k: v for k, v in result.items() 
                          if v is not None and v != "" 
                          and k not in ["extraction_type", "paper_id", "dataid"]}
        
        logger.info(f"   提取字段数: {len(non_null_fields)}")
        
        if verbose:
            # 字段分类统计
            categories = {}
            for field in non_null_fields.keys():
                parts = field.split('_')
                if len(parts) > 0:
                    category = parts[0]
                    categories[category] = categories.get(category, 0) + 1
            
            logger.info(f"\n   字段分类统计:")
            for category, count in sorted(categories.items()):
                logger.info(f"      {category}: {count} 个字段")
    
    if verbose:
        logger.info("\n" + "=" * 80)


def test_database_insertion(paper_dir: Path, verbose: bool = True):
    """测试数据库插入功能"""
    
    if verbose:
        logger.info("\n" + "=" * 80)
        logger.info("测试模式: 完整流程（包含数据库）")
        logger.info("=" * 80)
        logger.warning("⚠️  注意：此操作会真实写入数据库！")
    else:
        logger.info("\n测试数据库插入...")
    
    try:
        pipeline = ProcessingPipeline(use_database=True)
        result = pipeline.process_paper(str(paper_dir))
        
        if "error" in result:
            logger.error(f"处理失败: {result['error']}")
            return False
        
        if verbose:
            logger.info("\n" + "=" * 80)
            logger.info("处理结果")
            logger.info("=" * 80)
        
        # 显示结果
        logger.info(f"Paper ID: {result.get('paper_id', 'N/A')}")
        logger.info(f"提取类型: {result.get('extraction_type', 'N/A')}")
        
        if "database_insertion" in result:
            db_info = result["database_insertion"]
            success = db_info.get('success', False)
            
            if success:
                logger.info(f"✅ 数据库插入成功")
            else:
                logger.error(f"❌ 数据库插入失败")
            
            if db_info.get('extraction_type') == 'multi_experiment':
                success_count = db_info.get('success_count', 0)
                total = db_info.get('total_experiments', 0)
                logger.info(f"成功插入: {success_count}/{total} 组实验")
                
                if verbose:
                    for res in db_info.get('results', []):
                        status = "✓" if res.get('success') else "✗"
                        logger.info(f"  {status} {res.get('exp_id')}: dataid={res.get('dataid')}")
            else:
                logger.info(f"Data ID: {db_info.get('dataid', 'N/A')}")
        
        # 保存详细结果
        output_file = Path("logs") / f"database_test_{paper_dir.name}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        if verbose:
            logger.info(f"\n详细结果已保存到: {output_file}")
        
        return True
        
    except Exception as e:
        logger.exception(f"数据库测试失败: {str(e)}")
        return False


def interactive_mode():
    """交互式模式"""
    setup_logger(verbose=True)
    
    logger.info("=" * 80)
    logger.info("PDF 数据处理 Pipeline 测试工具")
    logger.info("=" * 80)
    
    # 选择测试论文
    paper_dir = select_test_paper()
    if not paper_dir:
        return
    
    logger.info("\n请选择测试模式:")
    logger.info("  1. 仅测试提取（不需要数据库）")
    logger.info("  2. 测试提取 + 数据库插入（需要SQLite）")
    logger.info("  3. 退出")
    
    choice = input("\n请输入选项 (1-3): ").strip()
    
    if choice == "1":
        test_extraction_only(paper_dir, verbose=True)
        logger.info("\n✅ 提取测试完成！")
        logger.info("\n💡 提示:")
        logger.info("   - 如需测试数据库插入，请重新运行并选择选项2")
        logger.info("   - 或直接运行: python test_pipeline.py --database")
    
    elif choice == "2":
        logger.info("\n开始完整流程测试（提取 + 数据库插入）...")
        
        # 直接运行完整流程（test_database_insertion内部会调用pipeline，包含提取和插入）
        success = test_database_insertion(paper_dir, verbose=True)
        
        if success:
            logger.info("\n✅ 完整流程测试成功！")
        else:
            logger.error("\n❌ 完整流程测试失败")
    
    elif choice == "3":
        logger.info("退出")
    
    else:
        logger.error("无效的选项")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="PDF数据处理Pipeline测试工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/test_pipeline.py              # 交互式模式
  python scripts/test_pipeline.py --extract    # 只测试提取
  python scripts/test_pipeline.py --database   # 完整测试（含数据库）
  python scripts/test_pipeline.py --simple     # 简洁输出
        """
    )
    
    parser.add_argument(
        '--extract',
        action='store_true',
        help='只测试提取功能（不需要数据库）'
    )
    
    parser.add_argument(
        '--database',
        action='store_true',
        help='测试完整流程（包含数据库插入）'
    )
    
    parser.add_argument(
        '--simple',
        action='store_true',
        help='使用简洁输出模式'
    )
    
    args = parser.parse_args()
    
    # 如果没有指定参数，使用交互式模式
    if not (args.extract or args.database):
        interactive_mode()
        return
    
    # 设置日志
    verbose = not args.simple
    setup_logger(verbose=verbose)
    
    # 选择测试论文
    paper_dir = select_test_paper()
    if not paper_dir:
        sys.exit(1)
    
    # 执行测试
    if args.extract:
        result = test_extraction_only(paper_dir, verbose=verbose)
        if result:
            logger.info("\n✅ 提取测试完成！")
            sys.exit(0)
        else:
            logger.error("\n❌ 提取测试失败")
            sys.exit(1)
    
    elif args.database:
        # 先提取
        logger.info("步骤1: 测试提取...")
        extraction_result = test_extraction_only(paper_dir, verbose=verbose)
        
        if not extraction_result:
            logger.error("提取失败")
            sys.exit(1)
        
        # 再测试数据库
        logger.info("\n步骤2: 测试数据库插入...")
        success = test_database_insertion(paper_dir, verbose=verbose)
        
        if success:
            logger.info("\n✅ 完整流程测试成功！")
            sys.exit(0)
        else:
            logger.error("\n❌ 数据库测试失败")
            sys.exit(1)


if __name__ == "__main__":
    main()
