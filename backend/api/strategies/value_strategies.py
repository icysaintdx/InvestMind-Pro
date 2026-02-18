"""价值投资策略"""

VALUE_STRATEGIES = [
    {
        "id": "buffett_value", 
        "name": "巴菲特价值投资", 
        "description": "护城河+长期持有，寻找具有持续竞争优势的优质企业", 
        "category": "value_investing", 
        "source": "preset", 
        "icon": "💎",
        "indicators": [
            {"name": "ROE", "type": "fundamental", "params": {"min": 15}, "weight": 0.3},
            {"name": "PE", "type": "fundamental", "params": {"max": 25}, "weight": 0.25},
            {"name": "Debt_Ratio", "type": "fundamental", "params": {"max": 50}, "weight": 0.2},
            {"name": "Revenue_Growth", "type": "fundamental", "params": {"min": 10}, "weight": 0.25}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "ROE", "operator": ">", "value": 15, "description": "ROE大于15%"},
            {"type": "entry", "indicator": "PE", "operator": "<", "value": 25, "description": "PE小于25"},
            {"type": "entry", "indicator": "Debt_Ratio", "operator": "<", "value": 50, "description": "资产负债率小于50%"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "PE", "operator": ">", "value": 40, "description": "PE过高"},
            {"type": "exit", "indicator": "ROE", "operator": "<", "value": 10, "description": "ROE下降"}
        ],
        "risk_params": {"stop_loss": 0.20, "take_profit": 1.00, "max_position": 0.30},
        "avg_win_rate": 0.60
    },
    {
        "id": "graham_margin", 
        "name": "格雷厄姆安全边际", 
        "description": "低估值+安全边际，寻找价格低于内在价值的股票", 
        "category": "value_investing", 
        "source": "preset", 
        "icon": "🛡️",
        "indicators": [
            {"name": "PE", "type": "fundamental", "params": {"max": 15}, "weight": 0.3},
            {"name": "PB", "type": "fundamental", "params": {"max": 1.5}, "weight": 0.3},
            {"name": "Current_Ratio", "type": "fundamental", "params": {"min": 2}, "weight": 0.2},
            {"name": "Dividend_Yield", "type": "fundamental", "params": {"min": 2}, "weight": 0.2}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "PE", "operator": "<", "value": 15, "description": "PE小于15"},
            {"type": "entry", "indicator": "PB", "operator": "<", "value": 1.5, "description": "PB小于1.5"},
            {"type": "entry", "indicator": "Current_Ratio", "operator": ">", "value": 2, "description": "流动比率大于2"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "PE", "operator": ">", "value": 25, "description": "PE过高"},
            {"type": "exit", "indicator": "PB", "operator": ">", "value": 3, "description": "PB过高"}
        ],
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.80, "max_position": 0.25},
        "avg_win_rate": 0.55
    },
    {
        "id": "graham_style", 
        "name": "格雷厄姆型风格策略", 
        "description": "严格遵循格雷厄姆的选股标准：低PE、低PB、高股息、稳定盈利", 
        "category": "value_investing", 
        "source": "preset", 
        "icon": "📚",
        "indicators": [
            {"name": "PE", "type": "fundamental", "params": {"max": 10}, "weight": 0.25},
            {"name": "PB", "type": "fundamental", "params": {"max": 1.2}, "weight": 0.25},
            {"name": "Dividend_Yield", "type": "fundamental", "params": {"min": 3}, "weight": 0.25},
            {"name": "Earnings_Stability", "type": "fundamental", "params": {"years": 10}, "weight": 0.25}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "PE", "operator": "<", "value": 10, "description": "PE小于10"},
            {"type": "entry", "indicator": "PB", "operator": "<", "value": 1.2, "description": "PB小于1.2"},
            {"type": "entry", "indicator": "Dividend_Yield", "operator": ">", "value": 3, "description": "股息率大于3%"},
            {"type": "entry", "indicator": "Profit_Years", "operator": ">=", "value": 10, "description": "连续10年盈利"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "PE", "operator": ">", "value": 20, "description": "PE超过20"},
            {"type": "exit", "indicator": "Dividend_Yield", "operator": "<", "value": 1, "description": "股息率低于1%"}
        ],
        "risk_params": {"stop_loss": 0.20, "take_profit": 0.60, "max_position": 0.20},
        "avg_win_rate": 0.58
    },
    {
        "id": "davis_style", 
        "name": "戴维斯型风格策略", 
        "description": "戴维斯双击策略：寻找低PE且盈利增长的公司", 
        "category": "value_investing", 
        "source": "preset", 
        "icon": "🎯",
        "indicators": [
            {"name": "PE", "type": "fundamental", "params": {"max": 15, "min": 5}, "weight": 0.3},
            {"name": "EPS_Growth", "type": "fundamental", "params": {"min": 15}, "weight": 0.3},
            {"name": "ROE", "type": "fundamental", "params": {"min": 12}, "weight": 0.2},
            {"name": "PEG", "type": "fundamental", "params": {"max": 1}, "weight": 0.2}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "PE", "operator": "<", "value": 15, "description": "PE小于15"},
            {"type": "entry", "indicator": "PE", "operator": ">", "value": 5, "description": "PE大于5"},
            {"type": "entry", "indicator": "EPS_Growth", "operator": ">", "value": 15, "description": "EPS增长率大于15%"},
            {"type": "entry", "indicator": "PEG", "operator": "<", "value": 1, "description": "PEG小于1"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "PE", "operator": ">", "value": 30, "description": "PE超过30"},
            {"type": "exit", "indicator": "EPS_Growth", "operator": "<", "value": 0, "description": "EPS负增长"}
        ],
        "risk_params": {"stop_loss": 0.15, "take_profit": 1.00, "max_position": 0.30},
        "avg_win_rate": 0.55
    },
    {
        "id": "lynch_growth", 
        "name": "彼得林奇成长股", 
        "description": "PEG<1选股，寻找被低估的成长股", 
        "category": "value_investing", 
        "source": "preset", 
        "icon": "🌱",
        "indicators": [
            {"name": "PEG", "type": "fundamental", "params": {"max": 1}, "weight": 0.4},
            {"name": "Revenue_Growth", "type": "fundamental", "params": {"min": 20}, "weight": 0.3},
            {"name": "Debt_Ratio", "type": "fundamental", "params": {"max": 40}, "weight": 0.3}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "PEG", "operator": "<", "value": 1, "description": "PEG小于1"},
            {"type": "entry", "indicator": "Revenue_Growth", "operator": ">", "value": 20, "description": "营收增长大于20%"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "PEG", "operator": ">", "value": 2, "description": "PEG过高"},
            {"type": "exit", "indicator": "Revenue_Growth", "operator": "<", "value": 5, "description": "增长放缓"}
        ],
        "risk_params": {"stop_loss": 0.25, "take_profit": 1.50, "max_position": 0.35},
        "avg_win_rate": 0.50
    },
]