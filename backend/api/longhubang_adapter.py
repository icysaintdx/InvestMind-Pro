"""
龙虎榜 API 适配器（优化版）
兼容旧前端调用，内部使用缓存优化
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
import time

from backend.utils.logging_config import get_logger
from backend.dataflows.longhubang import longhubang_data_fetcher

logger = get_logger("api.longhubang_adapter")
router = APIRouter(prefix="/api/longhubang", tags=["龙虎榜-缓存优化版"])

# 扩展缓存 - 用于summary/institution/traders
_summary_cache = {}
_summary_cache_time = 0
_summary_cache_ttl = 300  # 5分钟

_institution_cache = {}
_institution_cache_time = 0
_institution_cache_ttl = 300

_traders_cache = {}
_traders_cache_time = 0
_traders_cache_ttl = 300

_recent_cache = {}
_recent_cache_time = 0
_recent_cache_ttl = 300


def _get_cached(cache_dict, cache_time, ttl):
    """获取缓存"""
    if time.time() - cache_time < ttl:
        return cache_dict
    return None


def _set_cached(cache_dict, data):
    """设置缓存"""
    cache_dict.clear()
    cache_dict.update(data)
    return time.time()


@router.get("/daily")
async def get_daily_longhubang(
    date: Optional[str] = Query(None, description="日期，格式YYYY-MM-DD")
):
    """
    获取龙虎榜数据（带5分钟缓存）
    """
    try:
        logger.info(f"[龙虎榜适配器] 获取数据: {date or '最新'}")
        
        # 直接调用数据获取器（内部有缓存）
        result = longhubang_data_fetcher.get_longhubang_data(date)
        
        return result
        
    except Exception as e:
        logger.error(f"[龙虎榜适配器] 获取失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/recent")
async def get_recent_longhubang(
    days: int = Query(5, ge=1, le=30, description="最近N天")
):
    """获取最近N天龙虎榜（带缓存）"""
    global _recent_cache, _recent_cache_time
    
    cache_key = f"days_{days}"
    cached = _get_cached(_recent_cache.get(cache_key), _recent_cache_time, _recent_cache_ttl)
    if cached:
        logger.info("[龙虎榜适配器] recent返回缓存")
        return cached
    
    try:
        data_list = longhubang_data_fetcher.get_recent_days_data(days)
        summary = longhubang_data_fetcher.analyze_data_summary(data_list)
        
        result = {
            "success": True,
            "data": data_list,
            "count": len(data_list),
            "summary": {
                **summary,
                "total_buy": summary.get("total_buy_amount", 0),
                "total_sell": summary.get("total_sell_amount", 0),
                "net_buy": summary.get("total_net_amount", 0),
            },
        }
        
        _recent_cache[cache_key] = result
        _recent_cache_time = time.time()
        return result
        
    except Exception as e:
        logger.error(f"[龙虎榜适配器] 获取失败: {e}")
        return {"success": False, "data": [], "message": str(e)}


@router.get("/summary")
async def get_longhubang_summary():
    """获取龙虎榜统计摘要（带缓存）"""
    global _summary_cache, _summary_cache_time
    
    cached = _get_cached(_summary_cache, _summary_cache_time, _summary_cache_ttl)
    if cached:
        logger.info("[龙虎榜适配器] summary返回缓存")
        return cached
    
    try:
        # 直接获取今日数据生成摘要（避免遍历多日）
        today_data = longhubang_data_fetcher.get_longhubang_data()
        data_list = today_data.get('data', []) if isinstance(today_data, dict) else []
        summary = longhubang_data_fetcher.analyze_data_summary(data_list)
        
        # 字段重映射：后端 total_buy_amount → 前端 total_buy
        result = {
            "success": True,
            "summary": {
                **summary,
                "total_buy": summary.get("total_buy_amount", 0),
                "total_sell": summary.get("total_sell_amount", 0),
                "net_buy": summary.get("total_net_amount", 0),
            },
        }
        
        _summary_cache = result
        _summary_cache_time = time.time()
        return result
        
    except Exception as e:
        logger.error(f"[龙虎榜适配器] 获取失败: {e}")
        return {"success": False, "message": str(e)}


@router.get("/institution")
async def get_institution_trading():
    """获取机构交易统计（带缓存）"""
    global _institution_cache, _institution_cache_time
    
    cached = _get_cached(_institution_cache, _institution_cache_time, _institution_cache_ttl)
    if cached:
        logger.info("[龙虎榜适配器] ✅ institution返回缓存")
        return cached
    
    try:
        # 直接获取机构统计（不需要遍历多日数据）
        institution_stats = longhubang_data_fetcher.get_lhb_institution_stat(5)
        
        result = {
            "success": True,
            "data": institution_stats.get('data', []) if isinstance(institution_stats, dict) else [],
        }
        
        _institution_cache = result
        _institution_cache_time = time.time()
        logger.info("[龙虎榜适配器] 💾 institution缓存已保存")
        return result
        
    except Exception as e:
        logger.error(f"[龙虎榜适配器] 获取失败: {e}")
        return {"success": False, "data": []}


@router.get("/traders")
async def get_active_traders():
    """获取活跃游资统计（带缓存）"""
    global _traders_cache, _traders_cache_time
    
    cached = _get_cached(_traders_cache, _traders_cache_time, _traders_cache_ttl)
    if cached:
        logger.info("[龙虎榜适配器] traders返回缓存")
        return cached
    
    try:
        # 直接获取游资统计（不需要遍历多日数据）
        trader_stats = longhubang_data_fetcher.get_lhb_trader_stat(5)
        
        result = {
            "success": True,
            "data": trader_stats.get('data', []) if isinstance(trader_stats, dict) else [],
        }
        
        _traders_cache = result
        _traders_cache_time = time.time()
        logger.info("[龙虎榜适配器] 💾 traders缓存已保存")
        return result
        
    except Exception as e:
        logger.error(f"[龙虎榜适配器] 获取失败: {e}")
        return {"success": False, "data": []}


@router.get("/stock/{code}")
async def get_stock_longhubang_detail(code: str):
    """获取个股龙虎榜详情"""
    try:
        detail = longhubang_data_fetcher.get_lhb_stock_detail(code)
        return {
            "success": detail.get("success", False),
            "stock_code": code,
            "data": {
                "buy_seats": detail.get("buy_seats", []),
                "sell_seats": detail.get("sell_seats", []),
                "date": detail.get("date", ""),
            },
            **{k: v for k, v in detail.items() if k not in ("success", "buy_seats", "sell_seats", "date")}
        }
    except Exception as e:
        logger.error(f"[龙虎榜适配器] 获取失败: {e}")
        return {"success": False, "message": str(e)}
