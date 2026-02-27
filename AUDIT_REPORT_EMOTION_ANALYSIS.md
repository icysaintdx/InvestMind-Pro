# InvestMindPro 情绪分析系统审计报告

**审计日期**: 2026-02-27  
**审计人**: AI SubAgent  
**项目路径**: `/data/workspace-investmindpro/InvestMindPro`

---

## 1. 当前实现总结

### 1.1 整体架构

情绪分析系统采用**多引擎混合架构**，包含三个不同层次的实现：

| 组件 | 文件 | 实现方式 | 用途 |
|------|------|----------|------|
| **NewsEmotionAnalyzer** | `news_emotion_analyzer.py` | LLM (MiniMax-M2.1) | 深度情绪分析 |
| **SentimentEngine** | `sentiment_engine.py` | 关键词匹配 | 基础情绪分析 |
| **ImpactAssessor** | `impact_assessor.py` | LLM (kimi-k2.5) + 关键词降级 | 影响评估 |

### 1.2 LLM调用配置分析

#### NewsEmotionAnalyzer (主要情绪分析器)
```python
# 配置代码片段
self._llm_client.chat.completions.create(
    model="minimax-m2.1",  # 使用kirocpa中转的MiniMax模型
    messages=[...],
    temperature=0.3,
    max_tokens=800
)

# 客户端初始化
client = OpenAI(
    api_key="icysaintdx",
    base_url="https://kirocpa.zeabur.app/v1"
)
```

**✅ 配置正确**: 使用了 kirocpa 代理，但模型使用的是 `minimax-m2.1` 而非任务要求的 `kimi-k2.5`

#### ImpactAssessor (影响评估器)
```python
# 配置代码片段
self._llm_client = OpenAI(
    api_key="icysaintdx",
    base_url="https://kirocpa.zeabur.app/v1"
)

response = self._llm_client.chat.completions.create(
    model="kimi-k2.5",  # ✅ 正确配置
    messages=[...],
    temperature=0.2,
    max_tokens=600
)
```

**✅ 配置正确**: 使用了 kirocpa 代理和 kimi-k2.5 模型

### 1.3 分析维度覆盖情况

| 维度 | NewsEmotionAnalyzer | SentimentEngine | ImpactAssessor |
|------|---------------------|-----------------|----------------|
| **事件类型** | ✅ 业绩/政策/重组/并购/股东/龙虎榜/公告/行业/其他 | ❌ 无 | ✅ 自动识别 |
| **影响程度(1-10)** | ❌ 用high/medium/low | ❌ 用0-100分数 | ✅ 0-10分 |
| **影响时效** | ✅ short/medium/long | ❌ 无 | ✅ short/medium/long |
| **关联股票** | ✅ 支持 | ❌ 无 | ❌ 无 |

### 1.4 历史数据利用情况

**数据库表结构** (来自 `import_news_data.py`):
```sql
CREATE TABLE news_daily_sentiment (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stock_code TEXT NOT NULL, 
    company_name TEXT, 
    date TEXT NOT NULL,
    news_title_count INT DEFAULT 0, 
    news_content_count INT DEFAULT 0,
    positive_all INT DEFAULT 0, 
    neutral_all INT DEFAULT 0, 
    negative_all INT DEFAULT 0,
    positive_original INT DEFAULT 0, 
    neutral_original INT DEFAULT 0, 
    negative_original INT DEFAULT 0,
    source TEXT DEFAULT 'online'
);
```

**数据时间范围**: 1994-2024年 (约30年数据)

**当前利用情况**:
- ✅ `ai_sentiment_strategy.py` 充分利用了 `news_daily_sentiment` 表
- ✅ `import_news_data.py` 提供了完整的历史数据导入功能
- ❌ `news_emotion_analyzer.py` **没有直接利用**历史数据
- ❌ 没有基于历史数据的**情绪趋势校准**机制

### 1.5 情绪趋势构建能力

