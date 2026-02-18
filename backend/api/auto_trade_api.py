"""
自动交易API
提供交易计划的CRUD和监控控制接口
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
from datetime import datetime
import asyncio
import json
import logging

from backend.services.auto_trade_service import get_auto_trade_service, AutoTradeService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/auto-trade", tags=["自动交易"])


# ==================== 请求模型 ====================

class CreatePlanRequest(BaseModel):
    """创建交易计划请求"""
    strategy_id: str
    strategy_name: str
    strategy_config: Dict[str, Any]
    stock_code: str
    stock_name: Optional[str] = ""
    initial_capital: float = 100000
    max_position_ratio: float = 0.3
    entry_mode: str = "rule_only"  # rule_only | rule_llm | llm_only
    exit_mode: str = "rule_only"
    check_interval: int = 30
    stop_loss_pct: float = 0.05
    take_profit_pct: float = 0.15
    auto_start: bool = False


class UpdatePlanRequest(BaseModel):
    """更新交易计划请求"""
    initial_capital: Optional[float] = None
    max_position_ratio: Optional[float] = None
    entry_mode: Optional[str] = None
    exit_mode: Optional[str] = None
    check_interval: Optional[int] = None
    stop_loss_pct: Optional[float] = None
    take_profit_pct: Optional[float] = None


# ==================== WebSocket连接管理 ====================

class ConnectionManager:
    """WebSocket连接管理器"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"[WebSocket] 新连接，当前连接数: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        logger.info(f"[WebSocket] 断开连接，当前连接数: {len(self.active_connections)}")

    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"[WebSocket] 发送消息失败: {e}")
                disconnected.append(connection)

        # 清理断开的连接
        for conn in disconnected:
            self.disconnect(conn)


manager = ConnectionManager()


# ==================== API端点 ====================

@router.post("/plans")
async def create_plan(request: CreatePlanRequest):
    """创建交易计划"""
    try:
        service = get_auto_trade_service()

        plan_data = {
            "strategy_id": request.strategy_id,
            "strategy_name": request.strategy_name,
            "strategy_config": request.strategy_config,
            "stock_code": request.stock_code,
            "stock_name": request.stock_name,
            "initial_capital": request.initial_capital,
            "max_position_ratio": request.max_position_ratio,
            "entry_mode": request.entry_mode,
            "exit_mode": request.exit_mode,
            "check_interval": request.check_interval,
            "stop_loss_pct": request.stop_loss_pct,
            "take_profit_pct": request.take_profit_pct,
        }

        plan = service.create_plan(plan_data)

        # 如果需要自动启动
        if request.auto_start:
            service.start_plan(plan.plan_id)

        return {
            "success": True,
            "message": "交易计划创建成功",
            "data": service.get_plan(plan.plan_id)
        }

    except Exception as e:
        logger.error(f"创建交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans")
async def get_all_plans():
    """获取所有交易计划"""
    try:
        service = get_auto_trade_service()
        plans = service.get_all_plans()

        return {
            "success": True,
            "data": plans,
            "total": len(plans)
        }

    except Exception as e:
        logger.error(f"获取交易计划列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plans/{plan_id}")
