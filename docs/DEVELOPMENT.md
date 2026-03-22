# 开发指南

## 开发环境设置

### 前置要求
- Python 3.8+
- pip
- Git
- 文本编辑器 (推荐: VSCode, PyCharm)

### 安装开发环境

```bash
# 1. 克隆项目
git clone <repository_url>
cd sped

# 2. 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或 venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑.env填入你的API密钥

# 5. 测试安装
python -c "from src.agents import BaseAgent; print('✓ Installation successful')"
```

### 项目结构理解

```
sped/
├── src/                    # 源代码
│   ├── agents/            # Agent实现
│   ├── database/          # 数据库模块
│   ├── extractors/        # 提取器
│   ├── pdfs/              # PDF处理
│   ├── pipeline/          # 数据管道
│   ├── utils/             # 工具函数
│   └── workflow/          # 工作流编排
├── scripts/               # 脚本工具
├── tests/                 # 测试文件
├── docs/                  # 文档
├── data/                  # 数据目录
├── prompts/               # Prompt模板
└── workflows/             # 工作流定义
```

## 开发规范

### 代码风格

#### Python风格指南
遵循 PEP 8 规范:

```python
# 好的例子
class MyAgent(BaseAgent):
    """
    Agent描述
    
    Attributes:
        name: Agent名称
        description: Agent描述
    """
    
    def __init__(self, name: str, description: str):
        super().__init__(name, description)
        self.name = name
        
    def process(self, input_data: dict) -> AgentResult:
        """
        处理数据
        
        Args:
            input_data: 输入数据字典
            
        Returns:
            AgentResult: 处理结果
            
        Raises:
            ValueError: 当输入无效时
        """
        # 实现逻辑
        return AgentResult(success=True, data=result)


# 避免的例子
class myagent(BaseAgent):  # 类名应该使用驼峰命名
    def __init__(self,name,description):  # 缺少空格和类型注解
        self.name=name  # 缺少空格
        
    def process(self,input_data):  # 缺少类型注解
        return result  # 应该返回AgentResult
```

#### 命名规范

- **类名**: `PascalCase` (如: `PDFProcessAgent`)
- **函数/方法**: `snake_case` (如: `process_data`)
- **常量**: `UPPER_SNAKE_CASE` (如: `MAX_RETRIES`)
- **变量**: `snake_case` (如: `input_data`)
- **私有成员**: `_leading_underscore` (如: `_internal_method`)

### 类型注解

始终使用类型注解:

```python
from typing import Dict, List, Optional, Any
from src.agents.base import AgentResult

def extract_data(
    text: str,
    schema: Dict[str, Any],
    max_tokens: int = 4096
) -> AgentResult[Dict[str, Any]]:
    """提取数据"""
    result: Dict[str, Any] = {}
    # 处理逻辑
    return AgentResult(success=True, data=result)
```

### 文档字符串

使用Google风格的文档字符串:

```python
def complex_function(param1: str, param2: int, param3: Optional[bool] = None) -> Dict[str, Any]:
    """
    简短的单行描述。
    
    更详细的描述，可以多行。解释函数的作用、
    使用场景和注意事项。
    
    Args:
        param1: 参数1的描述
        param2: 参数2的描述
        param3: 参数3的描述，可选参数。默认None
        
    Returns:
        返回值的描述
        
    Raises:
        ValueError: 什么情况下抛出ValueError
        RuntimeError: 什么情况下抛出RuntimeError
        
    Example:
        >>> result = complex_function("test", 42)
        >>> print(result["status"])
        'success'
    """
    pass
```

## 开发新Agent

### 基础Agent模板

