"""
统一新闻数据模型

定义新闻数据的统一格式，支持多数据源的数据标准化。
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Dict, Optional, Any
from enum import Enum
import hashlib
import json


class MarketType(str, Enum):
    """市场类型"""
    A_SHARE = "A股"
    HK_STOCK = "港股"
    US_STOCK = "美股"
    GLOBAL = "全球"
    DOMESTIC = "国内"


class NewsType(str, Enum):
    """新闻类型"""
    STOCK_NEWS = "个股新闻"
    MARKET_NEWS = "市场要闻"
    ANNOUNCEMENT = "公告"
    RESEARCH_REPORT = "研报"
    POLICY = "政策"
    INDUSTRY = "行业"
    MACRO = "宏观"
    COMPANY = "公司"


class SourceType(str, Enum):
    """数据源类型"""
    AKSHARE = "akshare"
    WENCAI = "wencai"
    TUSHARE = "tushare"
    FINNHUB = "finnhub"
    ALPHA_VANTAGE = "alpha_vantage"
    NEWSAPI = "newsapi"
    GOOGLE = "google"


class SentimentLabel(str, Enum):
    """情绪标签"""
    POSITIVE = "积极"
    NEUTRAL = "中性"
    NEGATIVE = "消极"


class UrgencyLevel(str, Enum):
    """紧急程度"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


@dataclass
class UnifiedNewsItem:
    """统一新闻数据项"""
    
    # 基础信息
    title: str                                    # 新闻标题
    content: str = ""                             # 新闻内容
    summary: str = ""                             # 新闻摘要
    
    # 来源信息
    source: str = ""                              # 数据源名称（如：东方财富、财联社）
    source_type: str = SourceType.AKSHARE.value   # 数据源类型
    original_url: str = ""                        # 原始链接
    
    # 时间信息
    publish_time: Optional[datetime] = None       # 发布时间
    fetch_time: datetime = field(default_factory=datetime.now)  # 获取时间
    
    # 分类信息
    market: str = MarketType.A_SHARE.value        # 市场
    news_type: str = NewsType.MARKET_NEWS.value   # 类型
    category: str = ""                            # 分类
    
    # 关联信息
    related_stocks: List[str] = field(default_factory=list)  # 相关股票代码
    keywords: List[str] = field(default_factory=list)        # 关键词
    
    # 分析信息
    sentiment_score: float = 0.0                  # 情绪分数 -1到1
    sentiment_label: str = SentimentLabel.NEUTRAL.value  # 情绪标签
    urgency: str = UrgencyLevel.LOW.value         # 紧急程度
    relevance_score: float = 0.0                  # 相关性分数
    
    # 唯一标识（自动生成）
    id: str = field(default="")
    
    def __post_init__(self):
        """初始化后处理"""
        if not self.id:
            self.id = self._generate_id()
        if not self.summary and self.content:
            self.summary = self.content[:200] + "..." if len(self.content) > 200 else self.content
    
    def _generate_id(self) -> str:
        """生成唯一ID"""
        content = f"{self.title}_{self.source}_{self.publish_time}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "summary": self.summary,
            "source": self.source,
            "source_type": self.source_type,
            "original_url": self.original_url,
            "publish_time": self.publish_time.isoformat() if self.publish_time else None,
            "fetch_time": self.fetch_time.isoformat() if self.fetch_time else None,
            "market": self.market,
            "news_type": self.news_type,
            "category": self.category,
            "related_stocks": self.related_stocks,
            "keywords": self.keywords,
            "sentiment_score": self.sentiment_score,
            "sentiment_label": self.sentiment_label,
            "urgency": self.urgency,
            "relevance_score": self.relevance_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UnifiedNewsItem":
        """从字典创建"""
        # 处理时间字段
        if data.get("publish_time") and isinstance(data["publish_time"], str):
            data["publish_time"] = datetime.fromisoformat(data["publish_time"])
        if data.get("fetch_time") and isinstance(data["fetch_time"], str):
            data["fetch_time"] = datetime.fromisoformat(data["fetch_time"])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NewsStatistics:
    """新闻统计信息"""
    
    total_count: int = 0                          # 总数量
    by_market: Dict[str, int] = field(default_factory=dict)    # 按市场统计
    by_source: Dict[str, int] = field(default_factory=dict)    # 按数据源统计
    by_type: Dict[str, int] = field(default_factory=dict)      # 按类型统计
    by_sentiment: Dict[str, int] = field(default_factory=dict) # 按情绪统计
    time_range: Dict[str, str] = field(default_factory=dict)   # 时间范围
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "total_count": self.total_count,
            "by_market": self.by_market,
            "by_source": self.by_source,
            "by_type": self.by_type,
            "by_sentiment": self.by_sentiment,
            "time_range": self.time_range
        }
    
    @classmethod
    def from_news_list(cls, news_list: List[UnifiedNewsItem]) -> "NewsStatistics":
        """从新闻列表生成统计信息"""
        stats = cls()
        stats.total_count = len(news_list)
        
        for news in news_list:
            # 按市场统计
            stats.by_market[news.market] = stats.by_market.get(news.market, 0) + 1
            # 按数据源统计
            stats.by_source[news.source] = stats.by_source.get(news.source, 0) + 1
            # 按类型统计
            stats.by_type[news.news_type] = stats.by_type.get(news.news_type, 0) + 1
            # 按情绪统计
            stats.by_sentiment[news.sentiment_label] = stats.by_sentiment.get(news.sentiment_label, 0) + 1
        
        # 计算时间范围
        if news_list:
            times = [n.publish_time for n in news_list if n.publish_time]
            if times:
                stats.time_range = {
                    "start": min(times).isoformat(),
                    "end": max(times).isoformat()
                }
        
        return stats


