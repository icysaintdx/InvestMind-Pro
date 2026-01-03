"""
通知服务模块
支持邮件和微信推送通知
"""

import os
import smtplib
import hashlib
import hmac
import base64
import urllib.parse
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.header import Header
from typing import List, Dict, Optional, Any
from datetime import datetime
import json
from pathlib import Path

import httpx

from backend.utils.logging_config import get_logger

logger = get_logger("notification")

# 配置文件路径
CONFIG_FILE_PATH = Path(__file__).parent.parent / 'config' / 'notification_config.json'


# 自定义 classproperty 装饰器
class classproperty:
    """类属性装饰器，允许在类上定义属性"""
    def __init__(self, func):
        self.func = func

    def __get__(self, obj, objtype=None):
        return self.func(objtype)


class NotificationConfig:
    """通知配置 - 支持从配置文件和环境变量读取"""

    # 内存缓存
    _config_cache: Dict[str, Any] = {}
    _config_loaded: bool = False

    @classmethod
    def _load_config_file(cls) -> Dict[str, Any]:
        """从配置文件加载配置"""
        if CONFIG_FILE_PATH.exists():
            try:
                with open(CONFIG_FILE_PATH, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"加载通知配置文件失败: {e}")
        return {}

    @classmethod
    def _get_config(cls, key: str, default: Any = '') -> Any:
        """获取配置值，优先从配置文件读取，其次从环境变量"""
        # 先尝试从配置文件读取
        if not cls._config_loaded:
            cls._config_cache = cls._load_config_file()
            cls._config_loaded = True

        if key in cls._config_cache:
            return cls._config_cache[key]

        # 回退到环境变量
        return os.getenv(key, default)

    @classmethod
    def reload_config(cls):
        """重新加载配置"""
        cls._config_cache = cls._load_config_file()
        cls._config_loaded = True
        logger.info("通知配置已重新加载")

    @classmethod
    def save_config(cls, config: Dict[str, Any]) -> bool:
        """保存配置到文件"""
        try:
            # 确保目录存在
            CONFIG_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

            # 读取现有配置
            existing_config = cls._load_config_file()

            # 合并配置
            existing_config.update(config)

            # 保存到文件
            with open(CONFIG_FILE_PATH, 'w', encoding='utf-8') as f:
                json.dump(existing_config, f, ensure_ascii=False, indent=2)

            # 更新缓存
            cls._config_cache = existing_config
            cls._config_loaded = True

            logger.info(f"通知配置已保存到: {CONFIG_FILE_PATH}")
            return True
        except Exception as e:
            logger.error(f"保存通知配置失败: {e}")
            return False

    @classmethod
    def get_all_config(cls) -> Dict[str, Any]:
        """获取所有配置（用于前端显示，密码会被脱敏）"""
        if not cls._config_loaded:
            cls._config_cache = cls._load_config_file()
            cls._config_loaded = True

        # 返回脱敏后的配置
        config = {
            'SMTP_HOST': cls.SMTP_HOST,
            'SMTP_PORT': cls.SMTP_PORT,
            'SMTP_USER': cls.SMTP_USER,
            'SMTP_PASSWORD': '******' if cls.SMTP_PASSWORD else '',
            'SMTP_FROM': cls.SMTP_FROM,
            'SMTP_USE_SSL': cls.SMTP_USE_SSL,
            'EMAIL_RECIPIENTS': cls.EMAIL_RECIPIENTS,
            'WECHAT_WEBHOOK_URL': cls._mask_url(cls.WECHAT_WEBHOOK_URL),
            'DINGTALK_WEBHOOK_URL': cls._mask_url(cls.DINGTALK_WEBHOOK_URL),
            'DINGTALK_SECRET': '******' if cls.DINGTALK_SECRET else '',
            'SERVERCHAN_KEY': '******' if cls.SERVERCHAN_KEY else '',
            'BARK_KEY': '******' if cls.BARK_KEY else '',
            'BARK_SERVER': cls.BARK_SERVER,
        }
        return config

    @classmethod
    def _mask_url(cls, url: str) -> str:
        """脱敏URL"""
        if not url:
            return ''
        if len(url) > 20:
            return url[:15] + '...' + url[-5:]
        return url

    # 邮件配置 - 使用类属性动态获取
    @classproperty
    def SMTP_HOST(cls) -> str:
        return cls._get_config('SMTP_HOST', 'smtp.qq.com')

    @classproperty
    def SMTP_PORT(cls) -> int:
        port = cls._get_config('SMTP_PORT', '465')
        return int(port) if port else 465

    @classproperty
    def SMTP_USER(cls) -> str:
        return cls._get_config('SMTP_USER', '')

    @classproperty
    def SMTP_PASSWORD(cls) -> str:
        return cls._get_config('SMTP_PASSWORD', '')

    @classproperty
    def SMTP_FROM(cls) -> str:
        return cls._get_config('SMTP_FROM', '')

    @classproperty
    def SMTP_USE_SSL(cls) -> bool:
        val = cls._get_config('SMTP_USE_SSL', 'true')
        if isinstance(val, bool):
            return val
        return str(val).lower() == 'true'

    # 邮件收件人列表
    @classproperty
    def EMAIL_RECIPIENTS(cls) -> List[str]:
        """获取默认邮件收件人列表"""
        recipients = cls._get_config('EMAIL_RECIPIENTS', [])
        if isinstance(recipients, str):
            # 支持逗号分隔的字符串格式
            return [r.strip() for r in recipients.split(',') if r.strip()]
        return recipients if isinstance(recipients, list) else []

    # 企业微信配置
    @classproperty
    def WECHAT_WEBHOOK_URL(cls) -> str:
        return cls._get_config('WECHAT_WEBHOOK_URL', '')

    # 钉钉配置
    @classproperty
    def DINGTALK_WEBHOOK_URL(cls) -> str:
        return cls._get_config('DINGTALK_WEBHOOK_URL', '')

    @classproperty
    def DINGTALK_SECRET(cls) -> str:
        return cls._get_config('DINGTALK_SECRET', '')

    # Server酱配置
    @classproperty
    def SERVERCHAN_KEY(cls) -> str:
        return cls._get_config('SERVERCHAN_KEY', '')

    # Bark配置
    @classproperty
    def BARK_KEY(cls) -> str:
        return cls._get_config('BARK_KEY', '')

    @classproperty
    def BARK_SERVER(cls) -> str:
        return cls._get_config('BARK_SERVER', 'https://api.day.app')

    @classmethod
    def is_email_configured(cls) -> bool:
        """检查邮件是否已配置"""
        return bool(cls.SMTP_USER and cls.SMTP_PASSWORD)

    @classmethod
    def is_wechat_configured(cls) -> bool:
        """检查企业微信是否已配置"""
        return bool(cls.WECHAT_WEBHOOK_URL)

    @classmethod
    def is_dingtalk_configured(cls) -> bool:
        """检查钉钉是否已配置"""
        return bool(cls.DINGTALK_WEBHOOK_URL)

    @classmethod
    def is_serverchan_configured(cls) -> bool:
        """检查Server酱是否已配置"""
        return bool(cls.SERVERCHAN_KEY)

    @classmethod
    def is_bark_configured(cls) -> bool:
        """检查Bark是否已配置"""
        return bool(cls.BARK_KEY)

    @classmethod
    def get_available_channels(cls) -> List[str]:
        """获取可用的通知渠道"""
        channels = []
        if cls.is_email_configured():
            channels.append('email')
        if cls.is_wechat_configured():
            channels.append('wechat')
        if cls.is_dingtalk_configured():
            channels.append('dingtalk')
        if cls.is_serverchan_configured():
            channels.append('serverchan')
        if cls.is_bark_configured():
            channels.append('bark')
        return channels


