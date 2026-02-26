"""
统一数据中心 API 适配器
提供新旧API兼容层，逐步迁移前端调用 - 带缓存优化
"""

from fastapi import APIRouter, HTTPException
from typing import Optional
import asyncio
import time

from backend.utils.logging_config import get_logger
from backend.dataflows.unified import (
    Symbol, MarketType, unified_data_service, DataPriority
)

logger = get_logger("api.unified_adapter")
router = APIRouter(prefix="/api/sector-rotation", tags=["板块轮动-新API适配"])

# 缓存配置
_cache = {}
_cache_time = {}
_CACHE_TTL_TRADING = 60       # 交易时段1分钟（数据变化快）
_CACHE_TTL_NON_TRADING = 3600  # 非交易时段1小时（数据不变）


def _is_trading_time():
    from datetime import datetime
    now = datetime.now()
    if now.weekday() >= 5:
        return False
    hm = now.hour * 100 + now.minute
    return 915 <= hm <= 1530


def _get_cache(key: str):
    """获取缓存（非交易时段TTL延长到1小时）"""
    ttl = _CACHE_TTL_TRADING if _is_trading_time() else _CACHE_TTL_NON_TRADING
    if key in _cache and time.time() - _cache_time.get(key, 0) < ttl:
        return _cache[key]
    return None


def _set_cache(key: str, data):
    """设置缓存"""
    _cache[key] = data
    _cache_time[key] = time.time()


@router.get("/sectors")
async def get_sectors(type: str = "industry"):
    """板块列表 - 兼容旧API格式（带缓存）"""
    cache_key = f"sectors_{type}"
    cached = _get_cache(cache_key)
    if cached:
        logger.debug(f"[板块轮动适配器] 返回{type}板块缓存")
        return cached
    
    try:
        sectors = await unified_data_service.get_sectors(
            market=MarketType.A_SHARE,
            sector_type=type,
            priority=DataPriority.FAST
        )
        
        data = []
        for s in sectors:
            data.append({
                "name": s.name,
                "code": s.code,
                "change_pct": s.change_pct,
                "turnover": s.turnover,
                "top_stock": "",
            })
        
        result = {
            "success": True,
            "data": data,
            "count": len(data),
            "source": "unified_data_center"
        }
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"[板块轮动适配器] 获取{type}板块失败: {e}")
        return {"success": True, "data": [], "count": 0}


@router.get("/industry-sectors")
async def get_industry_sectors():
    """行业板块 - 使用统一数据中心（带缓存）"""
    cache_key = "industry_sectors"
    cached = _get_cache(cache_key)
    if cached:
        logger.debug("[板块轮动适配器] 返回行业板块缓存")
        return cached
    
    try:
        sectors = await unified_data_service.get_sectors(
            market=MarketType.A_SHARE,
            sector_type="industry",
            priority=DataPriority.FAST
        )
        
        data = []
        for s in sectors:
            data.append({
                "name": s.name,
                "code": s.code,
                "change_pct": s.change_pct,
                "turnover": s.turnover,
                "top_stock": "",
            })
        
        result = {
            "success": True,
            "data": data,
            "count": len(data),
            "source": "unified_data_center"
        }
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"[板块轮动适配器] 获取行业板块失败: {e}")
        return {"success": True, "data": [], "count": 0}


@router.get("/concept-sectors")
async def get_concept_sectors():
    """概念板块 - 使用统一数据中心（带缓存）"""
    cache_key = "concept_sectors"
    cached = _get_cache(cache_key)
    if cached:
        logger.debug("[板块轮动适配器] 返回概念板块缓存")
        return cached
    
    try:
        sectors = await unified_data_service.get_sectors(
            market=MarketType.A_SHARE,
            sector_type="concept",
            priority=DataPriority.FAST
        )
        
        data = []
        for s in sectors:
            data.append({
                "name": s.name,
                "code": s.code,
                "change_pct": s.change_pct,
                "turnover": s.turnover,
                "top_stock": "",
            })
        
        result = {
            "success": True,
            "data": data,
            "count": len(data),
            "source": "unified_data_center"
        }
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"[板块轮动适配器] 获取概念板块失败: {e}")
        return {"success": True, "data": [], "count": 0}