**现有实现**:
```python
# news_storage.py 中的基础统计
def get_stats_by_date(self, date: str) -> Dict[str, Any]:
    # 返回: total, p0_count, p1_count, p2_count, 
    #       positive_count, negative_count, neutral_count, avg_sentiment

# news_data_service.py 中的趋势
 def get_sentiment_trend(self, db: Session, ts_code: str, days: int = 7):
    # 返回最近N天的情绪统计数据
```

**缺失功能**:
- ❌ 没有专门的近7天/30天情绪变化曲线
- ❌ 没有情绪动量指标计算
- ❌ 没有基于历史数据的情绪基准线

---

## 2. 与目标的差距

### 2.1 模型不一致问题

| 目标要求 | 实际实现 | 差距 |
|----------|----------|------|
| 统一使用 kirocpa + kimi-k2.5 | NewsEmotionAnalyzer使用minimax-m2.1 | ❌ 不一致 |

### 2.2 历史数据利用不足

| 目标要求 | 实际实现 | 差距 |
|----------|----------|------|
| 利用2001-2024年数据进行情绪校准 | 仅ai_sentiment_strategy.py使用 | ❌ 分析器未利用 |
| 基于历史数据的趋势对比 | 缺失 | ❌ 未实现 |

### 2.3 情绪趋势构建不完整

| 目标要求 | 实际实现 | 差距 |
|----------|----------|------|
| 近7天/30天情绪变化曲线 | 只有基础统计 | ❌ 缺少可视化趋势 |
| 情绪动量指标 | ai_sentiment_strategy.py中有 | ⚠️ 未推广到全局 |

### 2.4 架构分散问题

三个情绪分析引擎（NewsEmotionAnalyzer、SentimentEngine、ImpactAssessor）各自独立，**没有统一的数据格式和接口**。

---

## 3. 改进建议列表

### 3.1 高优先级改进

#### P1: 统一LLM模型配置
```python
# 建议创建一个统一的LLM配置模块
# backend/services/llm/llm_config.py

DEFAULT_LLM_CONFIG = {
    "base_url": "https://kirocpa.zeabur.app/v1",
    "api_key": "icysaintdx",
    "default_model": "kimi-k2.5",
    "fallback_model": "minimax-m2.1",
    "temperature": 0.3,
    "max_tokens": 800
}
```

#### P2: 统一情绪分析接口
建议创建统一的情绪分析结果数据结构：
```python
@dataclass
class UnifiedSentimentResult:
    sentiment: str              # positive/negative/neutral
    score: float               # -1.0 ~ 1.0 (标准化)
    confidence: float          # 0.0 ~ 1.0
    event_type: str            # 事件类型
    event_subtype: str         # 子类型
    impact_level: int          # 1-10 影响程度
    impact_duration: str       # short/medium/long
    affected_sectors: List[str] # 影响板块
    affected_stocks: List[str] # 关联股票
    historical_context: Dict   # 历史数据对比
    trend_7d: float           # 7天情绪趋势
    trend_30d: float          # 30天情绪趋势
```

#### P3: 集成历史数据到情绪分析
```python
# 在 NewsEmotionAnalyzer.analyze() 中增加
async def analyze(self, title: str, content: str = "", stock_code: str = None):
    # 1. LLM分析
    llm_result = await self._llm_analyze(title, content, stock_code)
    
    # 2. 获取历史情绪基准 (新增)
    if stock_code:
        historical_baseline = self._get_historical_baseline(stock_code)
        llm_result = self._calibrate_with_history(llm_result, historical_baseline)
    
    return llm_result
```

### 3.2 中优先级改进

#### P4: 创建情绪趋势服务
```python
# backend/services/news_center/sentiment_trend_service.py
class SentimentTrendService:
    def get_7d_trend(self, stock_code: str) -> TrendData
    def get_30d_trend(self, stock_code: str) -> TrendData
    def get_market_sentiment_index(self) -> float  # 市场情绪指数
    def get_sector_sentiment(self, sector: str) -> Dict[str, float]
```

#### P5: 完善影响评估维度
当前 `impact_assessor.py` 已经比较完善，建议与 `news_emotion_analyzer.py` 整合。

### 3.3 低优先级改进

#### P6: 情绪分析结果持久化优化
当前使用SQLite，建议考虑：
- 为高频写入优化数据库配置
- 增加情绪分析结果缓存层

