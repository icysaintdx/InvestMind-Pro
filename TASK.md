# TASK: API 全面审计与优化

## 项目背景
InvestMindPro 是一个 A股智能分析系统，21个AI智能体协作分析股票。
- 后端：FastAPI (uvicorn)，端口 8000
- 前端：Vue.js (已构建在 frontend/dist/)
- 数据库：SQLite (InvestMindPro.db)
- 数据源：akshare (A股实时数据)
- LLM：通过 kirocpa 代理 (https://kirocpa.zeabur.app/v1)，key=icysaintdx，模型 kimi-k2.5

## 你的任务
系统性审计所有 API 端点，修复问题，优化性能。确保前端每个功能都能正常工作。

## 具体工作

### 1. 端点审计
逐个测试以下 API 路由（在 backend/server.py 和 backend/api/ 下）：
- `/api/market/overview` — 市场概览
- `/api/market/hot-sectors` — 热门板块
- `/api/market/top-amount` — 成交额排行
- `/api/market/bid-ask/{code}` — 盘口数据
- `/api/market/transactions/{code}` — 成交明细
- `/api/market/longhubang/*` — 龙虎榜
- `/api/analysis/*` — 智能体分析
- `/api/strategy/*` — 策略中心
- `/api/news/*` — 新闻中心
- `/api/monitor/*` — 自选股监控
- `/api/backtest/*` — 回测
- `/api/paper-trading/*` — 模拟交易
- `/api/auto-trading/*` — 自动交易
- `/api/sector-rotation/*` — 板块轮动

### 2. 每个端点检查
- 返回格式是否正确（前端期望的字段名、结构）
- 错误处理是否完善（网络超时、数据为空、非交易时间）
- 响应速度是否合理（目标 <3秒，市场数据可接受 <10秒）
- 非交易时间（周末/节假日）是否返回缓存数据而非空数据

### 3. 已知问题
- 部分端点在非交易时间返回空数据
- 某些端点返回格式与前端期望不匹配（如 data 包装层级问题）
- market_adapter.py 是实际的市场路由（不是 market_data_api.py，后者被注释掉了）
- longhubang_adapter.py 是龙虎榜路由
- sector_rotation_adapter.py 是板块轮动路由

### 4. 关键文件
- `backend/server.py` — 主服务器，所有路由注册
- `backend/api/market_adapter.py` — 市场数据 API
- `backend/api/longhubang_adapter.py` — 龙虎榜 API
- `backend/api/sector_rotation_adapter.py` — 板块轮动 API
- `backend/api/strategy_center_api.py` — 策略中心 API
- `backend/api/news_center_api.py` — 新闻中心 API
- `frontend/src/views/` — 前端页面（了解前端期望的数据格式）

## 约束
- 不要修改数据库结构（正在导入历史数据）
- 不要改动 LLM 调用逻辑（已调通）
- 修复时保持向后兼容，不要破坏已工作的功能
- 用 curl 测试每个端点，记录结果

## 交付物
1. API 审计报告（每个端点的状态、问题、修复）
2. 所有修复的代码变更
3. 测试验证结果
