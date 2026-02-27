"""
多策略组合交易系统 V2 - 趋势增强型

设计理念: 以EMA趋势为核心，其他指标作为确认而非过滤

策略架构:
1. EMA趋势跟踪 (核心) - 决定大方向
2. RSI动量确认 (辅助) - 确认趋势强度
3. 成交量验证 (辅助) - 确认信号质量
4. 自适应权重 - 根据市场环境动态调整

信号合成方法: 
- EMA信号为必要条件
- 其他指标提供加分/减分
- 避免过度过滤

作者: InvestMindPro Team
版本: 2.0.0
日期: 2026-02-28
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import sys
from pathlib import Path

sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace/InvestMindPro')
from strategies.ema_v2 import EMAV2Strategy, BacktestResult


class TrendEnhancedEnsemble:
    """趋势增强型组合策略"""
    
    def __init__(self, ema_params: Optional[Dict] = None):
        """
        初始化趋势增强组合策略
        """
        # EMA策略参数
        self.ema_params = ema_params or {
            "fast_ema": 8,
            "slow_ema": 25,
            "atr_period": 14,
            "atr_multiplier": 2.0,
            "market_filter": True
        }
        
        self.ema_strategy = EMAV2Strategy(self.ema_params)
        
        # RSI参数
        self.rsi_period = 14
        self.rsi_oversold = 35  # 放宽超卖阈值
        self.rsi_overbought = 65  # 放宽超买阈值
        
        # 成交量参数
        self.vol_short = 5
        self.vol_long = 20
        
        # 信号阈值
        self.entry_threshold = 0.6  # 入场置信度阈值
        self.exit_threshold = 0.4   # 出场置信度阈值
    
    def calculate_rsi(self, data: pd.Series) -> pd.Series:
        """计算RSI"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_volume_confidence(self, df: pd.DataFrame) -> pd.Series:
        """计算成交量置信度 (0-1)"""
        vol_short = df['volume'].rolling(window=self.vol_short).mean()
        vol_long = df['volume'].rolling(window=self.vol_long).mean()
        vol_ratio = vol_short / vol_long
        
        # 成交量放大配合价格上涨 = 高置信度
        price_change = df['close'].pct_change()
        
        confidence = pd.Series(index=df.index, dtype=float)
        
        # 放量上涨 - 强确认
        confidence[(vol_ratio > 1.2) & (price_change > 0)] = 0.9
        # 放量下跌 - 强警示
        confidence[(vol_ratio > 1.2) & (price_change < 0)] = 0.1
        # 缩量上涨 - 弱确认
        confidence[(vol_ratio < 0.8) & (price_change > 0)] = 0.5
        # 缩量下跌 - 弱警示
        confidence[(vol_ratio < 0.8) & (price_change < 0)] = 0.4
        # 其他情况
        confidence = confidence.fillna(0.5)
        
        return confidence
    
    def calculate_momentum_confidence(self, df: pd.DataFrame) -> pd.Series:
        """计算动量置信度 (0-1)"""
        rsi = self.calculate_rsi(df['close'])
        
        confidence = pd.Series(index=df.index, dtype=float)
        
        # RSI处于上升趋势初期 (40-60) - 中性偏强
        confidence[(rsi >= 40) & (rsi <= 60)] = 0.7
        # RSI确认强势 (>60) - 强确认
        confidence[rsi > 60] = 0.85
        # RSI超卖反弹 (<40) - 中等确认
        confidence[(rsi >= 30) & (rsi < 40)] = 0.6
        # RSI极端超卖 (<30) - 可能反转
        confidence[rsi < 30] = 0.8  # 超卖反弹机会
        
        return confidence.fillna(0.5)
    
    def generate_signals(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        生成交易信号
        
        逻辑:
        1. EMA信号为基础 (必须)
        2. 其他指标提供置信度调整
        3. 避免过度过滤，保持趋势跟踪能力
        """
        # 基础EMA信号
        data = self.ema_strategy.generate_signals(df, market_data)
        
        # 计算各组件置信度
        data['vol_confidence'] = self.calculate_volume_confidence(data)
        data['mom_confidence'] = self.calculate_momentum_confidence(data)
        
        # 综合置信度 (简单平均)
        data['composite_confidence'] = (data['vol_confidence'] + data['mom_confidence']) / 2
        
        # 调整后的买卖信号
        # 策略: EMA信号 + 置信度加权
        # 置信度 >= 0.7: 保持EMA信号
        # 置信度 0.4-0.7: 保持EMA信号但降低仓位 (这里简化为保持信号)
        # 置信度 < 0.4: 观望 (不生成信号)
        
        data['adjusted_buy'] = data['buy_signal'] & (data['composite_confidence'] >= 0.4)
        data['adjusted_sell'] = data['sell_signal']  # 卖出信号不过滤
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None,
                     initial_capital: float = 100000.0) -> Dict:
        """
        执行趋势增强组合策略回测
        """
        data = self.generate_signals(df, market_data)
        
        position = 0
        entry_price = 0.0
        entry_date = None
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        signal_history = []
        
        for i in range(1, len(data)):
            date = data.index[i]
            price = data['close'].iloc[i]
            confidence = data['composite_confidence'].iloc[i]
            
            # 记录信号历史
            if data['buy_signal'].iloc[i] or data['sell_signal'].iloc[i]:
                signal_history.append({
                    'date': date,
                    'price': price,
                    'ema_buy': data['buy_signal'].iloc[i],
                    'ema_sell': data['sell_signal'].iloc[i],
                    'adjusted_buy': data['adjusted_buy'].iloc[i],
                    'confidence': confidence
                })
            
            if position == 0:  # 空仓
                if data['adjusted_buy'].iloc[i]:
                    # 买入
                    position = 1
                    entry_price = price
                    entry_date = date
                    shares = current_capital / price
                    
            elif position == 1:  # 持仓
                exit_reason = None
                exit_price = price
                
                if data['adjusted_sell'].iloc[i]:
                    exit_reason = "signal"
                
                # 止损检查
                stop_price = data['stop_loss'].iloc[i]
                if price < stop_price:
                    exit_reason = "stop_loss"
                    exit_price = stop_price
                
                if exit_reason:
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    
                    trades.append({
                        'entry_date': entry_date,
                        'entry_price': entry_price,
                        'exit_date': date,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason
                    })
                    
                    current_capital += pnl
                    position = 0
                    entry_price = 0.0
                    entry_date = None
            
            equity_curve.append(current_capital)
        
        # 计算绩效指标
        total_return = (current_capital - initial_capital) / initial_capital * 100
        
        if len(trades) > 0:
            winning_trades = [t for t in trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(trades) * 100
            
            equity_series = pd.Series(equity_curve)
            rolling_max = equity_series.expanding().max()
            drawdown = (equity_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdown.min()
            
            returns = pd.Series(equity_curve).pct_change().dropna()
            if returns.std() != 0:
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            win_rate = 0
            max_drawdown = 0
            sharpe_ratio = 0
        
        return {
            'symbol': df.attrs.get('symbol', 'Unknown'),
            'strategy': 'TrendEnhanced',
            'total_return': total_return,
            'win_rate': win_rate,
            'total_trades': len(trades),
            'max_drawdown': max_drawdown,
            'sharpe_ratio': sharpe_ratio,
            'trades': trades,
            'signal_history': signal_history,
            'params': self.ema_params
        }


class WeightedEnsembleV2:
    """加权组合策略 V2 - 行业特化版本"""
    
    # 行业特定配置
    SECTOR_CONFIG = {
        'new_energy': {  # 新能源 - 高波动
            'ema_fast': 10,
            'ema_slow': 30,
            'atr_mult': 3.0,
            'rsi_period': 14,
            'use_volume': True
        },
        'tech': {  # 科技 - 高波动
            'ema_fast': 8,
            'ema_slow': 25,
            'atr_mult': 2.5,
            'rsi_period': 10,
            'use_volume': True
        },
        'consumer': {  # 消费 - 中波动
            'ema_fast': 8,
            'ema_slow': 25,
            'atr_mult': 2.0,
            'rsi_period': 14,
            'use_volume': True
        },
        'finance': {  # 金融 - 低波动
            'ema_fast': 5,
            'ema_slow': 20,
            'atr_mult': 1.5,
            'rsi_period': 14,
            'use_volume': False
        },
        'liquor': {  # 白酒 - 低波动
            'ema_fast': 5,
            'ema_slow': 20,
            'atr_mult': 1.5,
            'rsi_period': 21,
            'use_volume': False
        },
        'medical': {  # 医药 - 中波动
            'ema_fast': 8,
            'ema_slow': 25,
            'atr_mult': 2.0,
            'rsi_period': 14,
            'use_volume': True
        }
    }
    
    def __init__(self, sector: str = 'default'):
        """
        初始化行业特化组合策略
        
        Args:
            sector: 行业类型 (new_energy/tech/consumer/finance/liquor/medical)
        """
        config = self.SECTOR_CONFIG.get(sector, self.SECTOR_CONFIG['consumer'])
        
        ema_params = {
            "fast_ema": config['ema_fast'],
            "slow_ema": config['ema_slow'],
            "atr_period": 14,
            "atr_multiplier": config['atr_mult'],
            "market_filter": True
        }
        
        self.base_strategy = TrendEnhancedEnsemble(ema_params)
    
    def run_backtest(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None,
                     initial_capital: float = 100000.0) -> Dict:
        """执行回测"""
        return self.base_strategy.run_backtest(df, market_data, initial_capital)


if __name__ == '__main__':
    print("趋势增强型组合策略 V2 已加载")
    print("策略特点:")
    print("- EMA趋势为核心")
    print("- RSI和成交量作为确认而非过滤")
    print("- 避免过度过滤，保持趋势跟踪能力")
    print("- 支持行业特化参数")
