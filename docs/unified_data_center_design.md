# 统一数据中心架构设计 (Unified Data Center)

## 当前问题
- 17个Provider各自为战
- 22个数据文件分散在各地
- 调用方式不统一（async/sync混用）
- 缓存策略不一致
- 错误处理混乱

## 目标架构

```
┌─────────────────────────────────────────────────────────────┐
│                    API Gateway (统一入口)                    │
│              /api/data/stock/{code}                         │
│              /api/data/kline/{code}                         │
│              /api/data/sector/{type}                        │
│              /api/data/news/{category}                      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Unified Data Service (统一数据服务)              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  请求路由器   │  │   缓存管理器  │  │  降级处理器   │      │
│  │  (Router)    │  │   (Cache)    │  │  (Fallback)  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Provider Pool (数据源连接池)                     │
│  ┌──────────┬──────────┬──────────┬──────────┬──────────┐  │
│  │ AKShare  │ Tushare  │  TDX     │Baostock  │  巨潮    │  │  A股
│  └──────────┴──────────┴──────────┴──────────┴──────────┘  │
│  ┌──────────┬──────────┐                                    │
│  │ FinnHub  │ YFinance │                                    │  美股
│  └──────────┴──────────┘                                    │
│  ┌──────────┬──────────┐                                    │
│  │ HKEX     │ 自定义    │                                    │  港股
│  └──────────┴──────────┘                                    │
└─────────────────────────────────────────────────────────────┘
```

## 数据分类体系

### 1. 行情数据 (Quotes)
```python
@dataclass
class QuoteData:
    code: str
    name: str
    price: float
    change: float
    volume: int
    turnover: float
    bid_ask: BidAsk
    timestamp: datetime
```

### 2. K线数据 (Klines)
```python
@dataclass  
class KlineData:
    code: str
    timeframe: str  # 1m, 5m, 15m, 1h, 1d, 1w, 1M
    open: float
    high: float
    low: float
    close: float
    volume: int
    timestamp: datetime
```

### 3. 财务数据 (Financials)
```python
@dataclass
class FinancialData:
    code: str
    report_type: str  # balance, income, cashflow
    period: str       # 2024Q3
    metrics: Dict[str, float]
```

### 4. 新闻数据 (News)
```python
@dataclass
class NewsData:
    id: str
    title: str
    content: str
    source: str
    publish_time: datetime
    sentiment: str
    related_stocks: List[str]
```

### 5. 板块数据 (Sectors)
```python
@dataclass
class SectorData:
    code: str
    name: str
    type: str  # industry, concept
    change_pct: float
    top_stocks: List[str]
```

## 统一接口设计

```python
class UnifiedDataService:
    """统一数据服务中心"""
    
    # ========== 行情数据 ==========
    async def get_quote(self, code: str) -> QuoteData
    async def get_quotes(self, codes: List[str]) -> List[QuoteData]
    async def get_realtime_spot(self) -> List[QuoteData]  # 全市场
    
    # ========== K线数据 ==========
    async def get_kline(
        self, 
        code: str, 
        timeframe: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500
    ) -> List[KlineData]
    
    # ========== 财务数据 ==========
    async def get_financial(
        self, 
        code: str, 
        report_type: str = "income",
        period: Optional[str] = None
    ) -> FinancialData
    
    # ========== 新闻数据 ==========
    async def get_news(
        self,
        category: str = "market",  # market, stock, sector
        code: Optional[str] = None,
        hours: int = 24,
        limit: int = 100
    ) -> List[NewsData]
    
    # ========== 板块数据 ==========
    async def get_sectors(
        self,
        sector_type: str = "industry",  # industry, concept
        sort_by: str = "change_pct"
    ) -> List[SectorData]
    
    # ========== 资金流向 ==========
    async def get_fund_flow(self, code: str) -> FundFlowData
    async def get_sector_fund_flow(self, sector: str) -> FundFlowData
```

## 数据源优先级配置

```python
DATA_SOURCE_PRIORITY = {
    # 行情数据优先级
    "quote": ["tdx", "akshare", "tushare"],
    
    # K线数据优先级
    "kline": ["tdx", "akshare", "baostock"],
    
    # 财务数据优先级
    "financial": ["tushare", "akshare", "cninfo"],
    
    # 新闻数据优先级
    "news": ["unified_news", "akshare"],
    
    # 板块数据优先级
    "sector": ["akshare", "tdx"],
    
    # 资金流向优先级
    "fund_flow": ["akshare", "tushare"],
}
```

## 缓存策略统一

```python
CACHE_CONFIG = {
    # 实时行情 - 5秒
    "quote": {"ttl": 5, "max_size": 10000},
    
    # K线 - 5分钟
    "kline": {"ttl": 300, "max_size": 5000},
    
    # 财务 - 1小时
    "financial": {"ttl": 3600, "max_size": 2000},
    
    # 新闻 - 5分钟
    "news": {"ttl": 300, "max_size": 10000},
    
    # 板块 - 1分钟
    "sector": {"ttl": 60, "max_size": 500},
    
    # 资金流向 - 1分钟
    "fund_flow": {"ttl": 60, "max_size": 2000},
}
```

## 实施步骤

1. **Phase 1**: 创建统一数据服务框架
2. **Phase 2**: 迁移行情数据
3. **Phase 3**: 迁移K线数据
4. **Phase 4**: 迁移财务数据
5. **Phase 5**: 迁移新闻数据
6. **Phase 6**: 迁移板块数据
7. **Phase 7**: 废弃旧接口，统一入口

## 预期收益

- **代码量**: 减少40%（消除重复代码）
- **维护成本**: 降低60%（统一维护点）
- **响应速度**: 提升30%（统一缓存）
- **稳定性**: 提升50%（统一降级）
