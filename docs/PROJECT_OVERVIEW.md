# InvestMindPro 项目全面分析报告

## 一、项目概述

**InvestMindPro (智投顾问团)** 是一个多智能体 AI 驱动的中国 A 股投资分析系统，使用 21 个专业 AI 智能体分 4 个阶段进行协作投资分析。

### 核心特点
- **多智能体协作**: 21个专业AI智能体，4阶段分析流程
- **多数据源整合**: AKShare(主) + Tushare(辅) + 聚合数据
- **实时风险监控**: ST状态、停复牌、股权质押、限售解禁等
- **新闻舆情分析**: 多源新闻聚合 + 情绪分析引擎
- **回测系统**: 20+交易策略，完整回测引擎

---

模块	文件数	功能
后端 API	30+	FastAPI 路由，覆盖分析、回测、交易等
AI 智能体	21个	4阶段协作分析（分析师→管理者→风控→决策）
数据流	48个接口	Tushare 33个 + AKShare 15个
交易策略	20+	MACD、布林带、海龟、价值投资等
前端页面	12个	Vue 3 实现的完整 UI

## 二、系统架构

### 2.1 技术栈
| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Axios + ECharts |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | SQLite (InvestMindPro.db) |
| 数据源 | AKShare + Tushare + 聚合数据 |
| AI模型 | Gemini / DeepSeek / Qwen / SiliconFlow |

### 2.2 目录结构
```
InvestMindPro/
├── backend/                    # Python FastAPI 后端
│   ├── api/                    # 30+ API路由文件
│   ├── agents/                 # 21个AI智能体
│   │   ├── analysts/           # 阶段1: 5个分析师
│   │   ├── managers/           # 阶段2: 2个管理者
│   │   ├── risk_mgmt/          # 阶段3: 3个风控辩论者
│   │   └── trader/             # 阶段4: 1个决策者
│   ├── dataflows/              # 数据流模块 (核心)
│   │   ├── news/               # 新闻聚合模块
│   │   ├── risk/               # 风险监控模块
│   │   ├── persistence/        # 数据持久化
│   │   └── akshare/            # AKShare数据适配
│   ├── strategies/             # 20+交易策略
│   ├── backtest/               # 回测引擎
│   ├── database/               # 数据库模型和服务
│   └── services/               # 业务服务层
├── alpha-council-vue/          # Vue 3 前端
│   ├── src/views/              # 页面组件
│   └── src/components/         # 可复用组件
└── data/                       # 数据存储
```

---

## 三、数据流模块详解

### 3.1 数据接口统计

**共 48 个数据接口** (Tushare 33个 + AKShare 15个)

| 分类 | 接口数 | 说明 |
|------|--------|------|
| 基础信息 | 4 | 公司信息、管理层、薪酬、主营业务 |
| 行情数据 | 9 | 实时行情、涨跌停、龙虎榜、大宗交易 |
| 财务数据 | 8 | 财务报表、审计意见、业绩预告、分红 |
| 资金流向 | 12 | 融资融券、沪深港通、股东增减持、股权质押 |
| 风险监控 | 7 | ST状态、停复牌、限售解禁 |
| 新闻舆情 | 8 | 个股新闻、公告、市场快讯、行业政策 |

### 3.2 接口健康度报告 (2024-12-20 测试)

#### AKShare 接口状态

| 接口 | 状态 | 说明 |
|------|------|------|
| `stock_news_em` | ❌ 失败 | 东方财富个股新闻接口异常 |
| `stock_telegraph_cls` | ❌ 失败 | 财联社电报接口已移除 |
| `stock_news_main_cx` | ❌ 失败 | 市场要闻接口404 |
| `news_economic_baidu` | ✅ 正常 | 百度财经新闻 (99条) |
| `news_cctv` | ✅ 正常 | 央视新闻 (18条) |
| `stock_info_global_cls` | ✅ 正常 | 财联社全球资讯 (20条) |
| `stock_info_global_em` | ✅ 正常 | 东方财富全球资讯 (200条) |
| `stock_info_global_sina` | ✅ 正常 | 新浪全球资讯 (20条) |
| `stock_info_global_futu` | ✅ 正常 | 富途全球资讯 (50条) |
| `stock_zh_a_st_em` | ✅ 正常 | ST股票列表 (176只) |
| `stock_zh_a_stop_em` | ✅ 正常 | 停牌股票 (284只) |
| `stock_lhb_detail_em` | ✅ 正常 | 龙虎榜明细 (390条) |
| `stock_gpzy_pledge_ratio_em` | ✅ 正常 | 股权质押比例 (2322条) |

