"""
分析结果缓存 - 避免短时间内对同一股票重复调用 LLM
基于 stock_code + agent_id 的 TTL 缓存，交易时段5分钟，非交易时段30分钟
"""

import hashlib
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.utils.logging_config import get_logger

logger = get_logger("analysis_cache")


def _is_trading_time() -> bool:
    """判断当前是否为A股交易时段"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    hour_min = now.hour * 100 + now.minute
    return 915 <= hour_min <= 1530


@dataclass
class CachedResult:
    """缓存的分析结果"""
    agent_id: str
    stock_code: str
    result: str
    fallback_level: int = 0
    created_at: float = field(default_factory=time.time)
    data_hash: str = ""
    hit_count: int = 0

    @property
    def age_seconds(self) -> float:
        return time.time() - self.created_at


class AnalysisCache:
    """
    分析结果缓存

    缓存策略:
    - key: {agent_id}:{stock_code}
    - 交易时段 TTL: 5 分钟（数据变化快）
    - 非交易时段 TTL: 30 分钟（数据不变）
    - fallback_level >= 99 的结果不缓存（兜底文本）
    """

    _instance = None
    _lock = threading.Lock()

    TRADING_TTL = 300       # 5 分钟
    OFF_HOURS_TTL = 1800    # 30 分钟

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._cache: Dict[str, CachedResult] = {}
        self._cache_lock = threading.Lock()
        self._stats = {
            "hits": 0,
            "misses": 0,
            "stores": 0,
            "evictions": 0,
        }
        logger.info("✅ AnalysisCache 初始化完成")

    @staticmethod
    def _make_key(agent_id: str, stock_code: str) -> str:
        return f"{agent_id}:{stock_code}"

    @staticmethod
    def _hash_data(stock_data: Dict) -> str:
        """对股票数据生成摘要 hash，用于判断数据是否变化"""
        # 只取关键字段
        key_fields = ["nowPri", "price", "increase", "change", "traAmount", "volume"]
        parts = []
        for k in key_fields:
            if k in stock_data:
                parts.append(f"{k}={stock_data[k]}")
        return hashlib.md5("|".join(parts).encode()).hexdigest()[:12]

    def get(
        self, agent_id: str, stock_code: str, stock_data: Optional[Dict] = None
    ) -> Optional[str]:
        """
        获取缓存的分析结果

        Returns:
            缓存的结果文本，未命中返回 None
        """
        key = self._make_key(agent_id, stock_code)
        ttl = self.TRADING_TTL if _is_trading_time() else self.OFF_HOURS_TTL

        with self._cache_lock:
            cached = self._cache.get(key)
            if cached is None:
                self._stats["misses"] += 1
                return None

            # TTL 检查
            if cached.age_seconds > ttl:
                del self._cache[key]
                self._stats["misses"] += 1
                self._stats["evictions"] += 1
                return None

            # 数据变化检查（如果提供了新数据）
            if stock_data and cached.data_hash:
                new_hash = self._hash_data(stock_data)
                if new_hash != cached.data_hash:
                    del self._cache[key]
                    self._stats["misses"] += 1
                    logger.debug(f"📊 缓存失效(数据变化): {key}")
                    return None

            cached.hit_count += 1
            self._stats["hits"] += 1
            logger.info(f"💾 缓存命中: {key} (age={cached.age_seconds:.0f}s, hits={cached.hit_count})")
            return cached.result

    def put(
        self,
        agent_id: str,
        stock_code: str,
        result: str,
        fallback_level: int = 0,
        stock_data: Optional[Dict] = None,
    ) -> None:
        """
        存入分析结果

        fallback_level >= 99 的兜底文本不缓存
        """
        if fallback_level >= 99:
            return

        if not result or len(result.strip()) < 50:
            return

        key = self._make_key(agent_id, stock_code)
        data_hash = self._hash_data(stock_data) if stock_data else ""

        with self._cache_lock:
            self._cache[key] = CachedResult(
                agent_id=agent_id,
                stock_code=stock_code,
                result=result,
                fallback_level=fallback_level,
                data_hash=data_hash,
            )
            self._stats["stores"] += 1

        logger.info(f"💾 缓存存入: {key} (len={len(result)}, hash={data_hash})")

    def invalidate(self, stock_code: str, agent_id: Optional[str] = None) -> int:
        """
        使缓存失效

        Args:
            stock_code: 股票代码
            agent_id: 可选，指定智能体。为 None 时清除该股票所有缓存

        Returns:
            清除的缓存条目数
        """
        removed = 0
        with self._cache_lock:
            keys_to_remove = []
            for key, cached in self._cache.items():
                if cached.stock_code == stock_code:
                    if agent_id is None or cached.agent_id == agent_id:
                        keys_to_remove.append(key)
            for key in keys_to_remove:
                del self._cache[key]
                removed += 1

        if removed > 0:
            logger.info(f"🗑️ 缓存失效: stock={stock_code}, agent={agent_id or 'ALL'}, removed={removed}")
        return removed

    def cleanup(self) -> int:
        """清理过期缓存"""
        max_ttl = max(self.TRADING_TTL, self.OFF_HOURS_TTL)
        removed = 0
        with self._cache_lock:
            keys_to_remove = [
                key for key, cached in self._cache.items()
                if cached.age_seconds > max_ttl * 2
            ]
            for key in keys_to_remove:
                del self._cache[key]
                removed += 1
        return removed

    def get_stats(self) -> Dict:
        """获取缓存统计"""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = (self._stats["hits"] / total * 100) if total > 0 else 0
        return {
            **self._stats,
            "size": len(self._cache),
            "hit_rate": f"{hit_rate:.1f}%",
            "ttl_trading": self.TRADING_TTL,
            "ttl_off_hours": self.OFF_HOURS_TTL,
        }


# 全局单例
def get_analysis_cache() -> AnalysisCache:
    return AnalysisCache()
