# 数据流监控优化 Skill v2.0

## 概述

本 skill 用于优化 InvestMindPro 的数据流监控模块，建立统一新闻监控中心，实现高时效性的新闻、公告监控和智能通知。

## 核心架构

### 统一新闻监控中心 (NewsMonitorCenter)

所有新闻相关功能统一由 `NewsMonitorCenter` 管理：

```
NewsMonitorCenter
├── 后台数据采集层 (ProcessPoolExecutor)
├── 统一数据源层 (AKShare + Tushare + 巨潮资讯)
├── 统一缓存层 (NewsCache)
├── 智能分析层 (情绪 + 关联 + 影响评估)
└── 统一API层 (/api/news-center/*)
```

### 设计原则

1. **统一入口**: 所有新闻请求通过 `/api/news-center/*`
2. **后台静默**: 使用独立进程池，不阻塞主线程
3. **增量检测**: 只处理新新闻，避免重复
4. **实时推送**: WebSocket 主动推送，无需轮询

## 现有基础设施

| 组件 | 状态 | 说明 |
|------|------|------|
| 后台新闻服务 | ✅ 已有 | `background_news_service.py` |
| 情绪分析引擎 | ✅ 已有 | `sentiment_engine.py` |
| 巨潮资讯爬虫 | ⚠️ 待激活 | `cninfo_crawler.py` |
| 统一新闻API | ✅ 已有 | `unified_news_api_endpoint.py` |

## 数据源配置

### 高频数据源 (30秒)
- 财联社快讯: `ak.stock_info_global_cls()`
- 东方财富全球: `ak.stock_info_global_em()`
- 东方财富个股: `ak.stock_news_em(symbol)`
- 巨潮公告: `CninfoCrawler.get_company_announcements()`

### 中频数据源 (2分钟)
- 新浪财经: `ak.stock_info_global_sina()`
- 同花顺: `ak.stock_info_global_ths()`
- 富途牛牛: `ak.stock_info_global_futu()`

### 低频数据源 (5分钟+)
- 微博热议: `ak.stock_js_weibo_report()`
- 财经早餐: `ak.stock_info_cjzc_em()`
- 新闻联播: `ak.news_cctv(date)`

## 刷新频率设置

用户可在数据流页面设置：

| 类型 | 选项 | 默认值 |
|------|------|--------|
| 新闻监控 | 30秒/1分钟/2分钟/5分钟 | 1分钟 |
| 公告监控 | 1分钟/2分钟/5分钟/10分钟 | 2分钟 |
| 其他数据 | 5分钟/10分钟/30分钟/1小时 | 30分钟 |

## 智能分析

### 情绪分析 (复用现有)
- 正面词汇: 增长、利好、突破、中标...
- 负面词汇: 下跌、亏损、违规、处罚...
- 输出: positive/negative/neutral + 分数

### 股票关联分析 (新增)
- 直接匹配: 股票代码/名称出现在文本中
- 行业匹配: 相关行业关键词
- 概念匹配: 相关概念板块

### 影响评估 (新增)
- 影响分数: 1-10
- 紧急程度: high/medium/low
- 是否通知: 基于分数和关联度

## 通知分级

| 级别 | 条件 | 通知方式 |
|------|------|----------|
| 紧急 | urgency=high 或 impact>=9 | 弹窗+声音+推送 |
| 重要 | impact>=7 且有关联股票 | 弹窗+推送 |
| 一般 | impact>=5 且有关联股票 | 列表高亮 |
| 普通 | 其他 | 静默更新 |

## API 接口

```
GET  /api/news-center/latest          # 获取最新新闻
GET  /api/news-center/stock/{code}    # 获取股票相关新闻
GET  /api/news-center/announcements   # 获取公告
WS   /api/news-center/realtime        # WebSocket实时推送
```

## 前端调用

所有页面统一使用 `NewsService`:

```javascript
// 数据流页面
const news = await NewsService.getLatest({ limit: 50 })

// 详情模态框
const stockNews = await NewsService.getStockNews('000001.SZ')

// 实时监控
NewsService.connectRealtime((msg) => {
  if (msg.type === 'news_alert') {
    showNotification(msg.data)
  }
})
```

## 实施步骤

### 第一阶段：核心服务
1. 创建 `NewsMonitorCenter` 类
2. 整合所有数据源
3. 激活巨潮资讯爬虫
4. 实现统一缓存

### 第二阶段：智能分析
1. 复用情绪分析引擎
2. 实现股票关联分析
3. 实现影响评估引擎

### 第三阶段：实时推送
1. WebSocket 服务
2. 通知分级系统
3. 前端通知组件

### 第四阶段：前端迁移
1. 数据流页面迁移
2. 详情模态框迁移
3. 智能分析迁移

## 性能目标

| 指标 | 目标值 |
|------|--------|
| 新闻延迟 | <30秒 |
| 公告延迟 | <60秒 |
| API响应 | <200ms |
| 内存占用 | <500MB |

## 相关文件

- 优化方案: `docs/dataflow-monitoring-optimization.md`
- 后台服务: `backend/services/background_news_service.py`
- 情绪引擎: `backend/dataflows/news/sentiment_engine.py`
- 巨潮爬虫: `backend/dataflows/announcement/cninfo_crawler.py`
- 统一API: `backend/api/unified_news_api_endpoint.py`

## 使用建议

### 盯盘时
- 新闻: 30秒
- 公告: 1分钟
- 开启声音提醒

### 日常监控
- 新闻: 1分钟
- 公告: 2分钟
- 仅高影响通知

### 后台运行
- 新闻: 5分钟
- 公告: 10分钟
- 仅紧急通知
