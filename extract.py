#!/usr/bin/env python3
"""
人工关节材料数据提取系统 - 主程序

功能:
1. 测试系统 - 检查配置和依赖
2. 单个提取 - 从单个论文提取数据
3. 批量提取 - 批量处理多个论文
4. 查看prompt - 显示当前使用的prompt

使用:
    python extract.py test              # 测试系统
    python extract.py single <paper>    # 单个提取
    python extract.py batch             # 批量提取
    python extract.py prompt            # 查看prompt
"""

import sys
import os
from pathlib import Path
import json

# 添加项目路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.agents.llm_agent import LLMExtractionAgent
from loguru import logger
import settings


def test_system():
    """测试系统配置"""
    print("\n" + "="*80)
    print("系统测试")
    print("="*80 + "\n")
    
    # 1. 检查环境变量
    print("1. 检查环境变量")
    if settings.OPENAI_API_KEY:
        print(f"   ✅ OPENAI_API_KEY: {settings.OPENAI_API_KEY[:10]}...")
    else:
        print(f"   ❌ OPENAI_API_KEY 未设置")
        return False
    
    print(f"   ✅ OPENAI_MODEL: {settings.OPENAI_MODEL}")
    print(f"   ✅ OPENAI_API_BASE: {settings.OPENAI_API_BASE}")
    
    # 2. 检查配置
    print("\n2. 检查配置")
    print(f"   ✅ CHUNK_SIZE: {settings.CHUNK_SIZE}")
    print(f"   ✅ CHUNK_OVERLAP: {settings.CHUNK_OVERLAP}")
    
    # 3. 检查目录
    print("\n3. 检查目录")
    dirs_to_check = [
        settings.PARSED_DIR,
        settings.EXTRACTED_DIR,
        settings.SCHEMA_DIR,
    ]
    
    for dir_path in dirs_to_check:
        if dir_path.exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ⚠️  {dir_path} (不存在)")
    
    # 4. 检查prompt
    print("\n4. 检查Prompt文件")
    prompt_path = project_root / "prompts" / "prompt.md"
    if prompt_path.exists():
        size = prompt_path.stat().st_size / 1024
        print(f"   ✅ prompt.md ({size:.1f} KB)")
    else:
        print(f"   ❌ prompt.md 不存在")
        return False
    
    # 5. 检查论文
    print("\n5. 检查已解析论文")
    parsed_papers = list_parsed_papers()
    if parsed_papers:
        print(f"   ✅ 找到 {len(parsed_papers)} 篇已解析论文")
        for i, paper in enumerate(parsed_papers[:3], 1):
            print(f"      {i}. {paper['name']}")
        if len(parsed_papers) > 3:
            print(f"      ... 还有 {len(parsed_papers) - 3} 篇")
    else:
        print(f"   ⚠️  未找到已解析论文")
        print(f"      请先使用MinerU解析PDF文件")
    
    # 6. 测试API连接
    print("\n6. 测试API连接")
    try:
        from openai import OpenAI
        client = OpenAI(api_key=settings.OPENAI_API_KEY, base_url=settings.OPENAI_API_BASE)
        
        # 简单测试
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[{"role": "user", "content": "test"}],
            max_tokens=5
        )
        print(f"   ✅ API连接成功")
    except Exception as e:
        print(f"   ❌ API连接失败: {e}")
        return False
    
    print("\n" + "="*80)
    print("✅ 系统测试通过！")
    print("="*80)
    return True


def list_parsed_papers():
    """列出所有已解析的论文"""
    papers = []
    
    # 搜索所有full.md文件
    for full_md in settings.PARSED_DIR.rglob("full.md"):
        paper_dir = full_md.parent
        papers.append({
            'name': paper_dir.name,
            'path': paper_dir,
            'full_md': full_md
        })
    
    return sorted(papers, key=lambda x: x['name'])


def extract_single(paper_path=None):
    """单个论文提取"""
    print("\n" + "="*80)
    print("单个论文数据提取")
    print("="*80 + "\n")
    
    # 如果没指定论文，列出可选论文
    if not paper_path:
        papers = list_parsed_papers()
        
        if not papers:
            print("❌ 未找到已解析论文")
            print("   请先使用MinerU解析PDF文件到: data/processed/parsed/")
            return
        
        print(f"找到 {len(papers)} 篇已解析论文:\n")
        for i, paper in enumerate(papers, 1):
            print(f"  {i}. {paper['name']}")
        
        print("\n请选择论文编号 (1-{}): ".format(len(papers)), end='')
        try:
            choice = int(input().strip())
            if 1 <= choice <= len(papers):
                paper_path = papers[choice - 1]['path']
            else:
                print("❌ 无效的选择")
                return
        except (ValueError, KeyboardInterrupt):
            print("\n取消")
            return
    else:
        paper_path = Path(paper_path)
    
    # 检查full.md
    full_md = paper_path / "full.md"
    if not full_md.exists():
        print(f"❌ 未找到 {full_md}")
        return
    
    paper_id = paper_path.name
    print(f"\n开始提取: {paper_id}\n")
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 创建agent并提取
    agent = LLMExtractionAgent()
    
    try:
        result = agent.process({
            "paper_id": paper_id,
            "full_text_path": str(full_md)
        })
        
        # 显示结果
        print("\n" + "="*80)
        print("提取结果")
        print("="*80 + "\n")
        
        if isinstance(result, dict):
            if "records" in result:
                records = result["records"]
                count = len(records)
            elif "count" in result:
                count = result.get("count", 0)
                records = []
            else:
                records = [result]
                count = 1
        else:
            records = [result]
            count = 1
        
        print(f"提取到 {count} 条记录\n")
        
        # 显示记录摘要
        for i, record in enumerate(records[:3], 1):
            print(f"记录 {i}:")
            
            key_fields = [
                '数据标识',
                '应用部位',
                '球头信息.球头基本信息',
                '内衬信息.内衬-基本信息'
            ]
            
            for field in key_fields:
                value = record.get(field)
                if value and str(value) != 'null':
                    display_value = str(value)[:100]
                    print(f"  {field}: {display_value}")
            
            non_null = sum(1 for v in record.values() if v and str(v) != 'null')
            print(f"  非空字段: {non_null}\n")
        
        if count > 3:
            print(f"...还有 {count - 3} 条记录\n")
        
        # 保存结果
        output_dir = settings.EXTRACTED_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = output_dir / f"{paper_id}.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"✅ 结果已保存到: {output_file}")
        print("="*80)
        
    except Exception as e:
        print(f"\n❌ 提取失败: {e}")
        import traceback
        traceback.print_exc()


