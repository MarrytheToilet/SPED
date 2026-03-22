"""
新版BaseAgent - 支持多Agent工作流
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, TypeVar, Generic
from pathlib import Path
from datetime import datetime
from loguru import logger
import json

T = TypeVar('T')
R = TypeVar('R')


class AgentResult(Generic[R]):
    """Agent执行结果的标准封装"""
    
    def __init__(
        self,
        success: bool,
        data: Optional[R] = None,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }
    
    def __bool__(self) -> bool:
        return self.success


class BaseAgent(ABC, Generic[T, R]):
    """
    Agent基类 - 所有Agent的基础
    
    Generic[T, R]:
        T: 输入数据类型
        R: 输出数据类型
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        config: Optional[Dict[str, Any]] = None
    ):
        self.name = name
        self.description = description
        self.config = config or {}
        self.logger = logger.bind(agent=name)
        self._setup_logger()
    
    def _setup_logger(self):
        """设置Agent专属日志"""
        log_file = Path(f"logs/agents/{self.name}.log")
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            filter=lambda record: record["extra"].get("agent") == self.name,
            rotation="10 MB",
            retention="30 days",
            level="DEBUG"
        )
    
    @abstractmethod
    def process(self, input_data: T) -> AgentResult[R]:
        """
        处理输入数据 - 子类必须实现
        
        Args:
            input_data: 输入数据
            
        Returns:
            AgentResult: 包含处理结果的标准对象
        """
        pass
    
    def validate_input(self, input_data: T) -> bool:
        """
        验证输入数据 - 子类可以重写
        
        Args:
            input_data: 输入数据
            
        Returns:
            bool: 是否有效
        """
        return True
    
    def log_info(self, message: str, **kwargs):
        """记录信息日志"""
        self.logger.info(message, **kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """记录警告日志"""
        self.logger.warning(message, **kwargs)
    
    def log_error(self, message: str, **kwargs):
        """记录错误日志"""
        self.logger.error(message, **kwargs)
    
    def log_debug(self, message: str, **kwargs):
        """记录调试日志"""
        self.logger.debug(message, **kwargs)
    
    def save_result(
        self,
        result: Any,
        output_path: Path,
        format: str = "json"
    ) -> bool:
        """
        保存结果到文件
        
        Args:
            result: 要保存的结果
            output_path: 输出路径
            format: 格式 (json, txt, etc.)
            
        Returns:
            bool: 是否成功
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if format == "json":
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
            elif format == "txt":
                with open(output_path, 'w', encoding='utf-8') as f:
                    f.write(str(result))
            else:
                raise ValueError(f"不支持的格式: {format}")
            
            self.log_info(f"结果已保存: {output_path}")
            return True
        except Exception as e:
            self.log_error(f"保存结果失败: {e}")
            return False
    
    def load_data(self, input_path: Path, format: str = "json") -> Optional[Any]:
        """
        从文件加载数据
        
        Args:
            input_path: 输入路径
            format: 格式
            
        Returns:
            加载的数据
        """
        try:
            if format == "json":
                with open(input_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            elif format == "txt":
                with open(input_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise ValueError(f"不支持的格式: {format}")
        except Exception as e:
            self.log_error(f"加载数据失败: {e}")
            return None
    
    def get_config(self, key: str, default: Any = None) -> Any:
        """获取配置项"""
        return self.config.get(key, default)
    
    def set_config(self, key: str, value: Any):
        """设置配置项"""
        self.config[key] = value
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(name='{self.name}')>"


class StatefulAgent(BaseAgent[T, R]):
    """
    有状态的Agent - 可以保存和恢复执行状态
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        state_file: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, description, config)
        self.state_file = state_file or Path(f"data/.state/{name}_state.json")
        self.state: Dict[str, Any] = {}
        self.load_state()
    
    def load_state(self) -> bool:
        """加载状态"""
        if self.state_file.exists():
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    self.state = json.load(f)
                self.log_info(f"状态已加载: {len(self.state)} 项")
                return True
            except Exception as e:
                self.log_error(f"加载状态失败: {e}")
        return False
    
    def save_state(self) -> bool:
        """保存状态"""
        try:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
            self.log_debug(f"状态已保存: {len(self.state)} 项")
            return True
        except Exception as e:
            self.log_error(f"保存状态失败: {e}")
            return False
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """获取状态值"""
        return self.state.get(key, default)
    
    def set_state(self, key: str, value: Any, save: bool = True):
        """设置状态值"""
        self.state[key] = value
        if save:
            self.save_state()
    
    def clear_state(self):
        """清空状态"""
        self.state = {}
        self.save_state()


class BatchAgent(StatefulAgent[List[T], List[R]]):
    """
    批处理Agent - 支持批量处理和断点续传
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        batch_size: int = 10,
        state_file: Optional[Path] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        super().__init__(name, description, state_file, config)
        self.batch_size = batch_size
    
    @abstractmethod
    def process_single(self, item: T) -> AgentResult[R]:
        """处理单个项目 - 子类必须实现"""
        pass
    
    def process(self, input_data: List[T]) -> AgentResult[List[R]]:
        """
        批量处理
        
        Args:
            input_data: 输入数据列表
            
        Returns:
            AgentResult: 包含处理结果列表
        """
        results = []
        failed_items = []
        
        total = len(input_data)
        processed = self.get_state("processed_count", 0)
        
        self.log_info(f"开始批量处理: 总数={total}, 已处理={processed}")
        
        for i, item in enumerate(input_data):
            # 跳过已处理的项目
            if i < processed:
                continue
            
            try:
                result = self.process_single(item)
                if result.success:
                    results.append(result.data)
                else:
                    failed_items.append((i, item, result.error))
                    self.log_warning(f"处理失败 [{i+1}/{total}]: {result.error}")
            except Exception as e:
                failed_items.append((i, item, str(e)))
                self.log_error(f"处理异常 [{i+1}/{total}]: {e}")
            
            # 更新进度
            processed = i + 1
            self.set_state("processed_count", processed, save=(processed % 10 == 0))
            
            if (i + 1) % 10 == 0:
                self.log_info(f"进度: {processed}/{total} ({processed/total*100:.1f}%)")
        
        # 完成后清空状态
        self.set_state("processed_count", 0)
        
        success = len(failed_items) == 0
        metadata = {
            "total": total,
            "success": len(results),
            "failed": len(failed_items),
            "failed_items": failed_items
        }
        
        return AgentResult(
            success=success,
            data=results,
            error=f"{len(failed_items)} 项处理失败" if failed_items else None,
            metadata=metadata
        )
