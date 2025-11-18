#!/usr/bin/env python3
"""
LLM Agent - 统一Prompt + Chunking迭代式数据提取
采用chunk-by-chunk迭代提取，使用统一的prompt一次性提取所有字段
"""
import os
import json
import time
import re
import hashlib
from typing import Dict, Any, List, Optional
from pathlib import Path
from loguru import logger

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .base_agent import BaseAgent
from settings import OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL, CHUNK_SIZE, CHUNK_OVERLAP


class TextChunker:
    """文本分块器 - 智能分割长文本"""
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
        self.log_info = logger.info
    
    def filter_references(self, text: str) -> str:
        """过滤参考文献部分"""
        # 匹配常见的参考文献标题
        ref_patterns = [
            r'\n#+\s*References?\s*\n',
            r'\n#+\s*Bibliography\s*\n',
            r'\n#+\s*参考文献\s*\n',
            r'\n#+\s*REFERENCES?\s*\n',
            r'\n#+\s*文献\s*\n',
        ]
        
        for pattern in ref_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                filtered_text = text[:match.start()]
                self.log_info(f"过滤掉参考文献部分，从 {len(text)} 字符减少到 {len(filtered_text)} 字符")
                return filtered_text
        
        return text
    
    def chunk_text(self, text: str) -> List[Dict[str, Any]]:
        """
        将文本分块，优先在段落边界分割
        返回: List of {chunk_id, content, start_pos, end_pos, length}
        """
        # 先过滤参考文献
        text = self.filter_references(text)
        
        chunks = []
        text_length = len(text)
        start = 0
        chunk_id = 1
        
        self.log_info(f"开始分块: 总长度={text_length}字符, chunk_size={self.chunk_size}, overlap={self.overlap}")
        
        while start < text_length:
            # 计算结束位置
            end = min(start + self.chunk_size, text_length)
            
            # 如果不是最后一块，尝试在合适的边界处分割
            if end < text_length:
                # 在chunk_size附近寻找段落/句子结束标记
                search_start = max(end - 200, start)
                search_end = min(end + 200, text_length)
                search_range = text[search_start:search_end]
                
                # 优先级: 段落 > 句子 > 任意位置
                boundaries = [
                    ('\n\n', 100),  # 段落边界，权重100
                    ('\n', 50),      # 行边界，权重50
                    ('。', 80),      # 中文句号
                    ('.', 80),       # 英文句号
                    ('!', 70),
                    ('?', 70),
                ]
                
                best_pos = -1
                best_score = -1
                
                for marker, weight in boundaries:
                    pos = search_range.rfind(marker)
                    if pos != -1:
                        # 分数 = 权重 * (位置靠后的程度)
                        position_score = pos / len(search_range)
                        score = weight * position_score
                        if score > best_score:
                            best_score = score
                            best_pos = search_start + pos + len(marker)
                
                if best_pos > start:
                    end = best_pos
            
            # 提取chunk内容
            chunk_content = text[start:end].strip()
            
            if chunk_content:
                chunks.append({
                    'chunk_id': chunk_id,
                    'content': chunk_content,
                    'start_pos': start,
                    'end_pos': end,
                    'length': len(chunk_content)
                })
                chunk_id += 1
            
            # 移动到下一个chunk，保留overlap
            start = end - self.overlap
            
            # 避免无限循环
            if start >= text_length or end >= text_length:
                break
        
        self.log_info(f"分块完成: 共{len(chunks)}个chunks")
        return chunks


