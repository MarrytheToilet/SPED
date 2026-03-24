"""
两阶段骨架填充模式 - 先识别记录，再分块填充

输出规范：每条记录必须包含完整12表结构，没有数据的字段填null
"""
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
import json
import uuid
import hashlib
import random

from .base import ExtractionMode, ExtractionResult

import settings


def generate_data_id(
    paper_id: str, 
    record_index: int, 
    skeleton_info: Dict[str, Any] = None
) -> str:
    """
    生成唯一的数据ID - 确保同一论文中不同材料/处理的记录有唯一ID
    
    格式: SPED-{短哈希}-{序号}
    例如: SPED-a1b2c3d4-001
    
    Args:
        paper_id: 论文ID
        record_index: 记录索引（从0开始）
        skeleton_info: 骨架信息字典，包含identifier、material_name、treatment等
    
    Returns:
        唯一的数据ID字符串
    """
    # 组合唯一标识符的来源
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")
    
    # 从骨架信息中提取更多区分字段
    if skeleton_info:
        identifier = skeleton_info.get("identifier", "")
        material_name = skeleton_info.get("material_name", "")
        treatment = skeleton_info.get("treatment", "")
        key_features = skeleton_info.get("key_features", "")
        # 组合多个字段确保唯一性
        unique_str = f"{paper_id}_{timestamp}_{record_index}_{identifier}_{material_name}_{treatment}_{key_features}"
    else:
        unique_str = f"{paper_id}_{timestamp}_{record_index}"
    
    # 生成短哈希（8字符）
    hash_obj = hashlib.md5(unique_str.encode())
    short_hash = hash_obj.hexdigest()[:8]
    
    # 格式化序号（3位数字）
    seq = str(record_index + 1).zfill(3)
    
    return f"SPED-{short_hash}-{seq}"


def sample_long_paper(
    content: str,
    max_length: int = None,
    head_chars: int = None,
    sample_ratio: float = None,
    hard_limit: int = None,
    seed: int = None
) -> str:
    """
    对过长论文进行采样，保留开头部分 + 随机抽取剩余内容的一部分
    如果采样后仍超过硬截断阈值，则直接截断
    
    Args:
        content: 论文全文内容
        max_length: 触发采样的阈值（超过此长度才采样），默认从settings读取
        head_chars: 开头保留的字符数，默认从settings读取
        sample_ratio: 剩余内容的采样比例(0.0-1.0)，默认从settings读取
        hard_limit: 硬截断阈值（采样后仍超过则直接截断），默认从settings读取
        seed: 随机种子（用于可重复的采样）
    
    Returns:
        采样后的内容（如果原文不超长则返回原文）
    """
    # 从settings获取默认值
    if max_length is None:
        max_length = settings.SKELETON_MAX_LENGTH
    if head_chars is None:
        head_chars = settings.SKELETON_HEAD_CHARS
    if sample_ratio is None:
        sample_ratio = settings.SKELETON_SAMPLE_RATIO
    if hard_limit is None:
        hard_limit = settings.SKELETON_HARD_LIMIT
    
    # 如果内容不超长，直接返回
    if len(content) <= max_length:
        return content
    
    # 设置随机种子以确保可重复性
    if seed is not None:
        random.seed(seed)
    
    # 保留开头部分（包含摘要、引言等关键信息）
    head_part = content[:head_chars]
    remaining_part = content[head_chars:]
    
    # 将剩余部分按段落分割（以便保持语义完整性）
    # 使用双换行符作为段落分隔符
    paragraphs = remaining_part.split('\n\n')
    
    # 过滤掉空段落
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if not paragraphs:
        sampled_content = head_part
    else:
        # 计算需要抽取的段落数量
        sample_count = max(1, int(len(paragraphs) * sample_ratio))
        
        # 随机抽取段落（保持原有顺序）
        if sample_count < len(paragraphs):
            # 生成随机索引并排序以保持顺序
            sampled_indices = sorted(random.sample(range(len(paragraphs)), sample_count))
            sampled_paragraphs = [paragraphs[i] for i in sampled_indices]
        else:
            sampled_paragraphs = paragraphs
        
        # 组合结果
        sampled_content = head_part + "\n\n[...部分内容已采样...]\n\n" + "\n\n".join(sampled_paragraphs)
    
    # 如果采样后仍超过硬截断阈值，直接截断
    if len(sampled_content) > hard_limit:
        sampled_content = sampled_content[:hard_limit] + "\n\n[...内容已截断...]"
    
    return sampled_content


