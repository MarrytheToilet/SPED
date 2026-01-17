#!/usr/bin/env python3
"""
Excel多表导出器 - 按照schema规定的表结构导出为多sheet的Excel文件
"""
import json
import sqlite3
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.utils import get_column_letter

from .db_manager import DatabaseManager


class ExcelExporter:
    """Excel多表导出类"""
    
    # 中文表名到数据库表名的映射
    TABLE_NAME_MAPPING = {
        '基本信息表': 'basic_info',
        '内衬基本信息表': 'liner_basic',
        '球头基本信息表': 'head_basic',
        '配合信息表': 'fitting_info',
        '股骨柄基本信息表': 'stem_basic',
        '内衬物理性能表': 'liner_properties',
        '球头物理性能表': 'head_properties',
        '股骨柄物理性能表': 'stem_properties',
        '性能测试结果表': 'test_results',
        '计算模拟参数表': 'simulation_params',
        '计算模拟图像表': 'simulation_images'
    }
    
    def __init__(self, 
                 db_manager: Optional[DatabaseManager] = None,
                 schema_file: Path = Path("data_schema/schema.json")):
        """
        初始化Excel导出器
        
        Args:
            db_manager: 数据库管理器实例
            schema_file: schema文件路径
        """
        self.db = db_manager or DatabaseManager()
        self.schema_file = schema_file
        self.schema = self._load_schema()
    
    def _load_schema(self) -> Dict:
        """加载schema定义"""
        try:
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"加载schema失败: {e}")
            return {"schema_version": "2.0", "tables": []}
    
    def _parse_json_field(self, value: Any) -> Any:
        """
        解析JSON字段
        
        Args:
            value: 字段值
            
        Returns:
            解析后的值（字典或原值）
        """
        if value is None or value == '' or value == 'null':
            return {}
        
        if isinstance(value, str) and value.startswith('{'):
            try:
                return json.loads(value)
            except:
                return {}
        
        return value if isinstance(value, dict) else {}
    
    def _extract_field_value(self, record: Dict[str, Any], column_def: Dict) -> Any:
        """
        根据列定义从记录中提取字段值
        
        Args:
            record: 数据记录
            column_def: 列定义
            
        Returns:
            字段值
        """
        original_name = column_def.get('original', '')
        
        # 策略1: 直接匹配字段名
        if original_name in record:
            return record.get(original_name, '')
        
        # 策略2: 将点号转换为下划线尝试匹配（球头信息.球头基本信息 -> 球头信息_球头基本信息）
        normalized_name = original_name.replace('.', '_')
        if normalized_name in record:
            value = record.get(normalized_name, '')
            return value
        
        # 策略3: 处理嵌套字段（从JSON字段中提取子字段）
        if '.' in original_name:
            parts = original_name.split('.')
            
            # 尝试多级嵌套：球头信息.球头基本信息.材料编号
            # 先尝试从 球头信息_球头基本信息 中获取
            for i in range(len(parts) - 1, 0, -1):
                parent_key = '_'.join(parts[:i])
                sub_key = '.'.join(parts[i:])
                
                parent_value = record.get(parent_key)
                if parent_value:
                    parent_data = self._parse_json_field(parent_value)
                    if isinstance(parent_data, dict) and sub_key in parent_data:
                        return parent_data.get(sub_key, '')
            
            # 尝试从第一层字段中获取
            parent_field = parts[0]
            sub_field = '.'.join(parts[1:])
            
            parent_value = record.get(parent_field)
            if parent_value:
                parent_data = self._parse_json_field(parent_value)
                if isinstance(parent_data, dict):
                    return parent_data.get(sub_field, '')
        
        return ''
    
    def _style_header(self, worksheet):
        """设置表头样式"""
        header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        header_font = Font(bold=True, color="FFFFFF", size=11)
        
        for cell in worksheet[1]:
            cell.fill = header_fill
            cell.font = header_font
            cell.alignment = Alignment(horizontal='center', vertical='center', wrap_text=True)
    
    def _auto_adjust_column_width(self, worksheet):
        """自动调整列宽"""
        for column in worksheet.columns:
            max_length = 0
            column_letter = get_column_letter(column[0].column)
            
            for cell in column:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except:
                    pass
            
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    def export_by_schema(self, output_file: Path, filter_empty_sheets: bool = True) -> bool:
        """
        按照schema定义导出多表Excel
        
        Args:
            output_file: 输出文件路径
            filter_empty_sheets: 是否过滤空的sheet
            
        Returns:
            是否成功
        """
        try:
            # 创建Excel工作簿
            wb = openpyxl.Workbook()
            wb.remove(wb.active)  # 删除默认sheet
            
            # 支持新旧两种schema格式
            tables = self.schema.get('tables', [])
            if isinstance(tables, dict):
                # 旧格式：tables是字典
                tables_list = list(tables.items())
            else:
                # 新格式：tables是列表
                tables_list = [(t.get('sheet_name', t.get('table_name')), t) for t in tables]
            
            sheet_count = 0
            empty_sheets = []
            
            # 遍历schema中定义的每个表
            for table_key, table_def in tables_list:
                sheet_display_name = table_def.get('sheet_name', table_def.get('sheet', table_key))
                table_name = table_def.get('table_name', table_key)
                columns = table_def.get('columns', [])
                
                if not columns:
                    logger.warning(f"跳过表 {table_name}: 没有定义列")
                    continue
                
                # 获取数据库表名
                db_table_name = self.TABLE_NAME_MAPPING.get(table_name, table_name)
                
                logger.info(f"处理表: {sheet_display_name} -> {db_table_name} ({len(columns)} 列)")
                
                # 查询该表的数据
                try:
                    with sqlite3.connect(self.db.db_path) as conn:
                        conn.row_factory = sqlite3.Row
                        cursor = conn.cursor()
                        cursor.execute(f"SELECT * FROM {db_table_name}")
                        records = [dict(row) for row in cursor.fetchall()]
                except Exception as e:
                    logger.warning(f"查询表 {db_table_name} 失败: {e}")
                    records = []
                
                if not records and filter_empty_sheets:
                    empty_sheets.append(sheet_display_name)
                    logger.info(f"  跳过空表: {sheet_display_name}")
                    continue
                
                # 创建sheet
                ws = wb.create_sheet(title=sheet_display_name[:31])  # Excel sheet名称限制31字符
                
                # 写入表头
                headers = [col.get('name', '') for col in columns] if isinstance(columns[0], dict) else columns
                ws.append(headers)
                
                # 写入数据
                row_count = 0
                for record in records:
                    row_data = []
                    
                    for column_def in columns:
                        if isinstance(column_def, dict):
                            col_name = column_def.get('name', '')
                        else:
                            col_name = column_def
                        
                        # 直接从记录中获取值
                        value = record.get(col_name, '')
                        row_data.append(value if value else '')
                    
                    ws.append(row_data)
                    row_count += 1
                
                # 设置样式
                self._style_header(ws)
                self._auto_adjust_column_width(ws)
                
                if row_count == 0:
                    empty_sheets.append(sheet_display_name)
                    logger.info(f"  ✓ {sheet_display_name}: 0 条记录（空表）")
                else:
                    sheet_count += 1
                    logger.info(f"  ✓ {sheet_display_name}: {row_count} 条记录")
            
            # 如果需要过滤空sheet，删除它们
            if filter_empty_sheets and empty_sheets:
                logger.info(f"\n删除 {len(empty_sheets)} 个空sheet...")
                for sheet_name in empty_sheets:
                    if sheet_name in wb.sheetnames:
                        del wb[sheet_name]
            
            # 如果没有任何sheet，至少创建一个
            if len(wb.sheetnames) == 0:
                ws = wb.create_sheet(title="无数据")
                ws.append(["提示", "没有找到任何数据"])
            
            # 创建输出目录
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存Excel文件
            wb.save(output_file)
            
            logger.info(f"\n{'='*80}")
            logger.info(f"导出成功!")
            logger.info(f"文件: {output_file}")
            logger.info(f"Sheet数: {len(wb.sheetnames)}")
            logger.info(f"记录数: {len(records)}")
            if empty_sheets and filter_empty_sheets:
                logger.info(f"已过滤空sheet: {len(empty_sheets)} 个")
            logger.info(f"{'='*80}")
            
            return True
            
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def export_main_table_only(self, output_file: Path) -> bool:
        """
        只导出主表（is_main=True）
        
        Args:
            output_file: 输出文件路径
            
        Returns:
            是否成功
        """
        try:
            records = self.db.query_all()
            
            if not records:
                logger.warning("没有数据可导出")
                return False
            
            # 创建Excel工作簿
            wb = openpyxl.Workbook()
            wb.remove(wb.active)
            
            tables = self.schema.get('tables', {})
            
            # 只处理主表
            for table_name, table_def in tables.items():
                if not table_def.get('is_main', False):
                    continue
                
                sheet_display_name = table_def.get('sheet', table_name)
                columns = table_def.get('columns', [])
                
                if not columns:
                    continue
                
                logger.info(f"导出主表: {sheet_display_name}")
                
                # 创建sheet
                ws = wb.create_sheet(title=sheet_display_name[:31])
                
                # 写入表头
                headers = [col.get('original', col.get('name', '')) for col in columns]
                ws.append(headers)
                
                # 写入数据
                row_count = 0
                for record in records:
                    row_data = []
                    for column_def in columns:
                        value = self._extract_field_value(record, column_def)
                        row_data.append(value if value else '')
                    ws.append(row_data)
                    row_count += 1
                
                # 设置样式
                self._style_header(ws)
                self._auto_adjust_column_width(ws)
                
                logger.info(f"  ✓ {sheet_display_name}: {row_count} 条记录")
            
            if len(wb.sheetnames) == 0:
                logger.warning("没有找到主表")
                return False
            
            # 创建输出目录并保存
            output_file.parent.mkdir(parents=True, exist_ok=True)
            wb.save(output_file)
            
            logger.info(f"导出成功: {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出Excel失败: {e}")
            import traceback
            traceback.print_exc()
            return False


def export_excel_all_tables(output_dir: Path = Path("data/exports"), 
                            filter_empty: bool = True) -> bool:
    """
    导出所有表到Excel（按schema组织）
    
    Args:
        output_dir: 输出目录
        filter_empty: 是否过滤空表
        
    Returns:
        是否成功
    """
    exporter = ExcelExporter()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"multi_tables_{timestamp}.xlsx"
    
    logger.info("="*80)
    logger.info("开始导出Excel多表文件（按schema组织）")
    logger.info("="*80)
    
    return exporter.export_by_schema(output_file, filter_empty_sheets=filter_empty)


def export_excel_main_table(output_dir: Path = Path("data/exports")) -> bool:
    """
    只导出主表到Excel
    
    Args:
        output_dir: 输出目录
        
    Returns:
        是否成功
    """
    exporter = ExcelExporter()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"main_table_{timestamp}.xlsx"
    
    logger.info("="*80)
    logger.info("开始导出Excel主表")
    logger.info("="*80)
    
    return exporter.export_by_schema(output_file, filter_empty_sheets=True)


if __name__ == "__main__":
    # 测试
    logger.remove()
    logger.add(lambda msg: print(msg), level="INFO")
    
    export_excel_all_tables()
