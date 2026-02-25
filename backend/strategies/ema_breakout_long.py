"""
EMA中长线策略 - EMA30/60
持仓周期: 60-250天
"""

from .ema_breakout import EMABreakoutStrategy
from .base import StrategyConfig, register_strategy

@register_strategy("ema_breakout_long")
class EMABreakoutLongStrategy(EMABreakoutStrategy):
    """EMA中长线策略 - 大趋势跟踪"""
    
    description = "EMA中长线策略(30/60)，持仓60-250天，适合大趋势捕捉"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "EMA中长线突破"
        # 中长线参数
        self.ema_short = self.parameters.get('ema_short', 30)
        self.ema_mid1 = self.parameters.get('ema_mid1', 40)
        self.ema_mid2 = self.parameters.get('ema_mid2', 50)
        self.ema_long = self.parameters.get('ema_long', 60)
        # 中长线宽松止损
        self.stop_loss_pct = self.parameters.get('stop_loss_pct', 0.08)  # 8%止损
        self.take_profit_pct = self.parameters.get('take_profit_pct', 0.30)  # 30%止盈