async def get_plan(plan_id: str):
    """获取交易计划详情"""
    try:
        service = get_auto_trade_service()
        plan = service.get_plan(plan_id)

        if not plan:
            raise HTTPException(status_code=404, detail="计划不存在")

        return {
            "success": True,
            "data": plan
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取交易计划详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/plans/{plan_id}")
async def update_plan(plan_id: str, request: UpdatePlanRequest):
    """更新交易计划"""
    try:
        service = get_auto_trade_service()

        if plan_id not in service.plans:
            raise HTTPException(status_code=404, detail="计划不存在")

        plan = service.plans[plan_id]

        # 更新字段
        if request.initial_capital is not None:
            plan.initial_capital = request.initial_capital
        if request.max_position_ratio is not None:
            plan.max_position_ratio = request.max_position_ratio
        if request.entry_mode is not None:
            plan.entry_mode = request.entry_mode
        if request.exit_mode is not None:
            plan.exit_mode = request.exit_mode
        if request.check_interval is not None:
            plan.check_interval = request.check_interval
        if request.stop_loss_pct is not None:
            plan.stop_loss_pct = request.stop_loss_pct
        if request.take_profit_pct is not None:
            plan.take_profit_pct = request.take_profit_pct

        return {
            "success": True,
            "message": "交易计划更新成功",
            "data": service.get_plan(plan_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: str):
    """删除交易计划"""
    try:
        service = get_auto_trade_service()

        if not service.delete_plan(plan_id):
            raise HTTPException(status_code=404, detail="计划不存在")

        return {
            "success": True,
            "message": "交易计划删除成功"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/start")
async def start_plan(plan_id: str):
    """启动交易计划"""
    try:
        service = get_auto_trade_service()

        if not service.start_plan(plan_id):
            raise HTTPException(status_code=404, detail="计划不存在")

        # 设置状态更新回调
        async def on_status_update(plan_data):
            await manager.broadcast({
                "type": "status_update",
                "data": plan_data
            })

        # 设置交易回调
        async def on_trade(trade_data):
            await manager.broadcast({
                "type": "trade_executed",
                "data": trade_data
            })

        return {
            "success": True,
            "message": "交易计划已启动",
            "data": service.get_plan(plan_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"启动交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/pause")
async def pause_plan(plan_id: str):
    """暂停交易计划"""
    try:
        service = get_auto_trade_service()

        if not service.pause_plan(plan_id):
            raise HTTPException(status_code=404, detail="计划不存在")

        return {
            "success": True,
            "message": "交易计划已暂停",
            "data": service.get_plan(plan_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"暂停交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/plans/{plan_id}/stop")
async def stop_plan(plan_id: str):
    """停止交易计划"""
    try:
        service = get_auto_trade_service()

        if not service.stop_plan(plan_id):
            raise HTTPException(status_code=404, detail="计划不存在")

        return {
            "success": True,
            "message": "交易计划已停止",
            "data": service.get_plan(plan_id)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"停止交易计划失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/monitor/status")
async def get_monitor_status():
    """获取监控服务状态"""
    try:
        service = get_auto_trade_service()

        running_plans = [p for p in service.plans.values() if p.is_running]

        return {
            "success": True,
            "data": {
                "is_running": service._is_running,
                "total_plans": len(service.plans),
                "running_plans": len(running_plans),
                "plans": service.get_all_plans()
            }
        }

    except Exception as e:
        logger.error(f"获取监控状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/start")
async def start_monitor():
    """启动监控服务"""
    try:
        service = get_auto_trade_service()
        service.start_monitor()

        return {
            "success": True,
            "message": "监控服务已启动"
        }

    except Exception as e:
        logger.error(f"启动监控服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor/stop")
async def stop_monitor():
    """停止监控服务"""
    try:
        service = get_auto_trade_service()
        service.stop_monitor()

        return {
            "success": True,
            "message": "监控服务已停止"
        }

    except Exception as e:
        logger.error(f"停止监控服务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WebSocket端点 ====================

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket实时推送"""
    await manager.connect(websocket)

    service = get_auto_trade_service()

    # 设置回调函数
    def sync_status_callback(plan_data):
        asyncio.create_task(manager.broadcast({
            "type": "status_update",
            "timestamp": datetime.now().isoformat(),
            "data": plan_data
        }))

    def sync_trade_callback(trade_data):
        asyncio.create_task(manager.broadcast({
            "type": "trade_executed",
            "timestamp": datetime.now().isoformat(),
            "data": trade_data
        }))

    service.on_status_update_callback = sync_status_callback
    service.on_trade_callback = sync_trade_callback

    try:
        # 发送初始状态
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.now().isoformat(),
            "data": {
                "is_running": service._is_running,
                "plans": service.get_all_plans()
            }
        })

        # 保持连接
        while True:
            try:
                # 接收客户端消息
                data = await websocket.receive_text()
                message = json.loads(data)

                # 处理客户端请求
                if message.get("type") == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif message.get("type") == "get_status":
                    await websocket.send_json({
                        "type": "status",
                        "timestamp": datetime.now().isoformat(),
                        "data": {
                            "is_running": service._is_running,
                            "plans": service.get_all_plans()
                        }
                    })

            except WebSocketDisconnect:
                break
            except Exception as e:
                logger.error(f"[WebSocket] 处理消息失败: {e}")

    except WebSocketDisconnect:
        pass
    finally:
        manager.disconnect(websocket)


# ==================== 辅助端点 ====================

@router.get("/trading-time")
async def get_trading_time():
    """获取交易时间信息"""
    from backend.services.auto_trade_service import TradingTimeChecker

    is_trading = TradingTimeChecker.is_trading_time()
    next_trading = TradingTimeChecker.get_next_trading_time()

    return {
        "success": True,
        "data": {
            "is_trading_time": is_trading,
            "next_trading_time": next_trading.isoformat(),
            "current_time": datetime.now().isoformat(),
            "trading_hours": {
                "morning": "09:30 - 11:30",
                "afternoon": "13:00 - 15:00"
            }
        }
    }


@router.get("/strategies/preset")
async def get_preset_strategies():
    """获取预设策略列表（用于创建计划时选择）"""
    try:
        # 从策略服务获取预设策略
        from backend.services.preset_strategies import get_preset_strategies

        strategies = get_preset_strategies()

        return {
            "success": True,
            "data": strategies
        }

    except ImportError:
        # 如果没有预设策略服务，返回示例策略
        return {
            "success": True,
            "data": [
                {
                    "id": "vegas_adx",
                    "name": "Vegas+ADX趋势策略",
                    "description": "结合Vegas通道和ADX指标的趋势跟踪策略",
                    "category": "technical",
                    "indicators": [
                        {"name": "EMA", "params": {"period": 144}},
                        {"name": "EMA", "params": {"period": 169}},
                        {"name": "ADX", "params": {"period": 14}}
                    ],
                    "entry_conditions": [
                        {"indicator": "price", "operator": "cross_above", "value": "EMA144", "description": "价格上穿EMA144"},
                        {"indicator": "ADX", "operator": ">", "value": 25, "description": "ADX大于25"}
                    ],
                    "exit_conditions": [
                        {"indicator": "price", "operator": "cross_below", "value": "EMA169", "description": "价格下穿EMA169"}
                    ],
                    "risk_params": {
                        "stop_loss": 0.05,
                        "take_profit": 0.15,
                        "max_position": 0.3
                    }
                },
                {
                    "id": "macd_cross",
                    "name": "MACD金叉策略",
                    "description": "基于MACD金叉死叉的交易策略",
                    "category": "technical",
                    "indicators": [
                        {"name": "MACD", "params": {"fast": 12, "slow": 26, "signal": 9}}
                    ],
                    "entry_conditions": [
                        {"indicator": "MACD", "operator": "cross_above", "value": "MACD_Signal", "description": "MACD金叉"}
                    ],
                    "exit_conditions": [
                        {"indicator": "MACD", "operator": "cross_below", "value": "MACD_Signal", "description": "MACD死叉"}
                    ],
                    "risk_params": {
                        "stop_loss": 0.05,
                        "take_profit": 0.10,
                        "max_position": 0.3
                    }
                },
                {
                    "id": "rsi_oversold",
                    "name": "RSI超卖反弹策略",
                    "description": "在RSI超卖区域买入，超买区域卖出",
                    "category": "technical",
                    "indicators": [
                        {"name": "RSI", "params": {"period": 14}}
                    ],
                    "entry_conditions": [
                        {"indicator": "RSI", "operator": "<", "value": 30, "description": "RSI低于30"}
                    ],
                    "exit_conditions": [
                        {"indicator": "RSI", "operator": ">", "value": 70, "description": "RSI高于70"}
                    ],
                    "risk_params": {
                        "stop_loss": 0.05,
                        "take_profit": 0.10,
                        "max_position": 0.3
                    }
                }
            ]
        }
    except Exception as e:
        logger.error(f"获取预设策略失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
