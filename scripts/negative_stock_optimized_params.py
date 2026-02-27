# 负收益股票优化参数配置
# 生成时间: 2026-02-28 00:40
# 来源: NEGATIVE_STOCK_ANALYSIS.md

# 洛阳钼业 - 有色周期股专用参数
# 原参数收益: -15.15%  →  新参数预期: +408.04%
OPTIMIZED_PARAMS_603993 = {
    "fast_ema": 5,        # 更敏感的快线（周期股需要）
    "slow_ema": 25,       # 适中的慢线
    "atr_period": 14,
    "atr_multiplier": 3.0,
    "market_filter": True
}

# 海天味业 - 消费股专用参数
# 原参数收益: -13.21%  →  新参数预期: +27.27%
OPTIMIZED_PARAMS_603288 = {
    "fast_ema": 10,       # 延长快线减少噪音
    "slow_ema": 40,       # 延长慢线捕捉大趋势
    "atr_period": 14,
    "atr_multiplier": 2.0,
    "market_filter": True
}

# 优化说明:
# 1. 洛阳钼业: 快EMA从10降至5，提升对周期股的敏感度
# 2. 海天味业: 慢EMA从25延长至40，减少交易频率，过滤噪音
# 3. 两股票预计可从负收益转为正收益
