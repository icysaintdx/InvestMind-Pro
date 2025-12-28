"""
问财智能选股API
提供基于pywencai的自然语言股票筛选功能
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional

from backend.utils.logging_config import get_logger
from backend.services.wencai_selector import wencai_selector

logger = get_logger("api.wencai")
router = APIRouter(prefix="/api/wencai", tags=["Wencai Stock Selection"])


# ==================== 数据模型 ====================

class WencaiQueryRequest(BaseModel):
    """问财查询请求"""
    query: str = Field(..., description="自然语言查询条件")
    top_n: int = Field(default=50, ge=1, le=200, description="返回结果数量")


class WencaiResponse(BaseModel):
    """问财查询响应"""
    success: bool
    message: str
    data: List[Dict[str, Any]] = []
    count: int = 0
    columns: List[str] = []


# ==================== API端点 ====================

@router.get("/status")
async def get_wencai_status():
    """获取问财服务状态"""
    return {
        "success": True,
        "available": wencai_selector.is_available,
        "message": "pywencai模块可用" if wencai_selector.is_available else "pywencai模块未安装，请执行: pip install pywencai"
    }


@router.post("/query", response_model=WencaiResponse)
async def wencai_query(request: WencaiQueryRequest):
    """
    执行自然语言股票查询

    示例查询:
    - "涨停，沪深A股，非ST"
    - "市盈率<20，ROE>15%，沪深A股"
    - "主力资金净流入>1亿，涨跌幅>3%"
    """
    try:
        logger.info(f"[问财查询] {request.query}")
        result = wencai_selector.query(request.query, request.top_n)

        return WencaiResponse(
            success=result.get('success', False),
            message=result.get('message', ''),
            data=result.get('data', []),
            count=result.get('count', 0),
            columns=result.get('columns', [])
        )
    except Exception as e:
        logger.error(f"[问财查询] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 预设策略端点 ====================

@router.get("/strategy/profit-growth")
async def get_profit_growth_stocks(top_n: int = Query(default=20, ge=1, le=100)):
    """
    净利增长选股

    筛选条件:
    - 净利润增长率 ≥ 10%
    - 非ST、非科创板、非创业板
    - 按成交额排序
    """
    try:
        result = wencai_selector.get_profit_growth_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[净利增长选股] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/small-cap-growth")
async def get_small_cap_growth_stocks(top_n: int = Query(default=20, ge=1, le=100)):
    """
    小市值高增长选股

    筛选条件:
    - 总市值 ≤ 50亿
    - 营收增长率 ≥ 10%
    - 净利润增长率 ≥ 50%
    - 非ST
    """
    try:
        result = wencai_selector.get_small_cap_growth_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[小市值高增长选股] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/main-force-inflow")
async def get_main_force_inflow_stocks(top_n: int = Query(default=20, ge=1, le=100)):
    """
    主力资金净流入选股

    筛选条件:
    - 主力资金净流入 > 0
    - 涨跌幅 > 0
    - 非ST
    """
    try:
        result = wencai_selector.get_main_force_inflow_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[主力资金净流入选股] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/limit-up")
async def get_limit_up_stocks(top_n: int = Query(default=50, ge=1, le=200)):
    """
    涨停股票

    获取今日涨停的股票
    """
    try:
        result = wencai_selector.get_limit_up_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[涨停股票] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/breakout")
async def get_breakout_stocks(top_n: int = Query(default=20, ge=1, le=100)):
    """
    突破新高选股

    筛选条件:
    - 创60日新高
    - 量比 > 1.5
    - 非ST
    """
    try:
        result = wencai_selector.get_breakout_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[突破新高选股] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/low-pe-value")
async def get_low_pe_value_stocks(top_n: int = Query(default=20, ge=1, le=100)):
    """
    低估值价值股

    筛选条件:
    - 市盈率 < 20 且 > 0
    - 市净率 < 2 且 > 0
    - ROE > 10%
    - 非ST
    """
    try:
        result = wencai_selector.get_low_pe_value_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[低估值价值股] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/dividend")
async def get_dividend_stocks(top_n: int = Query(default=20, ge=1, le=100)):
    """
    高股息股票

    筛选条件:
    - 股息率 > 3%
    - 连续3年分红
    - 非ST
    """
    try:
        result = wencai_selector.get_dividend_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[高股息股票] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/sector-hot")
async def get_sector_hot_stocks(
    sector: str = Query(..., description="板块名称，如'人工智能'、'新能源'"),
    top_n: int = Query(default=20, ge=1, le=100)
):
    """
    板块热门股票

    获取指定板块的热门股票
    """
    try:
        result = wencai_selector.get_sector_hot_stocks(sector, top_n)
        return result
    except Exception as e:
        logger.error(f"[板块热门股票] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/institution-holding")
async def get_institution_holding_stocks(top_n: int = Query(default=20, ge=1, le=100)):
    """
    机构重仓股

    筛选条件:
    - 机构持股比例 > 20%
    - 非ST
    """
    try:
        result = wencai_selector.get_institution_holding_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[机构重仓股] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/northbound-inflow")
async def get_northbound_inflow_stocks(top_n: int = Query(default=20, ge=1, le=100)):
    """
    北向资金流入股

    筛选条件:
    - 北向资金持股
    - 非ST
    """
    try:
        result = wencai_selector.get_northbound_inflow_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[北向资金流入股] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== aiagents-stock 精选策略端点 ====================
# 以下策略来自 aiagents-stock 项目，返回精选的少量优质股票

@router.get("/strategy/main-force-v2")
async def get_main_force_stocks_v2(
    top_n: int = Query(default=5, ge=1, le=100, description="返回股票数量"),
    days_ago: int = Query(default=90, ge=7, le=365, description="距今天数"),
    min_market_cap: float = Query(default=50, ge=10, le=500, description="最小市值(亿)"),
    max_market_cap: float = Query(default=5000, ge=100, le=50000, description="最大市值(亿)"),
    max_range_change: float = Query(default=30, ge=5, le=100, description="最大涨跌幅(%)")
):
    """
    🎯 主力选股 (aiagents-stock 精选版)
    
    智能筛选主力资金净流入排名靠前的股票
    
    筛选条件:
    - 指定日期以来主力资金净流入排名
    - 区间涨跌幅 < max_range_change% (避免追高)
    - 市值范围: min_market_cap - max_market_cap 亿
    - 非ST、非科创板
    
    特点: 返回精选的少量优质标的，适合深度分析
    """
    try:
        result = wencai_selector.get_main_force_stocks_v2(
            top_n=top_n,
            days_ago=days_ago,
            min_market_cap=min_market_cap,
            max_market_cap=max_market_cap,
            max_range_change=max_range_change
        )
        return result
    except Exception as e:
        logger.error(f"[主力选股V2] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/low-price-bull")
async def get_low_price_bull_stocks(top_n: int = Query(default=5, ge=1, le=100)):
    """
    🐂 低价擒牛选股 (aiagents-stock 精选版)
    
    筛选低价高成长的潜力股
    
    筛选条件:
    - 股价 < 10元
    - 净利润增长率 ≥ 100%
    - 非ST、非科创板、非创业板
    - 沪深A股
    - 按成交额由小至大排名 (寻找低关注度的潜力股)
    
    特点: 寻找被市场忽视的低价高成长股
    """
    try:
        result = wencai_selector.get_low_price_bull_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[低价擒牛选股] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/small-cap-v2")
async def get_small_cap_stocks_v2(top_n: int = Query(default=5, ge=1, le=100)):
    """
    🚀 小市值策略 (aiagents-stock 精选版)
    
    筛选小市值高成长股票
    
    筛选条件:
    - 总市值 ≤ 50亿
    - 营收增长率 ≥ 10%
    - 净利润增长率 ≥ 100%
    - 沪深A股、非ST、非创业板、非科创板
    - 按总市值由小到大排名
    
    特点: 更严格的净利增长要求(100% vs 50%)
    """
    try:
        result = wencai_selector.get_small_cap_stocks_v2(top_n)
        return result
    except Exception as e:
        logger.error(f"[小市值策略V2] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/profit-growth-v2")
async def get_profit_growth_stocks_v2(top_n: int = Query(default=5, ge=1, le=100)):
    """
    📈 净利增长选股 (aiagents-stock 精选版)
    
    筛选净利润增长的潜力股
    
    筛选条件:
    - 净利润增长率 ≥ 10%
    - 深圳A股、非科创板、非创业板、非ST
    - 按成交额由小到大排名 (寻找低关注度的潜力股)
    
    特点: 按成交额由小到大排名，寻找被忽视的潜力股
    """
    try:
        result = wencai_selector.get_profit_growth_stocks_v2(top_n)
        return result
    except Exception as e:
        logger.error(f"[净利增长V2] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategy/volume-breakout")
async def get_volume_breakout_stocks(top_n: int = Query(default=5, ge=1, le=100)):
    """
    📊 放量突破选股 (aiagents-stock 风格)
    
    筛选放量突破的强势股
    
    筛选条件:
    - 创20日新高
    - 量比 > 2 (放量)
    - 换手率 > 3%
    - 非ST、沪深A股
    - 按涨跌幅由大至小排名
    
    特点: 寻找放量突破的短线机会
    """
    try:
        result = wencai_selector.get_volume_breakout_stocks(top_n)
        return result
    except Exception as e:
        logger.error(f"[放量突破选股] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 风险数据端点 ====================

@router.get("/risk/{stock_code}")
async def get_stock_risk_data(stock_code: str):
    """
    获取股票风险数据

    包括:
    - 限售解禁信息
    - 大股东减持公告
    - 近期重要事件
    """
    try:
        result = wencai_selector.get_stock_risk_data(stock_code)
        return result
    except Exception as e:
        logger.error(f"[股票风险数据] {stock_code} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 策略列表 ====================

@router.get("/strategies")
async def list_strategies():
    """获取所有可用的预设选股策略"""
    return {
        "success": True,
        "strategies": [
            # ==================== 精选策略 (aiagents-stock 风格) ====================
            {
                "id": "main-force-v2",
                "name": "🔥 主力选股",
                "description": "主力资金净流入排名，过滤涨幅过高股票，精选5只",
                "endpoint": "/api/wencai/strategy/main-force-v2",
                "category": "精选策略",
                "featured": True
            },
            {
                "id": "low-price-bull",
                "name": "🐂 低价擒牛",
                "description": "股价<10元 + 净利增长≥100%，按成交额由小至大排名",
                "endpoint": "/api/wencai/strategy/low-price-bull",
                "category": "精选策略",
                "featured": True
            },
            {
                "id": "small-cap-v2",
                "name": "💎 小市值策略",
                "description": "市值≤50亿 + 营收增长≥10% + 净利增长≥100%",
                "endpoint": "/api/wencai/strategy/small-cap-v2",
                "category": "精选策略",
                "featured": True
            },
            {
                "id": "profit-growth-v2",
                "name": "📈 净利增长",
                "description": "净利增长≥10%，深圳A股，按成交额由小至大排名",
                "endpoint": "/api/wencai/strategy/profit-growth-v2",
                "category": "精选策略",
                "featured": True
            },
            {
                "id": "volume-breakout",
                "name": "📊 放量突破",
                "description": "创20日新高 + 量比>2 + 换手率>3%",
                "endpoint": "/api/wencai/strategy/volume-breakout",
                "category": "精选策略",
                "featured": True
            },
            # ==================== 经典策略 ====================
            {
                "id": "profit-growth",
                "name": "净利增长选股",
                "description": "净利润增长率≥10%，非ST，按成交额排序",
                "endpoint": "/api/wencai/strategy/profit-growth",
                "category": "经典策略",
                "featured": False
            },
            {
                "id": "small-cap-growth",
                "name": "小市值高增长",
                "description": "总市值≤50亿，营收增长≥10%，净利增长≥50%",
                "endpoint": "/api/wencai/strategy/small-cap-growth",
                "category": "经典策略",
                "featured": False
            },
            {
                "id": "main-force-inflow",
                "name": "主力资金净流入",
                "description": "主力资金净流入>0，涨跌幅>0",
                "endpoint": "/api/wencai/strategy/main-force-inflow",
                "category": "经典策略",
                "featured": False
            },
            {
                "id": "limit-up",
                "name": "涨停股票",
                "description": "今日涨停的沪深A股",
                "endpoint": "/api/wencai/strategy/limit-up",
                "category": "经典策略",
                "featured": False
            },
            {
                "id": "breakout",
                "name": "突破新高",
                "description": "创60日新高，量比>1.5",
                "endpoint": "/api/wencai/strategy/breakout",
                "category": "经典策略",
                "featured": False
            },
            {
                "id": "low-pe-value",
                "name": "低估值价值股",
                "description": "PE<20，PB<2，ROE>10%",
                "endpoint": "/api/wencai/strategy/low-pe-value",
                "category": "经典策略",
                "featured": False
            },
            {
                "id": "dividend",
                "name": "高股息股票",
                "description": "股息率>3%，连续3年分红",
                "endpoint": "/api/wencai/strategy/dividend",
                "category": "经典策略",
                "featured": False
            },
            {
                "id": "sector-hot",
                "name": "板块热门股",
                "description": "指定板块的热门股票",
                "endpoint": "/api/wencai/strategy/sector-hot?sector=人工智能",
                "category": "经典策略",
                "featured": False
            },
            {
                "id": "institution-holding",
                "name": "机构重仓股",
                "description": "机构持股比例>20%",
                "endpoint": "/api/wencai/strategy/institution-holding",
                "category": "经典策略",
                "featured": False
            },
            {
                "id": "northbound-inflow",
                "name": "北向资金流入",
                "description": "北向资金持股的股票",
                "endpoint": "/api/wencai/strategy/northbound-inflow",
                "category": "经典策略",
                "featured": False
            }
        ]
    }
