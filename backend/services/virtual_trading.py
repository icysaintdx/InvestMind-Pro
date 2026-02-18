"""
虚拟交易服务
包含：持仓管理、订单管理、资金管理、风控管理
"""

from datetime import datetime, date
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import logging
import json
from pathlib import Path

from .trading_rules import (
    TradingTimeManager, PriceLimitManager, TPlusOneManager, TradingUnit,
    get_trading_time_manager, get_t_plus_one_manager
)

logger = logging.getLogger(__name__)


class OrderDirection(Enum):
    """订单方向"""
    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """订单类型"""
    LIMIT = "LIMIT"  # 限价单
    MARKET = "MARKET"  # 市价单


class OrderStatus(Enum):
    """订单状态"""
    PENDING = "PENDING"  # 待成交
    PARTIAL = "PARTIAL"  # 部分成交
    FILLED = "FILLED"  # 全部成交
    CANCELLED = "CANCELLED"  # 已撤销
    REJECTED = "REJECTED"  # 已拒绝


@dataclass
class Position:
    """持仓"""
    stock_code: str
    stock_name: str
    quantity: int  # 总持仓
    available_quantity: int  # 可卖数量
    frozen_quantity: int  # 冻结数量（T+1）
    cost_price: float  # 成本价
    current_price: float  # 当前价
    market_value: float  # 市值
    profit_loss: float  # 盈亏金额
    profit_loss_pct: float  # 盈亏比例
    
    def update_price(self, current_price: float):
        """更新当前价格"""
        self.current_price = current_price
        self.market_value = self.quantity * current_price
        self.profit_loss = (current_price - self.cost_price) * self.quantity
        self.profit_loss_pct = (current_price - self.cost_price) / self.cost_price if self.cost_price > 0 else 0
    
    def to_dict(self) -> Dict:
        return {
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "quantity": self.quantity,
            "available_quantity": self.available_quantity,
            "frozen_quantity": self.frozen_quantity,
            "cost_price": round(self.cost_price, 2),
            "current_price": round(self.current_price, 2),
            "market_value": round(self.market_value, 2),
            "profit_loss": round(self.profit_loss, 2),
            "profit_loss_pct": round(self.profit_loss_pct * 100, 2)
        }


@dataclass
class Order:
    """订单"""
    order_id: str
    stock_code: str
    stock_name: str
    direction: OrderDirection
    order_type: OrderType
    quantity: int
    price: float
    filled_quantity: int = 0
    filled_price: float = 0.0
    status: OrderStatus = OrderStatus.PENDING
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    strategy_id: Optional[str] = None
    signal_id: Optional[str] = None
    plan_id: Optional[str] = None  # 关联的交易计划ID
    source: str = "manual"  # 订单来源: manual | auto
    strategy_name: Optional[str] = None  # 策略名称
    reject_reason: str = ""

    def to_dict(self) -> Dict:
        return {
            "order_id": self.order_id,
            "stock_code": self.stock_code,
            "stock_name": self.stock_name,
            "direction": self.direction.value,
            "order_type": self.order_type.value,
            "quantity": self.quantity,
            "price": round(self.price, 2),
            "filled_quantity": self.filled_quantity,
            "filled_price": round(self.filled_price, 2),
            "status": self.status.value,
            "create_time": self.create_time.isoformat(),
            "update_time": self.update_time.isoformat(),
            "strategy_id": self.strategy_id,
            "signal_id": self.signal_id,
            "plan_id": self.plan_id,
            "source": self.source,
            "strategy_name": self.strategy_name,
            "reject_reason": self.reject_reason
        }


@dataclass
class Account:
    """账户"""
    account_id: str
    total_assets: float  # 总资产
    market_value: float  # 持仓市值
    available_cash: float  # 可用资金
    frozen_cash: float  # 冻结资金
    today_profit: float  # 今日盈亏
    total_profit: float  # 累计盈亏
    
    def to_dict(self) -> Dict:
        return {
            "account_id": self.account_id,
            "total_assets": round(self.total_assets, 2),
            "market_value": round(self.market_value, 2),
            "available_cash": round(self.available_cash, 2),
            "frozen_cash": round(self.frozen_cash, 2),
            "today_profit": round(self.today_profit, 2),
            "total_profit": round(self.total_profit, 2)
        }


