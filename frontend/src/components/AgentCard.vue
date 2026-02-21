<template>
  <div class="agent-card" :class="[colorClass, statusClass]">
    <!-- 头部 -->
    <div class="card-header">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-1">
          <div class="text-xl">{{ agent.icon }}</div>
          <div class="font-semibold text-white text-xs">{{ agent.title }}</div>
          <div class="info-icon-wrapper group ml-1">
            <span 
              class="info-icon cursor-help text-slate-400 hover:text-blue-400 transition-colors text-sm"
              :title="descriptions[agent.id] || descriptions[agent.role] || '专业投资分析智能体'"
            >ℹ️</span>
          </div>
        </div>
        <div class="flex items-center gap-2">
          <!-- GM评分显示（在状态左侧） -->
          <span
            v-if="agent.id === 'gm' && gmScore !== null"
            class="gm-score"
            :class="gmScoreClass"
            :title="gmScoreTooltip"
          >
            {{ gmScore }}分
          </span>
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
          <!-- 请求模式指示器（始终显示） -->
          <FallbackIndicator
            :fallback-level="fallbackLevel"
            :show-always="true"
            v-if="status === 'success'"
          />
        </div>
      </div>
      <div class="flex items-center justify-between pl-8 mt-1">
        <div class="text-xs text-slate-400 uppercase tracking-wide">{{ agent.role }}</div>
        <div v-if="tokens > 0 || durationSeconds" class="text-xs text-slate-500 font-mono flex items-center gap-1">
          <span v-if="durationSeconds">{{ formatDuration(durationSeconds) }}</span>
          <span v-if="tokens > 0">
            <span v-if="durationSeconds">· </span>
            {{ tokens.toLocaleString() }} tokens
          </span>
        </div>
      </div>
    </div>

    <!-- 配置区（配置模式下显示） -->
    <div v-if="showConfig" class="agent-config">
      <!-- Config content... -->
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

    <!-- 思维链展示区 (新增) -->
    <div v-if="thoughts && thoughts.length > 0" class="thoughts-container">
      <div class="thoughts-header">
        <span class="text-xs font-semibold text-blue-400">🧠 思考过程</span>
      </div>
      <div class="thoughts-list">
        <div v-for="(thought, index) in thoughts" :key="index" class="thought-item">
          <span class="thought-icon">{{ thought.icon || '💭' }}</span>
          <span class="thought-text">{{ thought.message }}</span>
        </div>
      </div>
    </div>

    <!-- 数据源展示区 (新增) -->
    <div v-if="dataSources && dataSources.length > 0" class="sources-container">
      <div class="sources-header">
        <span class="text-xs font-semibold text-emerald-400">📊 参考数据</span>
        <span class="text-xs text-slate-500">
          {{ dataSources.length }}个来源 | 
          <span v-if="totalDataCount" class="text-emerald-400 font-semibold">{{ totalDataCount }}条数据</span>
        </span>
        <!-- 折叠按钮 -->
        <button v-if="dataSources.length > 4" @click="toggleSourcesExpand" class="expand-btn">
          <span v-if="sourcesExpanded">▲</span>
          <span v-else>▼</span>
        </button>
      </div>
      <div class="sources-list">
        <div v-for="(source, index) in displayedSources" :key="index" class="source-tag" :title="getSourceTooltip(source)">
          <span class="source-name">{{ source.source }}</span>
          <span v-if="source.description" class="source-desc">({{ source.description }})</span>
          <span v-else-if="source.count" class="source-count">({{ source.count }}条数据)</span>
        </div>
      </div>
    </div>

    <!-- GM专用标签栏 -->
    <div v-if="agent.id === 'gm' && parsedGMContent.hasSimple && output" class="gm-tab-bar">
      <button 
        @click="currentView = 'professional'" 
        :class="{active: currentView === 'professional'}"
        class="gm-tab-btn"
      >
        📊 专业版
      </button>
      <button 
        @click="currentView = 'simple'" 
        :class="{active: currentView === 'simple'}"
        class="gm-tab-btn"
      >
        📢 白话版
      </button>
    </div>

    <!-- 内容区 -->
    <div v-show="isExpanded" class="card-content" :class="{ 'with-config': showConfig, 'with-tabs': agent.id === 'gm' && parsedGMContent.hasSimple }">
      <!-- 数据获取中 (fetching状态显示) -->
      <div v-if="status === 'fetching'" class="fetching-container">
        <div class="fetching-message">
          <span class="spinner"></span>
          <span>{{ getWaitingDescription() }}</span>
        </div>
      </div>
      
      <!-- 加载骨架屏 (analyzing状态显示) -->
      <div v-else-if="status === 'analyzing'" class="skeleton-loader">
        <div class="skeleton-line"></div>
        <div class="skeleton-line" style="width: 85%"></div>
        <div class="skeleton-line" style="width: 75%"></div>
        <div class="skeleton-line" style="width: 90%"></div>
        <div class="skeleton-line" style="width: 80%"></div>
      </div>

      <!-- GM的双版本内容 -->
      <div v-else-if="agent.id === 'gm' && parsedGMContent.hasSimple && output" class="gm-content">
        <!-- 专业版 -->
        <div v-show="currentView === 'professional'" class="professional-content">
          <TypeWriter 
            :text="parsedGMContent.professional" 
            :speed="20"
            @complete="handleTypeComplete"
          />
        </div>
        <!-- 白话版 -->
        <div v-show="currentView === 'simple'" class="simple-content">
          <TypeWriter 
            :text="parsedGMContent.simple" 
            :speed="20"
            @complete="handleTypeComplete"
          />
        </div>
      </div>

      <!-- 其他智能体的正常内容 -->
      <div v-else-if="output" class="analysis-output">
        <TypeWriter 
          :text="output" 
          :speed="20"
          @complete="handleTypeComplete"
        />
      </div>

      <!-- 空状态 -->
      <div v-else class="empty-state">
        <div class="waiting-icon">⏳</div>
        <span class="waiting-title">等待分析...</span>
        <p class="waiting-desc">{{ getWaitingDescription() }}</p>
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

