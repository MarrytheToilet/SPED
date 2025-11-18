#!/usr/bin/env python3
"""
优化的PDF处理Pipeline - 智能去重版本
功能：
1. 上传PDF（自动去重，已上传的移到processed目录）
2. 查询状态
3. 下载结果（自动去重，跳过已下载）
"""
import os, sys, csv, json, time, shutil, requests, zipfile, argparse
from math import ceil
from pathlib import Path
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except: pass

sys.path.insert(0, str(Path(__file__).parent.parent))

# ==================== 配置 ====================
MINERU_API_BASE = os.getenv("MINERU_API_BASE", "https://mineru.net/api/v4")
MINERU_TOKEN = os.getenv("MINERU_TOKEN", "")
HEADERS = {"Authorization": f"Bearer {MINERU_TOKEN}", "Content-Type": "application/json"}

PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PDF_DIR = DATA_DIR / "raw" / "pdfs"
PROCESSED_PDF_DIR = DATA_DIR / "raw" / "pdfs_processed"  # 已处理的PDF
OUTPUT_DIR = DATA_DIR / "processed" / "parsed" / "output"
BATCH_CSV = DATA_DIR / "uploads" / "upload_batches.csv"
STATUS_JSON = DATA_DIR / "uploads" / "processing_status.json"  # 状态追踪

for d in [PDF_DIR, PROCESSED_PDF_DIR, OUTPUT_DIR, BATCH_CSV.parent]:
    Path(d).mkdir(parents=True, exist_ok=True)

BATCH_SIZE = 10
UPLOAD_CONFIG = {"parse_method": "auto", "apply_ocr": False}
FILE_CONFIG = {"parse_method": "auto", "apply_ocr": False}

# ==================== 状态管理器 ====================
class StatusManager:
    """处理状态管理器 - 避免重复处理"""
    
    def __init__(self):
        self.status_file = STATUS_JSON
        self.status = self._load()
    
    def _load(self):
        if self.status_file.exists():
            with open(self.status_file) as f:
                return json.load(f)
        return {"uploaded": {}, "downloaded": [], "analyzed": []}
    
    def _save(self):
        with open(self.status_file, 'w') as f:
            json.dump(self.status, f, ensure_ascii=False, indent=2)
    
    def is_uploaded(self, pdf_name):
        """检查PDF是否已上传"""
        return pdf_name in self.status["uploaded"]
    
    def mark_uploaded(self, pdf_name, batch_id):
        """标记PDF已上传"""
        self.status["uploaded"][pdf_name] = batch_id
        self._save()
    
    def is_downloaded(self, batch_id):
        """检查batch是否已下载"""
        return batch_id in self.status["downloaded"]
    
    def mark_downloaded(self, batch_id):
        """标记batch已下载"""
        if batch_id not in self.status["downloaded"]:
            self.status["downloaded"].append(batch_id)
            self._save()
    
    def get_stats(self):
        return {
            "uploaded": len(self.status["uploaded"]),
            "downloaded": len(self.status["downloaded"]),
            "analyzed": len(self.status["analyzed"])
        }

status_mgr = StatusManager()

# ==================== 工具函数 ====================
def create_session():
    s = requests.Session()
    s.mount('http://', HTTPAdapter(max_retries=Retry(total=3)))
    s.mount('https://', HTTPAdapter(max_retries=Retry(total=3)))
    return s

def sanitize(name):
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in Path(name).stem)

def download_file(url, path):
    for i in range(3):
        try:
            r = requests.get(url, timeout=120, stream=True)
            if r.status_code == 200:
                with open(path, 'wb') as f:
                    for chunk in r.iter_content(8192):
                        f.write(chunk)
                return True
        except: time.sleep(2)
    return False

def unzip_file(zip_path, dest):
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(dest)
        return True
    except: return False