```python
from src.agents.base import BaseAgent, AgentResult
from typing import Dict, Any
from loguru import logger


class MyNewAgent(BaseAgent[Dict[str, Any], Dict[str, Any]]):
    """
    新Agent的描述
    
    这个Agent负责...
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化Agent
        
        Args:
            config: 配置字典
        """
        super().__init__(
            name="MyNewAgent",
            description="Agent简短描述"
        )
        self.config = config or {}
        self.log_info("Agent initialized")
        
    def process(self, input_data: Dict[str, Any]) -> AgentResult[Dict[str, Any]]:
        """
        处理数据
        
        Args:
            input_data: 输入数据
            
        Returns:
            处理结果
        """
        try:
            self.log_info(f"Processing data: {len(input_data)} items")
            
            # 你的处理逻辑
            result = self._process_logic(input_data)
            
            self.log_info("Processing completed successfully")
            return AgentResult(
                success=True,
                data=result,
                metadata={"processed_items": len(result)}
            )
            
        except Exception as e:
            self.log_error(f"Processing failed: {str(e)}")
            return AgentResult(
                success=False,
                error=str(e)
            )
    
    def _process_logic(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """内部处理逻辑"""
        # 实现具体逻辑
        return data


# 使用Agent
if __name__ == "__main__":
    agent = MyNewAgent(config={"param": "value"})
    result = agent.process({"key": "value"})
    
    if result:
        print("Success:", result.data)
    else:
        print("Failed:", result.error)
```

### 批处理Agent模板

```python
from src.agents.base import BatchAgent, AgentResult
from typing import Dict, Any
from pathlib import Path


class MyBatchAgent(BatchAgent[Dict[str, Any], Dict[str, Any]]):
    """批处理Agent"""
    
    def __init__(self, state_file: Path = None):
        super().__init__(
            name="MyBatchAgent",
            description="批处理Agent",
            state_file=state_file
        )
    
    def process_single(
        self,
        item: Dict[str, Any],
        item_index: int
    ) -> AgentResult[Dict[str, Any]]:
        """
        处理单个项目
        
        Args:
            item: 单个数据项
            item_index: 项目索引
            
        Returns:
            处理结果
        """
        try:
            # 处理逻辑
            result = {"processed": item, "index": item_index}
            return AgentResult(success=True, data=result)
        except Exception as e:
            return AgentResult(success=False, error=str(e))


# 使用
agent = MyBatchAgent(state_file=Path("state.json"))
items = [{"id": i} for i in range(100)]
results = agent.process(items)  # 自动批处理+进度跟踪
```

## 测试

### 编写测试

```python
# tests/test_my_agent.py
import pytest
from src.agents.my_agent import MyNewAgent


class TestMyNewAgent:
    """测试MyNewAgent"""
    
    def setup_method(self):
        """每个测试前运行"""
        self.agent = MyNewAgent()
    
    def test_initialization(self):
        """测试初始化"""
        assert self.agent.name == "MyNewAgent"
        assert self.agent.description
    
    def test_process_success(self):
        """测试成功处理"""
        input_data = {"key": "value"}
        result = self.agent.process(input_data)
        
        assert result.success
        assert result.data is not None
        assert result.error is None
    
    def test_process_failure(self):
        """测试失败处理"""
        invalid_input = None
        result = self.agent.process(invalid_input)
        
        assert not result.success
        assert result.error is not None
    
    def test_edge_cases(self):
        """测试边界情况"""
        # 空输入
        result = self.agent.process({})
        assert result.success
        
        # 大量数据
        large_input = {"data": "x" * 10000}
        result = self.agent.process(large_input)
        assert result.success


# 运行测试
# pytest tests/test_my_agent.py -v
```

### 运行测试

```bash
# 运行所有测试
pytest tests/

# 运行特定文件
pytest tests/test_my_agent.py

# 运行特定测试
pytest tests/test_my_agent.py::TestMyNewAgent::test_process_success

# 显示详细输出
pytest tests/ -v

# 显示打印输出
pytest tests/ -s

# 代码覆盖率
pytest tests/ --cov=src --cov-report=html
```

## 调试

### 使用日志

```python
from loguru import logger

# 配置日志
logger.add(
    "logs/debug.log",
    level="DEBUG",
    format="{time} {level} {message}",
    rotation="10 MB"
)

# 使用日志
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")

# 在Agent中
class MyAgent(BaseAgent):
    def process(self, data):
        self.log_debug(f"Input data: {data}")
        self.log_info("Starting processing")
        try:
            result = self._process(data)
            self.log_info("Processing completed")
            return result
        except Exception as e:
            self.log_error(f"Failed: {e}")
            raise
```

### 使用Python调试器

