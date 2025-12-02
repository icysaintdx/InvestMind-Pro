<template>
  <div class="agent-card" :class="[colorClass, statusClass]">
    <!-- 头部 -->
    <div class="card-header">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1">
          <div class="text-xl">{{ agent.icon }}</div>
          <div class="font-semibold text-white text-xs">{{ agent.title }}</div>
        </div>
        <span v-if="status === 'loading'" class="status-badge loading">
          分析中...
        </span>
        <span v-else-if="status === 'success'" class="status-badge success">
          完成
        </span>
        <span v-else-if="status === 'error'" class="status-badge error">
          错误
        </span>
        <span v-else class="status-badge idle">
          待命
        </span>
      </div>
      <div class="flex items-center justify-between pl-8 mt-1">
        <div class="text-xs text-slate-400 uppercase tracking-wide">{{ agent.role }}</div>
        <div v-if="tokens > 0" class="text-xs text-slate-500 font-mono">
          {{ tokens.toLocaleString() }} tokens
        </div>
      </div>
    </div>

    <!-- 配置区（配置模式下显示） -->
    <div v-if="showConfig" class="agent-config">
      <div class="config-item">
        <label class="config-label">模型 (Model)</label>
        <select 
          v-model="selectedModel" 
          @change="updateModel"
          class="model-select"
        >
          <option 
            v-for="opt in modelOptions" 
            :key="opt.name"
            :value="opt.name"
          >
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
            @input="updateTemperature"
            class="temp-slider"
            min="0" 
            max="1" 
            step="0.1"
          >
          <span class="temp-label">发散</span>
        </div>
      </div>
    </div>

    <!-- 内容区 -->
    <div class="card-content" :class="{ 'with-config': showConfig }">
      <!-- 加载骨架屏 -->
      <div v-if="status === 'loading'" class="skeleton-loader">
        <div class="skeleton-line"></div>
        <div class="skeleton-line" style="width: 85%"></div>
        <div class="skeleton-line" style="width: 75%"></div>
        <div class="skeleton-line" style="width: 90%"></div>
      </div>

      <!-- 分析结果 -->
      <div v-else-if="output" class="analysis-output">
        <TypeWriter 
          :text="output" 
          :speed="20"
          @complete="handleTypeComplete"
        />
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <span class="text-slate-500">等待分析...</span>
      </div>
    </div>

    <!-- 底部描述 -->
    <div class="card-footer">
      <p class="text-xs text-slate-500 leading-relaxed">
        {{ descriptions[agent.id] || '专业分析师' }}
      </p>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import TypeWriter from './TypeWriter.vue'

