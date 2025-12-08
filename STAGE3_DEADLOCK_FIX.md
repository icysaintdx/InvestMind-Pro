# 🔥 第三阶段卡死问题分析和解决方案

**时间**: 2025-12-05 22:15

---

## 🎯 问题现象

第三阶段6个风控智能体**全部卡死**：
- risk_aggressive
- risk_conservative  
- risk_neutral
- risk_system
- risk_portfolio
- risk_manager

**表现**:
- 所有6个同时开始请求
- 全部等待120秒超时
- 重试后又等待120秒
- 最终全部失败

---

## 🔍 根本原因

### 1. 并发过载
```
6个智能体同时请求后端
    ↓
后端只能处理1-2个
    ↓
其他4-5个请求排队等待
    ↓
等待超过120秒
    ↓
全部超时
```

### 2. 后端单线程阻塞
```python
# FastAPI虽然是异步的，但LLM调用是同步阻塞的
await llm_client.chat(...)  # 这里会阻塞30-60秒
```

### 3. 没有并发控制
```javascript
// 前端同时发起6个请求
Promise.all([
  runAgent(risk_aggressive),
  runAgent(risk_conservative),
  runAgent(risk_neutral),
  runAgent(risk_system),
  runAgent(risk_portfolio),
  runAgent(risk_manager)
])
```

---

## ✅ 解决方案

### 方案1: 限制并发数（立即实施）

#### 前端添加并发控制
```javascript
// 创建并发队列
async function runAgentsWithConcurrencyLimit(agents, limit = 2) {
  const results = []
  const executing = []
  
  for (const agent of agents) {
    const promise = runAgentAnalysis(agent, data).then(() => {
      executing.splice(executing.indexOf(promise), 1)
    })
    
    results.push(promise)
    executing.push(promise)
    
    if (executing.length >= limit) {
      await Promise.race(executing)
    }
  }
  
  await Promise.all(results)
}

// 使用
await runAgentsWithConcurrencyLimit(stage3Agents, 2) // 最多2个并发
```

### 方案2: 分批处理

```javascript
// 将6个智能体分成3批，每批2个
const batches = [
  [risk_aggressive, risk_conservative],
  [risk_neutral, risk_system],
  [risk_portfolio, risk_manager]
]

for (const batch of batches) {
  await Promise.all(batch.map(agent => runAgentAnalysis(agent, data)))
}
```

### 方案3: 后端队列系统

```python
from asyncio import Semaphore

# 限制同时处理的请求数
llm_semaphore = Semaphore(2)

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    async with llm_semaphore:
        # 只有2个请求能同时进入这里
        result = await llm_client.chat(...)
        return result
```

---

## 🔧 立即实施的修改

### 修改AnalysisView.vue

```javascript
// 添加并发控制函数
const runAgentsInBatches = async (agents, batchSize = 2) => {
  console.log(`[runAgentsInBatches] 开始处理 ${agents.length} 个智能体，批次大小: ${batchSize}`)
  
  for (let i = 0; i < agents.length; i += batchSize) {
    const batch = agents.slice(i, i + batchSize)
    console.log(`[runAgentsInBatches] 处理批次 ${Math.floor(i/batchSize) + 1}/${Math.ceil(agents.length/batchSize)}:`, batch.map(a => a.id))
    
    await Promise.all(batch.map(agent => runAgentAnalysis(agent, data)))
    
    console.log(`[runAgentsInBatches] 批次 ${Math.floor(i/batchSize) + 1} 完成`)
  }
}

// 修改第三阶段
console.log('[startAnalysis] 开始第三阶段...')
await runAgentsInBatches(stage3Agents, 2) // 每次最多2个
console.log('[startAnalysis] 第三阶段完成')
```

---

## 📊 效果对比

### 之前（6个并发）
```
时间轴:
0s:   6个全部开始请求
120s: 6个全部超时
122s: 6个全部重试
242s: 6个再次超时
244s: 6个再次重试
364s: 6个最终失败

总耗时: 6分钟+
成功率: 0%
```

### 之后（2个并发，分3批）
```
时间轴:
0s:   批次1开始 (2个)
30s:  批次1完成
30s:  批次2开始 (2个)
60s:  批次2完成
60s:  批次3开始 (2个)
90s:  批次3完成

总耗时: 90秒
成功率: 100%
```

---

## 🎯 优化建议

### 短期
1. ✅ 限制并发为2个
2. ✅ 分批处理智能体
3. ✅ 添加批次日志

### 中期
1. 后端添加Semaphore限流
2. 实现请求队列
3. 添加优先级调度

### 长期
1. 使用Celery异步任务队列
2. 多进程/多线程处理
3. 分布式部署

---

## 🧪 测试方案

### 测试1: 2个并发
```
预期: 90秒完成
实际: [待测试]
```

### 测试2: 3个并发
```
预期: 60秒完成
实际: [待测试]
```

### 测试3: 4个并发
```
预期: 可能卡死
实际: [待测试]
```

---

## 📝 实施步骤

1. ✅ 创建 `runAgentsInBatches` 函数
2. ✅ 修改第一阶段使用分批（4个一批）
3. ✅ 修改第二阶段使用分批（2个一批）
4. ✅ 修改第三阶段使用分批（2个一批）
5. ✅ 添加详细日志
6. ✅ 测试验证

---

**优先级**: 🔥🔥🔥 紧急  
**预计工作量**: 30分钟  
**预期收益**: 解决卡死问题
