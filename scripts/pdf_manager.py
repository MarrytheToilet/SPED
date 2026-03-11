#!/usr/bin/env python3
"""
改进的PDF处理工具 - 智能化、自动化
功能：
1. 自动扫描和管理PDF
2. 智能去重（基于MD5哈希）
3. 一键上传和下载
4. 自动轮询处理状态
5. 清晰的目录结构
"""
import os
import sys
import json
import time
import shutil
import requests
import zipfile
import argparse
from math import ceil
from pathlib import Path
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / '.env')
except:
    pass

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.pdfs.pdf_manager import PDFManager
import settings

# ==================== 配置 ====================
MINERU_API_BASE = settings.MINERU_API_BASE
MINERU_TOKEN = settings.MINERU_TOKEN
HEADERS = settings.MINERU_HEADERS

PDF_DIR = settings.PDF_DIR
PROCESSED_PDF_DIR = settings.PROCESSED_DIR / "pdfs_uploaded"
PARSED_DIR = settings.PARSED_DIR  # data/processed/parsed/
DB_PATH = settings.DATA_DIR / "uploads" / "pdf_manager.db"

BATCH_SIZE = 10

# 确保目录存在
for d in [PDF_DIR, PROCESSED_PDF_DIR, PARSED_DIR]:
    Path(d).mkdir(parents=True, exist_ok=True)

# 初始化管理器
pdf_mgr = PDFManager(DB_PATH)

# ==================== 颜色输出 ====================
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.CYAN}ℹ️  {msg}{Colors.END}")

def print_header(title):
    print(f"\n{Colors.BLUE}{Colors.BOLD}{'='*70}")
    print(f"{title:^70}")
    print(f"{'='*70}{Colors.END}\n")

# ==================== 工具函数 ====================
def create_session():
    s = requests.Session()
    retry = Retry(total=3, backoff_factor=1)
    s.mount('http://', HTTPAdapter(max_retries=retry))
    s.mount('https://', HTTPAdapter(max_retries=retry))
    return s

def sanitize_name(name):
    """清理文件名"""
    return "".join(c if c.isalnum() or c in "._-" else "_" for c in name)

def download_file(url, path, timeout=120):
    """下载文件"""
    try:
        r = requests.get(url, timeout=timeout, stream=True)
        if r.status_code == 200:
            with open(path, 'wb') as f:
                for chunk in r.iter_content(8192):
                    f.write(chunk)
            return True
    except Exception as e:
        print_error(f"下载失败: {e}")
    return False

def unzip_file(zip_path, dest):
    """解压文件"""
    try:
        with zipfile.ZipFile(zip_path) as z:
            z.extractall(dest)
        return True
    except Exception as e:
        print_error(f"解压失败: {e}")
    return False

# ==================== 命令：扫描PDF ====================
def cmd_scan(args):
    """扫描PDF目录，注册新PDF"""
    print_header("📂 扫描PDF目录")
    
    pdfs = list(PDF_DIR.glob("*.pdf"))
    
    if not pdfs:
        print_warning(f"未找到PDF文件: {PDF_DIR}")
        return
    
    print_info(f"找到 {len(pdfs)} 个PDF文件")
    print()
    
    new_count = 0
    exists_count = 0
    
    for pdf in pdfs:
        is_new, msg = pdf_mgr.add_pdf(pdf)
        if is_new:
            print_success(f"{pdf.name}")
            new_count += 1
        else:
            print_warning(f"{pdf.name} - {msg}")
            exists_count += 1
    
    print()
    print(f"{Colors.BOLD}扫描完成:{Colors.END}")
    print(f"  新增: {new_count} 个")
    print(f"  已存在: {exists_count} 个")
    print()
    
    if new_count > 0:
        print_info("下一步: python scripts/pdf_manager.py upload")

