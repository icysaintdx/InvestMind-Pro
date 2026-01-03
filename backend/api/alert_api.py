# -*- coding: utf-8 -*-
"""
预警API接口
提供预警查询、标记已读、统计等功能
"""

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call
from backend.services.alert_service import get_alert_service, AlertType, AlertLevel

logger = get_logger("api.alert")
router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


# ==================== 数据模型 ====================

class MarkReadRequest(BaseModel):
    """标记已读请求"""
    alert_id: int = Field(..., description="预警ID")


class MarkAllReadRequest(BaseModel):
    """标记全部已读请求"""
    ts_code: Optional[str] = Field(None, description="股票代码（可选，不传则标记所有）")


# ==================== API接口 ====================

@router.get("/list")
@log_api_call("获取预警列表")
async def get_alerts(
    ts_code: Optional[str] = Query(None, description="股票代码"),
    alert_type: Optional[str] = Query(None, description="预警类型"),
    alert_level: Optional[str] = Query(None, description="预警级别"),
    is_read: Optional[bool] = Query(None, description="是否已读"),
    days: int = Query(7, description="查询天数"),
    limit: int = Query(100, description="返回数量"),
    offset: int = Query(0, description="偏移量")
):
    """
    获取预警列表

    支持按股票代码、预警类型、预警级别、已读状态筛选
    """
    try:
        alert_service = get_alert_service()

        # 计算时间范围
        start_time = datetime.now() - timedelta(days=days)

        alerts = alert_service.get_alerts(
            ts_code=ts_code,
            alert_type=alert_type,
            alert_level=alert_level,
            is_read=is_read,
            start_time=start_time,
            limit=limit,
            offset=offset
        )

        return {
            "success": True,
            "alerts": alerts,
            "total": len(alerts)
        }

    except Exception as e:
        logger.error(f"获取预警列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/unread")
@log_api_call("获取未读预警")
async def get_unread_alerts(
    ts_code: Optional[str] = Query(None, description="股票代码"),
    limit: int = Query(50, description="返回数量")
):
    """
    获取未读预警列表
    """
    try:
        alert_service = get_alert_service()

        alerts = alert_service.get_alerts(
            ts_code=ts_code,
            is_read=False,
            limit=limit
        )

        unread_count = alert_service.get_unread_count(ts_code)

        return {
            "success": True,
            "alerts": alerts,
            "unread_count": unread_count
        }

    except Exception as e:
        logger.error(f"获取未读预警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/count")
@log_api_call("获取预警数量")
async def get_alert_count(
    ts_code: Optional[str] = Query(None, description="股票代码")
):
    """
    获取未读预警数量
    """
    try:
        alert_service = get_alert_service()
        count = alert_service.get_unread_count(ts_code)

        return {
            "success": True,
            "unread_count": count
        }

    except Exception as e:
        logger.error(f"获取预警数量失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats/today")
@log_api_call("获取今日预警统计")
async def get_today_stats():
    """
    获取今日预警统计
    """
    try:
        alert_service = get_alert_service()
        stats = alert_service.get_today_stats()

        return {
            "success": True,
            "stats": stats
        }

    except Exception as e:
        logger.error(f"获取今日预警统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-read")
@log_api_call("标记预警已读")
async def mark_alert_read(request: MarkReadRequest):
    """
    标记单个预警为已读
    """
    try:
        alert_service = get_alert_service()
        success = alert_service.mark_as_read(request.alert_id)

        if success:
            return {
                "success": True,
                "message": "已标记为已读"
            }
        else:
            return {
                "success": False,
                "message": "预警不存在"
            }

    except Exception as e:
        logger.error(f"标记预警已读失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/mark-all-read")
@log_api_call("标记全部预警已读")
async def mark_all_alerts_read(request: MarkAllReadRequest):
    """
    标记全部预警为已读
    """
    try:
        alert_service = get_alert_service()
        count = alert_service.mark_all_as_read(request.ts_code)

        return {
            "success": True,
            "message": f"已标记 {count} 条预警为已读",
            "count": count
        }

    except Exception as e:
        logger.error(f"标记全部预警已读失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/types")
