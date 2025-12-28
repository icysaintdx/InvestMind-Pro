"""
统一数据源提供器包
按市场分类组织数据提供器
"""
from .base_provider import BaseStockDataProvider

# 导入中国市场提供器（新路径）
try:
    from .china import (
        AKShareProvider,
        TushareProvider,
        BaostockProvider as BaoStockProvider,
        AKSHARE_AVAILABLE,
        TUSHARE_AVAILABLE,
        BAOSTOCK_AVAILABLE
    )
except ImportError:
    # 向后兼容：尝试从旧路径导入
    try:
        from .tushare_provider import TushareProvider
    except ImportError:
        TushareProvider = None

    try:
        from .akshare_provider import AKShareProvider
    except ImportError:
        AKShareProvider = None

    try:
        from .baostock_provider import BaoStockProvider
    except ImportError:
        BaoStockProvider = None

    AKSHARE_AVAILABLE = AKShareProvider is not None
    TUSHARE_AVAILABLE = TushareProvider is not None
    BAOSTOCK_AVAILABLE = BaoStockProvider is not None

# 导入港股提供器
try:
    from .hk import (
        ImprovedHKStockProvider,
        get_improved_hk_provider,
        HK_PROVIDER_AVAILABLE
    )
except ImportError:
    ImprovedHKStockProvider = None
    get_improved_hk_provider = None
    HK_PROVIDER_AVAILABLE = False

# 导入美股提供器
try:
    from .us import (
        YFinanceUtils,
        OptimizedUSDataProvider,
        get_data_in_range,
        YFINANCE_AVAILABLE,
        OPTIMIZED_US_AVAILABLE,
        FINNHUB_AVAILABLE
    )
except ImportError:
    # 向后兼容：尝试从旧路径导入
    try:
        from ..yfin_utils import YFinanceUtils
    except ImportError:
        YFinanceUtils = None

    try:
        from ..optimized_us_data import OptimizedUSDataProvider
    except ImportError:
        OptimizedUSDataProvider = None

    try:
        from ..finnhub_utils import get_data_in_range
    except ImportError:
        get_data_in_range = None

    YFINANCE_AVAILABLE = YFinanceUtils is not None
    OPTIMIZED_US_AVAILABLE = OptimizedUSDataProvider is not None
    FINNHUB_AVAILABLE = get_data_in_range is not None

# 其他提供器（预留）
try:
    from .yahoo_provider import YahooProvider
except ImportError:
    YahooProvider = None

try:
    from .finnhub_provider import FinnhubProvider
except ImportError:
    FinnhubProvider = None

# 问财 Provider
WENCAI_AVAILABLE = False
try:
    from .wencai_provider import WencaiProvider, get_wencai_provider, PYWENCAI_AVAILABLE
    WENCAI_AVAILABLE = PYWENCAI_AVAILABLE
except ImportError:
    WencaiProvider = None
    get_wencai_provider = None

# TDX Provider - 优先使用 Native Provider（纯Python），降级到 HTTP Provider
TDX_NATIVE_AVAILABLE = False
TDX_HTTP_AVAILABLE = False

try:
    from .tdx_native_provider import TDXNativeProvider, get_tdx_native_provider
    TDX_NATIVE_AVAILABLE = True
except ImportError:
    TDXNativeProvider = None
    get_tdx_native_provider = None

try:
    from .tdx_provider import get_tdx_provider as get_tdx_http_provider
    TDX_HTTP_AVAILABLE = True
except ImportError:
    get_tdx_http_provider = None


def get_best_tdx_provider():
    """
    获取最佳可用的 TDX Provider
    优先级: TDX Native (纯Python) > TDX HTTP (需要Docker服务)

    Returns:
        TDX Provider 实例，如果都不可用则返回 None
    """
    # 1. 优先使用 Native Provider
    if TDX_NATIVE_AVAILABLE and get_tdx_native_provider:
        try:
            provider = get_tdx_native_provider()
            if provider.is_available():
                return provider
        except Exception:
            pass

    # 2. 降级到 HTTP Provider
    if TDX_HTTP_AVAILABLE and get_tdx_http_provider:
        try:
            provider = get_tdx_http_provider()
            if provider.is_available():
                return provider
        except Exception:
            pass

    return None

__all__ = [
    # 基类
    'BaseStockDataProvider',

    # 中国市场
    'TushareProvider',
    'AKShareProvider',
    'BaoStockProvider',
    'AKSHARE_AVAILABLE',
    'TUSHARE_AVAILABLE',
    'BAOSTOCK_AVAILABLE',

    # TDX Provider
    'TDXNativeProvider',
    'get_tdx_native_provider',
    'get_best_tdx_provider',
    'TDX_NATIVE_AVAILABLE',
    'TDX_HTTP_AVAILABLE',

    # 问财 Provider
    'WencaiProvider',
    'get_wencai_provider',
    'WENCAI_AVAILABLE',

    # 港股
    'ImprovedHKStockProvider',
    'get_improved_hk_provider',
    'HK_PROVIDER_AVAILABLE',

    # 美股
    'YFinanceUtils',
    'OptimizedUSDataProvider',
    'get_data_in_range',
    'YFINANCE_AVAILABLE',
    'OPTIMIZED_US_AVAILABLE',
    'FINNHUB_AVAILABLE',

    # 其他（预留）
    'YahooProvider',
    'FinnhubProvider',
]
