"""
问财新闻数据源提供者

使用pywencai库获取问财的新闻和公告数据。
支持智能查询，可以通过自然语言获取相关新闻。
"""

import asyncio
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging

from ..base_provider import BaseNewsProvider, retry_on_error
from ..models import (
    UnifiedNewsItem,
    MarketType,
    NewsType,
    SourceType,
    SentimentLabel
)

logger = logging.getLogger(__name__)


class WencaiNewsProvider(BaseNewsProvider):
    """问财新闻数据源提供者"""
    
    name = "问财"
    source_type = SourceType.WENCAI.value
    description = "同花顺问财智能查询，支持自然语言搜索新闻和公告"
    supported_markets = [MarketType.A_SHARE.value]
    requires_api_key = False
    rate_limit_per_minute = 20  # 问财有较严格的限制
    
    def _initialize(self):
        """初始化pywencai"""
        try:
            import pywencai
            self._wencai = pywencai
            self._is_available = True
            logger.info("问财新闻提供者初始化成功")
        except ImportError:
            self._is_available = False
            self._last_error = "pywencai库未安装"
            logger.error("pywencai库未安装，请运行: pip install pywencai")
    
    async def fetch_news(
        self,
        stock_code: Optional[str] = None,
        keyword: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50
    ) -> List[UnifiedNewsItem]:
        """
        获取新闻列表
        
        Args:
            stock_code: 股票代码（可选）
            keyword: 关键词/查询语句（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 返回数量限制
            
        Returns:
            统一格式的新闻列表
        """
        if not self._is_available:
            logger.warning(f"问财不可用: {self._last_error}")
            return []
        
        all_news = []
        
        try:
            # 构建查询语句
            if stock_code:
                # 个股新闻查询
                query = f"{stock_code}最新新闻"
                news = await self._fetch_by_query(query, limit)
                all_news.extend(news)
                
                # 个股公告查询
                query = f"{stock_code}最新公告"
                announcements = await self._fetch_by_query(query, limit // 2)
                all_news.extend(announcements)
            elif keyword:
                # 关键词查询
                query = f"{keyword}相关新闻"
                news = await self._fetch_by_query(query, limit)
                all_news.extend(news)
            else:
                # 默认获取市场要闻
                queries = [
                    "今日重大新闻",
                    "今日涨停股新闻",
                    "今日热点板块新闻"
                ]
                for query in queries:
                    news = await self._fetch_by_query(query, limit // len(queries))
                    all_news.extend(news)
            
            # 按时间过滤
            if start_date:
                all_news = [n for n in all_news if n.publish_time and n.publish_time >= start_date]
            if end_date:
                all_news = [n for n in all_news if n.publish_time and n.publish_time <= end_date]
            
            # 按时间排序
            all_news.sort(key=lambda x: x.publish_time or datetime.min, reverse=True)
            
            # 去重
            seen_titles = set()
            unique_news = []
            for news in all_news:
                if news.title not in seen_titles:
                    seen_titles.add(news.title)
                    unique_news.append(news)
            
            self._last_update = datetime.now()
            
            return unique_news[:limit]
            
        except Exception as e:
            logger.error(f"问财获取新闻失败: {e}")
            self._last_error = str(e)
            return []
    
    @retry_on_error(max_retries=2, delay=2.0)
    async def _fetch_by_query(self, query: str, limit: int) -> List[UnifiedNewsItem]:
        """
        通过查询语句获取新闻
        
        Args:
            query: 问财查询语句
            limit: 返回数量限制
            
        Returns:
            新闻列表
        """
        news_list = []
        
        try:
            # 检查缓存
            cache_key = self._get_cache_key("query", query=query, limit=limit)
            cached = self._get_from_cache(cache_key)
            if cached:
                return cached
            
            # 使用线程池执行同步API调用
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                lambda: self._wencai.get(query=query, query_type="news")
            )
            
            if result is not None:
                if isinstance(result, dict):
                    # 处理字典格式的返回
                    news_list = self._parse_dict_result(result, limit)
                elif hasattr(result, 'iterrows'):
                    # 处理DataFrame格式的返回
                    news_list = self._parse_dataframe_result(result, limit)
                elif isinstance(result, list):
                    # 处理列表格式的返回
                    news_list = self._parse_list_result(result, limit)
            
            # 设置缓存
            if news_list:
                self._set_cache(cache_key, news_list)
            
            logger.info(f"问财查询'{query}'成功，共{len(news_list)}条")
            
        except Exception as e:
            logger.error(f"问财查询'{query}'失败: {e}")
            raise
        
        return news_list
    
    def _parse_dict_result(self, result: Dict, limit: int) -> List[UnifiedNewsItem]:
        """解析字典格式的结果"""
        news_list = []
        
        # 尝试从不同的键获取数据
        data = result.get('data', result.get('news', result.get('result', [])))
        
        if isinstance(data, list):
            for item in data[:limit]:
                if isinstance(item, dict):
                    news = self._create_news_item(item)
                    if news:
                        news_list.append(news)
        
        return news_list
    
    def _parse_dataframe_result(self, df, limit: int) -> List[UnifiedNewsItem]:
        """解析DataFrame格式的结果"""
        news_list = []
        
        # 列名映射
        title_cols = ['标题', '新闻标题', 'title', '内容']
        content_cols = ['内容', '新闻内容', 'content', '摘要', '详情']
        time_cols = ['发布时间', '时间', 'datetime', 'date', '日期']
        url_cols = ['链接', '新闻链接', 'url', '详情链接']
        stock_cols = ['股票代码', '代码', 'code', '相关股票']
        
        def get_col_value(row, col_names, default=''):
            for col in col_names:
                if col in row.index and row[col]:
                    return str(row[col])
            return default
        
        for _, row in df.head(limit).iterrows():
            title = get_col_value(row, title_cols)
            if not title:
                continue
            
            content = get_col_value(row, content_cols)
            time_str = get_col_value(row, time_cols)
            url = get_col_value(row, url_cols)
            stock_code = get_col_value(row, stock_cols)
            
            related_stocks = []
            if stock_code:
                related_stocks = [self._normalize_stock_code(stock_code)]
            related_stocks.extend(self._extract_stock_codes(title + content))
            related_stocks = list(set(related_stocks))
            
            news = UnifiedNewsItem(
                title=title,
                content=content,
                source="问财",
                source_type=self.source_type,
                original_url=url,
                publish_time=self._parse_datetime(time_str),
                market=MarketType.A_SHARE.value,
                news_type=self._detect_news_type(title),
                related_stocks=related_stocks,
                keywords=self._extract_keywords(title + content)
            )
            news_list.append(news)
        
        return news_list
    
    def _parse_list_result(self, result: List, limit: int) -> List[UnifiedNewsItem]:
        """解析列表格式的结果"""
        news_list = []
        
        for item in result[:limit]:
            if isinstance(item, dict):
                news = self._create_news_item(item)
                if news:
                    news_list.append(news)
            elif isinstance(item, str):
                # 如果是纯字符串，作为标题处理
                news = UnifiedNewsItem(
                    title=item,
                    source="问财",
                    source_type=self.source_type,
                    market=MarketType.A_SHARE.value,
                    news_type=NewsType.MARKET_NEWS.value
                )
                news_list.append(news)
        
        return news_list
    
    def _create_news_item(self, item: Dict) -> Optional[UnifiedNewsItem]:
        """从字典创建新闻项"""
        # 尝试获取标题
        title = (
            item.get('title') or 
            item.get('标题') or 
            item.get('新闻标题') or
            item.get('content', '')[:100]
        )
        
        if not title:
            return None
        
        content = item.get('content') or item.get('内容') or item.get('新闻内容') or ''
        time_str = item.get('datetime') or item.get('发布时间') or item.get('时间') or ''
        url = item.get('url') or item.get('链接') or item.get('新闻链接') or ''
        stock_code = item.get('code') or item.get('股票代码') or item.get('代码') or ''
        
        related_stocks = []
        if stock_code:
            related_stocks = [self._normalize_stock_code(stock_code)]
        related_stocks.extend(self._extract_stock_codes(title + content))
        related_stocks = list(set(related_stocks))
        
        return UnifiedNewsItem(
            title=title,
            content=content,
            source="问财",
            source_type=self.source_type,
            original_url=url,
            publish_time=self._parse_datetime(time_str),
            market=MarketType.A_SHARE.value,
            news_type=self._detect_news_type(title),
            related_stocks=related_stocks,
            keywords=self._extract_keywords(title + content)
        )
    
    def _detect_news_type(self, title: str) -> str:
        """根据标题检测新闻类型"""
        if not title:
            return NewsType.MARKET_NEWS.value
        
        # 公告类
        if any(kw in title for kw in ['公告', '披露', '报告', '年报', '季报', '快报']):
            return NewsType.ANNOUNCEMENT.value
        
        # 研报类
        if any(kw in title for kw in ['研报', '研究', '评级', '目标价', '买入', '增持']):
            return NewsType.RESEARCH_REPORT.value
        
        # 政策类
        if any(kw in title for kw in ['政策', '监管', '证监会', '央行', '国务院']):
            return NewsType.POLICY.value
        
        # 行业类
        if any(kw in title for kw in ['行业', '板块', '概念', '题材']):
            return NewsType.INDUSTRY.value
        
        # 公司类
        if any(kw in title for kw in ['公司', '企业', '集团', '股份']):
            return NewsType.COMPANY.value
        
        return NewsType.MARKET_NEWS.value
    
    async def fetch_stock_news(self, stock_code: str, limit: int = 50) -> List[UnifiedNewsItem]:
        """获取个股新闻"""
        return await self.fetch_news(stock_code=stock_code, limit=limit)
    
    async def fetch_announcements(self, stock_code: str, limit: int = 50) -> List[UnifiedNewsItem]:
        """获取个股公告"""
        if not self._is_available:
            return []
        
        query = f"{stock_code}最新公告"
        return await self._fetch_by_query(query, limit)
    
    async def search_news(self, keyword: str, limit: int = 50) -> List[UnifiedNewsItem]:
        """搜索新闻"""
        return await self.fetch_news(keyword=keyword, limit=limit)
    
    async def fetch_hot_news(self, limit: int = 50) -> List[UnifiedNewsItem]:
        """获取热点新闻"""
        if not self._is_available:
            return []
        
        queries = [
            "今日涨停股新闻",
            "今日热点板块",
            "今日重大利好"
        ]
        
        all_news = []
        for query in queries:
            news = await self._fetch_by_query(query, limit // len(queries))
            all_news.extend(news)
        
        # 去重并排序
        seen_titles = set()
        unique_news = []
        for news in all_news:
            if news.title not in seen_titles:
                seen_titles.add(news.title)
                unique_news.append(news)
        
        unique_news.sort(key=lambda x: x.publish_time or datetime.min, reverse=True)
        
        return unique_news[:limit]