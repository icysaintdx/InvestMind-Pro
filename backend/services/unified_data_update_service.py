"""
统一后台数据更新服务
实现数据库优先架构：后端独立获取数据 -> 保存到数据库 -> 前端从数据库读取

功能：
1. 定时更新所有监控股票的数据
2. 根据接口频率限制智能调度
3. 使用进程池避免阻塞主线程
4. 防止重复请求
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from dataclasses import dataclass, field

from backend.utils.logging_config import get_logger
from backend.config.interface_rate_limits import (
    get_min_interval,
    is_trading_hours_only,
    INTERFACE_RATE_LIMITS,
    UpdateFrequency
)

logger = get_logger("services.unified_data_update")


@dataclass
class UpdateTask:
    """更新任务"""
    ts_code: str
    task_type: str  # 'comprehensive', 'news', 'realtime'
    priority: int = 0  # 优先级，数字越小优先级越高
    scheduled_time: datetime = field(default_factory=datetime.utcnow)
    last_update: Optional[datetime] = None
    retry_count: int = 0
    max_retries: int = 3
    trigger_reason: str = 'unknown'  # 触发原因: 'scheduled', 'manual', 'new_stock'


class UnifiedDataUpdateService:
    """统一数据更新服务"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # 任务队列
        self._task_queue: List[UpdateTask] = []
        self._queue_lock = threading.Lock()

        # 正在执行的任务（防止重复）
        self._running_tasks: Set[str] = set()
        self._running_lock = threading.Lock()

        # 最后更新时间记录
        self._last_update_times: Dict[str, Dict[str, datetime]] = {}

        # 执行器
        self._executor = ThreadPoolExecutor(max_workers=4, thread_name_prefix="data_update_")

        # 调度器状态
        self._scheduler_running = False
        self._scheduler_thread: Optional[threading.Thread] = None

        # 配置
        self._default_update_interval = UpdateFrequency.MEDIUM.value  # 30分钟
        self._min_task_interval = 5  # 任务之间最小间隔（秒）

        logger.info("[统一更新服务] 初始化完成")

    def start_scheduler(self):
        """启动调度器"""
        if self._scheduler_running:
            logger.warning("[统一更新服务] 调度器已在运行")
            return

        self._scheduler_running = True
        self._scheduler_thread = threading.Thread(
            target=self._scheduler_loop,
            name="data_update_scheduler",
            daemon=True
        )
        self._scheduler_thread.start()
        logger.info("[统一更新服务] 调度器已启动")

    def stop_scheduler(self):
        """停止调度器"""
        self._scheduler_running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("[统一更新服务] 调度器已停止")

    def _scheduler_loop(self):
        """调度器主循环"""
        while self._scheduler_running:
            try:
                # 检查并执行到期任务
                self._process_due_tasks()

                # 自动添加监控股票的定时任务
                self._schedule_monitored_stocks()

                # 休眠一段时间
                time.sleep(10)

            except Exception as e:
                logger.error(f"[统一更新服务] 调度器错误: {e}")
                time.sleep(30)

    def _process_due_tasks(self):
        """处理到期任务"""
        now = datetime.utcnow()

        with self._queue_lock:
            # 找出所有到期任务
            due_tasks = [
                task for task in self._task_queue
                if task.scheduled_time <= now
            ]

            # 按优先级排序
            due_tasks.sort(key=lambda t: (t.priority, t.scheduled_time))

        for task in due_tasks:
            task_key = f"{task.ts_code}_{task.task_type}"

            # 检查是否已在执行
            with self._running_lock:
                if task_key in self._running_tasks:
                    continue
                self._running_tasks.add(task_key)

            # 从队列移除
            with self._queue_lock:
                if task in self._task_queue:
                    self._task_queue.remove(task)

            # 提交执行
            self._executor.submit(self._execute_task, task)

            # 任务间隔
            time.sleep(self._min_task_interval)

    def _execute_task(self, task: UpdateTask):
        """执行更新任务"""
        task_key = f"{task.ts_code}_{task.task_type}"
        start_time = time.time()

        # 触发原因映射
        reason_map = {
            'scheduled': '定时触发',
            'manual': '手动触发',
            'new_stock': '新增股票触发',
            'unknown': '未知触发'
        }
        reason_text = reason_map.get(task.trigger_reason, task.trigger_reason)

        try:
            logger.info(f"[统一更新服务] 开始执行任务: {task_key} ({reason_text})")

            if task.task_type == 'comprehensive':
                self._update_comprehensive_data(task.ts_code)
            elif task.task_type == 'news':
                self._update_news_data(task.ts_code)
            elif task.task_type == 'realtime':
                self._update_realtime_data(task.ts_code)

            # 记录更新时间
            if task.ts_code not in self._last_update_times:
                self._last_update_times[task.ts_code] = {}
            self._last_update_times[task.ts_code][task.task_type] = datetime.utcnow()

            elapsed = round(time.time() - start_time, 2)
            logger.info(f"[统一更新服务] 任务完成: {task_key}, 耗时: {elapsed}s")

        except Exception as e:
            logger.error(f"[统一更新服务] 任务失败: {task_key}, 错误: {e}")

            # 重试逻辑
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.scheduled_time = datetime.utcnow() + timedelta(minutes=5)
                with self._queue_lock:
                    self._task_queue.append(task)
                logger.info(f"[统一更新服务] 任务将重试: {task_key}, 重试次数: {task.retry_count}")

        finally:
            with self._running_lock:
                self._running_tasks.discard(task_key)

    def _update_comprehensive_data(self, ts_code: str):
        """更新综合数据"""
        from backend.database.database import get_db
        from backend.dataflows.comprehensive_stock_data import ComprehensiveStockDataService
        from backend.dataflows.data_persistence import DataPersistenceManager

        # 获取数据
        service = ComprehensiveStockDataService()
        comprehensive_data = service.get_all_stock_data(ts_code)

        # 保存到数据库
        db = next(get_db())
        try:
            DataPersistenceManager.save_comprehensive_data(
                db=db,
                ts_code=ts_code,
                comprehensive_data=comprehensive_data,
                source='background_update'
            )

            # 通过WebSocket通知前端
            self._notify_frontend_sync(ts_code, 'update_complete', {
                'source': 'background_update',
                'data_keys': list(comprehensive_data.keys()) if comprehensive_data else []
            })
        finally:
            db.close()

    def _update_news_data(self, ts_code: str):
        """更新新闻数据"""
        from backend.database.database import get_db
        from backend.dataflows.comprehensive_stock_data import get_category_data
        from backend.dataflows.data_persistence import DataPersistenceManager

        # 只获取新闻数据
        news_data = get_category_data(ts_code, 'news_sentiment')

        # 保存到数据库
        db = next(get_db())
        try:
            if news_data and 'data' in news_data:
                DataPersistenceManager.save_comprehensive_data(
                    db=db,
                    ts_code=ts_code,
                    comprehensive_data=news_data['data'],
                    source='background_news'
                )
        finally:
            db.close()

    def _update_realtime_data(self, ts_code: str):
        """更新实时行情数据"""
        from backend.database.database import get_db
        from backend.dataflows.comprehensive_stock_data import get_category_data
        from backend.dataflows.data_persistence import DataPersistenceManager

        # 只获取行情数据
        market_data = get_category_data(ts_code, 'market_data')

        # 保存到数据库
        db = next(get_db())
        try:
            if market_data and 'data' in market_data:
                DataPersistenceManager.save_comprehensive_data(
                    db=db,
                    ts_code=ts_code,
                    comprehensive_data=market_data['data'],
                    source='background_realtime'
                )
        finally:
            db.close()

    def _schedule_monitored_stocks(self):
        """为监控股票安排定时任务"""
        from backend.database.database import get_db
        from backend.database.services import MonitoredStockService

        db = next(get_db())
        try:
            stocks = MonitoredStockService.get_all_active(db)

            for stock in stocks:
                ts_code = stock.ts_code
                # 将 frequency 转换为秒数
                update_interval = self._frequency_to_seconds(stock.frequency) or self._default_update_interval

                # 检查是否需要安排新任务
                last_update = self._last_update_times.get(ts_code, {}).get('comprehensive')

                # 触发原因统一为定时触发（启动时也算定时检查）
                trigger_reason = 'scheduled'

                if last_update is None or \
                   (datetime.utcnow() - last_update).total_seconds() >= update_interval:

                    # 检查是否已有待执行任务
                    task_key = f"{ts_code}_comprehensive"
                    with self._queue_lock:
                        existing = any(
                            t.ts_code == ts_code and t.task_type == 'comprehensive'
                            for t in self._task_queue
                        )

                    with self._running_lock:
                        running = task_key in self._running_tasks

                    if not existing and not running:
                        self.schedule_update(ts_code, 'comprehensive', trigger_reason=trigger_reason)

        finally:
            db.close()

    def _frequency_to_seconds(self, frequency: str) -> int:
        """将频率字符串转换为秒数"""
        frequency_map = {
            '5m': 300,       # 5分钟
            '15m': 900,      # 15分钟
            '30m': 1800,     # 30分钟
            '1h': 3600,      # 1小时
            '2h': 7200,      # 2小时
            '4h': 14400,     # 4小时
            '1d': 86400,     # 1天
        }
        return frequency_map.get(frequency, self._default_update_interval)

    def schedule_update(
        self,
        ts_code: str,
        task_type: str = 'comprehensive',
        priority: int = 5,
        delay_seconds: int = 0,
        trigger_reason: str = 'unknown'
    ):
        """
        安排更新任务

        Args:
            ts_code: 股票代码
            task_type: 任务类型 ('comprehensive', 'news', 'realtime')
            priority: 优先级 (0-10, 数字越小优先级越高)
            delay_seconds: 延迟执行秒数
            trigger_reason: 触发原因 ('scheduled', 'manual', 'new_stock')
        """
        task = UpdateTask(
            ts_code=ts_code,
            task_type=task_type,
            priority=priority,
            scheduled_time=datetime.utcnow() + timedelta(seconds=delay_seconds),
            trigger_reason=trigger_reason
        )

        with self._queue_lock:
            # 检查是否已存在相同任务
            existing = any(
                t.ts_code == ts_code and t.task_type == task_type
                for t in self._task_queue
            )

            if not existing:
                self._task_queue.append(task)
                reason_map = {
                    'scheduled': '定时触发',
                    'manual': '手动触发',
                    'new_stock': '新增股票触发',
                    'unknown': '未知触发'
                }
                reason_text = reason_map.get(trigger_reason, trigger_reason)
                logger.info(f"[统一更新服务] 任务已安排: {ts_code}_{task_type}, 原因: {reason_text}, 延迟: {delay_seconds}s")
            else:
                logger.debug(f"[统一更新服务] 任务已存在: {ts_code}_{task_type}")

    def schedule_immediate_update(self, ts_code: str, task_type: str = 'comprehensive', trigger_reason: str = 'manual'):
        """立即安排更新任务（高优先级）"""
        self.schedule_update(ts_code, task_type, priority=0, delay_seconds=0, trigger_reason=trigger_reason)

    def is_task_running(self, ts_code: str, task_type: str = 'comprehensive') -> bool:
        """检查任务是否正在执行"""
        task_key = f"{ts_code}_{task_type}"
        with self._running_lock:
            return task_key in self._running_tasks

    def get_last_update_time(self, ts_code: str, task_type: str = 'comprehensive') -> Optional[datetime]:
        """获取最后更新时间"""
        return self._last_update_times.get(ts_code, {}).get(task_type)

    def get_queue_status(self) -> Dict:
        """获取队列状态"""
        with self._queue_lock:
            pending_count = len(self._task_queue)
            pending_tasks = [
                {
                    'ts_code': t.ts_code,
                    'task_type': t.task_type,
                    'scheduled_time': t.scheduled_time.isoformat(),
                    'priority': t.priority
                }
                for t in sorted(self._task_queue, key=lambda x: (x.priority, x.scheduled_time))[:10]
            ]

        with self._running_lock:
            running_count = len(self._running_tasks)
            running_tasks = list(self._running_tasks)

        return {
            'scheduler_running': self._scheduler_running,
            'pending_count': pending_count,
            'running_count': running_count,
            'pending_tasks': pending_tasks,
            'running_tasks': running_tasks
        }

    def cancel_task(self, ts_code: str, task_type: str = 'comprehensive') -> bool:
        """取消待执行任务"""
        with self._queue_lock:
            original_len = len(self._task_queue)
            self._task_queue = [
                t for t in self._task_queue
                if not (t.ts_code == ts_code and t.task_type == task_type)
            ]
            return len(self._task_queue) < original_len

    def _notify_frontend_sync(self, ts_code: str, event: str, data: dict = None):
        """同步方式通知前端（在线程中调用）"""
        try:
            import asyncio
            from backend.api.websocket_api import notify_stock_updated, notify_stock_update_error

            # 创建新的事件循环来执行异步通知
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                if event == 'update_complete':
                    loop.run_until_complete(notify_stock_updated(ts_code, data))
                elif event == 'update_error':
                    loop.run_until_complete(notify_stock_update_error(ts_code, data.get('error', 'Unknown error')))
                logger.debug(f"[统一更新服务] WebSocket通知已发送: {ts_code} - {event}")
            finally:
                loop.close()
        except Exception as e:
            logger.warning(f"[统一更新服务] WebSocket通知失败: {e}")


# 全局实例
_update_service: Optional[UnifiedDataUpdateService] = None


def get_update_service() -> UnifiedDataUpdateService:
    """获取更新服务实例"""
    global _update_service
    if _update_service is None:
        _update_service = UnifiedDataUpdateService()
    return _update_service


def start_background_update_service():
    """启动后台更新服务"""
    service = get_update_service()
    service.start_scheduler()
    return service


def stop_background_update_service():
    """停止后台更新服务"""
    global _update_service
    if _update_service:
        _update_service.stop_scheduler()
