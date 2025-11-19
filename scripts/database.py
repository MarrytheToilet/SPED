#!/usr/bin/env python3
"""
数据库管理命令行工具
"""
import sys
from pathlib import Path
from loguru import logger

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent))  # scripts/ -> sped/

from src.database.db_manager import DatabaseManager
from src.database.csv_exporter import CSVExporter, export_all_formats


def show_menu():
    """显示主菜单"""
    print("\n" + "="*80)
    print("数据库管理工具")
    print("="*80)
    print("\n1. 📊 查看数据库统计")
    print("2. 📥 从JSON文件导入数据")
    print("3. 📥 批量导入extracted目录的所有JSON")
    print("4. 📤 导出CSV（完整数据-展开JSON）⭐ 推荐")
    print("5. 📤 导出CSV（完整数据-保留JSON）")
    print("6. 📤 导出CSV（数据摘要）")
    print("7. 📤 导出所有格式（展开JSON）⭐")
    print("8. 🔍 查询论文数据")
    print("9. 🗑️  删除论文数据")
    print("10. ⚠️  清空所有数据")
    print("0. 🚪 退出")
    print("="*80)


def view_statistics(db: DatabaseManager):
    """查看统计信息"""
    print("\n" + "="*80)
    print("数据库统计信息")
    print("="*80)
    
    stats = db.get_statistics()
    
    print(f"\n📊 总记录数: {stats.get('total_records', 0)}")
    print(f"📝 有应用部位的记录: {stats.get('with_application', 0)}")
    print(f"📄 不同论文数: {stats.get('unique_papers', 0)}")
    print(f"🕐 最近更新: {stats.get('last_updated', 'N/A')}")
    
    size_mb = stats.get('database_size', 0) / 1024 / 1024
    print(f"💾 数据库大小: {size_mb:.2f} MB")
    
    print("\n" + "="*80)


def import_from_json(db: DatabaseManager):
    """从JSON文件导入"""
    print("\n请输入JSON文件路径（相对或绝对路径）:")
    file_path = input("路径: ").strip()
    
    if not file_path:
        print("❌ 路径不能为空")
        return
    
    json_file = Path(file_path)
    
    if not json_file.exists():
        print(f"❌ 文件不存在: {json_file}")
        return
    
    print(f"\n📥 开始导入: {json_file.name}")
    result = db.insert_from_json(json_file)
    
    print(f"\n✅ 导入完成:")
    print(f"   - 成功: {result['success']} 条")
    print(f"   - 失败: {result['failed']} 条")


def batch_import_extracted(db: DatabaseManager):
    """批量导入extracted目录"""
    extracted_dir = Path("data/processed/extracted")
    
    if not extracted_dir.exists():
        print(f"❌ 目录不存在: {extracted_dir}")
        return
    
    json_files = list(extracted_dir.glob("*.json"))
    
    if not json_files:
        print(f"❌ 目录中没有JSON文件: {extracted_dir}")
        return
    
    print(f"\n📥 找到 {len(json_files)} 个JSON文件")
    print("是否继续导入？(y/n): ", end='')
    
    if input().lower() != 'y':
        print("取消导入")
        return
    
    print("\n开始批量导入...")
    total_success = 0
    total_failed = 0
    
    for i, json_file in enumerate(json_files, 1):
        print(f"\n[{i}/{len(json_files)}] {json_file.name}")
        result = db.insert_from_json(json_file)
        total_success += result['success']
        total_failed += result['failed']
        print(f"  ✅ 成功: {result['success']}, ❌ 失败: {result['failed']}")
    
    print("\n" + "="*80)
    print("批量导入完成")
    print("="*80)
    print(f"总计成功: {total_success} 条")
    print(f"总计失败: {total_failed} 条")
    print("="*80)


