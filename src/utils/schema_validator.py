"""
Schema验证器 - 验证LLM提取结果是否符合schema定义

功能：
1. 验证JSON结构完整性
2. 验证必填字段
3. 验证数据格式（DOI、图片路径等）
4. 生成验证报告
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from loguru import logger


@dataclass
class ValidationError:
    """验证错误"""
    field: str
    table: str
    error_type: str  # missing, invalid_format, invalid_value, type_error
    message: str
    value: Any = None
    
    def __str__(self):
        return f"[{self.table}] {self.field}: {self.message}"


@dataclass
class ValidationResult:
    """验证结果"""
    is_valid: bool
    errors: List[ValidationError] = field(default_factory=list)
    warnings: List[ValidationError] = field(default_factory=list)
    record_count: int = 0
    validated_tables: int = 0
    
    def add_error(self, error: ValidationError):
        self.errors.append(error)
        self.is_valid = False
    
    def add_warning(self, warning: ValidationError):
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "is_valid": self.is_valid,
            "error_count": len(self.errors),
            "warning_count": len(self.warnings),
            "record_count": self.record_count,
            "validated_tables": self.validated_tables,
            "errors": [str(e) for e in self.errors],
            "warnings": [str(w) for w in self.warnings],
        }
    
    def summary(self) -> str:
        """生成简要报告"""
        lines = [
            f"验证结果: {'✅ 通过' if self.is_valid else '❌ 失败'}",
            f"  记录数: {self.record_count}",
            f"  验证表数: {self.validated_tables}",
            f"  错误数: {len(self.errors)}",
            f"  警告数: {len(self.warnings)}",
        ]
        
        if self.errors:
            lines.append("\n主要错误:")
            for err in self.errors[:5]:
                lines.append(f"  - {err}")
            if len(self.errors) > 5:
                lines.append(f"  ... 还有 {len(self.errors) - 5} 个错误")
        
        return "\n".join(lines)


class SchemaValidator:
    """
    Schema验证器
    
    用于验证LLM提取结果是否符合schema定义
    """
    
    # 12张表名
    REQUIRED_TABLES = [
        "Sheet1_基本信息表",
        "Sheet2_内衬基本信息表",
        "Sheet3_球头基本信息表",
        "Sheet4_配合信息表",
        "Sheet5_股骨柄基本信息表",
        "Sheet6_内衬物理性能表",
        "Sheet7_球头物理性能表",
        "Sheet8_股骨柄物理性能表",
        "Sheet9_实验参数",
        "Sheet10_性能测试结果表",
        "Sheet11_计算模拟参数表",
        "Sheet12_计算模拟图像表",
    ]
    
    # 每张表的必填字段
    REQUIRED_FIELDS = {
        "Sheet1_基本信息表": ["数据ID"],
        "Sheet2_内衬基本信息表": ["数据ID"],
        "Sheet3_球头基本信息表": ["数据ID"],
        "Sheet4_配合信息表": ["数据ID"],
        "Sheet5_股骨柄基本信息表": ["数据ID"],
        "Sheet6_内衬物理性能表": ["数据ID"],
        "Sheet7_球头物理性能表": ["数据ID"],
        "Sheet8_股骨柄物理性能表": ["数据ID"],
        "Sheet9_实验参数": ["数据ID"],
        "Sheet10_性能测试结果表": ["数据ID"],
        "Sheet11_计算模拟参数表": ["数据ID"],
        "Sheet12_计算模拟图像表": ["数据ID"],
    }
    
    # DOI格式正则
    DOI_PATTERN = re.compile(r'^10\.[0-9]{4,}/[^\s]+$')
    
    # 图片路径格式正则
    IMAGE_PATH_PATTERN = re.compile(r'^images/[a-zA-Z0-9_.-]+\.(jpg|jpeg|png|gif)$', re.IGNORECASE)
    
    # 枚举值约束
    ENUM_CONSTRAINTS = {
        "应用部位": ["髋关节", "膝关节", "肩关节", "踝关节", "肘关节", "指关节"],
        "内衬材料类别": ["高分子聚合物", "陶瓷", "金属", "复合材料"],
        "球头材料类别": ["金属", "陶瓷", "复合材料"],
        "股骨柄材料类别": ["金属", "复合材料"],
    }
    
    def __init__(self, schema_path: Path = None):
        """
        初始化验证器
        
        Args:
            schema_path: schema文件路径（可选，用于加载额外约束）
        """
        self.logger = logger.bind(module="SchemaValidator")
        self.schema: Dict[str, Any] = {}
        
        if schema_path and schema_path.exists():
            self._load_schema(schema_path)
    
    def _load_schema(self, schema_path: Path):
        """加载schema文件"""
        try:
            with open(schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
            self.logger.debug(f"加载schema: {schema_path}")
        except Exception as e:
            self.logger.warning(f"加载schema失败: {e}")
    
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """
        验证提取结果
        
        Args:
            data: LLM返回的JSON数据，格式为:
                  {"records": [...], "paper_info": {...}, ...}
                  或 {"records": [...]}
        
        Returns:
            ValidationResult
        """
        result = ValidationResult(is_valid=True)
        
        # 检查基本结构
        if not isinstance(data, dict):
            result.add_error(ValidationError(
                field="root",
                table="",
                error_type="type_error",
                message="数据必须是字典类型",
                value=type(data).__name__
            ))
            return result
        
        # 检查records字段
        records = data.get("records", [])
        if not isinstance(records, list):
            result.add_error(ValidationError(
                field="records",
                table="",
                error_type="type_error",
                message="records必须是列表类型",
                value=type(records).__name__
            ))
            return result
        
        if not records:
            result.add_warning(ValidationError(
                field="records",
                table="",
                error_type="missing",
                message="records为空，没有提取到任何记录"
            ))
            return result
        
        result.record_count = len(records)
        
        # 验证每条记录
        for i, record in enumerate(records):
            self._validate_record(record, i, result)
        
        return result
    
    def _validate_record(self, record: Dict[str, Any], index: int, result: ValidationResult):
        """验证单条记录"""
        if not isinstance(record, dict):
            result.add_error(ValidationError(
                field=f"records[{index}]",
                table="",
                error_type="type_error",
                message="记录必须是字典类型"
            ))
            return
        
        # 检查是否包含所有必需的表
        for table_name in self.REQUIRED_TABLES:
            if table_name not in record:
                result.add_warning(ValidationError(
                    field=f"records[{index}]",
                    table=table_name,
                    error_type="missing",
                    message=f"缺少表: {table_name}"
                ))
            else:
                result.validated_tables += 1
                table_data = record[table_name]
                
                if table_data is None:
                    # 表数据为null是允许的
                    continue
                
                if not isinstance(table_data, dict):
                    result.add_error(ValidationError(
                        field=f"records[{index}].{table_name}",
                        table=table_name,
                        error_type="type_error",
                        message="表数据必须是字典或null"
                    ))
                    continue
                
                # 验证必填字段
                self._validate_required_fields(table_name, table_data, index, result)
                
                # 验证特定字段格式
                self._validate_field_formats(table_name, table_data, index, result)
    
    def _validate_required_fields(
        self, 
        table_name: str, 
        table_data: Dict[str, Any], 
        record_index: int,
        result: ValidationResult
    ):
        """验证必填字段"""
        required_fields = self.REQUIRED_FIELDS.get(table_name, [])
        
        for field_name in required_fields:
            if field_name not in table_data:
                result.add_error(ValidationError(
                    field=field_name,
                    table=table_name,
                    error_type="missing",
                    message=f"缺少必填字段: {field_name}"
                ))
            elif table_data[field_name] is None:
                result.add_error(ValidationError(
                    field=field_name,
                    table=table_name,
                    error_type="invalid_value",
                    message=f"必填字段 {field_name} 不能为null"
                ))
    
    def _validate_field_formats(
        self, 
        table_name: str, 
        table_data: Dict[str, Any],
        record_index: int,
        result: ValidationResult
    ):
        """验证特定字段的格式"""
        
        # 验证DOI格式
        if table_name == "Sheet1_基本信息表":
            doi = table_data.get("论文DOI号")
            if doi is not None and doi != "":
                if not self.DOI_PATTERN.match(doi):
                    result.add_warning(ValidationError(
                        field="论文DOI号",
                        table=table_name,
                        error_type="invalid_format",
                        message=f"DOI格式不正确，应以10.开头: {doi}",
                        value=doi
                    ))
        
        # 验证图片路径格式
        if table_name == "Sheet12_计算模拟图像表":
            image_path = table_data.get("计算建模模拟结构图")
            if image_path is not None and image_path != "":
                if not self.IMAGE_PATH_PATTERN.match(image_path):
                    result.add_warning(ValidationError(
                        field="计算建模模拟结构图",
                        table=table_name,
                        error_type="invalid_format",
                        message=f"图片路径格式不正确，应为images/xxx.jpg: {image_path}",
                        value=image_path
                    ))
        
        # 验证枚举值
        for field_name, allowed_values in self.ENUM_CONSTRAINTS.items():
            if field_name in table_data:
                value = table_data[field_name]
                if value is not None and value not in allowed_values:
                    result.add_warning(ValidationError(
                        field=field_name,
                        table=table_name,
                        error_type="invalid_value",
                        message=f"值 '{value}' 不在允许的枚举列表中: {allowed_values}",
                        value=value
                    ))
    
    def validate_json_string(self, json_str: str) -> Tuple[ValidationResult, Optional[Dict]]:
        """
        验证JSON字符串
        
        Args:
            json_str: JSON字符串
        
        Returns:
            (ValidationResult, 解析后的数据或None)
        """
        result = ValidationResult(is_valid=True)
        
        # 尝试解析JSON
        try:
            # 清理可能的markdown代码块标记
            cleaned = json_str.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]
            if cleaned.startswith("```"):
                cleaned = cleaned[3:]
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            data = json.loads(cleaned)
            
        except json.JSONDecodeError as e:
            result.add_error(ValidationError(
                field="json",
                table="",
                error_type="invalid_format",
                message=f"JSON解析失败: {e}",
                value=json_str[:100]
            ))
            return result, None
        
        # 验证数据
        result = self.validate(data)
        return result, data


def validate_extraction_result(data: Dict[str, Any]) -> ValidationResult:
    """
    便捷函数：验证提取结果
    
    Args:
        data: LLM提取的数据
    
    Returns:
        ValidationResult
    """
    validator = SchemaValidator()
    return validator.validate(data)


def main():
    """测试验证器"""
    # 测试数据
    test_data = {
        "paper_info": {
            "title": "Test Paper",
            "doi": "10.1016/j.wear.2023.204896"
        },
        "record_count": 1,
        "records": [
            {
                "Sheet1_基本信息表": {
                    "数据ID": "${DATA_ID}",
                    "应用部位": "髋关节",
                    "论文标题": "Test Paper",
                    "论文DOI号": "10.1016/j.wear.2023.204896",
                    "来源文件": None,
                    "论文ID": None
                },
                "Sheet2_内衬基本信息表": {
                    "数据ID": "${DATA_ID}",
                    "内衬材料类别": "高分子聚合物",
                    "内衬材料名称": "UHMWPE"
                },
                "Sheet3_球头基本信息表": {"数据ID": "${DATA_ID}"},
                "Sheet4_配合信息表": {"数据ID": "${DATA_ID}"},
                "Sheet5_股骨柄基本信息表": {"数据ID": "${DATA_ID}"},
                "Sheet6_内衬物理性能表": {"数据ID": "${DATA_ID}"},
                "Sheet7_球头物理性能表": {"数据ID": "${DATA_ID}"},
                "Sheet8_股骨柄物理性能表": {"数据ID": "${DATA_ID}"},
                "Sheet9_实验参数": {"数据ID": "${DATA_ID}"},
                "Sheet10_性能测试结果表": {"数据ID": "${DATA_ID}"},
                "Sheet11_计算模拟参数表": {"数据ID": "${DATA_ID}"},
                "Sheet12_计算模拟图像表": {"数据ID": "${DATA_ID}"}
            }
        ]
    }
    
    validator = SchemaValidator()
    result = validator.validate(test_data)
    
    print(result.summary())
    print()
    print("详细结果:", result.to_dict())


if __name__ == "__main__":
    main()
