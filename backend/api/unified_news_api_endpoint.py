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
from backend.utils.log_stream_handler import attach_log_stream, detach_log_stream
from backend.api.agent_logs_api import end_agent_log_stream

logger = get_logger("unified_news_endpoint")

router = APIRouter(prefix="/api/unified-news", tags=["Unified News"])


class StockNewsRequest(BaseModel):
    """股票新闻请求"""
    ticker: str
    agent_id: Optional[str] = "news_analyst"  # 智能体ID，用于日志流
    

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
    获取股票综合新闻（带实时日志流）
    
    整合多个数据源：
    - 实时新闻聚合器
    - AKShare个股新闻
    - 财联社快讯
    - 微博热议
    - 情绪分析
    
    日志会实时推送到前端，显示在智能体卡片中
    """
    agent_id = request.agent_id
    
    # 附加日志流处理器到多个 logger
    handler1 = attach_log_stream("unified_news_endpoint", agent_id)
    handler2 = attach_log_stream("unified_news", agent_id)  # 也附加到 unified_news logger
    handler3 = attach_log_stream("agents", agent_id)  # 附加到 agents logger
    handler4 = attach_log_stream("akshare_news", agent_id)  # 附加到 akshare_news logger
    
    try:
        logger.info(f"收到股票新闻请求: {request.ticker}")
        logger.info(f"开始获取{request.ticker}的综合新闻数据...")
        
        api = get_unified_news_api()
        result = api.get_stock_news_comprehensive(request.ticker)
        
        logger.info("✅ 综合新闻数据获取完成")
        
        # 结束日志流
        end_agent_log_stream(agent_id)
        
        return StockNewsResponse(
            success=True,
            ticker=request.ticker,
            timestamp=datetime.now().isoformat(),
            data=result
        )
        
    except Exception as e:
        logger.error(f"❌ 获取股票新闻失败: {e}")
        end_agent_log_stream(agent_id)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # 移除所有日志流处理器
        detach_log_stream("unified_news_endpoint", handler1)
        detach_log_stream("unified_news", handler2)
        detach_log_stream("agents", handler3)
        detach_log_stream("akshare_news", handler4)


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
