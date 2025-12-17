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
from backend.trading.market_rules import market_rule_engine, MarketType

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
            # 检测市场类型
            market_type = market_rule_engine.detect_market(order.stock_code)
            market_rule = market_rule_engine.get_rule(market_type)
            
            # 检查交易数量是否合法
            is_valid, error_msg = market_rule_engine.validate_quantity(market_type, order.quantity)
            if not is_valid:
                raise ValueError(error_msg)
            
            # 检查T+N规则（卖出时）
            if order.action == "SELL" and order.stock_code in self.positions:
                pos = self.positions[order.stock_code]
                # 获取持仓中的买入记录
                if "trades" in pos:
                    available_qty = 0
                    for trade in pos["trades"]:
                        buy_date = datetime.fromisoformat(trade["date"])
                        if market_rule_engine.can_sell_today(market_type, buy_date):
                            available_qty += trade["quantity"]
                    
                    if available_qty < order.quantity:
                        raise ValueError(f"T+{market_rule.t_plus}规则限制：可卖数量不足，当前可卖{available_qty}股")
            
            # 计算交易金额和手续费
            amount = order.quantity * order.price
            commission = market_rule_engine.calculate_commission(
                market_type,
                order.action.lower(),
                amount
            )
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
                
                # 记录买入交易（用于T+N规则）
                trade_record = {
                    "date": datetime.now().isoformat(),
                    "quantity": order.quantity,
                    "price": order.price,
                    "market": market_type.value
                }
                
                if order.stock_code in self.positions:
                    # 加仓
                    pos = self.positions[order.stock_code]
                    total_quantity = pos["quantity"] + order.quantity
                    total_cost_basis = pos["quantity"] * pos["avg_cost"] + amount
                    pos["quantity"] = total_quantity
                    pos["avg_cost"] = total_cost_basis / total_quantity
                    pos["last_update"] = datetime.now().isoformat()
                    
                    # 添加买入记录
                    if "trades" not in pos:
                        pos["trades"] = []
                    pos["trades"].append(trade_record)
                else:
                    # 新建仓位
                    self.positions[order.stock_code] = {
                        "stock_code": order.stock_code,
                        "stock_name": await self._get_stock_name(order.stock_code),
                        "quantity": order.quantity,
                        "avg_cost": order.price,
                        "open_date": datetime.now().isoformat(),
                        "last_update": datetime.now().isoformat(),
                        "market": market_type.value,
                        "trades": [trade_record]  # 记录买入交易
                    }
                    
            else:  # SELL
                # 卖出处理
                self.portfolio["cash_balance"] += amount - commission
                
                pos = self.positions[order.stock_code]
                pos["quantity"] -= order.quantity
                
                # 更新买入记录（FIFO原则）
                if "trades" in pos:
                    remaining_to_sell = order.quantity
                    new_trades = []
                    
                    for trade in pos["trades"]:
                        if remaining_to_sell <= 0:
                            new_trades.append(trade)
                        elif trade["quantity"] > remaining_to_sell:
                            trade["quantity"] -= remaining_to_sell
                            new_trades.append(trade)
                            remaining_to_sell = 0
                        else:
                            remaining_to_sell -= trade["quantity"]
                    
                    pos["trades"] = new_trades
                
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
        """获取股票名称 - 使用真实数据"""
        try:
            from backend.services.market_data_service import get_stock_name
            name = get_stock_name(stock_code)
            if name and name != stock_code:
                return name
        except Exception as e:
            logger.warning(f"获取股票名称失败: {stock_code}, {e}")

        # 降级：使用本地缓存
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
        """获取当前价格 - 使用真实行情数据"""
        try:
            from backend.services.market_data_service import get_realtime_quote
            quote = get_realtime_quote(stock_code)
            price = quote.get("current_price", 0)
            if price > 0:
                return price
            # 如果获取失败，尝试从持仓成本获取
            if stock_code in self.positions:
                return self.positions[stock_code].get("avg_cost", 100)
            return 100.0
        except Exception as e:
            logger.warning(f"获取实时价格失败: {stock_code}, {e}")
            # 降级：使用持仓成本或默认值
            if stock_code in self.positions:
                return self.positions[stock_code].get("avg_cost", 100)
            return 100.0


# 创建全局交易模拟器实例
simulator = TradingSimulator()


# ==================== 账户管理端点 ====================

@router.get("/accounts")
async def get_accounts():
    """
    获取所有交易账户列表
    
    Returns:
        账户列表
    """
    try:
        # 目前返回默认模拟账户
        return {
            "success": True,
            "accounts": [
                {
                    "id": "default",
                    "name": "默认模拟账户",
                    "type": "simulation",
                    "balance": simulator.portfolio.get("cash_balance", 1000000),
                    "total_value": simulator.portfolio.get("total_value", 1000000),
                    "created_at": "2024-01-01",
                    "status": "active"
                }
            ],
            "total": 1
        }
    except Exception as e:
        logger.error(f"获取账户列表失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/account/create")
