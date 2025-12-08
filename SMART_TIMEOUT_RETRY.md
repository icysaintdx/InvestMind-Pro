# 🔧 智能超时和重试机制优化方案

**时间**: 2025-12-05 20:35

---

## 🎯 当前问题

### 问题1: 数据源显示失败
- **现象**: 后端成功获取数据，但前端显示"数据获取失败"
- **原因**: API返回的字段名和前端期望的不匹配
- **状态**: ✅ 已修复（添加console.log调试）

### 问题2: 超时机制不合理
- **现象**: 
  - 设置10分钟超时
  - 5分钟时卡住，要等到15分钟才触发超时
  - 后端重试机制不起作用
  - 等待20分钟后才报错

- **根本原因**:
  1. 超时时间太长（10分钟）
  2. 没有心跳检测机制
  3. 重试逻辑在超时后才触发
  4. 没有监控每个智能体的响应时间

---

## ✅ 解决方案

### 方案1: 分段超时机制

#### 概念
不是等10分钟，而是每30秒检查一次是否有响应

#### 实现
```javascript
const runAgentWithSmartTimeout = async (agent, data) => {
  const SEGMENT_TIMEOUT = 30000 // 30秒一段
  const MAX_SEGMENTS = 20 // 最多20段 = 10分钟
  const MAX_RETRIES = 3 // 最多重试3次
  
  for (let retry = 0; retry <= MAX_RETRIES; retry++) {
    let lastProgressTime = Date.now()
    let segmentCount = 0
    let responseReceived = false
    
    const controller = new AbortController()
    
    // 心跳检测
    const heartbeatInterval = setInterval(() => {
      const elapsed = Date.now() - lastProgressTime
      
      if (elapsed > SEGMENT_TIMEOUT) {
        segmentCount++
        console.warn(`[${agent.id}] 已等待 ${segmentCount * 30}秒，无响应`)
        
        if (segmentCount >= MAX_SEGMENTS) {
          console.error(`[${agent.id}] 超时，准备重试 (${retry + 1}/${MAX_RETRIES})`)
          controller.abort()
          clearInterval(heartbeatInterval)
        }
      }
    }, SEGMENT_TIMEOUT)
    
    try {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agent.id,
          stock_code: stockCode.value,
          stock_data: data,
          previous_outputs: agentOutputs.value
        }),
        signal: controller.signal
      })
      
      clearInterval(heartbeatInterval)
      responseReceived = true
      
      if (!response.ok) throw new Error('API Error')
      const result = await response.json()
      
      // 成功
      agentOutputs.value[agent.id] = result.result
      agentStatus.value[agent.id] = 'success'
      return
      
    } catch (error) {
      clearInterval(heartbeatInterval)
      
      if (error.name === 'AbortError' && retry < MAX_RETRIES) {
        console.log(`[${agent.id}] 重试 ${retry + 1}/${MAX_RETRIES}`)
        await new Promise(r => setTimeout(r, 2000))
        continue
      }
      
      throw error
    }
  }
}
```

---

### 方案2: 流式响应监控

#### 概念
使用Server-Sent Events (SSE)或WebSocket，实时监控后端进度

#### 后端修改
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
import asyncio

@app.post("/api/analyze/stream")
async def analyze_stream(request: AnalyzeRequest):
    async def generate():
        try:
            # 发送开始信号
            yield f"data: {json.dumps({'status': 'started'})}\n\n"
            
            # 调用LLM
            yield f"data: {json.dumps({'status': 'calling_llm'})}\n\n"
            
            result = await llm_client.chat(...)
            
            # 发送结果
            yield f"data: {json.dumps({'status': 'success', 'result': result})}\n\n"
            
        except Exception as e:
            yield f"data: {json.dumps({'status': 'error', 'error': str(e)})}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")
```

#### 前端修改
```javascript
const runAgentWithSSE = (agent, data) => {
  return new Promise((resolve, reject) => {
    const eventSource = new EventSource(
      `http://localhost:8000/api/analyze/stream?agent_id=${agent.id}`
    )
    
    let lastEventTime = Date.now()
    const HEARTBEAT_TIMEOUT = 30000 // 30秒无事件就超时
    
    const timeoutChecker = setInterval(() => {
      if (Date.now() - lastEventTime > HEARTBEAT_TIMEOUT) {
        console.error(`[${agent.id}] 30秒无响应，关闭连接`)
        eventSource.close()
        clearInterval(timeoutChecker)
        reject(new Error('Heartbeat timeout'))
      }
    }, 5000)
    
    eventSource.onmessage = (event) => {
      lastEventTime = Date.now()
      const data = JSON.parse(event.data)
      
      if (data.status === 'started') {
        console.log(`[${agent.id}] 开始分析`)
      } else if (data.status === 'calling_llm') {
        console.log(`[${agent.id}] 调用LLM中...`)
      } else if (data.status === 'success') {
        clearInterval(timeoutChecker)
        eventSource.close()
        resolve(data.result)
      } else if (data.status === 'error') {
        clearInterval(timeoutChecker)
        eventSource.close()
        reject(new Error(data.error))
      }
    }
    
    eventSource.onerror = (error) => {
      clearInterval(timeoutChecker)
      eventSource.close()
      reject(error)
    }
  })
}
```

---

### 方案3: 智能重试策略

#### 概念
根据错误类型决定是否重试，以及重试间隔

#### 实现
```javascript
const RETRY_STRATEGIES = {
  'ReadTimeout': { shouldRetry: true, delay: 2000, maxRetries: 3 },
  'ConnectionError': { shouldRetry: true, delay: 5000, maxRetries: 2 },
  'APIError': { shouldRetry: false, delay: 0, maxRetries: 0 },
  'RateLimitError': { shouldRetry: true, delay: 10000, maxRetries: 1 }
}

