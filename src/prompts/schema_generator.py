"""
Schema驱动的Prompt生成器

从增强版schema.json自动生成：
1. 字段定义文本（用于system prompt）
2. 完整输出示例（用于few-shot）
3. 字段提取提示（用于user prompt）
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass


@dataclass
class GeneratedPromptParts:
    """生成的Prompt组件"""
    field_definitions: str      # 字段定义文本
    output_example: str         # 完整输出示例JSON
    extraction_hints: str       # 提取提示
    validation_rules: str       # 验证规则说明
    

class SchemaPromptGenerator:
    """
    Schema驱动的Prompt生成器
    
    从增强版schema自动生成prompt片段，确保prompt与schema定义一致
    """
    
    def __init__(self, schema_path: Path = None):
        """
        初始化生成器
        
        Args:
            schema_path: schema.json路径，默认使用data_schema/schema.json
        """
        if schema_path is None:
            project_root = Path(__file__).parent.parent.parent
            schema_path = project_root / "data_schema" / "schema.json"
        
        self.schema_path = schema_path
        self.schema: Dict[str, Any] = {}
        self._load_schema()
    
    def _load_schema(self):
        """加载schema文件"""
        if self.schema_path.exists():
            with open(self.schema_path, 'r', encoding='utf-8') as f:
                self.schema = json.load(f)
        else:
            raise FileNotFoundError(f"Schema文件不存在: {self.schema_path}")
    
    def generate_all(self) -> GeneratedPromptParts:
        """生成所有Prompt组件"""
        return GeneratedPromptParts(
            field_definitions=self.generate_field_definitions(),
            output_example=self.generate_complete_example(),
            extraction_hints=self.generate_extraction_hints(),
            validation_rules=self.generate_validation_rules()
        )
    
    def generate_field_definitions(self) -> str:
        """
        生成字段定义文本
        
        格式：
        ## Sheet1_基本信息表
        | 字段 | 说明 | 示例 |
        |------|------|------|
        | 应用部位 | 人工关节的应用部位 | 髋关节, 膝关节 |
        ...
        """
        lines = ["# 数据库Schema字段定义\n"]
        lines.append("> 以下是12张表的完整字段定义，提取时必须严格遵守。\n")
        
        for table in self.schema.get("tables", []):
            table_name = table.get("table_name", "")
            description = table.get("description", "")
            
            lines.append(f"\n## {table_name}")
            lines.append(f"*{description}*\n")
            lines.append("| 字段 | 说明 | 示例值 |")
            lines.append("|------|------|--------|")
            
            for col in table.get("columns", []):
                name = col.get("name", "")
                desc = col.get("description", "")
                examples = col.get("examples", [])
                
                # 格式化示例
                if examples:
                    example_str = ", ".join([
                        str(e) if e is not None else "null" 
                        for e in examples[:3]
                    ])
                else:
                    example_str = "-"
                
                # 截断过长的描述
                if len(desc) > 50:
                    desc = desc[:47] + "..."
                
                lines.append(f"| {name} | {desc} | {example_str} |")
        
        return "\n".join(lines)
    
    def generate_extraction_hints(self) -> str:
        """
        生成提取提示汇总
        
        按表分组的关键字段提取提示
        """
        lines = ["# 关键字段提取提示\n"]
        
        for table in self.schema.get("tables", []):
            table_name = table.get("table_name", "")
            hints = []
            
            for col in table.get("columns", []):
                hint = col.get("extraction_hint", "")
                if hint:
                    name = col.get("name", "")
                    hints.append(f"- **{name}**: {hint}")
            
            if hints:
                lines.append(f"\n## {table_name}")
                lines.extend(hints)
        
        return "\n".join(lines)
    
    def generate_complete_example(self) -> str:
        """
        从complete_examples.json读取完整输出示例
        
        用于few-shot learning，确保示例字段丰富且格式正确
        """
        # 优先从complete_examples.json读取
        project_root = Path(__file__).parent.parent.parent
        examples_path = project_root / "prompts" / "examples" / "complete_examples.json"
        
        if examples_path.exists():
            try:
                with open(examples_path, 'r', encoding='utf-8') as f:
                    examples_data = json.load(f)
                
                # 获取第一个示例的output
                examples = examples_data.get("examples", [])
                if examples and "output" in examples[0]:
                    return json.dumps(examples[0]["output"], ensure_ascii=False, indent=2)
            except Exception as e:
                pass  # 回退到从schema生成
        
        # 回退：从schema生成示例
        example_record = {}
        
        for table in self.schema.get("tables", []):
            table_name = table.get("table_name", "")
            table_data = {}
            
            for col in table.get("columns", []):
                name = col.get("name", "")
                examples = col.get("examples", [])
                
                # 选择第一个非null的示例，如果都是null则用null
                value = None
                for ex in examples:
                    if ex is not None:
                        value = ex
                        break
                
                table_data[name] = value
            
            example_record[table_name] = table_data
        
        output = {
            "records": [example_record],
            "count": 1,
            "paper_title": "Tribological behavior of carbon nanotube reinforced UHMWPE composites",
            "paper_doi": "10.1016/j.wear.2023.204896"
        }
        
        return json.dumps(output, ensure_ascii=False, indent=2)
    
    def generate_validation_rules(self) -> str:
        """
        生成验证规则说明
        """
        lines = ["# 数据验证规则\n"]
        
        # 全局规则
        golden_rules = self.schema.get("extraction_rules", {}).get("golden_rules", [])
        if golden_rules:
            lines.append("## 五大黄金规则")
            for i, rule in enumerate(golden_rules, 1):
                lines.append(f"{i}. {rule}")
            lines.append("")
        
        # DOI规则
        doi_rules = self.schema.get("extraction_rules", {}).get("doi_extraction", {})
        if doi_rules:
            lines.append("## DOI提取规则")
            lines.append(f"- 格式: {doi_rules.get('format', '')}")
            lines.append(f"- 常见位置: {', '.join(doi_rules.get('locations', []))}")
            ocr_fixes = doi_rules.get('ocr_fixes', {})
            if ocr_fixes:
                lines.append(f"- OCR修正: {ocr_fixes}")
            lines.append("")
        
        # 枚举值约束
        lines.append("## 枚举值约束")
        for table in self.schema.get("tables", []):
            for col in table.get("columns", []):
                enum_values = col.get("enum_values", [])
                if enum_values:
                    name = col.get("name", "")
                    lines.append(f"- **{name}**: {', '.join(enum_values)}")
        
        return "\n".join(lines)
    
    def generate_table_prompt(self, table_name: str) -> str:
        """
        生成单个表的详细提取prompt
        
        Args:
            table_name: 表名，如 "Sheet2_内衬基本信息表"
        """
        for table in self.schema.get("tables", []):
            if table.get("table_name") == table_name:
                lines = [f"# {table_name} 提取指南\n"]
                lines.append(f"*{table.get('description', '')}*\n")
                
                for col in table.get("columns", []):
                    name = col.get("name", "")
                    desc = col.get("description", "")
                    hint = col.get("extraction_hint", "")
                    examples = col.get("examples", [])
                    mapping = col.get("material_mapping", col.get("equipment_mapping", col.get("treatment_mapping", {})))
                    
                    lines.append(f"\n### {name}")
                    if desc:
                        lines.append(f"- 说明: {desc}")
                    if hint:
                        lines.append(f"- 提取提示: {hint}")
                    if examples:
                        examples_str = ", ".join([str(e) if e is not None else "null" for e in examples])
                        lines.append(f"- 示例: {examples_str}")
                    if mapping:
                        lines.append(f"- 对照表:")
                        for k, v in list(mapping.items())[:5]:
                            lines.append(f"  - {k} → {v}")
                
                return "\n".join(lines)
        
        return f"未找到表: {table_name}"
    
    def get_material_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        获取所有材料/设备/处理的映射表
        
        Returns:
            {field_name: {english: chinese}}
        """
        mappings = {}
        
        for table in self.schema.get("tables", []):
            for col in table.get("columns", []):
                for mapping_key in ["material_mapping", "equipment_mapping", "treatment_mapping"]:
                    mapping = col.get(mapping_key, {})
                    if mapping:
                        field_name = col.get("name", "")
                        mappings[field_name] = mapping
        
        return mappings


def main():
    """测试生成器"""
    generator = SchemaPromptGenerator()
    parts = generator.generate_all()
    
    print("=" * 60)
    print("字段定义（前500字符）:")
    print("=" * 60)
    print(parts.field_definitions[:500])
    
    print("\n" + "=" * 60)
    print("提取提示（前500字符）:")
    print("=" * 60)
    print(parts.extraction_hints[:500])
    
    print("\n" + "=" * 60)
    print("完整示例（前1000字符）:")
    print("=" * 60)
    print(parts.output_example[:1000])
    
    print("\n" + "=" * 60)
    print("验证规则:")
    print("=" * 60)
    print(parts.validation_rules)


if __name__ == "__main__":
    main()