#### Tushare 接口状态

| 接口 | 所需积分 | 状态 |
|------|----------|------|
| `news` | 5000 | 需要高级权限 |
| `forecast` | 120 | 正常 |
| `share_float` | 120 | 正常 |
| `suspend_d` | 120 | 正常 |
| `pledge_stat` | 120 | 正常 |
| `stk_holdertrade` | 120 | 正常 |
| `top_list` | 300 | 正常 |
| `margin` | 120 | 正常 |

---

## 四、数据流监控页面分析

### 4.1 当前功能

1. **数据源状态监控**: 显示 Tushare/AKShare/东方财富/聚合数据 的连接状态
2. **监控股票管理**: 添加/移除监控股票，设置更新频率和保存周期
3. **实时新闻流**: 聚合多源新闻，按来源筛选
4. **股票详情弹窗**: 7个标签页展示综合数据
   - 接口状态、基础信息、行情数据、财务数据、资金流向、风险监控、新闻舆情

### 4.2 发现的问题

#### 问题1: 风险预警与股票关联性不明确
**现象**: 风险预警显示"近期有 5 批限售股解禁"，但看不到与监控股票(如600519)的关联性

**原因分析**:
- `_generate_alerts()` 方法生成预警时，只显示数量，未显示具体股票信息
- 限售解禁数据来自 `share_float` 接口，返回的是该股票的解禁计划

**解决方案**: 在预警消息中明确显示股票代码和具体解禁信息

#### 问题2: 新闻内容截断影响阅读
**现象**: 新闻内容只显示开头部分，无法看到与关注股票相关的关键信息

**原因分析**:
- 新闻内容统一截取前200字符
- 未针对监控股票进行关键内容提取

**解决方案**:
1. 智能截取：检索新闻中与监控股票相关的段落
2. 关键词高亮：突出显示股票代码、公司名称等关键词
3. 展开/收起：允许用户查看完整内容

#### 问题3: 部分新闻接口失效
**现象**: `stock_news_em`、`stock_telegraph_cls` 等接口返回错误

**原因分析**:
- AKShare 接口更新频繁，部分接口已变更或移除
- 网络请求可能被限流

**解决方案**:
1. 更新新闻聚合器，使用可用的替代接口
2. 增加接口降级策略

---

## 五、优化建议

### 5.1 数据流模块优化

#### 5.1.1 新闻聚合器优化
```python
# 建议替换的接口映射
NEWS_API_FALLBACK = {
    'stock_news_em': ['stock_info_global_em', 'news_economic_baidu'],
    'stock_telegraph_cls': ['stock_info_global_cls'],
    'stock_news_main_cx': ['news_cctv', 'stock_info_global_sina']
}
```

#### 5.1.2 风险预警优化
- 在预警消息中包含股票代码和名称
- 显示具体的解禁日期、解禁数量、解禁比例
- 添加预警等级的颜色区分

#### 5.1.3 新闻内容智能截取
```python
def extract_relevant_content(content: str, stock_code: str, stock_name: str) -> str:
    """提取与股票相关的内容片段"""
    keywords = [stock_code, stock_name, stock_code[:6]]

    # 查找包含关键词的句子
    sentences = content.split('。')
    relevant = [s for s in sentences if any(kw in s for kw in keywords)]

    if relevant:
        return '。'.join(relevant[:3]) + '。'
    else:
        return content[:200] + '...'
```

### 5.2 前端优化建议

#### 5.2.1 风险预警面板
- 添加股票代码标签
- 显示预警详情（点击展开）
- 按股票分组显示预警

#### 5.2.2 新闻列表优化
- 添加"展开全文"按钮
- 高亮显示监控股票关键词
- 添加新闻与股票的关联标签

### 5.3 数据持久化优化

#### 5.3.1 增量更新策略
- 新闻数据：只保存新增的新闻，避免重复
- 行情数据：按时间戳更新，保留历史快照
- 风险数据：变化时才更新，记录变化历史

