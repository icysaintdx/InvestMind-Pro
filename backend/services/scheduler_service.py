"""
定时任务调度服务
实现每日自动获取行情、执行策略、更新持仓等功能
"""

import asyncio
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Callable
import json
from pathlib import Path
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from backend.utils.logging_config import get_logger

logger = get_logger("services.scheduler")


class TradingScheduler:
    """交易调度器 - 管理每日定时任务"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.is_running = False
        self.task_history: List[Dict] = []
        self.config_file = Path("backend/data/scheduler_config.json")
        self.load_config()

    def load_config(self):
        """加载调度配置"""
        default_config = {
            "enabled": True,
            "market_open_time": "09:30",
            "market_close_time": "15:00",
            "update_interval_minutes": 30,
            "decision_times": ["09:35", "10:30", "13:30", "14:30"],
            "daily_summary_time": "15:30"
        }

        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except:
                self.config = default_config
        else:
            self.config = default_config
            self.save_config()

    def save_config(self):
        """保存调度配置"""
        self.config_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行")
            return

        if not self.config.get("enabled", True):
            logger.info("调度器已禁用")
            return

        # 添加定时任务

        # 1. 每日开盘后更新持仓行情
        self.scheduler.add_job(
            self._update_positions_price,
            CronTrigger(hour=9, minute=35),
            id="update_positions_morning",
            name="早盘更新持仓行情"
        )

        # 2. 盘中定时更新（每30分钟）
        self.scheduler.add_job(
            self._update_positions_price,
            CronTrigger(hour="9-14", minute="*/30"),
            id="update_positions_intraday",
            name="盘中更新持仓行情"
        )

        # 3. 定时执行交易决策
        for decision_time in self.config.get("decision_times", []):
            hour, minute = map(int, decision_time.split(":"))
            self.scheduler.add_job(
                self._execute_trading_decisions,
                CronTrigger(hour=hour, minute=minute),
                id=f"trading_decision_{decision_time}",
                name=f"交易决策 {decision_time}"
            )

        # 4. 每日收盘总结
        self.scheduler.add_job(
            self._daily_summary,
            CronTrigger(hour=15, minute=30),
            id="daily_summary",
            name="每日收盘总结"
        )

        # 5. 每日跟踪任务检查
        self.scheduler.add_job(
            self._check_tracking_tasks,
            CronTrigger(hour=16, minute=0),
            id="check_tracking",
            name="检查跟踪任务"
        )

        self.scheduler.start()
        self.is_running = True
        logger.info("交易调度器已启动")

    def stop(self):
        """停止调度器"""
        if not self.is_running:
            return

        self.scheduler.shutdown()
        self.is_running = False
        logger.info("交易调度器已停止")

    async def _update_positions_price(self):
        """更新所有持仓的当前价格"""
        logger.info("开始更新持仓行情...")

        try:
            from backend.api.trading_api import simulator
            from backend.services.market_data_service import get_realtime_quote

            updated_count = 0
            for stock_code, position in simulator.positions.items():
                try:
                    quote = get_realtime_quote(stock_code)
                    if quote.get("current_price", 0) > 0:
                        position["current_price"] = quote["current_price"]
                        position["last_update"] = datetime.now().isoformat()
                        updated_count += 1
                except Exception as e:
                    logger.warning(f"更新 {stock_code} 行情失败: {e}")

            # 更新组合价值
            await simulator._update_portfolio_value()
            simulator.save_data()

            self._record_task("update_positions", {
                "updated_count": updated_count,
                "total_positions": len(simulator.positions)
            })

            logger.info(f"持仓行情更新完成: {updated_count}/{len(simulator.positions)}")

        except Exception as e:
            logger.error(f"更新持仓行情失败: {e}")
            self._record_task("update_positions", {"error": str(e)})

    async def _execute_trading_decisions(self):
        """执行所有活跃任务的交易决策"""
        logger.info("开始执行交易决策...")

        try:
            from backend.api.auto_trading_api import active_tasks, make_decision, load_tasks

            load_tasks()

            executed_count = 0
            for task_id, task in active_tasks.items():
                if task.get("status") == "running":
                    try:
                        # 调用决策API
                        result = await make_decision(task_id)
                        executed_count += 1
                        logger.info(f"任务 {task_id} 决策完成: {result.get('decision', {}).get('action', 'unknown')}")
                    except Exception as e:
                        logger.error(f"任务 {task_id} 决策失败: {e}")

            self._record_task("trading_decisions", {
                "executed_count": executed_count,
                "total_tasks": len([t for t in active_tasks.values() if t.get("status") == "running"])
            })

            logger.info(f"交易决策执行完成: {executed_count}个任务")

        except Exception as e:
            logger.error(f"执行交易决策失败: {e}")
            self._record_task("trading_decisions", {"error": str(e)})

    async def _daily_summary(self):
        """生成每日交易总结"""
        logger.info("生成每日交易总结...")

        try:
            from backend.api.trading_api import simulator

            summary = {
                "date": datetime.now().strftime("%Y-%m-%d"),
                "portfolio": {
                    "total_value": simulator.portfolio.get("total_value", 0),
                    "cash_balance": simulator.portfolio.get("cash_balance", 0),
                    "positions_value": simulator.portfolio.get("positions_value", 0),
                    "total_profit_loss": simulator.portfolio.get("total_profit_loss", 0),
                    "total_profit_loss_rate": simulator.portfolio.get("total_profit_loss_rate", 0)
                },
                "positions_count": len(simulator.positions),
                "today_trades": len([
                    t for t in simulator.trade_history
                    if t.get("timestamp", "").startswith(datetime.now().strftime("%Y-%m-%d"))
                ])
            }

            # 保存每日总结
            summary_file = Path(f"backend/data/daily_summary_{summary['date']}.json")
            summary_file.parent.mkdir(parents=True, exist_ok=True)
            with open(summary_file, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)

            self._record_task("daily_summary", summary)
            logger.info(f"每日总结已生成: {summary_file}")

        except Exception as e:
            logger.error(f"生成每日总结失败: {e}")
            self._record_task("daily_summary", {"error": str(e)})

    async def _check_tracking_tasks(self):
        """检查跟踪任务"""
        logger.info("检查跟踪任务...")

        try:
            from backend.api.tracking_api import active_tracking_tasks, check_task, load_tracking_tasks

            load_tracking_tasks()

            checked_count = 0
            for task_id, task in active_tracking_tasks.items():
                if task.get("status") == "active":
                    try:
                        result = await check_task(task_id)
                        checked_count += 1
                        logger.info(f"跟踪任务 {task_id} 检查完成")
                    except Exception as e:
                        logger.error(f"跟踪任务 {task_id} 检查失败: {e}")

            self._record_task("check_tracking", {
                "checked_count": checked_count,
                "total_tasks": len([t for t in active_tracking_tasks.values() if t.get("status") == "active"])
            })

            logger.info(f"跟踪任务检查完成: {checked_count}个任务")

        except Exception as e:
            logger.error(f"检查跟踪任务失败: {e}")
            self._record_task("check_tracking", {"error": str(e)})

    def _record_task(self, task_type: str, result: Dict):
        """记录任务执行历史"""
        record = {
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
            "result": result
        }
        self.task_history.append(record)

        # 只保留最近100条记录
        if len(self.task_history) > 100:
            self.task_history = self.task_history[-100:]

    def get_status(self) -> Dict:
        """获取调度器状态"""
        jobs = []
        if self.is_running:
            for job in self.scheduler.get_jobs():
                jobs.append({
                    "id": job.id,
                    "name": job.name,
                    "next_run": job.next_run_time.isoformat() if job.next_run_time else None
                })

        return {
            "is_running": self.is_running,
            "config": self.config,
            "jobs": jobs,
            "recent_history": self.task_history[-10:]
        }

    def trigger_task(self, task_type: str):
        """手动触发任务"""
        task_map = {
            "update_positions": self._update_positions_price,
            "trading_decisions": self._execute_trading_decisions,
            "daily_summary": self._daily_summary,
            "check_tracking": self._check_tracking_tasks
        }

        if task_type not in task_map:
            raise ValueError(f"未知任务类型: {task_type}")

        asyncio.create_task(task_map[task_type]())
        logger.info(f"手动触发任务: {task_type}")


# 全局调度器实例
_scheduler = None


def get_scheduler() -> TradingScheduler:
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = TradingScheduler()
    return _scheduler


def start_scheduler():
    """启动调度器"""
    scheduler = get_scheduler()
    scheduler.start()


def stop_scheduler():
    """停止调度器"""
    scheduler = get_scheduler()
    scheduler.stop()
