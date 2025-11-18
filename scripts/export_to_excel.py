#!/usr/bin/env python3
"""
数据库导出为Excel工具
将SQLite数据库中的所有表导出为Excel文件

用法:
    python scripts/export_to_excel.py                           # 导出所有表
    python scripts/export_to_excel.py --output output.xlsx      # 指定输出文件
    python scripts/export_to_excel.py --tables sheet_1 sheet_2  # 只导出指定表
"""
import sys
import sqlite3
import argparse
from pathlib import Path
from datetime import datetime
from loguru import logger
import pandas as pd

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from settings import DB_PATH, DATA_DIR


def setup_logger():
    """配置日志"""
    logger.remove()
    logger.add(
        sys.stdout,
        level="INFO",
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>"
    )


def get_all_tables(conn):
    """获取数据库中所有表名"""
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    return tables


def export_table_to_dataframe(conn, table_name):
    """将表导出为DataFrame"""
    try:
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
        logger.info(f"✓ 表 {table_name}: {len(df)} 行")
        return df
    except Exception as e:
        logger.error(f"✗ 导出表 {table_name} 失败: {str(e)}")
        return None


def export_database_to_excel(
    db_path: str,
    output_path: str,
    table_names: list = None,
    include_metadata: bool = True
):
    """
    导出数据库到Excel文件
    
    Args:
        db_path: SQLite数据库路径
        output_path: 输出Excel文件路径
        table_names: 要导出的表名列表(None表示全部)
        include_metadata: 是否包含元数据Sheet
    """
    logger.info(f"=" * 80)
    logger.info(f"数据库导出到Excel")
    logger.info(f"=" * 80)
    logger.info(f"数据库: {db_path}")
    logger.info(f"输出文件: {output_path}")
    
    # 检查数据库文件
    if not Path(db_path).exists():
        logger.error(f"数据库文件不存在: {db_path}")
        return False
    
    # 连接数据库
    try:
        conn = sqlite3.connect(db_path)
        logger.info(f"✓ 数据库连接成功")
    except Exception as e:
        logger.error(f"✗ 数据库连接失败: {str(e)}")
        return False
    
    # 获取要导出的表
    all_tables = get_all_tables(conn)
    logger.info(f"数据库中共有 {len(all_tables)} 个表: {', '.join(all_tables)}")
    
    if table_names:
        # 验证指定的表是否存在
        invalid_tables = [t for t in table_names if t not in all_tables]
        if invalid_tables:
            logger.warning(f"以下表不存在: {', '.join(invalid_tables)}")
        tables_to_export = [t for t in table_names if t in all_tables]
    else:
        tables_to_export = all_tables
    
    if not tables_to_export:
        logger.error("没有要导出的表")
        conn.close()
        return False
    
    logger.info(f"将导出 {len(tables_to_export)} 个表")
    
    # 创建Excel写入器
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # 导出每个表
            exported_count = 0
            for table_name in tables_to_export:
                df = export_table_to_dataframe(conn, table_name)
                if df is not None:
                    # Excel sheet名称限制为31字符
                    sheet_name = table_name[:31]
                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    exported_count += 1
            
            # 添加元数据Sheet
            if include_metadata:
                metadata = {
                    "导出时间": [datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
                    "数据库路径": [db_path],
                    "导出表数量": [exported_count],
                    "总表数量": [len(all_tables)],
                    "导出的表": [", ".join(tables_to_export)]
                }
                metadata_df = pd.DataFrame(metadata)
                metadata_df.to_excel(writer, sheet_name="导出信息", index=False)
                logger.info(f"✓ 添加元数据Sheet")
            
        logger.info(f"=" * 80)
        logger.info(f"✅ 导出完成!")
        logger.info(f"   成功导出 {exported_count} 个表")
        logger.info(f"   输出文件: {output_path}")
        logger.info(f"=" * 80)
        
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"✗ 导出过程中出错: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        conn.close()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="将SQLite数据库导出为Excel文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s                                    # 导出所有表到默认文件
  %(prog)s --output my_export.xlsx            # 指定输出文件
  %(prog)s --tables sheet_1 sheet_2           # 只导出指定的表
  %(prog)s --no-metadata                      # 不包含元数据
        """
    )
    
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="输出Excel文件路径 (默认: data/exports/database_export_YYYYMMDD_HHMMSS.xlsx)"
    )
    
    parser.add_argument(
        "--tables", "-t",
        nargs="+",
        default=None,
        help="要导出的表名列表 (默认: 导出所有表)"
    )
    
    parser.add_argument(
        "--no-metadata",
        action="store_true",
        help="不包含元数据Sheet"
    )
    
    parser.add_argument(
        "--db",
        default=None,
        help=f"数据库路径 (默认: {DB_PATH})"
    )
    
    args = parser.parse_args()
    
    setup_logger()
    
    # 确定数据库路径
    db_path = args.db if args.db else DB_PATH
    
    # 确定输出路径
    if args.output:
        output_path = args.output
    else:
        # 默认输出到 data/exports/ 目录
        exports_dir = DATA_DIR / "exports"
        exports_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = exports_dir / f"database_export_{timestamp}.xlsx"
    
    # 执行导出
    success = export_database_to_excel(
        db_path=db_path,
        output_path=str(output_path),
        table_names=args.tables,
        include_metadata=not args.no_metadata
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
