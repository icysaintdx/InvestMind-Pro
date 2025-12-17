"""
调度器 API
管理定时任务的启动、停止、状态查询等
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any

from backend.utils.logging_config import get_logger
from backend.services.scheduler_service import get_scheduler

logger = get_logger("api.scheduler")

router = APIRouter(prefix="/api/scheduler", tags=["Scheduler"])


@router.get("/status")
async def get_scheduler_status():
    """
    获取调度器状态

    Returns:
        调度器状态信息
    """
    try:
        scheduler = get_scheduler()
        return {
            "success": True,
            "status": scheduler.get_status()
        }
    except Exception as e:
        logger.error(f"获取调度器状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/start")
async def start_scheduler():
    """
    启动调度器

    Returns:
        启动结果
    """
    try:
        scheduler = get_scheduler()
        scheduler.start()
        return {
            "success": True,
            "message": "调度器已启动",
            "status": scheduler.get_status()
        }
    except Exception as e:
        logger.error(f"启动调度器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_scheduler():
    """
    停止调度器

    Returns:
        停止结果
    """
    try:
        scheduler = get_scheduler()
        scheduler.stop()
        return {
            "success": True,
            "message": "调度器已停止",
            "status": scheduler.get_status()
        }
    except Exception as e:
        logger.error(f"停止调度器失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger/{task_type}")
async def trigger_task(task_type: str):
    """
    手动触发任务

    Args:
        task_type: 任务类型 (update_positions/trading_decisions/daily_summary/check_tracking)

    Returns:
        触发结果
    """
    try:
        scheduler = get_scheduler()
        scheduler.trigger_task(task_type)
        return {
            "success": True,
            "message": f"任务 {task_type} 已触发"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"触发任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history")
async def get_task_history(limit: int = 20):
    """
    获取任务执行历史

    Args:
        limit: 返回数量限制

    Returns:
        任务历史记录
    """
    try:
        scheduler = get_scheduler()
        history = scheduler.task_history[-limit:]
        return {
            "success": True,
            "history": history,
            "total": len(scheduler.task_history)
        }
    except Exception as e:
        logger.error(f"获取任务历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_config(config: Dict[str, Any]):
    """
    更新调度器配置

    Args:
        config: 新配置

    Returns:
        更新结果
    """
    try:
        scheduler = get_scheduler()

        # 更新配置
        for key, value in config.items():
            if key in scheduler.config:
                scheduler.config[key] = value

        scheduler.save_config()

        # 如果调度器正在运行，需要重启以应用新配置
        if scheduler.is_running:
            scheduler.stop()
            scheduler.start()

        return {
            "success": True,
            "message": "配置已更新",
            "config": scheduler.config
        }
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
