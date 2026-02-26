"""
统一数据中心 (Unified Data Center)

提供跨市场、跨数据源的标准化数据访问接口
"""

from .models import (
    MarketType,
    DataPriority,
    Symbol,
    TickData,
    OHLCV,
    MarketDepth,
    FinancialMetrics,
    NewsItem,
    SectorInfo,
    FundFlow,
    MarketOverview,
)

from .cache_manager import (
    CacheLevel,
    CacheConfig,
    UnifiedCacheManager,
    cache_manager,
)

from .circuit_breaker import (
    CircuitState,
    CircuitBreaker,
    ProviderHealth,
    ProviderManager,
    provider_manager,
)

from .base_provider import (
    IMarketDataProvider,
    BaseProvider,
    DataProviderRegistry,
    register_provider,
)

# 导入Providers（注册到注册表）
try:
    from .providers.tdx_provider import TDXProvider
    from .providers.akshare_provider import AKShareProvider
    from .providers.news_provider import UnifiedNewsProvider
except ImportError as e:
    import logging
    logging.getLogger("unified").debug(f"Provider导入失败: {e}")

# 导入服务
try:
    from .service import UnifiedDataService, unified_data_service
except ImportError as e:
    import logging
    logging.getLogger("unified").debug(f"服务导入失败: {e}")

__all__ = [
    # 数据模型
    "MarketType",
    "DataPriority",
    "Symbol",
    "TickData",
    "OHLCV",
    "MarketDepth",
    "FinancialMetrics",
    "NewsItem",
    "SectorInfo",
    "FundFlow",
    "MarketOverview",
    # 缓存
    "CacheLevel",
    "CacheConfig",
    "UnifiedCacheManager",
    "cache_manager",
    # 熔断
    "CircuitState",
    "CircuitBreaker",
    "ProviderHealth",
    "ProviderManager",
    "provider_manager",
    # Provider
    "IMarketDataProvider",
    "BaseProvider",
    "DataProviderRegistry",
    "register_provider",
    "TDXProvider",
    "AKShareProvider",
    "UnifiedNewsProvider",
    # 服务
    "UnifiedDataService",
    "unified_data_service",
]
