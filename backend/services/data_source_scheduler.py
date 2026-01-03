"""
数据源智能调度器 - 轻量级被动监控版本

特点：
1. 被动记录 - 只在请求时记录指标，不主动轮询
2. 配置驱动 - 所有设置通过JSON配置文件管理
3. 自动降级 - 主数据源失败自动切换备用源
4. 灵活缓存 - 按数据类别设置不同缓存策略
"""

import json
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import threading
import asyncio

logger = logging.getLogger(__name__)


@dataclass
class RequestMetrics:
    """请求指标 - 被动记录"""
    source: str
    category: str
    interface: str
    response_time_ms: float
    success: bool
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)
    data_size: int = 0


@dataclass
class SourceHealth:
    """数据源健康状态"""
    source: str
    total_requests: int = 0
    success_count: int = 0
    error_count: int = 0
    avg_response_time: float = 0.0
    last_success: Optional[datetime] = None
    last_error: Optional[datetime] = None
    last_error_message: Optional[str] = None

    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.success_count / self.total_requests

    @property
    def health_score(self) -> float:
        """健康分数 0-100"""
        if self.total_requests == 0:
            return 100.0

        # 成功率权重60%，响应时间权重40%
        success_score = self.success_rate * 60

        # 响应时间评分：<100ms=40分，100-500ms=30分，500-1000ms=20分，>1000ms=10分
        if self.avg_response_time < 100:
            time_score = 40
        elif self.avg_response_time < 500:
            time_score = 30
        elif self.avg_response_time < 1000:
            time_score = 20
        else:
            time_score = 10

        return success_score + time_score


