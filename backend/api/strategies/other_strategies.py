"""趋势跟踪、AI合成、民间策略"""

# 趋势跟踪策略
TREND_STRATEGIES = [
    {
        "id": "turtle_trading", 
        "name": "海龟交易法则", 
        "description": "唐奇安通道突破，经典的趋势跟踪系统", 
        "category": "trend_following", 
        "source": "preset", 
        "icon": "🐢",
        "indicators": [
            {"name": "Donchian", "type": "technical", "params": {"period": 20}, "weight": 0.5},
            {"name": "ATR", "type": "technical", "params": {"period": 20}, "weight": 0.5}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "price", "operator": "cross_above", "value": "Donchian_high", "description": "突破20日高点"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "price", "operator": "cross_below", "value": "Donchian_low_10", "description": "跌破10日低点"}
        ],
        "risk_params": {"stop_loss": 0.08, "take_profit": 0.20, "max_position": 0.40},
        "avg_win_rate": 0.40
    },
]

# AI合成策略
AI_STRATEGIES = [
    {
        "id": "sentiment_resonance", 
        "name": "情绪共振策略", 
        "description": "新闻情绪+技术+资金流向多维度共振", 
        "category": "ai_composite", 
        "source": "preset", 
        "icon": "🤖",
        "indicators": [
            {"name": "News_Sentiment", "type": "sentiment", "params": {}, "weight": 0.4},
            {"name": "Money_Flow", "type": "flow", "params": {}, "weight": 0.3},
            {"name": "RSI", "type": "technical", "params": {"period": 14}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "News_Sentiment", "operator": ">", "value": 0.6, "description": "新闻情绪积极"},
            {"type": "entry", "indicator": "Money_Flow", "operator": ">", "value": 0, "description": "资金净流入"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "News_Sentiment", "operator": "<", "value": -0.3, "description": "新闻情绪转负"},
            {"type": "exit", "indicator": "Money_Flow", "operator": "<", "value": 0, "description": "资金净流出"}
        ],
        "risk_params": {"stop_loss": 0.04, "take_profit": 0.12, "max_position": 0.40},
        "avg_win_rate": 0.55
    },
    {
        "id": "debate_weighted", 
        "name": "多空辩论加权策略", 
        "description": "21智能体多空辩论，综合多方观点形成交易决策", 
        "category": "ai_composite", 
        "source": "preset", 
        "icon": "⚖️",
        "indicators": [
            {"name": "Bull_Score", "type": "ai", "params": {}, "weight": 0.5},
            {"name": "Bear_Score", "type": "ai", "params": {}, "weight": 0.5}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "Bull_Score", "operator": ">", "value": 60, "description": "多方得分大于60"},
            {"type": "entry", "indicator": "Bull_Score", "operator": ">", "value": "Bear_Score", "description": "多方观点占优"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "Bear_Score", "operator": ">", "value": "Bull_Score", "description": "空方观点占优"},
            {"type": "exit", "indicator": "Bull_Score", "operator": "<", "value": 40, "description": "多方得分下降"}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15, "max_position": 0.35},
        "avg_win_rate": 0.58
    },
]

# 民间策略
FOLK_STRATEGIES = [
    {
        "id": "limit_up_trading", 
        "name": "涨停板战法", 
        "description": "首板涨停+T+1，追踪强势股的短线策略", 
        "category": "folk_strategy", 
        "source": "preset", 
        "icon": "🚀",
        "indicators": [
            {"name": "Limit_Up", "type": "technical", "params": {}, "weight": 0.5},
            {"name": "Volume", "type": "technical", "params": {"ma_period": 5}, "weight": 0.3},
            {"name": "Turnover_Rate", "type": "technical", "params": {}, "weight": 0.2}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "Limit_Up", "operator": "==", "value": True, "description": "首板涨停"},
            {"type": "entry", "indicator": "Volume", "operator": ">", "value": "MA5*1.5", "description": "成交量放大"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "price", "operator": "<", "value": "open", "description": "跌破开盘价"},
            {"type": "exit", "indicator": "Limit_Down", "operator": "==", "value": True, "description": "跌停"}
        ],
        "risk_params": {"stop_loss": 0.03, "take_profit": 0.05, "max_position": 0.20},
        "avg_win_rate": 0.45
    },
    {
        "id": "volume_price_surge", 
        "name": "量价齐升战法", 
        "description": "量价配合短线，成交量放大配合价格上涨", 
        "category": "folk_strategy", 
        "source": "preset", 
        "icon": "📊",
        "indicators": [
            {"name": "Volume", "type": "technical", "params": {"ma_period": 5}, "weight": 0.5},
            {"name": "Price_Change", "type": "technical", "params": {}, "weight": 0.5}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "Volume", "operator": ">", "value": "MA5*2", "description": "成交量放大2倍"},
            {"type": "entry", "indicator": "Price_Change", "operator": ">", "value": 3, "description": "涨幅大于3%"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "Volume", "operator": "<", "value": "MA5", "description": "成交量萎缩"},
            {"type": "exit", "indicator": "Price_Change", "operator": "<", "value": -2, "description": "跌幅超过2%"}
        ],
        "risk_params": {"stop_loss": 0.04, "take_profit": 0.08, "max_position": 0.30},
        "avg_win_rate": 0.42
    },
    {
        "id": "dragon_leader", 
        "name": "龙头股战法", 
        "description": "板块龙头盘整突破，追踪行业领头羊", 
        "category": "folk_strategy", 
        "source": "preset", 
        "icon": "🐉",
        "indicators": [
            {"name": "Sector_Rank", "type": "fundamental", "params": {}, "weight": 0.4},
            {"name": "Market_Cap_Rank", "type": "fundamental", "params": {}, "weight": 0.3},
            {"name": "Volume", "type": "technical", "params": {"ma_period": 5}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "Sector_Rank", "operator": "==", "value": 1, "description": "板块龙头"},
            {"type": "entry", "indicator": "price", "operator": "cross_above", "value": "resistance", "description": "突破盘整区间"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "price", "operator": "<", "value": "support", "description": "跌破支撑位"},
            {"type": "exit", "indicator": "Sector_Rank", "operator": ">", "value": 3, "description": "失去龙头地位"}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15, "max_position": 0.35},
        "avg_win_rate": 0.48
    },
]