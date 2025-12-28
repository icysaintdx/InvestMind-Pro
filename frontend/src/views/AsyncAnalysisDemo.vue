<template>
  <div class="async-analysis-demo">
    <h1>异步分析演示 (SSE 实时推送)</h1>

    <!-- 输入区 -->
    <div class="input-section">
      <div class="input-group">
        <label>股票代码:</label>
        <input
          v-model="stockCode"
          placeholder="输入股票代码，如 000001"
          :disabled="isAnalyzing"
        />
      </div>
      <div class="input-group">
        <label>股票名称:</label>
        <input
          v-model="stockName"
          placeholder="股票名称（可选）"
          :disabled="isAnalyzing"
        />
      </div>
      <div class="input-group">
        <label>分析深度:</label>
        <select v-model="depth" :disabled="isAnalyzing">
          <option :value="1">1 - 仅分析师层</option>
          <option :value="2">2 - 分析师 + 研究总监</option>
          <option :value="3">3 - 分析师 + 研究总监 + 风控</option>
          <option :value="4">4 - 完整分析（含决策）</option>
        </select>
      </div>
      <div class="button-group">
        <button
          @click="startAnalysis"
          :disabled="isAnalyzing || !stockCode"
          class="start-btn"
        >
          {{ isAnalyzing ? '分析中...' : '开始异步分析' }}
        </button>
        <button
          v-if="isAnalyzing"
          @click="cancelAnalysis"
          class="cancel-btn"
        >
          取消分析
        </button>
      </div>
    </div>

    <!-- 状态显示 -->
    <div v-if="taskId" class="status-section">
      <div class="status-header">
        <h2>任务状态</h2>
        <span class="task-id">Task ID: {{ taskId }}</span>
      </div>
      <div class="status-info">
        <div class="status-item">
          <span class="label">状态:</span>
          <span :class="['value', statusClass]">{{ taskStatus }}</span>
        </div>
        <div class="status-item">
          <span class="label">进度:</span>
          <div class="progress-bar">
            <div class="progress-fill" :style="{ width: progress + '%' }"></div>
          </div>
          <span class="progress-text">{{ progress }}%</span>
        </div>
        <div class="status-item">
          <span class="label">消息:</span>
          <span class="value">{{ statusMessage }}</span>
        </div>
      </div>
    </div>

    <!-- Agent 状态网格 -->
    <div v-if="Object.keys(agentStates).length > 0" class="agents-section">
      <h2>Agent 执行状态</h2>
      <div class="agents-grid">
        <div
          v-for="(state, agentId) in agentStates"
          :key="agentId"
          :class="['agent-card', state.status]"
        >
          <div class="agent-header">
            <span class="agent-icon">{{ getAgentIcon(agentId) }}</span>
            <span class="agent-name">{{ agentId }}</span>
          </div>
          <div class="agent-status">{{ state.status }}</div>
          <div v-if="state.progress" class="agent-progress">
            进度: {{ state.progress }}%
          </div>
        </div>
      </div>
    </div>

    <!-- 实时日志 -->
    <div class="logs-section">
      <div class="logs-header">
        <h2>实时日志</h2>
        <button @click="clearLogs" class="clear-btn">清空</button>
      </div>
      <div class="logs-container" ref="logsContainer">
        <div
          v-for="(log, index) in logs"
          :key="index"
          :class="['log-entry', log.level]"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-level">[{{ log.level }}]</span>
          <span v-if="log.agent_id" class="log-agent">[{{ log.agent_id }}]</span>
          <span class="log-message">{{ log.message }}</span>
        </div>
      </div>
    </div>

    <!-- 分析结果 -->
    <div v-if="results" class="results-section">
      <h2>分析结果</h2>
      <div class="results-summary">
        <div class="result-item">
          <span class="label">会话ID:</span>
          <span class="value">{{ results.session_id }}</span>
        </div>
        <div class="result-item">
          <span class="label">状态:</span>
          <span class="value">{{ results.status }}</span>
        </div>
        <div class="result-item">
          <span class="label">完成 Agent 数:</span>
          <span class="value">{{ Object.keys(results.agents || {}).length }}</span>
        </div>
      </div>
      <div class="results-detail">
        <h3>Agent 输出</h3>
        <div v-for="(agent, agentId) in results.agents" :key="agentId" class="agent-result">
          <div class="agent-result-header">
            <span class="agent-icon">{{ getAgentIcon(agentId) }}</span>
            <span class="agent-name">{{ agentId }}</span>
            <span :class="['agent-status-badge', agent.status]">{{ agent.status }}</span>
          </div>
          <div v-if="agent.output" class="agent-output">
            {{ agent.output }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onUnmounted, nextTick } from 'vue'
import { asyncAnalysisService } from '@/utils/asyncAnalysisService'

