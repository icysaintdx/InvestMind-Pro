"""
实时盯盘监控 API
提供监控启停、配置管理、股票管理等端点
"""

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional
from datetime import datetime

from backend.utils.logging_config import get_logger
from backend.services.realtime_monitor_service import get_monitor_service, MonitorMode

logger = get_logger("api.realtime_monitor")
router = APIRouter(prefix="/api/realtime-monitor", tags=["Realtime Monitor"])


# ==================== 数据模型 ====================

class MonitorConfigRequest(BaseModel):
    """监控配置请求"""
    monitor_interval: Optional[int] = Field(None, ge=60, le=3600, description="监控间隔秒数")
    enable_ai_decision: Optional[bool] = Field(None, description="是否启用AI决策")
    enable_auto_trade: Optional[bool] = Field(None, description="是否自动执行交易")
    trading_hours_only: Optional[bool] = Field(None, description="仅在交易时段运行")
    mode: Optional[str] = Field(None, description="监控模式: realtime/scheduled")


class StockConfigRequest(BaseModel):
    """股票配置请求"""
    stop_loss_rate: Optional[float] = Field(None, ge=0, le=1, description="止损比例")
    take_profit_rate: Optional[float] = Field(None, ge=0, le=1, description="止盈比例")
    strategy_id: Optional[str] = Field(None, description="策略ID")


class AddStockRequest(BaseModel):
    """添加股票请求"""
    stock_code: str = Field(..., description="股票代码")
    stop_loss_rate: Optional[float] = Field(None, ge=0, le=1, description="止损比例")
    take_profit_rate: Optional[float] = Field(None, ge=0, le=1, description="止盈比例")
    strategy_id: Optional[str] = Field(None, description="策略ID")


class BatchAddStocksRequest(BaseModel):
    """批量添加股票请求"""
    stocks: List[AddStockRequest] = Field(..., description="股票列表")


# ==================== 监控控制端点 ====================

