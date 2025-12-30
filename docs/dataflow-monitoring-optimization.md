# 数据流监控模块优化方案 v2.1

## 实施状态

| 组件 | 状态 | 文件位置 |
|------|------|----------|
| NewsCache | ✅ 已完成 | `backend/services/news_center/news_cache.py` |
| StockRelationAnalyzer | ✅ 已完成 | `backend/services/news_center/stock_relation_analyzer.py` |
| ImpactAssessor | ✅ 已完成 | `backend/services/news_center/impact_assessor.py` |
| NewsMonitorCenter | ✅ 已完成 | `backend/services/news_center/news_monitor_center.py` |
| 统一新闻API | ✅ 已完成 | `backend/api/news_center_api.py` |
| WebSocket推送 | ✅ 已完成 | `backend/api/websocket_api.py` (扩展) |
| 前端集成 | ✅ 已完成 | `frontend/src/views/DataFlowView.vue` |

---

## 一、现状深度分析

### 1.1 现有基础设施（已实现）

| 组件 | 文件位置 | 功能 | 使用情况 |
|------|----------|------|----------|
| 后台新闻服务 | `backend/services/background_news_service.py` | ProcessPoolExecutor独立进程池 | ✅ 已实现 |
| 情绪分析引擎 | `backend/dataflows/news/sentiment_engine.py` | 完整情绪词典+分析逻辑 | ✅ 已实现 |
| 巨潮资讯爬虫 | `backend/dataflows/announcement/cninfo_crawler.py` | 公告数据获取 | ⚠️ 未被调用 |
| 统一新闻API | `backend/api/unified_news_api_endpoint.py` | 12个数据源聚合 | ✅ 已实现 |
| 多源新闻聚合器 | `backend/dataflows/news/multi_source_news_aggregator.py` | Tushare+AKShare | ✅ 已实现 |

### 1.2 新闻数据调用点分析

| 调用位置 | 数据源 | 问题 |
|----------|--------|------|
| 数据流页面 (DataFlowView) | 2个数据源 | 数据源太少 |
| 统一新闻中心 (UnifiedNewsView) | 12个数据源 | 最完整，但独立运行 |
| 详情模态框 | 独立获取逻辑 | 与新闻流不共享 |
| 智能分析模块 | 独立获取逻辑 | 重复获取 |
| 综合数据服务 | 独立获取逻辑 | 缓存不统一 |

### 1.3 核心问题

1. **数据源分散**: 5个地方各自获取新闻，没有统一入口
2. **重复请求**: 同一条新闻可能被获取多次
3. **缓存不统一**: 各模块各自缓存，数据不一致
4. **巨潮爬虫闲置**: 已实现但未被任何模块调用
5. **情绪分析分散**: 多处重复实现情绪分析逻辑

---

## 二、统一架构方案

