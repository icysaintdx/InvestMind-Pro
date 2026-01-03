# InvestMindPro API 接口测试报告

**测试日期**: 2025-12-31
**测试环境**: Windows / Python 3.x / AKShare 最新版

---

## 一、新闻数据接口

| 接口名称 | AKShare函数 | 状态 | 返回列名 | 备注 |
|---------|------------|------|---------|------|
| 东方财富全球资讯 | `stock_info_global_em` | ✅ OK | `['标题', '摘要', '发布时间', '链接']` | 约200条 |
| 财联社电报 | `stock_info_global_cls` | ✅ OK | `['标题', '内容', '发布日期', '发布时间']` | 约20条 |
| 富途牛牛 | `stock_info_global_futu` | ✅ OK | `['标题', '内容', '发布时间', '链接']` | 约50条 |
| 同花顺 | `stock_info_global_ths` | ✅ OK | `['标题', '内容', '发布时间', '链接']` | 约20条 |
| 新浪财经 | `stock_info_global_sina` | ✅ OK | `['时间', '内容']` | 约20条，无标题字段 |
| 微博热议 | `stock_js_weibo_report` | ✅ OK | `['name', 'rate']` | 约50条 |
| 财经早餐 | `stock_info_cjzc_em` | ✅ OK | `['标题', '摘要', '发布时间', '链接']` | 约400条 |
| 新闻联播 | `news_cctv` | ✅ OK | `['date', 'title', 'content']` | 约19条 |
| 百度财经 | `news_economic_baidu` | ✅ OK | `['国家', '时间', '地区', '事件', '今值', '预期', '前值', '重要性']` | 约99条，经济日历数据 |
| 个股新闻 | `stock_news_em` | ❌ FAIL | - | JSON解析错误 |
| 东财公告 | `stock_notice_report` | ✅ OK | `['代码', '名称', '公告标题', '公告类型', '公告日期', '地址']` | 约3000条 |

---

## 二、行情数据接口

| 接口名称 | AKShare函数 | 状态 | 返回列名 | 备注 |
|---------|------------|------|---------|------|
| A股实时行情 | `stock_zh_a_spot_em` | ✅ OK | `['序号', '代码', '名称', '最新价', '涨跌幅', ...]` | 约5792条 |
| 股票历史行情 | `stock_zh_a_hist` | ✅ OK | `['日期', '股票代码', '开盘', '收盘', '最高', '最低', '成交量', ...]` | 支持前复权/后复权 |
| 指数行情 | `stock_zh_index_spot_em` | ✅ OK | `['序号', '代码', '名称', '最新价', ...]` | 约268条 |

---

## 三、资金数据接口

| 接口名称 | AKShare函数 | 状态 | 返回列名 | 备注 |
|---------|------------|------|---------|------|
| 个股资金流向 | `stock_individual_fund_flow` | ✅ OK | `['日期', '收盘价', '涨跌幅', '主力净流入', ...]` | 约120条 |
| 板块资金流向 | `stock_sector_fund_flow_rank` | ✅ OK | `['序号', '名称', '今日涨跌幅', '主力净流入', ...]` | 约86条 |
| 融资融券 | `stock_margin_detail_szse` | ✅ OK | `['证券代码', '证券简称', '融资买入额', ...]` | 约2039条 |
| 大宗交易 | `stock_dzjy_mrmx` | ✅ OK | `['序号', '交易日期', '证券代码', '证券简称', ...]` | 约720条 |

---

## 四、公司数据接口

| 接口名称 | AKShare函数 | 状态 | 返回列名 | 备注 |
|---------|------------|------|---------|------|
| 公司基本信息 | `stock_individual_info_em` | ✅ OK | `['item', 'value']` | 约9条 |
| 财务指标 | `stock_financial_analysis_indicator` | ✅ OK | `['日期', '摊薄每股收益', '加权每股收益', ...]` | 约7条 |

---

## 五、板块数据接口

