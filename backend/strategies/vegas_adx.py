"""
Vegas+ADX 策略实现
Vegas通道 + ADX趋势过滤器
适用于趋势行情
"""

import pandas as pd
import numpy as np
from typing import Optional
from .base import (
    BaseStrategy, 
    StrategySignal, 
    SignalType, 
    StrategyConfig,
    register_strategy
)


@register_strategy("vegas_adx")
class VegasADXStrategy(BaseStrategy):
    """
    Vegas+ADX 策略
    
    交易逻辑：
    1. Vegas通道（EMA12/144/169）判断趋势方向
    2. ADX>30 确认趋势强度
    3. 价格突破通道边界入场
    4. 动态止损跟踪
    
    参数：
    - ema_fast: 快速均线（默认12）
    - ema_slow1: 慢速均线1（默认144）
    - ema_slow2: 慢速均线2（默认169）
    - adx_period: ADX周期（默认14）
    - adx_threshold: ADX阈值（默认30）
    """
    
    # 策略描述属性
    description = "基于Vegas通道和ADX指标的趋势跟踪策略，在强趋势中表现优异"

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # 设置中文名称
        self.name = "Vegas+ADX趋势策略"
        self.category = "技术分析"
        
        # 策略参数
        self.ema_fast = self.parameters.get('ema_fast', 12)
        self.ema_slow1 = self.parameters.get('ema_slow1', 144)
        self.ema_slow2 = self.parameters.get('ema_slow2', 169)
        self.adx_period = self.parameters.get('adx_period', 14)
        self.adx_threshold = self.parameters.get('adx_threshold', 30)
        
        # 内部状态
        self._last_signal = None
        self._entry_price = 0

    def initialize(self, data: pd.DataFrame) -> None:
        """初始化策略，计算所需指标"""
        if not self.validate_data(data):
            raise ValueError("数据格式不正确")
        
        # 计算 EMA
        data[f'ema_{self.ema_fast}'] = data['close'].ewm(span=self.ema_fast).mean()
        data[f'ema_{self.ema_slow1}'] = data['close'].ewm(span=self.ema_slow1).mean()
        data[f'ema_{self.ema_slow2}'] = data['close'].ewm(span=self.ema_slow2).mean()
        
        # 计算 Vegas 通道
        data['vegas_upper'] = data[[f'ema_{self.ema_slow1}', f'ema_{self.ema_slow2}']].max(axis=1)
        data['vegas_lower'] = data[[f'ema_{self.ema_slow1}', f'ema_{self.ema_slow2}']].min(axis=1)
        data['vegas_mid'] = (data['vegas_upper'] + data['vegas_lower']) / 2
        
        # 计算 ADX
        data['adx'] = self._calculate_adx(data, self.adx_period)
        
        self._initialized = True

    def generate_signal(
        self, 
        data: pd.DataFrame,
        current_position: int = 0
    ) -> StrategySignal:
        """生成交易信号"""
        if not self._initialized:
            self.initialize(data)
        
        # 获取最新数据
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        
        price = latest['close']
        ema_fast = latest[f'ema_{self.ema_fast}']
        vegas_upper = latest['vegas_upper']
        vegas_lower = latest['vegas_lower']
        vegas_mid = latest['vegas_mid']
        adx = latest['adx']
        
        # 默认信号
        signal = StrategySignal(
            signal_type=SignalType.HOLD,
            price=price,
            confidence=0.3
        )
        
        # 趋势强度检查
        trend_strength = adx > self.adx_threshold
        
        # 做多信号
        if current_position <= 0:  # 空仓或持空
            # 条件1：价格突破上轨
            breakout_up = price > vegas_upper and prev['close'] <= prev['vegas_upper']
            # 条件2：快速EMA在通道之上
            ema_above = ema_fast > vegas_upper
            # 条件3：趋势够强
            
            if (breakout_up or ema_above) and trend_strength:
                signal.signal_type = SignalType.STRONG_BUY if adx > 40 else SignalType.BUY
                signal.confidence = min(0.9, 0.5 + (adx - 30) / 100)
                signal.stop_loss = self.calculate_stop_loss(price, 'buy')
                signal.take_profit = self.calculate_take_profit(price, 'buy')
                signal.reason = f"Vegas突破做多: ADX={adx:.1f}, 突破上轨"
                self._entry_price = price
        
        # 做空信号
        elif current_position >= 0:  # 空仓或持多
            # 条件1：价格跌破下轨
            breakout_down = price < vegas_lower and prev['close'] >= prev['vegas_lower']
            # 条件2：快速EMA在通道之下
            ema_below = ema_fast < vegas_lower
            
            if (breakout_down or ema_below) and trend_strength:
                signal.signal_type = SignalType.STRONG_SELL if adx > 40 else SignalType.SELL
                signal.confidence = min(0.9, 0.5 + (adx - 30) / 100)
                signal.stop_loss = self.calculate_stop_loss(price, 'sell')
                signal.take_profit = self.calculate_take_profit(price, 'sell')
                signal.reason = f"Vegas突破做空: ADX={adx:.1f}, 跌破下轨"
                self._entry_price = price
        
        # 持仓管理（动态止损）
        if current_position != 0:
            # 追踪止损
            if current_position > 0:  # 持多
                # 价格跌破中轨止损
                if price < vegas_mid:
                    signal.signal_type = SignalType.SELL
                    signal.confidence = 0.7
                    signal.reason = "跌破Vegas中轨止损"
                # 趋势减弱平仓
                elif adx < 25:
                    signal.signal_type = SignalType.SELL
                    signal.confidence = 0.6
                    signal.reason = f"趋势减弱平仓: ADX={adx:.1f}"
            
            else:  # 持空
                # 价格突破中轨止损
                if price > vegas_mid:
                    signal.signal_type = SignalType.BUY
                    signal.confidence = 0.7
                    signal.reason = "突破Vegas中轨止损"
                # 趋势减弱平仓
                elif adx < 25:
                    signal.signal_type = SignalType.BUY
                    signal.confidence = 0.6
                    signal.reason = f"趋势减弱平仓: ADX={adx:.1f}"
        
        # 记录额外信息
        signal.metadata = {
            "ema_fast": round(ema_fast, 2),
            "vegas_upper": round(vegas_upper, 2),
            "vegas_lower": round(vegas_lower, 2),
            "vegas_mid": round(vegas_mid, 2),
            "adx": round(adx, 1),
            "trend_strength": trend_strength
        }
        
        self._last_signal = signal
        return signal

    def get_required_indicators(self) -> list:
        """获取策略所需的技术指标"""
        return [
            f'ema_{self.ema_fast}',
            f'ema_{self.ema_slow1}',
            f'ema_{self.ema_slow2}',
            'vegas_upper',
            'vegas_lower',
            'vegas_mid',
            'adx'
        ]

    def _calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算 ADX 指标"""
        high = df['high']
        low = df['low']
        close = df['close']
        
        # 计算 True Range
        tr1 = high - low
        tr2 = abs(high - close.shift())
        tr3 = abs(low - close.shift())
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        
        # 计算 DM (Directional Movement)
        up_move = high - high.shift()
        down_move = low.shift() - low
        
        pos_dm = pd.Series(0.0, index=df.index)
        neg_dm = pd.Series(0.0, index=df.index)
        
        pos_dm[(up_move > down_move) & (up_move > 0)] = up_move
        neg_dm[(down_move > up_move) & (down_move > 0)] = down_move
        
        # 计算 DI (Directional Indicator)
        pos_di = 100 * (pos_dm.rolling(window=period).mean() / atr)
        neg_di = 100 * (neg_dm.rolling(window=period).mean() / atr)
        
        # 计算 DX 和 ADX
        dx = 100 * abs(pos_di - neg_di) / (pos_di + neg_di + 0.001)
        adx = dx.rolling(window=period).mean()
        
        return adx


# 创建预配置的策略实例
def create_vegas_adx_strategy() -> VegasADXStrategy:
    """创建 Vegas+ADX 策略实例"""
    config = StrategyConfig(
        name="Vegas+ADX",
        version="1.0.0",
        category="technical",
        description="Vegas通道结合ADX趋势过滤的趋势跟踪策略",
        author="InvestMind Team",
        parameters={
            "ema_fast": 12,
            "ema_slow1": 144,
            "ema_slow2": 169,
            "adx_period": 14,
            "adx_threshold": 30
        },
        risk_params={
            "max_position_pct": 0.3,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.15,
            "max_drawdown_pct": 0.10
        }
    )
    return VegasADXStrategy(config)