# ==================== 上传命令 ====================
def cmd_upload(args):
    pdf_dir = Path(args.input) if args.input else PDF_DIR
    pdfs = list(pdf_dir.glob("*.pdf"))
    
    if not pdfs:
        print(f"⚠️  未找到PDF: {pdf_dir}")
        return
    
    stats = status_mgr.get_stats()
    print(f"\n📊 状态统计:")
    print(f"   已上传: {stats['uploaded']} 个PDF")
    print(f"   已下载: {stats['downloaded']} 个批次")
    print(f"   已分析: {stats['analyzed']} 篇论文")
    print(f"\n📁 发现 {len(pdfs)} 个PDF，分 {ceil(len(pdfs)/BATCH_SIZE)} 批上传\n")
    
    # 检查已有的batch ID，避免重复
    existing_batch_ids = set()
    if BATCH_CSV.exists():
        with open(BATCH_CSV) as f:
            reader = csv.DictReader(f)
            for row in reader:
                if 'batch_id' in row:
                    existing_batch_ids.add(row['batch_id'])
        print(f"🔍 已有批次记录: {len(existing_batch_ids)} 个")
        if existing_batch_ids:
            print(f"   最近批次: {list(existing_batch_ids)[-3:]}")
        print()
    else:
        with open(BATCH_CSV, 'w') as f:
            csv.writer(f).writerow(["batch_index", "batch_id", "file_count", "access_url", "time"])
    
    session = create_session()
    uploaded_total = 0
    skipped_total = 0
    
    for batch_idx in range(ceil(len(pdfs)/BATCH_SIZE)):
        batch = pdfs[batch_idx*BATCH_SIZE:(batch_idx+1)*BATCH_SIZE]
        
        # 过滤已上传的PDF
        to_upload = []
        for pdf in batch:
            if status_mgr.is_uploaded(pdf.name):
                print(f"⏭️  跳过（已上传）: {pdf.name}")
                skipped_total += 1
            else:
                to_upload.append(pdf)
        
        if not to_upload:
            print(f"📦 批次 {batch_idx+1}: 全部已上传，跳过\n")
            continue
        
        print(f"\n📦 批次 {batch_idx+1}: {len(to_upload)} 个新文件（跳过{len(batch)-len(to_upload)}个）")
        
        # 准备上传数据
        files_data = []
        for i, p in enumerate(to_upload):
            name = p.stem[:60] if len(p.stem) > 60 else p.stem
            files_data.append({
                "name": p.name,
                "data_id": f"b{batch_idx+1}_{i+1}_{name}",
                **FILE_CONFIG
            })
        
        try:
            # 申请上传
            r = session.post(f"{MINERU_API_BASE}/file-urls/batch",
                           headers=HEADERS,
                           json={**UPLOAD_CONFIG, "files": files_data},
                           timeout=30)
            
            if r.status_code != 200 or r.json().get("code") != 0:
                print(f"  ❌ 申请失败: {r.json().get('msg', 'Unknown error')}")
                continue
            
            batch_id = r.json()["data"]["batch_id"]
            urls = r.json()["data"]["file_urls"]
            
            # 检查batch_id是否重复
            if batch_id in existing_batch_ids:
                print(f"  ⚠️  警告：batch_id 重复！{batch_id}")
                print(f"  此batch已存在于upload_batches.csv中")
                print(f"  跳过保存到CSV，但继续上传...")
            
            # 上传文件并移动
            success = 0
            for pdf, url in zip(to_upload, urls):
                with open(pdf, 'rb') as f:
                    if session.put(url, data=f, timeout=120).status_code in [200, 201]:
                        # 标记已上传
                        status_mgr.mark_uploaded(pdf.name, batch_id)
                        # 移动到processed目录
                        dest = PROCESSED_PDF_DIR / pdf.name
                        shutil.move(str(pdf), str(dest))
                        success += 1
                        uploaded_total += 1
                        print(f"  ✅ {pdf.name} → 已移至 pdfs_processed/")
                    else:
                        print(f"  ❌ {pdf.name}")
            
            print(f"  完成: {success}/{len(to_upload)}")
            print(f"  Batch ID: {batch_id}")
            print(f"  访问: https://mineru.net/extract/batch/{batch_id}")
            print(f"  ℹ️  MinerU将自动开始处理批次")
            
            # 保存批次记录（只有非重复的才保存）
            if batch_id not in existing_batch_ids:
                with open(BATCH_CSV, 'a') as f:
                    csv.writer(f).writerow([
                        batch_idx+1, batch_id, len(to_upload),
                        f"https://mineru.net/extract/batch/{batch_id}",
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    ])
                existing_batch_ids.add(batch_id)  # 添加到集合中
                print(f"  ✓ 批次记录已保存到CSV")
            else:
                print(f"  ⏭️  批次记录已存在，跳过保存")
        
        except Exception as e:
            print(f"  ❌ 异常: {e}")
        
        time.sleep(1)
    
    print(f"\n{'='*70}")
    print(f"✅ 上传完成!")
    print(f"   新上传: {uploaded_total} 个PDF")
    print(f"   已跳过: {skipped_total} 个PDF（已上传过）")
    print(f"   状态追踪: {STATUS_JSON}")
    print(f"   已上传PDF已移至: {PROCESSED_PDF_DIR}")
    print(f"{'='*70}")
    print(f"\n💡 下一步: python {Path(__file__).name} status")

