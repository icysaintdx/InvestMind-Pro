"""
EMA中短线策略 - EMA12/26
持仓周期: 20-60天
"""

from .ema_breakout import EMABreakoutStrategy
from .base import StrategyConfig, register_strategy

@register_strategy("ema_breakout_mid")
class EMABreakoutMidStrategy(EMABreakoutStrategy):
    """EMA中短线策略 - 趋势确认"""
    
    description = "EMA中短线策略(12/26)，持仓20-60天，适合趋势跟踪"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "EMA中短线突破"
        # 中短线参数
        self.ema_short = self.parameters.get('ema_short', 12)
        self.ema_mid1 = self.parameters.get('ema_mid1', 18)
        self.ema_mid2 = self.parameters.get('ema_mid2', 22)
        self.ema_long = self.parameters.get('ema_long', 26)
        # 中短线适中止损
        self.stop_loss_pct = self.parameters.get('stop_loss_pct', 0.05)  # 5%止损
        self.take_profit_pct = self.parameters.get('take_profit_pct', 0.15)  # 15%止盈