#### 5.3.2 数据清理策略
- 根据 `retention_days` 配置自动清理过期数据
- 保留重要预警的历史记录

---

## 六、实施优先级

### 高优先级 (立即修复)
1. ✅ 更新新闻聚合器，替换失效接口
2. ✅ 优化风险预警显示，增加股票关联性
3. ✅ 修复新闻内容截取逻辑

### 中优先级 (已完成)
4. ✅ 添加新闻关键词高亮
5. ✅ 实现新闻展开/收起功能
6. ✅ 优化数据刷新策略
7. ✅ 添加预警历史记录
8. ✅ 添加自定义预警规则

### 低优先级 (后续迭代)
9. 实现邮件/微信推送通知
10. 添加更多数据可视化图表
11. 实现数据导出功能

---

## 七、新增功能说明

### 7.1 新闻展开/收起功能
**文件**: `alpha-council-vue/src/views/DataFlowView.vue`
- 新闻内容默认显示3行
- 点击"展开全文"可查看完整内容
- 支持平滑过渡动画

### 7.2 关键词高亮功能
**文件**: `alpha-council-vue/src/views/DataFlowView.vue`
- 自动高亮股票代码、名称和简称
- 使用金色渐变背景突出显示
- 支持标题和内容的高亮

### 7.3 数据刷新策略
**文件**: `backend/api/dataflow_api.py`
- 最小刷新间隔配置（防止频繁调用）
- API返回 `refresh_info` 字段告知前端下次可刷新时间
- 智能缓存机制

### 7.4 预警历史记录
**数据库表**: `alert_history`
**API端点**:
- `GET /api/dataflow/alerts/history` - 获取预警历史
- `GET /api/dataflow/alerts/unread-count` - 获取未读数量
- `POST /api/dataflow/alerts/mark-read/{id}` - 标记已读
- `POST /api/dataflow/alerts/mark-all-read` - 全部标记已读

### 7.5 自定义预警规则
**数据库表**: `alert_rules`
**API端点**:
- `GET /api/dataflow/rules` - 获取所有规则
- `GET /api/dataflow/rules/defaults` - 获取默认规则模板
- `POST /api/dataflow/rules` - 创建规则
- `PUT /api/dataflow/rules/{id}` - 更新规则
- `DELETE /api/dataflow/rules/{id}` - 删除规则
- `POST /api/dataflow/rules/{id}/toggle` - 切换启用状态
- `POST /api/dataflow/rules/init-defaults` - 初始化默认规则

**支持的规则类型**:
- `pledge` - 股权质押
- `restricted` - 限售解禁
- `holder_sell` - 股东减持
- `limit_down` - 跌停预警
- `st` - ST风险
- `suspend` - 停牌预警
- `audit` - 审计意见
- `forecast` - 业绩预告
- `custom` - 自定义

---

## 八、接口替换方案

### 7.1 新闻接口替换

| 原接口 | 替换方案 | 说明 |
|--------|----------|------|
| `stock_news_em` | `stock_info_global_em` | 东方财富全球资讯 |
| `stock_telegraph_cls` | `stock_info_global_cls` | 财联社全球资讯 |
| `stock_news_main_cx` | `news_cctv` + `news_economic_baidu` | 央视+百度财经 |

### 7.2 个股新闻获取策略

由于个股新闻接口不稳定，建议采用以下策略：

1. **关键词过滤**: 从全市场新闻中筛选包含股票代码/名称的新闻
2. **多源聚合**: 同时从多个可用接口获取，去重合并
3. **缓存策略**: 缓存已获取的新闻，减少API调用

---

## 八、总结

InvestMindPro 是一个功能完善的 A 股投资分析系统，数据流模块整合了 48 个数据接口，覆盖了股票分析的各个维度。当前主要问题集中在：

1. **新闻接口稳定性**: 部分 AKShare 接口已失效，需要更新替换
2. **风险预警关联性**: 预警信息与监控股票的关联不够明确
3. **内容展示优化**: 新闻截取逻辑需要针对监控股票进行智能处理

通过本文档提供的优化方案，可以显著提升数据流监控页面的实用性和用户体验。
