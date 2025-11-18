#!/usr/bin/env python3
"""
数据库管理器 - 处理数据写入和查询
"""
import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from loguru import logger


class DatabaseManager:
    """数据库管理类"""
    
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
    
    def _create_tables(self):
        """创建数据表或升级现有表"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # 检查表是否存在
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sheet_1'")
            table_exists = cursor.fetchone()
            
            if table_exists:
                # 表已存在，检查并添加缺失的列
                logger.debug("表已存在，检查schema...")
                self._upgrade_table_schema(cursor)
            else:
                # 创建新表
                logger.info("创建新表 sheet_1...")
                cursor.execute("""
                    CREATE TABLE sheet_1 (
                        数据id TEXT PRIMARY KEY,
                        paper_id TEXT,
                        数据标识 TEXT,
                        应用部位 TEXT,
                        产品所属专利号或文献 TEXT,
                        球头信息_球头基本信息 TEXT,
                        球头信息_球头_成分组成 TEXT,
                        球头信息_球头_物理性能 TEXT,
                        球头信息_球头_微观组织 TEXT,
                        股骨柄信息_股骨柄基本信息 TEXT,
                        股骨柄信息_股骨柄_成分组成 TEXT,
                        股骨柄信息_股骨柄_物理性能 TEXT,
                        股骨柄信息_股骨柄_微观组织 TEXT,
                        内衬信息_内衬_基本信息 TEXT,
                        内衬信息_内衬_改性填料 TEXT,
                        内衬信息_内衬_成分组成 TEXT,
                        内衬信息_内衬_物理性能 TEXT,
                        内衬信息_复合材料性能 TEXT,
                        内衬信息_内衬_材料表征 TEXT,
                        体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置 TEXT,
                        体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验环境_润滑液组成 TEXT,
                        体外实验_内衬与球头摩擦腐蚀实验_球头磨损实验结果 TEXT,
                        体外实验_内衬与球头摩擦腐蚀实验_内衬磨损实验结果 TEXT,
                        体外实验_内衬与球头摩擦腐蚀实验_球头腐蚀实验结果 TEXT,
                        体外实验_内衬与球头摩擦腐蚀实验_内衬腐蚀实验结果 TEXT,
                        体外实验_内衬与球头摩擦腐蚀实验_球头表面成分分析 TEXT,
                        体外实验_球头与锥颈界面微动腐蚀实验_球头与锥颈_实验设置 TEXT,
                        体外实验_球头与锥颈界面微动腐蚀实验_锥颈与球头_实验环境_润滑液组成 TEXT,
                        体外实验_球头与锥颈界面微动腐蚀实验_腐蚀与磨损实验结果 TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        updated_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
            
            # 创建索引
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_paper_id ON sheet_1(paper_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON sheet_1(created_at)")
            
            conn.commit()
            logger.info("数据表准备完成")
    
    def _upgrade_table_schema(self, cursor):
        """升级表schema，添加缺失的列"""
        # 获取现有列
        cursor.execute("PRAGMA table_info(sheet_1)")
        existing_columns = {row[1] for row in cursor.fetchall()}
        
        # 需要的列
        required_columns = ['paper_id', 'created_at', 'updated_at']
        
        # 添加缺失的列
        for col in required_columns:
            if col not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE sheet_1 ADD COLUMN {col} TEXT")
                    logger.info(f"添加列: {col}")
                except Exception as e:
                    logger.debug(f"添加列 {col} 失败（可能已存在）: {e}")
    
    def _normalize_field_name(self, field_name: str) -> str:
        """
        标准化字段名（将点号替换为下划线）
        
        Args:
            field_name: 原始字段名
            
        Returns:
            标准化后的字段名
        """
        # dataid 和 数据id 是同义词
        if field_name == 'dataid':
            return '数据id'
        return field_name.replace('.', '_').replace('-', '_')
    
    def insert_record(self, record: Dict[str, Any]) -> bool:
        """
        插入单条记录
        
        Args:
            record: 记录字典
            
        Returns:
            是否成功
        """
        try:
            # 标准化字段名
            normalized_record = {}
            for key, value in record.items():
                normalized_key = self._normalize_field_name(key)
                normalized_record[normalized_key] = value
            
            # 确保有数据id
            if '数据id' not in normalized_record:
                logger.error("记录缺少dataid/数据id字段")
                return False
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 检查记录是否已存在
                cursor.execute("SELECT 数据id FROM sheet_1 WHERE 数据id = ?", 
                             (normalized_record['数据id'],))
                exists = cursor.fetchone()
                
                if exists:
                    # 更新现有记录
                    update_fields = []
                    update_values = []
                    for key, value in normalized_record.items():
                        if key != '数据id':
                            # 使用反引号包裹列名以处理中文
                            update_fields.append(f"`{key}` = ?")
                            update_values.append(value)
                    
                    update_values.append(normalized_record['数据id'])
                    sql = f"UPDATE sheet_1 SET {', '.join(update_fields)}, updated_at = CURRENT_TIMESTAMP WHERE 数据id = ?"
                    cursor.execute(sql, update_values)
                    logger.debug(f"更新记录: {normalized_record['数据id']}")
                else:
                    # 插入新记录
                    fields = [f"`{f}`" for f in normalized_record.keys()]
                    placeholders = ', '.join(['?'] * len(fields))
                    sql = f"INSERT INTO sheet_1 ({', '.join(fields)}) VALUES ({placeholders})"
                    cursor.execute(sql, list(normalized_record.values()))
                    logger.debug(f"插入记录: {normalized_record['数据id']}")
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"插入记录失败: {e}")
            logger.debug(f"记录内容: {record}")
            return False
    
    def insert_records(self, records: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        批量插入记录
        
        Args:
            records: 记录列表
            
        Returns:
            统计信息 {'success': 成功数, 'failed': 失败数}
        """
        stats = {'success': 0, 'failed': 0}
        
        for record in records:
            if self.insert_record(record):
                stats['success'] += 1
            else:
                stats['failed'] += 1
        
        logger.info(f"批量插入完成: 成功 {stats['success']}, 失败 {stats['failed']}")
        return stats
    
    def insert_from_json(self, json_file: Path) -> Dict[str, int]:
        """
        从JSON文件导入数据
        
        Args:
            json_file: JSON文件路径
            
        Returns:
            统计信息
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 处理不同的JSON格式
            if isinstance(data, dict):
                if 'records' in data:
                    # 格式: {"dataid": "...", "records": [...]}
                    records = data['records']
                    # 确保每条记录都有dataid和paper_id
                    for record in records:
                        if 'dataid' not in record:
                            record['dataid'] = data.get('dataid')
                        if 'paper_id' not in record:
                            record['paper_id'] = data.get('paper_id')
                else:
                    # 单条记录
                    records = [data]
            elif isinstance(data, list):
                records = data
            else:
                logger.error(f"不支持的JSON格式: {type(data)}")
                return {'success': 0, 'failed': 1}
            
            return self.insert_records(records)
            
        except Exception as e:
            logger.error(f"从JSON文件导入失败: {e}")
            return {'success': 0, 'failed': 1}
    
    def query_all(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        查询所有记录
        
        Args:
            limit: 限制返回数量
            
        Returns:
            记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                sql = "SELECT * FROM sheet_1 ORDER BY created_at DESC"
                if limit:
                    sql += f" LIMIT {limit}"
                
                cursor.execute(sql)
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return []
    
    def query_by_paper_id(self, paper_id: str) -> List[Dict[str, Any]]:
        """
        根据paper_id查询记录
        
        Args:
            paper_id: 论文ID
            
        Returns:
            记录列表
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute("SELECT * FROM sheet_1 WHERE paper_id = ?", (paper_id,))
                rows = cursor.fetchall()
                
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"查询失败: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        获取数据库统计信息
        
        Returns:
            统计信息字典
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 总记录数
                cursor.execute("SELECT COUNT(*) FROM sheet_1")
                total_count = cursor.fetchone()[0]
                
                # 有应用部位的记录数
                cursor.execute("SELECT COUNT(*) FROM sheet_1 WHERE 应用部位 IS NOT NULL AND 应用部位 != ''")
                with_application = cursor.fetchone()[0]
                
                # 不同论文数
                cursor.execute("SELECT COUNT(DISTINCT paper_id) FROM sheet_1")
                unique_papers = cursor.fetchone()[0]
                
                # 最近更新时间
                cursor.execute("SELECT MAX(updated_at) FROM sheet_1")
                last_updated = cursor.fetchone()[0]
                
                return {
                    'total_records': total_count,
                    'with_application': with_application,
                    'unique_papers': unique_papers,
                    'last_updated': last_updated,
                    'database_size': self.db_path.stat().st_size if self.db_path.exists() else 0
                }
                
        except Exception as e:
            logger.error(f"获取统计信息失败: {e}")
            return {}
    
    def delete_by_paper_id(self, paper_id: str) -> int:
        """
        删除指定论文的所有记录
        
        Args:
            paper_id: 论文ID
            
        Returns:
            删除的记录数
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sheet_1 WHERE paper_id = ?", (paper_id,))
                deleted = cursor.rowcount
                conn.commit()
                logger.info(f"删除了 {deleted} 条记录 (paper_id: {paper_id})")
                return deleted
                
        except Exception as e:
            logger.error(f"删除失败: {e}")
            return 0
    
    def clear_all(self) -> bool:
        """
        清空所有数据（保留表结构）
        
        Returns:
            是否成功
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM sheet_1")
                conn.commit()
                logger.warning("已清空所有数据")
                return True
                
        except Exception as e:
            logger.error(f"清空数据失败: {e}")
            return False


if __name__ == "__main__":
    # 测试
    logger.remove()
    logger.add(lambda msg: print(msg), level="INFO")
    
    db = DatabaseManager()
    
    # 测试插入
    test_record = {
        "dataid": "TEST_001",
        "paper_id": "test_paper",
        "数据标识": "测试数据",
        "应用部位": "髋关节",
        "球头信息.球头基本信息": '{"材料": "CoCrMo", "直径": "28 mm"}'
    }
    
    print("\n测试插入...")
    db.insert_record(test_record)
    
    print("\n查询统计...")
    stats = db.get_statistics()
    print(f"总记录数: {stats['total_records']}")
    print(f"不同论文数: {stats['unique_papers']}")
    
    print("\n删除测试数据...")
    db.delete_by_paper_id("test_paper")
