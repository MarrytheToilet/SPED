"""
文本提取器 - 从MinerU解析结果中提取文本
"""
import json
from pathlib import Path
from typing import Dict, List
from loguru import logger


class TextExtractor:
    """从MinerU解析结果中提取文本"""
    
    def extract_from_parsed(self, parsed_dir: str) -> Dict:
        """
        从解析目录提取信息
        
        Args:
            parsed_dir: MinerU解析结果目录
            
        Returns:
            包含提取信息的字典
        """
        parsed_path = Path(parsed_dir)
        
        result = {
            'text': '',
            'sections': {},
            'metadata': {},
            'figures': [],
            'tables': []
        }
        
        # 读取full.md
        md_file = parsed_path / 'full.md'
        if md_file.exists():
            with open(md_file, 'r', encoding='utf-8') as f:
                result['text'] = f.read()
                logger.info(f"读取full.md成功: {len(result['text'])} 字符")
        
        # 读取layout.json
        layout_file = parsed_path / 'layout.json'
        if layout_file.exists():
            with open(layout_file, 'r', encoding='utf-8') as f:
                layout = json.load(f)
                result['metadata']['layout'] = layout
                logger.info("读取layout.json成功")
        
        # 提取标题（从第一个heading）
        lines = result['text'].split('\n')
        for line in lines:
            if line.startswith('# '):
                result['metadata']['title'] = line[2:].strip()
                break
        
        # 分割章节
        result['sections'] = self.extract_sections(result['text'])
        
        # 提取图片信息
        images_dir = parsed_path / 'images'
        if images_dir.exists():
            result['figures'] = [str(f) for f in images_dir.glob('*.*')]
        
        return result
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        分割文本为章节，并剔除无用章节
        
        Args:
            text: 完整文本
            
        Returns:
            有效章节的字典
        """
        sections = {}
        current_section = 'introduction'
        current_text = []
        
        # 定义需要剔除的章节（不区分大小写）
        excluded_sections = {
            'references', 'reference', 'bibliography',
            'acknowledgements', 'acknowledgement', 'acknowledgments', 'acknowledgment',
            'supplementary', 'appendix', 'appendices'
        }
        
        for line in text.split('\n'):
            if line.startswith('# '):
                # 保存前一章节（如果不在排除列表中）
                if current_text and current_section not in excluded_sections:
                    sections[current_section] = '\n'.join(current_text)
                
                # 新章节
                section_title = line[2:].strip().lower()
                
                # 检查是否是需要排除的章节
                should_exclude = any(excl in section_title for excl in excluded_sections)
                
                if should_exclude:
                    current_section = '__excluded__'
                    current_text = []
                    logger.info(f"跳过无用章节: {section_title}")
                    continue
                
                # 标准化章节名称
                if 'abstract' in section_title:
                    current_section = 'abstract'
                elif 'introduction' in section_title:
                    current_section = 'introduction'
                elif 'method' in section_title or 'material' in section_title or 'experimental' in section_title:
                    current_section = 'methods'
                elif 'result' in section_title and 'discussion' not in section_title:
                    current_section = 'results'
                elif 'discussion' in section_title:
                    current_section = 'discussion'
                elif 'conclusion' in section_title:
                    current_section = 'conclusion'
                else:
                    current_section = section_title.replace(' ', '_')
                
                current_text = []
            else:
                if current_section != '__excluded__':
                    current_text.append(line)
        
        # 保存最后一章节（如果不在排除列表中）
        if current_text and current_section not in excluded_sections and current_section != '__excluded__':
            sections[current_section] = '\n'.join(current_text)
        
        logger.info(f"提取了 {len(sections)} 个有效章节，已剔除references/acknowledgements等")
        return sections
    
    def get_full_content_without_references(self, text: str) -> str:
        """
        获取去除references等无用章节后的完整文本
        
        Args:
            text: 原始完整文本
            
        Returns:
            清理后的完整文本
        """
        sections = self.extract_sections(text)
        # 按常规顺序重新组合
        ordered_sections = ['abstract', 'introduction', 'methods', 'results', 'discussion', 'conclusion']
        
        full_text_parts = []
        for section_name in ordered_sections:
            if section_name in sections:
                full_text_parts.append(f"## {section_name.upper()}\n{sections[section_name]}")
        
        # 添加其他未分类的章节
        for section_name, content in sections.items():
            if section_name not in ordered_sections:
                full_text_parts.append(f"## {section_name.upper()}\n{content}")
        
        full_text = '\n\n'.join(full_text_parts)
        logger.info(f"完整文本（去除无用章节）: {len(full_text)} 字符")
        return full_text
    
    def extract_metadata(self, text: str) -> Dict:
        """提取论文元数据"""
        metadata = {}
        
        lines = text.split('\n')[:50]  # 只看前50行
        
        # 简单的元数据提取逻辑
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # 提取作者
            if 'author' in line_lower and i < 20:
                metadata['authors'] = line.strip()
            
            # 提取期刊/会议
            if 'journal' in line_lower or 'conference' in line_lower:
                metadata['publication'] = line.strip()
            
            # 提取年份
            if 'year' in line_lower or any(str(y) in line for y in range(2000, 2030)):
                import re
                years = re.findall(r'\b(20\d{2})\b', line)
                if years:
                    metadata['year'] = int(years[0])
        
        return metadata
