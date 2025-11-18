#!/usr/bin/env python3
"""
数据库初始化脚本 - 根据 inferred_schema.json 创建表结构
"""
import sys
import json
from pathlib import Path
import sqlite3
from loguru import logger

sys.path.insert(0, str(Path(__file__).parent.parent))

from settings import DB_PATH, SCHEMA_DIR

logger.remove()
logger.add(sys.stdout, level="INFO")

def load_schema():
    """加载 schema 定义"""
    schema_file = SCHEMA_DIR / "inferred_schema.json"
    if not schema_file.exists():
        logger.error(f"Schema 文件不存在: {schema_file}")
        return None
    
    with open(schema_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_sqlite_type(json_type):
    """将 JSON 类型转换为 SQLite 类型"""
    type_mapping = {
        "TEXT": "TEXT",
        "INTEGER": "INTEGER",
        "FLOAT": "REAL",
        "BOOLEAN": "INTEGER",  # SQLite没有布尔类型
        "DATE": "TEXT",
        "TIMESTAMP": "TEXT"
    }
    return type_mapping.get(json_type, "TEXT")

def create_table_sql(table_name, table_info):
    """生成创建表的 SQL"""
    columns = []
    
    for col in table_info["columns"]:
        col_name = col["name"]
        col_type = get_sqlite_type(col["type"])
        nullable = "" if col["nullable"] else "NOT NULL"
        
        # 处理主键
        if table_info.get("primary_key") and col_name in table_info["primary_key"]:
            columns.append(f'    "{col_name}" {col_type} PRIMARY KEY')
        else:
            columns.append(f'    "{col_name}" {col_type} {nullable}')
    
    columns_sql = ",\n".join(columns)
    
    sql = f"""
CREATE TABLE IF NOT EXISTS {table_name} (
{columns_sql}
);
"""
    
    return sql

def init_database():
    """初始化数据库"""
    logger.info("=" * 80)
    logger.info("开始初始化数据库")
    logger.info("=" * 80)
    
    # 1. 加载 schema
    logger.info("\n📖 步骤 1: 加载数据库 Schema...")
    schema = load_schema()
    if not schema:
        return False
    
    tables = schema.get("tables", {})
    logger.info(f"   ✓ 发现 {len(tables)} 个表定义")
    
    # 2. 连接数据库
    logger.info(f"\n🔌 步骤 2: 连接数据库...")
    logger.info(f"   数据库文件: {DB_PATH}")
    
    # 确保数据库目录存在
    db_path = Path(DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        logger.info(f"   ✓ 数据库连接成功")
    except Exception as e:
        logger.error(f"   ✗ 数据库连接失败: {str(e)}")
        return False
    
    # 3. 创建表
    logger.info(f"\n🏗️  步骤 3: 创建表结构...")
    
    # 先创建主表，再创建有外键的表
    main_tables = []
    foreign_tables = []
    
    for table_name, table_info in tables.items():
        if table_info.get("is_main", False):
            main_tables.append((table_name, table_info))
        else:
            foreign_tables.append((table_name, table_info))
    
    all_tables = main_tables + foreign_tables
    created_count = 0
    
    for table_name, table_info in all_tables:
        try:
            sql = create_table_sql(table_name, table_info)
            cursor.execute(sql)
            conn.commit()
            
            col_count = len(table_info["columns"])
            is_main = "✨ 主表" if table_info.get("is_main") else ""
            logger.info(f"   ✓ {table_name} ({col_count} 列) {is_main}")
            created_count += 1
        except Exception as e:
            logger.error(f"   ✗ {table_name} 创建失败: {str(e)}")
            conn.rollback()
    
    # 4. 验证表
    logger.info(f"\n🔍 步骤 4: 验证表结构...")
    cursor.execute("""
        SELECT name 
        FROM sqlite_master 
        WHERE type='table'
        ORDER BY name
    """)
    
    existing_tables = [row[0] for row in cursor.fetchall()]
    # 过滤掉SQLite系统表
    existing_tables = [t for t in existing_tables if not t.startswith('sqlite_')]
    logger.info(f"   ✓ 数据库中共有 {len(existing_tables)} 个表")
    
    for table in existing_tables[:10]:  # 显示前10个
        logger.info(f"      - {table}")
    if len(existing_tables) > 10:
        logger.info(f"      ... 还有 {len(existing_tables) - 10} 个表")
    
    # 5. 关闭连接
    cursor.close()
    conn.close()
    
    logger.info("\n" + "=" * 80)
    logger.info(f"✅ 数据库初始化完成！成功创建 {created_count}/{len(tables)} 个表")
    logger.info("=" * 80)
    logger.info(f"\n💡 下一步:")
    logger.info(f"   1. 运行测试: python test_pipeline.py")
    logger.info(f"   2. 查看数据库: sqlite3 {DB_PATH}")
    
    return True

if __name__ == "__main__":
    try:
        success = init_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.warning("\n\n⚠️  用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n❌ 初始化失败: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)
