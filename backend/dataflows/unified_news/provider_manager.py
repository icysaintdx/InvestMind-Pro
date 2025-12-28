"""
新闻数据源管理器

负责管理所有新闻数据源提供者，提供统一的接口来获取新闻。
支持数据源优先级、故障转移、并发获取等功能。
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any, Type
import logging
from collections import defaultdict

from .base_provider import BaseNewsProvider
from .models import (
    UnifiedNewsItem,
    NewsSourceInfo,
    NewsStatistics,
    NewsFilter,
    MarketType,
    SourceType
)
from .providers import AKShareNewsProvider, WencaiNewsProvider

logger = logging.getLogger(__name__)


class NewsProviderManager:
    """新闻数据源管理器"""
    
    # 默认数据源优先级（数字越小优先级越高）
    DEFAULT_PRIORITY = {
        SourceType.AKSHARE.value: 1,      # AKShare优先（免费、稳定）
        SourceType.WENCAI.value: 2,       # 问财次之（免费、智能）
        SourceType.TUSHARE.value: 3,      # Tushare（需积分）
        SourceType.FINNHUB.value: 4,      # FinnHub（美股）
        SourceType.ALPHA_VANTAGE.value: 5, # Alpha Vantage（美股）
        SourceType.NEWSAPI.value: 6,      # NewsAPI（全球）
        SourceType.GOOGLE.value: 7,       # Google（备用）
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据源管理器
        
        Args:
            config: 配置字典，可包含各数据源的配置
        """
        self.config = config or {}
        self._providers: Dict[str, BaseNewsProvider] = {}
        self._priority: Dict[str, int] = self.DEFAULT_PRIORITY.copy()
        self._enabled_sources: List[str] = []
        
        # 初始化默认数据源
        self._initialize_providers()
    
    def _initialize_providers(self):
        """初始化所有数据源提供者"""
        # 注册AKShare提供者
        try:
            akshare_provider = AKShareNewsProvider(self.config.get('akshare', {}))
            self.register_provider(akshare_provider)
        except Exception as e:
            logger.error(f"初始化AKShare提供者失败: {e}")
        
        # 注册问财提供者
        try:
            wencai_provider = WencaiNewsProvider(self.config.get('wencai', {}))
            self.register_provider(wencai_provider)
        except Exception as e:
            logger.error(f"初始化问财提供者失败: {e}")
        
        # TODO: 注册其他提供者（Tushare、FinnHub等）
        
        logger.info(f"数据源管理器初始化完成，已注册{len(self._providers)}个数据源")
    
    def register_provider(self, provider: BaseNewsProvider):
        """
        注册数据源提供者
        
        Args:
            provider: 数据源提供者实例
        """
        source_type = provider.source_type
        self._providers[source_type] = provider
        
        if provider.is_available:
            self._enabled_sources.append(source_type)
            logger.info(f"注册数据源: {provider.name} ({source_type})")
        else:
            logger.warning(f"数据源不可用: {provider.name} - {provider.last_error}")
    
    def unregister_provider(self, source_type: str):
        """
        注销数据源提供者
        
        Args:
            source_type: 数据源类型
        """
        if source_type in self._providers:
            del self._providers[source_type]
            if source_type in self._enabled_sources:
                self._enabled_sources.remove(source_type)
            logger.info(f"注销数据源: {source_type}")
    
    def get_provider(self, source_type: str) -> Optional[BaseNewsProvider]:
        """
        获取指定数据源提供者
        
        Args:
            source_type: 数据源类型
            
        Returns:
            数据源提供者实例或None
        """
        return self._providers.get(source_type)
    
    def get_available_providers(self) -> List[BaseNewsProvider]:
        """获取所有可用的数据源提供者"""
        return [
            p for p in self._providers.values()
            if p.is_available
        ]
    
    def get_providers_by_market(self, market: str) -> List[BaseNewsProvider]:
        """
        获取支持指定市场的数据源提供者
        
        Args:
            market: 市场类型
            
        Returns:
            数据源提供者列表
        """
        return [
            p for p in self._providers.values()
            if p.is_available and market in p.supported_markets
        ]
    
    def set_priority(self, source_type: str, priority: int):
        """
        设置数据源优先级
        
        Args:
            source_type: 数据源类型
            priority: 优先级（数字越小优先级越高）
        """
        self._priority[source_type] = priority
    
    def enable_source(self, source_type: str):
        """启用数据源"""
        if source_type in self._providers and source_type not in self._enabled_sources:
            self._enabled_sources.append(source_type)
    
    def disable_source(self, source_type: str):
        """禁用数据源"""
        if source_type in self._enabled_sources:
            self._enabled_sources.remove(source_type)
    
    def get_sources_info(self) -> List[NewsSourceInfo]:
        """获取所有数据源信息"""
        return [p.get_source_info() for p in self._providers.values()]
    
    async def fetch_news(
        self,
        filter_params: Optional[NewsFilter] = None,
        sources: Optional[List[str]] = None,
        concurrent: bool = True
    ) -> List[UnifiedNewsItem]:
        """
        获取新闻列表
        
        Args:
            filter_params: 筛选参数
            sources: 指定数据源列表（可选）
            concurrent: 是否并发获取
            
        Returns:
            统一格式的新闻列表
        """
        filter_params = filter_params or NewsFilter()
        
        # 确定要使用的数据源
        if sources:
            target_sources = [s for s in sources if s in self._enabled_sources]
        else:
            target_sources = self._enabled_sources.copy()
        
        # 按优先级排序
        target_sources.sort(key=lambda x: self._priority.get(x, 999))
        
        if not target_sources:
            logger.warning("没有可用的数据源")
            return []
        
        all_news = []
        
        if concurrent:
            # 并发获取
            tasks = []
            for source_type in target_sources:
                provider = self._providers.get(source_type)
                if provider and provider.is_available:
                    task = self._fetch_from_provider(provider, filter_params)
                    tasks.append(task)
            
            if tasks:
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for result in results:
                    if isinstance(result, list):
                        all_news.extend(result)
                    elif isinstance(result, Exception):
                        logger.error(f"获取新闻失败: {result}")
        else:
            # 顺序获取
            for source_type in target_sources:
                provider = self._providers.get(source_type)
                if provider and provider.is_available:
                    try:
                        news = await self._fetch_from_provider(provider, filter_params)
                        all_news.extend(news)
                    except Exception as e:
                        logger.error(f"从{source_type}获取新闻失败: {e}")
        
        # 应用筛选条件
        all_news = self._apply_filters(all_news, filter_params)
        
        # 去重
        all_news = self._deduplicate(all_news)
        
        # 排序
        all_news = self._sort_news(all_news, filter_params.sort_by, filter_params.sort_order)
        
        # 分页
        start = (filter_params.page - 1) * filter_params.page_size
        end = start + filter_params.page_size
        
        return all_news[start:end]
    
    async def _fetch_from_provider(
        self,
        provider: BaseNewsProvider,
        filter_params: NewsFilter
    ) -> List[UnifiedNewsItem]:
        """从单个数据源获取新闻"""
        try:
            return await provider.fetch_news(
                stock_code=filter_params.stock_code or None,
                keyword=filter_params.keyword or None,
                start_date=filter_params.start_date,
                end_date=filter_params.end_date,
                limit=filter_params.page_size * 2  # 获取更多以便筛选
            )
        except Exception as e:
            logger.error(f"从{provider.name}获取新闻失败: {e}")
            return []
    
    def _apply_filters(
        self,
        news_list: List[UnifiedNewsItem],
        filter_params: NewsFilter
    ) -> List[UnifiedNewsItem]:
        """应用筛选条件"""
        filtered = news_list
        
        # 按市场筛选
        if filter_params.markets:
            filtered = [n for n in filtered if n.market in filter_params.markets]
        
        # 按数据源筛选
        if filter_params.sources:
            filtered = [n for n in filtered if n.source in filter_params.sources or n.source_type in filter_params.sources]
        
        # 按类型筛选
        if filter_params.news_types:
            filtered = [n for n in filtered if n.news_type in filter_params.news_types]
        
        # 按情绪筛选
        if filter_params.sentiments:
            filtered = [n for n in filtered if n.sentiment_label in filter_params.sentiments]
        
        # 按关键词筛选
        if filter_params.keyword:
            keyword = filter_params.keyword.lower()
            filtered = [
                n for n in filtered
                if keyword in n.title.lower() or keyword in n.content.lower()
            ]
        
        # 按股票代码筛选
        if filter_params.stock_code:
            code = filter_params.stock_code
            filtered = [
                n for n in filtered
                if code in n.related_stocks or code in n.title or code in n.content
            ]
        
        # 按时间筛选
        if filter_params.start_date:
            filtered = [
                n for n in filtered
                if n.publish_time and n.publish_time >= filter_params.start_date
            ]
        if filter_params.end_date:
            filtered = [
                n for n in filtered
                if n.publish_time and n.publish_time <= filter_params.end_date
            ]
        
        return filtered
    
    def _deduplicate(self, news_list: List[UnifiedNewsItem]) -> List[UnifiedNewsItem]:
        """去重"""
        seen_titles = set()
        unique_news = []
        
        for news in news_list:
            # 使用标题的前50个字符作为去重键
            key = news.title[:50] if news.title else news.id
            if key not in seen_titles:
                seen_titles.add(key)
                unique_news.append(news)
        
        return unique_news
    
    def _sort_news(
        self,
        news_list: List[UnifiedNewsItem],
        sort_by: str,
        sort_order: str
    ) -> List[UnifiedNewsItem]:
        """排序"""
        reverse = sort_order.lower() == 'desc'
        
        if sort_by == 'publish_time':
            return sorted(
                news_list,
                key=lambda x: x.publish_time or datetime.min,
                reverse=reverse
            )
        elif sort_by == 'relevance_score':
            return sorted(
                news_list,
                key=lambda x: x.relevance_score,
                reverse=reverse
            )
        elif sort_by == 'sentiment_score':
            return sorted(
                news_list,
                key=lambda x: x.sentiment_score,
                reverse=reverse
            )
        else:
            return news_list
    
    async def fetch_stock_news(
        self,
        stock_code: str,
        limit: int = 50,
        sources: Optional[List[str]] = None
    ) -> List[UnifiedNewsItem]:
        """
        获取个股新闻
        
        Args:
            stock_code: 股票代码
            limit: 返回数量限制
            sources: 指定数据源列表
            
        Returns:
            新闻列表
        """
        filter_params = NewsFilter(
            stock_code=stock_code,
            page_size=limit
        )
        return await self.fetch_news(filter_params, sources)
    
    async def fetch_market_news(
        self,
        market: str = MarketType.A_SHARE.value,
        limit: int = 50,
        sources: Optional[List[str]] = None
    ) -> List[UnifiedNewsItem]:
        """
        获取市场新闻
        
        Args:
            market: 市场类型
            limit: 返回数量限制
            sources: 指定数据源列表
            
        Returns:
            新闻列表
        """
        filter_params = NewsFilter(
            markets=[market],
            page_size=limit
        )
        return await self.fetch_news(filter_params, sources)
    
    async def search_news(
        self,
        keyword: str,
        limit: int = 50,
        sources: Optional[List[str]] = None
    ) -> List[UnifiedNewsItem]:
        """
        搜索新闻
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            sources: 指定数据源列表
            
        Returns:
            新闻列表
        """
        filter_params = NewsFilter(
            keyword=keyword,
            page_size=limit
        )
        return await self.fetch_news(filter_params, sources)
    
    async def get_statistics(
        self,
        filter_params: Optional[NewsFilter] = None
    ) -> NewsStatistics:
        """
        获取新闻统计信息
        
        Args:
            filter_params: 筛选参数
            
        Returns:
            统计信息
        """
        # 获取所有新闻（不分页）
        filter_params = filter_params or NewsFilter()
        filter_params.page_size = 1000  # 获取足够多的数据用于统计
        
        news_list = await self.fetch_news(filter_params)
        
        return NewsStatistics.from_news_list(news_list)
    
    async def health_check(self) -> Dict[str, bool]:
        """
        健康检查所有数据源
        
        Returns:
            各数据源的健康状态
        """
        results = {}
        
        for source_type, provider in self._providers.items():
            try:
                is_healthy = await provider.health_check()
                results[source_type] = is_healthy
            except Exception as e:
                logger.error(f"{source_type}健康检查失败: {e}")
                results[source_type] = False
        
        return results


# 全局单例
_manager_instance: Optional[NewsProviderManager] = None


def get_news_provider_manager(config: Optional[Dict[str, Any]] = None) -> NewsProviderManager:
    """
    获取新闻数据源管理器单例
    
    Args:
        config: 配置字典
        
    Returns:
        NewsProviderManager实例
    """
    global _manager_instance
    
    if _manager_instance is None:
        _manager_instance = NewsProviderManager(config)
    
    return _manager_instance