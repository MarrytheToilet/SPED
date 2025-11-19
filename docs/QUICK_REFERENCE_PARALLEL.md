# 🚀 快速参考 - 并行处理功能

## 📌 一句话总结

**批量提取现在支持并行处理，速度提升2-4倍！**

---

## 💡 最常用命令

### 推荐用法1：配置.env文件

在 `.env` 中设置：
```bash
DEFAULT_WORKERS=3
MAX_WORKERS=4
```

然后运行：
```bash
# 自动使用.env中配置的worker数
python scripts/extract.py batch
```

### 推荐用法2：命令行指定

```bash
# 使用默认配置（自动选择worker数）
python scripts/extract.py batch

# 指定worker数量（覆盖.env配置）
python scripts/extract.py batch --workers 4
```

### 自定义并行数

```bash
# 使用4个worker并行处理
python scripts/extract.py batch --workers 4

# 使用2个worker（API限流时）
python scripts/extract.py batch --workers 2
```

### 串行模式（调试时）

```bash
# 禁用并行，逐个处理
python scripts/extract.py batch --no-parallel
```

---

## 🎯 参数速查

| 参数 | 说明 | 默认值 | 配置位置 |
|------|------|--------|---------|
| `--workers N` | 并行worker数 | 见下方优先级 | 命令行 |
| `--no-parallel` | 禁用并行 | 启用并行 | 命令行 |
| `DEFAULT_WORKERS` | 默认worker数 | 留空=自动 | .env文件 |
| `MAX_WORKERS` | 最大worker数 | 4 | .env文件 |

**Worker数量优先级**：
1. 命令行 `--workers N` （最高）
2. 环境变量 `DEFAULT_WORKERS`
3. 自动选择 `min(CPU核心数, MAX_WORKERS)`

---

## 🔧 环境变量配置

在 `.env` 文件中添加：

```bash
# 并行处理配置
MAX_WORKERS=4              # 最大worker数量限制
DEFAULT_WORKERS=3          # 默认使用3个worker

# 或留空自动选择
# DEFAULT_WORKERS=         # 自动 = min(CPU核心数, MAX_WORKERS)
```

---

## ⚡ 性能对比

| 场景 | 命令 | 100篇耗时 |
|------|------|----------|
| 串行 | `--no-parallel` | ~50分钟 |
| 2个worker | `--workers 2` | ~25分钟 |
| 4个worker | `--workers 4` | ~13分钟 |

---

## ⚠️ 重要提示

1. **API限流**：如遇429错误，减少worker数或用`--no-parallel`
2. **内存占用**：每个worker需要额外内存，注意系统资源
3. **日志输出**：并行模式下日志可能交错，调试时用串行模式

---

## 🔧 完整示例

```bash
# 示例1: 默认配置（最简单）
python scripts/extract.py batch

# 示例2: 指定模型 + 并行
python scripts/extract.py batch --model gpt-4o-mini --workers 4

# 示例3: 指定模式 + 模型 + 并行
python scripts/extract.py batch full --model "Qwen/Qwen2.5-72B-Instruct" --workers 3

# 示例4: 调试模式（串行）
python scripts/extract.py batch --no-parallel
```

---

## 📊 Batch Index修复

现在batch_index会全局递增，不会重复：

```bash
# 第一次上传: batch_1, batch_2, batch_3, batch_4
python scripts/pdf_process.py upload

# 第二次上传: batch_5, batch_6, batch_7  ✅ 继续递增
python scripts/pdf_process.py upload
```

---

更新日期: 2025-11-19
