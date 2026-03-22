"""
全量提取模式 - 一次性提取完整论文
"""
from typing import Dict, List, Any
from datetime import datetime
import hashlib

from .base import ExtractionMode, ExtractionResult


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


class FullMode(ExtractionMode):
    """
    全量提取模式
    
    流程：
    1. 将完整论文 + 提取prompt组合
    2. 一次性调用LLM提取所有数据
    
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
        **kwargs
    ) -> ExtractionResult:
        """执行全量提取"""
        self.logger.info(f"开始全量提取: {paper_id}, 内容长度={len(content)}")
        
        # 组装Prompt
        assembled = self.prompt_assembler.assemble_full_mode(
            paper_text=content,
            paper_id=paper_id,
        )
        
        self.logger.debug(f"Prompt组装完成: {len(assembled.full_prompt)} 字符")
        
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
                "content_length": len(content),
            }
        )
