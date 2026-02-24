# -*- coding: utf-8 -*-
"""
EMA突破策略 V2.0 - 优化版
核心改进：
1. 参数优化：EMA8/25（回测最优）
2. ATR动态止损：2倍ATR自适应止损
3. Kelly仓位管理：根据历史胜率动态调整仓位
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


@register_strategy("ema_breakout_v2")
class EMABreakoutV2Strategy(BaseStrategy):
    """
    EMA突破策略 V2.0 - 优化版
    
    改进点：
    - 均线周期：8/25（回测最优参数）
    - 止损：2倍ATR动态止损
    - 仓位：Kelly公式动态仓位
    """
    
    description = "EMA8/25突破 + ATR动态止损 + Kelly仓位管理"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "EMA突破V2"
        self.category = "技术分析"
        
        # 优化后的参数
        self.ema_fast = self.parameters.get('ema_fast', 8)   # 原5→8
        self.ema_slow = self.parameters.get('ema_slow', 25)  # 原21→25
        
        # ATR止损参数
        self.atr_period = self.parameters.get('atr_period', 14)
        self.atr_multiplier = self.parameters.get('atr_multiplier', 2.0)
        
        # Kelly仓位参数
        self.kelly_fraction = self.parameters.get('kelly_fraction', 0.5)  # 半Kelly
        self.max_position = self.parameters.get('max_position', 0.4)
        self.min_position = self.parameters.get('min_position', 0.1)
        
        # 历史记录（用于计算Kelly）
        self.trade_history = []
        self.win_count = 0
        self.loss_count = 0
        
    def initialize(self, data: pd.DataFrame):
        """计算指标"""
        df = data.copy()
        
        # EMA
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.ewm(span=self.atr_period).mean()
        
        # RSI辅助
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(span=14).mean()
        loss = (-delta.clip(upper=0)).ewm(span=14).mean()
        df['rsi'] = 100 - 100 / (1 + gain / (loss + 0.001))
        
        # 趋势强度
        df['trend_strength'] = (df['ema_fast'] - df['ema_slow']) / df['ema_slow'] * 100
        
        self._data = df
        self._initialized = True
    
    def _calculate_kelly_position(self) -> float:
        """计算Kelly最优仓位
        f* = (p*b - q) / b
        其中 p=胜率, q=败率=1-p, b=平均盈利/平均亏损
        """
        total = self.win_count + self.loss_count
        if total < 10:  # 数据不足，用默认
            return 0.2
        
        p = self.win_count / total  # 胜率
        q = 1 - p
        
        # 简化：假设盈亏比为2:1
        b = 2.0
        
        kelly = (p * b - q) / b
        kelly = max(0, min(kelly, 0.5))  # 限制在0-50%
        
        # 半Kelly（更保守）
        return kelly * self.kelly_fraction
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> Optional[StrategySignal]:
        if not self._initialized:
            self.initialize(data)
        
        idx = len(data) - 1
        if idx >= len(self._data):
            return StrategySignal(signal_type=SignalType.HOLD, confidence=0.0, price=data['close'].iloc[-1])
        
        bar = self._data.iloc[idx]
        price = float(bar['close'])
        
        # 数据检查
        if pd.isna(bar.get('ema_fast')) or pd.isna(bar.get('atr')):
            return StrategySignal(signal_type=SignalType.HOLD, confidence=0.0, price=price, reason="指标计算中")
        
        # 金叉/死叉判断
        ema_fast = bar['ema_fast']
        ema_slow = bar['ema_slow']
        ema_fast_prev = self._data['ema_fast'].iloc[idx-1]
        ema_slow_prev = self._data['ema_slow'].iloc[idx-1]
        
        golden_cross = (ema_fast > ema_slow) and (ema_fast_prev <= ema_slow_prev)
        death_cross = (ema_fast < ema_slow) and (ema_fast_prev >= ema_slow_prev)
        
        # 趋势方向
        trend_up = ema_fast > ema_slow
        trend_down = ema_fast < ema_slow
        
        # RSI过滤
        rsi = bar.get('rsi', 50)
        
        # ATR止损价格
        atr = bar['atr']
        
        # ===== 买入逻辑 =====
        if current_position == 0:
            # 条件：金叉 + 趋势向上 + RSI不超买
            if golden_cross and trend_up and rsi < 70:
                # Kelly仓位
                position_size = self._calculate_kelly_position()
                
                # ATR止损：入场价 - 2*ATR
                stop_loss = price - self.atr_multiplier * atr
                
                # 止盈：2倍止损距离（盈亏比2:1）
                take_profit = price + 2 * (price - stop_loss)
                
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.75,
                    price=price,
                    stop_loss=round(stop_loss, 2),
                    take_profit=round(take_profit, 2),
                    position_size=position_size,
                    reason=f"EMA8/25金叉 | ATR止损={stop_loss:.2f} | Kelly仓位={position_size:.1%}"
                )
        
        # ===== 卖出逻辑 =====
        elif current_position > 0:
            # 条件1：死叉
            if death_cross:
                self._record_trade(False)  # 记录亏损
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.8,
                    price=price,
                    reason="EMA死叉，趋势反转"
                )
            
            # 条件2：跌破EMA8且趋势走弱
            if price < ema_fast and trend_down:
                self._record_trade(False)
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.7,
                    price=price,
                    reason="跌破EMA8，止损离场"
                )
        
        return StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.3,
            price=price,
            reason="等待信号",
            metadata={
                'ema_fast': round(ema_fast, 2),
                'ema_slow': round(ema_slow, 2),
                'trend': 'UP' if trend_up else 'DOWN',
                'rsi': round(rsi, 1),
                'atr': round(atr, 2)
            }
        )
    
    def _record_trade(self, is_win: bool):
        """记录交易结果用于Kelly计算"""
        if is_win:
            self.win_count += 1
        else:
            self.loss_count += 1
        self.trade_history.append(1 if is_win else 0)
        
        # 只保留最近50笔
        if len(self.trade_history) > 50:
            removed = self.trade_history.pop(0)
            if removed == 1:
                self.win_count -= 1
            else:
                self.loss_count -= 1
    
    def get_required_indicators(self) -> list:
        return ['ema_fast', 'ema_slow', 'atr', 'rsi', 'trend_strength']
