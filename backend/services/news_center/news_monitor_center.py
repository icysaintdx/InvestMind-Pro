# -*- coding: utf-8 -*-
import asyncio
import logging
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum

from .news_cache import NewsCache, CachedNews, get_news_cache
from .stock_relation_analyzer import StockRelationAnalyzer, get_stock_relation_analyzer
from .impact_assessor import ImpactAssessor, get_impact_assessor

logger = logging.getLogger(__name__)

# WebSocket 推送函数 (延迟导入避免循环依赖)
_ws_notify_news = None
_ws_notify_urgent = None

def _get_ws_notifiers():
    global _ws_notify_news, _ws_notify_urgent
    if _ws_notify_news is None:
        try:
            from backend.api.websocket_api import notify_news_update, notify_urgent_news
            _ws_notify_news = notify_news_update
            _ws_notify_urgent = notify_urgent_news
        except Exception as e:
            logger.warning(f"Failed to import WebSocket notifiers: {e}")
    return _ws_notify_news, _ws_notify_urgent

class DataSourceType(str, Enum):
    CLS = "cls"
    EASTMONEY = "eastmoney"
    SINA = "sina"
    CNINFO = "cninfo"

@dataclass
class DataSourceConfig:
    name: str
    source_type: DataSourceType
    interval: int
    enabled: bool = True
    priority: int = 1
    last_fetch: str = ""
    fetch_count: int = 0
    error_count: int = 0

