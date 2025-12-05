# 前端新闻API集成问题修复

> 发现时间: 2025-12-04 05:55  
> 问题: 前端未调用统一新闻API

---

## 🔍 问题分析

### 现象
1. ✅ 左侧显示AKShare和新浪财经"活跃"
2. ❌ 实际使用聚合数据
3. ❌ 新闻面板空空如也
4. ❌ 新闻舆情分析师提示"暂无重大事件"

### 根本原因
**前端没有调用统一新闻API！**

当前前端调用的是旧的端点：
```javascript
// 旧端点（AnalysisView.vue line 643）
fetch('http://localhost:8000/api/news/realtime', {
  method: 'POST',
  ...
})
```

应该调用新的统一新闻API：
```javascript
// 新端点
fetch('http://localhost:8000/api/unified-news/stock', {
  method: 'POST',
  ...
})
```

---

## 🔧 修复方案

### 方案1: 更新前端调用（推荐）

**文件**: `alpha-council-vue/src/views/AnalysisView.vue`

**修改位置**: 第643行附近

**修改前**:
```javascript
const response = await fetch('http://localhost:8000/api/news/realtime', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    ticker: stockCode,
    curr_date: new Date().toISOString().split('T')[0],
    hours_back: 24
  })
})
```

**修改后**:
```javascript
const response = await fetch('http://localhost:8000/api/unified-news/stock', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    ticker: stockCode
  })
})
```

**响应数据结构变化**:
```javascript
// 旧响应
{
  news: [...],
  sentiment: {...}
}

// 新响应
{
  success: true,
  ticker: "600519",
  timestamp: "2025-12-04T05:55:00",
  data: {
    sources: {
      realtime_news: {...},
      akshare_stock_news: {...},
      cls_telegraph: {...},
      weibo_hot: {...}
    },
    summary: {
      sentiment: {...},
      data_sources: {...}
    }
  }
}
```

**前端解析更新**:
```javascript
if (response.ok) {
  const result = await response.json()
  
  if (result.success) {
    // 获取所有新闻
    const allNews = []
    
    // 从各数据源提取新闻
    for (const [sourceName, sourceData] of Object.entries(result.data.sources)) {
      if (sourceData.status === 'success' && sourceData.data) {
        if (Array.isArray(sourceData.data)) {
          allNews.push(...sourceData.data)
        }
      }
    }
    
    // 更新新闻面板
    newsDataPanel.value.updateNews(allNews)
    
    // 更新情绪分析
    const sentiment = result.data.summary.sentiment
    if (sentiment) {
      newsDataPanel.value.updateSentiment(sentiment)
    }
    
    // 更新数据源统计
    const dataSources = result.data.summary.data_sources
    newsDataPanel.value.addLog(`成功率: ${dataSources.success_rate}`, 'success')
  }
}
```

---

### 方案2: 创建兼容层（临时方案）

如果不想立即修改前端，可以在后端创建兼容层：

**文件**: `backend/api/news_api.py`

**添加兼容端点**:
```python
@router.post("/realtime")
async def get_realtime_news_compat(request: dict):
    """兼容旧的实时新闻端点"""
    ticker = request.get('ticker')
    
    # 调用统一新闻API
    from backend.dataflows.news.unified_news_api import get_unified_news_api
    api = get_unified_news_api()
    result = api.get_stock_news_comprehensive(ticker)
    
    # 转换为旧格式
    all_news = []
    for source_data in result['sources'].values():
        if source_data['status'] == 'success' and source_data.get('data'):
            if isinstance(source_data['data'], list):
                all_news.extend(source_data['data'])
    
    return {
        'news': all_news,
        'sentiment': result['summary']['sentiment']
    }
```

---

## 📊 数据源优先级说明

### 当前优先级
```
AKShare > 新浪财经 > 聚合数据 > Tushare > BaoStock
```

### 为什么使用聚合数据？

1. **AKShare失败** - 可能原因：
   - 网络问题
   - API限流
   - 数据格式变化

2. **新浪财经失败** - 可能原因：
   - API已废弃
   - 反爬虫机制
   - 需要认证

3. **聚合数据成功** - 因为：
   - 有API Key配置
   - 接口稳定
   - 数据可靠

### 如何测试数据源

运行测试脚本：
```bash
python test_data_source_priority.py
```

这会测试：
1. AKShare是否可用
2. 新浪财经是否可用
3. 聚合数据是否可用
4. 统一新闻API是否正常

---

## 🧪 测试步骤

### 1. 测试数据源优先级
```bash
python test_data_source_priority.py
```

### 2. 测试统一新闻API
```bash
python test_api_endpoints.py
```

### 3. 更新前端代码
按照方案1修改 `AnalysisView.vue`

### 4. 重启前端
```bash
cd alpha-council-vue
npm run serve
```

### 5. 测试前端
1. 打开浏览器
2. 输入股票代码
3. 点击分析
4. 查看新闻面板是否有数据

---

## 📋 检查清单

- [ ] 运行 `test_data_source_priority.py`
- [ ] 确认哪些数据源可用
- [ ] 更新前端API调用
- [ ] 更新前端数据解析
- [ ] 测试新闻面板显示
- [ ] 测试情绪分析显示
- [ ] 测试数据源统计显示

---

## 🎯 预期结果

### 修复后
1. ✅ 新闻面板显示多个数据源的新闻
2. ✅ 情绪分析显示正确的情绪标签和评分
3. ✅ 数据源统计显示成功率
4. ✅ 日志显示所有尝试的数据源

### 数据源显示
```
数据源统计:
  总数: 4
  成功: 4
  成功率: 100%

各数据源:
  ✅ realtime_news: N/A条
  ✅ akshare_stock_news: 10条
  ✅ cls_telegraph: 10条
  ✅ weibo_hot: 50条
```

---

## 💡 建议

### 短期
1. 使用方案2创建兼容层，快速修复
2. 测试数据源可用性
3. 记录日志分析问题

### 长期
1. 使用方案1更新前端
2. 统一使用新的API端点
3. 完善错误处理
4. 添加数据源切换功能

---

**立即执行**: 运行 `python test_data_source_priority.py` 诊断问题！