# 完整的12表结构模板
FULL_TABLE_TEMPLATE = {
    "Sheet1_基本信息表": {
        "数据ID": "${DATA_ID}",
        "应用部位": None,
        "产品所属专利号或文献": None,
        "来源文件": None,
        "论文标题": None,
        "论文DOI号": None,
        "论文ID": None
    },
    "Sheet2_内衬基本信息表": {
        "数据ID": "${DATA_ID}",
        "内衬材料类别": None,
        "内衬材料名称": None,
        "成型方式": None,
        "熔融温度": None,
        "成型压力": None,
        "保温时间": None,
        "碳纤维质量分数": None,
        "碳纤维长度": None,
        "碳纤维外径": None,
        "碳纳米管质量分数": None,
        "碳纳米管长度": None,
        "碳纳米管外径": None,
        "石墨烯质量分数": None,
        "石墨烯厚度": None,
        "石墨烯长度": None,
        "碳化硅质量分数": None,
        "内衬厚度(mm)": None,
        "内衬偏移(mm)": None,
        "内衬锁定机制": None,
        "内衬加工工艺": None,
        "内衬后处理": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet3_球头基本信息表": {
        "数据ID": "${DATA_ID}",
        "球头材料类别": None,
        "球头材料名称": None,
        "球头合金成分": None,
        "球头直径(mm)": None,
        "球头纹理": None,
        "球头加工工艺": None,
        "球头后处理": None,
        "球头晶粒尺寸": None,
        "球头晶粒取向": None,
        "球头相组成": None,
        "碳化物尺寸": None,
        "碳化物分布位置": None,
        "碳化物连续性": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet4_配合信息表": {
        "数据ID": "${DATA_ID}",
        "内衬-球头径向间隙(mm)": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet5_股骨柄基本信息表": {
        "数据ID": "${DATA_ID}",
        "股骨柄材料类别": None,
        "股骨柄材料名称": None,
        "锥度(°)": None,
        "锥颈尺寸": None,
        "颈长(mm)": None,
        "锥套设计": None,
        "锥度间隙(°)": None,
        "股骨柄颈干角(°)": None,
        "股骨柄偏心距(mm)": None,
        "股骨柄拓扑结构": None,
        "股骨柄孔隙率(%)": None,
        "股骨柄横截面": None,
        "柄体长度H(mm)": None,
        "股骨柄加工工艺": None,
        "股骨柄后处理": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet6_内衬物理性能表": {
        "数据ID": "${DATA_ID}",
        "内衬硬度(HV)": None,
        "内衬表面粗糙度(μm)": None,
        "内衬弹性模量(GPa)": None,
        "内衬杨氏模量": None,
        "内衬极限拉伸强度": None,
        "内衬弯曲强度": None,
        "内衬剪切强度": None,
        "内衬断裂韧性": None,
        "内衬抗压强度(MPa)": None,
        "内衬屈服强度(MPa)": None,
        "内衬密度(g/cm³)": None,
        "内衬泊松比": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet7_球头物理性能表": {
        "数据ID": "${DATA_ID}",
        "球头硬度(HV)": None,
        "球头表面粗糙度(nm)": None,
        "弹性模量(GPa)": None,
        "球头抗压强度(MPa)": None,
        "球头屈服强度(MPa)": None,
        "球头断裂伸长率": None,
        "球头密度(g/cm³)": None,
        "球头泊松比": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet8_股骨柄物理性能表": {
        "数据ID": "${DATA_ID}",
        "股骨柄硬度(HV)": None,
        "股骨柄表面粗糙度(μm)": None,
        "股骨柄弹性模量(GPa)": None,
        "股骨柄抗压强度(MPa)": None,
        "股骨柄屈服强度(MPa)": None,
        "股骨柄密度(g/cm³)": None,
        "股骨柄泊松比": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet9_实验参数": {
        "数据ID": "${DATA_ID}",
        "实验器材": None,
        "滑动距离": None,
        "频率": None,
        "摩擦时间": None,
        "载荷": None,
        "实验温度": None,
        "润滑液类型": None,
        "蛋白质浓度": None,
        "润滑液pH": None,
        "接触载荷": None,
        "运动模式": None,
        "速率": None,
        "接触方式": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet10_性能测试结果表": {
        "数据ID": "${DATA_ID}",
        "内衬相含量变化": None,
        "累计磨损量": None,
        "磨损率": None,
        "摩擦系数": None,
        "腐蚀速率": None,
        "离子释放量": None,
        "磨损颗粒大小": None,
        "磨损颗粒形貌": None,
        "摩擦膜组成": None,
        "摩擦膜厚度": None,
        "抗疲劳性": None,
        "接触应力": None,
        "Von Mises应力": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet11_计算模拟参数表": {
        "数据ID": "${DATA_ID}",
        "计算建模软件": None,
        "计算建模输入参数": None,
        "计算建模输出参数": None,
        "来源文件": None,
        "论文ID": None
    },
    "Sheet12_计算模拟图像表": {
        "数据ID": "${DATA_ID}",
        "计算建模模拟结构图": None,
        "计算建模模拟结构图说明": None,
        "来源文件": None,
        "论文ID": None
    }
}


