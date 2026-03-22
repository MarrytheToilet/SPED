#!/usr/bin/env python3
"""
调试工具 - 查看LLM调用日志和输入输出

功能:
1. 列出所有调试文件
2. 查看特定论文的调用详情
3. 分析失败原因
4. 统计成功率
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

class DebugAnalyzer:
    """调试分析器"""
    
    def __init__(self, debug_dir: Path = None):
        if debug_dir is None:
            debug_dir = Path("logs/debug")
        self.debug_dir = debug_dir
        self.debug_dir.mkdir(parents=True, exist_ok=True)
    
    def list_papers(self) -> List[str]:
        """列出所有有调试记录的论文"""
        papers = set()
        
        if not self.debug_dir.exists():
            return []
        
        for file in self.debug_dir.glob("*_*"):
            if "_" in file.stem:
                paper_id = file.stem.split("_")[0]
                papers.add(paper_id)
        
        return sorted(papers)
    
    def list_calls(self, paper_id: str = None) -> List[Dict[str, Any]]:
        """列出所有LLM调用"""
        calls = []
        
        pattern = f"{paper_id}_*" if paper_id else "*_*"
        
        for input_file in self.debug_dir.glob(f"{pattern}_input.txt"):
            call_id = input_file.stem.replace("_input", "")
            
            call_info = {
                "call_id": call_id,
                "paper_id": call_id.split("_")[0],
                "input_file": input_file,
                "output_file": self.debug_dir / f"{call_id}_output.txt",
                "parsed_file": self.debug_dir / f"{call_id}_parsed.json",
                "error_files": list(self.debug_dir.glob(f"{call_id}_error_*.txt")),
                "parse_error_file": self.debug_dir / f"{call_id}_parse_error.txt"
            }
            
            # 判断状态
            if call_info["parsed_file"].exists():
                call_info["status"] = "success"
            elif call_info["parse_error_file"].exists():
                call_info["status"] = "parse_failed"
            elif call_info["error_files"]:
                call_info["status"] = "call_failed"
            elif call_info["output_file"].exists():
                call_info["status"] = "pending_parse"
            else:
                call_info["status"] = "no_output"
            
            # 获取时间信息
            if input_file.exists():
                call_info["timestamp"] = datetime.fromtimestamp(input_file.stat().st_mtime)
            
            calls.append(call_info)
        
        return sorted(calls, key=lambda x: x.get("timestamp", datetime.min))
    
    def show_call_details(self, call_id: str):
        """显示特定调用的详细信息"""
        print(f"\n{'='*80}")
        print(f"LLM调用详情: {call_id}")
        print(f"{'='*80}")
        
        input_file = self.debug_dir / f"{call_id}_input.txt"
        output_file = self.debug_dir / f"{call_id}_output.txt"
        parsed_file = self.debug_dir / f"{call_id}_parsed.json"
        parse_error_file = self.debug_dir / f"{call_id}_parse_error.txt"
        
        # 显示输入信息
        if input_file.exists():
            with open(input_file, 'r', encoding='utf-8') as f:
                content = f.read()
                # 只显示头部信息
                lines = content.split('\n')
                header_end = -1
                for i, line in enumerate(lines):
                    if '=' * 60 in line:
                        header_end = i
                        break
                
                if header_end > 0:
                    print("📥 输入信息:")
                    for line in lines[:header_end]:
                        print(f"  {line}")
                    
                    prompt_length = len('\n'.join(lines[header_end+1:]))
                    print(f"  Prompt内容长度: {prompt_length:,} 字符")
                else:
                    print(f"  📄 输入文件: {input_file}")
        else:
            print("❌ 找不到输入文件")
        
        # 显示输出信息
        print(f"\n📤 输出信息:")
        if output_file.exists():
            with open(output_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                # 显示头部信息
                for i, line in enumerate(lines):
                    if '=' * 60 in line:
                        for header_line in lines[:i]:
                            print(f"  {header_line}")
                        break
                
                # 显示输出预览
                response_start = False
                response_lines = []
                for line in lines:
                    if '=' * 60 in line:
                        response_start = True
                        continue
                    if response_start:
                        response_lines.append(line)
                
                if response_lines:
                    response = '\n'.join(response_lines)
                    print(f"  响应内容预览 (前500字符):")
                    print(f"  {response[:500]}")
                    if len(response) > 500:
                        print(f"  ... (还有 {len(response)-500:,} 字符)")
        else:
            print("  ❌ 找不到输出文件")
        
        # 显示解析结果
        print(f"\n🔍 解析结果:")
        if parsed_file.exists():
            try:
                with open(parsed_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if isinstance(data, dict) and "records" in data:
                    records = data["records"]
                    print(f"  ✅ 解析成功: {len(records)} 条记录")
                    
                    if records:
                        print(f"  示例记录:")
                        example = records[0]
                        for key, value in list(example.items())[:3]:
                            print(f"    {key}: {str(value)[:100]}")
                else:
                    print(f"  ⚠️ 数据格式异常: {type(data)}")
            except Exception as e:
                print(f"  ❌ 读取解析结果失败: {e}")
        elif parse_error_file.exists():
            print("  ❌ JSON解析失败")
            try:
                with open(parse_error_file, 'r', encoding='utf-8') as f:
                    error_content = f.read()
                    print(f"  错误详情:")
                    for line in error_content.split('\n')[:10]:
                        if line.strip():
                            print(f"    {line}")
            except:
                pass
        else:
            print("  ⏳ 未找到解析结果")
        
        # 显示错误信息
        error_files = list(self.debug_dir.glob(f"{call_id}_error_*.txt"))
        if error_files:
            print(f"\n❌ 错误信息:")
            for error_file in error_files:
                print(f"  📄 {error_file.name}:")
                try:
                    with open(error_file, 'r', encoding='utf-8') as f:
                        content = f.read()
                        lines = content.split('\n')[:15]  # 只显示前15行
                        for line in lines:
                            if line.strip():
                                print(f"    {line}")
                except:
                    print("    无法读取错误文件")
        
        print(f"\n💡 相关文件:")
        print(f"  输入: {input_file}")
        print(f"  输出: {output_file}")
        if parsed_file.exists():
            print(f"  解析结果: {parsed_file}")
        for error_file in error_files:
            print(f"  错误日志: {error_file}")
    
    def show_statistics(self) -> Dict[str, Any]:
        """显示统计信息"""
        calls = self.list_calls()
        
        if not calls:
            print("❌ 没有找到调试记录")
            return {}
        
        # 统计
        stats = {
            "total_calls": len(calls),
            "success": 0,
            "parse_failed": 0,
            "call_failed": 0,
            "pending": 0,
            "papers": len(set(call["paper_id"] for call in calls)),
            "latest": max(call.get("timestamp", datetime.min) for call in calls)
        }
        
        for call in calls:
            stats[call["status"]] = stats.get(call["status"], 0) + 1
        
        print(f"\n{'='*60}")
        print(f"LLM调用统计")
        print(f"{'='*60}")
        print(f"📊 总体统计:")
        print(f"  总调用次数: {stats['total_calls']}")
        print(f"  涉及论文: {stats['papers']} 篇")
        print(f"  最新调用: {stats['latest'].strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📈 成功率统计:")
        success_rate = (stats.get('success', 0) / stats['total_calls'] * 100) if stats['total_calls'] > 0 else 0
        print(f"  ✅ 成功: {stats.get('success', 0)} ({success_rate:.1f}%)")
        print(f"  ❌ JSON解析失败: {stats.get('parse_failed', 0)}")
        print(f"  ❌ LLM调用失败: {stats.get('call_failed', 0)}")
        print(f"  ⏳ 其他状态: {stats.get('pending_parse', 0) + stats.get('no_output', 0)}")
        
        return stats
    
    def show_paper_summary(self, paper_id: str):
        """显示特定论文的调用总结"""
        calls = self.list_calls(paper_id)
        
        if not calls:
            print(f"❌ 论文 {paper_id} 没有调试记录")
            return
        
        print(f"\n{'='*60}")
        print(f"论文调试总结: {paper_id}")
        print(f"{'='*60}")
        
        for i, call in enumerate(calls, 1):
            status_emoji = {
                "success": "✅",
                "parse_failed": "⚠️",
                "call_failed": "❌", 
                "pending_parse": "⏳",
                "no_output": "⏳"
            }.get(call["status"], "❓")
            
            timestamp = call.get("timestamp", datetime.min)
            print(f"{i:2d}. {status_emoji} {call['call_id']} ({timestamp.strftime('%H:%M:%S')})")
        
        # 统计
        success_count = sum(1 for call in calls if call["status"] == "success")
        print(f"\n📈 成功率: {success_count}/{len(calls)} ({success_count/len(calls)*100:.1f}%)")
        
        # 显示最新的失败调用
        failed_calls = [call for call in calls if call["status"] in ["parse_failed", "call_failed"]]
        if failed_calls:
            latest_failed = failed_calls[-1]
            print(f"\n🔍 最新失败调用: {latest_failed['call_id']}")
            print(f"   可以用命令查看详情: python scripts/debug.py call {latest_failed['call_id']}")


def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="LLM调试工具")
    subparsers = parser.add_subparsers(dest='action', help='操作类型')
    
    # list命令
    list_parser = subparsers.add_parser('list', help='列出调试记录')
    list_parser.add_argument('--paper', help='指定论文ID')
    
    # stats命令
    stats_parser = subparsers.add_parser('stats', help='显示统计信息')
    
    # call命令
    call_parser = subparsers.add_parser('call', help='查看特定调用详情')
    call_parser.add_argument('call_id', help='调用ID')
    
    # paper命令
    paper_parser = subparsers.add_parser('paper', help='查看论文调用总结')
    paper_parser.add_argument('paper_id', help='论文ID')
    
    # papers命令
    papers_parser = subparsers.add_parser('papers', help='列出所有论文')
    
    args = parser.parse_args()
    
    analyzer = DebugAnalyzer()
    
    if args.action == 'list':
        calls = analyzer.list_calls(args.paper)
        if not calls:
            print("❌ 没有找到调试记录")
            return
        
        print(f"📋 LLM调用记录 (共 {len(calls)} 条):")
        for call in calls[-20:]:  # 显示最新的20条
            status_emoji = {
                "success": "✅",
                "parse_failed": "⚠️", 
                "call_failed": "❌",
                "pending_parse": "⏳",
                "no_output": "⏳"
            }.get(call["status"], "❓")
            
            timestamp = call.get("timestamp", datetime.min)
            print(f"  {status_emoji} {call['call_id']} ({timestamp.strftime('%m-%d %H:%M')})")
    
    elif args.action == 'stats':
        analyzer.show_statistics()
    
    elif args.action == 'call':
        analyzer.show_call_details(args.call_id)
    
    elif args.action == 'paper':
        analyzer.show_paper_summary(args.paper_id)
    
    elif args.action == 'papers':
        papers = analyzer.list_papers()
        if not papers:
            print("❌ 没有找到论文调试记录")
            return
        
        print(f"📚 有调试记录的论文 (共 {len(papers)} 篇):")
        for paper in papers:
            calls = analyzer.list_calls(paper)
            success_count = sum(1 for call in calls if call["status"] == "success")
            total_count = len(calls)
            print(f"  📄 {paper}: {success_count}/{total_count} 成功")
    
    else:
        parser.print_help()
        print(f"\n常用命令:")
        print(f"  python scripts/debug.py papers        # 列出所有论文")
        print(f"  python scripts/debug.py stats         # 查看统计信息")
        print(f"  python scripts/debug.py paper PAPER_ID   # 查看论文详情")
        print(f"  python scripts/debug.py call CALL_ID     # 查看调用详情")


if __name__ == "__main__":
    main()