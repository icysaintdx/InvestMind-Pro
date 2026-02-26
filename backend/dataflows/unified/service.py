"""
统一数据服务
对外提供标准化的数据访问接口
"""

from typing import Optional, List, Dict, Any, AsyncIterator
from datetime import datetime
import asyncio

from backend.utils.logging_config import get_logger
from .models import (
    Symbol, MarketType, TickData, OHLCV, MarketDepth,
    FinancialMetrics, NewsItem, SectorInfo, DataPriority,
    MarketOverview, FundFlow
)
from .cache_manager import cache_manager
from .circuit_breaker import provider_manager

logger = get_logger("dataflows.unified.service")


class UnifiedDataService:
    """
    统一数据服务
    
    所有数据访问的统一入口，自动处理：
    - 缓存命中
    - Provider选择
    - 熔断降级
    - 错误处理
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._setup_providers()
        logger.info("[UnifiedDataService] 初始化完成")
    
    def _setup_providers(self):
        """设置并注册Provider"""
        try:
            # 注册TDX Provider
            from .providers.tdx_provider import TDXProvider
            tdx = TDXProvider()
            provider_manager.register_provider("tdx", tdx)
            logger.info("[UnifiedDataService] TDX Provider 已注册")
        except Exception as e:
            logger.warning(f"[UnifiedDataService] TDX Provider 注册失败: {e}")
        
        try:
            # 注册AKShare Provider
            from .providers.akshare_provider import AKShareProvider
            akshare = AKShareProvider()
            provider_manager.register_provider("akshare", akshare)
            logger.info("[UnifiedDataService] AKShare Provider 已注册")
        except Exception as e:
            logger.warning(f"[UnifiedDataService] AKShare Provider 注册失败: {e}")
        
        try:
            # 注册统一新闻Provider
            from .providers.news_provider import UnifiedNewsProvider
            news = UnifiedNewsProvider()
            provider_manager.register_provider("unified_news", news)
            logger.info("[UnifiedDataService] UnifiedNews Provider 已注册")
        except Exception as e:
            logger.warning(f"[UnifiedDataService] UnifiedNews Provider 注册失败: {e}")
    
    # ========== 实时行情 ==========
    
    async def get_tick(
        self,
        symbol: Symbol,
        priority: DataPriority = DataPriority.FAST
    ) -> Optional[TickData]:
        """获取最新Tick数据"""
        # 先查缓存
        cache_key = f"{symbol.market.value}:{symbol.code}"
        cached = cache_manager.get("tick", cache_key)
        if cached:
            return cached
        
        # 从Provider获取
        result = await provider_manager.execute_with_fallback(
            "get_tick", symbol, priority
        )
        
        if result:
            cache_manager.set("tick", cache_key, result)
        
        return result
    
    async def get_quotes(
        self,
        symbols: List[Symbol],
        priority: DataPriority = DataPriority.FAST
    ) -> List[TickData]:
        """批量获取行情数据"""
        # 分批获取，避免单次请求过多
        batch_size = 50
        all_results = []
        
        for i in range(0, len(symbols), batch_size):
            batch = symbols[i:i+batch_size]
            
            # 检查缓存
            cached_results = []
            missing_symbols = []
            
            for symbol in batch:
                cache_key = f"{symbol.market.value}:{symbol.code}"
                cached = cache_manager.get("tick", cache_key)
                if cached:
                    cached_results.append(cached)
                else:
                    missing_symbols.append(symbol)
            
            # 获取缺失的数据
            if missing_symbols:
                # 使用批量接口（如果Provider支持）
                batch_result = await provider_manager.execute_with_fallback(
                    "get_ticks", missing_symbols[0], priority, symbols=missing_symbols
                )
                
                if batch_result:
                    for tick in batch_result:
                        cache_key = f"{tick.symbol.market.value}:{tick.symbol.code}"
                        cache_manager.set("tick", cache_key, tick)
                    all_results.extend(batch_result)
            
            all_results.extend(cached_results)
        
        return all_results
    
    # ========== K线数据 ==========
    
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
        # 检查缓存
        cache_key = f"{symbol.market.value}:{symbol.code}:{timeframe}:{limit}"
        cached = cache_manager.get("klines", cache_key)
        if cached:
            return cached
        
        # 从Provider获取
        result = await provider_manager.execute_with_fallback(
            "get_klines", symbol, priority,
            timeframe=timeframe, start=start, end=end, limit=limit
        )
        
        if result:
            cache_manager.set("klines", cache_key, result)
        
        return result or []
    
    async def get_latest_kline(
        self,
        symbol: Symbol,
        timeframe: str = "1d"
    ) -> Optional[OHLCV]:
        """获取最新K线"""
        klines = await self.get_klines(symbol, timeframe, limit=1)
        return klines[0] if klines else None
    
    # ========== 板块数据 ==========
    
    async def get_sectors(
        self,
        market: MarketType = MarketType.A_SHARE,
        sector_type: str = "industry",
        priority: DataPriority = DataPriority.FAST
    ) -> List[SectorInfo]:
        """获取板块列表"""
        # 检查缓存
        cache_key = f"{market.value}:{sector_type}"
        cached = cache_manager.get("sector", cache_key)
        if cached:
            return cached
        
        # 从Provider获取
        result = await provider_manager.execute_with_fallback_no_symbol(
            "get_sectors", market, priority,
            sector_type=sector_type
        )
        
        if result:
            cache_manager.set("sector", cache_key, result)
        
        return result or []
    
    async def get_sector_detail(
        self,
        sector_code: str,
        market: MarketType = MarketType.A_SHARE
    ) -> Optional[SectorInfo]:
        """获取板块详情"""
        sectors = await self.get_sectors(market)
        for sector in sectors:
            if sector.code == sector_code:
                return sector
        return None
    
    # ========== 市场概览 ==========
    
    async def get_market_overview(
        self,
        market: MarketType = MarketType.A_SHARE
    ) -> MarketOverview:
        """获取市场概览"""
        # 获取全市场数据
        try:
            # 使用AKShare获取全市场实时行情
            import akshare as ak
            
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            
            if df is None or df.empty:
                return MarketOverview(market=market, timestamp=datetime.now())
            
            # 计算统计
            up_count = len(df[df['涨跌幅'] > 0])
            down_count = len(df[df['涨跌幅'] < 0])
            flat_count = len(df[df['涨跌幅'] == 0])
            
            # 涨停跌停（A股±10%，创业板±20%）
            limit_up = len(df[df['涨跌幅'] >= 9.9])
            limit_down = len(df[df['涨跌幅'] <= -9.9])
            
            # 总成交额
            total_turnover = df['成交额'].sum() if '成交额' in df.columns else 0
            
            # 市场情绪分（0-100）
            if len(df) > 0:
                sentiment = up_count / len(df) * 100
            else:
                sentiment = 50
            
            return MarketOverview(
                market=market,
                timestamp=datetime.now(),
                total_stocks=len(df),
                up_count=up_count,
                down_count=down_count,
                flat_count=flat_count,
                limit_up_count=limit_up,
                limit_down_count=limit_down,
                total_turnover=float(total_turnover),
                sentiment_score=sentiment,
            )
            
        except Exception as e:
            logger.error(f"[UnifiedDataService] 获取市场概览失败: {e}")
            return MarketOverview(market=market, timestamp=datetime.now())
    
    async def get_hot_stocks(
        self,
        market: MarketType = MarketType.A_SHARE,
        limit: int = 20
    ) -> List[Symbol]:
        """获取热门股票（成交额最高）"""
        try:
            import akshare as ak
            
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            
            if df is None or df.empty:
                return []
            
            # 按成交额排序
            df = df.nlargest(limit, '成交额')
            
            symbols = []
            for _, row in df.iterrows():
                code = str(row.get('代码', ''))
                if code:
                    exchange = 'SH' if code.startswith('6') else 'SZ'
                    symbols.append(Symbol(code, market, exchange))
            
            return symbols
            
        except Exception as e:
            logger.error(f"[UnifiedDataService] 获取热门股票失败: {e}")
            return []
    
    # ========== 盘口数据 ==========
    
    async def get_depth(
        self,
        symbol: Symbol,
        priority: DataPriority = DataPriority.FAST
    ) -> Optional[MarketDepth]:
        """获取盘口数据（五档买卖）"""
        # 检查缓存
        cache_key = f"{symbol.market.value}:{symbol.code}:depth"
        cached = cache_manager.get("depth", cache_key)
        if cached:
            return cached
        
        # 从Provider获取
        result = await provider_manager.execute_with_fallback(
            "get_depth", symbol, priority
        )
        
        if result:
            cache_manager.set("depth", cache_key, result)  # 盘口数据缓存
        
        return result
    
    # ========== 板块成分股 ==========
    
    async def get_sector_stocks(
        self,
        sector_name: str,
        sector_type: str = "industry",
        priority: DataPriority = DataPriority.FAST
    ) -> List[TickData]:
        """获取板块成分股列表"""
        # 检查缓存
        cache_key = f"{sector_type}:{sector_name}:stocks"
        cached = cache_manager.get("sector_stocks", cache_key)
        if cached:
            return cached
        
        # 从Provider获取
        result = await provider_manager.execute_with_fallback_no_symbol(
            "get_sector_stocks", MarketType.A_SHARE, priority,
            sector_name=sector_name, sector_type=sector_type
        )
        
        if result:
            cache_manager.set("sector_stocks", cache_key, result)  # 板块成分股缓存
        
        return result or []
    
    # ========== 健康检查 ==========
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        return {
            "cache_stats": cache_manager.get_stats(),
            "provider_health": provider_manager.get_health_report(),
        }


# 全局实例
unified_data_service = UnifiedDataService()
