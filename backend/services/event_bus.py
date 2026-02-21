"""
事件总线 - 连接数据采集流和AI分析流的核心组件
轻量级 pub/sub，支持同步/异步回调，线程安全
"""

import asyncio
import threading
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from backend.utils.logging_config import get_logger

logger = get_logger("event_bus")


class EventType(str, Enum):
    """事件类型"""
    # 数据采集事件
    NEWS_URGENT = "news.urgent"              # P0/P1 紧急新闻
    NEWS_BATCH = "news.batch"                # 批量新闻更新
    MARKET_DATA_UPDATED = "market.data.updated"  # 行情数据更新
    MARKET_ANOMALY = "market.anomaly"        # 市场异动（涨停/跌停/放量）

    # 分析事件
    ANALYSIS_REQUESTED = "analysis.requested"    # 分析请求
    ANALYSIS_COMPLETED = "analysis.completed"    # 分析完成
    ANALYSIS_FAILED = "analysis.failed"          # 分析失败

    # 系统事件
    SCHEDULER_TICK = "scheduler.tick"            # 调度器心跳


@dataclass
class Event:
    """事件对象"""
    event_type: EventType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    source: str = ""

    @property
    def age_seconds(self) -> float:
        return time.time() - self.timestamp


@dataclass
class Subscription:
    """订阅"""
    callback: Callable
    is_async: bool = False
    filter_fn: Optional[Callable[[Event], bool]] = None


class EventBus:
    """
    事件总线

    用法:
        bus = get_event_bus()
        bus.subscribe(EventType.NEWS_URGENT, my_handler)
        await bus.publish(Event(EventType.NEWS_URGENT, {"stock": "600519", "title": "..."}))
    """

    _instance = None
    _lock = threading.Lock()

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
        self._subscribers: Dict[EventType, List[Subscription]] = defaultdict(list)
        self._event_log: List[Event] = []
        self._max_log_size = 500
        self._sub_lock = threading.Lock()
        self._stats = {
            "published": 0,
            "delivered": 0,
            "errors": 0,
        }
        logger.info("✅ EventBus 初始化完成")

    def subscribe(
        self,
        event_type: EventType,
        callback: Callable,
        filter_fn: Optional[Callable[[Event], bool]] = None,
    ) -> None:
        """订阅事件"""
        is_async = asyncio.iscoroutinefunction(callback)
        sub = Subscription(callback=callback, is_async=is_async, filter_fn=filter_fn)
        with self._sub_lock:
            self._subscribers[event_type].append(sub)
        logger.info(f"📌 订阅事件: {event_type.value} -> {callback.__qualname__} (async={is_async})")

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """取消订阅"""
        with self._sub_lock:
            self._subscribers[event_type] = [
                s for s in self._subscribers[event_type] if s.callback != callback
            ]

    async def publish(self, event: Event) -> int:
        """
        发布事件，返回成功投递的订阅者数量

        异步回调直接 await，同步回调在线程池中执行
        """
        self._stats["published"] += 1
        self._log_event(event)

        with self._sub_lock:
            subs = list(self._subscribers.get(event.event_type, []))

        if not subs:
            return 0

        delivered = 0
        for sub in subs:
            # 过滤器检查
            if sub.filter_fn and not sub.filter_fn(event):
                continue
            try:
                if sub.is_async:
                    await sub.callback(event)
                else:
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(None, sub.callback, event)
                delivered += 1
                self._stats["delivered"] += 1
            except Exception as e:
                self._stats["errors"] += 1
                logger.error(f"❌ 事件处理失败: {event.event_type.value} -> {sub.callback.__qualname__}: {e}")

        logger.debug(f"📤 事件发布: {event.event_type.value} -> {delivered}/{len(subs)} 订阅者")
        return delivered

    def publish_sync(self, event: Event) -> None:
        """
        同步发布（用于非 async 上下文，如线程中）
        创建新的事件循环或使用已有的
        """
        try:
            loop = asyncio.get_running_loop()
            # 已在 async 上下文中，创建 task
            asyncio.ensure_future(self.publish(event))
        except RuntimeError:
            # 不在 async 上下文中，用 run
            asyncio.run(self.publish(event))

    def _log_event(self, event: Event):
        """记录事件到日志"""
        self._event_log.append(event)
        if len(self._event_log) > self._max_log_size:
            self._event_log = self._event_log[-self._max_log_size:]

    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            **self._stats,
            "subscriber_count": {
                et.value: len(subs) for et, subs in self._subscribers.items() if subs
            },
            "recent_events": [
                {
                    "type": e.event_type.value,
                    "source": e.source,
                    "age": f"{e.age_seconds:.1f}s",
                }
                for e in self._event_log[-10:]
            ],
        }

    def get_recent_events(
        self, event_type: Optional[EventType] = None, limit: int = 20
    ) -> List[Event]:
        """获取最近的事件"""
        events = self._event_log
        if event_type:
            events = [e for e in events if e.event_type == event_type]
        return events[-limit:]


# 全局单例
def get_event_bus() -> EventBus:
    return EventBus()
