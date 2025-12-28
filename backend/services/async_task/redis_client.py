"""
Redis 客户端封装
支持连接池、自动重连、降级到内存模式
"""
import asyncio
import json
import logging
from typing import Optional, Any, Dict, List
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MemoryFallback:
    """内存降级存储，当 Redis 不可用时使用"""

    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lists: Dict[str, List] = {}
        self._pubsub_callbacks: Dict[str, List] = {}
        self._expiry: Dict[str, datetime] = {}

    async def get(self, key: str) -> Optional[str]:
        self._check_expiry(key)
        return self._data.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        self._data[key] = value
        if ex:
            self._expiry[key] = datetime.now() + timedelta(seconds=ex)

    async def hset(self, key: str, mapping: dict = None, **kwargs):
        if key not in self._data:
            self._data[key] = {}
        if mapping:
            self._data[key].update(mapping)
        self._data[key].update(kwargs)

    async def hget(self, key: str, field: str) -> Optional[str]:
        if key in self._data and isinstance(self._data[key], dict):
            return self._data[key].get(field)
        return None

    async def hgetall(self, key: str) -> dict:
        if key in self._data and isinstance(self._data[key], dict):
            return self._data[key]
        return {}

    async def lpush(self, key: str, *values):
        if key not in self._lists:
            self._lists[key] = []
        for v in values:
            self._lists[key].insert(0, v)

    async def rpush(self, key: str, *values):
        if key not in self._lists:
            self._lists[key] = []
        self._lists[key].extend(values)

    async def brpop(self, key: str, timeout: int = 0) -> Optional[tuple]:
        if key in self._lists and self._lists[key]:
            return (key, self._lists[key].pop())
        if timeout > 0:
            await asyncio.sleep(min(timeout, 1))
        return None

    async def lrange(self, key: str, start: int, end: int) -> List:
        if key not in self._lists:
            return []
        return self._lists[key][start:end+1 if end >= 0 else None]

    async def llen(self, key: str) -> int:
        return len(self._lists.get(key, []))

    async def delete(self, *keys):
        for key in keys:
            self._data.pop(key, None)
            self._lists.pop(key, None)
            self._expiry.pop(key, None)

    async def exists(self, key: str) -> bool:
        self._check_expiry(key)
        return key in self._data or key in self._lists

    async def expire(self, key: str, seconds: int):
        self._expiry[key] = datetime.now() + timedelta(seconds=seconds)

    async def publish(self, channel: str, message: str):
        """发布消息到频道"""
        if channel in self._pubsub_callbacks:
            for callback in self._pubsub_callbacks[channel]:
                try:
                    await callback(message)
                except Exception as e:
                    logger.error(f"Pubsub callback error: {e}")

    def pubsub(self):
        return MemoryPubSub(self)

    def _check_expiry(self, key: str):
        if key in self._expiry and datetime.now() > self._expiry[key]:
            self._data.pop(key, None)
            self._lists.pop(key, None)
            self._expiry.pop(key, None)


class MemoryPubSub:
    """内存模式的 PubSub 实现"""

    def __init__(self, fallback: MemoryFallback):
        self._fallback = fallback
        self._channels: List[str] = []
        self._queue: asyncio.Queue = asyncio.Queue()

    async def subscribe(self, *channels):
        for channel in channels:
            self._channels.append(channel)
            if channel not in self._fallback._pubsub_callbacks:
                self._fallback._pubsub_callbacks[channel] = []
            self._fallback._pubsub_callbacks[channel].append(self._on_message)

    async def unsubscribe(self, *channels):
        for channel in channels:
            if channel in self._channels:
                self._channels.remove(channel)
            if channel in self._fallback._pubsub_callbacks:
                try:
                    self._fallback._pubsub_callbacks[channel].remove(self._on_message)
                except ValueError:
                    pass

    async def _on_message(self, message: str):
        await self._queue.put(message)

    async def listen(self):
        while True:
            try:
                message = await asyncio.wait_for(self._queue.get(), timeout=30)
                yield {"type": "message", "data": message}
            except asyncio.TimeoutError:
                yield {"type": "ping", "data": None}


class RedisClient:
    """
    Redis 客户端封装
    - 支持连接池
    - 自动重连
    - 降级到内存模式
    """

    _instance: Optional['RedisClient'] = None

    def __init__(self, url: str = "redis://localhost:6379", db: int = 0):
        self.url = url
        self.db = db
        self._redis = None
        self._fallback = MemoryFallback()
        self._use_fallback = False
        self._lock = asyncio.Lock()

    @classmethod
    def get_instance(cls, url: str = None) -> 'RedisClient':
        """获取单例实例"""
        if cls._instance is None:
            cls._instance = cls(url or "redis://localhost:6379")
        return cls._instance

    async def connect(self) -> bool:
        """连接 Redis"""
        async with self._lock:
            try:
                import redis.asyncio as aioredis
                self._redis = aioredis.from_url(
                    self.url,
                    db=self.db,
                    encoding="utf-8",
                    decode_responses=True
                )
                # 测试连接
                await self._redis.ping()
                self._use_fallback = False
                logger.info("Redis connected successfully")
                return True
            except ImportError:
                logger.debug("redis package not installed, using memory fallback")
                self._use_fallback = True
                return False
            except Exception as e:
                logger.debug(f"Redis connection failed: {e}, using memory fallback")
                self._use_fallback = True
                return False

    async def disconnect(self):
        """断开连接"""
        if self._redis:
            await self._redis.close()
            self._redis = None

    @property
    def client(self):
        """获取当前客户端（Redis 或内存降级）"""
        if self._use_fallback or self._redis is None:
            return self._fallback
        return self._redis

    @property
    def is_redis_available(self) -> bool:
        """Redis 是否可用"""
        return not self._use_fallback and self._redis is not None

    # 代理方法
    async def get(self, key: str) -> Optional[str]:
        return await self.client.get(key)

    async def set(self, key: str, value: str, ex: int = None):
        return await self.client.set(key, value, ex=ex)

    async def hset(self, key: str, mapping: dict = None, **kwargs):
        if mapping:
            return await self.client.hset(key, mapping=mapping)
        return await self.client.hset(key, **kwargs)

    async def hget(self, key: str, field: str) -> Optional[str]:
        return await self.client.hget(key, field)

    async def hgetall(self, key: str) -> dict:
        return await self.client.hgetall(key)

    async def lpush(self, key: str, *values):
        return await self.client.lpush(key, *values)

    async def rpush(self, key: str, *values):
        return await self.client.rpush(key, *values)

    async def brpop(self, key: str, timeout: int = 0):
        return await self.client.brpop(key, timeout=timeout)

    async def lrange(self, key: str, start: int, end: int) -> List:
        return await self.client.lrange(key, start, end)

    async def llen(self, key: str) -> int:
        return await self.client.llen(key)

    async def delete(self, *keys):
        return await self.client.delete(*keys)

    async def exists(self, key: str) -> bool:
        return await self.client.exists(key)

    async def expire(self, key: str, seconds: int):
        return await self.client.expire(key, seconds)

    async def publish(self, channel: str, message: str):
        return await self.client.publish(channel, message)

    def pubsub(self):
        return self.client.pubsub()


# 全局实例
redis_client = RedisClient.get_instance()
