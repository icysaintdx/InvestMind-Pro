# 情绪分析系统 + AI策略系统 审计报告

**审计时间**: 2026-02-28 00:16  
**审计范围**: InvestMindPro 情绪分析模块 + 策略系统  
**审计人员**: 自主执行代理

---

## 一、执行摘要

### 当前状态总览
| 模块 | 状态 | 说明 |
|------|------|------|
| 情绪分析引擎 | ✅ 已实现 | LLM驱动，多维度分析 |
| AI情绪策略 | ✅ 已实现 | 2个策略文件 |
| 情绪-策略联动 | ⚠️ 部分实现 | 有权重调整，但联动深度不足 |
| 实时数据流 | ⚠️ 待验证 | 需要确认实时性 |

### 核心发现
1. **情绪分析系统已较完善**：使用LLM (SiliconFlow Qwen/MiniMax) 进行深度分析
2. **AI策略已存在**：ai_sentiment_strategy + sentiment_resonance 两个策略
3. **联动机制存在但可能未充分发挥**：策略管理器有权重调整逻辑

---

## 二、情绪分析系统审计

### 2.1 架构与实现

**核心文件**: `backend/services/news_center/news_emotion_analyzer.py`

**已实现功能**:
```python
@dataclass
class SentimentAnalysis:
    sentiment: str          # positive/negative/neutral
    score: float           # -1.0 ~ 1.0
    confidence: float      # 0.0 ~ 1.0
    event_type: str        # 业绩/政策/重组/股东/龙虎榜/公告/行业/其他
    event_subtype: str     
    impact_level: str      # high/medium/low
    impact_duration: str   # short/medium/long
    affected_sectors: List[str]
    summary: str
    key_points: List[str]
    risk_factors: List[str]
```

**LLM调用链**:
1. 主路径: `llm_service.get_llm_service()` → kirocpa代理 → kimi-k2.5/MiniMax
2. 备用路径: 直接初始化OpenAI客户端
3. 降级方案: `_fallback_analysis()` 关键词匹配

### 2.2 数据源

**历史数据** (已导入):
- `news_daily_sentiment` - 每只股票每天的情绪统计 (2001-2024)
- `news_articles` - 原始新闻文章

**实时数据**:
- 各新闻API采集 → 实时分析 → 入库

### 2.3 存在的问题

| 问题 | 严重度 | 说明 |
|------|--------|------|
| 缺乏情绪趋势构建 | 中 | 没有近7天/30天情绪变化趋势 |
| 缺乏行业情绪聚合 | 中 | 没有行业级别的情绪指数 |
| 情绪缓存策略不明 | 低 | 不确定是否缓存避免重复分析 |

---

## 三、策略系统审计

### 3.1 策略清单 (29个策略)

**AI/情绪相关策略** (2个):
| 策略 | 文件 | 说明 |
|------|------|------|
| AI情绪驱动策略 | ai_sentiment_strategy.py | 结合历史情绪+技术指标+资金流向 |
| 情绪共振策略 | sentiment_resonance.py | 三维共振 (情绪+技术+资金) |

**传统技术策略** (14个):
- EMA系列: ema_breakout, ema_breakout_short/mid/long, ema_breakout_v2, v2_optimized, v2_2
- MACD、布林带、海龟交易、Vegas ADX等

**价值投资策略** (4个):
- buffett_value, graham_margin, lynch_growth

**其他策略** (9个):
- 涨停策略、龙头策略、 ensemble等

### 3.2 策略管理器

**核心文件**: `backend/strategies/manager.py`

**已实现功能**:
```python
# 策略权重动态调整
sentiment_summary = sentiment_svc.get_stock_sentiment_summary(stock_code)
if adjuster and sentiment_summary:
    adjusted_weights = adjuster.adjust_weights(
        sentiment_summary, self.strategy_weights
    )
```

**默认策略权重**:
```python
self.strategy_weights = {
    "sentiment_resonance": 0.75,  # 情绪策略权重较高
    # ... 其他策略
}
```

### 3.3 AI情绪策略详细分析

**ai_sentiment_strategy.py**:
- 数据: news_daily_sentiment (历史情绪) + AKShare (K线) + 技术指标
- 模型: 无AI模型，规则组合
- 信号: 情绪分+技术分+资金分加权

