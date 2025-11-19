#!/usr/bin/env python3
"""
交互式UI - 处理用户交互
"""
from typing import List, Dict, Optional


class InteractiveUI:
    """交互式用户界面"""
    
    @staticmethod
    def select_paper(papers: List[Dict]) -> Optional[Dict]:
        """
        交互式选择论文
        
        Args:
            papers: 论文列表
        
        Returns:
            Dict: 选中的论文，或None（取消）
        """
        if not papers:
            print("❌ 未找到已解析论文")
            print("   请先使用 scripts/pdf_process.py 解析PDF文件")
            return None
        
        print(f"找到 {len(papers)} 篇已解析论文:\n")
        
        # 显示论文列表（分页显示，每页20个）
        page_size = 20
        for i, paper in enumerate(papers[:page_size], 1):
            print(f"  {i:2d}. {paper['name']}")
        
        if len(papers) > page_size:
            print(f"\n  ... 还有 {len(papers) - page_size} 篇论文")
        
        # 用户选择
        try:
            choice = input(f"\n请选择论文编号 (1-{len(papers)}): ").strip()
            if not choice:
                print("取消操作")
                return None
            
            idx = int(choice) - 1
            if 0 <= idx < len(papers):
                return papers[idx]
            else:
                print("❌ 无效的选择")
                return None
                
        except (ValueError, KeyboardInterrupt):
            print("\n取消操作")
            return None
    
    @staticmethod
    def select_mode(default: str = "full") -> str:
        """
        交互式选择提取模式
        
        Args:
            default: 默认模式
        
        Returns:
            str: 选择的模式
        """
        print("请选择提取模式:")
        print("  1. full  - 全文提取（一次性处理，速度快，适合中短文本）")
        print("  2. chunk - 分块提取（适合长文本，LLM自动判断new/enrich）")
        
        mode_choice = input("\n选择模式 (1/2，默认1): ").strip()
        
        if mode_choice == "2":
            mode = "chunk"
            print("✓ 已选择：分块模式\n")
        else:
            mode = "full"
            print("✓ 已选择：全文模式\n")
        
        return mode
    
    @staticmethod
    def confirm_batch(count: int) -> bool:
        """
        确认批量操作
        
        Args:
            count: 论文数量
        
        Returns:
            bool: 是否确认
        """
        confirm = input(f"\n⚠️  确认开始批量提取 {count} 篇论文？(y/N): ").strip().lower()
        return confirm == 'y'