@router.get("/fund-flow")
async def get_sector_fund_flow():
    """板块资金流向 - 使用统一数据中心（带缓存）"""
    cache_key = "fund_flow"
    cached = _get_cache(cache_key)
    if cached:
        logger.debug("[板块轮动适配器] 返回资金流向缓存")
        return cached
    
    try:
        sectors = await unified_data_service.get_sectors(
            market=MarketType.A_SHARE,
            sector_type="industry",
            priority=DataPriority.FAST
        )
        
        # 转换格式兼容旧前端 - 使用涨跌幅估算资金流向
        data = []
        for s in sectors:
            # 使用涨跌幅作为资金流向指标（如果没有fund_flow）
            fund_flow = s.fund_flow if s.fund_flow else (s.change_pct * 1000000)  # 模拟数据
            data.append({
                "sector": s.name,
                "main_net_inflow": fund_flow,
                "main_net_inflow_pct": s.change_pct,
            })
        
        # 按净流入排序
        data.sort(key=lambda x: abs(x["main_net_inflow"]), reverse=True)
        
        result = {
            "success": True,
            "data": data[:20],  # 只返回前20
            "source": "unified_data_center"
        }
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"[板块轮动适配器] 获取资金流向失败: {e}")
        return {"success": True, "data": []}


@router.get("/analysis/heat")
async def get_sector_heat():
    """板块热度 - 使用统一数据中心（带缓存）"""
    cache_key = "heat"
    cached = _get_cache(cache_key)
    if cached:
        logger.debug("[板块轮动适配器] 返回板块热度缓存")
        return cached
    
    try:
        sectors = await unified_data_service.get_sectors(
            market=MarketType.A_SHARE,
            sector_type="industry",
            priority=DataPriority.FAST
        )
        
        # 按涨跌幅排序分类
        sorted_sectors = sorted(sectors, key=lambda x: x.change_pct, reverse=True)
        
        hottest = [{"sector": s.name, "heat_score": s.change_pct} for s in sorted_sectors[:10]]
        heating = [{"sector": s.name, "heat_score": s.change_pct} for s in sorted_sectors[10:20]]
        cooling = [{"sector": s.name, "heat_score": s.change_pct} for s in sorted_sectors[-10:]]
        
        result = {
            "success": True,
            "hottest": hottest,
            "heating": heating,
            "cooling": cooling,
            "source": "unified_data_center"
        }
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"[板块轮动适配器] 获取板块热度失败: {e}")
        return {"success": True, "hottest": [], "heating": [], "cooling": []}


@router.get("/analysis/rotation")
async def get_sector_rotation():
    """板块轮动信号 - 使用统一数据中心（带缓存）"""
    cache_key = "rotation"
    cached = _get_cache(cache_key)
    if cached:
        logger.debug("[板块轮动适配器] 返回轮动信号缓存")
        return cached
    
    try:
        sectors = await unified_data_service.get_sectors(
            market=MarketType.A_SHARE,
            sector_type="industry",
            priority=DataPriority.FAST
        )
        
        # 按涨跌幅分类
        current_strong = [{"sector": s.name, "change_pct": s.change_pct} for s in sectors if s.change_pct > 2]
        potential = [{"sector": s.name, "change_pct": s.change_pct} for s in sectors if 0 < s.change_pct <= 2]
        declining = [{"sector": s.name, "change_pct": s.change_pct} for s in sectors if s.change_pct < 0]
        
        result = {
            "success": True,
            "current_strong": current_strong[:10],
            "potential": potential[:10],
            "declining": declining[:10],
            "total_sectors": len(sectors),
            "source": "unified_data_center"
        }
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"[板块轮动适配器] 获取轮动信号失败: {e}")
        return {"success": True, "current_strong": [], "potential": [], "declining": [], "total_sectors": 0}


@router.get("/sector-stocks/{sector_name}")
async def get_sector_stocks(sector_name: str, sector_type: str = "industry"):
    """板块成分股 - 使用统一数据中心（带缓存）"""
    cache_key = f"sector_stocks_{sector_name}_{sector_type}"
    cached = _get_cache(cache_key)
    if cached:
        logger.debug(f"[板块轮动适配器] 返回{sector_name}成分股缓存")
        return cached
    
    try:
        stocks = await unified_data_service.get_sector_stocks(
            sector_name=sector_name,
            sector_type=sector_type,
            priority=DataPriority.FAST
        )
        
        data = []
        for s in stocks:
            data.append({
                "code": s.symbol.code,
                "name": s.name,
                "price": s.price,
                "change_pct": s.change_pct,
                "volume": s.volume,
            })
        
        result = {
            "success": True,
            "sector": sector_name,
            "stocks": data,
            "count": len(data),
            "source": "unified_data_center"
        }
        _set_cache(cache_key, result)
        return result
        
    except Exception as e:
        logger.error(f"[板块轮动适配器] 获取{sector_name}成分股失败: {e}")
        return {"success": True, "sector": sector_name, "stocks": [], "count": 0}
