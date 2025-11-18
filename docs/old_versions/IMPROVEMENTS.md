# 数据提取系统改进说明

## 改进概述

本次改进主要针对LLM数据提取的prompt设计和文本分块策略，提升提取准确性和效率。

## 主要改进点

### 1. ✅ Prompt完善 (prompts/prompt.md)

#### 改进前的问题:
- 缺少具体例子，LLM难以理解输出格式
- 指令不够明确，容易产生歧义
- 缺少边界情况的处理说明

#### 改进后:
- **增加详细示例**: 4个字段格式示例，展示如何从原文提取到JSON
- **完整提取示例**: 3个完整场景（新实验、完善记录、多组实验）
- **明确判断标准**: 详细说明何时创建新记录vs完善已有记录
- **边界情况处理**: 无数据、多组实验、字段冲突等情况的处理规则
- **强化核心规则**: 
  - 不推测、不编造
  - 数值必带单位
  - 多组实验分开记录

### 2. ✅ 分块策略改进 (src/agents/llm_agent.py)

#### 改进前的问题:
- 按一级标题分块，可能导致某些章节过长或过短
- 参考文献未完全过滤干净
- 分块边界不自然，可能切断关键信息

#### 改进后:
```python
# 新的分块流程:
1. 先过滤参考文献、致谢、附录等无用内容
2. 按固定字符数分块（可在settings.py配置）
3. 在自然边界切分（段落 > 换行 > 句子）
4. 保持overlap确保上下文连贯
5. 过滤太短的chunk（<100字符）
```

#### 配置参数 (settings.py):
```python
CHUNK_SIZE = 4000          # 每个chunk字符数（原3000→4000）
CHUNK_OVERLAP = 300        # 重叠字符数（原200→300）
```

### 3. ✅ 上下文构建优化

#### 改进前:
- 只显示简单的记录数量和标识
- LLM难以判断是否需要完善已有记录

#### 改进后:
- 展示最近3条记录的关键字段
- 明确指导LLM何时enrich vs new
- 显示记录索引，方便精确引用

示例:
```
### 已有记录: 2 条

请根据以下已有记录判断当前chunk中的数据应该:
- **完善已有记录** (action: "enrich", record_index: N) - 如果是同一实验的补充信息
- **创建新记录** (action: "new") - 如果是不同材料/条件/实验

**记录 1**:
  - 数据标识: CoCrMo-UHMWPE摩擦磨损实验
  - 球头信息.球头基本信息: {"材料类别": "CoCrMo合金", "直径": "28 mm"}
  - 体外实验-内衬与球头摩擦腐蚀实验.内衬与球头-实验设置: {"载荷": "50 N"}
```

### 4. ✅ 记录合并策略优化

#### 改进前:
- 简单的update覆盖，可能丢失已有数据

#### 改进后:
```python
# 智能合并策略:
1. 只更新null字段，不覆盖已有值（保守）
2. 遇到冲突时，保留原值并记录警告
3. 详细记录更新了哪些字段
4. 区分"完善记录"和"新增记录"的日志
```

### 5. ✅ 日志系统增强

#### 新增日志级别:
- `log_info()`: 常规信息
- `log_warning()`: 警告信息  
- `log_error()`: 错误信息
- `log_debug()`: 调试信息（字段冲突等）

#### 更详细的处理日志:
```
==================================================
处理 Chunk 3/15
  长度: 3845 字符
  位置: 8234-12079
  ✓ 提取到 1 条记录
  ↻ 完善了已有记录
  累计: 2 条记录
==================================================
```

### 6. ✅ 早停机制优化

#### 改进前:
- 连续3个空chunk就停止

#### 改进后:
- 连续5个空chunk才停止（更宽容）
- 停止时说明原因（可能已过实验数据部分）

## 使用方法

### 1. 测试改进效果

```bash
# 显示改进后的prompt
python test_improved_extraction.py --show-prompt

# 测试单个论文提取
python test_improved_extraction.py --test

# 交互式菜单
python test_improved_extraction.py
```

### 2. 配置调整

在 `settings.py` 中调整分块参数:

```python
# 增大chunk_size以包含更多上下文
CHUNK_SIZE = 5000  

# 增大overlap以确保不遗漏边界信息
CHUNK_OVERLAP = 500
```

### 3. 在环境变量中配置

创建 `.env` 文件:

```bash
# 分块配置
CHUNK_SIZE=4000
CHUNK_OVERLAP=300

# OpenAI配置
OPENAI_API_KEY=your_key
OPENAI_MODEL=gpt-4o
```

## 效果对比

### 提取准确性:
- ✅ 更准确识别实验数据字段
- ✅ 更好区分新实验vs补充数据
- ✅ 减少幻觉和推测

### 提取完整性:
- ✅ 参考文献不再污染数据
- ✅ 自然边界切分保持信息完整
- ✅ overlap机制避免遗漏

### 可维护性:
- ✅ 详细日志便于调试
- ✅ 配置化的chunk参数
- ✅ 清晰的代码注释

## 文件变更列表

```
修改的文件:
✓ prompts/prompt.md                    - 完善prompt，增加详细例子
✓ settings.py                          - 调整chunk配置参数
✓ src/agents/llm_agent.py             - 改进分块和合并策略
✓ src/agents/base_agent.py            - 增加日志方法

新增的文件:
+ test_improved_extraction.py          - 测试脚本
+ IMPROVEMENTS.md                      - 本说明文档
```

## 下一步优化建议

1. **Schema验证**: 添加JSON Schema验证，确保输出字段完整
2. **批量测试**: 在多篇论文上测试，统计准确率
3. **Prompt版本管理**: 保存不同版本的prompt，A/B测试
4. **并行处理**: 对独立的chunk并行调用LLM
5. **缓存机制**: 缓存已提取的chunk结果

## 常见问题

**Q: 为什么不直接用更大的chunk_size?**

A: chunk太大会超过LLM的上下文窗口，且降低提取精度。4000字符是经验值，在准确性和覆盖度之间平衡。

**Q: overlap会不会导致重复提取?**

A: 不会。智能合并策略会去重，overlap只是保证边界信息不丢失。

**Q: 如何处理多语言论文?**

A: 当前prompt主要针对英文，中文论文需调整prompt中的示例。可以根据语言动态选择prompt模板。

**Q: 提取失败怎么办?**

A: 查看日志中的错误信息，可能原因:
- API key无效
- 网络问题
- 文本格式异常
- Chunk太长超出token限制

## 技术细节

### 参考文献过滤正则表达式

```python
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
```

### Chunk边界优先级

```python
# 1. 段落边界（双换行）- 优先级最高
pos = text.rfind('\n\n', start, end)

# 2. 单换行
pos = text.rfind('\n', start, end)

# 3. 句子边界
for marker in ['. ', '。', '! ', '? ', '！', '？']:
    pos = text.rfind(marker, start, end)
```

## 版本历史

- **v1.1** (2024-11-02): 完善prompt，改进分块策略
- **v1.0** (2024-11-01): 初始版本，按一级标题分块

---

**作者**: AI Assistant  
**日期**: 2024-11-02  
**项目**: 人工关节材料数据提取系统
