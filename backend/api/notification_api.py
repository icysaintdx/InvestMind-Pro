"""
通知服务API
提供通知配置、测试和发送功能
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from sqlalchemy.orm import Session

from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call
from backend.database.database import get_db
from backend.database.services import AlertHistoryService
from backend.services.notification_service import get_notification_service, NotificationConfig

logger = get_logger("api.notification")
router = APIRouter(prefix="/api/notification", tags=["Notification"])


# ==================== 数据模型 ====================

class TestEmailRequest(BaseModel):
    """测试邮件请求"""
    to_email: str = Field(..., description="收件人邮箱")


class TestWeChatRequest(BaseModel):
    """测试企业微信请求"""
    content: str = Field("这是一条测试消息", description="消息内容")


class SendAlertRequest(BaseModel):
    """发送预警通知请求"""
    alert_ids: Optional[List[int]] = Field(None, description="预警ID列表，不传则发送所有未读预警")
    channels: Optional[List[str]] = Field(None, description="通知渠道列表")
    email_recipients: Optional[List[str]] = Field(None, description="邮件收件人列表")


class NotificationSettingsRequest(BaseModel):
    """通知设置请求"""
    email_enabled: bool = Field(False, description="是否启用邮件通知")
    email_recipients: List[str] = Field(default_factory=list, description="邮件收件人列表")
    wechat_enabled: bool = Field(False, description="是否启用企业微信通知")
    dingtalk_enabled: bool = Field(False, description="是否启用钉钉通知")
    serverchan_enabled: bool = Field(False, description="是否启用Server酱通知")
    bark_enabled: bool = Field(False, description="是否启用Bark通知")
    alert_levels: List[str] = Field(
        default_factory=lambda: ['critical', 'high'],
        description="需要通知的预警级别"
    )


class SaveNotificationConfigRequest(BaseModel):
    """保存通知配置请求"""
    # 邮件配置
    SMTP_HOST: Optional[str] = Field(None, description="SMTP服务器地址")
    SMTP_PORT: Optional[int] = Field(None, description="SMTP端口")
    SMTP_USER: Optional[str] = Field(None, description="SMTP用户名")
    SMTP_PASSWORD: Optional[str] = Field(None, description="SMTP密码/授权码")
    SMTP_FROM: Optional[str] = Field(None, description="发件人地址")
    SMTP_USE_SSL: Optional[bool] = Field(None, description="是否使用SSL")
    EMAIL_RECIPIENTS: Optional[List[str]] = Field(None, description="默认收件人列表")
    # 企业微信配置
    WECHAT_WEBHOOK_URL: Optional[str] = Field(None, description="企业微信Webhook地址")
    # 钉钉配置
    DINGTALK_WEBHOOK_URL: Optional[str] = Field(None, description="钉钉Webhook地址")
    DINGTALK_SECRET: Optional[str] = Field(None, description="钉钉签名密钥")
    # Server酱配置
    SERVERCHAN_KEY: Optional[str] = Field(None, description="Server酱SendKey")
    # Bark配置
    BARK_KEY: Optional[str] = Field(None, description="Bark推送Key")
    BARK_SERVER: Optional[str] = Field(None, description="Bark服务器地址")


# ==================== API端点 ====================

@router.get("/status")
@log_api_call("获取通知服务状态")
async def get_notification_status():
    """
    获取通知服务配置状态
    返回各通知渠道的配置情况
    """
    try:
        service = get_notification_service()
        status = service.get_status()

        return {
            "success": True,
            "status": status
        }
    except Exception as e:
        logger.error(f"获取通知状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/channels")
@log_api_call("获取可用通知渠道")
async def get_available_channels():
    """
    获取当前可用的通知渠道列表
    """
    try:
        channels = NotificationConfig.get_available_channels()

        channel_info = {
            'email': {
                'name': '邮件通知',
                'description': '通过SMTP发送邮件通知',
                'icon': '📧',
                'configured': NotificationConfig.is_email_configured()
            },
            'wechat': {
                'name': '企业微信',
                'description': '通过企业微信机器人发送通知',
                'icon': '💬',
                'configured': NotificationConfig.is_wechat_configured()
            },
            'dingtalk': {
                'name': '钉钉',
                'description': '通过钉钉机器人发送通知',
                'icon': '🔔',
                'configured': NotificationConfig.is_dingtalk_configured()
            },
            'serverchan': {
                'name': 'Server酱',
                'description': '通过Server酱推送到微信',
                'icon': '📱',
                'configured': NotificationConfig.is_serverchan_configured()
            },
            'bark': {
                'name': 'Bark',
                'description': '通过Bark推送到iOS设备',
                'icon': '🍎',
                'configured': NotificationConfig.is_bark_configured()
            }
        }

        return {
            "success": True,
            "available": channels,
            "channels": channel_info
        }
    except Exception as e:
        logger.error(f"获取通知渠道失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/email")
@log_api_call("测试邮件通知")
async def test_email_notification(request: TestEmailRequest):
    """
    发送测试邮件
    """
    try:
        if not NotificationConfig.is_email_configured():
            raise HTTPException(status_code=400, detail="邮件服务未配置，请先配置SMTP相关环境变量")

        service = get_notification_service()

        # 发送测试邮件
        result = service.email.send(
            to_emails=[request.to_email],
            subject="[InvestMindPro] 测试邮件",
            content="""
            <html>
            <body style="font-family: Arial, sans-serif; padding: 20px;">
                <h2>📊 InvestMindPro 邮件通知测试</h2>
                <p>恭喜！您的邮件通知配置成功。</p>
                <p>当系统检测到风险预警时，将通过此邮箱向您发送通知。</p>
                <hr>
                <p style="color: #666; font-size: 12px;">此邮件由 InvestMindPro 智投顾问团 自动发送</p>
            </body>
            </html>
            """
        )

        if result['success']:
            return {"success": True, "message": "测试邮件发送成功"}
        else:
            raise HTTPException(status_code=500, detail=result['message'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试邮件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/wechat")
@log_api_call("测试企业微信通知")
async def test_wechat_notification(request: TestWeChatRequest):
    """
    发送测试企业微信消息
    """
    try:
        if not NotificationConfig.is_wechat_configured():
            raise HTTPException(status_code=400, detail="企业微信未配置，请先配置WECHAT_WEBHOOK_URL环境变量")

        service = get_notification_service()

        content = f"""## 📊 InvestMindPro 通知测试