@dataclass
class UnifiedNewsResponse:
    """统一新闻API响应"""
    
    success: bool = True
    message: str = ""
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    filters: Dict[str, Any] = field(default_factory=dict)
    news_items: List[UnifiedNewsItem] = field(default_factory=list)
    statistics: Optional[NewsStatistics] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "success": self.success,
            "message": self.message,
            "total_count": self.total_count,
            "page": self.page,
            "page_size": self.page_size,
            "filters": self.filters,
            "news_items": [item.to_dict() for item in self.news_items],
            "statistics": self.statistics.to_dict() if self.statistics else None
        }


@dataclass
class NewsFilter:
    """新闻筛选条件"""
    
    markets: List[str] = field(default_factory=list)      # 市场筛选
    sources: List[str] = field(default_factory=list)      # 数据源筛选
    news_types: List[str] = field(default_factory=list)   # 类型筛选
    sentiments: List[str] = field(default_factory=list)   # 情绪筛选
    stock_code: str = ""                                   # 股票代码
    keyword: str = ""                                      # 关键词
    start_date: Optional[datetime] = None                  # 开始日期
    end_date: Optional[datetime] = None                    # 结束日期
    page: int = 1                                          # 页码
    page_size: int = 20                                    # 每页数量
    sort_by: str = "publish_time"                          # 排序字段
    sort_order: str = "desc"                               # 排序方向
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "markets": self.markets,
            "sources": self.sources,
            "news_types": self.news_types,
            "sentiments": self.sentiments,
            "stock_code": self.stock_code,
            "keyword": self.keyword,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "page": self.page,
            "page_size": self.page_size,
            "sort_by": self.sort_by,
            "sort_order": self.sort_order
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "NewsFilter":
        """从字典创建"""
        # 处理时间字段
        if data.get("start_date") and isinstance(data["start_date"], str):
            data["start_date"] = datetime.fromisoformat(data["start_date"])
        if data.get("end_date") and isinstance(data["end_date"], str):
            data["end_date"] = datetime.fromisoformat(data["end_date"])
        
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class NewsSourceInfo:
    """新闻数据源信息"""
    
    name: str                                     # 数据源名称
    source_type: str                              # 数据源类型
    description: str = ""                         # 描述
    supported_markets: List[str] = field(default_factory=list)  # 支持的市场
    requires_api_key: bool = False                # 是否需要API密钥
    is_available: bool = True                     # 是否可用
    rate_limit: int = 0                           # 速率限制（每分钟请求数）
    last_update: Optional[datetime] = None        # 最后更新时间
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "name": self.name,
            "source_type": self.source_type,
            "description": self.description,
            "supported_markets": self.supported_markets,
            "requires_api_key": self.requires_api_key,
            "is_available": self.is_available,
            "rate_limit": self.rate_limit,
            "last_update": self.last_update.isoformat() if self.last_update else None
        }