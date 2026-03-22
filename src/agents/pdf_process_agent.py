"""
PDF处理Agent - 简化版，使用统一的PDFProcessor

功能:
1. 扫描并注册PDF文件
2. 批量上传到MinerU
3. 查询处理状态
4. 下载解析结果
"""
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.agents.base import BaseAgent, AgentResult
from src.pdfs.pdf_processor import PDFProcessor


class PDFProcessAgent(BaseAgent[Path, Dict[str, Any]]):
    """
    PDF处理Agent - 简化版
    
    特性:
    - 基于文件哈希去重
    - SQLite状态持久化
    - 支持断点续传
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(
            name="PDFProcessAgent",
            description="PDF解析和下载Agent",
            config=config or {}
        )
        self.processor = PDFProcessor()
        self.log_info("PDFProcessAgent初始化完成")
    
    def process(self, input_data: Any) -> AgentResult[Dict[str, Any]]:
        """
        处理PDF目录 - 扫描并上传新PDF
        
        Args:
            input_data: PDF目录路径
        
        Returns:
            AgentResult包含batch_ids列表
        """
        try:
            pdf_dir = Path(input_data) if input_data else None
            
            self.log_info(f"开始处理PDF目录: {pdf_dir}")
            
            # 扫描新PDF
            new_pdfs = self.processor.scan_new_pdfs(pdf_dir)
            
            if not new_pdfs:
                self.log_info("没有新PDF需要上传")
                return AgentResult(
                    success=True,
                    data={"batch_ids": [], "message": "没有新PDF"}
                )
            
            # 分批上传（按大小+数量均衡）
            batch_ids = []
            planned_batches = self.processor.build_upload_batches(new_pdfs)

            for i, batch_pdfs in enumerate(planned_batches):
                batch_id = self.processor.upload_batch(batch_pdfs, i)
                if batch_id:
                    batch_ids.append(batch_id)
            
            self.log_info(f"上传完成：{len(batch_ids)} 个批次")
            
            return AgentResult(
                success=True,
                data={
                    "batch_ids": batch_ids,
                    "uploaded_count": len(new_pdfs),
                    "batch_count": len(batch_ids)
                }
            )
        
        except Exception as e:
            self.log_error(f"PDF处理失败: {e}")
            return AgentResult(
                success=False,
                error=str(e)
            )
    
    def check_batch_status(self, batch_id: str) -> Optional[Dict[str, Any]]:
        """查询批次状态"""
        return self.processor.check_batch_status(batch_id)
    
    def download_batch(self, batch_id: str, output_dir: Path = None) -> Dict[str, Any]:
        """下载批次结果"""
        return self.processor.download_batch(batch_id, output_dir)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return self.processor.get_statistics()
    
    def list_batches(self) -> List[Dict[str, Any]]:
        """列出所有批次"""
        return self.processor.list_batches()
    
    def list_pending_pdfs(self) -> List[Dict[str, Any]]:
        """列出待处理PDF"""
        return self.processor.list_pending_pdfs()