@router.post("/start")
async def start_monitor():
    """
    启动实时监控
    
    Returns:
        启动结果
    """
    try:
        service = get_monitor_service()
        result = await service.start_monitor()
        
        if result.get("success"):
            logger.info("实时监控已启动")
        else:
            logger.warning(f"启动监控失败: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"启动监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stop")
async def stop_monitor():
    """
    停止实时监控
    
    Returns:
        停止结果
    """
    try:
        service = get_monitor_service()
        result = await service.stop_monitor()
        
        if result.get("success"):
            logger.info("实时监控已停止")
        
        return result
        
    except Exception as e:
        logger.error(f"停止监控失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status")
async def get_monitor_status():
    """
    获取监控状态
    
    Returns:
        监控状态信息
    """
    try:
        service = get_monitor_service()
        status = service.get_status()
        
        return {
            "success": True,
            **status
        }
        
    except Exception as e:
        logger.error(f"获取状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/trigger")
async def trigger_check():
    """
    手动触发一次监控检查
    
    Returns:
        触发结果
    """
    try:
        service = get_monitor_service()
        
        # 直接执行一次检查
        await service._execute_monitor_check()
        
        return {
            "success": True,
            "message": "已触发监控检查",
            "stats": service.stats
        }
        
    except Exception as e:
        logger.error(f"触发检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 配置管理端点 ====================

@router.get("/config")
async def get_config():
    """
    获取监控配置
    
    Returns:
        配置信息
    """
    try:
        service = get_monitor_service()
        config = service.get_config()
        
        return {
            "success": True,
            "config": config
        }
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/config")
async def update_config(request: MonitorConfigRequest):
    """
    更新监控配置
    
    Args:
        request: 配置请求
        
    Returns:
        更新结果
    """
    try:
        service = get_monitor_service()
        result = service.update_config(
            monitor_interval=request.monitor_interval,
            enable_ai_decision=request.enable_ai_decision,
            enable_auto_trade=request.enable_auto_trade,
            trading_hours_only=request.trading_hours_only,
            mode=request.mode
        )
        
        logger.info(f"监控配置已更新: {request}")
        
        return result
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 股票管理端点 ====================

@router.get("/stocks")
async def list_stocks():
    """
    获取监控股票列表
    
    Returns:
        股票列表
    """
    try:
        service = get_monitor_service()
        stocks = service.monitored_stocks
        
        # 获取每只股票的当前行情
        stocks_with_price = []
        for code, config in stocks.items():
            stock_info = {
                "stock_code": code,
                **config
            }
            
            # 尝试获取当前价格
            try:
                from backend.services.market_data_service import get_realtime_quote
                quote = get_realtime_quote(code)
                stock_info["current_price"] = quote.get("current_price", 0)
                stock_info["change_rate"] = quote.get("change_rate", 0)
            except:
                stock_info["current_price"] = None
                stock_info["change_rate"] = None
            
            stocks_with_price.append(stock_info)
        
        return {
            "success": True,
            "stocks": stocks_with_price,
            "total": len(stocks)
        }
        
    except Exception as e:
        logger.error(f"获取股票列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stocks")
async def add_stock(request: AddStockRequest):
    """
    添加监控股票
    
    Args:
        request: 添加请求
        
    Returns:
        添加结果
    """
    try:
        service = get_monitor_service()
        result = service.add_stock(
            stock_code=request.stock_code,
            stop_loss_rate=request.stop_loss_rate,
            take_profit_rate=request.take_profit_rate,
            strategy_id=request.strategy_id
        )
        
        logger.info(f"添加监控股票: {request.stock_code}")
        
        return result
        
    except Exception as e:
        logger.error(f"添加股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stocks/batch")
async def batch_add_stocks(request: BatchAddStocksRequest):
    """
    批量添加监控股票
    
    Args:
        request: 批量添加请求
        
    Returns:
        添加结果
    """
    try:
        service = get_monitor_service()
        results = []
        
        for stock in request.stocks:
            result = service.add_stock(
                stock_code=stock.stock_code,
                stop_loss_rate=stock.stop_loss_rate,
                take_profit_rate=stock.take_profit_rate,
                strategy_id=stock.strategy_id
            )
            results.append({
                "stock_code": stock.stock_code,
                **result
            })
        
        success_count = sum(1 for r in results if r.get("success"))
        
        logger.info(f"批量添加监控股票: {success_count}/{len(request.stocks)} 成功")
        
        return {
            "success": True,
            "results": results,
            "success_count": success_count,
            "total": len(request.stocks)
        }
        
    except Exception as e:
        logger.error(f"批量添加股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/stocks/{stock_code}")
async def remove_stock(stock_code: str):
    """
    移除监控股票
    
    Args:
        stock_code: 股票代码
        
    Returns:
        移除结果
    """
    try:
        service = get_monitor_service()
        result = service.remove_stock(stock_code)
        
        if result.get("success"):
            logger.info(f"移除监控股票: {stock_code}")
        
        return result
        
    except Exception as e:
        logger.error(f"移除股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/stocks/{stock_code}")
async def update_stock_config(stock_code: str, request: StockConfigRequest):
    """
    更新股票配置
    
    Args:
        stock_code: 股票代码
        request: 配置请求
        
    Returns:
        更新结果
    """
    try:
        service = get_monitor_service()
        result = service.update_stock_config(
            stock_code=stock_code,
            stop_loss_rate=request.stop_loss_rate,
            take_profit_rate=request.take_profit_rate,
            strategy_id=request.strategy_id
        )
        
        if result.get("success"):
            logger.info(f"更新股票配置: {stock_code}")
        
        return result
        
    except Exception as e:
        logger.error(f"更新股票配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 从持仓同步 ====================

@router.post("/stocks/sync-from-positions")
async def sync_from_positions(
    stop_loss_rate: Optional[float] = 0.05,
    take_profit_rate: Optional[float] = 0.10
):
    """
    从当前持仓同步股票到监控列表
    
    Args:
        stop_loss_rate: 默认止损比例
        take_profit_rate: 默认止盈比例
        
    Returns:
        同步结果
    """
    try:
        from backend.api.trading_api import simulator
        
        service = get_monitor_service()
        added = []
        
        for stock_code in simulator.positions.keys():
            if stock_code not in service.monitored_stocks:
                service.add_stock(
                    stock_code=stock_code,
                    stop_loss_rate=stop_loss_rate,
                    take_profit_rate=take_profit_rate
                )
                added.append(stock_code)
        
        logger.info(f"从持仓同步股票: 新增 {len(added)} 只")
        
        return {
            "success": True,
            "message": f"已同步 {len(added)} 只股票",
            "added": added,
            "total_monitored": len(service.monitored_stocks)
        }
        
    except Exception as e:
        logger.error(f"同步持仓失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== WebSocket 实时推送 ====================

# 存储活跃的 WebSocket 连接
active_connections: List[WebSocket] = []


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket 端点，用于实时推送监控事件
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    logger.info(f"WebSocket 连接建立，当前连接数: {len(active_connections)}")
    
    # 注册事件回调
    service = get_monitor_service()
    
    async def event_callback(event: Dict):
        try:
            await websocket.send_json(event)
        except Exception as e:
            logger.error(f"WebSocket 发送失败: {e}")
    
    service.register_event_callback(event_callback)
    
    try:
        # 发送初始状态
        await websocket.send_json({
            "type": "connected",
            "data": service.get_status(),
            "timestamp": datetime.now().isoformat()
        })
        
        # 保持连接，接收客户端消息
        while True:
            data = await websocket.receive_text()
            
            # 处理客户端命令
            try:
                import json
                command = json.loads(data)
                cmd_type = command.get("type")
                
                if cmd_type == "ping":
                    await websocket.send_json({
                        "type": "pong",
                        "timestamp": datetime.now().isoformat()
                    })
                elif cmd_type == "get_status":
                    await websocket.send_json({
                        "type": "status",
                        "data": service.get_status(),
                        "timestamp": datetime.now().isoformat()
                    })
                elif cmd_type == "start":
                    result = await service.start_monitor()
                    await websocket.send_json({
                        "type": "start_result",
                        "data": result,
                        "timestamp": datetime.now().isoformat()
                    })
                elif cmd_type == "stop":
                    result = await service.stop_monitor()
                    await websocket.send_json({
                        "type": "stop_result",
                        "data": result,
                        "timestamp": datetime.now().isoformat()
                    })
                    
            except json.JSONDecodeError:
                pass
                
    except WebSocketDisconnect:
        logger.info("WebSocket 连接断开")
    except Exception as e:
        logger.error(f"WebSocket 错误: {e}")
    finally:
        service.unregister_event_callback(event_callback)
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"WebSocket 连接关闭，当前连接数: {len(active_connections)}")


async def broadcast_event(event: Dict):
    """
    广播事件到所有 WebSocket 连接
    """
    disconnected = []
    
    for connection in active_connections:
        try:
            await connection.send_json(event)
        except Exception as e:
            logger.error(f"广播失败: {e}")
            disconnected.append(connection)
    
    # 移除断开的连接
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


# ==================== 测试端点 ====================

@router.get("/test")
async def test_monitor_api():
    """测试监控 API 是否正常工作"""
    service = get_monitor_service()
    
    return {
        "status": "ok",
        "message": "Realtime Monitor API is working",
        "monitor_status": service.status.value,
        "features": [
            "实时循环监控",
            "交易时段检查",
            "AI 决策分析",
            "自动执行交易",
            "止盈止损触发",
            "WebSocket 实时推送"
        ],
        "timestamp": datetime.now().isoformat()
    }