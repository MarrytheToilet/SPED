#!/usr/bin/env python3
"""
人工关节材料数据提取系统 - 统一菜单

整合数据提取、数据库管理、测试等所有功能
"""

import os
import sys
from pathlib import Path

# ANSI颜色代码
BLUE = '\033[94m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
CYAN = '\033[96m'
MAGENTA = '\033[95m'
BOLD = '\033[1m'
END = '\033[0m'


def clear_screen():
    """清屏"""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    """打印标题"""
    print()
    print(f"{BLUE}{BOLD}{'='*80}{END}")
    print(f"{BLUE}{BOLD}           人工关节材料数据提取系统 - 统一菜单           {END}")
    print(f"{BLUE}{BOLD}{'='*80}{END}")
    print()


def print_main_menu():
    """打印主菜单"""
    print(f"{GREEN}{BOLD}主菜单：{END}")
    print()
    print(f"  {CYAN}【完整工作流程】{END}")
    print(f"    {BOLD}W.{END} 📖 查看完整工作流程指南")
    print()
    print(f"  {CYAN}【第一步：PDF处理】{END}")
    print(f"    {BOLD}P.{END} 📄 PDF处理菜单（上传/查询/下载）")
    print()
    print(f"  {CYAN}【第二步：数据提取】{END}")
    print(f"    {BOLD}1.{END} 📊 测试系统配置")
    print(f"    {BOLD}2.{END} 📝 提取单个论文（交互式选择）")
    print(f"    {BOLD}3.{END} 🚀 批量提取所有论文")
    print(f"    {BOLD}4.{END} 🧪 测试单条数据提取")
    print()
    print(f"  {CYAN}【第三步：数据库管理】{END}")
    print(f"    {BOLD}5.{END} 💾 数据库管理工具（交互式菜单）")
    print(f"    {BOLD}6.{END} 📥 快速：批量导入JSON到数据库")
    print(f"    {BOLD}7.{END} 📤 快速：导出所有CSV格式")
    print(f"    {BOLD}8.{END} 📊 快速：查看数据库统计")
    print(f"    {BOLD}9.{END} 📑 快速：导出Excel多表（按schema组织）")
    print()
    print(f"  {CYAN}【系统工具】{END}")
    print(f"    {BOLD}10.{END} 📚 查看使用指南")
    print(f"    {BOLD}11.{END} 📋 查看系统状态")
    print(f"    {BOLD}12.{END} 🔍 查看提取日志")
    print()
    print(f"    {BOLD}0.{END} 🚪 退出")
    print()


