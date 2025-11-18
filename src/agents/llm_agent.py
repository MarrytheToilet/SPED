#!/usr/bin/env python3
"""
LLM Agent - 统一Prompt + Chunking迭代式数据提取
"""
import os
import json
import time
import re
import hashlib
from typing import Dict, Any, List
from pathlib import Path

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

from .base_agent import BaseAgent
from settings import OPENAI_API_KEY, OPENAI_API_BASE, OPENAI_MODEL, CHUNK_SIZE, CHUNK_OVERLAP


class TextChunker:
    """文本分块器 - 过滤参考文献后进行分块"""
    
    def __init__(self, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP):
        self.chunk_size = chunk_size
        self.overlap = overlap
    
    def filter_references(self, text: str) -> str:
        """
        过滤参考文献和无用章节
        
        策略:
        1. 只在文章后60%部分查找参考文献/致谢
        2. 避免误删前面的"致谢"等普通章节
        """
        text_len = len(text)
        
        # 只在后60%部分查找（避免误删前面的内容）
        search_start = int(text_len * 0.4)
        search_text = text[search_start:]
        
        # 参考文献相关的标题模式
        ref_patterns = [
            r'\n#+\s*References?\s*\n',
            r'\n#+\s*Bibliography\s*\n',
            r'\n#+\s*参考文献\s*\n',
            r'\n#+\s*REFERENCES?\s*\n',
            r'\n#+\s*Acknowledgements?\s*\n',
            r'\n#+\s*Acknowledgments?\s*\n',
            r'\n#+\s*致谢\s*\n',
            r'\n#+\s*Supplementary\s+(?:Information|Material|Data)\s*\n',
            r'\n#+\s*Appendix\s*\n',
            r'\n#+\s*Appendices\s*\n',
        ]
        
        # 在后60%部分查找
        earliest_pos_in_search = len(search_text)
        matched_pattern = None
        
        for pattern in ref_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match and match.start() < earliest_pos_in_search:
                earliest_pos_in_search = match.start()
                matched_pattern = pattern
        
        # 如果找到了，计算在原文中的位置
        if earliest_pos_in_search < len(search_text):
            cut_pos = search_start + earliest_pos_in_search
            filtered_text = text[:cut_pos].strip()
            removed_length = len(text) - len(filtered_text)
            removed_percent = (removed_length / text_len) * 100
            print(f"  [TextChunker] 过滤了 {removed_length} 字符 ({removed_percent:.1f}%) 的参考文献和致谢部分")
            return filtered_text
        
        return text
    
    def chunk_text(self, text: str) -> List[Dict]:
        """
        分块策略:
        1. 先过滤参考文献等无用内容
        2. 按固定字符数分块
        3. 在自然边界（段落、句子）切分
        4. 保持overlap以确保上下文连贯
        """
        # 第一步: 过滤参考文献
        text = self.filter_references(text)
        
        if not text.strip():
            print(f"  [TextChunker] 警告: 过滤后文本为空")
            return []
        
        chunks = []
        start = 0
        chunk_id = 1
        
        while start < len(text):
            end = min(start + self.chunk_size, len(text))
            
            # 在自然边界分割（优先级从高到低）
            if end < len(text):
                # 1. 优先在段落边界（双换行）
                pos = text.rfind('\n\n', start, end)
                if pos > start + self.chunk_size // 2:  # 确保chunk不会太小
                    end = pos + 2
                else:
                    # 2. 其次在单换行
                    pos = text.rfind('\n', start, end)
                    if pos > start + self.chunk_size // 2:
                        end = pos + 1
                    else:
                        # 3. 最后在句子边界
                        for marker in ['. ', '。', '! ', '? ', '！', '？']:
                            pos = text.rfind(marker, start + self.chunk_size // 2, end)
                            if pos > start:
                                end = pos + len(marker)
                                break
            
            chunk_content = text[start:end].strip()
            
            # 只保留有实质内容的chunk（至少100字符）
            if len(chunk_content) >= 100:
                chunks.append({
                    'chunk_id': chunk_id,
                    'content': chunk_content,
                    'length': len(chunk_content),
                    'start_pos': start,
                    'end_pos': end
                })
                chunk_id += 1
            
            # 移动到下一个chunk，保持overlap
            start = end - self.overlap
            if start >= len(text) or (end >= len(text)):
                break
        
        print(f"  [TextChunker] 生成了 {len(chunks)} 个chunks，总长度 {len(text)} 字符")
        return chunks


class LLMExtractionAgent(BaseAgent):
    """LLM提取Agent"""
    
    def __init__(self, schema_path: str = None):
        super().__init__(name="LLM提取Agent", description="Chunking迭代式提取")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_API_BASE)
        self.model = OPENAI_MODEL
        self.chunker = TextChunker()
        
        # 加载prompt
        prompt_path = Path(__file__).parent.parent.parent / "prompts" / "prompt.md"
        with open(prompt_path, 'r', encoding='utf-8') as f:
            self.prompt_template = f.read()
    
    def _generate_dataid(self, paper_id: str) -> str:
        """生成dataid"""
        from datetime import datetime
        hash_val = hashlib.md5(paper_id.encode()).hexdigest()[:8]
        date_str = datetime.now().strftime("%Y%m%d")
        return f"AJ_{date_str}_{hash_val}"
    
    def process(self, input_data: Dict) -> Dict:
        """
        主流程: 分块迭代提取
        
        流程:
        1. 读取文本
        2. 过滤参考文献并分块
        3. 逐chunk迭代提取，传递已有记录作为上下文
        4. 智能合并和去重
        5. 添加元数据并返回
        """
        paper_id = input_data.get("paper_id", "unknown")
        full_text_path = input_data.get("full_text_path")
        
        # 读取文本
        with open(full_text_path, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # 生成dataid
        dataid = self._generate_dataid(paper_id)
        
        self.log_info(f"{'='*80}")
        self.log_info(f"开始提取论文: {paper_id}")
        self.log_info(f"DataID: {dataid}")
        self.log_info(f"原始文本长度: {len(text)} 字符")
        self.log_info(f"{'='*80}")
        
        # 分块（会自动过滤参考文献）
        chunks = self.chunker.chunk_text(text)
        self.log_info(f"文本分块完成: {len(chunks)} chunks")
        
        if not chunks:
            self.log_warning("没有生成有效的chunks，可能文本太短或被完全过滤")
            return {"dataid": dataid, "paper_id": paper_id, "records": [], "count": 0}
        
        # 迭代提取
        all_records = []
        empty_count = 0
        max_empty_chunks = 5  # 连续空chunk阈值
        
        for i, chunk in enumerate(chunks):
            self.log_info(f"\n{'─'*60}")
            self.log_info(f"处理 Chunk {i+1}/{len(chunks)}")
            self.log_info(f"  长度: {chunk['length']} 字符")
            self.log_info(f"  位置: {chunk['start_pos']}-{chunk['end_pos']}")
            
            records = self._extract_from_chunk(chunk, all_records)
            
            if records:
                self.log_info(f"  ✓ 提取到 {len(records)} 条记录")
                
                # 合并记录
                before_count = len(all_records)
                all_records = self._merge_records(all_records, records)
                after_count = len(all_records)
                
                if after_count > before_count:
                    self.log_info(f"  + 新增 {after_count - before_count} 条记录")
                else:
                    self.log_info(f"  ↻ 完善了已有记录")
                
                self.log_info(f"  累计: {len(all_records)} 条记录")
                empty_count = 0
            else:
                self.log_info(f"  - 该chunk无实验数据")
                empty_count += 1
                
                # 早停策略
                if empty_count >= max_empty_chunks:
                    self.log_info(f"\n⚠️  连续 {empty_count} 个chunk无数据，提前终止处理")
                    self.log_info(f"   （可能已过完实验数据部分，剩余为结论或讨论）")
                    break
            
            # API调用间隔
            if i < len(chunks) - 1:
                time.sleep(0.8)
        
        self.log_info(f"\n{'='*80}")
        self.log_info(f"提取完成")
        self.log_info(f"  处理chunks: {i+1}/{len(chunks)}")
        self.log_info(f"  最终记录数: {len(all_records)}")
        self.log_info(f"{'='*80}")
        
        # 添加元数据
        for record in all_records:
            if 'dataid' not in record or not record['dataid']:
                record['dataid'] = dataid
            if 'paper_id' not in record:
                record['paper_id'] = paper_id
        
        # 返回结果
        if len(all_records) == 0:
            self.log_warning("未提取到任何实验数据")
            return {"dataid": dataid, "paper_id": paper_id, "records": [], "count": 0}
        elif len(all_records) == 1:
            self.log_info(f"返回单条记录")
            return all_records[0]
        else:
            self.log_info(f"返回 {len(all_records)} 条记录")
            return {"dataid": dataid, "paper_id": paper_id, "records": all_records, "count": len(all_records)}
    
    def _extract_from_chunk(self, chunk: Dict, existing_records: List[Dict]) -> List[Dict]:
        """从chunk提取数据"""
        # 构建上下文
        context = self._build_context(existing_records)
        
        # 构建prompt
        prompt = f"""{self.prompt_template}

---

## 当前任务

{context}

### 当前文本片段 (Chunk {chunk['chunk_id']}):
```
{chunk['content']}
```

请提取数据，返回纯JSON格式。
"""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "你是专业的数据提取专家。只返回纯JSON，不要添加任何额外文字。保持JSON简洁完整。"},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"},
                max_tokens=4096  # 限制响应长度，避免不完整
            )
            
            content = response.choices[0].message.content
            
            # 调试：显示返回内容的前200字符
            self.log_debug(f"LLM返回内容（前200字符）: {content[:200]}")
            
            result = self._parse_json(content)
            
            if "records" in result and result["records"]:
                return self._process_records(result["records"])
            elif isinstance(result, list):
                # 如果直接返回了列表
                return self._process_records(result)
            else:
                # 检查是否有其他格式
                self.log_debug(f"返回格式: {type(result)}, keys: {result.keys() if isinstance(result, dict) else 'N/A'}")
            
            return []
            
        except json.JSONDecodeError as e:
            self.log_error(f"JSON解析失败: {e}")
            self.log_debug(f"LLM原始返回: {content[:500] if 'content' in locals() else 'N/A'}")
            return []
        except Exception as e:
            self.log_error(f"提取失败: {e}")
            import traceback
            self.log_debug(f"详细错误: {traceback.format_exc()}")
            return []
    
    def _build_context(self, existing_records: List[Dict]) -> str:
        """
        构建上下文信息
        
        向LLM展示已有记录的关键信息，帮助其判断:
        - 是否是同一个实验的补充数据（enrich）
        - 还是新的独立实验（new）
        """
        if not existing_records:
            return """### 已有记录: 无

这是第一个chunk，如果发现实验数据，请创建新记录（action: "new"）。"""
        
        context = f"### 已有记录: {len(existing_records)} 条\n\n"
        context += "请根据以下已有记录判断当前chunk中的数据应该:\n"
        context += "- **完善已有记录** (action: \"enrich\", record_index: N) - 如果是同一实验的补充信息\n"
        context += "- **创建新记录** (action: \"new\") - 如果是不同材料/条件/实验\n\n"
        
        # 显示最近3条记录的关键信息
        for i, rec in enumerate(existing_records[-3:], 1):
            actual_index = len(existing_records) - 3 + i
            context += f"**记录 {actual_index}**:\n"
            
            # 关键识别字段
            key_fields = [
                '数据标识',
                '应用部位', 
                '球头信息.球头基本信息',
                '内衬信息.内衬-基本信息',
                '体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置',
                '体外实验-球头与锥颈界面微动腐蚀实验.球头与锥颈-实验设置'
            ]
            
            shown_fields = 0
            for field in key_fields:
                value = rec.get(field)
                if value and value != 'null' and str(value).strip():
                    context += f"  - {field}: {str(value)[:100]}\n"
                    shown_fields += 1
            
            if shown_fields == 0:
                context += f"  - （记录中字段较少，可能还需补充）\n"
            
            context += "\n"
        
        if len(existing_records) > 3:
            context += f"...还有 {len(existing_records) - 3} 条更早的记录\n\n"
        
        return context
    
    def _parse_json(self, text: str) -> Dict:
        """
        解析JSON，处理常见的格式问题
        """
        # 去除markdown标记（更aggressive）
        text = re.sub(r'```json\s*\n?', '', text)
        text = re.sub(r'```\s*\n?', '', text)
        text = re.sub(r'^```.*?\n', '', text, flags=re.MULTILINE)
        text = text.strip()
        
        # 如果为空，返回空结果
        if not text:
            return {"records": []}
        
        try:
            # 尝试直接解析
            return json.loads(text)
        except json.JSONDecodeError as e:
            self.log_debug(f"JSON解析失败，尝试修复: {e}")
            
            # 先尝试简单修复：移除末尾的不完整部分
            try:
                # 找到最后一个完整的}
                last_brace = text.rfind('}')
                if last_brace > 0:
                    truncated = text[:last_brace + 1]
                    result = json.loads(truncated)
                    self.log_debug(f"通过截断修复成功")
                    return result
            except:
                pass
            # 如果失败，尝试找到第一个完整的JSON对象
            self.log_debug(f"JSON解析失败，尝试修复: {e}")
            
            # 查找第一个 { 和对应的 }
            start_idx = text.find('{')
            if start_idx == -1:
                self.log_error(f"未找到JSON对象起始")
                return {"records": []}
            
            # 找到匹配的右括号
            brace_count = 0
            end_idx = -1
            for i in range(start_idx, len(text)):
                if text[i] == '{':
                    brace_count += 1
                elif text[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_idx = i + 1
                        break
            
            if end_idx == -1:
                self.log_error(f"未找到JSON对象结束")
                # 尝试补全JSON
                json_str = text[start_idx:] + "}"
                try:
                    result = json.loads(json_str)
                    self.log_debug(f"通过补全{{}}修复成功")
                    return result
                except:
                    self.log_error(f"补全失败")
                    return {"records": []}
            
            # 提取第一个完整的JSON对象
            json_str = text[start_idx:end_idx]
            try:
                result = json.loads(json_str)
                self.log_debug(f"修复后解析成功")
                return result
            except json.JSONDecodeError as e2:
                self.log_error(f"修复后仍然失败: {e2}")
                self.log_debug(f"原始内容（前500字符）: {text[:500]}")
                return {"records": []}
    
    def _process_records(self, records: List[Dict]) -> List[Dict]:
        """处理记录"""
        processed = []
        for rec in records:
            if 'action' in rec and 'data' in rec:
                processed.append(rec)
            else:
                processed.append({"action": "new", "data": rec})
        return processed
    
    def _merge_records(self, existing: List[Dict], new_records: List[Dict]) -> List[Dict]:
        """
        智能合并记录 - 完全由LLM决定new还是enrich
        
        策略:
        1. action="enrich" + record_index: 更新指定记录的字段
        2. action="new": 添加新记录
        3. 更新规则:
           - null字段：直接更新
           - 非null字段：如果新值更详细（长度更长或包含更多信息），则合并
        """
        for rec in new_records:
            action = rec.get('action', 'new')
            data = rec.get('data', rec)
            
            if action == 'enrich' and 'record_index' in rec:
                # LLM指定完善某条记录
                idx = rec['record_index'] - 1
                
                if 0 <= idx < len(existing):
                    # 智能更新字段
                    updated_fields = []
                    merged_fields = []
                    
                    for key, new_value in data.items():
                        if not new_value or new_value == 'null' or str(new_value).strip() == '':
                            continue
                        
                        old_value = existing[idx].get(key)
                        
                        # 情况1: 旧值为null或空，直接更新
                        if not old_value or old_value == 'null' or str(old_value).strip() == '':
                            existing[idx][key] = new_value
                            updated_fields.append(key)
                        # 情况2: 新旧值都有内容且不同
                        elif old_value != new_value:
                            # 对于JSON字符串字段，尝试合并内容
                            if '.' in key:  # JSON字符串字段（如 "球头信息.球头基本信息"）
                                merged = self._merge_json_field_values(old_value, new_value)
                                if merged != old_value:
                                    existing[idx][key] = merged
                                    merged_fields.append(key)
                                    self.log_debug(f"      合并 {key}")
                            else:
                                # 基本字段（数据标识、应用部位等），保留旧值
                                self.log_debug(f"      保留 {key}: '{old_value}'")
                    
                    if updated_fields or merged_fields:
                        self.log_info(f"    ↻ 完善记录 {idx+1}: 新增{len(updated_fields)}字段, 合并{len(merged_fields)}字段")
                        if updated_fields:
                            self.log_debug(f"      新增: {', '.join(updated_fields[:3])}{'...' if len(updated_fields) > 3 else ''}")
                        if merged_fields:
                            self.log_debug(f"      合并: {', '.join(merged_fields[:3])}{'...' if len(merged_fields) > 3 else ''}")
                    else:
                        self.log_info(f"    ↻ 记录 {idx+1} 无新增信息")
                else:
                    self.log_warning(f"    ⚠️  record_index={rec['record_index']} 超出范围，改为新增")
                    existing.append(data)
            else:
                # 新记录
                existing.append(data)
                identifier = data.get('数据标识', 'Unknown')
                self.log_info(f"    + 新增记录: {identifier}")
        
        return existing
    
    def _merge_json_field_values(self, old_value: str, new_value: str) -> str:
        """
        合并JSON字符串字段的内容
        
        策略：
        1. 解析两个JSON字符串
        2. 合并键值对（新值优先，但如果旧值更详细则保留）
        3. 返回合并后的JSON字符串
        """
        try:
            # 尝试解析JSON字符串
            old_dict = json.loads(old_value) if isinstance(old_value, str) and old_value.startswith('{') else {}
            new_dict = json.loads(new_value) if isinstance(new_value, str) and new_value.startswith('{') else {}
            
            # 合并字典
            merged_dict = old_dict.copy()
            for key, val in new_dict.items():
                if key not in merged_dict or not merged_dict[key]:
                    # 新键或旧值为空，直接添加
                    merged_dict[key] = val
                elif len(str(val)) > len(str(merged_dict[key])):
                    # 新值更详细，更新
                    merged_dict[key] = val
                # 否则保留旧值
            
            # 返回JSON字符串
            return json.dumps(merged_dict, ensure_ascii=False)
        except:
            # 解析失败，返回更长的值
            return new_value if len(str(new_value)) > len(str(old_value)) else old_value
