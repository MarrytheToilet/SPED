"""
全量提取模式 - 一次性提取完整论文

特性：
1. 使用增强版prompt（详细字段提示+完整示例）
2. 长论文智能采样
3. Schema驱动的验证规则
"""
from typing import Dict, List, Any
from datetime import datetime
import hashlib
import random

from .base import ExtractionMode, ExtractionResult
import settings


def generate_data_id(paper_id: str, record_index: int, material_name: str = None) -> str:
    """
    生成唯一的数据ID
    
    格式: SPED-{短哈希}-{序号}
    例如: SPED-a1b2c3d4-001
    """
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    unique_str = f"{paper_id}_{timestamp}_{record_index}_{material_name or ''}"
    hash_obj = hashlib.md5(unique_str.encode())
    short_hash = hash_obj.hexdigest()[:8]
    seq = str(record_index + 1).zfill(3)
    return f"SPED-{short_hash}-{seq}"


def sample_long_paper(
    content: str,
    max_length: int = None,
    head_chars: int = None,
    sample_ratio: float = None,
    seed: int = None
) -> tuple[str, bool]:
    """
    对过长论文进行智能采样
    
    策略：保留开头（摘要+引言）+ 随机抽取剩余内容
    
    Args:
        content: 论文全文内容
        max_length: 触发采样的阈值
        head_chars: 开头保留的字符数
        sample_ratio: 剩余内容的采样比例
        seed: 随机种子
    
    Returns:
        (采样后内容, 是否被采样)
    """
    if max_length is None:
        max_length = settings.SKELETON_MAX_LENGTH
    if head_chars is None:
        head_chars = settings.SKELETON_HEAD_CHARS
    if sample_ratio is None:
        sample_ratio = settings.SKELETON_SAMPLE_RATIO
    
    if len(content) <= max_length:
        return content, False
    
    if seed is not None:
        random.seed(seed)
    
    # 保留开头部分
    head_part = content[:head_chars]
    remaining_part = content[head_chars:]
    
    # 按段落分割
    paragraphs = remaining_part.split('\n\n')
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if not paragraphs:
        return head_part, True
    
    # 随机抽取段落
    sample_count = max(1, int(len(paragraphs) * sample_ratio))
    if sample_count < len(paragraphs):
        sampled_indices = sorted(random.sample(range(len(paragraphs)), sample_count))
        sampled_paragraphs = [paragraphs[i] for i in sampled_indices]
    else:
        sampled_paragraphs = paragraphs
    
    result = head_part + "\n\n[...部分内容已采样保留关键信息...]\n\n" + "\n\n".join(sampled_paragraphs)
    
    # 硬截断
    hard_limit = settings.SKELETON_HARD_LIMIT
    if len(result) > hard_limit:
        result = result[:hard_limit] + "\n\n[...内容已截断...]"
    
    return result, True


class FullMode(ExtractionMode):
    """
    全量提取模式
    
    流程：
    1. 对长论文进行智能采样
    2. 组装增强版Prompt（包含详细字段提示和完整示例）
    3. 一次性调用LLM提取所有数据
    
    适用场景：
    - 短论文（<30KB）
    - 追求速度
    """
    
    @property
    def mode_name(self) -> str:
        return "full"
    
    def extract(
        self,
        paper_id: str,
        content: str,
        chunks: List[str] = None,
        use_sampling: bool = True,
        **kwargs
    ) -> ExtractionResult:
        """
        执行全量提取
        
        Args:
            paper_id: 论文ID
            content: 论文全文
            chunks: 分块（全量模式不使用）
            use_sampling: 是否对长论文进行采样
            **kwargs: 其他参数
        """
        original_length = len(content)
        self.logger.info(f"开始全量提取: {paper_id}, 内容长度={original_length}")
        
        # 对长论文进行采样
        if use_sampling:
            seed = int(hashlib.md5(paper_id.encode()).hexdigest()[:8], 16)
            content, was_sampled = sample_long_paper(content, seed=seed)
            if was_sampled:
                self.logger.info(f"长论文采样: {original_length} -> {len(content)} 字符")
        else:
            was_sampled = False
        
        # 组装增强版Prompt
        assembled = self.prompt_assembler.assemble_full_mode_enhanced(
            paper_text=content,
            paper_id=paper_id,
            include_hints=True,
            include_example=True,
        )
        
        self.logger.debug(f"Prompt组装完成: system={len(assembled.system_prompt)}, user={len(assembled.user_prompt)} 字符")
        
        # 调用LLM
        result = self._call_llm(
            system_prompt=assembled.system_prompt,
            user_prompt=assembled.user_prompt,
            call_id=f"{paper_id}_full",
        )
        
        if not result["success"]:
            return ExtractionResult(
                success=False,
                error=result["error"],
                metadata={"mode": self.mode_name, "paper_id": paper_id}
            )
        
        # 解析结果
        data = result["data"]
        records = data.get("records", [])
        
        # 为每条记录生成唯一数据ID
        for i, record in enumerate(records):
            material_name = record.get("material_name")
            data_id = generate_data_id(paper_id, i, material_name)
            
            # 将数据ID填入所有表的"数据ID"字段
            for table_name in record:
                if table_name.startswith("Sheet") and isinstance(record[table_name], dict):
                    if "数据ID" in record[table_name]:
                        record[table_name]["数据ID"] = data_id
        
        return ExtractionResult(
            success=True,
            records=records,
            count=len(records),
            metadata={
                "mode": self.mode_name,
                "paper_id": paper_id,
                "original_length": original_length,
                "processed_length": len(content),
                "was_sampled": was_sampled,
            }
        )
