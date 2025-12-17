"""
策略回测引擎 (Strategy Backtester)
支持对10个策略进行历史数据回测和性能评估

核心功能：
1. 历史数据回测
2. 性能指标计算
3. 多策略对比
4. 回测报告生成
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class StrategyBacktester:
    """
    策略回测引擎
    
    支持功能：
    - 单策略回测
    - 多策略对比
    - 性能指标计算
    - 回测报告生成
    """
    
    def __init__(self, initial_capital: float = 100000.0):
        """
        初始化回测引擎
        
        Args:
            initial_capital: 初始资金（默认10万）
        """
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}  # 持仓
        self.trades = []  # 交易记录
        self.equity_curve = []  # 资金曲线
    
    def run_backtest(
        self,
        strategy,
        data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        运行单策略回测
        
        Args:
            strategy: 策略实例
            data: 历史数据（OHLCV）
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            回测结果字典
        """
        # 重置状态
        self._reset()
        
        # 筛选日期范围
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        if len(data) < 50:
            return {
                "success": False,
                "error": "数据不足，至少需要50个交易日"
            }
        
        logger.info(f"开始回测策略: {strategy.name}")
        logger.info(f"回测周期: {data.index[0]} 至 {data.index[-1]}")
        logger.info(f"初始资金: {self.initial_capital:,.2f}")
        
        # 生成交易信号
        try:
            signals = strategy.generate_signals(data)
            logger.info(f"生成 {len(signals)} 个交易信号")
        except Exception as e:
            logger.error(f"生成信号失败: {e}")
            return {
                "success": False,
                "error": f"生成信号失败: {str(e)}"
            }
        
        # 执行交易
        for signal in signals:
            self._execute_signal(signal, data)
        
        # 计算性能指标
        performance = self._calculate_performance(data)
        
        return {
            "success": True,
            "strategy_name": strategy.name,
            "strategy_id": strategy.__class__.__name__,
            "backtest_period": {
                "start": str(data.index[0]),
                "end": str(data.index[-1]),
                "days": len(data)
            },
            "performance": performance,
            "trades": self.trades,
            "equity_curve": self.equity_curve
        }
    
    def compare_strategies(
        self,
        strategies: List,
        data: pd.DataFrame,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        对比多个策略
        
        Args:
            strategies: 策略列表
            data: 历史数据
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            对比结果
        """
        results = []
        
        for strategy in strategies:
            result = self.run_backtest(strategy, data, start_date, end_date)
            if result["success"]:
                results.append(result)
        
        if not results:
            return {
                "success": False,
                "error": "所有策略回测失败"
            }
        
        # 生成对比分析
        comparison = self._generate_comparison(results)
        
        return {
            "success": True,
            "strategies_count": len(results),
            "backtest_period": results[0]["backtest_period"],
            "individual_results": results,
            "comparison": comparison
        }
    
    def _reset(self):
        """重置回测状态"""
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
    
    def _execute_signal(self, signal, data: pd.DataFrame):
        """
        执行交易信号
        
        Args:
            signal: 交易信号
            data: 历史数据
        """
        signal_date = signal.timestamp
        
        # 找到信号日期在数据中的位置
        if signal_date not in data.index:
            return
        
        signal_idx = data.index.get_loc(signal_date)
        
        # 获取下一个交易日的开盘价（模拟T+1）
        if signal_idx + 1 >= len(data):
            return
        
        next_day = data.index[signal_idx + 1]
        execution_price = data.loc[next_day, 'open']
        
        if signal.signal_type.value == "BUY":
            self._execute_buy(signal, execution_price, next_day)
        elif signal.signal_type.value == "SELL":
            self._execute_sell(signal, execution_price, next_day)
    
    def _execute_buy(self, signal, price: float, date):
        """执行买入"""
        # 计算可买入股数
        position_value = self.current_capital * signal.position_size
        shares = int(position_value / price / 100) * 100  # 100股整数倍
        
        if shares < 100:
            return  # 不足一手，不交易
        
        # 计算实际成本
        cost = shares * price
        commission = cost * 0.0003  # 万三佣金
        total_cost = cost + commission
        
        if total_cost > self.current_capital:
            return  # 资金不足
        
        # 更新持仓
        if signal.strategy_id not in self.positions:
            self.positions[signal.strategy_id] = {
                "shares": 0,
                "cost": 0,
                "entry_price": 0
            }
        
        position = self.positions[signal.strategy_id]
        position["shares"] += shares
        position["cost"] += total_cost
        position["entry_price"] = position["cost"] / position["shares"]
        
        # 更新资金
        self.current_capital -= total_cost
        
        # 记录交易
        self.trades.append({
            "date": date,
            "strategy": signal.strategy_id,
            "action": "BUY",
            "price": price,
            "shares": shares,
            "cost": total_cost,
            "commission": commission,
            "capital_after": self.current_capital
        })
    
    def _execute_sell(self, signal, price: float, date):
        """执行卖出"""
        if signal.strategy_id not in self.positions:
            return
        
        position = self.positions[signal.strategy_id]
        if position["shares"] == 0:
            return
        
        # 全部卖出
        shares = position["shares"]
        revenue = shares * price
        commission = revenue * 0.0003  # 万三佣金
        stamp_tax = revenue * 0.001  # 千一印花税
        total_revenue = revenue - commission - stamp_tax
        
        # 计算盈亏
        profit = total_revenue - position["cost"]
        profit_pct = profit / position["cost"]
        
        # 更新资金
        self.current_capital += total_revenue
        
        # 记录交易
        self.trades.append({
            "date": date,
            "strategy": signal.strategy_id,
            "action": "SELL",
            "price": price,
            "shares": shares,
            "revenue": total_revenue,
            "commission": commission,
            "stamp_tax": stamp_tax,
            "profit": profit,
            "profit_pct": profit_pct,
            "capital_after": self.current_capital
        })
        
        # 清空持仓
        position["shares"] = 0
        position["cost"] = 0
        position["entry_price"] = 0
    
    def _calculate_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        计算性能指标
        
        Returns:
            性能指标字典
        """
        if not self.trades:
            return {
                "total_return": 0,
                "total_return_pct": 0,
                "win_rate": 0,
                "total_trades": 0,
                "message": "无交易记录"
            }
        
        # 计算总收益
        total_return = self.current_capital - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        
        # 计算胜率
        profitable_trades = [t for t in self.trades if t.get("action") == "SELL" and t.get("profit", 0) > 0]
        total_sell_trades = [t for t in self.trades if t.get("action") == "SELL"]
        win_rate = len(profitable_trades) / len(total_sell_trades) if total_sell_trades else 0
        
        # 计算平均盈亏
        profits = [t["profit"] for t in total_sell_trades]
        avg_profit = np.mean(profits) if profits else 0
        avg_profit_pct = np.mean([t["profit_pct"] for t in total_sell_trades]) if total_sell_trades else 0
        
        # 计算最大回撤
        equity_curve = [self.initial_capital]
        for trade in self.trades:
            equity_curve.append(trade["capital_after"])
        
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # 计算夏普比率（简化版）
        if len(profits) > 1:
            returns = np.array([t["profit_pct"] for t in total_sell_trades])
            sharpe_ratio = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe_ratio = 0
        
        return {
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "final_capital": self.current_capital,
            "win_rate": win_rate,
            "total_trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t["action"] == "BUY"]),
            "sell_trades": len(total_sell_trades),
            "profitable_trades": len(profitable_trades),
            "avg_profit": avg_profit,
            "avg_profit_pct": avg_profit_pct,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe_ratio
        }
    
    def _calculate_max_drawdown(self, equity_curve: List[float]) -> float:
        """计算最大回撤"""
        if not equity_curve:
            return 0
        
        peak = equity_curve[0]
        max_dd = 0
        
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def _generate_comparison(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        生成策略对比分析
        
        Args:
            results: 各策略回测结果列表
            
        Returns:
            对比分析结果
        """
        # 提取关键指标
        comparison_data = []
        for result in results:
            perf = result["performance"]
            comparison_data.append({
                "strategy_name": result["strategy_name"],
                "total_return_pct": perf["total_return_pct"],
                "win_rate": perf["win_rate"],
                "sharpe_ratio": perf["sharpe_ratio"],
                "max_drawdown": perf["max_drawdown"],
                "total_trades": perf["total_trades"]
            })
        
        # 排序
        by_return = sorted(comparison_data, key=lambda x: x["total_return_pct"], reverse=True)
        by_win_rate = sorted(comparison_data, key=lambda x: x["win_rate"], reverse=True)
        by_sharpe = sorted(comparison_data, key=lambda x: x["sharpe_ratio"], reverse=True)
        
        return {
            "best_return": by_return[0] if by_return else None,
            "best_win_rate": by_win_rate[0] if by_win_rate else None,
            "best_sharpe": by_sharpe[0] if by_sharpe else None,
            "ranking_by_return": by_return,
            "ranking_by_win_rate": by_win_rate,
            "ranking_by_sharpe": by_sharpe
        }
