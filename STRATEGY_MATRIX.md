# 策略矩阵 - 按持仓周期分类

## 短线策略 (持仓 1-20天)
| 策略 | 核心逻辑 | 适用场景 |
|------|---------|---------|
| scalping_blade | 超短线价差 | 高波动股票 |
| ema_breakout_short | EMA5/15金叉 | 强势股突破 |
| limit_up_trading | 涨停板追击 | 热点题材 |
| volume_price_surge | 量价齐升 | 资金涌入 |

## 中短线策略 (持仓 20-60天)
| 策略 | 核心逻辑 | 适用场景 |
|------|---------|---------|
| ema_breakout_mid | EMA12/26金叉 | 趋势确认 |
| sentiment_resonance | 情绪共振 | 利好驱动 |
| wavetrend_jma | WT+JMA指标 | 技术反弹 |
| macd_crossover | MACD金叉 | 动量延续 |

## 中长线策略 (持仓 60-250天)
| 策略 | 核心逻辑 | 适用场景 |
|------|---------|---------|
| ema_breakout_long | EMA30/60金叉 | 大趋势跟踪 |
| graham_margin | 安全边际 | 低估价值股 |
| buffett_value | ROE+PE | 优质蓝筹 |
| lynch_growth | 成长+合理价 | 成长股 |

## 组合配置建议
- 激进型: 40%短线 + 40%中短线 + 20%中长线
- 稳健型: 20%短线 + 30%中短线 + 50%中长线
- 保守型: 10%短线 + 20%中短线 + 70%中长线
