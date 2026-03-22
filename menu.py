#!/usr/bin/env python3
"""
人工关节材料数据提取系统 - 简洁菜单

基于scripts/cli.py的交互式菜单界面
"""

import os
import sys
import subprocess
from pathlib import Path

# 颜色代码
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
BOLD = '\033[1m'
END = '\033[0m'


def clear():
    """清屏"""
    os.system('clear' if os.name != 'nt' else 'cls')


def header():
    """打印标题"""
    print(f"\n{BLUE}{BOLD}{'='*80}{END}")
    print(f"{BLUE}{BOLD}    人工关节材料数据提取系统{END}")
    print(f"{BLUE}{BOLD}{'='*80}{END}\n")


def main_menu():
    """主菜单"""
    while True:
        try:
            clear()
            header()
            
            print(f"{GREEN}{BOLD}主菜单{END}\n")
            
            print(f"{CYAN}【PDF处理】{END}")
            print(f"  {BOLD}1.{END} 📤 上传PDF到MinerU")
            print(f"  {BOLD}2.{END} 🔍 查询批次状态")
            print(f"  {BOLD}3.{END} 📥 下载解析结果")
            print(f"  {BOLD}4.{END} 📊 PDF处理统计")
            print()
            
            print(f"{CYAN}【数据提取】{END}")
            print(f"  {BOLD}5.{END} 🧪 测试系统配置")
            print(f"  {BOLD}6.{END} 📝 提取单个论文（交互式）")
            print(f"  {BOLD}7.{END} 🚀 批量提取所有论文")
            print()
            
            print(f"{CYAN}【数据库管理】{END}")
            print(f"  {BOLD}8.{END} 📥 导入JSON到数据库")
            print(f"  {BOLD}9.{END} 📊 查看数据库统计")
            print(f"  {BOLD}10.{END} 📤 导出Excel")
            print(f"  {BOLD}11.{END} 📤 导出CSV")
            print()
            
            print(f"{CYAN}【系统工具】{END}")
            print(f"  {BOLD}12.{END} 📋 查看系统状态")
            print(f"  {BOLD}13.{END} 🛠️ LLM调试工具")
            print(f"  {BOLD}14.{END} 💡 使用说明")
            print()
            
            print(f"  {BOLD}0.{END} 🚪 退出")
            print()
            
            choice = input(f"{GREEN}请选择 (0-14): {END}").strip()
            
            if choice == '0':
                print(f"\n{BLUE}再见！{END}\n")
                sys.exit(0)
            elif choice == '1':
                pdf_upload()
            elif choice == '2':
                pdf_status()
            elif choice == '3':
                pdf_download()
            elif choice == '4':
                pdf_stats()
            elif choice == '5':
                test_config()
            elif choice == '6':
                extract_single()
            elif choice == '7':
                extract_batch()
            elif choice == '8':
                db_import()
            elif choice == '9':
                db_stats()
            elif choice == '10':
                db_export_excel()
            elif choice == '11':
                db_export_csv()
            elif choice == '12':
                system_status()
            elif choice == '13':
                debug_tools()
            elif choice == '14':
                usage_guide()
            else:
                print(f"\n{RED}无效选项{END}")
                input(f"\n{GREEN}按回车继续...{END}")
        
        except KeyboardInterrupt:
            print(f"\n\n{BLUE}再见！{END}\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n{RED}错误: {e}{END}")
            input(f"\n{GREEN}按回车继续...{END}")


