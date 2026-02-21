"""
自动分析触发器 - 连接数据采集流和AI分析流的桥梁

职责:
1. 订阅 EventBus 事件（紧急新闻、市场异动）
2. 紧急新闻到达时，使相关股票的分析缓存失效
3. 定时检测市场异动（涨停/跌停/放量）
4. 定时清理过期缓存和会话
"""

import asyncio
import threading
import time
from datetime import datetime
from typing import Dict, List, Optional

from backend.services.event_bus import get_event_bus, Event, EventType
from backend.services.analysis_cache import get_analysis_cache
from backend.services.shared_data_context import SharedDataContext
from backend.utils.logging_config import get_logger

logger = get_logger("auto_analysis_trigger")


def _is_trading_time() -> bool:
    """判断当前是否为A股交易时段"""
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    hour_min = now.hour * 100 + now.minute
    return 915 <= hour_min <= 1530


class AutoAnalysisTrigger:
    """自动分析触发器"""

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
        self._running = False
        self._tasks: List[asyncio.Task] = []
        self._stats = {
            "news_triggers": 0,
            "anomaly_triggers": 0,
            "cache_invalidations": 0,
            "scheduled_checks": 0,
        }
        logger.info("✅ AutoAnalysisTrigger 初始化完成")

    async def start(self):
        """启动触发器：订阅事件 + 启动定时任务"""
        if self._running:
            return
        self._running = True

        bus = get_event_bus()

        # 订阅紧急新闻事件
        bus.subscribe(EventType.NEWS_URGENT, self._on_urgent_news)
        # 订阅市场异动事件
        bus.subscribe(EventType.MARKET_ANOMALY, self._on_market_anomaly)
        # 订阅批量新闻（用于统计）
        bus.subscribe(EventType.NEWS_BATCH, self._on_news_batch)

        # 启动定时任务
        self._tasks.append(asyncio.create_task(self._periodic_anomaly_check()))
        self._tasks.append(asyncio.create_task(self._periodic_cleanup()))

        logger.info("✅ AutoAnalysisTrigger 已启动 (2个定时任务, 3个事件订阅)")

    async def stop(self):
        """停止触发器"""
        self._running = False
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

        bus = get_event_bus()
        bus.unsubscribe(EventType.NEWS_URGENT, self._on_urgent_news)
        bus.unsubscribe(EventType.MARKET_ANOMALY, self._on_market_anomaly)
        bus.unsubscribe(EventType.NEWS_BATCH, self._on_news_batch)

        logger.info("AutoAnalysisTrigger 已停止")

    # ==================== 事件处理 ====================

    async def _on_urgent_news(self, event: Event):
        """
        处理紧急新闻事件

        策略：使相关股票的分析缓存失效，下次用户请求时自动获取最新分析
        不主动触发LLM调用（避免烧额度），但确保缓存不会返回过时结论
        """
        self._stats["news_triggers"] += 1
        data = event.data
        related_stocks = data.get("related_stocks", [])
        priority = data.get("priority", "P1")
        news_list = data.get("news", [])

        if not related_stocks:
            return

        cache = get_analysis_cache()
        invalidated = 0
        for stock_code in related_stocks:
            count = cache.invalidate(stock_code)
            invalidated += count

        self._stats["cache_invalidations"] += invalidated

        # 同时清理共享数据上下文，强制下次预获取
        for stock_code in related_stocks:
            with SharedDataContext._session_lock:
                SharedDataContext._session_cache.pop(stock_code, None)

        titles = [n.get("title", "")[:40] for n in news_list[:3]]
        logger.info(
            f"🔔 紧急新闻触发 [{priority}]: "
            f"关联股票={related_stocks}, 缓存失效={invalidated}条, "
            f"新闻={titles}"
        )

    async def _on_market_anomaly(self, event: Event):
        """处理市场异动事件"""
        self._stats["anomaly_triggers"] += 1
        data = event.data
        stock_code = data.get("stock_code", "")
        anomaly_type = data.get("type", "unknown")

        if stock_code:
            cache = get_analysis_cache()
            count = cache.invalidate(stock_code)
            self._stats["cache_invalidations"] += count
            logger.info(f"📊 市场异动触发: {stock_code} ({anomaly_type}), 缓存失效={count}条")

    async def _on_news_batch(self, event: Event):
        """处理批量新闻事件（仅记录统计）"""
        data = event.data
        logger.debug(
            f"📰 新闻批次: source={data.get('source')}, "
            f"count={data.get('count')}, P0={data.get('p0', 0)}, P1={data.get('p1', 0)}"
        )

    # ==================== 定时任务 ====================

    async def _periodic_anomaly_check(self):
        """
        定时市场异动检测

        交易时段每60秒检查一次，非交易时段休眠
        检测：涨停/跌停/放量异动
        """
        await asyncio.sleep(30)  # 启动延迟
        while self._running:
            try:
                if _is_trading_time():
                    await self._check_market_anomalies()
                    self._stats["scheduled_checks"] += 1
                    await asyncio.sleep(60)
                else:
                    # 非交易时段，每5分钟检查一次是否进入交易时段
                    await asyncio.sleep(300)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"异动检测异常: {e}")
                await asyncio.sleep(60)

    async def _check_market_anomalies(self):
        """检查市场异动"""
        try:
            from backend.api.market_data_api import _get_market_data_cached
            df = _get_market_data_cached()
            if df is None or df.empty:
                return

            bus = get_event_bus()
            anomaly_count = 0

            # 获取监控股票列表
            monitored_codes = self._get_monitored_codes()

            for _, row in df.iterrows():
                code = str(row.get("代码", ""))
                if monitored_codes and code not in monitored_codes:
                    continue

                change_pct = float(row.get("涨跌幅", 0) or 0)
                turnover = float(row.get("换手率", 0) or 0)

                # 涨停/跌停检测
                if abs(change_pct) >= 9.8:
                    anomaly_type = "limit_up" if change_pct > 0 else "limit_down"
                    await bus.publish(Event(
                        event_type=EventType.MARKET_ANOMALY,
                        data={
                            "stock_code": code,
                            "type": anomaly_type,
                            "change_pct": change_pct,
                            "name": str(row.get("名称", "")),
                        },
                        source="anomaly_check",
                    ))
                    anomaly_count += 1

                # 放量异动（换手率 > 15%）
                elif turnover > 15:
                    await bus.publish(Event(
                        event_type=EventType.MARKET_ANOMALY,
                        data={
                            "stock_code": code,
                            "type": "volume_surge",
                            "turnover": turnover,
                            "change_pct": change_pct,
                            "name": str(row.get("名称", "")),
                        },
                        source="anomaly_check",
                    ))
                    anomaly_count += 1

            if anomaly_count > 0:
                logger.info(f"📊 异动检测完成: 发现 {anomaly_count} 个异动")

        except Exception as e:
            logger.debug(f"市场异动检测失败: {e}")

    async def _periodic_cleanup(self):
        """定时清理过期缓存和会话"""
        await asyncio.sleep(120)  # 启动延迟
        while self._running:
            try:
                # 清理分析缓存
                cache = get_analysis_cache()
                removed = cache.cleanup()
                if removed > 0:
                    logger.info(f"🗑️ 清理过期缓存: {removed}条")

                # 清理共享数据上下文
                SharedDataContext.cleanup_sessions()

                await asyncio.sleep(300)  # 每5分钟清理一次
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"缓存清理异常: {e}")
                await asyncio.sleep(300)

    # ==================== 辅助方法 ====================

    def _get_monitored_codes(self) -> set:
        """获取监控股票代码集合"""
        try:
            from backend.services.alert_service import get_alert_service
            alert_service = get_alert_service()
            monitored = alert_service.get_monitored_stocks()
            if monitored:
                return {ts.split(".")[0] for ts in monitored.keys()}
        except Exception:
            pass
        return set()

    def get_stats(self) -> Dict:
        """获取触发器统计"""
        return {
            **self._stats,
            "running": self._running,
            "cache_stats": get_analysis_cache().get_stats(),
            "event_bus_stats": get_event_bus().get_stats(),
        }


# 全局单例
def get_auto_analysis_trigger() -> AutoAnalysisTrigger:
    return AutoAnalysisTrigger()