async def create_account():
    """
    创建新交易账户
    
    Returns:
        创建的账户信息
    """
    try:
        # 目前只支持一个默认账户
        return {
            "success": True,
            "message": "账户已存在",
            "account": {
                "id": "default",
                "name": "默认模拟账户",
                "type": "simulation",
                "balance": simulator.portfolio.get("cash_balance", 1000000),
                "total_value": simulator.portfolio.get("total_value", 1000000),
                "created_at": "2024-01-01"
            }
        }
    except Exception as e:
        logger.error(f"创建账户失败: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


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


# 辅助函数 - 真实计算交易统计指标
def _calculate_win_rate(trades: List[Dict]) -> float:
    """计算胜率 - 基于实际交易记录"""
    if not trades:
        return 0.0

    # 配对买卖交易计算盈亏
    buy_trades = {}  # stock_code -> [buy_trades]
    winning_trades = 0
    total_closed_trades = 0

    for trade in trades:
        stock_code = trade.get("stock_code", "")
        action = trade.get("action", "")
        price = trade.get("price", 0)
        quantity = trade.get("quantity", 0)

        if action == "BUY":
            if stock_code not in buy_trades:
                buy_trades[stock_code] = []
            buy_trades[stock_code].append({"price": price, "quantity": quantity})
        elif action == "SELL" and stock_code in buy_trades and buy_trades[stock_code]:
            # FIFO匹配
            buy = buy_trades[stock_code][0]
            profit = (price - buy["price"]) * min(quantity, buy["quantity"])
            if profit > 0:
                winning_trades += 1
            total_closed_trades += 1
            # 更新买入记录
            if buy["quantity"] <= quantity:
                buy_trades[stock_code].pop(0)
            else:
                buy["quantity"] -= quantity

    if total_closed_trades == 0:
        return 0.0

    return winning_trades / total_closed_trades


def _calculate_max_drawdown(trades: List[Dict]) -> float:
    """计算最大回撤 - 基于交易记录构建净值曲线"""
    if not trades:
        return 0.0

    # 构建简化的净值曲线
    initial_capital = 1000000
    capital = initial_capital
    peak = initial_capital
    max_drawdown = 0

    for trade in sorted(trades, key=lambda x: x.get("timestamp", "")):
        action = trade.get("action", "")
        amount = trade.get("amount", 0)
        commission = trade.get("commission", 0)

        if action == "BUY":
            capital -= (amount + commission)
        elif action == "SELL":
            capital += (amount - commission)

        # 更新峰值和回撤
        if capital > peak:
            peak = capital
        drawdown = (peak - capital) / peak if peak > 0 else 0
        max_drawdown = max(max_drawdown, drawdown)

    return max_drawdown


def _calculate_sharpe_ratio(trades: List[Dict]) -> float:
    """计算夏普比率 - 基于交易收益率"""
    if len(trades) < 2:
        return 0.0

    import numpy as np

    # 计算每笔交易的收益率
    returns = []
    for trade in trades:
        if trade.get("action") == "SELL":
            amount = trade.get("amount", 0)
            commission = trade.get("commission", 0)
            # 简化：假设每笔交易投入10万
            investment = 100000
            ret = (amount - commission - investment) / investment
            returns.append(ret)

    if not returns:
        return 0.0

    returns = np.array(returns)
    mean_return = np.mean(returns)
    std_return = np.std(returns)

    if std_return == 0:
        return 0.0

    # 年化夏普比率（假设每年50笔交易）
    risk_free_rate = 0.03 / 50  # 年化3%无风险利率
    sharpe = (mean_return - risk_free_rate) / std_return * np.sqrt(50)

    return round(sharpe, 2)


def _calculate_avg_profit(trades: List[Dict]) -> float:
    """计算平均收益 - 基于实际交易"""
    if not trades:
        return 0.0

    total_profit = 0
    sell_count = 0

    buy_prices = {}  # stock_code -> avg_buy_price

    for trade in trades:
        stock_code = trade.get("stock_code", "")
        action = trade.get("action", "")
        price = trade.get("price", 0)
        quantity = trade.get("quantity", 0)
        commission = trade.get("commission", 0)

        if action == "BUY":
            if stock_code not in buy_prices:
                buy_prices[stock_code] = price
            else:
                # 简化：取平均
                buy_prices[stock_code] = (buy_prices[stock_code] + price) / 2
        elif action == "SELL" and stock_code in buy_prices:
            profit = (price - buy_prices[stock_code]) * quantity - commission
            total_profit += profit
            sell_count += 1

    if sell_count == 0:
        return 0.0

    return round(total_profit / sell_count, 2)


def _calculate_daily_returns(trades: List[Dict], days: int) -> List[Dict]:
    """计算日收益率 - 基于实际交易记录"""
    if not trades:
        return []

    # 按日期分组交易
    from collections import defaultdict
    daily_pnl = defaultdict(float)

    for trade in trades:
        timestamp = trade.get("timestamp", "")
        if timestamp:
            try:
                date = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d")
                action = trade.get("action", "")
                amount = trade.get("amount", 0)
                commission = trade.get("commission", 0)

                if action == "SELL":
                    # 简化：卖出金额减去假设的买入成本
                    daily_pnl[date] += amount - commission - 100000
                elif action == "BUY":
                    daily_pnl[date] -= commission
            except:
                pass

    # 构建日收益率列表
    returns = []
    initial_capital = 1000000
    cumulative_value = initial_capital

    for i in range(days):
        date = (datetime.now() - timedelta(days=days - 1 - i)).strftime("%Y-%m-%d")
        pnl = daily_pnl.get(date, 0)
        cumulative_value += pnl
        daily_return = pnl / initial_capital if initial_capital > 0 else 0

        returns.append({
            "date": date,
            "return": round(daily_return, 4),
            "value": round(cumulative_value, 2)
        })

    return returns


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