def pdf_upload():
    """上传PDF"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}上传PDF到MinerU{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{YELLOW}说明：{END}")
    print(f"  1. 将PDF文件放入 data/raw/pdfs/ 目录")
    print(f"  2. 系统自动扫描并去重")
    print(f"  3. 批量上传到MinerU服务")
    print()
    
    pdf_dir = Path("data/raw/pdfs")
    if not pdf_dir.exists():
        print(f"{RED}❌ PDF目录不存在: {pdf_dir}{END}")
        print(f"{YELLOW}创建目录...{END}")
        pdf_dir.mkdir(parents=True, exist_ok=True)
    
    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"{CYAN}📂 当前PDF目录中有 {len(pdf_files)} 个文件{END}\n")
    
    if not pdf_files:
        print(f"{YELLOW}⚠️ 目录中没有PDF文件{END}")
        input(f"\n{GREEN}按回车返回...{END}")
        return
    
    confirm = input(f"{GREEN}确认上传？(y/n): {END}").strip().lower()
    if confirm != 'y':
        return
    
    print()
    os.system("python scripts/cli.py pdf upload")
    
    input(f"\n{GREEN}按回车返回...{END}")


def pdf_status():
    """查询批次状态"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}查询批次状态{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    # 先列出所有批次
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.pdfs.pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        batches = processor.list_batches()
        
        if not batches:
            print(f"{YELLOW}⚠️ 没有找到任何批次{END}")
            print(f"{CYAN}提示: 请先上传PDF{END}")
            input(f"\n{GREEN}按回车返回...{END}")
            return
        
        print(f"{GREEN}已上传的批次 (共 {len(batches)} 个):{END}\n")
        for i, batch in enumerate(batches[:10], 1):
            print(f"  {i}. {batch['batch_id']}")
            print(f"     文件数: {batch['file_count']}, 状态: {batch['status']}")
            print(f"     创建时间: {batch['created_at']}")
        
        if len(batches) > 10:
            print(f"\n{YELLOW}  ... 还有 {len(batches)-10} 个批次{END}")
        
        print()
        choice = input(f"{GREEN}选择批次编号 (1-{min(10, len(batches))}), 或按回车查询所有: {END}").strip()
        
        if choice:
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(batches):
                    batch_id = batches[idx]['batch_id']
                    print()
                    os.system(f"python scripts/cli.py pdf status {batch_id}")
                else:
                    print(f"{RED}无效编号{END}")
            except ValueError:
                print(f"{RED}输入无效{END}")
        else:
            # 查询所有
            print()
            os.system("python scripts/cli.py pdf list")
    
    except Exception as e:
        print(f"{RED}错误: {e}{END}")
    
    input(f"\n{GREEN}按回车返回...{END}")


def pdf_download():
    """下载解析结果"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}下载解析结果{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    # 列出可下载的批次
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.pdfs.pdf_processor import PDFProcessor
        from src.utils.doi_extractor import DOIExtractor
        
        processor = PDFProcessor()
        batches = processor.list_batches()
        
        if not batches:
            print(f"{YELLOW}⚠️ 没有找到任何批次{END}")
            input(f"\n{GREEN}按回车返回...{END}")
            return
        
        print(f"{GREEN}可下载的批次 (共 {len(batches)} 个):{END}\n")
        for i, batch in enumerate(batches[:10], 1):
            print(f"  {i}. {batch['batch_id']}")
            print(f"     文件数: {batch['file_count']}, 状态: {batch['status']}")
        
        print()
        choice = input(f"{GREEN}选择批次编号 (1-{min(10, len(batches))}): {END}").strip()
        
        if not choice:
            return
        
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(batches):
                batch_id = batches[idx]['batch_id']
                print(f"\n{CYAN}下载批次: {batch_id}{END}\n")
                os.system(f"python scripts/cli.py pdf download {batch_id}")
                
                # 下载后自动添加DOI
                print(f"\n{CYAN}自动添加DOI信息...{END}")
                parsed_dir = Path("data/processed/parsed")
                stats = DOIExtractor.process_all_papers(parsed_dir)
                print(f"  添加DOI: {stats['success']} 篇, 已有: {stats['already_has_doi']} 篇")
            else:
                print(f"{RED}无效编号{END}")
        except ValueError:
            print(f"{RED}输入无效{END}")
    
    except Exception as e:
        print(f"{RED}错误: {e}{END}")
    
    input(f"\n{GREEN}按回车返回...{END}")


def pdf_stats():
    """PDF统计信息"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}PDF处理统计{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    try:
        sys.path.insert(0, str(Path(__file__).parent))
        from src.pdfs.pdf_processor import PDFProcessor
        
        processor = PDFProcessor()
        stats = processor.get_statistics()
        
        print(f"{CYAN}PDF文件:{END}")
        print(f"  总数: {stats['total_pdfs']}")
        print(f"  待上传: {stats['pending']}")
        print(f"  已上传: {stats['uploaded']}")
        print(f"  已下载: {stats['downloaded']}")
        print()
        print(f"{CYAN}批次:{END}")
        print(f"  总数: {stats['total_batches']}")
        print(f"  已完成: {stats['completed_batches']}")
    
    except Exception as e:
        print(f"{RED}错误: {e}{END}")
    
    input(f"\n{GREEN}按回车返回...{END}")


