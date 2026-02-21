# 情绪分析系统 + AI策略升级 实施报告

## 变更概览

### 1. 情绪趋势服务（新建）
**文件**: `backend/services/sentiment_trend_service.py`

从 `news_articles` 表聚合每日情绪数据，计算：
- 7天/30天情绪均值、趋势斜率、波动率
- 情绪动量（7天均值 vs 30天均值的归一化差值）
- 方向判断（bullish/bearish/neutral）
- 负面突增检测（近3天负面比例 > 30天均值×2）
- 趋势反转检测（7天与30天方向相反）

输出 `get_stock_sentiment_summary()` 供策略层直接消费。

### 2. impact_assessor.py 升级为AI驱动
**文件**: `backend/services/news_center/impact_assessor.py`

- 新增 `assess_with_ai()` 异步方法，调用 kirocpa kimi-k2.5 进行影响评估
- LLM输出结构化JSON：影响分数、事件类型、影响时效、影响板块、操作建议
- 失败自动降级到原有关键词匹配（`assess()` 方法完整保留）
- `ImpactAssessment` 新增字段：`event_type`, `impact_duration`, `affected_sectors`, `ai_analyzed`
- API兼容：`get_urgency()` 和 `get_impact_score()` 接口不变

### 3. sentiment_resonance 策略修复
**文件**: `backend/strategies/sentiment_resonance.py`

**之前**: `generate_signal()` 只用RSI+MACD，情绪数据完全没用
**之后**: 三维度加权共振
- 情绪维度（40%权重，有数据时）：score、direction、momentum、negative_spike
- 技术维度（35%）：RSI超买超卖 + MACD方向和柱状图
- 资金维度（25%）：量比
- 特殊处理：负面突增扣分、趋势反转降低置信度
- 删除 `_generate_signals_legacy()` 死代码

### 4. AI策略权重调节器（新建）
**文件**: `backend/services/strategy/ai_weight_adjuster.py`

策略分三类：
- 进攻型：ema_breakout, macd_crossover, dragon_leader, scalping_blade, limit_up_trading, volume_price_surge, sentiment_resonance
- 防守型：buffett_value, lynch_growth, graham_margin, turtle_trading
- 中性：vegas_adx, bollinger_breakout, trident, martingale_refined, debate_weighted

调整逻辑：
- bullish → 提升进攻型权重，轻微降低防守型
- bearish → 提升防守型权重，降低进攻型
- 负面突增 → 紧急降低进攻型40%，提升防守型20%
- 趋势反转 → 所有策略权重×0.85

### 5. 联动集成
**文件**: `backend/strategies/manager.py`

`StrategyManager` 改动：
- `__init__` 新增 `_sentiment_service` 和 `_weight_adjuster` 懒加载
- `run_strategies()` 执行前自动获取情绪摘要 → 动态调整权重
- `_run_strategy_safe()` 对 sentiment_resonance 策略传入完整情绪数据
- 其他策略通过权重调整间接受情绪影响

## 数据流

```
news_articles (SQLite)
    ↓ 聚合查询
SentimentTrendService.get_stock_sentiment_summary()
    ↓ 情绪摘要
    ├── AIWeightAdjuster.adjust_weights() → 动态策略权重
    └── SentimentResonanceStrategy.generate_signal(sentiment_data=...) → 三维度共振信号
```

## API兼容性

所有现有API接口保持不变：
- `ImpactAssessor.assess()` / `get_urgency()` / `get_impact_score()` 签名不变
- `StrategyManager.run_strategies()` 签名不变
- `StrategyManager.combine_signals()` 不变
- `SentimentResonanceStrategy.generate_signal()` 新增可选参数 `sentiment_data`，不传时行为与之前一致（技术指标兜底）

## 降级策略

| 组件 | 正常路径 | 降级路径 |
|------|---------|---------|
| impact_assessor | LLM (kimi-k2.5) | 关键词匹配 |
| sentiment_trend | news_articles查询 | 返回空趋势（neutral） |
| weight_adjuster | 动态调整 | 使用基准权重 |
| sentiment_resonance | 三维度共振 | 仅技术指标（sent_confidence=0时权重降至15%） |
