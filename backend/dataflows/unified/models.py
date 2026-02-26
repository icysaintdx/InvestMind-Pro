"""
统一数据模型定义
支持跨市场（A股/港股/美股/数字货币）的统一数据表示
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum


class MarketType(Enum):
    """市场类型枚举"""
    A_SHARE = "a_share"      # A股
    HK_SHARE = "hk_share"    # 港股
    US_SHARE = "us_share"    # 美股
    CRYPTO = "crypto"        # 数字货币
    FUTURES = "futures"      # 期货


class DataPriority(Enum):
    """数据优先级"""
    REALTIME = "realtime"    # 实时数据
    FAST = "fast"            # 快速
    NORMAL = "normal"        # 正常
    BACKUP = "backup"        # 备用
    STALE = "stale"          # 过期数据


@dataclass(frozen=True)
class Symbol:
    """
    统一证券代码表示
    
    Examples:
        >>> s1 = Symbol("600519", MarketType.A_SHARE, "SH")
        >>> str(s1)
        'a_share:600519'
        >>> s1.full_code
        'SH600519'
        
        >>> s2 = Symbol("AAPL", MarketType.US_SHARE)
        >>> str(s2)
        'us_share:AAPL'
    """
    code: str                    # 原始代码
    market: MarketType          # 市场类型
    exchange: Optional[str] = None  # 交易所代码
    
    def __str__(self) -> str:
        return f"{self.market.value}:{self.code}"
    
    @property
    def full_code(self) -> str:
        """完整代码表示"""
        if self.market == MarketType.A_SHARE and self.exchange:
            return f"{self.exchange}{self.code}"
        return self.code
    
    @property
    def is_a_share(self) -> bool:
        """是否为A股"""
        return self.market == MarketType.A_SHARE


@dataclass(frozen=True)
class TickData:
    """统一Tick数据（实时行情）"""
    symbol: Symbol
    timestamp: datetime
    price: float = 0
    volume: int = 0
    bid: float = 0              # 买一价
    ask: float = 0              # 卖一价
    bid_volume: int = 0         # 买一量
    ask_volume: int = 0         # 卖一量
    change_pct: float = 0       # 涨跌幅
    name: Optional[str] = None  # 股票名称
    turnover: Optional[float] = None  # 成交额
    open: Optional[float] = None      # 开盘价
    high: Optional[float] = None      # 最高价
    low: Optional[float] = None       # 最低价
    pre_close: Optional[float] = None # 昨收价
    extra: Dict[str, Any] = field(default_factory=dict)  # 市场特定数据


@dataclass(frozen=True)
class OHLCV:
    """统一K线数据"""
    symbol: Symbol
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    turnover: Optional[float] = None
    timeframe: str = "1d"   # 1m, 5m, 15m, 1h, 1d, 1w, 1M
    
    @property
    def change(self) -> float:
        """涨跌额"""
        return self.close - self.open
    
    @property
    def change_pct(self) -> float:
        """涨跌幅"""
        if self.open == 0:
            return 0.0
        return (self.close - self.open) / self.open * 100


@dataclass(frozen=True)
class MarketDepth:
    """统一盘口深度数据"""
    symbol: Symbol
    timestamp: datetime
    bids: List[tuple] = field(default_factory=list)  # [(price, volume), ...]
    asks: List[tuple] = field(default_factory=list)  # [(price, volume), ...]
    
    @property
    def bid_1(self) -> Optional[float]:
        """买一价"""
        return self.bids[0][0] if self.bids else None
    
    @property
    def ask_1(self) -> Optional[float]:
        """卖一价"""
        return self.asks[0][0] if self.asks else None


@dataclass
class FinancialMetrics:
    """统一财务指标数据"""
    symbol: Symbol
    report_date: str        # 报告期，如 "2024Q3"
    report_type: str        # income, balance, cashflow
    
    # 通用指标
    revenue: Optional[float] = None           # 营收
    net_profit: Optional[float] = None        # 净利润
    total_assets: Optional[float] = None      # 总资产
    total_liabilities: Optional[float] = None # 总负债
    equity: Optional[float] = None            # 净资产
    eps: Optional[float] = None               # 每股收益
    roe: Optional[float] = None               # 净资产收益率(%)
    gross_margin: Optional[float] = None      # 毛利率(%)
    net_margin: Optional[float] = None        # 净利率(%)
    debt_ratio: Optional[float] = None        # 资产负债率(%)
    
    # 原始数据
    raw_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NewsItem:
    """统一新闻数据"""
    id: str
    title: str
    content: str
    source: str
    publish_time: datetime
    sentiment: float = 0.0        # -1.0 ~ 1.0
    sentiment_label: str = "neutral"  # positive, negative, neutral
    related_symbols: List[Symbol] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    url: Optional[str] = None
    
    @property
    def is_positive(self) -> bool:
        """是否正面新闻"""
        return self.sentiment > 0.3
    
    @property
    def is_negative(self) -> bool:
        """是否负面新闻"""
        return self.sentiment < -0.3


@dataclass
class SectorInfo:
    """统一板块数据"""
    code: str
    name: str
    market: MarketType
    sector_type: str        # industry, concept, region
    change_pct: float = 0.0
    turnover: Optional[float] = None
    top_stocks: List[Symbol] = field(default_factory=list)
    fund_flow: Optional[float] = None  # 资金流向
    
    @property
    def is_rising(self) -> bool:
        """是否上涨"""
        return self.change_pct > 0


@dataclass
class FundFlow:
    """资金流向数据"""
    symbol: Symbol
    main_net_inflow: float      # 主力净流入
    retail_net_inflow: float    # 散户净流入
    large_order_inflow: float   # 大单流入
    medium_order_inflow: float  # 中单流入
    small_order_inflow: float   # 小单流入
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class MarketOverview:
    """市场概览数据"""
    market: MarketType
    timestamp: datetime
    total_stocks: int = 0
    up_count: int = 0
    down_count: int = 0
    flat_count: int = 0
    limit_up_count: int = 0     # 涨停数
    limit_down_count: int = 0   # 跌停数
    total_turnover: float = 0.0 # 总成交额
    sentiment_score: float = 50.0  # 市场情绪分 0-100
