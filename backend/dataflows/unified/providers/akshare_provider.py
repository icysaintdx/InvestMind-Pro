"""
AKShare Provider 实现
基于 AKShare 的A股数据Provider
"""

import asyncio
import akshare as ak
from typing import Optional, List, Dict, Any
from datetime import datetime

from backend.utils.logging_config import get_logger
from ..base_provider import BaseProvider, register_provider
from ..models import (
    Symbol, MarketType, TickData, OHLCV, MarketDepth,
    FinancialMetrics, NewsItem, SectorInfo, FundFlow
)
from ..cache_manager import cache_manager

logger = get_logger("provider.akshare")


@register_provider("akshare")
class AKShareProvider(BaseProvider):
    """
    AKShare数据Provider
    
    特点：
    - 数据源丰富（东方财富、新浪等）
    - 支持多种数据类型
    - 免费开源
    """
    
    def __init__(self):
        super().__init__("akshare", [MarketType.A_SHARE])
        self._request_delay = 0.5  # 请求间隔，避免被封
    
    def _code_to_symbol(self, symbol: Symbol) -> str:
        """转换为AKShare格式"""
        if symbol.code.startswith('6'):
            return f"sh{symbol.code}"
        else:
            return f"sz{symbol.code}"
    
    async def health_check(self) -> bool:
        """健康检查"""
        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            return len(df) > 0
        except Exception as e:
            logger.error(f"[AKShare] 健康检查失败: {e}")
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
            # 使用东方财富实时行情
            ak_code = self._code_to_symbol(symbol)
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            
            if df is None or df.empty:
                return None
            
            # 过滤指定股票
            row = df[df['代码'] == symbol.code]
            if row.empty:
                return None
            
            row = row.iloc[0]
            
            tick = TickData(
                symbol=symbol,
                timestamp=datetime.now(),
                price=float(row.get('最新价', 0)),
                volume=int(row.get('成交量', 0)),
                bid=float(row.get('买一', 0)),
                ask=float(row.get('卖一', 0)),
                bid_volume=int(row.get('买一盘', 0)),
                ask_volume=int(row.get('卖一盘', 0)),
                change_pct=float(row.get('涨跌幅', 0)),
                turnover=float(row.get('成交额', 0)),
                open=float(row.get('开盘价', 0)),
                high=float(row.get('最高价', 0)),
                low=float(row.get('最低价', 0)),
                pre_close=float(row.get('昨收', 0)),
            )
            
            cache_manager.set("tick", cache_key, tick)
            return tick
            
        except Exception as e:
            self._handle_error("get_tick", e)
            return None
    
    async def get_ticks(self, symbols: List[Symbol]) -> List[TickData]:
        """批量获取Tick数据（一次请求获取全市场，再过滤）"""
        try:
            df = await asyncio.to_thread(ak.stock_zh_a_spot_em)
            
            if df is None or df.empty:
                return []
            
            symbol_codes = {s.code for s in symbols}
            ticks = []
            
            for _, row in df.iterrows():
                code = str(row.get('代码', ''))
                if code not in symbol_codes:
                    continue
                
                symbol = next(s for s in symbols if s.code == code)
                
                try:
                    tick = TickData(
                        symbol=symbol,
                        timestamp=datetime.now(),
                        price=float(row.get('最新价', 0)),
                        volume=int(row.get('成交量', 0)),
                        bid=float(row.get('买一', 0)),
                        ask=float(row.get('卖一', 0)),
                        bid_volume=int(row.get('买一盘', 0)),
                        ask_volume=int(row.get('卖一盘', 0)),
                        change_pct=float(row.get('涨跌幅', 0)),
                        turnover=float(row.get('成交额', 0)),
                        open=float(row.get('开盘价', 0)),
                        high=float(row.get('最高价', 0)),
                        low=float(row.get('最低价', 0)),
                        pre_close=float(row.get('昨收', 0)),
                    )
                    ticks.append(tick)
                except Exception as e:
                    logger.debug(f"[AKShare] 解析{code}失败: {e}")
                    continue
            
            return ticks
            
        except Exception as e:
            self._handle_error("get_ticks", e)
            return []
    
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
        
        cache_key = f"{symbol.code}_{timeframe}_{limit}"
        cached = cache_manager.get("klines", cache_key)
        if cached:
            return cached
        
        try:
            # 使用新浪财经历史数据
            ak_code = self._code_to_symbol(symbol)
            
            df = await asyncio.to_thread(
                ak.stock_zh_a_daily,
                symbol=ak_code,
                start_date=start.strftime('%Y%m%d') if start else None,
                end_date=end.strftime('%Y%m%d') if end else None,
                adjust="qfq"  # 前复权
            )
            
            if df is None or df.empty:
                return []
            
            klines = []
            for _, row in df.tail(limit).iterrows():
                try:
                    ohlcv = OHLCV(
                        symbol=symbol,
                        timestamp=datetime.strptime(str(row.get('date', '')), '%Y-%m-%d'),
                        open=float(row.get('open', 0)),
                        high=float(row.get('high', 0)),
                        low=float(row.get('low', 0)),
                        close=float(row.get('close', 0)),
                        volume=int(row.get('volume', 0)),
                        turnover=float(row.get('amount', 0)) if 'amount' in row else None,
                        timeframe=timeframe,
                    )
                    klines.append(ohlcv)
                except Exception as e:
                    logger.debug(f"[AKShare] 解析K线失败: {e}")
                    continue
            
            if klines:
                cache_manager.set("klines", cache_key, klines)
            
            return klines
            
        except Exception as e:
            self._handle_error("get_klines", e)
            return []
    
    async def get_sectors(
        self,
        market: MarketType = MarketType.A_SHARE,
        sector_type: str = "industry"
    ) -> List[SectorInfo]:
        """获取板块数据"""
        # 直接检查market是否在支持的市场列表中
        if market not in self._supported_markets:
            logger.warning(f"[{self._name}] 不支持市场: {market}")
            return []
        
        cache_key = f"{sector_type}_top50"
        cached = cache_manager.get("sector", cache_key)
        if cached:
            return cached
        
        try:
            if sector_type == "industry":
                df = await asyncio.to_thread(ak.stock_board_industry_name_em)
            else:
                df = await asyncio.to_thread(ak.stock_board_concept_name_em)
            
            if df is None or df.empty:
                return []
            
            # 只取前50
            df = df.head(50)
            
            sectors = []
            for _, row in df.iterrows():
                try:
                    sector = SectorInfo(
                        code=str(row.get('板块代码', '')),
                        name=str(row.get('板块名称', '')),
                        market=market,
                        sector_type=sector_type,
                        change_pct=float(row.get('涨跌幅', 0)),
                        turnover=float(row.get('换手率', 0)) if '换手率' in row else None,
                        fund_flow=float(row.get('主力净流入', 0)) if '主力净流入' in row else None,
                    )
                    sectors.append(sector)
                except Exception as e:
                    logger.debug(f"[AKShare] 解析板块失败: {e}")
                    continue
            
            if sectors:
                cache_manager.set("sector", cache_key, sectors)
            
            return sectors
            
        except Exception as e:
            self._handle_error("get_sectors", e)
            return []
    
    async def get_sector_fund_flow(self, sector_code: str, sector_type: str = "industry") -> Optional[FundFlow]:
        """获取板块资金流向"""
        # AKShare不提供此功能
        return None
    
    async def get_sector_stocks(
        self,
        sector_name: str,
        sector_type: str = "industry"
    ) -> List[TickData]:
        """获取板块成分股"""
        cache_key = f"{sector_type}_{sector_name}_stocks"
        cached = cache_manager.get("sector_stocks", cache_key)
        if cached:
            return cached
        
        try:
            if sector_type == "industry":
                df = await asyncio.to_thread(ak.stock_board_industry_cons_em, symbol=sector_name)
            else:
                df = await asyncio.to_thread(ak.stock_board_concept_cons_em, symbol=sector_name)
            
            if df is None or df.empty:
                return []
            
            stocks = []
            for _, row in df.iterrows():
                try:
                    code = str(row.get('代码', ''))
                    name = str(row.get('名称', ''))
                    
                    # 获取实时行情
                    tick = TickData(
                        symbol=Symbol(code=code, market=MarketType.A_SHARE),
                        timestamp=datetime.now(),
                        name=name,
                        price=float(row.get('最新价', 0)) if '最新价' in row else 0,
                        change_pct=float(row.get('涨跌幅', 0)) if '涨跌幅' in row else 0,
                        volume=int(row.get('成交量', 0)) if '成交量' in row else 0,
                        turnover=float(row.get('成交额', 0)) if '成交额' in row else 0,
                    )
                    stocks.append(tick)
                except Exception as e:
                    logger.debug(f"[AKShare] 解析成分股失败: {e}")
                    continue
            
            if stocks:
                cache_manager.set("sector_stocks", cache_key, stocks)
            
            return stocks
            
        except Exception as e:
            self._handle_error("get_sector_stocks", e)
            return []
    
    async def get_depth(self, symbol: Symbol) -> Optional[MarketDepth]:
        """AKShare不提供深度盘口"""
        return None
    
    async def get_financial(self, symbol: Symbol, report_type: str = "income", period: Optional[str] = None) -> Optional[FinancialMetrics]:
        """获取财务数据"""
        # 简化实现，返回None，实际可从profit或finance接口获取
        return None
    
    async def get_news(self, symbols: Optional[List[Symbol]] = None, hours: int = 24, limit: int = 100) -> List[NewsItem]:
        """获取新闻"""
        # AKShare新闻获取较复杂，暂不实现
        return []
