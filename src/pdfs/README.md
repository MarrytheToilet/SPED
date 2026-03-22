# PDF处理模块 - 完整说明

## 📂 模块结构

```
src/pdfs/
├── pdf_processor.py    # ⭐ 统一PDF处理器（新）
├── upload.py          # 上传模块（旧，保留兼容）
├── download.py        # 下载模块（旧，保留兼容）
├── request.py         # 查询模块（旧，保留兼容）
└── pdf_manager.py     # 管理器（旧，保留兼容）
```

**推荐使用**: `pdf_processor.py` - 统一接口，更简洁

---

## 🚀 快速开始

### 方式1: 使用菜单（最简单）

```bash
python menu.py

# 选择对应选项：
# 1. 上传PDF到MinerU
# 2. 查询批次状态  
# 3. 下载解析结果
# 4. PDF处理统计
```

### 方式2: 使用CLI（推荐）

```bash
# 上传PDF
python scripts/cli.py pdf upload

# 查询状态
python scripts/cli.py pdf status <batch_id>

# 下载结果
python scripts/cli.py pdf download <batch_id>

# 列出所有批次
python scripts/cli.py pdf list
```

### 方式3: 直接使用模块

```python
from src.pdfs.pdf_processor import PDFProcessor

processor = PDFProcessor()

# 扫描新PDF
new_pdfs = processor.scan_new_pdfs()

# 上传批次
batch_id = processor.upload_batch(new_pdfs, batch_index=0)

# 查询状态
status = processor.check_batch_status(batch_id)

# 下载结果
result = processor.download_batch(batch_id)
```

---

## 📋 完整工作流程

### 第一步：准备PDF文件

```bash
# 将PDF放入指定目录
cp your_papers/*.pdf data/raw/pdfs/
```

### 第二步：上传到MinerU

```bash
# 使用CLI
python scripts/cli.py pdf upload

# 或使用Python
from src.pdfs.pdf_processor import quick_upload
batch_ids = quick_upload()
```

**输出示例**:
```
📂 扫描目录: data/raw/pdfs
📄 发现 5 个PDF文件
  ✅ 新PDF: paper1.pdf (2.34 MB)
  ✅ 新PDF: paper2.pdf (1.89 MB)
  ⏭️  跳过（已处理）: paper3.pdf

🚀 上传批次 1：2 个文件
📦 获得批次ID: batch_abc123
  上传: paper1.pdf ... ✅
  上传: paper2.pdf ... ✅

✅ 批次上传完成: 2/2 成功
🔗 访问地址: https://mineru.net/batch/batch_abc123
```

### 第三步：查询处理状态

```bash
# 查询单个批次
python scripts/cli.py pdf status batch_abc123

# 或查询所有批次
python scripts/cli.py pdf list
```

**输出示例**:
```
🔍 查询批次: batch_abc123
📊 批次状态:
  总文件数: 2
  ✅ 已完成: 2
  ⏳ 处理中: 0
  ❌ 失败: 0
  🎉 批次已全部完成！
```

**状态说明**:
- `done` - 已完成，可以下载
- `processing` / `waiting` - 处理中，需要等待
- `failed` - 处理失败

### 第四步：下载解析结果

```bash
# 下载批次结果
python scripts/cli.py pdf download batch_abc123

# 指定输出目录
python scripts/cli.py pdf download batch_abc123 --output /custom/path
```

**输出示例**:
```
📥 下载批次: batch_abc123
📁 输出目录: data/processed/parsed

📄 paper1.pdf
  状态: done
  ⬇️ 下载中...
  📦 解压中...
  ✅ 完成: data/processed/parsed/paper1

📄 paper2.pdf
  状态: done
  ⬇️ 下载中...
  📦 解压中...
  ✅ 完成: data/processed/parsed/paper2

============================================================
📊 下载统计:
  ✅ 成功: 2
  ❌ 失败: 0
  ⏭️  跳过: 0
============================================================
```

**输出结构**:
```
data/processed/parsed/
├── paper1/
│   ├── full.md          # 完整Markdown（用于提取）
│   ├── images/          # 图片
│   └── auto/            # 其他文件
└── paper2/
    ├── full.md
    ├── images/
    └── auto/
```

---

## 🎯 核心功能

### 1. 智能去重

**基于文件哈希**:
- 计算每个PDF的MD5哈希
- 已上传的文件自动跳过
- 即使文件改名也能识别

```python
processor = PDFProcessor()

# 扫描时自动去重
new_pdfs = processor.scan_new_pdfs()
# 只返回新的PDF
```

### 2. 状态持久化

**SQLite数据库**:
```
data/uploads/pdf_state.db
├── pdf_files表         # 每个PDF的状态
├── batches表          # 每个批次的信息
└── download_records表 # 下载记录
```

**状态流转**:
```
pending → uploaded → downloaded
```

### 3. 断点续传

**自动恢复**:
- 上传中断？重新运行自动跳过已上传
- 下载中断？重新运行自动跳过已下载
- 查询批次？自动读取数据库记录

