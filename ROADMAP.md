# InvestMindPro 项目总计划

> 最后更新: 2026-02-22 02:28 by 臭宝 🦨
> 一个活文档，做了就打勾，新的就往里加。

---

## ✅ 已完成

### 基础架构修复
- [x] LLM路由修复: SiliconFlow→kirocpa统一路由（14个文件）
- [x] API Key根因修复: sk-kirocpa → icysaintdx（11个文件）
- [x] 模型切换: minimax-m2.1 → kimi-k2.5（agent_configs.json 17处）
- [x] agent_configs.json确认为真正配置源（非agent_configs/llm_configs.json）
- [x] reasoning_content回退处理（kimi-k2.5推理模型content可能为空）
- [x] body级别错误检测
- [x] 分析验证通过: 技术分析智能体 → 贵州茅台成功返回

### 数据与缓存
- [x] 市场API缓存优化: 冷启动13.2s → 缓存17ms
- [x] 后台数据预取守护线程
- [x] 板块轮动缓存TTL: 交易时间60s / 非交易时间3600s
- [x] 非交易时间返回最后交易日缓存数据（不返回空）
- [x] 数据库路径bug修复: 改用基于__file__的绝对路径

### 前端
- [x] 前端重新构建（hash fa6c1d22）

### 端点修复
- [x] 龙虎榜summary字段重映射 + stock detail端点修复
- [x] 成交额榜修复
- [x] 盘口数据修复
- [x] 成交明细修复
- [x] 分析结果空值回退 + prompt泄露修复 + 重试逻辑

### 历史数据导入
- [x] 新闻每日情绪数据导入: news_daily_sentiment ~5.6M行（1994-2024）
- [x] 新闻文章数据导入: news_articles ~15.1M行（1994-2024）
- [x] 数据库从25MB → 4.9GB
- [x] 使用streaming openpyxl（pandas会OOM，openpyxl read_only + batch insert ~300MB）

### Round 1 并行Agent（Git Worktree）
- [x] 创建3个git worktree: worktree-api / worktree-arch / worktree-sentiment
- [x] Agent 1 — API审计: 93+端点测试，89+正常，3问题，1修复。产出API_AUDIT_REPORT.md
- [x] Agent 2 — 架构优化: EventBus + AnalysisCache + SharedDataContext + AutoAnalysisTrigger。修改server.py(+82行) + news_monitor_center.py(+84行)
- [x] Agent 3 — 情绪+策略: 重写impact_assessor.py(LLM驱动)，修复sentiment_resonance.py(3维加权)，重写manager.py(动态权重)。新建sentiment_trend_service.py + ai_weight_adjuster.py。600+行新代码
- [x] 3个分支合并到main: fix/api-flow, fix/dual-drive, fix/sentiment-ai
- [x] 导入路径修复: `from backend.xxx` → `from xxx`（10个文件）

### Round 2 并行Agent
- [x] Agent A — 集成+Bug: /api/monitor/status从>30s→0.41s（内存缓存+异步后台刷新）。POST /api/analyze 200 OK, 10.8s真实数据
- [x] Agent B — 回测+策略: 创建ai_sentiment_strategy.py（3维共振）。回测结果: 混合策略Sharpe 0.02 vs 纯技术-0.09。产出BACKTEST_REPORT.md
- [x] Agent C — 动态API配置: 创建api_provider_api.py + api_provider_service.py + dynamic_llm_client.py。产出DYNAMIC_API_DESIGN.md

### 工具与环境
- [x] OpenCode安装 v1.2.10
- [x] kirocpa provider加入OpenCode配置（tribios备用）
- [x] CODING-AGENT.md更新: pyright清理规则 + session复用规则
- [x] 进程清理规范建立（每个agent完成后必须kill pyright-langserver）

### Round 3 Agent（系统优化）
- [x] Agent ember-wharf: 全系统端点测试+优化，修复market_adapter.py overview fallback
- [x] Agent amber-willow: 模拟交易+实时管道验证

### 闲鱼数据调研
- [x] 搜索6个关键词，翻阅多页商品
- [x] 整理最终采购清单6项（¥34.17）
- [x] 设置明天10:00提醒大佬购买

---

## 🔄 进行中

### 系统稳定化（目标: 周一9:00开盘）
- [ ] 周一开盘实测: 实时数据是否正常流入
- [ ] 模拟交易实测: 能否跟实盘数据下模拟单
- [ ] 情绪→策略管道实测: 新闻变化是否实时影响策略权重
- [ ] 所有端点响应时间确认（目标<3s）
- [ ] 前端加载确认

