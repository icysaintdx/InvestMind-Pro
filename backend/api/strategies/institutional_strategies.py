"""机构持仓策略"""

INSTITUTIONAL_STRATEGIES = [
    {
        "id": "kuwait_investment", 
        "name": "科威特政府投资局持仓策略", 
        "description": "跟踪科威特政府投资局（KIA）的A股持仓变动，该机构是全球最大的主权财富基金之一", 
        "category": "institutional", 
        "source": "preset", 
        "icon": "🏛️",
        "indicators": [
            {"name": "KIA_Holding", "type": "institutional", "params": {}, "weight": 0.4},
            {"name": "KIA_Change", "type": "institutional", "params": {"quarters": 2}, "weight": 0.3},
            {"name": "PE", "type": "fundamental", "params": {"max": 30}, "weight": 0.15},
            {"name": "ROE", "type": "fundamental", "params": {"min": 10}, "weight": 0.15}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "KIA_Holding", "operator": ">", "value": 0, "description": "科威特投资局持仓"},
            {"type": "entry", "indicator": "KIA_Change", "operator": ">", "value": 0, "description": "近2季度增持"},
            {"type": "entry", "indicator": "PE", "operator": "<", "value": 30, "description": "估值合理"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "KIA_Change", "operator": "<", "value": -20, "description": "大幅减持超过20%"},
            {"type": "exit", "indicator": "KIA_Holding", "operator": "==", "value": 0, "description": "清仓"}
        ],
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.50, "max_position": 0.25},
        "avg_win_rate": 0.52
    },
    {
        "id": "ge_weidong_holding", 
        "name": "葛卫东流通股东策略", 
        "description": "跟踪知名私募大佬葛卫东的持仓变动，其投资风格偏向成长股和周期股", 
        "category": "institutional", 
        "source": "preset", 
        "icon": "👤",
        "indicators": [
            {"name": "GWD_Holding", "type": "institutional", "params": {}, "weight": 0.4},
            {"name": "GWD_Change", "type": "institutional", "params": {"quarters": 1}, "weight": 0.3},
            {"name": "Revenue_Growth", "type": "fundamental", "params": {"min": 15}, "weight": 0.15},
            {"name": "PE", "type": "fundamental", "params": {"max": 40}, "weight": 0.15}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "GWD_Holding", "operator": ">", "value": 0, "description": "葛卫东持仓"},
            {"type": "entry", "indicator": "GWD_Change", "operator": ">", "value": 0, "description": "近1季度增持"},
            {"type": "entry", "indicator": "Revenue_Growth", "operator": ">", "value": 10, "description": "营收增长"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "GWD_Change", "operator": "<", "value": -30, "description": "大幅减持超过30%"},
            {"type": "exit", "indicator": "GWD_Holding", "operator": "==", "value": 0, "description": "清仓"}
        ],
        "risk_params": {"stop_loss": 0.12, "take_profit": 0.40, "max_position": 0.25},
        "avg_win_rate": 0.50
    },
    {
        "id": "social_security_holding", 
        "name": "社保流通股东策略", 
        "description": "跟踪社保基金的持仓变动，社保基金以长期价值投资著称，持仓稳定性高", 
        "category": "institutional", 
        "source": "preset", 
        "icon": "🏦",
        "indicators": [
            {"name": "SSF_Holding", "type": "institutional", "params": {}, "weight": 0.4},
            {"name": "SSF_Change", "type": "institutional", "params": {"quarters": 2}, "weight": 0.3},
            {"name": "ROE", "type": "fundamental", "params": {"min": 12}, "weight": 0.15},
            {"name": "Dividend_Yield", "type": "fundamental", "params": {"min": 2}, "weight": 0.15}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "SSF_Holding", "operator": ">", "value": 0, "description": "社保基金持仓"},
            {"type": "entry", "indicator": "SSF_Change", "operator": ">", "value": 0, "description": "近2季度增持"},
            {"type": "entry", "indicator": "ROE", "operator": ">", "value": 10, "description": "ROE良好"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "SSF_Change", "operator": "<", "value": -25, "description": "大幅减持超过25%"},
            {"type": "exit", "indicator": "SSF_Holding", "operator": "==", "value": 0, "description": "清仓"}
        ],
        "risk_params": {"stop_loss": 0.15, "take_profit": 0.60, "max_position": 0.30},
        "avg_win_rate": 0.55
    },
    {
        "id": "qfii_holding", 
        "name": "QFII持仓策略", 
        "description": "跟踪合格境外机构投资者（QFII）的持仓变动，外资视角选股", 
        "category": "institutional", 
        "source": "preset", 
        "icon": "🌍",
        "indicators": [
            {"name": "QFII_Holding", "type": "institutional", "params": {}, "weight": 0.4},
            {"name": "QFII_Change", "type": "institutional", "params": {"quarters": 1}, "weight": 0.3},
            {"name": "PE", "type": "fundamental", "params": {"max": 35}, "weight": 0.15},
            {"name": "ROE", "type": "fundamental", "params": {"min": 15}, "weight": 0.15}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "QFII_Holding", "operator": ">", "value": 0, "description": "QFII持仓"},
            {"type": "entry", "indicator": "QFII_Change", "operator": ">", "value": 0, "description": "近1季度增持"},
            {"type": "entry", "indicator": "ROE", "operator": ">", "value": 12, "description": "ROE优秀"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "QFII_Change", "operator": "<", "value": -20, "description": "大幅减持超过20%"},
            {"type": "exit", "indicator": "QFII_Holding", "operator": "==", "value": 0, "description": "清仓"}
        ],
        "risk_params": {"stop_loss": 0.12, "take_profit": 0.45, "max_position": 0.28},
        "avg_win_rate": 0.53
    },
    {
        "id": "northbound_flow", 
        "name": "北向资金流入策略", 
        "description": "跟踪沪深港通北向资金流入，捕捉外资青睐的标的", 
        "category": "institutional", 
        "source": "preset", 
        "icon": "📈",
        "indicators": [
            {"name": "Northbound_Holding", "type": "institutional", "params": {}, "weight": 0.35},
            {"name": "Northbound_Change", "type": "institutional", "params": {"days": 5}, "weight": 0.35},
            {"name": "PE", "type": "fundamental", "params": {"max": 40}, "weight": 0.15},
            {"name": "Volume", "type": "technical", "params": {"ma_period": 5}, "weight": 0.15}
        ],
        "entry_conditions": [
            {"type": "entry", "indicator": "Northbound_Change", "operator": ">", "value": 0, "description": "北向资金净流入"},
            {"type": "entry", "indicator": "Northbound_Holding", "operator": ">", "value": 1, "description": "持股比例大于1%"},
            {"type": "entry", "indicator": "Volume", "operator": ">", "value": "MA5", "description": "成交量放大"}
        ],
        "exit_conditions": [
            {"type": "exit", "indicator": "Northbound_Change", "operator": "<", "value": -5, "description": "连续5日净流出"},
            {"type": "exit", "indicator": "Northbound_Holding", "operator": "<", "value": 0.5, "description": "持股比例低于0.5%"}
        ],
        "risk_params": {"stop_loss": 0.08, "take_profit": 0.25, "max_position": 0.35},
        "avg_win_rate": 0.48
    },
]