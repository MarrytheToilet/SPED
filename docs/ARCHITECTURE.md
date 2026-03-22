# 项目架构文档

## 系统概览

人工关节材料数据提取系统 v2.0 - 基于多Agent架构的智能数据提取系统

## 架构设计

### 层次结构

```
┌─────────────────────────────────────────────────────────┐
│                    用户交互层                            │
│         menu.py (交互式) | scripts/cli.py (CLI)        │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   工作流编排层                           │
│            workflows/full_extraction_pipeline.py        │
│              src/workflow/orchestrator.py              │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   Agent业务层                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │PDF处理Agent│  │提取Agent    │  │数据库Agent  │   │
│  │             │→ │             │→ │             │   │
│  │PDFProcess   │  │Extraction   │  │Database     │   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │
│  │分块过滤     │  │Prompt构建   │  │LLM Agent    │   │
│  │ChunkFilter  │  │PromptBuilder│  │LLMExtraction│   │
│  └─────────────┘  └─────────────┘  └─────────────┘   │
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   基础设施层                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌────────┐│
│  │PDF模块   │  │数据库    │  │提取器    │  │工具    ││
│  │pdfs/     │  │database/ │  │extractors│  │utils/  ││
│  └──────────┘  └──────────┘  └──────────┘  └────────┘│
└─────────────────────────────────────────────────────────┘
                            │
┌─────────────────────────────────────────────────────────┐
│                   外部服务层                             │
│     MinerU API  |  LLM APIs  |  SQLite Database       │
└─────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. Agent基类系统

#### 新版Agent基类 (src/agents/base.py)

**BaseAgent[T, R]** - 泛型基类
- 类型安全的输入输出
- 自动日志管理
- 结果封装 (AgentResult)
- 扩展性强

```python
from src.agents.base import BaseAgent, AgentResult

class MyAgent(BaseAgent[InputType, OutputType]):
    def __init__(self):
        super().__init__(
            name="MyAgent",
            description="Agent description"
        )
    
    def process(self, input_data: InputType) -> AgentResult[OutputType]:
        # 处理逻辑
        return AgentResult(success=True, data=result)
```

**StatefulAgent[T, R]** - 带状态持久化
- 自动状态保存
- 状态恢复
- 适合长时间运行任务

**BatchAgent[List[T], List[R]]** - 批处理Agent
- 断点续传
- 进度跟踪
- 失败重试
- 适合批量数据处理

#### 兼容层 (src/agents/legacy_compat.py)

为旧版Agent提供向后兼容性，保持简单API的同时内部使用新架构。

```python
from src.agents import BaseAgent  # 自动使用兼容层

class LegacyAgent(BaseAgent):
    def __init__(self):
        super().__init__("AgentName", "Description")
    
    def process(self, input_data):
        # 简单的处理逻辑
        return {"result": "data"}
```

### 2. Agent实现

#### PDF处理Agent (PDFProcessAgent)
- 批量上传PDF到MinerU
- 查询处理状态
- 下载解析结果
- 状态持久化

#### 提取Agent (ExtractionAgent)
- 协调整个提取流程
- 管理子Agent
- 结果聚合

#### 分块过滤Agent (ChunkFilterAgent)
- 文本分块
- 相关性过滤
- 减少无关内容

#### Prompt构建Agent (PromptBuilderAgent)
- 动态prompt生成
- Schema注入
- 示例组合

#### LLM Agent (LLMExtractionAgent)
- LLM调用
- 多模型支持
- 结果解析

#### 数据库Agent (DatabaseInsertionAgent)
- 数据验证
- 批量导入
- 错误处理

### 3. 工作流编排

#### Orchestrator (src/workflow/orchestrator.py)
- Agent注册
- 依赖管理
- 执行编排
- 错误处理

#### Full Pipeline (workflows/full_extraction_pipeline.py)
- 端到端流程
- 配置驱动
- 进度监控

### 4. 数据流

```
PDF文件 (data/raw/pdfs/)
    ↓
MinerU解析
    ↓
Markdown文本 (data/processed/parsed/)
    ↓
文本分块 & 过滤 (ChunkFilterAgent)
    ↓
Prompt构建 (PromptBuilderAgent)
    ↓
LLM提取 (LLMExtractionAgent)
    ↓
JSON数据 (data/processed/extracted/)
    ↓
数据库导入 (DatabaseAgent)
    ↓
SQLite (data/artificial_joint.db)
    ↓
导出 (Excel/CSV)
```

## 配置管理

### settings.py
- 路径配置
- API配置
- LLM参数
- 数据库配置

### .env文件
```bash
# MinerU
MINERU_TOKEN=your_token

# LLM
LLM_PROVIDER=siliconflow
SILICONFLOW_API_KEY=your_key
SILICONFLOW_MODEL=Qwen/Qwen2.5-72B-Instruct

# 参数
LLM_TEMPERATURE=0.1
CHUNK_SIZE=10000
```

## 扩展性

### 添加新Agent

1. 继承BaseAgent或使用兼容层
2. 实现process方法
3. 在工作流中注册
4. 配置依赖关系

```python
from src.agents.base import BaseAgent, AgentResult

class NewAgent(BaseAgent[InputType, OutputType]):
    def __init__(self):
        super().__init__(
            name="NewAgent",
            description="New agent description"
        )
    
    def process(self, input_data: InputType) -> AgentResult[OutputType]:
        # 实现处理逻辑
        return AgentResult(success=True, data=result)
```

### 添加新LLM提供商

1. 在settings.py添加配置
2. 在LLMAgent中添加支持
3. 更新.env.example

## 测试

```bash
# 测试Agent系统
python tests/test_new_agents.py

# 测试完整系统
python tests/test_new_system.py

# 测试导入
python -c "from src.agents import BaseAgent; print('OK')"
```

## 性能优化

### 批处理
- 使用BatchAgent自动批处理
- 并行处理支持
- 进度跟踪

### 缓存
- 状态持久化
- 断点续传
- 避免重复处理

### 资源管理
- 连接池
- 内存优化
- 日志轮转

## 部署

### 本地部署
```bash
pip install -r requirements.txt
cp .env.example .env
# 配置.env
python menu.py
```

### Docker部署
```bash
docker build -t sped:v2.0 .
docker run -v $(pwd)/data:/app/data sped:v2.0
```

## 维护

### 日志
- 位置: logs/
- Agent日志: logs/agents/
- 系统日志: logs/system.log

### 备份
- 数据库: data/artificial_joint.db
- JSON: data/processed/extracted/
- 配置: .env

### 监控
- 处理进度
- 错误率
- API使用情况

## 故障排除

### 常见问题

1. **导入错误**
   - 检查Python路径
   - 验证依赖安装

2. **API错误**
   - 检查.env配置
   - 验证API密钥
   - 检查网络连接

3. **Agent失败**
   - 查看日志文件
   - 检查输入数据
   - 验证配置参数

## 版本历史

- v2.0 (2026-03-15): 多Agent架构重构
- v1.0 (2025-11-19): 初始版本

## 相关文档

- [README.md](../README.md) - 项目概览
- [USAGE_GUIDE.md](./USAGE_GUIDE.md) - 使用指南
- [DEVELOPMENT.md](./DEVELOPMENT.md) - 开发指南
- [API.md](./API.md) - API文档
