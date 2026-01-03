"""
WebSocket API - 数据流实时通知
用于向前端推送数据更新通知
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from typing import Dict, Set, List
import json
import asyncio
from datetime import datetime

from backend.utils.logging_config import get_logger

logger = get_logger("api.websocket")
router = APIRouter(tags=["WebSocket"])


class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        # 活跃连接: {client_id: WebSocket}
        self.active_connections: Dict[str, WebSocket] = {}
        # 订阅关系: {ts_code: Set[client_id]}
        self.subscriptions: Dict[str, Set[str]] = {}
        # 新闻订阅: Set[client_id] - 订阅新闻推送的客户端
        self.news_subscribers: Set[str] = set()
        # 连接计数器
        self._connection_counter = 0

    async def connect(self, websocket: WebSocket) -> str:
        """接受新连接，返回client_id"""
        await websocket.accept()
        self._connection_counter += 1
        client_id = f"client_{self._connection_counter}_{datetime.now().strftime('%H%M%S')}"
        self.active_connections[client_id] = websocket
        logger.info(f"[WebSocket] 新连接: {client_id}, 当前连接数: {len(self.active_connections)}")
        return client_id

    def disconnect(self, client_id: str):
        """断开连接"""
        if client_id in self.active_connections:
            del self.active_connections[client_id]
            # 清理订阅
            for ts_code in list(self.subscriptions.keys()):
                self.subscriptions[ts_code].discard(client_id)
                if not self.subscriptions[ts_code]:
                    del self.subscriptions[ts_code]
            # 清理新闻订阅
            self.news_subscribers.discard(client_id)
            logger.info(f"[WebSocket] 断开连接: {client_id}, 剩余连接数: {len(self.active_connections)}")

    def subscribe(self, client_id: str, ts_code: str):
        """订阅股票更新"""
        if ts_code not in self.subscriptions:
            self.subscriptions[ts_code] = set()
        self.subscriptions[ts_code].add(client_id)
        logger.debug(f"[WebSocket] {client_id} 订阅 {ts_code}")

    def unsubscribe(self, client_id: str, ts_code: str):
        """取消订阅"""
        if ts_code in self.subscriptions:
            self.subscriptions[ts_code].discard(client_id)
            if not self.subscriptions[ts_code]:
                del self.subscriptions[ts_code]

    def subscribe_news(self, client_id: str):
        """订阅新闻推送"""
        self.news_subscribers.add(client_id)
        logger.debug(f"[WebSocket] {client_id} 订阅新闻推送")

    def unsubscribe_news(self, client_id: str):
        """取消新闻订阅"""
        self.news_subscribers.discard(client_id)

    async def send_personal_message(self, message: dict, client_id: str):
        """发送消息给特定客户端"""
        if client_id in self.active_connections:
            try:
                websocket = self.active_connections[client_id]
                # 检查连接状态
                if websocket.client_state.name == "CONNECTED":
                    await websocket.send_json(message)
            except Exception as e:
                # 只记录非正常关闭的错误
                error_msg = str(e)
                if "close frame" not in error_msg.lower() and "disconnect" not in error_msg.lower():
                    logger.warning(f"[WebSocket] 发送消息失败: {client_id}, {error_msg[:50]}")
                self.disconnect(client_id)

    async def broadcast(self, message: dict):
        """广播消息给所有连接"""
        disconnected = []
        for client_id, connection in self.active_connections.items():
            try:
                if connection.client_state.name == "CONNECTED":
                    await connection.send_json(message)
            except Exception as e:
                error_msg = str(e)
                if "close frame" not in error_msg.lower() and "disconnect" not in error_msg.lower():
                    logger.warning(f"[WebSocket] 广播失败: {client_id}, {error_msg[:50]}")
                disconnected.append(client_id)

        # 清理断开的连接
        for client_id in disconnected:
            self.disconnect(client_id)

    async def notify_stock_update(self, ts_code: str, event: str, data: dict = None):
        """
        通知订阅了特定股票的客户端

        Args:
            ts_code: 股票代码
            event: 事件类型 (update_complete, update_progress, update_error)
            data: 附加数据
        """
        if ts_code not in self.subscriptions:
            return

        message = {
            "type": "stock_update",
            "event": event,
            "ts_code": ts_code,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }

        disconnected = []
        for client_id in self.subscriptions[ts_code]:
            if client_id in self.active_connections:
                try:
                    websocket = self.active_connections[client_id]
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_json(message)
                except Exception as e:
                    error_msg = str(e)
                    if "close frame" not in error_msg.lower() and "disconnect" not in error_msg.lower():
                        logger.warning(f"[WebSocket] 通知失败: {client_id}, {error_msg[:50]}")
                    disconnected.append(client_id)

        # 清理断开的连接
        for client_id in disconnected:
            self.disconnect(client_id)

    def get_status(self) -> dict:
        """获取连接状态"""
        return {
            "active_connections": len(self.active_connections),
            "news_subscribers": len(self.news_subscribers),
            "subscriptions": {
                ts_code: len(clients)
                for ts_code, clients in self.subscriptions.items()
            }
        }

    async def notify_news(self, news_list: List[dict], urgency: str = "normal"):
        """
        推送新闻给订阅者

        Args:
            news_list: 新闻列表
            urgency: 紧急程度 (critical/high/normal)
        """
        if not self.news_subscribers:
            return

        message = {
            "type": "news_update",
            "urgency": urgency,
            "timestamp": datetime.now().isoformat(),
            "count": len(news_list),
            "news": news_list[:10]  # 最多推送10条
        }

        disconnected = []
        for client_id in self.news_subscribers:
            if client_id in self.active_connections:
                try:
                    websocket = self.active_connections[client_id]
                    if websocket.client_state.name == "CONNECTED":
                        await websocket.send_json(message)
                except Exception as e:
                    error_msg = str(e)
                    if "close frame" not in error_msg.lower() and "disconnect" not in error_msg.lower():
                        logger.warning(f"[WebSocket] 新闻推送失败: {client_id}, {error_msg[:50]}")
                    disconnected.append(client_id)

        for client_id in disconnected:
            self.disconnect(client_id)

        if news_list:
            logger.info(f"[WebSocket] 推送 {len(news_list)} 条新闻给 {len(self.news_subscribers)} 个订阅者")


# 全局连接管理器
manager = ConnectionManager()


@router.websocket("/ws/dataflow")
async def websocket_dataflow(websocket: WebSocket):
    """
    数据流WebSocket端点

    消息格式:
    - 订阅股票: {"action": "subscribe", "ts_code": "600519.SH"}
    - 取消订阅: {"action": "unsubscribe", "ts_code": "600519.SH"}
    - 订阅新闻: {"action": "subscribe_news"}
    - 取消新闻订阅: {"action": "unsubscribe_news"}
    - 心跳: {"action": "ping"}

    服务端推送:
    - 数据更新: {"type": "stock_update", "event": "update_complete", "ts_code": "...", "data": {...}}
    - 新闻更新: {"type": "news_update", "urgency": "...", "count": N, "news": [...]}
    - 心跳响应: {"type": "pong", "timestamp": "..."}
    """
    client_id = await manager.connect(websocket)

    try:
        # 发送欢迎消息
        await manager.send_personal_message({
            "type": "connected",
            "client_id": client_id,
            "message": "WebSocket连接成功"
        }, client_id)

        while True:
            # 接收消息
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
                action = message.get("action")

                if action == "subscribe":
                    ts_code = message.get("ts_code")
                    if ts_code:
                        manager.subscribe(client_id, ts_code)
                        await manager.send_personal_message({
                            "type": "subscribed",
                            "ts_code": ts_code
                        }, client_id)

                elif action == "unsubscribe":
                    ts_code = message.get("ts_code")
                    if ts_code:
                        manager.unsubscribe(client_id, ts_code)
                        await manager.send_personal_message({
                            "type": "unsubscribed",
                            "ts_code": ts_code
                        }, client_id)

                elif action == "subscribe_news":
                    manager.subscribe_news(client_id)
                    await manager.send_personal_message({
                        "type": "subscribed_news",
                        "message": "已订阅新闻推送"
                    }, client_id)

                elif action == "unsubscribe_news":
                    manager.unsubscribe_news(client_id)
                    await manager.send_personal_message({
                        "type": "unsubscribed_news",
                        "message": "已取消新闻订阅"
                    }, client_id)

                elif action == "ping":
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    }, client_id)

                elif action == "status":
                    await manager.send_personal_message({
                        "type": "status",
                        "data": manager.get_status()
                    }, client_id)

            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "无效的JSON格式"
                }, client_id)

    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        logger.error(f"[WebSocket] 错误: {client_id}, {e}")
        manager.disconnect(client_id)


@router.get("/ws/status")
async def get_websocket_status():
    """获取WebSocket连接状态"""
    return {
        "success": True,
        "status": manager.get_status()
    }


# 导出通知函数供其他模块使用
async def notify_stock_updated(ts_code: str, data: dict = None):
    """
    通知股票数据已更新（供其他模块调用）

    Args:
        ts_code: 股票代码
        data: 更新的数据摘要
    """
    await manager.notify_stock_update(ts_code, "update_complete", data)


async def notify_stock_update_progress(ts_code: str, progress: int, message: str = ""):
    """
    通知股票数据更新进度

    Args:
        ts_code: 股票代码
        progress: 进度百分比 (0-100)
        message: 进度消息
    """
    await manager.notify_stock_update(ts_code, "update_progress", {
        "progress": progress,
        "message": message
    })


async def notify_stock_update_error(ts_code: str, error: str):
    """
    通知股票数据更新失败

    Args:
        ts_code: 股票代码
        error: 错误信息
    """
    await manager.notify_stock_update(ts_code, "update_error", {
        "error": error
    })


def get_connection_manager() -> ConnectionManager:
    """获取连接管理器实例"""
    return manager


async def notify_news_update(news_list: List[dict], urgency: str = "normal"):
    """
    推送新闻更新（供其他模块调用）

    Args:
        news_list: 新闻列表
        urgency: 紧急程度 (critical/high/normal)
    """
    await manager.notify_news(news_list, urgency)


async def notify_urgent_news(news_list: List[dict]):
    """
    推送紧急新闻（供其他模块调用）

    Args:
        news_list: 紧急新闻列表
    """
    await manager.notify_news(news_list, "critical")
