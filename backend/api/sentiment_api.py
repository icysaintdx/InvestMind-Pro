"""
市场情绪分析API
提供市场情绪、恐慌贪婪指数、ARBR指标等分析接口
"""

from fastapi import APIRouter, HTTPException, Query

from backend.utils.logging_config import get_logger
from backend.dataflows.sentiment import market_sentiment_fetcher

logger = get_logger("api.sentiment")
router = APIRouter(prefix="/api/sentiment", tags=["Market Sentiment Analysis"])


# ==================== 市场整体情绪 ====================

@router.get("/market")
async def get_market_sentiment():
    """
    获取市场整体情绪数据

    返回:
    - 市场涨跌统计
    - 涨跌停统计
    - 恐慌贪婪指数
    - 北向资金
    - 融资融券数据
    """
    try:
        result = market_sentiment_fetcher.get_market_sentiment()
        return result
    except Exception as e:
        logger.error(f"[市场情绪] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/fear-greed")
async def get_fear_greed_index():
    """
    获取市场恐慌贪婪指数

    综合涨跌家数、涨跌停比例、涨跌幅分布计算
    返回0-100的指数值:
    - 0-25: 极度恐慌
    - 25-40: 恐慌
    - 40-60: 中性
    - 60-75: 贪婪
    - 75-100: 极度贪婪
    """
    try:
        result = market_sentiment_fetcher.get_market_sentiment()
        if result.get("success"):
            return {
                "success": True,
                "fear_greed_index": result.get("fear_greed_index", {}),
                "timestamp": result.get("timestamp")
            }
        return result
    except Exception as e:
        logger.error(f"[恐慌贪婪指数] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market-stats")
async def get_market_stats():
    """
    获取市场涨跌统计

    返回:
    - 涨跌家数
    - 涨跌比例
    - 涨跌幅分布
    - 市场情绪得分
    """
    try:
        result = market_sentiment_fetcher.get_market_sentiment()
        if result.get("success"):
            return {
                "success": True,
                "market_stats": result.get("market_stats", {}),
                "timestamp": result.get("timestamp")
            }
        return result
    except Exception as e:
        logger.error(f"[市场统计] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/limit-stats")
async def get_limit_stats():
    """
    获取涨跌停统计

    返回:
    - 涨停股数量和列表
    - 跌停股数量和列表
    - 涨跌停比例
    """
    try:
        result = market_sentiment_fetcher.get_market_sentiment()
        if result.get("success"):
            return {
                "success": True,
                "limit_stats": result.get("limit_stats", {}),
                "timestamp": result.get("timestamp")
            }
        return result
    except Exception as e:
        logger.error(f"[涨跌停统计] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/north-flow")
async def get_north_flow():
    """
    获取北向资金流向

    返回:
    - 北向资金净流入
    - 沪股通净流入
    - 深股通净流入
    """
    try:
        result = market_sentiment_fetcher.get_market_sentiment()
        if result.get("success"):
            return {
                "success": True,
                "north_flow": result.get("north_flow", {}),
                "timestamp": result.get("timestamp")
            }
        return result
    except Exception as e:
        logger.error(f"[北向资金] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/margin-trading")
async def get_margin_trading():
    """
    获取融资融券数据

    返回:
    - 融资余额
    - 融券余额
    - 融资买入额
    """
    try:
        result = market_sentiment_fetcher.get_market_sentiment()
        if result.get("success"):
            return {
                "success": True,
                "margin_trading": result.get("margin_trading", {}),
                "timestamp": result.get("timestamp")
            }
        return result
    except Exception as e:
        logger.error(f"[融资融券] 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 个股情绪 ====================

@router.get("/stock/{stock_code}")
async def get_stock_sentiment(stock_code: str):
    """
    获取个股情绪数据

    返回:
    - ARBR指标
    - 换手率数据
    - 成交量分析
    """
    try:
        result = market_sentiment_fetcher.get_stock_sentiment(stock_code)
        return result
    except Exception as e:
        logger.error(f"[个股情绪] {stock_code} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_code}/arbr")
async def get_stock_arbr(stock_code: str):
    """
    获取个股ARBR指标

    ARBR是衡量市场人气和意愿的技术指标:
    - AR (人气指标): 反映市场买卖人气
    - BR (意愿指标): 反映市场买卖意愿

    信号解读:
    - AR > 150: 超买信号
    - AR < 70: 超卖信号
    - BR > 300: 超买信号
    - BR < 50: 超卖信号
    """
    try:
        result = market_sentiment_fetcher.get_stock_sentiment(stock_code)
        if result.get("success"):
            return {
                "success": True,
                "stock_code": stock_code,
                "arbr_data": result.get("arbr_data", {}),
                "timestamp": result.get("timestamp")
            }
        return result
    except Exception as e:
        logger.error(f"[ARBR指标] {stock_code} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_code}/turnover")
async def get_stock_turnover(stock_code: str):
    """
    获取个股换手率

    换手率解读:
    - > 20%: 极高，可能存在炒作
    - 10-20%: 较高，交易活跃
    - 5-10%: 正常
    - 2-5%: 偏低
    - < 2%: 很低，交易清淡
    """
    try:
        result = market_sentiment_fetcher.get_stock_sentiment(stock_code)
        if result.get("success"):
            return {
                "success": True,
                "stock_code": stock_code,
                "turnover_data": result.get("turnover_data", {}),
                "timestamp": result.get("timestamp")
            }
        return result
    except Exception as e:
        logger.error(f"[换手率] {stock_code} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_code}/volume")
async def get_stock_volume_analysis(stock_code: str):
    """
    获取个股成交量分析

    量比解读:
    - > 3: 极高，成交异常放大
    - 1.5-3: 较高，成交活跃
    - 0.8-1.5: 正常
    - 0.5-0.8: 偏低，成交萎缩
    - < 0.5: 极低，成交极度萎缩
    """
    try:
        result = market_sentiment_fetcher.get_stock_sentiment(stock_code)
        if result.get("success"):
            return {
                "success": True,
                "stock_code": stock_code,
                "volume_analysis": result.get("volume_analysis", {}),
                "timestamp": result.get("timestamp")
            }
        return result
    except Exception as e:
        logger.error(f"[成交量分析] {stock_code} 错误: {e}")
        raise HTTPException(status_code=500, detail=str(e))