class LLMExtractionAgent(BaseAgent):
    """
    LLM提取Agent - 统一Prompt + Chunking迭代式提取
    
    核心思路：
    1. 文本分块（过滤参考文献后按chunk_size分割）
    2. 按chunk顺序处理，每次传递已提取的记录列表
    3. 让模型决定：完善现有记录 or 新增记录
    4. 使用统一的prompt，一次性提取所有字段
    """
    
    def __init__(self, schema_path: str = None, prompt_path: str = None):
        super().__init__(
            name="LLM提取Agent",
            description="统一Prompt + Chunking迭代式提取"
        )
        
        if OpenAI is None:
            raise ImportError("需要安装 openai 包")
        
        self.client = OpenAI(
            api_key=OPENAI_API_KEY,
            base_url=OPENAI_API_BASE
        )
        self.model = OPENAI_MODEL
        self.chunker = TextChunker(chunk_size=CHUNK_SIZE, overlap=CHUNK_OVERLAP)
        self.schema = self._load_schema(schema_path) if schema_path else None
        self.paper_data_id = None
        
        # 加载统一的prompt模板
        if prompt_path:
            self.unified_prompt = self._load_prompt(prompt_path)
        else:
            # 默认路径
            default_prompt_path = Path(__file__).parent.parent.parent / "prompts" / "prompt.md"
            if default_prompt_path.exists():
                self.unified_prompt = self._load_prompt(str(default_prompt_path))
            else:
                self.unified_prompt = ""
                self.log_warning("未找到prompt模板")
        
    def _load_schema(self, schema_path: str) -> Dict:
        """加载数据库schema"""
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema_data = json.load(f)
        
        # 提取主表的字段定义
        main_table = schema_data['tables'].get('sheet_1', {})
        columns = main_table.get('columns', [])
        
        # 构建字段说明
        field_descriptions = {}
        for col in columns:
            field_name = col.get('original', col.get('name'))
            field_type = col.get('type', 'TEXT')
            field_descriptions[field_name] = {
                'type': field_type,
                'nullable': col.get('nullable', True)
            }
        
        return {
            'fields': field_descriptions,
            'raw': schema_data
        }
    
    def _load_prompt(self, prompt_path: str) -> str:
        """加载prompt模板"""
        with open(prompt_path, 'r', encoding='utf-8') as f:
            return f.read()
    
    def _generate_data_id(self, paper_id: str) -> str:
        """生成唯一的dataid"""
        hash_obj = hashlib.md5(paper_id.encode('utf-8'))
        short_hash = hash_obj.hexdigest()[:8]
        
        from datetime import datetime
        date_str = datetime.now().strftime("%Y%m%d")
        dataid = f"AJ_{date_str}_{short_hash}"
        
        self.log_info(f"生成dataid: {dataid}")
        return dataid
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        迭代式提取主流程
        
        Args:
            input_data: {
                "full_text_path": "markdown文件路径",
                "paper_id": "论文ID"
            }
        
        Returns:
            提取的完整结构化数据（单个记录或多个记录）
        """
        paper_id = input_data.get("paper_id", "unknown")
        full_text_path = input_data.get("full_text_path")
        
        if not full_text_path or not Path(full_text_path).exists():
            self.log_error(f"找不到文件: {full_text_path}")
            return {"error": "文件不存在"}
        
        # 生成dataid
        if self.paper_data_id is None:
            self.paper_data_id = self._generate_data_id(paper_id)
        
        self.log_info(f"{'='*80}")
        self.log_info(f"开始迭代式提取 - Paper: {paper_id}")
        self.log_info(f"{'='*80}")
        
        # 提取章节
        sections = self.section_extractor.extract_sections(full_text_path)
        self.log_info(f"总共发现 {len(sections)} 个顶层章节")
        
        # 过滤相关章节
        relevant_sections = [s for s in sections if s.is_relevant]
        self.log_info(f"相关章节: {len(relevant_sections)}")
        for section in relevant_sections:
            self.log_info(f"  - {section.title}")
        
        if not relevant_sections:
            self.log_warning("未找到相关章节")
            return {"error": "无相关章节"}
        
        # Phase 1: 提取论文元数据
        paper_metadata = self._extract_paper_metadata(sections[0])
        self.log_info(f"\n论文元数据: {json.dumps(paper_metadata, ensure_ascii=False)}")
        
        # 优化：合并小章节
        relevant_sections = self._merge_small_sections(relevant_sections, min_length=500)
        self.log_info(f"合并后章节数: {len(relevant_sections)}")
        
        # 优化：关键章节优先
        relevant_sections = self._prioritize_sections(relevant_sections)
        
        # Phase 2: 迭代式提取 - 核心创新
        all_records = []
        empty_count = 0  # 连续空章节计数
        
        for i, section in enumerate(relevant_sections):
            self.log_info(f"\n处理章节 {i+1}/{len(relevant_sections)}: {section.title}")
            
            # 传递已有记录，让模型决定完善还是新增
            records = self._extract_from_section_with_context(
                section=section,
                paper_metadata=paper_metadata,
                existing_records=all_records
            )
            
            if records:
                self.log_info(f"  → 本章节: {len(records)} 条记录")
                # 智能合并：更新现有或新增
                all_records = self._intelligent_merge(all_records, records)
                self.log_info(f"  → 累计总数: {len(all_records)} 条记录")
                empty_count = 0  # 重置计数
            else:
                self.log_info(f"  → 未发现实验数据")
                empty_count += 1
                
                # 早停策略：连续5个章节无数据，提前终止
                if empty_count >= 5:
                    self.log_info(f"\n⚠️  连续{empty_count}个章节无数据，提前终止处理")
                    break
            
            time.sleep(0.5)  # 避免API限流
        
        # Phase 3: 最终清理和验证
        final_records = self._final_cleanup(all_records)
        self.log_info(f"\n{'='*80}")
        self.log_info(f"✓ 提取完成: {len(final_records)} 条有效记录")
        self.log_info(f"{'='*80}")
        
        # 如果只有一条记录，返回单个dict；否则返回列表
        if len(final_records) == 1:
            result = final_records[0]
            result["dataid"] = self.paper_data_id
            result["paper_id"] = paper_id
            return result
        else:
            # 多条记录，为每条生成带序号的dataid
            for idx, record in enumerate(final_records, 1):
                record["dataid"] = f"{self.paper_data_id}_EXP{idx:03d}"
                record["paper_id"] = paper_id
            return {
                "records": final_records,
                "count": len(final_records)
            }
    
    def _extract_paper_metadata(self, first_section: Section) -> Dict:
        """
        从第一章节提取论文元数据
        注：新的统一方案中，元数据也在迭代提取中一起处理，这里只做简单提取
        """
        # 简化：只提取最基础的信息，其余在后续章节中补充
        return {}
    
    def _extract_from_section_with_context(
        self,
        section: Section,
        paper_metadata: Dict,
        existing_records: List[Dict]
    ) -> List[Dict]:
        """
        从章节提取数据，带上下文信息
        
        **核心创新**: 让模型看到已有记录，智能决定完善还是新增
        """
        # 构建上下文信息
        context_info = self._build_context_info(existing_records)
        
        # 构建prompt
        prompt = self._build_extraction_prompt(
            section=section,
            paper_metadata=paper_metadata,
            context_info=context_info,
            is_first_section=(len(existing_records) == 0)
        )
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system", 
                        "content": "你是一个专业的人工关节数据提取专家。你需要从论文中精确提取实验数据，并智能地决定是完善现有记录还是创建新记录。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            
            # 调试：显示LLM原始返回
            self.log_info(f"    LLM原始返回 (前500字符): {content[:500]}")
            
            result = self._parse_json_safe(content)
            
            # 调试：显示解析后的结果
            if result:
                self.log_info(f"    解析结果: {list(result.keys())}")
            
            # 处理返回格式
            if "records" in result:
                records = result["records"]
                self.log_info(f"    找到records字段，包含 {len(records)} 条记录")
            elif isinstance(result, list):
                records = result
                self.log_info(f"    结果是列表，包含 {len(records)} 条记录")
            else:
                records = [result] if result else []
                self.log_info(f"    结果是单个对象或空: {bool(result)}")
            
            # 调试：显示每条记录的action
            for i, rec in enumerate(records):
                if isinstance(rec, dict):
                    action = rec.get('action', 'unknown')
                    has_data = 'data' in rec
                    self.log_info(f"      记录{i+1}: action={action}, has_data={has_data}")
            
            # 合并元数据并过滤有效记录
            valid_records = []
            for record in records:
                if isinstance(record, dict):
                    # 提取data字段（如果有）
                    data = record.get('data', record)
                    
                    # 检查是否有实验数据
                    if self._has_experimental_data(data):
                        merged = {**paper_metadata, **data}
                        valid_records.append(merged)
                        self.log_info(f"      ✓ 有效记录（包含实验数据）")
                    else:
                        self.log_info(f"      ✗ 无效记录（缺少实验数据）")
            
            self.log_info(f"    最终有效记录数: {len(valid_records)}")
            return valid_records
            
        except Exception as e:
            self.log_error(f"提取失败: {e}")
            return []
    
    def _build_context_info(self, existing_records: List[Dict]) -> str:
        """构建上下文信息，显示已有记录"""
        if not existing_records:
            return ""
        
        context = "\n## 已提取的记录\n\n"
        context += "从之前的章节中，你已经提取了以下记录：\n\n"
        
        # 显示最近3条记录的摘要
        for i, rec in enumerate(existing_records[-3:], 1):
            context += f"**记录 {i}**:\n"
            # 显示关键字段
            key_fields = [
                '数据标识', '球头信息_球头基本信息', '内衬信息_内衬_基本信息',
                '体外实验_内衬与球头摩擦腐蚀实验_内衬与球头_实验设置'
            ]
            for field in key_fields:
                if field in rec and rec[field]:
                    value = str(rec[field])[:100]  # 限制长度
                    context += f"  - {field}: {value}\n"
            context += "\n"
        
        context += """
