"""
任务调度器
支持定时任务、任务队列、失败重试和并发控制
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Callable, Optional
from enum import Enum
from dataclasses import dataclass, field
import traceback

from backend.utils.logging_config import get_logger

logger = get_logger("scheduler")


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"      # 待执行
    RUNNING = "running"      # 运行中
    SUCCESS = "success"      # 成功
    FAILED = "failed"        # 失败
    RETRY = "retry"          # 重试中


@dataclass
class ScheduledTask:
    """调度任务"""
    task_id: str
    name: str
    func: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    
    # 调度配置
    interval_minutes: int = 60  # 执行间隔(分钟)
    retry_count: int = 3        # 最大重试次数
    retry_delay: int = 5        # 重试延迟(秒)
    
    # 状态
    status: TaskStatus = TaskStatus.PENDING
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    attempts: int = 0
    error_message: Optional[str] = None


class TaskScheduler:
    """任务调度器"""
    
    def __init__(self, max_concurrent_tasks: int = 5):
        """
        初始化调度器
        
        Args:
            max_concurrent_tasks: 最大并发任务数
        """
        self.tasks: Dict[str, ScheduledTask] = {}
        self.max_concurrent_tasks = max_concurrent_tasks
        self.running_tasks: Dict[str, asyncio.Task] = {}
        self.is_running = False
        self._scheduler_task: Optional[asyncio.Task] = None
        
        logger.info(f"✅ 任务调度器初始化完成 (最大并发: {max_concurrent_tasks})")
    
    def add_task(
        self,
        task_id: str,
        name: str,
        func: Callable,
        interval_minutes: int = 60,
        retry_count: int = 3,
        retry_delay: int = 5,
        args: tuple = (),
        kwargs: dict = None
    ) -> ScheduledTask:
        """
        添加调度任务
        
        Args:
            task_id: 任务ID
            name: 任务名称
            func: 任务函数
            interval_minutes: 执行间隔(分钟)
            retry_count: 最大重试次数
            retry_delay: 重试延迟(秒)
            args: 函数参数
            kwargs: 函数关键字参数
        """
        if kwargs is None:
            kwargs = {}
        
        task = ScheduledTask(
            task_id=task_id,
            name=name,
            func=func,
            args=args,
            kwargs=kwargs,
            interval_minutes=interval_minutes,
            retry_count=retry_count,
            retry_delay=retry_delay
        )
        
        # 设置首次执行时间
        task.next_run = datetime.now()
        
        self.tasks[task_id] = task
        logger.info(f"➕ 添加任务: {name} ({task_id}) - 间隔:{interval_minutes}分钟")
        
        return task
    
    def remove_task(self, task_id: str):
        """移除任务"""
        if task_id in self.tasks:
            task = self.tasks[task_id]
            logger.info(f"➖ 移除任务: {task.name} ({task_id})")
            del self.tasks[task_id]
            
            # 如果任务正在运行,取消它
            if task_id in self.running_tasks:
                self.running_tasks[task_id].cancel()
                del self.running_tasks[task_id]
    
    async def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("⚠️ 调度器已在运行中")
            return
        
        self.is_running = True
        logger.info("🚀 启动任务调度器...")
        
        # 启动调度循环
        self._scheduler_task = asyncio.create_task(self._schedule_loop())
    
    async def stop(self):
        """停止调度器"""
        if not self.is_running:
            return
        
        logger.info("🛑 停止任务调度器...")
        self.is_running = False
        
        # 取消所有运行中的任务
        for task_id, task in list(self.running_tasks.items()):
            logger.info(f"取消任务: {task_id}")
            task.cancel()
        
        # 取消调度循环
        if self._scheduler_task:
            self._scheduler_task.cancel()
        
        self.running_tasks.clear()
    
    async def _schedule_loop(self):
        """调度循环"""
        logger.info("📅 调度循环开始")
        
        while self.is_running:
            try:
                current_time = datetime.now()
                
                # 遍历所有任务
                for task_id, task in list(self.tasks.items()):
                    # 检查是否需要执行
                    if task.next_run and current_time >= task.next_run:
                        # 检查并发限制
                        if len(self.running_tasks) >= self.max_concurrent_tasks:
                            logger.debug(f"⏸️ 达到最大并发数，任务{task.name}等待中...")
                            continue
                        
                        # 执行任务
                        await self._execute_task(task)
                
                # 每10秒检查一次
                await asyncio.sleep(10)
                
            except asyncio.CancelledError:
                logger.info("调度循环被取消")
                break
            except Exception as e:
                logger.error(f"❌ 调度循环异常: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(10)
    
    async def _execute_task(self, task: ScheduledTask):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.last_run = datetime.now()
        
        logger.info(f"▶️ 执行任务: {task.name} ({task.task_id})")
        
        # 创建任务
        async_task = asyncio.create_task(
            self._run_task_with_retry(task)
        )
        self.running_tasks[task.task_id] = async_task
        
        # 设置完成回调
        async_task.add_done_callback(
            lambda t: self._task_complete_callback(task.task_id, t)
        )
    
    async def _run_task_with_retry(self, task: ScheduledTask):
        """运行任务（带重试）"""
        for attempt in range(task.retry_count + 1):
            task.attempts = attempt + 1
            
            try:
                if attempt > 0:
                    logger.info(f"🔄 重试任务: {task.name} (第{attempt}次)")
                    task.status = TaskStatus.RETRY
                    await asyncio.sleep(task.retry_delay)
                
                # 执行任务函数
                if asyncio.iscoroutinefunction(task.func):
                    await task.func(*task.args, **task.kwargs)
                else:
                    # 同步函数在线程池中执行
                    loop = asyncio.get_event_loop()
                    await loop.run_in_executor(
                        None, 
                        task.func, 
                        *task.args
                    )
                
                # 成功
                task.status = TaskStatus.SUCCESS
                task.error_message = None
                logger.info(f"✅ 任务成功: {task.name}")
                break
                
            except asyncio.CancelledError:
                logger.info(f"⏹️ 任务被取消: {task.name}")
                task.status = TaskStatus.FAILED
                raise
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                task.error_message = error_msg
                
                if attempt < task.retry_count:
                    logger.warning(f"⚠️ 任务失败，将重试: {task.name} - {error_msg}")
                else:
                    logger.error(f"❌ 任务失败(已达最大重试): {task.name} - {error_msg}")
                    task.status = TaskStatus.FAILED
                    logger.error(traceback.format_exc())
        
        # 设置下次执行时间
        task.next_run = datetime.now() + timedelta(minutes=task.interval_minutes)
    
    def _task_complete_callback(self, task_id: str, async_task: asyncio.Task):
        """任务完成回调"""
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        if task_id in self.tasks:
            task = self.tasks[task_id]
            logger.debug(f"任务完成: {task.name} - 状态:{task.status.value}")
    
    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            'task_id': task.task_id,
            'name': task.name,
            'status': task.status.value,
            'last_run': task.last_run.isoformat() if task.last_run else None,
            'next_run': task.next_run.isoformat() if task.next_run else None,
            'attempts': task.attempts,
            'error_message': task.error_message,
            'interval_minutes': task.interval_minutes
        }
    
    def get_all_tasks_status(self) -> List[Dict]:
        """获取所有任务状态"""
        return [
            self.get_task_status(task_id)
            for task_id in self.tasks.keys()
        ]


# 全局调度器实例
_global_scheduler: Optional[TaskScheduler] = None


def get_scheduler() -> TaskScheduler:
    """获取全局调度器实例"""
    global _global_scheduler
    if _global_scheduler is None:
        _global_scheduler = TaskScheduler(max_concurrent_tasks=5)
    return _global_scheduler


# 便捷函数
def schedule_task(
    task_id: str,
    name: str,
    func: Callable,
    interval_minutes: int = 60,
    **kwargs
) -> ScheduledTask:
    """调度任务"""
    scheduler = get_scheduler()
    return scheduler.add_task(
        task_id=task_id,
        name=name,
        func=func,
        interval_minutes=interval_minutes,
        **kwargs
    )
