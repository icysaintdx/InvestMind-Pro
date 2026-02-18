"""
预设指标定义
包含所有系统预设的技术和基本面指标
"""

PRESET_INDICATORS = [
    # ==================== 技术指标 - 均线类 ====================
    {
        "name": "MA5",
        "name_cn": "5日均线",
        "category": "technical",
        "sub_category": "moving_average",
        "description": "5日移动平均线",
        "parameters": {"period": 5},
        "formula": "SUM(CLOSE, 5) / 5"
    },
    {
        "name": "MA10",
        "name_cn": "10日均线",
        "category": "technical",
        "sub_category": "moving_average",
        "description": "10日移动平均线",
        "parameters": {"period": 10},
        "formula": "SUM(CLOSE, 10) / 10"
    },
    {
        "name": "MA20",
        "name_cn": "20日均线",
        "category": "technical",
        "sub_category": "moving_average",
        "description": "20日移动平均线",
        "parameters": {"period": 20},
        "formula": "SUM(CLOSE, 20) / 20"
    },
    {
        "name": "MA60",
        "name_cn": "60日均线",
        "category": "technical",
        "sub_category": "moving_average",
        "description": "60日移动平均线（季线）",
        "parameters": {"period": 60},
        "formula": "SUM(CLOSE, 60) / 60"
    },
    {
        "name": "MA120",
        "name_cn": "120日均线",
        "category": "technical",
        "sub_category": "moving_average",
        "description": "120日移动平均线（半年线）",
        "parameters": {"period": 120},
        "formula": "SUM(CLOSE, 120) / 120"
    },
    {
        "name": "MA250",
        "name_cn": "250日均线",
        "category": "technical",
        "sub_category": "moving_average",
        "description": "250日移动平均线（年线）",
        "parameters": {"period": 250},
        "formula": "SUM(CLOSE, 250) / 250"
    },
    {
        "name": "EMA12",
        "name_cn": "12日指数均线",
        "category": "technical",
        "sub_category": "moving_average",
        "description": "12日指数移动平均线",
        "parameters": {"period": 12},
        "formula": "EMA(CLOSE, 12)"
    },
    {
        "name": "EMA26",
        "name_cn": "26日指数均线",
        "category": "technical",
        "sub_category": "moving_average",
        "description": "26日指数移动平均线",
        "parameters": {"period": 26},
        "formula": "EMA(CLOSE, 26)"
    },
    
    # ==================== 技术指标 - MACD ====================
    {
        "name": "MACD_DIF",
        "name_cn": "MACD快线",
        "category": "technical",
        "sub_category": "macd",
        "description": "MACD DIF线（快线）",
        "parameters": {"fast": 12, "slow": 26},
        "formula": "EMA(CLOSE, 12) - EMA(CLOSE, 26)"
    },
    {
        "name": "MACD_DEA",
        "name_cn": "MACD慢线",
        "category": "technical",
        "sub_category": "macd",
        "description": "MACD DEA线（慢线/信号线）",
        "parameters": {"signal": 9},
        "formula": "EMA(DIF, 9)"
    },
    {
        "name": "MACD_histogram",
        "name_cn": "MACD柱",
        "category": "technical",
        "sub_category": "macd",
        "description": "MACD柱状图",
        "parameters": {},
        "formula": "(DIF - DEA) * 2"
    },
    
    # ==================== 技术指标 - RSI ====================
    {
        "name": "RSI",
        "name_cn": "相对强弱指数",
        "category": "technical",
        "sub_category": "oscillator",
        "description": "14日RSI指标",
        "parameters": {"period": 14},
        "formula": "100 - 100 / (1 + RS)",
        "range": {"min": 0, "max": 100, "oversold": 30, "overbought": 70}
    },
    {
        "name": "RSI6",
        "name_cn": "6日RSI",
        "category": "technical",
        "sub_category": "oscillator",
        "description": "6日RSI指标（短期）",
        "parameters": {"period": 6},
        "formula": "100 - 100 / (1 + RS)",
        "range": {"min": 0, "max": 100, "oversold": 20, "overbought": 80}
    },
    {
        "name": "RSI12",
        "name_cn": "12日RSI",
        "category": "technical",
        "sub_category": "oscillator",
        "description": "12日RSI指标（中期）",
        "parameters": {"period": 12},
        "formula": "100 - 100 / (1 + RS)",
        "range": {"min": 0, "max": 100, "oversold": 30, "overbought": 70}
    },
    {
        "name": "RSI24",
        "name_cn": "24日RSI",
        "category": "technical",
        "sub_category": "oscillator",
        "description": "24日RSI指标（长期）",
        "parameters": {"period": 24},
        "formula": "100 - 100 / (1 + RS)",
        "range": {"min": 0, "max": 100, "oversold": 30, "overbought": 70}
    },
    
    # ==================== 技术指标 - KDJ ====================
    {
        "name": "KDJ_K",
        "name_cn": "KDJ-K值",
        "category": "technical",
        "sub_category": "kdj",
        "description": "KDJ K值",
        "parameters": {"n": 9, "m1": 3, "m2": 3},
        "formula": "SMA(RSV, M1)",
        "range": {"min": 0, "max": 100, "oversold": 20, "overbought": 80}
    },
    {
        "name": "KDJ_D",
        "name_cn": "KDJ-D值",
        "category": "technical",
        "sub_category": "kdj",
        "description": "KDJ D值",
        "parameters": {"n": 9, "m1": 3, "m2": 3},
        "formula": "SMA(K, M2)",
        "range": {"min": 0, "max": 100, "oversold": 20, "overbought": 80}
    },
    {
        "name": "KDJ_J",
        "name_cn": "KDJ-J值",
        "category": "technical",
        "sub_category": "kdj",
        "description": "KDJ J值",
        "parameters": {"n": 9, "m1": 3, "m2": 3},
        "formula": "3 * K - 2 * D",
        "range": {"min": -50, "max": 150, "oversold": 0, "overbought": 100}
    },
    
    # ==================== 技术指标 - 布林带 ====================
    {
        "name": "BOLL_upper",
        "name_cn": "布林上轨",
        "category": "technical",
        "sub_category": "bollinger",
        "description": "布林带上轨",
        "parameters": {"period": 20, "std": 2},
        "formula": "MA(CLOSE, 20) + 2 * STD(CLOSE, 20)"
    },
    {
        "name": "BOLL_middle",
        "name_cn": "布林中轨",
        "category": "technical",
        "sub_category": "bollinger",
        "description": "布林带中轨",
        "parameters": {"period": 20},
        "formula": "MA(CLOSE, 20)"
    },
    {
        "name": "BOLL_lower",
        "name_cn": "布林下轨",
        "category": "technical",
        "sub_category": "bollinger",
        "description": "布林带下轨",
        "parameters": {"period": 20, "std": 2},
        "formula": "MA(CLOSE, 20) - 2 * STD(CLOSE, 20)"
    },
    {
        "name": "BOLL_width",
        "name_cn": "布林带宽度",
        "category": "technical",
        "sub_category": "bollinger",
        "description": "布林带宽度（上轨-下轨）/中轨",
        "parameters": {"period": 20, "std": 2},
        "formula": "(UPPER - LOWER) / MIDDLE"
    },
    
    # ==================== 技术指标 - 成交量 ====================
    {
        "name": "volume_ratio",
        "name_cn": "量比",
        "category": "technical",
        "sub_category": "volume",
        "description": "当日成交量/5日平均成交量",
        "parameters": {"period": 5},
        "formula": "VOL / MA(VOL, 5)"
    },
    {
        "name": "turnover_rate",
        "name_cn": "换手率",
        "category": "technical",
        "sub_category": "volume",
        "description": "成交量/流通股本",
        "parameters": {},
        "formula": "VOL / FLOAT_SHARES * 100%"
    },
    {
        "name": "OBV",
        "name_cn": "能量潮",
        "category": "technical",
        "sub_category": "volume",
        "description": "累积成交量指标",
        "parameters": {},
        "formula": "累积(IF(CLOSE>REF(CLOSE,1), VOL, -VOL))"
    },
    {
        "name": "VR",
        "name_cn": "成交量比率",
        "category": "technical",
        "sub_category": "volume",
        "description": "26日成交量比率",
        "parameters": {"period": 26},
        "formula": "上涨日成交量 / 下跌日成交量"
    },
    
    # ==================== 技术指标 - 其他 ====================
    {
        "name": "ATR",
        "name_cn": "平均真实波幅",
        "category": "technical",
        "sub_category": "volatility",
        "description": "14日平均真实波幅",
        "parameters": {"period": 14},
        "formula": "MA(TR, 14)"
    },
    {
        "name": "CCI",
        "name_cn": "顺势指标",
        "category": "technical",
        "sub_category": "oscillator",
        "description": "14日CCI指标",
        "parameters": {"period": 14},
        "formula": "(TP - MA(TP, 14)) / (0.015 * MD)",
        "range": {"oversold": -100, "overbought": 100}
    },
    {
        "name": "WR",
        "name_cn": "威廉指标",
        "category": "technical",
        "sub_category": "oscillator",
        "description": "14日威廉指标",
        "parameters": {"period": 14},
        "formula": "(HHV - CLOSE) / (HHV - LLV) * 100",
        "range": {"min": 0, "max": 100, "oversold": 80, "overbought": 20}
    },
    {
        "name": "DMI_PDI",
        "name_cn": "DMI正向指标",
        "category": "technical",
        "sub_category": "trend",
        "description": "正向动向指标",
        "parameters": {"period": 14},
        "formula": "+DI"
    },
    {
        "name": "DMI_MDI",
        "name_cn": "DMI负向指标",
        "category": "technical",
        "sub_category": "trend",
        "description": "负向动向指标",
        "parameters": {"period": 14},
        "formula": "-DI"
    },
    {
        "name": "DMI_ADX",
        "name_cn": "ADX趋势强度",
        "category": "technical",
        "sub_category": "trend",
        "description": "平均趋向指数",
        "parameters": {"period": 14},
        "formula": "MA(ABS(+DI - -DI) / (+DI + -DI), 14)"
    },
    
    # ==================== 基本面指标 - 估值类 ====================
    {
        "name": "PE",
        "name_cn": "市盈率",
        "category": "fundamental",
        "sub_category": "valuation",
        "description": "股价/每股收益（TTM）",
        "parameters": {},
        "formula": "PRICE / EPS"
    },
    {
        "name": "PE_TTM",
        "name_cn": "市盈率TTM",
        "category": "fundamental",
        "sub_category": "valuation",
        "description": "滚动市盈率",
        "parameters": {},
        "formula": "PRICE / EPS_TTM"
    },
    {
        "name": "PB",
        "name_cn": "市净率",
        "category": "fundamental",
        "sub_category": "valuation",
        "description": "股价/每股净资产",
        "parameters": {},
        "formula": "PRICE / BPS"
    },
    {
        "name": "PS",
        "name_cn": "市销率",
        "category": "fundamental",
        "sub_category": "valuation",
        "description": "市值/营业收入",
        "parameters": {},
        "formula": "MARKET_CAP / REVENUE"
    },
    {
        "name": "PEG",
        "name_cn": "PEG",
        "category": "fundamental",
        "sub_category": "valuation",
        "description": "市盈率/盈利增长率",
        "parameters": {},
        "formula": "PE / PROFIT_GROWTH"
    },
    {
        "name": "EV_EBITDA",
        "name_cn": "企业价值倍数",
        "category": "fundamental",
        "sub_category": "valuation",
        "description": "企业价值/息税折旧摊销前利润",
        "parameters": {},
        "formula": "EV / EBITDA"
    },
    
    # ==================== 基本面指标 - 盈利能力 ====================
    {
        "name": "ROE",
        "name_cn": "净资产收益率",
        "category": "fundamental",
        "sub_category": "profitability",
        "description": "净利润/净资产",
        "parameters": {},
        "formula": "NET_PROFIT / EQUITY"
    },
    {
        "name": "ROA",
        "name_cn": "总资产收益率",
        "category": "fundamental",
        "sub_category": "profitability",
        "description": "净利润/总资产",
        "parameters": {},
        "formula": "NET_PROFIT / TOTAL_ASSETS"
    },
    {
        "name": "ROIC",
        "name_cn": "投入资本回报率",
        "category": "fundamental",
        "sub_category": "profitability",
        "description": "税后营业利润/投入资本",
        "parameters": {},
        "formula": "NOPAT / INVESTED_CAPITAL"
    },
    {
        "name": "gross_margin",
        "name_cn": "毛利率",
        "category": "fundamental",
        "sub_category": "profitability",
        "description": "毛利润/营业收入",
        "parameters": {},
        "formula": "GROSS_PROFIT / REVENUE"
    },
    {
        "name": "net_margin",
        "name_cn": "净利率",
        "category": "fundamental",
        "sub_category": "profitability",
        "description": "净利润/营业收入",
        "parameters": {},
        "formula": "NET_PROFIT / REVENUE"
    },
    {
        "name": "operating_margin",
        "name_cn": "营业利润率",
        "category": "fundamental",
        "sub_category": "profitability",
        "description": "营业利润/营业收入",
        "parameters": {},
        "formula": "OPERATING_PROFIT / REVENUE"
    },
    
    # ==================== 基本面指标 - 成长能力 ====================
    {
        "name": "revenue_growth",
        "name_cn": "营收增长率",
        "category": "fundamental",
        "sub_category": "growth",
        "description": "营业收入同比增长率",
        "parameters": {},
        "formula": "(REVENUE - REVENUE_LY) / REVENUE_LY"
    },
    {
        "name": "profit_growth",
        "name_cn": "利润增长率",
        "category": "fundamental",
        "sub_category": "growth",
        "description": "净利润同比增长率",
        "parameters": {},
        "formula": "(NET_PROFIT - NET_PROFIT_LY) / NET_PROFIT_LY"
    },
    {
        "name": "profit_growth_5y",
        "name_cn": "5年利润增长",
        "category": "fundamental",
        "sub_category": "growth",
        "description": "5年净利润复合增长率",
        "parameters": {},
        "formula": "CAGR(NET_PROFIT, 5)"
    },
    {
        "name": "eps_growth",
        "name_cn": "每股收益增长率",
        "category": "fundamental",
        "sub_category": "growth",
        "description": "每股收益同比增长率",
        "parameters": {},
        "formula": "(EPS - EPS_LY) / EPS_LY"
    },
    
    # ==================== 基本面指标 - 财务健康 ====================
    {
        "name": "debt_ratio",
        "name_cn": "资产负债率",
        "category": "fundamental",
        "sub_category": "financial_health",
        "description": "总负债/总资产",
        "parameters": {},
        "formula": "TOTAL_DEBT / TOTAL_ASSETS"
    },
    {
        "name": "current_ratio",
        "name_cn": "流动比率",
        "category": "fundamental",
        "sub_category": "financial_health",
        "description": "流动资产/流动负债",
        "parameters": {},
        "formula": "CURRENT_ASSETS / CURRENT_LIABILITIES"
    },
    {
        "name": "quick_ratio",
        "name_cn": "速动比率",
        "category": "fundamental",
        "sub_category": "financial_health",
        "description": "(流动资产-存货)/流动负债",
        "parameters": {},
        "formula": "(CURRENT_ASSETS - INVENTORY) / CURRENT_LIABILITIES"
    },
    {
        "name": "interest_coverage",
        "name_cn": "利息保障倍数",
        "category": "fundamental",
        "sub_category": "financial_health",
        "description": "息税前利润/利息费用",
        "parameters": {},
        "formula": "EBIT / INTEREST_EXPENSE"
    },
    
    # ==================== 基本面指标 - 股息 ====================
    {
        "name": "dividend_yield",
        "name_cn": "股息率",
        "category": "fundamental",
        "sub_category": "dividend",
        "description": "每股股息/股价",
        "parameters": {},
        "formula": "DPS / PRICE"
    },
    {
        "name": "payout_ratio",
        "name_cn": "派息率",
        "category": "fundamental",
        "sub_category": "dividend",
        "description": "每股股息/每股收益",
        "parameters": {},
        "formula": "DPS / EPS"
    },
    
    # ==================== 基本面指标 - 市值规模 ====================
    {
        "name": "market_cap",
        "name_cn": "总市值",
        "category": "fundamental",
        "sub_category": "size",
        "description": "股价 * 总股本",
        "parameters": {},
        "formula": "PRICE * TOTAL_SHARES"
    },
    {
        "name": "float_market_cap",
        "name_cn": "流通市值",
        "category": "fundamental",
        "sub_category": "size",
        "description": "股价 * 流通股本",
        "parameters": {},
        "formula": "PRICE * FLOAT_SHARES"
    },
    
    # ==================== 机构持仓指标 ====================
    {
        "name": "institutional_holding",
        "name_cn": "机构持仓比例",
        "category": "fundamental",
        "sub_category": "ownership",
        "description": "机构持股数/流通股本",
        "parameters": {},
        "formula": "INST_SHARES / FLOAT_SHARES"
    },
    {
        "name": "fund_holding",
        "name_cn": "基金持仓比例",
        "category": "fundamental",
        "sub_category": "ownership",
        "description": "基金持股数/流通股本",
        "parameters": {},
        "formula": "FUND_SHARES / FLOAT_SHARES"
    },
    {
        "name": "social_security_holding",
        "name_cn": "社保持仓比例",
        "category": "fundamental",
        "sub_category": "ownership",
        "description": "社保基金持股数/流通股本",
        "parameters": {},
        "formula": "SS_SHARES / FLOAT_SHARES"
    },
    {
        "name": "qfii_holding",
        "name_cn": "QFII持仓比例",
        "category": "fundamental",
        "sub_category": "ownership",
        "description": "QFII持股数/流通股本",
        "parameters": {},
        "formula": "QFII_SHARES / FLOAT_SHARES"
    },
    {
        "name": "northbound_holding",
        "name_cn": "北向资金持仓",
        "category": "fundamental",
        "sub_category": "ownership",
        "description": "北向资金持股数/流通股本",
        "parameters": {},
        "formula": "NORTHBOUND_SHARES / FLOAT_SHARES"
    },
]