### 代码审查
- [ ] Round 1 agent代码质量审查（event_bus/analysis_cache/shared_data_context/auto_analysis_trigger/sentiment_trend_service/ai_weight_adjuster）
- [ ] Round 2 agent代码质量审查（api_provider_api/api_provider_service/dynamic_llm_client/ai_sentiment_strategy/backtest_sentiment_strategy）
- [ ] 未提交的变更commit到git

---

## 📋 待做（按优先级排序）

### P0 — 本周必做
- [ ] 闲鱼数据采购+导入（等大佬买完下载）
  - [ ] 股吧评论情绪统计 ¥1（id=834199565464）
  - [ ] 股吧评论情绪统计CNRDS ¥2（id=1023967404940）
  - [ ] 上市公司媒体关注数据 ¥1.50（id=751973918836）
  - [ ] 报刊财经新闻量化统计 ¥8.88（id=721375495233）
  - [ ] 上市公司MD&A文本 ¥6（id=1004264867889）
  - [ ] 上市公司股吧评论文本 ¥14.79（id=1015246211323）
- [ ] akshare接口扩展（让Sisyphus搜文档自己对接）
  - [ ] 历史资金流向: stock_individual_fund_flow
  - [ ] 历史龙虎榜: stock_lhb_detail_daily_sina
  - [ ] 大宗交易: stock_dzjy_sctj
  - [ ] 融资融券: stock_margin_detail_szse / stock_margin_detail_sse
  - [ ] 股东变动
  - [ ] 分红送转
  - [ ] 其他Sisyphus搜到的有价值接口
- [ ] Dynamic API Config集成: 注册路由到server.py，端到端测试
- [ ] 策略迭代: 多策略变体，重点总收益+风险管理（止损/仓位），降低回撤

### P1 — 下周
- [ ] 打板模块
  - [ ] 涨停板实时监控（akshare: stock_zt_pool_em）
  - [ ] 跌停板/炸板监控
  - [ ] 连板统计与晋级率追踪
  - [ ] 集合竞价分析（9:15-9:25数据）
  - [ ] 题材热度追踪（结合新闻情绪）
- [ ] 补充历史数据（akshare可拉的）
  - [ ] 历史资金流向数据入库
  - [ ] 历史龙虎榜数据入库
  - [ ] 历史融资融券数据入库

### P2 — 下下周
- [ ] 交易决策中枢
  - [ ] 统一信号格式定义（方向/强度/置信度/时效）
  - [ ] 信号汇聚层: 收集所有模块输出
  - [ ] 机会评分引擎: 多维度加权打分+排序
  - [ ] 仓位管理器: 总仓位/单票上限/行业分散
  - [ ] 风控引擎: 止损止盈/最大回撤/资金曲线
  - [ ] 订单生成器: 输出具体可执行交易指令
- [ ] 智能体prompt增强: 注入精简版市场背景（混合模式C）

### P3 — 第3-4周
- [ ] 模拟实战验证
  - [ ] 完整流程跑通: 信号→决策→下单→监控→平仓
  - [ ] 每日复盘机制: 哪些信号准/不准
  - [ ] 策略参数迭代优化
  - [ ] 收益/回撤/夏普比率持续跟踪
  - [ ] 对比: 决策中枢 vs 纯智能体分析 vs 纯策略

### P4 — 待定
- [ ] 实盘对接
  - [ ] 券商API选择（需大佬定）
  - [ ] 小资金实盘测试
  - [ ] 风控加固（硬止损/异常熔断/网络断线保护）
- [ ] 4.9GB数据库优化（查询被OOM kill）
  - [ ] 考虑分表/归档旧数据
  - [ ] 或迁移到PostgreSQL
  - [ ] 或增加服务器内存

---

## 🔑 待大佬拍板

1. **架构选择**: ✅ 已定 — C混合模式（2026-02-22 大佬拍板）
2. **资金规模**: 模拟盘初始资金设多少？
3. **交易风格**: 短线打板 / 中线趋势 / 混合？
4. **券商选择**: 后期实盘用哪家？
5. **风险偏好**: 最大可接受回撤？

---

## 📊 关键指标

| 指标 | 当前值 | 目标值 |
|------|--------|--------|
| 智能体数量 | 21 | 21+ |
| 策略数量 | 16 | 20+ |
| 新闻情绪数据 | 5.6M行(1994-2024) | +股吧+媒体 |
| 分析响应时间 | ~10s | <5s |
| 监控响应时间 | 0.41s | <1s |
| 回测Sharpe(混合) | 0.02 | >0.5 |
| 回测最大回撤 | -60.82% | <-30% |
| 数据库大小 | 4.9GB | 需优化 |

---

*新东西随时加，做完就打勾。这是咱项目的唯一真相来源。🦨*
