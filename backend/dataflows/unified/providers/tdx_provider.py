"""
TDX Provider 实现
基于 pytdx 的A股数据Provider
"""

import asyncio
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from backend.utils.logging_config import get_logger
from ..base_provider import BaseProvider, register_provider
from ..models import (
    Symbol, MarketType, TickData, OHLCV, MarketDepth,
    FinancialMetrics, NewsItem, SectorInfo, DataPriority
)
from ..cache_manager import cache_manager

logger = get_logger("provider.tdx")


@register_provider("tdx")
class TDXProvider(BaseProvider):
    """
    TDX通达信数据Provider
    
    特点：
    - 实时行情速度快
    - 支持Level-2数据
    - 支持历史K线
    """
    
    def __init__(self):
        super().__init__("tdx", [MarketType.A_SHARE])
        self._api = None
        self._connected = False
        self._hosts = [
            ("124.71.187.122", 7709),
            ("122.51.120.217", 7709),
            ("111.229.247.189", 7709),
        ]
        self._current_host_idx = 0
    
    def _get_api(self):
        """获取TDX API连接"""
        if self._api is None:
            try:
                from pytdx.hq import TdxHq_API
                self._api = TdxHq_API()
                self._connect()
            except ImportError:
                logger.error("pytdx未安装，请运行: pip install pytdx")
                raise
        return self._api
    
    def _connect(self):
        """连接TDX服务器"""
        if self._connected:
            return
        
        for i, (host, port) in enumerate(self._hosts):
            try:
                if self._api.connect(host, port, time_out=5):
                    self._connected = True
                    self._current_host_idx = i
                    logger.info(f"[TDX] 连接成功: {host}:{port}")
                    return
            except Exception as e:
                logger.debug(f"[TDX] 连接失败 {host}:{port}: {e}")
        
        raise ConnectionError("[TDX] 所有服务器连接失败")
    
    def _code_to_tdx(self, symbol: Symbol) -> tuple:
        """转换为TDX格式"""
        # 0=深圳, 1=上海
        if symbol.code.startswith('6'):
            return 1, symbol.code  # 上海
        else:
            return 0, symbol.code  # 深圳
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            api = self._get_api()
            market, code = self._code_to_tdx(Symbol("000001", MarketType.A_SHARE, "SZ"))
            result = api.get_security_quotes([(market, code)])
            return len(result) > 0
        except Exception as e:
            logger.error(f"[TDX] 健康检查失败: {e}")
            return False
    
    async def get_tick(self, symbol: Symbol) -> Optional[TickData]:
        """获取实时Tick数据"""
        if not self._check_market_support(symbol):
            return None
        
        cache_key = f"{symbol.code}"
        cached = cache_manager.get("tick", cache_key)
        if cached:
            return cached
        
        try:
            api = self._get_api()
            market, code = self._code_to_tdx(symbol)
            
            result = await asyncio.to_thread(
                api.get_security_quotes, [(market, code)]
            )
            
            if not result:
                return None
            
            quote = result[0]
            
            # 判断是否是指数（指数价格不需要除以100）
            is_index = symbol.code in ['000001', '399001', '399006', '000688', '000016', '000300', '399005']
            price_divisor = 1 if is_index else 100
            
            tick = TickData(
                symbol=symbol,
                timestamp=datetime.now(),
                price=float(quote.get('price', 0)) / price_divisor,
                volume=int(quote.get('vol', 0)),
                bid=float(quote.get('bid1', 0)) / price_divisor,
                ask=float(quote.get('ask1', 0)) / price_divisor,
                bid_volume=int(quote.get('bid_vol1', 0)),
                ask_volume=int(quote.get('ask_vol1', 0)),
                change_pct=float(quote.get('price', 0) - quote.get('last_close', 0)) / quote.get('last_close', 1) * 100 if quote.get('last_close') else 0,
                open=float(quote.get('open', 0)) / price_divisor,
                high=float(quote.get('high', 0)) / price_divisor,
                low=float(quote.get('low', 0)) / price_divisor,
                pre_close=float(quote.get('last_close', 0)) / price_divisor,
            )
            
            cache_manager.set("tick", cache_key, tick)
            return tick
            
        except Exception as e:
            self._handle_error("get_tick", e)
            return None
    
    async def get_ticks(self, symbols: List[Symbol]) -> List[TickData]:
        """批量获取Tick数据"""
        tasks = [self.get_tick(s) for s in symbols]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None]
    
    async def get_klines(
        self,
        symbol: Symbol,
        timeframe: str = "1d",
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: int = 500
    ) -> List[OHLCV]:
        """获取K线数据"""
        if not self._check_market_support(symbol):
            return []
        
        # TDX K线类型映射
        kline_type_map = {
            "1m": 0, "5m": 1, "15m": 2, "30m": 3, "1h": 4,
            "1d": 9, "1w": 5, "1M": 6
        }
        kline_type = kline_type_map.get(timeframe, 9)
        
        cache_key = f"{symbol.code}_{timeframe}_{limit}"
        cached = cache_manager.get("klines", cache_key)
        if cached:
            return cached
        
        try:
            api = self._get_api()
            market, code = self._code_to_tdx(symbol)
            
            result = await asyncio.to_thread(
                api.get_security_bars,
                kline_type, market, code, 0, limit
            )
            
            if not result:
                return []
            
            klines = []
            for bar in result:
                try:
                    ohlcv = OHLCV(
                        symbol=symbol,
                        timestamp=datetime.strptime(bar.get('datetime', ''), '%Y-%m-%d %H:%M'),
                        open=float(bar.get('open', 0)) / 100,
                        high=float(bar.get('high', 0)) / 100,
                        low=float(bar.get('low', 0)) / 100,
                        close=float(bar.get('close', 0)) / 100,
                        volume=int(bar.get('vol', 0)),
                        turnover=float(bar.get('amount', 0)),
                        timeframe=timeframe,
                    )
                    klines.append(ohlcv)
                except Exception as e:
                    logger.debug(f"[TDX] 解析K线失败: {e}")
                    continue
            
            if klines:
                cache_manager.set("klines", cache_key, klines)
            
            return klines
            
        except Exception as e:
            self._handle_error("get_klines", e)
            return []
    
    async def get_depth(self, symbol: Symbol) -> Optional[MarketDepth]:
        """获取盘口深度"""
        if not self._check_market_support(symbol):
            return None
        
        try:
            api = self._get_api()
            market, code = self._code_to_tdx(symbol)
            
            # 获取10档盘口
            result = await asyncio.to_thread(
                api.get_security_quotes, [(market, code)]
            )
            
            if not result:
                return None
            
            quote = result[0]
            
            bids = []
            asks = []
            for i in range(1, 6):
                bid_price = quote.get(f'bid{i}', 0) / 100
                bid_vol = quote.get(f'bid_vol{i}', 0)
                ask_price = quote.get(f'ask{i}', 0) / 100
                ask_vol = quote.get(f'ask_vol{i}', 0)
                
                if bid_price > 0:
                    bids.append((bid_price, bid_vol))
                if ask_price > 0:
                    asks.append((ask_price, ask_vol))
            
            return MarketDepth(
                symbol=symbol,
                timestamp=datetime.now(),
                bids=bids,
                asks=asks,
            )
            
        except Exception as e:
            self._handle_error("get_depth", e)
            return None
    
    async def get_sectors(
        self,
        market: MarketType = MarketType.A_SHARE,
        sector_type: str = "industry"
    ) -> List[SectorInfo]:
        """获取板块数据（TDX不支持，返回空）"""
        return []
    
    async def get_financial(self, symbol: Symbol, report_type: str = "income", period: Optional[str] = None) -> Optional[FinancialMetrics]:
        """TDX不提供财务数据"""
        return None
    
    async def get_news(self, symbols: Optional[List[Symbol]] = None, hours: int = 24, limit: int = 100) -> List[NewsItem]:
        """TDX不提供新闻"""
        return []
