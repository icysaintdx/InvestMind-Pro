# 📋 InvestMindPro 项目接下来工作计划

**制定时间:** 2026-02-20 凌晨  
**制定人:** 臭宝 🦨

---

## 🎯 核心目标（未来2-4周）

**实现真正的"技术+新闻双驱动"系统**
- 技术面分析 ✅ 已有
- 新闻面分析 ✅ 已有  
- **双驱动融合** ❌ 缺失（重点！）
- **新闻回测** ❌ 缺失（重点！）

---

## Phase 1: 基础设施完善（本周内）

### 1.1 API修复验证与推送
- [ ] 启动后端，测试3个修复的API
  - `/api/paper-trading/*`
  - `/api/auto-trading/status`
  - `/api/backtest/status`
- [ ] 确认修复有效后push（等你发"怼"）

### 1.2 依赖包安装
```bash
pip install stockstats pymongo redis schedule pywencai
```
- [ ] stockstats - 技术指标
- [ ] schedule - 定时任务（数据清理调度器）
- [ ] 其他可选

### 1.3 NotificationService修复
- [ ] 补上 `send_batch_alerts` 方法
- [ ] P0新闻通知恢复正常

---

## Phase 2: 新闻回测引擎（第1-2周）⭐核心

### 2.1 设计数据对齐方案
```
回测时间点: 2024-06-15 10:00
├── K线数据: 开盘价、收盘价、成交量... ✅ 已有
└── 新闻数据: 当天及之前的新闻 ✅ 从数据库取
    └── AI情绪分析: 当日市场情绪得分
```

### 2.2 实现核心模块
| 模块 | 文件 | 功能 |
|------|------|------|
| 新闻历史查询 | `news_backtest_engine.py` | 按日期取新闻+情绪分析 |
| 联合回测 | `joint_backtest.py` | 技术+新闻联合回测 |
| 回测API | `backtest_api.py` 扩展 | 新增 `/backtest/news` 端点 |

### 2.3 关键算法
```python
# 伪代码示意
class NewsBacktestEngine:
    def run(self, strategy, stock_code, start_date, end_date):
        for date in trading_days:
            # 获取当日技术数据
            kline = get_kline(stock_code, date)
            
            # 获取当日新闻数据（关键！）
            news = self.get_news_until(date)
            sentiment = self.analyze_sentiment(news)
            
            # 策略决策（能看到新闻）
            signal = strategy.evaluate(
                kline=kline,
                news_sentiment=sentiment,
                news_events=news
            )
            
            # 记录结果
            results.append({date, signal, sentiment})
        
        return performance_report
```

### 2.4 验收标准
- [ ] 能选择"带新闻回测"或"纯技术回测"
- [ ] 回测报告包含新闻情绪曲线
- [ ] 能对比两种回测的差异

---

## Phase 3: 双驱动权重调配（第2-3周）⭐核心

### 3.1 市场状态识别
```python
class MarketStateDetector:
    """识别当前市场状态"""
    
    def detect(self, market_data):
        if self.is_high_volatility():  # 高波动
            return "震荡市"  # 技术面权重70%
        elif self.has_major_news():  # 重大事件
            return "事件驱动"  # 新闻面权重70%
        elif self.is_strong_trend():  # 强趋势
            return "趋势市"  # 技术面60%
        else:
            return "平衡市"  # 各50%
```

### 3.2 动态权重分配
| 市场状态 | 技术面权重 | 新闻面权重 | 触发条件 |
|---------|-----------|-----------|---------|
| 震荡市 | 70% | 30% | 波动率>3% |
| 事件驱动 | 30% | 70% | P0新闻出现 |
| 趋势市 | 60% | 40% | 均线多头排列 |
| 平衡市 | 50% | 50% | 默认状态 |

### 3.3 信号融合
```python
# 综合评分 = 技术面得分 × 技术权重 + 新闻面得分 × 新闻权重
combined_score = (
    tech_signal.score * weights['technical'] +
    news_signal.score * weights['news']
)
```

### 3.4 验收标准
- [ ] 前端显示当前市场状态
- [ ] 显示技术面/新闻面实时权重
- [ ] 权重变化有日志记录

---

## Phase 4: AI策略生成器（第3-4周）

### 4.1 自动生成策略
```python
class AIStrategyGenerator:
    def generate(self, stock_code):
        # 1. 分析股票特征
        features = self.analyze_stock_features(stock_code)
        
        # 2. LLM生成策略代码
        strategy_code = llm.generate(prompt=features)
        
        # 3. 自动回测验证
        result = backtest.run(strategy_code, stock_code)
        
        # 4. 表现好则保存
        if result.sharpe > 1.5:
            self.save_strategy(stock_code, strategy_code)
```

### 4.2 验收标准
- [ ] 输入股票代码，自动生成策略
- [ ] 策略自动回测验证
- [ ] 表现好的策略入库

---

## Phase 5: 数据与优化（持续）

### 5.1 新闻数据积累
- [x] 系统已运行，每日自动采集
- [ ] 等你闲鱼买的历史数据导入
- [ ] 目标：3个月后自有3个月历史数据

### 5.2 性能优化（可选）
- [ ] SQLite → PostgreSQL 迁移
- [ ] Redis缓存加速
- [ ] WebSocket实时推送优化

---

## 📊 优先级矩阵

| 优先级 | 任务 | 价值 | 工作量 | 建议 |
|--------|------|------|--------|------|
| 🔴 P0 | 新闻回测引擎 | ⭐⭐⭐⭐⭐ | 2周 | **必做，核心竞争力** |
| 🔴 P0 | 双驱动权重调配 | ⭐⭐⭐⭐⭐ | 1-2周 | **必做，双驱动核心** |
| 🟡 P1 | AI策略生成器 | ⭐⭐⭐⭐ | 1-2周 | 重要，可做 |
| 🟡 P1 | API修复验证 | ⭐⭐⭐ | 1天 | 简单，尽快做 |
| 🟢 P2 | 性能优化 | ⭐⭐⭐ | 持续 | 后期再做 |

---

## 🚀 立即开始

### 今天/明天要做的：
1. **启动后端**，验证3个API修复是否有效
2. **安装依赖包**（stockstats, schedule）
3. **白天提醒你**去闲鱼买历史新闻数据

### 本周要做的：
1. 开始写**新闻回测引擎**
2. 设计**双驱动权重调配**架构

---

## 💡 关键决策点

### 决策1: 先push修复还是先写新功能？
**建议:** 先验证API修复有效，然后push，再写新功能
**理由:** 基础要稳，新功能依赖这些API

### 决策2: 新闻回测的数据范围？
**建议:** 先支持近3个月数据（从系统数据库取）
**理由:** 等你买的历史数据导入后，自动扩展

### 决策3: 双驱动的权重算法复杂度？
**建议:** 先实现4种市场状态的固定权重
**理由:** 简单有效，后期可用强化学习优化

---

## ⏰ 提醒事项

| 时间 | 事项 | 谁来做 |
|------|------|--------|
| 白天 | 去闲鱼买历史新闻数据 | 大佬 |
| 随时 | 买完后发我数据格式，我写导入脚本 | 臭宝 |
| 本周内 | 验证API修复并push | 臭宝（等你"怼"） |
| 第1-2周 | 新闻回测引擎 | 臭宝 |
| 第2-3周 | 双驱动权重调配 | 臭宝 |

---

**怼不怼？** 
- 先验证API修复然后push？
- 还是直接开始写新闻回测引擎？
- 或者两者同时进行？
