"""
多策略组合交易系统 - Multi-Strategy Ensemble System

策略架构:
1. EMA趋势跟踪 (权重40%) - 趋势方向确认
2. RSI动量过滤 (权重25%) - 超买超卖过滤  
3. 布林带波动率 (权重20%) - 突破/均值回归
4. 成交量确认 (权重15%) - 信号有效性验证

信号合成方法: 加权投票制
- 总分 >= 70: 强烈买入
- 总分 >= 60: 买入
- 总分 <= 30: 强烈卖出
- 总分 <= 40: 卖出
- 其他: 观望

作者: InvestMindPro Team
版本: 1.0.0
日期: 2026-02-28
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

# 添加项目路径
sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace/InvestMindPro')
from strategies.ema_v2 import EMAV2Strategy, BacktestResult


class SignalStrength(Enum):
    """信号强度枚举"""
    STRONG_BUY = 4    # 强烈买入
    BUY = 3           # 买入
    HOLD = 2          # 观望
    SELL = 1          # 卖出
    STRONG_SELL = 0   # 强烈卖出


@dataclass
class ComponentSignal:
    """组件策略信号"""
    name: str           # 策略名称
    signal: int         # 信号值 (0-4)
    weight: float       # 权重
    confidence: float   # 置信度 (0-1)
    details: Dict       # 详细信息


@dataclass
class EnsembleResult:
    """组合策略结果"""
    symbol: str
    total_return: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Dict]
    params: Dict
    component_signals: List[ComponentSignal]  # 各组件信号详情
    signal_history: List[Dict]  # 历史信号记录


class RSIStrategy:
    """RSI动量策略"""
    
    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70):
        self.period = period
        self.oversold = oversold
        self.overbought = overbought
    
    def calculate_rsi(self, data: pd.Series) -> pd.Series:
        """计算RSI"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成RSI信号"""
        data = df.copy()
        data['rsi'] = self.calculate_rsi(data['close'])
        
        # 信号生成
        # RSI < 30 (超卖) -> 买入信号
        # RSI > 70 (超买) -> 卖出信号
        data['rsi_signal'] = 2  # 默认观望
        data.loc[data['rsi'] < self.oversold, 'rsi_signal'] = 3  # 买入
        data.loc[data['rsi'] > self.overbought, 'rsi_signal'] = 1  # 卖出
        
        # 金叉/死叉 (RSI上穿30或下穿70)
        data['rsi_cross_up'] = (data['rsi'] > self.oversold) & (data['rsi'].shift(1) <= self.oversold)
        data['rsi_cross_down'] = (data['rsi'] < self.overbought) & (data['rsi'].shift(1) >= self.overbought)
        
        return data
    
    def get_signal_strength(self, df: pd.DataFrame, idx: int) -> Tuple[int, float, Dict]:
        """获取当前信号强度和置信度"""
        rsi = df['rsi'].iloc[idx]
        
        if rsi < 20:  # 极度超卖
            return 4, 0.9, {'rsi': rsi, 'extreme': True}
        elif rsi < 30:  # 超卖
            return 3, 0.7, {'rsi': rsi}
        elif rsi > 80:  # 极度超买
            return 0, 0.9, {'rsi': rsi, 'extreme': True}
        elif rsi > 70:  # 超买
            return 1, 0.7, {'rsi': rsi}
        else:
            return 2, 0.5, {'rsi': rsi}


