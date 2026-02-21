# 架构审计报告：双驱动架构优化

## 1. 现状诊断

### 数据采集流（Data Collection）
```
akshare → market_adapter.py (daemon thread 预加载 spot)
       → news_monitor_center.py (4源轮询: CLS/东财/新浪/巨潮)
       → stock_data_service.py (按需获取)
       → 三级缓存: L1(内存5min) → L2(Redis 1hr) → L3(文件24hr)
```

### AI分析流（Analysis）
```
前端点击 → POST /api/analyze → 构建prompt → 调LLM(kirocpa/kimi-k2.5) → 返回结果
         → 21个智能体串行/并行调用，每个独立获取数据
```

### 断裂点（优化前）

| 断裂点 | 问题 | 影响 |
|--------|------|------|
| 数据→分析无联动 | 新闻更新后不触发任何分析动作 | 用户看到的分析可能基于过时数据 |
| 无分析缓存 | 同一股票5秒内点两次 = 两次LLM调用 | 浪费API额度，响应慢 |
| 智能体数据不共享 | 21个智能体各自获取相同的行情/新闻 | 重复IO，数据不一致 |
| 无异动自动检测 | 涨停/跌停/放量无主动通知 | 错过交易机会 |

## 2. 优化方案（已实施）

### 2.1 事件总线 EventBus
- 文件: `backend/services/event_bus.py`
- 轻量级 pub/sub，线程安全单例
- 事件类型: NEWS_URGENT / NEWS_BATCH / MARKET_ANOMALY / ANALYSIS_COMPLETED / ANALYSIS_FAILED
- 支持同步/异步回调

### 2.2 分析结果缓存 AnalysisCache
- 文件: `backend/services/analysis_cache.py`
- 缓存键: `{agent_id}:{stock_code}`
- 交易时段 TTL=5min，非交易时段 TTL=30min
- 数据变化检测（关键字段hash比对）
- fallback_level≥99 的兜底文本不缓存

### 2.3 共享数据上下文 SharedDataContext
- 文件: `backend/services/shared_data_context.py`
- 会话级数据预获取（新闻 + 增强行情）
- 同一股票2分钟内复用上下文
- 提供 `get_enriched_stock_data()` 和 `build_news_context()` 给智能体

### 2.4 自动分析触发器 AutoAnalysisTrigger
- 文件: `backend/services/auto_analysis_trigger.py`
- 订阅 NEWS_URGENT → 使相关股票缓存失效
- 订阅 MARKET_ANOMALY → 使异动股票缓存失效
- 定时任务: 交易时段每60秒异动检测（涨停/跌停/换手率>15%）
- 定时任务: 每5分钟清理过期缓存和会话

### 2.5 /api/analyze 端点增强
- 文件: `backend/server.py` (line ~2430)
- 新增: 缓存命中检查（命中直接返回，跳过LLM）
- 新增: SharedDataContext 预获取 + 数据增强
- 新增: 新闻上下文注入到 prompt
- 新增: 分析完成/失败事件发布

### 2.6 NewsMonitorCenter 接入 EventBus
- 文件: `backend/services/news_center/news_monitor_center.py`
- P0/P1 新闻 → 发布 NEWS_URGENT 事件（含关联股票列表）
- 每批新闻 → 发布 NEWS_BATCH 事件

## 3. 优化后数据流

```
                    ┌─────────────────────────────────────────┐
                    │              EventBus                     │
                    │  NEWS_URGENT / MARKET_ANOMALY / ...       │
                    └──┬──────────┬──────────────┬─────────────┘
                       │          │              │
              ┌────────▼──┐  ┌───▼────────┐  ┌──▼──────────────┐
              │ NewsMonitor│  │ AutoTrigger│  │ /api/analyze    │
              │ Center     │  │ (定时异动) │  │ (缓存+上下文)   │
              └────────────┘  └────────────┘  └─────────────────┘
                  发布事件        订阅事件         发布完成事件
                                 失效缓存         查缓存→LLM→存缓存
```

**关键改进**: 数据变更 → 事件 → 缓存失效 → 下次请求获取最新分析。
不主动触发LLM调用（避免烧额度），但保证用户永远看到基于最新数据的分析。

## 4. 新增文件清单

| 文件 | 类型 | 说明 |
|------|------|------|
| `backend/services/event_bus.py` | 新增 | 事件总线 |
| `backend/services/analysis_cache.py` | 新增 | 分析缓存 |
| `backend/services/shared_data_context.py` | 新增 | 共享数据上下文 |
| `backend/services/auto_analysis_trigger.py` | 新增 | 自动分析触发器 |
| `backend/server.py` | 修改 | /api/analyze 集成 + lifespan 注册 |
| `backend/services/news_center/news_monitor_center.py` | 修改 | EventBus 事件发布 |

## 5. 约束遵守

- ✅ 未修改数据库结构
- ✅ 未改动 LLM API 调用方式（kirocpa + kimi-k2.5 不变）
- ✅ API 接口完全兼容（前端无需改动，返回格式不变，新增 `cached` 字段可选）
- ✅ 所有新组件通过 try/except 保护，失败时降级为原有行为
