"""
EMA短线策略 - EMA5/15
持仓周期: 1-20天
"""

from .ema_breakout import EMABreakoutStrategy
from .base import StrategyConfig, register_strategy

@register_strategy("ema_breakout_short")
class EMABreakoutShortStrategy(EMABreakoutStrategy):
    """EMA短线策略 - 快速进出"""
    
    description = "EMA短线策略(5/15)，持仓1-20天，适合强势股突破"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "EMA短线突破"
        # 短线参数
        self.ema_short = self.parameters.get('ema_short', 5)
        self.ema_mid1 = self.parameters.get('ema_mid1', 8)
        self.ema_mid2 = self.parameters.get('ema_mid2', 12)
        self.ema_long = self.parameters.get('ema_long', 15)
        # 短线严格止损
        self.stop_loss_pct = self.parameters.get('stop_loss_pct', 0.03)  # 3%止损
        self.take_profit_pct = self.parameters.get('take_profit_pct', 0.10)  # 10%止盈
