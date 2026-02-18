"""
策略回测与实时信号 API
提供历史回测、实时信号分析、与虚拟交易对接等功能
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import logging

from backend.utils.logging_config import get_logger
from backend.api.strategies import PRESET_STRATEGIES
from backend.services.strategy_rule_engine import get_strategy_rule_engine, BacktestResult

logger = get_logger("api.strategy_backtest")
router = APIRouter(prefix="/api/strategy-backtest", tags=["Strategy Backtest"])


# ==================== 数据模型 ====================

class BacktestRequest(BaseModel):
    """回测请求"""
    stock_code: str = Field(..., description="股票代码")
    strategy_id: str = Field(..., description="策略ID")
    start_date: Optional[str] = Field(None, description="开始日期 YYYYMMDD")
    end_date: Optional[str] = Field(None, description="结束日期 YYYYMMDD")
    initial_capital: float = Field(100000, description="初始资金")


class RealTimeAnalysisRequest(BaseModel):
    """实时分析请求"""
    stock_code: str = Field(..., description="股票代码")
    strategy_id: str = Field(..., description="策略ID")
    kline_count: int = Field(120, description="K线数量")


class VirtualTradeRequest(BaseModel):
    """虚拟交易请求"""
    stock_code: str = Field(..., description="股票代码")
    strategy_id: str = Field(..., description="策略ID")
    action: str = Field(..., description="交易动作: BUY/SELL")
    price: float = Field(..., description="交易价格")
    quantity: int = Field(..., description="交易数量")
    signal_id: Optional[str] = Field(None, description="关联的信号ID")


class SignalMonitorConfig(BaseModel):
    """信号监控配置"""
    stock_code: str = Field(..., description="股票代码")
    strategy_id: str = Field(..., description="策略ID")
    auto_trade: bool = Field(False, description="是否自动交易")
    notify_on_signal: bool = Field(True, description="信号时是否通知")
    check_interval: int = Field(60, description="检查间隔（秒）")


# ==================== 存储 ====================

# 存储自定义策略（从strategy_center_api导入）
from backend.api.strategy_center_api import custom_strategies

# 信号监控任务
signal_monitors: Dict[str, Dict[str, Any]] = {}

# 虚拟交易记录
virtual_trades: List[Dict[str, Any]] = []


# ==================== 辅助函数 ====================

def get_strategy_by_id(strategy_id: str) -> Optional[Dict[str, Any]]:
    """根据ID获取策略"""
    for s in PRESET_STRATEGIES:
        if s["id"] == strategy_id:
            return s
    
    if strategy_id in custom_strategies:
        return custom_strategies[strategy_id]
    
    return None


async def get_kline_data(stock_code: str, start_date: str = None, end_date: str = None, count: int = 120) -> List[Dict]:
    """获取K线数据"""
    clean_symbol = stock_code.replace('.SH', '').replace('.SZ', '')
    
    try:
        from backend.dataflows.akshare.stock_data import get_stock_data
        stock_data = get_stock_data()
        
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        if not start_date:
            start_date = (datetime.now() - timedelta(days=count * 2)).strftime('%Y%m%d')
        
        hist_data = stock_data.get_stock_hist(
            symbol=clean_symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq"
        )
        
        if hist_data:
            return hist_data[-count:] if len(hist_data) > count else hist_data
        return []
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        return []


# ==================== API端点 ====================

@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """
    执行策略回测
    
    根据策略在历史K线数据上进行回测，找出所有买卖点，计算收益率等指标
    """
    # 获取策略
    strategy = get_strategy_by_id(request.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    logger.info(f"开始回测: 股票={request.stock_code}, 策略={strategy['name']}")
    
    try:
        # 获取K线数据
        kline_data = await get_kline_data(
            request.stock_code,
            request.start_date,
            request.end_date,
            count=500  # 回测需要更多数据
        )
        
        if not kline_data or len(kline_data) < 60:
            raise HTTPException(status_code=400, detail="K线数据不足，需要至少60根K线")
        
        # 执行回测
        engine = get_strategy_rule_engine()
        strategy_with_code = {**strategy, "stock_code": request.stock_code}
        result = engine.backtest(kline_data, strategy_with_code, request.initial_capital)
        
        # 转换结果为可序列化格式
        response_data = {
            "strategy_id": result.strategy_id,
            "strategy_name": result.strategy_name,
            "stock_code": request.stock_code,
            "start_date": result.start_date.strftime("%Y-%m-%d") if isinstance(result.start_date, datetime) else str(result.start_date),
            "end_date": result.end_date.strftime("%Y-%m-%d") if isinstance(result.end_date, datetime) else str(result.end_date),
            "initial_capital": request.initial_capital,
            "final_capital": request.initial_capital * (1 + result.total_return),
            "statistics": {
                "total_trades": result.total_trades,
                "winning_trades": result.winning_trades,
                "losing_trades": result.losing_trades,
                "win_rate": round(result.win_rate * 100, 2),
                "total_return": round(result.total_return * 100, 2),
                "max_drawdown": round(result.max_drawdown * 100, 2),
            },
            "buy_signals": result.buy_signals,
            "sell_signals": result.sell_signals,
            "trades": [
                {
                    "entry_date": t.entry_date.strftime("%Y-%m-%d") if isinstance(t.entry_date, datetime) else str(t.entry_date),
                    "entry_price": t.entry_price,
                    "exit_date": t.exit_date.strftime("%Y-%m-%d") if t.exit_date and isinstance(t.exit_date, datetime) else str(t.exit_date) if t.exit_date else None,
                    "exit_price": t.exit_price,
                    "profit_pct": round(t.profit_pct * 100, 2),
                    "status": t.status
                }
                for t in result.trades
            ],
            "kline_count": len(kline_data)
        }
        
        logger.info(f"回测完成: 总交易={result.total_trades}, 胜率={result.win_rate*100:.1f}%, 总收益={result.total_return*100:.1f}%")
        
        return {"success": True, "data": response_data}
        
    except Exception as e:
        logger.error(f"回测失败: {e}")
        raise HTTPException(status_code=500, detail=f"回测失败: {str(e)}")


@router.post("/analyze")
async def analyze_current_state(request: RealTimeAnalysisRequest):
    """
    分析当前状态
    
    根据策略分析当前K线数据，判断是否有交易机会
    返回各个条件的满足状态和交易建议
    """
    # 获取策略
    strategy = get_strategy_by_id(request.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    logger.info(f"分析当前状态: 股票={request.stock_code}, 策略={strategy['name']}")
    
    try:
        # 获取K线数据
        kline_data = await get_kline_data(request.stock_code, count=request.kline_count)
        
        if not kline_data or len(kline_data) < 60:
            raise HTTPException(status_code=400, detail="K线数据不足")
        
        # 分析当前状态
        engine = get_strategy_rule_engine()
        result = engine.analyze_current_state(kline_data, strategy)
        
        # 添加股票信息
        result["stock_code"] = request.stock_code
        result["strategy_id"] = request.strategy_id
        result["strategy_name"] = strategy.get("name", "")
        result["analyzed_at"] = datetime.now().isoformat()
        result["kline_count"] = len(kline_data)
        
        return {"success": True, "data": result}
        
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.post("/find-signals")
async def find_all_signals(request: BacktestRequest):
    """
    查找所有信号点
    
    在历史数据中找出所有满足策略条件的买卖点
    """
    # 获取策略
    strategy = get_strategy_by_id(request.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    try:
        # 获取K线数据
        kline_data = await get_kline_data(
            request.stock_code,
            request.start_date,
            request.end_date,
            count=500
        )
        
        if not kline_data or len(kline_data) < 60:
            raise HTTPException(status_code=400, detail="K线数据不足")
        
        # 准备数据并计算指标
        engine = get_strategy_rule_engine()
        df = engine.prepare_dataframe(kline_data)
        df = engine.calculate_all_indicators(df, strategy)
        
        # 找出所有信号
        signals = engine.find_all_signals(df, strategy)
        
        # 转换为可序列化格式
        signal_list = []
        for signal in signals:
            signal_list.append({
                "type": signal.signal_type.value,
                "date": signal.timestamp.strftime("%Y-%m-%d") if isinstance(signal.timestamp, datetime) else str(signal.timestamp),
                "price": signal.price,
                "confidence": signal.confidence,
                "conditions_met": signal.conditions_met,
                "stop_loss": signal.stop_loss,
                "take_profit": signal.take_profit,
                "reason": signal.reason,
                "indicators": signal.indicators
            })
        
        return {
            "success": True,
            "data": {
                "stock_code": request.stock_code,
                "strategy_id": request.strategy_id,
                "strategy_name": strategy.get("name", ""),
                "total_signals": len(signal_list),
                "buy_signals": [s for s in signal_list if s["type"] == "BUY"],
                "sell_signals": [s for s in signal_list if s["type"] == "SELL"],
                "signals": signal_list
            }
        }
        
    except Exception as e:
        logger.error(f"查找信号失败: {e}")
        raise HTTPException(status_code=500, detail=f"查找信号失败: {str(e)}")


@router.post("/monitor/start")
async def start_signal_monitor(config: SignalMonitorConfig, background_tasks: BackgroundTasks):
    """
    启动信号监控
    
    持续监控指定股票，当满足策略条件时生成信号
    可配置自动交易
    """
    monitor_id = f"{config.stock_code}_{config.strategy_id}"
    
    # 检查策略是否存在
    strategy = get_strategy_by_id(config.strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    # 保存监控配置
    signal_monitors[monitor_id] = {
        "id": monitor_id,
        "stock_code": config.stock_code,
        "strategy_id": config.strategy_id,
        "strategy_name": strategy.get("name", ""),
        "auto_trade": config.auto_trade,
        "notify_on_signal": config.notify_on_signal,
        "check_interval": config.check_interval,
        "status": "running",
        "started_at": datetime.now().isoformat(),
        "last_check": None,
        "last_signal": None
    }
    
    logger.info(f"启动信号监控: {monitor_id}")
    
    return {
        "success": True,
        "data": signal_monitors[monitor_id],
        "message": f"信号监控已启动: {config.stock_code} - {strategy.get('name', '')}"
    }


@router.post("/monitor/stop/{monitor_id}")
async def stop_signal_monitor(monitor_id: str):
    """停止信号监控"""
    if monitor_id not in signal_monitors:
        raise HTTPException(status_code=404, detail="监控任务不存在")
    
    signal_monitors[monitor_id]["status"] = "stopped"
    signal_monitors[monitor_id]["stopped_at"] = datetime.now().isoformat()
    
    logger.info(f"停止信号监控: {monitor_id}")
    
    return {
        "success": True,
        "message": "信号监控已停止"
    }


@router.get("/monitor/list")
async def list_signal_monitors():
    """获取所有信号监控任务"""
    return {
        "success": True,
        "data": list(signal_monitors.values())
    }


@router.post("/monitor/check/{monitor_id}")
async def check_signal_now(monitor_id: str):
    """
    立即检查信号
    
    手动触发一次信号检查
    """
    if monitor_id not in signal_monitors:
        raise HTTPException(status_code=404, detail="监控任务不存在")
    
    monitor = signal_monitors[monitor_id]
    
    try:
        # 获取K线数据
        kline_data = await get_kline_data(monitor["stock_code"], count=120)
        
        if not kline_data:
            return {"success": False, "message": "无法获取K线数据"}
        
        # 获取策略
        strategy = get_strategy_by_id(monitor["strategy_id"])
        if not strategy:
            return {"success": False, "message": "策略不存在"}
        
        # 分析当前状态
        engine = get_strategy_rule_engine()
        result = engine.analyze_current_state(kline_data, strategy)
        
        # 更新监控状态
        monitor["last_check"] = datetime.now().isoformat()
        
        if result.get("has_signal"):
            monitor["last_signal"] = {
                "type": result.get("signal_type"),
                "time": datetime.now().isoformat(),
                "price": result.get("current_price"),
                "suggestion": result.get("trade_suggestion")
            }
            
            # 如果配置了自动交易
            if monitor.get("auto_trade") and result.get("trade_suggestion"):
                suggestion = result["trade_suggestion"]
                # 这里可以调用虚拟交易接口
                logger.info(f"自动交易信号: {suggestion}")
        
        return {
            "success": True,
            "data": {
                "monitor_id": monitor_id,
                "has_signal": result.get("has_signal"),
                "signal_type": result.get("signal_type"),
                "analysis": result
            }
        }
        
    except Exception as e:
        logger.error(f"检查信号失败: {e}")
        return {"success": False, "message": str(e)}


@router.post("/virtual-trade")
async def execute_virtual_trade(request: VirtualTradeRequest):
    """
    执行虚拟交易
    
    记录虚拟交易，用于策略验证
    """
    trade = {
        "id": f"vt_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(virtual_trades)}",
        "stock_code": request.stock_code,
        "strategy_id": request.strategy_id,
        "action": request.action,
        "price": request.price,
        "quantity": request.quantity,
        "amount": request.price * request.quantity,
        "signal_id": request.signal_id,
        "executed_at": datetime.now().isoformat(),
        "status": "executed"
    }
    
    virtual_trades.append(trade)
    logger.info(f"虚拟交易执行: {trade}")
    
    return {
        "success": True,
        "data": trade,
        "message": f"虚拟{request.action}交易已执行"
    }


@router.get("/virtual-trades")
async def get_virtual_trades(
    stock_code: Optional[str] = Query(None),
    strategy_id: Optional[str] = Query(None)
):
    """获取虚拟交易记录"""
    trades = virtual_trades
    
    if stock_code:
        trades = [t for t in trades if t["stock_code"] == stock_code]
    if strategy_id:
        trades = [t for t in trades if t["strategy_id"] == strategy_id]
    
    return {
        "success": True,
        "data": trades,
        "total": len(trades)
    }


@router.get("/virtual-trades/summary")
async def get_virtual_trades_summary(strategy_id: Optional[str] = Query(None)):
    """获取虚拟交易汇总"""
    trades = virtual_trades
    
    if strategy_id:
        trades = [t for t in trades if t["strategy_id"] == strategy_id]
    
    # 计算汇总
    buy_trades = [t for t in trades if t["action"] == "BUY"]
    sell_trades = [t for t in trades if t["action"] == "SELL"]
    
    total_buy_amount = sum(t["amount"] for t in buy_trades)
    total_sell_amount = sum(t["amount"] for t in sell_trades)
    
    return {
        "success": True,
        "data": {
            "total_trades": len(trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "total_buy_amount": total_buy_amount,
            "total_sell_amount": total_sell_amount,
            "net_amount": total_sell_amount - total_buy_amount
        }
    }


@router.get("/strategy-conditions/{strategy_id}")
async def get_strategy_conditions(strategy_id: str):
    """
    获取策略的详细条件说明
    
    返回策略的所有入场和出场条件，便于理解策略逻辑
    """
    strategy = get_strategy_by_id(strategy_id)
    if not strategy:
        raise HTTPException(status_code=404, detail="策略不存在")
    
    return {
        "success": True,
        "data": {
            "strategy_id": strategy_id,
            "strategy_name": strategy.get("name", ""),
            "description": strategy.get("description", ""),
            "indicators": strategy.get("indicators", []),
            "entry_conditions": strategy.get("entry_conditions", []),
            "exit_conditions": strategy.get("exit_conditions", []),
            "risk_params": strategy.get("risk_params", {}),
            "explanation": _generate_strategy_explanation(strategy)
        }
    }


def _generate_strategy_explanation(strategy: Dict) -> str:
    """生成策略的文字说明"""
    name = strategy.get("name", "未命名策略")
    description = strategy.get("description", "")
    
    explanation = f"## {name}\n\n{description}\n\n"
    
    # 指标说明
    indicators = strategy.get("indicators", [])
    if indicators:
        explanation += "### 使用的指标\n"
        for ind in indicators:
            ind_name = ind.get("name", "")
            params = ind.get("params", {})
            weight = ind.get("weight", 1.0)
            explanation += f"- **{ind_name}**: 参数={params}, 权重={weight}\n"
        explanation += "\n"
    
    # 入场条件
    entry_conditions = strategy.get("entry_conditions", [])
    if entry_conditions:
        explanation += "### 入场条件（全部满足时买入）\n"
        for i, cond in enumerate(entry_conditions, 1):
            desc = cond.get("description", "")
            indicator = cond.get("indicator", "")
            operator = cond.get("operator", "")
            value = cond.get("value", "")
            explanation += f"{i}. {desc} ({indicator} {operator} {value})\n"
        explanation += "\n"
    
    # 出场条件
    exit_conditions = strategy.get("exit_conditions", [])
    if exit_conditions:
        explanation += "### 出场条件（任一满足时卖出）\n"
        for i, cond in enumerate(exit_conditions, 1):
            desc = cond.get("description", "")
            indicator = cond.get("indicator", "")
            operator = cond.get("operator", "")
            value = cond.get("value", "")
            explanation += f"{i}. {desc} ({indicator} {operator} {value})\n"
        explanation += "\n"
    
    # 风险参数
    risk_params = strategy.get("risk_params", {})
    if risk_params:
        explanation += "### 风险控制\n"
        explanation += f"- 止损: {risk_params.get('stop_loss', 0.05) * 100}%\n"
        explanation += f"- 止盈: {risk_params.get('take_profit', 0.15) * 100}%\n"
        explanation += f"- 最大仓位: {risk_params.get('max_position', 0.30) * 100}%\n"
    
    return explanation