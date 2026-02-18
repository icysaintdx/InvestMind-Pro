"""技术分析策略"""

TECHNICAL_STRATEGIES = [
    {
        "id": "vegas_adx", 
        "name": "Vegas+ADX策略", 
        "description": "结合Vegas隧道和ADX趋势强度指标的趋势跟踪策略", 
        "category": "technical", 
        "source": "preset", 
        "icon": "📊",
        "indicators": [
            {"name": "EMA", "type": "technical", "params": {"period": 144}, "weight": 0.4},
            {"name": "EMA", "type": "technical", "params": {"period": 169}, "weight": 0.3},
            {"name": "ADX", "type": "technical", "params": {"period": 14}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "price", "operator": "cross_above", "value": "EMA144", "description": "价格上穿EMA144"},
            {"type": "entry", "indicator": "ADX", "operator": ">", "value": 25, "description": "ADX大于25确认趋势"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "price", "operator": "cross_below", "value": "EMA169", "description": "价格下穿EMA169"},
            {"type": "exit", "indicator": "ADX", "operator": "<", "value": 20, "description": "ADX小于20趋势减弱"}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15, "max_position": 0.30},
        "avg_win_rate": 0.52
    },
    {
        "id": "macd_crossover", 
        "name": "MACD交叉策略", 
        "description": "经典MACD金叉死叉策略，适合震荡市场中的波段操作", 
        "category": "technical", 
        "source": "preset", 
        "icon": "📈",
        "indicators": [
            {"name": "MACD", "type": "technical", "params": {"fast": 12, "slow": 26, "signal": 9}, "weight": 0.6},
            {"name": "Volume", "type": "technical", "params": {"ma_period": 5}, "weight": 0.4}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "MACD", "operator": "cross_above", "value": "Signal", "description": "MACD金叉"},
            {"type": "entry", "indicator": "MACD_Histogram", "operator": ">", "value": 0, "description": "柱状图转正"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "MACD", "operator": "cross_below", "value": "Signal", "description": "MACD死叉"},
            {"type": "exit", "indicator": "MACD_Histogram", "operator": "<", "value": 0, "description": "柱状图转负"}
        ],
        "risk_params": {"stop_loss": 0.04, "take_profit": 0.10, "max_position": 0.40},
        "avg_win_rate": 0.48
    },
    {
        "id": "bollinger_breakout", 
        "name": "布林带突破策略", 
        "description": "布林带突破回归策略，利用价格突破上下轨进行交易", 
        "category": "technical", 
        "source": "preset", 
        "icon": "📊",
        "indicators": [
            {"name": "BOLL", "type": "technical", "params": {"period": 20, "std": 2}, "weight": 0.7},
            {"name": "RSI", "type": "technical", "params": {"period": 14}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "price", "operator": "cross_above", "value": "BOLL_upper", "description": "突破上轨"},
            {"type": "entry", "indicator": "RSI", "operator": "<", "value": 70, "description": "RSI未超买"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "price", "operator": "cross_below", "value": "BOLL_middle", "description": "回落中轨"},
            {"type": "exit", "indicator": "RSI", "operator": ">", "value": 80, "description": "RSI超买"}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.12, "max_position": 0.35},
        "avg_win_rate": 0.45
    },
    {
        "id": "multi_period_ma", 
        "name": "多周期均线上涨战法", 
        "description": "多周期均线共振策略，当5日、10日、20日、60日均线多头排列时入场", 
        "category": "technical", 
        "source": "preset", 
        "icon": "📈",
        "indicators": [
            {"name": "MA", "type": "technical", "params": {"period": 5}, "weight": 0.25},
            {"name": "MA", "type": "technical", "params": {"period": 10}, "weight": 0.25},
            {"name": "MA", "type": "technical", "params": {"period": 20}, "weight": 0.25},
            {"name": "MA", "type": "technical", "params": {"period": 60}, "weight": 0.25}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "MA5", "operator": ">", "value": "MA10", "description": "MA5 > MA10"},
            {"type": "entry", "indicator": "MA10", "operator": ">", "value": "MA20", "description": "MA10 > MA20"},
            {"type": "entry", "indicator": "MA20", "operator": ">", "value": "MA60", "description": "MA20 > MA60"},
            {"type": "entry", "indicator": "price", "operator": ">", "value": "MA5", "description": "价格站上MA5"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "price", "operator": "cross_below", "value": "MA10", "description": "价格跌破MA10"},
            {"type": "exit", "indicator": "MA5", "operator": "cross_below", "value": "MA10", "description": "MA5下穿MA10"}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.20, "max_position": 0.35},
        "avg_win_rate": 0.50
    },
]