class EmailNotifier:
    """邮件通知器"""

    def __init__(self):
        self.config = NotificationConfig

    def send(
        self,
        to_emails: List[str],
        subject: str,
        content: str,
        content_type: str = 'html'
    ) -> Dict[str, Any]:
        """
        发送邮件

        Args:
            to_emails: 收件人列表
            subject: 邮件主题
            content: 邮件内容
            content_type: 内容类型 (html/plain)

        Returns:
            {'success': bool, 'message': str}
        """
        if not self.config.is_email_configured():
            return {'success': False, 'message': '邮件服务未配置'}

        try:
            # 创建邮件
            msg = MIMEMultipart('alternative')
            msg['Subject'] = Header(subject, 'utf-8')
            msg['From'] = self.config.SMTP_FROM or self.config.SMTP_USER
            msg['To'] = ', '.join(to_emails)

            # 添加内容
            if content_type == 'html':
                part = MIMEText(content, 'html', 'utf-8')
            else:
                part = MIMEText(content, 'plain', 'utf-8')
            msg.attach(part)

            # 发送邮件
            if self.config.SMTP_USE_SSL:
                server = smtplib.SMTP_SSL(self.config.SMTP_HOST, self.config.SMTP_PORT)
            else:
                server = smtplib.SMTP(self.config.SMTP_HOST, self.config.SMTP_PORT)
                server.starttls()

            server.login(self.config.SMTP_USER, self.config.SMTP_PASSWORD)
            server.sendmail(
                self.config.SMTP_FROM or self.config.SMTP_USER,
                to_emails,
                msg.as_string()
            )
            server.quit()

            logger.info(f"✅ 邮件发送成功: {subject} -> {to_emails}")
            return {'success': True, 'message': '邮件发送成功'}

        except Exception as e:
            logger.error(f"❌ 邮件发送失败: {e}")
            return {'success': False, 'message': str(e)}


