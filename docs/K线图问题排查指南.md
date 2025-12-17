# K线图问题排查指南

**问题**: K线图显示"加载K线数据中..."但一直不显示

---

## 🔍 排查步骤

### 1. 检查浏览器控制台

**操作**:
1. 按F12打开开发者工具
2. 切换到Console标签
3. 点击"加载"按钮
4. 查看控制台输出

**应该看到**:
```
开始加载K线数据: 600519 5分钟
请求URL: http://localhost:8000/api/kline/data
请求参数: {symbol: "600519", period: "5", adjust: "qfq", limit: 200}
API响应: {...}
获取到数据条数: X
```

**如果看到错误**:
- 记录错误信息
- 检查是什么类型的错误

---

### 2. 直接测试API

**在浏览器中访问**:
```
http://localhost:8000/api/kline/data?symbol=600519&period=daily&limit=10
```

**预期响应**:
```json
{
  "success": true,
  "symbol": "600519",
  "period": "daily",
  "count": 10,
  "data": [...]
}
```

**如果返回空数据**:
```json
{
  "success": true,
  "count": 0,
  "data": []
}
```
说明后端获取数据失败

---

### 3. 检查后端日志

**查看终端输出**:
- 查找"K线"相关的日志
- 查找错误信息
- 查找AKShare相关错误

**常见错误**:
1. `ModuleNotFoundError: No module named 'akshare'`
   - 解决: `pip install akshare`

2. `未获取到数据`
   - AKShare接口可能暂时不可用
   - 尝试其他股票代码

3. `缺少必须的列`
   - AKShare返回的列名可能变化
   - 需要更新列名映射

---

### 4. 测试AKShare

**创建测试文件**: `test_akshare.py`

```python
import akshare as ak
from datetime import datetime, timedelta

# 测试日线
df = ak.stock_zh_a_hist(
    symbol="600519",
    period="daily",
    start_date=(datetime.now() - timedelta(days=30)).strftime('%Y%m%d'),
    end_date=datetime.now().strftime('%Y%m%d'),
    adjust="qfq"
)

print(f"日线数据: {len(df)} 条")
print(f"列名: {df.columns.tolist()}")
print(df.head())

# 测试分钟线
df2 = ak.stock_zh_a_hist_min_em(
    symbol="600519",
    period="5",
    adjust="qfq"
)

print(f"\n5分钟数据: {len(df2)} 条")
print(f"列名: {df2.columns.tolist()}")
print(df2.head())
```

**运行**:
```bash
python test_akshare.py
```

---

## 🔧 常见问题和解决方案

### 问题1: ECharts未安装

**症状**: 控制台显示 `Cannot find module 'echarts'`

**解决**:
```bash
cd alpha-council-vue
npm install echarts --save
npm run serve
```

---

### 问题2: 数据返回为空

**症状**: API返回 `{"success": true, "count": 0, "data": []}`

**原因**:
1. AKShare接口问题
2. 股票代码不正确
3. 网络问题

**解决**:
1. 尝试其他股票代码（如：000001）
2. 检查网络连接
3. 等待一段时间后重试
4. 查看AKShare官方文档确认接口是否变更

---

### 问题3: K线图不显示

**症状**: 数据获取成功但图表不显示

**检查**:
1. 浏览器控制台是否有ECharts错误
2. 数据格式是否正确
3. DOM元素是否存在

**解决**:
```javascript
// 在renderKlineChart函数开始添加
console.log('开始渲染K线图')
console.log('图表容器:', klineChart.value)
console.log('数据:', klineData.value)
```

---

### 问题4: 周期切换无效

**症状**: 切换周期后没有重新加载

**检查**:
```vue
<select v-model="klinePeriod" @change="loadKlineData">
```

确保有 `@change="loadKlineData"`

---

## 🚀 临时解决方案

### 使用模拟数据

如果AKShare暂时不可用，可以使用模拟数据：

```javascript
// 在loadKlineData中添加
if (response.data.count === 0) {
  // 使用模拟数据
  klineData.value = generateMockData()
  await nextTick()
  renderKlineChart()
}

function generateMockData() {
  const data = []
  const basePrice = 100
  for (let i = 0; i < 100; i++) {
    const date = new Date()
    date.setDate(date.getDate() - (100 - i))
    data.push({
      time: date.toISOString().split('T')[0],
      open: basePrice + Math.random() * 10,
      close: basePrice + Math.random() * 10,
      high: basePrice + Math.random() * 15,
      low: basePrice - Math.random() * 5,
      volume: Math.floor(Math.random() * 1000000)
    })
  }
  return data
}
```

---

## 📝 调试清单

- [ ] 浏览器控制台无错误
- [ ] 后端API可以访问
- [ ] AKShare可以正常获取数据
- [ ] ECharts已安装
- [ ] 数据格式正确
- [ ] DOM元素存在
- [ ] 事件绑定正确

---

## 💡 建议

1. **先测试后端API**: 确保后端能正常返回数据
2. **再测试前端**: 确保前端能正确调用和显示
3. **查看日志**: 浏览器控制台和后端日志都要看
4. **逐步调试**: 一步一步排查问题

---

## 📞 需要帮助

如果以上步骤都无法解决问题，请提供：

1. 浏览器控制台的完整错误信息
2. 后端终端的日志输出
3. 直接访问API的响应结果
4. AKShare测试脚本的输出

---

**祝你顺利解决问题！** 🎉
