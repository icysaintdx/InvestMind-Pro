"""
板块轮动分析API
提供板块轮动、热度、资金流向等分析接口
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from backend.utils.logging_config import get_logger
from backend.dataflows.sector_rotation import sector_rotation_fetcher, sector_rotation_analyzer

logger = get_logger("api.sector_rotation")
router = APIRouter(prefix="/api/sector-rotation", tags=["Sector Rotation Analysis"])


# ==================== 数据获取端点 ====================

@router.get("/industry-sectors")
async def get_industry_sectors():
    """
    获取行业板块实时行情

    返回所有行业板块的涨跌幅、换手率、领涨股等信息
    """
    try:
        result = sector_rotation_fetcher.get_industry_sectors()
        return result
    except Exception as e:
        logger.error(f"[行业板块] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/concept-sectors")
async def get_concept_sectors():
    """
    获取概念板块实时行情

    返回所有概念板块的涨跌幅、换手率、领涨股等信息
    """
    try:
        result = sector_rotation_fetcher.get_concept_sectors()
        return result
    except Exception as e:
        logger.error(f"[概念板块] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fund-flow")
async def get_sector_fund_flow(
    indicator: str = Query(default="今日", description="时间周期: 今日, 5日, 10日")
):
    """
    获取行业资金流向

    返回各行业的主力资金、超大单、大单等资金流向数据
    """
    try:
        result = sector_rotation_fetcher.get_sector_fund_flow(indicator)
        return result
    except Exception as e:
        logger.error(f"[资金流向] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector-stocks/{sector_name}")
async def get_sector_stocks(
    sector_name: str,
    sector_type: str = Query(default="industry", description="板块类型: industry, concept")
):
    """
    获取板块成分股

    返回指定板块的所有成分股及其行情数据
    """
    try:
        result = sector_rotation_fetcher.get_sector_stocks(sector_name, sector_type)
        return result
    except Exception as e:
        logger.error(f"[板块成分股] {sector_name} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sector-history/{sector_name}")
async def get_sector_history(
    sector_name: str,
    sector_type: str = Query(default="industry", description="板块类型: industry, concept"),
    period: str = Query(default="日k", description="K线周期"),
    adjust: str = Query(default="qfq", description="复权类型")
):
    """
    获取板块历史行情

    返回指定板块的历史K线数据
    """
    try:
        result = sector_rotation_fetcher.get_sector_history(sector_name, sector_type, period, adjust)
        return result
    except Exception as e:
        logger.error(f"[板块历史] {sector_name} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-overview")
async def get_market_overview():
    """
    获取市场总体情况

    返回A股市场涨跌统计、主要指数等信息
    """
    try:
        result = sector_rotation_fetcher.get_market_overview()
        return result
    except Exception as e:
        logger.error(f"[市场概况] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/north-flow")
async def get_north_money_flow():
    """
    获取北向资金流向

    返回沪股通、深股通资金流向数据
    """
    try:
        result = sector_rotation_fetcher.get_north_money_flow()
        return result
    except Exception as e:
        logger.error(f"[北向资金] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 分析端点 ====================

@router.get("/analysis/ranking")
async def analyze_sector_ranking(
    sector_type: str = Query(default="industry", description="板块类型: industry, concept"),
    top_n: int = Query(default=20, ge=1, le=100, description="返回数量")
):
    """
    板块涨跌排名分析

    返回涨幅榜、跌幅榜、活跃榜
    """
    try:
        result = sector_rotation_analyzer.analyze_sector_ranking(sector_type, top_n)
        return result
    except Exception as e:
        logger.error(f"[排名分析] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/fund-flow")
async def analyze_fund_flow_ranking(
    top_n: int = Query(default=20, ge=1, le=100, description="返回数量")
):
    """
    资金流向排名分析

    返回主力流入榜、流出榜、超大单流入榜
    """
    try:
        result = sector_rotation_analyzer.analyze_fund_flow_ranking(top_n)
        return result
    except Exception as e:
        logger.error(f"[资金流向分析] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/heat")
async def analyze_sector_heat(
    top_n: int = Query(default=20, ge=1, le=100, description="返回数量")
):
    """
    板块热度分析

    综合涨跌幅、换手率、资金流入计算热度
    返回最热板块、升温板块、降温板块
    """
    try:
        result = sector_rotation_analyzer.analyze_sector_heat(top_n)
        return result
    except Exception as e:
        logger.error(f"[热度分析] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/rotation")
async def analyze_rotation_signal():
    """
    板块轮动信号分析

    识别当前强势板块、潜力板块、衰退板块
    """
    try:
        result = sector_rotation_analyzer.analyze_rotation_signal()
        return result
    except Exception as e:
        logger.error(f"[轮动分析] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/sector-detail/{sector_name}")
async def get_sector_detail(
    sector_name: str,
    sector_type: str = Query(default="industry", description="板块类型: industry, concept")
):
    """
    获取板块详细信息

    返回板块基本信息、成分股、历史行情
    """
    try:
        result = sector_rotation_analyzer.get_sector_detail(sector_name, sector_type)
        return result
    except Exception as e:
        logger.error(f"[板块详情] {sector_name} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analysis/comprehensive")
async def get_comprehensive_analysis():
    """
    获取综合分析报告

    返回排名、资金流向、热度、轮动信号等综合分析
    """
    try:
        result = sector_rotation_analyzer.get_comprehensive_analysis()
        return result
    except Exception as e:
        logger.error(f"[综合分析] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 综合数据端点 ====================

@router.get("/comprehensive-data")
async def get_comprehensive_data():
    """
    获取综合板块数据

    返回行业板块、概念板块、资金流向、市场概况、北向资金等全部数据
    """
    try:
        result = sector_rotation_fetcher.get_comprehensive_data()
        return result
    except Exception as e:
        logger.error(f"[综合数据] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
