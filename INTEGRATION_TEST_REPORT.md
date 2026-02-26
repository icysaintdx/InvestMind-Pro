# 集成测试报告 - InvestMindPro

**测试时间**: 2026-02-22 00:55 ~ 01:10 CST  
**测试环境**: http://localhost:8000  
**测试人**: AI集成测试智能体

---

## 1. 新模块验证

### 1.1 模块导入与单例测试

| 模块 | 导入 | 单例 | 备注 |
|------|------|------|------|
| `services/event_bus.py` | ✅ | ✅ | EventBus 线程安全单例，8种事件类型 |
| `services/analysis_cache.py` | ✅ | ✅ | TTL缓存，交易时段5min/非交易30min |
| `services/shared_data_context.py` | ✅ | ✅ | 会话级复用（2min TTL），get_or_create 正常 |
| `services/auto_analysis_trigger.py` | ✅ | ✅ | 依赖 event_bus + analysis_cache + shared_data_context |
| `services/sentiment_trend_service.py` | ✅ | ✅ | DB路径: data/news_storage/news_database.db |
| `services/strategy/ai_weight_adjuster.py` | ✅ | ✅ | 16个策略权重，进攻/防守/中性分类 |

### 1.2 事件总线 Pub/Sub 测试

```
测试: 发布 ANALYSIS_COMPLETED 事件 → 异步订阅者接收
结果: ✅ 成功接收 {"test": true}
```

### 1.3 AnalysisCache Put/Get 测试

```
测试: put("test_agent", "600519", 90字符文本) → get("test_agent", "600519")
结果: ✅ 缓存命中，stats: hits=1, stores=1, hit_rate=100.0%
```

### 1.4 AIWeightAdjuster 调整测试

```
输入: direction=bullish, momentum=0.5, confidence=0.8
结果: ✅ 16个策略权重已调整
  - ema_breakout: 0.7 → 0.8 (进攻型加成)
  - vegas_adx: 0.8 (中性不变)
```

### 1.5 跨模块导入关系

| 消费方 | 导入的模块 |
|--------|-----------|
| `server.py` | event_bus, analysis_cache, shared_data_context, auto_analysis_trigger |
| `auto_analysis_trigger.py` | event_bus, analysis_cache, shared_data_context |
| `strategies/manager.py` | sentiment_trend_service, ai_weight_adjuster |
| `news_center/news_monitor_center.py` | event_bus |

---

## 2. Monitor API 超时修复

### 2.1 问题

`/api/monitor/status` 和 `/api/monitor/summary` 每次请求都实时测试所有外部API（AKShare 50+接口、AI服务6个、内部API 8个），导致响应时间 >30秒。

### 2.2 修复方案

文件: `backend/api/api_monitor_api.py`

- 新增 `_monitor_cache` 内存缓存字典
- 新增 `_refresh_status_cache()` 和 `_refresh_summary_cache()` 后台刷新函数
- `/status` 和 `/summary` 端点改为：
  - 有缓存且未过期 → 直接返回（毫秒级）
  - 有缓存但过期 → 返回旧缓存 + `asyncio.ensure_future` 后台刷新
  - 无缓存（首次） → 返回空响应 + 后台刷新（不阻塞）
- 缓存 TTL: status=120s, summary=60s
- 新增 `force_refresh` 查询参数支持强制刷新

### 2.3 测试结果

| 端点 | 修复前 | 修复后 | 状态 |
|------|--------|--------|------|
| `/api/monitor/status?include_akshare=false&include_ai=false` | >30s | 0.41s | ✅ |
| `/api/monitor/status` (全量，含AKShare) | >60s | 首次空响应+后台刷新，后续<1s | ✅ |
| `/api/monitor/summary` | >30s | 首次空响应+后台刷新，后续<1s | ✅ |

**注意**: 未修改 `server.py`，仅修改 `api_monitor_api.py`。

---

## 3. 分析端点测试

### 3.1 POST /api/analyze

```bash
curl -X POST http://localhost:8000/api/analyze \
  -H 'Content-Type: application/json' \
  -d '{"agent_id":"technical","stock_code":"600519","stock_data":{"stock_name":"贵州茅台","nowPri":"1800","increase":"1.5"}}'
```

| 项目 | 结果 |
|------|------|
| HTTP状态码 | 200 ✅ |
| 响应时间 | 10.8s（含LLM调用） |
| 返回格式 | `{"success":true, "result":"...", "fallback_level":0}` ✅ |
| LLM分析内容 | 技术分析师返回完整分析（含DIGEST摘要） ✅ |
| fallback_level | 0（原始质量，未降级） ✅ |

**注意**: 请求体需要 `agent_id` 字段（非 `agents` 数组），这是单智能体分析接口。

---

## 4. 前端关键API测试

| 端点 | 状态码 | 响应时间 | 数据格式 | 状态 |
|------|--------|----------|----------|------|
| `GET /api/news-center/market?limit=3` | 200 | 11ms | `{success, news[], data[], sentiment_stats}` | ✅ |
| `GET /api/config` | 200 | 3ms | `{api_keys, model_configs, endpoints}` | ✅ |
| `GET /api/dataflow/sources/status` | 200 | 3ms | `{success, sources[]}` | ✅ |
| `GET /api/backtest/strategies` | 200 | 3ms | `{success, strategies[], total:16}` | ✅ |
| `GET /health` | 200 | 3ms | `{"status":"healthy"}` | ✅ |
| `GET /api/agents` | 404 | <1ms | 接口不存在 | ⚠️ 已知问题 |

---

## 5. 已知问题

| # | 问题 | 严重度 | 说明 |
|---|------|--------|------|
| 1 | `/api/agents` 返回404 | 低 | 内部监控配置中引用了该端点，但路由未注册 |
| 2 | TDX导入路径错误 | 低 | `api_monitor_api.py` 中 `from backend.dataflows.providers.tdx_native_provider` 无法解析（pre-existing，非本次引入） |
| 3 | `/api/monitor/summary` 首次调用需等待后台刷新 | 低 | 设计如此，前端可轮询或使用 `/api/monitor/stream` SSE |

---

## 6. 总结

- **6个新模块**: 全部通过导入、单例、功能验证 ✅
- **事件总线**: pub/sub 工作正常 ✅
- **Monitor超时修复**: 已实现后台缓存方案，`/status` 响应从 >30s 降至 <1s ✅
- **分析端点**: LLM调用正常，返回格式正确 ✅
- **前端API**: 5/6 关键端点正常 ✅
