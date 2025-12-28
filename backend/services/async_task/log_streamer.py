"""
实时日志流服务
支持日志记录、存储和实时推送
"""
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from .redis_client import redis_client, RedisClient

logger = logging.getLogger(__name__)


class LogLevel(str, Enum):
    """日志级别"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class LogStreamer:
    """
    实时日志流服务

    功能:
    - 记录日志到 Redis
    - 实时推送日志到订阅者
    - 支持按会话/任务查询历史日志
    """

    # 日志列表前缀
    LOG_PREFIX = "logs:"
    # 日志频道前缀
    CHANNEL_PREFIX = "log_stream:"
    # 日志过期时间（秒）
    LOG_EXPIRE = 3600 * 24  # 24小时
    # 最大日志条数
    MAX_LOGS = 1000

    def __init__(self, redis: RedisClient = None):
        self.redis = redis or redis_client

    async def log(
        self,
        session_id: str,
        level: LogLevel,
        message: str,
        agent_id: str = None,
        task_id: str = None,
        extra: Dict = None
    ):
        """
        记录并推送日志

        Args:
            session_id: 会话ID
            level: 日志级别
            message: 日志消息
            agent_id: Agent ID（可选）
            task_id: 任务ID（可选）
            extra: 额外数据（可选）
        """
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level.value if isinstance(level, LogLevel) else level,
            "message": message,
            "agent_id": agent_id,
            "task_id": task_id,
            **(extra or {})
        }

        log_key = f"{self.LOG_PREFIX}{session_id}"

        # 存储日志
        await self.redis.lpush(log_key, json.dumps(log_entry, ensure_ascii=False))

        # 限制日志数量
        await self.redis.client.ltrim(log_key, 0, self.MAX_LOGS - 1) if hasattr(self.redis.client, 'ltrim') else None

        # 设置过期时间
        await self.redis.expire(log_key, self.LOG_EXPIRE)

        # 实时推送
        channel = f"{self.CHANNEL_PREFIX}{session_id}"
        await self.redis.publish(channel, json.dumps({
            "event": "log",
            "data": log_entry
        }, ensure_ascii=False))

        # 同时记录到 Python logger
        log_func = getattr(logger, level.value if isinstance(level, LogLevel) else level, logger.info)
        log_func(f"[{session_id}] {message}")

    async def debug(self, session_id: str, message: str, **kwargs):
        """记录 DEBUG 日志"""
        await self.log(session_id, LogLevel.DEBUG, message, **kwargs)

    async def info(self, session_id: str, message: str, **kwargs):
        """记录 INFO 日志"""
        await self.log(session_id, LogLevel.INFO, message, **kwargs)

    async def warning(self, session_id: str, message: str, **kwargs):
        """记录 WARNING 日志"""
        await self.log(session_id, LogLevel.WARNING, message, **kwargs)

    async def error(self, session_id: str, message: str, **kwargs):
        """记录 ERROR 日志"""
        await self.log(session_id, LogLevel.ERROR, message, **kwargs)

    async def get_logs(
        self,
        session_id: str,
        start: int = 0,
        count: int = 100,
        level: LogLevel = None
    ) -> List[Dict]:
        """
        获取历史日志

        Args:
            session_id: 会话ID
            start: 起始位置
            count: 获取数量
            level: 过滤日志级别（可选）

        Returns:
            日志列表
        """
        log_key = f"{self.LOG_PREFIX}{session_id}"
        logs = await self.redis.lrange(log_key, start, start + count - 1)

        result = []
        for log_str in logs:
            try:
                log_entry = json.loads(log_str)
                if level is None or log_entry.get("level") == level.value:
                    result.append(log_entry)
            except json.JSONDecodeError:
                continue

        return result

    async def get_log_count(self, session_id: str) -> int:
        """获取日志总数"""
        log_key = f"{self.LOG_PREFIX}{session_id}"
        return await self.redis.llen(log_key)

    async def clear_logs(self, session_id: str):
        """清除会话日志"""
        log_key = f"{self.LOG_PREFIX}{session_id}"
        await self.redis.delete(log_key)

    async def publish_event(
        self,
        session_id: str,
        event_type: str,
        data: Dict
    ):
        """
        发布自定义事件

        Args:
            session_id: 会话ID
            event_type: 事件类型
            data: 事件数据
        """
        channel = f"{self.CHANNEL_PREFIX}{session_id}"
        await self.redis.publish(channel, json.dumps({
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }, ensure_ascii=False))

    async def publish_agent_event(
        self,
        session_id: str,
        agent_id: str,
        event_type: str,
        data: Dict = None
    ):
        """
        发布 Agent 相关事件

        Args:
            session_id: 会话ID
            agent_id: Agent ID
            event_type: 事件类型 (start, progress, complete, error)
            data: 事件数据
        """
        await self.publish_event(session_id, f"agent_{event_type}", {
            "agent_id": agent_id,
            **(data or {})
        })

    async def publish_stage_event(
        self,
        session_id: str,
        stage: int,
        event_type: str,
        data: Dict = None
    ):
        """
        发布阶段相关事件

        Args:
            session_id: 会话ID
            stage: 阶段编号
            event_type: 事件类型 (start, complete)
            data: 事件数据
        """
        await self.publish_event(session_id, f"stage_{event_type}", {
            "stage": stage,
            **(data or {})
        })


# 全局日志流实例
log_streamer = LogStreamer()