import FallbackIndicator from './FallbackIndicator.vue'
import API_BASE_URL from '@/config/api.js'

export default {
  name: 'AgentCard',
  components: {
    TypeWriter,
    FallbackIndicator
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
    thoughts: {
      type: Array,
      default: () => []
    },
    dataSources: {
      type: Array,
      default: () => []
    },
    showConfig: {
      type: Boolean,
      default: false
    },
    modelUpdateTrigger: {
      type: Number,
      default: 0
    },
    isExpanded: {
      type: Boolean,
      default: false
    },
    fallbackLevel: {
      type: Number,
      default: 0
    },
    durationSeconds: {
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
    },
  },
  data() {
    return {
      currentView: 'professional', // GM卡片的标签切换：'professional' 或 'simple'
      selectedModel: this.agent.modelName || 'Qwen/Qwen3-8B',
      temperature: this.agent.temperature || 0.3,
      modelOptions: [], // 将从后端加载
      sourcesExpanded: false, // 数据源是否展开
      descriptions: {
        'news_analyst': '基于NLP技术实时监控全网24小时内的财经新闻与公告，提取关键事件对股价的潜在影响。',
        'social_analyst': '利用情感分析模型扫描雪球、股吧等社区讨论，量化散户恐慌与贪婪指数，捕捉市场情绪拐点。',
        'china_market': '专注分析中国A股市场特有的政策导向、流动性环境及监管动态，评估系统性环境。',
        'macro': '分析GDP、CPI、货币政策及系统性风险，判断宏观经济周期与大类资产配置方向。',
        'industry': '跟踪行业指数、景气度及产业链上下游关系，结合竞争格局判断行业生命周期。',
        'technical': '运用量化技术指标（MA/MACD/布林带）对K线形态进行模式识别，寻找关键支撑位与阻力位。',
        'funds': '监控主力资金流向、北向资金动态及龙虎榜数据，洞察机构席位与游资的真实意图。',
        'fundamental': '深度解析财报数据、估值模型（DCF/PE/PB）及业绩预期，寻找具备安全边际的价值洼地。',
        'bull_researcher': '作为永远的乐观派，专注于挖掘公司的增长潜力、护城河优势及潜在的股价催化剂。',
        'bear_researcher': '作为冷静的怀疑论者，专注于寻找财报瑕疵、估值泡沫及可能导致下跌的风险因素。',
        'manager_fundamental': '基于深度基本面研究，忽略短期波动，从企业长期价值创造角度给出投资建议。',
        'manager_momentum': '基于动量因子与市场情绪，捕捉短期价格趋势，寻找高盈亏比的交易机会。',
        'research_manager': '统筹各领域分析师的观点，解决逻辑冲突，确保研究结论的一致性与准确性。',
        'risk_aggressive': '追求高赔率，愿意承担适度回撤以换取超额收益，关注上涨空间大于下跌风险的机会。',
        'risk_conservative': '厌恶亏损，首要目标是本金安全，强调严格的仓位控制与止损策略。',
        'risk_neutral': '平衡收益与风险，寻求夏普比率最大化，不偏激也不保守。',
        'risk_system': '专注评估市场崩盘、流动性枯竭等极端系统性风险，监控黑天鹅事件。',
        'risk_portfolio': '管理组合的行业集中度、相关性及最大回撤，防止单一资产风险暴露过大。',
        'risk_manager': '拥有风控一票否决权，确保所有投资决策均在既定的风险容忍度框架内。',
        'gm': '投资决策委员会主席，综合基本面、技术面、资金面及风控意见，下达最终买卖指令。',
        'trader': '执行层智能体，根据指令优化具体的交易算法（VWAP/TWAP），以最小滑点完成建仓。'
      }
    }
  },
  computed: {
    totalDataCount() {
      // 计算总数据数量
      if (!this.dataSources || this.dataSources.length === 0) return 0
      return this.dataSources.reduce((total, source) => {
        return total + (source.count || 0)
      }, 0)
    },
    displayedSources() {
      // 显示的数据源（折叠/展开）
      if (!this.dataSources || this.dataSources.length === 0) return []
      if (this.dataSources.length <= 4) return this.dataSources
      return this.sourcesExpanded ? this.dataSources : this.dataSources.slice(0, 4)
    },
    parsedGMContent() {
      // 解析GM的双版本输出
      if (this.agent.id !== 'gm' || !this.output) {
        return { professional: this.output, simple: '', hasSimple: false }
      }

      const professionalMatch = this.output.match(/===PROFESSIONAL_START===([\s\S]*?)===PROFESSIONAL_END===/)
      const simpleMatch = this.output.match(/===SIMPLE_START===([\s\S]*?)===SIMPLE_END===/)

      return {
        professional: professionalMatch ? professionalMatch[1].trim() : this.output,
        simple: simpleMatch ? simpleMatch[1].trim() : '',
        hasSimple: !!simpleMatch
      }
    },
    // GM评分计算
    gmScore() {
      if (this.agent.id !== 'gm' || !this.output || this.status !== 'success') {
        return null
      }

      // 从输出中提取多维度评分
      const scores = {
        recommendation: 0,  // 推荐强度
        confidence: 0,      // 置信度
        risk: 0,            // 风险评估（反向）
        timing: 0           // 时机评估
      }

      const text = this.output.toLowerCase()

      // 1. 推荐强度评分 (0-30分)
      if (text.includes('强烈推荐') || text.includes('强烈买入') || text.includes('大力买入')) {
        scores.recommendation = 30
      } else if (text.includes('推荐买入') || text.includes('建议买入') || text.includes('适合买入')) {
        scores.recommendation = 25
      } else if (text.includes('可以考虑') || text.includes('谨慎买入') || text.includes('小仓位')) {
        scores.recommendation = 18
      } else if (text.includes('观望') || text.includes('持有') || text.includes('等待')) {
        scores.recommendation = 12
      } else if (text.includes('减仓') || text.includes('卖出') || text.includes('回避')) {
        scores.recommendation = 5
      } else {
        scores.recommendation = 15 // 默认中性
      }

      // 2. 置信度评分 (0-25分)
      const confidenceMatch = this.output.match(/置信度[：:]\s*(\d+)/i) ||
                              this.output.match(/信心[：:]\s*(\d+)/i) ||
                              this.output.match(/(\d+)%\s*置信/i)
      if (confidenceMatch) {
        const conf = parseInt(confidenceMatch[1])
        scores.confidence = Math.min(25, Math.round(conf * 0.25))
      } else if (text.includes('高度确信') || text.includes('非常确定')) {
        scores.confidence = 22
      } else if (text.includes('较为确信') || text.includes('比较确定')) {
        scores.confidence = 18
      } else if (text.includes('一定把握') || text.includes('有信心')) {
        scores.confidence = 15
      } else {
        scores.confidence = 12 // 默认
      }

      // 3. 风险评估 (0-25分，风险越低分越高)
      if (text.includes('风险较低') || text.includes('低风险') || text.includes('风险可控')) {
        scores.risk = 23
      } else if (text.includes('风险适中') || text.includes('中等风险')) {
        scores.risk = 18
      } else if (text.includes('风险较高') || text.includes('高风险') || text.includes('风险较大')) {
        scores.risk = 10
      } else if (text.includes('风险极高') || text.includes('极高风险')) {
        scores.risk = 5
      } else {
        scores.risk = 15 // 默认
      }

      // 4. 时机评估 (0-20分)
      if (text.includes('绝佳时机') || text.includes('最佳时机') || text.includes('难得机会')) {
        scores.timing = 20
      } else if (text.includes('较好时机') || text.includes('不错的时机') || text.includes('适合入场')) {
        scores.timing = 16
      } else if (text.includes('时机一般') || text.includes('可以考虑')) {
        scores.timing = 12
      } else if (text.includes('时机不佳') || text.includes('不是好时机') || text.includes('等待更好')) {
        scores.timing = 6
      } else {
        scores.timing = 10 // 默认
      }

      // 计算总分 (0-100)
      const total = scores.recommendation + scores.confidence + scores.risk + scores.timing
      return Math.min(100, Math.max(0, total))
    },
    gmScoreClass() {
      const score = this.gmScore
      if (score === null) return ''
      if (score >= 80) return 'score-excellent'
      if (score >= 65) return 'score-good'
      if (score >= 50) return 'score-medium'
      if (score >= 35) return 'score-low'
      return 'score-poor'
    },
    gmScoreTooltip() {
      const score = this.gmScore
      if (score === null) return ''
      if (score >= 80) return '综合评分优秀，投资价值高'
      if (score >= 65) return '综合评分良好，可考虑投资'
      if (score >= 50) return '综合评分中等，需谨慎考虑'
      if (score >= 35) return '综合评分偏低，风险较大'
      return '综合评分较差，建议回避'
    }
  },
  methods: {
    getSourceTooltip(source) {
      // 生成数据源的完整提示信息
      if (source.count) {
        return `${source.source}: ${source.count}条数据`
      }
      if (source.title) {
        return `${source.source}: ${source.title}`
      }
      return source.source
    },
    toggleSourcesExpand() {
      // 切换数据源展开/折叠
      this.sourcesExpanded = !this.sourcesExpanded
    },
    async loadSelectedModels() {
      try {
        // 从后端加载配置（包含selectedModels和agent配置）
        const response = await fetch(`${API_BASE_URL}/api/config/agents`)
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
                { name: 'Qwen/Qwen3-8B', label: 'Qwen3-8B' },
                { name: 'deepseek-chat', label: 'DeepSeek Chat' },
                { name: 'qwen-plus', label: '通义千问 Plus' },
                { name: 'gemini-2.0-flash-exp', label: 'Gemini 2.0 Flash' }
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
          { name: 'Qwen/Qwen3-8B', label: 'Qwen3-8B' },
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
        'qwen-turbo': '通义千问 Turbo',
        'Qwen/Qwen3-8B': 'Qwen3-8B'
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
        const loadResponse = await fetch(`${API_BASE_URL}/api/config/agents`)
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
        const saveResponse = await fetch(`${API_BASE_URL}/api/config/agents`, {
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
    },
    getWaitingDescription() {
      // 根据智能体ID返回等待时的描述
      const waitingDescriptions = {
        'news_analyst': '准备分析财经新闻对股价的影响...',
        'social_analyst': '准备扫描社交媒体情绪...',
        'china_market': '准备评估中国市场环境...',
        'industry': '准备分析行业周期与竞争格局...',
        'macro': '准备分析宏观经济影响...',
        'technical': '准备进行技术图形分析...',
        'funds': '准备追踪主力资金流向...',
        'fundamental': '准备进行基本面估值...',
        'bull_researcher': '准备挖掘上涨逻辑...',
        'bear_researcher': '准备寻找下跌风险...',
        'manager_fundamental': '准备进行价值评估...',
        'manager_momentum': '准备分析市场动能...',
        'research_manager': '准备综合各方意见...',
        'risk_aggressive': '准备制定激进策略...',
        'risk_conservative': '准备评估保守策略...',
        'risk_neutral': '准备进行中性评估...',
        'risk_system': '准备分析系统性风险...',
        'risk_portfolio': '准备优化组合配置...',
        'risk_manager': '准备进行风险把控...',
        'gm': '准备做出最终决策...',
        'trader': '准备制定交易策略...',
        'interpreter': '准备翻译成大白话...'
      }
      return waitingDescriptions[this.agent.id] || '准备开始分析...'
    },
    formatDuration(value) {
      if (!value || value <= 0) {
        return ''
      }
      const seconds = Number(value)
      return `${seconds.toFixed(1)}s`
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
  /* min-height: 360px; */  /* 移除固定高度，让高度自适应 */
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

/* GM评分样式 */
.gm-score {
  padding: 0.25rem 0.625rem;
  border-radius: 8px;
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 0.02em;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
  animation: scoreAppear 0.5s ease-out;
}

@keyframes scoreAppear {
  from {
    opacity: 0;
    transform: scale(0.8);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

/* 优秀 80-100 绿色 */
.gm-score.score-excellent {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.3) 0%, rgba(5, 150, 105, 0.2) 100%);
  color: #34d399;
  border: 1px solid rgba(16, 185, 129, 0.5);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.4);
}

/* 良好 65-79 蓝色 */
.gm-score.score-good {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(37, 99, 235, 0.2) 100%);
  color: #60a5fa;
  border: 1px solid rgba(59, 130, 246, 0.5);
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);
}

/* 中等 50-64 黄色 */
.gm-score.score-medium {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.3) 0%, rgba(217, 119, 6, 0.2) 100%);
  color: #fbbf24;
  border: 1px solid rgba(245, 158, 11, 0.5);
  box-shadow: 0 0 12px rgba(245, 158, 11, 0.4);
}

/* 偏低 35-49 橙色 */
.gm-score.score-low {
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.3) 0%, rgba(249, 115, 22, 0.2) 100%);
  color: #fb923c;
  border: 1px solid rgba(251, 146, 60, 0.5);
  box-shadow: 0 0 12px rgba(251, 146, 60, 0.4);
}

