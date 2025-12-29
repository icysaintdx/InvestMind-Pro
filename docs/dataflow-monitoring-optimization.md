# 数据流监控模块优化方案

## 一、现状分析

### 1.1 当前架构问题

#### 数据源分散
- **数据流页面 (DataFlowView)**: 仅使用2个数据源（东方财富全球资讯、个股新闻）
- **统一新闻中心 (UnifiedNewsView)**: 使用12个数据源
- **详情模态框**: 使用独立的新闻获取逻辑
- **问题**: 三个地方的新闻数据没有统一管理，存在重复获取和数据不一致

#### 时效性不足
- 当前缓存TTL: 5分钟
- 前端定时刷新: 2分钟
- 实际新闻延迟: 5-10分钟
- **问题**: 无法满足30秒内通知的需求

#### 公告数据不完整
- 巨潮资讯网爬虫存在但未充分利用
- AKShare的公告接口按日更新，时效性差
- 缺少交易所实时公告推送

### 1.2 数据源时效性评估

| 数据源 | 理论时效 | 实际时效 | 接口稳定性 | 建议更新频率 |
|--------|----------|----------|------------|--------------|
| 财联社快讯 | 10秒级 | 30-60秒 | 高 | 30秒 |
| 东方财富新闻 | 秒级 | 10-30秒 | 高 | 30秒 |
| 新浪财经 | 5-10秒 | 30-60秒 | 中 | 60秒 |
| 同花顺 | 3分钟 | 3-5分钟 | 中 | 60秒 |
| 巨潮资讯公告 | 实时 | 1-5分钟 | 高 | 60秒 |
| 微博热议 | 实时 | 5-10分钟 | 低 | 5分钟 |
| 新闻联播 | 按日 | 按日 | 高 | 1小时 |

### 1.3 现有接口清单

#### AKShare 新闻接口
```python
# 高时效性接口（建议30-60秒更新）
ak.stock_info_global_cls()      # 财联社快讯 - 最快
ak.stock_info_global_em()       # 东方财富全球资讯
ak.stock_news_em(symbol)        # 东方财富个股新闻

# 中时效性接口（建议1-5分钟更新）
ak.stock_info_global_sina()     # 新浪财经
ak.stock_info_global_ths()      # 同花顺
ak.stock_info_global_futu()     # 富途牛牛
ak.stock_notice_report()        # 公告数据

# 低时效性接口（建议5分钟以上更新）
ak.stock_js_weibo_report()      # 微博热议
ak.stock_info_cjzc_em()         # 财经早餐
ak.news_cctv(date)              # 新闻联播
```

#### Tushare 新闻接口
```python
# 需要5000积分
pro.news(src='sina')            # 新浪新闻
pro.news(src='wallstreetcn')    # 华尔街见闻
pro.news(src='10jqka')          # 同花顺
pro.news(src='eastmoney')       # 东方财富
pro.news(src='yuncaijing')      # 云财经
```

#### 公告接口
```python
# AKShare
ak.stock_notice_report(symbol, date)  # 巨潮资讯公告

# 自建爬虫
CninfoCrawler.get_company_announcements(stock_code, days)  # 巨潮资讯网
```

---

## 二、优化方案

### 2.1 架构重构：统一新闻中心

