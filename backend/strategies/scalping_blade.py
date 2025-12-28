"""
剃头皮策略 (Scalping Blade Strategy)
高频均值回归思路：利用VWAP/Bollinger偏离 + 成交量脉冲捕捉短线回撤，
并通过ATR/时间窗限制风险。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np
import pandas as pd

from .base import (
    BaseStrategy,
    StrategySignal,
    SignalType,
    StrategyConfig,
    register_strategy
)


def _calc_vwap(df: pd.DataFrame, window: int) -> pd.Series:
    typical_price = (df["high"] + df["low"] + df["close"]) / 3
    vol = df["volume"].rolling(window).sum()
    pv = (typical_price * df["volume"]).rolling(window).sum()
    return pv / (vol + 1e-9)


@dataclass
class ScalpingState:
    position_side: Optional[str] = None
    entry_price: float = 0.0
    bars_held: int = 0


@register_strategy("scalping_blade")
class ScalpingBladeStrategy(BaseStrategy):
    """剃头皮策略。"""
    
    # 策略描述属性
    description = "高频短线策略，利用VWAP偏离+成交量脉冲捕捉短线回调机会"

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # 设置中文名称
        self.name = "剃头皮策略"
        self.category = "民间策略"
        params = self.parameters
        self.vwap_window = params.get("vwap_window", 20)
        self.boll_window = params.get("boll_window", 20)
        self.boll_std = params.get("boll_std", 2.0)
        self.volume_spike = params.get("volume_spike", 1.8)
        self.max_hold_bars = params.get("max_hold_bars", 5)
        self.take_profit_pct = params.get("take_profit_pct", 0.01)
        self.stop_loss_pct = params.get("stop_loss_pct", 0.007)

        self.state = ScalpingState()

    def initialize(self, data: pd.DataFrame) -> None:
        if not self.validate_data(data):
            raise ValueError("数据不完整，至少需要OHLCV字段")

        df = data
        df["vwap"] = _calc_vwap(df, self.vwap_window)
        df["ma"] = df["close"].rolling(self.boll_window).mean()
        df["std"] = df["close"].rolling(self.boll_window).std().fillna(0)
        df["upper"] = df["ma"] + self.boll_std * df["std"]
        df["lower"] = df["ma"] - self.boll_std * df["std"]
        df["volume_ratio"] = df["volume"] / df["volume"].rolling(self.vwap_window).mean()
        df["atr"] = (df["high"] - df["low"]).rolling(14).mean().fillna(0)
        self._initialized = True

    def _reset(self):
        self.state = ScalpingState()

    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> StrategySignal:
        if not self._initialized:
            self.initialize(data)

        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        price = latest["close"]
        vwap = latest.get("vwap", price)
        upper = latest.get("upper", price)
        lower = latest.get("lower", price)
        vol_ratio = latest.get("volume_ratio", 1.0)
        atr = latest.get("atr", 0.01) or 0.01

        signal = StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.3,
            price=price,
            reason="观望：等待剃头皮偏离"
        )

        deviation = (price - vwap) / (atr + 1e-9)
        entering = current_position == 0

        if entering:
            # 做空：价格远高于VWAP + 上轨，且放量（放宽条件）
            if price >= upper and deviation > 1.0 and vol_ratio >= self.volume_spike * 0.8:
                self.state.position_side = "short"
                self.state.entry_price = price
                self.state.bars_held = 0
                size = min(self.risk_params.get("max_position_pct", 0.3), 0.1)
                signal = StrategySignal(
                    signal_type=SignalType.STRONG_SELL,
                    confidence=0.75,
                    price=price,
                    target_price=round(price * (1 - self.take_profit_pct), 2),
                    stop_loss=round(price * (1 + self.stop_loss_pct), 2),
                    position_size=size,
                    reason="上轨放量假突破，做空回归VWAP"
                )
                return signal

            # 做多：价格跌破下轨且放量（放宽条件）
            if price <= lower and deviation < -1.0 and vol_ratio >= self.volume_spike * 0.8:
                self.state.position_side = "long"
                self.state.entry_price = price
                self.state.bars_held = 0
                size = min(self.risk_params.get("max_position_pct", 0.3), 0.1)
                signal = StrategySignal(
                    signal_type=SignalType.STRONG_BUY,
                    confidence=0.75,
                    price=price,
                    target_price=round(price * (1 + self.take_profit_pct), 2),
                    stop_loss=round(price * (1 - self.stop_loss_pct), 2),
                    position_size=size,
                    reason="下轨放量恐慌，抢反弹至VWAP"
                )
                return signal

            # 额外入场条件：价格接近下轨且有反弹迹象
            if price <= lower * 1.01 and vol_ratio >= 1.2:
                self.state.position_side = "long"
                self.state.entry_price = price
                self.state.bars_held = 0
                size = min(self.risk_params.get("max_position_pct", 0.3), 0.08)
                signal = StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.6,
                    price=price,
                    target_price=round(price * (1 + self.take_profit_pct), 2),
                    stop_loss=round(price * (1 - self.stop_loss_pct), 2),
                    position_size=size,
                    reason="接近下轨，尝试抢反弹"
                )
                return signal

        else:
            self.state.bars_held += 1
            side = self.state.position_side
            entry = self.state.entry_price
            take_profit = entry * (1 + self.take_profit_pct) if side == "long" else entry * (1 - self.take_profit_pct)
            stop_loss = entry * (1 - self.stop_loss_pct) if side == "long" else entry * (1 + self.stop_loss_pct)

            take_hit = (side == "long" and price >= take_profit) or (side == "short" and price <= take_profit)
            stop_hit = (side == "long" and price <= stop_loss) or (side == "short" and price >= stop_loss)
            mean_revert = (side == "long" and price >= vwap) or (side == "short" and price <= vwap)
            time_out = self.state.bars_held >= self.max_hold_bars

            if take_hit or mean_revert or time_out or stop_hit:
                action = SignalType.SELL if side == "long" else SignalType.BUY
                confidence = 0.8 if take_hit or mean_revert else 0.6
                reason = "触及目标/回归VWAP" if take_hit or mean_revert else "时间/止损退出"
                self._reset()
                return StrategySignal(
                    signal_type=action,
                    confidence=confidence,
                    price=price,
                    reason=reason
                )

        signal.metadata = {
            "deviation_atr": round(float(deviation), 3),
            "vol_ratio": round(float(vol_ratio), 2),
            "side": self.state.position_side,
            "bars_held": self.state.bars_held
        }
        return signal

    def get_required_indicators(self) -> list:
        return ["vwap", "upper", "lower", "volume_ratio", "atr"]
