"""
马丁格尔改良版策略
核心思路：在顺势的前提下进行有限次加仓，利用RSI超卖信号切入，
并通过EMA200趋势过滤、逐级限仓、单轮循环限制等手段控制风险。
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


def _compute_rsi(series: pd.Series, period: int) -> pd.Series:
    """RSI 计算。"""
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False).mean()
    rs = avg_gain / (avg_loss + 1e-9)
    rsi = 100 - (100 / (1 + rs))
    return rsi.fillna(50)


@dataclass
class MartingaleLayerState:
    entry_price: float = 0.0
    layers_filled: int = 0
    cycle_active: bool = False


@register_strategy("martingale_refined")
class MartingaleRefinedStrategy(BaseStrategy):
    """马丁格尔改良版策略。"""
    
    # 策略描述属性
    description = "改良版马丁格尔策略，单轮分层加仓，严格止损和止盈"

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # 设置中文名称
        self.name = "马丁格尔改良策略"
        self.category = "民间策略"
        params = self.parameters
        self.ema_period = params.get("ema_period", 200)
        self.rsi_period = params.get("rsi_period", 14)
        self.rsi_oversold = params.get("rsi_oversold", 38)
        self.rsi_exit = params.get("rsi_exit", 58)
        self.max_layers = params.get("max_layers", 3)
        self.layer_step_pct = params.get("layer_step_pct", 0.02)
        self.take_profit_pct = params.get("take_profit_pct", 0.04)
        self.stop_loss_pct = params.get("stop_loss_pct", 0.06)
        self.base_position_pct = params.get("base_position_pct", 0.06)

        self.state = MartingaleLayerState()
        self.latest_trend = None

    def initialize(self, data: pd.DataFrame) -> None:
        if not self.validate_data(data):
            raise ValueError("数据不完整，至少需要OHLCV字段")
        self._initialized = True
    
    def _calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        df["ema_trend"] = df["close"].ewm(span=self.ema_period).mean()
        df["rsi"] = _compute_rsi(df["close"], self.rsi_period)
        df["volatility"] = df["close"].pct_change().rolling(20).std()
        return df

    def _reset_cycle(self):
        self.state = MartingaleLayerState()

    def _layer_position_size(self, layer: int) -> float:
        return min(self.base_position_pct * (2 ** layer), self.risk_params.get("max_position_pct", 0.3))

    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> StrategySignal:
        if not self._initialized:
            self.initialize(data)
        
        # 计算指标
        df = self._calculate_indicators(data)

        latest = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else latest
        price = latest["close"]
        ema_trend = latest.get("ema_trend", price)
        rsi_value = latest.get("rsi", 50)
        volatility = latest.get("volatility", 0.01) or 0.01

        signal = StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.35,
            price=price,
            reason="观望：未触发马丁格尔循环"
        )

        trend_up = price > ema_trend and prev["close"] > prev.get("ema_trend", prev["close"])
        self.latest_trend = "up" if trend_up else "down"

        # 结束循环条件
        if current_position == 0 and self.state.cycle_active:
            self._reset_cycle()

        # 进入循环
        if not self.state.cycle_active and trend_up and rsi_value <= self.rsi_oversold:
            self.state.cycle_active = True
            self.state.layers_filled = 0
            self.state.entry_price = price

            position_pct = self._layer_position_size(0)
            signal = StrategySignal(
                signal_type=SignalType.BUY,
                confidence=0.7,
                price=price,
                stop_loss=round(price * (1 - self.stop_loss_pct), 2),
                take_profit=round(price * (1 + self.take_profit_pct), 2),
                position_size=position_pct,
                reason="趋势向上 + RSI超卖，启动单轮马丁格尔"
            )
            return signal

        # 加仓逻辑
        if self.state.cycle_active and self.state.layers_filled < self.max_layers:
            next_trigger = self.state.entry_price * (1 - (self.state.layers_filled + 1) * self.layer_step_pct)
            if price <= next_trigger:
                layer = self.state.layers_filled + 1
                position_pct = self._layer_position_size(layer)
                self.state.layers_filled = layer

                signal = StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.6,
                    price=price,
                    stop_loss=round(price * (1 - self.stop_loss_pct), 2),
                    take_profit=round(self.state.entry_price * (1 + self.take_profit_pct), 2),
                    position_size=position_pct,
                    reason=f"第{layer+1}层补仓，价格较首仓回撤{(1 - price / self.state.entry_price) * 100:.1f}%"
                )
                return signal

        # 出场逻辑
        if self.state.cycle_active and current_position > 0:
            reached_target = price >= self.state.entry_price * (1 + self.take_profit_pct)
            rsi_recovery = rsi_value >= self.rsi_exit
            hit_stop = price <= self.state.entry_price * (1 - self.stop_loss_pct)

            if reached_target or rsi_recovery:
                self._reset_cycle()
                signal = StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.8,
                    price=price,
                    reason="达到止盈/RSI修复，退出本轮循环"
                )
                return signal

            if hit_stop:
                self._reset_cycle()
                signal = StrategySignal(
                    signal_type=SignalType.STRONG_SELL,
                    confidence=0.9,
                    price=price,
                    reason="触发整体止损，终止策略循环"
                )
                return signal

        signal.metadata = {
            "trend_up": trend_up,
            "rsi": round(rsi_value, 2),
            "ema_trend": round(ema_trend, 2),
            "layers_filled": self.state.layers_filled,
            "volatility": float(volatility)
        }
        return signal

    def get_required_indicators(self) -> list:
        return [
            "ema_trend",
            "rsi",
            "volatility"
        ]