# ==================== 命令：上传PDF ====================
def cmd_upload(args):
    """上传待处理的PDF到MinerU"""
    print_header("📤 上传PDF到MinerU")
    
    # 获取待处理的PDF
    pending = pdf_mgr.get_pending_pdfs()
    
    if not pending:
        print_warning("没有待上传的PDF")
        print_info("提示: 先运行 scan 命令扫描新PDF")
        return
    
    print_info(f"待上传: {len(pending)} 个PDF")
    print()
    
    # 分批上传
    session = create_session()
    max_batch_idx = pdf_mgr.get_max_batch_index()
    
    for batch_idx in range(ceil(len(pending) / BATCH_SIZE)):
        current_batch_idx = max_batch_idx + batch_idx + 1
        batch_start = batch_idx * BATCH_SIZE
        batch_end = min((batch_idx + 1) * BATCH_SIZE, len(pending))
        batch_pdfs = pending[batch_start:batch_end]
        
        print(f"{Colors.BOLD}📦 批次 {current_batch_idx}: {len(batch_pdfs)} 个文件{Colors.END}")
        
        # 准备上传数据
        files_data = []
        pdf_paths = []
        
        for i, pdf_info in enumerate(batch_pdfs):
            pdf_path = PDF_DIR / pdf_info['filename']
            if not pdf_path.exists():
                print_error(f"文件不存在: {pdf_path}")
                continue
            
            pdf_paths.append(pdf_path)
            name = sanitize_name(pdf_path.stem[:60])
            data_id = f"b{current_batch_idx}_{i+1}_{name}"
            
            files_data.append({
                "name": pdf_path.name,
                "data_id": data_id,
                "parse_method": "auto",
                "apply_ocr": False
            })
        
        if not files_data:
            print_warning("批次中没有有效文件，跳过")
            continue
        
        try:
            # 申请上传
            r = session.post(
                f"{MINERU_API_BASE}/file-urls/batch",
                headers=HEADERS,
                json={
                    "parse_method": "auto",
                    "apply_ocr": False,
                    "files": files_data
                },
                timeout=30
            )
            
            if r.status_code != 200 or r.json().get("code") != 0:
                print_error(f"申请上传失败: {r.json().get('msg', 'Unknown')}")
                continue
            
            batch_id = r.json()["data"]["batch_id"]
            file_urls = r.json()["data"]["file_urls"]
            
            print(f"  Batch ID: {Colors.CYAN}{batch_id}{Colors.END}")
            
            # 上传文件
            success = 0
            for pdf_path, url, file_data in zip(pdf_paths, file_urls, files_data):
                with open(pdf_path, 'rb') as f:
                    upload_resp = session.put(url, data=f, timeout=120)
                
                if upload_resp.status_code in [200, 201]:
                    # 更新状态
                    pdf_mgr.update_pdf_status(pdf_path.name, 'uploaded', batch_id)
                    # 移动文件
                    dest = PROCESSED_PDF_DIR / pdf_path.name
                    shutil.move(str(pdf_path), str(dest))
                    print_success(f"  {pdf_path.name}")
                    success += 1
                else:
                    print_error(f"  {pdf_path.name}")
            
            # 保存批次记录
            access_url = f"https://mineru.net/extract/batch/{batch_id}"
            pdf_mgr.add_batch(batch_id, current_batch_idx, success, access_url)
            
            print(f"  {Colors.BOLD}完成: {success}/{len(pdf_paths)}{Colors.END}")
            print(f"  访问: {Colors.CYAN}{access_url}{Colors.END}")
            print()
            
        except Exception as e:
            print_error(f"上传异常: {e}")
        
        time.sleep(1)
    
    print_header("✅ 上传完成")
    stats = pdf_mgr.get_statistics()
    print(f"  待上传: {stats['pending_pdfs']}")
    print(f"  已上传: {stats['uploaded_pdfs']}")
    print()
    print_info("下一步: python scripts/pdf_manager.py status")

# ==================== 命令：查询状态 ====================
def cmd_status(args):
    """查询批次处理状态"""
    print_header("📊 批次处理状态")
    
    batches = pdf_mgr.get_all_batches()
    
    if not batches:
        print_warning("没有批次记录")
        return
    
    session = create_session()
    
    for batch in batches[:20]:  # 只显示最近20个
        batch_id = batch['batch_id']
        batch_idx = batch['batch_index']
        
        print(f"{Colors.BOLD}📦 批次 {batch_idx}: {batch_id[:8]}...{Colors.END}")
        print(f"  状态: {batch['status']}")
        
        try:
            r = session.get(
                f"{MINERU_API_BASE}/extract-results/batch/{batch_id}",
                headers=HEADERS,
                timeout=30
            )
            
            if r.status_code == 200 and r.json().get("code") == 0:
                data = r.json()["data"]
                results = data.get("extract_result", [])
                
                total = len(results)
                done = sum(1 for item in results if item.get("state") == "done")
                processing = sum(1 for item in results if item.get("state") in ["processing", "waiting"])
                failed = sum(1 for item in results if item.get("state") == "failed")
                
                print(f"  总计: {total} | 完成: {Colors.GREEN}{done}{Colors.END} | " +
                      f"处理中: {Colors.YELLOW}{processing}{Colors.END} | " +
                      f"失败: {Colors.RED}{failed}{Colors.END}")
                
                # 保存结果状态
                for item in results:
                    pdf_mgr.add_batch_result(
                        batch_id=batch_id,
                        data_id=item.get("data_id", ""),
                        filename=item.get("file_name", ""),
                        mineru_status=item.get("state", "unknown")
                    )
                
                # 更新批次状态
                if done == total and total > 0:
                    pdf_mgr.update_batch_status(batch_id, 'completed')
                    print_success("  可以下载了！")
                elif done > 0 and processing == 0 and failed > 0:
                    print_warning("  部分失败，可使用 --force-partial 下载已完成的")
            else:
                print_error("  查询失败")
        
        except Exception as e:
            print_error(f"  异常: {e}")
        
        print()
    
    # 统计
    stats = pdf_mgr.get_statistics()
    print(f"{Colors.BOLD}总计:{Colors.END}")
    print(f"  批次数: {stats['total_batches']}")
    print(f"  已完成: {stats['completed_batches']}")
    print()
    
    # 检查是否有可下载的
    completed = [b for b in batches if b['status'] == 'completed']
    if completed:
        print_info(f"有 {len(completed)} 个批次可以下载")
        print_info("运行: python scripts/pdf_manager.py download")

