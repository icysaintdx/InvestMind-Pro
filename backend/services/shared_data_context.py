"""
共享数据上下文 - 分析会话级数据预获取和共享
避免多个智能体重复获取相同数据
"""

import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from backend.utils.logging_config import get_logger

logger = get_logger("shared_data_context")


@dataclass
class DataSlot:
    """数据槽位"""
    key: str
    data: Any = None
    fetched_at: float = 0
    fetch_duration: float = 0
    source: str = ""
    error: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        return self.data is not None and self.error is None


class SharedDataContext:
    """
    共享数据上下文

    在一次分析会话中，预获取所有需要的数据，供多个智能体共享。
    避免每个智能体独立获取相同数据。

    用法:
        ctx = SharedDataContext(stock_code="600519")
        await ctx.prefetch()
        # 传给每个智能体
        news = ctx.get("news")
        fundamentals = ctx.get("fundamentals")
    """

    # 会话级缓存：同一股票短时间内的多次分析共享上下文
    _session_cache: Dict[str, "SharedDataContext"] = {}
    _session_lock = threading.Lock()
    _SESSION_TTL = 120  # 2 分钟内复用

    def __init__(self, stock_code: str, stock_data: Optional[Dict] = None):
        self.stock_code = stock_code
        self.stock_data = stock_data or {}
        self.created_at = time.time()
        self._slots: Dict[str, DataSlot] = {}
        self._lock = threading.Lock()

    @classmethod
    def get_or_create(cls, stock_code: str, stock_data: Optional[Dict] = None) -> "SharedDataContext":
        """获取或创建共享上下文（同一股票短时间内复用）"""
        with cls._session_lock:
            cached = cls._session_cache.get(stock_code)
            if cached and (time.time() - cached.created_at) < cls._SESSION_TTL:
                logger.info(f"♻️ 复用共享上下文: {stock_code} (age={time.time() - cached.created_at:.0f}s)")
                return cached

            ctx = cls(stock_code, stock_data)
            cls._session_cache[stock_code] = ctx
            logger.info(f"🆕 创建共享上下文: {stock_code}")
            return ctx

    async def prefetch(self) -> Dict[str, bool]:
        """
        预获取所有数据

        Returns:
            各数据槽位的获取状态 {key: success}
        """
        results = {}
        start = time.time()

        # 预获取新闻
        results["news"] = await self._fetch_news()

        # 预获取市场行情增强数据
        results["market_enhanced"] = await self._fetch_market_enhanced()

        duration = time.time() - start
        success_count = sum(1 for v in results.values() if v)
        logger.info(
            f"📦 预获取完成: {self.stock_code} "
            f"({success_count}/{len(results)} 成功, {duration:.2f}s)"
        )
        return results

    async def _fetch_news(self) -> bool:
        """获取新闻数据"""
        try:
            from backend.services.news_center.news_monitor_center import get_news_monitor_center
            monitor = get_news_monitor_center()

            # 从新闻缓存中获取与该股票相关的新闻
            recent_news = monitor.get_latest_news(limit=20)
            if recent_news:
                # 过滤与当前股票相关的新闻
                stock_news = []
                general_news = []
                for news in recent_news:
                    related = news.get("related_stocks", [])
                    clean_code = self.stock_code.replace(".SH", "").replace(".SZ", "")
                    if clean_code in str(related):
                        stock_news.append(news)
                    else:
                        general_news.append(news)

                self._set_slot("stock_news", stock_news, source="news_cache")
                self._set_slot("market_news", general_news[:10], source="news_cache")
                return True
        except Exception as e:
            logger.debug(f"新闻预获取失败: {e}")
            self._set_slot("stock_news", [], error=str(e))
            self._set_slot("market_news", [], error=str(e))
        return False

    async def _fetch_market_enhanced(self) -> bool:
        """获取增强市场数据"""
        try:
            from backend.api.market_data_api import _get_market_data_cached
            df = _get_market_data_cached()
            if df is not None and not df.empty:
                clean_code = self.stock_code.replace(".SH", "").replace(".SZ", "")
                stock_row = df[df["代码"] == clean_code]
                if not stock_row.empty:
                    row = stock_row.iloc[0]
                    enhanced = {
                        "price": row.get("最新价", 0),
                        "change_pct": row.get("涨跌幅", 0),
                        "change": row.get("涨跌额", 0),
                        "volume": row.get("成交量", 0),
                        "amount": row.get("成交额", 0),
                        "high": row.get("最高", 0),
                        "low": row.get("最低", 0),
                        "open": row.get("今开", 0),
                        "pre_close": row.get("昨收", 0),
                        "turnover": row.get("换手率", 0),
                    }
                    self._set_slot("market_enhanced", enhanced, source="market_cache")
                    return True
        except Exception as e:
            logger.debug(f"增强行情预获取失败: {e}")
        return False

    def _set_slot(self, key: str, data: Any, source: str = "", error: Optional[str] = None):
        """设置数据槽位"""
        with self._lock:
            self._slots[key] = DataSlot(
                key=key,
                data=data,
                fetched_at=time.time(),
                source=source,
                error=error,
            )

    def get(self, key: str) -> Any:
        """获取数据"""
        with self._lock:
            slot = self._slots.get(key)
            if slot and slot.is_valid:
                return slot.data
            return None

    def get_enriched_stock_data(self) -> Dict:
        """
        获取增强后的股票数据（合并原始数据 + 预获取数据）
        用于替代前端传来的简单 stock_data
        """
        enriched = dict(self.stock_data)

        # 合并增强行情
        market = self.get("market_enhanced")
        if market:
            for k, v in market.items():
                if k not in enriched or not enriched[k]:
                    enriched[k] = v

        return enriched

    def build_news_context(self, max_items: int = 5) -> str:
        """构建新闻上下文文本，供智能体 prompt 使用"""
        stock_news = self.get("stock_news") or []
        market_news = self.get("market_news") or []

        parts = []
        if stock_news:
            parts.append("【个股相关新闻】")
            for n in stock_news[:max_items]:
                title = n.get("title", "")
                sentiment = n.get("sentiment", "neutral")
                parts.append(f"- [{sentiment}] {title}")

        if market_news:
            parts.append("\n【市场新闻】")
            for n in market_news[:3]:
                parts.append(f"- {n.get('title', '')}")

        return "\n".join(parts) if parts else ""

    def get_summary(self) -> Dict:
        """获取上下文摘要"""
        with self._lock:
            return {
                "stock_code": self.stock_code,
                "age": f"{time.time() - self.created_at:.0f}s",
                "slots": {
                    key: {
                        "valid": slot.is_valid,
                        "source": slot.source,
                        "error": slot.error,
                    }
                    for key, slot in self._slots.items()
                },
            }

    @classmethod
    def cleanup_sessions(cls):
        """清理过期的会话缓存"""
        with cls._session_lock:
            expired = [
                k for k, v in cls._session_cache.items()
                if (time.time() - v.created_at) > cls._SESSION_TTL * 3
            ]
            for k in expired:
                del cls._session_cache[k]
