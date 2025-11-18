#!/usr/bin/env python3
"""
CSV导出器 - 将数据库数据导出为CSV文件
"""
import csv
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger

from .db_manager import DatabaseManager


class CSVExporter:
    """CSV导出类"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """
        初始化CSV导出器
        
        Args:
            db_manager: 数据库管理器实例
        """
        self.db = db_manager or DatabaseManager()
    
    def _flatten_json_field(self, value: Any) -> str:
        """
        展平JSON字段（将JSON字符串转换为可读格式）
        
        Args:
            value: 字段值
            
        Returns:
            展平后的字符串
        """
        if value is None or value == '':
            return ''
        
        # 如果是JSON字符串，尝试解析并格式化
        if isinstance(value, str) and value.startswith('{'):
            try:
                data = json.loads(value)
                # 将字典转换为 key:value 格式
                items = [f"{k}: {v}" for k, v in data.items()]
                return '; '.join(items)
            except:
                return value
        
        return str(value)
    
    def _expand_json_fields(self, records: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        将JSON字段完全展开为独立字段
        
        例如:
        "实验设置": '{"载荷": "70.7 N", "频率": "1 Hz"}'
        展开为:
        "实验设置.载荷": "70.7 N"
        "实验设置.频率": "1 Hz"
        
        Args:
            records: 原始记录列表
            
        Returns:
            展开后的记录列表和所有字段名
        """
        expanded_records = []
        all_fields = set()
        
        # 第一遍：收集所有可能的字段名
        for record in records:
            expanded = {}
            for key, value in record.items():
                if not value or value == '' or value == 'null':
                    expanded[key] = value
                    all_fields.add(key)
                    continue
                
                # 尝试解析JSON
                if isinstance(value, str) and value.startswith('{'):
                    try:
                        json_data = json.loads(value)
                        if isinstance(json_data, dict):
                            # 展开JSON字段
                            for sub_key, sub_value in json_data.items():
                                expanded_key = f"{key}.{sub_key}"
                                expanded[expanded_key] = sub_value if sub_value else ''
                                all_fields.add(expanded_key)
                        else:
                            expanded[key] = value
                            all_fields.add(key)
                    except json.JSONDecodeError:
                        expanded[key] = value
                        all_fields.add(key)
                else:
                    expanded[key] = value
                    all_fields.add(key)
            
            expanded_records.append(expanded)
        
        # 第二遍：确保所有记录有相同的字段（填充缺失字段）
        for record in expanded_records:
            for field in all_fields:
                if field not in record:
                    record[field] = ''
        
        return expanded_records, sorted(all_fields)
    
    def export_all(self, output_file: Path, flatten_json: bool = True, expand_json: bool = False) -> bool:
        """
        导出所有数据到CSV
        
        Args:
            output_file: 输出文件路径
            flatten_json: 是否展平JSON字段为可读字符串 (key: value; key: value...)
            expand_json: 是否完全展开JSON字段为独立列 (优先级高于flatten_json)
            
        Returns:
            是否成功
        """
        try:
            # 查询所有数据
            records = self.db.query_all()
            
            if not records:
                logger.warning("没有数据可导出")
                return False
            
            # 创建输出目录
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 根据选项处理记录
            if expand_json:
                # 完全展开JSON为独立字段
                logger.info("完全展开JSON字段为独立列...")
                processed_records, fieldnames = self._expand_json_fields(records)
            else:
                # 使用原始字段名
                fieldnames = list(records[0].keys())
                processed_records = records
            
            # 写入CSV
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in processed_records:
                    if flatten_json and not expand_json:
                        # 展平JSON字段为可读字符串
                        flat_record = {}
                        for key, value in record.items():
                            flat_record[key] = self._flatten_json_field(value)
                        writer.writerow(flat_record)
                    else:
                        writer.writerow(record)
            
            logger.info(f"导出成功: {len(processed_records)} 条记录, {len(fieldnames)} 个字段 -> {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def export_by_paper(self, paper_id: str, output_file: Path, flatten_json: bool = True) -> bool:
        """
        导出指定论文的数据到CSV
        
        Args:
            paper_id: 论文ID
            output_file: 输出文件路径
            flatten_json: 是否展平JSON字段
            
        Returns:
            是否成功
        """
        try:
            # 查询指定论文的数据
            records = self.db.query_by_paper_id(paper_id)
            
            if not records:
                logger.warning(f"论文 {paper_id} 没有数据")
                return False
            
            # 创建输出目录
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 获取所有字段名
            fieldnames = list(records[0].keys())
            
            # 写入CSV
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for record in records:
                    if flatten_json:
                        flat_record = {}
                        for key, value in record.items():
                            flat_record[key] = self._flatten_json_field(value)
                        writer.writerow(flat_record)
                    else:
                        writer.writerow(record)
            
            logger.info(f"导出成功: {len(records)} 条记录 -> {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return False
    
    def export_custom_fields(self, 
                            output_file: Path, 
                            fields: List[str],
                            filter_empty: bool = True,
                            flatten_json: bool = True) -> bool:
        """
        导出自定义字段到CSV
        
        Args:
            output_file: 输出文件路径
            fields: 要导出的字段列表
            filter_empty: 是否过滤空记录
            flatten_json: 是否展平JSON字段
            
        Returns:
            是否成功
        """
        try:
            # 查询所有数据
            all_records = self.db.query_all()
            
            if not all_records:
                logger.warning("没有数据可导出")
                return False
            
            # 过滤记录和字段
            filtered_records = []
            for record in all_records:
                # 提取指定字段
                filtered_record = {}
                has_data = False
                
                for field in fields:
                    value = record.get(field)
                    if flatten_json:
                        value = self._flatten_json_field(value)
                    filtered_record[field] = value
                    
                    # 检查是否有非空数据
                    if value and value != '' and value != 'null':
                        has_data = True
                
                # 如果开启过滤且没有数据，跳过
                if filter_empty and not has_data:
                    continue
                
                filtered_records.append(filtered_record)
            
            if not filtered_records:
                logger.warning("过滤后没有数据")
                return False
            
            # 创建输出目录
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入CSV
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                writer.writerows(filtered_records)
            
            logger.info(f"导出成功: {len(filtered_records)} 条记录 -> {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出CSV失败: {e}")
            return False
    
    def export_summary(self, output_file: Path) -> bool:
        """
        导出数据摘要到CSV
        
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
            
            # 生成摘要
            summary_records = []
            for record in records:
                # 统计非空字段数
                non_null_count = sum(1 for v in record.values() 
                                    if v and v != '' and v != 'null' 
                                    and v != 'None')
                
                summary = {
                    'dataid': record.get('dataid', ''),
                    'paper_id': record.get('paper_id', ''),
                    '数据标识': record.get('数据标识', ''),
                    '应用部位': record.get('应用部位', ''),
                    '非空字段数': non_null_count,
                    '创建时间': record.get('created_at', ''),
                    '更新时间': record.get('updated_at', '')
                }
                summary_records.append(summary)
            
            # 创建输出目录
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 写入CSV
            fieldnames = ['dataid', 'paper_id', '数据标识', '应用部位', '非空字段数', '创建时间', '更新时间']
            with open(output_file, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(summary_records)
            
            logger.info(f"导出摘要成功: {len(summary_records)} 条记录 -> {output_file}")
            return True
            
        except Exception as e:
            logger.error(f"导出摘要失败: {e}")
            return False


def export_all_formats(output_dir: Path = Path("data/exports"), expand_json: bool = True):
    """
    导出所有格式的数据
    
    Args:
        output_dir: 输出目录
        expand_json: 是否完全展开JSON字段为独立列
    """
    exporter = CSVExporter()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    logger.info("="*80)
    logger.info("开始导出数据")
    logger.info("="*80)
    
    # 1. 导出完整数据（完全展开JSON字段）
    logger.info("\n1. 导出完整数据（完全展开JSON字段为独立列）...")
    output_file = output_dir / f"full_data_expanded_{timestamp}.csv"
    exporter.export_all(output_file, flatten_json=False, expand_json=expand_json)
    
    # 2. 导出完整数据（保留JSON）
    logger.info("\n2. 导出完整数据（保留原始JSON）...")
    output_file = output_dir / f"full_data_raw_{timestamp}.csv"
    exporter.export_all(output_file, flatten_json=False, expand_json=False)
    
    # 3. 导出摘要
    logger.info("\n3. 导出数据摘要...")
    output_file = output_dir / f"summary_{timestamp}.csv"
    exporter.export_summary(output_file)
    
    logger.info("\n" + "="*80)
    logger.info(f"所有导出完成！文件保存在: {output_dir}")
    logger.info("="*80)


if __name__ == "__main__":
    # 测试
    logger.remove()
    logger.add(lambda msg: print(msg), level="INFO")
    
    export_all_formats()