/* 较差 0-34 红色 */
.gm-score.score-poor {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.3) 0%, rgba(220, 38, 38, 0.2) 100%);
  color: #f87171;
  border: 1px solid rgba(239, 68, 68, 0.5);
  box-shadow: 0 0 12px rgba(239, 68, 68, 0.4);
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

/* 思维链样式 */
.thoughts-container {
  padding: 0.5rem 0.75rem;
  background: rgba(30, 41, 59, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  margin-top: 0.5rem;
}

.thoughts-header {
  margin-bottom: 0.25rem;
}

.thoughts-list {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.thought-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
  color: #94a3b8;
  animation: fadeIn 0.3s ease-out;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

/* 数据源样式 */
.sources-container {
  padding: 0.5rem 0.75rem;
  background: rgba(15, 23, 42, 0.3);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.sources-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.25rem;
  gap: 0.5rem;
}

.expand-btn {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  color: #10b981;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.7rem;
  transition: all 0.2s;
}

.expand-btn:hover {
  background: rgba(16, 185, 129, 0.2);
  transform: scale(1.1);
}

.sources-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.source-tag {
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.2);
  color: #6ee7b7;
  font-size: 0.65rem;
  padding: 0.125rem 0.375rem;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.source-tag:hover {
  background: rgba(16, 185, 129, 0.2);
}

.source-name {
  font-weight: 600;
  color: #10b981;
}

.source-desc {
  color: #94a3b8;
  font-size: 0.6rem;
  margin-left: 0.25rem;
}

.source-count {
  color: #6ee7b7;
  font-size: 0.6rem;
  margin-left: 0.25rem;
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
  max-height: 600px;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 0.5rem;
  margin: 0.5rem;
  font-size: 0.813rem;
}

.card-content.with-config {
  min-height: 120px;
  max-height: 400px;
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
  padding: 20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
}

.waiting-icon {
  font-size: 32px;
  animation: pulse 2s ease-in-out infinite;
}

.waiting-title {
  color: #64748b;
  font-size: 0.875rem;
  font-weight: 500;
}

.waiting-desc {
  color: #94a3b8;
  font-size: 0.75rem;
  line-height: 1.4;
  margin: 0;
  padding: 0 10px;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

/* GM标签栏样式 */
.gm-tab-bar {
  display: flex;
  gap: 8px;
  padding: 10px 15px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  background: rgba(30, 41, 59, 0.3);
}

.gm-tab-btn {
  flex: 1;
  padding: 8px 16px;
  background: rgba(51, 65, 85, 0.5);
  border: none;
  border-radius: 8px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

.gm-tab-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
  transform: translateY(-1px);
}

.gm-tab-btn.active {
  background: rgba(59, 130, 246, 0.3);
  color: #60a5fa;
  font-weight: 600;
  box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

/* GM内容区域 */
.gm-content {
  min-height: 200px;
}

.professional-content {
  color: #e2e8f0;
  font-size: 0.875rem;
  line-height: 1.6;
}

.simple-content {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
  padding: 15px;
  border-radius: 10px;
  color: #e2e8f0;
  font-size: 0.875rem;
  line-height: 1.8;
}

.simple-content strong {
  color: #10b981;
  font-weight: 600;
}

.card-content.with-tabs {
  padding-top: 0;
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

/* Tooltip 气泡样式 */
.info-icon-wrapper {
  display: inline-flex;
  align-items: center;
}

.tooltip-bubble {
  animation: tooltipFadeIn 0.2s ease-out;
  pointer-events: none;
}

.tooltip-arrow {
  position: absolute;
  top: -6px;
  left: 12px;
  width: 12px;
  height: 12px;
  background: #0f172a;
  border-left: 1px solid rgba(59, 130, 246, 0.3);
  border-top: 1px solid rgba(59, 130, 246, 0.3);
  transform: rotate(45deg);
}

/* 数据获取中 */
.fetching-container {
  padding: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fetching-message {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: #94a3b8;
  font-size: 0.875rem;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(59, 130, 246, 0.3);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes tooltipFadeIn {
  from {
    opacity: 0;
    transform: translateY(-4px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
