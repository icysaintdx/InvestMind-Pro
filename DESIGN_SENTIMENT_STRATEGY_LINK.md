# 情绪-策略联动升级方案

**设计日期**: 2026-02-27  
**目标**: 让情绪分析结果直接影响策略决策

---

## 1. 当前问题总结

### 1.1 情绪分析系统问题
| 问题 | 影响 | 优先级 |
|------|------|--------|
| 模型不一致 | NewsEmotionAnalyzer使用minimax而非kimi-k2.5 | P1 |
| 架构分散 | 三个引擎各自独立，没有统一接口 | P1 |
| 历史数据利用不足 | 只有ai_sentiment_strategy.py使用历史数据 | P2 |
| 情绪趋势不完整 | 缺少7天/30天情绪变化曲线 | P2 |

### 1.2 策略系统问题
| 问题 | 影响 | 优先级 |
|------|------|--------|
| AI策略占比低 | 16个策略只有2个AI驱动(12.5%) | P1 |
| debate_weighted未使用智能体结果 | 策略设计但未实现 | P2 |
| 情绪联动深度有限 | 只有sentiment_resonance直接使用情绪 | P2 |

---

## 2. 改造方案

### 2.1 P1: 统一LLM配置模块

**新建文件**: `backend/services/llm/llm_config.py`

```python
"""统一LLM配置模块"""
from typing import Dict, Any
from openai import OpenAI

DEFAULT_LLM_CONFIG = {
    "base_url": "https://kirocpa.zeabur.app/v1",
    "api_key": "icysaintdx",
    "default_model": "kimi-k2.5",
    "fallback_model": "minimax-m2.1",
    "temperature": 0.3,
    "max_tokens": 800
}

class LLMClient:
    """统一LLM客户端"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or DEFAULT_LLM_CONFIG
        self.client = OpenAI(
            api_key=self.config["api_key"],
            base_url=self.config["base_url"]
        )
    
    def chat(self, messages: list, model: str = None, **kwargs) -> str:
        """统一聊天接口"""
        try:
            response = self.client.chat.completions.create(
                model=model or self.config["default_model"],
                messages=messages,
                temperature=kwargs.get("temperature", self.config["temperature"]),
                max_tokens=kwargs.get("max_tokens", self.config["max_tokens"])
            )
            return response.choices[0].message.content
        except Exception as e:
            # 降级到fallback模型
            if model != self.config["fallback_model"]:
                return self.chat(messages, model=self.config["fallback_model"], **kwargs)
            raise
```

**修改文件**:
- `backend/services/news_center/news_emotion_analyzer.py` - 使用统一配置
- `backend/services/news_center/impact_assessor.py` - 使用统一配置

---

### 2.2 P1: 统一情绪分析接口

**新建文件**: `backend/services/news_center/unified_sentiment.py`

```python
"""统一情绪分析结果数据结构"""
from dataclasses import dataclass
from typing import List, Dict, Optional
from datetime import datetime

@dataclass
class UnifiedSentimentResult:
    """统一情绪分析结果"""
    # 基础情绪
    sentiment: str              # positive/negative/neutral
    score: float               # -1.0 ~ 1.0 (标准化)
    confidence: float          # 0.0 ~ 1.0
    
    # 事件分析
    event_type: str            # 业绩/政策/重组/并购/股东/龙虎榜/公告/行业/其他
    event_subtype: str         # 子类型
    impact_level: int          # 1-10 影响程度
    impact_duration: str       # short/medium/long
    
    # 影响范围
    affected_sectors: List[str] # 影响板块
    affected_stocks: List[str] # 关联股票
    
    # 历史对比
    historical_baseline: float  # 历史平均情绪分数
    deviation_from_baseline: float  # 偏离度
    
    # 趋势
    trend_7d: float           # 7天情绪趋势 (-1~1)
    trend_30d: float          # 30天情绪趋势 (-1~1)
    
    # 元数据
    source: str               # 分析来源 (llm/keyword/impact_assessor)
    timestamp: datetime
    raw_data: Dict           # 原始分析数据
```

---

### 2.3 P1: 增强DebateWeightedStrategy

**修改文件**: `backend/strategies/debate_weighted.py`

核心改造：让策略真正使用21个智能体结果

---

### 2.4 P2: 情绪趋势服务

**新建文件**: `backend/services/news_center/sentiment_trend_service.py`

提供：
- 7天/30天情绪趋势计算
- 市场情绪指数
- 板块情绪排行
- 情绪异常预警

---

### 2.5 P2: 情绪-策略联动增强

**修改文件**: `backend/services/strategy/ai_weight_adjuster.py`

增强权重调整逻辑：
- 结合情绪趋势（不只是当前情绪）
- 增加行业情绪因子
- 增加市场情绪指数因子

---

## 3. 实施计划

### 阶段1: 基础设施 (今晚)
- [x] 审计报告提交
- [ ] 统一LLM配置模块
- [ ] 修复NewsEmotionAnalyzer模型配置
- [ ] 统一情绪分析接口

### 阶段2: 策略升级 (明天)
- [ ] 增强DebateWeightedStrategy
- [ ] 情绪趋势服务
- [ ] 权重调节器增强

### 阶段3: 测试验证 (后天)
- [ ] 单元测试
- [ ] 集成测试
- [ ] 回测验证

---

## 4. 预期效果

| 指标 | 当前 | 目标 |
|------|------|------|
| AI策略占比 | 12.5% (2/16) | 25%+ (4+/16) |
| 情绪联动策略数 | 1 | 3+ |
| 模型一致性 | 不一致 | 统一kimi-k2.5 |
| 历史数据利用率 | 低 | 高 |

---

*设计方案 v1.0 | 2026-02-27*
