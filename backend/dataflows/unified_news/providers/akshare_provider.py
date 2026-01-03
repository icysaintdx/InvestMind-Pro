"""
AKShare新闻数据源提供者

整合AKShare提供的多个新闻接口：
- 东方财富个股新闻: ak.stock_news_em()
- 东方财富全球资讯: ak.stock_info_global_em()
- 财联社全球资讯: ak.stock_info_global_cls()
- 央视新闻: ak.news_cctv()
- 百度财经新闻: ak.news_economic_baidu()
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


class AKShareNewsProvider(BaseNewsProvider):
    """AKShare新闻数据源提供者"""
    
    name = "AKShare"
    source_type = SourceType.AKSHARE.value
    description = "整合东方财富、财联社、央视新闻、百度财经等多个免费数据源"
    supported_markets = [
        MarketType.A_SHARE.value,
        MarketType.GLOBAL.value,
        MarketType.DOMESTIC.value
    ]
    requires_api_key = False
    rate_limit_per_minute = 30
    
    # 子数据源配置
    SUB_SOURCES = {
        "eastmoney_stock": {
            "name": "东方财富个股",
            "method": "stock_news_em",
            "market": MarketType.A_SHARE.value,
            "news_type": NewsType.STOCK_NEWS.value
        },
        "eastmoney_global": {
            "name": "东方财富全球",
            "method": "stock_info_global_em",
            "market": MarketType.GLOBAL.value,
            "news_type": NewsType.MARKET_NEWS.value
        },
        "cls_global": {
            "name": "财联社",
            "method": "stock_info_global_cls",
            "market": MarketType.GLOBAL.value,
            "news_type": NewsType.MARKET_NEWS.value
        },
        "cctv": {
            "name": "央视新闻",
            "method": "news_cctv",
            "market": MarketType.DOMESTIC.value,
            "news_type": NewsType.POLICY.value
        },
        "baidu": {
            "name": "百度财经",
            "method": "news_economic_baidu",
            "market": MarketType.DOMESTIC.value,
            "news_type": NewsType.MARKET_NEWS.value
        }
    }
    
    def _initialize(self):
        """初始化AKShare"""
        try:
            import akshare as ak
            self._ak = ak
            self._is_available = True
            logger.info("AKShare新闻提供者初始化成功")
        except ImportError:
            self._is_available = False
            self._last_error = "akshare库未安装"
            logger.error("akshare库未安装，请运行: pip install akshare")
    
    async def fetch_news(
        self,
        stock_code: Optional[str] = None,
        keyword: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 50,
        sources: Optional[List[str]] = None
    ) -> List[UnifiedNewsItem]:
        """
        获取新闻列表
        
        Args:
            stock_code: 股票代码（可选）
            keyword: 关键词（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 返回数量限制
            sources: 指定子数据源列表（可选）
            
        Returns:
            统一格式的新闻列表
        """
        if not self._is_available:
            logger.warning(f"AKShare不可用: {self._last_error}")
            return []
        
        all_news = []
        
        # 如果指定了股票代码，优先获取个股新闻
        if stock_code:
            stock_news = await self._fetch_stock_news(stock_code, limit)
            all_news.extend(stock_news)
        else:
            # 获取各数据源的新闻
            source_list = sources or list(self.SUB_SOURCES.keys())
            
            for source_key in source_list:
                if source_key not in self.SUB_SOURCES:
                    continue
                
                try:
                    source_config = self.SUB_SOURCES[source_key]
                    news = await self._fetch_from_source(source_key, source_config, limit // len(source_list))
                    all_news.extend(news)
                except Exception as e:
                    logger.error(f"获取{source_key}新闻失败: {e}")
        
        # 按关键词过滤
        if keyword:
            all_news = [n for n in all_news if keyword in n.title or keyword in n.content]
        
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
    
    @retry_on_error(max_retries=2, delay=1.0)
    async def _fetch_stock_news(self, stock_code: str, limit: int) -> List[UnifiedNewsItem]:
        """获取个股新闻"""
        news_list = []
        
        try:
            # 标准化股票代码
            code = self._normalize_stock_code(stock_code)
            
            # 使用线程池执行同步API调用
            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None,
                lambda: self._ak.stock_news_em(symbol=code)
            )
            
            if df is not None and not df.empty:
                for _, row in df.head(limit).iterrows():
                    news = UnifiedNewsItem(
                        title=str(row.get('新闻标题', row.get('title', ''))),
                        content=str(row.get('新闻内容', row.get('content', ''))),
                        source="东方财富",
                        source_type=self.source_type,
                        original_url=str(row.get('新闻链接', row.get('url', ''))),
                        publish_time=self._parse_datetime(str(row.get('发布时间', row.get('datetime', '')))),
                        market=MarketType.A_SHARE.value,
                        news_type=NewsType.STOCK_NEWS.value,
                        related_stocks=[code]
                    )
                    news_list.append(news)
                    
            logger.info(f"获取{stock_code}个股新闻成功，共{len(news_list)}条")
            
        except Exception as e:
            logger.error(f"获取个股新闻失败: {e}")
            raise
        
        return news_list
    
    async def _fetch_from_source(
        self,
        source_key: str,
        source_config: Dict[str, Any],
        limit: int
    ) -> List[UnifiedNewsItem]:
        """从指定数据源获取新闻"""
        news_list = []
        
        try:
            method_name = source_config["method"]
            source_name = source_config["name"]
            market = source_config["market"]
            news_type = source_config["news_type"]
            
            # 获取AKShare方法
            method = getattr(self._ak, method_name, None)
            if not method:
                logger.warning(f"AKShare方法不存在: {method_name}")
                return []

            # 使用线程池执行同步API调用
            loop = asyncio.get_event_loop()

            if method_name == "news_cctv":
                # 央视新闻需要日期参数
                date_str = datetime.now().strftime("%Y%m%d")
                df = await loop.run_in_executor(
                    None,
                    lambda: method(date=date_str)
                )
            elif method_name == "news_economic_baidu":
                # 百度财经新闻需要日期参数
                date_str = datetime.now().strftime("%Y%m%d")
                df = await loop.run_in_executor(
                    None,
                    lambda: method(date=date_str)
                )
            else:
                df = await loop.run_in_executor(None, method)
            
            if df is not None and not df.empty:
                news_list = self._parse_dataframe(df, source_name, market, news_type, limit)
                logger.info(f"获取{source_name}新闻成功，共{len(news_list)}条")
            
        except Exception as e:
            logger.error(f"获取{source_key}新闻失败: {e}")
        
        return news_list
    
    def _parse_dataframe(
        self,
        df,
        source_name: str,
        market: str,
        news_type: str,
        limit: int
    ) -> List[UnifiedNewsItem]:
        """解析DataFrame为新闻列表"""
        news_list = []
        
        # 列名映射（不同接口的列名可能不同）
        title_cols = ['标题', '新闻标题', 'title', 'Title', '内容']
        content_cols = ['内容', '新闻内容', 'content', 'Content', '摘要']
        time_cols = ['发布时间', '时间', 'datetime', 'date', 'time', 'Date', 'Time', '日期']
        url_cols = ['链接', '新闻链接', 'url', 'URL', 'link']
        
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
            
            news = UnifiedNewsItem(
                title=title,
                content=content,
                source=source_name,
                source_type=self.source_type,
                original_url=url,
                publish_time=self._parse_datetime(time_str),
                market=market,
                news_type=news_type,
                related_stocks=self._extract_stock_codes(title + content),
                keywords=self._extract_keywords(title + content)
            )
            news_list.append(news)
        
        return news_list
    
    async def fetch_eastmoney_stock_news(self, stock_code: str, limit: int = 50) -> List[UnifiedNewsItem]:
        """获取东方财富个股新闻"""
        return await self._fetch_stock_news(stock_code, limit)
    
    async def fetch_eastmoney_global_news(self, limit: int = 50) -> List[UnifiedNewsItem]:
        """获取东方财富全球资讯"""
        return await self._fetch_from_source(
            "eastmoney_global",
            self.SUB_SOURCES["eastmoney_global"],
            limit
        )
    
    async def fetch_cls_news(self, limit: int = 50) -> List[UnifiedNewsItem]:
        """获取财联社新闻"""
        return await self._fetch_from_source(
            "cls_global",
            self.SUB_SOURCES["cls_global"],
            limit
        )
    
    async def fetch_cctv_news(self, limit: int = 50) -> List[UnifiedNewsItem]:
        """获取央视新闻"""
        return await self._fetch_from_source(
            "cctv",
            self.SUB_SOURCES["cctv"],
            limit
        )
    
    async def fetch_baidu_news(self, limit: int = 50) -> List[UnifiedNewsItem]:
        """获取百度财经新闻"""
        return await self._fetch_from_source(
            "baidu",
            self.SUB_SOURCES["baidu"],
            limit
        )
    
    def get_available_sources(self) -> List[Dict[str, str]]:
        """获取可用的子数据源列表"""
        return [
            {
                "key": key,
                "name": config["name"],
                "market": config["market"],
                "news_type": config["news_type"]
            }
            for key, config in self.SUB_SOURCES.items()
        ]