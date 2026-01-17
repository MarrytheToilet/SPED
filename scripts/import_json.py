#!/usr/bin/env python3
"""
数据导入脚本：导入JSON到数据库
"""
import json
import sqlite3
import sys
from pathlib import Path
from datetime import datetime

# 中文表名到英文表名的映射
TABLE_MAPPING = {
    "基本信息表": "basic_info",
    "内衬基本信息表": "liner_basic",
    "球头基本信息表": "head_basic",
    "配合信息表": "fitting_info",
    "股骨柄基本信息表": "stem_basic",
    "内衬物理性能表": "liner_properties",
    "球头物理性能表": "head_properties",
    "股骨柄物理性能表": "stem_properties",
    "性能测试结果表": "test_results",
    "计算模拟参数表": "simulation_params",
    "计算模拟图像表": "simulation_images"
}

# 中文字段名到英文字段名的映射
FIELD_MAPPING = {
    # 基本信息表
    "数据ID": "data_id",
    "应用部位": "application_site",
    "产品所属专利号或文献": "patent_or_literature",
    
    # 内衬基本信息表
    "内衬材料类别": "material_category",
    "内衬材料名称": "material_name",
    "内衬厚度(mm)": "thickness_mm",
    "内衬偏移(mm)": "offset_mm",
    "内衬锁定机制": "locking_mechanism",
    "内衬加工工艺": "processing_technology",
    "内衬后处理": "post_treatment",
    
    # 球头基本信息表
    "球头材料类别": "material_category",
    "球头材料名称": "material_name",
    "球头直径(mm)": "diameter_mm",
    "球头纹理": "texture",
    "球头加工工艺": "processing_technology",
    "球头后处理": "post_treatment",
    
    # 配合信息表
    "内衬-球头径向间隙(mm)": "radial_clearance_mm",
    
    # 股骨柄基本信息表
    "股骨柄材料类别": "material_category",
    "股骨柄材料名称": "material_name",
    "锥度(°)": "taper_degree",
    "锥颈尺寸": "taper_size",
    "颈长(mm)": "neck_length_mm",
    "锥套设计": "sleeve_design",
    "锥度间隙(°)": "taper_clearance_degree",
    "股骨柄颈干角(°)": "neck_shaft_angle_degree",
    "股骨柄偏心距(mm)": "offset_mm",
    "股骨柄拓扑结构": "topology_structure",
    "股骨柄孔隙率(%)": "porosity_percent",
    "股骨柄横截面": "cross_section",
    "柄体长度H(mm)": "body_length_mm",
    "股骨柄加工工艺": "processing_technology",
    "股骨柄后处理": "post_treatment",
    
    # 物理性能表（通用）
    "内衬硬度(HV)": "hardness_hv",
    "内衬表面粗糙度(μm)": "surface_roughness_um",
    "内衬弹性模量(GPa)": "elastic_modulus_gpa",
    "内衬抗压强度(MPa)": "compressive_strength_mpa",
    "内衬屈服强度(MPa)": "yield_strength_mpa",
    "内衬密度(g/cm³)": "density_g_cm3",
    "内衬泊松比": "poisson_ratio",
    
    "球头硬度(HV)": "hardness_hv",
    "球头表面粗糙度(nm)": "surface_roughness_nm",
    "弹性模量(GPa)": "elastic_modulus_gpa",
    "球头抗压强度(MPa)": "compressive_strength_mpa",
    "球头屈服强度(MPa)": "yield_strength_mpa",
    "球头密度(g/cm³)": "density_g_cm3",
    "球头泊松比": "poisson_ratio",
    
    "股骨柄硬度(HV)": "hardness_hv",
    "股骨柄表面粗糙度(μm)": "surface_roughness_um",
    "股骨柄弹性模量(GPa)": "elastic_modulus_gpa",
    "股骨柄抗压强度(MPa)": "compressive_strength_mpa",
    "股骨柄屈服强度(MPa)": "yield_strength_mpa",
    "股骨柄密度(g/cm³)": "density_g_cm3",
    "股骨柄泊松比": "poisson_ratio",
    
    # 测试结果表
    "内衬相含量变化": "phase_content_change",
    "累计磨损量": "cumulative_wear",
    "磨损率": "wear_rate",
    "抗疲劳性": "fatigue_resistance",
    "接触应力": "contact_stress",
    "Von Mises应力": "von_mises_stress",
    
    # 计算模拟表
    "计算建模软件": "software",
    "计算建模输入参数": "input_params",
    "计算建模输出参数": "output_params",
    "计算建模模拟结构图": "structure_diagram",
    "计算建模模拟结构图说明": "diagram_description"
}


