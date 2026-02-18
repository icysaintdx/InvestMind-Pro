"""
智能交易API
整合策略规则引擎、虚拟交易
注：监控功能已整合到 auto_trade_api.py
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, List, Optional
from datetime import datetime
import logging

from ..services.strategy_rule_engine import get_strategy_rule_engine
from ..services.virtual_trading import get_virtual_trading_service
from ..services.trading_rules import (
    get_trading_time_manager,
    PriceLimitManager,
    TradingUnit
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/smart-trading", tags=["智能交易"])


# ==================== 请求模型 ====================

class BacktestRequest(BaseModel):
    """回测请求"""
    strategy_id: str
    strategy_config: Dict
    stock_code: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    initial_capital: float = 100000


class AnalyzeRequest(BaseModel):
    """分析请求"""
    strategy_config: Dict
    stock_code: str


class BuyRequest(BaseModel):
    """买入请求"""
    stock_code: str
    stock_name: str
    quantity: int
    price: float
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None


class SellRequest(BaseModel):
    """卖出请求"""
    stock_code: str
    quantity: int
    price: float
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None


class UpdatePricesRequest(BaseModel):
    """更新价格请求"""
    prices: Dict[str, float]


# ==================== 交易时间API ====================

@router.get("/trading-time/status")
async def get_trading_time_status():
    """获取当前交易时间状态"""
    manager = get_trading_time_manager()

    can_trade, reason = manager.can_trade_now()
    session = manager.get_current_session()
    is_trading_day = manager.is_trading_day()

    return {
        "success": True,
        "data": {
            "is_trading_day": is_trading_day,
            "can_trade": can_trade,
            "reason": reason,
            "current_session": {
                "name": session.session.value,
                "description": session.description,
                "can_trade": session.can_trade,
                "can_cancel": session.can_cancel
            },
            "server_time": datetime.now().isoformat()
        }
    }


@router.get("/trading-time/next-trading-day")
async def get_next_trading_day():
    """获取下一个交易日"""
    manager = get_trading_time_manager()
    next_day = manager.get_next_trading_day()

    return {
        "success": True,
        "data": {
            "next_trading_day": next_day.isoformat()
        }
    }


# ==================== 策略分析API ====================

async def _get_kline_data(stock_code: str, count: int = 100):
    """获取K线数据"""
    try:
        from ..dataflows.akshare.base import AKShareStockData
        provider = AKShareStockData()

        # 获取历史K线
        from datetime import timedelta
        end_date = datetime.now()
        start_date = end_date - timedelta(days=count * 2)  # 预留足够天数

        df = provider.get_history_kline(
            stock_code,
            start_date.strftime("%Y%m%d"),
            end_date.strftime("%Y%m%d"),
            "daily"
        )

        if df is None or df.empty:
            return None

        # 转换为列表格式
        kline_data = []
        for _, row in df.iterrows():
            kline_data.append({
                "date": row.get("date", row.get("trade_date", "")),
                "open": float(row.get("open", 0)),
                "high": float(row.get("high", 0)),
                "low": float(row.get("low", 0)),
                "close": float(row.get("close", 0)),
                "volume": float(row.get("volume", row.get("vol", 0)))
            })

        return kline_data[-count:] if len(kline_data) > count else kline_data
    except Exception as e:
        logger.error(f"获取K线数据失败: {e}")
        return None


@router.post("/analyze")
async def analyze_strategy(request: AnalyzeRequest):
    """分析当前状态"""
    try:
        engine = get_strategy_rule_engine()

        # 获取K线数据
        kline_data = await _get_kline_data(request.stock_code, count=100)

        if not kline_data:
            raise HTTPException(status_code=400, detail="获取K线数据失败")

        # 分析
        result = engine.analyze_current_state(kline_data, request.strategy_config)

        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        logger.error(f"分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backtest")
async def run_backtest(request: BacktestRequest):
    """执行回测"""
    try:
        engine = get_strategy_rule_engine()

        # 获取K线数据
        kline_data = await _get_kline_data(request.stock_code, count=500)

        if not kline_data:
            raise HTTPException(status_code=400, detail="获取K线数据失败")

        # 执行回测
        result = engine.backtest(kline_data, request.strategy_config, request.initial_capital)

        return {
            "success": True,
            "data": {
                "strategy_id": result.strategy_id,
                "strategy_name": result.strategy_name,
                "stock_code": result.stock_code,
                "start_date": result.start_date.isoformat() if result.start_date else None,
                "end_date": result.end_date.isoformat() if result.end_date else None,
                "total_trades": result.total_trades,
                "winning_trades": result.winning_trades,
                "losing_trades": result.losing_trades,
                "win_rate": round(result.win_rate * 100, 2),
                "total_return": round(result.total_return * 100, 2),
                "max_drawdown": round(result.max_drawdown * 100, 2),
                "buy_signals": result.buy_signals,
                "sell_signals": result.sell_signals
            }
        }
    except Exception as e:
        logger.error(f"回测失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/find-signals")
async def find_signals(request: AnalyzeRequest):
    """查找历史信号点"""
    try:
        engine = get_strategy_rule_engine()

        # 获取K线数据
        kline_data = await _get_kline_data(request.stock_code, count=200)

        if not kline_data:
            raise HTTPException(status_code=400, detail="获取K线数据失败")

        # 准备数据
        df = engine.prepare_dataframe(kline_data)
        df = engine.calculate_all_indicators(df, request.strategy_config)

        # 查找信号
        signals = engine.find_all_signals(df, request.strategy_config)

        return {
            "success": True,
            "data": {
                "total_signals": len(signals),
                "signals": [
                    {
                        "type": s.signal_type.value,
                        "timestamp": s.timestamp.isoformat() if hasattr(s.timestamp, 'isoformat') else str(s.timestamp),
                        "price": s.price,
                        "confidence": round(s.confidence * 100, 2),
                        "conditions": s.conditions_met,
                        "stop_loss": s.stop_loss,
                        "take_profit": s.take_profit
                    }
                    for s in signals
                ]
            }
        }
    except Exception as e:
        logger.error(f"查找信号失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 虚拟交易API ====================

@router.get("/account")
async def get_account():
    """获取账户信息"""
    service = get_virtual_trading_service()

    return {
        "success": True,
        "data": service.get_account()
    }


@router.get("/positions")
async def get_positions():
    """获取持仓列表"""
    service = get_virtual_trading_service()

    return {
        "success": True,
        "data": service.get_positions()
    }


@router.get("/positions/{stock_code}")
async def get_position(stock_code: str):
    """获取单只股票持仓"""
    service = get_virtual_trading_service()

    position = service.get_position(stock_code)
    if position:
        return {"success": True, "data": position}
    else:
        raise HTTPException(status_code=404, detail="无持仓")


@router.post("/trade/buy")
async def buy_stock(request: BuyRequest):
    """买入股票"""
    service = get_virtual_trading_service()

    success, msg, order = service.buy(
        stock_code=request.stock_code,
        stock_name=request.stock_name,
        quantity=request.quantity,
        price=request.price,
        strategy_id=request.strategy_id,
        signal_id=request.signal_id
    )

    if success:
        return {"success": True, "message": msg, "data": order}
    else:
        raise HTTPException(status_code=400, detail=msg)


@router.post("/trade/sell")
async def sell_stock(request: SellRequest):
    """卖出股票"""
    service = get_virtual_trading_service()

    success, msg, order = service.sell(
        stock_code=request.stock_code,
        quantity=request.quantity,
        price=request.price,
        strategy_id=request.strategy_id,
        signal_id=request.signal_id
    )

    if success:
        return {"success": True, "message": msg, "data": order}
    else:
        raise HTTPException(status_code=400, detail=msg)


@router.get("/trade/orders")
async def get_orders(status: str = None):
    """获取订单列表"""
    service = get_virtual_trading_service()

    return {
        "success": True,
        "data": service.get_orders(status)
    }


@router.post("/trade/update-prices")
async def update_prices(request: UpdatePricesRequest):
    """更新持仓价格"""
    service = get_virtual_trading_service()
    service.update_prices(request.prices)

    return {"success": True, "message": "价格已更新"}


@router.post("/trade/daily-settlement")
async def daily_settlement():
    """每日结算"""
    service = get_virtual_trading_service()
    service.daily_settlement()

    return {"success": True, "message": "结算完成"}


@router.post("/trade/reset")
async def reset_account(initial_capital: float = 100000):
    """重置账户"""
    service = get_virtual_trading_service()
    service.reset_account(initial_capital)

    return {"success": True, "message": f"账户已重置，初始资金: {initial_capital}"}


# ==================== 工具API ====================

@router.get("/tools/price-limits/{stock_code}")
async def get_price_limits(stock_code: str, prev_close: float, stock_name: str = ""):
    """获取涨跌停价格"""
    limit_up, limit_down = PriceLimitManager.calculate_limit_prices(
        stock_code, prev_close, stock_name
    )

    market_type = PriceLimitManager.get_market_type(stock_code)
    limit_pct = PriceLimitManager.get_price_limit(stock_code, stock_name)

    return {
        "success": True,
        "data": {
            "stock_code": stock_code,
            "market_type": market_type.value,
            "limit_pct": limit_pct,
            "prev_close": prev_close,
            "limit_up": limit_up,
            "limit_down": limit_down
        }
    }


@router.get("/tools/calculate-buy-quantity")
async def calculate_buy_quantity(available_cash: float, price: float):
    """计算可买数量"""
    quantity = TradingUnit.calculate_buy_quantity(available_cash, price)

    return {
        "success": True,
        "data": {
            "available_cash": available_cash,
            "price": price,
            "max_quantity": quantity,
            "estimated_cost": quantity * price
        }
    }