class RiskManager:
    """风险管理器"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            "max_single_position": 0.30,  # 单只股票最大仓位30%
            "max_total_position": 0.80,   # 总仓位最大80%
            "max_daily_loss": 0.05,       # 单日最大亏损5%
            "max_single_loss": 0.10,      # 单只股票最大亏损10%
            "min_cash_reserve": 0.10,     # 最小现金储备10%
            "max_order_value": 100000,    # 单笔最大金额
        }
    
    def check_buy_risk(self, account: Account, positions: Dict[str, Position],
                       stock_code: str, quantity: int, price: float) -> Tuple[bool, str]:
        """买入风控检查"""
        order_value = quantity * price
        
        # 1. 检查资金是否充足
        if order_value > account.available_cash:
            return False, f"资金不足: 需要{order_value:.2f}, 可用{account.available_cash:.2f}"
        
        # 2. 检查单笔金额限制
        if order_value > self.config["max_order_value"]:
            return False, f"单笔金额超限: {order_value:.2f} > {self.config['max_order_value']}"
        
        # 3. 检查单只股票仓位限制
        current_position_value = 0
        if stock_code in positions:
            current_position_value = positions[stock_code].market_value
        
        new_position_value = current_position_value + order_value
        max_single_value = account.total_assets * self.config["max_single_position"]
        
        if new_position_value > max_single_value:
            return False, f"单只股票仓位超限: {new_position_value:.2f} > {max_single_value:.2f}"
        
        # 4. 检查总仓位限制
        total_position_value = account.market_value + order_value
        max_total_value = account.total_assets * self.config["max_total_position"]
        
        if total_position_value > max_total_value:
            return False, f"总仓位超限: {total_position_value:.2f} > {max_total_value:.2f}"
        
        # 5. 检查现金储备
        remaining_cash = account.available_cash - order_value
        min_cash = account.total_assets * self.config["min_cash_reserve"]
        
        if remaining_cash < min_cash:
            return False, f"现金储备不足: 剩余{remaining_cash:.2f} < 最低{min_cash:.2f}"
        
        # 6. 检查单日亏损限制
        if account.today_profit < -account.total_assets * self.config["max_daily_loss"]:
            return False, f"今日亏损已达限制，暂停交易"
        
        return True, "风控检查通过"
    
    def check_sell_risk(self, positions: Dict[str, Position],
                        stock_code: str, quantity: int) -> Tuple[bool, str]:
        """卖出风控检查"""
        if stock_code not in positions:
            return False, f"无持仓: {stock_code}"
        
        position = positions[stock_code]
        
        if quantity > position.available_quantity:
            return False, f"可卖数量不足: 需要{quantity}, 可卖{position.available_quantity}"
        
        return True, "风控检查通过"


class VirtualTradingService:
    """虚拟交易服务"""
    
    def __init__(self, initial_capital: float = 100000, data_dir: str = "data/virtual_trading"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.trading_time_manager = get_trading_time_manager()
        self.t_plus_one_manager = get_t_plus_one_manager()
        self.risk_manager = RiskManager()
        
        # 初始化账户
        self.account = Account(
            account_id="virtual_001",
            total_assets=initial_capital,
            market_value=0,
            available_cash=initial_capital,
            frozen_cash=0,
            today_profit=0,
            total_profit=0
        )
        
        # 持仓
        self.positions: Dict[str, Position] = {}
        
        # 订单
        self.orders: Dict[str, Order] = {}
        self.order_history: List[Order] = []
        
        # 交易记录
        self.trade_history: List[Dict] = []
        
        # 加载持久化数据
        self._load_data()
    
    def _load_data(self):
        """加载持久化数据"""
        account_file = self.data_dir / "account.json"
        positions_file = self.data_dir / "positions.json"
        orders_file = self.data_dir / "orders.json"
        
        try:
            if account_file.exists():
                with open(account_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.account = Account(**data)
            
            if positions_file.exists():
                with open(positions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for code, pos_data in data.items():
                        self.positions[code] = Position(**pos_data)
            
            if orders_file.exists():
                with open(orders_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for order_data in data:
                        order_data['direction'] = OrderDirection(order_data['direction'])
                        order_data['order_type'] = OrderType(order_data['order_type'])
                        order_data['status'] = OrderStatus(order_data['status'])
                        order_data['create_time'] = datetime.fromisoformat(order_data['create_time'])
                        order_data['update_time'] = datetime.fromisoformat(order_data['update_time'])
                        self.order_history.append(Order(**order_data))
                        
        except Exception as e:
            logger.error(f"加载数据失败: {e}")
    
    def _save_data(self):
        """保存持久化数据"""
        try:
            account_file = self.data_dir / "account.json"
            with open(account_file, 'w', encoding='utf-8') as f:
                json.dump(self.account.to_dict(), f, ensure_ascii=False, indent=2)
            
            positions_file = self.data_dir / "positions.json"
            positions_data = {code: pos.to_dict() for code, pos in self.positions.items()}
            with open(positions_file, 'w', encoding='utf-8') as f:
                json.dump(positions_data, f, ensure_ascii=False, indent=2)
            
            orders_file = self.data_dir / "orders.json"
            orders_data = [order.to_dict() for order in self.order_history[-100:]]  # 只保留最近100条
            with open(orders_file, 'w', encoding='utf-8') as f:
                json.dump(orders_data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            logger.error(f"保存数据失败: {e}")
    
    def get_account(self) -> Dict:
        """获取账户信息"""
        return self.account.to_dict()
    
    def get_positions(self) -> List[Dict]:
        """获取持仓列表"""
        return [pos.to_dict() for pos in self.positions.values()]
    
    def get_position(self, stock_code: str) -> Optional[Dict]:
        """获取单只股票持仓"""
        if stock_code in self.positions:
            return self.positions[stock_code].to_dict()
        return None
    
    def get_orders(self, status: str = None) -> List[Dict]:
        """获取订单列表"""
        orders = list(self.orders.values()) + self.order_history
        
        if status:
            orders = [o for o in orders if o.status.value == status]
        
        return [o.to_dict() for o in sorted(orders, key=lambda x: x.create_time, reverse=True)]
    
    def buy(self, stock_code: str, stock_name: str, quantity: int, price: float,
            strategy_id: str = None, signal_id: str = None,
            plan_id: str = None, source: str = "manual", strategy_name: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """买入"""
        # 1. 检查交易时间
        can_trade, reason = self.trading_time_manager.can_trade_now()
        # 虚拟交易允许非交易时间操作，但记录警告
        if not can_trade:
            logger.warning(f"非交易时间买入: {reason}")

        # 2. 验证买入数量
        valid, msg = TradingUnit.validate_buy_quantity(quantity)
        if not valid:
            return False, msg, None

        # 3. 风控检查
        passed, msg = self.risk_manager.check_buy_risk(
            self.account, self.positions, stock_code, quantity, price
        )
        if not passed:
            return False, msg, None

        # 4. 创建订单
        order = Order(
            order_id=str(uuid.uuid4())[:8],
            stock_code=stock_code,
            stock_name=stock_name,
            direction=OrderDirection.BUY,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            strategy_id=strategy_id,
            signal_id=signal_id,
            plan_id=plan_id,
            source=source,
            strategy_name=strategy_name
        )
        
        # 5. 执行买入（虚拟交易直接成交）
        order_value = quantity * price
        commission = order_value * 0.0003  # 万三手续费
        total_cost = order_value + commission
        
        # 更新账户
        self.account.available_cash -= total_cost
        self.account.market_value += order_value
        
        # 更新持仓
        if stock_code in self.positions:
            pos = self.positions[stock_code]
            # 计算新的成本价
            total_value = pos.cost_price * pos.quantity + order_value
            total_qty = pos.quantity + quantity
            pos.cost_price = total_value / total_qty
            pos.quantity = total_qty
            pos.frozen_quantity += quantity  # T+1冻结
            pos.update_price(price)
        else:
            self.positions[stock_code] = Position(
                stock_code=stock_code,
                stock_name=stock_name,
                quantity=quantity,
                available_quantity=0,  # T+1，当日不可卖
                frozen_quantity=quantity,
                cost_price=price,
                current_price=price,
                market_value=order_value,
                profit_loss=0,
                profit_loss_pct=0
            )
        
        # 冻结持仓（T+1）
        self.t_plus_one_manager.freeze_position(stock_code, quantity)
        
        # 更新订单状态
        order.filled_quantity = quantity
        order.filled_price = price
        order.status = OrderStatus.FILLED
        order.update_time = datetime.now()
        
        self.order_history.append(order)
        
        # 记录交易
        trade_record = {
            "time": datetime.now().isoformat(),
            "stock_code": stock_code,
            "stock_name": stock_name,
            "direction": "BUY",
            "quantity": quantity,
            "price": price,
            "amount": order_value,
            "commission": commission,
            "order_id": order.order_id
        }
        self.trade_history.append(trade_record)
        
        # 保存数据
        self._save_data()
        
        logger.info(f"买入成功: {stock_code} {stock_name} {quantity}股 @ {price}")
        
        return True, "买入成功", order.to_dict()
    
    def sell(self, stock_code: str, quantity: int, price: float,
             strategy_id: str = None, signal_id: str = None,
             plan_id: str = None, source: str = "manual", strategy_name: str = None) -> Tuple[bool, str, Optional[Dict]]:
        """卖出"""
        # 1. 检查交易时间
        can_trade, reason = self.trading_time_manager.can_trade_now()
        if not can_trade:
            logger.warning(f"非交易时间卖出: {reason}")

        # 2. 检查持仓
        if stock_code not in self.positions:
            return False, f"无持仓: {stock_code}", None

        pos = self.positions[stock_code]

        # 3. 验证卖出数量
        valid, msg = TradingUnit.validate_sell_quantity(quantity, pos.available_quantity)
        if not valid:
            return False, msg, None

        # 4. T+1检查
        can_sell, msg = self.t_plus_one_manager.can_sell(stock_code, quantity, pos.quantity)
        if not can_sell:
            return False, msg, None

        # 5. 风控检查
        passed, msg = self.risk_manager.check_sell_risk(self.positions, stock_code, quantity)
        if not passed:
            return False, msg, None

        # 6. 创建订单
        order = Order(
            order_id=str(uuid.uuid4())[:8],
            stock_code=stock_code,
            stock_name=pos.stock_name,
            direction=OrderDirection.SELL,
            order_type=OrderType.LIMIT,
            quantity=quantity,
            price=price,
            strategy_id=strategy_id,
            signal_id=signal_id,
            plan_id=plan_id,
            source=source,
            strategy_name=strategy_name
        )
        
        # 7. 执行卖出
        order_value = quantity * price
        commission = max(order_value * 0.0003, 5)  # 万三手续费，最低5元
        stamp_tax = order_value * 0.001  # 印花税千一
        total_receive = order_value - commission - stamp_tax
        
        # 计算盈亏
        profit = (price - pos.cost_price) * quantity
        
        # 更新账户
        self.account.available_cash += total_receive
        self.account.market_value -= pos.cost_price * quantity
        self.account.today_profit += profit
        self.account.total_profit += profit
        self.account.total_assets = self.account.available_cash + self.account.market_value
        
        # 更新持仓
        pos.quantity -= quantity
        pos.available_quantity -= quantity
        pos.update_price(price)
        
        if pos.quantity <= 0:
            del self.positions[stock_code]
        
        # 更新订单状态
        order.filled_quantity = quantity
        order.filled_price = price
        order.status = OrderStatus.FILLED
        order.update_time = datetime.now()
        
        self.order_history.append(order)
        
        # 记录交易
        trade_record = {
            "time": datetime.now().isoformat(),
            "stock_code": stock_code,
            "stock_name": pos.stock_name,
            "direction": "SELL",
            "quantity": quantity,
            "price": price,
            "amount": order_value,
            "commission": commission,
            "stamp_tax": stamp_tax,
            "profit": profit,
            "order_id": order.order_id
        }
        self.trade_history.append(trade_record)
        
        # 保存数据
        self._save_data()
        
        logger.info(f"卖出成功: {stock_code} {quantity}股 @ {price}, 盈亏: {profit:.2f}")
        
        return True, "卖出成功", order.to_dict()
    
    def update_prices(self, prices: Dict[str, float]):
        """更新持仓价格"""
        for stock_code, price in prices.items():
            if stock_code in self.positions:
                self.positions[stock_code].update_price(price)
        
        # 重新计算账户市值
        self.account.market_value = sum(pos.market_value for pos in self.positions.values())
        self.account.total_assets = self.account.available_cash + self.account.market_value
        
        self._save_data()
    
    def daily_settlement(self):
        """每日结算（解冻T+1持仓）"""
        # 解冻持仓
        unfrozen = self.t_plus_one_manager.unfreeze_positions()
        
        # 更新持仓可卖数量
        for stock_code, pos in self.positions.items():
            frozen_qty = self.t_plus_one_manager.get_frozen_quantity(stock_code)
            pos.frozen_quantity = frozen_qty
            pos.available_quantity = pos.quantity - frozen_qty
        
        # 重置今日盈亏
        self.account.today_profit = 0
        
        self._save_data()
        
        logger.info(f"每日结算完成，解冻{unfrozen}笔持仓")
    
    def reset_account(self, initial_capital: float = 100000):
        """重置账户"""
        self.account = Account(
            account_id="virtual_001",
            total_assets=initial_capital,
            market_value=0,
            available_cash=initial_capital,
            frozen_cash=0,
            today_profit=0,
            total_profit=0
        )
        self.positions.clear()
        self.orders.clear()
        self.order_history.clear()
        self.trade_history.clear()
        self.t_plus_one_manager.frozen_positions.clear()
        
        self._save_data()
        
        logger.info(f"账户已重置，初始资金: {initial_capital}")


# 创建全局实例
virtual_trading_service = VirtualTradingService()


def get_virtual_trading_service() -> VirtualTradingService:
    """获取虚拟交易服务"""
    return virtual_trading_service