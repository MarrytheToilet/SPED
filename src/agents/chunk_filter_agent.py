#!/usr/bin/env python3
"""
ChunkFilterAgent - 文档切分和过滤Agent

功能:
1. 智能文档切分（基于章节、段落）
2. 过滤无关内容（致谢、参考文献、附录等）
3. 提取元信息（title、DOI、authors等）
4. 构建结构化的文档块
"""
import re
from typing import Dict, List, Optional, Any
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime

from .base import BaseAgent, AgentResult
from settings import CHUNK_SIZE, CHUNK_OVERLAP


@dataclass
class DocumentMetadata:
    """文档元信息"""
    paper_id: str
    title: Optional[str] = None
    doi: Optional[str] = None
    authors: Optional[List[str]] = None
    abstract: Optional[str] = None
    keywords: Optional[List[str]] = None
    publication_date: Optional[str] = None
    journal: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class DocumentChunk:
    """文档块"""
    chunk_id: str
    content: str
    section: str
    start_pos: int
    end_pos: int
    char_count: int
    is_filtered: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class FilteredDocument:
    """过滤后的文档"""
    paper_id: str
    metadata: DocumentMetadata
    chunks: List[DocumentChunk]
    filtered_sections: List[str]
    total_chars: int
    effective_chars: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "metadata": self.metadata.to_dict(),
            "chunks": [chunk.to_dict() for chunk in self.chunks],
            "filtered_sections": self.filtered_sections,
            "total_chars": self.total_chars,
            "effective_chars": self.effective_chars,
            "chunk_count": len(self.chunks),
            "active_chunk_count": len([c for c in self.chunks if not c.is_filtered])
        }