**重要提示**:
- 如果当前章节提到的样品/实验与已有记录相同（根据材料、实验条件判断），请**完善现有记录**
- 如果是全新的样品/实验，请**创建新记录**
- 在返回的JSON中明确标注操作类型：
  - "action": "enrich" - 完善现有记录（提供record_index）
  - "action": "new" - 创建新记录
"""
        
        return context
    
    def _build_extraction_prompt(
        self,
        section: Section,
        paper_metadata: Dict,
        context_info: str,
        is_first_section: bool
    ) -> str:
        """构建提取prompt - 使用统一的prompt模板"""
        
        metadata_str = ", ".join([f"{k}: {v}" for k, v in paper_metadata.items()])
        
        # 使用统一的prompt模板
        prompt = f"""{self.unified_prompt}

---

## 当前提取任务

### 论文元数据
{metadata_str if metadata_str else "暂无"}

### 当前章节
**标题**: {section.title}
**内容**:
{section.content}

{context_info}

---

请根据上述Prompt中的规则和Schema，从当前章节提取数据。
"""
        
        return prompt
    
    def _has_experimental_data(self, record: Dict) -> bool:
        """检查记录是否包含有效实验数据"""
        # 关键材料字段
        material_fields = [
            '球头信息.球头基本信息',
            '内衬信息.内衬-基本信息',
            '股骨柄信息.股骨柄基本信息'
        ]
        
        # 实验字段
        experimental_fields = [
            '体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置',
            '体外实验-内衬与球头摩擦腐蚀实验.球头磨损实验结果',
            '体外实验-内衬与球头摩擦腐蚀实验.内衬磨损实验结果',
            '体外实验-内衬与球头摩擦腐蚀实验.球头腐蚀实验结果'
        ]
        
        # 基本信息字段
        basic_fields = [
            '数据标识',
            '应用部位'
        ]
        
        # 统计非空字段数
        material_count = sum(1 for field in material_fields 
                            if record.get(field) and record[field] not in [None, "null", ""])
        
        experimental_count = sum(1 for field in experimental_fields 
                                if record.get(field) and record[field] not in [None, "null", ""])
        
        basic_count = sum(1 for field in basic_fields 
                         if record.get(field) and record[field] not in [None, "null", ""])
        
        # 调试信息
        total_fields = len([k for k, v in record.items() if v and v != "null"])
        self.log_info(f"        字段统计: 材料={material_count}, 实验={experimental_count}, 基本={basic_count}, 总非空={total_fields}")
        
        # 至少有一个材料字段或至少有一个实验字段
        return material_count >= 1 or experimental_count >= 1 or basic_count >= 1
    
    def _intelligent_merge(
        self, 
        existing_records: List[Dict], 
        new_records: List[Dict]
    ) -> List[Dict]:
        """
        智能合并记录
        
        根据new_records中的action字段决定：
        - enrich: 完善指定的现有记录
        - new: 添加新记录
        """
        if not existing_records:
            # 第一批记录，直接添加data部分
            return [rec.get('data', rec) for rec in new_records]
        
        merged = existing_records.copy()
        
        for new_rec in new_records:
            action = new_rec.get('action', 'new')
            data = new_rec.get('data', new_rec)
            
            if action == 'enrich':
                # 完善现有记录
                record_index = new_rec.get('record_index', 1)
                target_idx = record_index - 1  # 转为0-based索引
                
                if 0 <= target_idx < len(merged):
                    merged[target_idx] = self._enrich_record(
                        merged[target_idx], 
                        data
                    )
                    self.log_info(f"    ✓ 完善了记录 #{record_index}")
                else:
                    self.log_warning(f"    ! 记录索引 #{record_index} 无效，作为新记录添加")
                    merged.append(data)
            else:
                # 新增记录
                merged.append(data)
                self.log_info(f"    + 添加了新记录")
        
        return merged
    
    def _enrich_record(self, existing: Dict, new_data: Dict) -> Dict:
        """
        用新数据完善现有记录
        
        策略:
        - 保留现有非null值
        - 补充新的非null值
        - 冲突时，选择更详细的值
        """
        enriched = existing.copy()
        
        for key, new_value in new_data.items():
            if new_value is not None and new_value != "null":
                existing_value = enriched.get(key)
                
                if existing_value is None or existing_value == "null":
                    # 填补缺失数据
                    enriched[key] = new_value
                elif existing_value != new_value:
                    # 冲突：两者都有值但不同
                    # 选择更详细的（更长的）
                    if len(str(new_value)) > len(str(existing_value)):
                        enriched[key] = new_value
        
        return enriched
    
    def _final_cleanup(self, records: List[Dict]) -> List[Dict]:
        """最终清理：去重和验证"""
        if not records:
            return records
        
        # 去除完全重复的记录
        seen = set()
        unique_records = []
        
        for record in records:
            record_str = json.dumps(record, sort_keys=True)
            if record_str not in seen:
                seen.add(record_str)
                unique_records.append(record)
        
        # 只保留有效记录
        valid_records = [r for r in unique_records if self._has_experimental_data(r)]
        
        return valid_records
    
    def _merge_small_sections(self, sections: List[Section], min_length: int = 500) -> List[Section]:
        """合并小章节以减少API调用"""
        if not sections:
            return sections
        
        merged = []
        current = None
        
        for section in sections:
            if len(section.content) < min_length:
                if current:
                    # 合并到当前章节
                    current.content += f"\n\n### {section.title}\n\n{section.content}"
                else:
                    current = section
            else:
                if current:
                    merged.append(current)
                current = section
        
        if current:
            merged.append(current)
        
        return merged
    
    def _prioritize_sections(self, sections: List[Section]) -> List[Section]:
        """关键章节优先处理"""
        high_priority_keywords = [
            'material', 'method', 'experiment', 'test',
            '材料', '方法', '实验', '测试', '试验'
        ]
        
        medium_priority_keywords = [
            'result', 'analysis', 'friction', 'wear', 'corrosion',
            '结果', '分析', '摩擦', '磨损', '腐蚀'
        ]
        
        high_priority = []
        medium_priority = []
        low_priority = []
        
        for s in sections:
            title_lower = s.title.lower()
            if any(kw in title_lower for kw in high_priority_keywords):
                high_priority.append(s)
            elif any(kw in title_lower for kw in medium_priority_keywords):
                medium_priority.append(s)
            else:
                low_priority.append(s)
        
        self.log_info(f"章节优先级: 高={len(high_priority)}, 中={len(medium_priority)}, 低={len(low_priority)}")
        
        return high_priority + medium_priority + low_priority
    
    def _parse_json_safe(self, text: str) -> Dict:
        """
        安全地解析JSON，处理markdown代码块等格式
        """
        import re
        
        # 尝试1: 直接解析
        try:
            return json.loads(text)
        except:
            pass
        
        # 尝试2: 去除markdown代码块
        # 匹配 ```json ... ``` 或 ``` ... ```
        code_block_pattern = r'```(?:json)?\s*\n?(.*?)\n?```'
        match = re.search(code_block_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except:
                pass
        
        # 尝试3: 提取第一个JSON对象
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        match = re.search(json_pattern, text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(0))
            except:
                pass
        
        # 失败
        self.log_error(f"JSON解析失败: {text[:200]}...")
        return {}
