#!/usr/bin/env python3
"""
数据库管理器 - 处理多表数据写入和查询
Schema版本: 3.0
"""
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger


class DatabaseManager:
    """数据库管理类 - 支持12表结构"""
    
    # 表名映射
    TABLE_MAPPING = {
        "Sheet1_基本信息表": "basic_info",
        "Sheet2_内衬基本信息表": "liner_basic",
        "Sheet3_球头基本信息表": "head_basic",
        "Sheet4_配合信息表": "fitting_info",
        "Sheet5_股骨柄基本信息表": "stem_basic",
        "Sheet6_内衬物理性能表": "liner_properties",
        "Sheet7_球头物理性能表": "head_properties",
        "Sheet8_股骨柄物理性能表": "stem_properties",
        "Sheet9_实验参数": "experiment_params",
        "Sheet10_性能测试结果表": "test_results",
        "Sheet11_计算模拟参数表": "simulation_params",
        "Sheet12_计算模拟图像表": "simulation_images"
    }
    
    def __init__(self, db_path: str = "data/artificial_joint.db"):
        """
        初始化数据库管理器
        
        Args:
            db_path: 数据库文件路径
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_database()
    
    def _ensure_database(self):
        """确保数据库和表存在"""
        if not self.db_path.exists():
            logger.info(f"数据库不存在，创建新数据库: {self.db_path}")
            self._create_tables()
        else:
            logger.debug(f"使用现有数据库: {self.db_path}")
            # 检查表是否完整
            self._check_and_create_missing_tables()
    
    def _create_tables(self):
        """创建所有数据表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            logger.info("创建12个数据表...")
            
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS basic_info (
                    '数据ID' TEXT PRIMARY KEY NOT NULL,\n                    '应用部位' TEXT,\n                    '产品所属专利号或文献' TEXT,\n                    '来源文件' TEXT,\n                    '论文标题' TEXT,\n                    '论文DOI号' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS liner_basic (
                    '数据ID' TEXT NOT NULL,\n                    '内衬材料类别' TEXT,\n                    '内衬材料名称' TEXT,\n                    '成型方式' TEXT,\n                    '熔融温度' TEXT,\n                    '成型压力' TEXT,\n                    '保温时间' TEXT,\n                    '碳纤维质量分数' TEXT,\n                    '碳纤维长度' TEXT,\n                    '碳纤维外径' TEXT,\n                    '碳纳米管质量分数' TEXT,\n                    '碳纳米管长度' TEXT,\n                    '碳纳米管外径' TEXT,\n                    '石墨烯质量分数' TEXT,\n                    '石墨烯厚度' TEXT,\n                    '石墨烯长度' TEXT,\n                    '碳化硅质量分数' TEXT,\n                    '内衬厚度(mm)' TEXT,\n                    '内衬偏移(mm)' TEXT,\n                    '内衬锁定机制' TEXT,\n                    '内衬加工工艺' TEXT,\n                    '内衬后处理' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS head_basic (
                    '数据ID' TEXT NOT NULL,\n                    '球头材料类别' TEXT,\n                    '球头材料名称' TEXT,\n                    '球头合金成分' TEXT,\n                    '球头直径(mm)' TEXT,\n                    '球头纹理' TEXT,\n                    '球头加工工艺' TEXT,\n                    '球头后处理' TEXT,\n                    '球头晶粒尺寸' TEXT,\n                    '球头晶粒取向' TEXT,\n                    '球头相组成' TEXT,\n                    '碳化物尺寸' TEXT,\n                    '碳化物分布位置' TEXT,\n                    '碳化物连续性' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS fitting_info (
                    '数据ID' TEXT NOT NULL,\n                    '内衬-球头径向间隙(mm)' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stem_basic (
                    '数据ID' TEXT NOT NULL,\n                    '股骨柄材料类别' TEXT,\n                    '股骨柄材料名称' TEXT,\n                    '锥度(°)' TEXT,\n                    '锥颈尺寸' TEXT,\n                    '颈长(mm)' TEXT,\n                    '锥套设计' TEXT,\n                    '锥度间隙(°)' TEXT,\n                    '股骨柄颈干角(°)' TEXT,\n                    '股骨柄偏心距(mm)' TEXT,\n                    '股骨柄拓扑结构' TEXT,\n                    '股骨柄孔隙率(%)' TEXT,\n                    '股骨柄横截面' TEXT,\n                    '柄体长度H(mm)' TEXT,\n                    '股骨柄加工工艺' TEXT,\n                    '股骨柄后处理' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS liner_properties (
                    '数据ID' TEXT NOT NULL,\n                    '内衬硬度(HV)' TEXT,\n                    '内衬表面粗糙度(μm)' TEXT,\n                    '内衬弹性模量(GPa)' TEXT,\n                    '内衬杨氏模量' TEXT,\n                    '内衬极限拉伸强度' TEXT,\n                    '内衬弯曲强度' TEXT,\n                    '内衬剪切强度' TEXT,\n                    '内衬断裂韧性' TEXT,\n                    '内衬抗压强度(MPa)' TEXT,\n                    '内衬屈服强度(MPa)' TEXT,\n                    '内衬密度(g/cm³)' TEXT,\n                    '内衬泊松比' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS head_properties (
                    '数据ID' TEXT NOT NULL,\n                    '球头硬度(HV)' TEXT,\n                    '球头表面粗糙度(nm)' TEXT,\n                    '弹性模量(GPa)' TEXT,\n                    '球头抗压强度(MPa)' TEXT,\n                    '球头屈服强度(MPa)' TEXT,\n                    '球头断裂伸长率' TEXT,\n                    '球头密度(g/cm³)' TEXT,\n                    '球头泊松比' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS stem_properties (
                    '数据ID' TEXT NOT NULL,\n                    '股骨柄硬度(HV)' TEXT,\n                    '股骨柄表面粗糙度(μm)' TEXT,\n                    '股骨柄弹性模量(GPa)' TEXT,\n                    '股骨柄抗压强度(MPa)' TEXT,\n                    '股骨柄屈服强度(MPa)' TEXT,\n                    '股骨柄密度(g/cm³)' TEXT,\n                    '股骨柄泊松比' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS experiment_params (
                    '数据ID' TEXT NOT NULL,\n                    '实验器材' TEXT,\n                    '滑动距离' TEXT,\n                    '频率' TEXT,\n                    '摩擦时间' TEXT,\n                    '载荷' TEXT,\n                    '实验温度' TEXT,\n                    '润滑液类型' TEXT,\n                    '蛋白质浓度' TEXT,\n                    '润滑液pH' TEXT,\n                    '接触载荷' TEXT,\n                    '运动模式' TEXT,\n                    '速率' TEXT,\n                    '接触方式' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS test_results (
                    '数据ID' TEXT NOT NULL,\n                    '内衬相含量变化' TEXT,\n                    '累计磨损量' TEXT,\n                    '磨损率' TEXT,\n                    '摩擦系数' TEXT,\n                    '腐蚀速率' TEXT,\n                    '离子释放量' TEXT,\n                    '磨损颗粒大小' TEXT,\n                    '磨损颗粒形貌' TEXT,\n                    '摩擦膜组成' TEXT,\n                    '摩擦膜厚度' TEXT,\n                    '抗疲劳性' TEXT,\n                    '接触应力' TEXT,\n                    'Von Mises应力' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_params (
                    '数据ID' TEXT NOT NULL,\n                    '计算建模软件' TEXT,\n                    '计算建模输入参数' TEXT,\n                    '计算建模输出参数' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS simulation_images (
                    '数据ID' TEXT NOT NULL,\n                    '计算建模模拟结构图' TEXT,\n                    '计算建模模拟结构图说明' TEXT,\n                    '来源文件' TEXT,\n                    '论文ID' TEXT,\n                    'created_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP,\n                    'updated_at' TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_basic_info_dataid ON basic_info(数据ID)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_basic_info_paperid ON basic_info(论文ID)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_basic_info_application ON basic_info(应用部位)")
            
            conn.commit()
            logger.info("✅ 所有数据表创建完成")
    
    def _check_and_create_missing_tables(self):
        """检查并创建缺失的表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            for sheet_name, table_name in self.TABLE_MAPPING.items():
                cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
                if not cursor.fetchone():
                    logger.warning(f"表 {table_name} 不存在，重新创建...")
                    self._create_tables()
                    break
    
    def insert_record(self, record: Dict[str, Any]) -> bool:
        """
        插入单条记录（多表）
        
        Args:
            record: 包含所有表数据的记录字典
            
        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                data_id = None
                success_count = 0
                
                # 首先从任意非空表中获取数据ID
                for sheet_name, table_name in self.TABLE_MAPPING.items():
                    table_data = record.get(sheet_name)
                    if table_data and isinstance(table_data, dict) and table_data.get('数据ID'):
                        data_id = table_data.get('数据ID')
                        break
                
                if not data_id:
                    logger.error(f"记录缺少数据ID字段")
                    return False
                
                # 遍历所有表
                for sheet_name, table_name in self.TABLE_MAPPING.items():
                    table_data = record.get(sheet_name)
                    
                    # 如果表数据为None或空，插入一条只有数据ID的记录
                    if table_data is None or (isinstance(table_data, dict) and not table_data):
                        # 插入空记录（只有数据ID）
                        sql = f"""
                            INSERT OR REPLACE INTO {table_name} 
                            ('数据ID', 'updated_at')
                            VALUES (?, CURRENT_TIMESTAMP)
                        """
                        cursor.execute(sql, [data_id])
                        success_count += 1
                        continue
                    
                    # 准备插入数据
                    columns = []
                    values = []
                    placeholders = []
                    
                    for key, value in table_data.items():
                        if key in ['created_at', 'updated_at']:
                            continue
                        
                        columns.append(f"'{key}'")
                        
                        # 处理值
                        if value is None:
                            values.append(None)
                        elif isinstance(value, (dict, list)):
                            values.append(json.dumps(value, ensure_ascii=False))
                        else:
                            values.append(str(value))
                        
                        placeholders.append('?')
                    
                    # 构建INSERT OR REPLACE语句
                    sql = f"""
                        INSERT OR REPLACE INTO {table_name} 
                        ({', '.join(columns)}, 'updated_at')
                        VALUES ({', '.join(placeholders)}, CURRENT_TIMESTAMP)
                    """
                    
                    cursor.execute(sql, values)
                    success_count += 1
                
                conn.commit()
                logger.debug(f"✅ 成功插入记录 {data_id}，更新了 {success_count} 个表（包含空表）")
                return True
                
        except Exception as e:
            logger.error(f"插入记录失败: {e}")
            return False
    
    def batch_insert(self, records: List[Dict[str, Any]]) -> int:
        """
        批量插入记录
        
        Args:
            records: 记录列表
            
        Returns:
            成功插入的数量
        """
        success_count = 0
        for record in records:
            if self.insert_record(record):
                success_count += 1
        return success_count
    
    def get_all_records(self, table_name: str = "basic_info") -> List[Dict]:
        """
        获取所有记录
        
        Args:
            table_name: 表名（默认主表）
            
        Returns:
            记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute(f"SELECT * FROM {table_name}")
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"查询记录失败: {e}")
            return []
    
    def get_record_by_id(self, data_id: str) -> Dict[str, Any]:
        """
        根据数据ID获取完整记录（所有表）
        
        Args:
            data_id: 数据ID
            
        Returns:
            包含所有表数据的记录字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                record = {}
                
                for sheet_name, table_name in self.TABLE_MAPPING.items():
                    cursor.execute(f"SELECT * FROM {table_name} WHERE 数据ID = ?", (data_id,))
                    row = cursor.fetchone()
                    
                    if row:
                        record[sheet_name] = dict(row)
                    else:
                        record[sheet_name] = None
                
                return record
        except Exception as e:
            logger.error(f"查询记录失败: {e}")
            return {}
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # 统计各表记录数
                for sheet_name, table_name in self.TABLE_MAPPING.items():
                    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                    count = cursor.fetchone()[0]
                    stats[sheet_name] = count
                
                # 应用部位分布
                cursor.execute("""
                    SELECT 应用部位, COUNT(*) as count 
                    FROM basic_info 
                    WHERE 应用部位 IS NOT NULL 
                    GROUP BY 应用部位
                """)
                stats['应用部位分布'] = dict(cursor.fetchall())
                
                return stats
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息（详细版本，用于scripts）
        
        Returns:
            统计信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总记录数
                cursor.execute("SELECT COUNT(*) FROM basic_info")
                total_records = cursor.fetchone()[0]
                
                # 有应用部位的记录
                cursor.execute("SELECT COUNT(*) FROM basic_info WHERE 应用部位 IS NOT NULL AND 应用部位 != ''")
                with_application = cursor.fetchone()[0]
                
                # 不同论文数
                cursor.execute("SELECT COUNT(DISTINCT 论文ID) FROM basic_info WHERE 论文ID IS NOT NULL")
                unique_papers = cursor.fetchone()[0]
                
                # 最近更新时间
                cursor.execute("SELECT MAX(updated_at) FROM basic_info")
                last_updated = cursor.fetchone()[0]
                
                # 数据库大小
                database_size = self.db_path.stat().st_size if self.db_path.exists() else 0
                
                return {
                    'total_records': total_records,
                    'with_application': with_application,
                    'unique_papers': unique_papers,
                    'last_updated': last_updated,
                    'database_size': database_size
                }
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {
                'total_records': 0,
                'with_application': 0,
                'unique_papers': 0,
                'last_updated': 'N/A',
                'database_size': 0
            }
    
    def delete_record(self, data_id: str) -> bool:
        """
        删除记录（所有表）
        
        Args:
            data_id: 数据ID
            
        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for table_name in self.TABLE_MAPPING.values():
                    cursor.execute(f"DELETE FROM {table_name} WHERE 数据ID = ?", (data_id,))
                
                conn.commit()
                logger.info(f"✅ 已删除记录: {data_id}")
                return True
        except Exception as e:
            logger.error(f"删除记录失败: {e}")
            return False
    
    def insert_from_json(self, json_file: Path) -> Dict[str, int]:
        """
        从JSON文件导入数据
        
        支持两种格式:
        1. 新格式: {"records": [{...}, {...}], "paper_id": "xxx"}
        2. 旧格式: {"data": {...}, "paper_id": "xxx"}
        
        Args:
            json_file: JSON文件路径
            
        Returns:
            {"success": int, "failed": int}
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 从文件名提取论文ID（去掉.json后缀）
            paper_id = json_file.stem
            
            success_count = 0
            failed_count = 0
            
            # 判断格式
            if 'records' in data:
                # 新格式: {"records": [...]}
                records = data['records']
                for record in records:
                    # 处理每条记录
                    processed_record = self._process_record(record, paper_id, json_file.name)
                    if self.insert_record(processed_record):
                        success_count += 1
                    else:
                        failed_count += 1
            
            elif 'data' in data:
                # 旧格式: {"data": {...}}
                record_data = data['data']
                processed_record = self._process_record(record_data, paper_id, json_file.name)
                if self.insert_record(processed_record):
                    success_count += 1
                else:
                    failed_count += 1
            
            else:
                logger.error(f"未知的JSON格式: {json_file.name}")
                failed_count = 1
            
            return {"success": success_count, "failed": failed_count}
            
        except Exception as e:
            logger.error(f"从JSON导入失败: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"success": 0, "failed": 1}
    
    def _process_record(self, record: Dict, paper_id: str, file_name: str) -> Dict:
        """
        处理单条记录，添加来源文件和论文ID
        
        Args:
            record: 原始记录
            paper_id: 论文ID
            file_name: 文件名
            
        Returns:
            处理后的记录
        """
        # 如果是旧格式的嵌套结构（有action、data等）
        if 'data' in record and isinstance(record['data'], dict):
            record = record['data']
        
        # 确保record是字典格式
        if not isinstance(record, dict):
            logger.error(f"记录格式错误: {type(record)}")
            return record
        
        # 获取或生成数据ID
        data_id = record.get('dataid') or record.get('数据ID')
        
        # 尝试从任意表中获取数据ID
        if not data_id:
            for key, value in record.items():
                if isinstance(value, dict) and '数据ID' in value:
                    data_id = value['数据ID']
                    break
        
        # 如果仍然没有数据ID，生成一个
        if not data_id:
            import hashlib
            import time
            timestamp = str(time.time())
            random_str = hashlib.md5(timestamp.encode()).hexdigest()[:8]
            data_id = f"AJ_{datetime.now().strftime('%Y%m%d')}_{random_str}"
            logger.warning(f"记录缺少数据ID，自动生成: {data_id}")
        
        # 旧表名到新表名的映射
        old_to_new_mapping = {
            '基本信息表': 'Sheet1_基本信息表',
            '内衬基本信息表': 'Sheet2_内衬基本信息表',
            '球头基本信息表': 'Sheet3_球头基本信息表',
            '配合信息表': 'Sheet4_配合信息表',
            '股骨柄基本信息表': 'Sheet5_股骨柄基本信息表',
            '内衬物理性能表': 'Sheet6_内衬物理性能表',
            '球头物理性能表': 'Sheet7_球头物理性能表',
            '股骨柄物理性能表': 'Sheet8_股骨柄物理性能表',
            '实验参数': 'Sheet9_实验参数',
            '性能测试结果表': 'Sheet10_性能测试结果表',
            '计算模拟参数表': 'Sheet11_计算模拟参数表',
            '计算模拟图像表': 'Sheet12_计算模拟图像表'
        }
        
        # 转换旧格式到新格式
        new_record = {}
        for old_name, new_name in old_to_new_mapping.items():
            if old_name in record:
                new_record[new_name] = record[old_name]
            elif new_name in record:
                new_record[new_name] = record[new_name]
        
        # 如果没有转换成功，保留原始record
        if not new_record:
            new_record = record
        
        # 为每个表添加来源文件和论文ID
        for sheet_name in self.TABLE_MAPPING.keys():
            if sheet_name in new_record and new_record[sheet_name]:
                if isinstance(new_record[sheet_name], dict):
                    # 添加数据ID（如果缺失）
                    if '数据ID' not in new_record[sheet_name]:
                        new_record[sheet_name]['数据ID'] = data_id
                    # 添加来源文件和论文ID
                    new_record[sheet_name]['来源文件'] = file_name
                    new_record[sheet_name]['论文ID'] = paper_id
        
        return new_record