**sentiment_resonance.py**:
- 三维度: 新闻情绪(-1~1) + 技术得分(0~100) + 资金流向(-1~1)
- 共振阈值: news≥0.5, technical≥70, fund≥0.4
- 严格过滤: 只有三维同向共振才发出信号

### 3.4 存在的问题

| 问题 | 严重度 | 说明 |
|------|--------|------|
| AI策略没有真正AI | 🔴 高 | ai_sentiment_strategy只是规则组合 |
| 缺乏市场环境判断 | 中 | 没有根据大盘环境调整策略选择 |
| 策略权重调整逻辑不透明 | 中 | 权重调整器实现细节不明确 |
| 缺乏策略回测对比 | 中 | 没有各策略历史表现对比 |

---

## 四、情绪-策略联动审计

### 4.1 当前联动机制

```
新闻采集 → 情绪分析器(LLM) → sentiment_trend_service → 策略管理器
                                     ↓
                              权重调整器 → 策略权重更新 → 信号生成
```

### 4.2 联动强度评估

| 联动点 | 当前状态 | 目标状态 |
|--------|----------|----------|
| 新闻→情绪分析 | ✅ 强 | 强 |
| 情绪→策略权重 | ⚠️ 中 | 强 |
| 情绪→信号生成 | ⚠️ 弱 | 强 |
| 实时情绪→实时决策 | ❓ 未知 | 强 |

### 4.3 关键缺失

1. **实时情绪流**: 新新闻到达时是否立即触发策略重评估？
2. **情绪阈值触发**: 重大负面新闻是否触发强制减仓？
3. **行业情绪映射**: 行业政策变化是否调整该行业所有股票策略？

---

## 五、改进建议

### 5.1 短期 (1-2周)

1. **增强AI情绪策略**
   - 让 ai_sentiment_strategy 真正使用LLM做决策
   - 输入: 新闻情绪+技术数据 → LLM → 输出: 交易建议

2. **添加情绪趋势指标**
   - 构建 7日/30日情绪移动平均线
   - 情绪趋势变化率 (MACD式)

3. **策略表现监控**
   - 记录每个策略的实时表现
   - 自动降低表现差策略的权重

### 5.2 中期 (1个月)

1. **AI策略选择器**
   - 根据市场环境 (牛市/熊市/震荡) AI选择策略组合
   - 根据舆情热度调整策略权重

2. **情绪预警系统**
   - 重大负面新闻 → 自动风险预警
   - 连续负面情绪 → 建议空仓/减仓

3. **行业情绪聚合**
   - 构建行业情绪指数
   - 行业政策变化 → 该行业股票策略调整

### 5.3 长期 (2-3个月)

1. **端到端AI策略**
   - 训练专门的金融LLM做交易决策
   - 多模态输入: 新闻+行情+财报+宏观数据

2. **强化学习优化**
   - 策略权重强化学习自动优化
   - 在线学习适应市场变化

---

## 六、下一步行动计划

**建议优先级**:
1. 🔴 **P0**: 验证情绪-策略联动的实时性，确保新新闻能触发策略更新
2. 🔴 **P0**: 增强 ai_sentiment_strategy，真正使用LLM决策
3. 🟡 **P1**: 添加情绪趋势指标 (7/30日移动平均线)
4. 🟡 **P1**: 实现重大负面新闻自动风险预警
5. 🟢 **P2**: 构建行业情绪指数
6. 🟢 **P2**: 策略表现监控与自动权重调整

---

## 七、附录

### 关键文件清单
```
backend/services/news_center/news_emotion_analyzer.py  # 情绪分析器
backend/services/sentiment_trend_service.py            # 情绪趋势服务
backend/strategies/manager.py                          # 策略管理器
backend/strategies/ai_sentiment_strategy.py            # AI情绪策略
backend/strategies/sentiment_resonance.py              # 情绪共振策略
```

### 数据表清单
```
news_daily_sentiment  # 每日情绪统计 (2001-2024)
news_articles         # 原始新闻
```

---

*报告生成时间: 2026-02-28 00:16*  
*状态: 审计完成，等待下一步指令*