def test_config():
    """测试系统配置"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}测试系统配置{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{YELLOW}此测试将验证：{END}")
    print(f"  • API密钥配置")
    print(f"  • LLM模型连接")
    print(f"  • 数据目录结构")
    print()
    
    # 显示API Key负载均衡状态
    try:
        from src.llm.load_balancer import get_key_rotator
        import settings
        provider = getattr(settings, 'LLM_PROVIDER', 'siliconflow')
        rotator = get_key_rotator(provider)
        stats = rotator.get_stats()
        
        if stats['total_keys'] > 1:
            print(f"{CYAN}【API Key负载均衡配置】{END}")
            print(f"  提供商: {provider}")
            print(f"  配置Key数: {stats['total_keys']} (健康: {stats['healthy_keys']})")
            for k in stats['keys']:
                status = f"{GREEN}✓{END}" if k['is_healthy'] else f"{RED}✗{END}"
                print(f"    {status} {k['name']}: 请求{k['request_count']}次, 失败{k['fail_count']}次")
            print()
        elif stats['total_keys'] == 1:
            print(f"{CYAN}【API配置】单Key模式 ({provider}){END}")
            print(f"{YELLOW}提示: 可配置多个API Key分散并发压力{END}")
            print(f"  在 .env 中添加: {provider.upper()}_BACKUP_KEYS=key2,key3")
            print()
    except Exception:
        pass
    
    os.system("python scripts/cli.py extract test")
    input(f"\n{GREEN}按回车返回...{END}")


def extract_single():
    """提取单个论文"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}提取单个论文{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    # 列出可用论文
    parsed_dir = Path("data/processed/parsed")
    if not parsed_dir.exists():
        print(f"{RED}❌ 找不到解析后的论文目录: {parsed_dir}{END}")
        input(f"\n{GREEN}按回车返回...{END}")
        return
    
    papers = [d.name for d in parsed_dir.iterdir() 
              if d.is_dir() and (d / "full.md").exists()]
    
    if not papers:
        print(f"{RED}❌ 没有可用论文{END}")
        print(f"{YELLOW}请先运行PDF处理流程{END}")
        input(f"\n{GREEN}按回车返回...{END}")
        return
    
    papers.sort()
    
    print(f"{GREEN}可用论文 (共 {len(papers)} 篇):{END}\n")
    for i, paper in enumerate(papers[:20], 1):
        print(f"  {i}. {paper}")
    
    if len(papers) > 20:
        print(f"\n{YELLOW}  ... 还有 {len(papers)-20} 篇{END}")
    
    print(f"\n{CYAN}提取模式:{END}")
    print(f"  1. skeleton_fill (推荐) - 两阶段骨架填充，稳定性最好")
    print(f"  2. full - 一次性提取，速度快，适合短论文")
    print(f"  3. chunk - 分块独立提取")
    
    try:
        choice = input(f"\n{GREEN}选择论文编号 (1-{min(20, len(papers))}): {END}").strip()
        if not choice:
            return
        
        idx = int(choice) - 1
        if idx < 0 or idx >= len(papers):
            print(f"{RED}无效编号{END}")
            input(f"\n{GREEN}按回车返回...{END}")
            return
        
        paper_id = papers[idx]
        
        mode_choice = input(f"{GREEN}选择模式 (1/2/3, 默认1): {END}").strip() or "1"
        mode_map = {"1": "skeleton_fill", "2": "full", "3": "chunk"}
        mode = mode_map.get(mode_choice, "skeleton_fill")
        
        print(f"\n{CYAN}开始提取: {paper_id} (模式: {mode}){END}\n")
        
        os.system(f"python scripts/cli.py extract single {paper_id} --mode {mode}")
        
    except ValueError:
        print(f"\n{RED}输入无效{END}")
    
    input(f"\n{GREEN}按回车返回...{END}")


