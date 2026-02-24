# -*- coding: utf-8 -*-
"""
Top3 融合策略 (Ensemble Top3)
组合表现最好的三个策略：ema_breakout + sentiment_resonance + graham_margin

投票机制：
- 2个或以上策略同时发出买入信号 → STRONG_BUY
- 1个策略发出买入信号 → BUY
- 信号冲突 → HOLD

权重分配：
- ema_breakout: 40% (夏普最高)
- sentiment_resonance: 30%
- graham_margin: 30%

仓位管理：
- STRONG_BUY: 30% 仓位
- BUY: 15% 仓位
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


@register_strategy("ensemble_top3")
class EnsembleTop3Strategy(BaseStrategy):
    """
    Top3 策略融合 - ema_breakout + sentiment_resonance + graham_margin
    多策略投票制，提高信号质量
    """

    description = "Top3策略融合：ema_breakout + sentiment_resonance + graham_margin 投票制"

    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "Top3融合策略"
        self.category = "融合策略"

        params = self.parameters

        # 信号阈值
        self.strong_buy_threshold = params.get('strong_buy_threshold', 2)  # 2个以上策略同意
        self.buy_threshold = params.get('buy_threshold', 1)  # 1个策略同意

        # 仓位配置
        self.strong_buy_position = params.get('strong_buy_position', 0.30)
        self.buy_position = params.get('buy_position', 0.15)

        # 风控
        self.stop_loss_pct = params.get('stop_loss', 0.08)
        self.take_profit_pct = params.get('take_profit', 0.20)

        # 子策略实例
        self._ema_strategy = None
        self._sentiment_strategy = None
        self._graham_strategy = None

    def initialize(self, data: pd.DataFrame):
        """初始化所有子策略"""
        from .ema_breakout import EMABreakoutStrategy
        from .sentiment_resonance import SentimentResonanceStrategy
        from .graham_margin import GrahamMarginStrategy

        # 创建子策略配置
        sub_config = StrategyConfig(
            name="sub",
            parameters=self.parameters
        )

        self._ema_strategy = EMABreakoutStrategy(sub_config)
        self._sentiment_strategy = SentimentResonanceStrategy(sub_config)
        self._graham_strategy = GrahamMarginStrategy(sub_config)

        # 初始化子策略
        self._ema_strategy.initialize(data)
        self._sentiment_strategy.initialize(data)
        self._graham_strategy.initialize(data)

        self._initialized = True

    def get_required_indicators(self) -> list:
        return ['ensemble_signal', 'sub_signals']

    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> Optional[StrategySignal]:
        """生成融合信号"""
        if not self._initialized:
            self.initialize(data)

        price = float(data['close'].iloc[-1])

        # 获取各子策略信号
        try:
            ema_signal = self._ema_strategy.generate_signal(data, current_position)
            sentiment_signal = self._sentiment_strategy.generate_signal(data, current_position)
            graham_signal = self._graham_strategy.generate_signal(data, current_position)
        except Exception as e:
            return StrategySignal(
                signal_type=SignalType.HOLD,
                confidence=0.0,
                reason=f"子策略信号获取失败: {e}"
            )

        # 解析信号类型
        def is_buy(signal):
            if signal is None:
                return False
            return signal.signal_type in (SignalType.BUY, SignalType.STRONG_BUY)

        def is_sell(signal):
            if signal is None:
                return False
            return signal.signal_type in (SignalType.SELL, SignalType.STRONG_SELL)

        buy_count = sum([is_buy(ema_signal), is_buy(sentiment_signal), is_buy(graham_signal)])
        sell_count = sum([is_sell(ema_signal), is_sell(sentiment_signal), is_sell(graham_signal)])

        # 构建元数据
        sub_signals = {
            'ema': ema_signal.signal_type.value if ema_signal else 'none',
            'sentiment': sentiment_signal.signal_type.value if sentiment_signal else 'none',
            'graham': graham_signal.signal_type.value if graham_signal else 'none',
            'buy_count': buy_count,
            'sell_count': sell_count
        }

        # 融合决策逻辑
        # 情况1：2个以上买入信号 → STRONG_BUY
        if buy_count >= self.strong_buy_threshold and current_position == 0:
            return StrategySignal(
                signal_type=SignalType.STRONG_BUY,
                confidence=0.70 + buy_count * 0.10,
                price=price,
                stop_loss=round(price * (1 - self.stop_loss_pct), 2),
                take_profit=round(price * (1 + self.take_profit_pct), 2),
                position_size=self.strong_buy_position,
                reason=f"Top3共振: {buy_count}/3 策略看多 | EMA:{sub_signals['ema']} | 情绪:{sub_signals['sentiment']} | 格雷厄姆:{sub_signals['graham']}",
                metadata=sub_signals
            )

        # 情况2：1个买入信号 → BUY
        if buy_count >= self.buy_threshold and current_position == 0:
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

        # 情况3：2个以上卖出信号 → SELL
        if sell_count >= self.strong_buy_threshold and current_position > 0:
            return StrategySignal(
                signal_type=SignalType.STRONG_SELL,
                confidence=0.75,
                price=price,
                reason=f"Top3共振看空: {sell_count}/3 策略看空 | EMA:{sub_signals['ema']} | 情绪:{sub_signals['sentiment']} | 格雷厄姆:{sub_signals['graham']}"
            )

        # 情况4：1个卖出信号 → SELL
        if sell_count >= self.buy_threshold and current_position > 0:
            return StrategySignal(
                signal_type=SignalType.SELL,
                confidence=0.60,
                price=price,
                reason=f"Top3弱共振看空: {sell_count}/3 策略看空 | EMA:{sub_signals['ema']} | 情绪:{sub_signals['sentiment']} | 格雷厄姆:{sub_signals['graham']}"
            )

        # 默认：观望
        return StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.30,
            price=price,
            reason=f"Top3分歧 | 看多:{buy_count} | 看空:{sell_count} | EMA:{sub_signals['ema']} | 情绪:{sub_signals['sentiment']} | 格雷厄姆:{sub_signals['graham']}",
            metadata=sub_signals
        )
