# EMA V2.1 参数优化报告

生成时间: 2026-02-27 14:08:32

优化股票数量: 20/20

## 优化结果汇总

| 代码 | 名称 | 优化收益 | 胜率 | 交易数 | 最大回撤 | Sharpe | 最佳参数 |
|:---:|:---:|------:|-----:|-----:|--------:|------:|:--------|
| 000001 | 平安银行 | +17.91% | 31.8% | 22 | -16.08% | 0.30 | EMA7/20,ATR×1.0 |
| 000333 | 美的集团 | +53.41% | 50.0% | 18 | -8.12% | 0.54 | EMA3/40,ATR×1.5 |
| 000568 | 泸州老窖 | +153.92% | 50.0% | 6 | -13.29% | 0.39 | EMA15/40,ATR×2.5 |
| 000651 | 格力电器 | +10.43% | 42.9% | 14 | -9.52% | 0.19 | EMA10/30,ATR×1.5 |
| 000858 | 五粮液 | +65.86% | 40.0% | 10 | -17.21% | 0.37 | EMA8/35,ATR×2.5 |
| 002415 | 海康威视 | +85.53% | 50.0% | 14 | -14.25% | 0.65 | EMA12/15,ATR×3.0 |
| 002460 | 赣锋锂业 | +701.13% | 45.5% | 11 | -10.67% | 0.76 | EMA15/18,ATR×2.0 |
| 002594 | 比亚迪 | +439.61% | 30.8% | 26 | -21.68% | 0.58 | EMA3/30,ATR×2.5 |
| 300014 | 亿纬锂能 | +451.20% | 46.2% | 13 | -18.06% | 0.77 | EMA12/18,ATR×2.5 |
| 300124 | 汇川技术 | +332.72% | 50.0% | 10 | -6.68% | 0.48 | EMA15/30,ATR×1.5 |
| 300750 | 宁德时代 | +355.18% | 42.9% | 14 | -17.72% | 0.78 | EMA15/20,ATR×2.0 |
| 600036 | 招商银行 | +38.67% | 54.5% | 11 | -8.05% | 0.59 | EMA12/40,ATR×2.5 |
| 600276 | 恒瑞医药 | +42.06% | 50.0% | 12 | -14.31% | 0.46 | EMA15/35,ATR×2.5 |
| 600519 | 贵州茅台 | +59.02% | 31.6% | 19 | -13.96% | 0.39 | EMA3/40,ATR×1.5 |
| 600887 | 伊利股份 | +13.68% | 40.0% | 10 | -9.85% | 0.24 | EMA12/40,ATR×1.0 |
| 600900 | 长江电力 | +31.55% | 47.4% | 19 | -5.88% | 0.53 | EMA10/15,ATR×2.0 |
| 601288 | 农业银行 | +73.32% | 23.1% | 39 | -9.97% | 0.62 | EMA3/15,ATR×2.5 |
| 601318 | 中国平安 | +62.84% | 38.5% | 13 | -16.13% | 0.51 | EMA15/40,ATR×1.5 |
| 601398 | 工商银行 | +59.98% | 47.1% | 17 | -3.07% | 0.75 | EMA10/20,ATR×2.0 |
| 601888 | 中国中免 | +293.02% | 42.9% | 14 | -29.61% | 0.51 | EMA3/40,ATR×1.5 |


## 最佳参数配置 (可直接使用)

```python
OPTIMIZED_PARAMS = {
    '000001': {
        'name': '平安银行',
        'fast_ema': 7,
        'slow_ema': 20,
        'atr_period': 14,
        'atr_multiplier': 1.0,
        'market_filter': True
    },
    '000333': {
        'name': '美的集团',
        'fast_ema': 3,
        'slow_ema': 40,
        'atr_period': 14,
        'atr_multiplier': 1.5,
        'market_filter': True
    },
    '000568': {
        'name': '泸州老窖',
        'fast_ema': 15,
        'slow_ema': 40,
        'atr_period': 14,
        'atr_multiplier': 2.5,
        'market_filter': True
    },
    '000651': {
        'name': '格力电器',
        'fast_ema': 10,
        'slow_ema': 30,
        'atr_period': 14,
        'atr_multiplier': 1.5,
        'market_filter': True
    },
    '000858': {
        'name': '五粮液',
        'fast_ema': 8,
        'slow_ema': 35,
        'atr_period': 14,
        'atr_multiplier': 2.5,
        'market_filter': True
    },
    '002415': {
        'name': '海康威视',
        'fast_ema': 12,
        'slow_ema': 15,
        'atr_period': 14,
        'atr_multiplier': 3.0,
        'market_filter': True
    },
    '002460': {
        'name': '赣锋锂业',
        'fast_ema': 15,
        'slow_ema': 18,
        'atr_period': 14,
        'atr_multiplier': 2.0,
        'market_filter': True
    },
    '002594': {
        'name': '比亚迪',
        'fast_ema': 3,
        'slow_ema': 30,
        'atr_period': 14,
        'atr_multiplier': 2.5,
        'market_filter': True
    },
    '300014': {
        'name': '亿纬锂能',
        'fast_ema': 12,
        'slow_ema': 18,
        'atr_period': 14,
        'atr_multiplier': 2.5,
        'market_filter': True
    },
    '300124': {
        'name': '汇川技术',
        'fast_ema': 15,
        'slow_ema': 30,
        'atr_period': 14,
        'atr_multiplier': 1.5,
        'market_filter': True
    },
    '300750': {
        'name': '宁德时代',
        'fast_ema': 15,
        'slow_ema': 20,
        'atr_period': 14,
        'atr_multiplier': 2.0,
        'market_filter': True
    },
    '600036': {
        'name': '招商银行',
        'fast_ema': 12,
        'slow_ema': 40,
        'atr_period': 14,
        'atr_multiplier': 2.5,
        'market_filter': True
    },
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
    '600887': {
        'name': '伊利股份',
        'fast_ema': 12,
        'slow_ema': 40,
        'atr_period': 14,
        'atr_multiplier': 1.0,
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
    '601288': {
        'name': '农业银行',
        'fast_ema': 3,
        'slow_ema': 15,
        'atr_period': 14,
        'atr_multiplier': 2.5,
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
    '601398': {
        'name': '工商银行',
        'fast_ema': 10,
        'slow_ema': 20,
        'atr_period': 14,
        'atr_multiplier': 2.0,
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