def extract_batch():
    """批量提取"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}批量提取所有论文{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    project_root = Path(__file__).resolve().parent
    parsed_dir = project_root / "data/processed/parsed"
    extracted_dir = project_root / "data/processed/extracted"
    if parsed_dir.exists():
        papers = [
            d.name for d in parsed_dir.iterdir()
            if d.is_dir() and (d / "full.md").exists()
        ]
        
        # 智能统计：区分成功提取和需要重试的
        import json
        success_count = 0
        retry_count = 0
        new_count = 0
        
        for paper in papers:
            json_file = extracted_dir / f"{paper}.json"
            if json_file.exists():
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                    has_records = data.get('count', 0) > 0 or len(data.get('records', [])) > 0
                    has_error = 'error' in data or data.get('success') == False
                    if has_records and not has_error:
                        success_count += 1
                    else:
                        retry_count += 1  # 空记录或失败
                except:
                    retry_count += 1  # JSON损坏
            else:
                new_count += 1
        
        print(f"{YELLOW}共发现 {len(papers)} 篇论文{END}")
        print(f"{YELLOW}  - 已成功提取: {success_count} 篇{END}")
        if retry_count > 0:
            print(f"{YELLOW}  - 需重试(失败/空): {retry_count} 篇{END}")
        if new_count > 0:
            print(f"{YELLOW}  - 新增未提取: {new_count} 篇{END}")
        
        if len(papers) == 0:
            input(f"\n{GREEN}没有可处理论文，按回车返回...{END}")
            return
    else:
        print(f"{YELLOW}找不到论文目录{END}")
        input(f"\n{GREEN}按回车返回...{END}")
        return
    
    print(f"\n{CYAN}提取模式:{END}")
    print(f"  1. skeleton_fill (推荐) - 两阶段骨架填充，适合长论文，稳定性最好")
    print(f"  2. full - 一次性提取，速度快，适合短论文(<30KB)")
    print(f"  3. chunk - 分块独立提取")
    
    mode_choice = input(f"\n{GREEN}选择模式 (1/2/3, 默认1): {END}").strip() or "1"
    mode_map = {"1": "skeleton_fill", "2": "full", "3": "chunk"}
    mode = mode_map.get(mode_choice, "skeleton_fill")

    incremental_choice = input(
        f"{GREEN}增量模式？(Y跳过已成功/n全部重跑): {END}"
    ).strip().lower()
    use_incremental = incremental_choice != "n"
    if use_incremental and retry_count > 0:
        print(f"{CYAN}  (增量模式会自动重试失败/空记录的论文){END}")
    
    # 并行配置
    parallel_choice = input(
        f"{GREEN}使用并行处理？(Y/n): {END}"
    ).strip().lower()
    use_parallel = parallel_choice != "n"
    
    workers = None
    if use_parallel:
        workers_input = input(
            f"{GREEN}并行worker数量 (回车使用默认): {END}"
        ).strip()
        if workers_input:
            try:
                workers = int(workers_input)
            except ValueError:
                pass
    
    confirm = input(f"\n{YELLOW}确认批量提取？(y/n): {END}").strip().lower()
    if confirm != 'y':
        return
    
    print(
        f"\n{CYAN}开始批量提取 (模式: {mode}, "
        f"{'增量' if use_incremental else '全量重跑'}, "
        f"{'并行' if use_parallel else '串行'}){END}\n"
    )
    # 使用新的 extract.py 脚本
    cmd = [sys.executable, "scripts/extract.py", "batch", "--mode", mode]
    if not use_incremental:
        cmd.append("--force")
    if not use_parallel:
        cmd.append("--no-parallel")
    if workers:
        cmd.extend(["--workers", str(workers)])

    result = subprocess.run(cmd, cwd=project_root)
    if result.returncode == 0:
        print(f"\n{GREEN}✅ 批量提取执行完成{END}")
    else:
        print(f"\n{RED}❌ 批量提取失败，退出码: {result.returncode}{END}")
        print(f"{YELLOW}请检查 logs/debug/ 下最新 *_error_*.txt 日志{END}")
    
    input(f"\n{GREEN}按回车返回...{END}")


def db_import():
    """导入数据库"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}导入JSON到数据库{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    extracted_dir = Path("data/processed/extracted")
    if extracted_dir.exists():
        json_files = list(extracted_dir.glob("*.json"))
        print(f"{GREEN}找到 {len(json_files)} 个JSON文件{END}")
    else:
        print(f"{YELLOW}找不到提取结果目录{END}")
    
    confirm = input(f"\n{GREEN}确认导入？(y/n): {END}").strip().lower()
    if confirm != 'y':
        return
    
    print()
    os.system("python scripts/cli.py db import")
    
    input(f"\n{GREEN}按回车返回...{END}")


