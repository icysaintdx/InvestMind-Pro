"""
统一新闻API接口

提供统一的新闻获取、搜索、筛选等RESTful API接口。
"""

from fastapi import APIRouter, Query, HTTPException
from typing import List, Optional
from datetime import datetime
import logging

from ..dataflows.unified_news import (
    UnifiedNewsService,
    UnifiedNewsResponse,
    NewsStatistics,
    NewsSourceInfo
)
from ..dataflows.unified_news.news_service import get_unified_news_service

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/unified-news", tags=["统一新闻"])


@router.get("/list", response_model=dict)
async def get_news_list(
    markets: Optional[str] = Query(None, description="市场筛选，多个用逗号分隔，如：A股,港股,美股"),
    sources: Optional[str] = Query(None, description="数据源筛选，多个用逗号分隔，如：东方财富,财联社,问财"),
    news_types: Optional[str] = Query(None, description="类型筛选，多个用逗号分隔，如：个股新闻,市场要闻,公告"),
    sentiments: Optional[str] = Query(None, description="情绪筛选，多个用逗号分隔，如：积极,中性,消极"),
    stock_code: Optional[str] = Query(None, description="股票代码"),
    keyword: Optional[str] = Query(None, description="关键词搜索"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    sort_by: str = Query("publish_time", description="排序字段：publish_time/relevance_score/sentiment_score"),
    sort_order: str = Query("desc", description="排序方向：asc/desc")
):
    """
    获取新闻列表
    
    支持多维度筛选：市场、数据源、类型、情绪、股票代码、关键词、时间范围
    """
    try:
        service = get_unified_news_service()
        
        # 解析参数
        markets_list = markets.split(",") if markets else None
        sources_list = sources.split(",") if sources else None
        news_types_list = news_types.split(",") if news_types else None
        sentiments_list = sentiments.split(",") if sentiments else None
        
        # 解析日期
        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        
        response = await service.get_news_list(
            markets=markets_list,
            sources=sources_list,
            news_types=news_types_list,
            sentiments=sentiments_list,
            stock_code=stock_code,
            keyword=keyword,
            start_date=start_dt,
            end_date=end_dt,
            page=page,
            page_size=page_size,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"获取新闻列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{stock_code}", response_model=dict)
async def get_stock_news(
    stock_code: str,
    limit: int = Query(50, ge=1, le=200, description="返回数量限制")
):
    """
    获取个股新闻
    
    Args:
        stock_code: 股票代码，如：600519、000001
        limit: 返回数量限制
    """
    try:
        service = get_unified_news_service()
        response = await service.get_stock_news(stock_code, limit)
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"获取个股新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/{market}", response_model=dict)
async def get_market_news(
    market: str,
    limit: int = Query(50, ge=1, le=200, description="返回数量限制")
):
    """
    获取市场新闻
    
    Args:
        market: 市场类型，如：A股、港股、美股、全球
        limit: 返回数量限制
    """
    try:
        service = get_unified_news_service()
        response = await service.get_market_news(market, limit)
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"获取市场新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/realtime", response_model=dict)
async def get_realtime_news(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    获取实时新闻流
    
    返回最新的新闻，不使用缓存
    """
    try:
        service = get_unified_news_service()
        response = await service.get_realtime_news(limit)
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"获取实时新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/search", response_model=dict)
async def search_news(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制")
):
    """
    全文搜索新闻
    
    Args:
        keyword: 搜索关键词
        limit: 返回数量限制
    """
    try:
        service = get_unified_news_service()
        response = await service.search_news(keyword, limit)
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"搜索新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources", response_model=dict)
async def get_sources():
    """
    获取可用数据源列表
    
    返回所有已注册的新闻数据源信息
    """
    try:
        service = get_unified_news_service()
        sources = await service.get_sources()
        
        return {
            "success": True,
            "sources": [s.to_dict() for s in sources]
        }
        
    except Exception as e:
        logger.error(f"获取数据源列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics", response_model=dict)
async def get_statistics(
    markets: Optional[str] = Query(None, description="市场筛选，多个用逗号分隔"),
    start_date: Optional[str] = Query(None, description="开始日期，格式：YYYY-MM-DD"),
    end_date: Optional[str] = Query(None, description="结束日期，格式：YYYY-MM-DD")
):
    """
    获取新闻统计信息
    
    返回按市场、数据源、类型、情绪的统计数据
    """
    try:
        service = get_unified_news_service()
        
        markets_list = markets.split(",") if markets else None
        start_dt = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        end_dt = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None
        
        statistics = await service.get_statistics(
            markets=markets_list,
            start_date=start_dt,
            end_date=end_dt
        )
        
        return {
            "success": True,
            "statistics": statistics.to_dict()
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sentiment", response_model=dict)
async def get_sentiment_analysis(
    stock_code: Optional[str] = Query(None, description="股票代码"),
    market: Optional[str] = Query(None, description="市场类型"),
    days: int = Query(7, ge=1, le=30, description="分析天数")
):
    """
    获取情绪分析结果
    
    分析指定股票或市场的新闻情绪趋势
    """
    try:
        service = get_unified_news_service()
        result = await service.get_sentiment_analysis(
            stock_code=stock_code,
            market=market,
            days=days
        )
        return result
        
    except Exception as e:
        logger.error(f"获取情绪分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/sync", response_model=dict)
async def sync_news(
    sources: Optional[str] = Query(None, description="指定数据源，多个用逗号分隔"),
    force: bool = Query(False, description="是否强制刷新（忽略缓存）")
):
    """
    手动触发新闻同步
    
    从指定数据源获取最新新闻
    """
    try:
        service = get_unified_news_service()
        
        sources_list = sources.split(",") if sources else None
        result = await service.sync_news(sources=sources_list, force=force)
        
        return result
        
    except Exception as e:
        logger.error(f"新闻同步失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health", response_model=dict)
async def health_check():
    """
    健康检查
    
    检查所有数据源的可用性
    """
    try:
        service = get_unified_news_service()
        result = await service.health_check()
        return result
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# 便捷接口

@router.get("/hot", response_model=dict)
async def get_hot_news(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    获取热点新闻
    
    返回当前热门新闻
    """
    try:
        service = get_unified_news_service()
        response = await service.get_news_list(
            page_size=limit,
            sort_by="relevance_score",
            sort_order="desc"
        )
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"获取热点新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/positive", response_model=dict)
async def get_positive_news(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    获取利好新闻
    
    返回情绪积极的新闻
    """
    try:
        service = get_unified_news_service()
        response = await service.get_news_list(
            sentiments=["积极"],
            page_size=limit,
            sort_by="sentiment_score",
            sort_order="desc"
        )
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"获取利好新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/negative", response_model=dict)
async def get_negative_news(
    limit: int = Query(20, ge=1, le=100, description="返回数量限制")
):
    """
    获取利空新闻
    
    返回情绪消极的新闻
    """
    try:
        service = get_unified_news_service()
        response = await service.get_news_list(
            sentiments=["消极"],
            page_size=limit,
            sort_by="sentiment_score",
            sort_order="asc"
        )
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"获取利空新闻失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/announcements", response_model=dict)
async def get_announcements(
    stock_code: Optional[str] = Query(None, description="股票代码"),
    limit: int = Query(50, ge=1, le=200, description="返回数量限制")
):
    """
    获取公告
    
    返回公司公告类新闻
    """
    try:
        service = get_unified_news_service()
        response = await service.get_news_list(
            stock_code=stock_code,
            news_types=["公告"],
            page_size=limit
        )
        return response.to_dict()
        
    except Exception as e:
        logger.error(f"获取公告失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))