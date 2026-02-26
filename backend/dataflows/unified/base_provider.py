"""
Provider抽象基类
定义统一的数据源接口规范
"""

from abc import ABC, abstractmethod
from typing import Optional, List, AsyncIterator, Dict, Any
from datetime import datetime

from .models import (
    Symbol, TickData, OHLCV, MarketDepth,
    FinancialMetrics, NewsItem, SectorInfo,
    MarketType, DataPriority
)


class IMarketDataProvider(ABC):
    """
    市场数据Provider接口（抽象基类）
    
    所有具体Provider必须实现此接口
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Provider名称"""
        pass
    
    @property
    @abstractmethod
    def supported_markets(self) -> List[MarketType]:
        """支持的市场类型"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """健康检查"""
        pass
    
    # ========== 实时行情 ==========
    
    @abstractmethod
    async def get_tick(self, symbol: Symbol) -> Optional[TickData]:
        """获取最新Tick数据"""
        pass
    
    @abstractmethod
    async def get_ticks(self, symbols: List[Symbol]) -> List[TickData]:
        """批量获取Tick数据"""
        pass
    
    @abstractmethod
    async def get_depth(self, symbol: Symbol) -> Optional[MarketDepth]:
        """获取盘口深度"""
        pass
    
    # ========== K线数据 ==========
    
    @abstractmethod
    async def get_klines(
        self,
        symbol: Symbol,
        timeframe: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500
    ) -> List[OHLCV]:
        """获取K线数据"""
        pass
    
    @abstractmethod
    async def get_latest_kline(self, symbol: Symbol, timeframe: str = "1d") -> Optional[OHLCV]:
        """获取最新K线"""
        pass
    
    # ========== 财务数据 ==========
    
    @abstractmethod
    async def get_financial(
        self,
        symbol: Symbol,
        report_type: str = "income",
        period: Optional[str] = None
    ) -> Optional[FinancialMetrics]:
        """获取财务数据"""
        pass
    
    # ========== 新闻数据 ==========
    
    @abstractmethod
    async def get_news(
        self,
        symbols: Optional[List[Symbol]] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[NewsItem]:
        """获取新闻"""
        pass
    
    # ========== 板块数据 ==========
    
    @abstractmethod
    async def get_sectors(
        self,
        market: MarketType = MarketType.A_SHARE,
        sector_type: str = "industry"
    ) -> List[SectorInfo]:
        """获取板块列表"""
        pass
    
    @abstractmethod
    async def get_sector_stocks(
        self,
        sector_name: str,
        sector_type: str = "industry"
    ) -> List[TickData]:
        """获取板块成分股"""
        pass


class BaseProvider(IMarketDataProvider):
    """
    Provider基类
    
    提供通用的错误处理和日志记录
    """
    
    def __init__(self, name: str, supported_markets: List[MarketType]):
        self._name = name
        self._supported_markets = supported_markets
        self._stats = {
            "total_requests": 0,
            "total_successes": 0,
            "total_failures": 0,
            "avg_latency": 0.0,
        }
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def supported_markets(self) -> List[MarketType]:
        return self._supported_markets
    
    def _handle_error(self, operation: str, error: Exception) -> None:
        """统一错误处理"""
        from backend.utils.logging_config import get_logger
        logger = get_logger(f"provider.{self._name}")
        logger.error(f"[{self._name}.{operation}] 错误: {error}")
    
    def _check_market_support(self, symbol: Symbol) -> bool:
        """检查是否支持该市场"""
        if symbol.market not in self._supported_markets:
            from backend.utils.logging_config import get_logger
            logger = get_logger(f"provider.{self._name}")
            logger.warning(
                f"[{self._name}] 不支持市场: {symbol.market}, "
                f"支持的市场: {self._supported_markets}"
            )
            return False
        return True
    
    async def health_check(self) -> bool:
        """默认健康检查"""
        return True
    
    # 子类需要实现的抽象方法
    
    async def get_tick(self, symbol: Symbol) -> Optional[TickData]:
        raise NotImplementedError
    
    async def get_ticks(self, symbols: List[Symbol]) -> List[TickData]:
        raise NotImplementedError
    
    async def get_depth(self, symbol: Symbol) -> Optional[MarketDepth]:
        raise NotImplementedError
    
    async def get_klines(
        self,
        symbol: Symbol,
        timeframe: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500
    ) -> List[OHLCV]:
        raise NotImplementedError
    
    async def get_latest_kline(self, symbol: Symbol, timeframe: str = "1d") -> Optional[OHLCV]:
        raise NotImplementedError
    
    async def get_financial(
        self,
        symbol: Symbol,
        report_type: str = "income",
        period: Optional[str] = None
    ) -> Optional[FinancialMetrics]:
        raise NotImplementedError
    
    async def get_news(
        self,
        symbols: Optional[List[Symbol]] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[NewsItem]:
        raise NotImplementedError
    
    async def get_sectors(
        self,
        market: MarketType = MarketType.A_SHARE,
        sector_type: str = "industry"
    ) -> List[SectorInfo]:
        raise NotImplementedError
    
    async def get_sector_stocks(
        self,
        sector_name: str,
        sector_type: str = "industry"
    ) -> List[TickData]:
        """获取板块成分股（默认返回空列表）"""
        return []


class DataProviderRegistry:
    """
    Provider注册表
    
    管理所有Provider的注册和发现
    """
    
    _providers: Dict[str, type] = {}
    
    @classmethod
    def register(cls, name: str, provider_class: type):
        """注册Provider"""
        cls._providers[name] = provider_class
    
    @classmethod
    def get(cls, name: str) -> Optional[type]:
        """获取Provider类"""
        return cls._providers.get(name)
    
    @classmethod
    def list_providers(cls) -> List[str]:
        """列出所有Provider"""
        return list(cls._providers.keys())


def register_provider(name: str):
    """Provider注册装饰器"""
    def decorator(cls):
        DataProviderRegistry.register(name, cls)
        return cls
    return decorator
