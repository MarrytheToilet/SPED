#!/usr/bin/env python3
"""
DOI提取器 - 从MinerU解析结果中提取DOI并添加到full.md

功能：
1. 从content_list.json提取DOI
2. 将DOI作为元信息添加到full.md开头
"""
import json
import re
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger


class DOIExtractor:
    """DOI提取器"""
    
    # DOI正则模式：10.xxxx/xxxxx
    DOI_PATTERN = re.compile(r'10\.\d{4,}/[^\s\"\',}\]]+')
    
    # 常见的OCR错误修正映射
    OCR_FIXES = {
        'doi.0rg': 'doi.org',  # 0被误识别为o
        'doi.0RG': 'doi.org',
        'd0i.org': 'doi.org',  # o被误识别为0
        'D0I': 'DOI',
        'd01': 'doi',
    }
    
    @classmethod
    def _fix_ocr_errors(cls, text: str) -> str:
        """修复DOI相关的常见OCR错误"""
        result = text
        for wrong, correct in cls.OCR_FIXES.items():
            result = result.replace(wrong, correct)
        return result
    
    @classmethod
    def extract_from_json(cls, json_path: Path) -> Optional[str]:
        """
        从JSON文件中提取DOI
        
        Args:
            json_path: JSON文件路径（content_list.json或layout.json）
        
        Returns:
            提取到的DOI或None
        """
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 转为字符串进行搜索
            text = json.dumps(data)
            
            # 先修复常见的OCR错误
            text = cls._fix_ocr_errors(text)
            
            # 查找DOI
            matches = cls.DOI_PATTERN.findall(text)
            if matches:
                # 清理DOI（移除末尾的标点符号）
                doi = matches[0].rstrip('.,;:)')
                return doi
                
        except Exception as e:
            logger.error(f"读取JSON失败: {json_path} - {e}")
        
        return None
    
    @classmethod
    def extract_from_paper_dir(cls, paper_dir: Path) -> Optional[str]:
        """
        从论文目录中提取DOI
        
        尝试顺序：
        1. *_content_list.json（更可能包含元信息）
        2. layout.json
        
        Args:
            paper_dir: 论文目录路径
        
        Returns:
            提取到的DOI或None
        """
        # 优先查找content_list.json
        content_jsons = list(paper_dir.glob("*_content_list.json"))
        if content_jsons:
            for json_path in content_jsons:
                doi = cls.extract_from_json(json_path)
                if doi:
                    logger.debug(f"从 {json_path.name} 提取到DOI: {doi}")
                    return doi
        
        # 尝试layout.json
        layout_json = paper_dir / "layout.json"
        if layout_json.exists():
            doi = cls.extract_from_json(layout_json)
            if doi:
                logger.debug(f"从 layout.json 提取到DOI: {doi}")
                return doi
        
        return None
    
    @classmethod
    def add_doi_to_markdown(cls, md_path: Path, doi: str) -> bool:
        """
        将DOI添加到Markdown文件开头
        
        Args:
            md_path: Markdown文件路径
            doi: DOI字符串
        
        Returns:
            是否成功添加（如果已存在则返回False）
        """
        try:
            with open(md_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 检查是否已有DOI
            if f'**DOI**: {doi}' in content or f'DOI: {doi}' in content:
                logger.debug(f"Markdown已包含DOI: {md_path.name}")
                return False
            
            # 在开头添加DOI信息
            doi_header = f"**DOI**: {doi}\n\n---\n\n"
            new_content = doi_header + content
            
            with open(md_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"✅ 已添加DOI到: {md_path.name}")
            return True
            
        except Exception as e:
            logger.error(f"处理Markdown失败: {md_path} - {e}")
            return False
    
    @classmethod
    def process_paper_directory(cls, paper_dir: Path) -> Dict[str, Any]:
        """
        处理单个论文目录：提取DOI并添加到full.md
        
        Args:
            paper_dir: 论文目录
        
        Returns:
            处理结果字典
        """
        result = {
            "paper": paper_dir.name,
            "doi": None,
            "added": False,
            "error": None
        }
        
        # 提取DOI
        doi = cls.extract_from_paper_dir(paper_dir)
        if not doi:
            result["error"] = "未找到DOI"
            return result
        
        result["doi"] = doi
        
        # 添加到full.md
        md_path = paper_dir / "full.md"
        if md_path.exists():
            result["added"] = cls.add_doi_to_markdown(md_path, doi)
        else:
            result["error"] = "full.md不存在"
        
        return result
    
    @classmethod
    def process_all_papers(cls, parsed_dir: Path) -> Dict[str, Any]:
        """
        处理所有已解析的论文
        
        Args:
            parsed_dir: 解析目录（包含多个论文子目录）
        
        Returns:
            统计信息
        """
        stats = {
            "total": 0,
            "success": 0,
            "already_has_doi": 0,
            "no_doi_found": 0,
            "failed": 0,
            "papers": []
        }
        
        # 查找所有论文目录
        paper_dirs = [
            d for d in parsed_dir.iterdir()
            if d.is_dir() and (d / "full.md").exists()
        ]
        
        logger.info(f"找到 {len(paper_dirs)} 个论文目录")
        
        for paper_dir in paper_dirs:
            stats["total"] += 1
            result = cls.process_paper_directory(paper_dir)
            stats["papers"].append(result)
            
            if result["added"]:
                stats["success"] += 1
            elif result["doi"] and not result["added"]:
                stats["already_has_doi"] += 1
            elif result["error"] == "未找到DOI":
                stats["no_doi_found"] += 1
            else:
                stats["failed"] += 1
        
        return stats


def main():
    """命令行入口"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))
    from settings import PARSED_DIR
    
    print("="*60)
    print("DOI提取与添加工具")
    print("="*60)
    
    stats = DOIExtractor.process_all_papers(PARSED_DIR)
    
    print(f"\n处理完成:")
    print(f"  总数: {stats['total']}")
    print(f"  成功添加: {stats['success']}")
    print(f"  已有DOI: {stats['already_has_doi']}")
    print(f"  未找到DOI: {stats['no_doi_found']}")
    print(f"  失败: {stats['failed']}")


if __name__ == "__main__":
    main()
