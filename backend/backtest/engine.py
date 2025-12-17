"""
回测引擎核心模块
实现历史数据回测逻辑
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import logging

from ..strategies.base import BaseStrategy, StrategySignal, SignalType
from ..trading.market_rules import MarketRuleEngine, MarketType
from .metrics import MetricsCalculator, PerformanceMetrics

logger = logging.getLogger(__name__)


@dataclass
class BacktestConfig:
    """回测配置"""
    initial_capital: float = 100000.0      # 初始资金
    commission_rate: float = 0.0003        # 手续费率
    slippage_rate: float = 0.0005          # 滑点
    start_date: str = None                 # 开始日期
    end_date: str = None                   # 结束日期
    benchmark: str = "000001.SH"           # 基准指数
    position_sizing: str = "fixed"         # 仓位管理（fixed/kelly/risk_parity）
    max_position_pct: float = 0.3          # 最大仓位比例
    use_ai_agents: bool = False            # 是否使用AI智能体
    ai_agent_names: List[str] = field(default_factory=list)  # AI智能体列表


@dataclass
class Trade:
    """交易记录"""
    trade_id: str
    timestamp: datetime
    stock_code: str
    side: str               # buy/sell
    price: float
    quantity: int
    commission: float
    slippage: float
    total_cost: float
    signal: StrategySignal
    portfolio_value: float  # 交易后组合价值


@dataclass 
class Position:
    """持仓记录"""
    stock_code: str
    quantity: int
    avg_price: float
    current_price: float
    entry_time: datetime
    unrealized_pnl: float
    realized_pnl: float


@dataclass
class BacktestResult:
    """回测结果"""
    # 基本信息
    start_date: datetime
    end_date: datetime
    initial_capital: float
    final_capital: float
    
    # 交易记录
    trades: List[Trade]
    positions: Dict[str, Position]
    
    # 性能指标
    metrics: PerformanceMetrics
    
    # 净值曲线
    equity_curve: pd.DataFrame
    drawdown_curve: pd.DataFrame
    
    # 详细分析
    monthly_returns: pd.DataFrame
    trade_analysis: Dict[str, Any]
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "summary": {
                "start_date": self.start_date.isoformat(),
                "end_date": self.end_date.isoformat(),
                "initial_capital": self.initial_capital,
                "final_capital": self.final_capital,
                "total_return": (self.final_capital - self.initial_capital) / self.initial_capital,
                "total_trades": len(self.trades)
            },
            "metrics": self.metrics.to_dict(),
            "equity_curve": self.equity_curve.to_dict(),
            "trade_analysis": self.trade_analysis
        }


class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.market_rules = MarketRuleEngine()
        self.metrics_calculator = MetricsCalculator()
        
        # 账户状态
        self.cash = config.initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve = []
        
        # AI智能体（可选）
        self.ai_agents = None
        if config.use_ai_agents:
            self._init_ai_agents()
    
    def _init_ai_agents(self):
        """初始化AI智能体"""
        # TODO: 集成AI智能体系统
        pass
    
    def run(
        self,
        strategy: BaseStrategy,
        data: pd.DataFrame,
        stock_code: str
    ) -> BacktestResult:
        """运行回测"""
        logger.info(f"开始回测 {stock_code}，策略：{strategy.name}")
        
        # 数据预处理
        data = self._preprocess_data(data)
        
        # 初始化策略
        strategy.initialize(data)
        
        # 检测市场类型
        market_type = self.market_rules.detect_market(stock_code)
        
        # 逐行回测
        for idx in range(30, len(data)):  # 从的30行开始，确保有足够的历史数据
            current_data = data.iloc[:idx+1]
            current_bar = data.iloc[idx]
                    
            # 更新持仓价值
            self._update_positions(current_bar['close'])
                    
            # 获取当前仓位
            current_position = self.positions.get(stock_code, None)
            current_qty = current_position.quantity if current_position else 0
                    
            # 生成信号
            signal = strategy.generate_signal(current_data, current_qty)
                        
            # 检查signal是否为None
            if signal is None:
                logger.warning(f"[策略 {strategy.name}] 在 {current_bar.name} 返回None，跳过")
                signal = StrategySignal(
                    signal_type=SignalType.HOLD,
                    confidence=0.0,
                    reason="策略返回None"
                )
                        
            # 调试日志：记录信号
            if idx % 20 == 0 or signal.signal_type != SignalType.HOLD:
                logger.info(f"[{current_bar.name}] 信号: {signal.signal_type.value}, 置信度: {signal.confidence:.2f}, 原因: {signal.reasons if hasattr(signal, 'reasons') else signal.reason}")
            
            # AI增强（可选）
            if self.config.use_ai_agents and self.ai_agents:
                signal = self._enhance_signal_with_ai(signal, current_data, stock_code)
            
            # 执行交易
            if signal.signal_type in [SignalType.BUY, SignalType.STRONG_BUY]:
                self._execute_buy(
                    stock_code,
                    current_bar,
                    signal,
                    market_type
                )
            elif signal.signal_type in [SignalType.SELL, SignalType.STRONG_SELL]:
                self._execute_sell(
                    stock_code,
                    current_bar,
                    signal,
                    market_type
                )
            
            # 记录净值
            portfolio_value = self._calculate_portfolio_value(current_bar['close'])
            self.equity_curve.append({
                'date': current_bar.name,
                'portfolio_value': portfolio_value,
                'cash': self.cash,
                'positions_value': portfolio_value - self.cash,
                'signal': signal.signal_type.value
            })
        
        # 计算性能指标
        result = self._calculate_results(data, stock_code)
        
        logger.info(f"回测完成，总收益率：{result.metrics.total_return:.2%}")
        
        return result
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """数据预处理"""
        # 确保索引是日期
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)
        
        # 按日期过滤
        if self.config.start_date:
            data = data[data.index >= self.config.start_date]
        if self.config.end_date:
            data = data[data.index <= self.config.end_date]
        
        return data
    
    def _execute_buy(
        self,
        stock_code: str,
        bar: pd.Series,
        signal: StrategySignal,
        market_type: MarketType
    ):
        """执行买入"""
        price = bar['close']
        
        # 计算买入数量
        position_size = self._calculate_position_size(
            price,
            signal,
            market_type
        )
        
        if position_size <= 0:
            return
        
        # 计算成本
        trade_value = price * position_size
        slippage = trade_value * self.config.slippage_rate
        commission = self.market_rules.calculate_commission(
            market_type,
            'buy',
            trade_value
        )
        total_cost = trade_value + slippage + commission
        
        # 检查资金是否足够
        if total_cost > self.cash:
            # 调整数量
            available_value = self.cash * 0.98  # 留2%缓冲
            position_size = int(available_value / price / 100) * 100
            if position_size <= 0:
                return
            
            trade_value = price * position_size
            slippage = trade_value * self.config.slippage_rate
            commission = self.market_rules.calculate_commission(
                market_type,
                'buy',
                trade_value
            )
            total_cost = trade_value + slippage + commission
        
        # 执行交易
        self.cash -= total_cost
        
        # 更新持仓
        if stock_code in self.positions:
            position = self.positions[stock_code]
            # 加仓
            total_qty = position.quantity + position_size
            position.avg_price = (
                (position.avg_price * position.quantity + price * position_size) /
                total_qty
            )
            position.quantity = total_qty
        else:
            # 新建仓位
            self.positions[stock_code] = Position(
                stock_code=stock_code,
                quantity=position_size,
                avg_price=price,
                current_price=price,
                entry_time=bar.name,
                unrealized_pnl=0,
                realized_pnl=0
            )
        
        # 记录交易
        trade = Trade(
            trade_id=f"T{len(self.trades)+1:04d}",
            timestamp=bar.name,
            stock_code=stock_code,
            side='buy',
            price=price,
            quantity=position_size,
            commission=commission,
            slippage=slippage,
            total_cost=total_cost,
            signal=signal,
            portfolio_value=self._calculate_portfolio_value(price)
        )
        self.trades.append(trade)
        
        logger.info(f"买入 {stock_code}: {position_size}股 @ {price:.2f}, 成本: {total_cost:.2f}")
    
    def _execute_sell(
        self,
        stock_code: str,
        bar: pd.Series,
        signal: StrategySignal,
        market_type: MarketType
    ):
        """执行卖出"""
        if stock_code not in self.positions:
            return
        
        position = self.positions[stock_code]
        if position.quantity <= 0:
            return
        
        price = bar['close']
        
        # 确定卖出数量
        if signal.signal_type == SignalType.STRONG_SELL:
            sell_qty = position.quantity  # 全部卖出
        else:
            sell_qty = position.quantity // 2  # 卖出一半
            sell_qty = max(sell_qty, 100)  # 至少100股
            sell_qty = min(sell_qty, position.quantity)
        
        # 计算收入
        trade_value = price * sell_qty
        slippage = trade_value * self.config.slippage_rate
        commission = self.market_rules.calculate_commission(
            market_type,
            'sell',
            trade_value
        )
        net_proceeds = trade_value - slippage - commission
        
        # 执行交易
        self.cash += net_proceeds
        
        # 计算盈亏
        realized_pnl = (price - position.avg_price) * sell_qty - commission - slippage
        position.realized_pnl += realized_pnl
        
        # 更新持仓
        position.quantity -= sell_qty
        if position.quantity <= 0:
            del self.positions[stock_code]
        
        # 记录交易
        trade = Trade(
            trade_id=f"T{len(self.trades)+1:04d}",
            timestamp=bar.name,
            stock_code=stock_code,
            side='sell',
            price=price,
            quantity=sell_qty,
            commission=commission,
            slippage=slippage,
            total_cost=-net_proceeds,  # 负数表示收入
            signal=signal,
            portfolio_value=self._calculate_portfolio_value(price)
        )
        self.trades.append(trade)
        
        logger.info(f"卖出 {stock_code}: {sell_qty}股 @ {price:.2f}, 盈亏: {realized_pnl:.2f}")
    
    def _calculate_position_size(
        self,
        price: float,
        signal: StrategySignal,
        market_type: MarketType
    ) -> int:
        """计算仓位大小"""
        portfolio_value = self._calculate_portfolio_value(price)
        
        # 基于信号强度的仓位
        if signal.signal_type == SignalType.STRONG_BUY:
            position_pct = self.config.max_position_pct
        else:
            position_pct = self.config.max_position_pct * 0.6
        
        # 考虑置信度
        position_pct *= signal.confidence
        
        # 计算数量
        position_value = portfolio_value * position_pct
        quantity = int(position_value / price)
        
        # 调整为手数
        rule = self.market_rules.get_rule(market_type)
        quantity = (quantity // rule.lot_size) * rule.lot_size
        
        final_qty = max(quantity, rule.lot_size)
        
        logger.info(f"仓位计算: 组合价值={portfolio_value:.2f}, 信号={signal.signal_type.value}, "
                   f"置信度={signal.confidence:.2f}, 仓位比={position_pct:.2%}, 数量={final_qty}")
        
        return final_qty
    
    def _update_positions(self, current_price: float):
        """更新持仓价值"""
        for position in self.positions.values():
            position.current_price = current_price
            position.unrealized_pnl = (
                (current_price - position.avg_price) * position.quantity
            )
    
    def _calculate_portfolio_value(self, current_price: float) -> float:
        """计算组合价值"""
        positions_value = sum(
            pos.quantity * current_price
            for pos in self.positions.values()
        )
        return self.cash + positions_value
    
    def _enhance_signal_with_ai(
        self,
        signal: StrategySignal,
        data: pd.DataFrame,
        stock_code: str
    ) -> StrategySignal:
        """使用AI智能体增强信号"""
        # TODO: 调用AI智能体系统
        return signal
    
    def _calculate_results(
        self,
        data: pd.DataFrame,
        stock_code: str
    ) -> BacktestResult:
        """计算回测结果"""
        # 创建净值曲线DataFrame
        equity_df = pd.DataFrame(self.equity_curve)
        equity_df.set_index('date', inplace=True)
        
        # 计算回撤
        drawdown_df = self.metrics_calculator.calculate_drawdown(equity_df['portfolio_value'])
        
        # 计算性能指标
        metrics = self.metrics_calculator.calculate_metrics(
            equity_df,
            self.trades,
            self.config.initial_capital
        )
        
        # 交易分析
        trade_analysis = self._analyze_trades()
        
        # 月度收益
        monthly_returns = self._calculate_monthly_returns(equity_df)
        
        return BacktestResult(
            start_date=equity_df.index[0],
            end_date=equity_df.index[-1],
            initial_capital=self.config.initial_capital,
            final_capital=equity_df['portfolio_value'].iloc[-1],
            trades=self.trades,
            positions=self.positions,
            metrics=metrics,
            equity_curve=equity_df,
            drawdown_curve=drawdown_df,
            monthly_returns=monthly_returns,
            trade_analysis=trade_analysis
        )
    
    def _analyze_trades(self) -> Dict[str, Any]:
        """分析交易"""
        if not self.trades:
            return {}
        
        buy_trades = [t for t in self.trades if t.side == 'buy']
        sell_trades = [t for t in self.trades if t.side == 'sell']
        
        return {
            "total_trades": len(self.trades),
            "buy_trades": len(buy_trades),
            "sell_trades": len(sell_trades),
            "avg_buy_price": np.mean([t.price for t in buy_trades]) if buy_trades else 0,
            "avg_sell_price": np.mean([t.price for t in sell_trades]) if sell_trades else 0,
            "total_commission": sum(t.commission for t in self.trades),
            "total_slippage": sum(t.slippage for t in self.trades),
            "trade_frequency": len(self.trades) / len(self.equity_curve) if self.equity_curve else 0
        }
    
    def _calculate_monthly_returns(self, equity_df: pd.DataFrame) -> pd.DataFrame:
        """计算月度收益"""
        monthly_equity = equity_df['portfolio_value'].resample('M').last()
        monthly_returns = monthly_equity.pct_change()
        
        return pd.DataFrame({
            'return': monthly_returns,
            'cumulative': (1 + monthly_returns).cumprod() - 1
        })


def create_backtest_engine(config: Optional[BacktestConfig] = None) -> BacktestEngine:
    """创建回测引擎实例"""
    if config is None:
        config = BacktestConfig()
    return BacktestEngine(config)