def db_stats():
    """数据库统计"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}数据库统计{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/cli.py db stats")
    
    input(f"\n{GREEN}按回车返回...{END}")


def db_export_excel():
    """导出Excel"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}导出Excel{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{CYAN}将导出为多sheet的Excel文件{END}")
    print(f"{CYAN}每个sheet对应一个数据表{END}\n")
    
    os.system("python scripts/cli.py db export --format excel")
    
    print(f"\n{GREEN}文件保存在: data/exports/{END}")
    input(f"\n{GREEN}按回车返回...{END}")


def db_export_csv():
    """导出CSV"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}导出CSV{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{CYAN}将导出为CSV文件{END}\n")
    
    os.system("python scripts/cli.py db export --format csv")
    
    print(f"\n{GREEN}文件保存在: data/exports/{END}")
    input(f"\n{GREEN}按回车返回...{END}")


def system_status():
    """系统状态"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}系统状态{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    # 检查目录
    print(f"{CYAN}【目录结构】{END}\n")
    
    dirs = [
        ("data/raw/pdfs", "原始PDF"),
        ("data/processed/parsed", "解析后的论文"),
        ("data/processed/extracted", "提取的JSON"),
        ("data/exports", "导出文件"),
        ("data/artificial_joint.db", "数据库"),
    ]
    
    for path_str, desc in dirs:
        path = Path(path_str)
        if path.exists():
            if path.is_file():
                size_kb = path.stat().st_size / 1024
                print(f"  ✅ {desc:15s} {path_str:40s} ({size_kb:.1f} KB)")
            else:
                count = len(list(path.iterdir()))
                print(f"  ✅ {desc:15s} {path_str:40s} ({count} 项)")
        else:
            print(f"  ❌ {desc:15s} {path_str:40s} (不存在)")
    
    # 统计
    print(f"\n{CYAN}【数据统计】{END}\n")
    
    parsed_dir = Path("data/processed/parsed")
    if parsed_dir.exists():
        papers = [d for d in parsed_dir.iterdir() if d.is_dir() and (d / "full.md").exists()]
        print(f"  📄 已解析论文: {len(papers)} 篇")
    
    extracted_dir = Path("data/processed/extracted")
    if extracted_dir.exists():
        json_files = list(extracted_dir.glob("*.json"))
        print(f"  📊 已提取JSON: {len(json_files)} 个")
    
    db_path = Path("data/artificial_joint.db")
    if db_path.exists():
        try:
            sys.path.insert(0, str(Path(__file__).parent))
            from src.database import DatabaseManager
            from loguru import logger
            logger.remove()
            
            db = DatabaseManager()
            stats = db.get_statistics()
            print(f"  💾 数据库记录: {stats.get('total_records', 0)} 条")
            print(f"  📝 不同论文: {stats.get('unique_papers', 0)} 篇")
        except:
            print(f"  💾 数据库记录: (无法读取)")
    
    # 配置
    print(f"\n{CYAN}【配置检查】{END}\n")
    
    env_file = Path(".env")
    if env_file.exists():
        print(f"  ✅ .env 配置文件存在")
        try:
            from dotenv import load_dotenv
            load_dotenv()
            
            api_key = os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")
            model = os.getenv("LLM_MODEL", "moonshotai/Kimi-K2-Instruct-0905")
            
            if api_key:
                print(f"  ✅ API_KEY: 已配置 ({api_key[:10]}...)")
            else:
                print(f"  ❌ API_KEY: 未配置")
            
            print(f"  ℹ️  当前模型: {model}")
        except:
            pass
    else:
        print(f"  ❌ .env 配置文件不存在")
    
    input(f"\n{GREEN}按回车返回...{END}")


