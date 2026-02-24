# -*- coding: utf-8 -*-
"""
WaveTrend + JMA 策略 (A股适配版) - 参数扫描版本
原始脚本: sol_wt_jma_alert_sqlite.py (SOL/USDT 5m 加密货币策略)
适配: 日线级别 A股市场

可调参数:
- long_wt2_th: WT2 买入阈值 (默认 -50，可扫 -40/-50/-60/-70)

买入条件:
  WaveTrend金叉 & JMA向上 & WT2低于阈值 & RSI超卖 & 非大幅波动 & 成交量放大
"""

import numpy as np
import pandas as pd
from typing import Dict, Optional

from .base import (
    BaseStrategy,
    StrategySignal,
    SignalType,
    StrategyConfig,
    register_strategy
)


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


def _hlc3(df: pd.DataFrame) -> pd.Series:
    return (df['high'] + df['low'] + df['close']) / 3.0


def _compute_wavetrend(df: pd.DataFrame, n1: int, n2: int):
    """计算 WaveTrend 指标 (wt1, wt2)"""
    ap = _hlc3(df)
    esa = _ema(ap, n1)
    d = _ema((ap - esa).abs(), n1)
    ci = (ap - esa) / (0.015 * d.replace(0, np.nan))
    tci = _ema(ci, n2)
    wt1 = tci
    wt2 = _sma(wt1, 4)
    return wt1, wt2


def _jma(series: pd.Series, length: int = 10, phase: int = 50, power: int = 2) -> pd.Series:
    """Jurik Moving Average - 递推实现"""
    phase_ratio = 0.5 if phase < -100 else 2.5 if phase > 100 else phase / 100.0 + 1.5
    beta = 0.45 * (length - 1) / (0.45 * (length - 1) + 2)
    alpha = beta ** power

    e0 = np.nan
    e1 = np.nan
    e2 = np.nan
    j = np.nan

    out = []
    for x in series.values.astype(float):
        if np.isnan(x):
            out.append(np.nan)
            continue
        if np.isnan(e0): e0 = x
        if np.isnan(e1): e1 = 0.0
        if np.isnan(e2): e2 = 0.0
        if np.isnan(j):  j = x

        e0 = (1 - alpha) * x + alpha * e0
        e1 = (x - e0) * (1 - beta) + beta * e1
        e2 = (e0 + phase_ratio * e1 - j) * ((1 - alpha) ** 2) + (alpha ** 2) * e2
        j = e2 + j
        out.append(j)

    return pd.Series(out, index=series.index)


def _crossover(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a > b) & (a.shift(1) <= b.shift(1))


def _crossunder(a: pd.Series, b: pd.Series) -> pd.Series:
    return (a < b) & (a.shift(1) >= b.shift(1))


