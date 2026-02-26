# 🐛 InvestMindPro Bug 检测报告

**检测时间:** 2026-02-20  
**检测者:** 臭宝 🦨  
**项目路径:** `/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro`

---

## 🔴 严重 Bug (Critical)

### Bug #1: paper_trading_api 未注册到主服务器 ❌

**问题描述:**
- 文件 `backend/api/paper_trading_api.py` 存在且完整定义了路由
- 但 `backend/server.py` 中**完全没有导入和注册** `paper_trading_router`

**影响:**
- 所有 `/api/paper-trading/*` 端点返回 404
- 包括：创建账户、查询持仓、下单等功能全部不可用

**修复方案:**
```python
# 在 backend/server.py 中添加：
from backend.api.paper_trading_api import router as paper_trading_router

# 在路由注册区域添加：
app.include_router(paper_trading_router)  # 模拟交易API
```

---

### Bug #2: auto_trading_api 缺少 /status 端点 ❌

**问题描述:**
- `backend/api/auto_trading_api.py` 已注册到server.py
- 但定义的路由中没有 `/status` 端点

**现有端点:**
- ✅ `/api/auto-trading/start` (POST)
- ✅ `/api/auto-trading/stop/{task_id}` (POST)
- ✅ `/api/auto-trading/tasks` (GET)
- ✅ `/api/auto-trading/task/{task_id}` (GET)
- ✅ `/api/auto-trading/test` (GET)
- ❌ `/api/auto-trading/status` (GET) - **缺失！**

**修复方案:**
在 `auto_trading_api.py` 中添加状态端点：
```python
@router.get("/status")
async def get_auto_trading_status():
    """获取自动交易服务状态"""
    return {
        "service_status": "running" if active_tasks else "idle",
        "active_tasks_count": len(active_tasks),
        "total_tasks": len(active_tasks)
    }
```

---

### Bug #3: backtest_api 的 /status 需要 task_id ❌

**问题描述:**
- 用户期望: `/api/backtest/status` 返回整体回测服务状态
- 实际情况: 只有 `/api/backtest/status/{task_id}` 返回特定任务状态

**现有端点:**
- ✅ `/api/backtest/status/{task_id}` - 查询特定任务状态
- ❌ `/api/backtest/status` - 缺失整体状态端点

**修复方案:**
添加无参数的整体状态端点：
```python
@router.get("/status")
async def get_backtest_service_status():
    """获取回测服务整体状态"""
    return {
        "service": "running",
        "active_tasks": len(active_backtests),
        "queue_size": backtest_queue.qsize() if backtest_queue else 0
    }
```

---

## 🟡 中度 Bug (Major)

### Bug #4: API Key 无效导致新闻分析失败 ⚠️

**问题描述:**
日志中大量报错：
```
NewsEmotionAnalyzer - ERROR - LLM call failed: Error code: 401 - Api key is invalid
```

**影响:**
- 新闻情绪分析功能完全失效
- 所有新闻的情绪评分都失败

**原因:**
- SiliconFlow API Key 可能已过期或无效
- 或其他LLM提供商的API Key配置错误

**修复方案:**
1. 检查 `.env` 文件中的 API Keys
2. 更新有效的 SiliconFlow API Key
3. 或切换到其他LLM提供商

---

### Bug #5: NotificationService 缺少 send_batch_alerts 方法 ⚠️

**问题描述:**
```
Failed to send P0 notification: 'NotificationService' object has no attribute 'send_batch_alerts'
```

**位置:** `backend/services/news_center/news_monitor_center.py`

**影响:**
- P0级重要新闻无法发送通知
- 预警系统部分功能失效

---

## 🟢 轻微问题 (Minor)

### Issue #6: 依赖包缺失

**缺失的依赖:**
- `stockstats` - 技术指标功能不可用
- `pymongo` - MongoDB功能不可用
- `redis` - Redis缓存不可用（已降级到内存模式）
- `schedule` - 数据清理调度器启动失败
- `pywencai` - 问财数据源不可用

**修复:**
```bash
pip install stockstats pymongo redis schedule pywencai
```

---

## ✅ 确认正常工作的组件

| 组件 | 状态 | 说明 |
|------|------|------|
| 后端服务器 | ✅ | FastAPI 可正常启动 |
| 21个AI智能体 | ✅ | 全部注册成功 |
| 16个交易策略 | ✅ | 全部加载成功 |
| 新闻采集 | ✅ | 各数据源正常采集 |
| 数据库存储 | ✅ | SQLite 工作正常 |
| 新闻中心 | ✅ | 统一新闻监控运行中 |
| /api/trading/* | ✅ | 交易API正常（前端在用） |
| /api/agents/* | ✅ | 智能体API正常 |
| /api/news/* | ✅ | 新闻API正常 |

---

## 📝 前端-后端API对应关系

| 前端调用 | 实际后端端点 | 状态 |
|---------|-------------|------|
| `/api/paper-trading/*` | 未注册 | ❌ 404 |
| `/api/trading/portfolio` | `/api/trading/portfolio` | ✅ 正常 |
| `/api/auto-trading/status` | **不存在** | ❌ 404 |
| `/api/backtest/status` | **不存在** (需要task_id) | ❌ 404 |

---

## 🔧 修复优先级建议

1. **P0 (立即修复):**
   - Bug #1: 注册 paper_trading_api
   - Bug #2: 添加 auto_trading/status 端点
   - Bug #3: 添加 backtest/status 端点

2. **P1 (本周修复):**
   - Bug #4: 更新API Keys
   - Bug #5: 修复 NotificationService

3. **P2 (可选):**
   - Issue #6: 安装缺失依赖

---

## 🚀 怼不怼？

大佬，这些bug我都理清楚了：
- **核心问题**: paper_trading_api 完全没注册，是个明显的遗漏
- **接口问题**: 前端期望的 status 端点后端没实现
- **配置问题**: API Key 需要更新

要我直接修吗？还是你先看看？ 🦨
