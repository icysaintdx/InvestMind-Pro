"""
统一新闻模块

整合多个数据源的新闻获取接口，提供统一的新闻服务。

数据源包括：
- AKShare: 东方财富、财联社、央视新闻、百度财经
- 问财: pywencai智能查询
- Tushare: 需要5000积分
- FinnHub: 美股/港股实时新闻
- Alpha Vantage: 美股新闻含情绪分析
- NewsAPI: 全球新闻关键词搜索
- Google新闻: 备用方案
"""

from .models import UnifiedNewsItem, NewsStatistics, UnifiedNewsResponse
from .provider_manager import NewsProviderManager
from .news_service import UnifiedNewsService

__all__ = [
    'UnifiedNewsItem',
    'NewsStatistics', 
    'UnifiedNewsResponse',
    'NewsProviderManager',
    'UnifiedNewsService'
]