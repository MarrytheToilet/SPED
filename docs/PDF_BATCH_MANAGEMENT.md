# PDF批次管理指南

## 问题说明

在使用MinerU处理PDF时，可能会遇到以下问题：
1. **批次卡住**：部分文件处理完成，但有文件处理失败，无法继续
2. **无法下载**：批次未完全完成，常规下载被阻止
3. **需要重新处理**：想要重置批次状态，重新上传或下载

## 解决方案

### 1. 查看批次状态

```bash
python scripts/pdf_process.py status
```

**输出示例**：
```
📦 批次 3: 0d1d50ce-9e7a-4468-8465-d009e5bb077f
   总计: 10 个文件
   ✅ 完成: 9
   ⏳ 处理中: 0
   ❌ 失败: 1
      - 不同碳含量对钴铬钼摩擦腐蚀的影响.pdf
   ⚠️  批次卡住: 9/10 完成，1 失败，0 处理中
   💡 提示: 可使用 --force-download 下载已完成的 9 个文件
```

### 2. 下载部分完成的批次

当批次中有文件处理失败，但其他文件已完成时，可以下载已完成的文件：

```bash
python scripts/pdf_process.py download --force-partial
```

**特点**：
- ✅ 下载所有已完成（state=done）的文件
- ✅ 跳过失败和处理中的文件
- ✅ 自动标记为已下载

**使用场景**：
- 批次部分失败，但大部分文件已完成
- 不想等待失败文件重试
- 想尽快使用已完成的数据

### 3. 重置批次状态

完全重置批次，允许重新上传和下载：

```bash
python scripts/pdf_process.py reset --batch-id <batch_id>
```

**效果**：
- ❌ 从上传记录中移除
- ❌ 从下载记录中移除
- ✅ 允许重新处理

**后续操作**：
1. 将PDF从 `pdfs_processed/` 移回 `pdfs/`
2. 重新上传：`python scripts/pdf_process.py upload`

**使用场景**：
- 批次完全失败
- 想要重新上传相同的PDF
- 清理测试数据

### 4. 强制重新下载

强制重新下载特定批次（忽略已下载标记）：

```bash
python scripts/pdf_process.py force-download --batch-id <batch_id>
```

**特点**：
- ✅ 忽略"已下载"标记
- ✅ 下载所有已完成的文件
- ✅ 覆盖已存在的文件

**使用场景**：
- 下载的文件损坏或不完整
- 想要重新获取最新版本
- 之前的下载中断

### 5. 常规下载（带去重）

常规下载，跳过已下载的批次：

```bash
python scripts/pdf_process.py download
```

**特点**：
- ✅ 自动跳过已下载的批次
- ✅ 只下载100%完成的批次
- ✅ 安全且高效

## 菜单使用

在 `menu.py` 的PDF处理菜单中：

```
PDF处理流程：

  1. 📤 上传PDF到MinerU（自动去重）
  2. 📊 查询处理状态
  3. 📥 下载解析结果（自动去重）
  4. 📈 查看统计信息
  5. 🔧 完整流程：上传→查询→下载

高级选项：

  6. ⚠️  下载部分完成的批次        → 对应 --force-partial
  7. 🔄 重置卡住的批次            → 对应 reset --batch-id
  8. 🔃 强制重新下载批次          → 对应 force-download --batch-id

  0. 🔙 返回主菜单
```

## 典型场景

### 场景1：批次部分失败

**问题**：10个文件中9个成功，1个失败

**解决方案**：
```bash
# 方式1：下载已完成的9个文件
python scripts/pdf_process.py download --force-partial

# 方式2：在菜单中选择"6. 下载部分完成的批次"
python menu.py  # 然后选择 P → 6
```

### 场景2：下载后发现文件有问题

**问题**：已下载的文件损坏或缺失