### 4. 批量处理

**自动分批**:
- 默认每批200个文件（可配置）
- 自动分批上传
- 返回所有batch_id

---

## 🔧 高级用法

### 自定义PDF目录

```bash
python scripts/cli.py pdf upload --dir /path/to/pdfs
```

### 自定义输出目录

```bash
python scripts/cli.py pdf download batch_abc123 --output /path/to/output
```

### 并行上传多个批次

```python
from src.pdfs.pdf_processor import PDFProcessor
from pathlib import Path

processor = PDFProcessor()

# 扫描
pdfs = processor.scan_new_pdfs()

# 分3批
batch_size = len(pdfs) // 3

for i in range(3):
    start = i * batch_size
    end = start + batch_size if i < 2 else len(pdfs)
    batch_pdfs = pdfs[start:end]
    
    batch_id = processor.upload_batch(batch_pdfs, i)
    print(f"批次 {i+1}: {batch_id}")
```

---

## 📊 状态管理

### 查看PDF文件状态

```python
from src.pdfs.pdf_processor import PDFProcessor

processor = PDFProcessor()

# 查看统计
stats = processor.get_statistics()
print(f"总PDF: {stats['total_pdfs']}")
print(f"待上传: {stats['pending']}")
print(f"已上传: {stats['uploaded']}")
print(f"已下载: {stats['downloaded']}")
```

### 查看批次信息

```python
# 列出所有批次
batches = processor.list_batches()

for batch in batches:
    print(f"批次: {batch['batch_id']}")
    print(f"  文件数: {batch['file_count']}")
    print(f"  状态: {batch['status']}")
```

### 查看待处理PDF

```python
# 列出pending状态的PDF
pending = processor.list_pending_pdfs()

for pdf in pending:
    print(f"{pdf['filename']}: {pdf['file_size']/1024/1024:.2f} MB")
```

---

## 🐛 故障排除

### 问题1: 上传失败

**检查**:
```bash
# 检查API配置
cat .env | grep MINERU

# 测试API连接
curl -H "Authorization: Bearer $MINERU_TOKEN" \
     https://mineru.net/api/v4/file-urls/batch
```

**解决方案**:
1. 确认MINERU_TOKEN配置正确
2. 检查API_BASE地址
3. 确认网络连接

### 问题2: 批次状态一直是processing

**说明**: MinerU处理需要时间（5-30分钟）

**解决方案**:
```bash
# 定期查询状态
python scripts/cli.py pdf status batch_id

# 或使用watch命令自动刷新
watch -n 60 "python scripts/cli.py pdf status batch_id"
```

### 问题3: 下载的文件找不到full.md

**检查**:
```bash
# 查看下载的文件结构
ls -la data/processed/parsed/paper_name/

# 应该包含：
# - full.md (完整Markdown)
# - images/ (图片目录)
# - auto/ (其他文件)
```

**解决方案**:
1. 确认批次状态为done
2. 重新下载: `python scripts/cli.py pdf download batch_id`
3. 检查MinerU服务是否正常

### 问题4: 重复上传相同PDF

**说明**: 系统基于文件哈希自动去重

**验证**:
```python
from src.pdfs.pdf_processor import PDFProcessor

processor = PDFProcessor()
new_pdfs = processor.scan_new_pdfs()
# 返回为空表示全部已处理
```

---

## 🔍 API参考

### PDFProcessor类

```python
class PDFProcessor:
    """PDF处理器"""
    
    def __init__(self, db_path: Path = None)
    
    def scan_new_pdfs(self, pdf_dir: Path = None) -> List[Path]
        """扫描新PDF（去重）"""
    
    def upload_batch(self, pdfs: List[Path], batch_index: int = 0) -> Optional[str]
        """上传批次到MinerU"""
    
    def check_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]
        """查询批次状态"""
    
    def download_batch(self, batch_id: str, output_dir: Path = None) -> Dict[str, Any]
        """下载批次结果"""
    
    def get_statistics(self) -> Dict[str, Any]
        """获取统计信息"""
    
    def list_batches(self) -> List[Dict[str, Any]]
        """列出所有批次"""
    
    def list_pending_pdfs(self) -> List[Dict[str, Any]]
        """列出待处理PDF"""
```

### 便捷函数

```python
def quick_upload(pdf_dir: Path = None) -> List[str]
    """快速上传：扫描+上传"""

def quick_status(batch_id: str = None) -> None
    """快速查询：单个或所有批次"""

def quick_download(batch_id: str, output_dir: Path = None) -> bool
    """快速下载：下载批次"""

def show_stats() -> None
    """显示统计信息"""
```

---

## 📝 配置说明

### 环境变量（.env）

```bash
# MinerU API配置
MINERU_TOKEN=your_token_here
MINERU_API_BASE=https://mineru.net/api/v4
MINERU_WEB_BASE=https://mineru.net/batch

# 处理配置
BATCH_SIZE=200              # 每批文件数
HTTP_REQUEST_TIMEOUT=30     # 请求超时（秒）
DOWNLOAD_TIMEOUT=300        # 下载超时（秒）
DOWNLOAD_RETRY=3           # 重试次数
```

