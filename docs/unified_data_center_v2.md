# InvestMindPro - 企业级统一数据中心架构 v2.0

## 设计目标

### 性能目标（硬性指标）
| 场景 | 目标响应时间 | 最大容忍 | 达标率 |
|------|------------|---------|-------|
| 首页加载 | <500ms | 1s | 99% |
| 行情数据 | <200ms | 500ms | 99.9% |
| K线加载 | <1s | 2s | 99% |
| 板块数据 | <1s | 2s | 99% |
| 新闻列表 | <500ms | 1s | 99% |
| 财务数据 | <1s | 2s | 98% |

### 架构目标
- ✅ 多市场支持（A股/港股/美股/数字货币）
- ✅ 自动降级（数据源故障时无缝切换）
- ✅ 多级缓存（L1内存/L2本地/L3远程）
- ✅ 统一接口（所有市场同一套API）
- ✅ 可观测性（全链路监控）

---

## 核心架构

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           API Gateway Layer                                  │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌──────────────┐       │
│  │  限流/熔断    │ │  鉴权/加密    │ │  请求路由    │ │  日志追踪    │       │
│  │ Rate Limit   │ │   Auth       │ │   Router    │ │  Tracing    │       │
│  └──────────────┘ └──────────────┘ └──────────────┘ └──────────────┘       │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      Unified Data Orchestrator                               │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                         Request Router                                  │ │
│  │   /data/{market}/{type}/{symbol}?priority=realtime|fast|normal         │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│  ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐            │ │
│  │   Cache Manager  │ │  Circuit Breaker │ │   Load Balancer  │            │ │
│  │   (多级缓存)      │ │   (熔断降级)      │ │   (负载均衡)      │            │ │
│  └──────────────────┘ └──────────────────┘ └──────────────────┘            │ │
│  ┌────────────────────────────────────────────────────────────────────────┐ │
│  │                    Provider Strategy Engine                             │ │
│  │   Priority: L1(内存) → L2(本地) → L3(远程) → L4(降级数据源)            │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
                                      │
                                      ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Multi-Market Provider Pool                            │
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                           A-Share Market                                ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐          ││
│  │  │ Level-1 │ │ Level-2 │ │ Level-3 │ │ Level-4 │ │ Level-5 │          ││
│  │  │  内存缓存 │ │ 本地缓存 │ │   TDX   │ │ AKShare │ │Tushare  │          ││
│  │  │  <1ms   │ │  <10ms  │ │  <100ms │ │  <500ms │ │ <1000ms │          ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘ └─────────┘          ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         HK-Share Market                               ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                       ││
│  │  │ 内存缓存 │ │ 本地缓存 │ │ HKEX API│ │ 备用爬虫 │                       ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                         US-Share Market                               ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                       ││
│  │  │ 内存缓存 │ │ 本地缓存 │ │ Finnhub │ │ Yahoo   │                       ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │                        Crypto Market                                  ││
│  │  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐                       ││
│  │  │ 内存缓存 │ │ 本地缓存 │ │ Binance │ │ OKX     │                       ││
│  │  └─────────┘ └─────────┘ └─────────┘ └─────────┘                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 统一数据模型

### 1. 基础数据模型（跨市场通用）

```python
from dataclasses import dataclass
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum

class MarketType(Enum):
    A_SHARE = "a_share"      # A股
    HK_SHARE = "hk_share"    # 港股
    US_SHARE = "us_share"    # 美股
    CRYPTO = "crypto"        # 数字货币
    FUTURES = "futures"      # 期货

class DataPriority(Enum):
    REALTIME = "realtime"    # 实时数据（从交易所）
    FAST = "fast"            # 快速（缓存+数据源）
    NORMAL = "normal"        # 正常（优先级获取）
    BACKUP = "backup"        # 备用数据源
    STALE = "stale"          # 过期数据（托底）

@dataclass(frozen=True)
class Symbol:
    """统一证券代码表示"""
    code: str                    # 原始代码，如 "600519"
    market: MarketType          # 市场类型
    exchange: Optional[str] = None  # 交易所，如 "SH", "SZ", "NASDAQ"
    
    def __str__(self) -> str:
        return f"{self.market.value}:{self.code}"
    
    @property
    def full_code(self) -> str:
        """完整代码，如 "SH600519" 或 "AAPL""""
        if self.market == MarketType.A_SHARE and self.exchange:
            return f"{self.exchange}{self.code}"
        return self.code

@dataclass
class TickData:
    """统一Tick数据（跨市场）"""
    symbol: Symbol
    timestamp: datetime
    price: float
    volume: int
    bid: float              # 买一价
    ask: float              # 卖一价
    bid_volume: int         # 买一量
    ask_volume: int         # 卖一量
    change_pct: float       # 涨跌幅
    turnover: Optional[float] = None  # 成交额
    
    # 市场特定字段
    extra: Dict[str, any] = None  # 市场特定数据

@dataclass  
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

@dataclass
class MarketDepth:
    """统一盘口数据"""
    symbol: Symbol
    timestamp: datetime
    bids: List[tuple]       # [(price, volume), ...] 买1-买10
    asks: List[tuple]       # [(price, volume), ...] 卖1-卖10

@dataclass
class FinancialMetrics:
    """统一财务指标"""
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
    roe: Optional[float] = None               # 净资产收益率
    
    # 原始数据（市场特定）
    raw_data: Dict[str, any] = None

@dataclass
class NewsItem:
    """统一新闻数据"""
    id: str
    title: str
    content: str
    source: str
    publish_time: datetime
    sentiment: float        # -1.0 ~ 1.0
    sentiment_label: str    # positive, negative, neutral
    related_symbols: List[Symbol] = None
    tags: List[str] = None

@dataclass
class SectorInfo:
    """统一板块数据"""
    code: str
    name: str
    market: MarketType
    sector_type: str        # industry, concept, region
    change_pct: float
    top_stocks: List[Symbol] = None
    fund_flow: Optional[float] = None  # 资金流向
```

