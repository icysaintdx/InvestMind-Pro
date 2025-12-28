"""
新闻数据同步服务
后台异步同步新闻数据，支持多数据源
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor
import threading

from backend.database.database import get_db, SessionLocal
from backend.database.models import MonitoredStock, StockNewsRecord
from backend.services.news_data_service import NewsDataService, get_news_data_service
from backend.dataflows.news.multi_source_news_aggregator import MultiSourceNewsAggregator

logger = logging.getLogger(__name__)


@dataclass
class SyncTask:
    """同步任务"""
    ts_code: str
    stock_name: str
    status: str = "pending"  # pending/running/completed/failed
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    result: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class SyncStats:
    """同步统计"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    total_news_saved: int = 0
    total_news_filtered: int = 0
    total_news_duplicate: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: float = 0


class NewsSyncService:
    """新闻同步服务"""

    def __init__(self, max_workers: int = 3):
        """
        初始化同步服务

        Args:
            max_workers: 最大并发工作线程数
        """
        self.logger = logging.getLogger(__name__)
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.news_service = get_news_data_service()

        # 同步状态
        self._is_running = False
        self._current_sync_id = None
        self._tasks: Dict[str, SyncTask] = {}
        self._stats = SyncStats()
        self._lock = threading.Lock()

        # 数据源聚合器
        self._aggregator = None

    def _get_aggregator(self) -> MultiSourceNewsAggregator:
        """获取数据源聚合器"""
        if self._aggregator is None:
            self._aggregator = MultiSourceNewsAggregator()
        return self._aggregator

    def _sync_stock_news(self, ts_code: str, stock_name: str) -> Dict[str, Any]:
        """
        同步单个股票的新闻

        Args:
            ts_code: 股票代码
            stock_name: 股票名称

        Returns:
            同步结果
        """
        result = {
            "ts_code": ts_code,
            "stock_name": stock_name,
            "saved": 0,
            "filtered": 0,
            "duplicate": 0,
            "skipped": 0,
            "error": None
        }

        try:
            # 获取新闻数据
            aggregator = self._get_aggregator()
            news_list = aggregator.get_stock_news(ts_code, max_news=50)

            if not news_list:
                self.logger.info(f"📰 {ts_code} 没有获取到新闻")
                return result

            # 转换为标准格式
            formatted_news = []
            for news in news_list:
                formatted_news.append({
                    'title': news.get('title', news.get('新闻标题', '')),
                    'content': news.get('content', news.get('新闻内容', '')),
                    'summary': news.get('summary', news.get('摘要', '')),
                    'source': news.get('source', news.get('来源', '')),
                    'url': news.get('url', news.get('链接', '')),
                    'pub_time': news.get('pub_time', news.get('发布时间'))
                })

            # 保存到数据库
            db = SessionLocal()
            try:
                save_result = self.news_service.save_news(
                    db=db,
                    ts_code=ts_code,
                    news_list=formatted_news,
                    apply_filter=True,
                    min_relevance_score=30
                )

                result["saved"] = save_result.get("saved", 0)
                result["filtered"] = save_result.get("filtered", 0)
                result["duplicate"] = save_result.get("duplicate", 0)
                result["skipped"] = save_result.get("skipped", 0)

            finally:
                db.close()

            self.logger.info(f"✅ {ts_code} 新闻同步完成: 保存={result['saved']}, 过滤={result['filtered']}")

        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"❌ {ts_code} 新闻同步失败: {e}")

        return result

    def start_sync(
        self,
        stock_codes: Optional[List[str]] = None,
        sync_all_monitored: bool = False
    ) -> str:
        """
        启动同步任务

        Args:
            stock_codes: 要同步的股票代码列表
            sync_all_monitored: 是否同步所有监控股票

        Returns:
            同步任务ID
        """
        if self._is_running:
            self.logger.warning("⚠️ 同步任务正在运行中")
            return self._current_sync_id

        # 生成同步ID
        sync_id = f"sync_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self._current_sync_id = sync_id
        self._is_running = True

        # 重置统计
        self._stats = SyncStats()
        self._stats.start_time = datetime.now()
        self._tasks.clear()

        # 获取要同步的股票列表
        stocks_to_sync = []

        if sync_all_monitored:
            # 从数据库获取所有监控股票
            db = SessionLocal()
            try:
                monitored = db.query(MonitoredStock).filter(
                    MonitoredStock.is_active == 1
                ).all()
                stocks_to_sync = [(s.ts_code, s.name) for s in monitored]
            finally:
                db.close()
        elif stock_codes:
            # 使用指定的股票代码
            stocks_to_sync = [(code, code) for code in stock_codes]

        if not stocks_to_sync:
            self.logger.warning("⚠️ 没有要同步的股票")
            self._is_running = False
            return sync_id

        self._stats.total_tasks = len(stocks_to_sync)

        # 创建任务
        for ts_code, stock_name in stocks_to_sync:
            self._tasks[ts_code] = SyncTask(ts_code=ts_code, stock_name=stock_name)

        # 启动后台同步
        threading.Thread(target=self._run_sync, args=(stocks_to_sync,), daemon=True).start()

        self.logger.info(f"🚀 启动新闻同步任务: {sync_id}, 共 {len(stocks_to_sync)} 只股票")
        return sync_id

    def _run_sync(self, stocks_to_sync: List[tuple]):
        """运行同步任务"""
        try:
            futures = []

            for ts_code, stock_name in stocks_to_sync:
                # 更新任务状态
                with self._lock:
                    if ts_code in self._tasks:
                        self._tasks[ts_code].status = "running"
                        self._tasks[ts_code].start_time = datetime.now()

                # 提交任务
                future = self.executor.submit(self._sync_stock_news, ts_code, stock_name)
                futures.append((ts_code, future))

            # 等待所有任务完成
            for ts_code, future in futures:
                try:
                    result = future.result(timeout=120)  # 2分钟超时

                    with self._lock:
                        if ts_code in self._tasks:
                            self._tasks[ts_code].status = "completed"
                            self._tasks[ts_code].end_time = datetime.now()
                            self._tasks[ts_code].result = result

                            if result.get("error"):
                                self._tasks[ts_code].status = "failed"
                                self._tasks[ts_code].error = result["error"]
                                self._stats.failed_tasks += 1
                            else:
                                self._stats.completed_tasks += 1
                                self._stats.total_news_saved += result.get("saved", 0)
                                self._stats.total_news_filtered += result.get("filtered", 0)
                                self._stats.total_news_duplicate += result.get("duplicate", 0)

                except Exception as e:
                    with self._lock:
                        if ts_code in self._tasks:
                            self._tasks[ts_code].status = "failed"
                            self._tasks[ts_code].end_time = datetime.now()
                            self._tasks[ts_code].error = str(e)
                            self._stats.failed_tasks += 1

                    self.logger.error(f"❌ {ts_code} 同步任务异常: {e}")

        finally:
            # 完成同步
            self._stats.end_time = datetime.now()
            if self._stats.start_time:
                self._stats.duration_seconds = (self._stats.end_time - self._stats.start_time).total_seconds()

            self._is_running = False
            self.logger.info(f"✅ 新闻同步完成: 成功={self._stats.completed_tasks}, 失败={self._stats.failed_tasks}, "
                           f"保存={self._stats.total_news_saved}条, 耗时={self._stats.duration_seconds:.1f}秒")

    def get_sync_status(self) -> Dict[str, Any]:
        """获取同步状态"""
        with self._lock:
            tasks_status = {}
            for ts_code, task in self._tasks.items():
                tasks_status[ts_code] = {
                    "stock_name": task.stock_name,
                    "status": task.status,
                    "start_time": task.start_time.isoformat() if task.start_time else None,
                    "end_time": task.end_time.isoformat() if task.end_time else None,
                    "result": task.result,
                    "error": task.error
                }

            return {
                "sync_id": self._current_sync_id,
                "is_running": self._is_running,
                "stats": {
                    "total_tasks": self._stats.total_tasks,
                    "completed_tasks": self._stats.completed_tasks,
                    "failed_tasks": self._stats.failed_tasks,
                    "total_news_saved": self._stats.total_news_saved,
                    "total_news_filtered": self._stats.total_news_filtered,
                    "total_news_duplicate": self._stats.total_news_duplicate,
                    "start_time": self._stats.start_time.isoformat() if self._stats.start_time else None,
                    "end_time": self._stats.end_time.isoformat() if self._stats.end_time else None,
                    "duration_seconds": self._stats.duration_seconds
                },
                "tasks": tasks_status
            }

    def stop_sync(self):
        """停止同步"""
        if not self._is_running:
            return

        self.logger.info("⏹️ 正在停止同步任务...")
        self._is_running = False
        self.executor.shutdown(wait=False)
        self.executor = ThreadPoolExecutor(max_workers=self.max_workers)