class WeChatNotifier:
    """企业微信通知器"""

    def __init__(self):
        self.config = NotificationConfig

    async def send(
        self,
        content: str,
        msg_type: str = 'markdown',
        mentioned_list: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        发送企业微信消息

        Args:
            content: 消息内容
            msg_type: 消息类型 (text/markdown)
            mentioned_list: @的用户列表

        Returns:
            {'success': bool, 'message': str}
        """
        if not self.config.is_wechat_configured():
            return {'success': False, 'message': '企业微信未配置'}

        try:
            if msg_type == 'markdown':
                data = {
                    'msgtype': 'markdown',
                    'markdown': {
                        'content': content
                    }
                }
            else:
                data = {
                    'msgtype': 'text',
                    'text': {
                        'content': content,
                        'mentioned_list': mentioned_list or []
                    }
                }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.config.WECHAT_WEBHOOK_URL,
                    json=data,
                    timeout=10
                )
                result = response.json()

            if result.get('errcode') == 0:
                logger.info(f"✅ 企业微信消息发送成功")
                return {'success': True, 'message': '发送成功'}
            else:
                logger.error(f"❌ 企业微信发送失败: {result}")
                return {'success': False, 'message': result.get('errmsg', '未知错误')}

        except Exception as e:
            logger.error(f"❌ 企业微信发送异常: {e}")
            return {'success': False, 'message': str(e)}


class DingTalkNotifier:
    """钉钉通知器"""

    def __init__(self):
        self.config = NotificationConfig

    def _generate_sign(self) -> tuple:
        """生成钉钉签名"""
        timestamp = str(round(time.time() * 1000))
        secret = self.config.DINGTALK_SECRET

        if not secret:
            return timestamp, ''

        secret_enc = secret.encode('utf-8')
        string_to_sign = f'{timestamp}\n{secret}'
        string_to_sign_enc = string_to_sign.encode('utf-8')
        hmac_code = hmac.new(secret_enc, string_to_sign_enc, digestmod=hashlib.sha256).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))

        return timestamp, sign

    async def send(
        self,
        content: str,
        msg_type: str = 'markdown',
        title: str = '预警通知',
        at_mobiles: Optional[List[str]] = None,
        at_all: bool = False
    ) -> Dict[str, Any]:
        """
        发送钉钉消息

        Args:
            content: 消息内容
            msg_type: 消息类型 (text/markdown)
            title: 标题 (markdown类型需要)
            at_mobiles: @的手机号列表
            at_all: 是否@所有人

        Returns:
            {'success': bool, 'message': str}
        """
        if not self.config.is_dingtalk_configured():
            return {'success': False, 'message': '钉钉未配置'}

        try:
            timestamp, sign = self._generate_sign()

            url = self.config.DINGTALK_WEBHOOK_URL
            if sign:
                url = f"{url}&timestamp={timestamp}&sign={sign}"

            if msg_type == 'markdown':
                data = {
                    'msgtype': 'markdown',
                    'markdown': {
                        'title': title,
                        'text': content
                    },
                    'at': {
                        'atMobiles': at_mobiles or [],
                        'isAtAll': at_all
                    }
                }
            else:
                data = {
                    'msgtype': 'text',
                    'text': {
                        'content': content
                    },
                    'at': {
                        'atMobiles': at_mobiles or [],
                        'isAtAll': at_all
                    }
                }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=10)
                result = response.json()

            if result.get('errcode') == 0:
                logger.info(f"✅ 钉钉消息发送成功")
                return {'success': True, 'message': '发送成功'}
            else:
                logger.error(f"❌ 钉钉发送失败: {result}")
                return {'success': False, 'message': result.get('errmsg', '未知错误')}

        except Exception as e:
            logger.error(f"❌ 钉钉发送异常: {e}")
            return {'success': False, 'message': str(e)}


class ServerChanNotifier:
    """Server酱通知器 (微信推送)"""

    def __init__(self):
        self.config = NotificationConfig

    async def send(
        self,
        title: str,
        content: str = ''
    ) -> Dict[str, Any]:
        """
        发送Server酱消息

        Args:
            title: 消息标题
            content: 消息内容 (支持Markdown)

        Returns:
            {'success': bool, 'message': str}
        """
        if not self.config.is_serverchan_configured():
            return {'success': False, 'message': 'Server酱未配置'}

        try:
            url = f"https://sctapi.ftqq.com/{self.config.SERVERCHAN_KEY}.send"

            data = {
                'title': title,
                'desp': content
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, data=data, timeout=10)
                result = response.json()

            if result.get('code') == 0:
                logger.info(f"✅ Server酱消息发送成功")
                return {'success': True, 'message': '发送成功'}
            else:
                logger.error(f"❌ Server酱发送失败: {result}")
                return {'success': False, 'message': result.get('message', '未知错误')}

        except Exception as e:
            logger.error(f"❌ Server酱发送异常: {e}")
            return {'success': False, 'message': str(e)}


class BarkNotifier:
    """Bark通知器 (iOS推送)"""

    def __init__(self):
        self.config = NotificationConfig

    async def send(
        self,
        title: str,
        content: str,
        group: str = 'InvestMindPro',
        sound: str = 'alarm'
    ) -> Dict[str, Any]:
        """
        发送Bark消息

        Args:
            title: 消息标题
            content: 消息内容
            group: 消息分组
            sound: 提示音

        Returns:
            {'success': bool, 'message': str}
        """
        if not self.config.is_bark_configured():
            return {'success': False, 'message': 'Bark未配置'}

        try:
            url = f"{self.config.BARK_SERVER}/{self.config.BARK_KEY}"

            data = {
                'title': title,
                'body': content,
                'group': group,
                'sound': sound
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=data, timeout=10)
                result = response.json()

            if result.get('code') == 200:
                logger.info(f"✅ Bark消息发送成功")
                return {'success': True, 'message': '发送成功'}
            else:
                logger.error(f"❌ Bark发送失败: {result}")
                return {'success': False, 'message': result.get('message', '未知错误')}

        except Exception as e:
            logger.error(f"❌ Bark发送异常: {e}")
            return {'success': False, 'message': str(e)}


class NotificationService:
    """统一通知服务"""

    def __init__(self):
        self.email = EmailNotifier()
        self.wechat = WeChatNotifier()
        self.dingtalk = DingTalkNotifier()
        self.serverchan = ServerChanNotifier()
        self.bark = BarkNotifier()

    def get_status(self) -> Dict[str, Any]:
        """获取通知服务状态"""
        return {
            'available_channels': NotificationConfig.get_available_channels(),
            'email': {
                'configured': NotificationConfig.is_email_configured(),
                'host': NotificationConfig.SMTP_HOST,
                'user': NotificationConfig.SMTP_USER[:3] + '***' if NotificationConfig.SMTP_USER else ''
            },
            'wechat': {
                'configured': NotificationConfig.is_wechat_configured()
            },
            'dingtalk': {
                'configured': NotificationConfig.is_dingtalk_configured()
            },
            'serverchan': {
                'configured': NotificationConfig.is_serverchan_configured()
            },
            'bark': {
                'configured': NotificationConfig.is_bark_configured()
            }
        }

    def format_alert_email(self, alerts: List[Dict]) -> str:
        """格式化预警邮件内容"""
        html = """
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; background: #f5f5f5; padding: 20px; }
                .container { max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; padding: 20px; }
                .header { text-align: center; border-bottom: 2px solid #3b82f6; padding-bottom: 15px; margin-bottom: 20px; }
                .header h1 { color: #1e40af; margin: 0; }
                .alert { border-left: 4px solid; padding: 15px; margin-bottom: 15px; border-radius: 4px; }
                .alert.critical { border-color: #ef4444; background: #fef2f2; }
                .alert.high { border-color: #f59e0b; background: #fffbeb; }
                .alert.medium { border-color: #eab308; background: #fefce8; }
                .alert.low { border-color: #22c55e; background: #f0fdf4; }
                .alert-title { font-weight: bold; margin-bottom: 8px; }
                .alert-message { color: #374151; margin-bottom: 8px; }
                .alert-suggestion { color: #6b7280; font-style: italic; font-size: 14px; }
                .footer { text-align: center; color: #9ca3af; font-size: 12px; margin-top: 20px; padding-top: 15px; border-top: 1px solid #e5e7eb; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 InvestMindPro 风险预警</h1>
                    <p>""" + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + """</p>
                </div>
        """

        for alert in alerts:
            level = alert.get('level', 'medium')
            html += f"""
                <div class="alert {level}">
                    <div class="alert-title">{alert.get('title', '')}</div>
                    <div class="alert-message">{alert.get('message', '')}</div>
                    <div class="alert-suggestion">💡 {alert.get('suggestion', '')}</div>
                </div>
            """

        html += """
                <div class="footer">
                    <p>此邮件由 InvestMindPro 智投顾问团 自动发送</p>
                    <p>如需取消订阅，请在系统设置中关闭邮件通知</p>
                </div>
            </div>
        </body>
        </html>
        """

        return html

    def format_alert_markdown(self, alerts: List[Dict]) -> str:
        """格式化预警为Markdown格式"""
        level_icons = {
            'critical': '🔴',
            'high': '🟠',
            'medium': '🟡',
            'low': '🟢'
        }

        md = f"## 📊 InvestMindPro 风险预警\n\n"
        md += f"**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        md += f"**预警数量**: {len(alerts)}条\n\n"
        md += "---\n\n"

        for alert in alerts:
            level = alert.get('level', 'medium')
            icon = level_icons.get(level, '⚪')

            md += f"### {icon} {alert.get('title', '')}\n\n"
            md += f"**股票**: {alert.get('stock_code', '')}\n\n"
            md += f"**详情**: {alert.get('message', '')}\n\n"
            md += f"**建议**: {alert.get('suggestion', '')}\n\n"
            md += "---\n\n"

        return md

    async def send_alert_notification(
        self,
        alerts: List[Dict],
        channels: Optional[List[str]] = None,
        email_recipients: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        发送预警通知

        Args:
            alerts: 预警列表
            channels: 通知渠道列表 (email/wechat/dingtalk/serverchan/bark)
            email_recipients: 邮件收件人列表

        Returns:
            各渠道发送结果
        """
        if not alerts:
            return {'success': True, 'message': '无预警需要发送'}

        # 默认使用所有可用渠道
        if channels is None:
            channels = NotificationConfig.get_available_channels()

        results = {}

        # 邮件通知
        if 'email' in channels and email_recipients:
            subject = f"[InvestMindPro] 风险预警 - {len(alerts)}条新预警"
            content = self.format_alert_email(alerts)
            results['email'] = self.email.send(email_recipients, subject, content)

        # 企业微信通知
        if 'wechat' in channels:
            content = self.format_alert_markdown(alerts)
            results['wechat'] = await self.wechat.send(content)

        # 钉钉通知
        if 'dingtalk' in channels:
            content = self.format_alert_markdown(alerts)
            results['dingtalk'] = await self.dingtalk.send(
                content,
                title=f"风险预警 - {len(alerts)}条"
            )

        # Server酱通知
        if 'serverchan' in channels:
            title = f"[InvestMindPro] {len(alerts)}条风险预警"
            content = self.format_alert_markdown(alerts)
            results['serverchan'] = await self.serverchan.send(title, content)

        # Bark通知
        if 'bark' in channels:
            title = f"InvestMindPro 风险预警"
            # Bark内容简短
            content = f"检测到{len(alerts)}条风险预警，请及时查看"
            results['bark'] = await self.bark.send(title, content)

        # 统计结果
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(results)

        logger.info(f"📤 预警通知发送完成: {success_count}/{total_count} 成功")

        return {
            'success': success_count > 0,
            'message': f'{success_count}/{total_count} 渠道发送成功',
            'details': results
        }


# 全局实例
_notification_service = None


def get_notification_service() -> NotificationService:
    """获取通知服务实例"""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service
