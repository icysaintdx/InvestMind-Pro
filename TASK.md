# TASK: 情绪分析系统 + AI智能策略 升级

## 项目背景
InvestMindPro 是 A股智能分析系统。核心理念：**实时舆情比传统技术指标更能影响短期走势**。
但当前系统的情绪分析和策略都很初级：
- 情绪分析：硬编码关键词匹配，不是真正的AI分析
- 策略系统：从网上搬来的固定规则策略，跟AI没关系
- 两者割裂：情绪分析结果没有真正影响策略决策

## 技术栈
- 后端：FastAPI (Python 3.12)，SQLite
- LLM：kirocpa 代理 (https://kirocpa.zeabur.app/v1)，key=icysaintdx，模型 kimi-k2.5
- 历史新闻数据：正在导入中（news_daily_sentiment 表 + news_articles 表，2001-2024年数据）
- 数据源：akshare（实时行情）、各新闻API（实时新闻）

## 你的任务
升级情绪分析为真正的AI驱动，让策略系统基于实时舆情+技术指标综合决策。

## 具体工作

### 1. 情绪分析系统审计与升级
当前状态：
- `backend/services/news_center/news_emotion_analyzer.py` — 当前的情绪分析器
- 使用 LLM 但可能只是简单的正负面判断
- 没有深度分析（影响程度、持续时间、关联股票、事件类型）

升级方向：
- 审计当前情绪分析的完整流程
- 确保 LLM 情绪分析真正工作（不是关键词匹配）
- 增加分析维度：事件类型（政策/财报/舆论/行业）、影响程度（1-10）、影响时效（短期/中期/长期）
- 利用历史数据：news_daily_sentiment 表有每只股票每天的正面/中性/负面新闻数量统计（2001-2024）
- 构建情绪趋势：近7天/30天情绪变化趋势

### 2. AI策略系统审计与升级
当前状态：
- `backend/services/strategy/` — 策略服务
- `backend/api/strategy_center_api.py` — 策略API
- 策略可能是固定规则（均线交叉、MACD、RSI等传统技术指标）

升级方向：
- 审计当前所有策略的实现
- 找出哪些是"死策略"（固定规则，不用AI）
- 设计"AI策略选择器"：根据当前市场环境+舆情，AI决定用哪个策略组合
- 策略权重动态调整：舆情好时偏进攻，舆情差时偏防守
- 加入舆情因子：策略决策时必须考虑近期新闻情绪

### 3. 情绪-策略联动
核心目标：让情绪分析结果直接影响策略决策
- 情绪评分 → 策略权重调整
- 重大负面新闻 → 触发风险预警 → 建议减仓
- 持续正面舆情 → 提高看多策略权重
- 行业政策变化 → 调整行业配置建议

### 4. 关键文件
- `backend/services/news_center/news_emotion_analyzer.py` — 情绪分析器
- `backend/services/news_center/` — 新闻中心所有文件
- `backend/services/strategy/` — 策略服务
- `backend/api/strategy_center_api.py` — 策略API
- `backend/agents/` — 21个智能体定义
- `backend/server.py` — 分析端点（analyze_stock 约第2420行）
- 数据库表：news_daily_sentiment, news_articles（历史数据正在导入）

## 约束
- 不要修改数据库表结构（历史数据正在导入中）
- 可以新增数据库表（如策略评分表、情绪趋势表）
- LLM 调用走 kirocpa 代理，key=icysaintdx，模型 kimi-k2.5
- 保持 API 接口兼容
- 先审计出报告，再动手改代码

## 交付物
1. 情绪分析系统审计报告（当前实现 vs 目标）
2. 策略系统审计报告（哪些是死策略、哪些可以AI化）
3. 情绪-策略联动设计方案
4. 代码实现 + 测试验证
