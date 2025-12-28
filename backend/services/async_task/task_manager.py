"""
异步任务管理器
负责任务的提交、状态管理、进度更新
"""
import asyncio
import json
import uuid
import logging
from typing import Optional, Dict, Any, Callable, List
from datetime import datetime
from enum import Enum
from dataclasses import dataclass, asdict

from .redis_client import redis_client, RedisClient

logger = logging.getLogger(__name__)


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"       # 等待执行
    RUNNING = "running"       # 执行中
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消


class TaskPriority(int, Enum):
    """任务优先级"""
    HIGH = 0
    NORMAL = 1
    LOW = 2


@dataclass
class TaskInfo:
    """任务信息"""
    task_id: str
    task_type: str
    status: TaskStatus
    progress: int = 0
    message: str = ""
    result: Any = None
    error: str = None
    created_at: str = None
    started_at: str = None
    completed_at: str = None
    payload: Dict = None

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "status": self.status.value if isinstance(self.status, TaskStatus) else self.status,
            "progress": self.progress,
            "message": self.message,
            "result": self.result,
            "error": self.error,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
        }


class TaskManager:
    """
    异步任务管理器

    功能:
    - 提交任务到队列
    - 查询任务状态
    - 更新任务进度
    - 发布任务事件
    """

    # 队列名称前缀
    QUEUE_PREFIX = "task_queue:"
    # 任务信息前缀
    TASK_PREFIX = "task:"
    # 任务过期时间（秒）
    TASK_EXPIRE = 3600 * 24  # 24小时

    def __init__(self, redis: RedisClient = None):
        self.redis = redis or redis_client
        self._handlers: Dict[str, Callable] = {}
        self._running = False
        self._workers: List[asyncio.Task] = []

    async def initialize(self):
        """初始化任务管理器"""
        await self.redis.connect()
        logger.info("TaskManager initialized")

    async def shutdown(self):
        """关闭任务管理器"""
        self._running = False
        for worker in self._workers:
            worker.cancel()
        await self.redis.disconnect()
        logger.info("TaskManager shutdown")

    def register_handler(self, task_type: str, handler: Callable):
        """注册任务处理器"""
        self._handlers[task_type] = handler
        logger.info(f"Registered handler for task type: {task_type}")

    async def submit_task(
        self,
        task_type: str,
        payload: Dict,
        priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        提交任务

        Args:
            task_type: 任务类型
            payload: 任务数据
            priority: 优先级

        Returns:
            task_id: 任务ID
        """
        task_id = str(uuid.uuid4())
        now = datetime.now().isoformat()

        task_info = TaskInfo(
            task_id=task_id,
            task_type=task_type,
            status=TaskStatus.PENDING,
            progress=0,
            message="任务已提交",
            created_at=now,
            payload=payload
        )

        # 保存任务信息
        await self.redis.hset(
            f"{self.TASK_PREFIX}{task_id}",
            mapping={
                "task_id": task_id,
                "task_type": task_type,
                "status": TaskStatus.PENDING.value,
                "progress": "0",
                "message": "任务已提交",
                "created_at": now,
                "payload": json.dumps(payload, ensure_ascii=False)
            }
        )
        await self.redis.expire(f"{self.TASK_PREFIX}{task_id}", self.TASK_EXPIRE)

        # 加入队列
        queue_name = f"{self.QUEUE_PREFIX}{priority.value}"
        await self.redis.lpush(queue_name, json.dumps({
            "task_id": task_id,
            "task_type": task_type,
            "payload": payload
        }, ensure_ascii=False))

        logger.info(f"Task submitted: {task_id} ({task_type})")

        # 发布任务创建事件
        await self.publish_event(task_id, "task_created", task_info.to_dict())

        return task_id

    async def get_task_status(self, task_id: str) -> Optional[TaskInfo]:
        """获取任务状态"""
        data = await self.redis.hgetall(f"{self.TASK_PREFIX}{task_id}")
        if not data:
            return None

        return TaskInfo(
            task_id=data.get("task_id", task_id),
            task_type=data.get("task_type", ""),
            status=TaskStatus(data.get("status", "pending")),
            progress=int(data.get("progress", 0)),
            message=data.get("message", ""),
            result=json.loads(data["result"]) if data.get("result") else None,
            error=data.get("error"),
            created_at=data.get("created_at"),
            started_at=data.get("started_at"),
            completed_at=data.get("completed_at")
        )

    async def update_progress(
        self,
        task_id: str,
        progress: int,
        message: str = "",
        extra: Dict = None
    ):
        """
        更新任务进度

        Args:
            task_id: 任务ID
            progress: 进度 (0-100)
            message: 进度消息
            extra: 额外数据
        """
        update_data = {
            "progress": str(progress),
            "message": message,
            "updated_at": datetime.now().isoformat()
        }

        await self.redis.hset(f"{self.TASK_PREFIX}{task_id}", mapping=update_data)

        # 发布进度事件
        event_data = {
            "progress": progress,
            "message": message,
            **(extra or {})
        }
        await self.publish_event(task_id, "progress", event_data)

    async def start_task(self, task_id: str):
        """标记任务开始执行"""
        now = datetime.now().isoformat()
        await self.redis.hset(
            f"{self.TASK_PREFIX}{task_id}",
            mapping={
                "status": TaskStatus.RUNNING.value,
                "started_at": now,
                "message": "任务执行中"
            }
        )
        await self.publish_event(task_id, "task_started", {"started_at": now})

    async def complete_task(self, task_id: str, result: Any = None):
        """标记任务完成"""
        now = datetime.now().isoformat()
        await self.redis.hset(
            f"{self.TASK_PREFIX}{task_id}",
            mapping={
                "status": TaskStatus.COMPLETED.value,
                "progress": "100",
                "completed_at": now,
                "message": "任务已完成",
                "result": json.dumps(result, ensure_ascii=False) if result else ""
            }
        )
        await self.publish_event(task_id, "task_completed", {
            "completed_at": now,
            "result": result
        })
        logger.info(f"Task completed: {task_id}")

    async def fail_task(self, task_id: str, error: str):
        """标记任务失败"""
        now = datetime.now().isoformat()
        await self.redis.hset(
            f"{self.TASK_PREFIX}{task_id}",
            mapping={
                "status": TaskStatus.FAILED.value,
                "completed_at": now,
                "message": f"任务失败: {error}",
                "error": error
            }
        )
        await self.publish_event(task_id, "task_failed", {
            "completed_at": now,
            "error": error
        })
        logger.error(f"Task failed: {task_id} - {error}")

    async def cancel_task(self, task_id: str):
        """取消任务"""
        now = datetime.now().isoformat()
        await self.redis.hset(
            f"{self.TASK_PREFIX}{task_id}",
            mapping={
                "status": TaskStatus.CANCELLED.value,
                "completed_at": now,
                "message": "任务已取消"
            }
        )
        await self.publish_event(task_id, "task_cancelled", {"cancelled_at": now})
        logger.info(f"Task cancelled: {task_id}")

    async def publish_event(self, task_id: str, event_type: str, data: Dict):
        """发布任务事件"""
        channel = f"task:{task_id}"
        message = json.dumps({
            "event": event_type,
            "task_id": task_id,
            "timestamp": datetime.now().isoformat(),
            "data": data
        }, ensure_ascii=False)
        await self.redis.publish(channel, message)

    async def start_workers(self, num_workers: int = 3):
        """启动工作进程"""
        self._running = True
        for i in range(num_workers):
            worker = asyncio.create_task(self._worker_loop(i))
            self._workers.append(worker)
        logger.info(f"Started {num_workers} workers")

    async def _worker_loop(self, worker_id: int):
        """工作进程主循环"""
        logger.info(f"Worker {worker_id} started")

        while self._running:
            try:
                # 按优先级从队列获取任务
                task_data = None
                for priority in TaskPriority:
                    queue_name = f"{self.QUEUE_PREFIX}{priority.value}"
                    result = await self.redis.brpop(queue_name, timeout=1)
                    if result:
                        task_data = json.loads(result[1])
                        break

                if not task_data:
                    continue

                task_id = task_data["task_id"]
                task_type = task_data["task_type"]
                payload = task_data["payload"]

                # 获取处理器
                handler = self._handlers.get(task_type)
                if not handler:
                    await self.fail_task(task_id, f"No handler for task type: {task_type}")
                    continue

                # 执行任务
                await self.start_task(task_id)
                try:
                    result = await handler(task_id, payload, self)
                    await self.complete_task(task_id, result)
                except Exception as e:
                    logger.exception(f"Task {task_id} failed")
                    await self.fail_task(task_id, str(e))

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.exception(f"Worker {worker_id} error: {e}")
                await asyncio.sleep(1)

        logger.info(f"Worker {worker_id} stopped")


# 全局任务管理器实例
task_manager = TaskManager()
