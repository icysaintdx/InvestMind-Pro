"""
InvestMindPro 策略系统
集成价值投资、技术分析、量化因子、民间策略等多种交易策略
"""

from .base import (
    BaseStrategy,
    StrategySignal,
    StrategyPerformance,
    SignalType,
    StrategyCategory,
    get_strategy_registry,
    register_strategy
)

from .manager import StrategyManager

# 导入所有策略类，触发 @register_strategy 装饰器注册
from .vegas_adx import VegasADXStrategy
from .ema_breakout import EMABreakoutStrategy
from .buffett_value import BuffettValueStrategy
from .graham_margin import GrahamMarginStrategy
from .lynch_growth import LynchGrowthStrategy
from .macd_crossover import MACDCrossoverStrategy
from .bollinger_breakout import BollingerBreakoutStrategy
from .turtle_trading import TurtleTradingStrategy
from .dragon_leader import DragonLeaderStrategy
from .martingale_refined import MartingaleRefinedStrategy
from .scalping_blade import ScalpingBladeStrategy
from .trident import TridentStrategy
from .sentiment_resonance import SentimentResonanceStrategy
from .debate_weighted import DebateWeightedStrategy
from .limit_up_trading import LimitUpTradingStrategy
from .volume_price_surge import VolumePriceSurgeStrategy

__all__ = [
    'BaseStrategy',
    'StrategySignal',
    'StrategyPerformance',
    'SignalType',
    'StrategyCategory',
    'StrategyManager',
    'get_strategy_registry',
    'register_strategy',
    # 策略类
    'VegasADXStrategy',
    'EMABreakoutStrategy',
    'BuffettValueStrategy',
    'GrahamMarginStrategy',
    'LynchGrowthStrategy',
    'MACDCrossoverStrategy',
    'BollingerBreakoutStrategy',
    'TurtleTradingStrategy',
    'DragonLeaderStrategy',
    'MartingaleRefinedStrategy',
    'ScalpingBladeStrategy',
    'TridentStrategy',
    'SentimentResonanceStrategy',
    'DebateWeightedStrategy',
    'LimitUpTradingStrategy',
    'VolumePriceSurgeStrategy'
]
