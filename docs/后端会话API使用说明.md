# 后端会话 API 使用说明

## 📋 概述

后端会话管理 API 已实现，支持：
- ✅ 页面刷新后恢复分析状态
- ✅ 移动端后台运行时实时同步
- ✅ 跨设备访问分析结果
- ✅ 分析进度实时查询

## 🔌 API 端点

### 1. 创建会话
```http
POST /api/analysis/session/create
Content-Type: application/json

{
  "stock_code": "600000",
  "stock_name": "浦发银行"
}
```

**响应**：
```json
{
  "session_id": "session_1733625600_a1b2c3d4",
  "stock_code": "600000",
  "status": "created",
  "message": "会话创建成功，请开始分析"
}
```

---

### 2. 开始分析
```http
POST /api/analysis/session/{session_id}/start
```

**响应**：
```json
{
  "message": "分析已开始",
  "session_id": "session_1733625600_a1b2c3d4"
}
```

---

### 3. 查询会话状态
```http
GET /api/analysis/session/{session_id}/status
```

**响应**：
```json
{
  "session_id": "session_1733625600_a1b2c3d4",
  "stock_code": "600000",
  "stock_name": "浦发银行",
  "status": "running",
  "progress": 45,
  "current_stage": 2,
  "completed_agents": [
    "news_analyst",
    "social_analyst",
    "china_market",
    "industry",
    "macro"
  ],
  "total_agents": 21,
  "start_time": 1733625600.0,
  "elapsed_time": 125.5,
  "error_message": null
}
```

---

### 4. 获取智能体结果
```http
GET /api/analysis/session/{session_id}/agent/{agent_id}
```

**响应**：
```json
{
  "agent_id": "news_analyst",
  "status": "completed",
  "output": "## 新闻舆情分析\n\n...",
  "tokens": 1500,
  "thoughts": [
    {"step": 1, "content": "搜索相关新闻"},
    {"step": 2, "content": "分析情绪倾向"}
  ],
  "data_sources": [
    {"source": "东方财富", "count": 5},
    {"source": "新浪财经", "count": 3}
  ],
  "error": null
}
```

---

### 5. 更新会话进度（后端内部调用）
```http
POST /api/analysis/session/{session_id}/update
Content-Type: application/json

{
  "agent_id": "news_analyst",
  "status": "completed",
  "output": "分析结果...",
  "tokens": 1500,
  "progress": 10,
  "current_stage": 1
}
```

---

### 6. 完成会话
```http
POST /api/analysis/session/{session_id}/complete
Content-Type: application/json

{
  "success": true,
  "error": null
}
```

---

### 7. 查看所有活跃会话（调试）
```http
GET /api/analysis/sessions/active
```

**响应**：
```json
{
  "total": 2,
  "sessions": [
    {
      "session_id": "session_1733625600_a1b2c3d4",
      "stock_code": "600000",
      "status": "running",
      "progress": 45,
      "elapsed": 125
    }
  ]
}
```

---

## 🔄 前端集成流程

### 1. 开始分析
```javascript
// 创建会话
const response = await fetch('http://localhost:8000/api/analysis/session/create', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({
    stock_code: '600000',
    stock_name: '浦发银行'
  })
})

const data = await response.json()
const sessionId = data.session_id

// 保存到 localStorage
localStorage.setItem('current_session_id', sessionId)

// 开始分析
await fetch(`http://localhost:8000/api/analysis/session/${sessionId}/start`, {
  method: 'POST'
})

// 启动轮询
startPolling(sessionId)
```

### 2. 轮询状态
```javascript
const pollBackendStatus = async () => {
  const sessionId = localStorage.getItem('current_session_id')
  
  const response = await fetch(
    `http://localhost:8000/api/analysis/session/${sessionId}/status`
  )
  const status = await response.json()
  
  console.log(`进度: ${status.progress}%`)
  
  // 检查新完成的智能体
  for (const agentId of status.completed_agents) {
    if (!agentOutputs.value[agentId]) {
      // 获取智能体结果
      const agentResponse = await fetch(
        `http://localhost:8000/api/analysis/session/${sessionId}/agent/${agentId}`
      )
      const agentResult = await agentResponse.json()
      
      // 更新UI
      agentOutputs.value[agentId] = agentResult.output
      agentStatus.value[agentId] = 'completed'
      agentTokens.value[agentId] = agentResult.tokens
    }
  }
  
  // 检查是否完成
  if (status.status === 'completed') {
    stopPolling()
    showReport.value = true
  }
}
```

### 3. 页面刷新恢复
```javascript
onMounted(() => {
  const sessionId = localStorage.getItem('current_session_id')
  
  if (sessionId) {
    // 查询会话状态
    fetch(`http://localhost:8000/api/analysis/session/${sessionId}/status`)
      .then(r => r.json())
      .then(status => {
        if (status.status === 'running') {
          // 恢复状态
          restoreFromSession(status)
          // 启动轮询
          startPolling(sessionId)
        }
      })
  }
})
```

---

## 💾 数据存储

### 当前实现：内存存储
```python
# 优点：简单快速
# 缺点：服务器重启后丢失

analysis_sessions: Dict[str, Dict] = {}
```

### 生产环境：Redis
```python
import redis

redis_client = redis.Redis(host='localhost', port=6379, db=0)

# 保存会话
redis_client.setex(
    f"session:{session_id}",
    3600,  # 1小时过期
    json.dumps(session_data)
)

# 读取会话
data = redis_client.get(f"session:{session_id}")
session = json.loads(data) if data else None
```

---

## ⚠️ 注意事项

1. **会话过期**
   - 默认 1 小时后自动清理
   - 可通过 `SESSION_TIMEOUT` 配置

2. **并发限制**
   - 内存存储无限制
   - Redis 需要配置连接池

3. **数据大小**
   - 每个会话约 100KB-1MB
   - 1000 个会话约 100MB-1GB

4. **安全性**
   - 当前无认证
   - 生产环境需要添加用户认证

---

## 🚀 下一步

1. ✅ 后端 API 已实现
2. ⏳ 前端集成（下一步）
3. ⏳ 测试验证
4. ⏳ 生产环境优化（Redis）

---

## 📝 测试

### 测试创建会话
```bash
curl -X POST http://localhost:8000/api/analysis/session/create \
  -H "Content-Type: application/json" \
  -d '{"stock_code": "600000", "stock_name": "浦发银行"}'
```

### 测试查询状态
```bash
curl http://localhost:8000/api/analysis/session/session_xxx_xxx/status
```

### 测试查看所有会话
```bash
curl http://localhost:8000/api/analysis/sessions/active
```