**状态**: ✅ 配置成功

{request.content}

---
*此消息由 InvestMindPro 智投顾问团 自动发送*
"""

        result = await service.wechat.send(content)

        if result['success']:
            return {"success": True, "message": "企业微信消息发送成功"}
        else:
            raise HTTPException(status_code=500, detail=result['message'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试企业微信失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/dingtalk")
@log_api_call("测试钉钉通知")
async def test_dingtalk_notification():
    """
    发送测试钉钉消息
    """
    try:
        if not NotificationConfig.is_dingtalk_configured():
            raise HTTPException(status_code=400, detail="钉钉未配置，请先配置DINGTALK_WEBHOOK_URL环境变量")

        service = get_notification_service()

        content = """## 📊 InvestMindPro 通知测试

**状态**: ✅ 配置成功

恭喜！您的钉钉通知配置成功。

---
*此消息由 InvestMindPro 智投顾问团 自动发送*
"""

        result = await service.dingtalk.send(content, title="InvestMindPro 测试")

        if result['success']:
            return {"success": True, "message": "钉钉消息发送成功"}
        else:
            raise HTTPException(status_code=500, detail=result['message'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试钉钉失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/serverchan")
@log_api_call("测试Server酱通知")
async def test_serverchan_notification():
    """
    发送测试Server酱消息
    """
    try:
        if not NotificationConfig.is_serverchan_configured():
            raise HTTPException(status_code=400, detail="Server酱未配置，请先配置SERVERCHAN_KEY环境变量")

        service = get_notification_service()

        result = await service.serverchan.send(
            title="InvestMindPro 通知测试",
            content="恭喜！您的Server酱通知配置成功。\n\n当系统检测到风险预警时，将通过此渠道向您发送通知。"
        )

        if result['success']:
            return {"success": True, "message": "Server酱消息发送成功"}
        else:
            raise HTTPException(status_code=500, detail=result['message'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试Server酱失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/test/bark")
@log_api_call("测试Bark通知")
async def test_bark_notification():
    """
    发送测试Bark消息
    """
    try:
        if not NotificationConfig.is_bark_configured():
            raise HTTPException(status_code=400, detail="Bark未配置，请先配置BARK_KEY环境变量")

        service = get_notification_service()

        result = await service.bark.send(
            title="InvestMindPro 通知测试",
            content="恭喜！您的Bark通知配置成功。"
        )

        if result['success']:
            return {"success": True, "message": "Bark消息发送成功"}
        else:
            raise HTTPException(status_code=500, detail=result['message'])

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"测试Bark失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/send-alerts")
@log_api_call("发送预警通知")
async def send_alert_notifications(
    request: SendAlertRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    发送预警通知

    可以指定预警ID列表，或发送所有未读预警
    """
    try:
        # 获取预警列表
        if request.alert_ids:
            # 获取指定的预警
            alerts = []
            for alert_id in request.alert_ids:
                alert = db.query(AlertHistoryService).filter_by(id=alert_id).first()
                if alert:
                    alerts.append(alert.to_dict())
        else:
            # 获取所有未读预警
            alerts_obj = AlertHistoryService.get_recent_alerts(db, days=1, limit=50)
            alerts = [a.to_dict() for a in alerts_obj if not a.is_read]

        if not alerts:
            return {
                "success": True,
                "message": "没有需要发送的预警"
            }

        # 发送通知
        service = get_notification_service()
        result = await service.send_alert_notification(
            alerts=alerts,
            channels=request.channels,
            email_recipients=request.email_recipients
        )

        return {
            "success": result['success'],
            "message": result['message'],
            "alert_count": len(alerts),
            "details": result.get('details', {})
        }

    except Exception as e:
        logger.error(f"发送预警通知失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/config-guide")