class BollingerStrategy:
    """布林带策略"""
    
    def __init__(self, period: int = 20, std_dev: float = 2.0):
        self.period = period
        self.std_dev = std_dev
    
    def calculate_bollinger(self, df: pd.DataFrame) -> pd.DataFrame:
        """计算布林带"""
        data = df.copy()
        data['bb_middle'] = data['close'].rolling(window=self.period).mean()
        data['bb_std'] = data['close'].rolling(window=self.period).std()
        data['bb_upper'] = data['bb_middle'] + self.std_dev * data['bb_std']
        data['bb_lower'] = data['bb_middle'] - self.std_dev * data['bb_std']
        data['bb_width'] = (data['bb_upper'] - data['bb_lower']) / data['bb_middle']
        data['bb_position'] = (data['close'] - data['bb_lower']) / (data['bb_upper'] - data['bb_lower'])
        return data
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成布林带信号"""
        data = self.calculate_bollinger(df)
        
        # 信号生成
        # 价格跌破下轨 -> 买入 (均值回归)
        # 价格突破上轨 -> 卖出 (均值回归)
        # 价格从中轨向上突破 -> 买入 (趋势跟踪)
        # 价格从中轨向下跌破 -> 卖出 (趋势跟踪)
        
        data['bb_signal'] = 2  # 默认观望
        
        # 均值回归信号
        data.loc[data['close'] < data['bb_lower'], 'bb_signal'] = 3  # 买入
        data.loc[data['close'] > data['bb_upper'], 'bb_signal'] = 1  # 卖出
        
        # 布林带收窄 (波动率收缩，预示大行情)
        data['bb_squeeze'] = data['bb_width'] < data['bb_width'].rolling(window=50).mean() * 0.85
        
        return data
    
    def get_signal_strength(self, df: pd.DataFrame, idx: int) -> Tuple[int, float, Dict]:
        """获取当前信号强度和置信度"""
        position = df['bb_position'].iloc[idx]
        width = df['bb_width'].iloc[idx]
        squeeze = df['bb_squeeze'].iloc[idx]
        
        details = {'position': position, 'width': width, 'squeeze': squeeze}
        
        if position < 0:  # 跌破下轨
            return 4, 0.85, details
        elif position < 0.2:
            return 3, 0.65, details
        elif position > 1:  # 突破上轨
            return 0, 0.85, details
        elif position > 0.8:
            return 1, 0.65, details
        else:
            return 2, 0.4, details


class VolumeStrategy:
    """成交量确认策略"""
    
    def __init__(self, short_period: int = 5, long_period: int = 20):
        self.short_period = short_period
        self.long_period = long_period
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成成交量信号"""
        data = df.copy()
        
        # 成交量均线
        data['vol_short'] = data['volume'].rolling(window=self.short_period).mean()
        data['vol_long'] = data['volume'].rolling(window=self.long_period).mean()
        
        # 成交量比率
        data['vol_ratio'] = data['vol_short'] / data['vol_long']
        
        # 价量配合
        data['price_change'] = data['close'].pct_change()
        data['volume_trend'] = np.where(
            (data['price_change'] > 0) & (data['vol_ratio'] > 1.2),
            3,  # 放量上涨 - 强势
            np.where(
                (data['price_change'] < 0) & (data['vol_ratio'] > 1.2),
                1,  # 放量下跌 - 弱势
                np.where(
                    (data['price_change'] > 0) & (data['vol_ratio'] < 0.8),
                    1,  # 缩量上涨 - 弱势
                    np.where(
                        (data['price_change'] < 0) & (data['vol_ratio'] < 0.8),
                        3,  # 缩量下跌 - 可能反转
                        2
                    )
                )
            )
        )
        
        return data
    
    def get_signal_strength(self, df: pd.DataFrame, idx: int) -> Tuple[int, float, Dict]:
        """获取当前信号强度和置信度"""
        vol_ratio = df['vol_ratio'].iloc[idx]
        price_change = df['price_change'].iloc[idx]
        
        details = {'vol_ratio': vol_ratio, 'price_change': price_change}
        
        if vol_ratio > 1.5 and price_change > 0:
            return 4, 0.8, details  # 放量大涨
        elif vol_ratio > 1.2 and price_change > 0:
            return 3, 0.6, details  # 放量上涨
        elif vol_ratio > 1.5 and price_change < 0:
            return 0, 0.8, details  # 放量大跌
        elif vol_ratio > 1.2 and price_change < 0:
            return 1, 0.6, details  # 放量下跌
        else:
            return 2, 0.3, details  # 观望


