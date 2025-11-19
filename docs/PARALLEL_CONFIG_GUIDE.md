# 并行处理环境变量配置指南

## 📋 配置说明

系统支持通过 `.env` 文件配置并行处理的默认参数。

---

## 🔧 环境变量

### `MAX_WORKERS`

**说明**：并行处理的最大worker数量限制

**默认值**：`4`

**作用**：
- 系统不会创建超过此数量的worker
- 自动选择模式下，worker数 = `min(CPU核心数, MAX_WORKERS)`

**推荐值**：
- 一般使用：`4`
- API限流严格：`2-3`
- 性能优先（多核CPU）：`6-8`

**示例**：
```bash
# .env
MAX_WORKERS=4
```

---

### `DEFAULT_WORKERS`

**说明**：默认使用的worker数量

**默认值**：`None`（留空）

**行为**：
- **留空或不设置**：自动选择 = `min(CPU核心数, MAX_WORKERS)`
- **设置为数字**：固定使用该数量的worker

**推荐值**：
- **留空**：让系统自动选择（推荐）
- **固定值**：如果您明确知道最优worker数

**示例**：
```bash
# .env

# 方式1: 留空，自动选择（推荐）
# DEFAULT_WORKERS=

# 方式2: 固定使用3个worker
DEFAULT_WORKERS=3
```

---

## 🎯 配置优先级

Worker数量的决定顺序：

```
1. 命令行参数 --workers N     （最高优先级）
   ↓
2. 环境变量 DEFAULT_WORKERS    （中等优先级）
   ↓
3. 自动选择                     （最低优先级）
   = min(CPU核心数, MAX_WORKERS)
```

---

## 💡 配置示例

### 示例1：完全自动（推荐）

**.env 配置**：
```bash
MAX_WORKERS=4
# DEFAULT_WORKERS留空
```

**结果**：
- 4核CPU → 使用4个worker
- 8核CPU → 使用4个worker（受MAX_WORKERS限制）
- 2核CPU → 使用2个worker

---

### 示例2：固定worker数

**.env 配置**：
```bash
MAX_WORKERS=4
DEFAULT_WORKERS=3
```

**结果**：
- 无论CPU核心数，都使用3个worker

---

### 示例3：命令行覆盖

**.env 配置**：
```bash
MAX_WORKERS=4
DEFAULT_WORKERS=3
```

**命令**：
```bash
python scripts/extract.py batch --workers 2
```

**结果**：
- 使用2个worker（命令行参数优先）

---

## 📊 配置建议

### 场景1：一般使用

```bash
# .env
MAX_WORKERS=4
# DEFAULT_WORKERS=  # 留空
```

让系统自动选择，适配不同的硬件。

---

### 场景2：API限流严格

```bash
# .env
MAX_WORKERS=2
DEFAULT_WORKERS=2
```

固定使用2个worker，避免触发API限流。

---

### 场景3：性能优先

```bash
# .env
MAX_WORKERS=8
DEFAULT_WORKERS=6
```

如果您的API没有严格限流，可以使用更多worker。

---

### 场景4：调试开发

```bash
# .env
MAX_WORKERS=1
DEFAULT_WORKERS=1
```

或使用命令行：
```bash
python scripts/extract.py batch --no-parallel
```

串行处理，日志更清晰。

---

## ⚠️ 注意事项

### 1. API限流

过多的并发请求可能触发API限流（429错误）：

**解决方法**：
- 减少 `MAX_WORKERS` 和 `DEFAULT_WORKERS`
- 使用 `--no-parallel` 临时禁用并行

### 2. 内存使用

每个worker会占用额外内存（约200-500MB）：

**8GB内存建议**：`MAX_WORKERS=4`
**16GB内存建议**：`MAX_WORKERS=6-8`

### 3. CPU使用

并行处理主要受限于网络IO，而非CPU：

- 4核CPU足够支持4-6个worker
- CPU核心数不是主要瓶颈

---

## 🔍 验证配置

运行以下命令查看当前配置：

```bash
python -c "
import settings
print(f'MAX_WORKERS: {settings.MAX_WORKERS}')
print(f'DEFAULT_WORKERS: {settings.DEFAULT_WORKERS}')
"
```

启动提取时，系统会显示实际使用的worker数：

```
Extractor初始化: 并行worker数=4
启动并行提取模式: 4 workers
```

---

## 📝 完整 .env 示例

```bash
# ==========================
# 并行处理配置
# ==========================

# 最大worker数量限制（系统不会超过这个值）
MAX_WORKERS=4

# 默认worker数量（留空则自动选择为 min(CPU核心数, MAX_WORKERS)）
# 设置为具体数字（如2或3）可固定worker数量
# DEFAULT_WORKERS=3

# 留空示例（推荐）：
# DEFAULT_WORKERS=
```

---

更新日期: 2025-11-19
