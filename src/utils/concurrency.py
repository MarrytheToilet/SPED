#!/usr/bin/env python3
"""
并发控制模块 - 提供可配置的并发执行能力

功能：
1. ThreadPoolExecutor封装
2. 可配置的worker数量
3. 速率限制（避免API限流）
4. 错误处理和重试
5. 进度显示
"""
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from typing import Callable, List, Dict, Any, Optional, TypeVar, Generic
from dataclasses import dataclass, field
from loguru import logger

T = TypeVar('T')
R = TypeVar('R')


@dataclass
class TaskResult(Generic[R]):
    """任务执行结果"""
    task_id: str
    success: bool
    result: Optional[R] = None
    error: Optional[str] = None
    duration: float = 0.0


@dataclass
class BatchStats:
    """批量执行统计"""
    total: int = 0
    success: int = 0
    failed: int = 0
    total_duration: float = 0.0
    results: List[TaskResult] = field(default_factory=list)
    
    @property
    def success_rate(self) -> float:
        return self.success / self.total if self.total > 0 else 0.0


class RateLimiter:
    """速率限制器 - 基于令牌桶算法"""
    
    def __init__(self, rate: float = 1.0, burst: int = 1):
        """
        初始化速率限制器
        
        Args:
            rate: 每秒允许的请求数
            burst: 突发容量（桶大小）
        """
        self.rate = rate
        self.burst = burst
        self.tokens = burst
        self.last_time = time.monotonic()
        self._lock = threading.Lock()
    
    def acquire(self) -> float:
        """
        获取令牌，返回需要等待的时间
        
        Returns:
            等待时间（秒）
        """
        with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_time
            self.last_time = now
            
            # 补充令牌
            self.tokens = min(self.burst, self.tokens + elapsed * self.rate)
            
            if self.tokens >= 1:
                self.tokens -= 1
                return 0.0
            else:
                # 需要等待
                wait_time = (1 - self.tokens) / self.rate
                self.tokens = 0
                return wait_time
    
    def wait(self):
        """等待直到获取到令牌"""
        wait_time = self.acquire()
        if wait_time > 0:
            time.sleep(wait_time)


