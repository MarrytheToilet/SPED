#!/usr/bin/env python3
"""
API Key轮询器 - 支持多个API Key分散并发压力

功能：
1. 同一模型配置多个API Key，轮询使用
2. 自动故障检测和跳过不可用的Key
3. 健康检查和自动恢复
4. 线程安全的并发访问

配置方式（.env文件）：
1. 逗号分隔的多Key: SILICONFLOW_API_KEYS=key1,key2,key3
2. 编号方式: SILICONFLOW_API_KEY_2=xxx, SILICONFLOW_API_KEY_3=xxx
3. 备用Key: SILICONFLOW_BACKUP_KEYS=key1,key2
"""
import threading
import time
import os
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from loguru import logger

# 确保环境变量已加载
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


@dataclass
class APIKey:
    """API Key配置"""
    key: str
    name: str = ""  # 可选的标识名（如 "账号1", "账号2"）
    
    # 运行时状态
    is_healthy: bool = True
    fail_count: int = 0
    last_fail_time: float = 0.0
    request_count: int = 0
    
    # 配置
    max_fails: int = 3  # 连续失败N次后标记为不健康
    recovery_time: float = 120.0  # 不健康后等待恢复的时间（秒）
    
    def __post_init__(self):
        if not self.name:
            # 使用key的前8位作为标识
            self.name = f"key_{self.key[:8]}..."


class APIKeyRotator:
    """
    API Key轮询器
    
    支持：
    - 轮询分配请求到多个API Key
    - 自动故障检测和跳过
    - 健康恢复检测
    """
    
    def __init__(self, keys: List[str] = None):
        """
        初始化轮询器
        
        Args:
            keys: API Key列表
        """
        self._keys: List[APIKey] = []
        self._current_index = 0
        self._lock = threading.Lock()
        
        if keys:
            for i, key in enumerate(keys):
                self._keys.append(APIKey(key=key, name=f"key{i+1}"))
    
    def add_key(self, key: str, name: str = None):
        """添加API Key"""
        with self._lock:
            api_key = APIKey(key=key, name=name or f"key{len(self._keys)+1}")
            self._keys.append(api_key)
            logger.debug(f"添加API Key: {api_key.name}")
    
    def get_key(self) -> Optional[str]:
        """
        获取下一个可用的API Key（轮询）
        
        Returns:
            API Key字符串，如果没有可用Key则返回None
        """
        with self._lock:
            if not self._keys:
                return None
            
            # 检查是否有Key可以恢复
            self._check_recovery()
            
            # 获取健康的Key列表
            healthy_keys = [k for k in self._keys if k.is_healthy]
            
            if healthy_keys:
                # 轮询健康的Key
                self._current_index = self._current_index % len(healthy_keys)
                api_key = healthy_keys[self._current_index]
                self._current_index = (self._current_index + 1) % len(healthy_keys)
            elif self._keys:
                # 没有健康Key时，使用第一个（主Key）
                api_key = self._keys[0]
                logger.warning(f"没有健康的API Key，回退到主Key: {api_key.name}")
            else:
                return None
            
            api_key.request_count += 1
            return api_key.key
    
    def get_key_with_info(self) -> Optional[APIKey]:
        """获取下一个可用的APIKey对象（包含完整信息）"""
        with self._lock:
            if not self._keys:
                return None
            
            self._check_recovery()
            healthy_keys = [k for k in self._keys if k.is_healthy]
            
            if healthy_keys:
                self._current_index = self._current_index % len(healthy_keys)
                api_key = healthy_keys[self._current_index]
                self._current_index = (self._current_index + 1) % len(healthy_keys)
            elif self._keys:
                api_key = self._keys[0]
            else:
                return None
            
            api_key.request_count += 1
            return api_key
    
    def report_success(self, key: str):
        """报告请求成功"""
        with self._lock:
            for api_key in self._keys:
                if api_key.key == key:
                    api_key.fail_count = 0
                    if not api_key.is_healthy:
                        api_key.is_healthy = True
                        logger.info(f"API Key恢复健康: {api_key.name}")
                    break
    
    def report_failure(self, key: str, error: str = ""):
        """报告请求失败"""
        with self._lock:
            for api_key in self._keys:
                if api_key.key == key:
                    api_key.fail_count += 1
                    api_key.last_fail_time = time.time()
                    
                    if api_key.fail_count >= api_key.max_fails and api_key.is_healthy:
                        api_key.is_healthy = False
                        healthy_count = sum(1 for k in self._keys if k.is_healthy)
                        logger.warning(
                            f"API Key标记为不健康: {api_key.name} "
                            f"(连续失败{api_key.fail_count}次, 剩余健康Key: {healthy_count})"
                        )
                    break
    
    def _check_recovery(self):
        """检查不健康的Key是否可以恢复"""
        now = time.time()
        for api_key in self._keys:
            if not api_key.is_healthy:
                elapsed = now - api_key.last_fail_time
                if elapsed >= api_key.recovery_time:
                    api_key.is_healthy = True
                    api_key.fail_count = 0
                    logger.info(f"API Key自动恢复: {api_key.name}")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        with self._lock:
            return {
                "total_keys": len(self._keys),
                "healthy_keys": sum(1 for k in self._keys if k.is_healthy),
                "keys": [
                    {
                        "name": k.name,
                        "is_healthy": k.is_healthy,
                        "fail_count": k.fail_count,
                        "request_count": k.request_count,
                    }
                    for k in self._keys
                ]
            }
    
    @property
    def key_count(self) -> int:
        """返回Key总数"""
        return len(self._keys)
    
    @property
    def healthy_count(self) -> int:
        """返回健康Key数"""
        return sum(1 for k in self._keys if k.is_healthy)
    
    def get_key_for_worker(self, worker_id: int) -> Optional[str]:
        """
        为指定worker获取固定的API Key
        
        按worker_id分配Key，如果分配的Key不健康则自动切换到其他健康Key
        
        Args:
            worker_id: worker编号
            
        Returns:
            API Key字符串
        """
        with self._lock:
            if not self._keys:
                return None
            
            self._check_recovery()
            healthy_keys = [k for k in self._keys if k.is_healthy]
            
            if not healthy_keys:
                # 没有健康Key，回退到主Key
                api_key = self._keys[0]
                logger.warning(f"Worker-{worker_id}: 没有健康Key，回退到主Key {api_key.name}")
            else:
                # 按worker_id分配到健康Key
                key_index = worker_id % len(healthy_keys)
                api_key = healthy_keys[key_index]
            
            api_key.request_count += 1
            return api_key.key
    
    def get_worker_key_info(self, worker_id: int) -> Dict[str, Any]:
        """获取worker分配的Key信息"""
        with self._lock:
            if not self._keys:
                return {"worker_id": worker_id, "key_name": None, "healthy": False}
            
            healthy_keys = [k for k in self._keys if k.is_healthy]
            if healthy_keys:
                key_index = worker_id % len(healthy_keys)
                api_key = healthy_keys[key_index]
            else:
                api_key = self._keys[0]
            
            return {
                "worker_id": worker_id,
                "key_name": api_key.name,
                "key_short": api_key.key[:12] + "...",
                "healthy": api_key.is_healthy,
            }


