# Realtime Flash（金十 + 汇通）全链路说明

> 目标：将 JIN10 WebSocket + FX678 抓取写入 `news_storage`，并通过后端 API + 前端页面可视化。

## 1. 架构与能力

### 1.1 数据链路

1. **采集层**
   - `backend/realtime_flash/jin10_ws.py`：JIN10 WebSocket 实时流
   - `backend/realtime_flash/fx678_fetcher.py`：FX678 页面抓取轮询
2. **处理层**
   - `backend/realtime_flash/dedup_store.py`：TTL 去重缓存（文件持久化）
   - `backend/realtime_flash/writer.py`：统一归一化并写入 `news_storage`
3. **运行层**
   - `backend/realtime_flash/runner.py`：支持 daemon、run-once、双源聚合统计
4. **服务层**
   - `backend/api/realtime_flash_api.py`：健康检查/最新数据/run-once/统计/iframe配置

### 1.2 可观测性

- 运行统计：`received/written/duplicated/invalid`
- 源级结果：`source_results`（jin10/fx678 分项）
- 源级错误：`source_errors`
- 降级状态：`degraded + degrade_reasons`
- 去重缓存状态：`dedup_cache_size`、cache 文件存在性

## 2. 配置

```bash
cp backend/realtime_flash/.env.example backend/realtime_flash/.env
```

关键变量：

- `REALTIME_FLASH_ENABLED`：总开关
- `REALTIME_FLASH_JIN10_WS_ENABLED` / `REALTIME_FLASH_FX678_ENABLED`：源开关
- `REALTIME_FLASH_FX678_POLL_SECONDS`：汇通轮询间隔
- `REALTIME_FLASH_*_TIMEOUT_SECONDS`：超时
- `REALTIME_FLASH_FX678_MAX_RETRIES`：重试
- `REALTIME_FLASH_DEDUP_*`：去重缓存策略
- `REALTIME_FLASH_LOG_LEVEL`：日志级别

## 3. 启动与联调

### 3.1 启动后端

```bash
cd backend
python server.py
```

### 3.2 单次采集验证（后端）

```bash
curl -s -X POST 'http://127.0.0.1:8000/api/realtime-flash/run-once' \
  -H 'Content-Type: application/json' \
  -d '{"max_items":30,"ws_wait_seconds":4}'
```

### 3.3 查询最新快讯

```bash
curl -s 'http://127.0.0.1:8000/api/realtime-flash/latest?limit=20&source=all'
```

### 3.4 查看健康与统计

```bash
curl -s 'http://127.0.0.1:8000/api/realtime-flash/health'
curl -s 'http://127.0.0.1:8000/api/realtime-flash/stats'
```

### 3.5 启动前端并查看页面

```bash
cd frontend
npm run serve
```

打开页面后进入：**市场 -> 实时快讯**。

## 4. API 说明

- `GET /api/realtime-flash/health`
  - 返回模块状态、源开关、去重缓存状态、最近降级信息
- `GET /api/realtime-flash/latest?limit=&source=`
  - `source` 支持：`all|jin10|fx678`
  - 返回最新快讯（时间/标题/来源/链接）
- `POST /api/realtime-flash/run-once`
  - body: `{"max_items":20,"ws_wait_seconds":4}`
  - 执行一次双源抓取并写库，返回源级结果与降级信息
- `GET /api/realtime-flash/stats`
  - 返回运行统计、最近执行结果、24h news_storage 概览
- `GET /api/realtime-flash/iframe-config`
  - 读取 `frontend/config/realtime_flash_iframe.yaml`（前端接线入口）

## 5. 前端接线说明（YAML）

`frontend/config/realtime_flash_iframe.yaml` 已由后端接口读取并返回给前端页面：

- `default_provider`：页面默认站点
- `refresh_seconds`：自动刷新间隔
- `providers.jin10/fx678.iframe_url`：站点入口

前端 `RealtimeFlashView.vue` 会调用 `/api/realtime-flash/iframe-config` 动态加载以上配置，不再是“仅文件存在”。

## 6. 降级策略（外网不可达）

- 后端：若外部源不可达，`run-once` 返回 `degraded=true` 与 `degrade_reasons`
- 前端：页面顶部与列表空态显示降级提示（而非静默失败）
- 不注入假数据；仅展示真实抓取与明确错误信息

## 7. 故障排查

1. **run-once 失败**
   - 检查后端日志中的 `source_errors`
   - 检查网络/代理（尤其是 ws/wss 与站点可达性）
2. **latest 无数据**
   - 先调用 `run-once`；再查看 `stats.last_run`
   - 检查 `source_key in (jin10, fx678)` 是否有写入
3. **iframe 空白**
   - 目标站可能启用 `X-Frame-Options/CSP`
   - 使用“新窗口打开”按钮
4. **去重后写入为 0**
   - 检查 `dedup_cache_size` 与 TTL 设置

## 8. 快速验证命令

```bash
python -m py_compile backend/realtime_flash/*.py backend/api/realtime_flash_api.py
python scripts/realtime_flash_smoke_test.py --max-items 20 --hours 24
```

`smoke_test` 输出 `degraded/degrade_reason`，用于判断网络不可达时的可观测降级路径。