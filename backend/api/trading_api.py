"""
模拟交易系统API
实现交易执行、持仓管理、收益跟踪
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import json
from pathlib import Path

# 导入日志系统
from backend.utils.logging_config import get_logger
from backend.utils.tool_logging import log_api_call

logger = get_logger("api.trading")

# 创建路由器
router = APIRouter(prefix="/api/trading", tags=["Trading System"])


class TradeOrder(BaseModel):
    """交易订单"""
    stock_code: str
    action: str = Field(..., description="BUY/SELL")
    quantity: int = Field(..., ge=100, description="数量(需为100整数倍)")
    price: float = Field(..., gt=0, description="价格")
    order_type: str = Field("LIMIT", description="LIMIT/MARKET")
    stop_loss: Optional[float] = Field(None, description="止损价")
    take_profit: Optional[float] = Field(None, description="止盈价")
    
class Position(BaseModel):
    """持仓信息"""
    stock_code: str
    stock_name: str
    quantity: int
    avg_cost: float
    current_price: float
    market_value: float
    profit_loss: float
    profit_loss_rate: float
    holding_days: int
    
class Portfolio(BaseModel):
    """投资组合"""
    total_value: float
    cash_balance: float
    positions_value: float
    total_profit_loss: float
    total_profit_loss_rate: float
    positions: List[Position]
    win_rate: float
    max_drawdown: float
    sharpe_ratio: float
    
class TradeRecord(BaseModel):
    """交易记录"""
    trade_id: str
    timestamp: datetime
    stock_code: str
    stock_name: str
    action: str
    quantity: int
    price: float
    amount: float
    commission: float
    status: str = Field(..., description="PENDING/EXECUTED/CANCELLED")
    notes: str


class TradingSimulator:
    """模拟交易引擎"""
    
    def __init__(self):
        self.data_file = Path("backend/data/trading_simulation.json")
        self.load_data()
        
    def load_data(self):
        """加载交易数据"""
        if self.data_file.exists():
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.portfolio = data.get("portfolio", self._default_portfolio())
                self.positions = data.get("positions", {})
                self.trade_history = data.get("trade_history", [])
        else:
            self.portfolio = self._default_portfolio()
            self.positions = {}
            self.trade_history = []
            self.save_data()
            
    def save_data(self):
        """保存交易数据"""
        self.data_file.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "portfolio": self.portfolio,
            "positions": self.positions,
            "trade_history": self.trade_history,
            "last_update": datetime.now().isoformat()
        }
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)
            
    def _default_portfolio(self):
        """默认投资组合"""
        return {
            "initial_capital": 1000000,  # 100万初始资金
            "cash_balance": 1000000,
            "total_value": 1000000,
            "positions_value": 0,
            "total_profit_loss": 0,
            "total_profit_loss_rate": 0
        }
        
    async def execute_trade(self, order: TradeOrder) -> Dict[str, Any]:
        """执行交易"""
        try:
            # 计算交易金额
            amount = order.quantity * order.price
            commission = max(5, amount * 0.0003)  # 佣金万3，最低5元
            total_cost = amount + commission if order.action == "BUY" else -amount + commission
            
            # 检查资金是否充足
            if order.action == "BUY" and total_cost > self.portfolio["cash_balance"]:
                raise ValueError("资金不足")
                
            # 检查持仓是否充足
            if order.action == "SELL":
                position = self.positions.get(order.stock_code, {})
                if position.get("quantity", 0) < order.quantity:
                    raise ValueError("持仓不足")
                    
            # 执行交易
            trade_id = f"T{datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            if order.action == "BUY":
                # 买入处理
                self.portfolio["cash_balance"] -= total_cost
                
                if order.stock_code in self.positions:
                    # 加仓
                    pos = self.positions[order.stock_code]
                    total_quantity = pos["quantity"] + order.quantity
                    total_cost_basis = pos["quantity"] * pos["avg_cost"] + amount
                    pos["quantity"] = total_quantity
                    pos["avg_cost"] = total_cost_basis / total_quantity
                    pos["last_update"] = datetime.now().isoformat()
                else:
                    # 新建仓位
                    self.positions[order.stock_code] = {
                        "stock_code": order.stock_code,
                        "stock_name": await self._get_stock_name(order.stock_code),
                        "quantity": order.quantity,
                        "avg_cost": order.price,
                        "open_date": datetime.now().isoformat(),
                        "last_update": datetime.now().isoformat()
                    }
                    
            else:  # SELL
                # 卖出处理
                self.portfolio["cash_balance"] += amount - commission
                
                pos = self.positions[order.stock_code]
                pos["quantity"] -= order.quantity
                
                # 计算收益
                profit = (order.price - pos["avg_cost"]) * order.quantity - commission
                self.portfolio["total_profit_loss"] += profit
                
                # 如果全部卖出，移除持仓
                if pos["quantity"] == 0:
                    del self.positions[order.stock_code]
                else:
                    pos["last_update"] = datetime.now().isoformat()
                    
            # 记录交易
            trade_record = {
                "trade_id": trade_id,
                "timestamp": datetime.now().isoformat(),
                "stock_code": order.stock_code,
                "stock_name": await self._get_stock_name(order.stock_code),
                "action": order.action,
                "quantity": order.quantity,
                "price": order.price,
                "amount": amount,
                "commission": commission,
                "status": "EXECUTED"
            }
            
            self.trade_history.append(trade_record)
            
            # 更新组合价值
            await self._update_portfolio_value()
            
            # 保存数据
            self.save_data()
            
            return {
                "success": True,
                "trade_id": trade_id,
                "message": f"交易成功: {order.action} {order.quantity}股 @ {order.price}",
                "trade": trade_record
            }
            
        except Exception as e:
            logger.error(f"交易执行失败: {str(e)}")
            raise
            
    async def _get_stock_name(self, stock_code: str) -> str:
        """获取股票名称"""
        # TODO: 从数据源获取实际股票名称
        stock_names = {
            "600519": "贵州茅台",
            "000858": "五粮液",
            "000333": "美的集团",
            "000002": "万科A",
            "600036": "招商银行"
        }
        
        code = stock_code.replace(".SH", "").replace(".SZ", "")
        return stock_names.get(code, stock_code)
        
    async def _update_portfolio_value(self):
        """更新投资组合价值"""
        positions_value = 0
        
        for code, pos in self.positions.items():
            # 获取当前价格（模拟）
            current_price = await self._get_current_price(code)
            market_value = pos["quantity"] * current_price
            positions_value += market_value
            
        self.portfolio["positions_value"] = positions_value
        self.portfolio["total_value"] = self.portfolio["cash_balance"] + positions_value
        
        # 计算总收益率
        initial = self.portfolio["initial_capital"]
        self.portfolio["total_profit_loss_rate"] = (
            (self.portfolio["total_value"] - initial) / initial * 100
        )
        
    async def _get_current_price(self, stock_code: str) -> float:
        """获取当前价格（模拟）"""
        # TODO: 从实际数据源获取
        import random
        base_price = 100
        return base_price * (1 + random.uniform(-0.05, 0.05))


# 创建全局交易模拟器实例
simulator = TradingSimulator()


@router.post("/execute", response_model=Dict[str, Any])
@log_api_call("执行交易")
async def execute_trade(order: TradeOrder):
    """
    执行模拟交易
    
    Args:
        order: 交易订单
        
    Returns:
        交易执行结果
    """
    try:
        result = await simulator.execute_trade(order)
        logger.success(f"交易成功: {order.action} {order.stock_code} x{order.quantity}")
        return result
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"交易执行失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"交易失败: {str(e)}")


@router.get("/portfolio", response_model=Dict[str, Any])
@log_api_call("查询组合")
async def get_portfolio():
    """
    获取投资组合信息
    
    Returns:
        组合详情
    """
    try:
        # 更新组合价值
        await simulator._update_portfolio_value()
        
        # 构建持仓列表
        positions_list = []
        for code, pos in simulator.positions.items():
            current_price = await simulator._get_current_price(code)
            market_value = pos["quantity"] * current_price
            profit_loss = (current_price - pos["avg_cost"]) * pos["quantity"]
            profit_loss_rate = (current_price - pos["avg_cost"]) / pos["avg_cost"] * 100
            
            # 计算持有天数
            open_date = datetime.fromisoformat(pos["open_date"])
            holding_days = (datetime.now() - open_date).days
            
            positions_list.append({
                "stock_code": code,
                "stock_name": pos["stock_name"],
                "quantity": pos["quantity"],
                "avg_cost": round(pos["avg_cost"], 2),
                "current_price": round(current_price, 2),
                "market_value": round(market_value, 2),
                "profit_loss": round(profit_loss, 2),
                "profit_loss_rate": round(profit_loss_rate, 2),
                "holding_days": holding_days
            })
            
        # 计算统计指标
        win_rate = _calculate_win_rate(simulator.trade_history)
        max_drawdown = _calculate_max_drawdown(simulator.trade_history)
        sharpe_ratio = _calculate_sharpe_ratio(simulator.trade_history)
        
        return {
            "success": True,
            "portfolio": {
                **simulator.portfolio,
                "positions": positions_list,
                "positions_count": len(positions_list),
                "win_rate": win_rate,
                "max_drawdown": max_drawdown,
                "sharpe_ratio": sharpe_ratio
            }
        }
        
    except Exception as e:
        logger.error(f"查询组合失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/history", response_model=Dict[str, Any])
async def get_trade_history(
    limit: int = 50,
    offset: int = 0,
    stock_code: Optional[str] = None,
    action: Optional[str] = None
):
    """
    获取交易历史
    
    Args:
        limit: 返回数量限制
        offset: 偏移量
        stock_code: 股票代码筛选
        action: 交易方向筛选
        
    Returns:
        交易历史记录
    """
    try:
        # 筛选交易记录
        history = simulator.trade_history
        
        if stock_code:
            history = [t for t in history if t["stock_code"] == stock_code]
            
        if action:
            history = [t for t in history if t["action"] == action]
            
        # 排序（最新的在前）
        history = sorted(history, key=lambda x: x["timestamp"], reverse=True)
        
        # 分页
        total = len(history)
        history = history[offset:offset + limit]
        
        return {
            "success": True,
            "total": total,
            "offset": offset,
            "limit": limit,
            "trades": history
        }
        
    except Exception as e:
        logger.error(f"查询历史失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/reset")
@log_api_call("重置交易")
async def reset_trading():
    """
    重置模拟交易账户
    
    Returns:
        重置结果
    """
    try:
        # 重置数据
        simulator.portfolio = simulator._default_portfolio()
        simulator.positions = {}
        simulator.trade_history = []
        simulator.save_data()
        
        logger.info("模拟交易账户已重置")
        
        return {
            "success": True,
            "message": "交易账户已重置",
            "portfolio": simulator.portfolio
        }
        
    except Exception as e:
        logger.error(f"重置失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/performance", response_model=Dict[str, Any])
async def get_performance_metrics(days: int = 30):
    """
    获取交易表现指标
    
    Args:
        days: 统计天数
        
    Returns:
        表现指标
    """
    try:
        # 计算起始日期
        start_date = datetime.now() - timedelta(days=days)
        
        # 筛选时间范围内的交易
        recent_trades = [
            t for t in simulator.trade_history
            if datetime.fromisoformat(t["timestamp"]) >= start_date
        ]
        
        # 计算各项指标
        metrics = {
            "period_days": days,
            "total_trades": len(recent_trades),
            "buy_trades": len([t for t in recent_trades if t["action"] == "BUY"]),
            "sell_trades": len([t for t in recent_trades if t["action"] == "SELL"]),
            "total_volume": sum(t["amount"] for t in recent_trades),
            "total_commission": sum(t["commission"] for t in recent_trades),
            "win_rate": _calculate_win_rate(recent_trades),
            "avg_profit_per_trade": _calculate_avg_profit(recent_trades),
            "max_drawdown": _calculate_max_drawdown(recent_trades),
            "sharpe_ratio": _calculate_sharpe_ratio(recent_trades),
            "daily_returns": _calculate_daily_returns(recent_trades, days)
        }
        
        return {
            "success": True,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"计算表现指标失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# 辅助函数
def _calculate_win_rate(trades: List[Dict]) -> float:
    """计算胜率"""
    if not trades:
        return 0.0
        
    sells = [t for t in trades if t["action"] == "SELL"]
    if not sells:
        return 0.0
        
    # TODO: 需要关联买卖交易计算实际盈亏
    # 这里简化处理
    return 0.55  # 模拟55%胜率


def _calculate_max_drawdown(trades: List[Dict]) -> float:
    """计算最大回撤"""
    if not trades:
        return 0.0
        
    # TODO: 需要根据净值曲线计算
    return 0.12  # 模拟12%最大回撤


def _calculate_sharpe_ratio(trades: List[Dict]) -> float:
    """计算夏普比率"""
    if not trades:
        return 0.0
        
    # TODO: 需要计算收益率标准差
    return 1.5  # 模拟1.5夏普比率


def _calculate_avg_profit(trades: List[Dict]) -> float:
    """计算平均收益"""
    if not trades:
        return 0.0
        
    # TODO: 需要关联买卖计算
    return 1000  # 模拟平均每笔1000元收益


def _calculate_daily_returns(trades: List[Dict], days: int) -> List[Dict]:
    """计算日收益率"""
    # TODO: 根据实际交易计算每日收益
    # 这里生成模拟数据
    import random
    
    returns = []
    for i in range(min(days, 30)):
        date = datetime.now() - timedelta(days=i)
        returns.append({
            "date": date.strftime("%Y-%m-%d"),
            "return": random.uniform(-0.03, 0.03),
            "value": 1000000 * (1 + random.uniform(-0.05, 0.05))
        })
        
    return returns[::-1]  # 按日期正序


# 测试端点
@router.get("/test")
async def test_trading_api():
    """测试交易API是否正常工作"""
    return {
        "status": "ok",
        "message": "Trading API is working",
        "features": [
            "Trade execution",
            "Portfolio management",
            "Trade history",
            "Performance metrics",
            "Risk management"
        ],
        "timestamp": datetime.now().isoformat()
    }
