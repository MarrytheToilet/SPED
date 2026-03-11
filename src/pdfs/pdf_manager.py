#!/usr/bin/env python3
"""
PDF管理器 - 统一管理PDF处理状态
使用SQLite数据库替代CSV文件，提供更可靠的状态追踪
"""
import sqlite3
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple


class PDFManager:
    """PDF处理状态管理器"""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pdf_files (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                file_hash TEXT NOT NULL,
                file_size INTEGER,
                batch_id TEXT,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS batches (
                batch_id TEXT PRIMARY KEY,
                batch_index INTEGER,
                file_count INTEGER,
                status TEXT DEFAULT 'uploaded',
                access_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        conn.execute("""
            CREATE TABLE IF NOT EXISTS batch_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                batch_id TEXT NOT NULL,
                data_id TEXT NOT NULL,
                filename TEXT,
                mineru_status TEXT,
                download_status TEXT DEFAULT 'pending',
                output_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (batch_id) REFERENCES batches(batch_id)
            )
        """)
        
        # 创建索引
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pdf_status ON pdf_files(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_pdf_hash ON pdf_files(file_hash)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_batch_status ON batches(status)")
        
        conn.commit()
        conn.close()
    
    def _get_file_hash(self, filepath: Path) -> str:
        """计算文件MD5哈希"""
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()
    
    def add_pdf(self, filepath: Path, batch_id: Optional[str] = None) -> Tuple[bool, str]:
        """
        添加PDF文件记录
        
        Returns:
            (is_new, message): 是否是新文件，消息
        """
        file_hash = self._get_file_hash(filepath)
        file_size = filepath.stat().st_size
        
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # 检查是否已存在（基于哈希）
        cur.execute("SELECT filename, status FROM pdf_files WHERE file_hash = ?", (file_hash,))
        existing = cur.fetchone()
        
        if existing:
            conn.close()
            return False, f"文件已存在: {existing[0]} (状态: {existing[1]})"
        
        # 添加新记录
        try:
            cur.execute("""
                INSERT INTO pdf_files (filename, file_hash, file_size, batch_id, status)
                VALUES (?, ?, ?, ?, ?)
            """, (filepath.name, file_hash, file_size, batch_id, 'pending' if not batch_id else 'uploaded'))
            conn.commit()
            conn.close()
            return True, "新文件已添加"
        except sqlite3.IntegrityError:
            conn.close()
            return False, f"文件名重复: {filepath.name}"
    
    def update_pdf_status(self, filename: str, status: str, batch_id: Optional[str] = None):
        """更新PDF状态"""
        conn = sqlite3.connect(self.db_path)
        if batch_id:
            conn.execute("""
                UPDATE pdf_files 
                SET status = ?, batch_id = ?, updated_at = CURRENT_TIMESTAMP
                WHERE filename = ?
            """, (status, batch_id, filename))
        else:
            conn.execute("""
                UPDATE pdf_files 
                SET status = ?, updated_at = CURRENT_TIMESTAMP
                WHERE filename = ?
            """, (status, filename))
        conn.commit()
        conn.close()
    
    def get_pending_pdfs(self) -> List[Dict]:
        """获取待处理的PDF列表"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM pdf_files 
            WHERE status = 'pending'
            ORDER BY created_at
        """)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return rows
    
    def add_batch(self, batch_id: str, batch_index: int, file_count: int, access_url: str):
        """添加批次记录"""
        conn = sqlite3.connect(self.db_path)
        try:
            conn.execute("""
                INSERT INTO batches (batch_id, batch_index, file_count, access_url)
                VALUES (?, ?, ?, ?)
            """, (batch_id, batch_index, file_count, access_url))
            conn.commit()
        except sqlite3.IntegrityError:
            # 批次已存在，更新
            conn.execute("""
                UPDATE batches 
                SET file_count = ?, access_url = ?, updated_at = CURRENT_TIMESTAMP
                WHERE batch_id = ?
            """, (file_count, access_url, batch_id))
            conn.commit()
        conn.close()
    
    def update_batch_status(self, batch_id: str, status: str):
        """更新批次状态"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE batches 
            SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE batch_id = ?
        """, (status, batch_id))
        conn.commit()
        conn.close()
    
    def get_all_batches(self) -> List[Dict]:
        """获取所有批次"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM batches 
            ORDER BY batch_index DESC
        """)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return rows
    
    def get_batch_by_id(self, batch_id: str) -> Optional[Dict]:
        """根据ID获取批次"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM batches WHERE batch_id = ?", (batch_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    
    def get_max_batch_index(self) -> int:
        """获取最大批次索引"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("SELECT MAX(batch_index) FROM batches")
        result = cur.fetchone()[0]
        conn.close()
        return result if result else 0
    
    def add_batch_result(self, batch_id: str, data_id: str, filename: str, 
                         mineru_status: str, output_path: Optional[str] = None):
        """添加批次结果记录"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO batch_results 
            (batch_id, data_id, filename, mineru_status, output_path)
            VALUES (?, ?, ?, ?, ?)
        """, (batch_id, data_id, filename, mineru_status, output_path))
        conn.commit()
        conn.close()
    
    def update_result_download_status(self, data_id: str, status: str, output_path: str):
        """更新下载状态"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE batch_results 
            SET download_status = ?, output_path = ?, updated_at = CURRENT_TIMESTAMP
            WHERE data_id = ?
        """, (status, output_path, data_id))
        conn.commit()
        conn.close()
    
    def get_batch_results(self, batch_id: str) -> List[Dict]:
        """获取批次的所有结果"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM batch_results 
            WHERE batch_id = ?
            ORDER BY filename
        """, (batch_id,))
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return rows
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # PDF统计
        cur.execute("SELECT COUNT(*) FROM pdf_files")
        total_pdfs = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM pdf_files WHERE status = 'pending'")
        pending_pdfs = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM pdf_files WHERE status = 'uploaded'")
        uploaded_pdfs = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM pdf_files WHERE status = 'downloaded'")
        downloaded_pdfs = cur.fetchone()[0]
        
        # 批次统计
        cur.execute("SELECT COUNT(*) FROM batches")
        total_batches = cur.fetchone()[0]
        
        cur.execute("SELECT COUNT(*) FROM batches WHERE status = 'completed'")
        completed_batches = cur.fetchone()[0]
        
        # 结果统计
        cur.execute("SELECT COUNT(*) FROM batch_results WHERE download_status = 'downloaded'")
        downloaded_results = cur.fetchone()[0]
        
        conn.close()
        
        return {
            "total_pdfs": total_pdfs,
            "pending_pdfs": pending_pdfs,
            "uploaded_pdfs": uploaded_pdfs,
            "downloaded_pdfs": downloaded_pdfs,
            "total_batches": total_batches,
            "completed_batches": completed_batches,
            "downloaded_results": downloaded_results,
        }
    
    def reset_pdf(self, filename: str):
        """重置PDF状态为pending"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE pdf_files 
            SET status = 'pending', batch_id = NULL, updated_at = CURRENT_TIMESTAMP
            WHERE filename = ?
        """, (filename,))
        conn.commit()
        conn.close()
    
    def delete_pdf(self, filename: str):
        """删除PDF记录"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("DELETE FROM pdf_files WHERE filename = ?", (filename,))
        conn.commit()
        conn.close()
    
    def get_pdfs_by_batch(self, batch_id: str) -> List[Dict]:
        """获取批次中的所有PDF"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM pdf_files 
            WHERE batch_id = ?
            ORDER BY filename
        """, (batch_id,))
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return rows
