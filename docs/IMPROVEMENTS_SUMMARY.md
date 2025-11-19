# 系统改进总结

更新日期: 2025-11-19

---

## ✅ 已完成的改进

### 1. 修复batch_index重复问题

**问题描述**：
- 每次上传新PDF时，batch_index都从1开始，导致：
  - `upload_batches.csv`中batch_index重复
  - 下载时文件夹命名冲突（batch_1会被覆盖）
  - 无法追踪全局批次历史

**解决方案**：
- ✅ 从CSV中读取最大的batch_index
- ✅ 新批次从`max_batch_index + 1`开始
- ✅ 确保batch_index全局唯一递增
- ✅ 下载文件夹不会被覆盖

**修改文件**：
- `scripts/pdf_process.py`

**示例**：
```bash
# 第一次上传
batch_index: 1, 2, 3, 4

# 第二次上传（新的PDF）
batch_index: 5, 6, 7  # ✅ 继续递增，不会重复
```

---

### 2. 添加数据提取并行处理

**问题描述**：
- 批量提取速度慢，串行处理耗时长
- 无法充分利用CPU和网络资源

**解决方案**：
- ✅ 使用`ThreadPoolExecutor`实现并行处理
- ✅ 支持环境变量配置默认worker数
- ✅ 支持命令行参数覆盖
- ✅ 支持自定义worker数量
- ✅ 支持串行/并行模式切换
- ✅ 线程安全：每个worker独立创建Agent实例

**修改文件**：
- `settings.py` - 添加并行配置
- `src/pipeline/processor.py` - 支持环境变量配置
- `src/extractors/extractor.py` - 支持环境变量配置
- `scripts/extract.py` - 支持环境变量配置
- `.env.example` - 添加配置说明

**配置方式**：
```bash
# .env 文件
MAX_WORKERS=4          # 最大worker数
DEFAULT_WORKERS=3      # 默认worker数（留空则自动）
```

**使用方法**：
```bash
# 使用.env配置
python scripts/extract.py batch

# 命令行覆盖
python scripts/extract.py batch --workers 4

# 禁用并行
python scripts/extract.py batch --no-parallel
```

---

## 📊 改进对比

### Batch Index管理

| 项目 | 改进前 | 改进后 |
|------|--------|--------|
| batch_index | 每次从1开始 | 全局递增 |
| 文件夹命名 | 可能重复覆盖 | 唯一不重复 |
| 批次追踪 | 混乱 | 清晰有序 |

### 数据提取性能

| 项目 | 改进前 | 改进后 |
|------|--------|--------|
| 处理模式 | 仅串行 | 串行/并行可选 |
| Worker数 | 固定1个 | 1-4个可调 |
| 100篇论文耗时 | ~50分钟 | ~13-25分钟 |
| CPU利用率 | 低 | 高 |

---

## 🎯 命令行参数

### PDF处理（未改变）

```bash
# 上传PDF
python scripts/pdf_process.py upload

# 查询状态
python scripts/pdf_process.py status

# 下载结果
python scripts/pdf_process.py download
```

### 数据提取（新增参数）

**环境变量配置（.env文件）**：
```bash
# 并行处理配置
MAX_WORKERS=4              # 最大worker数量
DEFAULT_WORKERS=3          # 默认worker数（留空则自动）
```

**命令行参数**：
```bash
# 批量提取 - 新增参数
python scripts/extract.py batch [mode] [--model MODEL] [--workers N] [--no-parallel]

参数说明:
  --workers N, -w N    并行worker数量（覆盖.env配置）
  --no-parallel        禁用并行处理
  --model MODEL        指定LLM模型
```

**优先级**：
- 命令行 `--workers` > 环境变量 `DEFAULT_WORKERS` > 自动选择

### Pipeline处理（新增参数）

```bash
# 批量处理 - 新增参数
python src/pipeline/processor.py --batch BATCH [--workers N] [--no-parallel]

参数说明:
  --workers N          并行worker数量
  --no-parallel        禁用并行处理
```

---

## 📝 使用建议

### 1. PDF上传阶段

```bash
# 正常上传（会自动从上次的batch_index继续）
python scripts/pdf_process.py upload

# 查看状态（会显示所有批次，包括历史批次）
python scripts/pdf_process.py status

# 下载结果（batch_1, batch_2, ... 不会被覆盖）
python scripts/pdf_process.py download
```

### 2. 数据提取阶段

**方法1：使用.env配置（推荐）**

在 `.env` 文件中设置：
```bash
# 固定使用3个worker
DEFAULT_WORKERS=3
MAX_WORKERS=4
```

然后运行：
```bash
# 自动使用配置的worker数
python scripts/extract.py batch
```

**方法2：命令行参数**

```bash
# 推荐：使用默认配置
python scripts/extract.py batch

# 如果API有限流，减少worker数
python scripts/extract.py batch --workers 2

# 调试时使用串行模式
python scripts/extract.py batch --no-parallel
```

---

## ⚠️ 注意事项

### 1. Batch Index

- ✅ 现在batch_index会全局递增，不会重复
- ✅ 下载的文件夹（batch_1, batch_5, ...）不会被覆盖
- ✅ 可以安全地多次上传新PDF

### 2. 并行处理

- ⚡ 默认启用，自动使用合适的worker数
- 🔒 线程安全，每个worker独立运行
- ⚠️ 注意API限流，建议worker数不超过4
- 📊 并行模式下日志可能交错

### 3. 性能优化

- 💡 并行主要适用于batch模式
- 💡 single模式仍然是串行处理
- 💡 数据库写入仍是串行（SQLite限制）

---

## 🔧 技术细节

### 1. Batch Index追踪

```python
# 读取最大batch_index
max_batch_index = 0
if BATCH_CSV.exists():
    for row in csv.DictReader(f):
        idx = int(row['batch_index'])
        max_batch_index = max(max_batch_index, idx)

# 新批次从max+1开始
current_batch_index = max_batch_index + batch_idx + 1
```

### 2. 并行处理实现

```python
# 使用ThreadPoolExecutor
with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
    future_to_paper = {
        executor.submit(self._process_single_paper_safe, paper): paper
        for paper in papers
    }
    
    for future in as_completed(future_to_paper):
        result = future.result()
        # 处理结果
```

---

## 📚 相关文档

- [并行处理详细指南](./PARALLEL_PROCESSING_GUIDE.md)
- [快速使用指南](./QUICK_USAGE_GUIDE.md)
- [项目结构说明](../PROJECT_STRUCTURE.md)

---

## 🚀 下一步优化建议

### 可能的优化方向

1. **数据库并发**：使用PostgreSQL替代SQLite，支持并发写入
2. **批处理优化**：支持断点续传，失败重试机制
3. **监控仪表板**：实时查看处理进度和状态
4. **智能调度**：根据API响应速度动态调整worker数

---

更新日期: 2025-11-19
作者: AI Assistant
