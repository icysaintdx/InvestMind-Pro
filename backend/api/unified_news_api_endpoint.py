#!/usr/bin/env python3
"""
统一新闻API端点
供前端调用
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import datetime

from backend.dataflows.news.unified_news_api import get_unified_news_api
from backend.dataflows.news.hot_search_api import get_hot_search_api
from backend.utils.logging_config import get_logger

logger = get_logger("unified_news_endpoint")

router = APIRouter(prefix="/api/unified-news", tags=["Unified News"])


class StockNewsRequest(BaseModel):
    """股票新闻请求"""
    ticker: str
    

class StockNewsResponse(BaseModel):
    """股票新闻响应"""
    success: bool
    ticker: str
    timestamp: str
    data: dict
    message: Optional[str] = None


@router.post("/stock", response_model=StockNewsResponse)
async def get_stock_comprehensive_news(request: StockNewsRequest):
    """
    获取股票综合新闻
    
    整合多个数据源：
    - 实时新闻聚合器
    - AKShare个股新闻
    - 财联社快讯
    - 微博热议
    - 情绪分析
    """
    try:
        logger.info(f"收到股票新闻请求: {request.ticker}")
        
        api = get_unified_news_api()
        result = api.get_stock_news_comprehensive(request.ticker)
        
        return StockNewsResponse(
            success=True,
            ticker=request.ticker,
            timestamp=datetime.now().isoformat(),
            data=result
        )
        
    except Exception as e:
        logger.error(f"获取股票新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market")
async def get_market_news():
    """
    获取市场新闻
    
    包含：
    - 财经早餐
    - 全球财经新闻
    """
    try:
        logger.info("收到市场新闻请求")
        
        api = get_unified_news_api()
        result = api.get_market_news()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取市场新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/hot-search")
async def get_hot_search():
    """
    获取热搜数据
    
    包含：
    - 微博热搜
    - 百度热搜
    - 股票相关话题过滤
    """
    try:
        logger.info("收到热搜请求")
        
        api = get_hot_search_api()
        result = api.get_all_stock_hot_topics()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "data": result
        }
        
    except Exception as e:
        logger.error(f"获取热搜失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """健康检查"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "endpoints": [
            "/api/unified-news/stock",
            "/api/unified-news/market",
            "/api/unified-news/hot-search"
        ]
    }