def translate_fields(chinese_data, table_name):
    """将中文字段名转换为英文字段名"""
    english_data = {}
    for cn_field, value in chinese_data.items():
        en_field = FIELD_MAPPING.get(cn_field)
        if en_field:
            english_data[en_field] = value
        else:
            print(f"⚠️  警告: 表 {table_name} 中的字段 '{cn_field}' 没有映射")
    return english_data


def insert_record(conn, record):
    """插入一条记录到数据库（多表）"""
    cursor = conn.cursor()
    data_id = None
    
    try:
        # 1. 插入主表（基本信息表）
        if record.get("基本信息表"):
            basic_info = translate_fields(record["基本信息表"], "基本信息表")
            data_id = basic_info.get("data_id")
            
            cursor.execute("""
                INSERT INTO basic_info (data_id, application_site, patent_or_literature)
                VALUES (?, ?, ?)
            """, (basic_info.get("data_id"), 
                  basic_info.get("application_site"),
                  basic_info.get("patent_or_literature")))
        
        # 2. 插入从表
        for cn_table, en_table in TABLE_MAPPING.items():
            if cn_table == "基本信息表":
                continue
            
            if record.get(cn_table) and record[cn_table] is not None:
                table_data = translate_fields(record[cn_table], cn_table)
                
                # 构造INSERT语句
                fields = list(table_data.keys())
                placeholders = ", ".join(["?"] * len(fields))
                field_names = ", ".join(fields)
                values = [table_data[f] for f in fields]
                
                sql = f"INSERT INTO {en_table} ({field_names}) VALUES ({placeholders})"
                cursor.execute(sql, values)
        
        conn.commit()
        return {"success": True, "data_id": data_id}
    
    except Exception as e:
        conn.rollback()
        return {"success": False, "error": str(e), "data_id": data_id}


def import_json_file(json_file, db_path):
    """导入单个JSON文件"""
    print(f"\n处理文件: {json_file}")
    
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    records = data.get("records", [])
    print(f"  找到 {len(records)} 条记录")
    
    conn = sqlite3.connect(db_path)
    
    success_count = 0
    failed_count = 0
    
    for i, record in enumerate(records, 1):
        result = insert_record(conn, record)
        if result["success"]:
            print(f"  [{i}/{len(records)}] ✅ {result['data_id']}")
            success_count += 1
        else:
            print(f"  [{i}/{len(records)}] ❌ {result.get('data_id', 'unknown')}: {result['error']}")
            failed_count += 1
    
    conn.close()
    
    return {"success": success_count, "failed": failed_count}


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/import_json.py <json_file_or_dir>")
        print("\n示例:")
        print("  python scripts/import_json.py data/processed/extracted/paper1.json")
        print("  python scripts/import_json.py data/processed/extracted/")
        sys.exit(1)
    
    input_path = Path(sys.argv[1])
    db_path = Path("data/artificial_joint.db")
    
    if not db_path.exists():
        print(f"❌ 数据库不存在: {db_path}")
        print("   请先运行: sqlite3 data/artificial_joint.db < data_schema/schema.sql")
        sys.exit(1)
    
    print("=" * 60)
    print("导入JSON到数据库")
    print("=" * 60)
    
    json_files = []
    if input_path.is_file():
        json_files = [input_path]
    elif input_path.is_dir():
        json_files = list(input_path.glob("*.json"))
    else:
        print(f"❌ 路径不存在: {input_path}")
        sys.exit(1)
    
    print(f"\n找到 {len(json_files)} 个JSON文件")
    
    total_success = 0
    total_failed = 0
    
    for json_file in json_files:
        result = import_json_file(json_file, db_path)
        total_success += result["success"]
        total_failed += result["failed"]
    
    print("\n" + "=" * 60)
    print("导入完成！")
    print("=" * 60)
    print(f"✅ 成功: {total_success} 条")
    print(f"❌ 失败: {total_failed} 条")


if __name__ == "__main__":
    main()
