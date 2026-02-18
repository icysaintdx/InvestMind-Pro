"""
策略数据包
汇总所有预设策略
"""

from .technical_strategies import TECHNICAL_STRATEGIES
from .value_strategies import VALUE_STRATEGIES
from .other_strategies import TREND_STRATEGIES, AI_STRATEGIES, FOLK_STRATEGIES
from .institutional_strategies import INSTITUTIONAL_STRATEGIES

# 合并所有预设策略 (共22个)
PRESET_STRATEGIES = (
    TECHNICAL_STRATEGIES +      # 4个技术分析策略
    VALUE_STRATEGIES +          # 5个价值投资策略
    TREND_STRATEGIES +          # 1个趋势跟踪策略
    AI_STRATEGIES +             # 2个AI合成策略
    FOLK_STRATEGIES +           # 3个民间策略
    INSTITUTIONAL_STRATEGIES    # 5个机构持仓策略 (新增2个: 科威特、葛卫东、社保、QFII、北向资金)
)

# 策略分类
STRATEGY_CATEGORIES = {
    "technical": {"name": "技术分析", "icon": "📊", "count": len(TECHNICAL_STRATEGIES)},
    "value_investing": {"name": "价值投资", "icon": "💎", "count": len(VALUE_STRATEGIES)},
    "trend_following": {"name": "趋势跟踪", "icon": "🐢", "count": len(TREND_STRATEGIES)},
    "ai_composite": {"name": "AI合成", "icon": "🤖", "count": len(AI_STRATEGIES)},
    "folk_strategy": {"name": "民间策略", "icon": "🚀", "count": len(FOLK_STRATEGIES)},
    "institutional": {"name": "机构持仓", "icon": "🏛️", "count": len(INSTITUTIONAL_STRATEGIES)},
}

__all__ = [
    'PRESET_STRATEGIES',
    'STRATEGY_CATEGORIES',
    'TECHNICAL_STRATEGIES',
    'VALUE_STRATEGIES', 
    'TREND_STRATEGIES',
    'AI_STRATEGIES',
    'FOLK_STRATEGIES',
    'INSTITUTIONAL_STRATEGIES',
]