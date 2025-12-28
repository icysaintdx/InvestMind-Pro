"""
预警通知集成模块
将预警系统与通知服务集成，实现自动推送
"""

import asyncio
from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy.orm import Session

from backend.utils.logging_config import get_logger
from backend.database.services import AlertHistoryService, AlertRuleService
from backend.services.notification_service import get_notification_service, NotificationConfig

logger = get_logger("alert_notification")


class AlertNotificationIntegration:
    """预警通知集成服务"""

    def __init__(self):
        self.notification_service = get_notification_service()

    async def process_and_notify(
        self,
        db: Session,
        ts_code: str,
        stock_name: str,
        alerts: List[Dict],
        email_recipients: Optional[List[str]] = None
    ) -> Dict:
        """
        处理预警并发送通知

        Args:
            db: 数据库会话
            ts_code: 股票代码
            stock_name: 股票名称
            alerts: 预警列表
            email_recipients: 邮件收件人列表（可选）

        Returns:
            处理结果
        """
        if not alerts:
            return {'success': True, 'message': '无预警需要处理'}

        # 1. 保存预警到数据库
        saved_count = AlertHistoryService.save_alerts_batch(
            db=db,
            ts_code=ts_code,
            alerts=alerts,
            stock_name=stock_name
        )
        logger.info(f"💾 保存{saved_count}条预警到数据库: {ts_code}")

        # 2. 筛选需要通知的预警
        alerts_to_notify = []
        for alert in alerts:
            # 检查是否需要通知
            should_notify = False
            notify_channels = []

            # 检查预警级别（critical和high级别默认通知）
            level = alert.get('level', 'medium')
            if level in ['critical', 'high']:
                should_notify = True
                notify_channels = NotificationConfig.get_available_channels()

            # 检查规则设置的通知选项
            if alert.get('notify_email'):
                should_notify = True
                if 'email' not in notify_channels and NotificationConfig.is_email_configured():
                    notify_channels.append('email')

            if alert.get('notify_wechat'):
                should_notify = True
                if 'wechat' not in notify_channels and NotificationConfig.is_wechat_configured():
                    notify_channels.append('wechat')

            if should_notify:
                alert['stock_code'] = ts_code
                alert['stock_name'] = stock_name
                alerts_to_notify.append({
                    'alert': alert,
                    'channels': notify_channels
                })

        if not alerts_to_notify:
            logger.info(f"📭 无需发送通知的预警: {ts_code}")
            return {
                'success': True,
                'saved_count': saved_count,
                'notified_count': 0,
                'message': '预警已保存，无需发送通知'
            }

        # 3. 发送通知
        notification_results = []
        for item in alerts_to_notify:
            alert = item['alert']
            channels = item['channels']

            # 格式化单条预警为列表格式
            alert_list = [{
                'title': alert.get('title', ''),
                'message': alert.get('message', ''),
                'suggestion': alert.get('suggestion', ''),
                'level': alert.get('level', 'medium'),
                'stock_code': alert.get('stock_code', ts_code)
            }]

            try:
                result = await self.notification_service.send_alert_notification(
                    alerts=alert_list,
                    channels=channels,
                    email_recipients=email_recipients
                )
                notification_results.append(result)
            except Exception as e:
                logger.error(f"❌ 发送通知失败: {e}")
                notification_results.append({
                    'success': False,
                    'message': str(e)
                })

        # 4. 统计结果
        success_count = sum(1 for r in notification_results if r.get('success'))

        logger.info(f"📤 通知发送完成: {success_count}/{len(alerts_to_notify)} 成功")

        return {
            'success': True,
            'saved_count': saved_count,
            'notified_count': success_count,
            'total_alerts': len(alerts),
            'message': f'保存{saved_count}条预警，发送{success_count}条通知'
        }

    async def send_batch_alerts(
        self,
        alerts: List[Dict],
        channels: Optional[List[str]] = None,
        email_recipients: Optional[List[str]] = None
    ) -> Dict:
        """
        批量发送预警通知

        Args:
            alerts: 预警列表
            channels: 通知渠道
            email_recipients: 邮件收件人

        Returns:
            发送结果
        """
        if not alerts:
            return {'success': True, 'message': '无预警需要发送'}

        # 使用所有可用渠道
        if channels is None:
            channels = NotificationConfig.get_available_channels()

        if not channels:
            return {'success': False, 'message': '没有可用的通知渠道'}

        try:
            result = await self.notification_service.send_alert_notification(
                alerts=alerts,
                channels=channels,
                email_recipients=email_recipients
            )
            return result
        except Exception as e:
            logger.error(f"❌ 批量发送通知失败: {e}")
            return {'success': False, 'message': str(e)}

    def check_and_trigger_alerts(
        self,
        db: Session,
        ts_code: str,
        stock_name: str,
        data: Dict
    ) -> List[Dict]:
        """
        检查数据并触发预警

        Args:
            db: 数据库会话
            ts_code: 股票代码
            stock_name: 股票名称
            data: 股票综合数据

        Returns:
            触发的预警列表
        """
        # 使用规则服务评估预警
        triggered_alerts = AlertRuleService.evaluate_rules(db, ts_code, data)

        if triggered_alerts:
            logger.info(f"⚠️ {ts_code} 触发{len(triggered_alerts)}条预警")

        return triggered_alerts


# 全局实例
_integration_instance = None


def get_alert_notification_integration() -> AlertNotificationIntegration:
    """获取预警通知集成服务实例"""
    global _integration_instance
    if _integration_instance is None:
        _integration_instance = AlertNotificationIntegration()
    return _integration_instance


async def process_stock_alerts(
    db: Session,
    ts_code: str,
    stock_name: str,
    data: Dict,
    email_recipients: Optional[List[str]] = None
) -> Dict:
    """
    处理股票预警的便捷函数

    Args:
        db: 数据库会话
        ts_code: 股票代码
        stock_name: 股票名称
        data: 股票综合数据
        email_recipients: 邮件收件人

    Returns:
        处理结果
    """
    integration = get_alert_notification_integration()

    # 1. 检查并触发预警
    alerts = integration.check_and_trigger_alerts(db, ts_code, stock_name, data)

    if not alerts:
        return {'success': True, 'message': '无预警触发'}

    # 2. 处理预警并发送通知
    result = await integration.process_and_notify(
        db=db,
        ts_code=ts_code,
        stock_name=stock_name,
        alerts=alerts,
        email_recipients=email_recipients
    )

    return result