@log_api_call("获取预警类型列表")
async def get_alert_types():
    """
    获取所有预警类型
    """
    try:
        types = [
            {"value": t.value, "label": _get_alert_type_label(t)}
            for t in AlertType
        ]

        levels = [
            {"value": l.value, "label": _get_alert_level_label(l)}
            for l in AlertLevel
        ]

        return {
            "success": True,
            "types": types,
            "levels": levels
        }

    except Exception as e:
        logger.error(f"获取预警类型失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stock/{ts_code}")
@log_api_call("获取股票预警")
async def get_stock_alerts(
    ts_code: str,
    days: int = Query(7, description="查询天数"),
    limit: int = Query(50, description="返回数量")
):
    """
    获取指定股票的预警列表
    """
    try:
        alert_service = get_alert_service()

        start_time = datetime.now() - timedelta(days=days)

        alerts = alert_service.get_alerts(
            ts_code=ts_code,
            start_time=start_time,
            limit=limit
        )

        unread_count = alert_service.get_unread_count(ts_code)

        return {
            "success": True,
            "ts_code": ts_code,
            "alerts": alerts,
            "unread_count": unread_count,
            "total": len(alerts)
        }

    except Exception as e:
        logger.error(f"获取股票预警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/cleanup")
@log_api_call("清理旧预警")
async def cleanup_old_alerts(
    days: int = Query(30, description="保留天数")
):
    """
    清理指定天数之前的预警记录
    """
    try:
        alert_service = get_alert_service()
        count = alert_service.cleanup_old_alerts(days)

        return {
            "success": True,
            "message": f"已清理 {count} 条旧预警",
            "count": count
        }

    except Exception as e:
        logger.error(f"清理旧预警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 辅助函数 ====================

def _get_alert_type_label(alert_type: AlertType) -> str:
    """获取预警类型的中文标签"""
    labels = {
        AlertType.NEWS_MAJOR: "重大新闻",
        AlertType.NEWS_POLICY: "政策相关",
        AlertType.NEWS_NEGATIVE: "负面新闻",
        AlertType.NEWS_POSITIVE: "正面新闻",
        AlertType.ANNOUNCEMENT_EARNINGS: "业绩公告",
        AlertType.ANNOUNCEMENT_DIVIDEND: "分红公告",
        AlertType.ANNOUNCEMENT_HOLDER: "股东变动",
        AlertType.ANNOUNCEMENT_RISK: "风险提示",
        AlertType.ANNOUNCEMENT_SUSPEND: "停复牌",
        AlertType.PRICE_LIMIT_UP: "涨停",
        AlertType.PRICE_LIMIT_DOWN: "跌停",
        AlertType.PRICE_SURGE: "急涨",
        AlertType.PRICE_PLUNGE: "急跌",
        AlertType.VOLUME_SURGE: "放量",
        AlertType.FUND_INFLOW: "资金流入",
        AlertType.FUND_OUTFLOW: "资金流出",
        AlertType.HSGT_CHANGE: "北向资金",
        AlertType.RATING_UPGRADE: "评级上调",
        AlertType.RATING_DOWNGRADE: "评级下调",
        AlertType.RISK_ST: "ST风险",
        AlertType.RISK_DELIST: "退市风险",
        AlertType.RISK_PLEDGE: "质押风险",
    }
    return labels.get(alert_type, alert_type.value)


def _get_alert_level_label(alert_level: AlertLevel) -> str:
    """获取预警级别的中文标签"""
    labels = {
        AlertLevel.CRITICAL: "紧急",
        AlertLevel.HIGH: "高",
        AlertLevel.MEDIUM: "中",
        AlertLevel.LOW: "低",
    }
    return labels.get(alert_level, alert_level.value)