class ChunkFilterAgent(BaseAgent[Dict[str, Any], FilteredDocument]):
    """文档切分和过滤Agent"""
    
    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化Agent
        
        Args:
            chunk_size: 分块大小（字符数），None使用配置文件
            chunk_overlap: 分块重叠大小，None使用配置文件
            config: 额外配置
        """
        super().__init__(
            name="ChunkFilterAgent",
            description="文档切分和过滤Agent",
            config=config or {}
        )
        
        self.chunk_size = chunk_size or CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or CHUNK_OVERLAP
        
        # 过滤关键词（不区分大小写）
        self.filter_keywords = [
            # 英文
            "references", "reference", "bibliography", "works cited",
            "acknowledgment", "acknowledgement", "acknowledgments", "acknowledgements",
            "appendix", "appendices", "supplementary", "supporting information",
            "conflict of interest", "competing interests", "funding",
            "author contribution", "data availability",
            # 中文
            "参考文献", "致谢", "附录", "补充材料", "利益冲突", "基金资助",
            "作者贡献", "数据可用性"
        ]
        
        # 保留的重要章节
        self.keep_sections = [
            "abstract", "introduction", "background", "related work",
            "methods", "methodology", "materials and methods", "experimental",
            "results", "discussion", "conclusion", "findings",
            "摘要", "引言", "背景", "方法", "实验", "结果", "讨论", "结论"
        ]
        
        self.log_info(f"初始化完成: chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
    
    def process(self, input_data: Dict[str, Any]) -> AgentResult[FilteredDocument]:
        """
        处理文档
        
        Args:
            input_data: {
                "paper_id": str,
                "file_path": str or Path,  # 文件路径
                "content": str (可选)      # 或直接提供内容
            }
        
        Returns:
            AgentResult[FilteredDocument]: 过滤后的文档
        """
        try:
            paper_id = input_data.get("paper_id")
            if not paper_id:
                return AgentResult(
                    success=False,
                    error="缺少paper_id参数"
                )
            
            # 获取文档内容
            content = input_data.get("content")
            if not content:
                file_path = input_data.get("file_path")
                if not file_path:
                    return AgentResult(
                        success=False,
                        error="必须提供content或file_path参数"
                    )
                
                file_path = Path(file_path)
                if not file_path.exists():
                    return AgentResult(
                        success=False,
                        error=f"文件不存在: {file_path}"
                    )
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            
            self.log_info(f"开始处理文档: {paper_id}, 长度: {len(content)} 字符")
            
            # 1. 提取元信息
            metadata = self._extract_metadata(paper_id, content)
            
            # 2. 过滤无关内容
            filtered_content, filtered_sections = self._filter_content(content)
            
            # 3. 智能分块
            chunks = self._chunk_document(paper_id, filtered_content)
            
            # 4. 构建结果
            result = FilteredDocument(
                paper_id=paper_id,
                metadata=metadata,
                chunks=chunks,
                filtered_sections=filtered_sections,
                total_chars=len(content),
                effective_chars=len(filtered_content)
            )
            
            self.log_info(
                f"处理完成: {paper_id}, "
                f"原始字符={result.total_chars}, "
                f"有效字符={result.effective_chars}, "
                f"分块数={len(chunks)}, "
                f"过滤章节={len(filtered_sections)}"
            )
            
            return AgentResult(
                success=True,
                data=result,
                metadata={
                    "paper_id": paper_id,
                    "chunk_count": len(chunks),
                    "filtered_sections": filtered_sections
                }
            )
            
        except Exception as e:
            self.log_error(f"处理失败: {paper_id}, 错误: {e}")
            return AgentResult(
                success=False,
                error=str(e)
            )
    
    def _extract_metadata(self, paper_id: str, content: str) -> DocumentMetadata:
        """提取文档元信息"""
        metadata = DocumentMetadata(paper_id=paper_id)
        
        # 提取标题（通常是第一个# 标题）
        title_match = re.search(r'^#\s+(.+?)$', content, re.MULTILINE)
        if title_match:
            metadata.title = title_match.group(1).strip()
        
        # 提取DOI
        doi_match = re.search(
            r'(?:doi|DOI)[:：\s]*(?:https?://(?:dx\.)?doi\.org/)?(10\.\d{4,}/[^\s\)]+)',
            content
        )
        if doi_match:
            metadata.doi = doi_match.group(1)
        
        # 提取摘要（Abstract后的段落）
        abstract_match = re.search(
            r'(?:^|\n)##?\s*(?:Abstract|ABSTRACT|摘要)[\s\n]+(.*?)(?:\n##|\n---|\Z)',
            content,
            re.IGNORECASE | re.DOTALL
        )
        if abstract_match:
            abstract_text = abstract_match.group(1).strip()
            # 限制长度
            metadata.abstract = abstract_text[:2000] if len(abstract_text) > 2000 else abstract_text
        
        # 提取关键词
        keywords_match = re.search(
            r'(?:Keywords?|KEYWORDS?|关键词)[:：\s]+(.*?)(?:\n|$)',
            content,
            re.IGNORECASE
        )
        if keywords_match:
            keywords_text = keywords_match.group(1)
            metadata.keywords = [k.strip() for k in re.split(r'[;,，；]', keywords_text) if k.strip()]
        
        self.log_debug(f"元信息提取完成: title={bool(metadata.title)}, doi={bool(metadata.doi)}")
        
        return metadata
    
    def _filter_content(self, content: str) -> tuple[str, List[str]]:
        """
        过滤无关内容
        
        Returns:
            (filtered_content, filtered_sections): 过滤后的内容和被过滤的章节列表
        """
        filtered_sections = []
        
        # 策略1: 只在文章后60%部分查找参考文献/致谢
        content_length = len(content)
        search_start = int(content_length * 0.6)
        
        # 查找参考文献开始位置
        ref_start = None
        for keyword in self.filter_keywords:
            # 在后60%部分查找
            pattern = rf'(?:^|\n)##?\s*{re.escape(keyword)}\s*(?:\n|$)'
            match = re.search(pattern, content[search_start:], re.IGNORECASE)
            if match:
                actual_pos = search_start + match.start()
                if ref_start is None or actual_pos < ref_start:
                    ref_start = actual_pos
                    filtered_sections.append(f"{keyword} (位置: {actual_pos})")
        
        # 如果找到参考文献，截断内容
        if ref_start:
            filtered_content = content[:ref_start].strip()
            self.log_info(f"过滤内容: 原始{content_length}字符 -> {len(filtered_content)}字符")
        else:
            filtered_content = content
            self.log_debug("未找到需要过滤的章节")
        
        return filtered_content, filtered_sections
    
    def _chunk_document(self, paper_id: str, content: str) -> List[DocumentChunk]:
        """
        智能文档分块
        
        策略:
        1. 优先按章节（##标题）分块
        2. 如果章节过大，再按字符数分块
        3. 保持段落完整性
        """
        chunks = []
        
        # 策略1: 尝试按章节分块
        sections = self._split_by_sections(content)
        
        if sections and len(sections) > 1:
            # 按章节分块成功
            self.log_debug(f"按章节分块: {len(sections)}个章节")
            
            for i, (section_title, section_content, start_pos) in enumerate(sections):
                if len(section_content) <= self.chunk_size:
                    # 章节小于chunk_size，直接作为一个chunk
                    chunk = DocumentChunk(
                        chunk_id=f"{paper_id}_chunk_{i}",
                        content=section_content,
                        section=section_title or "Unknown",
                        start_pos=start_pos,
                        end_pos=start_pos + len(section_content),
                        char_count=len(section_content),
                        is_filtered=False
                    )
                    chunks.append(chunk)
                else:
                    # 章节过大，继续分块
                    sub_chunks = self._split_large_section(
                        paper_id, i, section_title, section_content, start_pos
                    )
                    chunks.extend(sub_chunks)
        else:
            # 无法按章节分块，使用字符数分块
            self.log_debug("无明显章节，使用字符数分块")
            chunks = self._split_by_chars(paper_id, content)
        
        self.log_info(f"分块完成: {len(chunks)}个chunk")
        return chunks
    
    def _split_by_sections(self, content: str) -> List[tuple[str, str, int]]:
        """
        按章节分割
        
        Returns:
            List of (section_title, section_content, start_pos)
        """
        # 匹配## 或### 标题
        pattern = r'^(##\s+.+?)$'
        matches = list(re.finditer(pattern, content, re.MULTILINE))
        
        if not matches:
            return []
        
        sections = []
        for i, match in enumerate(matches):
            section_title = match.group(1).strip('#').strip()
            start_pos = match.start()
            
            # 确定内容范围
            if i < len(matches) - 1:
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(content)
            
            section_content = content[start_pos:end_pos].strip()
            sections.append((section_title, section_content, start_pos))
        
        return sections
    
    def _split_large_section(
        self,
        paper_id: str,
        section_idx: int,
        section_title: str,
        content: str,
        base_pos: int
    ) -> List[DocumentChunk]:
        """分割过大的章节"""
        chunks = []
        current_pos = 0
        chunk_idx = 0
        
        while current_pos < len(content):
            # 确定本次chunk的结束位置
            end_pos = min(current_pos + self.chunk_size, len(content))
            
            # 如果不是最后一块，尝试在段落边界切分
            if end_pos < len(content):
                # 向后查找段落边界（\n\n）
                newline_pos = content.find('\n\n', end_pos - 100, end_pos + 100)
                if newline_pos != -1:
                    end_pos = newline_pos + 2
            
            chunk_content = content[current_pos:end_pos].strip()
            
            chunk = DocumentChunk(
                chunk_id=f"{paper_id}_sec{section_idx}_chunk_{chunk_idx}",
                content=chunk_content,
                section=section_title,
                start_pos=base_pos + current_pos,
                end_pos=base_pos + end_pos,
                char_count=len(chunk_content),
                is_filtered=False
            )
            chunks.append(chunk)
            
            # 移动位置（带重叠）
            current_pos = end_pos - self.chunk_overlap
            if current_pos >= len(content) - self.chunk_overlap:
                break
            
            chunk_idx += 1
        
        return chunks
    
    def _split_by_chars(self, paper_id: str, content: str) -> List[DocumentChunk]:
        """按字符数分块（保持段落完整）"""
        chunks = []
        current_pos = 0
        chunk_idx = 0
        
        while current_pos < len(content):
            end_pos = min(current_pos + self.chunk_size, len(content))
            
            # 尝试在段落边界切分
            if end_pos < len(content):
                newline_pos = content.find('\n\n', end_pos - 100, end_pos + 100)
                if newline_pos != -1:
                    end_pos = newline_pos + 2
            
            chunk_content = content[current_pos:end_pos].strip()
            
            chunk = DocumentChunk(
                chunk_id=f"{paper_id}_chunk_{chunk_idx}",
                content=chunk_content,
                section="Main",
                start_pos=current_pos,
                end_pos=end_pos,
                char_count=len(chunk_content),
                is_filtered=False
            )
            chunks.append(chunk)
            
            current_pos = end_pos - self.chunk_overlap
            if current_pos >= len(content) - self.chunk_overlap:
                break
            
            chunk_idx += 1
        
        return chunks
    
    def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """验证输入"""
        if not isinstance(input_data, dict):
            return False
        
        if "paper_id" not in input_data:
            return False
        
        # 必须有content或file_path之一
        has_content = "content" in input_data
        has_path = "file_path" in input_data
        
        return has_content or has_path
    
    def log_info(self, message: str):
        """记录INFO日志"""
        self.logger.info(message)
    
    def log_debug(self, message: str):
        """记录DEBUG日志"""
        self.logger.debug(message)
    
    def log_error(self, message: str):
        """记录ERROR日志"""
        self.logger.error(message)