@log_api_call("获取通知配置指南")
async def get_config_guide():
    """
    获取通知服务配置指南
    """
    return {
        "success": True,
        "guide": {
            "email": {
                "title": "邮件通知配置",
                "description": "通过SMTP发送邮件通知",
                "env_vars": [
                    {"name": "SMTP_HOST", "description": "SMTP服务器地址", "example": "smtp.qq.com"},
                    {"name": "SMTP_PORT", "description": "SMTP端口", "example": "465"},
                    {"name": "SMTP_USER", "description": "SMTP用户名（邮箱地址）", "example": "your@qq.com"},
                    {"name": "SMTP_PASSWORD", "description": "SMTP密码（授权码）", "example": "your_auth_code"},
                    {"name": "SMTP_FROM", "description": "发件人地址（可选）", "example": "your@qq.com"},
                    {"name": "SMTP_USE_SSL", "description": "是否使用SSL", "example": "true"}
                ],
                "tips": [
                    "QQ邮箱需要在设置中开启SMTP服务并获取授权码",
                    "163邮箱同样需要开启SMTP服务",
                    "企业邮箱请咨询管理员获取SMTP配置"
                ]
            },
            "wechat": {
                "title": "企业微信机器人配置",
                "description": "通过企业微信群机器人发送通知",
                "env_vars": [
                    {"name": "WECHAT_WEBHOOK_URL", "description": "企业微信机器人Webhook地址", "example": "https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"}
                ],
                "tips": [
                    "在企业微信群中添加机器人获取Webhook地址",
                    "支持Markdown格式消息",
                    "可以@指定成员"
                ]
            },
            "dingtalk": {
                "title": "钉钉机器人配置",
                "description": "通过钉钉群机器人发送通知",
                "env_vars": [
                    {"name": "DINGTALK_WEBHOOK_URL", "description": "钉钉机器人Webhook地址", "example": "https://oapi.dingtalk.com/robot/send?access_token=xxx"},
                    {"name": "DINGTALK_SECRET", "description": "钉钉签名密钥（可选）", "example": "SECxxx"}
                ],
                "tips": [
                    "在钉钉群中添加自定义机器人获取Webhook地址",
                    "建议开启签名验证提高安全性",
                    "支持Markdown格式消息"
                ]
            },
            "serverchan": {
                "title": "Server酱配置",
                "description": "通过Server酱推送到微信",
                "env_vars": [
                    {"name": "SERVERCHAN_KEY", "description": "Server酱SendKey", "example": "SCTxxx"}
                ],
                "tips": [
                    "访问 https://sct.ftqq.com 注册并获取SendKey",
                    "需要关注Server酱公众号接收消息",
                    "免费版每天有发送次数限制"
                ]
            },
            "bark": {
                "title": "Bark配置",
                "description": "通过Bark推送到iOS设备",
                "env_vars": [
                    {"name": "BARK_KEY", "description": "Bark推送Key", "example": "your_bark_key"},
                    {"name": "BARK_SERVER", "description": "Bark服务器地址（可选）", "example": "https://api.day.app"}
                ],
                "tips": [
                    "在App Store下载Bark应用",
                    "打开应用获取推送Key",
                    "支持自建Bark服务器"
                ]
            }
        }
    }


