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


# ==================== 预警规则配置API ====================

class AlertRuleCreate(BaseModel):
    """创建预警规则请求"""
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    rule_type: str = Field(..., description="规则类型")
    conditions: Dict[str, Any] = Field(..., description="触发条件")
    alert_level: str = Field("medium", description="预警级别")
    apply_to_all: bool = Field(True, description="是否应用到所有股票")
    stock_codes: Optional[List[str]] = Field(None, description="指定股票代码")
    notify_email: bool = Field(False, description="是否邮件通知")
    notify_wechat: bool = Field(False, description="是否微信通知")
    is_enabled: bool = Field(True, description="是否启用")


class AlertRuleUpdate(BaseModel):
    """更新预警规则请求"""
    name: Optional[str] = None
    description: Optional[str] = None
    conditions: Optional[Dict[str, Any]] = None
    alert_level: Optional[str] = None
    apply_to_all: Optional[bool] = None
    stock_codes: Optional[List[str]] = None
    notify_email: Optional[bool] = None
    notify_wechat: Optional[bool] = None
    is_enabled: Optional[bool] = None


class AlertThresholdConfig(BaseModel):
    """预警阈值配置"""
    surge_pct: float = Field(5.0, description="急涨阈值(%)")
    plunge_pct: float = Field(-5.0, description="急跌阈值(%)")
    limit_up_pct: float = Field(9.9, description="涨停阈值(%)")
    limit_down_pct: float = Field(-9.9, description="跌停阈值(%)")
    volume_ratio: float = Field(3.0, description="放量倍数")


@router.get("/rules")
@log_api_call("获取预警规则列表")
async def get_alert_rules():
    """获取所有预警规则"""
    try:
        from backend.database.database import get_db_context
        from backend.database.models import AlertRule

        with get_db_context() as db:
            rules = db.query(AlertRule).order_by(AlertRule.created_at.desc()).all()
            return {
                "success": True,
                "rules": [rule.to_dict() for rule in rules]
            }

    except Exception as e:
        logger.error(f"获取预警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules")
@log_api_call("创建预警规则")
async def create_alert_rule(request: AlertRuleCreate):
    """创建新的预警规则"""
    try:
        from backend.database.database import get_db_context
        from backend.database.models import AlertRule

        with get_db_context() as db:
            rule = AlertRule(
                name=request.name,
                description=request.description,
                rule_type=request.rule_type,
                conditions=request.conditions,
                alert_level=request.alert_level,
                apply_to_all=1 if request.apply_to_all else 0,
                stock_codes=request.stock_codes,
                notify_email=1 if request.notify_email else 0,
                notify_wechat=1 if request.notify_wechat else 0,
                is_enabled=1 if request.is_enabled else 0
            )
            db.add(rule)
            db.commit()
            db.refresh(rule)

            return {
                "success": True,
                "message": "规则创建成功",
                "rule": rule.to_dict()
            }

    except Exception as e:
        logger.error(f"创建预警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}")
@log_api_call("更新预警规则")
async def update_alert_rule(rule_id: int, request: AlertRuleUpdate):
    """更新预警规则"""
    try:
        from backend.database.database import get_db_context
        from backend.database.models import AlertRule

        with get_db_context() as db:
            rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if not rule:
                raise HTTPException(status_code=404, detail="规则不存在")

            # 更新字段
            if request.name is not None:
                rule.name = request.name
            if request.description is not None:
                rule.description = request.description
            if request.conditions is not None:
                rule.conditions = request.conditions
            if request.alert_level is not None:
                rule.alert_level = request.alert_level
            if request.apply_to_all is not None:
                rule.apply_to_all = 1 if request.apply_to_all else 0
            if request.stock_codes is not None:
                rule.stock_codes = request.stock_codes
            if request.notify_email is not None:
                rule.notify_email = 1 if request.notify_email else 0
            if request.notify_wechat is not None:
                rule.notify_wechat = 1 if request.notify_wechat else 0
            if request.is_enabled is not None:
                rule.is_enabled = 1 if request.is_enabled else 0

            db.commit()
            db.refresh(rule)

            return {
                "success": True,
                "message": "规则更新成功",
                "rule": rule.to_dict()
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新预警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
@log_api_call("删除预警规则")
async def delete_alert_rule(rule_id: int):
    """删除预警规则"""
    try:
        from backend.database.database import get_db_context
        from backend.database.models import AlertRule

        with get_db_context() as db:
            rule = db.query(AlertRule).filter(AlertRule.id == rule_id).first()
            if not rule:
                raise HTTPException(status_code=404, detail="规则不存在")

            db.delete(rule)
            db.commit()

            return {
                "success": True,
                "message": "规则删除成功"
            }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除预警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/thresholds")
@log_api_call("获取预警阈值配置")
async def get_alert_thresholds():
    """获取行情异动预警阈值配置"""
    try:
        from backend.services.price_monitor_service import get_price_monitor_service
        service = get_price_monitor_service()
        stats = service.get_stats()

        return {
            "success": True,
            "thresholds": stats.get('thresholds', {}),
            "check_interval": stats.get('check_interval', 60),
            "is_running": stats.get('running', False),
            "is_trading_time": stats.get('is_trading_time', False)
        }

    except Exception as e:
        logger.error(f"获取预警阈值失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/thresholds")
@log_api_call("更新预警阈值配置")
async def update_alert_thresholds(config: AlertThresholdConfig):
    """更新行情异动预警阈值配置"""
    try:
        from backend.services.price_monitor_service import get_price_monitor_service
        service = get_price_monitor_service()

        service.set_thresholds({
            'surge_pct': config.surge_pct,
            'plunge_pct': config.plunge_pct,
            'limit_up_pct': config.limit_up_pct,
            'limit_down_pct': config.limit_down_pct,
            'volume_ratio': config.volume_ratio
        })

        return {
            "success": True,
            "message": "阈值配置已更新",
            "thresholds": service.get_stats().get('thresholds', {})
        }

    except Exception as e:
        logger.error(f"更新预警阈值失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rule-types")
@log_api_call("获取预警规则类型")
async def get_rule_types():
    """获取可用的预警规则类型"""
    return {
        "success": True,
        "rule_types": [
            {"value": "price_change", "label": "价格变动", "description": "股价涨跌幅超过阈值"},
            {"value": "volume_change", "label": "成交量变动", "description": "成交量超过均量倍数"},
            {"value": "pledge_ratio", "label": "质押比例", "description": "股权质押比例超过阈值"},
            {"value": "restricted_release", "label": "限售解禁", "description": "限售股解禁提醒"},
            {"value": "holder_change", "label": "股东变动", "description": "大股东增减持"},
            {"value": "st_warning", "label": "ST风险", "description": "ST或退市风险警示"},
            {"value": "suspend", "label": "停复牌", "description": "停牌或复牌提醒"},
            {"value": "news_sentiment", "label": "新闻情绪", "description": "负面新闻预警"},
            {"value": "custom", "label": "自定义", "description": "自定义条件规则"}
        ],
        "operators": [
            {"value": ">", "label": "大于"},
            {"value": ">=", "label": "大于等于"},
            {"value": "<", "label": "小于"},
            {"value": "<=", "label": "小于等于"},
            {"value": "==", "label": "等于"},
            {"value": "!=", "label": "不等于"},
            {"value": "contains", "label": "包含"},
            {"value": "not_contains", "label": "不包含"}
        ]
    }