### 2.1 核心设计原则

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         统一新闻监控中心 (NewsMonitorCenter)                  │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        后台数据采集层                                │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │   │
│  │  │ 进程池执行器  │  │ 定时调度器   │  │ 增量检测器                │  │   │
│  │  │ (已有)       │  │ (新增)       │  │ (新增)                   │  │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                        统一数据源层                                  │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │   │
│  │  │ AKShare    │ │ Tushare    │ │ 巨潮资讯   │ │ 其他数据源     │   │   │
│  │  │ 新闻接口   │ │ 新闻接口   │ │ 爬虫(激活) │ │ (财联社等)     │   │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                        统一缓存层                                    │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ 新闻缓存池 (NewsCache)                                        │  │   │
│  │  │ - 全局新闻列表 (去重后)                                       │  │   │
│  │  │ - 按股票索引 (stock_code -> news_ids)                        │  │   │
│  │  │ - 新闻指纹集合 (防重复)                                       │  │   │
│  │  │ - TTL: 新闻30分钟, 公告1小时                                  │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                        智能分析层                                    │   │
│  │  ┌────────────────┐ ┌────────────────┐ ┌────────────────────────┐  │   │
│  │  │ 情绪分析引擎   │ │ 股票关联分析   │ │ 影响评估引擎           │  │   │
│  │  │ (已有,复用)    │ │ (新增)         │ │ (新增)                 │  │   │
│  │  └────────────────┘ └────────────────┘ └────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                        │
│  ┌─────────────────────────────────▼───────────────────────────────────┐   │
│  │                        统一API层                                     │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │ /api/news-center/*                                           │  │   │
│  │  │ - GET /latest          获取最新新闻                          │  │   │
│  │  │ - GET /stock/{code}    获取股票相关新闻                      │  │   │
│  │  │ - GET /announcements   获取公告                              │  │   │
│  │  │ - WS  /realtime        WebSocket实时推送                     │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              前端调用方                                      │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐ ┌──────────────┐ │
│  │ 数据流页面     │ │ 统一新闻中心   │ │ 详情模态框     │ │ 智能分析     │ │
│  │ (DataFlowView) │ │ (UnifiedNews)  │ │ (StockDetail)  │ │ (Analysis)   │ │
│  └────────────────┘ └────────────────┘ └────────────────┘ └──────────────┘ │
│                              │                                              │
│                    全部调用统一API，不再各自获取                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 2.2 统一 vs 独立的选择

**结论：采用统一架构**

| 对比项 | 统一架构 | 独立架构 |
|--------|----------|----------|
| 数据一致性 | ✅ 所有模块数据一致 | ❌ 可能不一致 |
| 请求效率 | ✅ 一次获取，多处使用 | ❌ 重复请求 |
| 缓存效率 | ✅ 统一缓存，命中率高 | ❌ 各自缓存，浪费内存 |
| 维护成本 | ✅ 一处修改，全局生效 | ❌ 多处修改 |
| 实时性 | ✅ 统一推送机制 | ❌ 各自轮询 |
| 复杂度 | ⚠️ 初期开发复杂 | ✅ 简单独立 |

### 2.3 后台静默运行机制

```python
class NewsMonitorCenter:
    """统一新闻监控中心 - 后台静默运行"""

    def __init__(self):
        # 使用独立进程池，不影响主线程
        self.process_pool = ProcessPoolExecutor(max_workers=4)
        # 使用独立线程池处理分析任务
        self.thread_pool = ThreadPoolExecutor(max_workers=8)
        # 定时调度器
        self.scheduler = BackgroundScheduler()

    async def start(self):
        """启动后台监控"""
        # 所有任务在后台运行，不阻塞主线程
        self.scheduler.add_job(
            self._fetch_news_batch,
            'interval',
            seconds=30,  # 30秒获取一次
            id='news_fetch'
        )
        self.scheduler.add_job(
            self._fetch_announcements,
            'interval',
            seconds=60,  # 60秒获取一次公告
            id='announcement_fetch'
        )
        self.scheduler.start()
```

---

## 三、数据源整合方案

### 3.1 激活巨潮资讯爬虫

当前 `CninfoCrawler` 已实现但未被调用，需要整合到统一新闻中心：

```python
# 在 NewsMonitorCenter 中整合
from backend.dataflows.announcement.cninfo_crawler import CninfoCrawler

class NewsMonitorCenter:
    def __init__(self):
        self.cninfo_crawler = CninfoCrawler()

    async def _fetch_announcements(self):
        """获取监控股票的公告"""
        for stock_code in self.monitored_stocks:
            announcements = self.cninfo_crawler.get_company_announcements(
                stock_code=stock_code,
                days=1  # 只获取最近1天
            )
            await self._process_announcements(announcements)
```

### 3.2 数据源优先级和更新频率

| 优先级 | 数据源 | 更新频率 | 用途 |
|--------|--------|----------|------|
| P0 | 财联社快讯 | 30秒 | 突发新闻 |
| P0 | 巨潮资讯公告 | 60秒 | 权威公告 |
| P1 | 东方财富新闻 | 30秒 | 综合新闻 |
| P1 | 监控股票个股新闻 | 30秒 | 直接相关 |
| P2 | 新浪/同花顺/富途 | 2分钟 | 补充来源 |
| P3 | 微博热议 | 5分钟 | 舆情参考 |
| P4 | 新闻联播/财经早餐 | 1小时 | 宏观参考 |

### 3.3 完整数据源清单

```python
DATA_SOURCES = {
    # 高频数据源 (30秒)
    'high_frequency': [
        {'name': 'cls_flash', 'func': 'ak.stock_info_global_cls', 'desc': '财联社快讯'},
        {'name': 'em_global', 'func': 'ak.stock_info_global_em', 'desc': '东方财富全球'},
        {'name': 'em_stock', 'func': 'ak.stock_news_em', 'desc': '东方财富个股', 'need_code': True},
        {'name': 'cninfo', 'func': 'CninfoCrawler.get_company_announcements', 'desc': '巨潮公告', 'need_code': True},
    ],

    # 中频数据源 (2分钟)
    'medium_frequency': [
        {'name': 'sina_global', 'func': 'ak.stock_info_global_sina', 'desc': '新浪财经'},
        {'name': 'ths_global', 'func': 'ak.stock_info_global_ths', 'desc': '同花顺'},
        {'name': 'futu_global', 'func': 'ak.stock_info_global_futu', 'desc': '富途牛牛'},
        {'name': 'em_notice', 'func': 'ak.stock_notice_report', 'desc': '东方财富公告'},
    ],

    # 低频数据源 (5分钟+)
    'low_frequency': [
        {'name': 'weibo_hot', 'func': 'ak.stock_js_weibo_report', 'desc': '微博热议'},
        {'name': 'cjzc', 'func': 'ak.stock_info_cjzc_em', 'desc': '财经早餐'},
        {'name': 'cctv', 'func': 'ak.news_cctv', 'desc': '新闻联播'},
        {'name': 'baidu_eco', 'func': 'ak.news_economic_baidu', 'desc': '百度财经'},
    ],

    # Tushare数据源 (需要积分)
    'tushare': [
        {'name': 'ts_news', 'func': 'pro.news', 'desc': 'Tushare新闻', 'points': 5000},
    ]
}
```

---

## 四、智能分析层设计

### 4.1 复用现有情绪分析引擎

```python
from backend.dataflows.news.sentiment_engine import SentimentEngine

class NewsAnalyzer:
    """新闻分析器 - 复用现有组件"""

    def __init__(self):
        # 复用已有的情绪分析引擎
        self.sentiment_engine = SentimentEngine()

    def analyze(self, news: dict) -> dict:
        """分析单条新闻"""
        title = news.get('title', '')
        content = news.get('content', '')

        # 情绪分析 (复用现有)
        sentiment = self.sentiment_engine.analyze(title + ' ' + content)

        # 股票关联分析 (新增)
        related_stocks = self._find_related_stocks(title, content)

        # 影响评估 (新增)
        impact = self._assess_impact(news, sentiment, related_stocks)

        return {
            'news': news,
            'sentiment': sentiment,
            'related_stocks': related_stocks,
            'impact': impact
        }
```

### 4.2 股票关联分析

```python
class StockRelationAnalyzer:
    """股票关联分析器"""

    def __init__(self, monitored_stocks: List[str]):
        self.monitored_stocks = monitored_stocks
        self.stock_info = {}  # 股票代码 -> {name, industry, concepts}

    def find_related(self, text: str) -> List[dict]:
        """查找文本中提到的监控股票"""
        related = []

        for code in self.monitored_stocks:
            info = self.stock_info.get(code, {})
            name = info.get('name', '')

            # 直接匹配
            if code in text or name in text:
                related.append({
                    'code': code,
                    'name': name,
                    'match_type': 'direct',
                    'relevance': 1.0
                })
            # 行业匹配
            elif self._match_industry(info.get('industry'), text):
                related.append({
                    'code': code,
                    'name': name,
                    'match_type': 'industry',
                    'relevance': 0.6
                })

        return related
```

### 4.3 影响评估引擎

```python
class ImpactAssessor:
    """影响评估引擎"""

    # 高影响关键词
    HIGH_IMPACT = ['涨停', '跌停', '停牌', '退市', '重组', '立案', '处罚']
    URGENT = ['停牌', '退市', '立案', '暴跌', '闪崩', '紧急']

    def assess(self, news: dict, sentiment: dict, related_stocks: List) -> dict:
        """评估新闻影响"""
        text = news.get('title', '') + news.get('content', '')

        # 计算影响分数 (1-10)
        score = 5
        for keyword in self.HIGH_IMPACT:
            if keyword in text:
                score += 1
        score = min(10, score)

        # 判断紧急程度
        urgency = 'high' if any(k in text for k in self.URGENT) else 'medium'

        # 是否需要通知
        should_notify = (
            score >= 7 or
            urgency == 'high' or
            (len(related_stocks) > 0 and score >= 5)
        )

        return {
            'impact_score': score,
            'urgency': urgency,
            'sentiment': sentiment.get('label', 'neutral'),
            'should_notify': should_notify,
            'related_count': len(related_stocks)
        }
```

---

## 五、实时通知系统

### 5.1 WebSocket 推送

```python
class RealtimeNotifier:
    """实时通知器"""

    def __init__(self):
        self.connections: Set[WebSocket] = set()

    async def broadcast(self, message: dict):
        """广播消息到所有连接"""
        data = json.dumps(message, ensure_ascii=False)
        for ws in self.connections.copy():
            try:
                await ws.send_text(data)
            except:
                self.connections.discard(ws)

    async def notify_news(self, news: dict, analysis: dict):
        """通知新新闻"""
        if analysis['impact']['should_notify']:
            await self.broadcast({
                'type': 'news_alert',
                'data': {
                    'news': news,
                    'analysis': analysis,
                    'timestamp': datetime.now().isoformat()
                }
            })
```

### 5.2 通知分级

| 级别 | 条件 | 通知方式 |
|------|------|----------|
| 紧急 | urgency=high 或 impact>=9 | 弹窗+声音+推送 |
| 重要 | impact>=7 且 related_stocks>0 | 弹窗+推送 |
| 一般 | impact>=5 且 related_stocks>0 | 列表高亮 |
| 普通 | 其他 | 静默更新 |

---

## 六、API 统一设计

### 6.1 新闻中心 API

```python
# 所有新闻相关请求统一入口
@router.get("/api/news-center/latest")
async def get_latest_news(
    limit: int = 50,
    source: str = None,
    sentiment: str = None
):
    """获取最新新闻（所有模块调用此接口）"""
    return news_center.get_latest(limit, source, sentiment)

@router.get("/api/news-center/stock/{code}")
async def get_stock_news(code: str, limit: int = 20):
    """获取股票相关新闻（详情模态框、智能分析调用）"""
    return news_center.get_by_stock(code, limit)

@router.get("/api/news-center/announcements")
async def get_announcements(code: str = None, limit: int = 20):
    """获取公告（整合巨潮资讯）"""
    return news_center.get_announcements(code, limit)

@router.websocket("/api/news-center/realtime")
async def realtime_news(websocket: WebSocket):
    """WebSocket 实时推送"""
    await news_center.connect(websocket)
```

### 6.2 前端调用统一

```javascript
// 所有页面统一使用 NewsService
class NewsService {
  static async getLatest(options = {}) {
    return axios.get('/api/news-center/latest', { params: options })
  }

  static async getStockNews(code, limit = 20) {
    return axios.get(`/api/news-center/stock/${code}`, { params: { limit } })
  }

  static async getAnnouncements(code = null) {
    return axios.get('/api/news-center/announcements', { params: { code } })
  }

  static connectRealtime(onMessage) {
    const ws = new WebSocket(`${WS_BASE}/api/news-center/realtime`)
    ws.onmessage = (event) => onMessage(JSON.parse(event.data))
    return ws
  }
}
```

---

## 七、实施计划

### 第一阶段：统一新闻中心核心（3-4天）

1. **创建 NewsMonitorCenter 类**
   - 整合所有数据源
   - 实现统一缓存
   - 激活巨潮资讯爬虫

2. **实现后台调度器**
   - 分层定时任务
   - 进程池隔离
   - 增量检测

3. **统一 API 接口**
   - 创建 `/api/news-center/*` 路由
   - 迁移现有接口

### 第二阶段：智能分析整合（2-3天）

1. **复用情绪分析引擎**
2. **实现股票关联分析**
3. **实现影响评估引擎**

### 第三阶段：实时推送（2天）

1. **WebSocket 服务**
2. **通知分级系统**
3. **前端通知组件**

### 第四阶段：前端迁移（2天）

1. **数据流页面迁移**
2. **详情模态框迁移**
3. **智能分析迁移**
4. **统一新闻中心迁移**

---

## 八、性能指标

| 指标 | 目标值 | 测量方法 |
|------|--------|----------|
| 新闻延迟 | <30秒 | 发布时间 vs 通知时间 |
| 公告延迟 | <60秒 | 发布时间 vs 通知时间 |
| API响应 | <200ms | 接口响应时间 |
| 内存占用 | <500MB | 新闻缓存内存 |
| CPU占用 | <10% | 后台任务CPU |

---

## 九、文件结构

```
backend/
├── services/
│   └── news_monitor_center.py      # 统一新闻监控中心 (新建)
├── dataflows/
│   ├── news/
│   │   ├── sentiment_engine.py     # 情绪分析引擎 (复用)
│   │   ├── stock_relation.py       # 股票关联分析 (新建)
│   │   └── impact_assessor.py      # 影响评估引擎 (新建)
│   └── announcement/
│       └── cninfo_crawler.py       # 巨潮爬虫 (激活)
├── api/
│   └── news_center_api.py          # 统一新闻API (新建)
└── websocket/
    └── news_realtime.py            # WebSocket推送 (新建)
```