export default {
  name: 'AgentCard',
  components: {
    TypeWriter
  },
  props: {
    agent: {
      type: Object,
      required: true
    },
    status: {
      type: String,
      default: 'idle' // idle, loading, success, error
    },
    output: {
      type: String,
      default: ''
    },
    tokens: {
      type: Number,
      default: 0
    },
    showConfig: {
      type: Boolean,
      default: false
    },
    modelUpdateTrigger: {
      type: Number,
      default: 0
    }
  },
  async created() {
    // 组件创建时加载可用模型列表
    await this.loadSelectedModels()
  },
  watch: {
    // 监听模型更新触发器
    modelUpdateTrigger() {
      console.log(`[${this.agent.id}] 检测到模型更新，重新加载模型列表`)
      this.loadSelectedModels()
    }
  },
  data() {
    return {
      selectedModel: this.agent.modelName || 'deepseek-chat',
      temperature: this.agent.temperature || 0.3,
      modelOptions: [], // 将从后端加载
      descriptions: {
        'macro': '分析GDP、CPI、货币政策及系统性风险，判断宏观水位',
        'industry': '跟踪行业指数、景气度及轮动规律，把握产业机会',
        'technical': '精通趋势分析、支撑阻力位及量价关系，识别买卖信号',
        'funds': '监控主力资金、北向资金及融资融券，洞察资金意图',
        'fundamental': '深度解析财报、估值模型及业绩预期，发现价值洼地',
        'manager_fundamental': '整合基本面分析，给出长期价值判断',
        'manager_momentum': '综合短期动能，捕捉交易机会',
        'risk_system': '评估市场系统性风险，监控黑天鹅事件',
        'risk_portfolio': '管理组合集中度、回撤及止损策略，控制风险暴露',
        'gm': '拥有最终决策权，综合收益与风险，做唯一指令'
      }
    }
  },
  methods: {
    async loadSelectedModels() {
      try {
        // 从后端加载配置（包含selectedModels和agent配置）
        const response = await fetch('http://localhost:8000/api/config/agents')
        if (response.ok) {
          const data = await response.json()
          if (data.data) {
            // 加载可用模型列表
            if (data.data.selectedModels && data.data.selectedModels.length > 0) {
              this.modelOptions = data.data.selectedModels.map(modelName => ({
                name: modelName,
                label: this.formatModelLabel(modelName)
              }))
              console.log(`[${this.agent.id}] 加载了 ${this.modelOptions.length} 个可用模型`)
            } else {
              console.log(`[${this.agent.id}] 没有找到已选择的模型，使用默认列表`)
              // 如果没有已选择的模型，加载一些默认模型
              this.modelOptions = [
                { name: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash' },
                { name: 'deepseek-chat', label: 'DeepSeek Chat' },
                { name: 'qwen-plus', label: '通义千问 Plus' },
                { name: 'Qwen/Qwen3-8B', label: 'Qwen3-8B' }
              ]
            }
            
            // 加载智能体的配置
            if (data.data.agents) {
              const agentConfig = data.data.agents.find(a => a.id === this.agent.id)
              if (agentConfig) {
                this.selectedModel = agentConfig.modelName || this.selectedModel
                this.temperature = agentConfig.temperature || this.temperature
                console.log(`[${this.agent.id}] 加载配置: 模型=${this.selectedModel}, 温度=${this.temperature}`)
              }
            }
          }
        }
      } catch (error) {
        console.error('加载模型列表失败:', error)
        // 如果加载失败，使用默认列表
        this.modelOptions = [
          { name: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash' },
          { name: 'deepseek-chat', label: 'DeepSeek Chat' },
          { name: 'qwen-plus', label: '通义千问 Plus' }
        ]
      }
    },
    formatModelLabel(modelName) {
      // 格式化模型名称为友好的显示标签
      if (modelName.includes('/')) {
        // 处理类似 "Qwen/Qwen3-8B" 的格式
        const parts = modelName.split('/')
        return parts[parts.length - 1]
      }
      // 处理其他格式
      const labelMap = {
        'gemini-2.0-flash-exp': 'Gemini 2.0 Flash',
        'deepseek-chat': 'DeepSeek Chat',
        'deepseek-coder': 'DeepSeek Coder',
        'qwen-plus': '通义千问 Plus',
        'qwen-max': '通义千问 Max',
        'qwen-turbo': '通义千问 Turbo'
      }
      return labelMap[modelName] || modelName
    },
    async updateModel() {
      console.log(`更新模型: ${this.agent.id} -> ${this.selectedModel}`)
      // 保存到后端配置文件
      await this.saveAgentConfig()
    },
    async updateTemperature() {
      console.log(`更新温度: ${this.agent.id} -> ${this.temperature}`)
      // 保存到后端配置文件
      await this.saveAgentConfig()
    },
    async saveAgentConfig() {
      try {
        // 先加载现有配置
        const loadResponse = await fetch('http://localhost:8000/api/config/agents')
        let configData = { agents: [], selectedModels: [] }
        
        if (loadResponse.ok) {
          const data = await loadResponse.json()
          if (data.data) {
            configData = data.data
          }
        }
        
        // 更新当前智能体的配置
        const agentIndex = configData.agents.findIndex(a => a.id === this.agent.id)
        if (agentIndex >= 0) {
          configData.agents[agentIndex].modelName = this.selectedModel
          configData.agents[agentIndex].temperature = this.temperature
        } else {
          // 如果没找到，添加新的配置
          configData.agents.push({
            id: this.agent.id,
            modelName: this.selectedModel,
            modelProvider: 'AUTO',
            temperature: this.temperature
          })
        }
        
        // 保存到后端
        const saveResponse = await fetch('http://localhost:8000/api/config/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(configData)
        })
        
        if (saveResponse.ok) {
          console.log(`[${this.agent.id}] 配置已保存`)
        }
      } catch (error) {
        console.error('保存配置失败:', error)
      }
    }
  },
  setup(props) {
    const statusClass = computed(() => {
      return `status-${props.status}`
    })

    const colorClass = computed(() => {
      const colorMap = {
        slate: 'gradient-card-slate',
        cyan: 'gradient-card-cyan',
        violet: 'gradient-card-violet',
        emerald: 'gradient-card-emerald',
        blue: 'gradient-card-blue',
        indigo: 'gradient-card-indigo',
        fuchsia: 'gradient-card-fuchsia',
        orange: 'gradient-card-orange',
        amber: 'gradient-card-amber',
        red: 'gradient-card-red'
      }
      return colorMap[props.agent.color] || 'gradient-card-blue'
    })

    const handleTypeComplete = () => {
      console.log(`${props.agent.title} 打字效果完成`)
    }

    return {
      statusClass,
      colorClass,
      handleTypeComplete
    }
  }
}
</script>

<style scoped>
.agent-card {
  border-radius: 0.75rem;
  overflow: hidden;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
  min-height: 360px;
  width: 100%;
  backdrop-filter: blur(10px);
}

.agent-card:hover {
  transform: scale(1.05);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

/* 渐变卡片效果 - 与原版完全一致 */
.gradient-card-slate {
  background: linear-gradient(135deg, rgba(100, 116, 139, 0.1) 0%, rgba(71, 85, 105, 0.05) 100%);
  border: 1px solid rgba(100, 116, 139, 0.3);
}
.gradient-card-cyan {
  background: linear-gradient(135deg, rgba(6, 182, 212, 0.1) 0%, rgba(8, 145, 178, 0.05) 100%);
  border: 1px solid rgba(6, 182, 212, 0.3);
}
.gradient-card-violet {
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.1) 0%, rgba(124, 58, 237, 0.05) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
}
.gradient-card-emerald {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.05) 100%);
  border: 1px solid rgba(16, 185, 129, 0.3);
}
.gradient-card-blue {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(37, 99, 235, 0.05) 100%);
  border: 1px solid rgba(59, 130, 246, 0.3);
}
.gradient-card-indigo {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(79, 70, 229, 0.05) 100%);
  border: 1px solid rgba(99, 102, 241, 0.3);
}
.gradient-card-fuchsia {
  background: linear-gradient(135deg, rgba(217, 70, 239, 0.1) 0%, rgba(192, 38, 211, 0.05) 100%);
  border: 1px solid rgba(217, 70, 239, 0.3);
}
.gradient-card-orange {
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.1) 0%, rgba(249, 115, 22, 0.05) 100%);
  border: 1px solid rgba(251, 146, 60, 0.3);
}
.gradient-card-amber {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.1) 0%, rgba(217, 119, 6, 0.05) 100%);
  border: 1px solid rgba(245, 158, 11, 0.3);
}
.gradient-card-red {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.05) 100%);
  border: 1px solid rgba(239, 68, 68, 0.3);
}

