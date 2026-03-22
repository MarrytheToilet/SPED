"""
状态管理器 - 管理工作流和任务状态
"""
import sqlite3
import json
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime
from loguru import logger


class StateManager:
    """工作流状态管理器 - 使用SQLite持久化"""
    
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or Path("data/.state/workflow_state.db")
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        
        # 工作流运行表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS workflow_runs (
                run_id TEXT PRIMARY KEY,
                workflow_name TEXT NOT NULL,
                pipeline TEXT,
                status TEXT DEFAULT 'running',
                start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                end_time TIMESTAMP,
                total_tasks INTEGER DEFAULT 0,
                completed_tasks INTEGER DEFAULT 0,
                failed_tasks INTEGER DEFAULT 0
            )
        """)
        
        # 任务状态表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_status (
                task_id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                input_data TEXT,
                output_data TEXT,
                error_message TEXT,
                metadata TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES workflow_runs(run_id)
            )
        """)
        
        conn.execute("CREATE INDEX IF NOT EXISTS idx_run_status ON workflow_runs(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_run ON task_status(run_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_task_status ON task_status(status)")
        
        conn.commit()
        conn.close()
    
    def start_run(
        self,
        run_id: str,
        workflow_name: str,
        pipeline: List[str]
    ):
        """记录工作流开始"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO workflow_runs (run_id, workflow_name, pipeline, total_tasks)
            VALUES (?, ?, ?, ?)
        """, (run_id, workflow_name, json.dumps(pipeline), len(pipeline)))
        conn.commit()
        conn.close()
    
    def complete_run(self, run_id: str, success: bool):
        """记录工作流完成"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE workflow_runs
            SET status = ?, end_time = CURRENT_TIMESTAMP
            WHERE run_id = ?
        """, ('completed' if success else 'failed', run_id))
        conn.commit()
        conn.close()
    
    def start_task(self, run_id: str, agent_id: str, input_data: Any) -> str:
        """记录任务开始"""
        import uuid
        task_id = str(uuid.uuid4())
        
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT INTO task_status (task_id, run_id, agent_id, status, input_data)
            VALUES (?, ?, ?, 'running', ?)
        """, (task_id, run_id, agent_id, json.dumps(input_data) if input_data else None))
        conn.commit()
        conn.close()
        
        return task_id
    
    def complete_task(
        self,
        task_id: str,
        success: bool,
        output_data: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        """记录任务完成"""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            UPDATE task_status
            SET status = ?,
                output_data = ?,
                error_message = ?,
                metadata = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE task_id = ?
        """, (
            'completed' if success else 'failed',
            json.dumps(output_data) if output_data else None,
            error,
            json.dumps(metadata) if metadata else None,
            task_id
        ))
        conn.commit()
        conn.close()
    
    def get_run(self, run_id: str) -> Optional[Dict]:
        """获取运行信息"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM workflow_runs WHERE run_id = ?", (run_id,))
        row = cur.fetchone()
        conn.close()
        
        return dict(row) if row else None
    
    def get_completed_tasks(self, run_id: str) -> List[Dict]:
        """获取已完成的任务"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM task_status
            WHERE run_id = ? AND status IN ('completed', 'failed')
            ORDER BY created_at
        """, (run_id,))
        rows = cur.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        # 总运行次数
        cur.execute("SELECT COUNT(*) FROM workflow_runs")
        total_runs = cur.fetchone()[0]
        
        # 成功/失败次数
        cur.execute("SELECT status, COUNT(*) FROM workflow_runs GROUP BY status")
        status_counts = dict(cur.fetchall())
        
        # 总任务数
        cur.execute("SELECT COUNT(*) FROM task_status")
        total_tasks = cur.fetchone()[0]
        
        conn.close()
        
        return {
            "total_runs": total_runs,
            "status_counts": status_counts,
            "total_tasks": total_tasks
        }