# 参数扫描版本：创建多个变体
for threshold in [-40, -50, -60, -70]:
    strategy_class_name = f"WaveTrendJMA_{abs(threshold)}"
    
    @register_strategy(f"wavetrend_jma_t{abs(threshold)}")
    class WaveTrendJMAVariant(BaseStrategy):
        """WaveTrend + JMA 策略 - 参数扫描版本"""
        
        description = f"WaveTrend+JMA策略 (WT2阈值={threshold})"
        _threshold = threshold  # 类变量存储阈值
        
        def __init__(self, config: StrategyConfig):
            super().__init__(config)
            self.name = f"WT+JMA_T{abs(threshold)}"
            self.category = "复合策略"
            
            params = self.parameters
            self.long_wt2_th = params.get('long_wt2_th', threshold)
            self.wt_n1 = params.get('wt_n1', 10)
            self.wt_n2 = params.get('wt_n2', 21)
            self.jma_length = params.get('jma_length', 10)
            self.jma_phase = params.get('jma_phase', 50)
            self.jma_power = params.get('jma_power', 2)
            self.rsi_periods = params.get('rsi_periods', [7, 14, 21])
            self.rsi_ob = params.get('rsi_ob', 70)
            self.vol_window = params.get('vol_window', 5)
            self.vol_median_window = params.get('vol_median_window', 100)
            self.max_change_pct = params.get('max_change_pct', 5.0)
            self.stop_loss_pct = params.get('stop_loss', 0.08)
            self.take_profit_pct = params.get('take_profit', 0.20)
            self._data_with_indicators = None
            self._holding = False
            self._entry_price = 0.0

        def initialize(self, data: pd.DataFrame):
            self._data_with_indicators = self._calculate_all_indicators(data)
            self._initialized = True
            self._holding = False
            self._entry_price = 0.0

        def _calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
            df = data.copy()
            wt1, wt2 = _compute_wavetrend(df, self.wt_n1, self.wt_n2)
            df['wt1'] = wt1
            df['wt2'] = wt2
            df['bullishCross'] = _crossover(wt1, wt2)
            df['bearishCross'] = _crossunder(wt1, wt2)
            
            j = _jma(df['close'], self.jma_length, self.jma_phase, self.jma_power)
            df['jma'] = j
            df['jmaUp'] = j > j.shift(1)
            df['jmaDown'] = j < j.shift(1)
            
            prev_change = ((df['close'].shift(1) - df['open'].shift(1)) / df['open'].shift(1)) * 100.0
            prev_change1 = ((df['close'].shift(2) - df['open'].shift(2)) / df['open'].shift(2)) * 100.0
            df['tooBigChange'] = (prev_change.abs() >= self.max_change_pct) | (prev_change1.abs() >= self.max_change_pct)
            
            for period in self.rsi_periods:
                df[f'rsi_{period}'] = _rsi(df['close'], period)
            
            rsi_cols = [f'rsi_{p}' for p in self.rsi_periods]
            df['rsiOversold'] = False
            for col in rsi_cols:
                df['rsiOversold'] = df['rsiOversold'] | (df[col] <= self.rsi_ob)
            
            df['vol_rolling'] = df['volume'].rolling(self.vol_window, min_periods=self.vol_window).sum()
            df['vol_median'] = df['vol_rolling'].rolling(self.vol_median_window, min_periods=10).median()
            df['volAboveMedian'] = df['vol_rolling'].notna() & df['vol_median'].notna() & (df['vol_rolling'] > df['vol_median'])
            
            df['longCond'] = (
                df['bullishCross']
                & df['jmaUp']
                & (df['wt2'] < self.long_wt2_th)
                & df['rsiOversold']
                & (~df['tooBigChange'])
                & df['volAboveMedian']
            )
            
            df['sellSignal'] = df['bearishCross'] & df['jmaDown']
            
            return df

        def get_required_indicators(self) -> list:
            return ['wt1', 'wt2', 'jma', 'bullishCross', 'bearishCross', 'longCond', 'sellSignal']

        def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> Optional[StrategySignal]:
            if self._data_with_indicators is not None:
                idx = len(data) - 1
                if idx >= len(self._data_with_indicators):
                    return StrategySignal(signal_type=SignalType.HOLD, confidence=0.0, reason="数据越界")
                bar = self._data_with_indicators.iloc[idx]
            else:
                calc = self._calculate_all_indicators(data)
                bar = calc.iloc[-1]

            price = float(bar['close'])

            if pd.isna(bar.get('wt1')) or pd.isna(bar.get('jma')):
                return StrategySignal(signal_type=SignalType.HOLD, confidence=0.0, reason="指标数据不足")

            if current_position == 0 and not self._holding:
                if bar.get('longCond', False):
                    self._holding = True
                    self._entry_price = price
                    wt2_val = bar.get('wt2', 0)
                    confidence = min(0.85, 0.6 + abs(wt2_val) / 100)

                    return StrategySignal(
                        signal_type=SignalType.BUY,
                        confidence=confidence,
                        price=price,
                        stop_loss=round(price * (1 - self.stop_loss_pct), 2),
                        take_profit=round(price * (1 + self.take_profit_pct), 2),
                        reason=f"WT金叉+JMA↑ | WT2={wt2_val:.1f} | 阈值={self.long_wt2_th}",
                        metadata={'wt1': float(bar.get('wt1', 0)), 'wt2': float(bar.get('wt2', 0)), 'jma': float(bar.get('jma', 0))}
                    )

            if current_position > 0 or self._holding:
                profit_pct = (price - self._entry_price) / self._entry_price if self._entry_price > 0 else 0

                if profit_pct <= -self.stop_loss_pct:
                    self._holding = False
                    self._entry_price = 0
                    return StrategySignal(signal_type=SignalType.SELL, confidence=0.9, price=price, reason=f"止损触发 | 亏损{profit_pct:.2%}")

                if profit_pct >= self.take_profit_pct:
                    self._holding = False
                    self._entry_price = 0
                    return StrategySignal(signal_type=SignalType.SELL, confidence=0.85, price=price, reason=f"止盈触发 | 盈利{profit_pct:.2%}")

                if bar.get('sellSignal', False):
                    self._holding = False
                    self._entry_price = 0
                    return StrategySignal(signal_type=SignalType.SELL, confidence=0.75, price=price, reason=f"WT死叉+JMA↓ | 盈亏{profit_pct:.2%}")

            return StrategySignal(signal_type=SignalType.HOLD, confidence=0.3, price=price, reason="等待信号")