# 全局服务实例
_news_sync_service = None


def get_news_sync_service() -> NewsSyncService:
    """获取新闻同步服务实例"""
    global _news_sync_service
    if _news_sync_service is None:
        _news_sync_service = NewsSyncService()
        logger.info("✅ 新闻同步服务初始化成功")
    return _news_sync_service


# ==================== 定时同步调度器 ====================

class NewsSyncScheduler:
    """新闻同步调度器"""

    def __init__(self, sync_interval_minutes: int = 30):
        """
        初始化调度器

        Args:
            sync_interval_minutes: 同步间隔（分钟）
        """
        self.sync_interval = sync_interval_minutes
        self.sync_service = get_news_sync_service()
        self._is_running = False
        self._scheduler_thread = None
        self.logger = logging.getLogger(__name__)

    def start(self):
        """启动调度器"""
        if self._is_running:
            return

        self._is_running = True
        self._scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self._scheduler_thread.start()
        self.logger.info(f"⏰ 新闻同步调度器已启动，间隔: {self.sync_interval}分钟")

    def stop(self):
        """停止调度器"""
        self._is_running = False
        self.logger.info("⏹️ 新闻同步调度器已停止")

    def _run_scheduler(self):
        """运行调度器"""
        while self._is_running:
            try:
                # 检查是否在交易时间（9:00-15:30）
                now = datetime.now()
                hour = now.hour
                minute = now.minute

                # 交易时间内更频繁同步
                if 9 <= hour < 16:
                    self.logger.info("📅 开始定时新闻同步...")
                    self.sync_service.start_sync(sync_all_monitored=True)

                    # 等待同步完成
                    while self.sync_service._is_running:
                        import time
                        time.sleep(5)

            except Exception as e:
                self.logger.error(f"❌ 定时同步异常: {e}")

            # 等待下一次同步
            import time
            time.sleep(self.sync_interval * 60)


# 全局调度器实例
_news_sync_scheduler = None


def get_news_sync_scheduler() -> NewsSyncScheduler:
    """获取新闻同步调度器实例"""
    global _news_sync_scheduler
    if _news_sync_scheduler is None:
        _news_sync_scheduler = NewsSyncScheduler()
    return _news_sync_scheduler