# 全局轮询器实例（按provider分）
_rotators: Dict[str, APIKeyRotator] = {}
_rotator_lock = threading.Lock()


def get_key_rotator(provider: str = None) -> APIKeyRotator:
    """
    获取指定provider的Key轮询器
    
    Args:
        provider: 供应商名称，默认使用当前配置的provider
    """
    global _rotators
    
    if provider is None:
        try:
            import settings
            provider = settings.LLM_PROVIDER
        except ImportError:
            provider = "default"
    
    with _rotator_lock:
        if provider not in _rotators:
            _rotators[provider] = APIKeyRotator()
            _init_rotator_from_env(_rotators[provider], provider)
        return _rotators[provider]


def _init_rotator_from_env(rotator: APIKeyRotator, provider: str):
    """
    从环境变量初始化轮询器
    
    支持的配置方式：
    1. 主Key: SILICONFLOW_API_KEY
    2. 逗号分隔的多Keys: SILICONFLOW_API_KEYS=key1,key2,key3
    3. 备用Keys: SILICONFLOW_BACKUP_KEYS=key1,key2
    4. 编号Keys: SILICONFLOW_API_KEY_2, SILICONFLOW_API_KEY_3, ...
    """
    # 获取主Key环境变量名
    key_env_map = {
        "siliconflow": "SILICONFLOW_API_KEY",
        "zhipu": "ZHIPU_API_KEY",
        "deepseek": "DEEPSEEK_API_KEY",
        "openai": "OPENAI_API_KEY",
    }
    
    main_key_env = key_env_map.get(provider, f"{provider.upper()}_API_KEY")
    
    # 方式1: 检查是否有逗号分隔的多Keys配置 (SILICONFLOW_API_KEYS)
    multi_keys_env = f"{provider.upper()}_API_KEYS"
    multi_keys_str = os.getenv(multi_keys_env, "")
    
    if multi_keys_str:
        # 使用逗号分隔的多Key配置
        keys = [k.strip() for k in multi_keys_str.split(",") if k.strip()]
        for i, key in enumerate(keys):
            rotator.add_key(key, f"key{i+1}")
        logger.info(f"[{provider}] 从 {multi_keys_env} 加载了 {len(keys)} 个API Key")
    else:
        # 方式2: 使用单一主Key
        main_key = os.getenv(main_key_env, "")
        if main_key:
            rotator.add_key(main_key, "primary")
    
    # 方式3: 备用Keys（格式：SILICONFLOW_BACKUP_KEYS=key1,key2,key3）
    backup_keys_str = os.getenv(f"{provider.upper()}_BACKUP_KEYS", "")
    if backup_keys_str:
        backup_keys = [k.strip() for k in backup_keys_str.split(",") if k.strip()]
        for i, key in enumerate(backup_keys):
            # 检查是否重复
            if not any(k.key == key for k in rotator._keys):
                rotator.add_key(key, f"backup{i+1}")
    
    # 方式4: 编号Keys（SILICONFLOW_API_KEY_2, _3, ..., _9）
    for i in range(2, 10):
        key = os.getenv(f"{main_key_env}_{i}", "")
        if key and not any(k.key == key for k in rotator._keys):
            rotator.add_key(key, f"key{i}")
    
    if rotator.key_count > 0:
        logger.info(f"[{provider}] API Key轮询器初始化完成: {rotator.key_count}个Key可用")


def reset_rotators():
    """重置所有轮询器"""
    global _rotators
    with _rotator_lock:
        _rotators = {}

