"""
后台新闻获取服务
使用独立进程池处理新闻请求，完全不阻塞FastAPI主事件循环

特点:
1. 使用 ProcessPoolExecutor 在独立进程中运行AKShare请求
2. 请求结果缓存到内存/文件，供其他API使用
3. 支持任务队列，避免重复请求
4. 完全非阻塞，不影响其他API响应
"""
import asyncio
import json
import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import threading
import queue

logger = logging.getLogger(__name__)


class NewsTaskStatus(str, Enum):
    """新闻任务状态"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class NewsTask:
    """新闻获取任务"""
    task_id: str
    stock_code: str
    status: NewsTaskStatus
    created_at: str
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    news_count: int = 0
    error: Optional[str] = None
    progress: int = 0

    def to_dict(self) -> dict:
        return {
            "task_id": self.task_id,
            "stock_code": self.stock_code,
            "status": self.status.value,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "news_count": self.news_count,
            "error": self.error,
            "progress": self.progress
        }


# ========== 独立进程中执行的函数 ==========
# 这些函数会在ProcessPoolExecutor的子进程中运行，完全独立于主进程

def _fetch_news_in_process(stock_code: str, timeout: int = 30) -> Dict:
    """
    在独立进程中获取新闻
    这个函数会在子进程中运行，不会阻塞主进程
    """
    import warnings
    warnings.filterwarnings('ignore')

    result = {
        "success": False,
        "stock_code": stock_code,
        "news": [],
        "sources": {},
        "error": None,
        "elapsed": 0
    }

    start_time = time.time()

    try:
        import akshare as ak
        import concurrent.futures
        symbol = stock_code.split('.')[0]
        all_news = []

        # 1. 东方财富新闻 (带超时控制，避免长时间阻塞)
        try:
            logger.info(f"[子进程] 开始获取 {symbol} 东方财富新闻...")
            # 使用线程池执行，设置超时
            with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(ak.stock_news_em, symbol=symbol)
                try:
                    df = future.result(timeout=15)  # 15秒超时
                    if df is not None and not df.empty:
                        for _, row in df.head(20).iterrows():
                            title = str(row.get("新闻标题", ""))
                            if title:  # 只保存有标题的新闻
                                all_news.append({
                                    "title": title,
                                    "content": str(row.get("新闻内容", ""))[:500],
                                    "pub_time": str(row.get("发布时间", "")),
                                    "source": "东方财富",
                                    "url": str(row.get("新闻链接", ""))
                                })
                        result["sources"]["eastmoney"] = len(df)
                        logger.info(f"[子进程] 东方财富新闻获取成功: {len(df)}条")
                except concurrent.futures.TimeoutError:
                    logger.warning(f"[子进程] 东方财富新闻获取超时(>15s)")
                    result["sources"]["eastmoney"] = "timeout"
        except json.JSONDecodeError as e:
            logger.warning(f"[子进程] 东方财富新闻JSON解析错误: {e}")
            result["sources"]["eastmoney"] = "json_error"
        except Exception as e:
            error_msg = str(e)[:50]
            # 忽略常见的非致命错误
            if "Extra data" in error_msg or "JSONDecodeError" in error_msg:
                logger.warning(f"[子进程] 东方财富新闻数据格式异常，跳过")
                result["sources"]["eastmoney"] = "data_format_error"
            else:
                logger.warning(f"[子进程] 东方财富新闻获取失败: {e}")
                result["sources"]["eastmoney"] = f"error: {error_msg}"

        # 2. 财联社电报 (stock_telegraph_cls已改名为stock_info_global_cls)
        try:
            df = ak.stock_info_global_cls()
            if df is not None and not df.empty:
                for _, row in df.head(15).iterrows():
                    title = str(row.get("标题", ""))
                    if title:
                        all_news.append({
                            "title": title,
                            "content": str(row.get("内容", ""))[:500],
                            "pub_time": str(row.get("发布时间", "")),
                            "source": "财联社",
                            "url": ""
                        })
                result["sources"]["cls"] = len(df)
                logger.info(f"[子进程] 财联社电报获取成功: {len(df)}条")
        except Exception as e:
            logger.debug(f"[子进程] 财联社电报获取失败: {e}")
            result["sources"]["cls"] = f"error: {str(e)[:30]}"

        # 3. 东方财富全球资讯 (作为补充)
        try:
            df = ak.stock_info_global_em()
            if df is not None and not df.empty:
                for _, row in df.head(10).iterrows():
                    title = str(row.get("标题", ""))
                    if title:
                        all_news.append({
                            "title": title,
                            "content": str(row.get("摘要", ""))[:500],
                            "pub_time": str(row.get("发布时间", "")),
                            "source": "东方财富全球",
                            "url": str(row.get("链接", ""))
                        })
                result["sources"]["global_em"] = len(df)
        except Exception as e:
            logger.debug(f"[子进程] 东方财富全球资讯获取失败: {e}")
            result["sources"]["global_em"] = f"error: {str(e)[:30]}"

        result["news"] = all_news
        result["success"] = len(all_news) > 0  # 只要有新闻就算成功

    except Exception as e:
        result["error"] = str(e)
        logger.error(f"[子进程] 新闻获取异常: {e}")

    result["elapsed"] = round(time.time() - start_time, 2)
    return result


class BackgroundNewsService:
    """
    后台新闻获取服务

    使用独立进程池处理新闻请求，完全不阻塞FastAPI
    """

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        self._initialized = True

        # 进程池 - 使用独立进程，完全不阻塞主线程
        self._executor: Optional[ProcessPoolExecutor] = None
        self._max_workers = 2  # 最多2个并行新闻获取进程

        # 任务管理
        self._tasks: Dict[str, NewsTask] = {}  # task_id -> NewsTask
        self._stock_tasks: Dict[str, str] = {}  # stock_code -> task_id (防止重复请求)
        self._task_lock = threading.Lock()

        # 新闻缓存
        self._news_cache: Dict[str, Dict] = {}  # stock_code -> news_data
        self._cache_expiry: Dict[str, datetime] = {}  # stock_code -> expiry_time
        self._cache_duration = timedelta(minutes=30)  # 缓存30分钟

        # 文件缓存目录
        self._cache_dir = Path("data/news_cache")
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # 运行状态
        self._running = False
        self._background_task: Optional[asyncio.Task] = None

        logger.info("BackgroundNewsService initialized")

    async def start(self):
        """启动后台服务"""
        if self._running:
            return

        self._running = True
        self._executor = ProcessPoolExecutor(max_workers=self._max_workers)
        logger.info(f"BackgroundNewsService started with {self._max_workers} workers")

    async def stop(self):
        """停止后台服务"""
        self._running = False
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
        logger.info("BackgroundNewsService stopped")

    def submit_news_task(self, stock_code: str) -> str:
        """
        提交新闻获取任务（线程安全）

        Returns:
            task_id: 任务ID
        """
        with self._task_lock:
            # 检查是否已有该股票的任务在运行
            if stock_code in self._stock_tasks:
                existing_task_id = self._stock_tasks[stock_code]
                existing_task = self._tasks.get(existing_task_id)
                if existing_task and existing_task.status in [NewsTaskStatus.PENDING, NewsTaskStatus.RUNNING]:
                    logger.info(f"股票 {stock_code} 已有任务在运行: {existing_task_id}")
                    return existing_task_id

            # 检查缓存是否有效
            if self._is_cache_valid(stock_code):
                logger.info(f"股票 {stock_code} 缓存有效，跳过新请求")
                return f"cached_{stock_code}"

            # 创建新任务
            task_id = f"news_{stock_code}_{int(time.time() * 1000)}"
            task = NewsTask(
                task_id=task_id,
                stock_code=stock_code,
                status=NewsTaskStatus.PENDING,
                created_at=datetime.now().isoformat()
            )

            self._tasks[task_id] = task
            self._stock_tasks[stock_code] = task_id

            # 在后台执行（线程安全方式）
            try:
                loop = asyncio.get_running_loop()
                # 如果在异步上下文中，使用 create_task
                asyncio.create_task(self._execute_task(task_id))
            except RuntimeError:
                # 如果不在异步上下文中（如从线程池调用），使用线程执行
                logger.info(f"从非异步上下文提交任务，使用线程执行: {task_id}")
                thread = threading.Thread(
                    target=self._execute_task_sync,
                    args=(task_id,),
                    daemon=True
                )
                thread.start()

            logger.info(f"新闻任务已提交: {task_id}")
            return task_id

    def _execute_task_sync(self, task_id: str):
        """同步执行新闻获取任务（在线程中运行）"""
        task = self._tasks.get(task_id)
        if not task:
            return

        # 更新状态为运行中
        task.status = NewsTaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        task.progress = 10

        try:
            logger.info(f"开始在线程中获取新闻: {task.stock_code}")
            task.progress = 30

            # 直接调用同步函数获取新闻
            result = _fetch_news_in_process(task.stock_code, 60)

            task.progress = 90

            if result["success"]:
                task.status = NewsTaskStatus.COMPLETED
                task.news_count = len(result["news"])

                # 保存到缓存
                self._save_to_cache(task.stock_code, result)

                logger.info(f"新闻任务完成: {task_id}, 获取 {task.news_count} 条新闻, 耗时 {result['elapsed']}s")
            else:
                task.status = NewsTaskStatus.FAILED
                task.error = result.get("error", "Unknown error")
                logger.error(f"新闻任务失败: {task_id}, 错误: {task.error}")

        except Exception as e:
            task.status = NewsTaskStatus.FAILED
            task.error = str(e)
            logger.exception(f"新闻任务异常: {task_id}")

        finally:
            task.completed_at = datetime.now().isoformat()
            task.progress = 100

    async def _execute_task(self, task_id: str):
        """执行新闻获取任务"""
        task = self._tasks.get(task_id)
        if not task:
            return

        # 更新状态为运行中
        task.status = NewsTaskStatus.RUNNING
        task.started_at = datetime.now().isoformat()
        task.progress = 10

        try:
            if not self._executor:
                await self.start()

            # 在独立进程中执行新闻获取
            loop = asyncio.get_event_loop()

            logger.info(f"开始在独立进程中获取新闻: {task.stock_code}")
            task.progress = 30

            # 使用 run_in_executor 在进程池中执行
            # 这不会阻塞主事件循环
            result = await asyncio.wait_for(
                loop.run_in_executor(
                    self._executor,
                    _fetch_news_in_process,
                    task.stock_code,
                    60  # 60秒超时
                ),
                timeout=120  # 总超时120秒
            )

            task.progress = 90

            if result["success"]:
                task.status = NewsTaskStatus.COMPLETED
                task.news_count = len(result["news"])

                # 保存到缓存
                self._save_to_cache(task.stock_code, result)

                logger.info(f"新闻任务完成: {task_id}, 获取 {task.news_count} 条新闻, 耗时 {result['elapsed']}s")
            else:
                task.status = NewsTaskStatus.FAILED
                task.error = result.get("error", "Unknown error")
                logger.error(f"新闻任务失败: {task_id}, 错误: {task.error}")

        except asyncio.TimeoutError:
            task.status = NewsTaskStatus.TIMEOUT
            task.error = "任务超时 (>120s)"
            logger.warning(f"新闻任务超时: {task_id}")

        except Exception as e:
            task.status = NewsTaskStatus.FAILED
            task.error = str(e)
            logger.exception(f"新闻任务异常: {task_id}")

        finally:
            task.completed_at = datetime.now().isoformat()
            task.progress = 100

            # 清理股票任务映射
            with self._task_lock:
                if task.stock_code in self._stock_tasks:
                    if self._stock_tasks[task.stock_code] == task_id:
                        del self._stock_tasks[task.stock_code]

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        # 检查是否是缓存任务
        if task_id.startswith("cached_"):
            stock_code = task_id.replace("cached_", "")
            return {
                "task_id": task_id,
                "stock_code": stock_code,
                "status": "completed",
                "from_cache": True,
                "news_count": len(self._news_cache.get(stock_code, {}).get("news", []))
            }

        task = self._tasks.get(task_id)
        if task:
            return task.to_dict()
        return None

    def get_cached_news(self, stock_code: str) -> Optional[Dict]:
        """获取缓存的新闻"""
        # 先检查内存缓存
        if self._is_cache_valid(stock_code):
            return self._news_cache.get(stock_code)

        # 再检查文件缓存
        return self._load_from_file_cache(stock_code)

    def _is_cache_valid(self, stock_code: str) -> bool:
        """检查缓存是否有效"""
        if stock_code not in self._cache_expiry:
            return False
        return datetime.now() < self._cache_expiry[stock_code]

    def _save_to_cache(self, stock_code: str, data: Dict):
        """保存到缓存"""
        # 内存缓存
        self._news_cache[stock_code] = data
        self._cache_expiry[stock_code] = datetime.now() + self._cache_duration

        # 文件缓存
        try:
            cache_file = self._cache_dir / f"{stock_code.replace('.', '_')}.json"
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "stock_code": stock_code,
                    "data": data,
                    "cached_at": datetime.now().isoformat(),
                    "expires_at": (datetime.now() + self._cache_duration).isoformat()
                }, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"保存新闻缓存文件失败: {e}")

    def _load_from_file_cache(self, stock_code: str) -> Optional[Dict]:
        """从文件缓存加载"""
        try:
            cache_file = self._cache_dir / f"{stock_code.replace('.', '_')}.json"
            if not cache_file.exists():
                return None

            with open(cache_file, 'r', encoding='utf-8') as f:
                cached = json.load(f)

            # 检查是否过期
            expires_at = datetime.fromisoformat(cached["expires_at"])
            if datetime.now() > expires_at:
                return None

            # 加载到内存缓存
            self._news_cache[stock_code] = cached["data"]
            self._cache_expiry[stock_code] = expires_at

            return cached["data"]

        except Exception as e:
            logger.warning(f"加载新闻缓存文件失败: {e}")
            return None

    def get_all_tasks(self) -> List[Dict]:
        """获取所有任务状态"""
        return [task.to_dict() for task in self._tasks.values()]

    def get_running_tasks(self) -> List[Dict]:
        """获取正在运行的任务"""
        return [
            task.to_dict()
            for task in self._tasks.values()
            if task.status in [NewsTaskStatus.PENDING, NewsTaskStatus.RUNNING]
        ]

    def clear_old_tasks(self, max_age_hours: int = 24):
        """清理旧任务"""
        cutoff = datetime.now() - timedelta(hours=max_age_hours)

        with self._task_lock:
            old_tasks = [
                task_id for task_id, task in self._tasks.items()
                if task.completed_at and datetime.fromisoformat(task.completed_at) < cutoff
            ]

            for task_id in old_tasks:
                del self._tasks[task_id]

            if old_tasks:
                logger.info(f"清理了 {len(old_tasks)} 个旧任务")


# 全局实例
background_news_service = BackgroundNewsService()


# ========== 便捷函数 ==========

async def fetch_news_async(stock_code: str) -> str:
    """
    异步获取新闻（非阻塞）

    Returns:
        task_id: 任务ID，可用于查询状态
    """
    return background_news_service.submit_news_task(stock_code)


def get_news_task_status(task_id: str) -> Optional[Dict]:
    """获取新闻任务状态"""
    return background_news_service.get_task_status(task_id)


def get_cached_news(stock_code: str) -> Optional[Dict]:
    """获取缓存的新闻"""
    return background_news_service.get_cached_news(stock_code)
