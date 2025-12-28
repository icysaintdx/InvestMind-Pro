"""
回测性能指标计算模块
"""

import pandas as pd
import numpy as np
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class PerformanceMetrics:
    """性能指标"""
    # 收益指标
    total_return: float          # 总收益率
    annual_return: float         # 年化收益率
    monthly_return: float        # 月均收益率
    
    # 风险指标
    max_drawdown: float          # 最大回撤
    max_drawdown_duration: int   # 最大回撤持续天数
    volatility: float            # 波动率（年化）
    downside_deviation: float    # 下行标准差
    
    # 风险调整收益
    sharpe_ratio: float          # 夏普比率
    sortino_ratio: float         # 索提诺比率
    calmar_ratio: float          # 卡尔玛比率
    information_ratio: float     # 信息比率
    
    # 交易统计
    total_trades: int            # 总交易次数
    winning_trades: int          # 盈利交易次数
    losing_trades: int           # 亏损交易次数
    win_rate: float              # 胜率
    profit_factor: float         # 盈亏比
    avg_win: float               # 平均盈利
    avg_loss: float              # 平均亏损
    largest_win: float           # 最大单笔盈利
    largest_loss: float          # 最大单笔亏损
    avg_holding_days: float      # 平均持仓天数
    
    # 相对指标
    benchmark_return: float      # 基准收益率
    alpha: float                 # 超额收益
    beta: float                  # 贝塔系数
    correlation: float           # 相关系数
    
    def to_dict(self) -> Dict:
        """转换为字典 - 返回原始数值，前端负责格式化显示"""
        import math

        def safe_float(val, default=0):
            """处理inf和nan值"""
            if val is None or (isinstance(val, float) and (math.isnan(val) or math.isinf(val))):
                return default
            return val

        return {
            # 收益指标 - 返回小数形式（如0.1234表示12.34%）
            "total_return": round(safe_float(self.total_return), 4),
            "annual_return": round(safe_float(self.annual_return), 4),
            "monthly_return": round(safe_float(self.monthly_return), 4),

            # 风险指标
            "max_drawdown": round(safe_float(self.max_drawdown), 4),
            "max_drawdown_duration": self.max_drawdown_duration,
            "volatility": round(safe_float(self.volatility), 4),
            "downside_deviation": round(safe_float(self.downside_deviation), 4),

            # 风险调整收益
            "sharpe_ratio": round(safe_float(self.sharpe_ratio), 2),
            "sortino_ratio": round(safe_float(self.sortino_ratio), 2),
            "calmar_ratio": round(safe_float(self.calmar_ratio), 2),
            "information_ratio": round(safe_float(self.information_ratio), 2),

            # 交易统计
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": round(safe_float(self.win_rate), 4),
            "profit_factor": round(safe_float(self.profit_factor, 999.99), 2),  # inf时返回999.99
            "avg_win": round(safe_float(self.avg_win), 2),
            "avg_loss": round(safe_float(self.avg_loss), 2),
            "largest_win": round(safe_float(self.largest_win), 2),
            "largest_loss": round(safe_float(self.largest_loss), 2),
            "avg_holding_days": round(safe_float(self.avg_holding_days), 1),

            # 相对指标
            "benchmark_return": round(safe_float(self.benchmark_return), 4),
            "alpha": round(safe_float(self.alpha), 4),
            "beta": round(safe_float(self.beta), 2),
            "correlation": round(safe_float(self.correlation), 2),

            # 同时提供格式化版本供直接显示
            "total_return_formatted": f"{safe_float(self.total_return):.2%}",
            "annual_return_formatted": f"{safe_float(self.annual_return):.2%}",
            "max_drawdown_formatted": f"{safe_float(self.max_drawdown):.2%}",
            "win_rate_formatted": f"{safe_float(self.win_rate):.2%}"
        }