class NewsMonitorCenter:
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
        self._cache = get_news_cache()
        self._stock_analyzer = get_stock_relation_analyzer()
        self._impact_assessor = get_impact_assessor()
        self._sentiment_engine = None
        self._init_sentiment_engine()
        self._sources: Dict[str, DataSourceConfig] = {
            "cls": DataSourceConfig("财联社电报", DataSourceType.CLS, 30, priority=10),
            "eastmoney": DataSourceConfig("东方财富", DataSourceType.EASTMONEY, 60, priority=8),
            "eastmoney_global": DataSourceConfig("东财全球", DataSourceType.EASTMONEY, 120, priority=5),
            "cninfo": DataSourceConfig("巨潮公告", DataSourceType.CNINFO, 300, priority=7),
        }
        self._running = False
        self._executor: Optional[ThreadPoolExecutor] = None
        self._fetch_tasks: Dict[str, asyncio.Task] = {}
        self._on_new_news: List[Callable] = []
        self._on_urgent_news: List[Callable] = []
        self._stats = {"total_fetched": 0, "total_processed": 0, "total_duplicates": 0, "start_time": None, "last_fetch_time": None}
        logger.info("NewsMonitorCenter initialized")
    
    def _init_sentiment_engine(self):
        try:
            from backend.dataflows.news.sentiment_engine import get_sentiment_engine
            self._sentiment_engine = get_sentiment_engine()
        except Exception as e:
            logger.warning(f"Failed to load sentiment engine: {e}")
    
    async def start(self):
        if self._running:
            return
        self._running = True
        self._stats["start_time"] = datetime.now().isoformat()
        self._executor = ThreadPoolExecutor(max_workers=4)
        for source_id, config in self._sources.items():
            if config.enabled:
                task = asyncio.create_task(self._fetch_loop(source_id))
                self._fetch_tasks[source_id] = task
        logger.info(f"NewsMonitorCenter started with {len(self._fetch_tasks)} sources")
    
    async def stop(self):
        self._running = False
        for task in self._fetch_tasks.values():
            task.cancel()
        self._fetch_tasks.clear()
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
        self._cache.save_to_file()
        logger.info("NewsMonitorCenter stopped")
    
    async def _fetch_loop(self, source_id: str):
        config = self._sources.get(source_id)
        if not config:
            return
        while self._running:
            try:
                await self._fetch_source(source_id)
                config.last_fetch = datetime.now().isoformat()
                config.fetch_count += 1
            except Exception as e:
                config.error_count += 1
                logger.error(f"Fetch error for {source_id}: {e}")
            await asyncio.sleep(config.interval)

    async def _fetch_source(self, source_id: str):
        config = self._sources.get(source_id)
        if not config:
            return
        news_list = []
        try:
            if config.source_type == DataSourceType.CLS:
                news_list = await self._fetch_cls()
            elif config.source_type == DataSourceType.EASTMONEY:
                if source_id == "eastmoney_global":
                    news_list = await self._fetch_eastmoney_global()
                else:
                    news_list = await self._fetch_eastmoney()
        except Exception as e:
            logger.error(f"Fetch {source_id} failed: {e}")
            return
        if news_list:
            await self._process_news(news_list, source_id)
    
    async def _fetch_cls(self) -> List[Dict]:
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(self._executor, ak.stock_telegraph_cls)
            if df is None or df.empty:
                return []
            news_list = []
            for _, row in df.head(30).iterrows():
                news_list.append({"title": str(row.get("标题", "")), "content": str(row.get("内容", ""))[:1000], "pub_time": str(row.get("发布时间", "")), "source": "财联社", "url": ""})
            return news_list
        except Exception as e:
            logger.error(f"Fetch CLS failed: {e}")
            return []
    
    async def _fetch_eastmoney(self) -> List[Dict]:
        return []
    
    async def _fetch_eastmoney_global(self) -> List[Dict]:
        try:
            import akshare as ak
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(self._executor, ak.stock_info_global_em)
            if df is None or df.empty:
                return []
            news_list = []
            for _, row in df.head(20).iterrows():
                news_list.append({"title": str(row.get("标题", "")), "content": str(row.get("摘要", ""))[:500], "pub_time": str(row.get("发布时间", "")), "source": "东财全球", "url": str(row.get("链接", ""))})
            return news_list
        except Exception as e:
            logger.error(f"Fetch eastmoney global failed: {e}")
            return []
    
    async def _process_news(self, news_list: List[Dict], source_id: str):
        new_count = 0
        urgent_news = []
        for news_data in news_list:
            title = news_data.get("title", "")
            content = news_data.get("content", "")
            if not title:
                continue
            if self._cache.is_duplicate(title, news_data.get("pub_time", "")):
                self._stats["total_duplicates"] += 1
                continue
            sentiment_result = {"sentiment": "neutral", "score": 50, "urgency": "low"}
            if self._sentiment_engine:
                try:
                    sentiment_result = self._sentiment_engine.analyze(title, content)
                except:
                    pass
            related_stocks = self._stock_analyzer.get_related_codes(title, content)
            impact = self._impact_assessor.assess(title, content, sentiment_result.get("score", 50))
            enriched_news = {**news_data, "sentiment": sentiment_result.get("sentiment", "neutral"), "sentiment_score": sentiment_result.get("score", 50), "urgency": impact.urgency, "keywords": sentiment_result.get("keywords", []), "related_stocks": related_stocks, "impact_score": impact.score}
            result = self._cache.add_news_batch([enriched_news])
            if result["added"] > 0:
                new_count += 1
                self._stats["total_processed"] += 1
                if impact.urgency in ["critical", "high"]:
                    urgent_news.append(enriched_news)
        self._stats["total_fetched"] += len(news_list)
        self._stats["last_fetch_time"] = datetime.now().isoformat()
        if new_count > 0:
            logger.info(f"[{source_id}] Processed {new_count} new news")
            for callback in self._on_new_news:
                try:
                    callback(new_count, source_id)
                except:
                    pass
        if urgent_news:
            logger.warning(f"[{source_id}] Found {len(urgent_news)} urgent news!")
            for callback in self._on_urgent_news:
                try:
                    callback(urgent_news)
                except:
                    pass
            # WebSocket 推送紧急新闻
            ws_notify, ws_urgent = _get_ws_notifiers()
            if ws_urgent:
                try:
                    asyncio.create_task(ws_urgent(urgent_news))
                except:
                    pass

    def get_latest_news(self, limit: int = 50, **filters) -> List[Dict]:
        news_list = self._cache.get_latest_news(limit, **filters)
        return [n.to_dict() for n in news_list]
    
    def get_urgent_news(self, limit: int = 20) -> List[Dict]:
        news_list = self._cache.get_urgent_news(limit)
        return [n.to_dict() for n in news_list]
    
    def get_news_for_stock(self, stock_code: str, limit: int = 30) -> List[Dict]:
        news_list = self._cache.get_news_for_stock(stock_code, limit)
        return [n.to_dict() for n in news_list]
    
    def get_stats(self) -> Dict[str, Any]:
        cache_stats = self._cache.get_stats()
        source_stats = {sid: {"name": cfg.name, "interval": cfg.interval, "enabled": cfg.enabled, "last_fetch": cfg.last_fetch, "fetch_count": cfg.fetch_count, "error_count": cfg.error_count} for sid, cfg in self._sources.items()}
        return {**self._stats, "cache": cache_stats, "sources": source_stats, "running": self._running}
    
    def set_source_interval(self, source_id: str, interval: int):
        if source_id in self._sources:
            self._sources[source_id].interval = max(10, interval)
            logger.info(f"Set {source_id} interval to {interval}s")
    
    def enable_source(self, source_id: str, enabled: bool = True):
        if source_id in self._sources:
            self._sources[source_id].enabled = enabled
            logger.info(f"Set {source_id} enabled={enabled}")
    
    def on_new_news(self, callback: Callable):
        self._on_new_news.append(callback)
    
    def on_urgent_news(self, callback: Callable):
        self._on_urgent_news.append(callback)
    
    async def fetch_now(self, source_id: str = None):
        if source_id:
            await self._fetch_source(source_id)
        else:
            for sid in self._sources:
                await self._fetch_source(sid)
    
    def cleanup(self):
        return self._cache.cleanup_expired()

_monitor_center = None

def get_news_monitor_center() -> NewsMonitorCenter:
    global _monitor_center
    if _monitor_center is None:
        _monitor_center = NewsMonitorCenter()
    return _monitor_center
