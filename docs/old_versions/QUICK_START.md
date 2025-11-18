# 快速开始 - 改进后的数据提取系统

## 🚀 立即使用

### 1. 查看改进内容
```bash
# 显示改进后的prompt（包含详细例子）
python test_improved_extraction.py --show-prompt

# 查看完整改进说明
cat README_IMPROVEMENTS_CN.md
```

### 2. 测试提取
```bash
# 测试单个论文
python test_improved_extraction.py --test

# 如果有多个论文，会选择第一个
# 查看输出日志了解提取过程
```

### 3. 批量提取
```python
# 在Python脚本中使用
from src.agents.llm_agent import LLMExtractionAgent

agent = LLMExtractionAgent()

# 处理单个论文
result = agent.process({
    "paper_id": "paper_123",
    "full_text_path": "data/processed/parsed/paper_123/full.md"
})

print(f"提取到 {result.get('count', 1)} 条记录")
```

## ⚙️ 配置调整

### 方法1: 修改 settings.py
```python
# 修改默认值
CHUNK_SIZE = 5000          # 增大chunk包含更多上下文
CHUNK_OVERLAP = 500        # 增大overlap避免信息丢失
```

### 方法2: 环境变量（推荐）
创建或修改 `.env` 文件：
```bash
# 分块配置
CHUNK_SIZE=5000
CHUNK_OVERLAP=500

# LLM配置
OPENAI_MODEL=gpt-4o
OPENAI_API_KEY=your_api_key
OPENAI_API_BASE=https://api.openai.com/v1
```

## 📊 核心改进

| 改进点 | 说明 | 效果 |
|--------|------|------|
| **Prompt** | 增加4个示例+3个场景 | ✅ 提取更准确 |
| **分块策略** | 先过滤参考文献再chunk | ✅ 无污染数据 |
| **Chunk大小** | 可配置（默认4000字符） | ✅ 灵活调整 |
| **边界切分** | 段落>换行>句子 | ✅ 保持完整 |
| **智能合并** | 只更新null字段 | ✅ 不覆盖数据 |
| **详细日志** | warning/debug级别 | ✅ 易于调试 |

## 📁 主要文件

```
prompts/
  └── prompt.md                    ← 改进后的prompt（14KB，338行）

src/agents/
  ├── llm_agent.py                 ← 核心提取逻辑（改进后）
  └── base_agent.py                ← 基础Agent类（增加日志方法）

settings.py                        ← 配置文件（CHUNK_SIZE等）

test_improved_extraction.py        ← 测试脚本（新增）

文档:
  ├── README_IMPROVEMENTS_CN.md    ← 完整中文总结
  ├── IMPROVEMENTS.md              ← 英文详细说明
  ├── CHANGELOG_20241102.md        ← 更新日志
  └── QUICK_START.md               ← 本文档
```

## 🔍 查看日志

### 默认日志（INFO级别）
```bash
python test_improved_extraction.py --test
```

### 详细日志（DEBUG级别）
```bash
export LOG_LEVEL=DEBUG
python test_improved_extraction.py --test
```

### 保存日志到文件
```bash
python test_improved_extraction.py --test 2>&1 | tee extraction.log
```

## 💡 使用技巧

### 优化准确性
- 使用更强大的模型：`OPENAI_MODEL=gpt-4o`
- 增加chunk大小：`CHUNK_SIZE=5000`
- 增加overlap：`CHUNK_OVERLAP=500`

### 优化速度
- 使用更快的模型：`OPENAI_MODEL=gpt-4o-mini`
- 减小chunk大小：`CHUNK_SIZE=3000`
- 减小早停阈值（代码中调整）

### 调试问题
1. 设置 `LOG_LEVEL=DEBUG`
2. 查看详细的chunk处理日志
3. 检查是否过滤了太多内容
4. 检查API调用是否成功

## 📖 详细文档

- **完整说明**: `README_IMPROVEMENTS_CN.md` - 详细的改进说明和使用指南
- **技术细节**: `IMPROVEMENTS.md` - 英文版技术文档
- **更新日志**: `CHANGELOG_20241102.md` - 本次更新的详细记录
- **在线帮助**: `python test_improved_extraction.py --help`

## ❓ 常见问题

**Q: 提取结果不准确？**
- 检查prompt是否适合你的数据
- 尝试调整CHUNK_SIZE（太小可能切断关键信息）
- 检查是否使用了足够强大的模型

**Q: 提取速度慢？**
- 减小CHUNK_SIZE可以提高速度
- 考虑使用gpt-4o-mini等更快的模型
- 调整早停阈值（max_empty_chunks）

**Q: 遗漏了一些数据？**
- 增大CHUNK_OVERLAP确保边界信息不丢失
- 检查参考文献过滤是否过于激进
- 查看DEBUG日志确认chunk划分

**Q: 如何处理中文论文？**
- 当前prompt主要针对英文
- 可以在prompt.md中增加中文示例
- 或创建单独的中文prompt模板

## 🎯 下一步

1. **测试**: 运行 `python test_improved_extraction.py --test`
2. **查看结果**: 检查 `data/processed/extracted/` 目录
3. **调整配置**: 根据效果调整CHUNK_SIZE等参数
4. **批量处理**: 处理所有论文并评估效果

---

**需要帮助？** 查看 `README_IMPROVEMENTS_CN.md` 获取详细说明