def extract_batch():
    """批量提取"""
    print("\n" + "="*80)
    print("批量数据提取")
    print("="*80 + "\n")
    
    papers = list_parsed_papers()
    
    if not papers:
        print("❌ 未找到已解析论文")
        return
    
    print(f"找到 {len(papers)} 篇论文")
    print(f"开始批量提取...\n")
    
    # 配置日志
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO"
    )
    
    # 创建agent
    agent = LLMExtractionAgent()
    
    success_count = 0
    fail_count = 0
    
    for i, paper in enumerate(papers, 1):
        print(f"\n{'='*80}")
        print(f"[{i}/{len(papers)}] {paper['name']}")
        print(f"{'='*80}\n")
        
        try:
            result = agent.process({
                "paper_id": paper['name'],
                "full_text_path": str(paper['full_md'])
            })
            
            # 保存结果
            output_file = settings.EXTRACTED_DIR / f"{paper['name']}.json"
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            
            count = result.get('count', 1) if isinstance(result, dict) else 1
            print(f"\n✅ 成功: 提取 {count} 条记录")
            success_count += 1
            
        except Exception as e:
            print(f"\n❌ 失败: {e}")
            fail_count += 1
        
        # 间隔
        if i < len(papers):
            import time
            time.sleep(2)
    
    # 总结
    print(f"\n{'='*80}")
    print("批量提取完成")
    print(f"{'='*80}")
    print(f"成功: {success_count}")
    print(f"失败: {fail_count}")
    print(f"总计: {len(papers)}")
    print(f"{'='*80}\n")


def show_prompt():
    """显示prompt内容"""
    prompt_path = project_root / "prompts" / "prompt.md"
    
    if not prompt_path.exists():
        print("❌ 未找到prompt文件")
        return
    
    print("\n" + "="*80)
    print("当前Prompt内容")
    print("="*80 + "\n")
    
    with open(prompt_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    print(content[:2000])
    print("\n...")
    print(f"\n总长度: {len(content)} 字符")
    print(f"文件路径: {prompt_path}")
    print("="*80)


def show_help():
    """显示帮助"""
    print("""
╔══════════════════════════════════════════════════════════════════════════════╗
║              人工关节材料数据提取系统 v1.1                                      ║
╚══════════════════════════════════════════════════════════════════════════════╝

使用方法:
  python extract.py <命令> [选项]

命令:
  test              测试系统配置和连接
  single [论文]     单个论文数据提取
  batch             批量提取所有论文
  prompt            查看当前prompt内容
  help              显示此帮助

示例:
  # 1. 首次使用，测试系统
  python extract.py test

  # 2. 单个论文提取（交互式选择）
  python extract.py single

  # 3. 指定论文提取
  python extract.py single "data/processed/parsed/output/batch_1/论文名"

  # 4. 批量提取所有论文
  python extract.py batch

  # 5. 查看prompt
  python extract.py prompt

配置:
  编辑 .env 文件调整参数:
    CHUNK_SIZE=4000          # chunk大小
    CHUNK_OVERLAP=300        # 重叠大小
    OPENAI_MODEL=gpt-4o      # 使用的模型
    OPENAI_API_KEY=sk-xxx    # API密钥

文档:
  README.md                  - 项目说明
  README_IMPROVEMENTS_CN.md  - 改进详情
  QUICK_START.md             - 快速开始

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")


def main():
    """主函数"""
    if len(sys.argv) < 2:
        show_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == 'test':
        test_system()
    
    elif command == 'single':
        paper_path = sys.argv[2] if len(sys.argv) > 2 else None
        extract_single(paper_path)
    
    elif command == 'batch':
        extract_batch()
    
    elif command == 'prompt':
        show_prompt()
    
    elif command in ['help', '-h', '--help']:
        show_help()
    
    else:
        print(f"❌ 未知命令: {command}")
        print("使用 'python extract.py help' 查看帮助")


if __name__ == "__main__":
    main()