class ConcurrencyController:
    """
    并发控制器
    
    使用示例:
    ```python
    controller = ConcurrencyController(max_workers=4, rate_limit=2.0)
    
    def process_item(item):
        # 处理逻辑
        return result
    
    items = [{"id": "1", ...}, {"id": "2", ...}, ...]
    stats = controller.execute_batch(
        items,
        process_item,
        id_func=lambda x: x["id"]
    )
    ```
    """
    
    def __init__(
        self,
        max_workers: int = 4,
        rate_limit: float = None,
        min_interval: float = 0.0,
        retry_count: int = 0,
        retry_delay: float = 2.0,
        on_progress: Callable[[int, int, TaskResult], None] = None,
    ):
        """
        初始化并发控制器
        
        Args:
            max_workers: 最大并行worker数量
            rate_limit: 每秒最大请求数（None表示不限制）
            min_interval: 每个API Key的最小请求间隔（秒）
            retry_count: 失败重试次数
            retry_delay: 重试间隔（秒）
            on_progress: 进度回调函数 (completed, total, result)
        """
        self.max_workers = max_workers
        self.retry_count = retry_count
        self.retry_delay = retry_delay
        self.on_progress = on_progress
        self.min_interval = min_interval
        
        # 速率限制器
        if rate_limit:
            self.rate_limiter = RateLimiter(rate=rate_limit, burst=max_workers)
        else:
            self.rate_limiter = None
        
        # 每个worker的上次执行时间（用于min_interval）
        # 每个worker对应一个API Key，分别计时
        self._worker_last_exec: Dict[int, float] = {}
        self._exec_lock = threading.Lock()
        
        logger.info(
            f"ConcurrencyController初始化: workers={max_workers}, "
            f"rate_limit={rate_limit}, min_interval={min_interval}s (per-worker)"
        )
    
    def _wait_for_interval(self, worker_id: int = 0):
        """
        等待最小间隔（按worker分别计时）
        
        Args:
            worker_id: worker编号，相同编号共享间隔计时
        """
        if self.min_interval <= 0:
            return
        
        with self._exec_lock:
            now = time.monotonic()
            last_exec = self._worker_last_exec.get(worker_id, 0.0)
            elapsed = now - last_exec
            
            if elapsed < self.min_interval:
                wait_time = self.min_interval - elapsed
                # 在锁外等待，避免阻塞其他worker
                self._exec_lock.release()
                try:
                    time.sleep(wait_time)
                finally:
                    self._exec_lock.acquire()
            
            self._worker_last_exec[worker_id] = time.monotonic()
    
    def _execute_with_retry(
        self,
        task_id: str,
        func: Callable[[T], R],
        item: T,
        worker_id: int = 0,
    ) -> TaskResult[R]:
        """
        执行单个任务（带重试）
        
        Args:
            task_id: 任务ID
            func: 处理函数
            item: 任务数据
            worker_id: worker编号（用于按API Key分别限速）
        
        Returns:
            TaskResult
        """
        start_time = time.time()
        last_error = None
        
        for attempt in range(self.retry_count + 1):
            try:
                # 速率限制
                if self.rate_limiter:
                    self.rate_limiter.wait()
                
                # 最小间隔（按worker分别计时）
                self._wait_for_interval(worker_id)
                
                # 执行任务
                result = func(item)
                
                duration = time.time() - start_time
                return TaskResult(
                    task_id=task_id,
                    success=True,
                    result=result,
                    duration=duration
                )
                
            except Exception as e:
                last_error = str(e)
                logger.warning(
                    f"任务 {task_id} 执行失败 (尝试 {attempt + 1}/{self.retry_count + 1}): {e}"
                )
                
                # 重试延迟（指数退避）
                if attempt < self.retry_count:
                    delay = self.retry_delay * (2 ** attempt)
                    time.sleep(delay)
        
        # 所有重试都失败
        duration = time.time() - start_time
        return TaskResult(
            task_id=task_id,
            success=False,
            error=last_error,
            duration=duration
        )
    
    def execute_batch(
        self,
        items: List[T],
        func: Callable[[T], R],
        id_func: Callable[[T], str] = None,
    ) -> BatchStats:
        """
        批量执行任务
        
        Args:
            items: 任务列表
            func: 处理函数
            id_func: 获取任务ID的函数，默认使用索引
        
        Returns:
            BatchStats
        """
        if not items:
            return BatchStats()
        
        stats = BatchStats(total=len(items))
        completed = 0
        
        logger.info(f"开始批量执行: {len(items)} 个任务, {self.max_workers} workers")
        
        start_time = time.time()
        
        # 用于分配worker_id的计数器
        worker_counter = {"value": 0}
        counter_lock = threading.Lock()
        
        def get_worker_id():
            """获取下一个worker_id（循环分配）"""
            with counter_lock:
                wid = worker_counter["value"]
                worker_counter["value"] = (wid + 1) % self.max_workers
                return wid
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            futures: Dict[Future, str] = {}
            
            for i, item in enumerate(items):
                task_id = id_func(item) if id_func else str(i)
                worker_id = get_worker_id()
                future = executor.submit(
                    self._execute_with_retry,
                    task_id,
                    func,
                    item,
                    worker_id
                )
                futures[future] = task_id
            
            # 处理完成的任务
            for future in as_completed(futures):
                task_id = futures[future]
                
                try:
                    result = future.result()
                except Exception as e:
                    result = TaskResult(
                        task_id=task_id,
                        success=False,
                        error=str(e)
                    )
                
                completed += 1
                stats.results.append(result)
                
                if result.success:
                    stats.success += 1
                else:
                    stats.failed += 1
                
                # 进度回调
                if self.on_progress:
                    self.on_progress(completed, stats.total, result)
        
        stats.total_duration = time.time() - start_time
        
        logger.info(
            f"批量执行完成: 成功 {stats.success}/{stats.total}, "
            f"耗时 {stats.total_duration:.1f}s"
        )
        
        return stats
    
    def execute_sequential(
        self,
        items: List[T],
        func: Callable[[T], R],
        id_func: Callable[[T], str] = None,
    ) -> BatchStats:
        """
        顺序执行任务（非并行）
        
        Args:
            items: 任务列表
            func: 处理函数
            id_func: 获取任务ID的函数
        
        Returns:
            BatchStats
        """
        if not items:
            return BatchStats()
        
        stats = BatchStats(total=len(items))
        
        logger.info(f"开始顺序执行: {len(items)} 个任务")
        
        start_time = time.time()
        
        for i, item in enumerate(items):
            task_id = id_func(item) if id_func else str(i)
            result = self._execute_with_retry(task_id, func, item)
            
            stats.results.append(result)
            
            if result.success:
                stats.success += 1
            else:
                stats.failed += 1
            
            # 进度回调
            if self.on_progress:
                self.on_progress(i + 1, stats.total, result)
        
        stats.total_duration = time.time() - start_time
        
        logger.info(
            f"顺序执行完成: 成功 {stats.success}/{stats.total}, "
            f"耗时 {stats.total_duration:.1f}s"
        )
        
        return stats
