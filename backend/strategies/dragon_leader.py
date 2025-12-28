"""
龙头股战法 (Dragon Leader Strategy)
核心理念：聚焦板块/行业龙头，通过强势趋势、换手率、盘整突破
等条件筛选标的，追求波段性收益。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any

import numpy as np
import pandas as pd

from .base import (
    BaseStrategy,
    StrategySignal,
    SignalType,
    StrategyConfig,
    register_strategy
)


def _rolling_rank(series: pd.Series, window: int) -> pd.Series:
    return series.rolling(window).apply(
        lambda x: (x[-1] - x.min()) / (x.max() - x.min() + 1e-9), raw=False
    )


@dataclass
class ConsolidationBox:
    high: float
    low: float
    duration: int


@register_strategy("dragon_leader")
class DragonLeaderStrategy(BaseStrategy):
    """龙头股战法。"""
    
    # 策略描述属性
    description = "聚焦板块/行业龙头，捕捉强势盘整突破，追求波段性收益"

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # 设置中文名称
        self.name = "龙头股战法"
        self.category = "民间策略"
        params = self.parameters
        self.trend_window = params.get("trend_window", 60)
        self.rank_window = params.get("rank_window", 120)
        self.volume_window = params.get("volume_window", 20)
        self.consolidation_min = params.get("consolidation_min", 10)
        self.consolidation_max = params.get("consolidation_max", 40)
        self.breakout_buffer = params.get("breakout_buffer", 0.005)
        self.max_pullback = params.get("max_pullback", 0.08)
        self.take_profit_pct = params.get("take_profit_pct", 0.15)
        self.stop_loss_pct = params.get("stop_loss_pct", 0.05)

        self.active_box: ConsolidationBox | None = None

    def initialize(self, data: pd.DataFrame) -> None:
        if not self.validate_data(data):
            raise ValueError("数据不完整，至少需要OHLCV字段")

        df = data
        df["ema_20"] = df["close"].ewm(span=20).mean()
        df["ema_60"] = df["close"].ewm(span=60).mean()
        df["ema_120"] = df["close"].ewm(span=120).mean()
        # 修复：pandas Series不能使用链式比较，需要分开比较
        df["trend_strength"] = ((df["ema_20"] > df["ema_60"]) & (df["ema_60"] > df["ema_120"])).astype(int)
        df["momentum_rank"] = _rolling_rank(df["close"], self.rank_window)
        df["turnover"] = (df["volume"] * df["close"]) / (df["volume"].rolling(self.volume_window).mean() * df["close"].rolling(self.volume_window).mean())
        df["turnover_ratio"] = df["turnover"].rolling(self.volume_window).mean()
        df["atr20"] = df["close"].diff().abs().rolling(20).mean()

        self._initialized = True

    def _detect_consolidation(self, data: pd.DataFrame) -> ConsolidationBox | None:
        recent = data.tail(self.consolidation_max)
        for length in range(self.consolidation_max, self.consolidation_min - 1, -1):
            window = recent.tail(length)
            high = window["high"].max()
            low = window["low"].min()
            range_pct = (high - low) / low if low else 0
            if range_pct <= self.max_pullback:
                return ConsolidationBox(high=high, low=low, duration=length)
        return None

    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> StrategySignal:
        if not self._initialized:
            self.initialize(data)

        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        price = latest["close"]

        signal = StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.35,
            price=price,
            reason="观望：等待龙头板块信号"
        )

        trend_ok = latest.get("trend_strength", 0) == 1
        momentum_rank = latest.get("momentum_rank", 0.5) or 0.5
        turnover_ratio = latest.get("turnover_ratio", 1.0) or 1.0

        if self.active_box is None:
            box = self._detect_consolidation(data)
            if box:
                self.active_box = box

        breakout = False
        if self.active_box:
            breakout_price = self.active_box.high * (1 + self.breakout_buffer)
            breakout = price > breakout_price and prev["close"] <= breakout_price

        # 放宽入场条件：不再要求所有条件同时满足
        # 条件1：严格突破（需要盘整突破+趋势+动量）
        if current_position == 0 and trend_ok and momentum_rank >= 0.7 and turnover_ratio >= 1.2 and breakout:
            atr = latest.get("atr20", 0.02) or 0.02
            position_size = min(self.risk_params.get("max_position_pct", 0.3), 0.1 + momentum_rank * 0.2)
            signal = StrategySignal(
                signal_type=SignalType.STRONG_BUY,
                confidence=0.82,
                price=price,
                target_price=round(price * (1 + self.take_profit_pct), 2),
                stop_loss=round(self.active_box.low * (1 - self.stop_loss_pct), 2),
                position_size=position_size,
                reason=f"龙头突破：多头排列+高换手+盘整{self.active_box.duration}日后放量突破"
            )
            self.active_box = None
            return signal

        # 条件2：放宽的入场条件（趋势向上+动量较强）
        elif current_position == 0 and trend_ok and momentum_rank >= 0.5:
            # 价格创近期新高
            recent_high = data['high'].tail(20).max()
            if price >= recent_high * 0.98:
                signal = StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.65,
                    price=price,
                    target_price=round(price * (1 + self.take_profit_pct * 0.7), 2),
                    stop_loss=round(price * (1 - self.stop_loss_pct), 2),
                    position_size=0.15,
                    reason=f"龙头趋势：多头排列+动量{momentum_rank:.2f}+接近新高"
                )
                return signal

        # 条件3：更宽松的入场（仅趋势向上）
        elif current_position == 0 and trend_ok and turnover_ratio >= 1.0:
            ema20 = latest.get("ema_20", price)
            # 价格站上EMA20
            if price > ema20 and prev["close"] <= ema20:
                signal = StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.55,
                    price=price,
                    target_price=round(price * 1.08, 2),
                    stop_loss=round(ema20 * 0.98, 2),
                    position_size=0.1,
                    reason="龙头信号：站上EMA20，趋势向上"
                )
                return signal

        if current_position > 0:
            take_profit_hit = price >= current_position * 0 and price >= latest.get("target_price", price * (1 + self.take_profit_pct))
            stop_loss_hit = price <= latest.get("stop_loss", price * (1 - self.stop_loss_pct))
            ema20 = latest.get("ema_20", price)
            ema60 = latest.get("ema_60", price)
            ema20_cross = ema20 < ema60

            if stop_loss_hit or ema20_cross:
                signal = StrategySignal(
                    signal_type=SignalType.STRONG_SELL,
                    confidence=0.85,
                    price=price,
                    reason="跌破关键均线或止损，下撤离场"
                )
                self.active_box = None
                return signal

            if take_profit_hit:
                signal = StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.7,
                    price=price,
                    reason="达到波段目标，建议落袋"
                )
                return signal

        signal.metadata = {
            "trend_ok": trend_ok,
            "momentum_rank": round(float(momentum_rank or 0), 3),
            "turnover_ratio": round(float(turnover_ratio or 0), 3),
            "box_high": getattr(self.active_box, "high", None),
            "box_low": getattr(self.active_box, "low", None)
        }
        return signal

    def get_required_indicators(self) -> list:
        return [
            "ema_20",
            "ema_60",
            "ema_120",
            "trend_strength",
            "momentum_rank",
            "turnover_ratio",
            "atr20"
        ]
