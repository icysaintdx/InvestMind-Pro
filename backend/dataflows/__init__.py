# 导入日志模块
from backend.utils.logging_config import get_logger
logger = get_logger('dataflow')

# 尝试导入基础模块，如果失败则跳过
try:
    from .finnhub_utils import get_data_in_range, FINNHUB_AVAILABLE
    if not FINNHUB_AVAILABLE:
        logger.debug("ℹ️ finnhub_utils: 数据目录未配置，离线数据功能不可用")
except ImportError as e:
    logger.debug(f"ℹ️ finnhub_utils模块加载失败: {e}")
    get_data_in_range = None
    FINNHUB_AVAILABLE = False

try:
    from .googlenews_utils import getNewsData, GOOGLENEWS_AVAILABLE
    if not GOOGLENEWS_AVAILABLE:
        logger.debug("ℹ️ googlenews_utils: requests/beautifulsoup4 未安装，Google News 功能不可用")
except ImportError as e:
    logger.debug(f"ℹ️ googlenews_utils模块加载失败: {e}")
    getNewsData = None
    GOOGLENEWS_AVAILABLE = False

try:
    from .reddit_utils import fetch_top_from_category, REDDIT_AVAILABLE
    if not REDDIT_AVAILABLE:
        logger.debug("ℹ️ reddit_utils: 数据目录未配置，Reddit 数据功能不可用")
except ImportError as e:
    logger.debug(f"ℹ️ reddit_utils模块加载失败: {e}")
    fetch_top_from_category = None
    REDDIT_AVAILABLE = False

# 尝试导入yfinance相关模块，如果失败则跳过
try:
    from .yfin_utils import YFinanceUtils, get_stock_data_with_indicators
    try:
        import yfinance
        YFINANCE_AVAILABLE = True
    except ImportError:
        YFINANCE_AVAILABLE = False
        logger.debug("ℹ️ yfin_utils: yfinance 未安装，Yahoo Finance 功能不可用。安装: pip install yfinance")
except ImportError as e:
    logger.debug(f"ℹ️ yfin_utils模块加载失败: {e}")
    YFinanceUtils = None
    get_stock_data_with_indicators = None
    YFINANCE_AVAILABLE = False

try:
    from .stockstats_utils import StockstatsUtils, get_technical_indicator
    try:
        import stockstats
        STOCKSTATS_AVAILABLE = True
    except ImportError:
        STOCKSTATS_AVAILABLE = False
        logger.debug("ℹ️ stockstats_utils: stockstats 未安装，技术指标功能不可用。安装: pip install stockstats")
except ImportError as e:
    logger.debug(f"ℹ️ stockstats_utils模块加载失败: {e}")
    StockstatsUtils = None
    get_technical_indicator = None
    STOCKSTATS_AVAILABLE = False

# 尝试导入 interface 模块
try:
    from .interface import (
        # News and sentiment functions
        get_finnhub_news,
        get_finnhub_company_insider_sentiment,
        get_finnhub_company_insider_transactions,
        get_google_news,
        get_reddit_global_news,
        get_reddit_company_news,
        # Financial statements functions
        get_simfin_balance_sheet,
        get_simfin_cashflow,
        get_simfin_income_statements,
        # Technical analysis functions
        get_stock_stats_indicators_window,
        get_stockstats_indicator,
        # Market data functions
        get_YFin_data_window,
        get_YFin_data,
        # Tushare data functions
        # get_china_stock_data_tushare,  # 暂时禁用，使用统一接口
        # search_china_stocks_tushare,  # 不存在
        # get_china_stock_fundamentals_tushare,  # 暂时禁用
        # get_china_stock_info_tushare,  # 暂时禁用
        # Unified China data functions (recommended)
        get_china_stock_data_unified,
        get_china_stock_info_unified,
        switch_china_data_source,
        get_current_china_data_source,
        # Hong Kong stock functions
        get_hk_stock_data_unified,
        get_hk_stock_info_unified,
        get_stock_data_by_market,
    )
    INTERFACE_AVAILABLE = True
except ImportError as e:
    logger.debug(f"ℹ️ interface模块加载失败: {e}")
    INTERFACE_AVAILABLE = False
    # 设置默认值
    get_finnhub_news = None
    get_finnhub_company_insider_sentiment = None
    get_finnhub_company_insider_transactions = None
    get_google_news = None
    get_reddit_global_news = None
    get_reddit_company_news = None
    get_simfin_balance_sheet = None
    get_simfin_cashflow = None
    get_simfin_income_statements = None
    get_stock_stats_indicators_window = None
    get_stockstats_indicator = None
    get_YFin_data_window = None
    get_YFin_data = None
    # Tushare 函数暂时不可用，使用统一接口
    get_china_stock_data_tushare = None
    search_china_stocks_tushare = None
    get_china_stock_fundamentals_tushare = None
    get_china_stock_info_tushare = None
    get_china_stock_data_unified = None
    get_china_stock_info_unified = None
    switch_china_data_source = None
    get_current_china_data_source = None
    get_hk_stock_data_unified = None
    get_hk_stock_info_unified = None
    get_stock_data_by_market = None

__all__ = [
    # 基础模块导出
    "get_data_in_range",
    "getNewsData",
    "fetch_top_from_category",
    "YFinanceUtils",
    "get_stock_data_with_indicators",
    "StockstatsUtils",
    "get_technical_indicator",
    # 可用性标志
    "FINNHUB_AVAILABLE",
    "GOOGLENEWS_AVAILABLE",
    "REDDIT_AVAILABLE",
    "YFINANCE_AVAILABLE",
    "STOCKSTATS_AVAILABLE",
    "INTERFACE_AVAILABLE",
    # News and sentiment functions
    "get_finnhub_news",
    "get_finnhub_company_insider_sentiment",
    "get_finnhub_company_insider_transactions",
    "get_google_news",
    "get_reddit_global_news",
    "get_reddit_company_news",
    # Financial statements functions
    "get_simfin_balance_sheet",
    "get_simfin_cashflow",
    "get_simfin_income_statements",
    # Technical analysis functions
    "get_stock_stats_indicators_window",
    "get_stockstats_indicator",
    # Market data functions
    "get_YFin_data_window",
    "get_YFin_data",
    # Tushare data functions
    "get_china_stock_data_tushare",
    "search_china_stocks_tushare",
    "get_china_stock_fundamentals_tushare",
    "get_china_stock_info_tushare",
    # Unified China data functions
    "get_china_stock_data_unified",
    "get_china_stock_info_unified",
    "switch_china_data_source",
    "get_current_china_data_source",
    # Hong Kong stock functions
    "get_hk_stock_data_unified",
    "get_hk_stock_info_unified",
    "get_stock_data_by_market",
]
