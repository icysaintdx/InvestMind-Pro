# EMA V2.1 参数优化报告

生成时间: 2026-02-27 14:05:04

优化股票数量: 17/8

## 优化结果汇总

| 代码 | 名称 | 优化收益 | 胜率 | 交易数 | 最大回撤 | Sharpe | 最佳参数 |
|:---:|:---:|------:|-----:|-----:|--------:|------:|:--------|
| 600276 | 恒瑞医药 | +42.06% | 50.0% | 12 | -14.31% | 0.46 | EMA15/35,ATR×2.5 |
| 600519 | 贵州茅台 | +59.02% | 31.6% | 19 | -13.96% | 0.39 | EMA3/40,ATR×1.5 |
| 600900 | 长江电力 | +31.55% | 47.4% | 19 | -5.88% | 0.53 | EMA10/15,ATR×2.0 |
| 601318 | 中国平安 | +62.84% | 38.5% | 13 | -16.13% | 0.51 | EMA15/40,ATR×1.5 |
| 601888 | 中国中免 | +293.02% | 42.9% | 14 | -29.61% | 0.51 | EMA3/40,ATR×1.5 |


## 最佳参数配置 (可直接使用)

```python
OPTIMIZED_PARAMS = {
    '600276': {
        'name': '恒瑞医药',
        'fast_ema': 15,
        'slow_ema': 35,
        'atr_period': 14,
        'atr_multiplier': 2.5,
        'market_filter': True
    },
    '600519': {
        'name': '贵州茅台',
        'fast_ema': 3,
        'slow_ema': 40,
        'atr_period': 14,
        'atr_multiplier': 1.5,
        'market_filter': True
    },
    '600900': {
        'name': '长江电力',
        'fast_ema': 10,
        'slow_ema': 15,
        'atr_period': 14,
        'atr_multiplier': 2.0,
        'market_filter': True
    },
    '601318': {
        'name': '中国平安',
        'fast_ema': 15,
        'slow_ema': 40,
        'atr_period': 14,
        'atr_multiplier': 1.5,
        'market_filter': True
    },
    '601888': {
        'name': '中国中免',
        'fast_ema': 3,
        'slow_ema': 40,
        'atr_period': 14,
        'atr_multiplier': 1.5,
        'market_filter': True
    },
}
```
