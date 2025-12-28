#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知服务 - 支持钉钉/飞书Webhook和邮件通知
基于aiagents-stock子项目的notification_service.py适配
"""

import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional, Tuple, List
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


class WebhookNotificationService:
    """Webhook通知服务 - 支持钉钉和飞书"""

    def __init__(self):
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """从环境变量加载配置"""
        return {
            # 邮件配置
            'email_enabled': os.getenv('EMAIL_ENABLED', 'false').lower() == 'true',
            'smtp_server': os.getenv('SMTP_SERVER', ''),
            'smtp_port': int(os.getenv('SMTP_PORT', '587')),
            'email_from': os.getenv('EMAIL_FROM', ''),
            'email_password': os.getenv('EMAIL_PASSWORD', ''),
            'email_to': os.getenv('EMAIL_TO', ''),
            # Webhook配置
            'webhook_enabled': os.getenv('WEBHOOK_ENABLED', 'false').lower() == 'true',
            'webhook_url': os.getenv('WEBHOOK_URL', ''),
            'webhook_type': os.getenv('WEBHOOK_TYPE', 'dingtalk').lower(),  # dingtalk 或 feishu
            'webhook_keyword': os.getenv('WEBHOOK_KEYWORD', '智投顾问团'),  # 钉钉自定义关键词
        }

    def reload_config(self):
        """重新加载配置"""
        self.config = self._load_config()

    # ==================== 钉钉通知 ====================

    async def send_dingtalk_message(
        self,
        title: str,
        content: str,
        at_mobiles: Optional[List[str]] = None,
        at_all: bool = False
    ) -> Tuple[bool, str]:
        """
        发送钉钉Markdown消息

        Args:
            title: 消息标题
            content: Markdown格式的消息内容
            at_mobiles: 需要@的手机号列表
            at_all: 是否@所有人

        Returns:
            (是否成功, 消息)
        """
        if not self.config['webhook_enabled'] or not self.config['webhook_url']:
            return False, "Webhook未启用或URL未配置"

        if self.config['webhook_type'] != 'dingtalk':
            return False, f"当前配置的Webhook类型是 {self.config['webhook_type']}，不是钉钉"

        try:
            # 添加关键词（钉钉安全设置需要）
            keyword = self.config['webhook_keyword']
            full_content = f"### {keyword}\n\n{content}"

            data = {
                "msgtype": "markdown",
                "markdown": {
                    "title": f"{keyword} - {title}",
                    "text": full_content
                },
                "at": {
                    "atMobiles": at_mobiles or [],
                    "isAtAll": at_all
                }
            }

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.config['webhook_url'],
                    json=data,
                    headers={'Content-Type': 'application/json'}
                )

            if response.status_code == 200:
                result = response.json()
                if result.get('errcode') == 0:
                    logger.info(f"钉钉消息发送成功: {title}")
                    return True, "发送成功"
                else:
                    error_msg = result.get('errmsg', '未知错误')
                    logger.error(f"钉钉消息发送失败: {error_msg}")
                    return False, f"钉钉返回错误: {error_msg}"
            else:
                logger.error(f"钉钉请求失败: HTTP {response.status_code}")
                return False, f"HTTP请求失败: {response.status_code}"

        except Exception as e:
            logger.error(f"钉钉消息发送异常: {e}")
            return False, f"发送异常: {str(e)}"

    # ==================== 飞书通知 ====================

    async def send_feishu_message(
        self,
        title: str,
        content: str
    ) -> Tuple[bool, str]:
        """
        发送飞书卡片消息

        Args:
            title: 消息标题
            content: 消息内容

        Returns:
            (是否成功, 消息)
        """
        if not self.config['webhook_enabled'] or not self.config['webhook_url']:
            return False, "Webhook未启用或URL未配置"

        if self.config['webhook_type'] != 'feishu':
            return False, f"当前配置的Webhook类型是 {self.config['webhook_type']}，不是飞书"

        try:
            data = {
                "msg_type": "interactive",
                "card": {
                    "header": {
                        "title": {
                            "content": f"📊 {title}",
                            "tag": "plain_text"
                        },
                        "template": "blue"
                    },
                    "elements": [
                        {
                            "tag": "div",
                            "text": {
                                "content": content,
                                "tag": "lark_md"
                            }
                        },
                        {
                            "tag": "hr"
                        },
                        {
                            "tag": "note",
                            "elements": [
                                {
                                    "tag": "plain_text",
                                    "content": f"智投顾问团 · {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                                }
                            ]
                        }
                    ]
                }
            }

            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.post(
                    self.config['webhook_url'],
                    json=data,
                    headers={'Content-Type': 'application/json'}
                )

            if response.status_code == 200:
                result = response.json()
                if result.get('code') == 0:
                    logger.info(f"飞书消息发送成功: {title}")
                    return True, "发送成功"
                else:
                    error_msg = result.get('msg', '未知错误')
                    logger.error(f"飞书消息发送失败: {error_msg}")
                    return False, f"飞书返回错误: {error_msg}"
            else:
                logger.error(f"飞书请求失败: HTTP {response.status_code}")
                return False, f"HTTP请求失败: {response.status_code}"

        except Exception as e:
            logger.error(f"飞书消息发送异常: {e}")
            return False, f"发送异常: {str(e)}"

    # ==================== 统一发送接口 ====================

    async def send_webhook_notification(
        self,
        title: str,
        content: str,
        **kwargs
    ) -> Tuple[bool, str]:
        """
        统一的Webhook通知发送接口

        Args:
            title: 消息标题
            content: 消息内容
            **kwargs: 其他参数（如at_mobiles, at_all等）

        Returns:
            (是否成功, 消息)
        """
        webhook_type = self.config['webhook_type']

        if webhook_type == 'dingtalk':
            return await self.send_dingtalk_message(
                title, content,
                at_mobiles=kwargs.get('at_mobiles'),
                at_all=kwargs.get('at_all', False)
            )
        elif webhook_type == 'feishu':
            return await self.send_feishu_message(title, content)
        else:
            return False, f"不支持的Webhook类型: {webhook_type}"

    # ==================== 邮件通知 ====================

    def send_email(
        self,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        发送邮件通知

        Args:
            subject: 邮件主题
            html_body: HTML格式的邮件正文
            text_body: 纯文本格式的邮件正文（可选）

        Returns:
            (是否成功, 消息)
        """
        if not self.config['email_enabled']:
            return False, "邮件通知未启用"

        required_fields = ['smtp_server', 'email_from', 'email_password', 'email_to']
        missing = [f for f in required_fields if not self.config.get(f)]
        if missing:
            return False, f"邮件配置不完整，缺少: {', '.join(missing)}"

        try:
            msg = MIMEMultipart('alternative')
            msg['From'] = self.config['email_from']
            msg['To'] = self.config['email_to']
            msg['Subject'] = subject

            if text_body:
                msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
            msg.attach(MIMEText(html_body, 'html', 'utf-8'))

            # 根据端口选择连接方式
            if self.config['smtp_port'] == 465:
                server = smtplib.SMTP_SSL(
                    self.config['smtp_server'],
                    self.config['smtp_port'],
                    timeout=15
                )
            else:
                server = smtplib.SMTP(
                    self.config['smtp_server'],
                    self.config['smtp_port'],
                    timeout=15
                )
                server.starttls()

            server.login(self.config['email_from'], self.config['email_password'])
            server.send_message(msg)
            server.quit()

            logger.info(f"邮件发送成功: {subject}")
            return True, "邮件发送成功"

        except smtplib.SMTPAuthenticationError:
            logger.error("邮箱认证失败")
            return False, "邮箱认证失败，请检查邮箱和授权码"
        except smtplib.SMTPException as e:
            logger.error(f"SMTP错误: {e}")
            return False, f"SMTP错误: {str(e)}"
        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False, f"发送失败: {str(e)}"

    # ==================== 股票分析通知 ====================

    async def send_analysis_notification(
        self,
        stock_code: str,
        stock_name: str,
        rating: str,
        summary: str,
        confidence: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        发送股票分析完成通知

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            rating: 投资评级
            summary: 分析摘要
            confidence: 信心度

        Returns:
            (是否成功, 消息)
        """
        title = f"分析完成 - {stock_code} {stock_name}"

        # 评级图标
        rating_icon = "🟡"
        if "买入" in rating or "增持" in rating:
            rating_icon = "🟢"
        elif "卖出" in rating or "减持" in rating:
            rating_icon = "🔴"

        content = f"""**{stock_code} {stock_name}**

{rating_icon} **投资评级**: {rating}
{"📊 **信心度**: " + str(confidence) + "/10" if confidence else ""}

**分析摘要**:
{summary}

---
_智投顾问团 AI分析系统_
"""

        return await self.send_webhook_notification(title, content)

    async def send_alert_notification(
        self,
        stock_code: str,
        stock_name: str,
        alert_type: str,
        message: str,
        current_price: Optional[float] = None,
        change_pct: Optional[float] = None
    ) -> Tuple[bool, str]:
        """
        发送股票预警通知

        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            alert_type: 预警类型
            message: 预警消息
            current_price: 当前价格
            change_pct: 涨跌幅

        Returns:
            (是否成功, 消息)
        """
        title = f"⚠️ 预警 - {stock_code} {stock_name}"

        content = f"""**{stock_code} {stock_name}**

🚨 **预警类型**: {alert_type}

**预警内容**: {message}

"""
        if current_price:
            content += f"💰 **当前价格**: ¥{current_price}\n"
        if change_pct is not None:
            icon = "📈" if change_pct >= 0 else "📉"
            content += f"{icon} **涨跌幅**: {change_pct:+.2f}%\n"

        content += f"""
⏰ **触发时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

---
_智投顾问团 预警系统_
"""

        return await self.send_webhook_notification(title, content)

    # ==================== 测试接口 ====================

    async def test_webhook(self) -> Tuple[bool, str]:
        """测试Webhook配置"""
        title = "配置测试"
        content = f"""这是一条测试消息

如果您收到此消息，说明Webhook配置正确！

**配置信息**:
- 类型: {self.config['webhook_type']}
- 关键词: {self.config['webhook_keyword']}
- 时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        return await self.send_webhook_notification(title, content)

    def test_email(self) -> Tuple[bool, str]:
        """测试邮件配置"""
        subject = "智投顾问团 - 邮件配置测试"
        html_body = f"""
        <html>
        <body>
            <h2>邮件配置测试成功！</h2>
            <p>如果您收到这封邮件，说明邮件通知功能已正常工作。</p>
            <hr>
            <p><strong>配置信息：</strong></p>
            <ul>
                <li>SMTP服务器: {self.config['smtp_server']}</li>
                <li>SMTP端口: {self.config['smtp_port']}</li>
                <li>发送邮箱: {self.config['email_from']}</li>
                <li>接收邮箱: {self.config['email_to']}</li>
            </ul>
            <hr>
            <p><em>智投顾问团 InvestMindPro</em></p>
        </body>
        </html>
        """
        return self.send_email(subject, html_body)

    def get_config_status(self) -> Dict[str, Any]:
        """获取配置状态"""
        return {
            'email': {
                'enabled': self.config['email_enabled'],
                'smtp_server': self.config['smtp_server'] or '未配置',
                'smtp_port': self.config['smtp_port'],
                'email_from': self.config['email_from'] or '未配置',
                'email_to': self.config['email_to'] or '未配置',
                'configured': all([
                    self.config['smtp_server'],
                    self.config['email_from'],
                    self.config['email_password'],
                    self.config['email_to']
                ])
            },
            'webhook': {
                'enabled': self.config['webhook_enabled'],
                'type': self.config['webhook_type'],
                'keyword': self.config['webhook_keyword'],
                'url_configured': bool(self.config['webhook_url']),
                'url_preview': (self.config['webhook_url'][:50] + '...') if self.config['webhook_url'] else '未配置'
            }
        }


# 单例实例
webhook_notification_service = WebhookNotificationService()
