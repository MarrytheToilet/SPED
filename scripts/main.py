"""
主入口 - PDF批量解析工具
"""
import sys
import os


def print_help():
    """打印帮助信息"""
    help_text = """
    ╔═══════════════════════════════════════════════════════════════╗
    ║           PDF 批量解析工具 - MinerU API                        ║
    ╚═══════════════════════════════════════════════════════════════╝
    
    使用方法：
        python main.py [命令]
    
    可用命令：
        upload      上传PDF文件到服务器进行解析
        status      查询处理状态
        download    下载并解压处理结果
        help        显示此帮助信息
    
    完整流程：
        1. python main.py upload     # 上传PDF文件
        2. python main.py status     # 查询处理状态
        3. python main.py download   # 下载处理结果
    
    配置文件：
        config.py - 修改API密钥、路径等配置
    
    目录结构：
        pdfs/       - 放置待解析的PDF文件
        output/     - 下载的解析结果
        upload_batches.csv - 批次记录
    """
    print(help_text)


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("❌ 缺少命令参数")
        print_help()
        return
    
    command = sys.argv[1].lower()
    
    if command == "upload":
        print("🚀 开始上传PDF文件...")
        import upload
        upload.main()
    
    elif command == "status":
        print("📊 查询处理状态...")
        import request
        request.main()
    
    elif command == "download":
        print("📥 开始下载处理结果...")
        import download
        download.main()
    
    elif command == "help":
        print_help()
    
    else:
        print(f"❌ 未知命令：{command}")
        print_help()


if __name__ == "__main__":
    main()
