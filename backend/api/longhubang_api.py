"""
龙虎榜分析API
提供龙虎榜数据查询和分析功能
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from backend.utils.logging_config import get_logger
from backend.dataflows.longhubang import longhubang_data_fetcher

logger = get_logger("api.longhubang")
router = APIRouter(prefix="/api/longhubang", tags=["龙虎榜分析"])


# ==================== 数据模型 ====================

class LHBDataResponse(BaseModel):
    """龙虎榜数据响应"""
    success: bool
    data: List[Dict[str, Any]]
    count: int
    date: Optional[str] = None
    message: Optional[str] = None


class LHBSummaryResponse(BaseModel):
    """龙虎榜摘要响应"""
    success: bool
    summary: Dict[str, Any]
    formatted_text: Optional[str] = None


class LHBStockDetailResponse(BaseModel):
    """龙虎榜股票详情响应"""
    success: bool
    stock_code: str
    date: str
    buy_seats: List[Dict[str, Any]]
    sell_seats: List[Dict[str, Any]]


# ==================== API端点 ====================

@router.get("/daily", response_model=LHBDataResponse)
async def get_daily_longhubang(
    date: Optional[str] = Query(None, description="日期，格式YYYY-MM-DD，默认昨天")
):
    """
    获取指定日期的龙虎榜数据

    Args:
        date: 日期，格式YYYY-MM-DD

    Returns:
        龙虎榜数据列表
    """
    try:
        logger.info(f"获取龙虎榜数据: {date or '最近交易日'}")

        result = longhubang_data_fetcher.get_longhubang_data(date)

        return LHBDataResponse(
            success=result.get('success', False),
            data=result.get('data', []),
            count=result.get('count', 0),
            date=result.get('date'),
            message=result.get('message')
        )

    except Exception as e:
        logger.error(f"获取龙虎榜数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_longhubang(
    days: int = Query(5, ge=1, le=30, description="获取最近N个交易日的数据")
):
    """
    获取最近N个交易日的龙虎榜数据

    Args:
        days: 天数，默认5天

    Returns:
        龙虎榜数据列表和统计摘要
    """
    try:
        logger.info(f"获取最近 {days} 天龙虎榜数据")

        data_list = longhubang_data_fetcher.get_recent_days_data(days)
        summary = longhubang_data_fetcher.analyze_data_summary(data_list)

        return {
            "success": True,
            "data": data_list,
            "count": len(data_list),
            "days": days,
            "summary": summary
        }

    except Exception as e:
        logger.error(f"获取龙虎榜数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_code}")
async def get_stock_lhb_detail(
    stock_code: str,
    date: Optional[str] = Query(None, description="日期，格式YYYY-MM-DD")
):
    """
    获取单只股票的龙虎榜详情（买卖席位）

    Args:
        stock_code: 股票代码
        date: 日期

    Returns:
        席位详情
    """
    try:
        logger.info(f"获取股票 {stock_code} 龙虎榜详情")

        result = longhubang_data_fetcher.get_lhb_stock_detail(stock_code, date)

        return result

    except Exception as e:
        logger.error(f"获取龙虎榜详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/institution")
async def get_institution_stat(
    days: int = Query(5, ge=1, le=30, description="统计天数")
):
    """
    获取机构席位统计

    Args:
        days: 统计天数

    Returns:
        机构买卖统计
    """
    try:
        logger.info(f"获取机构席位统计")

        result = longhubang_data_fetcher.get_lhb_institution_stat(days)

        return result

    except Exception as e:
        logger.error(f"获取机构统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/traders")
async def get_trader_stat(
    days: int = Query(5, ge=1, le=30, description="统计天数")
):
    """
    获取营业部统计（活跃游资）

    Args:
        days: 统计天数

    Returns:
        营业部排行
    """
    try:
        logger.info(f"获取营业部统计")

        result = longhubang_data_fetcher.get_lhb_trader_stat(days)

        return result

    except Exception as e:
        logger.error(f"获取营业部统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/summary")
async def get_lhb_summary(
    days: int = Query(5, ge=1, le=30, description="统计天数")
):
    """
    获取龙虎榜综合摘要（适合AI分析）

    Args:
        days: 统计天数

    Returns:
        格式化的摘要文本
    """
    try:
        logger.info(f"获取龙虎榜摘要")

        data_list = longhubang_data_fetcher.get_recent_days_data(days)
        summary = longhubang_data_fetcher.analyze_data_summary(data_list)
        formatted_text = longhubang_data_fetcher.format_data_for_ai(data_list, summary)

        # 转换字段名以匹配前端期望
        # 前端期望: total_stocks, total_buy, total_sell, net_buy
        # 后端返回: total_stocks, total_buy_amount, total_sell_amount, total_net_amount
        frontend_data = {
            "total_stocks": summary.get("total_stocks", 0),
            "total_buy": summary.get("total_buy_amount", 0),
            "total_sell": summary.get("total_sell_amount", 0),
            "net_buy": summary.get("total_net_amount", 0),
            # 保留原始字段
            "total_records": summary.get("total_records", 0),
            "top_stocks": summary.get("top_stocks", []),
            "reason_stats": summary.get("reason_stats", {})
        }

        return {
            "success": True,
            "data": frontend_data,  # 前端使用 result.data
            "summary": summary,  # 保留原始summary
            "formatted_text": formatted_text,
            "data_count": len(data_list)
        }

    except Exception as e:
        logger.error(f"获取龙虎榜摘要失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/{stock_code}")
async def analyze_stock_lhb(
    stock_code: str,
    days: int = Query(30, ge=1, le=90, description="分析天数")
):
    """
    分析单只股票的龙虎榜历史

    Args:
        stock_code: 股票代码
        days: 分析天数

    Returns:
        股票龙虎榜分析结果
    """
    try:
        logger.info(f"分析股票 {stock_code} 龙虎榜历史")

        # 获取最近的龙虎榜数据
        data_list = longhubang_data_fetcher.get_recent_days_data(days)

        # 筛选该股票的数据
        stock_data = [d for d in data_list if d.get('stock_code') == stock_code]

        if not stock_data:
            return {
                "success": True,
                "stock_code": stock_code,
                "message": f"最近 {days} 天内该股票未上龙虎榜",
                "lhb_count": 0,
                "data": []
            }

        # 统计分析
        total_buy = sum(d.get('lhb_buy_amount', 0) for d in stock_data)
        total_sell = sum(d.get('lhb_sell_amount', 0) for d in stock_data)
        total_net = sum(d.get('lhb_net_amount', 0) for d in stock_data)

        return {
            "success": True,
            "stock_code": stock_code,
            "stock_name": stock_data[0].get('stock_name', ''),
            "lhb_count": len(stock_data),
            "total_buy_amount": total_buy,
            "total_sell_amount": total_sell,
            "total_net_amount": total_net,
            "avg_change_pct": sum(d.get('change_pct', 0) for d in stock_data) / len(stock_data),
            "data": stock_data
        }

    except Exception as e:
        logger.error(f"分析龙虎榜失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