class MultiStrategyEnsemble:
    """多策略组合系统"""
    
    # 默认权重配置
    DEFAULT_WEIGHTS = {
        'ema': 0.40,
        'rsi': 0.25,
        'bollinger': 0.20,
        'volume': 0.15
    }
    
    # 信号阈值
    THRESHOLDS = {
        'strong_buy': 70,
        'buy': 60,
        'sell': 40,
        'strong_sell': 30
    }
    
    def __init__(self, weights: Optional[Dict] = None, ema_params: Optional[Dict] = None):
        """
        初始化组合策略
        
        Args:
            weights: 各组件权重，默认使用DEFAULT_WEIGHTS
            ema_params: EMA策略参数
        """
        self.weights = weights or self.DEFAULT_WEIGHTS
        
        # 初始化组件策略
        self.ema_strategy = EMAV2Strategy(params=ema_params) if ema_params else EMAV2Strategy()
        self.rsi_strategy = RSIStrategy()
        self.bollinger_strategy = BollingerStrategy()
        self.volume_strategy = VolumeStrategy()
    
    def calculate_composite_signal(self, signals: List[ComponentSignal]) -> Tuple[int, float]:
        """
        计算组合信号
        
        Returns:
            (信号类型, 综合得分)
        """
        # 加权计算总分 (0-100)
        total_score = 0
        total_weight = 0
        
        for sig in signals:
            # 将信号值(0-4)映射到分数(0-100)
            score = (sig.signal / 4) * 100
            weighted_score = score * sig.weight * sig.confidence
            total_score += weighted_score
            total_weight += sig.weight * sig.confidence
        
        if total_weight > 0:
            final_score = total_score / total_weight
        else:
            final_score = 50  # 默认中立
        
        # 根据阈值确定信号类型
        if final_score >= self.THRESHOLDS['strong_buy']:
            signal_type = 4  # 强烈买入
        elif final_score >= self.THRESHOLDS['buy']:
            signal_type = 3  # 买入
        elif final_score <= self.THRESHOLDS['strong_sell']:
            signal_type = 0  # 强烈卖出
        elif final_score <= self.THRESHOLDS['sell']:
            signal_type = 1  # 卖出
        else:
            signal_type = 2  # 观望
        
        return signal_type, final_score
    
    def generate_signals(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        生成组合交易信号
        """
        data = df.copy()
        
        # 各组件生成信号
        data = self.ema_strategy.generate_signals(data, market_data)
        data = self.rsi_strategy.generate_signals(data)
        data = self.bollinger_strategy.generate_signals(data)
        data = self.volume_strategy.generate_signals(data)
        
        # 计算组合信号
        data['composite_score'] = 50.0  # 默认中立
        data['composite_signal'] = 2  # 默认观望
        data['signal_components'] = ''  # 信号组成详情
        
        for i in range(len(data)):
            if i < 50:  # 跳过前期数据不足的情况
                continue
            
            # 收集各组件信号
            signals = []
            
            # EMA信号
            if data['buy_signal'].iloc[i]:
                ema_sig = 3
            elif data['sell_signal'].iloc[i]:
                ema_sig = 1
            else:
                ema_sig = 2
            signals.append(ComponentSignal('EMA', ema_sig, self.weights['ema'], 0.8, {}))
            
            # RSI信号
            rsi_sig, rsi_conf, rsi_details = self.rsi_strategy.get_signal_strength(data, i)
            signals.append(ComponentSignal('RSI', rsi_sig, self.weights['rsi'], rsi_conf, rsi_details))
            
            # 布林带信号
            bb_sig, bb_conf, bb_details = self.bollinger_strategy.get_signal_strength(data, i)
            signals.append(ComponentSignal('Bollinger', bb_sig, self.weights['bollinger'], bb_conf, bb_details))
            
            # 成交量信号
            vol_sig, vol_conf, vol_details = self.volume_strategy.get_signal_strength(data, i)
            signals.append(ComponentSignal('Volume', vol_sig, self.weights['volume'], vol_conf, vol_details))
            
            # 计算组合信号
            composite_signal, composite_score = self.calculate_composite_signal(signals)
            
            data.loc[data.index[i], 'composite_signal'] = composite_signal
            data.loc[data.index[i], 'composite_score'] = composite_score
        
        # 生成最终买卖信号
        data['final_buy_signal'] = data['composite_signal'] >= 3  # 买入或强烈买入
        data['final_sell_signal'] = data['composite_signal'] <= 1  # 卖出或强烈卖出
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None,
                     initial_capital: float = 100000.0) -> EnsembleResult:
        """
        执行组合策略回测
        """
        data = self.generate_signals(df, market_data)
        
        position = 0  # 0: 空仓, 1: 持仓
        entry_price = 0.0
        entry_date = None
        entry_score = 0.0
        trades = []
        signal_history = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        
        for i in range(1, len(data)):
            date = data.index[i]
            price = data['close'].iloc[i]
            signal = data['composite_signal'].iloc[i]
            score = data['composite_score'].iloc[i]
            
            # 记录信号历史
            signal_history.append({
                'date': date,
                'price': price,
                'signal': signal,
                'score': score
            })
            
            if position == 0:  # 空仓
                if data['final_buy_signal'].iloc[i]:
                    # 买入
                    position = 1
                    entry_price = price
                    entry_date = date
                    entry_score = score
                    shares = current_capital / price
                    
            elif position == 1:  # 持仓
                # 检查卖出条件
                exit_reason = None
                exit_price = price
                
                if data['final_sell_signal'].iloc[i]:
                    exit_reason = "signal"
                
                # 止损检查 (使用EMA策略的ATR止损)
                stop_price = data['stop_loss'].iloc[i]
                if price < stop_price:
                    exit_reason = "stop_loss"
                    exit_price = stop_price
                
                if exit_reason:
                    # 卖出
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    
                    trades.append({
                        'entry_date': entry_date,
                        'entry_price': entry_price,
                        'entry_score': entry_score,
                        'exit_date': date,
                        'exit_price': exit_price,
                        'exit_signal': signal,
                        'exit_score': score,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason,
                        'holding_days': (date - entry_date).days if hasattr(date, 'days') else 0
                    })
                    
                    current_capital += pnl
                    position = 0
                    entry_price = 0.0
                    entry_date = None
                    entry_score = 0.0
            
            equity_curve.append(current_capital)
        
        # 计算绩效指标
        total_return = (current_capital - initial_capital) / initial_capital * 100
        
        if len(trades) > 0:
            winning_trades = [t for t in trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(trades) * 100
            
            # 计算最大回撤
            equity_series = pd.Series(equity_curve)
            rolling_max = equity_series.expanding().max()
            drawdown = (equity_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdown.min()
            
            # 计算Sharpe比率
            returns = pd.Series(equity_curve).pct_change().dropna()
            if returns.std() != 0:
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            win_rate = 0
            max_drawdown = 0
            sharpe_ratio = 0
        
        return EnsembleResult(
            symbol=df.attrs.get('symbol', 'Unknown'),
            total_return=total_return,
            win_rate=win_rate,
            total_trades=len(trades),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=trades,
            params=self.weights,
            component_signals=[],  # 简化版，详细信号可在signal_history中查看
            signal_history=signal_history
        )


# 兼容原EMA V2策略的接口
class EnsembleStrategyWrapper:
    """组合策略包装器，兼容原回测框架"""
    
    def __init__(self, weights: Optional[Dict] = None, ema_params: Optional[Dict] = None):
        self.ensemble = MultiStrategyEnsemble(weights, ema_params)
    
    def run_backtest(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None,
                     initial_capital: float = 100000.0) -> BacktestResult:
        """运行回测并返回兼容格式的结果"""
        result = self.ensemble.run_backtest(df, market_data, initial_capital)
        
        # 转换为BacktestResult格式
        return BacktestResult(
            symbol=result.symbol,
            total_return=result.total_return,
            win_rate=result.win_rate,
            total_trades=result.total_trades,
            max_drawdown=result.max_drawdown,
            sharpe_ratio=result.sharpe_ratio,
            trades=result.trades,
            params=result.params
        )


if __name__ == '__main__':
    # 简单测试
    print("多策略组合系统已加载")
    print("权重配置:", MultiStrategyEnsemble.DEFAULT_WEIGHTS)
    print("信号阈值:", MultiStrategyEnsemble.THRESHOLDS)
