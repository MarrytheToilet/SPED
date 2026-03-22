#!/usr/bin/env python3
"""
PDF处理快捷脚本 - 直接调用pdf_processor模块

使用示例:
  python scripts/pdf.py upload                    # 上传PDF
  python scripts/pdf.py status [batch_id]         # 查询状态
  python scripts/pdf.py download batch_id         # 下载结果
  python scripts/pdf.py stats                     # 查看统计
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pdfs.pdf_processor import main

if __name__ == "__main__":
    sys.exit(main())
