# -*- coding: utf-8 -*-
from fastapi import APIRouter, Query, HTTPException, Body
from typing import Optional, List, Dict
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news-center", tags=["news-center"])

# ==================== 请求模型 ====================

class SourceConfigUpdate(BaseModel):
    """数据源配置更新"""
    enabled: Optional[bool] = None
    interval: Optional[int] = None
    priority: Optional[int] = None
    limit: Optional[int] = None
    days_back: Optional[int] = None

class CninfoConfigUpdate(BaseModel):
    """巨潮配置更新"""
    enabled: Optional[bool] = None
    announcement_enabled: Optional[bool] = None
    announcement_days_back: Optional[int] = None
    announcement_page_size: Optional[int] = None
    status_change_enabled: Optional[bool] = None
    status_change_limit: Optional[int] = None

class HotStocksUpdate(BaseModel):
    """热门股票列表更新"""
    stocks: List[str]

def get_monitor():
    from backend.services.news_center import get_news_monitor_center
    return get_news_monitor_center()

def get_storage():
    """获取新闻存储服务"""
    from backend.services.news_center.news_storage import get_news_storage
    return get_news_storage()

# ==================== 新闻获取API ====================

@router.get("/latest")
async def get_latest_news(
    limit: int = Query(50, ge=1, le=200),
    urgency: Optional[str] = Query(None),
    source: Optional[str] = Query(None),
    stock_code: Optional[str] = Query(None)
):
    try:
        monitor = get_monitor()
        news = monitor.get_latest_news(
            limit=limit,
            urgency=urgency,
            source=source,
            stock_code=stock_code
        )
        return {"success": True, "data": news, "count": len(news)}
    except Exception as e:
        logger.error(f"Get latest news failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/urgent")
async def get_urgent_news(limit: int = Query(500, ge=1, le=5000, description="返回数量限制")):
    try:
        monitor = get_monitor()
        news = monitor.get_urgent_news(limit=limit)
        return {"success": True, "data": news, "count": len(news)}
    except Exception as e:
        logger.error(f"Get urgent news failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{stock_code}")