| 接口名称 | AKShare函数 | 状态 | 返回列名 | 备注 |
|---------|------------|------|---------|------|
| 行业板块 | `stock_board_industry_name_em` | ✅ OK | `['排名', '板块名称', '板块代码', ...]` | 约86条 |
| 概念板块 | `stock_board_concept_name_em` | ✅ OK | `['排名', '板块名称', '板块代码', ...]` | 约441条 |

---

## 六、市场数据接口

| 接口名称 | AKShare函数 | 状态 | 返回列名 | 备注 |
|---------|------------|------|---------|------|
| 龙虎榜 | `stock_lhb_detail_em` | ✅ OK | `['序号', '代码', '名称', '上榜原因', ...]` | 约100条 |
| 涨停池 | `stock_zt_pool_em` | ✅ OK | `['序号', '代码', '名称', '涨停时间', ...]` | 约54条 |
| 市场情绪 | `stock_market_activity_legu` | ✅ OK | `['item', 'value']` | 约12条 |

---

## 七、内部API接口

| 接口名称 | 端点 | 状态 | 备注 |
|---------|------|------|------|
| 新闻中心-市场新闻 | `/api/news-center/market` | ✅ OK | 聚合多源新闻 |
| 新闻中心-新闻列表 | `/api/news-center/list` | ✅ OK | 分页获取 |
| 新闻中心-搜索 | `/api/news-center/search` | ✅ OK | 关键词搜索 |
| 新闻中心-健康检查 | `/api/news-center/health` | ✅ OK | 服务状态 |
| 系统配置 | `/api/config` | ✅ OK | API密钥配置 |
| 数据源状态 | `/api/dataflow/sources/status` | ✅ OK | 数据源健康 |

---

## 八、AI服务接口

| 接口名称 | 端点 | 状态 | 备注 |
|---------|------|------|------|
| Gemini API | `https://generativelanguage.googleapis.com/v1beta/models` | 需配置 | 需要API Key |
| DeepSeek API | `https://api.deepseek.com/models` | 需配置 | 需要API Key |
| SiliconFlow API | `https://api.siliconflow.cn/v1/models` | 需配置 | 需要API Key |

---

## 九、已知问题

1. **个股新闻接口** (`stock_news_em`): JSON解析错误，可能是AKShare版本问题或数据源变更
2. **新浪财经**: 返回列名与其他新闻源不同，需要特殊处理（已修复）
3. **百度财经**: 返回的是经济日历数据，非传统新闻格式（已修复）

---

## 十、接口监控

已创建接口监控页面，可通过以下方式访问：

- **前端**: 工具 → 接口监控
- **后端API**:
  - `GET /api/monitor/status` - 获取所有API状态
  - `GET /api/monitor/akshare` - 获取AKShare接口状态
  - `GET /api/monitor/internal` - 获取内部API状态
  - `GET /api/monitor/ai` - 获取AI服务状态
  - `GET /api/monitor/ping/{api_name}` - Ping单个API
  - `GET /api/monitor/summary` - 获取快速摘要

---

## 十一、代码修复记录

### 1. CNINFO API配置检测问题
- **问题**: `.env`使用`CNINFO_ACCESS_SECRET`，但`server.py`读取`CNINFO_SECRET_KEY`
- **修复**: 统一使用官方命名 `CNINFO_ACCESS_KEY`, `CNINFO_ACCESS_SECRET`, `CNINFO_ACCESS_TOKEN`

### 2. 新浪财经返回0条数据
- **问题**: 代码查找`标题`字段，但实际返回`['时间', '内容']`
- **修复**: 使用`内容`字段前50字符作为标题

### 3. 百度财经返回0条数据
- **问题**: 代码查找`标题`字段，但实际返回经济日历格式
- **修复**: 使用`事件`作为标题，组合`今值/预期/前值/重要性`作为内容

### 4. 新闻数量限制
- **问题**: 多处API限制100条
- **修复**: 所有新闻相关API限制提升至5000-10000条

---

**报告生成时间**: 2025-12-31
