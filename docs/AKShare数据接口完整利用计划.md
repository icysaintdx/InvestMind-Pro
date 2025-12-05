# AKShare数据接口完整利用计划

> **创建时间**: 2025-12-05  
> **目标**: 充分利用AKShare提供的所有数据接口  
> **参考**: https://akshare.akfamily.xyz/data/stock/stock.html

---

## 📊 AKShare数据分类

### 1. 股票基础数据 📈

#### 1.1 实时行情
```python
import akshare as ak

# A股实时行情
df = ak.stock_zh_a_spot_em()

# 个股实时行情
df = ak.stock_zh_a_hist(symbol="000001", period="daily", start_date="20210301", adjust="")
```

**用途**:
- 实时价格监控
- 技术分析
- 趋势判断

---

#### 1.2 历史行情
```python
# 日线数据
df = ak.stock_zh_a_hist(symbol="000001", period="daily")

# 分钟数据
df = ak.stock_zh_a_hist_min_em(symbol="000001", period="5")
```

**用途**:
- 回测
- 技术指标计算
- 历史分析

---

#### 1.3 财务数据
```python
# 财务指标
df = ak.stock_financial_analysis_indicator(symbol="000001", start_year="2020")

# 业绩预告
df = ak.stock_yjyg_em(date="20240331")

# 业绩快报
df = ak.stock_yjkb_em(date="20240331")
```

**用途**:
- 基本面分析
- 估值计算
- 财务健康度评估

---

### 2. 新闻舆情数据 📰

#### 2.1 个股新闻
```python
# 东方财富个股新闻
df = ak.stock_news_em(symbol="000001")

# 财经早餐
df = ak.stock_info_cjzc_em()

# 全球财经新闻
df = ak.stock_info_global_em()
```

**用途**:
- 舆情监控
- 情绪分析
- 事件驱动

---

#### 2.2 社交媒体
```python
# 微博热议股票
df = ak.stock_js_weibo_report(symbol="000001", date="20240101")

# 股吧情绪
df = ak.stock_guba_sina()
```

**用途**:
- 散户情绪
- 热点追踪
- 舆情预警

---

### 3. 风险数据 ⚠️

#### 3.1 期权风险指标（已发现）
```python
# 期权风险分析
df = ak.option_risk_analysis_em()

# 上交所期权风险指标
df = ak.option_risk_indicator_sse()
```

**用途**:
- 市场风险评估
- 波动率分析
- 对冲策略

---

#### 3.2 其他风险相关（需要查找）
```python
# 可能存在的接口（需要验证）
# - 停牌信息
# - 退市风险
# - ST股票
# - 异常交易
```

**待查找的风险数据**:
- [ ] 停牌公告
- [ ] 退市风险警示
- [ ] ST/\*ST股票名单
- [ ] 异常交易监控
- [ ] 大宗交易
- [ ] 股权质押
- [ ] 限售解禁

---

### 4. 监管数据 🏛️

#### 4.1 交易所公告
```python
# 可能存在的接口
# - 上交所公告
# - 深交所公告
# - 监管函
# - 处罚决定
```

**待查找**:
- [ ] 交易所公告接口
- [ ] 监管函接口
- [ ] 处罚决定接口

---

#### 4.2 股东数据
```python
# 股东人数
df = ak.stock_zh_a_gdhs(symbol="000001")

# 股东户数
# 待查找具体接口
```

**用途**:
- 筹码分析
- 主力追踪
- 散户情绪

---

### 5. 资金流向数据 💰

#### 5.1 主力资金
```python
# 个股资金流
df = ak.stock_individual_fund_flow(symbol="000001", market="沪深A股")

# 板块资金流
df = ak.stock_sector_fund_flow_rank(indicator="今日")

# 大单追踪
df = ak.stock_lhb_detail_em(symbol="000001", start_date="20240101", end_date="20240331")
```

**用途**:
- 主力动向
- 资金流向
- 龙虎榜分析

---

#### 5.2 北向资金
```python
# 沪深港通资金流向
df = ak.stock_hsgt_fund_flow_summary_em()

# 北向持股
df = ak.stock_hsgt_hold_stock_em(symbol="北向", indicator="持股数量")
```

**用途**:
- 外资动向
- 市场情绪
- 资金流向

---

### 6. 市场情绪数据 😊

#### 6.1 情绪指标
```python
# 市场情绪
# 待查找具体接口

# 恐慌指数
# 待查找

# 涨跌停统计
df = ak.stock_zt_pool_em(date="20240101")
df = ak.stock_dt_pool_em(date="20240101")
```