def show_workflow_guide():
    """显示完整工作流程指南"""
    clear_screen()
    print(f"{BLUE}{BOLD}{'='*80}{END}")
    print(f"{BLUE}{BOLD}           完整工作流程指南           {END}")
    print(f"{BLUE}{BOLD}{'='*80}{END}\n")
    
    print(f"{GREEN}{BOLD}工作流程概览：{END}")
    print(f"""
    {CYAN}PDF文件{END} → {CYAN}MinerU解析{END} → {CYAN}LLM提取{END} → {CYAN}数据库存储{END} → {CYAN}导出分析{END}
       ↓           ↓          ↓          ↓           ↓
    上传PDF    下载结果   提取JSON    导入DB    导出Excel/CSV
    """)
    
    print(f"{GREEN}{BOLD}详细步骤：{END}\n")
    
    print(f"{YELLOW}【第一步：PDF处理】{END}")
    print(f"  1. 将PDF放入 {CYAN}data/raw/pdfs/{END}")
    print(f"  2. 菜单选择 {BOLD}P{END} → 上传PDF到MinerU")
    print(f"  3. 记录返回的 {CYAN}batch_id{END}")
    print(f"  4. 菜单选择 {BOLD}P{END} → 查询状态（等待处理完成）")
    print(f"  5. 菜单选择 {BOLD}P{END} → 下载结果到 {CYAN}data/processed/parsed/{END}")
    print()
    
    print(f"{YELLOW}【第二步：数据提取】{END}")
    print(f"  1. 菜单选择 {BOLD}1{END} → 测试系统配置（首次使用）")
    print(f"  2. 菜单选择 {BOLD}2{END} → 提取单个论文（交互式）")
    print(f"     或选择 {BOLD}3{END} → 批量提取所有论文")
    print(f"  3. 提取结果保存到 {CYAN}data/processed/extracted/{END}")
    print()
    
    print(f"{YELLOW}【第三步：数据库管理】{END}")
    print(f"  1. 菜单选择 {BOLD}6{END} → 批量导入JSON到数据库")
    print(f"  2. 菜单选择 {BOLD}8{END} → 查看数据库统计")
    print(f"  3. 菜单选择 {BOLD}9{END} → 导出Excel多表")
    print(f"     或选择 {BOLD}7{END} → 导出CSV格式")
    print(f"  4. 导出文件保存到 {CYAN}data/exports/{END}")
    print()
    
    print(f"{GREEN}{BOLD}快速开始（完整流程）：{END}")
    print(f"  假设你有新的PDF论文需要处理：")
    print(f"  {CYAN}P{END} → {CYAN}上传{END} → {CYAN}查询{END} → {CYAN}下载{END} → {CYAN}2/3{END} → {CYAN}6{END} → {CYAN}9{END}")
    print()
    
    print(f"{MAGENTA}{BOLD}数据流向：{END}")
    print(f"  data/raw/pdfs/")
    print(f"    └→ MinerU处理")
    print(f"       └→ data/processed/parsed/[论文]/full.md")
    print(f"          └→ LLM提取")
    print(f"             └→ data/processed/extracted/[论文].json")
    print(f"                └→ 导入数据库")
    print(f"                   └→ data/artificial_joint.db")
    print(f"                      └→ 导出")
    print(f"                         └→ data/exports/*.xlsx/*.csv")
    print()
    
    print(f"{BLUE}{BOLD}{'='*80}{END}")
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def run_pdf_menu():
    """PDF处理菜单 - 新版集成"""
    while True:
        clear_screen()
        print(f"\n{BLUE}{'='*80}{END}")
        print(f"{BLUE}{BOLD}PDF处理菜单（智能版）{END}")
        print(f"{BLUE}{'='*80}{END}\n")
        
        print(f"{CYAN}{BOLD}✨ 推荐使用（智能化）：{END}\n")
        print(f"  {BOLD}1.{END} 🚀 快速处理新PDF（自动：扫描→上传→等待→下载）")
        print(f"  {BOLD}2.{END} 📊 查看系统统计")
        print()
        print(f"{YELLOW}{BOLD}分步执行（精细控制）：{END}\n")
        print(f"  {BOLD}3.{END} 📂 扫描新PDF（智能去重）")
        print(f"  {BOLD}4.{END} 📤 上传到MinerU")
        print(f"  {BOLD}5.{END} 📋 查询处理状态")
        print(f"  {BOLD}6.{END} ⬇️  下载解析结果")
        print(f"  {BOLD}7.{END} 📝 列出待处理PDF")
        print()
        print(f"{MAGENTA}{BOLD}旧版工具（兼容）：{END}\n")
        print(f"  {BOLD}8.{END} 🔧 使用旧版PDF工具")
        print()
        print(f"  {BOLD}0.{END} 🔙 返回主菜单")
        print()
        
        choice = input(f"{GREEN}请选择操作 (0-8): {END}").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            run_pdf_auto()
        elif choice == "2":
            run_pdf_stats_new()
        elif choice == "3":
            run_pdf_scan()
        elif choice == "4":
            run_pdf_upload_new()
        elif choice == "5":
            run_pdf_status_new()
        elif choice == "6":
            run_pdf_download_new()
        elif choice == "7":
            run_pdf_list_pending()
        elif choice == "8":
            pdf_menu_old()
        else:
            print(f"\n{RED}❌ 无效选项{END}")
            input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_upload():
    """上传PDF到MinerU"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}上传PDF到MinerU{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_process.py upload")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_status():
    """查询处理状态"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}查询MinerU处理状态{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_process.py status")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_download():
    """下载解析结果"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}下载MinerU解析结果{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_process.py download")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_stats():
    """查看统计信息"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}PDF处理统计{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_process.py stats")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_full_workflow():
    """完整PDF处理流程"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}{BOLD}完整PDF处理流程{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{YELLOW}此流程将依次执行：{END}")
    print(f"  1. 上传PDF到MinerU")
    print(f"  2. 等待处理完成（自动查询）")
    print(f"  3. 下载解析结果")
    print()
    
    confirm = input(f"{GREEN}确认执行完整流程？(y/n): {END}").strip().lower()
    if confirm != 'y':
        return
    
    # 上传
    print(f"\n{CYAN}{'='*60}{END}")
    print(f"{CYAN}步骤 1/3: 上传PDF{END}")
    print(f"{CYAN}{'='*60}{END}\n")
    os.system("python scripts/pdf_process.py upload")
    
    # 查询
    print(f"\n{CYAN}{'='*60}{END}")
    print(f"{CYAN}步骤 2/3: 查询状态{END}")
    print(f"{CYAN}{'='*60}{END}\n")
    os.system("python scripts/pdf_process.py status")
    
    # 下载
    print(f"\n{CYAN}{'='*60}{END}")
    print(f"{CYAN}步骤 3/3: 下载结果{END}")
    print(f"{CYAN}{'='*60}{END}\n")
    os.system("python scripts/pdf_process.py download")
    
    print(f"\n{GREEN}{'='*60}{END}")
    print(f"{GREEN}✅ 完整流程执行完成{END}")
    print(f"{GREEN}{'='*60}{END}\n")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_download_partial():
    """下载部分完成的批次"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}下载部分完成的批次{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{YELLOW}此选项将下载已完成的文件，即使批次未全部完成{END}")
    print(f"{YELLOW}适用于：批次卡住，但部分文件已处理完成的情况{END}\n")
    
    confirm = input(f"{GREEN}确认继续？(y/n): {END}").strip().lower()
    if confirm != 'y':
        return
    
    os.system("python scripts/pdf_process.py download --force-partial")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_reset_batch():
    """重置批次状态"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}重置批次状态{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{YELLOW}⚠️  重置批次将：{END}")
    print(f"  - 从上传记录中移除")
    print(f"  - 从下载记录中移除")
    print(f"  - 允许重新上传和下载\n")
    
    # 先显示状态
    os.system("python scripts/pdf_process.py status")
    print()
    
    batch_id = input(f"{GREEN}请输入要重置的Batch ID (或按回车取消): {END}").strip()
    if not batch_id:
        return
    
    confirm = input(f"{YELLOW}确认重置批次 {batch_id}？(y/n): {END}").strip().lower()
    if confirm != 'y':
        return
    
    os.system(f"python scripts/pdf_process.py reset --batch-id {batch_id}")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_force_download():
    """强制重新下载批次"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}强制重新下载批次{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{YELLOW}此选项将强制重新下载指定批次，即使已下载过{END}\n")
    
    # 先显示状态
    os.system("python scripts/pdf_process.py status")
    print()
    
    batch_id = input(f"{GREEN}请输入要重新下载的Batch ID (或按回车取消): {END}").strip()
    if not batch_id:
        return
    
    confirm = input(f"{YELLOW}确认重新下载批次 {batch_id}？(y/n): {END}").strip().lower()
    if confirm != 'y':
        return
    
    os.system(f"python scripts/pdf_process.py force-download --batch-id {batch_id}")
    
    input(f"\n{GREEN}按回车键继续...{END}")