def usage_guide():
    """使用说明"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}使用说明{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{GREEN}{BOLD}完整工作流程：{END}\n")
    
    print(f"{YELLOW}第一步：PDF处理{END}")
    print(f"  1. 将PDF文件放入 data/raw/pdfs/")
    print(f"  2. 使用MinerU解析（需单独工具）")
    print(f"  3. 解析结果放入 data/processed/parsed/[论文名]/full.md")
    print()
    
    print(f"{YELLOW}第二步：数据提取{END}")
    print(f"  1. 菜单选择 {BOLD}1{END} 测试配置（首次使用）")
    print(f"  2. 菜单选择 {BOLD}2{END} 提取单个论文")
    print(f"     或选择 {BOLD}3{END} 批量提取")
    print(f"  3. 提取结果保存到 data/processed/extracted/")
    print()
    
    print(f"{YELLOW}第三步：数据库管理{END}")
    print(f"  1. 菜单选择 {BOLD}4{END} 导入JSON到数据库")
    print(f"  2. 菜单选择 {BOLD}5{END} 查看统计")
    print(f"  3. 菜单选择 {BOLD}6{END} 或 {BOLD}7{END} 导出数据")
    print()
    
    print(f"{GREEN}{BOLD}提取模式说明：{END}\n")
    print(f"  • {BOLD}skeleton_fill{END} - 两阶段骨架填充（推荐，稳定性最好）")
    print(f"  • {BOLD}full{END} - 一次性提取完整论文（适合短论文<30KB）")
    print(f"  • {BOLD}chunk{END} - 分块迭代提取（适合超长论文）")
    print()
    
    print(f"{GREEN}{BOLD}命令行工具：{END}\n")
    print(f"  除了菜单，也可以直接使用命令行：")
    print(f"  {CYAN}python scripts/extract.py single{END}")
    print(f"  {CYAN}python scripts/extract.py batch{END}")
    print(f"  {CYAN}python scripts/cli.py db import{END}")
    print()
    
    print(f"{GREEN}{BOLD}文档位置：{END}\n")
    print(f"  • README.md - 系统完整介绍")
    print(f"  • prompts/README.md - Prompt组装说明")
    print(f"  • scripts/README.md - 脚本使用说明")
    print()
    
    input(f"{GREEN}按回车返回...{END}")

def debug_tools():
    """LLM调试工具"""
    clear()
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}🛠️ LLM调试工具{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{GREEN}调试功能：{END}")
    print(f"  {BOLD}1.{END} 📊 快速状态查看")
    print(f"  {BOLD}2.{END} 📋 调用统计")
    print(f"  {BOLD}3.{END} 📚 论文调用记录")
    print(f"  {BOLD}4.{END} 🔍 查看具体调用")
    print(f"  {BOLD}5.{END} ⚡ 查看超时错误")
    print()
    
    choice = input(f"{GREEN}选择功能 (1-5, 回车返回): {END}").strip()
    
    if not choice:
        return
    
    try:
        if choice == "1":
            print(f"\n{YELLOW}📊 快速状态查看{END}")
            print("-" * 60)
            os.system("python scripts/quick_debug.py")
        
        elif choice == "2":
            print(f"\n{YELLOW}📋 调用统计{END}")
            print("-" * 60)
            os.system("python scripts/debug.py stats")
        
        elif choice == "3":
            print(f"\n{YELLOW}📚 论文调用记录{END}")
            print("-" * 60)
            os.system("python scripts/debug.py papers")
            print()
            paper_id = input(f"{GREEN}输入论文ID查看详情 (回车跳过): {END}").strip()
            if paper_id:
                os.system(f"python scripts/debug.py paper {paper_id}")
        
        elif choice == "4":
            print(f"\n{YELLOW}🔍 查看具体调用{END}")
            print("-" * 60)
            os.system("python scripts/debug.py list | tail -10")
            print()
            call_id = input(f"{GREEN}输入调用ID查看详情: {END}").strip()
            if call_id:
                os.system(f"python scripts/debug.py call {call_id}")
        
        elif choice == "5":
            print(f"\n{YELLOW}⚡ 超时错误分析{END}")
            print("-" * 60)
            
            debug_dir = Path("logs/debug")
            if debug_dir.exists():
                timeout_count = 0
                for error_file in debug_dir.glob("*error*.txt"):
                    try:
                        with open(error_file, "r", encoding="utf-8") as f:
                            if "timeout" in f.read().lower():
                                timeout_count += 1
                    except Exception:
                        continue
                
                print(f"🔎 发现 {timeout_count} 个超时错误")
                
                if timeout_count > 0:
                    from settings import (
                        LLM_MAX_RETRIES, LLM_CALL_TIMEOUT,
                        LLM_RETRY_BACKOFF_BASE, LLM_RETRY_BACKOFF_MAX
                    )
                    print("\n📋 超时错误分析:")
                    print("  • 请求超时通常是网络或API服务器问题")
                    timeout_desc = "不限制" if LLM_CALL_TIMEOUT is None else f"{LLM_CALL_TIMEOUT} 秒"
                    print(
                        f"  • 当前配置: 最多重试 {LLM_MAX_RETRIES} 次, "
                        f"单次超时 {timeout_desc}"
                    )
                    print(
                        f"  • 退避策略: 指数退避, 基数 {LLM_RETRY_BACKOFF_BASE}, "
                        f"最大等待 {LLM_RETRY_BACKOFF_MAX} 秒"
                    )
                    print("  • 每次调用的输入输出都已保存到 logs/debug/")
                    print(f"\n💡 建议:")
                    print(f"  1. 检查网络连接")
                    print(f"  2. 检查API配置: cat .env | grep API")
                    print(f"  3. 查看具体错误: ls -la logs/debug/*error*.txt | tail -5")
                else:
                    print("✅ 没有发现超时错误")
            else:
                print("⚠️ 调试目录不存在，请先进行一次数据提取")
    
    except Exception as e:
        print(f"\n{RED}调试工具错误: {e}{END}")
    
    input(f"\n{GREEN}按回车返回...{END}")


if __name__ == "__main__":
    main_menu()
