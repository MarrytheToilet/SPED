#!/usr/bin/env python3
"""
快速日志查看工具

功能:
1. 快速查看最新的调试日志
2. 查看超时错误的详情
3. 实时监控日志
"""
import os
from pathlib import Path
from datetime import datetime, timedelta

def show_recent_logs(hours=1):
    """显示最近的日志"""
    debug_dir = Path("logs/debug")
    
    if not debug_dir.exists():
        print("❌ 调试目录不存在")
        return
    
    print(f"🔍 最近 {hours} 小时的调试记录:\n")
    
    # 获取指定时间内的文件
    cutoff_time = datetime.now() - timedelta(hours=hours)
    recent_files = []
    
    for file in debug_dir.glob("*"):
        if file.stat().st_mtime > cutoff_time.timestamp():
            recent_files.append((file, datetime.fromtimestamp(file.stat().st_mtime)))
    
    recent_files.sort(key=lambda x: x[1], reverse=True)
    
    if not recent_files:
        print(f"⚠️ 没有找到最近 {hours} 小时内的记录")
        return
    
    for file, timestamp in recent_files[:20]:  # 只显示最新的20个
        file_type = ""
        status_emoji = ""
        
        if "input.txt" in file.name:
            file_type = "📥 输入"
            status_emoji = "⏳"
        elif "output.txt" in file.name:
            file_type = "📤 输出"
            status_emoji = "⏳"
        elif "parsed.json" in file.name:
            file_type = "✅ 成功"
            status_emoji = "✅"
        elif "error" in file.name:
            file_type = "❌ 错误"
            status_emoji = "❌"
        elif "parse_error" in file.name:
            file_type = "⚠️ 解析失败"
            status_emoji = "⚠️"
        
        print(f"{status_emoji} {timestamp.strftime('%H:%M:%S')} - {file_type} - {file.name}")

def show_timeout_errors():
    """显示超时错误详情"""
    debug_dir = Path("logs/debug")
    
    if not debug_dir.exists():
        print("❌ 调试目录不存在")
        return
    
    print("🕐 查找超时错误:\n")
    
    timeout_files = []
    for error_file in debug_dir.glob("*error*.txt"):
        try:
            with open(error_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if "timeout" in content.lower() or "timed out" in content.lower():
                    timestamp = datetime.fromtimestamp(error_file.stat().st_mtime)
                    timeout_files.append((error_file, timestamp, content))
        except:
            continue
    
    if not timeout_files:
        print("✅ 没有发现超时错误")
        return
    
    timeout_files.sort(key=lambda x: x[1], reverse=True)
    
    for error_file, timestamp, content in timeout_files[:5]:  # 显示最新的5个
        print(f"❌ {timestamp.strftime('%Y-%m-%d %H:%M:%S')} - {error_file.name}")
        
        # 提取关键信息
        lines = content.split('\n')
        for line in lines:
            if any(keyword in line.lower() for keyword in ['论文id', 'paper_id', '错误', 'error', '尝试']):
                print(f"   {line.strip()}")
        
        # 找到对应的输入文件
        call_id = error_file.stem.replace("_error_1", "").replace("_error_2", "").replace("_error_3", "")
        input_file = debug_dir / f"{call_id}_input.txt"
        
        if input_file.exists():
            try:
                with open(input_file, 'r', encoding='utf-8') as f:
                    input_content = f.read()
                    # 提取prompt长度
                    for line in input_content.split('\n'):
                        if "Prompt长度" in line:
                            print(f"   {line.strip()}")
                            break
            except:
                pass
        
        print()

def show_latest_call():
    """显示最新的LLM调用"""
    debug_dir = Path("logs/debug")
    
    if not debug_dir.exists():
        print("❌ 调试目录不存在")
        return
    
    # 找到最新的输入文件
    input_files = list(debug_dir.glob("*_input.txt"))
    if not input_files:
        print("❌ 没有找到调用记录")
        return
    
    latest_input = max(input_files, key=lambda f: f.stat().st_mtime)
    call_id = latest_input.stem.replace("_input", "")
    
    print(f"🔍 最新LLM调用: {call_id}")
    print("=" * 60)
    
    # 显示输入信息
    try:
        with open(latest_input, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
            for line in lines[:10]:  # 显示前10行
                if line.strip() and not line.startswith('='):
                    print(f"📥 {line}")
    except:
        print("❌ 无法读取输入文件")
    
    # 检查状态
    output_file = debug_dir / f"{call_id}_output.txt"
    parsed_file = debug_dir / f"{call_id}_parsed.json" 
    error_files = list(debug_dir.glob(f"{call_id}_error_*.txt"))
    
    print(f"\n📊 调用状态:")
    if parsed_file.exists():
        print("  ✅ 成功完成")
    elif error_files:
        print("  ❌ 调用失败")
        # 显示错误
        latest_error = max(error_files, key=lambda f: f.stat().st_mtime)
        try:
            with open(latest_error, 'r', encoding='utf-8') as f:
                content = f.read()
                for line in content.split('\n')[:5]:
                    if line.strip() and '错误' in line:
                        print(f"    {line.strip()}")
        except:
            pass
    elif output_file.exists():
        print("  ⏳ 等待解析")
    else:
        print("  ⏳ 进行中")

def main():
    print("🛠️  LLM调试工具 - 快速查看")
    print("=" * 60)
    
    # 显示最新调用
    show_latest_call()
    
    print("\n" + "=" * 60)
    
    # 显示最近1小时的日志
    show_recent_logs(1)
    
    print("\n" + "=" * 60)
    
    # 显示超时错误
    show_timeout_errors()
    
    print("\n💡 使用说明:")
    print("  详细调试: python scripts/debug.py stats")
    print("  查看论文: python scripts/debug.py papers")
    print("  调用详情: python scripts/debug.py call CALL_ID")

if __name__ == "__main__":
    main()