# ==================== 新版PDF管理器函数 ====================

def run_pdf_auto():
    """自动处理新PDF"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}🚀 自动处理新PDF{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{CYAN}此功能将自动执行：{END}")
    print(f"  1. 扫描 data/raw/pdfs/ 目录")
    print(f"  2. 上传新PDF到MinerU")
    print(f"  3. 轮询等待处理完成")
    print(f"  4. 自动下载结果\n")
    
    print(f"{YELLOW}提示：请确保已将新PDF放入 data/raw/pdfs/ 目录{END}\n")
    
    confirm = input(f"{GREEN}是否等待处理完成？(y/n, 默认n): {END}").strip().lower()
    
    if confirm == 'y':
        os.system("python scripts/pdf_manager.py auto --wait")
    else:
        os.system("python scripts/pdf_manager.py auto")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_scan():
    """扫描新PDF"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}📂 扫描新PDF{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_manager.py scan")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_upload_new():
    """上传PDF（新版）"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}📤 上传PDF到MinerU（新版）{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_manager.py upload")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_status_new():
    """查询状态（新版）"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}📊 查询处理状态（新版）{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_manager.py status")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_download_new():
    """下载结果（新版）"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}⬇️  下载解析结果（新版）{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_manager.py download")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_stats_new():
    """查看统计（新版）"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}📊 系统统计（新版）{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_manager.py stats")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def run_pdf_list_pending():
    """列出待处理PDF"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}📝 待处理PDF列表{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/pdf_manager.py list-pending")
    
    input(f"\n{GREEN}按回车键继续...{END}")


def pdf_menu_old():
    """旧版PDF处理菜单（兼容）"""
    while True:
        clear_screen()
        print(f"\n{BLUE}{'='*80}{END}")
        print(f"{BLUE}{BOLD}PDF处理菜单（旧版）{END}")
        print(f"{BLUE}{'='*80}{END}\n")
        
        print(f"{GREEN}{BOLD}PDF处理流程：{END}\n")
        print(f"  {BOLD}1.{END} 📤 上传PDF到MinerU（自动去重）")
        print(f"  {BOLD}2.{END} 📊 查询处理状态")
        print(f"  {BOLD}3.{END} 📥 下载解析结果（自动去重）")
        print(f"  {BOLD}4.{END} 📈 查看统计信息")
        print(f"  {BOLD}5.{END} 🔧 完整流程：上传→查询→下载")
        print()
        print(f"{YELLOW}{BOLD}高级选项：{END}\n")
        print(f"  {BOLD}6.{END} ⚠️  下载部分完成的批次")
        print(f"  {BOLD}7.{END} 🔄 重置卡住的批次")
        print(f"  {BOLD}8.{END} 🔃 强制重新下载批次")
        print()
        print(f"  {BOLD}0.{END} 🔙 返回上级菜单")
        print()
        
        choice = input(f"{GREEN}请选择操作 (0-8): {END}").strip()
        
        if choice == "0":
            break
        elif choice == "1":
            run_pdf_upload()
        elif choice == "2":
            run_pdf_status()
        elif choice == "3":
            run_pdf_download()
        elif choice == "4":
            run_pdf_stats()
        elif choice == "5":
            run_pdf_full_workflow()
        elif choice == "6":
            run_pdf_download_partial()
        elif choice == "7":
            run_pdf_reset_batch()
        elif choice == "8":
            run_pdf_force_download()
        else:
            print(f"\n{RED}❌ 无效选项{END}")
            input(f"\n{GREEN}按回车键继续...{END}")

    
    confirm = input(f"{GREEN}确认开始完整流程？(y/n): {END}")
    
    if confirm.lower() != 'y':
        print(f"\n{YELLOW}已取消{END}")
        input(f"\n{GREEN}按回车键继续...{END}")
        return
    
    # 步骤1: 上传
    print(f"\n{CYAN}{'='*80}{END}")
    print(f"{CYAN}步骤 1/3: 上传PDF{END}")
    print(f"{CYAN}{'='*80}{END}\n")
    os.system("python scripts/pdf_process.py upload")
    
    input(f"\n{GREEN}按回车键继续到下一步...{END}")
    
    # 步骤2: 查询状态（循环直到完成）
    print(f"\n{CYAN}{'='*80}{END}")
    print(f"{CYAN}步骤 2/3: 查询处理状态{END}")
    print(f"{CYAN}{'='*80}{END}\n")
    
    print(f"{YELLOW}提示: 请查看状态，如果未完成需要等待后再次查询{END}")
    print(f"{YELLOW}      可以多次按回车重复查询，直到所有文件处理完成{END}\n")
    
    while True:
        os.system("python scripts/pdf_process.py status")
        
        choice = input(f"\n{GREEN}处理完成了吗？(y=继续下载 / n=再次查询 / q=退出): {END}").strip().lower()
        
        if choice == 'y':
            break
        elif choice == 'q':
            print(f"\n{YELLOW}已退出完整流程{END}")
            input(f"\n{GREEN}按回车键继续...{END}")
            return
        else:
            print(f"\n{CYAN}重新查询状态...{END}\n")
            import time
            time.sleep(2)
    
    # 步骤3: 下载
    print(f"\n{CYAN}{'='*80}{END}")
    print(f"{CYAN}步骤 3/3: 下载解析结果{END}")
    print(f"{CYAN}{'='*80}{END}\n")
    os.system("python scripts/pdf_process.py download")
    
    print(f"\n{GREEN}{'='*80}{END}")
    print(f"{GREEN}✅ 完整流程已完成！{END}")
    print(f"{GREEN}{'='*80}{END}")
    print(f"\n{CYAN}💡 下一步建议：{END}")
    print(f"   • 返回主菜单选择 2 或 3 进行数据提取")
    print(f"   • 提取完成后选择 6 导入数据库")
    
    input(f"\n{GREEN}按回车键返回PDF菜单...{END}")


def run_extract_test():
    """测试系统配置"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}测试系统配置{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/extract.py test")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def run_extract_single():
    """提取单个论文"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}提取单个论文{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/extract.py single")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def run_extract_batch():
    """批量提取"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}批量提取所有论文{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    print(f"{YELLOW}⚠️  这将提取所有未处理的论文，可能需要较长时间{END}\n")
    confirm = input(f"{GREEN}确认开始批量提取？(y/n): {END}")
    
    if confirm.lower() == 'y':
        os.system("python scripts/extract.py batch")
    else:
        print(f"\n{YELLOW}已取消{END}")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def run_test_single_extraction():
    """测试单条数据提取"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}测试单条数据提取{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    # 列出可用论文
    parsed_dir = Path("data/processed/parsed")
    if not parsed_dir.exists():
        print(f"{RED}❌ 未找到解析后的论文目录{END}")
        input(f"\n{GREEN}按回车键返回...{END}")
        return
    
    # 递归查找所有包含full.md的目录
    papers = []
    for full_md in parsed_dir.rglob("full.md"):
        paper_dir = full_md.parent
        papers.append(paper_dir.name)
    
    # 排序
    papers.sort()
    
    if not papers:
        print(f"{RED}❌ 没有找到可用的论文{END}")
        input(f"\n{GREEN}按回车键返回...{END}")
        return
    
    print(f"{GREEN}可用论文列表 (共 {len(papers)} 篇)：{END}\n")
    for i, paper in enumerate(papers[:20], 1):
        print(f"  {i}. {paper}")
    
    if len(papers) > 20:
        print(f"\n{YELLOW}  ... 还有 {len(papers)-20} 篇论文{END}")
    
    print(f"\n{YELLOW}提示: 将随机选择一篇论文进行测试提取{END}")
    
    try:
        choice = input(f"\n{GREEN}输入论文编号 (1-{min(20, len(papers))}) 或回车随机选择: {END}")
        
        if choice.strip():
            idx = int(choice) - 1
            if 0 <= idx < len(papers):
                selected = papers[idx]
            else:
                print(f"{RED}无效选择，随机选择一篇{END}")
                import random
                selected = random.choice(papers)
        else:
            import random
            selected = random.choice(papers)
        
        print(f"\n{CYAN}选择的论文: {selected}{END}\n")
        
        # 执行测试
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.agents.llm_agent import LLMExtractionAgent
        from loguru import logger
        
        # 配置简洁日志
        logger.remove()
        logger.add(sys.stderr, level="INFO")
        
        agent = LLMExtractionAgent()
        
        paper_path = parsed_dir / selected / "full.md"
        
        print(f"{BLUE}开始测试提取...{END}\n")
        
        result = agent.process({
            "paper_id": selected,
            "full_text_path": str(paper_path)
        })
        
        print(f"\n{GREEN}{'='*80}{END}")
        print(f"{GREEN}✅ 测试提取完成！{END}")
        print(f"{GREEN}{'='*80}{END}\n")
        
        print(f"论文: {result.get('paper_id', 'N/A')}")
        print(f"Data ID: {result.get('dataid', 'N/A')}")
        print(f"提取记录数: {result.get('count', 0)}")
        
        if result.get('records'):
            print(f"\n{CYAN}记录预览：{END}\n")
            for i, record in enumerate(result['records'][:3], 1):
                non_null = sum(1 for v in record.values() if v and v != 'null')
                print(f"  记录 {i}:")
                print(f"    数据标识: {record.get('数据标识', 'N/A')[:50]}...")
                print(f"    应用部位: {record.get('应用部位', 'N/A')}")
                print(f"    非空字段: {non_null}/28")
                print()
            
            if len(result['records']) > 3:
                print(f"  {YELLOW}... 还有 {len(result['records']) - 3} 条记录{END}")
        
    except KeyboardInterrupt:
        print(f"\n{YELLOW}已取消{END}")
    except Exception as e:
        print(f"\n{RED}❌ 错误: {e}{END}")
        import traceback
        traceback.print_exc()
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def run_database_menu():
    """打开数据库管理菜单"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}启动数据库管理工具{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    os.system("python scripts/database.py")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def run_quick_import():
    """快速批量导入"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}批量导入JSON到数据库{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    extracted_dir = Path("data/processed/extracted")
    
    if not extracted_dir.exists():
        print(f"{RED}❌ 未找到extracted目录{END}")
        input(f"\n{GREEN}按回车键返回...{END}")
        return
    
    json_files = list(extracted_dir.glob("*.json"))
    
    if not json_files:
        print(f"{YELLOW}⚠️  extracted目录中没有JSON文件{END}")
        input(f"\n{GREEN}按回车键返回...{END}")
        return
    
    print(f"{GREEN}找到 {len(json_files)} 个JSON文件{END}\n")
    
    confirm = input(f"{GREEN}确认导入？(y/n): {END}")
    
    if confirm.lower() == 'y':
        import sys
        sys.path.insert(0, str(Path(__file__).parent))
        
        from src.database import DatabaseManager
        from loguru import logger
        
        logger.remove()
        logger.add(sys.stderr, level="INFO")
        
        db = DatabaseManager()
        
        total_success = 0
        total_failed = 0
        
        print(f"\n{BLUE}开始导入...{END}\n")
        
        for i, json_file in enumerate(json_files, 1):
            print(f"[{i}/{len(json_files)}] {json_file.name} ... ", end='', flush=True)
            result = db.insert_from_json(json_file)
            total_success += result['success']
            total_failed += result['failed']
            print(f"✅ {result['success']} 条, ❌ {result['failed']} 条")
        
        print(f"\n{GREEN}{'='*80}{END}")
        print(f"{GREEN}导入完成！{END}")
        print(f"{GREEN}{'='*80}{END}\n")
        print(f"总计成功: {total_success} 条")
        print(f"总计失败: {total_failed} 条")
    else:
        print(f"\n{YELLOW}已取消{END}")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def run_quick_export():
    """快速导出CSV"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}导出所有CSV格式（展开JSON）{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from src.database.csv_exporter import export_all_formats
    from loguru import logger
    
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    print(f"{CYAN}模式: 完全展开JSON字段为独立列{END}")
    print(f"{BLUE}开始导出...{END}\n")
    
    export_all_formats(Path("data/exports"), expand_json=True)
    
    print(f"\n{GREEN}{'='*80}{END}")
    print(f"{GREEN}导出完成！{END}")
    print(f"{GREEN}{'='*80}{END}\n")
    print(f"文件保存在: data/exports/")
    print(f"\n{CYAN}导出的文件：{END}")
    print(f"  • full_data_expanded_*.csv - 完整数据（展开JSON）⭐")
    print(f"  • full_data_raw_*.csv - 完整数据（原始JSON）")
    print(f"  • summary_*.csv - 数据摘要")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def run_quick_excel_export():
    """快速导出Excel多表"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}导出Excel多表（从JSON提取结果）{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from src.database.json_to_excel import export_json_to_excel
    from loguru import logger
    
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    print(f"{CYAN}说明: 从 data/processed/extracted/ 中读取所有JSON文件{END}")
    print(f"{CYAN}      按照schema定义组织为多sheet的Excel文件{END}")
    print(f"{BLUE}开始导出...{END}\n")
    
    success = export_json_to_excel(
        output_dir=Path("data/exports"),
        extracted_dir=Path("data/processed/extracted"),
        schema_file=Path("data_schema/schema.json"),
        filter_empty=True
    )
    
    if success:
        print(f"\n{GREEN}{'='*80}{END}")
        print(f"{GREEN}✅ 导出完成！{END}")
        print(f"{GREEN}{'='*80}{END}\n")
        print(f"📁 文件保存在: data/exports/")
        print(f"\n{CYAN}特点：{END}")
        print(f"  • 📄 直接从JSON提取结果导出，无需数据库")
        print(f"  • 📊 多个sheet，每个对应一个数据表")
        print(f"  • 🎯 按照schema.json定义的结构组织")
        print(f"  • 🗑️  自动过滤没有数据的空表")
        print(f"  • 🎨 表头样式美化，自动调整列宽")
    else:
        print(f"\n{RED}{'='*80}{END}")
        print(f"{RED}❌ 导出失败！请查看日志{END}")
        print(f"{RED}{'='*80}{END}")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def run_quick_stats():
    """快速查看统计"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}数据库统计信息{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    import sys
    sys.path.insert(0, str(Path(__file__).parent))
    
    from src.database import DatabaseManager
    from loguru import logger
    
    logger.remove()
    
    db = DatabaseManager()
    stats = db.get_statistics()
    
    if stats:
        print(f"📊 总记录数: {stats.get('total_records', 0)}")
        print(f"📝 有应用部位的记录: {stats.get('with_application', 0)}")
        print(f"📄 不同论文数: {stats.get('unique_papers', 0)}")
        print(f"🕐 最近更新: {stats.get('last_updated', 'N/A')}")
        
        size_mb = stats.get('database_size', 0) / 1024 / 1024
        print(f"💾 数据库大小: {size_mb:.2f} MB")
    else:
        print(f"{RED}❌ 无法获取统计信息{END}")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def view_guide():
    """查看使用指南"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}使用指南{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    readme = Path("README.md")
    quick_guide = Path("docs/QUICK_USAGE_GUIDE.md")
    
    if quick_guide.exists():
        print(f"{GREEN}显示快速使用指南...{END}\n")
        os.system(f"cat {quick_guide} | head -80")
        print(f"\n{YELLOW}完整指南请查看: {quick_guide}{END}")
    elif readme.exists():
        print(f"{GREEN}显示README...{END}\n")
        os.system(f"cat {readme} | head -80")
        print(f"\n{YELLOW}完整文档请查看: {readme}{END}")
    else:
        print(f"{RED}❌ 找不到文档文件{END}")
    
    print(f"\n{CYAN}其他文档：{END}")
    print(f"  • README.md - 系统完整介绍")
    print(f"  • docs/QUICK_USAGE_GUIDE.md - 快速使用指南")
    print(f"  • docs/DATABASE_GUIDE.md - 数据库管理指南")
    print(f"  • docs/EXTRACTION_SUCCESS_REPORT.md - 测试报告")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def view_system_status():
    """查看系统状态"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}系统状态{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    # 检查目录
    print(f"{CYAN}【目录结构】{END}\n")
    
    dirs_to_check = [
        ("data/processed/parsed", "输入：解析后的论文"),
        ("data/processed/extracted", "输出：提取的JSON"),
        ("data/exports", "导出：CSV文件"),
        ("data/artificial_joint.db", "数据库文件"),
        ("prompts/prompt.md", "提取Prompt"),
    ]
    
    for path_str, desc in dirs_to_check:
        path = Path(path_str)
        if path.exists():
            if path.is_file():
                size = path.stat().st_size / 1024
                print(f"  ✅ {desc}: {path_str} ({size:.1f} KB)")
            else:
                count = len(list(path.iterdir()))
                print(f"  ✅ {desc}: {path_str} ({count} 项)")
        else:
            print(f"  ❌ {desc}: {path_str} (不存在)")
    
    # 统计信息
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
            import sys
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
    
    # 配置检查
    print(f"\n{CYAN}【配置检查】{END}\n")
    
    env_file = Path(".env")
    if env_file.exists():
        print(f"  ✅ .env 配置文件存在")
        # 检查关键配置
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        # 检查API key（优先SiliconFlow）
        api_key = os.getenv("SILICONFLOW_API_KEY") or os.getenv("OPENAI_API_KEY")
        model = os.getenv("LLM_MODEL", "moonshotai/Kimi-K2-Instruct-0905")
        
        if api_key:
            print(f"  ✅ API_KEY: 已配置 ({api_key[:10]}...)")
        else:
            print(f"  ❌ API_KEY: 未配置")
        
        print(f"  ℹ️  当前模型: {model}")
    else:
        print(f"  ❌ .env 配置文件不存在")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def view_logs():
    """查看提取日志"""
    print(f"\n{BLUE}{'='*80}{END}")
    print(f"{BLUE}提取日志{END}")
    print(f"{BLUE}{'='*80}{END}\n")
    
    log_dir = Path("logs")
    
    if not log_dir.exists():
        print(f"{YELLOW}⚠️  日志目录不存在{END}")
        input(f"\n{GREEN}按回车键返回...{END}")
        return
    
    log_files = sorted(log_dir.glob("*.log"), key=lambda x: x.stat().st_mtime, reverse=True)
    
    if not log_files:
        print(f"{YELLOW}⚠️  没有找到日志文件{END}")
        input(f"\n{GREEN}按回车键返回...{END}")
        return
    
    print(f"{GREEN}最近的日志文件：{END}\n")
    
    for i, log_file in enumerate(log_files[:10], 1):
        size = log_file.stat().st_size / 1024
        from datetime import datetime
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        print(f"  {i}. {log_file.name}")
        print(f"     大小: {size:.1f} KB | 时间: {mtime}")
    
    print(f"\n{CYAN}查看日志命令示例：{END}")
    if log_files:
        print(f"  tail -f {log_files[0]}     # 实时查看最新日志")
        print(f"  cat {log_files[0]} | grep ERROR  # 查看错误信息")
    
    input(f"\n{GREEN}按回车键返回主菜单...{END}")


