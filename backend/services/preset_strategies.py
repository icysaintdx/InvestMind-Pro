"""
预设策略数据
这些策略会在系统初始化时导入到数据库中
"""

PRESET_STRATEGIES = [
    # ==================== 技术分析策略 ====================
    {
        "name": "Vegas+ADX策略",
        "description": "结合Vegas隧道(EMA144/169)和ADX趋势强度指标的趋势跟踪策略",
        "category": "technical",
        "icon": "📊",
        "indicators": [
            {"name": "EMA", "type": "trend", "params": {"periods": [144, 169]}, "weight": 0.4},
            {"name": "ADX", "type": "trend", "params": {"period": 14}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"name": "价格突破Vegas隧道", "logic": "AND", "conditions": [
                {"indicator": "price", "operator": ">", "compare_to": "EMA144"},
                {"indicator": "ADX", "operator": ">", "value": 25}
            ], "weight": 1.0}
        ],
        "exit_conditions": [
            {"name": "价格跌破Vegas隧道", "conditions": [
                {"indicator": "price", "operator": "<", "compare_to": "EMA169"}
            ]}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15, "max_position": 0.30}
    },
    {
        "name": "MACD交叉策略",
        "description": "经典MACD金叉死叉策略，结合成交量确认",
        "category": "technical",
        "icon": "📈",
        "indicators": [
            {"name": "MACD", "type": "momentum", "params": {"fast": 12, "slow": 26, "signal": 9}, "weight": 0.6},
            {"name": "Volume", "type": "volume", "params": {"ma_periods": [5, 10]}, "weight": 0.4}
        ],
        "entry_conditions": [
            {"name": "MACD金叉", "logic": "AND", "conditions": [
                {"indicator": "MACD_DIF", "operator": "cross_above", "compare_to": "MACD_DEA"}
            ], "weight": 1.0}
        ],
        "exit_conditions": [
            {"name": "MACD死叉", "conditions": [
                {"indicator": "MACD_DIF", "operator": "cross_below", "compare_to": "MACD_DEA"}
            ]}
        ],
        "risk_params": {"stop_loss": 0.04, "take_profit": 0.10, "max_position": 0.40}
    },
    {
        "name": "布林带突破策略",
        "description": "布林带突破回归策略，结合RSI过滤假突破",
        "category": "technical",
        "icon": "📊",
        "indicators": [
            {"name": "BOLL", "type": "volatility", "params": {"period": 20, "std_dev": 2}, "weight": 0.7},
            {"name": "RSI", "type": "oscillator", "params": {"period": 14}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"name": "突破上轨", "logic": "AND", "conditions": [
                {"indicator": "price", "operator": ">", "compare_to": "BOLL_UPPER"},
                {"indicator": "RSI", "operator": "<", "value": 70}
            ], "weight": 1.0}
        ],
        "exit_conditions": [
            {"name": "回落中轨", "conditions": [
                {"indicator": "price", "operator": "<", "compare_to": "BOLL_MIDDLE"}
            ]}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.12, "max_position": 0.35}
    },
    {
        "name": "多周期均线上涨战法",
        "description": "多周期均线共振策略，当均线多头排列时入场",
        "category": "technical",
        "icon": "📈",
        "indicators": [
            {"name": "MA", "type": "trend", "params": {"periods": [5, 10, 20, 60]}, "weight": 1.0}
        ],
        "entry_conditions": [
            {"name": "均线多头排列", "logic": "AND", "conditions": [
                {"indicator": "MA5", "operator": ">", "compare_to": "MA10"},
                {"indicator": "MA10", "operator": ">", "compare_to": "MA20"},
                {"indicator": "MA20", "operator": ">", "compare_to": "MA60"}
            ], "weight": 1.0}
        ],
        "exit_conditions": [
            {"name": "价格跌破MA10", "conditions": [
                {"indicator": "price", "operator": "<", "compare_to": "MA10"}
            ]}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.20, "max_position": 0.35}
    },
    {
        "name": "KDJ超卖反弹策略",
        "description": "利用KDJ指标捕捉超卖反弹机会",
        "category": "technical",
        "icon": "📉",
        "indicators": [
            {"name": "KDJ", "type": "oscillator", "params": {"n": 9}, "weight": 0.7},
            {"name": "Volume", "type": "volume", "params": {"ma_periods": [5]}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"name": "KDJ超卖金叉", "logic": "AND", "conditions": [
                {"indicator": "KDJ_K", "operator": "cross_above", "compare_to": "KDJ_D"},
                {"indicator": "KDJ_J", "operator": "<", "value": 20}
            ], "weight": 1.0}
        ],
        "exit_conditions": [
            {"name": "KDJ超买", "conditions": [
                {"indicator": "KDJ_J", "operator": ">", "value": 80}
            ]}
        ],
        "risk_params": {"stop_loss": 0.04, "take_profit": 0.08, "max_position": 0.30}
    },
    
    # ==================== 价值投资策略 ====================
    {
        "name": "格雷厄姆型风格策略",
        "description": "严格遵循格雷厄姆的选股标准：低PE、低PB、高股息、稳定盈利",
        "category": "fundamental",
        "icon": "📚",
        "indicators": [
            {"name": "PE", "type": "valuation", "params": {"max": 10}, "weight": 0.25},
            {"name": "PB", "type": "valuation", "params": {"max": 1.2}, "weight": 0.25},
            {"name": "Dividend_Yield", "type": "income", "params": {"min": 3}, "weight": 0.25},
            {"name": "Earnings_Stability", "type": "quality", "params": {"years": 10}, "weight": 0.25}
        ],
        "entry_conditions": [
            {"name": "低估值", "logic": "AND", "conditions": [
                {"indicator": "PE", "operator": "<", "value": 10},
                {"indicator": "PB", "operator": "<", "value": 1.2}
            ], "weight": 0.5}
        ],
        "exit_conditions": [
            {"name": "估值过高", "conditions": [
                {"indicator": "PE", "operator": ">", "value": 20}
            ]}
        ],
        "risk_params": {"stop_loss": 0.20, "take_profit": 0.60, "max_position": 0.20}
    },
    {
        "name": "戴维斯型风格策略",
        "description": "戴维斯双击策略：寻找低PE且盈利增长的公司",
        "category": "fundamental",
        "icon": "🎯",
        "indicators": [
            {"name": "PE", "type": "valuation", "params": {"max": 15, "min": 5}, "weight": 0.3},
            {"name": "EPS_Growth", "type": "growth", "params": {"min": 15}, "weight": 0.3},
            {"name": "ROE", "type": "profitability", "params": {"min": 12}, "weight": 0.2},
            {"name": "PEG", "type": "valuation", "params": {"max": 1}, "weight": 0.2}
        ],
        "entry_conditions": [
            {"name": "低PE高增长", "logic": "AND", "conditions": [
                {"indicator": "PE", "operator": "<", "value": 15},
                {"indicator": "EPS_Growth", "operator": ">", "value": 15}
            ], "weight": 0.6}
        ],
        "exit_conditions": [
            {"name": "戴维斯双杀风险", "conditions": [
                {"indicator": "PE", "operator": ">", "value": 30}
            ]}
        ],
        "risk_params": {"stop_loss": 0.15, "take_profit": 1.00, "max_position": 0.30}
    },
    
    # ==================== 机构持仓策略 ====================
    {
        "name": "科威特政府投资局持仓策略",
        "description": "跟踪科威特政府投资局（KIA）的A股持仓变动",
        "category": "institutional",
        "icon": "🏛️",
        "indicators": [
            {"name": "KIA_Holding", "type": "institutional", "params": {}, "weight": 0.4},
            {"name": "KIA_Change", "type": "institutional", "params": {"quarters": 2}, "weight": 0.3},
            {"name": "PE", "type": "valuation", "params": {"max": 30}, "weight": 0.15},
            {"name": "ROE", "type": "profitability", "params": {"min": 10}, "weight": 0.15}
        ],
        "entry_conditions": [
            {"name": "KIA增持", "logic": "AND", "conditions": [
                {"indicator": "KIA_Holding", "operator": ">", "value": 0},
                {"indicator": "KIA_Change", "operator": ">", "value": 0}
            ], "weight": 0.7}
        ],
        "exit_conditions": [
            {"name": "KIA清仓", "conditions": [
                {"indicator": "KIA_Holding", "operator": "==", "value": 0}
            ]}
        ],
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.50, "max_position": 0.25}
    },
    {
        "name": "葛卫东流通股东策略",
        "description": "跟踪知名私募大佬葛卫东的持仓变动",
        "category": "institutional",
        "icon": "👤",
        "indicators": [
            {"name": "GWD_Holding", "type": "institutional", "params": {}, "weight": 0.4},
            {"name": "GWD_Change", "type": "institutional", "params": {"quarters": 1}, "weight": 0.3},
            {"name": "Revenue_Growth", "type": "growth", "params": {"min": 15}, "weight": 0.15},
            {"name": "PE", "type": "valuation", "params": {"max": 40}, "weight": 0.15}
        ],
        "entry_conditions": [
            {"name": "葛卫东增持", "logic": "AND", "conditions": [
                {"indicator": "GWD_Holding", "operator": ">", "value": 0},
                {"indicator": "GWD_Change", "operator": ">", "value": 0}
            ], "weight": 0.7}
        ],
        "exit_conditions": [
            {"name": "葛卫东清仓", "conditions": [
                {"indicator": "GWD_Holding", "operator": "==", "value": 0}
            ]}
        ],
        "risk_params": {"stop_loss": 0.12, "take_profit": 0.40, "max_position": 0.25}
    },
    {
        "name": "社保流通股东策略",
        "description": "跟踪社保基金的持仓变动，社保基金以长期价值投资著称",
        "category": "institutional",
        "icon": "🏦",
        "indicators": [
            {"name": "SSF_Holding", "type": "institutional", "params": {}, "weight": 0.4},
            {"name": "SSF_Change", "type": "institutional", "params": {"quarters": 2}, "weight": 0.3},
            {"name": "ROE", "type": "profitability", "params": {"min": 12}, "weight": 0.15},
            {"name": "Dividend_Yield", "type": "income", "params": {"min": 2}, "weight": 0.15}
        ],
        "entry_conditions": [
            {"name": "社保增持", "logic": "AND", "conditions": [
                {"indicator": "SSF_Holding", "operator": ">", "value": 0},
                {"indicator": "SSF_Change", "operator": ">", "value": 0}
            ], "weight": 0.7}
        ],
        "exit_conditions": [
            {"name": "社保清仓", "conditions": [
                {"indicator": "SSF_Holding", "operator": "==", "value": 0}
            ]}
        ],
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.60, "max_position": 0.30}
    },
    {
        "name": "北向资金流入策略",
        "description": "跟踪沪深港通北向资金流入，捕捉外资青睐的标的",
        "category": "institutional",
        "icon": "📈",
        "indicators": [
            {"name": "Northbound_Holding", "type": "institutional", "params": {}, "weight": 0.35},
            {"name": "Northbound_Change", "type": "institutional", "params": {"days": 5}, "weight": 0.35},
            {"name": "PE", "type": "valuation", "params": {"max": 40}, "weight": 0.15},
            {"name": "Volume", "type": "volume", "params": {"ma_periods": [5]}, "weight": 0.15}
        ],
        "entry_conditions": [
            {"name": "北向资金流入", "logic": "AND", "conditions": [
                {"indicator": "Northbound_Change", "operator": ">", "value": 0},
                {"indicator": "Northbound_Holding", "operator": ">", "value": 1}
            ], "weight": 0.7}
        ],
        "exit_conditions": [
            {"name": "北向资金持续流出", "conditions": [
                {"indicator": "Northbound_Change", "operator": "<", "value": -5}
            ]}
        ],
        "risk_params": {"stop_loss": 0.08, "take_profit": 0.25, "max_position": 0.35}
    },
    
    # ==================== 民间策略 ====================
    {
        "name": "涨停板战法",
        "description": "首板涨停+T+1，追踪强势股的短线策略",
        "category": "folk",
        "icon": "🚀",
        "indicators": [
            {"name": "Limit_Up", "type": "price_action", "params": {}, "weight": 0.5},
            {"name": "Volume", "type": "volume", "params": {"ma_periods": [5]}, "weight": 0.3},
            {"name": "Turnover_Rate", "type": "liquidity", "params": {}, "weight": 0.2}
        ],
        "entry_conditions": [
            {"name": "首板涨停", "logic": "AND", "conditions": [
                {"indicator": "Limit_Up", "operator": "==", "value": True},
                {"indicator": "Limit_Up_Count", "operator": "==", "value": 1}
            ], "weight": 0.6}
        ],
        "exit_conditions": [
            {"name": "跌破开盘价", "conditions": [
                {"indicator": "price", "operator": "<", "compare_to": "open"}
            ]}
        ],
        "risk_params": {"stop_loss": 0.03, "take_profit": 0.05, "max_position": 0.20}
    },
    {
        "name": "量价齐升战法",
        "description": "量价配合短线，成交量放大配合价格上涨",
        "category": "folk",
        "icon": "📊",
        "indicators": [
            {"name": "Volume", "type": "volume", "params": {"ma_periods": [5, 10]}, "weight": 0.5},
            {"name": "Price_Change", "type": "price_action", "params": {}, "weight": 0.5}
        ],
        "entry_conditions": [
            {"name": "量价齐升", "logic": "AND", "conditions": [
                {"indicator": "volume", "operator": ">", "compare_to": "VOL_MA5"},
                {"indicator": "Price_Change", "operator": ">", "value": 3}
            ], "weight": 1.0}
        ],
        "exit_conditions": [
            {"name": "量能萎缩", "conditions": [
                {"indicator": "volume", "operator": "<", "compare_to": "VOL_MA5"}
            ]}
        ],
        "risk_params": {"stop_loss": 0.04, "take_profit": 0.08, "max_position": 0.30}
    },
    {
        "name": "龙头股战法",
        "description": "板块龙头盘整突破，追踪行业领头羊",
        "category": "folk",
        "icon": "🐉",
        "indicators": [
            {"name": "Sector_Rank", "type": "relative", "params": {}, "weight": 0.4},
            {"name": "Market_Cap_Rank", "type": "relative", "params": {}, "weight": 0.3},
            {"name": "Volume", "type": "volume", "params": {"ma_periods": [5]}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"name": "板块龙头", "logic": "AND", "conditions": [
                {"indicator": "Sector_Rank", "operator": "==", "value": 1},
                {"indicator": "price", "operator": ">", "compare_to": "resistance"}
            ], "weight": 1.0}
        ],
        "exit_conditions": [
            {"name": "跌破支撑", "conditions": [
                {"indicator": "price", "operator": "<", "compare_to": "support"}
            ]}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15, "max_position": 0.35}
    },
    
    # ==================== AI策略 ====================
    {
        "name": "情绪共振策略",
        "description": "新闻情绪+技术+资金流向多维度共振，利用AI分析市场情绪",
        "category": "ai",
        "icon": "🤖",
        "indicators": [
            {"name": "News_Sentiment", "type": "sentiment", "params": {}, "weight": 0.4},
            {"name": "Money_Flow", "type": "flow", "params": {}, "weight": 0.3},
            {"name": "RSI", "type": "oscillator", "params": {"period": 14}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"name": "情绪积极", "logic": "AND", "conditions": [
                {"indicator": "News_Sentiment", "operator": ">", "value": 0.6},
                {"indicator": "Money_Flow", "operator": ">", "value": 0}
            ], "weight": 0.7}
        ],
        "exit_conditions": [
            {"name": "情绪转负", "conditions": [
                {"indicator": "News_Sentiment", "operator": "<", "value": -0.3}
            ]}
        ],
        "risk_params": {"stop_loss": 0.04, "take_profit": 0.12, "max_position": 0.40}
    },
    {
        "name": "多空辩论加权策略",
        "description": "21智能体多空辩论，综合多方观点形成交易决策",
        "category": "ai",
        "icon": "⚖️",
        "indicators": [
            {"name": "Bull_Score", "type": "ai", "params": {}, "weight": 0.5},
            {"name": "Bear_Score", "type": "ai", "params": {}, "weight": 0.5}
        ],
        "entry_conditions": [
            {"name": "多头占优", "logic": "AND", "conditions": [
                {"indicator": "Bull_Score", "operator": ">", "value": 0.6},
                {"indicator": "Bull_Score", "operator": ">", "compare_to": "Bear_Score"}
            ], "weight": 1.0}
        ],
        "exit_conditions": [
            {"name": "空头占优", "conditions": [
                {"indicator": "Bear_Score", "operator": ">", "compare_to": "Bull_Score"}
            ]}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15, "max_position": 0.35}
    },
    {
        "name": "K线图像识别策略",
        "description": "使用多模态LLM分析K线图截图，识别形态和趋势",
        "category": "ai",
        "icon": "🖼️",
        "indicators": [
            {"name": "Chart_Pattern", "type": "ai_vision", "params": {}, "weight": 0.5},
            {"name": "Trend_Score", "type": "ai_vision", "params": {}, "weight": 0.3},
            {"name": "Support_Resistance", "type": "ai_vision", "params": {}, "weight": 0.2}
        ],
        "entry_conditions": [
            {"name": "看涨形态", "logic": "AND", "conditions": [
                {"indicator": "Chart_Pattern", "operator": "in", "value": ["双底", "头肩底", "上升三角形"]},
                {"indicator": "Trend_Score", "operator": ">", "value": 0.6}
            ], "weight": 1.0}
        ],
        "exit_conditions": [
            {"name": "看跌形态", "conditions": [
                {"indicator": "Chart_Pattern", "operator": "in", "value": ["双顶", "头肩顶", "下降三角形"]}
            ]}
        ],
        "risk_params": {"stop_loss": 0.05, "take_profit": 0.15, "max_position": 0.30}
    }
]


# 策略分类定义
STRATEGY_CATEGORIES = {
    "technical": {"name": "技术分析", "icon": "📊", "description": "基于技术指标的交易策略"},
    "fundamental": {"name": "价值投资", "icon": "📚", "description": "基于基本面分析的投资策略"},
    "institutional": {"name": "机构跟踪", "icon": "🏛️", "description": "跟踪机构持仓变动的策略"},
    "folk": {"name": "民间战法", "icon": "🎯", "description": "民间流传的交易方法"},
    "ai": {"name": "AI策略", "icon": "🤖", "description": "基于人工智能的交易策略"}
}


def get_preset_strategies():
    """获取所有预设策略"""
    return PRESET_STRATEGIES


def get_strategies_by_category(category: str):
    """按分类获取策略"""
    return [s for s in PRESET_STRATEGIES if s.get("category") == category]


def get_strategy_by_name(name: str):
    """按名称获取策略"""
    for strategy in PRESET_STRATEGIES:
        if strategy.get("name") == name:
            return strategy
    return None