# ==================== 命令：下载结果 ====================
def cmd_download(args):
    """下载解析结果"""
    print_header("⬇️  下载解析结果")
    
    # 获取已完成的批次
    batches = pdf_mgr.get_all_batches()
    completed = [b for b in batches if b['status'] == 'completed']
    
    if not completed:
        print_warning("没有已完成的批次")
        return
    
    session = create_session()
    
    for batch in completed:
        batch_id = batch['batch_id']
        batch_idx = batch['batch_index']
        
        print(f"{Colors.BOLD}📦 批次 {batch_idx}: {batch_id[:8]}...{Colors.END}")
        
        try:
            r = session.get(
                f"{MINERU_API_BASE}/extract-results/batch/{batch_id}",
                headers=HEADERS,
                timeout=30
            )
            
            if r.status_code != 200 or r.json().get("code") != 0:
                print_error("  查询失败")
                continue
            
            results = r.json()["data"].get("extract_result", [])
            done_results = [r for r in results if r.get("state") == "done"]
            
            if not done_results:
                print_warning("  没有已完成的文件")
                continue
            
            success = 0
            for item in done_results:
                data_id = item.get("data_id", "unknown")
                url = item.get("full_zip_url")
                
                if not url:
                    continue
                
                # 使用data_id中的论文名作为目录名
                # data_id格式: b1_1_论文名
                parts = data_id.split('_', 2)
                paper_name = parts[2] if len(parts) > 2 else data_id
                paper_name = sanitize_name(paper_name)
                
                # 直接保存到 parsed/ 目录下
                paper_dir = PARSED_DIR / paper_name
                paper_dir.mkdir(exist_ok=True)
                
                # 下载并解压
                zip_path = paper_dir / "temp.zip"
                if download_file(url, zip_path):
                    if unzip_file(zip_path, paper_dir):
                        zip_path.unlink()
                        
                        # 更新状态
                        pdf_mgr.update_result_download_status(
                            data_id, 'downloaded', str(paper_dir)
                        )
                        
                        print_success(f"  {paper_name}")
                        success += 1
                    else:
                        print_error(f"  解压失败: {paper_name}")
                else:
                    print_error(f"  下载失败: {paper_name}")
            
            if success > 0:
                # 更新批次状态
                pdf_mgr.update_batch_status(batch_id, 'downloaded')
                print(f"  {Colors.BOLD}完成: {success}/{len(done_results)}{Colors.END}")
        
        except Exception as e:
            print_error(f"  异常: {e}")
        
        print()
    
    print_header("✅ 下载完成")
    print(f"  输出目录: {Colors.CYAN}{PARSED_DIR}{Colors.END}")
    print()
    print_info("下一步: 使用菜单进行数据提取")

# ==================== 命令：自动处理 ====================
def cmd_auto(args):
    """自动处理流程：扫描 → 上传 → 轮询 → 下载"""
    print_header("🚀 自动处理流程")
    
    # 1. 扫描
    print(f"{Colors.BOLD}步骤 1/4: 扫描PDF{Colors.END}")
    cmd_scan(args)
    print()
    
    # 2. 上传
    print(f"{Colors.BOLD}步骤 2/4: 上传PDF{Colors.END}")
    cmd_upload(args)
    print()
    
    # 3. 轮询状态
    if args.wait:
        print(f"{Colors.BOLD}步骤 3/4: 等待处理完成{Colors.END}")
        print_info("每30秒检查一次状态...")
        
        max_wait = args.max_wait if hasattr(args, 'max_wait') else 3600  # 默认1小时
        elapsed = 0
        
        while elapsed < max_wait:
            time.sleep(30)
            elapsed += 30
            
            # 检查状态
            batches = pdf_mgr.get_all_batches()
            if not batches:
                break
            
            # 查询最新批次
            latest = batches[0]
            batch_id = latest['batch_id']
            
            try:
                session = create_session()
                r = session.get(
                    f"{MINERU_API_BASE}/extract-results/batch/{batch_id}",
                    headers=HEADERS,
                    timeout=30
                )
                
                if r.status_code == 200 and r.json().get("code") == 0:
                    results = r.json()["data"].get("extract_result", [])
                    total = len(results)
                    done = sum(1 for item in results if item.get("state") == "done")
                    
                    print(f"  [{elapsed}s] 进度: {done}/{total}")
                    
                    if done == total:
                        print_success("处理完成！")
                        pdf_mgr.update_batch_status(batch_id, 'completed')
                        break
            except:
                pass
        
        print()
    
    # 4. 下载
    print(f"{Colors.BOLD}步骤 4/4: 下载结果{Colors.END}")
    cmd_download(args)
    
    print_header("🎉 自动处理完成")

