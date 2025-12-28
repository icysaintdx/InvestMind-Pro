"""
统一新闻服务

提供统一的新闻获取、缓存、情绪分析等功能。
作为API层和数据获取层之间的桥梁。
"""

import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
import logging
import json
from functools import lru_cache

from .provider_manager import NewsProviderManager, get_news_provider_manager
from .models import (
    UnifiedNewsItem,
    UnifiedNewsResponse,
    NewsStatistics,
    NewsFilter,
    NewsSourceInfo,
    MarketType,
    NewsType,
    SentimentLabel
)

logger = logging.getLogger(__name__)


class NewsCacheService:
    """新闻缓存服务"""
    
    def __init__(self, ttl: int = 300):
        """
        初始化缓存服务
        
        Args:
            ttl: 缓存有效期（秒），默认5分钟
        """
        self._cache: Dict[str, tuple] = {}  # {key: (data, timestamp)}
        self._ttl = ttl
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if key in self._cache:
            data, timestamp = self._cache[key]
            if datetime.now().timestamp() - timestamp < self._ttl:
                return data
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, data: Any):
        """设置缓存"""
        self._cache[key] = (data, datetime.now().timestamp())
    
    def delete(self, key: str):
        """删除缓存"""
        if key in self._cache:
            del self._cache[key]
    
    def clear(self):
        """清空缓存"""
        self._cache.clear()
    
    def cleanup(self):
        """清理过期缓存"""
        now = datetime.now().timestamp()
        expired_keys = [
            key for key, (_, timestamp) in self._cache.items()
            if now - timestamp >= self._ttl
        ]
        for key in expired_keys:
            del self._cache[key]


class SentimentAnalyzer:
    """情绪分析服务"""
    
    # 积极词汇
    POSITIVE_WORDS = [
        '涨停', '大涨', '暴涨', '利好', '突破', '新高', '增长', '盈利',
        '超预期', '买入', '增持', '推荐', '看好', '强势', '反弹', '回升',
        '创新高', '放量', '主力', '资金流入', '北向资金', '加仓'
    ]
    
    # 消极词汇
    NEGATIVE_WORDS = [
        '跌停', '大跌', '暴跌', '利空', '破位', '新低', '下滑', '亏损',
        '不及预期', '卖出', '减持', '回避', '看空', '弱势', '下跌', '回落',
        '创新低', '缩量', '出货', '资金流出', '外资撤离', '减仓', '爆雷'
    ]
    
    def analyze(self, text: str) -> tuple:
        """
        分析文本情绪
        
        Args:
            text: 待分析文本
            
        Returns:
            (情绪分数, 情绪标签) 分数范围-1到1
        """
        if not text:
            return 0.0, SentimentLabel.NEUTRAL.value
        
        text_lower = text.lower()
        
        # 计算积极和消极词汇出现次数
        positive_count = sum(1 for word in self.POSITIVE_WORDS if word in text_lower)
        negative_count = sum(1 for word in self.NEGATIVE_WORDS if word in text_lower)
        
        total = positive_count + negative_count
        if total == 0:
            return 0.0, SentimentLabel.NEUTRAL.value
        
        # 计算情绪分数
        score = (positive_count - negative_count) / total
        
        # 确定情绪标签
        if score > 0.2:
            label = SentimentLabel.POSITIVE.value
        elif score < -0.2:
            label = SentimentLabel.NEGATIVE.value
        else:
            label = SentimentLabel.NEUTRAL.value
        
        return round(score, 2), label
    
    def analyze_batch(self, news_list: List[UnifiedNewsItem]) -> List[UnifiedNewsItem]:
        """
        批量分析新闻情绪
        
        Args:
            news_list: 新闻列表
            
        Returns:
            添加了情绪分析结果的新闻列表
        """
        for news in news_list:
            text = f"{news.title} {news.content}"
            score, label = self.analyze(text)
            news.sentiment_score = score
            news.sentiment_label = label
        
        return news_list