class SkeletonFillMode(ExtractionMode):
    """
    两阶段骨架填充模式
    
    流程：
    阶段1 (Skeleton): 使用全文识别记录骨架
    阶段2 (Chunk Fill): 遍历所有chunk，填充详细数据
    
    输出：每条记录包含完整12表结构，没有数据的字段为null
    """
    
    @property
    def mode_name(self) -> str:
        return "skeleton_fill"
    
    def extract(
        self,
        paper_id: str,
        content: str,
        chunks: List[str] = None,
        **kwargs
    ) -> ExtractionResult:
        """执行两阶段提取"""
        self.logger.info(f"开始两阶段提取: {paper_id}")
        
        # ====== 阶段1: 骨架提取 ======
        self.logger.info("阶段1: 骨架提取")
        
        skeleton_result = self._extract_skeleton(paper_id, content)
        if not skeleton_result["success"]:
            return ExtractionResult(
                success=False,
                error=f"骨架提取失败: {skeleton_result['error']}",
                metadata={"mode": self.mode_name, "phase": "skeleton"}
            )
        
        skeleton_data = skeleton_result["data"]
        record_count = skeleton_data.get("record_count", 0)
        skeleton_records = skeleton_data.get("records", [])
        
        # 诊断日志：检查数据完整性
        paper_info = skeleton_data.get("paper_info", {})
        application = paper_info.get("application", "未知")
        actual_records_count = len(skeleton_records)
        
        self.logger.info(f"骨架提取完成: 识别 {record_count} 条记录, 实际records数组长度={actual_records_count}, application={application}")
        
        # 警告：record_count 与实际 records 数组长度不匹配
        if record_count != actual_records_count:
            self.logger.warning(
                f"[{paper_id}] record_count({record_count}) != len(records)({actual_records_count}), "
                f"可能导致数据丢失"
            )
        
        # 诊断：如果 record_count 为 0，记录 skeleton_data 的结构
        if record_count == 0:
            self.logger.info(
                f"[{paper_id}] record_count=0 诊断: "
                f"skeleton_data keys={list(skeleton_data.keys())}, "
                f"paper_info={paper_info}"
            )
        
        if record_count == 0:
            return ExtractionResult(
                success=True,
                records=[],
                count=0,
                metadata={
                    "mode": self.mode_name,
                    "paper_id": paper_id,
                    "strategy": "skeleton_fill_no_records"
                }
            )
        
        # 初始化记录
        records = self._init_records_from_skeleton(skeleton_records)
        
        # ====== 阶段2: 分块填充 ======
        if chunks and record_count > 0:
            self.logger.info(f"阶段2: 分块填充 ({len(chunks)} 个chunks)")
            
            paper_info = skeleton_data.get("paper_info", {})
            skeleton_json = {
                "paper_title": paper_info.get("title", ""),
                "paper_doi": paper_info.get("doi", ""),
                "application": paper_info.get("application", ""),
                "record_count": record_count,
                "records": skeleton_records
            }
            
            for i, chunk in enumerate(chunks):
                # 支持 DocumentChunk 对象或字符串
                chunk_text = chunk.content if hasattr(chunk, 'content') else str(chunk)
                
                self._fill_chunk(
                    paper_id=paper_id,
                    chunk_text=chunk_text,
                    chunk_index=i,
                    total_chunks=len(chunks),
                    skeleton_json=skeleton_json,
                    records=records,
                )
        
        # 清理内部字段并生成唯一数据ID
        for i, record in enumerate(records):
            # 收集骨架信息用于生成唯一ID
            skeleton_info = {
                "identifier": record.get("_skeleton", ""),
                "material_name": record.get("material_name", ""),
                "treatment": record.get("treatment", ""),
                "key_features": record.get("key_features", ""),
                "application": record.get("application", ""),
            }
            
            # 生成唯一数据ID - 使用完整骨架信息确保唯一性
            data_id = generate_data_id(paper_id, i, skeleton_info)
            
            # 将数据ID填入所有12张表的"数据ID"字段
            for table_name in record:
                if table_name.startswith("Sheet") and isinstance(record[table_name], dict):
                    if "数据ID" in record[table_name]:
                        record[table_name]["数据ID"] = data_id
            
            # 清理内部追踪字段
            record.pop("_index", None)
            record.pop("_skeleton", None)
        
        return ExtractionResult(
            success=True,
            records=records,
            count=len(records),
            metadata={
                "mode": self.mode_name,
                "paper_id": paper_id,
                "strategy": "two_phase_skeleton_fill",
                "extraction_time": datetime.now().isoformat(),
                "skeleton_record_count": record_count,
                "total_chunks": len(chunks) if chunks else 0,
            }
        )
    
    def _extract_skeleton(self, paper_id: str, content: str) -> Dict[str, Any]:
        """
        提取骨架
        
        对于过长论文，采用"开头保留 + 随机抽样"策略，减少token消耗同时保留关键信息
        """
        original_length = len(content)
        
        # 对长论文进行采样（使用paper_id的hash作为seed确保同一论文采样结果一致）
        seed = int(hashlib.md5(paper_id.encode()).hexdigest()[:8], 16)
        sampled_content = sample_long_paper(content, seed=seed)
        
        sampled_length = len(sampled_content)
        if sampled_length < original_length:
            truncated = "[...内容已截断...]" in sampled_content
            self.logger.info(
                f"长论文处理: {original_length} -> {sampled_length} 字符 "
                f"(开头{settings.SKELETON_HEAD_CHARS}字符 + "
                f"随机抽取{settings.SKELETON_SAMPLE_RATIO*100:.0f}%"
                f"{' + 硬截断' if truncated else ''})"
            )
        
        assembled = self.prompt_assembler.assemble_skeleton_mode(
            paper_text=sampled_content,
            paper_id=paper_id,
        )
        
        self.logger.debug(f"骨架Prompt: {len(assembled.full_prompt)} 字符")
        
        return self._call_llm(
            system_prompt=assembled.system_prompt,
            user_prompt=assembled.user_prompt,
            call_id=f"{paper_id}_skeleton",
        )
    
    def _init_records_from_skeleton(self, skeleton_records: List[Dict]) -> List[Dict]:
        """
        从骨架初始化记录，包含完整12表结构
        
        每条记录都会预先初始化所有12张表，所有字段默认为null
        """
        import copy
        
        records = []
        for i, skel in enumerate(skeleton_records):
            # 以完整12表模板为基础
            record = copy.deepcopy(FULL_TABLE_TEMPLATE)
            
            # 添加内部追踪字段
            record["_index"] = i
            record["_skeleton"] = skel.get("name", f"Record_{i}")
            
            # 保留骨架中的基本信息（用于记录识别）
            record["component"] = skel.get("component", "")
            record["material_type"] = skel.get("category", "")
            record["material_name"] = skel.get("material", "")
            record["treatment"] = skel.get("treatment", "")
            record["description"] = skel.get("description", "")
            
            records.append(record)
        
        return records
    
    def _fill_chunk(
        self,
        paper_id: str,
        chunk_text: str,
        chunk_index: int,
        total_chunks: int,
        skeleton_json: Dict,
        records: List[Dict],
    ):
        """填充单个chunk"""
        self.logger.debug(f"处理 chunk {chunk_index + 1}/{total_chunks}")
        
        assembled = self.prompt_assembler.assemble_chunk_fill_mode(
            chunk_text=chunk_text,
            skeleton_json=skeleton_json,
            chunk_index=chunk_index,
            total_chunks=total_chunks,
            paper_id=paper_id,
        )
        
        result = self._call_llm(
            system_prompt=assembled.system_prompt,
            user_prompt=assembled.user_prompt,
            call_id=f"{paper_id}_fill_{chunk_index}",
        )
        
        if not result["success"]:
            self.logger.warning(f"Chunk {chunk_index + 1} 填充失败: {result['error']}")
            return
        
        # 合并更新
        fill_data = result["data"]
        
        # 检查是否无相关数据
        if fill_data.get("no_relevant_data", False):
            self.logger.debug(f"Chunk {chunk_index + 1} 无相关数据")
            return
        
        # extractions数组格式
        extractions = fill_data.get("extractions", [])
        for extraction in extractions:
            record_id = extraction.get("record_id")
            fields = extraction.get("fields", {})
            
            if record_id is not None and 0 <= record_id < len(records):
                self._merge_fields(records[record_id], fields)
        
        self.logger.debug(f"Chunk {chunk_index + 1} 完成，更新了 {len(extractions)} 条记录")
    
    def _merge_fields(self, record: Dict, fields: Dict):
        """
        合并字段到记录（递归合并嵌套字典）
        
        只更新非null值，保留已有数据
        """
        for table_name, table_fields in fields.items():
            # 跳过空值
            if table_fields is None or table_fields == "" or table_fields == []:
                continue
            
            # 跳过非表字段
            if not table_name.startswith("Sheet"):
                continue
            
            if not isinstance(table_fields, dict):
                continue
            
            # 确保记录中有该表
            if table_name not in record:
                record[table_name] = {}
            
            # 合并表内字段
            for field_name, field_value in table_fields.items():
                # 跳过空值
                if field_value is None or field_value == "" or field_value == []:
                    continue
                
                # 跳过占位符
                if field_value == "${DATA_ID}":
                    continue
                
                # 更新字段：如果现有值为空或为null，则更新
                existing_value = record[table_name].get(field_name)
                if existing_value is None or existing_value == "${DATA_ID}":
                    record[table_name][field_name] = field_value
                elif isinstance(existing_value, list) and isinstance(field_value, list):
                    record[table_name][field_name] = list(set(existing_value + field_value))
