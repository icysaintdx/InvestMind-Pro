<template>
  <div class="debate-panel" :class="statusClass">
    <div class="debate-header">
      <div class="debate-title">
        <span class="debate-icon">🎯</span>
        <h3>{{ title }}</h3>
      </div>
      <div class="debate-status">
        <span v-if="status === 'idle'" class="status-badge idle">待命</span>
        <span v-else-if="status === 'debating'" class="status-badge debating">辩论中...</span>
        <span v-else-if="status === 'finished'" class="status-badge finished">已完成</span>
        <button v-if="showConfig" @click="toggleConfig" class="config-toggle-btn" :class="{active: configExpanded}">
          ⚙️ {{ configExpanded ? '收起配置' : '配置模型' }}
        </button>
      </div>
    </div>

    <!-- 配置区（配置模式下显示） -->
    <div v-if="showConfig && configExpanded" class="debate-config">
      <div class="config-header">
        <span class="config-title">🤖 辩论智能体配置</span>
        <span class="config-hint">一键配置所有参与辩论的智能体</span>
      </div>
      <div class="config-body">
        <div class="config-item">
          <label class="config-label">模型 (Model)</label>
          <select v-model="selectedModel" @change="applyConfigToAll" class="model-select">
            <option v-for="opt in modelOptions" :key="opt.name" :value="opt.name">
              {{ opt.label }}
            </option>
          </select>
        </div>
        <div class="config-item">
          <div class="temp-header">
            <label class="config-label">随机性 (Temp)</label>
            <span class="temp-value">{{ temperature }}</span>
          </div>
          <div class="temp-slider-container">
            <span class="temp-label">严谨</span>
            <input 
              type="range" 
              v-model.number="temperature"
              @input="applyConfigToAll"
              class="temp-slider"
              min="0" 
              max="1" 
              step="0.1"
            >
            <span class="temp-label">发散</span>
          </div>
        </div>
        <div class="config-agents-list">
          <span class="agents-label">当前配置将应用于：</span>
          <div class="agents-tags">
            <span v-for="agentId in agentIds" :key="agentId" class="agent-tag">
              {{ getAgentName(agentId) }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <div class="debate-content">
      <!-- 辩论双方展示 -->
      <div class="sides-header" v-if="sides.length > 0">
        <div class="side left">
          <span class="side-icon">{{ sides[0].icon }}</span>
          <span class="side-name text-red-400">{{ sides[0].name }}</span>
        </div>
        <div class="vs-badge">VS</div>
        <div class="side right">
          <span class="side-name text-green-400">{{ sides[1].name }}</span>
          <span class="side-icon">{{ sides[1].icon }}</span>
        </div>
      </div>

      <!-- 辩论记录流 -->
      <div class="debate-stream" ref="streamContainer">
        <transition-group name="message-fade">
          <div 
            v-for="(msg, index) in messages" 
            :key="index" 
            class="debate-message"
            :class="getMessageClass(msg)"
          >
            <div class="message-avatar">
              {{ msg.agentIcon }}
            </div>
            <div class="message-bubble">
              <div class="message-sender">{{ msg.agentName }}</div>
              <div class="message-text">{{ msg.content }}</div>
              <div class="message-meta" v-if="msg.round">Round {{ msg.round }}</div>
            </div>
          </div>
        </transition-group>
        
        <!-- 加载指示器 -->
        <div v-if="status === 'debating'" class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <!-- 结论区域 -->
    <div v-if="conclusion" class="debate-footer">
      <div class="conclusion-box">
        <div class="conclusion-title">
          <span>🏆 最终结论</span>
          <span class="conclusion-score" :class="getScoreClass(conclusion.score)">
            评分: {{ conclusion.score }}/100
          </span>
        </div>
        <div class="conclusion-text">
          {{ conclusion.content }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DebatePanel',
  props: {
    title: {
      type: String,
      required: true
    },
    topic: {
      type: String,
      required: true
    },
    status: {
      type: String,
      default: 'idle' // idle, debating, finished
    },
    sides: {
      type: Array,
      default: () => [] // [{name: '多头', icon: '🐂'}, {name: '空头', icon: '🐻'}]
    },
    messages: {
      type: Array,
      default: () => []
    },
    conclusion: {
      type: Object,
      default: null // { content: '...', score: 85 }
    },
    showConfig: {
      type: Boolean,
      default: false
    },
    agentIds: {
      type: Array,
      default: () => []
    }
  },
  data() {
    return {
      configExpanded: false,
      selectedModel: 'Qwen/Qwen3-8B',
      temperature: 0.3,
      modelOptions: [],
      agentNameMap: {
        'bull_researcher': '🐂 看涨研究员',
        'bear_researcher': '🐻 看跌研究员',
        'research_manager': '🎓 研究部经理',
        'risk_aggressive': '⚔️ 激进风控师',
        'risk_conservative': '🛡️ 保守风控师',
        'risk_neutral': '⚖️ 中立风控师',
        'risk_manager': '👮 风控部经理'
      }
    }
  },
  computed: {
    statusClass() {
      return `status-${this.status}`
    }
  },
  async mounted() {
    await this.loadConfig()
  },
  updated() {
    this.scrollToBottom()
  },
  methods: {
    toggleConfig() {
      this.configExpanded = !this.configExpanded
    },
    getAgentName(agentId) {
      return this.agentNameMap[agentId] || agentId
    },
    async loadConfig() {
      try {
        const response = await fetch('http://localhost:8000/api/config/agents')
        if (response.ok) {
          const data = await response.json()
          if (data.data) {
            if (data.data.selectedModels && data.data.selectedModels.length > 0) {
              this.modelOptions = data.data.selectedModels.map(modelName => ({
                name: modelName,
                label: this.formatModelLabel(modelName)
              }))
            }
            if (data.data.agents && this.agentIds.length > 0) {
              const firstAgent = data.data.agents.find(a => a.id === this.agentIds[0])
              if (firstAgent) {
                this.selectedModel = firstAgent.modelName || 'Qwen/Qwen3-8B'
                this.temperature = firstAgent.temperature || 0.3
              }
            }
          }
        }
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    },
    formatModelLabel(modelName) {
      if (modelName.includes('/')) {
        const parts = modelName.split('/')
        return parts[parts.length - 1]
      }
      const labelMap = {
        'gemini-2.0-flash-exp': 'Gemini 2.0 Flash',
        'deepseek-chat': 'DeepSeek Chat',
        'qwen-plus': '通义千问 Plus'
      }
      return labelMap[modelName] || modelName
    },
    async applyConfigToAll() {
      try {
        const loadResponse = await fetch('http://localhost:8000/api/config/agents')
        let configData = { agents: [], selectedModels: [] }
        
        if (loadResponse.ok) {
          const data = await loadResponse.json()
          if (data.data) {
            configData = data.data
          }
        }
        
        this.agentIds.forEach(agentId => {
          const agentIndex = configData.agents.findIndex(a => a.id === agentId)
          if (agentIndex >= 0) {
            configData.agents[agentIndex].modelName = this.selectedModel
            configData.agents[agentIndex].temperature = this.temperature
          } else {
            configData.agents.push({
              id: agentId,
              modelName: this.selectedModel,
              modelProvider: 'AUTO',
              temperature: this.temperature
            })
          }
        })
        
        const saveResponse = await fetch('http://localhost:8000/api/config/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(configData)
        })
        
        if (saveResponse.ok) {
          console.log(`[辩论面板] 已一键配置 ${this.agentIds.length} 个智能体`)
        }
      } catch (error) {
        console.error('保存配置失败:', error)
      }
    },
    getMessageClass(msg) {
      if (this.sides.length < 2) return 'left'
      if (msg.agentName === this.sides[0].name) return 'message-left'
      if (msg.agentName === this.sides[1].name) return 'message-right'
      return 'message-center'
    },
    getScoreClass(score) {
      if (score >= 70) return 'text-green-400'
      if (score >= 40) return 'text-yellow-400'
      return 'text-red-400'
    },
    scrollToBottom() {
      const container = this.$refs.streamContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    }
  }
}
</script>

<style scoped>
.debate-panel {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 0.75rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 400px;
  backdrop-filter: blur(10px);
}

.debate-header {
  padding: 1rem;
  background: rgba(30, 41, 59, 0.5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.status-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
  color: #94a3b8;
}

.status-badge.debating {
  background: rgba(234, 179, 8, 0.2);
  color: #fcd34d;
  animation: pulse 2s infinite;
}

.status-badge.finished {
  background: rgba(16, 185, 129, 0.2);
  color: #6ee7b7;
}

.sides-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 2rem;
  background: rgba(0, 0, 0, 0.2);
}

.side {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: bold;
}

.side-icon {
  font-size: 1.5rem;
}

.vs-badge {
  font-weight: 900;
  font-style: italic;
  color: #6366f1;
  font-size: 1.25rem;
}

.debate-stream {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  scroll-behavior: smooth;
}

.debate-message {
  display: flex;
  gap: 0.75rem;
  max-width: 80%;
  align-items: flex-start;
}

.message-left {
  align-self: flex-start;
  flex-direction: row;
}

.message-right {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-center {
  align-self: center;
  max-width: 90%;
  background: rgba(255, 255, 255, 0.05);
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
}

.message-avatar {
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-bubble {
  background: rgba(30, 41, 59, 0.8);
  padding: 0.75rem;
  border-radius: 0.75rem;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.message-left .message-bubble {
  border-top-left-radius: 0;
  border-left: 2px solid rgba(239, 68, 68, 0.5); /* Red tint for left/bear */
}

.message-right .message-bubble {
  border-top-right-radius: 0;
  border-right: 2px solid rgba(34, 197, 94, 0.5); /* Green tint for right/bull */
}

.message-sender {
  font-size: 0.75rem;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 0.25rem;
}

.message-text {
  font-size: 0.875rem;
  color: #e2e8f0;
  line-height: 1.5;
  white-space: pre-wrap;
}

.message-meta {
  font-size: 0.65rem;
  color: #64748b;
  margin-top: 0.25rem;
  text-align: right;
}

.debate-footer {
  padding: 1rem;
  background: rgba(15, 23, 42, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.conclusion-box {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 0.5rem;
  padding: 1rem;
}

.conclusion-title {
  display: flex;
  justify-content: space-between;
  font-weight: bold;
  color: #818cf8;
  margin-bottom: 0.5rem;
}

.conclusion-text {
  font-size: 0.875rem;
  color: #c7d2fe;
  line-height: 1.6;
}

/* Animations */
.message-fade-enter-active, .message-fade-leave-active {
  transition: all 0.5s ease;
}
.message-fade-enter-from, .message-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 0.5rem;
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  margin-left: 3rem;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #94a3b8;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}

/* 配置区样式 */
.debate-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.debate-title h3 {
  font-size: 1.125rem;
  font-weight: bold;
  color: white;
  margin: 0;
}

.debate-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.config-toggle-btn {
  font-size: 0.75rem;
  padding: 0.25rem 0.75rem;
  background: rgba(99, 102, 241, 0.2);
  border: 1px solid rgba(99, 102, 241, 0.4);
  border-radius: 0.375rem;
  color: #a5b4fc;
  cursor: pointer;
  transition: all 0.2s;
}

.config-toggle-btn:hover {
  background: rgba(99, 102, 241, 0.3);
  border-color: rgba(99, 102, 241, 0.6);
}

.config-toggle-btn.active {
  background: rgba(99, 102, 241, 0.4);
  color: #c7d2fe;
}

.debate-config {
  padding: 1rem;
  background: rgba(30, 41, 59, 0.5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.config-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #a5b4fc;
}

.config-hint {
  font-size: 0.75rem;
  color: #64748b;
}

.config-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.config-label {
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 500;
}

.model-select {
  width: 100%;
  padding: 0.375rem 0.5rem;
  background: #1e293b;
  border: 1px solid #475569;
  border-radius: 0.375rem;
  color: white;
  font-size: 0.75rem;
  cursor: pointer;
}

.model-select:focus {
  outline: none;
  border-color: #6366f1;
}

.temp-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.temp-value {
  color: #60a5fa;
  font-size: 0.75rem;
  font-weight: 600;
  font-family: monospace;
}

.temp-slider-container {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.temp-label {
  color: #64748b;
  font-size: 0.625rem;
  white-space: nowrap;
}

.temp-slider {
  flex: 1;
  -webkit-appearance: none;
  height: 6px;
  background: #1e293b;
  border-radius: 9999px;
  outline: none;
  border: 1px solid #334155;
}

.temp-slider::-webkit-slider-thumb {
  -webkit-appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #6366f1;
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
  border: 2px solid #0f172a;
  cursor: pointer;
}

.temp-slider::-webkit-slider-thumb:hover {
  background: #818cf8;
  transform: scale(1.1);
}

.config-agents-list {
  margin-top: 0.5rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.agents-label {
  font-size: 0.75rem;
  color: #94a3b8;
  display: block;
  margin-bottom: 0.5rem;
}

.agents-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.agent-tag {
  background: rgba(99, 102, 241, 0.15);
  border: 1px solid rgba(99, 102, 241, 0.3);
  color: #a5b4fc;
  font-size: 0.7rem;
  padding: 0.125rem 0.5rem;
  border-radius: 0.25rem;
}
</style>
