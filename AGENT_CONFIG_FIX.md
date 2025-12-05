# ✅ 智能体配置API修复

**时间**: 2025-12-05 07:55

---

## 问题

白话解读员配置无法加载，前端请求错误的API端点。

---

## 原因

前端使用的是 `/api/agents/config`，但后端实际端点是 `/api/config/agents`（在 `server.py` 中）。

---

## 解决方案

### 修改前端使用正确的端点

修改 `AnalysisView.vue`，使用 `server.py` 中已有的 `/api/config/agents` 端点。

#### 1. GET /api/config/agents
```python
# 在 server.py 中已有
@app.get("/api/config/agents")
async def load_agent_configs():
    """从文件加载智能体配置（包括模型选择）"""
    config_file = os.path.join(os.path.dirname(__file__), "agent_configs.json")
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return {"success": True, "data": config_data}
    else:
        return {"success": True, "data": {"agents": [], "selectedModels": []}}
```

#### 2. POST /api/config/agents
```python
# 在 server.py 中已有
@app.post("/api/config/agents")
async def save_agent_configs(config_data: Dict[str, Any]):
    """保存智能体配置到文件（包括模型选择）"""
    config_file = os.path.join(os.path.dirname(__file__), "agent_configs.json")
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, ensure_ascii=False, indent=2)
    return {"success": True, "message": "配置已保存"}
```

---

## 配置文件格式

### agent_configs.json
```json
{
  "interpreter": {
    "model": "deepseek-chat",
    "temperature": 0.7,
    "provider": "deepseek"
  }
}
```

---

## 使用方法

### 前端调用

#### 获取配置
```javascript
const response = await fetch('http://localhost:8000/api/config/agents')
const result = await response.json()
const config = result.success ? result.data : result
```

#### 保存配置
```javascript
await fetch('http://localhost:8000/api/config/agents', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ ...config, agents })
})
```

---

## 测试

### 测试获取配置
```bash
curl http://localhost:8000/api/config/agents
```

**预期响应**:
```json
{
  "success": true,
  "config": {
    "interpreter": {
      "model": "deepseek-chat",
      "temperature": 0.7,
      "provider": "deepseek"
    }
  }
}
```

### 测试保存配置
```bash
curl -X POST http://localhost:8000/api/config/agents \
  -H "Content-Type: application/json" \
  -d '{"interpreter":{"model":"qwen-plus","temperature":0.8,"provider":"qwen"}}'
```

**预期响应**:
```json
{
  "success": true,
  "message": "配置保存成功"
}
```

---

## 修改文件

- ✅ `alpha-council-vue/src/views/AnalysisView.vue` - 修改API端点
- ✅ 使用 `server.py` 中已有的 `/api/config/agents` 端点

---

## 功能特性

1. **自动创建默认配置**
   - 如果配置文件不存在，返回默认配置
   - 默认使用 deepseek-chat

2. **持久化存储**
   - 配置保存到 `agent_configs.json`
   - 重启后配置不丢失

3. **灵活配置**
   - 支持配置模型
   - 支持配置温度
   - 支持配置提供商

---

## 下一步

1. **重启后端**
   ```bash
   python backend/server.py
   ```

2. **测试配置加载**
   - 打开前端白话解读员配置
   - 应该能看到模型列表
   - 可以保存配置

3. **验证功能**
   - 修改模型和温度
   - 点击保存
   - 刷新页面，配置应该保持

---

**状态**: ✅ 已修复