# ==================== 命令：统计信息 ====================
def cmd_stats(args):
    """显示统计信息"""
    print_header("📊 系统统计")
    
    stats = pdf_mgr.get_statistics()
    
    print(f"{Colors.BOLD}PDF文件:{Colors.END}")
    print(f"  总数: {stats['total_pdfs']}")
    print(f"  待上传: {stats['pending_pdfs']}")
    print(f"  已上传: {stats['uploaded_pdfs']}")
    print(f"  已下载: {stats['downloaded_pdfs']}")
    print()
    
    print(f"{Colors.BOLD}批次:{Colors.END}")
    print(f"  总数: {stats['total_batches']}")
    print(f"  已完成: {stats['completed_batches']}")
    print()
    
    print(f"{Colors.BOLD}解析结果:{Colors.END}")
    print(f"  已下载: {stats['downloaded_results']}")
    print()
    
    print(f"{Colors.BOLD}目录:{Colors.END}")
    print(f"  PDF输入: {Colors.CYAN}{PDF_DIR}{Colors.END}")
    print(f"  已上传: {Colors.CYAN}{PROCESSED_PDF_DIR}{Colors.END}")
    print(f"  解析输出: {Colors.CYAN}{PARSED_DIR}{Colors.END}")
    print(f"  数据库: {Colors.CYAN}{DB_PATH}{Colors.END}")

# ==================== 命令：列出待处理 ====================
def cmd_list_pending(args):
    """列出待处理的PDF"""
    print_header("📋 待处理PDF列表")
    
    pending = pdf_mgr.get_pending_pdfs()
    
    if not pending:
        print_info("没有待处理的PDF")
        return
    
    for i, pdf in enumerate(pending, 1):
        size_mb = pdf['file_size'] / 1024 / 1024
        print(f"  {i}. {pdf['filename']} ({size_mb:.1f} MB)")
    
    print()
    print(f"总计: {len(pending)} 个PDF")

# ==================== 主函数 ====================
def main():
    parser = argparse.ArgumentParser(
        description="PDF处理管理工具 - 智能化、自动化",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 扫描新PDF
  python scripts/pdf_manager.py scan
  
  # 上传到MinerU
  python scripts/pdf_manager.py upload
  
  # 查询处理状态
  python scripts/pdf_manager.py status
  
  # 下载结果
  python scripts/pdf_manager.py download
  
  # 自动处理（扫描+上传+等待+下载）
  python scripts/pdf_manager.py auto --wait
  
  # 查看统计
  python scripts/pdf_manager.py stats
        """
    )
    
    sub = parser.add_subparsers(dest='cmd', help='命令')
    
    # 命令：扫描
    sub.add_parser('scan', help='扫描PDF目录，注册新PDF')
    
    # 命令：上传
    sub.add_parser('upload', help='上传待处理的PDF')
    
    # 命令：状态
    sub.add_parser('status', help='查询批次处理状态')
    
    # 命令：下载
    sub.add_parser('download', help='下载解析结果')
    
    # 命令：自动处理
    auto_parser = sub.add_parser('auto', help='自动处理流程')
    auto_parser.add_argument('--wait', action='store_true', help='等待处理完成')
    auto_parser.add_argument('--max-wait', type=int, default=3600, help='最大等待时间（秒）')
    
    # 命令：统计
    sub.add_parser('stats', help='显示统计信息')
    
    # 命令：列出待处理
    sub.add_parser('list-pending', help='列出待处理的PDF')
    
    args = parser.parse_args()
    
    if not args.cmd:
        parser.print_help()
        print()
        print_info("快速开始: python scripts/pdf_manager.py scan")
        return
    
    # 执行命令
    if args.cmd == 'scan':
        cmd_scan(args)
    elif args.cmd == 'upload':
        cmd_upload(args)
    elif args.cmd == 'status':
        cmd_status(args)
    elif args.cmd == 'download':
        cmd_download(args)
    elif args.cmd == 'auto':
        cmd_auto(args)
    elif args.cmd == 'stats':
        cmd_stats(args)
    elif args.cmd == 'list-pending':
        cmd_list_pending(args)

if __name__ == "__main__":
    main()
