"""
预设策略数据
包含22个完整的预设策略定义
"""

# 完整的22个预设策略
PRESET_STRATEGIES = [
    # ==================== 技术分析策略 (4个) ====================
    {
        "id": "vegas_adx", 
        "name": "Vegas+ADX策略", 
        "description": "结合Vegas隧道和ADX趋势强度指标的趋势跟踪策略，适合中长线趋势交易", 
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
        "description": "多周期均线共振策略，当5日、10日、20日、60日均线多头排列时入场，适合趋势行情", 
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
    # ==================== 价值投资策略 (5个) ====================
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
        "description": "严格遵循格雷厄姆的选股标准：低PE、低PB、高股息、稳定盈利，追求极致的安全边际", 
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
        "description": "戴维斯双击策略：寻找低PE且盈利增长的公司，享受估值和盈利双重提升带来的收益", 
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
    # ==================== 趋势跟踪策略 (1个) ====================
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
    # ==================== AI合成策略 (2个) ====================
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
    # ==================== 民间策略 (3个) ====================
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
    # ==================== 机构持仓策略 (4个) ====================
    {
        "id": "kuwait_investment", 
        "name": "科威特政府投资局持仓策略", 
        "description": "跟踪科威特政府投资局（KIA）的A股持仓变动，该机构是全球最大的主权财富基金之一，投资风格稳健", 
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