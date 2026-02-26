"""
统一新闻Provider
整合所有新闻数据源
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from backend.utils.logging_config import get_logger
from ..base_provider import BaseProvider, register_provider
from ..models import (
    Symbol, MarketType, NewsItem, DataPriority
)
from ..cache_manager import cache_manager

logger = get_logger("provider.unified_news")


@register_provider("unified_news")
class UnifiedNewsProvider(BaseProvider):
    """
    统一新闻Provider
    
    整合多个新闻源：
    - 东方财富
    - 财联社
    - 新浪财经
    - 同花顺
    """
    
    def __init__(self):
        super().__init__("unified_news", [MarketType.A_SHARE])
        self._sources = [
            "eastmoney", "cls", "sina", "ths", "futu", "weibo"
        ]
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            news = await self.get_news(limit=1)
            return len(news) > 0
        except Exception as e:
            logger.error(f"[UnifiedNews] 健康检查失败: {e}")
            return False
    
    async def get_news(
        self,
        symbols: Optional[List[Symbol]] = None,
        hours: int = 24,
        limit: int = 100,
        priority: DataPriority = DataPriority.FAST
    ) -> List[NewsItem]:
        """
        获取新闻（并行从多个源获取）
        """
        cache_key = f"all_{hours}_{limit}"
        cached = cache_manager.get("news", cache_key)
        if cached:
            return cached
        
        try:
            import akshare as ak
            
            # 并行获取多个新闻源
            tasks = []
            
            # 1. 东方财富全球资讯
            tasks.append(self._fetch_eastmoney_global(ak))
            
            # 2. 财联社
            tasks.append(self._fetch_cls(ak))
            
            # 3. 新浪财经
            tasks.append(self._fetch_sina(ak))
            
            # 4. 同花顺
            tasks.append(self._fetch_ths(ak))
            
            # 5. 富途牛牛
            tasks.append(self._fetch_futu(ak))
            
            # 6. 微博热议
            tasks.append(self._fetch_weibo(ak))
            
            # 并行执行
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 合并去重
            all_news = []
            seen_titles = set()
            
            for result in results:
                if isinstance(result, list):
                    for news in result:
                        title = news.get("title", "")
                        if title and title not in seen_titles:
                            seen_titles.add(title)
                            all_news.append(news)
            
            # 按时间排序
            all_news.sort(key=lambda x: x.get("publish_time", ""), reverse=True)
            
            # 限制数量
            all_news = all_news[:limit]
            
            # 转换为NewsItem
            news_items = []
            for news in all_news:
                try:
                    item = NewsItem(
                        id=f"news_{hash(news.get('title', ''))}",
                        title=news.get("title", ""),
                        content=news.get("content", ""),
                        source=news.get("source", "未知"),
                        publish_time=datetime.fromisoformat(news.get("publish_time", datetime.now().isoformat())),
                        sentiment=float(news.get("sentiment", 0)),
                        sentiment_label=news.get("sentiment_label", "neutral"),
                        url=news.get("url"),
                    )
                    news_items.append(item)
                except Exception as e:
                    logger.debug(f"[UnifiedNews] 转换新闻失败: {e}")
                    continue
            
            if news_items:
                cache_manager.set("news", cache_key, news_items)
            
            return news_items
            
        except Exception as e:
            self._handle_error("get_news", e)
            return []
    
    async def _fetch_eastmoney_global(self, ak) -> List[Dict]:
        """东方财富全球资讯"""
        try:
            df = await asyncio.to_thread(ak.stock_info_global_em)
            if df is None or df.empty:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                title = str(row.get("标题", ""))
                if title:
                    news_list.append({
                        "title": title,
                        "content": str(row.get("摘要", row.get("内容", "")))[:500],
                        "source": "东方财富",
                        "publish_time": datetime.now().isoformat(),  # 简化处理
                        "sentiment": 0,
                        "url": str(row.get("链接", "")),
                    })
            return news_list
        except Exception as e:
            logger.debug(f"[UnifiedNews] 东方财富获取失败: {e}")
            return []
    
    async def _fetch_cls(self, ak) -> List[Dict]:
        """财联社"""
        try:
            df = await asyncio.to_thread(ak.stock_info_global_cls)
            if df is None or df.empty:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                title = str(row.get("标题", ""))
                if title:
                    news_list.append({
                        "title": title,
                        "content": str(row.get("内容", ""))[:500],
                        "source": "财联社",
                        "publish_time": f"{row.get('发布日期', '')} {row.get('发布时间', '')}",
                        "sentiment": 0,
                    })
            return news_list
        except Exception as e:
            logger.debug(f"[UnifiedNews] 财联社获取失败: {e}")
            return []
    
    async def _fetch_sina(self, ak) -> List[Dict]:
        """新浪财经"""
        try:
            df = await asyncio.to_thread(ak.stock_info_global_sina)
            if df is None or df.empty:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                title = str(row.get("标题", ""))
                if title:
                    news_list.append({
                        "title": title,
                        "content": str(row.get("内容", ""))[:500],
                        "source": "新浪财经",
                        "publish_time": str(row.get("pub_time", datetime.now().isoformat())),
                        "sentiment": 0,
                    })
            return news_list
        except Exception as e:
            logger.debug(f"[UnifiedNews] 新浪财经获取失败: {e}")
            return []
    
    async def _fetch_ths(self, ak) -> List[Dict]:
        """同花顺"""
        try:
            df = await asyncio.to_thread(ak.stock_info_global_ths)
            if df is None or df.empty:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                title = str(row.get("标题", ""))
                if title:
                    news_list.append({
                        "title": title,
                        "content": str(row.get("内容", ""))[:500],
                        "source": "同花顺",
                        "publish_time": str(row.get("发布时间", datetime.now().isoformat())),
                        "sentiment": 0,
                    })
            return news_list
        except Exception as e:
            logger.debug(f"[UnifiedNews] 同花顺获取失败: {e}")
            return []
    
    async def _fetch_futu(self, ak) -> List[Dict]:
        """富途牛牛"""
        try:
            df = await asyncio.to_thread(ak.stock_info_global_futu)
            if df is None or df.empty:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                title = str(row.get("标题", ""))
                if title:
                    news_list.append({
                        "title": title,
                        "content": str(row.get("内容", ""))[:500],
                        "source": "富途牛牛",
                        "publish_time": str(row.get("发布时间", datetime.now().isoformat())),
                        "sentiment": 0,
                    })
            return news_list
        except Exception as e:
            logger.debug(f"[UnifiedNews] 富途牛牛获取失败: {e}")
            return []
    
    async def _fetch_weibo(self, ak) -> List[Dict]:
        """微博热议"""
        try:
            df = await asyncio.to_thread(ak.stock_js_weibo_report)
            if df is None or df.empty:
                return []
            
            news_list = []
            for _, row in df.iterrows():
                title = str(row.get("标题", ""))
                if title:
                    news_list.append({
                        "title": title,
                        "content": str(row.get("内容", ""))[:500],
                        "source": "微博热议",
                        "publish_time": str(row.get("发布时间", datetime.now().isoformat())),
                        "sentiment": 0,
                    })
            return news_list
        except Exception as e:
            logger.debug(f"[UnifiedNews] 微博热议获取失败: {e}")
            return []