```
┌─────────────────────────────────────────────────────────────────┐
│                    实时新闻监控中心                              │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    新闻聚合引擎                              ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ ││
│  │  │ 高频轮询器   │  │ 增量检测器   │  │ 智能去重器          │ ││
│  │  │ (30秒)      │  │ (新闻指纹)   │  │ (标题+时间+来源)    │ ││
│  │  └─────────────┘  └─────────────┘  └─────────────────────┘ ││
│  └─────────────────────────────────────────────────────────────┘│
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                    股票关联分析器                          │  │
│  │  - 监控股票匹配                                           │  │
│  │  - 行业关联分析                                           │  │
│  │  - 概念板块关联                                           │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                    影响评估引擎                            │  │
│  │  - 情绪分析 (正面/负面/中性)                              │  │
│  │  - 重要性评分 (1-10)                                      │  │
│  │  - 紧急程度判定 (高/中/低)                                │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                    通知推送系统                            │  │
│  │  - WebSocket 实时推送                                     │  │
│  │  - 浏览器通知                                             │  │
│  │  - 声音提醒                                               │  │
│  │  - 微信/钉钉推送 (可选)                                   │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 分层更新策略

#### 第一层：高频监控（30秒）
- 财联社快讯
- 东方财富全球资讯
- 监控股票个股新闻
- 巨潮资讯公告（监控股票）

#### 第二层：中频监控（2分钟）
- 新浪财经
- 同花顺
- 富途牛牛
- 全市场公告

#### 第三层：低频监控（10分钟）
- 微博热议
- 财经早餐
- 新闻联播
- 百度财经日历

### 2.3 增量更新机制

```python
class IncrementalNewsMonitor:
    """增量新闻监控器"""

    def __init__(self):
        self.news_fingerprints = set()  # 新闻指纹集合
        self.last_check_time = {}       # 各数据源最后检查时间

    def generate_fingerprint(self, news: dict) -> str:
        """生成新闻指纹"""
        content = f"{news['title']}_{news['source']}_{news['publish_time'][:16]}"
        return hashlib.md5(content.encode()).hexdigest()

    def is_new(self, news: dict) -> bool:
        """判断是否为新新闻"""
        fp = self.generate_fingerprint(news)
        if fp in self.news_fingerprints:
            return False
        self.news_fingerprints.add(fp)
        return True

    def check_incremental(self, source: str) -> List[dict]:
        """增量检查新新闻"""
        all_news = self.fetch_news(source)
        new_news = [n for n in all_news if self.is_new(n)]
        return new_news
```

### 2.4 股票关联分析

```python
class StockNewsRelationAnalyzer:
    """股票新闻关联分析器"""

    def __init__(self, monitored_stocks: List[str]):
        self.monitored_stocks = monitored_stocks
        self.stock_names = {}      # 股票代码 -> 名称
        self.stock_industries = {} # 股票代码 -> 行业
        self.stock_concepts = {}   # 股票代码 -> 概念板块

    def analyze_relevance(self, news: dict) -> dict:
        """分析新闻与监控股票的关联性"""
        title = news.get('title', '')
        content = news.get('content', '')
        text = f"{title} {content}"

        related_stocks = []
        for code in self.monitored_stocks:
            name = self.stock_names.get(code, '')
            # 直接匹配
            if code in text or name in text:
                related_stocks.append({
                    'code': code,
                    'name': name,
                    'match_type': 'direct',
                    'relevance_score': 1.0
                })
            # 行业关联
            elif self._check_industry_match(code, text):
                related_stocks.append({
                    'code': code,
                    'name': name,
                    'match_type': 'industry',
                    'relevance_score': 0.6
                })
            # 概念关联
            elif self._check_concept_match(code, text):
                related_stocks.append({
                    'code': code,
                    'name': name,
                    'match_type': 'concept',
                    'relevance_score': 0.4
                })

        return {
            'news': news,
            'related_stocks': related_stocks,
            'is_relevant': len(related_stocks) > 0
        }
```

### 2.5 影响评估引擎

```python
class NewsImpactAssessor:
    """新闻影响评估器"""

    # 高影响关键词
    HIGH_IMPACT_KEYWORDS = [
        '涨停', '跌停', '停牌', '复牌', '退市', '摘帽', '戴帽',
        '重组', '并购', '收购', '增持', '减持', '回购',
        '业绩预增', '业绩预减', '业绩亏损', '业绩扭亏',
        '立案调查', '行政处罚', '违规', '造假',
        '中标', '签约', '合同', '订单',
        '突发', '紧急', '重大', '利好', '利空'
    ]

    # 紧急关键词
    URGENT_KEYWORDS = [
        '停牌', '退市', '立案', '处罚', '违规', '造假',
        '突发', '紧急', '重大利空', '暴跌', '闪崩'
    ]

    def assess(self, news: dict, related_stocks: List[dict]) -> dict:
        """评估新闻影响"""
        title = news.get('title', '')
        content = news.get('content', '')
        text = f"{title} {content}"

        # 计算影响分数
        impact_score = self._calculate_impact_score(text)

        # 判断紧急程度
        urgency = self._determine_urgency(text)

        # 情绪分析
        sentiment = self._analyze_sentiment(text)

        return {
            'impact_score': impact_score,      # 1-10
            'urgency': urgency,                # high/medium/low
            'sentiment': sentiment,            # positive/negative/neutral
            'should_notify': impact_score >= 7 or urgency == 'high',
            'notification_level': self._get_notification_level(impact_score, urgency)
        }

    def _calculate_impact_score(self, text: str) -> int:
        """计算影响分数"""
        score = 5  # 基础分
        for keyword in self.HIGH_IMPACT_KEYWORDS:
            if keyword in text:
                score += 1
        return min(10, score)

    def _determine_urgency(self, text: str) -> str:
        """判断紧急程度"""
        for keyword in self.URGENT_KEYWORDS:
            if keyword in text:
                return 'high'
        return 'medium' if any(k in text for k in self.HIGH_IMPACT_KEYWORDS) else 'low'
