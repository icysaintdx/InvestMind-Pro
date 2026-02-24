# -*- coding: utf-8 -*-
"""
WaveTrend + JMA 策略 (A股适配版)
原始脚本: sol_wt_jma_alert_sqlite.py (SOL/USDT 5m 加密货币策略)
适配: 日线级别 A股市场

核心逻辑:
- WaveTrend 震荡指标交叉信号
- JMA (Jurik Moving Average) 趋势过滤
- 多周期 RSI 超买超卖确认
- 成交量中位数条件过滤
- 大阳/大阴线过滤（避免追高杀低）

买入条件 (longCond):
  WaveTrend金叉 & JMA向上 & WT2低于阈值 & RSI超卖 & 非大幅波动 & 成交量放大

卖出条件:
  WaveTrend死叉 | JMA向下 | 止损 | 止盈
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any

from .base import (
    BaseStrategy,
    StrategySignal,
    SignalType,
    StrategyConfig,
    register_strategy
)


# ============ 指标计算函数 ============

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


# ============ 策略类 ============

@register_strategy("wavetrend_jma")
class WaveTrendJMAStrategy(BaseStrategy):
    """
    WaveTrend + JMA 复合策略 (A股日线适配版)
    
    原始来源: 加密货币 SOL/USDT 5分钟策略
    适配改动:
    - 5m K线 → 日线
    - 多时间框架RSI → 多周期RSI (7/14/21日)
    - 4h成交量 → 5日成交量滚动和
    - 移除做空逻辑 (A股不能融券做空)
    - 调整阈值适配日线波动特征
    """

    description = "WaveTrend震荡指标 + JMA趋势过滤，多维度确认的复合交易策略"

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "WaveTrend+JMA复合策略"
        self.category = "复合策略"

        params = self.parameters

        # WaveTrend 参数
        self.wt_n1 = params.get('wt_n1', 10)
        self.wt_n2 = params.get('wt_n2', 21)
        self.long_wt2_th = params.get('long_wt2_th', -30)   # 日线适配: -45 → -30

        # JMA 参数
        self.jma_length = params.get('jma_length', 10)
        self.jma_phase = params.get('jma_phase', 50)
        self.jma_power = params.get('jma_power', 2)

        # RSI 参数 (多周期)
        self.rsi_periods = params.get('rsi_periods', [7, 14, 21])
        self.rsi_ob = params.get('rsi_ob', 70)
        self.rsi_os = params.get('rsi_os', 30)

        # 成交量参数
        self.vol_window = params.get('vol_window', 5)        # 5日成交量滚动和
        self.vol_median_window = params.get('vol_median_window', 100)  # 中位数窗口

        # 大幅波动过滤
        self.max_change_pct = params.get('max_change_pct', 5.0)  # 日线: 5%

        # 风控参数
        self.stop_loss_pct = params.get('stop_loss', 0.08)
        self.take_profit_pct = params.get('take_profit', 0.20)

        # 内部状态
        self._data_with_indicators = None
        self._holding = False
        self._entry_price = 0.0

    def initialize(self, data: pd.DataFrame):
        """预计算所有指标"""
        self._data_with_indicators = self._calculate_all_indicators(data)
        self._initialized = True
        self._holding = False
        self._entry_price = 0.0

    def _calculate_all_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算全部指标"""
        df = data.copy()

        # WaveTrend
        wt1, wt2 = _compute_wavetrend(df, self.wt_n1, self.wt_n2)
        df['wt1'] = wt1
        df['wt2'] = wt2
        df['bullishCross'] = _crossover(wt1, wt2)
        df['bearishCross'] = _crossunder(wt1, wt2)

        # JMA
        j = _jma(df['close'], self.jma_length, self.jma_phase, self.jma_power)
        df['jma'] = j
        df['jmaUp'] = j > j.shift(1)
        df['jmaDown'] = j < j.shift(1)

        # 大幅波动过滤 (前2根K线)
        prev_change = ((df['close'].shift(1) - df['open'].shift(1)) / df['open'].shift(1)) * 100.0
        prev_change1 = ((df['close'].shift(2) - df['open'].shift(2)) / df['open'].shift(2)) * 100.0
        df['tooBigChange'] = (prev_change.abs() >= self.max_change_pct) | (prev_change1.abs() >= self.max_change_pct)

        # 多周期 RSI
        for period in self.rsi_periods:
            df[f'rsi_{period}'] = _rsi(df['close'], period)

        # RSI 超卖条件: 任一周期 RSI <= 超卖线
        rsi_cols = [f'rsi_{p}' for p in self.rsi_periods]
        df['rsiOversold'] = False
        for col in rsi_cols:
            df['rsiOversold'] = df['rsiOversold'] | (df[col] <= self.rsi_ob)

        # 成交量条件: 5日成交量和 > 100日中位数
        df['vol_rolling'] = df['volume'].rolling(self.vol_window, min_periods=self.vol_window).sum()
        df['vol_median'] = df['vol_rolling'].rolling(self.vol_median_window, min_periods=10).median()
        df['volAboveMedian'] = df['vol_rolling'].notna() & df['vol_median'].notna() & (df['vol_rolling'] > df['vol_median'])

        # 最终买入条件
        df['longCond'] = (
            df['bullishCross']
            & df['jmaUp']
            & (df['wt2'] < self.long_wt2_th)
            & df['rsiOversold']
            & (~df['tooBigChange'])
            & df['volAboveMedian']
        )

        # 卖出信号 (死叉 + JMA向下)
        df['sellSignal'] = df['bearishCross'] & df['jmaDown']

        return df

    def get_required_indicators(self) -> list:
        return ['wt1', 'wt2', 'jma', 'bullishCross', 'bearishCross', 'longCond', 'sellSignal']

    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> Optional[StrategySignal]:
        """生成交易信号"""
        # 使用预计算的指标
        if self._data_with_indicators is not None:
            idx = len(data) - 1
            if idx >= len(self._data_with_indicators):
                return StrategySignal(signal_type=SignalType.HOLD, confidence=0.0, reason="数据越界")
            bar = self._data_with_indicators.iloc[idx]
        else:
            # fallback: 实时计算
            calc = self._calculate_all_indicators(data)
            bar = calc.iloc[-1]

        price = float(bar['close'])

        # 数据不足
        if pd.isna(bar.get('wt1')) or pd.isna(bar.get('jma')):
            return StrategySignal(signal_type=SignalType.HOLD, confidence=0.0, reason="指标数据不足")

        # 买入逻辑
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
                    reason=f"WT金叉+JMA↑ | WT2={wt2_val:.1f} | 成交量放大 | RSI超卖区",
                    metadata={
                        'wt1': float(bar.get('wt1', 0)),
                        'wt2': float(bar.get('wt2', 0)),
                        'jma': float(bar.get('jma', 0)),
                    }
                )

        # 卖出逻辑
        if current_position > 0 or self._holding:
            profit_pct = (price - self._entry_price) / self._entry_price if self._entry_price > 0 else 0

            # 止损
            if profit_pct <= -self.stop_loss_pct:
                self._holding = False
                self._entry_price = 0
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.9,
                    price=price,
                    reason=f"止损触发 | 亏损{profit_pct:.2%}"
                )

            # 止盈
            if profit_pct >= self.take_profit_pct:
                self._holding = False
                self._entry_price = 0
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.85,
                    price=price,
                    reason=f"止盈触发 | 盈利{profit_pct:.2%}"
                )

            # 技术卖出信号
            if bar.get('sellSignal', False):
                self._holding = False
                self._entry_price = 0
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.75,
                    price=price,
                    reason=f"WT死叉+JMA↓ | 盈亏{profit_pct:.2%}"
                )

        return StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.3,
            price=price,
            reason="等待信号"
        )
