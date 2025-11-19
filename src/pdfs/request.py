"""
查询模块 - 查询批次处理状态
"""
import os
import sys
import csv
import requests
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from settings import (
    MINERU_API_BASE as API_BASE,
    MINERU_HEADERS as HEADERS,
    BATCH_CSV,
    HTTP_REQUEST_TIMEOUT
)


def check_batch_status(batch_id):
    """
    查询单个批次的处理状态
    
    Args:
        batch_id: 批次ID
    
    Returns:
        dict: 批次状态信息
    """
    url = f"{API_BASE}/extract-results/batch/{batch_id}"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=HTTP_REQUEST_TIMEOUT)
        
        if response.status_code != 200:
            return {
                "success": False,
                "error": f"HTTP {response.status_code}"
            }
        
        result = response.json()
        
        if result.get("code") != 0:
            return {
                "success": False,
                "error": result.get("msg", "未知错误")
            }
        
        data = result["data"]
        extract_results = data.get("extract_result", [])
        
        # 统计状态
        total = len(extract_results)
        done = sum(1 for item in extract_results if item.get("state") == "done")
        processing = sum(1 for item in extract_results if item.get("state") in ["processing", "waiting"])
        failed = sum(1 for item in extract_results if item.get("state") == "failed")
        
        return {
            "success": True,
            "batch_id": data.get("batch_id"),
            "total": total,
            "done": done,
            "processing": processing,
            "failed": failed,
            "all_done": done == total,
            "results": extract_results
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


def main():
    """主函数 - 查询所有批次状态"""
    if not os.path.exists(BATCH_CSV):
        print(f"❌ 找不到批次记录文件：{BATCH_CSV}")
        print("请先运行 upload.py 上传文件")
        return
    
    # 读取批次信息
    batches = []
    with open(BATCH_CSV, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        batches = list(reader)
    
    if not batches:
        print("⚠️ 没有找到任何批次信息")
        return
    
    print(f"📋 查询 {len(batches)} 个批次的处理状态\n")
    print("="*80)
    
    total_stats = {
        "total": 0,
        "done": 0,
        "processing": 0,
        "failed": 0
    }
    
    for batch in batches:
        batch_index = batch["batch_index"]
        batch_id = batch["batch_id"]
        
        print(f"\n📦 批次 {batch_index}：{batch_id}")
        
        status = check_batch_status(batch_id)
        
        if not status["success"]:
            print(f"  ❌ 查询失败：{status['error']}")
            continue
        
        total = status["total"]
        done = status["done"]
        processing = status["processing"]
        failed = status["failed"]
        
        total_stats["total"] += total
        total_stats["done"] += done
        total_stats["processing"] += processing
        total_stats["failed"] += failed
        
        print(f"  总文件数：{total}")
        print(f"  ✅ 已完成：{done}")
        print(f"  ⏳ 处理中：{processing}")
        print(f"  ❌ 失败：{failed}")
        
        if status["all_done"]:
            print(f"  🎉 批次已全部完成！")
        else:
            progress = done / total * 100 if total > 0 else 0
            print(f"  📊 进度：{progress:.1f}%")
    
    # 打印总结
    print("\n" + "="*80)
    print("📊 总体状态")
    print("="*80)
    print(f"总文件数：{total_stats['total']}")
    print(f"✅ 已完成：{total_stats['done']}")
    print(f"⏳ 处理中：{total_stats['processing']}")
    print(f"❌ 失败：{total_stats['failed']}")
    
    if total_stats['total'] > 0:
        progress = total_stats['done'] / total_stats['total'] * 100
        print(f"📊 总进度：{progress:.1f}%")
        
        if progress == 100:
            print("\n🎉 所有文件处理完成！可以运行 download.py 下载结果")
        else:
            print(f"\n⏳ 还有 {total_stats['processing']} 个文件正在处理中...")


if __name__ == "__main__":
    main()