# ==================== 查询命令 ====================
def cmd_status(args):
    if not BATCH_CSV.exists():
        print("⚠️  未找到批次记录")
        return
    
    with open(BATCH_CSV) as f:
        batches = list(csv.DictReader(f))
    
    print(f"\n{'='*70}\n📊 批次处理状态\n{'='*70}\n")
    
    session = create_session()
    for b in batches:
        bid, idx = b['batch_id'], b['batch_index']
        print(f"📦 批次 {idx}: {bid}")
        
        try:
            r = session.get(f"{MINERU_API_BASE}/extract-results/batch/{bid}",
                          headers=HEADERS, timeout=30)
            if r.status_code == 200 and r.json().get("code") == 0:
                d = r.json()["data"]
                extract_results = d.get("extract_result", [])
                total = len(extract_results)
                done = sum(1 for item in extract_results if item.get("state") == "done")
                processing = sum(1 for item in extract_results if item.get("state") in ["processing", "waiting"])
                failed = sum(1 for item in extract_results if item.get("state") == "failed")
                
                print(f"   总计: {total} 个文件")
                print(f"   ✅ 完成: {done}")
                print(f"   ⏳ 处理中: {processing}")
                if failed > 0:
                    print(f"   ❌ 失败: {failed}")
                if done == total and total > 0:
                    is_dl = status_mgr.is_downloaded(bid)
                    print(f"   下载: {'✅ 已下载' if is_dl else '⬇️  待下载'}")
        except Exception as e:
            print(f"   ❌ {e}")
        print()
    
    stats = status_mgr.get_stats()
    print(f"{'='*70}")
    print(f"📊 总计:")
    print(f"   已上传: {stats['uploaded']} 个PDF")
    print(f"   已下载: {stats['downloaded']} 个批次")
    print(f"   已分析: {stats['analyzed']} 篇论文")
    print(f"{'='*70}")
    print(f"\n💡 下一步: python {Path(__file__).name} download")