async def get_news_for_stock(stock_code: str, limit: int = Query(500, ge=1, le=5000, description="返回数量限制")):
    try:
        monitor = get_monitor()
        news = monitor.get_news_for_stock(stock_code, limit=limit)
        return {"success": True, "data": news, "count": len(news), "stock_code": stock_code}
    except Exception as e:
        logger.error(f"Get news for stock failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 市场新闻/个股新闻分离API ====================

@router.get("/market")
async def fetch_market_news(
    limit: int = Query(5000, ge=1, le=10000, description="返回数量限制，默认5000"),
    hours: int = Query(24, ge=1, le=168, description="获取最近N小时的新闻"),
    force_refresh: bool = Query(False, description="强制刷新（忽略数据库缓存）")
):
    """
    获取市场新闻（用于新闻中心/实时新闻流）

    优先从数据库查询，如果数据库为空或强制刷新则触发抓取
    返回格式与旧API兼容，包含情绪统计
    """
    try:
        storage = get_storage()

        # 优先从数据库查询
        if not force_refresh:
            db_news = storage.get_market_news(limit=limit, hours=hours)
            if db_news:
                # 格式化数据库返回的数据
                formatted_news = []
                for n in db_news:
                    formatted_news.append({
                        'id': n.get('news_id', n.get('id', '')),
                        'title': n.get('title', ''),
                        'summary': n.get('summary', ''),
                        'content': n.get('content', ''),
                        'publishTime': n.get('pub_time', ''),
                        'pub_time': n.get('pub_time', ''),
                        'source': n.get('source', ''),
                        'sentiment': n.get('sentiment', 'neutral'),
                        'sentiment_score': n.get('sentiment_score', 50),
                        'url': n.get('source_url', ''),
                        'keywords': n.get('keywords', []),
                        'urgency': 'low',
                        'related_stocks': [n.get('stock_code')] if n.get('stock_code') else [],
                        'stock_code': n.get('stock_code', ''),
                        'stock_name': n.get('stock_name', ''),
                        'category': n.get('category', ''),
                        'source_type': n.get('source_type', 'market')
                    })

                # 计算情绪统计
                sentiment_stats = {
                    'positive': sum(1 for n in formatted_news if n.get('sentiment') == 'positive'),
                    'negative': sum(1 for n in formatted_news if n.get('sentiment') == 'negative'),
                    'neutral': sum(1 for n in formatted_news if n.get('sentiment') == 'neutral')
                }

                logger.info(f"从数据库返回 {len(formatted_news)} 条新闻")
                return {
                    "success": True,
                    "news": formatted_news,
                    "data": formatted_news,
                    "total": len(formatted_news),
                    "total_fetched": len(formatted_news),  # 数据库查询时，total_fetched等于total
                    "count": len(formatted_news),
                    "sentiment_stats": sentiment_stats,
                    "type": "market",
                    "source": "database"
                }

        # 数据库为空或强制刷新，触发抓取
        monitor = get_monitor()
        news = await monitor.fetch_market_news()

        # 格式化新闻数据，与旧API兼容
        formatted_news = []
        for n in news[:limit]:
            formatted_news.append({
                'id': n.get('id', f"news_{hash(n.get('title', ''))}"),
                'title': n.get('title', ''),
                'summary': n.get('content', '')[:200] if n.get('content') else '',
                'content': n.get('content', ''),
                'publishTime': n.get('pub_time', ''),
                'pub_time': n.get('pub_time', ''),
                'source': n.get('source', ''),
                'sentiment': n.get('sentiment', 'neutral'),
                'sentiment_score': n.get('sentiment_score', 50),
                'url': n.get('url', ''),
                'keywords': n.get('keywords', []),
                'urgency': n.get('urgency', 'low'),
                'related_stocks': n.get('related_stocks', []),
                'impact_score': n.get('impact_score', 0),
                'importance': n.get('importance', 'low'),
                'announcement_type': n.get('announcement_type', '')
            })

        # 计算情绪统计
        sentiment_stats = {
            'positive': sum(1 for n in formatted_news if n.get('sentiment') == 'positive'),
            'negative': sum(1 for n in formatted_news if n.get('sentiment') == 'negative'),
            'neutral': sum(1 for n in formatted_news if n.get('sentiment') == 'neutral')
        }

        return {
            "success": True,
            "news": formatted_news,
            "data": formatted_news,  # 兼容新格式
            "total": len(formatted_news),
            "total_fetched": len(news),
            "count": len(formatted_news),
            "sentiment_stats": sentiment_stats,
            "type": "market",
            "source": "fetch"
        }
    except Exception as e:
        logger.error(f"Fetch market news failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock-news/{stock_code}")
async def fetch_stock_news(
    stock_code: str,
    stock_name: Optional[str] = Query(None, description="股票名称")
):
    """
    获取个股新闻（用于智能分析/个股监控）
    调用个股新闻接口，获取特定股票相关新闻
    """
    try:
        monitor = get_monitor()
        news = await monitor.fetch_stock_news(stock_code, stock_name or "")
        return {
            "success": True,
            "data": news,
            "count": len(news),
            "stock_code": stock_code,
            "type": "stock"
        }
    except Exception as e:
        logger.error(f"Fetch stock news failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hot-stocks-news")
async def fetch_hot_stocks_news():
    """
    获取热门股票新闻
    从配置的热门股票列表中获取新闻
    """
    try:
        monitor = get_monitor()
        news = await monitor.fetch_hot_stocks_news()
        return {
            "success": True,
            "data": news,
            "count": len(news),
            "type": "hot_stocks"
        }
    except Exception as e:
        logger.error(f"Fetch hot stocks news failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 统计和控制API ====================

@router.get("/stats")
async def get_stats():
    try:
        monitor = get_monitor()
        stats = monitor.get_stats()
        return {"success": True, "data": stats}
    except Exception as e:
        logger.error(f"Get stats failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/fetch")
async def fetch_now(source_id: Optional[str] = None):
    try:
        monitor = get_monitor()
        await monitor.fetch_now(source_id)
        return {"success": True, "message": f"Fetch triggered for {source_id or 'all sources'}"}
    except Exception as e:
        logger.error(f"Fetch failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/interval")
async def set_interval(source_id: str, interval: int = Query(ge=10, le=3600)):
    try:
        monitor = get_monitor()
        monitor.set_source_interval(source_id, interval)
        return {"success": True, "message": f"Set {source_id} interval to {interval}s"}
    except Exception as e:
        logger.error(f"Set interval failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/config/enable")
async def enable_source(source_id: str, enabled: bool = True):
    try:
        monitor = get_monitor()
        monitor.enable_source(source_id, enabled)
        return {"success": True, "message": f"Set {source_id} enabled={enabled}"}
    except Exception as e:
        logger.error(f"Enable source failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup")
async def cleanup():
    """清理内存缓存中的过期新闻"""
    try:
        monitor = get_monitor()
        count = monitor.cleanup()
        return {"success": True, "message": f"Cleaned up {count} expired news from cache"}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cleanup-database")
async def cleanup_database(days: int = Query(30, ge=1, le=365, description="保留最近N天的新闻")):
    """清理数据库中的旧新闻"""
    try:
        storage = get_storage()
        deleted = storage.cleanup_old_news(days=days)
        return {"success": True, "message": f"Cleaned up {deleted} old news from database (older than {days} days)"}
    except Exception as e:
        logger.error(f"Database cleanup failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/start")
async def start_monitor():
    try:
        monitor = get_monitor()
        await monitor.start()
        return {"success": True, "message": "News monitor started"}
    except Exception as e:
        logger.error(f"Start monitor failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stop")
async def stop_monitor():
    try:
        monitor = get_monitor()
        await monitor.stop()
        return {"success": True, "message": "News monitor stopped"}
    except Exception as e:
        logger.error(f"Stop monitor failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 配置管理API ====================

@router.get("/config")
async def get_news_config():
    """获取新闻配置"""
    try:
        monitor = get_monitor()
        config = monitor.get_news_config()
        return {"success": True, "data": config}
    except Exception as e:
        logger.error(f"Get news config failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config")
async def update_news_config(data: Dict = Body(...)):
    """更新新闻配置"""
    try:
        monitor = get_monitor()
        success = monitor.update_news_config(data)
        if success:
            return {"success": True, "message": "Config updated"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update config")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update news config failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config/source/{source_type}")
async def update_source_config(source_type: str, updates: SourceConfigUpdate):
    """更新单个数据源配置"""
    try:
        monitor = get_monitor()
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        success = monitor.update_source_config(source_type, update_dict)
        if success:
            return {"success": True, "message": f"Source {source_type} config updated"}
        else:
            raise HTTPException(status_code=400, detail=f"Source {source_type} not found or update failed")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update source config failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config/cninfo")
async def update_cninfo_config(updates: CninfoConfigUpdate):
    """更新巨潮配置"""
    try:
        monitor = get_monitor()
        update_dict = {k: v for k, v in updates.dict().items() if v is not None}
        success = monitor.update_cninfo_config(update_dict)
        if success:
            return {"success": True, "message": "CNINFO config updated"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update CNINFO config")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update CNINFO config failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/config/hot-stocks")
async def update_hot_stocks(data: HotStocksUpdate):
    """更新热门股票列表"""
    try:
        monitor = get_monitor()
        success = monitor.update_hot_stocks(data.stocks)
        if success:
            return {"success": True, "message": f"Hot stocks updated ({len(data.stocks)} stocks)"}
        else:
            raise HTTPException(status_code=400, detail="Failed to update hot stocks")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update hot stocks failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/config/sources")
async def get_available_sources():
    """获取可用的数据源列表"""
    try:
        from backend.services.news_center.news_config import NewsSourceType
        market_sources = [
            {"type": NewsSourceType.EASTMONEY_GLOBAL.value, "name": "东方财富全球资讯", "category": "market"},
            {"type": NewsSourceType.CLS_GLOBAL.value, "name": "财联社电报", "category": "market"},
            {"type": NewsSourceType.FUTU_GLOBAL.value, "name": "富途牛牛", "category": "market"},
            {"type": NewsSourceType.THS_GLOBAL.value, "name": "同花顺", "category": "market"},
            {"type": NewsSourceType.SINA_GLOBAL.value, "name": "新浪财经", "category": "market"},
            {"type": NewsSourceType.WEIBO_HOT.value, "name": "微博热议", "category": "market"},
            {"type": NewsSourceType.CJZC.value, "name": "财经早餐", "category": "market"},
            {"type": NewsSourceType.CCTV.value, "name": "新闻联播", "category": "market"},
            {"type": NewsSourceType.BAIDU.value, "name": "百度财经", "category": "market"},
            {"type": NewsSourceType.CNINFO_MARKET.value, "name": "巨潮市场公告", "category": "market"},
            {"type": NewsSourceType.CNINFO_NEWS.value, "name": "巨潮新闻数据(VIP)", "category": "market", "vip": True},
            {"type": NewsSourceType.CNINFO_RESEARCH.value, "name": "巨潮研报摘要(VIP)", "category": "market", "vip": True},
            {"type": NewsSourceType.CNINFO_MANAGEMENT.value, "name": "巨潮高管变动", "category": "market"},
        ]
        stock_sources = [
            {"type": NewsSourceType.STOCK_NEWS_EM.value, "name": "东方财富个股新闻", "category": "stock"},
            {"type": NewsSourceType.CNINFO_STOCK.value, "name": "巨潮个股公告", "category": "stock"},
            {"type": NewsSourceType.CNINFO_STOCK_NEWS.value, "name": "巨潮个股新闻(VIP)", "category": "stock", "vip": True},
        ]
        return {
            "success": True,
            "data": {
                "market_sources": market_sources,
                "stock_sources": stock_sources
            }
        }
    except Exception as e:
        logger.error(f"Get available sources failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ==================== 统一新闻中心兼容API ====================

def _calculate_news_statistics(news_list: List[Dict]) -> Dict:
    """计算新闻统计数据"""
    total = len(news_list)
    positive = sum(1 for n in news_list if n.get("sentiment") == "positive")
    negative = sum(1 for n in news_list if n.get("sentiment") == "negative")
    neutral = total - positive - negative

    source_counts = {}
    for n in news_list:
        source = n.get("source", "unknown")
        source_counts[source] = source_counts.get(source, 0) + 1

    market_counts = {}
    for n in news_list:
        market = n.get("market", "未知")
        market_counts[market] = market_counts.get(market, 0) + 1

    type_counts = {}
    for n in news_list:
        news_type = n.get("news_type", n.get("announcement_type", "未知"))
        type_counts[news_type] = type_counts.get(news_type, 0) + 1

    return {
        "total_count": total,
        "positive_count": positive,
        "negative_count": negative,
        "neutral_count": neutral,
        "source_counts": source_counts,
        "market_counts": market_counts,
        "type_counts": type_counts
    }

@router.get("/list")
async def get_news_list(
    market: Optional[str] = Query(None, description="市场筛选"),
    news_type: Optional[str] = Query(None, description="新闻类型"),
    sentiment: Optional[str] = Query(None, description="情绪筛选"),
    source_filter: Optional[str] = Query(None, alias="source", description="数据源筛选"),
    limit: int = Query(5000, ge=1, le=10000, description="返回数量限制，默认5000")
):
    """
    获取新闻列表（统一新闻中心使用）
    与旧API /api/unified-news/list 兼容
    """
    try:
        monitor = get_monitor()
        news = await monitor.fetch_market_news()

        # 格式化新闻数据
        formatted_news = []
        for n in news:
            # 判断市场类型
            news_source = n.get('source', '')
            is_a_stock = news_source in ['巨潮市场公告', '巨潮高管变动', '巨潮新闻数据(VIP)', '巨潮研报摘要(VIP)', '东方财富个股新闻', '巨潮个股公告', '巨潮个股新闻(VIP)']

            formatted_news.append({
                "id": n.get('id', f"news_{hash(n.get('title', ''))}"),
                "title": n.get('title', ''),
                "summary": n.get('content', '')[:300] if n.get('content') else '',
                "content": n.get('content', ''),
                "source": news_source,
                "source_name": news_source,
                "publish_time": n.get('pub_time', ''),
                "pub_time": n.get('pub_time', ''),
                "market": "A股" if is_a_stock else "全球",
                "news_type": n.get('announcement_type', '综合新闻'),
                "sentiment": n.get('sentiment', 'neutral'),
                "sentiment_score": n.get('sentiment_score', 50) / 100,
                "url": n.get('url', ''),
                "keywords": n.get('keywords', []),
                "urgency": n.get('urgency', 'low'),
                "related_stocks": n.get('related_stocks', []),
                "importance": n.get('importance', 'low')
            })

        # 计算全部数据的统计
        full_statistics = _calculate_news_statistics(formatted_news)

        # 筛选
        result = formatted_news.copy()
        if market:
            result = [n for n in result if n.get("market") == market]
        if news_type:
            result = [n for n in result if n.get("news_type") == news_type]
        if sentiment:
            result = [n for n in result if n.get("sentiment") == sentiment]
        if source_filter:
            result = [n for n in result if n.get("source") == source_filter or n.get("source_name") == source_filter]

        # 筛选后的统计
        filtered_statistics = _calculate_news_statistics(result)

        # 限制返回数量
        result = result[:limit]

        return {
            "success": True,
            "data": result,
            "statistics": full_statistics,
            "filtered_statistics": filtered_statistics,
            "total": len(result),
            "full_total": len(formatted_news)
        }
    except Exception as e:
        logger.error(f"Get news list failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/statistics")
async def get_news_statistics(
    hours: int = Query(24, ge=1, le=168, description="统计最近N小时的数据")
):
    """
    获取新闻统计数据（统一新闻中心使用）
    优先从数据库获取统计
    """
    try:
        storage = get_storage()
        stats = storage.get_statistics(hours=hours)

        return {
            "success": True,
            "data": {
                "total_count": stats.get("total", 0),
                "positive_count": stats.get("by_sentiment", {}).get("positive", 0),
                "negative_count": stats.get("by_sentiment", {}).get("negative", 0),
                "neutral_count": stats.get("by_sentiment", {}).get("neutral", 0),
                "source_counts": stats.get("by_source", {}),
                "hours": hours
            }
        }
    except Exception as e:
        logger.error(f"Get news statistics failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sources")
async def get_news_sources():
    """
    获取数据源状态（统一新闻中心使用）
    与旧API /api/unified-news/sources 兼容
    """
    try:
        from backend.services.news_center.news_config import NewsSourceType, get_news_config_manager

        config_manager = get_news_config_manager()
        config = config_manager.config

        sources = {}

        # 市场新闻源
        for source_type, source_cfg in config.market_sources.items():
            sources[source_type] = {
                "id": source_type,
                "name": source_cfg.name,
                "description": f"{source_cfg.name}数据源",
                "priority": source_cfg.priority,
                "status": "healthy" if source_cfg.enabled else "disabled",
                "enabled": source_cfg.enabled,
                "interval": source_cfg.interval,
                "news_count": 0  # 实际数量需要从缓存获取
            }

        return {
            "success": True,
            "data": sources
        }
    except Exception as e:
        logger.error(f"Get news sources failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/refresh")
async def refresh_news():
    """
    刷新新闻数据（统一新闻中心使用）
    与旧API /api/unified-news/refresh 兼容
    """
    try:
        monitor = get_monitor()
        await monitor.fetch_now()
        return {"success": True, "message": "News refresh triggered"}
    except Exception as e:
        logger.error(f"Refresh news failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/health")
async def health_check():
    """
    健康检查（统一新闻中心使用）
    与旧API /api/unified-news/health 兼容
    """
    try:
        from backend.services.news_center.news_config import get_news_config_manager

        config_manager = get_news_config_manager()
        config = config_manager.config

        sources = {}
        for source_type, source_cfg in config.market_sources.items():
            sources[source_type] = {
                "status": "healthy" if source_cfg.enabled else "disabled"
            }

        return {
            "success": True,
            "status": "healthy",
            "sources": sources
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/search")
async def search_news(
    keyword: str = Query(..., description="搜索关键词"),
    limit: int = Query(5000, ge=1, le=10000, description="返回数量限制，默认5000"),
    hours: int = Query(72, ge=1, le=168, description="搜索最近N小时的新闻")
):
    """
    搜索新闻（统一新闻中心使用）
    优先从数据库搜索
    """
    try:
        storage = get_storage()
        db_news = storage.search_news(keyword=keyword, limit=limit, hours=hours)

        # 格式化数据库返回的数据
        result = []
        for n in db_news:
            source = n.get('source', '')
            is_a_stock = source in ['巨潮市场公告', '巨潮高管变动', '巨潮新闻数据(VIP)', '巨潮研报摘要(VIP)']

            result.append({
                "id": n.get('news_id', n.get('id', '')),
                "title": n.get('title', ''),
                "summary": n.get('summary', ''),
                "content": n.get('content', ''),
                "source": source,
                "source_name": source,
                "publish_time": n.get('pub_time', ''),
                "pub_time": n.get('pub_time', ''),
                "market": "A股" if is_a_stock else "全球",
                "news_type": n.get('category', '综合新闻'),
                "sentiment": n.get('sentiment', 'neutral'),
                "sentiment_score": (n.get('sentiment_score', 50) or 50) / 100,
                "url": n.get('source_url', ''),
                "stock_code": n.get('stock_code', ''),
                "stock_name": n.get('stock_name', ''),
                "related_stocks": [n.get('stock_code')] if n.get('stock_code') else []
            })

        return {
            "success": True,
            "data": result,
            "total": len(result),
            "keyword": keyword,
            "source": "database"
        }
    except Exception as e:
        logger.error(f"Search news failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
