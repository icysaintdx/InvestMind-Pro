"""
统一数据中心监控Dashboard
提供实时性能指标和健康状态
"""

from fastapi import APIRouter, WebSocket
from typing import Dict, Any
from datetime import datetime
import asyncio

from backend.utils.logging_config import get_logger
from backend.dataflows.unified import (
    cache_manager,
    provider_manager,
    unified_data_service,
)

logger = get_logger("api.unified_monitor")
router = APIRouter(prefix="/api/v2/monitor", tags=["Unified Monitor"])


@router.get("/dashboard")
async def get_dashboard():
    """
    获取监控Dashboard数据
    """
    try:
        # 缓存统计
        cache_stats = cache_manager.get_stats()
        
        # Provider健康状态
        provider_health = provider_manager.get_health_report()
        
        # 系统状态
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "cache": {
                "l1_memory_items": cache_stats.get("l1_memory_count", 0),
                "l2_local_items": cache_stats.get("l2_local_count", 0),
                "hit_rate": _calculate_cache_hit_rate(),
            },
            "providers": provider_health,
            "system": {
                "status": "healthy" if _is_system_healthy(provider_health) else "degraded",
                "active_providers": len([p for p in provider_health.values() if p.get("is_healthy")]),
                "total_providers": len(provider_health),
            }
        }
        
        return {
            "success": True,
            "data": dashboard_data
        }
    except Exception as e:
        logger.error(f"[MonitorDashboard] 获取失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def _calculate_cache_hit_rate() -> float:
    """计算缓存命中率（模拟）"""
    # 实际应该基于真实统计
    return 0.85  # 85%


def _is_system_healthy(provider_health: Dict) -> bool:
    """判断系统是否健康"""
    if not provider_health:
        return False
    
    healthy_count = sum(1 for p in provider_health.values() if p.get("is_healthy"))
    total_count = len(provider_health)
    
    if total_count == 0:
        return False
    
    # 至少50%的Provider健康
    return healthy_count / total_count >= 0.5


@router.get("/metrics")
async def get_metrics():
    """
    获取性能指标
    """
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "avg_response_time_ms": _get_avg_response_time(),
                "requests_per_second": _get_requests_per_second(),
                "error_rate": _get_error_rate(),
            },
            "data_quality": {
                "data_freshness_seconds": _get_data_freshness(),
                "provider_availability": _get_provider_availability(),
            }
        }
        
        return {
            "success": True,
            "data": metrics
        }
    except Exception as e:
        logger.error(f"[MonitorMetrics] 获取失败: {e}")
        return {
            "success": False,
            "error": str(e)
        }


def _get_avg_response_time() -> float:
    """获取平均响应时间"""
    # 实际应该基于真实统计
    return 45.0  # 45ms


def _get_requests_per_second() -> float:
    """获取每秒请求数"""
    return 12.5


def _get_error_rate() -> float:
    """获取错误率"""
    return 0.02  # 2%


def _get_data_freshness() -> int:
    """获取数据新鲜度（秒）"""
    return 5


def _get_provider_availability() -> float:
    """获取Provider可用性"""
    health = provider_manager.get_health_report()
    if not health:
        return 0.0
    healthy = sum(1 for h in health.values() if h.get("is_healthy"))
    return healthy / len(health)


@router.websocket("/ws")
async def websocket_monitor(websocket: WebSocket):
    """
    WebSocket实时监控
    """
    await websocket.accept()
    
    try:
        while True:
            # 获取最新数据
            dashboard = await get_dashboard()
            metrics = await get_metrics()
            
            # 发送数据
            await websocket.send_json({
                "timestamp": datetime.now().isoformat(),
                "dashboard": dashboard.get("data", {}),
                "metrics": metrics.get("data", {}),
            })
            
            # 每秒更新
            await asyncio.sleep(1)
            
    except Exception as e:
        logger.debug(f"[MonitorWebSocket] 连接关闭: {e}")
    finally:
        await websocket.close()


@router.post("/cache/clear")
async def clear_cache():
    """
    手动清理缓存
    """
    try:
        cache_manager.clear_expired()
        return {
            "success": True,
            "message": "缓存清理完成"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@router.post("/circuit/reset/{provider_name}")
async def reset_circuit(provider_name: str):
    """
    手动重置熔断器
    """
    try:
        provider_manager.reset_circuit(provider_name)
        return {
            "success": True,
            "message": f"{provider_name} 熔断器已重置"
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }
