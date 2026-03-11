#!/usr/bin/env python3
"""
DOI提取器 - 从MinerU的JSON文件中提取DOI并添加到Markdown
"""
import json
import re
from pathlib import Path
from typing import Optional
from loguru import logger


def extract_doi_from_json(json_path: Path) -> Optional[str]:
    """从JSON文件中提取DOI"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            text = str(data)
            
            # 查找DOI模式：10.xxxx/xxxxx
            dois = re.findall(r'10\.\d{4,}/[^\s\"\',}]+', text)
            if dois:
                # 清理DOI（移除末尾的标点符号）
                doi = dois[0].rstrip('.,;:')
                return doi
    except Exception as e:
        logger.error(f"读取JSON失败: {json_path} - {e}")
    
    return None


def add_doi_to_markdown(md_path: Path, doi: str) -> bool:
    """将DOI添加到Markdown开头"""
    try:
        with open(md_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 检查是否已有DOI
        if f'DOI: {doi}' in content or doi in content[:500]:
            logger.info(f"Markdown已包含DOI: {md_path.name}")
            return False
        
        # 在开头添加DOI信息
        doi_header = f"**DOI**: {doi}\n\n---\n\n"
        new_content = doi_header + content
        
        with open(md_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.success(f"✅ 已添加DOI到: {md_path.name}")
        return True
        
    except Exception as e:
        logger.error(f"处理Markdown失败: {md_path} - {e}")
        return False


def process_paper_directory(paper_dir: Path) -> dict:
    """处理单个论文目录"""
    result = {
        "paper": paper_dir.name,
        "doi": None,
        "added": False,
        "error": None
    }
    
    # 查找layout.json或content_list.json
    layout_json = paper_dir / "layout.json"
    content_json = list(paper_dir.glob("*_content_list.json"))
    
    doi = None
    
    # 优先从layout.json提取
    if layout_json.exists():
        doi = extract_doi_from_json(layout_json)
        if doi:
            logger.info(f"从layout.json提取到DOI: {doi}")
    
    # 如果没有，从content_list.json提取
    if not doi and content_json:
        doi = extract_doi_from_json(content_json[0])
        if doi:
            logger.info(f"从content_list.json提取到DOI: {doi}")
    
    if not doi:
        result["error"] = "未找到DOI"
        return result
    
    result["doi"] = doi
    
    # 添加到full.md
    md_path = paper_dir / "full.md"
    if md_path.exists():
        result["added"] = add_doi_to_markdown(md_path, doi)
    else:
        result["error"] = "full.md不存在"
    
    return result


def process_batch(parsed_dir: Path, batch_name: str = None) -> dict:
    """处理批次或所有论文"""
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "no_doi": 0,
        "papers": []
    }
    
    # 确定要处理的目录
    if batch_name:
        search_dir = parsed_dir / "output" / batch_name
        if not search_dir.exists():
            logger.error(f"批次目录不存在: {search_dir}")
            return stats
    else:
        search_dir = parsed_dir / "output"
    
    # 查找所有论文目录（包含full.md的目录）
    paper_dirs = []
    for path in search_dir.rglob("full.md"):
        paper_dirs.append(path.parent)
    
    logger.info(f"找到 {len(paper_dirs)} 个论文目录")
    
    # 处理每个论文
    for paper_dir in paper_dirs:
        stats["total"] += 1
        result = process_paper_directory(paper_dir)
        stats["papers"].append(result)
        
        if result["added"]:
            stats["success"] += 1
        elif result["error"] == "未找到DOI":
            stats["no_doi"] += 1
        else:
            stats["failed"] += 1
    
    return stats


def main():
    """主函数"""
    import sys
    from pathlib import Path
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    parsed_dir = project_root / "data" / "processed" / "parsed"
    
    logger.info("=" * 80)
    logger.info("DOI提取器 - 从JSON文件提取DOI并添加到Markdown")
    logger.info("=" * 80)
    
    # 处理命令行参数
    batch_name = sys.argv[1] if len(sys.argv) > 1 else None
    
    if batch_name:
        logger.info(f"处理批次: {batch_name}")
    else:
        logger.info("处理所有批次")
    
    # 处理
    stats = process_batch(parsed_dir, batch_name)
    
    # 显示结果
    print("\n" + "=" * 80)
    print("处理结果")
    print("=" * 80)
    print(f"总计: {stats['total']} 个论文")
    print(f"✅ 成功添加DOI: {stats['success']} 个")
    print(f"⚠️  未找到DOI: {stats['no_doi']} 个")
    print(f"❌ 失败: {stats['failed']} 个")
    
    # 显示详情
    if stats['no_doi'] > 0:
        print(f"\n未找到DOI的论文:")
        for p in stats["papers"]:
            if p["error"] == "未找到DOI":
                print(f"  - {p['paper']}")
    
    if stats['success'] > 0:
        print(f"\n成功添加DOI的论文（前10个）:")
        count = 0
        for p in stats["papers"]:
            if p["added"] and count < 10:
                print(f"  - {p['paper']}: {p['doi']}")
                count += 1


if __name__ == "__main__":
    main()