#### P7: 增加情绪分析监控面板
- 实时情绪分布图
- 热点板块情绪排行
- 异常情绪预警

---

## 4. 关键代码片段分析

### 4.1 备用分析逻辑 (关键词匹配降级)

```python
# news_emotion_analyzer.py: _fallback_analysis()
def _fallback_analysis(self, title: str) -> SentimentAnalysis:
    """备用分析（基于关键词）"""
    title_lower = title.lower()
    
    # 简单关键词匹配
    positive_words = ['预增', '增长', '利好', '突破', '创新高', '中标', '订单']
    negative_words = ['预减', '亏损', '下滑', '利空', '减持', '跌停', '暴雷']
    
    pos_count = sum(1 for w in positive_words if w in title_lower)
    neg_count = sum(1 for w in negative_words if w in title_lower)
    
    if pos_count > neg_count:
        sentiment = "positive"
        score = min(0.3 + pos_count * 0.1, 0.8)
    elif neg_count > pos_count:
        sentiment = "negative"
        score = max(-0.3 - neg_count * 0.1, -0.8)
    else:
        sentiment = "neutral"
        score = 0.0
```

**分析**: 备用方案过于简单，仅7个关键词，覆盖率不足。

### 4.2 LLM提示词设计

```python
# news_emotion_analyzer.py: _build_prompt()
def _build_prompt(self, title: str, content: str, stock_code: str = None) -> str:
    prompt = f"""你是一位专业的金融新闻分析师。请分析以下新闻的情绪、事件类型和影响。

新闻标题: {title}
{stock_context}
新闻内容: {content[:500] if content else title}

请输出JSON格式的分析结果:
{{
    "sentiment": "positive/negative/neutral",
    "score": 0.0,  // -1.0到1.0
    "confidence": 0.0,  // 0-1
    "event_type": "业绩/政策/重组/并购/股东/龙虎榜/公告/行业/其他",
    ...
}}
"""
```

**分析**: 提示词设计合理，但缺少**历史对比**和**时效性分析**的引导。

### 4.3 余额不足保护机制

```python
# news_emotion_analyzer.py: _call_llm()
except Exception as e:
    error_msg = str(e)
    # 余额不足时不抛异常，返回None让上层用fallback
    if "balance" in error_msg.lower() or "insufficient" in error_msg.lower() or "30001" in error_msg:
        self.logger.warning(f"LLM余额不足，使用备用分析: {error_msg[:100]}")
        return None
```

**分析**: 有完善的降级保护机制，但日志记录可以更详细。

---

## 5. 结论

### 5.1 总体评价

| 维度 | 评分 | 说明 |
|------|------|------|
| **功能完整性** | ⭐⭐⭐⭐ | 基础功能完整，但缺少历史数据深度利用 |
| **架构设计** | ⭐⭐⭐ | 多引擎并行但缺乏统一接口 |
| **LLM配置** | ⭐⭐⭐⭐ | 已配置kirocpa代理，但模型不统一 |
| **降级方案** | ⭐⭐⭐ | 有降级机制但关键词库太小 |
| **数据利用** | ⭐⭐ | 历史数据表存在但未充分利用 |

### 5.2 核心问题

1. **模型不统一**: NewsEmotionAnalyzer使用minimax-m2.1，而非目标要求的kimi-k2.5
2. **历史数据沉睡**: 2001-2024年的news_daily_sentiment数据未被情绪分析器直接利用
3. **缺少趋势构建**: 没有系统的近7天/30天情绪变化曲线
4. **架构分散**: 三个情绪分析引擎没有统一接口

### 5.3 建议优先级

1. 🔴 **高**: 统一LLM模型为kimi-k2.5
2. 🔴 **高**: 创建统一的情绪分析结果数据结构
3. 🟡 **中**: 集成历史数据到情绪分析流程
4. 🟡 **中**: 创建专门的情绪趋势服务
5. 🟢 **低**: 优化持久化和增加监控面板

---

**审计完成时间**: 2026-02-27 23:50 GMT+8  
**报告版本**: v1.0
