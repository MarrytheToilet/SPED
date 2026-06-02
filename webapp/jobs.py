"""
轻量后台任务管理器（线程内执行，进程内注册表）。

用于驱动「解析 / 设计schema / 提取」等耗时操作，前端通过 /api/jobs 轮询进度。
每个任务在独立守护线程中运行，回调函数接收一个 JobHandle 用于上报进度与日志。
"""
from __future__ import annotations

import threading
import traceback
import uuid
from collections import deque
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional


class JobHandle:
    """传给任务函数，用于上报进度/日志/检查取消。"""

    def __init__(self, job: "Job"):
        self._job = job

    def log(self, message: str) -> None:
        line = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        with self._job._lock:
            self._job.logs.append(line)
            self._job.updated_at = datetime.now().isoformat(timespec="seconds")

    def set_progress(self, done: int, total: int) -> None:
        with self._job._lock:
            self._job.done = done
            self._job.total = total
            self._job.updated_at = datetime.now().isoformat(timespec="seconds")

    def set_meta(self, **kwargs) -> None:
        with self._job._lock:
            self._job.meta.update(kwargs)

    @property
    def cancelled(self) -> bool:
        return self._job.cancel_requested


class Job:
    def __init__(self, job_type: str, title: str):
        self.id = uuid.uuid4().hex[:12]
        self.type = job_type
        self.title = title
        self.status = "queued"  # queued/running/success/failed/cancelled
        self.done = 0
        self.total = 0
        self.logs: deque = deque(maxlen=500)
        self.result: Dict[str, Any] = {}
        self.meta: Dict[str, Any] = {}
        self.error: Optional[str] = None
        self.cancel_requested = False
        self.created_at = datetime.now().isoformat(timespec="seconds")
        self.updated_at = self.created_at
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None

    def to_dict(self, with_logs: bool = False) -> Dict[str, Any]:
        with self._lock:
            d = {
                "id": self.id,
                "type": self.type,
                "title": self.title,
                "status": self.status,
                "done": self.done,
                "total": self.total,
                "result": self.result,
                "meta": self.meta,
                "error": self.error,
                "created_at": self.created_at,
                "updated_at": self.updated_at,
            }
            if with_logs:
                d["logs"] = list(self.logs)
            else:
                d["last_log"] = self.logs[-1] if self.logs else ""
            return d


class JobManager:
    def __init__(self):
        self._jobs: Dict[str, Job] = {}
        self._lock = threading.Lock()

    def submit(self, job_type: str, title: str,
               fn: Callable[[JobHandle], Any]) -> Job:
        job = Job(job_type, title)
        with self._lock:
            self._jobs[job.id] = job
        handle = JobHandle(job)

        def runner():
            with job._lock:
                job.status = "running"
                job.updated_at = datetime.now().isoformat(timespec="seconds")
            handle.log(f"任务开始: {title}")
            try:
                result = fn(handle)
                with job._lock:
                    if job.cancel_requested:
                        job.status = "cancelled"
                    else:
                        job.status = "success"
                        if isinstance(result, dict):
                            job.result = result
                    job.updated_at = datetime.now().isoformat(timespec="seconds")
                handle.log(f"任务结束: {job.status}")
            except Exception as e:  # noqa: BLE001
                with job._lock:
                    job.status = "failed"
                    job.error = str(e)
                    job.updated_at = datetime.now().isoformat(timespec="seconds")
                handle.log(f"任务异常: {e}")
                handle.log(traceback.format_exc().splitlines()[-1])

        t = threading.Thread(target=runner, daemon=True)
        job._thread = t
        t.start()
        return job

    def get(self, job_id: str) -> Optional[Job]:
        return self._jobs.get(job_id)

    def cancel(self, job_id: str) -> bool:
        job = self._jobs.get(job_id)
        if job and job.status in ("queued", "running"):
            job.cancel_requested = True
            return True
        return False

    def list(self) -> List[Dict[str, Any]]:
        with self._lock:
            jobs = list(self._jobs.values())
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return [j.to_dict() for j in jobs]

    def active(self) -> List[Job]:
        """正在排队/运行的任务（最新优先）。"""
        with self._lock:
            jobs = [j for j in self._jobs.values() if j.status in ("queued", "running")]
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs

    def has_active(self) -> bool:
        return bool(self.active())


# 全局单例
JOBS = JobManager()