**用途**:
- 市场情绪
- 超买超卖
- 反转信号

---

#### 6.2 技术指标
```python
# 技术面数据
# 需要基于历史行情自己计算
# 或查找是否有现成接口
```

---

### 7. 宏观经济数据 🌍

#### 7.1 经济指标
```python
# GDP
df = ak.macro_china_gdp()

# CPI
df = ak.macro_china_cpi()

# PMI
df = ak.macro_china_pmi()

# 货币供应
df = ak.macro_china_money_supply()
```

**用途**:
- 宏观分析
- 政策判断
- 周期研判

---

#### 7.2 利率汇率
```python
# 利率
df = ak.macro_china_shibor()

# 汇率
df = ak.currency_boc_sina()
```

**用途**:
- 资金成本
- 汇率风险
- 政策预期

---

### 8. 行业板块数据 🏭

#### 8.1 行业分类
```python
# 申万行业
df = ak.stock_board_industry_name_em()

# 概念板块
df = ak.stock_board_concept_name_em()

# 地域板块
df = ak.stock_board_area_name_em()
```

**用途**:
- 行业轮动
- 板块效应
- 热点追踪

---

#### 8.2 行业数据
```python
# 行业资金流
df = ak.stock_board_industry_fund_flow_em()

# 行业涨跌幅
df = ak.stock_board_industry_spot_em()
```

**用途**:
- 行业比较
- 强弱分析
- 配置建议

---

## 🎯 数据利用优先级

### 第一优先级：核心数据（立即使用）

1. **实时行情** ⭐⭐⭐⭐⭐
   - `stock_zh_a_spot_em()` - A股实时行情
   - `stock_zh_a_hist()` - 历史行情
   - **用途**: 价格监控、技术分析

2. **个股新闻** ⭐⭐⭐⭐⭐
   - `stock_news_em()` - 个股新闻
   - `stock_info_cjzc_em()` - 财经早餐
   - **用途**: 舆情分析、事件驱动

3. **资金流向** ⭐⭐⭐⭐⭐
   - `stock_individual_fund_flow()` - 个股资金流
   - `stock_lhb_detail_em()` - 龙虎榜
   - **用途**: 主力追踪、资金分析

4. **财务数据** ⭐⭐⭐⭐⭐
   - `stock_financial_analysis_indicator()` - 财务指标
   - `stock_yjyg_em()` - 业绩预告
   - **用途**: 基本面分析、估值

---

### 第二优先级：补充数据（2周内）

5. **社交媒体** ⭐⭐⭐⭐
   - `stock_js_weibo_report()` - 微博热议
   - `stock_guba_sina()` - 股吧情绪
   - **用途**: 散户情绪、热点

6. **北向资金** ⭐⭐⭐⭐
   - `stock_hsgt_fund_flow_summary_em()` - 沪深港通
   - `stock_hsgt_hold_stock_em()` - 北向持股
   - **用途**: 外资动向

7. **行业板块** ⭐⭐⭐⭐
   - `stock_board_industry_spot_em()` - 行业行情
   - `stock_board_industry_fund_flow_em()` - 行业资金流
   - **用途**: 行业轮动、板块效应

---

### 第三优先级：高级数据（1个月内）

8. **宏观经济** ⭐⭐⭐
   - `macro_china_gdp()` - GDP
   - `macro_china_cpi()` - CPI
   - **用途**: 宏观分析

9. **期权风险** ⭐⭐⭐
   - `option_risk_analysis_em()` - 期权风险
   - `option_risk_indicator_sse()` - 风险指标
   - **用途**: 市场风险、波动率

10. **市场情绪** ⭐⭐⭐
    - `stock_zt_pool_em()` - 涨停板
    - `stock_dt_pool_em()` - 跌停板
    - **用途**: 情绪指标

---

## 📋 实施计划

### 第1周：核心数据集成

**目标**: 集成最重要的4类数据

#### Day 1-2: 实时行情
- [ ] 创建 `backend/dataflows/akshare/stock_data.py`
- [ ] 实现实时行情获取
- [ ] 实现历史行情获取
- [ ] 创建API端点 `/api/akshare/stock/realtime`
- [ ] 测试验证

#### Day 3-4: 新闻舆情
- [ ] 创建 `backend/dataflows/akshare/news_data.py`
- [ ] 集成个股新闻
- [ ] 集成财经早餐
- [ ] 创建API端点 `/api/akshare/news`
- [ ] 测试验证

