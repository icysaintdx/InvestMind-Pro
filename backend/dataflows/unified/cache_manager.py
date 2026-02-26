"""
多级缓存管理器
实现 L1内存 / L2本地 / L3远程 三级缓存架构
"""

import time
import sqlite3
import threading
import pickle
import hashlib
from enum import Enum
from typing import Any, Optional, Dict
from dataclasses import dataclass
from pathlib import Path

from backend.utils.logging_config import get_logger

logger = get_logger("dataflows.unified.cache")


class CacheLevel(Enum):
    """缓存级别"""
    L1_MEMORY = "l1_memory"      # 进程内存，<1ms
    L2_LOCAL = "l2_local"        # 本地SQLite，<10ms
    L3_REMOTE = "l3_remote"      # 远程Redis，<50ms


@dataclass
class CacheEntry:
    """缓存条目"""
    value: Any
    expire_time: float
    data_type: str


class CacheConfig:
    """缓存配置"""
    
    # 默认TTL配置（秒）
    DEFAULT_TTL = {
        "tick": {              # 实时行情
            CacheLevel.L1_MEMORY: 1,     # 1秒
            CacheLevel.L2_LOCAL: 5,      # 5秒
        },
        "klines": {            # K线数据
            CacheLevel.L1_MEMORY: 60,    # 1分钟
            CacheLevel.L2_LOCAL: 300,    # 5分钟
        },
        "financial": {         # 财务数据
            CacheLevel.L1_MEMORY: 3600,  # 1小时
            CacheLevel.L2_LOCAL: 86400,  # 1天
        },
        "news": {              # 新闻数据
            CacheLevel.L1_MEMORY: 30,    # 30秒
            CacheLevel.L2_LOCAL: 300,    # 5分钟
        },
        "sector": {            # 板块数据
            CacheLevel.L1_MEMORY: 5,     # 5秒
            CacheLevel.L2_LOCAL: 60,     # 1分钟
        },
        "fund_flow": {         # 资金流向
            CacheLevel.L1_MEMORY: 10,    # 10秒
            CacheLevel.L2_LOCAL: 60,     # 1分钟
        },
    }
    
    # 最大缓存大小
    MAX_SIZE = {
        CacheLevel.L1_MEMORY: 10000,
        CacheLevel.L2_LOCAL: 100000,
    }


