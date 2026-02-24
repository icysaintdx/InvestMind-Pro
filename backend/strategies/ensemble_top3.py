# -*- coding: utf-8 -*-
"""
Top3 融合策略 (Ensemble Top3) - 简化版
直接复制 Top3 策略的核心逻辑，避免导入依赖问题

Top3: ema_breakout + sentiment_resonance + graham_margin
"""

import pandas as pd
import numpy as np
from typing import Optional, Dict, Any

from .base import (
    BaseStrategy,
    StrategySignal,
    SignalType,
    StrategyConfig,
    register_strategy
)


# ============ 子策略核心逻辑 ============

def _ema(series: pd.Series, span: int) -> pd.Series:
    return series.ewm(span=span, adjust=False).mean()


def _sma(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window=window, min_periods=1).mean()


def _rsi(series: pd.Series, length: int = 14) -> pd.Series:
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = (-delta).clip(lower=0)
    avg_gain = gain.ewm(alpha=1.0 / length, min_periods=length, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / length, min_periods=length, adjust=False).mean()
    rs = avg_gain / avg_loss.replace(0, np.nan)
    return 100.0 - 100.0 / (1.0 + rs)


# EMA breakout 信号
def _ema_breakout_signal(df: pd.DataFrame) -> pd.Series:
    """EMA突破：短期均线上穿长期均线"""
    ema_short = _ema(df['close'], 12)
    ema_long = _ema(df['close'], 26)
    bullish = (ema_short > ema_long) & (ema_short.shift(1) <= ema_long.shift(1))
    bearish = (ema_short < ema_long) & (ema_short.shift(1) >= ema_long.shift(1))
    return bullish, bearish


# Sentiment resonance 信号（简化版：用价格和成交量变化模拟情绪）
def _sentiment_signal(df: pd.DataFrame) -> pd.Series:
    """情绪共振：价格上涨 + 成交量放大 + RSI 确认"""
    price_change = df['close'].pct_change(5)  # 5日涨幅
    vol_ma = _sma(df['volume'], 20)
    vol_expanding = df['volume'] > vol_ma * 1.2
    rsi_val = _rsi(df['close'], 14)
    
    bullish = (price_change > 0.03) & vol_expanding & (rsi_val > 50) & (rsi_val < 70)
    bearish = (price_change < -0.03) & vol_expanding & (rsi_val < 50) & (rsi_val > 30)
    return bullish, bearish


# Graham margin 信号（简化版：低估 + 安全边际）
def _graham_signal(df: pd.DataFrame) -> pd.Series:
    """格雷厄姆：价格低于近期均值 + RSI 超卖"""
    price_ma60 = _sma(df['close'], 60)
    price_below_ma = df['close'] < price_ma60 * 0.95  # 低于60日均线5%
    rsi_val = _rsi(df['close'], 14)
    
    bullish = price_below_ma & (rsi_val < 40)
    bearish = (df['close'] > price_ma60 * 1.05) & (rsi_val > 60)
    return bullish, bearish


# ============ 融合策略类 ============

@register_strategy("ensemble_top3")
class EnsembleTop3Strategy(BaseStrategy):
    """
    Top3 策略融合 - 直接实现子策略逻辑，避免导入依赖
    组合：ema_breakout + sentiment_resonance + graham_margin
    """

    description = "Top3策略融合：EMA突破 + 情绪共振 + 格雷厄姆安全边际 投票制"

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "Top3融合策略"
        self.category = "融合策略"

        params = self.parameters
        self.strong_buy_threshold = params.get('strong_buy_threshold', 2)
        self.buy_threshold = params.get('buy_threshold', 1)
        self.strong_buy_position = params.get('strong_buy_position', 0.30)
        self.buy_position = params.get('buy_position', 0.15)
        self.stop_loss_pct = params.get('stop_loss', 0.08)
        self.take_profit_pct = params.get('take_profit', 0.20)

    def initialize(self, data: pd.DataFrame):
        """预计算所有信号"""
        df = data.copy()
        
        # 计算三个子策略的信号
        df['ema_bull'], df['ema_bear'] = _ema_breakout_signal(df)
        df['sentiment_bull'], df['sentiment_bear'] = _sentiment_signal(df)
        df['graham_bull'], df['graham_bear'] = _graham_signal(df)
        
        # 统计买入信号数
        df['buy_count'] = df['ema_bull'].astype(int) + df['sentiment_bull'].astype(int) + df['graham_bull'].astype(int)
        df['sell_count'] = df['ema_bear'].astype(int) + df['sentiment_bear'].astype(int) + df['graham_bear'].astype(int)
        
        self._data = df
        self._initialized = True

    def get_required_indicators(self) -> list:
        return ['buy_count', 'sell_count', 'ema_bull', 'sentiment_bull', 'graham_bull']

    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> Optional[StrategySignal]:
        """生成融合信号"""
        if not self._initialized:
            self.initialize(data)
        
        idx = len(data) - 1
        if idx >= len(self._data):
            return StrategySignal(signal_type=SignalType.HOLD, confidence=0.0, reason="数据越界")
        
        bar = self._data.iloc[idx]
        price = float(bar['close'])
        
        buy_count = int(bar.get('buy_count', 0))
        sell_count = int(bar.get('sell_count', 0))
        
        sub_signals = {
            'ema': 'buy' if bar.get('ema_bull') else ('sell' if bar.get('ema_bear') else 'hold'),
            'sentiment': 'buy' if bar.get('sentiment_bull') else ('sell' if bar.get('sentiment_bear') else 'hold'),
            'graham': 'buy' if bar.get('graham_bull') else ('sell' if bar.get('graham_bear') else 'hold'),
            'buy_count': buy_count,
            'sell_count': sell_count
        }
        
        # 买入逻辑
        if current_position == 0:
            if buy_count >= self.strong_buy_threshold:
                return StrategySignal(
                    signal_type=SignalType.STRONG_BUY,
                    confidence=0.70 + buy_count * 0.10,
                    price=price,
                    stop_loss=round(price * (1 - self.stop_loss_pct), 2),
                    take_profit=round(price * (1 + self.take_profit_pct), 2),
                    position_size=self.strong_buy_position,
                    reason=f"Top3强共振: {buy_count}/3 策略看多 | EMA:{sub_signals['ema']} | 情绪:{sub_signals['sentiment']} | 格雷厄姆:{sub_signals['graham']}",
                    metadata=sub_signals
                )
            
            if buy_count >= self.buy_threshold:
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.50 + buy_count * 0.15,
                    price=price,
                    stop_loss=round(price * (1 - self.stop_loss_pct), 2),
                    take_profit=round(price * (1 + self.take_profit_pct), 2),
                    position_size=self.buy_position,
                    reason=f"Top3弱共振: {buy_count}/3 策略看多 | EMA:{sub_signals['ema']} | 情绪:{sub_signals['sentiment']} | 格雷厄姆:{sub_signals['graham']}",
                    metadata=sub_signals
                )
        
        # 卖出逻辑
        if current_position > 0:
            if sell_count >= self.strong_buy_threshold:
                return StrategySignal(
                    signal_type=SignalType.STRONG_SELL,
                    confidence=0.75,
                    price=price,
                    reason=f"Top3共振看空: {sell_count}/3 策略看空"
                )
            
            if sell_count >= self.buy_threshold:
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.60,
                    price=price,
                    reason=f"Top3弱共振看空: {sell_count}/3 策略看空"
                )
        
        return StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.30,
            price=price,
            reason=f"Top3分歧 | 看多:{buy_count} | 看空:{sell_count}",
            metadata=sub_signals
        )
