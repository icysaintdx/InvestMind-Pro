# -*- coding: utf-8 -*-
from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/news-center", tags=["news-center"])

def get_monitor():
    from backend.services.news_center import get_news_monitor_center
    return get_news_monitor_center()

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
async def get_urgent_news(limit: int = Query(20, ge=1, le=100)):
    try:
        monitor = get_monitor()
        news = monitor.get_urgent_news(limit=limit)
        return {"success": True, "data": news, "count": len(news)}
    except Exception as e:
        logger.error(f"Get urgent news failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/stock/{stock_code}")
async def get_news_for_stock(stock_code: str, limit: int = Query(30, ge=1, le=100)):
    try:
        monitor = get_monitor()
        news = monitor.get_news_for_stock(stock_code, limit=limit)
        return {"success": True, "data": news, "count": len(news), "stock_code": stock_code}
    except Exception as e:
        logger.error(f"Get news for stock failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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
    try:
        monitor = get_monitor()
        count = monitor.cleanup()
        return {"success": True, "message": f"Cleaned up {count} expired news"}
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
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