class UnifiedCacheManager:
    """
    统一缓存管理器
    
    实现多级缓存：
    - L1: 进程内存字典（最快）
    - L2: 本地SQLite（持久化）
    - L3: 远程Redis（分布式，可选）
    
    自动回填：L3 → L2 → L1
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, db_path: str = "data/cache/unified_cache.db"):
        if self._initialized:
            return
        
        self._initialized = True
        self._l1_cache: Dict[str, CacheEntry] = {}  # 内存缓存
        self._l1_lock = threading.RLock()
        
        # L2: SQLite
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_l2()
        
        # L3: Redis（可选）
        self._l3_enabled = False
        self._redis_client = None
        
        logger.info(f"[CacheManager] 初始化完成，L2路径: {self._db_path}")
    
    def _init_l2(self):
        """初始化L2缓存（SQLite）"""
        try:
            conn = sqlite3.connect(str(self._db_path), check_same_thread=False)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB,
                    expire_time REAL,
                    data_type TEXT,
                    created_at REAL DEFAULT (unixepoch())
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_expire ON cache(expire_time)
            """)
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"[CacheManager] L2初始化失败: {e}")
    
    def _make_key(self, data_type: str, identifier: str) -> str:
        """生成缓存key"""
        raw = f"{data_type}:{identifier}"
        return hashlib.md5(raw.encode()).hexdigest()
    
    def _get_ttl(self, data_type: str, level: CacheLevel) -> int:
        """获取TTL"""
        config = CacheConfig.DEFAULT_TTL.get(data_type, {})
        return config.get(level, 60)  # 默认60秒
    
    # ========== L1 内存缓存 ==========
    
    def _get_l1(self, key: str) -> Optional[Any]:
        """读取L1缓存"""
        with self._l1_lock:
            entry = self._l1_cache.get(key)
            if entry:
                if time.time() < entry.expire_time:
                    return entry.value
                else:
                    # 过期删除
                    del self._l1_cache[key]
            return None
    
    def _set_l1(self, key: str, value: Any, data_type: str):
        """写入L1缓存"""
        ttl = self._get_ttl(data_type, CacheLevel.L1_MEMORY)
        with self._l1_lock:
            # 容量控制
            if len(self._l1_cache) >= CacheConfig.MAX_SIZE[CacheLevel.L1_MEMORY]:
                # 删除最早的10%
                sorted_keys = sorted(
                    self._l1_cache.keys(),
                    key=lambda k: self._l1_cache[k].expire_time
                )
                for old_key in sorted_keys[:len(sorted_keys)//10]:
                    del self._l1_cache[old_key]
            
            self._l1_cache[key] = CacheEntry(
                value=value,
                expire_time=time.time() + ttl,
                data_type=data_type
            )
    
    # ========== L2 本地缓存 ==========
    
    def _get_l2(self, key: str) -> Optional[Any]:
        """读取L2缓存"""
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=5)
            cursor = conn.cursor()
            cursor.execute(
                "SELECT value, expire_time FROM cache WHERE key = ?",
                (key,)
            )
            row = cursor.fetchone()
            conn.close()
            
            if row:
                value_blob, expire_time = row
                if time.time() < expire_time:
                    return pickle.loads(value_blob)
                else:
                    # 异步删除过期数据
                    self._delete_l2(key)
            return None
        except Exception as e:
            logger.debug(f"[CacheManager] L2读取失败: {e}")
            return None
    
    def _set_l2(self, key: str, value: Any, data_type: str):
        """写入L2缓存"""
        try:
            ttl = self._get_ttl(data_type, CacheLevel.L2_LOCAL)
            expire_time = time.time() + ttl
            value_blob = pickle.dumps(value)
            
            conn = sqlite3.connect(str(self._db_path), timeout=5)
            cursor = conn.cursor()
            cursor.execute(
                """INSERT OR REPLACE INTO cache 
                   (key, value, expire_time, data_type) 
                   VALUES (?, ?, ?, ?)""",
                (key, value_blob, expire_time, data_type)
            )
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"[CacheManager] L2写入失败: {e}")
    
    def _delete_l2(self, key: str):
        """删除L2缓存"""
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=5)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.debug(f"[CacheManager] L2删除失败: {e}")
    
    # ========== 公共接口 ==========
    
    def get(self, data_type: str, identifier: str) -> Optional[Any]:
        """
        多级缓存读取
        
        顺序: L1 → L2 → L3（回填）
        """
        key = self._make_key(data_type, identifier)
        
        # L1
        value = self._get_l1(key)
        if value is not None:
            logger.debug(f"[CacheManager] L1命中: {data_type}:{identifier}")
            return value
        
        # L2
        value = self._get_l2(key)
        if value is not None:
            logger.debug(f"[CacheManager] L2命中: {data_type}:{identifier}")
            # 回填L1
            self._set_l1(key, value, data_type)
            return value
        
        logger.debug(f"[CacheManager] 缓存未命中: {data_type}:{identifier}")
        return None
    
    def set(self, data_type: str, identifier: str, value: Any):
        """
        多级缓存写入
        
        同时写入L1和L2
        """
        key = self._make_key(data_type, identifier)
        self._set_l1(key, value, data_type)
        self._set_l2(key, value, data_type)
        logger.debug(f"[CacheManager] 缓存写入: {data_type}:{identifier}")
    
    def delete(self, data_type: str, identifier: str):
        """删除缓存"""
        key = self._make_key(data_type, identifier)
        
        # L1
        with self._l1_lock:
            self._l1_cache.pop(key, None)
        
        # L2
        self._delete_l2(key)
        
        logger.debug(f"[CacheManager] 缓存删除: {data_type}:{identifier}")
    
    def clear_expired(self):
        """清理过期缓存"""
        # L1
        current_time = time.time()
        with self._l1_lock:
            expired_keys = [
                k for k, v in self._l1_cache.items()
                if v.expire_time < current_time
            ]
            for k in expired_keys:
                del self._l1_cache[k]
        
        # L2
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=5)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM cache WHERE expire_time < ?", (current_time,))
            deleted = cursor.rowcount
            conn.commit()
            conn.close()
            logger.info(f"[CacheManager] 清理过期缓存: L1={len(expired_keys)}, L2={deleted}")
        except Exception as e:
            logger.error(f"[CacheManager] 清理L2失败: {e}")
    
    def get_stats(self) -> Dict[str, int]:
        """获取缓存统计"""
        with self._l1_lock:
            l1_count = len(self._l1_cache)
        
        try:
            conn = sqlite3.connect(str(self._db_path), timeout=5)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM cache")
            l2_count = cursor.fetchone()[0]
            conn.close()
        except:
            l2_count = 0
        
        return {
            "l1_memory_count": l1_count,
            "l2_local_count": l2_count,
        }


# 全局实例
cache_manager = UnifiedCacheManager()
