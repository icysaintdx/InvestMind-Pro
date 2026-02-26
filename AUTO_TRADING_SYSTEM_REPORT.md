# InvestMindPro 自动模拟交易执行系统 - 完成报告

## 系统概述

基于InvestMindPro现有基础设施，构建了完整的自动模拟交易执行系统。系统通过HTTP API对接现有的策略中心、模拟交易、实时行情三大模块，实现从早盘扫描→自动交易→收盘报告的全流程自动化。

## 文件结构

```
backend/scripts/auto_trading/
├── __init__.py              # 包初始化
├── main.py                  # 主控脚本（CLI入口）
├── pre_market_scanner.py    # 早盘扫描模块
├── trading_engine.py        # 自动交易引擎
├── monitor_reporter.py      # 监控报告模块
├── logs/                    # 运行日志（自动创建）
└── data/                    # 候选列表/交易报告（自动创建）
```

## 模块说明

### 1. 早盘扫描模块 (`pre_market_scanner.py`)

- 扫描沪深15只热门标的（可自定义选股池）
- 调用 `/api/strategy-center/strategies` 自动选择技术类策略
- 调用 `/api/strategy-center/signal/generate` 为每只股票生成信号
- 过滤条件：信号类型非HOLD + 置信度 ≥ 0.55
- 输出：候选列表JSON（股票代码/方向/目标价/止损位/止盈位/置信度）
- API失败自动重试3次，间隔递增

### 2. 自动交易引擎 (`trading_engine.py`)

- 通过 `/api/paper-trading/account/create` 创建模拟账户（初始资金100万）
- 通过 `akshare.stock_zh_a_spot_em()` 批量获取全市场实时价格（5秒缓存）
- 每30秒轮询：
  - 检查持仓是否触发止损/止盈 → 自动通过 `/api/paper-trading/order/place` 平仓
  - 检查未入场候选是否满足条件 → 自动下单买入
- 买入数量按整百股计算，仓位比例由策略信号决定
- 交易时间自动判断（9:30-11:30, 13:00-15:00），收盘自动停止
- Ctrl+C优雅退出

### 3. 监控报告模块 (`monitor_reporter.py`)

- 实时持仓盈亏表：代码/名称/数量/成本/现价/市值/盈亏/盈亏%
- 止损止盈监控状态显示
- 收盘报告：
  - 交易统计：总笔数/买入/卖出/盈利/亏损
  - 盈亏统计：胜率/总盈亏/收益率/平均盈利/平均亏损
- 报告自动保存为JSON

### 4. 主控脚本 (`main.py`)

```bash
# 早盘扫描
python -m backend.scripts.auto_trading.main --mode=pre_market

# 实时交易（需先有候选列表）
python -m backend.scripts.auto_trading.main --mode=realtime

# 完整流程（扫描+交易+报告）
python -m backend.scripts.auto_trading.main --mode=full

# 自定义参数
python -m backend.scripts.auto_trading.main --mode=full \
    --capital=1000000 --interval=30 --stocks=600519,000858,601318
```

CLI参数：
| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--mode` | full | pre_market / realtime / full |
| `--api` | http://localhost:8000 | 后端API地址 |
| `--capital` | 1000000 | 初始资金 |
| `--interval` | 30 | 轮询间隔（秒） |
| `--confidence` | 0.55 | 最低置信度 |
| `--strategy` | 自动选择 | 指定策略ID |
| `--stocks` | 15只热门股 | 自定义选股池 |
| `--candidates-file` | 无 | 直接加载候选文件 |

## 对接的现有API

| API | 用途 |
|-----|------|
| `POST /api/paper-trading/account/create` | 创建模拟账户 |
| `GET /api/paper-trading/account/{id}` | 查询账户+持仓+盈亏 |
| `POST /api/paper-trading/order/place` | 下单（买入/卖出） |
| `GET /api/paper-trading/account/{id}/trades` | 查询交易记录 |
| `GET /api/strategy-center/strategies` | 获取策略列表 |
| `POST /api/strategy-center/signal/generate` | 生成交易信号 |
| `akshare.stock_zh_a_spot_em()` | 全市场实时行情 |

## LLM配置

信号生成通过策略中心API间接调用LLM，配置已在 `agent_configs.json` 中：
- 代理: `https://kirocpa.zeabur.app/v1`
- Key: `icysaintdx`
- Model: `kimi-k2.5`

## 错误处理

- 所有API调用：失败自动重试3次，间隔递增（2s, 4s, 6s）
- akshare行情：5秒缓存避免重复拉取，失败跳过本轮
- 交易引擎：异常不中断主循环，记录日志继续运行
- 信号处理：Ctrl+C / SIGTERM 优雅退出

## 明日9:30运行步骤

1. 启动后端: `python backend/server.py`
2. 运行自动交易: `python -m backend.scripts.auto_trading.main --mode=full`
3. 日志查看: `backend/scripts/auto_trading/logs/`
4. 报告查看: `backend/scripts/auto_trading/data/`

## 验证状态

- [x] 4个模块Python语法验证通过（ast.parse）
- [x] 对接paper_trading_api（不自己写下单逻辑）
- [x] 模拟盘 initial_capital=100万
- [x] 详细日志（每步操作记录，文件+控制台双输出）
- [x] API失败重试3次