const runAgentWithSmartRetry = async (agent, data) => {
  let retryCount = 0
  
  while (true) {
    try {
      const result = await callAgentAPI(agent, data)
      return result
      
    } catch (error) {
      const errorType = detectErrorType(error)
      const strategy = RETRY_STRATEGIES[errorType] || { shouldRetry: false }
      
      if (!strategy.shouldRetry || retryCount >= strategy.maxRetries) {
        throw error
      }
      
      console.log(`[${agent.id}] ${errorType}，等待${strategy.delay}ms后重试 (${retryCount + 1}/${strategy.maxRetries})`)
      
      await new Promise(r => setTimeout(r, strategy.delay))
      retryCount++
    }
  }
}

const detectErrorType = (error) => {
  if (error.message.includes('ReadTimeout')) return 'ReadTimeout'
  if (error.message.includes('Connection')) return 'ConnectionError'
  if (error.message.includes('Rate limit')) return 'RateLimitError'
  return 'APIError'
}
```

---

### 方案4: 后端超时优化

#### 问题
后端的重试机制在前端超时后不起作用

#### 解决
```python
from fastapi import FastAPI, BackgroundTasks
import asyncio

# 全局任务跟踪
active_tasks = {}

@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    task_id = f"{request.agent_id}_{request.stock_code}_{time.time()}"
    
    # 创建超时任务
    async def run_with_timeout():
        try:
            # 30秒超时
            result = await asyncio.wait_for(
                llm_client.chat(...),
                timeout=30.0
            )
            return {"success": True, "result": result}
            
        except asyncio.TimeoutError:
            logger.warning(f"[{request.agent_id}] 30秒超时，准备重试")
            
            # 重试1次
            try:
                result = await asyncio.wait_for(
                    llm_client.chat(...),
                    timeout=30.0
                )
                return {"success": True, "result": result}
            except asyncio.TimeoutError:
                return {"success": False, "error": "Timeout after retry"}
    
    result = await run_with_timeout()
    return result
```

---

## 📊 推荐方案

### 短期（立即实施）
**方案1: 分段超时机制**
- ✅ 实现简单
- ✅ 不需要修改后端
- ✅ 立即见效

### 中期（本周）
**方案3: 智能重试策略**
- ✅ 根据错误类型决定重试
- ✅ 避免无意义的重试
- ✅ 提高成功率

### 长期（下周）
**方案2: 流式响应监控**
- ✅ 实时监控进度
- ✅ 更好的用户体验
- ✅ 更精确的超时控制

---

## 🔧 立即实施的修改

### 1. 修改前端超时时间
```javascript
// 从10分钟改为2分钟
const TIMEOUT = 120000 // 2分钟

// 添加心跳检测
const HEARTBEAT_INTERVAL = 30000 // 30秒
```

### 2. 添加进度监控
```javascript
let lastProgressTime = Date.now()

const progressMonitor = setInterval(() => {
  const elapsed = Date.now() - lastProgressTime
  if (elapsed > 30000) {
    console.warn(`[${agent.id}] 已等待${Math.floor(elapsed/1000)}秒`)
  }
}, 5000)
```

### 3. 优化重试逻辑
```javascript
// 指数退避
const retryDelay = Math.min(2000 * Math.pow(2, retryCount), 10000)
await new Promise(r => setTimeout(r, retryDelay))
```

---

## 🧪 测试方案

### 1. 模拟超时
```javascript
// 在后端添加延迟
await asyncio.sleep(35) // 35秒延迟
```

### 2. 模拟网络错误
```javascript
// 断开网络，测试重试
```

### 3. 压力测试
```javascript
// 同时分析10只股票
```

---

## 📝 实施步骤

### Step 1: 修改超时时间（5分钟）
```javascript
const timeoutId = setTimeout(() => controller.abort(), 120000) // 2分钟
```

### Step 2: 添加心跳检测（10分钟）
```javascript
const heartbeat = setInterval(() => {
  console.log(`[${agent.id}] 仍在等待响应...`)
}, 30000)
```

### Step 3: 优化重试策略（15分钟）
```javascript
const maxRetries = 3
const retryDelay = 2000 * Math.pow(2, retryCount)
```

### Step 4: 添加进度显示（20分钟）
```javascript
agentStatus.value[agent.id] = `analyzing_${Math.floor(elapsed/30)}段`
```

---

## ✅ 预期效果

### 之前
- ❌ 5分钟卡住，等到15分钟才超时
- ❌ 重试机制不起作用
- ❌ 用户不知道发生了什么
- ❌ 等待20分钟才报错

### 之后
- ✅ 30秒无响应就警告
- ✅ 2分钟超时立即重试
- ✅ 最多3次重试
- ✅ 用户看到实时进度
- ✅ 最多6分钟就知道结果

---

**优先级**: 🔥🔥🔥 高优先级  
**预计工作量**: 2-3小时  
**预期收益**: 大幅提升用户体验