# 指标分类定义
INDICATOR_CATEGORIES = {
    "technical": {
        "name_cn": "技术指标",
        "sub_categories": {
            "moving_average": "均线类",
            "macd": "MACD类",
            "oscillator": "震荡指标",
            "kdj": "KDJ类",
            "bollinger": "布林带",
            "volume": "成交量",
            "volatility": "波动率",
            "trend": "趋势指标"
        }
    },
    "fundamental": {
        "name_cn": "基本面指标",
        "sub_categories": {
            "valuation": "估值类",
            "profitability": "盈利能力",
            "growth": "成长能力",
            "financial_health": "财务健康",
            "dividend": "股息类",
            "size": "市值规模",
            "ownership": "持仓类"
        }
    },
    "sentiment": {
        "name_cn": "情绪指标",
        "sub_categories": {
            "news": "新闻情绪",
            "social": "社交媒体",
            "market": "市场情绪"
        }
    }
}


# 操作符定义
OPERATORS = {
    ">": {"name_cn": "大于", "description": "左值大于右值"},
    "<": {"name_cn": "小于", "description": "左值小于右值"},
    ">=": {"name_cn": "大于等于", "description": "左值大于等于右值"},
    "<=": {"name_cn": "小于等于", "description": "左值小于等于右值"},
    "=": {"name_cn": "等于", "description": "左值等于右值"},
    "!=": {"name_cn": "不等于", "description": "左值不等于右值"},
    "cross_above": {"name_cn": "上穿", "description": "左值从下方穿越右值"},
    "cross_below": {"name_cn": "下穿", "description": "左值从上方穿越右值"},
    "between": {"name_cn": "区间", "description": "左值在指定区间内"},
    "in": {"name_cn": "包含", "description": "左值在指定集合中"}
}