**解决方案**：
```bash
# 方式1：命令行强制重新下载
python scripts/pdf_process.py force-download --batch-id <batch_id>

# 方式2：在菜单中操作
python menu.py  # 然后选择 P → 8 → 输入batch_id
```

### 场景3：批次完全卡住

**问题**：批次长时间无进展，想重新开始

**解决方案**：
```bash
# 步骤1：重置批次状态
python scripts/pdf_process.py reset --batch-id <batch_id>

# 步骤2：移动PDF文件
mv data/raw/pdfs_processed/xxx.pdf data/raw/pdfs/

# 步骤3：重新上传
python scripts/pdf_process.py upload
```

### 场景4：查看哪些批次有问题

**解决方案**：
```bash
python scripts/pdf_process.py status
```

**输出会自动高亮**：
- ✅ 完全成功的批次
- ⏳ 处理中的批次
- ⚠️  卡住的批次（会单独列出）

## 状态文件

系统维护一个状态文件：`data/uploads/processing_status.json`

**结构**：
```json
{
  "uploaded": {
    "paper1.pdf": "batch_id_1",
    "paper2.pdf": "batch_id_2"
  },
  "downloaded": [
    "batch_id_1",
    "batch_id_2"
  ],
  "analyzed": []
}
```

**字段说明**：
- `uploaded`: 已上传的PDF及其batch_id
- `downloaded`: 已下载的batch_id列表
- `analyzed`: 已分析的论文（预留）

**手动编辑**（高级用户）：
```bash
# 备份
cp data/uploads/processing_status.json data/uploads/processing_status.json.bak

# 编辑（移除某个batch_id）
nano data/uploads/processing_status.json
```

## 命令速查表

| 操作 | 命令 | 说明 |
|------|------|------|
| 查看状态 | `python scripts/pdf_process.py status` | 查看所有批次状态 |
| 常规下载 | `python scripts/pdf_process.py download` | 下载100%完成的批次 |
| 部分下载 | `python scripts/pdf_process.py download --force-partial` | 下载部分完成的批次 |
| 强制下载 | `python scripts/pdf_process.py download --force` | 强制重新下载所有 |
| 重置批次 | `python scripts/pdf_process.py reset --batch-id <id>` | 重置特定批次 |
| 单独下载 | `python scripts/pdf_process.py force-download --batch-id <id>` | 强制下载特定批次 |

## 最佳实践

1. **定期查看状态**
   ```bash
   python scripts/pdf_process.py status
   ```

2. **优先使用部分下载**
   - 有文件失败时，先下载已完成的
   - 失败的文件可以单独重新上传

3. **保留备份**
   - 重要的PDF保留原始文件
   - 定期备份 `processing_status.json`

4. **失败文件处理**
   - 检查PDF是否损坏
   - 确认文件大小是否合理
   - 可以尝试转换格式后重新上传

5. **避免频繁重置**
   - 重置会丢失处理进度
   - 优先使用部分下载

## 故障排查

### Q: 批次一直显示"处理中"但无进展？

**A**: 
1. 查看处理时间（在upload_batches.csv中）
2. 如果超过24小时无进展，可能已卡住
3. 使用 `--force-partial` 下载已完成的
4. 联系MinerU支持团队

### Q: 下载的文件不完整？

**A**:
1. 检查网络连接
2. 使用 `force-download` 重新下载
3. 查看日志文件确认错误信息

### Q: 重置后还是无法重新上传？

**A**:
1. 确认PDF已从 `pdfs_processed/` 移回 `pdfs/`
2. 检查 `processing_status.json` 是否已更新
3. 如果还有问题，手动编辑状态文件

## 总结

- ✅ **正常流程**：upload → status → download
- ⚠️  **批次卡住**：使用 `--force-partial` 下载已完成的
- 🔄 **重新处理**：reset → 移动PDF → upload
- 🔃 **重新下载**：force-download --batch-id <id>

系统现在能够智能处理各种异常情况，确保数据不会丢失！