#### Day 5: 资金流向
- [ ] 创建 `backend/dataflows/akshare/fund_flow.py`
- [ ] 实现资金流向查询
- [ ] 实现龙虎榜查询
- [ ] 创建API端点 `/api/akshare/fund`
- [ ] 测试验证

---

### 第2周：补充数据

#### Day 1-2: 财务数据
- [ ] 创建 `backend/dataflows/akshare/financial_data.py`
- [ ] 实现财务指标查询
- [ ] 实现业绩预告查询
- [ ] 创建API端点 `/api/akshare/financial`

#### Day 3-4: 社交媒体
- [ ] 创建 `backend/dataflows/akshare/social_data.py`
- [ ] 集成微博热议
- [ ] 集成股吧情绪
- [ ] 创建API端点 `/api/akshare/social`

#### Day 5: 北向资金
- [ ] 创建 `backend/dataflows/akshare/hsgt_data.py`
- [ ] 实现北向资金查询
- [ ] 创建API端点 `/api/akshare/hsgt`

---

### 第3-4周：高级数据

- [ ] 行业板块数据
- [ ] 宏观经济数据
- [ ] 期权风险数据
- [ ] 市场情绪数据

---

## 🛠️ 技术实现

### 统一封装模式

```python
# backend/dataflows/akshare/base.py
class AKShareBase:
    """AKShare数据基类"""
    
    def __init__(self):
        self.logger = get_logger(self.__class__.__name__)
    
    def safe_call(self, func, *args, **kwargs):
        """安全调用AKShare接口"""
        try:
            return func(*args, **kwargs)
        except Exception as e:
            self.logger.error(f"AKShare调用失败: {e}")
            return None
```

### 数据缓存策略

```python
# 使用Redis缓存
# - 实时数据: 缓存5分钟
# - 日线数据: 缓存1小时
# - 财务数据: 缓存1天
# - 宏观数据: 缓存1周
```

### API设计

```python
# 统一的API响应格式
{
    "code": 200,
    "message": "success",
    "data": {
        "source": "akshare",
        "timestamp": "2025-12-05 05:00:00",
        "result": [...]
    }
}
```

---

## 📊 数据整合方案

### 多维度分析

```python
# 综合分析示例
def comprehensive_analysis(stock_code):
    """综合分析"""
    return {
        "基本面": {
            "财务指标": get_financial_data(stock_code),
            "业绩预告": get_performance_forecast(stock_code)
        },
        "技术面": {
            "实时行情": get_realtime_quote(stock_code),
            "技术指标": calculate_indicators(stock_code)
        },
        "资金面": {
            "资金流向": get_fund_flow(stock_code),
            "龙虎榜": get_lhb_data(stock_code),
            "北向资金": get_hsgt_data(stock_code)
        },
        "消息面": {
            "个股新闻": get_stock_news(stock_code),
            "社交媒体": get_social_sentiment(stock_code)
        },
        "风险面": {
            "市场风险": get_market_risk(),
            "个股风险": get_stock_risk(stock_code)
        }
    }
```

---

## 🎯 成功标准

### 第1周目标
- ✅ 4个核心数据源集成
- ✅ 基础API端点完成
- ✅ 测试覆盖率 > 80%
- ✅ 响应时间 < 2秒

### 第2周目标
- ✅ 8个数据源集成
- ✅ 数据缓存实现
- ✅ 综合分析接口
- ✅ 文档完善

### 最终目标
- ✅ 10+个数据源集成
- ✅ 多维度分析系统
- ✅ 智能推荐引擎
- ✅ 可视化仪表盘

---

## 📚 参考资源

### 官方文档
- AKShare文档: https://akshare.akfamily.xyz/
- 数据字典: https://akshare.akfamily.xyz/data/stock/stock.html

### 已有文档
- `docs/爬虫.md` - 巨潮网Selenium爬虫示例
- `docs/风险数据源汇总.md` - 风险数据源总结
- `docs/风险数据源开发计划.md` - 风险数据开发计划

---

## 🚀 立即开始

### 第一步：验证AKShare接口
```bash
python -c "import akshare as ak; print(ak.stock_zh_a_spot_em().head())"
```

### 第二步：创建基础模块
```bash
mkdir -p backend/dataflows/akshare
touch backend/dataflows/akshare/__init__.py
touch backend/dataflows/akshare/base.py
touch backend/dataflows/akshare/stock_data.py
```

### 第三步：开始编码
从实时行情开始，快速看到成果！

---

现在我们有了完整的AKShare数据利用计划！🎉