### 目录结构（settings.py）

```python
PDF_DIR = Path("data/raw/pdfs")              # 原始PDF
PARSED_DIR = Path("data/processed/parsed")   # 解析结果
DB_PATH = Path("data/uploads/pdf_state.db")  # 状态数据库
```

---

## 🎯 最佳实践

### 1. 批量处理流程

```bash
# 1. 将所有PDF放入目录
cp papers/*.pdf data/raw/pdfs/

# 2. 上传
python scripts/cli.py pdf upload

# 3. 等待5-30分钟

# 4. 查询状态
python scripts/cli.py pdf status batch_id

# 5. 下载结果
python scripts/cli.py pdf download batch_id
```

### 2. 增量处理

```bash
# 第一批
cp batch1/*.pdf data/raw/pdfs/
python scripts/cli.py pdf upload

# 第二批（自动去重）
cp batch2/*.pdf data/raw/pdfs/
python scripts/cli.py pdf upload
# 只上传新文件
```

### 3. 错误恢复

```bash
# 上传中断了？重新运行
python scripts/cli.py pdf upload
# 自动跳过已上传

# 下载中断了？重新运行
python scripts/cli.py pdf download batch_id
# 自动跳过已下载
```

---

## 🔄 与旧系统的对比

### 旧系统问题
- ❌ 使用CSV管理状态（易损坏）
- ❌ 没有去重逻辑（重复处理）
- ❌ 没有断点续传（中断需重新开始）
- ❌ 分散的模块（upload.py, download.py, request.py）
- ❌ 函数命名不统一

### 新系统优势
- ✅ SQLite数据库（可靠持久化）
- ✅ 基于哈希去重（智能跳过）
- ✅ 支持断点续传（随时恢复）
- ✅ 统一接口（PDFProcessor）
- ✅ 函数命名统一

---

## 📊 数据库Schema

### pdf_files表
```sql
CREATE TABLE pdf_files (
    id INTEGER PRIMARY KEY,
    filename TEXT NOT NULL UNIQUE,
    file_hash TEXT NOT NULL,        -- MD5哈希，用于去重
    file_size INTEGER,
    batch_id TEXT,                  -- 所属批次
    data_id TEXT,                   -- MinerU data_id
    status TEXT DEFAULT 'pending',  -- pending/uploaded/downloaded
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### batches表
```sql
CREATE TABLE batches (
    batch_id TEXT PRIMARY KEY,      -- MinerU批次ID
    batch_index INTEGER,            -- 批次索引
    file_count INTEGER,             -- 文件数量
    status TEXT DEFAULT 'uploaded', -- uploaded/processing/completed/partial
    access_url TEXT,                -- MinerU访问链接
    created_at TIMESTAMP,
    updated_at TIMESTAMP
)
```

### download_records表
```sql
CREATE TABLE download_records (
    id INTEGER PRIMARY KEY,
    batch_id TEXT NOT NULL,
    data_id TEXT NOT NULL,
    filename TEXT,
    output_path TEXT,               -- 下载保存路径
    download_status TEXT,           -- pending/completed
    created_at TIMESTAMP
)
```

---

## 🧪 测试命令

### 测试导入
```bash
python -c "
from src.pdfs.pdf_processor import PDFProcessor
print('✅ Import OK')
"
```

### 测试初始化
```bash
python -c "
from src.pdfs.pdf_processor import PDFProcessor
processor = PDFProcessor()
stats = processor.get_statistics()
print(f'PDF总数: {stats[\"total_pdfs\"]}')
"
```

### 测试CLI
```bash
python scripts/cli.py pdf --help
python scripts/cli.py pdf upload --help
python scripts/cli.py pdf status --help
python scripts/cli.py pdf download --help
```

---

## 💡 Tips

### 提高处理速度
- 一次上传多个PDF（最多200个/批次）
- MinerU并行处理，多个批次可同时进行
- 下载时自动跳过已下载文件

### 节省存储空间
- 下载完成后自动删除ZIP文件
- 只保留解压后的内容

### 监控处理进度
```bash
# 持续监控
watch -n 60 "python scripts/cli.py pdf status batch_id"

# 或使用脚本
while true; do
    python scripts/cli.py pdf status batch_id
    sleep 60
done
```

---

## 📚 相关文档

- **scripts/README.md** - CLI工具说明
- **README.md** - 系统完整文档
- **settings.py** - 配置文件

---

## 🎉 总结

新的PDF处理系统具有以下特点：

✅ **统一接口** - PDFProcessor类封装所有功能  
✅ **智能去重** - 基于文件哈希，避免重复处理  
✅ **状态持久化** - SQLite数据库，可靠追踪  
✅ **断点续传** - 支持中断恢复  
✅ **简洁易用** - 清晰的API，完整的文档  

**推荐使用CLI或Menu进行日常操作，简单高效！** 🚀
