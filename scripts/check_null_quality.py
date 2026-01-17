#!/usr/bin/env python3
"""
检查提取结果中的空值质量
用于验证prompt改进效果
"""
import json
import sys
from pathlib import Path
from collections import Counter

def check_null_quality(json_file):
    """检查单个JSON文件的空值质量"""
    with open(json_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    issues = []
    records = data.get('records', [])
    
    if not records:
        return issues
    
    for idx, record in enumerate(records):
        record_data = record.get('data', record)
        
        # 检查所有字段
        def check_fields(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    current_path = f"{path}.{key}" if path else key
                    
                    # 检查错误的空值标记
                    if isinstance(value, str):
                        error_markers = ["未提及", "不清楚", "无", "N/A", "未知", "None", ""]
                        for marker in error_markers:
                            if value == marker:
                                issues.append({
                                    'record': idx,
                                    'field': current_path,
                                    'issue': f'错误的空值标记: "{value}"',
                                    'should_be': 'null'
                                })
                            elif marker in value and len(value) < 10:  # 短字符串中包含错误标记
                                issues.append({
                                    'record': idx,
                                    'field': current_path,
                                    'issue': f'可疑的值: "{value}"',
                                    'should_be': 'null 或更具体的值'
                                })
                    
                    # 递归检查嵌套对象
                    if isinstance(value, dict):
                        check_fields(value, current_path)
        
        check_fields(record_data)
    
    return issues

def main():
    # 检查目录
    extracted_dir = Path("data/processed/extracted")
    
    if not extracted_dir.exists():
        print("❌ 未找到提取结果目录")
        sys.exit(1)
    
    json_files = list(extracted_dir.glob("*.json"))
    
    if not json_files:
        print("❌ 未找到JSON文件")
        sys.exit(1)
    
    print(f"检查 {len(json_files)} 个JSON文件...\n")
    
    # 统计
    total_issues = 0
    files_with_issues = 0
    issue_types = Counter()
    
    # 检查每个文件
    for json_file in json_files:
        issues = check_null_quality(json_file)
        
        if issues:
            files_with_issues += 1
            total_issues += len(issues)
            
            print(f"\n📄 {json_file.name}")
            for issue in issues[:5]:  # 只显示前5个问题
                print(f"   ❌ 记录{issue['record']}: {issue['field']}")
                print(f"      {issue['issue']}")
                print(f"      建议: {issue['should_be']}")
                issue_types[issue['issue'].split(':')[0]] += 1
            
            if len(issues) > 5:
                print(f"   ... 还有 {len(issues) - 5} 个问题")
    
    # 总结
    print(f"\n{'='*70}")
    print(f"检查结果总结")
    print(f"{'='*70}")
    print(f"总文件数: {len(json_files)}")
    print(f"有问题的文件: {files_with_issues}")
    print(f"总问题数: {total_issues}")
    
    if total_issues == 0:
        print(f"\n✅ 太棒了！所有文件的空值处理都是正确的！")
    else:
        print(f"\n⚠️  发现 {total_issues} 个空值质量问题")
        print(f"\n问题类型分布:")
        for issue_type, count in issue_types.most_common(10):
            print(f"  {issue_type}: {count} 次")
        
        print(f"\n💡 建议:")
        print(f"  1. 检查prompt是否正确加载")
        print(f"  2. 尝试重新提取有问题的文件")
        print(f"  3. 查看 docs/PROMPT_IMPROVEMENT_20260117.md 了解改进详情")
    
    print(f"{'='*70}")

if __name__ == "__main__":
    main()
