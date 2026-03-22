"""
Prompt组装器 - 负责将各部件组合成完整的Prompt

职责：
1. 加载和管理Prompt模板（3种模式）
2. 组合模板 + 文章内容
3. 根据不同模式生成不同格式的Prompt

模式：
- full: 全量提取模式
- skeleton: 骨架识别模式（两阶段第一阶段）
- chunk_fill: 分块填充模式（两阶段第二阶段）
"""
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
from loguru import logger


@dataclass
class AssembledPrompt:
    """组装后的Prompt"""
    system_prompt: str
    user_prompt: str
    mode: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def full_prompt(self) -> str:
        """完整的prompt文本（用于日志）"""
        return f"{self.system_prompt}\n\n---\n\n{self.user_prompt}"
    
    def to_messages(self) -> List[Dict[str, str]]:
        """转换为消息格式"""
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": self.user_prompt},
        ]


class PromptAssembler:
    """
    Prompt组装器
    
    使用三个标准模板：
    - prompts/system_prompt.md: 系统提示（规则+Schema）
    - prompts/modes/full_mode.md: 全量提取用户提示
    - prompts/modes/skeleton_mode.md: 骨架识别用户提示
    - prompts/modes/chunk_fill_mode.md: 分块填充用户提示
    """
    
    def __init__(
        self,
        template_dir: Path = None,
        schema_path: Path = None,
    ):
        self.logger = logger.bind(module="PromptAssembler")
        
        # 确定路径
        project_root = Path(__file__).parent.parent.parent
        self.template_dir = template_dir or project_root / "prompts"
        self.schema_path = schema_path or project_root / "data_schema" / "schema.json"
        
        # 加载资源
        self._system_prompt: str = ""
        self._full_template: str = ""
        self._skeleton_template: str = ""
        self._chunk_fill_template: str = ""
        self._output_example: str = ""
        
        self._load_templates()
        
        self.logger.info(f"初始化完成: system={len(self._system_prompt)}, full={len(self._full_template)}, skeleton={len(self._skeleton_template)}, chunk_fill={len(self._chunk_fill_template)}")
    
    def _load_templates(self):
        """加载所有模板文件"""
        # 系统提示
        system_path = self.template_dir / "system_prompt.md"
        if system_path.exists():
            self._system_prompt = system_path.read_text(encoding="utf-8")
        else:
            self._system_prompt = self._get_default_system_prompt()
            self.logger.warning("未找到system_prompt.md，使用默认值")
        
        # 全量模式
        full_path = self.template_dir / "modes" / "full_mode.md"
        if full_path.exists():
            self._full_template = full_path.read_text(encoding="utf-8")
        else:
            self._full_template = self._get_default_full_template()
            self.logger.warning("未找到full_mode.md，使用默认值")
        
        # 骨架模式
        skeleton_path = self.template_dir / "modes" / "skeleton_mode.md"
        if skeleton_path.exists():
            self._skeleton_template = skeleton_path.read_text(encoding="utf-8")
        else:
            self._skeleton_template = self._get_default_skeleton_template()
            self.logger.warning("未找到skeleton_mode.md，使用默认值")
        
        # 分块填充模式
        chunk_fill_path = self.template_dir / "modes" / "chunk_fill_mode.md"
        if chunk_fill_path.exists():
            self._chunk_fill_template = chunk_fill_path.read_text(encoding="utf-8")
        else:
            self._chunk_fill_template = self._get_default_chunk_fill_template()
            self.logger.warning("未找到chunk_fill_mode.md，使用默认值")
        
        # 输出示例
        example_path = self.template_dir / "examples" / "full_output.json"
        if example_path.exists():
            self._output_example = example_path.read_text(encoding="utf-8")
        
        self.logger.debug(f"加载模板完成")
    
    def assemble_full_mode(
        self,
        paper_text: str,
        paper_id: str = "unknown",
    ) -> AssembledPrompt:
        """
        组装全量模式Prompt
        
        system: 系统提示（规则+Schema）
        user: 全量模式模板 + 论文内容
        """
        # 构建user prompt
        user_prompt = self._full_template.replace("{PAPER_CONTENT}", paper_text)
        
        return AssembledPrompt(
            system_prompt=self._system_prompt,
            user_prompt=user_prompt,
            mode="full",
            metadata={
                "paper_id": paper_id,
                "paper_length": len(paper_text),
            }
        )
    
    def assemble_skeleton_mode(
        self,
        paper_text: str,
        paper_id: str = "unknown",
    ) -> AssembledPrompt:
        """
        组装骨架识别模式Prompt（两阶段第一阶段）
        
        system: 简化的系统提示
        user: 骨架模式模板 + 论文全文
        """
        # 构建user prompt
        user_prompt = self._skeleton_template.replace("{PAPER_CONTENT}", paper_text)
        
        # 骨架模式使用简化的系统提示
        system_prompt = "你是专业的人工关节材料数据提取专家。请仔细阅读论文，识别所有独立实验记录。只返回纯JSON，不要添加任何额外文字。"
        
        return AssembledPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            mode="skeleton",
            metadata={
                "paper_id": paper_id,
                "paper_length": len(paper_text),
            }
        )
    
    def assemble_chunk_fill_mode(
        self,
        chunk_text: str,
        skeleton_json: Dict[str, Any],
        chunk_index: int,
        total_chunks: int,
        paper_id: str = "unknown",
    ) -> AssembledPrompt:
        """
        组装分块填充模式Prompt（两阶段第二阶段）
        
        system: 简化的系统提示
        user: 分块填充模板（包含骨架、Schema、chunk内容、ICL示例）
        """
        # 构建骨架信息字符串
        records = skeleton_json.get("records", [])
        skeleton_lines = []
        for rec in records:
            name = rec.get("name", f"Record_{rec.get('id', 0)}")
            component = rec.get("component", "")
            category = rec.get("category", "")
            material = rec.get("material", "")
            treatment = rec.get("treatment", "")
            
            line = f"- [{rec.get('id', 0)}] {name}: {component} | {category} | {material}"
            if treatment:
                line += f" | {treatment}"
            skeleton_lines.append(line)
        
        skeleton_str = "\n".join(skeleton_lines) if skeleton_lines else "（无记录）"
        
        # 替换占位符
        user_prompt = self._chunk_fill_template
        user_prompt = user_prompt.replace("{SKELETON_INFO}", skeleton_str)
        user_prompt = user_prompt.replace("{SKELETON_JSON}", json.dumps(skeleton_json, ensure_ascii=False, indent=2))
        user_prompt = user_prompt.replace("{CHUNK_INDEX}", str(chunk_index + 1))
        user_prompt = user_prompt.replace("{TOTAL_CHUNKS}", str(total_chunks))
        user_prompt = user_prompt.replace("{CHUNK_CONTENT}", chunk_text)
        
        # 分块填充模式使用系统提示
        system_prompt = self._system_prompt
        
        return AssembledPrompt(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            mode="chunk_fill",
            metadata={
                "paper_id": paper_id,
                "chunk_index": chunk_index,
                "total_chunks": total_chunks,
                "chunk_length": len(chunk_text),
                "skeleton_records": skeleton_json.get("record_count", 0),
            }
        )
    
    # ==================== 默认模板（备用） ====================
    
    def _get_default_system_prompt(self) -> str:
        return """# 人工关节材料数据提取专家

你的任务是从学术论文中提取人工关节材料实验数据。

## 五大黄金规则
1. 禁止单位转换
2. 禁止编造数据
3. 禁止推断计算
4. 保留原始精度
5. 没有数据填null
"""
    
    def _get_default_full_template(self) -> str:
        return """# 全量提取任务

## 论文内容
{PAPER_CONTENT}

---

请提取所有实验数据，输出完整12表结构的JSON。"""
    
    def _get_default_skeleton_template(self) -> str:
        return """# 骨架识别任务

## 论文内容
{PAPER_CONTENT}

---

请识别论文中的独立实验记录，输出骨架JSON。"""
    
    def _get_default_chunk_fill_template(self) -> str:
        return """# 分块填充任务

## 已识别的记录骨架
{SKELETON_JSON}

## 当前文本块（第 {CHUNK_INDEX}/{TOTAL_CHUNKS} 块）
{CHUNK_CONTENT}

---

请从当前文本块中提取数据，填充到完整12表结构。"""
