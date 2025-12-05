# 快速诊断指南

> 时间: 2025-12-04 07:16

---

## 🔍 当前问题

### 问题1: 只显示3条模拟数据，真实数据没显示

**现象**:
```
📊 参考数据 3个来源 | 3条数据
中国证券报(1条) 上证报(1条) 证券时报(1条)
```

**预期**:
```
📊 参考数据 5个来源 | 23条数据
中国证券报 (贵州茅台所属行业政策分析)
上证报 (A股市场整体走势分析)
证券时报 (贵州茅台市场环境评估)
财联社快讯 (10条真实数据)
东方财富 (10条真实数据)
```

**后端返回**:
```javascript
{
  success: true,
  ticker: "000001",
  timestamp: "2025-12-04T07:12:21.000199",
  data: {
    sources: {
      // 这里有数据
    }
  }
}
```

---

## 🧪 诊断步骤

### 步骤1: 重启前端并查看控制台

```bash
# 1. 停止前端
taskkill /F /IM node.exe /T

# 2. 重启前端
cd alpha-council-vue
npm run serve
```

### 步骤2: 打开浏览器控制台

```
F12 → Console标签
```

### 步骤3: 输入股票代码并分析

```
输入: 000001
点击: 开始分析
```

### 步骤4: 查看控制台输出

**关键日志**:
```javascript
[fetchNewsData] 后端返回数据: {...}
[news_analyst] newsData结构: {...}
[news_analyst] newsData.sources: {...}
[news_analyst] sources数量: X
[news_analyst] 处理数据源: realtime_news {...}
[news_analyst] 添加数据源: {...}
[news_analyst] 设置数据源: [...]
```

---

## 📊 预期日志输出

### 正常情况
```javascript
[fetchNewsData] 后端返回数据:
{
  success: true,
  data: {
    sources: {
      realtime_news: { status: 'success', count: 10, source: '实时新闻聚合器（东方财富）' },
      akshare_stock_news: { status: 'success', count: 20, source: 'AKShare（东方财富）' },
      cls_telegraph: { status: 'success', count: 10, source: '财联社' },
      weibo_hot: { status: 'success', count: 50, source: '微博热议' }
    }
  }
}

[news_analyst] newsData结构: { sources: {...}, summary: {...} }
[news_analyst] newsData.sources: { realtime_news: {...}, ... }
[news_analyst] sources数量: 4
[news_analyst] 处理数据源: realtime_news { status: 'success', count: 10, ... }
[news_analyst] 添加数据源: { source: '实时新闻聚合器（东方财富）', count: 10, title: '10条真实数据' }
[news_analyst] 处理数据源: akshare_stock_news { status: 'success', count: 20, ... }
[news_analyst] 添加数据源: { source: 'AKShare（东方财富）', count: 20, title: '20条真实数据' }
...
[news_analyst] 设置数据源: [
  { source: '东方财富', count: 1, title: '平安银行：最新市场动态分析' },
  { source: '新浪财经', count: 1, title: '平安银行所属行业板块走势分析' },
  { source: '雪球社区', count: 1, title: '平安银行投资者情绪报告' },
  { source: '实时新闻聚合器（东方财富）', count: 10, title: '10条真实数据' },
  { source: 'AKShare（东方财富）', count: 20, title: '20条真实数据' },
  { source: '财联社', count: 10, title: '10条真实数据' },
  { source: '微博热议', count: 50, title: '50条真实数据' }
]
```

### 异常情况1: sources不存在
```javascript
[news_analyst] newsData结构: { ... }
[news_analyst] newsData.sources: undefined
[news_analyst] newsData.sources不存在
[news_analyst] 设置数据源: [
  { source: '东方财富', count: 1, ... },
  { source: '新浪财经', count: 1, ... },
  { source: '雪球社区', count: 1, ... }
]
```

### 异常情况2: 所有数据源status不是success
```javascript
[news_analyst] sources数量: 4
[news_analyst] 处理数据源: realtime_news { status: 'error', ... }
[news_analyst] 跳过数据源: realtime_news, status=error, count=0
[news_analyst] 处理数据源: akshare_stock_news { status: 'error', ... }
[news_analyst] 跳过数据源: akshare_stock_news, status=error, count=0
...
[news_analyst] 设置数据源: [
  { source: '东方财富', count: 1, ... },
  { source: '新浪财经', count: 1, ... },
  { source: '雪球社区', count: 1, ... }
]
```

---

## 🔧 可能的问题和解决方案

### 问题1: newsData.sources不存在

**原因**: 后端返回的数据结构不对

**解决方案**:
```javascript
// 检查后端返回的完整数据结构
console.log('[fetchNewsData] 完整响应:', newsResult)
console.log('[fetchNewsData] data:', newsResult.data)
console.log('[fetchNewsData] data.sources:', newsResult.data?.sources)
```

### 问题2: 所有数据源status都是error

**原因**: 后端数据源全部失败

**解决方案**:
- 检查后端日志
- 测试后端API: `http://localhost:8000/api/news/unified/000001`
- 检查网络连接

### 问题3: count为0

**原因**: 数据源返回了但没有数据

**解决方案**:
- 检查后端数据源配置
- 测试AKShare是否正常
- 检查股票代码是否正确

---

## 🚀 立即执行

### 1. 重启前端
```bash
RESTART_FRONTEND.bat
```

### 2. 打开浏览器控制台
```
F12 → Console
```

### 3. 测试并复制日志
```
输入: 000001
点击: 开始分析
复制控制台所有日志
```

### 4. 分析日志
查找以下关键信息:
- `[fetchNewsData] 后端返回数据`
- `[news_analyst] newsData结构`
- `[news_analyst] sources数量`
- `[news_analyst] 处理数据源`
- `[news_analyst] 设置数据源`

---

## 📝 问题报告模板

如果问题依然存在，请提供以下信息：

```
### 控制台日志
[粘贴完整的控制台日志]

### 后端返回数据
[粘贴 fetchNewsData 的返回数据]

### newsData结构
[粘贴 newsData 的完整结构]

### sources数量
[粘贴 sources 的数量]

### 最终设置的数据源
[粘贴最终的 sources 数组]
```

---

**请立即执行诊断步骤并提供控制台日志！**