---

## 统一服务接口

```python
from abc import ABC, abstractmethod
from typing import AsyncIterator

class IUnifiedDataService(ABC):
    """统一数据服务接口"""
    
    # ==================== 实时行情 ====================
    @abstractmethod
    async def get_tick(self, symbol: Symbol, priority: DataPriority = DataPriority.FAST) -> TickData:
        """获取最新Tick数据"""
        pass
    
    @abstractmethod
    async def get_ticks(self, symbols: List[Symbol], priority: DataPriority = DataPriority.FAST) -> List[TickData]:
        """批量获取Tick数据"""
        pass
    
    @abstractmethod
    async def subscribe_ticks(self, symbols: List[Symbol]) -> AsyncIterator[TickData]:
        """订阅实时Tick流（WebSocket）"""
        pass
    
    # ==================== K线数据 ====================
    @abstractmethod
    async def get_klines(
        self, 
        symbol: Symbol, 
        timeframe: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500,
        priority: DataPriority = DataPriority.NORMAL
    ) -> List[OHLCV]:
        """获取K线数据"""
        pass
    
    @abstractmethod
    async def get_latest_kline(self, symbol: Symbol, timeframe: str = "1d") -> OHLCV:
        """获取最新K线"""
        pass
    
    # ==================== 盘口数据 ====================
    @abstractmethod
    async def get_depth(self, symbol: Symbol) -> MarketDepth:
        """获取盘口深度"""
        pass
    
    # ==================== 财务数据 ====================
    @abstractmethod
    async def get_financial(
        self, 
        symbol: Symbol, 
        report_type: str = "income",
        period: Optional[str] = None,
        priority: DataPriority = DataPriority.NORMAL
    ) -> FinancialMetrics:
        """获取财务数据"""
        pass
    
    @abstractmethod
    async def get_financial_history(
        self, 
        symbol: Symbol, 
        report_type: str = "income",
        periods: int = 8
    ) -> List[FinancialMetrics]:
        """获取历史财务数据"""
        pass
    
    # ==================== 新闻数据 ====================
    @abstractmethod
    async def get_news(
        self,
        symbols: Optional[List[Symbol]] = None,
        category: str = "market",
        hours: int = 24,
        limit: int = 100,
        priority: DataPriority = DataPriority.FAST
    ) -> List[NewsItem]:
        """获取新闻"""
        pass
    
    @abstractmethod
    async def subscribe_news(self, symbols: Optional[List[Symbol]] = None) -> AsyncIterator[NewsItem]:
        """订阅实时新闻流"""
        pass
    
    # ==================== 板块数据 ====================
    @abstractmethod
    async def get_sectors(
        self,
        market: MarketType = MarketType.A_SHARE,
        sector_type: str = "industry",
        sort_by: str = "change_pct",
        priority: DataPriority = DataPriority.FAST
    ) -> List[SectorInfo]:
        """获取板块列表"""
        pass
    
    @abstractmethod
    async def get_sector_stocks(self, sector_code: str, market: MarketType = MarketType.A_SHARE) -> List[Symbol]:
        """获取板块成分股"""
        pass
    
    # ==================== 市场概览 ====================
    @abstractmethod
    async def get_market_overview(self, market: MarketType = MarketType.A_SHARE) -> Dict[str, any]:
        """获取市场概览（涨跌停数、成交额等）"""
        pass
    
    @abstractmethod
    async def get_hot_stocks(self, market: MarketType = MarketType.A_SHARE, limit: int = 20) -> List[Symbol]:
        """获取热门股票"""
        pass
```

