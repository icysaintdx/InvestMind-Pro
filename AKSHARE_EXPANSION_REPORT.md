# AKShare 数据接口扩展报告

## 概述

为 InvestMindPro 项目扩展了 7 类 AKShare 历史数据接口，新增 2 个文件，未修改任何现有文件。

## 新增文件

| 文件 | 用途 |
|------|------|
| `backend/services/akshare_data_service.py` | 数据服务层，封装所有 akshare 调用 |
| `backend/api/akshare_history_api.py` | RESTful API 路由层，前缀 `/api/data` |

## 接口清单

| 路由 | 方法 | 说明 | akshare 接口 |
|------|------|------|-------------|
| `/api/data/fund-flow/{stock_code}` | GET | 个股历史资金流向 | `stock_individual_fund_flow` + `stock_individual_fund_flow_rank` |
| `/api/data/lhb/history` | GET | 龙虎榜历史明细 | `stock_lhb_detail_daily_sina` + `stock_lhb_jgzz_sina` |
| `/api/data/block-trade/{stock_code}` | GET | 大宗交易 | `stock_dzjy_sctj` + `stock_dzjy_mrmx` |
| `/api/data/margin/{stock_code}` | GET | 融资融券 | `stock_margin_detail_szse` + `stock_margin_detail_sse` |
| `/api/data/zt-pool` | GET | 涨停板池 | `stock_zt_pool_em` + `stock_zt_pool_strong_em` |
| `/api/data/dt-pool` | GET | 跌停板池 | `stock_zt_pool_dtgc_em` |
| `/api/data/zb-pool` | GET | 炸板池 | `stock_zt_pool_zbgc_em` |
| `/api/data/cache/stats` | GET | 缓存统计 | — |
| `/api/data/cache/clear` | POST | 清空缓存 | — |

## 接口修正说明

原始需求中有 2 个接口名称在 akshare 中不存在，已自动修正：

| 原始需求 | 实际使用 | 原因 |
|----------|----------|------|
| `stock_dzjy_mdetail` | `stock_dzjy_mrmx` | akshare 无 mdetail 函数，mrmx 为每日明细 |
| `stock_lhb_jgzz` | `stock_lhb_jgzz_sina` | 实际函数名带 _sina 后缀 |

## 缓存策略

- 交易时段（周一至周五 9:15-15:30）：TTL = 60 秒
- 非交易时段：TTL = 3600 秒（1小时）
- 基于内存字典 + 线程锁，轻量无外部依赖

## 技术实现

- 异步执行：akshare 同步调用通过 `ThreadPoolExecutor` + `asyncio.wait_for` 包装为异步
- 并行请求：同一接口内多个 akshare 调用使用 `asyncio.gather` 并行
- 错误处理：每个 akshare 调用独立 try/except，超时自动降级返回空
- 日志：使用项目统一的 `get_logger` 记录调用结果
- NaN 处理：DataFrame 中的 NaN 转为 None，避免 JSON 序列化问题

## 路由注册

在 `backend/server.py` 中添加以下代码即可启用：

```python
from backend.api.akshare_history_api import router as akshare_history_router
app.include_router(akshare_history_router)
```

## curl 测试命令

路由注册后可用以下命令验证：

```bash
# 个股资金流向
curl http://localhost:8000/api/data/fund-flow/000001

# 龙虎榜历史
curl "http://localhost:8000/api/data/lhb/history?date=20260220"

# 大宗交易
curl "http://localhost:8000/api/data/block-trade/600519?start_date=20260201&end_date=20260220"

# 融资融券
curl "http://localhost:8000/api/data/margin/000001?date=20260220"

# 涨停板池
curl http://localhost:8000/api/data/zt-pool

# 跌停板池
curl http://localhost:8000/api/data/dt-pool

# 炸板池
curl http://localhost:8000/api/data/zb-pool

# 缓存统计
curl http://localhost:8000/api/data/cache/stats
```

## 注意事项

- `akshare_data_api.py`（已有文件，前缀 `/api/akshare`）未被修改
- 新路由使用 `/api/data` 前缀，与现有路由无冲突
- 涨停/跌停/炸板池接口仅支持最近 30 个交易日的数据