```python
# 在代码中设置断点
import pdb; pdb.set_trace()

# 或使用ipdb (需要安装: pip install ipdb)
import ipdb; ipdb.set_trace()

# VSCode调试配置 (.vscode/launch.json)
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Python: Current File",
            "type": "python",
            "request": "launch",
            "program": "${file}",
            "console": "integratedTerminal"
        }
    ]
}
```

## Git工作流

### 分支策略

```bash
main          # 主分支，稳定版本
├── develop   # 开发分支
├── feature/* # 功能分支
├── bugfix/*  # 修复分支
└── release/* # 发布分支
```

### 提交规范

```bash
# 格式: <type>(<scope>): <subject>

# type类型:
# feat: 新功能
# fix: 修复bug
# docs: 文档更新
# style: 代码格式(不影响功能)
# refactor: 重构
# test: 测试
# chore: 构建/工具

# 示例:
git commit -m "feat(agent): add new PDF processing agent"
git commit -m "fix(database): resolve connection pool issue"
git commit -m "docs(readme): update installation guide"
```

### 开发流程

```bash
# 1. 创建功能分支
git checkout -b feature/my-new-feature develop

# 2. 开发和提交
git add .
git commit -m "feat: implement new feature"

# 3. 推送到远程
git push origin feature/my-new-feature

# 4. 创建Pull Request

# 5. 合并后删除分支
git checkout develop
git pull
git branch -d feature/my-new-feature
```

## 性能优化

### 性能分析

```python
import cProfile
import pstats

# 分析函数
def profile_function():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # 你的代码
    result = your_function()
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)  # 显示前20个

# 或使用装饰器
from functools import wraps
import time

def timing_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end-start:.2f}s")
        return result
    return wrapper

@timing_decorator
def slow_function():
    time.sleep(1)
```

### 内存优化

```python
# 使用生成器
def process_large_file(filepath):
    with open(filepath) as f:
        for line in f:  # 逐行读取，不加载整个文件
            yield process_line(line)

# 及时释放资源
def process_data():
    data = load_large_data()
    result = process(data)
    del data  # 显式释放
    return result
```

## 常见问题

### Q: 如何添加新的LLM供应商?

在 `src/agents/llm_agent.py` 中添加配置:

```python
# 1. 在settings.py添加配置
NEW_PROVIDER_API_KEY = os.getenv("NEW_PROVIDER_API_KEY")
NEW_PROVIDER_BASE_URL = os.getenv("NEW_PROVIDER_BASE_URL")

# 2. 在LLMAgent中添加支持
class LLMExtractionAgent:
    def _get_client(self):
        if self.provider == "new_provider":
            return OpenAI(
                api_key=NEW_PROVIDER_API_KEY,
                base_url=NEW_PROVIDER_BASE_URL
            )
```

### Q: 如何调试Agent执行失败?

1. 检查日志文件 `logs/agents/AgentName.log`
2. 使用debug模式运行
3. 添加更多日志点
4. 使用Python调试器

### Q: 如何优化LLM调用成本?

1. 减小chunk_size
2. 使用更便宜的模型
3. 添加缓存机制
4. 批量处理

## 发布流程

### 版本号规范

遵循语义化版本 (Semantic Versioning):
- MAJOR.MINOR.PATCH (如: 2.1.0)
- MAJOR: 不兼容的API变更
- MINOR: 向后兼容的功能新增
- PATCH: 向后兼容的问题修正

### 发布checklist

- [ ] 更新版本号
- [ ] 更新CHANGELOG.md
- [ ] 运行所有测试
- [ ] 更新文档
- [ ] 创建release分支
- [ ] 打标签
- [ ] 构建分发包

```bash
# 打标签
git tag -a v2.1.0 -m "Release version 2.1.0"
git push origin v2.1.0
```

## 资源链接

- [Python官方文档](https://docs.python.org/3/)
- [PEP 8风格指南](https://pep8.org/)
- [Loguru文档](https://loguru.readthedocs.io/)
- [Pytest文档](https://docs.pytest.org/)

## 获取帮助

- 查看项目文档 `docs/`
- 查看代码注释
- 提交Issue
- 联系开发团队