---

## 多级缓存架构

```python
class CacheLevel(Enum):
    L1_MEMORY = "l1_memory"      # 进程内存，<1ms
    L2_LOCAL = "l2_local"        # 本地SQLite/Redis，<10ms
    L3_REMOTE = "l3_remote"      # 远程Redis，<50ms
    L4_DISK = "l4_disk"          # 本地文件，<100ms

class CacheConfig:
    """缓存配置"""
    CONFIG = {
        # 实时行情 - 极短TTL
        "tick": {
            CacheLevel.L1_MEMORY: {"ttl": 1, "max_size": 10000},      # 1秒
            CacheLevel.L2_LOCAL: {"ttl": 5, "max_size": 50000},        # 5秒
        },
        # K线 - 较长TTL（历史数据不变）
        "klines": {
            CacheLevel.L1_MEMORY: {"ttl": 60, "max_size": 2000},       # 1分钟
            CacheLevel.L2_LOCAL: {"ttl": 300, "max_size": 10000},      # 5分钟
            CacheLevel.L4_DISK: {"ttl": 86400, "max_size": 100000},    # 1天
        },
        # 财务数据 - 长TTL（季报）
        "financial": {
            CacheLevel.L1_MEMORY: {"ttl": 3600, "max_size": 1000},     # 1小时
            CacheLevel.L2_LOCAL: {"ttl": 86400, "max_size": 5000},     # 1天
            CacheLevel.L4_DISK: {"ttl": 604800, "max_size": 20000},    # 7天
        },
        # 新闻 - 中TTL
        "news": {
            CacheLevel.L1_MEMORY: {"ttl": 30, "max_size": 5000},       # 30秒
            CacheLevel.L2_LOCAL: {"ttl": 300, "max_size": 20000},      # 5分钟
        },
        # 板块 - 短TTL（实时变化）
        "sector": {
            CacheLevel.L1_MEMORY: {"ttl": 5, "max_size": 500},         # 5秒
            CacheLevel.L2_LOCAL: {"ttl": 60, "max_size": 2000},        # 1分钟
        },
    }

class UnifiedCacheManager:
    """统一缓存管理器"""
    
    def __init__(self):
        self.l1_cache = {}  # 内存字典
        self.l2_cache = None  # SQLite/Redis连接
        self.l3_cache = None  # Redis连接
        
    async def get(self, key: str, data_type: str) -> Optional[Any]:
        """多级缓存读取"""
        # L1
        if key in self.l1_cache:
            value, expire_time = self.l1_cache[key]
            if time.time() < expire_time:
                return value
            del self.l1_cache[key]
        
        # L2
        value = await self._get_l2(key)
        if value:
            # 回填L1
            await self._set_l1(key, value, data_type)
            return value
        
        # L3
        value = await self._get_l3(key)
        if value:
            await self._set_l2(key, value, data_type)
            await self._set_l1(key, value, data_type)
            return value
        
        return None
    
    async def set(self, key: str, value: Any, data_type: str):
        """多级缓存写入"""
        config = CacheConfig.CONFIG.get(data_type, {})
        
        # 写入所有级别
        if CacheLevel.L1_MEMORY in config:
            await self._set_l1(key, value, data_type)
        if CacheLevel.L2_LOCAL in config:
            await self._set_l2(key, value, data_type)
        if CacheLevel.L3_REMOTE in config:
            await self._set_l3(key, value, data_type)
```

---

## 熔断降级机制

