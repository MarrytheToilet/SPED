"""
工作流配置 - 统一管理配置
"""
from dataclasses import dataclass, field
from typing import Dict, Any, List
import yaml
from pathlib import Path


@dataclass
class AgentConfig:
    """Agent配置"""
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowConfig:
    """工作流配置"""
    mode: str = "auto"  # auto, full, chunk, hybrid
    max_workers: int = 4
    retry_limit: int = 3
    stop_on_error: bool = False
    
    # Agent配置
    pdf_agent: AgentConfig = field(default_factory=lambda: AgentConfig(
        config={
            "batch_size": 200,
            "concurrent_batches": 2,
            "download_threads": 4
        }
    ))
    
    chunk_agent: AgentConfig = field(default_factory=lambda: AgentConfig(
        config={
            "chunk_size": 10000,
            "overlap": 500,
            "filter_sections": ["References", "Acknowledgments", "参考文献", "致谢"]
        }
    ))
    
    extraction_agent: AgentConfig = field(default_factory=lambda: AgentConfig(
        config={
            "llm_model": "moonshotai/Kimi-K2-Instruct-0905",
            "temperature": 0.1,
            "max_tokens": 4096,
            "auto_fallback": True
        }
    ))
    
    database_agent: AgentConfig = field(default_factory=lambda: AgentConfig(
        config={
            "conflict_strategy": "update",
            "validate": True
        }
    ))
    
    export_agent: AgentConfig = field(default_factory=lambda: AgentConfig(
        config={
            "format": ["excel", "csv"],
            "filter_empty": True,
            "beautify": True
        }
    ))
    
    @classmethod
    def from_yaml(cls, yaml_path: Path) -> 'WorkflowConfig':
        """从YAML文件加载配置"""
        with open(yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # 简化版，实际需要更完整的解析
        config = cls()
        if 'workflow' in data:
            for key, value in data['workflow'].items():
                if hasattr(config, key):
                    setattr(config, key, value)
        
        return config
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "mode": self.mode,
            "max_workers": self.max_workers,
            "retry_limit": self.retry_limit,
            "stop_on_error": self.stop_on_error,
            "agents": {
                "pdf": self.pdf_agent.config,
                "chunk": self.chunk_agent.config,
                "extraction": self.extraction_agent.config,
                "database": self.database_agent.config,
                "export": self.export_agent.config
            }
        }
