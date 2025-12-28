"""
新闻数据源基类

定义所有新闻数据源提供者的基础接口和通用功能。
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import List, Dict, Optional, Any
import logging
import asyncio
from functools import wraps
import time

from .models import (
    UnifiedNewsItem, 
    NewsSourceInfo, 
    MarketType, 
    NewsType,
    SourceType
)


logger = logging.getLogger(__name__)


def rate_limit(calls_per_minute: int = 60):
    """速率限制装饰器"""
    min_interval = 60.0 / calls_per_minute
    last_call = [0.0]
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_call[0]
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            last_call[0] = time.time()
            return await func(*args, **kwargs)
        return wrapper
    return decorator


def retry_on_error(max_retries: int = 3, delay: float = 1.0):
    """错误重试装饰器"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    logger.warning(f"尝试 {attempt + 1}/{max_retries} 失败: {e}")
                    if attempt < max_retries - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator


class BaseNewsProvider(ABC):
    """新闻数据源基类"""
    
    # 子类需要覆盖的属性
    name: str = "BaseProvider"
    source_type: str = SourceType.AKSHARE.value
    description: str = "基础新闻提供者"
    supported_markets: List[str] = [MarketType.A_SHARE.value]
    requires_api_key: bool = False
    rate_limit_per_minute: int = 60
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化数据源提供者
        
        Args:
            config: 配置字典，可包含API密钥等信息
        """
        self.config = config or {}
        self._is_available = True
        self._last_error: Optional[str] = None
        self._last_update: Optional[datetime] = None
        self._cache: Dict[str, Any] = {}
        self._cache_ttl: int = 300  # 缓存有效期（秒）
        
        # 初始化
        self._initialize()
    
    def _initialize(self):
        """初始化钩子，子类可覆盖"""
        pass
    
    @property
    def is_available(self) -> bool:
        """检查数据源是否可用"""
        return self._is_available
    
    @property
    def last_error(self) -> Optional[str]:
        """获取最后一次错误信息"""
        return self._last_error
    
    def get_source_info(self) -> NewsSourceInfo:
        """获取数据源信息"""
        return NewsSourceInfo(
            name=self.name,
            source_type=self.source_type,
            description=self.description,
            supported_markets=self.supported_markets,
            requires_api_key=self.requires_api_key,
            is_available=self._is_available,
            rate_limit=self.rate_limit_per_minute,
            last_update=self._last_update
        )
    
    def _get_cache_key(self, method: str, **kwargs) -> str:
        """生成缓存键"""
        import hashlib
        import json
        key_data = f"{self.name}:{method}:{json.dumps(kwargs, sort_keys=True, default=str)}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Any]:
        """从缓存获取数据"""
        if cache_key in self._cache:
            data, timestamp = self._cache[cache_key]
            if time.time() - timestamp < self._cache_ttl:
                return data
            else:
                del self._cache[cache_key]
        return None
    
    def _set_cache(self, cache_key: str, data: Any):
        """设置缓存"""
        self._cache[cache_key] = (data, time.time())
    
    def _clear_cache(self):
        """清除缓存"""
        self._cache.clear()
    
    @abstractmethod
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
            keyword: 关键词（可选）
            start_date: 开始日期（可选）
            end_date: 结束日期（可选）
            limit: 返回数量限制
            
        Returns:
            统一格式的新闻列表
        """
        pass
    
    async def fetch_stock_news(
        self,
        stock_code: str,
        limit: int = 50
    ) -> List[UnifiedNewsItem]:
        """
        获取个股新闻
        
        Args:
            stock_code: 股票代码
            limit: 返回数量限制
            
        Returns:
            统一格式的新闻列表
        """
        return await self.fetch_news(stock_code=stock_code, limit=limit)
    
    async def fetch_market_news(
        self,
        market: str = MarketType.A_SHARE.value,
        limit: int = 50
    ) -> List[UnifiedNewsItem]:
        """
        获取市场新闻
        
        Args:
            market: 市场类型
            limit: 返回数量限制
            
        Returns:
            统一格式的新闻列表
        """
        return await self.fetch_news(limit=limit)
    
    async def search_news(
        self,
        keyword: str,
        limit: int = 50
    ) -> List[UnifiedNewsItem]:
        """
        搜索新闻
        
        Args:
            keyword: 搜索关键词
            limit: 返回数量限制
            
        Returns:
            统一格式的新闻列表
        """
        return await self.fetch_news(keyword=keyword, limit=limit)
    
    async def health_check(self) -> bool:
        """
        健康检查
        
        Returns:
            数据源是否正常工作
        """
        try:
            news = await self.fetch_news(limit=1)
            self._is_available = True
            self._last_error = None
            return True
        except Exception as e:
            self._is_available = False
            self._last_error = str(e)
            logger.error(f"{self.name} 健康检查失败: {e}")
            return False
    
    def _normalize_stock_code(self, code: str) -> str:
        """
        标准化股票代码
        
        Args:
            code: 原始股票代码
            
        Returns:
            标准化后的股票代码
        """
        if not code:
            return code
        
        # 移除前缀
        code = code.upper().strip()
        for prefix in ['SH', 'SZ', 'BJ', 'HK', 'US', '.SS', '.SZ', '.HK']:
            code = code.replace(prefix, '')
        
        return code
    
    def _detect_market(self, stock_code: str) -> str:
        """
        根据股票代码检测市场
        
        Args:
            stock_code: 股票代码
            
        Returns:
            市场类型
        """
        if not stock_code:
            return MarketType.A_SHARE.value
        
        code = self._normalize_stock_code(stock_code)
        
        # A股判断
        if code.startswith(('60', '68')):  # 上海
            return MarketType.A_SHARE.value
        elif code.startswith(('00', '30', '002', '003')):  # 深圳
            return MarketType.A_SHARE.value
        elif code.startswith(('8', '4')):  # 北交所
            return MarketType.A_SHARE.value
        
        # 港股判断
        if len(code) == 5 and code.isdigit():
            return MarketType.HK_STOCK.value
        
        # 美股判断（字母代码）
        if code.isalpha():
            return MarketType.US_STOCK.value
        
        return MarketType.A_SHARE.value
    
    def _parse_datetime(self, date_str: str) -> Optional[datetime]:
        """
        解析日期时间字符串
        
        Args:
            date_str: 日期时间字符串
            
        Returns:
            datetime对象或None
        """
        if not date_str:
            return None
        
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d",
            "%Y%m%d%H%M%S",
            "%Y%m%d",
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(str(date_str).strip(), fmt)
            except ValueError:
                continue
        
        return None
    
    def _extract_keywords(self, text: str, max_keywords: int = 5) -> List[str]:
        """
        从文本中提取关键词（简单实现）
        
        Args:
            text: 文本内容
            max_keywords: 最大关键词数量
            
        Returns:
            关键词列表
        """
        if not text:
            return []
        
        # 简单的关键词提取：提取股票代码和常见财经词汇
        import re
        
        keywords = []
        
        # 提取股票代码
        stock_codes = re.findall(r'\b[036]\d{5}\b', text)
        keywords.extend(stock_codes[:2])
        
        # 提取常见财经关键词
        finance_keywords = [
            '涨停', '跌停', '利好', '利空', '业绩', '增长', '下跌', '上涨',
            '收购', '并购', '重组', '分红', '配股', '增发', '减持', '增持',
            '财报', '年报', '季报', '预告', '快报', '公告', '研报'
        ]
        
        for kw in finance_keywords:
            if kw in text and kw not in keywords:
                keywords.append(kw)
                if len(keywords) >= max_keywords:
                    break
        
        return keywords[:max_keywords]
    
    def _extract_stock_codes(self, text: str) -> List[str]:
        """
        从文本中提取股票代码
        
        Args:
            text: 文本内容
            
        Returns:
            股票代码列表
        """
        if not text:
            return []
        
        import re
        
        # 匹配A股代码
        a_share_codes = re.findall(r'\b[036]\d{5}\b', text)
        
        # 匹配带前缀的代码
        prefixed_codes = re.findall(r'(?:SH|SZ|BJ|sh|sz|bj)[036]\d{5}', text)
        prefixed_codes = [self._normalize_stock_code(c) for c in prefixed_codes]
        
        # 合并去重
        all_codes = list(set(a_share_codes + prefixed_codes))
        
        return all_codes[:10]  # 最多返回10个