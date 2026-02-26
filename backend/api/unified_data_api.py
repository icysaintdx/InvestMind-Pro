"""
统一数据API路由
"""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime

from backend.utils.logging_config import get_logger
from backend.dataflows.unified import (
    Symbol, MarketType, TickData, OHLCV, SectorInfo,
    DataPriority, unified_data_service, provider_manager
)

logger = get_logger("api.unified_data")
router = APIRouter(prefix="/api/v2/data", tags=["Unified Data"])


@router.get("/tick/{code}")
async def get_tick(
    code: str,
    market: str = Query("a_share", description="市场类型"),
    exchange: Optional[str] = Query(None, description="交易所SH/SZ"),
):
    """获取实时Tick数据"""
    try:
        market_type = MarketType(market)
        symbol = Symbol(code, market_type, exchange)
        
        tick = await unified_data_service.get_tick(symbol)
        
        if not tick:
            raise HTTPException(status_code=404, detail="数据未找到")
        
        return {
            "success": True,
            "data": {
                "symbol": str(tick.symbol),
                "price": tick.price,
                "change_pct": tick.change_pct,
                "volume": tick.volume,
                "bid": tick.bid,
                "ask": tick.ask,
                "timestamp": tick.timestamp.isoformat(),
            }
        }
    except Exception as e:
        logger.error(f"[UnifiedDataAPI] get_tick error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/klines/{code}")
async def get_klines(
    code: str,
    market: str = Query("a_share", description="市场类型"),
    exchange: Optional[str] = Query(None, description="交易所SH/SZ"),
    timeframe: str = Query("1d", description="时间周期1m/5m/15m/1h/1d/1w"),
    limit: int = Query(100, ge=1, le=1000),
):
    """获取K线数据"""
    try:
        market_type = MarketType(market)
        symbol = Symbol(code, market_type, exchange)
        
        klines = await unified_data_service.get_klines(
            symbol, timeframe=timeframe, limit=limit
        )
        
        return {
            "success": True,
            "data": [
                {
                    "timestamp": k.timestamp.isoformat(),
                    "open": k.open,
                    "high": k.high,
                    "low": k.low,
                    "close": k.close,
                    "volume": k.volume,
                }
                for k in klines
            ],
            "count": len(klines),
        }
    except Exception as e:
        logger.error(f"[UnifiedDataAPI] get_klines error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sectors")
async def get_sectors(
    market: str = Query("a_share", description="市场类型"),
    sector_type: str = Query("industry", description="板块类型industry/concept"),
):
    """获取板块列表"""
    try:
        market_type = MarketType(market)
        
        sectors = await unified_data_service.get_sectors(
            market=market_type, sector_type=sector_type
        )
        
        return {
            "success": True,
            "data": [
                {
                    "code": s.code,
                    "name": s.name,
                    "change_pct": s.change_pct,
                    "turnover": s.turnover,
                    "fund_flow": s.fund_flow,
                }
                for s in sectors
            ],
            "count": len(sectors),
        }
    except Exception as e:
        logger.error(f"[UnifiedDataAPI] get_sectors error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/overview")
async def get_market_overview(
    market: str = Query("a_share", description="市场类型"),
):
    """获取市场概览"""
    try:
        market_type = MarketType(market)
        overview = await unified_data_service.get_market_overview(market_type)
        
        return {
            "success": True,
            "data": {
                "total_stocks": overview.total_stocks,
                "up_count": overview.up_count,
                "down_count": overview.down_count,
                "flat_count": overview.flat_count,
                "limit_up_count": overview.limit_up_count,
                "limit_down_count": overview.limit_down_count,
                "total_turnover": overview.total_turnover,
                "sentiment_score": overview.sentiment_score,
                "timestamp": overview.timestamp.isoformat(),
            }
        }
    except Exception as e:
        logger.error(f"[UnifiedDataAPI] get_market_overview error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def get_health():
    """获取系统健康状态"""
    try:
        health = await unified_data_service.health_check()
        return {
            "success": True,
            "data": health,
        }
    except Exception as e:
        logger.error(f"[UnifiedDataAPI] health check error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