```

### 2.6 实时推送系统

```python
class RealtimeNotificationSystem:
    """实时通知系统"""

    def __init__(self):
        self.websocket_connections = set()
        self.notification_queue = asyncio.Queue()

    async def push_notification(self, notification: dict):
        """推送通知到所有连接的客户端"""
        message = json.dumps({
            'type': 'news_alert',
            'data': notification,
            'timestamp': datetime.now().isoformat()
        })

        # WebSocket 推送
        for ws in self.websocket_connections:
            try:
                await ws.send_text(message)
            except:
                self.websocket_connections.discard(ws)

        # 记录通知
        await self._log_notification(notification)

    async def create_notification(self, news: dict, assessment: dict, related_stocks: List[dict]):
        """创建通知"""
        notification = {
            'id': str(uuid.uuid4()),
            'title': news['title'],
            'source': news['source'],
            'publish_time': news['publish_time'],
            'related_stocks': related_stocks,
            'impact_score': assessment['impact_score'],
            'urgency': assessment['urgency'],
            'sentiment': assessment['sentiment'],
            'notification_level': assessment['notification_level'],
            'created_at': datetime.now().isoformat()
        }

        await self.push_notification(notification)
        return notification
```

---

## 三、前端优化方案

### 3.1 刷新频率设置组件

```vue
<template>
  <div class="refresh-settings">
    <h4>刷新频率设置</h4>
    <div class="setting-item">
      <label>新闻监控频率</label>
      <select v-model="newsRefreshInterval">
        <option value="30">30秒（高频）</option>
        <option value="60">1分钟</option>
        <option value="120">2分钟（默认）</option>
        <option value="300">5分钟</option>
      </select>
    </div>
    <div class="setting-item">
      <label>公告监控频率</label>
      <select v-model="announcementRefreshInterval">
        <option value="60">1分钟</option>
        <option value="120">2分钟</option>
        <option value="300">5分钟（默认）</option>
      </select>
    </div>
    <div class="setting-item">
      <label>其他数据更新频率</label>
      <select v-model="otherDataRefreshInterval">
        <option value="300">5分钟</option>
        <option value="600">10分钟</option>
        <option value="1800">30分钟</option>
        <option value="3600">1小时（默认）</option>
      </select>
    </div>
  </div>
</template>
```

### 3.2 实时通知组件

```vue
<template>
  <div class="realtime-notifications">
    <!-- 通知铃铛 -->
    <div class="notification-bell" @click="toggleNotificationPanel">
      <span class="bell-icon">🔔</span>
      <span v-if="unreadCount > 0" class="badge">{{ unreadCount }}</span>
    </div>

    <!-- 通知面板 -->
    <div v-if="showPanel" class="notification-panel">
      <div class="panel-header">
        <h4>实时预警</h4>
        <button @click="markAllRead">全部已读</button>
      </div>
      <div class="notification-list">
        <div
          v-for="notification in notifications"
          :key="notification.id"
          :class="['notification-item', notification.urgency, { unread: !notification.read }]"
        >
          <div class="notification-header">
            <span class="urgency-badge">{{ getUrgencyText(notification.urgency) }}</span>
            <span class="time">{{ formatTime(notification.created_at) }}</span>
          </div>
          <div class="notification-title">{{ notification.title }}</div>
          <div class="related-stocks">
            <span v-for="stock in notification.related_stocks" :key="stock.code" class="stock-tag">
              {{ stock.name }}
            </span>
          </div>
          <div class="notification-footer">
            <span class="source">{{ notification.source }}</span>
            <span class="impact">影响: {{ notification.impact_score }}/10</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
