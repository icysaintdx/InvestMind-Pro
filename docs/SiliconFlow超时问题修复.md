# SiliconFlow超时问题修复方案

**问题**: 第二阶段完成后，多个智能体调用SiliconFlow API时频繁超时

## 🔍 问题分析

1. **并发请求过多**: 第二阶段有5个智能体同时调用API
2. **API限流**: SiliconFlow可能有并发限制
3. **超时设置**: 当前180秒超时，但多个请求可能导致排队

## ✅ 解决方案

### 方案1: 增加超时时间（推荐）

修改 `backend/server.py` 第433行：

```python
# 修改前
timeout=httpx.Timeout(180.0, connect=60.0)

# 修改后
timeout=httpx.Timeout(300.0, connect=60.0)  # 5分钟超时
```

### 方案2: 减少并发数量

修改 `alpha-council-vue/src/views/AnalysisView.vue`：

```javascript
// 修改 runAgentsParallel 函数
const runAgentsParallel = async (agentIds, data) => {
  const targetAgents = AGENTS.filter(a => agentIds.includes(a.id))
  
  // 分批执行，每批2个
  const batchSize = 2
  for (let i = 0; i < targetAgents.length; i += batchSize) {
    const batch = targetAgents.slice(i, i + batchSize)
    await Promise.all(batch.map(agent => runAgentAnalysis(agent, data)))
  }
}
```

### 方案3: 切换到其他模型

为容易超时的智能体使用更快的模型：

1. 打开API配置
2. 将第二阶段智能体的模型改为：
   - DeepSeek (更快)
   - Qwen (更稳定)
   - Gemini (速度适中)

## 🚀 立即修复

### 快速方案（推荐）

```bash
# 1. 增加超时时间
# 编辑 backend/server.py 第433行
# 将 180.0 改为 300.0

# 2. 重启后端
python backend\server.py
```

### 临时方案

在前端API配置中，将所有使用SiliconFlow的智能体改为DeepSeek或Qwen。

## 📊 各模型性能对比

| 模型 | 平均响应时间 | 稳定性 | 质量 |
|------|------------|--------|------|
| **DeepSeek** | 5-10秒 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Qwen** | 8-15秒 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Gemini** | 10-20秒 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **SiliconFlow** | 15-30秒 | ⭐⭐⭐ | ⭐⭐⭐⭐ |

## 💡 建议配置

### 高速配置（推荐）
- 第1阶段（新闻/社交/市场）: DeepSeek
- 第2阶段（行业/宏观/技术/资金/基本面）: Qwen
- 第3阶段（风控）: DeepSeek
- 第4阶段（决策）: Gemini

### 平衡配置
- 所有阶段: Qwen

### 高质量配置
- 所有阶段: Gemini（但较慢）

## 🔧 调试方法

查看后端日志，如果看到：
```
[SiliconFlow] 超时，正在重试... (尝试 2/2)
[SiliconFlow] 所有重试都失败，返回降级响应
```

说明确实是超时问题，建议：
1. 增加超时时间到300秒
2. 或切换到DeepSeek/Qwen模型