# ==================== 下载命令 ====================
def cmd_download(args):
    out = Path(args.output) if args.output else OUTPUT_DIR
    
    if not BATCH_CSV.exists():
        print("⚠️  未找到批次记录")
        return
    
    with open(BATCH_CSV) as f:
        batches = list(csv.DictReader(f))
    
    print(f"\n{'='*70}\n⬇️  下载解析结果\n{'='*70}\n")
    
    session = create_session()
    new, skipped = 0, 0
    
    for b in batches:
        bid, idx = b['batch_id'], b['batch_index']
        
        # 检查是否已下载
        if status_mgr.is_downloaded(bid):
            print(f"📦 批次 {idx}: {bid}")
            print(f"   ⏭️  已下载，跳过\n")
            skipped += 1
            continue
        
        print(f"📦 批次 {idx}: {bid}")
        
        try:
            r = session.get(f"{MINERU_API_BASE}/extract-results/batch/{bid}",
                          headers=HEADERS, timeout=30)
            
            if r.status_code != 200 or r.json().get("code") != 0:
                print("  ❌ 查询失败\n")
                continue
            
            d = r.json()["data"]
            extract_results = d.get("extract_result", [])
            total = len(extract_results)
            done = sum(1 for item in extract_results if item.get("state") == "done")
            
            if done < total:
                print(f"  ⏳ 处理中: {done}/{total} 个文件完成\n")
                continue
            
            # 下载文件
            batch_dir = out / f"batch_{idx}"
            batch_dir.mkdir(exist_ok=True)
            success = 0
            
            for f_info in extract_results:
                if f_info.get("state") != "done":
                    continue
                
                did = f_info.get("data_id", "unknown")
                url = f_info.get("full_zip_url")
                if not url:
                    continue
                
                safe = sanitize(did)
                zip_path = batch_dir / f"{safe}.zip"
                extract_dir = batch_dir / safe
                
                if download_file(url, zip_path):
                    if unzip_file(zip_path, extract_dir):
                        zip_path.unlink()
                        success += 1
                        print(f"  ✅ {did}")
            
            if success > 0:
                # 标记已下载
                status_mgr.mark_downloaded(bid)
                new += 1
                print(f"  完成: {success} 个文件")
        
        except Exception as e:
            print(f"  ❌ {e}")
        print()
    
    print(f"{'='*70}")
    print(f"✅ 下载完成!")
    print(f"   新下载: {new} 个批次")
    print(f"   已跳过: {skipped} 个批次（已下载过）")
    print(f"   输出目录: {out}")
    print(f"{'='*70}")
    print(f"\n💡 下一步: python test_new_pipeline.py")

# ==================== 主函数 ====================
def main():
    parser = argparse.ArgumentParser(description="PDF Pipeline（智能去重版）")
    sub = parser.add_subparsers(dest='cmd')
    
    up = sub.add_parser('upload', help='上传PDF（自动去重）')
    up.add_argument('-i', '--input', help=f'PDF目录(默认{PDF_DIR})')
    
    sub.add_parser('status', help='查询处理状态')
    
    dl = sub.add_parser('download', help='下载结果（自动去重）')
    dl.add_argument('-o', '--output', help=f'输出目录(默认{OUTPUT_DIR})')
    
    sub.add_parser('stats', help='查看统计信息')
    
    args = parser.parse_args()
    
    if args.cmd:
        print(f"\n{'='*70}")
        print(f"⚙️  配置信息")
        print(f"{'='*70}")
        print(f"MinerU API: {MINERU_API_BASE}")
        print(f"Token: {'✓ 已配置' if MINERU_TOKEN else '✗ 未配置'}")
        print(f"PDF目录: {PDF_DIR}")
        print(f"已处理目录: {PROCESSED_PDF_DIR}")
        print(f"输出目录: {OUTPUT_DIR}")
        print(f"状态追踪: {STATUS_JSON}")
        print(f"{'='*70}")
    
    if args.cmd == 'upload':
        cmd_upload(args)
    elif args.cmd == 'status':
        cmd_status(args)
    elif args.cmd == 'download':
        cmd_download(args)
    elif args.cmd == 'stats':
        s = status_mgr.get_stats()
        print(f"\n📊 处理统计:")
        print(f"   已上传: {s['uploaded']} 个PDF")
        print(f"   已下载: {s['downloaded']} 个批次")
        print(f"   已分析: {s['analyzed']} 篇论文")
        print(f"\n📁 文件位置:")
        print(f"   待上传: {PDF_DIR}")
        print(f"   已上传: {PROCESSED_PDF_DIR}")
        print(f"   解析结果: {OUTPUT_DIR}")
        print(f"   状态文件: {STATUS_JSON}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