class MetricsCalculator:
    """指标计算器"""
    
    def __init__(self, risk_free_rate: float = 0.03):
        """
        初始化
        Args:
            risk_free_rate: 无风险利率（年化）
        """
        self.risk_free_rate = risk_free_rate
    
    def calculate_metrics(
        self,
        equity_curve: pd.DataFrame,
        trades: List,
        initial_capital: float,
        benchmark_returns: Optional[pd.Series] = None
    ) -> PerformanceMetrics:
        """
        计算所有性能指标
        
        Args:
            equity_curve: 净值曲线
            trades: 交易记录
            initial_capital: 初始资金
            benchmark_returns: 基准收益率序列
        
        Returns:
            性能指标
        """
        # 计算收益序列
        returns = equity_curve['portfolio_value'].pct_change().dropna()
        
        # 计算总收益率
        total_return = (equity_curve['portfolio_value'].iloc[-1] / initial_capital) - 1
        
        # 计算年化收益率
        days = (equity_curve.index[-1] - equity_curve.index[0]).days
        years = days / 365.25
        annual_return = (1 + total_return) ** (1 / years) - 1 if years > 0 else 0
        
        # 计算月均收益率
        monthly_return = returns.resample('M').apply(lambda x: (1 + x).prod() - 1).mean()
        
        # 计算最大回撤
        drawdown_data = self.calculate_drawdown(equity_curve['portfolio_value'])
        max_drawdown = drawdown_data['drawdown'].min()
        max_drawdown_duration = self._calculate_max_drawdown_duration(drawdown_data)
        
        # 计算波动率
        volatility = returns.std() * np.sqrt(252)  # 年化波动率
        
        # 计算下行标准差
        downside_returns = returns[returns < 0]
        downside_deviation = downside_returns.std() * np.sqrt(252) if len(downside_returns) > 0 else 0
        
        # 计算夏普比率
        excess_return = annual_return - self.risk_free_rate
        sharpe_ratio = excess_return / volatility if volatility > 0 else 0
        
        # 计算索提诺比率
        sortino_ratio = excess_return / downside_deviation if downside_deviation > 0 else 0
        
        # 计算卡尔玛比率
        calmar_ratio = annual_return / abs(max_drawdown) if max_drawdown != 0 else 0
        
        # 计算交易统计
        trade_stats = self._calculate_trade_statistics(trades, initial_capital)
        
        # 计算相对指标
        relative_metrics = self._calculate_relative_metrics(
            returns,
            benchmark_returns
        ) if benchmark_returns is not None else {
            'benchmark_return': 0,
            'alpha': 0,
            'beta': 0,
            'correlation': 0,
            'information_ratio': 0
        }
        
        return PerformanceMetrics(
            # 收益指标
            total_return=total_return,
            annual_return=annual_return,
            monthly_return=monthly_return,
            
            # 风险指标
            max_drawdown=max_drawdown,
            max_drawdown_duration=max_drawdown_duration,
            volatility=volatility,
            downside_deviation=downside_deviation,
            
            # 风险调整收益
            sharpe_ratio=sharpe_ratio,
            sortino_ratio=sortino_ratio,
            calmar_ratio=calmar_ratio,
            information_ratio=relative_metrics.get('information_ratio', 0),
            
            # 交易统计
            **trade_stats,
            
            # 相对指标
            benchmark_return=relative_metrics.get('benchmark_return', 0),
            alpha=relative_metrics.get('alpha', 0),
            beta=relative_metrics.get('beta', 0),
            correlation=relative_metrics.get('correlation', 0)
        )
    
    def calculate_drawdown(self, equity_series: pd.Series) -> pd.DataFrame:
        """计算回撤序列"""
        # 计算累计最高值
        cummax = equity_series.expanding().max()
        
        # 计算回撤
        drawdown = (equity_series - cummax) / cummax
        
        return pd.DataFrame({
            'equity': equity_series,
            'cummax': cummax,
            'drawdown': drawdown
        })
    
    def _calculate_max_drawdown_duration(self, drawdown_data: pd.DataFrame) -> int:
        """计算最大回撤持续时间"""
        # 找出所有回撤期
        in_drawdown = drawdown_data['drawdown'] < 0
        
        # 计算连续回撤天数
        max_duration = 0
        current_duration = 0
        
        for is_dd in in_drawdown:
            if is_dd:
                current_duration += 1
                max_duration = max(max_duration, current_duration)
            else:
                current_duration = 0
        
        return max_duration
    
    def _calculate_trade_statistics(
        self,
        trades: List,
        initial_capital: float
    ) -> Dict:
        """计算交易统计"""
        if not trades:
            return {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'avg_holding_days': 0
            }
        
        # 配对交易（买入-卖出）
        paired_trades = self._pair_trades(trades)
        
        if not paired_trades:
            return {
                'total_trades': len(trades),
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'avg_win': 0,
                'avg_loss': 0,
                'largest_win': 0,
                'largest_loss': 0,
                'avg_holding_days': 0
            }
        
        # 计算每笔交易的盈亏
        pnls = []
        holding_days = []
        
        for pair in paired_trades:
            buy_trade = pair['buy']
            sell_trade = pair['sell']
            
            # 计算盈亏
            pnl = (sell_trade.price - buy_trade.price) * sell_trade.quantity
            pnl -= buy_trade.commission + sell_trade.commission
            pnl -= buy_trade.slippage + sell_trade.slippage
            pnls.append(pnl)
            
            # 计算持仓天数
            days = (sell_trade.timestamp - buy_trade.timestamp).days
            holding_days.append(days)
        
        # 统计
        winning_pnls = [p for p in pnls if p > 0]
        losing_pnls = [p for p in pnls if p < 0]
        
        total_trades = len(pnls)
        winning_trades = len(winning_pnls)
        losing_trades = len(losing_pnls)
        
        win_rate = winning_trades / total_trades if total_trades > 0 else 0
        
        total_win = sum(winning_pnls) if winning_pnls else 0
        total_loss = abs(sum(losing_pnls)) if losing_pnls else 0
        profit_factor = total_win / total_loss if total_loss > 0 else float('inf')
        
        avg_win = np.mean(winning_pnls) if winning_pnls else 0
        avg_loss = abs(np.mean(losing_pnls)) if losing_pnls else 0
        
        largest_win = max(winning_pnls) if winning_pnls else 0
        largest_loss = abs(min(losing_pnls)) if losing_pnls else 0
        
        avg_holding_days = np.mean(holding_days) if holding_days else 0
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'largest_win': largest_win,
            'largest_loss': largest_loss,
            'avg_holding_days': avg_holding_days
        }
    
    def _pair_trades(self, trades: List) -> List[Dict]:
        """配对买入和卖出交易"""
        paired = []
        buy_trades = {}
        
        for trade in trades:
            if trade.side == 'buy':
                if trade.stock_code not in buy_trades:
                    buy_trades[trade.stock_code] = []
                buy_trades[trade.stock_code].append(trade)
            
            elif trade.side == 'sell':
                if trade.stock_code in buy_trades and buy_trades[trade.stock_code]:
                    buy_trade = buy_trades[trade.stock_code].pop(0)
                    paired.append({
                        'buy': buy_trade,
                        'sell': trade
                    })
        
        return paired
    
    def _calculate_relative_metrics(
        self,
        returns: pd.Series,
        benchmark_returns: pd.Series
    ) -> Dict:
        """计算相对指标"""
        # 对齐数据
        aligned_returns = returns.align(benchmark_returns, join='inner')
        strategy_returns = aligned_returns[0]
        bench_returns = aligned_returns[1]
        
        if len(strategy_returns) == 0:
            return {
                'benchmark_return': 0,
                'alpha': 0,
                'beta': 0,
                'correlation': 0,
                'information_ratio': 0
            }
        
        # 基准总收益
        benchmark_return = (1 + bench_returns).prod() - 1
        
        # 计算beta和alpha
        covariance = strategy_returns.cov(bench_returns)
        benchmark_variance = bench_returns.var()
        
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0
        
        # 年化收益率
        strategy_annual = strategy_returns.mean() * 252
        benchmark_annual = bench_returns.mean() * 252
        
        # Alpha
        alpha = strategy_annual - (self.risk_free_rate + beta * (benchmark_annual - self.risk_free_rate))
        
        # 相关系数
        correlation = strategy_returns.corr(bench_returns)
        
        # 信息比率
        active_returns = strategy_returns - bench_returns
        tracking_error = active_returns.std() * np.sqrt(252)
        information_ratio = (strategy_annual - benchmark_annual) / tracking_error if tracking_error > 0 else 0
        
        return {
            'benchmark_return': benchmark_return,
            'alpha': alpha,
            'beta': beta,
            'correlation': correlation,
            'information_ratio': information_ratio
        }


def create_metrics_calculator(risk_free_rate: float = 0.03) -> MetricsCalculator:
    """创建指标计算器实例"""
    return MetricsCalculator(risk_free_rate)