export default {
  name: 'AsyncAnalysisDemo',
  setup() {
    // 输入状态
    const stockCode = ref('000001')
    const stockName = ref('平安银行')
    const depth = ref(2)

    // 任务状态
    const taskId = ref(null)
    const sessionId = ref(null)
    const taskStatus = ref('')
    const progress = ref(0)
    const statusMessage = ref('')
    const isAnalyzing = ref(false)

    // Agent 状态
    const agentStates = ref({})

    // 日志
    const logs = ref([])
    const logsContainer = ref(null)

    // 结果
    const results = ref(null)

    // Agent 图标映射
    const agentIcons = {
      macro_analyst: '🌍',
      industry_analyst: '🏭',
      technical_analyst: '📈',
      funds_analyst: '💰',
      fundamental_analyst: '💼',
      fundamental_director: '👔',
      momentum_director: '⚡',
      systemic_risk_director: '⚠️',
      portfolio_risk_director: '📉',
      investment_gm: '👑'
    }

    const getAgentIcon = (agentId) => {
      return agentIcons[agentId] || '🤖'
    }

    const statusClass = computed(() => {
      switch (taskStatus.value) {
        case 'completed': return 'success'
        case 'failed': return 'error'
        case 'running': return 'running'
        case 'pending': return 'pending'
        default: return ''
      }
    })

    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit',
        second: '2-digit',
        fractionalSecondDigits: 3
      })
    }

    const addLog = (log) => {
      logs.value.push(log)
      // 自动滚动到底部
      nextTick(() => {
        if (logsContainer.value) {
          logsContainer.value.scrollTop = logsContainer.value.scrollHeight
        }
      })
    }

    const clearLogs = () => {
      logs.value = []
    }

    const startAnalysis = async () => {
      if (!stockCode.value || isAnalyzing.value) return

      // 重置状态
      isAnalyzing.value = true
      taskStatus.value = 'pending'
      progress.value = 0
      statusMessage.value = '正在提交任务...'
      agentStates.value = {}
      results.value = null
      clearLogs()

      try {
        const result = await asyncAnalysisService.startAnalysis(
          {
            stockCode: stockCode.value,
            stockName: stockName.value,
            depth: depth.value
          },
          {
            onConnected: () => {
              addLog({ level: 'info', message: 'SSE 连接成功', timestamp: new Date().toISOString() })
            },

            onAgentStart: (data) => {
              agentStates.value[data.agent_id] = { status: 'running', progress: 0 }
            },

            onAgentProgress: (data) => {
              if (agentStates.value[data.agent_id]) {
                agentStates.value[data.agent_id].progress = data.progress
              }
            },

            onAgentComplete: (data) => {
              agentStates.value[data.agent_id] = { status: 'completed', progress: 100 }
            },

            onAgentError: (data) => {
              agentStates.value[data.agent_id] = { status: 'error', error: data.error }
            },

            onStageStart: (data) => {
              statusMessage.value = `开始第 ${data.stage} 阶段`
            },

            onStageComplete: (data) => {
              statusMessage.value = `第 ${data.stage} 阶段完成`
            },

            onLog: (data) => {
              addLog(data)
            },

            onComplete: async () => {
              taskStatus.value = 'completed'
              progress.value = 100
              statusMessage.value = '分析完成'
              isAnalyzing.value = false

              // 获取完整结果
              try {
                results.value = await asyncAnalysisService.getResults()
              } catch (e) {
                console.error('获取结果失败:', e)
              }
            },

            onError: (error) => {
              taskStatus.value = 'failed'
              statusMessage.value = `错误: ${error.message || error}`
              isAnalyzing.value = false
            }
          }
        )

        taskId.value = result.taskId
        sessionId.value = result.sessionId
        taskStatus.value = 'running'
        statusMessage.value = '任务已提交，等待执行...'

        // 启动状态轮询（作为 SSE 的备份）
        pollTaskStatus()

      } catch (error) {
        console.error('启动分析失败:', error)
        taskStatus.value = 'failed'
        statusMessage.value = `启动失败: ${error.message}`
        isAnalyzing.value = false
      }
    }

    const pollTaskStatus = async () => {
      if (!isAnalyzing.value) return

      try {
        const status = await asyncAnalysisService.getTaskStatus()
        if (status) {
          taskStatus.value = status.status
          progress.value = status.progress
          if (status.message) {
            statusMessage.value = status.message
          }

          if (status.status === 'completed' || status.status === 'failed') {
            isAnalyzing.value = false
            if (status.status === 'completed') {
              results.value = await asyncAnalysisService.getResults()
            }
            return
          }
        }
      } catch (e) {
        console.error('轮询状态失败:', e)
      }

      // 继续轮询
      if (isAnalyzing.value) {
        setTimeout(pollTaskStatus, 2000)
      }
    }

    const cancelAnalysis = async () => {
      try {
        await asyncAnalysisService.cancelTask()
        taskStatus.value = 'cancelled'
        statusMessage.value = '任务已取消'
        isAnalyzing.value = false
      } catch (error) {
        console.error('取消失败:', error)
      }
    }

    // 组件卸载时断开连接
    onUnmounted(() => {
      asyncAnalysisService.disconnect()
    })

    return {
      stockCode,
      stockName,
      depth,
      taskId,
      sessionId,
      taskStatus,
      progress,
      statusMessage,
      isAnalyzing,
      agentStates,
      logs,
      logsContainer,
      results,
      statusClass,
      getAgentIcon,
      formatTime,
      clearLogs,
      startAnalysis,
      cancelAnalysis
    }
  }
}
</script>