/* 状态高亮 */
.agent-card.status-loading { border-color: rgba(59, 130, 246, 0.5); }
.agent-card.status-success { border-color: rgba(16, 185, 129, 0.5); }
.agent-card.status-error { border-color: rgba(239, 68, 68, 0.5); }

.card-header {
  padding: 0.75rem;
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
  justify-content: space-between;
  align-items: center;
}

.agent-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.agent-icon {
  font-size: 1.5rem;
}

.agent-title {
  color: #f1f5f9;
  font-size: 1rem;
  font-weight: 600;
  margin: 0;
}

.agent-status {
  display: flex;
  align-items: center;
}

.status-badge {
  padding: 0.125rem 0.375rem;
  border-radius: 9999px;
  font-size: 0.625rem;
  font-weight: 500;
  white-space: nowrap;
}

.status-badge.idle {
  background: #475569;
  color: #cbd5e1;
}

.status-badge.loading {
  background: rgba(251, 191, 36, 0.2);
  color: #fbbf24;
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

.status-badge.success {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.status-badge.error {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.status-spinner {
  width: 12px;
  height: 12px;
  border: 2px solid rgba(96, 165, 250, 0.3);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* 配置区域 */
.agent-config {
  padding: 0.75rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 0.5rem;
  margin: 0.75rem;
  margin-bottom: 0;
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
  border-color: #3b82f6;
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
  background: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
  border: 2px solid #0f172a;
  cursor: pointer;
}

.temp-slider::-webkit-slider-thumb:hover {
  background: #60a5fa;
  transform: scale(1.1);
}

.card-content {
  flex: 1;
  padding: 0.75rem;
  overflow-y: auto;
  min-height: 200px;
  max-height: 400px;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 0.5rem;
  margin: 0.5rem;
  font-size: 0.813rem;
}

.card-content.with-config {
  min-height: 120px;
  max-height: 250px;
}

.skeleton-loader {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.skeleton-line {
  height: 14px;
  background: linear-gradient(90deg, 
    rgba(71, 85, 105, 0.3) 25%, 
    rgba(71, 85, 105, 0.5) 50%, 
    rgba(71, 85, 105, 0.3) 75%
  );
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  width: 100%;
}

@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}

.analysis-output {
  color: #e2e8f0;
  font-size: 0.875rem;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
}

.empty-state {
  color: #64748b;
  font-size: 0.875rem;
}

.card-footer {
  padding: 0.5rem 0.75rem;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.token-info {
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 500;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 滚动条样式 */
.card-content::-webkit-scrollbar {
  width: 6px;
}

.card-content::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
  border-radius: 3px;
}

.card-content::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.5);
  border-radius: 3px;
}

.card-content::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.7);
}
</style>
