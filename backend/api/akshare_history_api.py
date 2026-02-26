"""
AKShare历史数据扩展API
提供个股资金流向、龙虎榜、大宗交易、融资融券、涨停/跌停/炸板池等RESTful接口
路由前缀: /api/data
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from utils.logging_config import get_logger
from services.akshare_data_service import (
    get_individual_fund_flow,
    get_lhb_history,
    get_block_trade,
    get_margin_detail,
    get_zt_pool,
    get_dt_pool,
    get_zb_pool,
    get_cache_stats,
    clear_cache,
)

logger = get_logger("api.akshare_history")
router = APIRouter(prefix="/api/data", tags=["AKShare历史数据"])


# ==================== 个股资金流向 ====================

@router.get("/fund-flow/{stock_code}")
async def api_fund_flow(stock_code: str):
    """
    获取个股历史资金流向

    Args:
        stock_code: 股票代码（如 000001、600519）

    Returns:
        flow: 个股历史资金流向明细
        rank: 今日资金流向排名
    """
    try:
        data = await get_individual_fund_flow(stock_code)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"[资金流向] {stock_code} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取资金流向失败: {e}")


# ==================== 龙虎榜历史 ====================

@router.get("/lhb/history")
async def api_lhb_history(
    date: Optional[str] = Query(None, description="日期 YYYYMMDD，默认最近交易日"),
    jgzz_period: str = Query("5", description="机构驻扎周期: 5/10/30/60"),
):
    """
    获取龙虎榜历史明细

    Returns:
        detail: 龙虎榜每日明细（新浪）
        jgzz: 机构驻扎排名
    """
    try:
        data = await get_lhb_history(date=date, jgzz_period=jgzz_period)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"[龙虎榜] 失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取龙虎榜失败: {e}")


# ==================== 大宗交易 ====================

@router.get("/block-trade/{stock_code}")
async def api_block_trade(
    stock_code: str,
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
):
    """
    获取大宗交易数据

    Args:
        stock_code: 股票代码

    Returns:
        stats: 大宗交易市场统计
        detail: 大宗交易明细（按股票过滤）
    """
    try:
        data = await get_block_trade(
            stock_code=stock_code, start_date=start_date, end_date=end_date
        )
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"[大宗交易] {stock_code} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取大宗交易失败: {e}")


# ==================== 融资融券 ====================

@router.get("/margin/{stock_code}")
async def api_margin(
    stock_code: str,
    date: Optional[str] = Query(None, description="日期 YYYYMMDD"),
):
    """
    获取融资融券明细（深交所+上交所合并）

    Args:
        stock_code: 股票代码

    Returns:
        szse: 深交所融资融券
        sse: 上交所融资融券
        combined: 合并数据
    """
    try:
        data = await get_margin_detail(stock_code=stock_code, date=date)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"[融资融券] {stock_code} 失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取融资融券失败: {e}")


# ==================== 涨停板池 ====================

@router.get("/zt-pool")
async def api_zt_pool(
    date: Optional[str] = Query(None, description="日期 YYYYMMDD，默认今天"),
):
    """
    获取涨停板池（涨停+强势股）

    Returns:
        zt_pool: 涨停板池
        strong_pool: 强势股池
    """
    try:
        data = await get_zt_pool(date=date)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"[涨停池] 失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取涨停池失败: {e}")


# ==================== 跌停板池 ====================

@router.get("/dt-pool")
async def api_dt_pool(
    date: Optional[str] = Query(None, description="日期 YYYYMMDD，默认今天"),
):
    """
    获取跌停板池

    Returns:
        dt_pool: 跌停板池
    """
    try:
        data = await get_dt_pool(date=date)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"[跌停池] 失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取跌停池失败: {e}")


# ==================== 炸板池 ====================

@router.get("/zb-pool")
async def api_zb_pool(
    date: Optional[str] = Query(None, description="日期 YYYYMMDD，默认今天"),
):
    """
    获取炸板池（涨停后打开）

    Returns:
        zb_pool: 炸板池
    """
    try:
        data = await get_zb_pool(date=date)
        return {"success": True, "data": data}
    except Exception as e:
        logger.error(f"[炸板池] 失败: {e}")
        raise HTTPException(status_code=500, detail=f"获取炸板池失败: {e}")


# ==================== 缓存管理 ====================

@router.get("/cache/stats")
async def api_cache_stats():
    """获取缓存统计信息"""
    return {"success": True, "data": get_cache_stats()}


@router.post("/cache/clear")
async def api_cache_clear():
    """清空所有缓存"""
    clear_cache()
    return {"success": True, "message": "缓存已清空"}