class DataSourceScheduler:
    """数据源智能调度器"""

    CONFIG_PATH = Path("data/data_source_config.json")
    METRICS_PATH = Path("data/api_metrics.json")

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """单例模式"""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True
        self._config: Dict = {}
        self._health: Dict[str, SourceHealth] = {}
        self._metrics_buffer: List[RequestMetrics] = []
        self._metrics_lock = threading.Lock()

        # 加载配置
        self._load_config()
        self._load_metrics()

        logger.info("DataSourceScheduler initialized")

    def _load_config(self):
        """加载配置文件"""
        try:
            if self.CONFIG_PATH.exists():
                with open(self.CONFIG_PATH, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                logger.info(f"Loaded config from {self.CONFIG_PATH}")
            else:
                logger.warning(f"Config file not found: {self.CONFIG_PATH}")
                self._config = self._get_default_config()
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            self._config = self._get_default_config()

    def _get_default_config(self) -> Dict:
        """默认配置"""
        return {
            "data_sources": {
                "tdx": {"enabled": True, "priority": 1, "timeout": 5000},
                "tushare": {"enabled": True, "priority": 2, "timeout": 10000},
                "akshare": {"enabled": True, "priority": 3, "timeout": 15000},
                "cninfo": {"enabled": True, "priority": 4, "timeout": 10000},
            },
            "data_categories": {},
            "monitoring": {"enabled": True, "mode": "passive"},
            "fallback": {"enabled": True, "max_retries": 3}
        }

    def _load_metrics(self):
        """加载历史指标"""
        try:
            if self.METRICS_PATH.exists():
                with open(self.METRICS_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for source, metrics in data.get("health", {}).items():
                        self._health[source] = SourceHealth(
                            source=source,
                            total_requests=metrics.get("total_requests", 0),
                            success_count=metrics.get("success_count", 0),
                            error_count=metrics.get("error_count", 0),
                            avg_response_time=metrics.get("avg_response_time", 0),
                        )
                logger.info(f"Loaded metrics from {self.METRICS_PATH}")
        except Exception as e:
            logger.error(f"Failed to load metrics: {e}")

    def _save_metrics(self):
        """保存指标到文件"""
        try:
            self.METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
            data = {
                "updated_at": datetime.now().isoformat(),
                "health": {
                    source: {
                        "total_requests": h.total_requests,
                        "success_count": h.success_count,
                        "error_count": h.error_count,
                        "avg_response_time": h.avg_response_time,
                        "success_rate": h.success_rate,
                        "health_score": h.health_score,
                        "last_success": h.last_success.isoformat() if h.last_success else None,
                        "last_error": h.last_error.isoformat() if h.last_error else None,
                        "last_error_message": h.last_error_message,
                    }
                    for source, h in self._health.items()
                }
            }
            with open(self.METRICS_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")

    def record_request(self, source: str, category: str, interface: str,
                       response_time_ms: float, success: bool,
                       error_message: Optional[str] = None, data_size: int = 0):
        """记录请求指标 - 被动记录，不阻塞"""
        if not self._config.get("monitoring", {}).get("enabled", True):
            return

        # 更新健康状态
        if source not in self._health:
            self._health[source] = SourceHealth(source=source)

        h = self._health[source]
        h.total_requests += 1

        if success:
            h.success_count += 1
            h.last_success = datetime.now()
            # 更新平均响应时间（滑动平均）
            if h.avg_response_time == 0:
                h.avg_response_time = response_time_ms
            else:
                h.avg_response_time = h.avg_response_time * 0.9 + response_time_ms * 0.1
        else:
            h.error_count += 1
            h.last_error = datetime.now()
            h.last_error_message = error_message

        # 异步保存（每100次请求保存一次）
        if h.total_requests % 100 == 0:
            threading.Thread(target=self._save_metrics, daemon=True).start()

    def get_best_source(self, category: str) -> Optional[str]:
        """获取指定数据类别的最优数据源"""
        cat_config = self._config.get("data_categories", {}).get(category, {})
        sources = cat_config.get("sources", [])

        if not sources:
            return None

        # 过滤已启用的数据源
        enabled_sources = [
            s for s in sources
            if self._config.get("data_sources", {}).get(s, {}).get("enabled", True)
        ]

        if not enabled_sources:
            return None

        # 按健康分数排序
        def get_score(source: str) -> float:
            if source in self._health:
                return self._health[source].health_score
            # 未知数据源给予默认分数
            priority = self._config.get("data_sources", {}).get(source, {}).get("priority", 99)
            return 100 - priority * 10

        return max(enabled_sources, key=get_score)

    def get_fallback_sources(self, category: str, exclude: str = None) -> List[str]:
        """获取备用数据源列表"""
        cat_config = self._config.get("data_categories", {}).get(category, {})
        sources = cat_config.get("sources", [])

        # 过滤已启用的数据源，排除指定源
        fallbacks = [
            s for s in sources
            if s != exclude and self._config.get("data_sources", {}).get(s, {}).get("enabled", True)
        ]

        # 按健康分数排序
        def get_score(source: str) -> float:
            if source in self._health:
                return self._health[source].health_score
            return 50

        return sorted(fallbacks, key=get_score, reverse=True)

    def get_cache_config(self, category: str) -> Dict:
        """获取数据类别的缓存配置"""
        cat_config = self._config.get("data_categories", {}).get(category, {})
        return {
            "ttl": cat_config.get("cache_ttl", 300),
            "level": cat_config.get("cache_level", "memory"),
        }

    def get_timeout(self, source: str) -> int:
        """获取数据源超时时间（毫秒）"""
        return self._config.get("data_sources", {}).get(source, {}).get("timeout", 10000)

    def get_health_status(self) -> Dict:
        """获取所有数据源健康状态"""
        result = {}
        # 遍历所有配置的数据源，确保都有状态返回
        for source, source_config in self._config.get("data_sources", {}).items():
            if source in self._health:
                h = self._health[source]
                result[source] = {
                    "name": source_config.get("name", source),
                    "enabled": source_config.get("enabled", True),
                    "health_score": h.health_score,
                    "success_rate": f"{h.success_rate * 100:.1f}%",
                    "avg_response_time": f"{h.avg_response_time:.0f}ms",
                    "total_requests": h.total_requests,
                    "last_success": h.last_success.isoformat() if h.last_success else None,
                    "last_error": h.last_error.isoformat() if h.last_error else None,
                    "last_error_message": h.last_error_message,
                }
            else:
                # 没有请求记录的数据源，返回默认状态
                result[source] = {
                    "name": source_config.get("name", source),
                    "enabled": source_config.get("enabled", True),
                    "health_score": 100.0,  # 默认满分
                    "success_rate": "100.0%",
                    "avg_response_time": "0ms",
                    "total_requests": 0,
                    "last_success": None,
                    "last_error": None,
                    "last_error_message": None,
                }
        return result

    def get_category_status(self) -> Dict:
        """获取所有数据类别状态"""
        result = {}
        for cat_name, cat_config in self._config.get("data_categories", {}).items():
            best_source = self.get_best_source(cat_name)
            result[cat_name] = {
                "name": cat_config.get("name", cat_name),
                "description": cat_config.get("description", ""),
                "sources": cat_config.get("sources", []),
                "primary": cat_config.get("primary"),
                "best_source": best_source,
                "cache_ttl": cat_config.get("cache_ttl", 300),
                "cache_level": cat_config.get("cache_level", "memory"),
            }
        return result

    def update_config(self, updates: Dict) -> bool:
        """更新配置"""
        try:
            # 深度合并配置
            def deep_merge(base: Dict, update: Dict) -> Dict:
                for key, value in update.items():
                    if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                        deep_merge(base[key], value)
                    else:
                        base[key] = value
                return base

            self._config = deep_merge(self._config, updates)
            self._config["updated_at"] = datetime.now().isoformat()

            # 保存到文件
            self.CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(self.CONFIG_PATH, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, ensure_ascii=False, indent=2)

            logger.info("Config updated successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to update config: {e}")
            return False

    def set_source_enabled(self, source: str, enabled: bool) -> bool:
        """启用/禁用数据源"""
        return self.update_config({
            "data_sources": {
                source: {"enabled": enabled}
            }
        })

    def set_category_primary(self, category: str, source: str) -> bool:
        """设置数据类别的主数据源"""
        return self.update_config({
            "data_categories": {
                category: {"primary": source}
            }
        })

    def set_cache_ttl(self, category: str, ttl: int) -> bool:
        """设置数据类别的缓存时效"""
        return self.update_config({
            "data_categories": {
                category: {"cache_ttl": ttl}
            }
        })

    def reset_metrics(self, source: str = None):
        """重置指标"""
        if source:
            if source in self._health:
                self._health[source] = SourceHealth(source=source)
        else:
            self._health.clear()
        self._save_metrics()

    def get_config(self) -> Dict:
        """获取完整配置"""
        return self._config.copy()


# 装饰器：自动记录请求指标
def track_request(source: str, category: str, interface: str):
    """装饰器：自动记录请求指标"""
    def decorator(func: Callable):
        def wrapper(*args, **kwargs):
            scheduler = DataSourceScheduler()
            start_time = time.time()
            success = True
            error_message = None
            data_size = 0

            try:
                result = func(*args, **kwargs)
                if result is not None:
                    if hasattr(result, '__len__'):
                        data_size = len(result)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                response_time = (time.time() - start_time) * 1000
                scheduler.record_request(
                    source=source,
                    category=category,
                    interface=interface,
                    response_time_ms=response_time,
                    success=success,
                    error_message=error_message,
                    data_size=data_size
                )

        return wrapper
    return decorator


# 异步版本装饰器
def track_request_async(source: str, category: str, interface: str):
    """异步装饰器：自动记录请求指标"""
    def decorator(func: Callable):
        async def wrapper(*args, **kwargs):
            scheduler = DataSourceScheduler()
            start_time = time.time()
            success = True
            error_message = None
            data_size = 0

            try:
                result = await func(*args, **kwargs)
                if result is not None:
                    if hasattr(result, '__len__'):
                        data_size = len(result)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                response_time = (time.time() - start_time) * 1000
                scheduler.record_request(
                    source=source,
                    category=category,
                    interface=interface,
                    response_time_ms=response_time,
                    success=success,
                    error_message=error_message,
                    data_size=data_size
                )

        return wrapper
    return decorator


# 全局实例
scheduler = DataSourceScheduler()