```python
from enum import Enum
from dataclasses import dataclass

class CircuitState(Enum):
    CLOSED = "closed"      # 正常
    OPEN = "open"          # 熔断
    HALF_OPEN = "half_open"  # 半开试探

@dataclass
class ProviderHealth:
    """Provider健康状态"""
    provider_name: str
    state: CircuitState
    success_rate: float     # 成功率
    avg_latency: float      # 平均延迟
    last_failure: Optional[datetime] = None
    consecutive_failures: int = 0

class CircuitBreaker:
    """熔断器"""
    
    def __init__(self, 
                 failure_threshold: int = 5,      # 连续失败阈值
                 recovery_timeout: int = 30,      # 恢复时间（秒）
                 success_threshold: int = 3):     # 半开成功阈值
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold
        self.state = CircuitState.CLOSED
        self.failures = 0
        self.successes = 0
        self.last_failure_time = None
        
    def can_execute(self) -> bool:
        """判断是否可执行"""
        if self.state == CircuitState.CLOSED:
            return True
        elif self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = CircuitState.HALF_OPEN
                self.successes = 0
                return True
            return False
        else:  # HALF_OPEN
            return True
    
    def record_success(self):
        """记录成功"""
        self.failures = 0
        if self.state == CircuitState.HALF_OPEN:
            self.successes += 1
            if self.successes >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.successes = 0
    
    def record_failure(self):
        """记录失败"""
        self.failures += 1
        self.last_failure_time = time.time()
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
        elif self.failures >= self.failure_threshold:
            self.state = CircuitState.OPEN

class ProviderManager:
    """Provider管理器（带熔断）"""
    
    def __init__(self):
        self.providers: Dict[str, BaseProvider] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.health_status: Dict[str, ProviderHealth] = {}
        
    async def execute_with_fallback(
        self, 
        operation: str,
        symbol: Symbol,
        priority: DataPriority = DataPriority.FAST
    ) -> Optional[Any]:
        """带降级的执行"""
        
        # 根据优先级和市场选择Provider链
        provider_chain = self._get_provider_chain(symbol.market, operation, priority)
        
        last_error = None
        for provider_name in provider_chain:
            breaker = self.circuit_breakers.get(provider_name)
            
            # 检查熔断器
            if breaker and not breaker.can_execute():
                logger.warning(f"[{provider_name}] 熔断器开启，跳过")
                continue
            
            provider = self.providers.get(provider_name)
            if not provider:
                continue
            
            try:
                start = time.time()
                result = await asyncio.wait_for(
                    self._execute_provider(provider, operation, symbol),
                    timeout=10  # 单个Provider 10秒超时
                )
                latency = time.time() - start
                
                # 记录成功
                if breaker:
                    breaker.record_success()
                self._record_health(provider_name, True, latency)
                
                return result
                
            except Exception as e:
                logger.error(f"[{provider_name}] 执行失败: {e}")
                last_error = e
                
                # 记录失败
                if breaker:
                    breaker.record_failure()
                self._record_health(provider_name, False, 0)
        
        # 所有Provider都失败
        logger.error(f"所有Provider都失败，最后错误: {last_error}")
        return None
    
    def _get_provider_chain(
        self, 
        market: MarketType, 
        operation: str,
        priority: DataPriority
    ) -> List[str]:
        """获取Provider优先级链"""
        
        # A股市场Provider链
        if market == MarketType.A_SHARE:
            if priority == DataPriority.REALTIME:
                return ["tdx", "akshare", "tushare"]
            elif priority == DataPriority.FAST:
                return ["akshare", "tdx", "tushare"]
            else:
                return ["tushare", "akshare", "baostock"]
        
        # 港股市场
        elif market == MarketType.HK_SHARE:
            return ["hkex", "akshare"]
        
        # 美股市场
        elif market == MarketType.US_SHARE:
            return ["finnhub", "yfinance"]
        
        return []
```

---

## 实施路线图

### Phase 1: 基础设施搭建 (2天)
- [ ] 创建统一数据模型
- [ ] 实现多级缓存管理器
- [ ] 实现熔断降级机制
- [ ] 创建Provider抽象基类

### Phase 2: A股数据迁移 (3天)
- [ ] TDX Provider封装
- [ ] AKShare Provider封装
- [ ] Tushare Provider封装
- [ ] 统一行情接口
- [ ] 统一K线接口

### Phase 3: 新闻/板块迁移 (2天)
- [ ] 新闻数据统一接口
- [ ] 板块数据统一接口
- [ ] 财务数据统一接口

### Phase 4: 性能优化 (2天)
- [ ] 热点数据预加载
- [ ] 并行查询优化
- [ ] 缓存命中率监控
- [ ] 响应时间监控

### Phase 5: 监控与可观测性 (1天)
- [ ] Provider健康监控
- [ ] 缓存命中率监控
- [ ] 响应时间Dashboard
- [ ] 熔断状态监控

### Phase 6: 多市场扩展 (可选)
- [ ] 港股接入
- [ ] 美股接入
- [ ] 数字货币接入

---

## 预期效果

### 性能提升
| 指标 | 当前 | 目标 | 提升 |
|------|------|------|------|
| 首页加载 | 5-8s | <500ms | **10-16x** |
| 行情数据 | 2-3s | <200ms | **10-15x** |
| K线加载 | 3-5s | <1s | **3-5x** |
| 板块数据 | 5-6s | <1s | **5-6x** |
| 新闻列表 | 10-15s | <500ms | **20-30x** |

### 稳定性提升
- Provider故障自动切换：**秒级**
- 缓存命中率：**>90%**
- 服务可用性：**99.9%**

### 维护成本
- 代码量减少：**50%**
- 新增数据源时间：**从1天降至2小时**
- Bug定位时间：**从小时级降至分钟级**

---

## 下一步行动

**是否开始Phase 1搭建基础设施？**

需要约 **2天** 完成核心框架，之后可以逐步迁移现有数据源。
