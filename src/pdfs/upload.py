"""
上传模块 - 批量上传PDF文件到MinerU API
"""
import os
import sys
import csv
import requests
from glob import glob
from math import ceil
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from settings import (
    MINERU_API_BASE as API_BASE,
    MINERU_HEADERS as HEADERS,
    MINERU_WEB_BASE as WEB_BASE,
    PDF_DIR,
    BATCH_CSV,
    BATCH_SIZE,
    UPLOAD_CONFIG,
    FILE_CONFIG
)

def upload_batch(batch_files, batch_index):
    """
    上传一批PDF文件
    
    Args:
        batch_files: PDF文件路径列表
        batch_index: 批次索引（从0开始）
    
    Returns:
        batch_id: 批次ID，失败返回None
    """
    print(f"\n🚀 开始上传第 {batch_index+1} 批，共 {len(batch_files)} 个文件")

    # 1️⃣ 申请上传URL
    files_data = []
    for idx, pdf in enumerate(batch_files):
        filename = os.path.basename(pdf)
        base_name = os.path.splitext(filename)[0]
        
        # 限制data_id长度，避免超过128字符
        if len(base_name) > 60:
            base_name = base_name[:60]
        
        data_id = f"b{batch_index+1}_{idx+1}_{base_name}"
        
        files_data.append({
            "name": filename,
            "data_id": data_id,
            **FILE_CONFIG
        })

    response = requests.post(
        f"{API_BASE}/file-urls/batch",
        headers=HEADERS,
        json={
            **UPLOAD_CONFIG,
            "files": files_data,
        },
    )

    if response.status_code != 200:
        print(f"❌ 申请上传URL失败：HTTP {response.status_code}")
        print(response.text)
        return None

    result = response.json()
    if result.get("code") != 0:
        print(f"❌ 申请失败：{result.get('msg', '未知错误')}")
        return None

    batch_id = result["data"]["batch_id"]
    urls = result["data"]["file_urls"]

    # 2️⃣ 上传文件
    success = 0
    for pdf_path, upload_url in zip(batch_files, urls):
        with open(pdf_path, "rb") as f:
            res = requests.put(upload_url, data=f)
            if res.status_code in [200, 201]:
                success += 1
                print(f"✅ 成功上传：{os.path.basename(pdf_path)}")
            else:
                print(f"❌ 上传失败：{os.path.basename(pdf_path)} | 状态码：{res.status_code}")

    # 3️⃣ 打印 & 保存结果
    print(f"🎯 批次完成：成功 {success}/{len(batch_files)} 个文件")
    print(f"📦 批次 ID：{batch_id}")
    access_url = f"{WEB_BASE}/{batch_id}"
    print(f"🔗 访问地址：{access_url}\n")

    # ✅ 追加保存到 CSV
    os.makedirs(os.path.dirname(BATCH_CSV), exist_ok=True)
    with open(BATCH_CSV, "a", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([batch_index + 1, batch_id, len(batch_files), access_url])

    return batch_id


def main():
    """主函数 - 批量上传PDF文件"""
    pdf_files = glob(str(PDF_DIR / "*.pdf"))
    if not pdf_files:
        print(f"⚠️ 没有找到 PDF 文件：{PDF_DIR}")
        return

    total_batches = ceil(len(pdf_files) / BATCH_SIZE)
    print(f"共发现 {len(pdf_files)} 个 PDF 文件，将分成 {total_batches} 批上传。")

    # 初始化 CSV
    if not os.path.exists(BATCH_CSV):
        with open(BATCH_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["batch_index", "batch_id", "file_count", "access_url"])

    all_batches = []
    for i in range(total_batches):
        start = i * BATCH_SIZE
        end = start + BATCH_SIZE
        batch_files = pdf_files[start:end]
        batch_id = upload_batch(batch_files, i)
        if batch_id:
            all_batches.append(batch_id)

    print("\n✅ 所有批次上传完成！结果已保存至：upload_batches.csv")
    for b in all_batches:
        print(f"📦 批次ID：{b} | 访问链接：{WEB_BASE}/{b}")


if __name__ == "__main__":
    main()