class UnifiedNewsService:
    """统一新闻服务"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化新闻服务
        
        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._provider_manager = get_news_provider_manager(config)
        self._cache = NewsCacheService(ttl=self.config.get('cache_ttl', 300))
        self._sentiment_analyzer = SentimentAnalyzer()
        
        logger.info("统一新闻服务初始化完成")
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        import hashlib
        key_data = f"{method}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get_news_list(
        self,
        markets: Optional[List[str]] = None,
        sources: Optional[List[str]] = None,
        news_types: Optional[List[str]] = None,
        sentiments: Optional[List[str]] = None,
        stock_code: Optional[str] = None,
        keyword: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        page: int = 1,
        page_size: int = 20,
        sort_by: str = "publish_time",
        sort_order: str = "desc",
        use_cache: bool = True
    ) -> UnifiedNewsResponse:
        """
        获取新闻列表
        
        Args:
            markets: 市场筛选
            sources: 数据源筛选
            news_types: 类型筛选
            sentiments: 情绪筛选
            stock_code: 股票代码
            keyword: 关键词
            start_date: 开始日期
            end_date: 结束日期
            page: 页码
            page_size: 每页数量
            sort_by: 排序字段
            sort_order: 排序方向
            use_cache: 是否使用缓存
            
        Returns:
            统一新闻响应
        """
        try:
            # 构建筛选参数
            filter_params = NewsFilter(
                markets=markets or [],
                sources=sources or [],
                news_types=news_types or [],
                sentiments=sentiments or [],
                stock_code=stock_code or "",
                keyword=keyword or "",
                start_date=start_date,
                end_date=end_date,
                page=page,
                page_size=page_size,
                sort_by=sort_by,
                sort_order=sort_order
            )
            
            # 检查缓存
            cache_key = self._get_cache_key("news_list", **filter_params.to_dict())
            if use_cache:
                cached = self._cache.get(cache_key)
                if cached:
                    logger.debug(f"命中缓存: {cache_key}")
                    return cached
            
            # 获取新闻
            news_list = await self._provider_manager.fetch_news(filter_params, sources)
            
            # 情绪分析
            news_list = self._sentiment_analyzer.analyze_batch(news_list)
            
            # 如果有情绪筛选，再次过滤
            if sentiments:
                news_list = [n for n in news_list if n.sentiment_label in sentiments]
            
            # 计算统计信息
            statistics = NewsStatistics.from_news_list(news_list)
            
            # 构建响应
            response = UnifiedNewsResponse(
                success=True,
                message="获取成功",
                total_count=len(news_list),
                page=page,
                page_size=page_size,
                filters=filter_params.to_dict(),
                news_items=news_list,
                statistics=statistics
            )
            
            # 设置缓存
            if use_cache:
                self._cache.set(cache_key, response)
            
            return response
            
        except Exception as e:
            logger.error(f"获取新闻列表失败: {e}")
            return UnifiedNewsResponse(
                success=False,
                message=f"获取失败: {str(e)}",
                total_count=0,
                page=page,
                page_size=page_size
            )
    
    async def get_stock_news(
        self,
        stock_code: str,
        limit: int = 50,
        use_cache: bool = True
    ) -> UnifiedNewsResponse:
        """
        获取个股新闻
        
        Args:
            stock_code: 股票代码
            limit: 返回数量限制
            use_cache: 是否使用缓存
            
        Returns:
            统一新闻响应
        """
        return await self.get_news_list(
            stock_code=stock_code,
            page_size=limit,
            use_cache=use_cache
        )
    
    async def get_market_news(
        self,
        market: str = MarketType.A_SHARE.value,
        limit: int = 50,
        use_cache: bool = True
    ) -> UnifiedNewsResponse:
        """
        获取市场新闻
        
        Args:
            market: 市场类型
            limit: 返回数量限制
            use_cache: 是否使用缓存
            
        Returns:
            统一新闻响应
        """
        return await self.get_news_list(
            markets=[market],
            page_size=limit,
            use_cache=use_cache
        )
    
    async def get_realtime_news(
        self,
        limit: int = 20
    ) -> UnifiedNewsResponse:
        """
        获取实时新闻
        
        Args:
            limit: 返回数量限制
            
        Returns:
            统一新闻响应
        """
        # 实时新闻不使用缓存
        return await self.get_news_list(
            page_size=limit,
            sort_by="publish_time",
            sort_order="desc",
            use_cache=False
        )
    
    async def search_news(
        self,
        keyword: str,
        limit: int = 50,
        use_cache: bool = True
    ) -> UnifiedNewsResponse:
        """
        搜索新闻
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            use_cache: 是否使用缓存
            
        Returns:
            统一新闻响应
        """
        return await self.get_news_list(
            keyword=keyword,
            page_size=limit,
            use_cache=use_cache
        )
    
    async def get_sources(self) -> List[NewsSourceInfo]:
        """
        获取可用数据源列表
        
        Returns:
            数据源信息列表
        """
        return self._provider_manager.get_sources_info()
    
    async def get_statistics(
        self,
        markets: Optional[List[str]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> NewsStatistics:
        """
        获取新闻统计信息
        
        Args:
            markets: 市场筛选
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            统计信息
        """
        filter_params = NewsFilter(
            markets=markets or [],
            start_date=start_date,
            end_date=end_date,
            page_size=1000
        )
        
        return await self._provider_manager.get_statistics(filter_params)
    
    async def get_sentiment_analysis(
        self,
        stock_code: Optional[str] = None,
        market: Optional[str] = None,
        days: int = 7
    ) -> Dict[str, Any]:
        """
        获取情绪分析结果
        
        Args:
            stock_code: 股票代码
            market: 市场类型
            days: 分析天数
            
        Returns:
            情绪分析结果
        """
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 获取新闻
        response = await self.get_news_list(
            stock_code=stock_code,
            markets=[market] if market else None,
            start_date=start_date,
            end_date=end_date,
            page_size=500
        )
        
        if not response.success or not response.news_items:
            return {
                "success": False,
                "message": "没有足够的新闻数据",
                "data": None
            }
        
        news_list = response.news_items
        
        # 计算情绪统计
        sentiment_counts = {
            SentimentLabel.POSITIVE.value: 0,
            SentimentLabel.NEUTRAL.value: 0,
            SentimentLabel.NEGATIVE.value: 0
        }
        
        total_score = 0.0
        for news in news_list:
            sentiment_counts[news.sentiment_label] = sentiment_counts.get(news.sentiment_label, 0) + 1
            total_score += news.sentiment_score
        
        avg_score = total_score / len(news_list) if news_list else 0
        
        # 按日期统计情绪趋势
        daily_sentiment = {}
        for news in news_list:
            if news.publish_time:
                date_str = news.publish_time.strftime("%Y-%m-%d")
                if date_str not in daily_sentiment:
                    daily_sentiment[date_str] = {"scores": [], "count": 0}
                daily_sentiment[date_str]["scores"].append(news.sentiment_score)
                daily_sentiment[date_str]["count"] += 1
        
        # 计算每日平均情绪
        daily_avg = {
            date: {
                "avg_score": sum(data["scores"]) / len(data["scores"]),
                "count": data["count"]
            }
            for date, data in daily_sentiment.items()
        }
        
        return {
            "success": True,
            "message": "分析完成",
            "data": {
                "total_news": len(news_list),
                "avg_sentiment_score": round(avg_score, 3),
                "sentiment_distribution": sentiment_counts,
                "daily_sentiment": daily_avg,
                "period": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                    "days": days
                }
            }
        }
    
    async def sync_news(
        self,
        sources: Optional[List[str]] = None,
        force: bool = False
    ) -> Dict[str, Any]:
        """
        手动触发新闻同步
        
        Args:
            sources: 指定数据源
            force: 是否强制刷新（忽略缓存）
            
        Returns:
            同步结果
        """
        try:
            # 清除缓存
            if force:
                self._cache.clear()
            
            # 获取最新新闻
            response = await self.get_news_list(
                sources=sources,
                page_size=100,
                use_cache=False
            )
            
            return {
                "success": True,
                "message": f"同步完成，获取{response.total_count}条新闻",
                "total_count": response.total_count,
                "sources": sources or "all"
            }
            
        except Exception as e:
            logger.error(f"新闻同步失败: {e}")
            return {
                "success": False,
                "message": f"同步失败: {str(e)}",
                "total_count": 0
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        健康检查
        
        Returns:
            健康状态
        """
        source_status = await self._provider_manager.health_check()
        
        available_count = sum(1 for v in source_status.values() if v)
        total_count = len(source_status)
        
        return {
            "status": "healthy" if available_count > 0 else "unhealthy",
            "available_sources": available_count,
            "total_sources": total_count,
            "source_status": source_status
        }


# 全局单例
_service_instance: Optional[UnifiedNewsService] = None


def get_unified_news_service(config: Optional[Dict[str, Any]] = None) -> UnifiedNewsService:
    """
    获取统一新闻服务单例
    
    Args:
        config: 配置字典
        
    Returns:
        UnifiedNewsService实例
    """
    global _service_instance
    
    if _service_instance is None:
        _service_instance = UnifiedNewsService(config)
    
    return _service_instance