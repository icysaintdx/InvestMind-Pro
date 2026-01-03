# -*- coding: utf-8 -*-
"""
预警服务模块
负责预警的创建、存储、查询和推送
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum
from dataclasses import dataclass

from backend.database.database import get_db_context
from backend.database.models import AlertHistory, MonitoredStock
from backend.utils.logging_config import get_logger

logger = get_logger("alert_service")


class AlertType(str, Enum):
    """预警类型"""
    # 新闻类预警
    NEWS_MAJOR = "news_major"           # 重大新闻
    NEWS_POLICY = "news_policy"         # 政策相关
    NEWS_NEGATIVE = "news_negative"     # 负面新闻
    NEWS_POSITIVE = "news_positive"     # 正面新闻

    # 公告类预警
    ANNOUNCEMENT_EARNINGS = "ann_earnings"    # 业绩公告
    ANNOUNCEMENT_DIVIDEND = "ann_dividend"    # 分红公告
    ANNOUNCEMENT_HOLDER = "ann_holder"        # 股东变动
    ANNOUNCEMENT_RISK = "ann_risk"            # 风险提示
    ANNOUNCEMENT_SUSPEND = "ann_suspend"      # 停复牌公告

    # 行情类预警
    PRICE_LIMIT_UP = "price_limit_up"         # 涨停
    PRICE_LIMIT_DOWN = "price_limit_down"     # 跌停
    PRICE_SURGE = "price_surge"               # 急涨(>5%)
    PRICE_PLUNGE = "price_plunge"             # 急跌(>5%)
    VOLUME_SURGE = "volume_surge"             # 放量(>3倍)

    # 资金类预警
    FUND_INFLOW = "fund_inflow"               # 大额流入
    FUND_OUTFLOW = "fund_outflow"             # 大额流出
    HSGT_CHANGE = "hsgt_change"               # 北向资金变化

    # 评级类预警
    RATING_UPGRADE = "rating_upgrade"         # 评级上调
    RATING_DOWNGRADE = "rating_downgrade"     # 评级下调

    # 风险类预警
    RISK_ST = "risk_st"                       # ST风险
    RISK_DELIST = "risk_delist"               # 退市风险
    RISK_PLEDGE = "risk_pledge"               # 质押风险


class AlertLevel(str, Enum):
    """预警级别"""
    CRITICAL = "critical"   # 紧急
    HIGH = "high"           # 高
    MEDIUM = "medium"       # 中
    LOW = "low"             # 低


@dataclass
class AlertData:
    """预警数据"""
    ts_code: str
    stock_name: str
    alert_type: AlertType
    alert_level: AlertLevel
    title: str
    message: str
    suggestion: str = ""
    source: str = ""
    url: str = ""
    extra_data: Dict = None


class AlertService:
    """预警服务"""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._monitored_stocks: Dict[str, Dict] = {}
        self._alert_callbacks: List[callable] = []
        self._load_monitored_stocks()
        logger.info("AlertService initialized")

    def _load_monitored_stocks(self):
        """加载监控股票列表"""
        try:
            with get_db_context() as db:
                stocks = db.query(MonitoredStock).filter(MonitoredStock.is_active == 1).all()
                self._monitored_stocks = {
                    stock.ts_code: {
                        'name': stock.name,
                        'ts_code': stock.ts_code,
                        'items': stock.items or {}
                    }
                    for stock in stocks
                }
            logger.info(f"Loaded {len(self._monitored_stocks)} monitored stocks")
        except Exception as e:
            logger.error(f"Failed to load monitored stocks: {e}")
            self._monitored_stocks = {}

    def refresh_monitored_stocks(self):
        """刷新监控股票列表"""
        self._load_monitored_stocks()

    def get_monitored_stocks(self) -> Dict[str, Dict]:
        """获取监控股票列表"""
        return self._monitored_stocks.copy()

    def get_monitored_stock_codes(self) -> List[str]:
        """获取监控股票代码列表（纯数字格式）"""
        codes = []
        for ts_code in self._monitored_stocks.keys():
            # 转换 600519.SH -> 600519
            code = ts_code.split('.')[0]
            codes.append(code)
        return codes

    def is_monitored(self, stock_code: str) -> bool:
        """检查股票是否在监控列表中"""
        # 支持多种格式: 600519, 600519.SH, SH600519
        clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.BJ', '')
        clean_code = clean_code.replace('SH', '').replace('SZ', '').replace('BJ', '')

        for ts_code in self._monitored_stocks.keys():
            if clean_code in ts_code:
                return True
        return False

    def get_stock_info(self, stock_code: str) -> Optional[Dict]:
        """获取监控股票信息"""
        clean_code = stock_code.replace('.SH', '').replace('.SZ', '').replace('.BJ', '')
        clean_code = clean_code.replace('SH', '').replace('SZ', '').replace('BJ', '')

        for ts_code, info in self._monitored_stocks.items():
            if clean_code in ts_code:
                return info
        return None

    def register_callback(self, callback: callable):
        """注册预警回调"""
        self._alert_callbacks.append(callback)

    async def create_alert(self, alert_data: AlertData) -> Optional[int]:
        """创建预警记录"""
        try:
            with get_db_context() as db:
                alert = AlertHistory(
                    ts_code=alert_data.ts_code,
                    stock_name=alert_data.stock_name,
                    alert_type=alert_data.alert_type.value if isinstance(alert_data.alert_type, AlertType) else alert_data.alert_type,
                    alert_level=alert_data.alert_level.value if isinstance(alert_data.alert_level, AlertLevel) else alert_data.alert_level,
                    title=alert_data.title,
                    message=alert_data.message,
                    suggestion=alert_data.suggestion,
                    is_read=0,
                    is_resolved=0,
                    alert_time=datetime.now()
                )
                db.add(alert)
                db.commit()
                db.refresh(alert)

                logger.info(f"Created alert: [{alert_data.alert_level}] {alert_data.ts_code} - {alert_data.title}")

                # 触发回调
                alert_dict = alert.to_dict()
                for callback in self._alert_callbacks:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            asyncio.create_task(callback(alert_dict))
                        else:
                            callback(alert_dict)
                    except Exception as e:
                        logger.error(f"Alert callback error: {e}")

                # WebSocket 推送
                await self._push_alert_websocket(alert_dict)

                # 发送通知（高级别预警）
                if alert_data.alert_level in [AlertLevel.CRITICAL, AlertLevel.HIGH]:
                    await self._send_notification(alert_dict)

                return alert.id

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None

    async def create_alert_from_news(self, news: Dict, stock_code: str, stock_name: str) -> Optional[int]:
        """从新闻创建预警"""
        # 确定预警类型和级别
        title = news.get('title', '')
        content = news.get('content', '')
        urgency = news.get('urgency', 'low')
        sentiment = news.get('sentiment', 'neutral')
        source = news.get('source', '')

        # 根据新闻内容判断预警类型
        alert_type = AlertType.NEWS_MAJOR
        if any(kw in title for kw in ['政策', '监管', '央行', '证监会', '国务院']):
            alert_type = AlertType.NEWS_POLICY
        elif any(kw in title for kw in ['业绩', '财报', '年报', '季报', '中报']):
            alert_type = AlertType.ANNOUNCEMENT_EARNINGS
        elif any(kw in title for kw in ['分红', '派息', '送股']):
            alert_type = AlertType.ANNOUNCEMENT_DIVIDEND
        elif any(kw in title for kw in ['股东', '增持', '减持', '举牌']):
            alert_type = AlertType.ANNOUNCEMENT_HOLDER
        elif any(kw in title for kw in ['风险', '警示', 'ST', '退市']):
            alert_type = AlertType.ANNOUNCEMENT_RISK
        elif any(kw in title for kw in ['停牌', '复牌']):
            alert_type = AlertType.ANNOUNCEMENT_SUSPEND
        elif sentiment == 'negative':
            alert_type = AlertType.NEWS_NEGATIVE
        elif sentiment == 'positive':
            alert_type = AlertType.NEWS_POSITIVE

        # 根据紧急程度判断预警级别
        if urgency == 'critical':
            alert_level = AlertLevel.CRITICAL
        elif urgency == 'high':
            alert_level = AlertLevel.HIGH
        elif urgency == 'medium':
            alert_level = AlertLevel.MEDIUM
        else:
            alert_level = AlertLevel.LOW

        # 构建预警数据
        alert_data = AlertData(
            ts_code=stock_code,
            stock_name=stock_name,
            alert_type=alert_type,
            alert_level=alert_level,
            title=f"[{source}] {title[:100]}",
            message=content[:500] if content else title,
            suggestion=f"来源: {source} | 情绪: {sentiment}",
            source=source,
            url=news.get('url', ''),
            extra_data={'news': news}
        )

        return await self.create_alert(alert_data)

    async def _push_alert_websocket(self, alert: Dict):
        """通过 WebSocket 推送预警"""
        try:
            from backend.api.websocket_api import notify_stock_alert
            await notify_stock_alert(alert)
        except Exception as e:
            logger.debug(f"WebSocket push failed: {e}")

    async def _send_notification(self, alert: Dict):
        """发送通知（邮件/微信等）"""
        try:
            from backend.services.notification_service import get_notification_service
            notification_service = get_notification_service()

            alerts = [{
                'title': alert.get('title', ''),
                'message': alert.get('message', ''),
                'level': alert.get('alert_level', 'medium'),
                'stock_code': alert.get('ts_code', ''),
                'suggestion': alert.get('suggestion', '')
            }]

            result = await notification_service.send_alert_notification(alerts)
            if result.get('success'):
                logger.info(f"Alert notification sent: {alert.get('title', '')[:50]}")
        except Exception as e:
            logger.debug(f"Notification send failed: {e}")

    def get_alerts(
        self,
        ts_code: str = None,
        alert_type: str = None,
        alert_level: str = None,
        is_read: bool = None,
        start_time: datetime = None,
        end_time: datetime = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Dict]:
        """查询预警记录"""
        try:
            with get_db_context() as db:
                query = db.query(AlertHistory)

                if ts_code:
                    query = query.filter(AlertHistory.ts_code == ts_code)
                if alert_type:
                    query = query.filter(AlertHistory.alert_type == alert_type)
                if alert_level:
                    query = query.filter(AlertHistory.alert_level == alert_level)
                if is_read is not None:
                    query = query.filter(AlertHistory.is_read == (1 if is_read else 0))
                if start_time:
                    query = query.filter(AlertHistory.alert_time >= start_time)
                if end_time:
                    query = query.filter(AlertHistory.alert_time <= end_time)

                query = query.order_by(AlertHistory.alert_time.desc())
                query = query.offset(offset).limit(limit)

                alerts = query.all()
                return [alert.to_dict() for alert in alerts]

        except Exception as e:
            logger.error(f"Failed to get alerts: {e}")
            return []

    def get_unread_count(self, ts_code: str = None) -> int:
        """获取未读预警数量"""
        try:
            with get_db_context() as db:
                query = db.query(AlertHistory).filter(AlertHistory.is_read == 0)
                if ts_code:
                    query = query.filter(AlertHistory.ts_code == ts_code)
                return query.count()
        except Exception as e:
            logger.error(f"Failed to get unread count: {e}")
            return 0

    def mark_as_read(self, alert_id: int) -> bool:
        """标记预警为已读"""
        try:
            with get_db_context() as db:
                alert = db.query(AlertHistory).filter(AlertHistory.id == alert_id).first()
                if alert:
                    alert.is_read = 1
                    alert.read_time = datetime.now()
                    db.commit()
                    return True
                return False
        except Exception as e:
            logger.error(f"Failed to mark alert as read: {e}")
            return False

    def mark_all_as_read(self, ts_code: str = None) -> int:
        """标记所有预警为已读"""
        try:
            with get_db_context() as db:
                query = db.query(AlertHistory).filter(AlertHistory.is_read == 0)
                if ts_code:
                    query = query.filter(AlertHistory.ts_code == ts_code)

                count = query.count()
                query.update({
                    AlertHistory.is_read: 1,
                    AlertHistory.read_time: datetime.now()
                })
                db.commit()
                return count
        except Exception as e:
            logger.error(f"Failed to mark all alerts as read: {e}")
            return 0

    def get_today_stats(self) -> Dict:
        """获取今日预警统计"""
        try:
            today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)

            with get_db_context() as db:
                # 今日总数
                total = db.query(AlertHistory).filter(
                    AlertHistory.alert_time >= today
                ).count()

                # 按级别统计
                critical = db.query(AlertHistory).filter(
                    AlertHistory.alert_time >= today,
                    AlertHistory.alert_level == 'critical'
                ).count()

                high = db.query(AlertHistory).filter(
                    AlertHistory.alert_time >= today,
                    AlertHistory.alert_level == 'high'
                ).count()

                # 未读数
                unread = db.query(AlertHistory).filter(
                    AlertHistory.alert_time >= today,
                    AlertHistory.is_read == 0
                ).count()

                return {
                    'total': total,
                    'critical': critical,
                    'high': high,
                    'unread': unread,
                    'date': today.strftime('%Y-%m-%d')
                }

        except Exception as e:
            logger.error(f"Failed to get today stats: {e}")
            return {'total': 0, 'critical': 0, 'high': 0, 'unread': 0}

    def cleanup_old_alerts(self, days: int = 30) -> int:
        """清理旧预警记录"""
        try:
            cutoff = datetime.now() - timedelta(days=days)

            with get_db_context() as db:
                count = db.query(AlertHistory).filter(
                    AlertHistory.alert_time < cutoff
                ).delete()
                db.commit()

                logger.info(f"Cleaned up {count} old alerts")
                return count

        except Exception as e:
            logger.error(f"Failed to cleanup old alerts: {e}")
            return 0


# 单例获取函数
_alert_service = None

def get_alert_service() -> AlertService:
    global _alert_service
    if _alert_service is None:
        _alert_service = AlertService()
    return _alert_service
