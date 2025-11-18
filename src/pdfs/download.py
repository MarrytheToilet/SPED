"""
下载模块 - 下载并解压处理结果
"""
import os
import sys
import csv
import time
import requests
import zipfile
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from settings import (
    MINERU_API_BASE as API_BASE,
    MINERU_HEADERS as HEADERS,
    BATCH_CSV,
    PARSED_DIR,
    DOWNLOAD_RETRY,
    DOWNLOAD_TIMEOUT
)

# OUTPUT_DIR是parsed/output
OUTPUT_DIR = PARSED_DIR / "output"


def get_batch_results(batch_id):
    """
    获取批次处理结果
    
    Args:
        batch_id: 批次ID
    
    Returns:
        dict: 包含批次结果的字典，失败返回None
    """
    url = f"{API_BASE}/extract-results/batch/{batch_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        if response.status_code != 200:
            print(f"❌ 获取批次结果失败：HTTP {response.status_code}")
            return None
        
        result = response.json()
        if result.get("code") != 0:
            print(f"❌ 获取失败：{result.get('msg', '未知错误')}")
            return None
        
        return result["data"]
    except Exception as e:
        print(f"❌ 请求异常：{e}")
        return None


def download_file(url, save_path, retry=DOWNLOAD_RETRY):
    """
    下载文件（带重试）
    
    Args:
        url: 下载链接
        save_path: 保存路径
        retry: 重试次数
    
    Returns:
        bool: 下载成功返回True
    """
    for attempt in range(retry):
        try:
            response = requests.get(url, timeout=DOWNLOAD_TIMEOUT, stream=True)
            if response.status_code == 200:
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                return True
            else:
                print(f"⚠️ 下载失败 (尝试 {attempt+1}/{retry})：HTTP {response.status_code}")
        except Exception as e:
            print(f"⚠️ 下载异常 (尝试 {attempt+1}/{retry})：{e}")
        
        if attempt < retry - 1:
            time.sleep(2)
    
    return False


def unzip_file(zip_path, extract_to):
    """
    解压ZIP文件
    
    Args:
        zip_path: ZIP文件路径
        extract_to: 解压目标目录
    
    Returns:
        bool: 解压成功返回True
    """
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return True
    except Exception as e:
        print(f"❌ 解压失败：{e}")
        return False


def process_batch(batch_id, batch_index):
    """
    处理单个批次：下载和解压
    
    Args:
        batch_id: 批次ID
        batch_index: 批次索引
    
    Returns:
        dict: 处理结果统计
    """
    print(f"\n📥 开始处理批次 {batch_index}：{batch_id}")
    
    # 获取批次结果
    batch_data = get_batch_results(batch_id)
    if not batch_data:
        return {"success": 0, "failed": 0, "total": 0}
    
    extract_results = batch_data.get("extract_result", [])
    total = len(extract_results)
    success = 0
    failed = 0
    
    # 创建批次输出目录
    batch_dir = OUTPUT_DIR / f"batch_{batch_index}"
    os.makedirs(batch_dir, exist_ok=True)
    
    print(f"📊 批次包含 {total} 个文件")
    
    for item in extract_results:
        data_id = item.get("data_id", "unknown")
        file_name = item.get("file_name", "unknown.pdf")
        state = item.get("state", "unknown")
        zip_url = item.get("full_zip_url", "")
        
        print(f"\n处理文件：{file_name}")
        print(f"  状态：{state}")
        print(f"  Data ID：{data_id}")
        
        if state != "done" or not zip_url:
            print(f"  ⚠️ 跳过（状态：{state}）")
            failed += 1
            continue
        
        # 下载ZIP文件
        safe_name = "".join(c if c.isalnum() or c in "._- " else "_" for c in os.path.splitext(file_name)[0])
        zip_path = batch_dir / f"{safe_name}.zip"
        extract_dir = batch_dir / safe_name
        
        print(f"  ⬇️ 下载中...")
        if download_file(zip_url, zip_path):
            print(f"  ✅ 下载完成")
            
            # 解压文件
            print(f"  📦 解压中...")
            if unzip_file(zip_path, extract_dir):
                print(f"  ✅ 解压完成：{extract_dir}")
                # 删除ZIP文件以节省空间
                os.remove(zip_path)
                success += 1
            else:
                print(f"  ❌ 解压失败")
                failed += 1
        else:
            print(f"  ❌ 下载失败")
            failed += 1
    
    print(f"\n✅ 批次 {batch_index} 处理完成：成功 {success}/{total}，失败 {failed}/{total}")
    
    return {"success": success, "failed": failed, "total": total}


def main():
    """主函数 - 下载所有批次的处理结果"""
    if not os.path.exists(BATCH_CSV):
        print(f"❌ 找不到批次记录文件：{BATCH_CSV}")
        print("请先运行 upload.py 上传文件")
        return
    
    # 创建输出目录
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # 读取批次信息
    batches = []
    with open(BATCH_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batches = list(reader)
    
    if not batches:
        print("⚠️ 没有找到任何批次信息")
        return
    
    print(f"📋 发现 {len(batches)} 个批次")
    
    # 处理所有批次
    total_stats = {"success": 0, "failed": 0, "total": 0}
    
    for batch in batches:
        batch_index = batch["batch_index"]
        batch_id = batch["batch_id"]
        
        stats = process_batch(batch_id, batch_index)
        total_stats["success"] += stats["success"]
        total_stats["failed"] += stats["failed"]
        total_stats["total"] += stats["total"]
    
    # 打印总结
    print("\n" + "="*60)
    print("📊 下载汇总")
    print("="*60)
    print(f"总文件数：{total_stats['total']}")
    print(f"成功：{total_stats['success']}")
    print(f"失败：{total_stats['failed']}")
    print(f"成功率：{total_stats['success']/total_stats['total']*100:.1f}%" if total_stats['total'] > 0 else "N/A")
    print(f"\n所有文件已保存到：{OUTPUT_DIR}")


if __name__ == "__main__":
    main()