def export_csv_expanded(db: DatabaseManager):
    """导出CSV（展开JSON）"""
    exporter = CSVExporter(db)
    
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"full_data_expanded_{timestamp}.csv"
    
    print(f"\n📤 导出到: {output_file}")
    print("⏳ 正在展开JSON字段...")
    
    if exporter.export_all(output_file, flatten_json=False, expand_json=True):
        print(f"✅ 导出成功!")
        print(f"文件: {output_file.absolute()}")
        
        # 显示统计
        import csv
        with open(output_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            records = list(reader)
        print(f"📊 导出了 {len(records)} 条记录, {len(headers)} 个字段")
    else:
        print("❌ 导出失败")


def export_csv_raw(db: DatabaseManager):
    """导出CSV（保留JSON）"""
    exporter = CSVExporter(db)
    
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"full_data_raw_{timestamp}.csv"
    
    print(f"\n📤 导出到: {output_file}")
    
    if exporter.export_all(output_file, flatten_json=False, expand_json=False):
        print(f"✅ 导出成功!")
        print(f"文件: {output_file.absolute()}")
    else:
        print("❌ 导出失败")


def export_csv_summary(db: DatabaseManager):
    """导出CSV摘要"""
    exporter = CSVExporter(db)
    
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"summary_{timestamp}.csv"
    
    print(f"\n📤 导出摘要到: {output_file}")
    
    if exporter.export_summary(output_file):
        print(f"✅ 导出成功!")
        print(f"文件: {output_file.absolute()}")
    else:
        print("❌ 导出失败")


def export_all_csv_formats(db: DatabaseManager):
    """导出所有格式CSV"""
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n📤 导出所有格式到: {output_dir}")
    print("⏳ 开始导出...")
    
    export_all_formats(output_dir, expand_json=True)
    
    print(f"\n✅ 所有格式导出完成!")
    print(f"目录: {output_dir.absolute()}")
    
    output_dir = Path("data/exports")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    from datetime import datetime
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"key_fields_{timestamp}.csv"
    
    print(f"\n📤 导出关键字段到: {output_file}")
    print(f"字段数: {len(key_fields)}")
    
    if exporter.export_custom_fields(output_file, key_fields, filter_empty=True):
        print(f"✅ 导出成功!")
        print(f"文件: {output_file.absolute()}")
    else:
        print("❌ 导出失败")


def query_paper_data(db: DatabaseManager):
    """查询论文数据"""
    print("\n请输入论文ID（paper_id）:")
    paper_id = input("Paper ID: ").strip()
    
    if not paper_id:
        print("❌ Paper ID不能为空")
        return
    
    records = db.query_by_paper_id(paper_id)
    
    if not records:
        print(f"❌ 未找到论文 '{paper_id}' 的数据")
        return
    
    print(f"\n找到 {len(records)} 条记录:\n")
    
    for i, record in enumerate(records, 1):
        non_null = sum(1 for v in record.values() if v and v != '' and v != 'null')
        print(f"{i}. DataID: {record.get('dataid', 'N/A')}")
        print(f"   数据标识: {record.get('数据标识', 'N/A')}")
        print(f"   应用部位: {record.get('应用部位', 'N/A')}")
        print(f"   非空字段: {non_null}/30")
        print()


def delete_paper_data(db: DatabaseManager):
    """删除论文数据"""
    print("\n⚠️  警告: 此操作将删除指定论文的所有数据!")
    print("\n请输入论文ID（paper_id）:")
    paper_id = input("Paper ID: ").strip()
    
    if not paper_id:
        print("❌ Paper ID不能为空")
        return
    
    # 先查询
    records = db.query_by_paper_id(paper_id)
    
    if not records:
        print(f"❌ 未找到论文 '{paper_id}' 的数据")
        return
    
    print(f"\n找到 {len(records)} 条记录")
    print(f"确认删除？(y/n): ", end='')
    
    if input().lower() != 'y':
        print("取消删除")
        return
    
    deleted = db.delete_by_paper_id(paper_id)
    print(f"\n✅ 已删除 {deleted} 条记录")


def clear_all_data(db: DatabaseManager):
    """清空所有数据"""
    print("\n⚠️⚠️⚠️  警告: 此操作将清空所有数据！⚠️⚠️⚠️")
    print("请输入 'DELETE ALL' 确认:")
    
    confirm = input("确认: ").strip()
    
    if confirm != 'DELETE ALL':
        print("取消操作")
        return
    
    print("\n再次确认，是否清空所有数据？(yes/no): ", end='')
    
    if input().lower() != 'yes':
        print("取消操作")
        return
    
    if db.clear_all():
        print("\n✅ 所有数据已清空")
    else:
        print("\n❌ 清空失败")


def main():
    """主函数"""
    # 配置日志
    logger.remove()
    logger.add(sys.stderr, level="WARNING")
    
    # 初始化数据库
    db = DatabaseManager()
    
    while True:
        show_menu()
        choice = input("\n请选择操作 (0-10): ").strip()
        
        if choice == '0':
            print("\n再见！👋")
            break
        elif choice == '1':
            view_statistics(db)
        elif choice == '2':
            import_from_json(db)
        elif choice == '3':
            batch_import_extracted(db)
        elif choice == '4':
            export_csv_expanded(db)
        elif choice == '5':
            export_csv_raw(db)
        elif choice == '6':
            export_csv_summary(db)
        elif choice == '7':
            export_all_csv_formats(db)
        elif choice == '8':
            query_paper_data(db)
        elif choice == '9':
            delete_paper_data(db)
        elif choice == '10':
            clear_all_data(db)
        else:
            print("❌ 无效选择，请重试")
        
        input("\n按回车继续...")


if __name__ == "__main__":
    main()
