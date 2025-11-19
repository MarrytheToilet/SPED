# 并行处理功能指南

## 📋 概述

系统已支持**数据提取阶段的并行处理**，可显著提升批量处理速度。

### ⚡ 性能提升

- **串行模式**：逐个处理论文，每篇处理完再处理下一篇
- **并行模式**：同时处理多篇论文，充分利用CPU和网络资源
- **预期提速**：2-4倍（取决于CPU核心数和API响应速度）

---

## 🎯 使用方法

### 1. 批量提取 - 默认并行模式

```bash
# 默认并行处理（自动使用CPU核心数，最大4个worker）
python scripts/extract.py batch

# 指定worker数量
python scripts/extract.py batch --workers 4

# 指定模型 + 并行
python scripts/extract.py batch --model gpt-4o-mini --workers 3
```

### 2. 批量提取 - 串行模式

```bash
# 禁用并行（逐个处理）
python scripts/extract.py batch --no-parallel
```

### 3. Pipeline方式

```bash
# 并行处理（默认）
python src/pipeline/processor.py --batch batch_1

# 指定worker数量
python src/pipeline/processor.py --batch batch_1 --workers 4

# 禁用并行
python src/pipeline/processor.py --batch batch_1 --no-parallel
```

---

## ⚙️ 配置参数

### `--workers` / `-w`
- **作用**：设置并行worker数量
- **默认值**：`min(CPU核心数, 4)`
- **建议值**：
  - CPU较多：3-4个worker
  - CPU较少：2个worker
  - API有限流：1-2个worker

### `--no-parallel`
- **作用**：禁用并行，使用串行模式
- **适用场景**：
  - API有严格的速率限制
  - 调试时需要查看详细日志
  - 系统资源紧张

---

## 📊 处理阶段对比

| 阶段 | 是否并行 | 说明 |
|------|---------|------|
| PDF上传到MinerU | ❌ 不并行 | 按批次顺序上传 |
| MinerU处理PDF | ✅ 自动并行 | MinerU服务器端自动处理 |
| 下载解析结果 | ❌ 不并行 | 按批次顺序下载 |
| **数据提取（LLM）** | ✅ **可并行** | **新增功能** |
| 数据入库 | ❌ 不并行 | SQLite不支持并发写入 |

---

## 💡 最佳实践

### 1. 推荐配置

```bash
# 对于大多数情况，使用默认配置即可
python scripts/extract.py batch

# 如果有更多CPU核心，可以增加worker
python scripts/extract.py batch --workers 4
```

### 2. API限流处理

如果遇到API限流错误（429 Too Many Requests），可以：

```bash
# 减少worker数量
python scripts/extract.py batch --workers 2

# 或者使用串行模式
python scripts/extract.py batch --no-parallel
```

### 3. 调试模式

调试时建议使用串行模式，日志更清晰：

```bash
python scripts/extract.py batch --no-parallel
```

---

## 📈 性能对比示例

假设处理100篇论文，每篇平均耗时30秒：

| 模式 | Worker数 | 总耗时 | 提速比 |
|------|----------|--------|-------|
| 串行 | 1 | 50分钟 | 1x |
| 并行 | 2 | 25分钟 | 2x |
| 并行 | 4 | 13分钟 | 3.8x |

*注：实际提速取决于API响应速度和网络状况*

---

## 🔧 技术实现

### 线程池（ThreadPoolExecutor）

使用Python的`concurrent.futures.ThreadPoolExecutor`实现：

- **线程安全**：每个worker创建独立的LLM Agent实例
- **异常处理**：单个论文失败不影响其他论文
- **进度显示**：实时显示完成进度

### 示例输出

```
启动并行提取模式: 4 workers
[1/20] ✓ paper_001 - 3 条记录
[2/20] ✓ paper_002 - 2 条记录
[3/20] ✗ paper_003 - 错误: API timeout
[4/20] ✓ paper_004 - 5 条记录
...
```

---

## ⚠️ 注意事项

1. **API限流**：过多并发请求可能触发API限流，建议worker数不超过4
2. **内存使用**：每个worker会占用一定内存，注意系统资源
3. **日志顺序**：并行模式下日志可能交错，调试时建议用串行模式
4. **数据库写入**：目前数据库写入仍是串行（SQLite限制）

---

## 📝 更新日志

### 2025-11-19

- ✅ 添加数据提取阶段的并行处理
- ✅ 支持自定义worker数量
- ✅ 添加串行/并行模式切换
- ✅ 优化进度显示和错误处理
- ✅ 修复batch_index重复问题

---

## 🆘 常见问题

### Q: 并行会不会导致API费用增加？

A: 不会。并行只是同时处理多个请求，总请求数不变，费用相同。

### Q: 最多可以用多少个worker？

A: 建议不超过4个，过多worker可能导致API限流或系统资源不足。

### Q: 为什么有时并行反而更慢？

A: 可能原因：
- API响应慢，多个请求在排队
- 网络带宽不足
- 系统资源紧张

建议降低worker数量或使用串行模式。

### Q: 如何查看当前使用了多少worker？

A: 启动时会显示：
```
Pipeline初始化: 并行worker数=4
启动并行提取模式: 4 workers
```

---

更新日期: 2025-11-19