<style scoped>
.async-analysis-demo {
  max-width: 1200px;
  margin: 0 auto;
  padding: 20px;
  color: #e0e0e0;
  background: #1a1a2e;
  min-height: 100vh;
}

h1 {
  text-align: center;
  color: #4fc3f7;
  margin-bottom: 30px;
}

h2 {
  color: #81d4fa;
  margin-bottom: 15px;
  font-size: 1.2rem;
}

/* 输入区 */
.input-section {
  background: #252542;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
}

.input-group {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.input-group label {
  width: 100px;
  color: #b0bec5;
}

.input-group input,
.input-group select {
  flex: 1;
  padding: 10px;
  border: 1px solid #3d3d5c;
  border-radius: 5px;
  background: #1a1a2e;
  color: #e0e0e0;
  font-size: 14px;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-top: 20px;
}

.start-btn {
  flex: 1;
  padding: 12px 24px;
  background: linear-gradient(135deg, #4fc3f7, #29b6f6);
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  font-weight: bold;
}

.start-btn:disabled {
  background: #3d3d5c;
  cursor: not-allowed;
}

.cancel-btn {
  padding: 12px 24px;
  background: #ef5350;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
}

/* 状态区 */
.status-section {
  background: #252542;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
}

.status-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.task-id {
  font-size: 12px;
  color: #78909c;
  font-family: monospace;
}

.status-info {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.status-item .label {
  width: 60px;
  color: #b0bec5;
}

.status-item .value {
  color: #e0e0e0;
}

.status-item .value.success { color: #66bb6a; }
.status-item .value.error { color: #ef5350; }
.status-item .value.running { color: #4fc3f7; }
.status-item .value.pending { color: #ffb74d; }

.progress-bar {
  flex: 1;
  height: 20px;
  background: #1a1a2e;
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4fc3f7, #29b6f6);
  transition: width 0.3s ease;
}

.progress-text {
  width: 50px;
  text-align: right;
  color: #4fc3f7;
}

/* Agent 网格 */
.agents-section {
  background: #252542;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 10px;
}

.agent-card {
  background: #1a1a2e;
  padding: 15px;
  border-radius: 8px;
  border: 1px solid #3d3d5c;
  text-align: center;
}

.agent-card.running {
  border-color: #4fc3f7;
  animation: pulse 1.5s infinite;
}

.agent-card.completed {
  border-color: #66bb6a;
}

.agent-card.error {
  border-color: #ef5350;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

.agent-header {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  margin-bottom: 8px;
}

.agent-icon {
  font-size: 20px;
}

.agent-name {
  font-size: 12px;
  color: #b0bec5;
}

.agent-status {
  font-size: 11px;
  color: #78909c;
  text-transform: uppercase;
}

.agent-progress {
  font-size: 11px;
  color: #4fc3f7;
  margin-top: 5px;
}

/* 日志区 */
.logs-section {
  background: #252542;
  padding: 20px;
  border-radius: 10px;
  margin-bottom: 20px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.clear-btn {
  padding: 5px 15px;
  background: #3d3d5c;
  color: #b0bec5;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 12px;
}

.logs-container {
  background: #1a1a2e;
  border-radius: 5px;
  padding: 10px;
  height: 300px;
  overflow-y: auto;
  font-family: monospace;
  font-size: 12px;
}

.log-entry {
  padding: 3px 0;
  border-bottom: 1px solid #252542;
}

.log-entry.debug { color: #78909c; }
.log-entry.info { color: #4fc3f7; }
.log-entry.warning { color: #ffb74d; }
.log-entry.error { color: #ef5350; }

.log-time {
  color: #546e7a;
  margin-right: 10px;
}

.log-level {
  margin-right: 5px;
}

.log-agent {
  color: #81d4fa;
  margin-right: 5px;
}

/* 结果区 */
.results-section {
  background: #252542;
  padding: 20px;
  border-radius: 10px;
}

.results-summary {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #3d3d5c;
}

.result-item {
  display: flex;
  gap: 5px;
}

.result-item .label {
  color: #b0bec5;
}

.result-item .value {
  color: #e0e0e0;
}

.results-detail h3 {
  color: #81d4fa;
  margin-bottom: 15px;
  font-size: 1rem;
}

.agent-result {
  background: #1a1a2e;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 10px;
}

.agent-result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}

.agent-status-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  text-transform: uppercase;
}

.agent-status-badge.completed {
  background: #1b5e20;
  color: #a5d6a7;
}

.agent-status-badge.error {
  background: #b71c1c;
  color: #ef9a9a;
}

.agent-output {
  color: #b0bec5;
  font-size: 13px;
  line-height: 1.5;
  white-space: pre-wrap;
}
</style>