@router.get("/config")
@log_api_call("获取通知配置")
async def get_notification_config():
    """
    获取当前通知配置（敏感信息会脱敏）
    """
    try:
        config = NotificationConfig.get_all_config()
        return {
            "success": True,
            "config": config
        }
    except Exception as e:
        logger.error(f"获取通知配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/config")
@log_api_call("保存通知配置")
async def save_notification_config(request: SaveNotificationConfigRequest):
    """
    保存通知配置到配置文件
    只保存非空的配置项
    """
    try:
        # 构建配置字典，只包含非空值
        config = {}
        request_dict = request.model_dump(exclude_none=True)

        for key, value in request_dict.items():
            if value is not None and value != '':
                # 如果是密码字段且值为 '******'，跳过（保持原值）
                if key in ['SMTP_PASSWORD', 'DINGTALK_SECRET', 'SERVERCHAN_KEY', 'BARK_KEY']:
                    if value == '******':
                        continue
                config[key] = value

        if not config:
            return {
                "success": False,
                "message": "没有需要保存的配置"
            }

        # 保存配置
        success = NotificationConfig.save_config(config)

        if success:
            # 重新加载配置
            NotificationConfig.reload_config()
            return {
                "success": True,
                "message": "配置保存成功",
                "saved_keys": list(config.keys())
            }
        else:
            return {
                "success": False,
                "message": "配置保存失败"
            }

    except Exception as e:
        logger.error(f"保存通知配置失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 飞书/钉钉Webhook增强API ====================

class WebhookTestRequest(BaseModel):
    """Webhook测试请求"""
    webhook_type: str = Field("dingtalk", description="webhook类型: dingtalk 或 feishu")


class SendWebhookRequest(BaseModel):
    """发送Webhook消息请求"""
    title: str = Field(..., description="消息标题")
    content: str = Field(..., description="消息内容(Markdown格式)")
    at_mobiles: Optional[List[str]] = Field(None, description="需要@的手机号列表(仅钉钉)")
    at_all: bool = Field(False, description="是否@所有人(仅钉钉)")


class AnalysisNotificationRequest(BaseModel):
    """分析完成通知请求"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    rating: str = Field(..., description="投资评级")
    summary: str = Field(..., description="分析摘要")
    confidence: Optional[int] = Field(None, description="信心度(1-10)")


class AlertNotificationRequest(BaseModel):
    """预警通知请求"""
    stock_code: str = Field(..., description="股票代码")
    stock_name: str = Field(..., description="股票名称")
    alert_type: str = Field(..., description="预警类型")
    message: str = Field(..., description="预警消息")
    current_price: Optional[float] = Field(None, description="当前价格")
    change_pct: Optional[float] = Field(None, description="涨跌幅")


@router.get("/webhook/status")
@log_api_call("获取Webhook配置状态")
async def get_webhook_status():
    """获取钉钉/飞书Webhook配置状态"""
    try:
        from backend.services.webhook_notification_service import webhook_notification_service
        status = webhook_notification_service.get_config_status()
        return {"success": True, "status": status}
    except Exception as e:
        logger.error(f"获取Webhook状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/test")
@log_api_call("测试Webhook通知")
async def test_webhook_notification(request: WebhookTestRequest):
    """测试钉钉/飞书Webhook配置"""
    try:
        from backend.services.webhook_notification_service import webhook_notification_service
        original_type = webhook_notification_service.config['webhook_type']
        webhook_notification_service.config['webhook_type'] = request.webhook_type
        success, message = await webhook_notification_service.test_webhook()
        webhook_notification_service.config['webhook_type'] = original_type
        return {"success": success, "message": message, "webhook_type": request.webhook_type}
    except Exception as e:
        logger.error(f"测试Webhook失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/send")
@log_api_call("发送Webhook消息")
async def send_webhook_message(request: SendWebhookRequest):
    """发送自定义Webhook消息"""
    try:
        from backend.services.webhook_notification_service import webhook_notification_service
        success, message = await webhook_notification_service.send_webhook_notification(
            title=request.title, content=request.content,
            at_mobiles=request.at_mobiles, at_all=request.at_all
        )
        return {"success": success, "message": message}
    except Exception as e:
        logger.error(f"发送Webhook消息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/analysis")
@log_api_call("发送分析完成通知")
async def send_analysis_webhook_notification(request: AnalysisNotificationRequest):
    """发送股票分析完成通知"""
    try:
        from backend.services.webhook_notification_service import webhook_notification_service
        success, message = await webhook_notification_service.send_analysis_notification(
            stock_code=request.stock_code, stock_name=request.stock_name,
            rating=request.rating, summary=request.summary, confidence=request.confidence
        )
        return {"success": success, "message": message}
    except Exception as e:
        logger.error(f"发送分析通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/webhook/alert")
@log_api_call("发送预警通知")
async def send_alert_webhook_notification(request: AlertNotificationRequest):
    """发送股票预警通知"""
    try:
        from backend.services.webhook_notification_service import webhook_notification_service
        success, message = await webhook_notification_service.send_alert_notification(
            stock_code=request.stock_code, stock_name=request.stock_name,
            alert_type=request.alert_type, message=request.message,
            current_price=request.current_price, change_pct=request.change_pct
        )
        return {"success": success, "message": message}
    except Exception as e:
        logger.error(f"发送预警通知失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/webhook/config-guide")
@log_api_call("获取Webhook配置指南")
async def get_webhook_config_guide():
    """获取钉钉/飞书Webhook配置指南"""
    return {
        "success": True,
        "guide": {
            "dingtalk": {
                "title": "钉钉机器人配置",
                "env_vars": [
                    {"name": "WEBHOOK_ENABLED", "example": "true"},
                    {"name": "WEBHOOK_TYPE", "example": "dingtalk"},
                    {"name": "WEBHOOK_URL", "example": "https://oapi.dingtalk.com/robot/send?access_token=xxx"},
                    {"name": "WEBHOOK_KEYWORD", "example": "智投顾问团"}
                ],
                "tips": ["在钉钉群中添加自定义机器人", "安全设置选择'自定义关键词'"]
            },
            "feishu": {
                "title": "飞书机器人配置",
                "env_vars": [
                    {"name": "WEBHOOK_ENABLED", "example": "true"},
                    {"name": "WEBHOOK_TYPE", "example": "feishu"},
                    {"name": "WEBHOOK_URL", "example": "https://open.feishu.cn/open-apis/bot/v2/hook/xxx"}
                ],
                "tips": ["在飞书群中添加自定义机器人", "支持卡片消息格式"]
            }
        }
    }