```

### 3.3 新闻高亮显示

```vue
<template>
  <div
    :class="['news-item', {
      'highlight-high': isHighImpact,
      'highlight-related': isRelatedToMonitored,
      'new-item': isNew
    }]"
  >
    <div class="news-header">
      <span v-if="isRelatedToMonitored" class="related-badge">📌 监控股票</span>
      <span v-if="isHighImpact" class="impact-badge">⚠️ 高影响</span>
      <span v-if="isNew" class="new-badge">NEW</span>
    </div>
    <div class="news-title">{{ news.title }}</div>
    <div class="news-meta">
      <span class="source">{{ news.source }}</span>
      <span class="time">{{ formatTime(news.publish_time) }}</span>
      <span v-if="news.related_stocks?.length" class="stocks">
        相关: {{ news.related_stocks.map(s => s.name).join(', ') }}
      </span>
    </div>
  </div>
</template>
```

---

## 四、数据更新频率建议

### 4.1 按数据类型分类

| 数据类型 | 建议更新频率 | 原因 |
|----------|--------------|------|
| 财联社快讯 | 30秒 | 最快的财经快讯来源 |
| 东方财富新闻 | 30秒 | 覆盖面广，更新快 |
| 监控股票个股新闻 | 30秒 | 直接相关，需要高时效 |
| 巨潮公告（监控股票） | 60秒 | 权威来源，影响大 |
| 新浪/同花顺/富途 | 2分钟 | 补充数据源 |
| 全市场公告 | 5分钟 | 数据量大，非直接相关 |
| 微博热议 | 10分钟 | 舆情参考，非实时需求 |
| 财经早餐/新闻联播 | 1小时 | 按日更新的内容 |

### 4.2 按数据重要性分类

| 重要性 | 数据类型 | 更新频率 | 通知方式 |
|--------|----------|----------|----------|
| 紧急 | 停牌/退市/立案公告 | 实时 | 弹窗+声音+推送 |
| 高 | 业绩预告/重组/增减持 | 30秒 | 弹窗+推送 |
| 中 | 一般新闻/行业动态 | 2分钟 | 列表高亮 |
| 低 | 舆情/热搜 | 10分钟 | 静默更新 |

---

## 五、实施计划

### 第一阶段：基础优化（1-2天）
1. 添加前端刷新频率设置
2. 实现静默刷新机制
3. 统一新闻数据源

### 第二阶段：增量监控（2-3天）
1. 实现增量新闻检测
2. 添加新闻指纹去重
3. 实现股票关联分析

### 第三阶段：实时推送（2-3天）
1. 实现 WebSocket 实时推送
2. 添加浏览器通知
3. 实现影响评估引擎

### 第四阶段：智能通知（1-2天）
1. 实现通知分级
2. 添加声音提醒
3. 优化通知展示

---

## 六、技术实现要点

### 6.1 30秒内通知的实现路径

```
新闻发布 → 数据源API → 后端轮询(30秒) → 增量检测 → 关联分析 → 影响评估 → WebSocket推送 → 前端通知
   0秒        1-5秒         30秒           <1秒        <1秒        <1秒         <1秒          <1秒

总延迟: 约 30-35 秒
```

### 6.2 关键优化点

1. **并行获取**: 多数据源并行请求，减少总耗时
2. **增量检测**: 只处理新新闻，减少计算量
3. **WebSocket**: 服务端主动推送，无需轮询
4. **本地缓存**: 前端缓存已读新闻，减少重复通知

### 6.3 性能考虑

- 后端轮询间隔: 30秒
- 单次请求超时: 10秒
- 最大并发请求: 5个
- 新闻指纹缓存: 最近1000条
- WebSocket 心跳: 30秒

---

## 七、监控效果评估指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 新闻延迟 | <30秒 | 对比新闻发布时间和通知时间 |
| 公告延迟 | <60秒 | 对比公告发布时间和通知时间 |
| 关联准确率 | >90% | 人工抽检 |
| 误报率 | <5% | 统计无关通知比例 |
| 漏报率 | <1% | 对比全量新闻和通知 |
| 系统可用性 | >99.9% | 监控服务状态 |
