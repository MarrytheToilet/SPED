#!/usr/bin/env python3
"""
数据组织脚本 - 整理和清理data目录结构

功能：
1. 检查并创建标准目录结构
2. 清理空目录
3. 显示数据统计信息
4. 验证配置一致性
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

# ANSI颜色
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
BOLD = '\033[1m'
END = '\033[0m'


class DataOrganizer:
    """数据目录组织器"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        
        # 标准目录结构
        self.standard_structure = {
            "raw": {
                "pdfs": "原始PDF文件"
            },
            "uploads": {
                "_file": "upload_batches.csv - 上传批次记录"
            },
            "processed": {
                "parsed": {
                    "output": "MinerU解析结果（按batch_*组织）"
                },
                "extracted": "文本提取中间结果（可选）",
                "analyzed": "AI提取的JSON结果"
            },
            "exports": "数据库导出的Excel文件"
        }
    
    def print_header(self, text):
        """打印标题"""
        print(f"\n{BLUE}{BOLD}{'='*70}{END}")
        print(f"{BLUE}{BOLD}{text:^70}{END}")
        print(f"{BLUE}{BOLD}{'='*70}{END}\n")
    
    def ensure_directory_structure(self):
        """确保标准目录结构存在"""
        self.print_header("检查目录结构")
        
        created = []
        existing = []
        
        def create_dirs(base_path, structure, level=0):
            for name, desc in structure.items():
                if name == "_file":
                    continue
                    
                path = base_path / name
                indent = "  " * level
                
                if isinstance(desc, dict):
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                        created.append(str(path))
                        print(f"{indent}✅ {GREEN}创建{END}: {path}")
                    else:
                        existing.append(str(path))
                        print(f"{indent}✓ {path}")
                    
                    create_dirs(path, desc, level + 1)
                else:
                    if not path.exists():
                        path.mkdir(parents=True, exist_ok=True)
                        created.append(str(path))
                        print(f"{indent}✅ {GREEN}创建{END}: {path}")
                        print(f"{indent}   说明: {desc}")
                    else:
                        existing.append(str(path))
                        print(f"{indent}✓ {path}")
                        print(f"{indent}   说明: {desc}")
        
        create_dirs(self.data_dir, self.standard_structure)
        
        print(f"\n{BOLD}目录统计:{END}")
        print(f"  新建目录: {len(created)}")
        print(f"  已存在目录: {len(existing)}")
        
        return created, existing
    
    def count_files(self, directory, pattern="*"):
        """统计目录中的文件数量"""
        if not directory.exists():
            return 0
        return len(list(directory.glob(pattern)))
    
    def get_dir_size(self, directory):
        """获取目录大小"""
        if not directory.exists():
            return 0
        
        total_size = 0
        for item in directory.rglob('*'):
            if item.is_file():
                total_size += item.stat().st_size
        
        return total_size
    
    def format_size(self, size_bytes):
        """格式化文件大小"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    def show_statistics(self):
        """显示数据统计信息"""
        self.print_header("数据统计")
        
        stats = []
        
        # 原始PDF
        pdf_dir = self.data_dir / "raw" / "pdfs"
        pdf_count = self.count_files(pdf_dir, "*.pdf")
        pdf_size = self.get_dir_size(pdf_dir)
        stats.append(("原始PDF文件", pdf_count, pdf_size, pdf_dir))
        
        # 解析结果
        parsed_dir = self.data_dir / "processed" / "parsed" / "output"
        if parsed_dir.exists():
            batch_count = len([d for d in parsed_dir.iterdir() if d.is_dir()])
            parsed_size = self.get_dir_size(parsed_dir)
            stats.append(("解析结果批次", batch_count, parsed_size, parsed_dir))
        
        # 分析结果
        analyzed_dir = self.data_dir / "processed" / "analyzed"
        analyzed_count = self.count_files(analyzed_dir)
        analyzed_size = self.get_dir_size(analyzed_dir)
        stats.append(("AI提取结果", analyzed_count, analyzed_size, analyzed_dir))
        
        # Excel导出
        exports_dir = self.data_dir / "exports"
        exports_count = self.count_files(exports_dir, "*.xlsx")
        exports_size = self.get_dir_size(exports_dir)
        stats.append(("Excel导出", exports_count, exports_size, exports_dir))
        
        # 数据库
        db_file = self.data_dir / "artificial_joint.db"
        if db_file.exists():
            db_size = db_file.stat().st_size
            stats.append(("数据库文件", 1, db_size, db_file))
        
        # 打印统计表格
        print(f"{BOLD}{'类型':<20} {'数量':<10} {'大小':<15} {'路径'}{END}")
        print("-" * 80)
        
        total_size = 0
        for name, count, size, path in stats:
            total_size += size
            size_str = self.format_size(size)
            print(f"{name:<20} {count:<10} {size_str:<15} {path}")
        
        print("-" * 80)
        print(f"{'总计':<20} {'':<10} {self.format_size(total_size):<15}")
    
    def check_empty_directories(self):
        """检查并报告空目录"""
        self.print_header("检查空目录")
        
        empty_dirs = []
        
        def check_dir(directory, level=0):
            if not directory.exists() or not directory.is_dir():
                return
            
            indent = "  " * level
            items = list(directory.iterdir())
            
            if not items:
                empty_dirs.append(directory)
                print(f"{indent}{YELLOW}⚠ 空目录:{END} {directory}")
            else:
                for item in items:
                    if item.is_dir():
                        check_dir(item, level + 1)
        
        check_dir(self.data_dir)
        
        if not empty_dirs:
            print(f"{GREEN}✓ 没有发现空目录{END}")
        else:
            print(f"\n{BOLD}空目录总数:{END} {len(empty_dirs)}")
            print(f"{YELLOW}提示: 空目录是正常的，它们用于组织未来的数据{END}")
        
        return empty_dirs
    
    def verify_config(self):
        """验证配置一致性"""
        self.print_header("验证配置")
        
        # 检查.env文件
        env_file = self.project_root / ".env"
        if env_file.exists():
            print(f"{GREEN}✓{END} .env 文件存在")
        else:
            print(f"{RED}✗{END} .env 文件不存在")
            print(f"   {YELLOW}建议:{END} 复制 .env.example 并填写配置")
        
        # 检查config.py
        config_file = self.project_root / "config" / "config.py"
        if config_file.exists():
            print(f"{GREEN}✓{END} config/config.py 存在")
            
            # 检查是否使用环境变量
            content = config_file.read_text()
            if "os.getenv" in content or "load_dotenv" in content:
                print(f"  {GREEN}✓{END} 使用环境变量配置")
            else:
                print(f"  {YELLOW}⚠{END} 可能仍在使用硬编码配置")
        else:
            print(f"{RED}✗{END} config/config.py 不存在")
        
        # 检查批次记录文件
        batch_csv = self.data_dir / "uploads" / "upload_batches.csv"
        if batch_csv.exists():
            print(f"{GREEN}✓{END} 批次记录文件存在: {batch_csv}")
            
            # 统计批次数量
            import csv
            with open(batch_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                batches = list(reader)
                if batches:
                    print(f"  {BOLD}已记录批次:{END} {len(batches)}")
        else:
            print(f"{YELLOW}⚠{END} 批次记录文件不存在（尚未上传过文件）")
    
    def generate_report(self):
        """生成完整报告"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = self.data_dir / f"data_organization_report_{timestamp}.txt"
        
        print(f"\n{BLUE}生成详细报告: {report_file}{END}")
        
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write("="*70 + "\n")
            f.write(f"数据组织报告 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("="*70 + "\n\n")
            
            f.write("目录结构:\n")
            f.write("-"*70 + "\n")
            
            def write_tree(directory, level=0, file_obj=f):
                if not directory.exists():
                    return
                
                indent = "  " * level
                f.write(f"{indent}{directory.name}/\n")
                
                try:
                    items = sorted(directory.iterdir())
                    for item in items:
                        if item.is_dir():
                            write_tree(item, level + 1, file_obj)
                        else:
                            size = self.format_size(item.stat().st_size)
                            f.write(f"{indent}  {item.name} ({size})\n")
                except PermissionError:
                    f.write(f"{indent}  [权限不足]\n")
            
            write_tree(self.data_dir)
        
        print(f"{GREEN}✓ 报告已生成{END}")
        return report_file
    
    def run(self, generate_report=False):
        """运行完整的组织流程"""
        print(f"\n{BOLD}数据组织工具{END}")
        print(f"项目根目录: {self.project_root}")
        print(f"数据目录: {self.data_dir}")
        
        # 1. 确保目录结构
        self.ensure_directory_structure()
        
        # 2. 显示统计信息
        self.show_statistics()
        
        # 3. 检查空目录
        self.check_empty_directories()
        
        # 4. 验证配置
        self.verify_config()
        
        # 5. 生成报告（可选）
        if generate_report:
            self.generate_report()
        
        # 总结
        self.print_header("完成")
        print(f"{GREEN}✓ 数据目录组织完成{END}")
        print(f"\n{BOLD}后续步骤:{END}")
        print(f"  1. 将PDF文件放入: {self.data_dir / 'raw' / 'pdfs'}")
        print(f"  2. 运行上传: python scripts/pdf_pipeline.py upload")
        print(f"  3. 查看指南: docs/PDF_PIPELINE_GUIDE.md")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="数据组织工具")
    parser.add_argument("--report", action="store_true", help="生成详细报告")
    args = parser.parse_args()
    
    organizer = DataOrganizer()
    organizer.run(generate_report=args.report)


if __name__ == "__main__":
    main()