def main():
    """主函数"""
    while True:
        try:
            clear_screen()
            print_header()
            print_main_menu()
            
            choice = input(f"{GREEN}请输入选项 (0-12, W, P): {END}").strip().lower()
            
            if choice == "0":
                print(f"\n{BLUE}再见！👋{END}\n")
                sys.exit(0)
            
            elif choice == "w":
                show_workflow_guide()
            
            elif choice == "p":
                run_pdf_menu()
            
            elif choice == "1":
                run_extract_test()
            
            elif choice == "2":
                run_extract_single()
            
            elif choice == "3":
                run_extract_batch()
            
            elif choice == "4":
                run_test_single_extraction()
            
            elif choice == "5":
                run_database_menu()
            
            elif choice == "6":
                run_quick_import()
            
            elif choice == "7":
                run_quick_export()
            
            elif choice == "8":
                run_quick_stats()
            
            elif choice == "9":
                run_quick_excel_export()
            
            elif choice == "10":
                view_guide()
            
            elif choice == "11":
                view_system_status()
            
            elif choice == "12":
                view_logs()
            
            else:
                print(f"\n{RED}❌ 无效的选项{END}")
                input(f"\n{GREEN}按回车键继续...{END}")
        
        except KeyboardInterrupt:
            print(f"\n\n{BLUE}再见！👋{END}\n")
            sys.exit(0)
        except Exception as e:
            print(f"\n{RED}❌ 错误: {str(e)}{END}")
            import traceback
            traceback.print_exc()
            input(f"\n{GREEN}按回车键继续...{END}")


if __name__ == "__main__":
    main()
