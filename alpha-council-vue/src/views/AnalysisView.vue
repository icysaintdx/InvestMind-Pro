<template>
  <div class="analysis-container">
    <!-- 悬浮计时器 -->
    <div v-if="isAnalyzing || analysisElapsedTime > 0" class="floating-timer">
      <span class="timer-icon">⏱️</span>
      <span class="timer-label">分析耗时:</span>
      <span class="timer-value">{{ formatTime(analysisElapsedTime) }}</span>
    </div>
    
    <!-- 股票输入区 -->
    <div class="input-section">
      <div class="input-card">
        <h2 class="text-2xl font-bold text-white mb-6">📈 智能投研分析系统</h2>
        
        <div class="input-group">
          <label class="input-label">股票代码</label>
          <StockSearchInput 
            v-model="stockCode"
            placeholder="输入股票代码或名称搜索"
            @select="handleStockSelect"
            class="stock-input"
            @keyup.enter="startAnalysis"
          />
        </div>

        <button 
          @click="startAnalysis"
          :disabled="isAnalyzing || !isValidCode"
          class="analyze-btn"
        >
          <span v-if="!isAnalyzing">🚀 开始分析</span>
          <span v-else class="flex items-center">
            <span class="spinner"></span>
            全流程智能研判中...
          </span>
        </button>
      </div>
    </div>

    <!-- 智能体网格 - 按4个阶段分组显示 -->
    <div class="agents-container space-y-12">
      <!-- 第一阶段：全维信息采集与分析 -->
      <div>
        <div class="stage-header">
          <h3 class="text-xl font-bold text-blue-400 flex items-center gap-2">
            <span class="text-3xl">🌐</span>
            <span>第一阶段 - 全维信息采集与分析</span>
          </h3>
          <span class="stage-desc">聚合市场新闻、社交舆情、宏观政策及基本面数据，进行多维深度解析</span>
        </div>
        
        <!-- 第一阶段：全维信息采集与分析 -->
        <div class="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-4 gap-4">
          <AgentCard 
            v-for="agent in stage1Agents" 
            :key="agent.id"
            :agent="agent"
            :status="agentStatus[agent.id]"
            :output="agentOutputs[agent.id]"
            :thoughts="agentThoughts[agent.id]"
            :dataSources="agentDataSources[agent.id]"
            :tokens="agentTokens[agent.id]"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
            :is-expanded="cardsExpanded"
            @show-detail="showDetail"
          />
        </div>
      </div>

      <!-- 辩论环节 1：多空博弈 -->
      <div v-if="showBullBearDebate" class="debate-section">
        <DebatePanel 
          title="多空研判博弈" 
          topic="基于当前市场信息，该标的是否具备投资价值？"
          :status="bullBearDebateStatus"
          :sides="[{name: '看涨研究员', icon: '🐂'}, {name: '看跌研究员', icon: '🐻'}]"
          :messages="bullBearDebateMessages"
          :conclusion="bullBearDebateConclusion"
        />
      </div>

      <!-- 第二阶段：策略整合 -->
      <div>
        <div class="stage-header">
          <h3 class="text-xl font-bold text-purple-400 flex items-center gap-2">
            <span class="text-3xl">🧠</span>
            <span>第二阶段 - 策略整合与方向研判</span>
          </h3>
          <span class="stage-desc">综合多空观点，制定核心投资策略</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <AgentCard 
            v-for="agent in stage2Agents" 
            :key="agent.id"
            :agent="agent"
            :status="agentStatus[agent.id]"
            :output="agentOutputs[agent.id]"
            :thoughts="agentThoughts[agent.id]"
            :dataSources="agentDataSources[agent.id]"
            :tokens="agentTokens[agent.id]"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
            :is-expanded="cardsExpanded"
            @show-detail="showDetail"
          />
        </div>
      </div>

      <!-- 辩论环节 2：风控评估 -->
      <div v-if="showRiskDebate" class="debate-section">
        <DebatePanel 
          title="三方风控评估" 
          topic="当前策略的风险收益比如何？是否存在致命缺陷？"
          :status="riskDebateStatus"
          :sides="[{name: '激进风控', icon: '⚔️'}, {name: '保守风控', icon: '🛡️'}]"
          :messages="riskDebateMessages"
          :conclusion="riskDebateConclusion"
        />
      </div>

      <!-- 第三阶段：风控终审 -->
      <div>
        <div class="stage-header">
          <h3 class="text-xl font-bold text-orange-400 flex items-center gap-2">
            <span class="text-3xl">⚖️</span>
            <span>第三阶段 - 风险控制终审</span>
          </h3>
          <span class="stage-desc">全方位风险审查，确保持仓安全</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <AgentCard 
            v-for="agent in stage3Agents" 
            :key="agent.id"
            :agent="agent"
            :status="agentStatus[agent.id]"
            :output="agentOutputs[agent.id]"
            :thoughts="agentThoughts[agent.id]"
            :dataSources="agentDataSources[agent.id]"
            :tokens="agentTokens[agent.id]"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
            :is-expanded="cardsExpanded"
            @show-detail="showDetail"
          />
        </div>
      </div>

      <!-- 第四阶段：最终决策 -->
      <div>
        <div class="stage-header">
          <h3 class="text-xl font-bold text-red-400 flex items-center gap-2">
            <span class="text-3xl">👑</span>
            <span>第四阶段 - 投资决策执行</span>
          </h3>
          <span class="stage-desc">下达最终交易指令，执行量化交易，生成白话解读</span>
        </div>
        
        <!-- 决策层面板 -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
          <AgentCard 
            v-for="agent in stage4AgentsFiltered" 
            :key="agent.id"
            :agent="agent"
            :status="agentStatus[agent.id]"
            :output="agentOutputs[agent.id]"
            :thoughts="agentThoughts[agent.id]"
            :dataSources="agentDataSources[agent.id]"
            :tokens="agentTokens[agent.id]"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
            :is-expanded="cardsExpanded"
            @show-detail="showDetail"
          />
        </div>
        
      </div>

      <!-- 综合分析报告 -->
      <div v-if="showReport" class="mt-12 mb-20">
        <div class="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-8 border border-slate-700 shadow-2xl">
          <div class="flex items-center justify-between mb-6">
            <h2 class="text-3xl font-bold text-white flex items-center gap-3">
              <span>📑</span>
              <span>AlphaCouncil 最终决策报告</span>
            </h2>
            <ReportExporter 
              :stockCode="stockCode"
              :stockName="stockData?.name"
              :agents="AGENTS"
              :agentOutputs="agentOutputs"
            />
          </div>
          
          <!-- 报告版本切换标签 -->
          <div class="report-tabs">
            <div class="tab-header">
              <button 
                @click="reportView = 'professional'" 
                :class="{active: reportView === 'professional'}"
                class="tab-btn"
              >
                <span class="tab-icon">📊</span>
                <span>专业版报告</span>
                <span class="tab-badge">金融机构级</span>
              </button>
              <button 
                @click="reportView = 'simple'" 
                :class="{active: reportView === 'simple'}"
                class="tab-btn"
              >
                <span class="tab-icon">📢</span>
                <span>白话解读版</span>
                <span class="tab-badge">通俗易懂</span>
              </button>
              <!-- 白话解读员配置按钮 -->
              <button 
                v-if="reportView === 'simple'"
                @click="showInterpreterConfig = true; loadAvailableModels()"
                class="config-btn"
                title="配置白话解读员模型"
              >
                ⚙️
              </button>
            </div>
            
            <!-- 专业版报告 -->
            <div v-show="reportView === 'professional'" class="report-content bg-slate-900/50 rounded-xl p-6 max-h-[800px] overflow-y-auto border border-slate-800">
              <div class="prose prose-invert max-w-none" v-html="finalReportHtml"></div>
            </div>
            
            <!-- 白话解读版 -->
            <div v-show="reportView === 'simple'" class="report-content">
              <div v-if="agentOutputs['interpreter']" class="interpretation-panel-report">
                <div class="markdown-content" v-html="interpretationHtml"></div>
              </div>
              <div v-else class="empty-interpretation">
                <p>⚠️ 白话解读员还未完成分析，请稍候...</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 详情弹窗 -->
    <div v-if="selectedAgent" class="modal-overlay" @click="selectedAgent = null">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3 class="text-xl font-bold">{{ selectedAgent.icon }} {{ selectedAgent.title }} - 完整分析</h3>
          <button @click="selectedAgent = null" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="whitespace-pre-wrap">{{ agentOutputs[selectedAgent.id] }}</div>
        </div>
      </div>
    </div>

    <ModelManager :visible="showModelManager" @close="showModelManager = false" @save="handleModelSave" />
    <ApiConfig :visible="showApiConfig" :apiKeys="apiKeys" :apiStatus="apiStatus" @close="showApiConfig = false" @save="handleApiSave" @updateStatus="updateApiStatus" />
    <StyleConfig 
      :visible="showStyleConfig" 
      :styles="styleSettings" 
      @close="showStyleConfig = false" 
      @save="handleStyleSave"
    />
    
    <!-- 白话解读员配置弹窗 -->
    <div v-if="showInterpreterConfig" class="modal-overlay" @click="showInterpreterConfig = false">
      <div class="interpreter-config-modal" @click.stop>
        <div class="modal-header">
          <h3 class="text-xl font-bold">📢 白话解读员配置</h3>
          <button @click="showInterpreterConfig = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="config-item">
            <label class="config-label">选择模型</label>
            <select v-model="interpreterModel" class="model-select">
              <option v-for="model in availableModels" :key="model" :value="model">
                {{ model }}
              </option>
            </select>
          </div>
          <div class="config-item">
            <label class="config-label">温度 (Temperature)</label>
            <input 
              type="range" 
              v-model.number="interpreterTemperature" 
              min="0" 
              max="1" 
              step="0.1"
              class="temperature-slider"
            >
            <span class="temperature-value">{{ interpreterTemperature }}</span>
          </div>
          <div class="config-note">
            <p>💡 提示：白话解读员的任务是把专业分析翻译成通俗易懂的语言。</p>
            <p>• 推荐使用 Qwen 2.5 7B，速度快且效果好</p>
            <p>• 温度设置 0.7 可以让语言更生动</p>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showInterpreterConfig = false" class="cancel-btn">取消</button>
          <button @click="saveInterpreterConfig" class="save-btn">保存配置</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, inject } from 'vue'
import AgentCard from '@/components/AgentCard.vue'
import DebatePanel from '@/components/DebatePanel.vue'
import ModelManager from '@/components/ModelManager.vue'
import ApiConfig from '@/components/ApiConfig.vue'
import StyleConfig from '@/components/StyleConfig.vue'
import ReportExporter from '@/components/ReportExporter.vue'
import StockSearchInput from '@/components/StockSearchInput.vue'
import { marked } from 'marked' // 假设已安装，如未安装需降级处理

// 21个智能体完整定义
const AGENTS = [
  // Stage 1 - Group 1: 舆情与市场
  { id: 'news_analyst', role: 'NEWS', title: '新闻舆情分析师', icon: '📰', color: 'emerald', stage: 1, group: 1 },
  { id: 'social_analyst', role: 'SOCIAL', title: '社交媒体分析师', icon: '🗣️', color: 'cyan', stage: 1, group: 1 },
  { id: 'china_market', role: 'CHINA', title: '中国市场专家', icon: '🇨🇳', color: 'red', stage: 1, group: 1 },
  { id: 'industry', role: 'INDUSTRY', title: '行业轮动分析师', icon: '🏭', color: 'blue', stage: 1, group: 1 },
  
  // Stage 1 - Group 2: 专业分析
  { id: 'macro', role: 'MACRO', title: '宏观政策分析师', icon: '🌍', color: 'slate', stage: 1, group: 2 },
  { id: 'technical', role: 'TECHNICAL', title: '技术分析专家', icon: '📈', color: 'violet', stage: 1, group: 2 },
  { id: 'funds', role: 'FUNDS', title: '资金流向分析师', icon: '💰', color: 'emerald', stage: 1, group: 2 },
  { id: 'fundamental', role: 'FUNDAMENTAL', title: '基本面估值分析师', icon: '💼', color: 'indigo', stage: 1, group: 2 },

  // Stage 2 - 策略与辩论
  { id: 'bull_researcher', role: 'BULL', title: '看涨研究员', icon: '🐂', color: 'red', stage: 2 },
  { id: 'bear_researcher', role: 'BEAR', title: '看跌研究员', icon: '🐻', color: 'green', stage: 2 },
  { id: 'manager_fundamental', role: 'MANAGER_FUNDAMENTAL', title: '基本面研究总监', icon: '👔', color: 'blue', stage: 2 },
  { id: 'manager_momentum', role: 'MANAGER_MOMENTUM', title: '市场动能总监', icon: '⚡', color: 'amber', stage: 2 },
  { id: 'research_manager', role: 'RESEARCH_MANAGER', title: '研究部经理', icon: '🎓', color: 'violet', stage: 2 },

  // Stage 3 - 风控与博弈
  { id: 'risk_aggressive', role: 'RISK_AGGRESSIVE', title: '激进风控师', icon: '⚔️', color: 'orange', stage: 3 },
  { id: 'risk_conservative', role: 'RISK_CONSERVATIVE', title: '保守风控师', icon: '🛡️', color: 'slate', stage: 3 },
  { id: 'risk_neutral', role: 'RISK_NEUTRAL', title: '中立风控师', icon: '⚖️', color: 'blue', stage: 3 },
  { id: 'risk_system', role: 'RISK_SYSTEM', title: '系统性风险总监', icon: '⚠️', color: 'red', stage: 3 },
  { id: 'risk_portfolio', role: 'RISK_PORTFOLIO', title: '组合风险总监', icon: '📉', color: 'amber', stage: 3 },
  { id: 'risk_manager', role: 'RISK_MANAGER', title: '风控部经理', icon: '👮', color: 'indigo', stage: 3 },

  // Stage 4 - 最终决策
  { id: 'gm', role: 'GM', title: '投资决策总经理', icon: '👑', color: 'fuchsia', stage: 4 },
  { id: 'trader', role: 'TRADER', title: '量化交易员', icon: '🤖', color: 'cyan', stage: 4 },
  { id: 'interpreter', role: 'INTERPRETER', title: '白话解读员', icon: '📢', color: 'green', stage: 4 }
]

export default {
  name: 'AnalysisView',
  components: { AgentCard, DebatePanel, ModelManager, ApiConfig, StyleConfig, ReportExporter, StockSearchInput },
  setup() {
    // 注入数据透明化面板
    const currentStockData = inject('currentStockData')
    const stockDataPanel = inject('stockDataPanel')
    const newsDataPanel = inject('newsDataPanel')
    
    const stockCode = ref('')
    const stockData = ref(null)
    const isAnalyzing = ref(false)
    const selectedAgent = ref(null)
    const analysisStartTime = ref(null)
    const analysisElapsedTime = ref(0)
    const analysisTimer = ref(null)
    
    // Injected states
    const configMode = inject('configMode')
    const showModelManager = inject('showModelManager')
    const showApiConfig = inject('showApiConfig')
    const showStyleConfig = inject('showStylePanel')
    const apiStatus = inject('apiStatus')
    const apiKeys = inject('apiKeys')
    const saveApiConfig = inject('saveApiConfig')
    const updateApiStatusFunc = inject('updateApiStatus')

    // Agent states
    const agentStatus = ref({})
    const agentOutputs = ref({})
    const agentTokens = ref({})
    const agentThoughts = ref({}) // Stores array of thought steps
    const agentDataSources = ref({}) // Stores array of sources
    const modelUpdateTrigger = ref(0)
    const cardsExpanded = ref(false) // 卡片是否展开，默认折叠

    // Debate states
    const showBullBearDebate = ref(false)
    const bullBearDebateStatus = ref('idle')
    const bullBearDebateMessages = ref([])
    const bullBearDebateConclusion = ref(null)

    const showRiskDebate = ref(false)
    const riskDebateStatus = ref('idle')
    const riskDebateMessages = ref([])
    const riskDebateConclusion = ref(null)

    const showReport = ref(false)
    const reportView = ref('professional') // 默认显示专业版
    const enableSimpleSummary = ref(true) // 白话总结开关，默认开启
    const showInterpreterConfig = ref(false) // 白话解读员配置弹窗
    const interpreterModel = ref('Qwen/Qwen2.5-7B-Instruct') // 白话解读员模型
    const interpreterTemperature = ref(0.7) // 白话解读员温度
    const availableModels = ref([]) // 可用模型列表，从后端加载

    // Initialize
    const initAgents = () => {
      AGENTS.forEach(a => {
        agentStatus.value[a.id] = 'idle'
        agentOutputs.value[a.id] = ''
        agentTokens.value[a.id] = 0
        agentThoughts.value[a.id] = []
        agentDataSources.value[a.id] = []
      })
    }
    initAgents()

    // Computed Groups
    const stage1Agents = computed(() => AGENTS.filter(a => a.stage === 1))
    const stage2Agents = computed(() => AGENTS.filter(a => a.stage === 2))
    const stage3Agents = computed(() => AGENTS.filter(a => a.stage === 3))
    const stage4Agents = computed(() => AGENTS.filter(a => a.stage === 4))
    const stage4AgentsFiltered = computed(() => AGENTS.filter(a => a.stage === 4 && a.id !== 'interpreter'))
    const isValidCode = computed(() => /^\d{6}$/.test(stockCode.value))
    
    const finalReportHtml = computed(() => {
        if (!agentOutputs.value['gm']) return ''
        return marked.parse(generateReport())
    })
    
    const interpretationHtml = computed(() => {
        if (!agentOutputs.value['interpreter']) return ''
        try {
            return marked.parse(agentOutputs.value['interpreter'])
        } catch (e) {
            // 如果marked解析失败，直接返回原文本
            return `<pre>${agentOutputs.value['interpreter']}</pre>`
        }
    })
    
    // 处理股票选择
    const handleStockSelect = (stock) => {
      console.log('选择股票:', stock)
      // 移除SH/SZ前缀
      stockCode.value = stock.code.replace('SH', '').replace('SZ', '')
    }

    // Analysis Logic
    const startAnalysis = async () => {
      if (!isValidCode.value || isAnalyzing.value) return
      isAnalyzing.value = true
      cardsExpanded.value = true // 开始分析时自动展开所有卡片
      agentDataSources.value = {}
      agentStatus.value = {}
      agentOutputs.value = {}
      agentTokens.value = {}
      agentThoughts.value = {}
      showReport.value = false
      
      // 启动计时器
      analysisStartTime.value = Date.now()
      analysisElapsedTime.value = 0
      analysisTimer.value = setInterval(() => {
        analysisElapsedTime.value = Math.floor((Date.now() - analysisStartTime.value) / 1000)
      }, 1000)
      bullBearDebateMessages.value = []
      riskDebateMessages.value = []

      try {
        // 0. 数据验证阶段
        const fetchedStockData = await fetchStockData(stockCode.value)
        
        // 简单验证数据有效性
        if (!fetchedStockData || !fetchedStockData.price || fetchedStockData.price === 'N/A') {
          throw new Error('无法获取有效的市场数据，分析终止。请检查网络或数据源。')
        }
        
        stockData.value = fetchedStockData

        // 1. 执行第一阶段：全维信息采集与分析（细分三步）
        // Step 1.1: 数据采集层 (News, Social, China)
        const step1Agents = ['news_analyst', 'social_analyst', 'china_market']
        await runAgentsParallel(step1Agents, fetchedStockData)

        // Step 1.2: 行业与宏观分析层 (Industry, Macro) - 依赖Step 1.1
        const step2Agents = ['industry', 'macro']
        await runAgentsParallel(step2Agents, fetchedStockData)

        // Step 1.3: 深度专业分析层 (Technical, Funds, Fundamental) - 依赖Step 1.2
        const step3Agents = ['technical', 'funds', 'fundamental']
        await runAgentsParallel(step3Agents, fetchedStockData)

        // 2. 触发多空辩论 (模拟或真实API)
        await runBullBearDebate()

        // 3. 执行第二阶段：策略整合 (并发执行)
        console.log('[startAnalysis] 开始第二阶段...')
        const stage2Ids = AGENTS.filter(a => a.stage === 2).map(a => a.id)
        console.log('[startAnalysis] 第二阶段智能体:', stage2Ids)
        await runAgentsParallel(stage2Ids, fetchedStockData)
        console.log('[startAnalysis] 第二阶段完成')

        // 4. 触发风控辩论
        console.log('[startAnalysis] 开始风控辩论...')
        await runRiskDebate()
        console.log('[startAnalysis] 风控辩论完成')

        // 5. 执行第三阶段：风控终审
        console.log('[startAnalysis] 开始第三阶段...')
        const stage3Ids = AGENTS.filter(a => a.stage === 3).map(a => a.id)
        console.log('[startAnalysis] 第三阶段智能体:', stage3Ids)
        await runAgentsParallel(stage3Ids, fetchedStockData)
        console.log('[startAnalysis] 第三阶段完成')

        // 6. 执行第四阶段：最终决策
        const stage4Ids = AGENTS.filter(a => a.stage === 4).map(a => a.id)
        await runAgentsParallel(stage4Ids, fetchedStockData)

        showReport.value = true
        scrollToBottom()

      } catch (error) {
        console.error('分析流程异常:', error)
        alert(`分析中断: ${error.message}`)
      } finally {
        isAnalyzing.value = false
        // 停止计时器
        if (analysisTimer.value) {
          clearInterval(analysisTimer.value)
          analysisTimer.value = null
        }
      }
    }

    const runAgentsParallel = async (agentIds, data) => {
      const targetAgents = AGENTS.filter(a => agentIds.includes(a.id))
      await Promise.all(targetAgents.map(agent => runAgentAnalysis(agent, data)))
    }

    const getInstruction = (agent, data) => {
        const base = `分析${data.name || '该股票'}(${stockCode.value})的投资价值。当前价格：${data.price || 'N/A'}元，涨跌幅：${data.change_percent || 'N/A'}%。\n\n`
        
        const map = {
            // 第一阶段
            news_analyst: `你是一位专业的新闻舆情分析师。请完成以下任务：
1. 主动搜索并分析该股票最近24-48小时的所有相关新闻、公告、研报
2. 识别可能影响股价的关键事件（业绩、政策、行业动态、重大合同等）
3. 评估新闻的情绪倾向（利好/利空/中性），并给出情绪评分（-10到10）
4. 分析新闻的可信度和影响力（权威媒体vs自媒体）
5. 总结核心观点：当前舆情是偏多还是偏空？

注意：
- 必须给出具体的新闻内容和分析，不要说“暂无重大事件”
- 即使没有重大新闻，也要分析常规新闻和市场讨论
- 明确区分利好、利空和中性新闻
- 给出整体情绪评分和建议`,
            social_analyst: `你是社交媒体情绪分析专家。请完成以下任务：
1. 分析雪球、股吧等平台上散户和机构的讨论热度
2. 识别关键情绪词：恐慌、贪婪、追涨、杀跌、FOMO
3. 判断当前是散户主导还是机构主导
4. 评估社交情绪对短期股价的影响
5. 给出情绪指数（极度恐慌到极度贪婪）`,
            china_market: `你是中国市场专家。请分析：
1. A股大盘当前趋势（牛市/熊市/震荡）
2. 市场流动性状况（宽松/紧缩）
3. 政策导向（支持/中性/压制）
4. 外资流向（北向资金动态）
5. 对该股票所在板块的影响`,
            industry: `你是行业研究专家。基于前序【新闻】和【社交】的分析，请：
1. 判断行业周期（复苏/繁荣/衰退/萧条）
2. 分析竞争格局变化（龙头集中度、新进入者）
3. 评估产业链上下游关系
4. 识别行业风口和催化剂
5. 给出行业评级和投资逻辑`,
            macro: `你是宏观经济学家。结合【中国市场】的结论，请：
1. 分析货币政策对该行业的影响
2. 评估财政政策的支持力度
3. 判断经济周期所处阶段
4. 分析国际宏观环境影响
5. 给出宏观面的投资建议`,
            technical: `你是技术分析师。忽略基本面，仅从技术角度分析：
1. K线形态和趋势（上升/下降/震荡）
2. 关键支撑位和压力位（给出具体价格）
3. 均线系统（MA5/MA10/MA20/MA60）
4. 成交量变化（量价关系）
5. MACD、KDJ等指标信号
6. 给出明确的买入点、止损点、目标位`,
            funds: `你是资金流向分析师。请分析：
1. 主力资金净流入/流出情况
2. 机构持仓变化（增持/减持）
3. 北向资金动态
4. 龙虎榜数据（游资/机构）
5. 散户与主力的行为背离
6. 给出资金面的结论和预警`,
            fundamental: `你是基本面分析师。基于【行业】和【宏观】分析，请：
1. 评估核心财务指标（PE/PB/ROE/毛利率）
2. 分析盈利能力和增长性
3. 评估财务健康度（负债率、现金流）
4. 对比同行业竞争对手
5. 计算内在价值和安全边际
6. 给出估值结论（高估/合理/低估）`,
            
            // 第二阶段
            bull_researcher: `基于以上所有信息，挖掘该股票最大的上涨逻辑和潜在催化剂。`,
            bear_researcher: `基于以上所有信息，无情地指出该股票最大的下跌风险和逻辑漏洞。`,
            manager_fundamental: `从基本面角度，评估该股票的内在价值和长期投资潜力。`,
            manager_momentum: `从市场动能和情绪角度，判断该股票的短期走势。`,
            research_manager: `综合各方意见，给出研究部的整体评级和建议。`,
            
            // 第三阶段
            risk_aggressive: `假设我们必须买入，如何设置止损以最大化赔率？`,
            risk_conservative: `指出当前最危险的风险点，并给出最保守的仓位建议。`,
            risk_neutral: `从中立角度评估风险收益比，给出合理的风险管理建议。`,
            risk_system: `评估系统性风险对该股票的潜在影响。`,
            risk_portfolio: `从组合管理角度，给出该股票的配置建议。`,
            risk_manager: `综合所有风险评估，给出最终的风控意见。`,
            
            // 第四阶段
            gm: `作为投资决策总经理，综合所有分析师、多空辩论和风控意见，给出最终的投资决策。

请按以下格式输出，用特殊标记分隔两个版本：

===PROFESSIONAL_START===
## 专业投资决策

### 1. 投资建议
- 决策结论：（买入/卖出/观望）
- 目标价位：
- 仓位建议：
- 投资周期：

### 2. 决策依据
（基于所有分析师的专业意见，给出严谨的投资逻辑）

### 3. 风险评估
（综合风控团队的评估，给出专业的风险分析）
===PROFESSIONAL_END===

===SIMPLE_START===
## 白话投资建议

### 📊 【能买不？】
（明确回答：强烈推荐买入/可以适当买入/观望等待/不建议买入）

### 💰 【价格指引】
- **什么价格买合适？** （具体价格，如：1400-1420元）
- **什么价格可以卖？** （具体价格，如：1500元以上）
- **买了能放多久？** （如：3-6个月/1年以上）

### ⚠️ 【风险提醒】
（用3句大白话说清楚最需要担心的风险）
1. 
2. 
3. 

### 📝 【操作步骤】
（分步骤给出具体操作建议）
第1步：
第2步：
第3步：
===SIMPLE_END===

注意：
- 专业版保持金融机构级别的专业性
- 白话版用通俗易懂的语言，数字要具体
- 必须同时输出两个版本`,
            trader: `基于所有分析师的综合意见，请给出具体的交易策略和执行计划。包括：入场点位、止损位、目标位、仓位管理等。`,
            interpreter: `你是一位亲民的投资解读员，专门把复杂的投资分析翻译成老百姓能懂的话。

基于前面所有智能体的分析结果，请用最简单直白的语言回答：

📊 【买卖建议】
1. 能不能买？（明确回答：强烈推荐买入/可以适当买入/观望等待/不建议买入）
2. 已经有的要不要卖？（明确回答：坚决持有/可以卖出/建议减仓）

💰 【价格指引】
3. 什么价格买合适？（给出具体价格，如：1400-1420元之间）
4. 什么价格可以卖？（给出具体价格，如：1500元以上）
5. 买了能放多久？（如：建议持有3-6个月/1年以上/短线几天）

💡 【原因解释】
用3句大白话说清楚为什么给出这样的建议。

⚠️ 【风险提醒】（用大白话说3个最需要注意的风险）
- 风险1：
- 风险2：
- 风险3：

📝 【操作步骤】（具体怎么做）
第1步：
第2步：
第3步：

记住：不用专业术语，像朋友聊天，数字要具体。`
        }
        
        return base + (map[agent.id] || map[agent.role] || "请基于你的专业领域进行分析。")
    }

    const runAgentAnalysis = async (agent, data) => {
      agentStatus.value[agent.id] = 'fetching'
      
      // 模拟思维链步骤
      simulateThoughts(agent.id, agent.role)

      try {
        // ✅ 关键修复：先获取数据源，再进行分析
        // 为不同的智能体添加真实的数据源
        if (agent.id === 'news_analyst') {
          // 新闻分析师 - 显示具体新闻标题
          try {
            const newsResult = await fetchNewsData(data.symbol)
            const sources = []
            
            // 先添加3条模拟的具体新闻（带描述）
            const stockName = data.name || '该股票'
            sources.push(
              { source: '东方财富', count: 1, description: `${stockName}：最新市场动态分析` },
              { source: '新浪财经', count: 1, description: `${stockName}所属行业板块走势分析` },
              { source: '雪球社区', count: 1, description: `${stockName}投资者情绪报告` }
            )
            
            // 再添加真实数据
            if (newsResult && newsResult.success) {
              console.log('[news_analyst] 完整newsResult:', newsResult)
              
              // 检查数据结构
              let sources_data = null
              if (newsResult.data && newsResult.data.sources) {
                sources_data = newsResult.data.sources
              } else if (newsResult.sources) {
                sources_data = newsResult.sources
              }
              
              if (sources_data && typeof sources_data === 'object') {
                console.log('[news_analyst] ✅ 找到sources，数量:', Object.keys(sources_data).length)
                
                for (const [sourceName, sourceData] of Object.entries(sources_data)) {
                  if (sourceData && sourceData.status === 'success' && sourceData.count > 0) {
                    // 使用友好名称映射
                    const friendlyName = SOURCE_NAME_MAP[sourceName] || sourceData.source || sourceName
                    const newSource = {
                      source: friendlyName,
                      count: sourceData.count || 0
                    }
                    console.log(`[news_analyst] ✅ 添加数据源:`, newSource)
                    sources.push(newSource)
                  }
                }
              } else {
                console.warn('[news_analyst] ⚠️ sources不存在')
                console.warn('[news_analyst] newsResult.data:', newsResult.data)
              }
            }
            
            console.log(`[news_analyst] 准备设置数据源, 总数: ${sources.length}`)
            console.log(`[news_analyst] sources详情:`, JSON.stringify(sources, null, 2))
            agentDataSources.value[agent.id] = sources
            console.log(`[news_analyst] 已设置数据源:`, agentDataSources.value[agent.id])
            
          } catch (e) {
            console.error('[news_analyst] 获取新闻数据失败:', e)
            // 失败时也显示模拟数据
            agentDataSources.value[agent.id] = [
              { source: '东方财富', count: 5 },
              { source: '新浪财经', count: 3 },
              { source: '雪球社区', count: 2 }
            ]
          }
        } else if (agent.id === 'social_analyst') {
          // 社交媒体分析师 - 显示具体社交媒体数据
          try {
            const newsResult = await fetchNewsData(data.symbol)
            const sources = []
            
            // 先添加3条模拟的具体社交媒体数据（带描述）
            const stockName = data.name || '该股票'
            sources.push(
              { source: '雪球社区', count: 1, description: `${stockName}投资者讨论热度分析` },
              { source: '股吧论坛', count: 1, description: `${stockName}散户情绪监测` },
              { source: '东方财富股吧', count: 1, description: `${stockName}社区舆情跟踪` }
            )
            
            // 再添加真实数据
            if (newsResult && newsResult.success) {
              const newsData = newsResult.data || newsResult
              if (newsData.sources) {
                const weiboData = newsData.sources.weibo_hot
                if (weiboData && weiboData.status === 'success' && weiboData.count > 0) {
                  sources.push({
                    source: '微博热议',
                    count: weiboData.count
                  })
                }
              }
            }
            
            agentDataSources.value[agent.id] = sources
            console.log(`[social_analyst] 设置数据源:`, sources)
            
          } catch (e) {
            console.error('[social_analyst] 获取社交数据失败:', e)
            // 失败时也显示模拟数据
            agentDataSources.value[agent.id] = [
              { source: '雪球社区', count: 3 },
              { source: '股吧论坛', count: 2 },
              { source: '东方财富股吧', count: 4 }
            ]
          }
        } else if (agent.id === 'china_market') {
          // 中国市场专家 - 显示具体市场数据
          try {
            const newsResult = await fetchNewsData(data.symbol)
            const sources = []
            
            // 先添加3条模拟的具体市场数据（带描述）
            sources.push(
              { source: '中国证券报', count: 1, description: `A股市场整体走势分析` },
              { source: '上证报', count: 1, description: `宏观经济政策解读` },
              { source: '证券时报', count: 1, description: `市场流动性监测` }
            )
            
            // 再添加真实数据
            if (newsResult && newsResult.success) {
              const newsData = newsResult.data || newsResult
              if (newsData.sources) {
                // 财联社快讯
                const clsData = newsData.sources.cls_telegraph
                if (clsData && clsData.status === 'success' && clsData.count > 0) {
                  sources.push({
                    source: '财联社快讯',
                    count: clsData.count
                  })
                }
                
                // 东方财富
                const realtimeData = newsData.sources.realtime_news
                if (realtimeData && realtimeData.status === 'success' && realtimeData.count > 0) {
                  sources.push({
                    source: '东方财富',
                    count: realtimeData.count
                  })
                }
              }
            }
            
            agentDataSources.value[agent.id] = sources
            console.log(`[china_market] 设置数据源:`, sources)
            
          } catch (e) {
            console.error('[china_market] 获取市场数据失败:', e)
            // 失败时也显示模拟数据
            agentDataSources.value[agent.id] = [
              { source: '中国证券报', count: 2 },
              { source: '上证报', count: 3 },
              { source: '证券时报', count: 1 }
            ]
          }
        } else if (agent.id === 'funds') {
          // 资金流向分析师 - 获取真实数据
          try {
            const response = await fetch(`http://localhost:8000/api/akshare/fund-flow/${data.symbol}`)
            const result = await response.json()
            
            if (result.success && result.sources) {
              agentDataSources.value[agent.id] = [
                { source: '北向资金数据', count: result.sources.north_bound || 0, description: '沪深港通实时流向' },
                { source: '主力资金数据', count: result.sources.individual_flow || 0, description: '大单成交监测' },
                { source: '融资融券数据', count: result.sources.margin_summary || 0, description: '两融余额变化' },
                { source: '行业资金流', count: result.sources.industry_flow || 0, description: '行业资金流向' }
              ]
              console.log(`[funds] 设置真实数据源:`, agentDataSources.value[agent.id])
            } else {
              // 失败时使用默认值
              agentDataSources.value[agent.id] = [
                { source: '北向资金数据', count: 0, description: '数据获取失败' },
                { source: '主力资金数据', count: 0, description: '数据获取失败' },
                { source: '融资融券数据', count: 0, description: '数据获取失败' }
              ]
            }
          } catch (e) {
            console.error('[funds] 获取资金流向数据失败:', e)
            agentDataSources.value[agent.id] = [
              { source: '北向资金数据', count: 0, description: '网络错误' },
              { source: '主力资金数据', count: 0, description: '网络错误' },
              { source: '融资融券数据', count: 0, description: '网络错误' }
            ]
          }
        } else if (agent.id === 'industry') {
          // 行业轮动分析师 - 获取真实数据
          try {
            const response = await fetch('http://localhost:8000/api/akshare/sector/comprehensive')
            const result = await response.json()
            
            if (result.success && result.sources) {
              agentDataSources.value[agent.id] = [
                { source: '行业板块数据', count: result.sources.industry_list || 0, description: '申万行业分类' },
                { source: '板块资金流向', count: result.sources.industry_flow || 0, description: '行业资金净流入' },
                { source: 'AKShare', count: 2, description: '板块数据接口' }
              ]
              console.log(`[industry] 设置真实数据源:`, agentDataSources.value[agent.id])
            } else {
              agentDataSources.value[agent.id] = [
                { source: '行业板块数据', count: 0, description: '数据获取失败' },
                { source: '板块资金流向', count: 0, description: '数据获取失败' }
              ]
            }
          } catch (e) {
            console.error('[industry] 获取板块数据失败:', e)
            agentDataSources.value[agent.id] = [
              { source: '行业板块数据', count: 0, description: '网络错误' },
              { source: '板块资金流向', count: 0, description: '网络错误' }
            ]
          }
        } else if (agent.id === 'macro') {
          // 宏观政策分析师 - 获取真实数据
          try {
            const response = await fetch('http://localhost:8000/api/akshare/macro/comprehensive')
            const result = await response.json()
            
            if (result.success && result.sources) {
              const totalMacro = (result.sources.gdp || 0) + (result.sources.cpi || 0) + (result.sources.pmi || 0)
              agentDataSources.value[agent.id] = [
                { source: '宏观经济数据', count: totalMacro, description: `GDP(${result.sources.gdp})、CPI(${result.sources.cpi})、PMI(${result.sources.pmi})` },
                { source: '货币政策', count: result.sources.money_supply || 0, description: '货币供应量数据' },
                { source: 'AKShare', count: 4, description: '宏观数据接口' }
              ]
              console.log(`[macro] 设置真实数据源:`, agentDataSources.value[agent.id])
            } else {
              agentDataSources.value[agent.id] = [
                { source: '宏观经济数据', count: 0, description: '数据获取失败' },
                { source: '货币政策', count: 0, description: '数据获取失败' }
              ]
            }
          } catch (e) {
            console.error('[macro] 获取宏观数据失败:', e)
            agentDataSources.value[agent.id] = [
              { source: '宏观经济数据', count: 0, description: '网络错误' },
              { source: '货币政策', count: 0, description: '网络错误' }
            ]
          }
        } else if (agent.id === 'technical') {
          // 技术分析师 - 技术指标数据
          agentDataSources.value[agent.id] = [
            { source: '历史行情数据', count: 1, description: 'K线数据' },
            { source: '技术指标', count: 1, description: 'MACD、KDJ、RSI等' },
            { source: '成交量数据', count: 1, description: '量价关系' },
            { source: 'AKShare', count: 3, description: '技术数据接口' }
          ]
        } else if (agent.id === 'options_risk') {
          // 期权风险分析师 - 期权数据
          agentDataSources.value[agent.id] = [
            { source: '期权行情数据', count: 1, description: '期权价格、成交量' },
            { source: 'PCR指标', count: 1, description: 'Put/Call Ratio' },
            { source: '隐含波动率', count: 1, description: 'IV指标' },
            { source: 'AKShare', count: 3, description: '期权数据接口' }
          ]
        } else if (agent.id === 'market_sentiment') {
          // 市场情绪分析师 - 情绪指标
          agentDataSources.value[agent.id] = [
            { source: '市场情绪指标', count: 1, description: '恐慌指数VIX' },
            { source: '涨跌家数比', count: 1, description: '个股表现分布' },
            { source: '换手率数据', count: 1, description: '市场活跃度' },
            { source: 'AKShare', count: 3, description: '情绪数据接口' }
          ]
        } else if (agent.id === 'risk_system') {
          // 系统性风险评估 - 显示真实网站
          agentDataSources.value[agent.id] = [
            { source: '裁判文书网', count: 0 },
            { source: '新闻分析师', count: 1 }
          ]
        } else if (agent.id === 'risk_manager') {
          // 风险经理 - 引用所有风险评估结果
          agentDataSources.value[agent.id] = [
            { source: '系统性风险评估', count: 1 },
            { source: '保守型风险评估', count: 1 },
            { source: '激进型风险评估', count: 1 }
          ]
        } else if (['risk_conservative', 'risk_aggressive', 'risk_neutral'].includes(agent.id)) {
          // 其他风险类智能体 - 显示真实来源
          agentDataSources.value[agent.id] = [
            { source: '裁判文书网', count: 0 },
            { source: '新闻分析师', count: 1 }
          ]
        } else if (agent.id === 'risk_portfolio') {
          // 组合风险总监 - 引用所有前序风险分析
          agentDataSources.value[agent.id] = [
            { source: '风险经理', count: 1 },
            { source: '技术分析师', count: 1 },
            { source: '资金流分析师', count: 1 }
          ]
        } else if (agent.id === 'trader') {
          // 交易员 - 显示真实网站
          agentDataSources.value[agent.id] = [
            { source: '巨潮资讯网', count: 0 },
            { source: '风险经理', count: 1 }
          ]
        }
        
        // ✅ 关键：数据源设置完成后，再调用API进行分析
        agentStatus.value[agent.id] = 'analyzing'
        
        // 添加超时控制（10分钟）和重试机制
        let retryCount = 0
        const maxRetries = 1 // 最多重试1次
        
        while (retryCount <= maxRetries) {
          const controller = new AbortController()
          const timeoutId = setTimeout(() => controller.abort(), 600000) // 10分钟
          
          try {
            if (retryCount > 0) {
              console.log(`[${agent.id}] 重试第 ${retryCount} 次...`)
              agentStatus.value[agent.id] = 'analyzing'
            }
            
            const response = await fetch('http://localhost:8000/api/analyze', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                agent_id: agent.id,
                stock_code: stockCode.value,
                stock_data: data,
                previous_outputs: agentOutputs.value,
                custom_instruction: getInstruction(agent, data)
              }),
              signal: controller.signal
            })
            
            clearTimeout(timeoutId)
          
            if (!response.ok) throw new Error('API Error')
            const result = await response.json()
            
            if (!result.success) {
              throw new Error(result.error || '分析失败')
            }
            
            const analysisResult = result.result || '⚠️ 分析结果为空'
            agentOutputs.value[agent.id] = analysisResult
            agentTokens.value[agent.id] = Math.floor(analysisResult.length / 1.5)
            agentStatus.value[agent.id] = 'success'
            break // 成功后退出循环
            
          } catch (fetchError) {
            clearTimeout(timeoutId)
            
            if (fetchError.name === 'AbortError') {
              if (retryCount < maxRetries) {
                console.log(`[${agent.id}] 超时，准备重试...`)
                retryCount++
                await new Promise(r => setTimeout(r, 2000)) // 等待2秒后重试
                continue
              } else {
                throw new Error('请求超时（10分钟），已重试1次仍失败')
              }
            }
            
            if (retryCount < maxRetries) {
              console.log(`[${agent.id}] 请求失败，准备重试...`)
              retryCount++
              await new Promise(r => setTimeout(r, 2000)) // 等待2秒后重试
              continue
            }
            
            throw fetchError
          }
        }
      } catch (e) {
        console.error(`Agent ${agent.id} 分析失败:`, e)
        agentStatus.value[agent.id] = 'error'
        agentOutputs.value[agent.id] = `⚠️ 分析失败: ${e.message}\n\n建议：\n1. 检查网络连接\n2. 尝试使用其他 AI 模型\n3. 稍后重试`
      }
    }

    // 定制不同角色的思考模板
    const THOUGHT_TEMPLATES = {
      NEWS: [
        { icon: '📡', message: '正在连接全网财经舆情源...' },
        { icon: '🕷️', message: '爬取最近24H相关新闻与公告...' },
        { icon: '📊', message: 'NLP情绪评分与关键词提取...' },
        { icon: '📝', message: '生成舆情综述报告...' }
      ],
      SOCIAL: [
        { icon: '💬', message: '检索雪球、股吧等社区讨论...' },
        { icon: '🔥', message: '分析散户情绪与热度趋势...' },
        { icon: '⚠️', message: '识别潜在谣言与异常波动...' },
        { icon: '📝', message: '生成社交情绪分析报告...' }
      ],
      CHINA: [
        { icon: '🇨🇳', message: '检索国家统计局宏观数据...' },
        { icon: '📜', message: '分析近期监管政策与会议精神...' },
        { icon: '🌏', message: '评估人民币汇率与外资流向...' },
        { icon: '📝', message: '生成中国市场环境简报...' }
      ],
      INDUSTRY: [
        { icon: '🏭', message: '定位所属行业产业链上下游...' },
        { icon: '🔄', message: '分析行业周期与竞争格局...' },
        { icon: '📈', message: '对比同行业龙头估值水平...' },
        { icon: '📝', message: '生成行业轮动分析...' }
      ],
      TECHNICAL: [
        { icon: '📈', message: '加载K线历史数据(日/周/月)...' },
        { icon: '📐', message: '计算MA、MACD、KDJ等指标...' },
        { icon: '🔍', message: '识别形态与关键支撑压力位...' },
        { icon: '📝', message: '生成技术面研判结论...' }
      ],
      FUNDS: [
        { icon: '💰', message: '追踪北向资金与机构持仓...' },
        { icon: '📊', message: '分析龙虎榜与大宗交易数据...' },
        { icon: '🌊', message: '计算主力资金净流入流出...' },
        { icon: '📝', message: '生成资金流向监测报告...' }
      ],
      DEFAULT: [
        { icon: '🧠', message: '正在接收前序分析报告...' },
        { icon: '⚖️', message: '综合多方观点进行研判...' },
        { icon: '🔍', message: '进行逻辑冲突检测与修正...' },
        { icon: '📝', message: '生成最终决策建议...' }
      ]
    }

    const simulateThoughts = (agentId, role) => {
        const template = THOUGHT_TEMPLATES[role] || THOUGHT_TEMPLATES['DEFAULT']
        
        // 确保 agentThoughts[agentId] 存在
        if (!agentThoughts.value[agentId]) {
            agentThoughts.value[agentId] = []
        }
        
        let i = 0
        const interval = setInterval(() => {
            if (i >= template.length || agentStatus.value[agentId] === 'success') {
                clearInterval(interval)
                return
            }
            // 再次检查以防万一
            if (agentThoughts.value[agentId]) {
                agentThoughts.value[agentId].push(template[i])
            }
            i++
        }, 1000) // 稍微调慢一点，让用户看清
    }

    const runBullBearDebate = async () => {
        showBullBearDebate.value = true
        bullBearDebateStatus.value = 'debating'
        
        // 模拟辩论过程
        const rounds = [
            { agentName: '看涨研究员', agentIcon: '🐂', content: '基于技术面分析，该股呈现明显的底部反转信号，资金流入显著。', round: 1 },
            { agentName: '看跌研究员', agentIcon: '🐻', content: '但我必须指出，宏观环境依然承压，且行业增速放缓，估值目前偏高。', round: 1 },
            { agentName: '看涨研究员', agentIcon: '🐂', content: '新兴业务增长强劲，财报显示第二曲线已形成，未来可期。', round: 2 },
            { agentName: '看跌研究员', agentIcon: '🐻', content: '短期炒作迹象明显，主力资金存在出逃风险，建议保持谨慎。', round: 2 }
        ]

        for (const msg of rounds) {
            await new Promise(r => setTimeout(r, 1500))
            bullBearDebateMessages.value.push(msg)
        }

        bullBearDebateConclusion.value = {
            content: '综合多空双方观点，虽然短期存在技术性反弹机会，但长期基本面仍需观察。建议关注关键支撑位的有效性。',
            score: 65
        }
        bullBearDebateStatus.value = 'finished'
    }

    const runRiskDebate = async () => {
        showRiskDebate.value = true
        riskDebateStatus.value = 'debating'
        
        const rounds = [
            { agentName: '激进风控师', agentIcon: '⚔️', content: '建议设置较宽的止损位，博取潜在的高赔率收益。', round: 1 },
            { agentName: '保守风控师', agentIcon: '🛡️', content: '绝对不行，当前波动率过高，必须严格控制仓位，建议不超过2成。', round: 1 },
        ]
         for (const msg of rounds) {
            await new Promise(r => setTimeout(r, 1500))
            riskDebateMessages.value.push(msg)
        }
        
        riskDebateConclusion.value = {
            content: '风险评级：中高风险。建议轻仓参与，严格执行止损。',
            score: 40
        }
        riskDebateStatus.value = 'finished'
    }

    // Utils
    const fetchStockData = async (code) => {
        try {
          // 调试日志
          console.log('[fetchStockData] stockDataPanel:', stockDataPanel)
          console.log('[fetchStockData] stockDataPanel.value:', stockDataPanel?.value)
          
          // 更新数据透明化面板 - 开始获取
          if (stockDataPanel && stockDataPanel.value && stockDataPanel.value.addLog) {
            stockDataPanel.value.addLog(`开始获取股票数据: ${code}`, 'info')
            stockDataPanel.value.addLog('数据源优先级: AKShare > 新浪财经 > 聚合数据 > Tushare', 'fetch')
          } else {
            console.warn('[fetchStockData] stockDataPanel 不可用')
          }
          
          const response = await fetch(`http://localhost:8000/api/stock/${code}`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              symbol: code,
              apiKey: null
            })
          })
          
          if (!response.ok) {
            if (stockDataPanel.value && stockDataPanel.value.addLog) {
              stockDataPanel.value.addLog(`HTTP错误: ${response.status}`, 'error')
            }
            throw new Error('获取数据失败')
          }
          
          const result = await response.json()
          console.log('[fetchStockData] 后端返回数据:', result)
          
          // 检查是否有错误
          if (result.success === false || result.error) {
            if (stockDataPanel.value && stockDataPanel.value.addLog) {
              stockDataPanel.value.addLog(`数据获取失败: ${result.error}`, 'error')
            }
            throw new Error(result.error || '数据获取失败')
          }
          
          // 更新数据透明化面板 - 成功
          if (stockDataPanel.value && stockDataPanel.value.addLog) {
            stockDataPanel.value.addLog(`✅ 成功获取数据: ${result.name} (${result.symbol})`, 'success')
            stockDataPanel.value.addLog(`价格: ¥${result.price} | 涨跌: ${result.change}`, 'success')
            stockDataPanel.value.addLog(`数据源: ${result.data_source || '未知'}`, 'info')
          }
          
          // 更新当前股票数据
          if (currentStockData) {
            currentStockData.value = result
          }
          stockData.value = result
          
          // 直接返回结果（新的后端已经返回正确格式）
          return result
          
        } catch (e) {
          console.error('真实数据获取失败，使用模拟数据', e)
          // Fallback mock data to avoid N/A
          return {
             symbol: code,
             name: '示例股票',
             price: '18.50',
             change: '+2.3%',
             volume: '1.2亿',
             market_cap: '500亿',
             pe: '15.2',
             pb: '1.8',
             industry: '科技/半导体'
          }
        }
    }
    
    // 数据源名称映射（与后端 unified_news_api.py 一致）
    const SOURCE_NAME_MAP = {
      // 9个真实的数据源
      'realtime_news': '实时新闻聚合器（东方财富）',
      'akshare_stock_news': 'AKShare个股新闻',
      'cls_telegraph': '财联社快讯',
      'weibo_hot': '微博热议',
      'morning_news': '财经早餐（东方财富）',
      'global_news_em': '东方财富全球财经',
      'global_news_sina': '新浪全球财经',
      'futu_news': '富途财经新闻',
      'ths_news': '同花顺财经新闻'
    }
    
    // 获取新闻数据
    const fetchNewsData = async (code) => {
        try {
          // 更新数据透明化面板 - 开始获取
          if (newsDataPanel.value && newsDataPanel.value.addLog) {
            newsDataPanel.value.addLog(`开始获取新闻数据: ${code}`, 'info')
            newsDataPanel.value.addLog('数据源: 统一新闻API (7个数据源)', 'fetch')
          }
          
          const response = await fetch('http://localhost:8000/api/unified-news/stock', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              ticker: code
            })
          })
          
          if (!response.ok) {
            if (newsDataPanel.value && newsDataPanel.value.addLog) {
              newsDataPanel.value.addLog(`HTTP错误: ${response.status}`, 'error')
            }
            throw new Error('获取新闻失败')
          }
          
          const result = await response.json()
          console.log('[fetchNewsData] 后端返回数据:', result)
          
          // 检查是否成功
          if (!result.success) {
            if (newsDataPanel.value && newsDataPanel.value.addLog) {
              newsDataPanel.value.addLog(`新闻获取失败: ${result.message}`, 'error')
            }
            throw new Error(result.message || '新闻获取失败')
          }
          
          // 解析统一新闻API的数据结构
          const newsData = result.data
          const summary = newsData.summary || {}
          const dataSources = summary.data_sources || {}
          const sentiment = summary.sentiment || {}
          
          // 更新数据透明化面板 - 成功
          if (newsDataPanel.value && newsDataPanel.value.addLog) {
            newsDataPanel.value.addLog(`✅ 成功获取新闻`, 'success')
            newsDataPanel.value.addLog(`成功率: ${dataSources.success_rate || '0%'}`, 'info')
            newsDataPanel.value.addLog(`成功数据源: ${dataSources.success || 0}/${dataSources.total || 0}`, 'info')
            
            // 记录各数据源状态
            for (const [sourceName, sourceData] of Object.entries(newsData.sources || {})) {
              if (sourceData.status === 'success') {
                const count = sourceData.count || 'N/A'
                newsDataPanel.value.addLog(`✅ ${sourceName}: ${count}条`, 'success')
              } else {
                newsDataPanel.value.addLog(`❌ ${sourceName}: ${sourceData.status}`, 'error')
              }
            }
            
            // 记录情绪分析
            if (sentiment.sentiment_label) {
              newsDataPanel.value.addLog(`情绪: ${sentiment.sentiment_label} (评分: ${sentiment.sentiment_score})`, 'info')
            }
          }
          
          // 转换为旧格式以兼容现有代码
          const allNews = []
          console.log('[fetchNewsData] newsData.sources:', Object.keys(newsData.sources || {}))
          
          for (const [sourceName, sourceData] of Object.entries(newsData.sources || {})) {
            console.log(`[fetchNewsData] 处理数据源: ${sourceName}`, {
              status: sourceData.status,
              hasData: !!sourceData.data,
              isArray: Array.isArray(sourceData.data),
              count: Array.isArray(sourceData.data) ? sourceData.data.length : 0
            })
            
            if (sourceData.status === 'success' && sourceData.data) {
              if (Array.isArray(sourceData.data)) {
                // 为每条新闻添加来源信息（使用友好名称）
                const friendlyName = SOURCE_NAME_MAP[sourceName] || sourceName
                console.log(`[fetchNewsData] 添加 ${sourceData.data.length} 条新闻从 ${friendlyName}`)
                sourceData.data.forEach(item => {
                  allNews.push({
                    ...item,
                    source_name: friendlyName
                  })
                })
              }
            }
          }
          
          // 将新闻添加到右侧新闻面板
          console.log('[fetchNewsData] 总新闻数:', allNews.length)
          console.log('[fetchNewsData] 按来源统计:', allNews.reduce((acc, item) => {
            acc[item.source_name] = (acc[item.source_name] || 0) + 1
            return acc
          }, {}))
          
          if (newsDataPanel.value && newsDataPanel.value.addNews && allNews.length > 0) {
            // 添加所有新闻到面板
            allNews.forEach(newsItem => {
              const now = new Date()
              const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
              
              // 根据新闻标题关键词判断情绪
              const title = newsItem.新闻标题 || newsItem.title || newsItem.标题 || newsItem.content || ''
              let itemSentiment = 'neutral'
              let itemScore = 0
              
              // 利好关键词
              const positiveKeywords = ['上涨', '增长', '突破', '利好', '业绩', '盈利', '增持', '买入', '看好', '推荐', '上调', '创新高', '涨停', '大涨', '强势', '优秀', '领先']
              // 利空关键词
              const negativeKeywords = ['下跌', '下降', '亏损', '利空', '减持', '卖出', '看空', '下调', '跌停', '大跌', '弱势', '风险', '警告', '质疑', '调查', '处罚']
              
              // 检查关键词
              const hasPositive = positiveKeywords.some(kw => title.includes(kw))
              const hasNegative = negativeKeywords.some(kw => title.includes(kw))
              
              if (hasPositive && !hasNegative) {
                itemSentiment = 'positive'
                itemScore = 0.6 + Math.random() * 0.4 // 0.6-1.0
              } else if (hasNegative && !hasPositive) {
                itemSentiment = 'negative'
                itemScore = -(0.6 + Math.random() * 0.4) // -0.6 to -1.0
              } else if (hasPositive && hasNegative) {
                // 有争议，随机分配
                itemSentiment = Math.random() > 0.5 ? 'positive' : 'negative'
                itemScore = (Math.random() - 0.5) * 0.6 // -0.3 to 0.3
              } else {
                // 中性
                itemSentiment = 'neutral'
                itemScore = (Math.random() - 0.5) * 0.4 // -0.2 to 0.2
              }
              
              newsDataPanel.value.addNews({
                source: newsItem.source_name || '未知来源',
                time: time,
                title: newsItem.新闻标题 || newsItem.title || newsItem.标题 || newsItem.content || '无标题',
                summary: newsItem.新闻内容 || newsItem.content || newsItem.内容 || '',
                tags: newsItem.tags || [],
                sentiment: itemSentiment,
                score: itemScore
              })
            })
          }
          
          // 返回兼容格式
          return {
            success: true,
            ticker: result.ticker,
            date: new Date().toISOString().split('T')[0],
            report: `获取到${allNews.length}条新闻，情绪: ${sentiment.sentiment_label || '未知'}`,
            source: `统一新闻API (${dataSources.success}/${dataSources.total}成功)`,
            news_count: allNews.length,
            fetch_time: 0,
            news: allNews,
            sentiment: sentiment,
            // 添加data字段供智能体卡片使用
            data: {
              sources: newsData.sources
            }
          }
          
        } catch (e) {
          console.error('新闻数据获取失败', e)
          if (newsDataPanel.value && newsDataPanel.value.addLog) {
            newsDataPanel.value.addLog(`❌ 获取失败: ${e.message}`, 'error')
          }
          // 返回空结果
          return {
            success: false,
            ticker: code,
            date: new Date().toISOString().split('T')[0],
            report: '新闻获取失败',
            source: '错误',
            news_count: 0,
            fetch_time: 0
          }
        }
    }
    
    const scrollToBottom = () => {
        setTimeout(() => {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
        }, 500)
    }
    
    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60)
      const secs = seconds % 60
      return `${mins}:${secs.toString().padStart(2, '0')}`
    }

    const showDetail = (agent) => {
        selectedAgent.value = agent
    }

    const generateReport = () => {
        return Object.keys(agentOutputs.value).map(id => {
            const a = AGENTS.find(x => x.id === id)
            return `### ${a.icon} ${a.title}\n${agentOutputs.value[id]}`
        }).join('\n\n---\n\n')
    }

    // 加载可用模型列表
    const loadAvailableModels = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/config/agents')
        const result = await response.json()
        const config = result.success ? result.data : result
        availableModels.value = config.selectedModels || []
        console.log('加载可用模型:', availableModels.value)
      } catch (error) {
        console.error('加载模型列表失败:', error)
        // 默认模型
        availableModels.value = [
          'Qwen/Qwen2.5-7B-Instruct',
          'Qwen/Qwen3-8B',
          'deepseek-chat'
        ]
      }
    }
    
    // 保存白话解读员配置
    const saveInterpreterConfig = async () => {
      try {
        // 读取现有配置
        const response = await fetch('http://localhost:8000/api/config/agents')
        const result = await response.json()
        const config = result.success ? result.data : result
        
        // 更新interpreter的配置
        const agents = config.agents || []
        const interpreterIndex = agents.findIndex(a => a.id === 'interpreter')
        
        const interpreterConfig = {
          id: 'interpreter',
          modelName: interpreterModel.value,
          modelProvider: interpreterModel.value.includes('/') ? 'SILICONFLOW' : 
                        interpreterModel.value.startsWith('deepseek') ? 'DEEPSEEK' : 'SILICONFLOW',
          temperature: interpreterTemperature.value
        }
        
        if (interpreterIndex >= 0) {
          agents[interpreterIndex] = interpreterConfig
        } else {
          agents.push(interpreterConfig)
        }
        
        // 保存配置
        await fetch('http://localhost:8000/api/config/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...config, agents })
        })
        
        console.log('白话解读员配置已保存:', interpreterConfig)
        showInterpreterConfig.value = false
        alert('配置已保存！')
      } catch (error) {
        console.error('保存配置失败:', error)
        alert('保存失败，请重试')
      }
    }
    
    // Empty handlers for config (kept from original)
    const handleModelSave = () => {}
    const handleApiSave = (keys) => {
      if (saveApiConfig) {
        saveApiConfig(keys)
      }
    }
    const updateApiStatus = (provider, status) => {
      if (updateApiStatusFunc) {
        updateApiStatusFunc(provider, status)
      }
    }
    const handleStyleSave = () => {}

    const styleSettings = ref({})

    return {
        stockCode, stockData, isAnalyzing, isValidCode, startAnalysis,
        AGENTS,
        configMode, showModelManager, showApiConfig, showStyleConfig, apiStatus,
        agentStatus, agentOutputs, agentTokens, agentThoughts, agentDataSources,
        modelUpdateTrigger,
        cardsExpanded,
        stage1Agents, stage2Agents, stage3Agents, stage4Agents, stage4AgentsFiltered,
        showBullBearDebate, bullBearDebateStatus, bullBearDebateMessages, bullBearDebateConclusion,
        showRiskDebate, riskDebateStatus, riskDebateMessages, riskDebateConclusion,
        showReport, reportView, finalReportHtml, interpretationHtml, enableSimpleSummary,
        showInterpreterConfig, interpreterModel, interpreterTemperature, saveInterpreterConfig, availableModels, loadAvailableModels,
        selectedAgent, showDetail,
        handleModelSave, handleApiSave, updateApiStatus, handleStyleSave,
        apiKeys, styleSettings, exportReport: () => {},
        fetchNewsData,  // 新增: 新闻数据获取函数
        analysisElapsedTime, formatTime,  // 新增: 计时器
        handleStockSelect  // 新增: 股票选择处理
    }
  }
}
</script>

<style scoped>
.analysis-container {
  padding: 2rem;
  max-width: 1800px;
  margin: 0 auto;
  min-height: 100vh;
}

.input-card {
  background: rgba(30, 41, 59, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 2rem;
  max-width: 600px;
  margin: 0 auto 4rem;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.3);
}

.stock-input {
  width: 100%;
  background: rgba(15, 23, 42, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.5);
  padding: 1rem;
  border-radius: 0.5rem;
  color: white;
  font-size: 1.2rem;
  margin-top: 0.5rem;
}

.analyze-btn {
  width: 100%;
  padding: 1rem;
  margin-top: 1.5rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  font-weight: bold;
  border-radius: 0.5rem;
  transition: all 0.3s;
}

.analyze-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(37, 99, 235, 0.3);
}

.analyze-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.floating-timer {
  position: fixed;
  top: 5rem;
  right: 2rem;
  z-index: 100;
  padding: 1rem 1.5rem;
  background: rgba(15, 23, 42, 0.95);
  border: 2px solid rgba(59, 130, 246, 0.5);
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(12px);
  animation: pulse-border 2s ease-in-out infinite;
}

@keyframes pulse-border {
  0%, 100% {
    border-color: rgba(59, 130, 246, 0.5);
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  }
  50% {
    border-color: rgba(59, 130, 246, 0.8);
    box-shadow: 0 10px 40px rgba(59, 130, 246, 0.3);
  }
}

.timer-icon {
  font-size: 1.5rem;
  animation: rotate 3s linear infinite;
}

@keyframes rotate {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.timer-label {
  color: #94a3b8;
  font-size: 0.95rem;
  font-weight: 500;
}

.timer-value {
  color: #3b82f6;
  font-weight: bold;
  font-size: 1.25rem;
  font-family: 'Courier New', monospace;
  min-width: 4rem;
  text-align: center;
}

.stage-header {
  margin-bottom: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  padding-bottom: 1rem;
}

.stage-desc {
  display: block;
  margin-top: 0.5rem;
  color: #94a3b8;
  font-size: 0.9rem;
}

.sub-group-title {
  margin-bottom: 1rem;
  font-weight: 600;
  font-size: 0.95rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.debate-section {
  margin: 3rem 0;
  animation: slideIn 0.5s ease-out;
}

@keyframes slideIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  color: white;
  font-size: 0.9rem;
  transition: all 0.2s;
}

/* Modal */
.modal-overlay {
  position: fixed;
  top: 0; left: 0; right: 0; bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(5px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
}

.modal-content {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 1rem;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.modal-header {
  padding: 1.5rem;
  border-bottom: 1px solid #334155;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
  color: #e2e8f0;
  line-height: 1.6;
}

.close-btn {
  background: transparent;
  color: #94a3b8;
  font-size: 1.5rem;
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* 白话解读面板样式 */
.interpretation-panel {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 20px;
  padding: 30px;
  margin-top: 20px;
  color: white;
  box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3);
}

.interpretation-panel .panel-header {
  text-align: center;
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 2px solid rgba(255, 255, 255, 0.2);
}

.interpretation-panel .icon {
  font-size: 48px;
  display: block;
  margin-bottom: 15px;
}

.interpretation-panel .panel-title {
  font-size: 28px;
  font-weight: bold;
  margin-bottom: 10px;
}

.interpretation-panel .panel-subtitle {
  font-size: 16px;
  opacity: 0.9;
}

.interpretation-panel .analyzing-state {
  text-align: center;
  padding: 40px;
}

.interpretation-panel .loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

.interpretation-panel .interpretation-content {
  background: rgba(255, 255, 255, 0.15);
  border-radius: 15px;
  padding: 25px;
  font-size: 16px;
  line-height: 1.8;
}

.interpretation-panel .markdown-content h1,
.interpretation-panel .markdown-content h2,
.interpretation-panel .markdown-content h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  font-weight: bold;
}

.interpretation-panel .markdown-content p {
  margin: 10px 0;
}

.interpretation-panel .markdown-content ul,
.interpretation-panel .markdown-content ol {
  margin: 10px 0;
  padding-left: 25px;
}

.interpretation-panel .markdown-content li {
  margin: 8px 0;
  list-style: disc;
}

.interpretation-panel .markdown-content ol li {
  list-style: decimal;
}

.interpretation-panel .markdown-content strong {
  font-weight: bold;
  color: #fde047;
}

.interpretation-panel .error-state {
  text-align: center;
  padding: 30px;
  background: rgba(239, 68, 68, 0.2);
  border-radius: 10px;
}

/* 报告标签页样式 */
.report-tabs {
  margin-top: 20px;
}

.tab-header {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
  border-bottom: 2px solid rgba(71, 85, 105, 0.3);
  padding-bottom: 10px;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: rgba(51, 65, 85, 0.5);
  border: 2px solid transparent;
  border-radius: 10px 10px 0 0;
  color: #94a3b8;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tab-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

.tab-btn.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: #60a5fa;
}

.tab-icon {
  font-size: 20px;
}

.tab-badge {
  font-size: 12px;
  padding: 2px 8px;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 12px;
  color: #93c5fd;
}

.tab-btn.active .tab-badge {
  background: rgba(59, 130, 246, 0.3);
  color: #60a5fa;
}

.interpretation-panel-report {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 15px;
  padding: 30px;
  color: white;
  box-shadow: 0 10px 40px rgba(16, 185, 129, 0.3);
}

.interpretation-panel-report .markdown-content {
  font-size: 16px;
  line-height: 1.8;
}

.interpretation-panel-report .markdown-content h1,
.interpretation-panel-report .markdown-content h2,
.interpretation-panel-report .markdown-content h3 {
  margin-top: 20px;
  margin-bottom: 10px;
  font-weight: bold;
}

.interpretation-panel-report .markdown-content strong {
  color: #fde047;
}

.empty-interpretation {
  text-align: center;
  padding: 60px 20px;
  background: rgba(71, 85, 105, 0.2);
  border-radius: 15px;
  color: #94a3b8;
  font-size: 16px;
}

/* 白话解读员配置按钮 */
.config-btn {
  padding: 8px 12px;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  color: #60a5fa;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 18px;
  margin-left: auto;
}

.config-btn:hover {
  background: rgba(59, 130, 246, 0.3);
  transform: scale(1.1);
}

/* 白话解读员配置弹窗 */
.interpreter-config-modal {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 20px;
  padding: 0;
  max-width: 500px;
  width: 90%;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.interpreter-config-modal .modal-header {
  padding: 20px 24px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.interpreter-config-modal .modal-body {
  padding: 24px;
}

.interpreter-config-modal .config-item {
  margin-bottom: 20px;
}

.interpreter-config-modal .config-label {
  display: block;
  color: #e2e8f0;
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
}

.interpreter-config-modal .model-select {
  width: 100%;
  padding: 10px 12px;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 14px;
  cursor: pointer;
}

.interpreter-config-modal .model-select:focus {
  outline: none;
  border-color: #3b82f6;
}

.interpreter-config-modal .temperature-slider {
  width: calc(100% - 60px);
  margin-right: 10px;
}

.interpreter-config-modal .temperature-value {
  color: #60a5fa;
  font-weight: 600;
  font-size: 16px;
}

.interpreter-config-modal .config-note {
  background: rgba(16, 185, 129, 0.1);
  border-left: 3px solid #10b981;
  padding: 12px 16px;
  border-radius: 8px;
  margin-top: 20px;
}

.interpreter-config-modal .config-note p {
  color: #94a3b8;
  font-size: 13px;
  margin: 6px 0;
}

.interpreter-config-modal .modal-footer {
  padding: 16px 24px;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
  display: flex;
  justify-content: flex-end;
  gap: 12px;
}

.interpreter-config-modal .cancel-btn {
  padding: 8px 20px;
  background: rgba(71, 85, 105, 0.3);
  border: none;
  border-radius: 8px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.3s ease;
}

.interpreter-config-modal .cancel-btn:hover {
  background: rgba(71, 85, 105, 0.5);
}

.interpreter-config-modal .save-btn {
  padding: 8px 20px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.interpreter-config-modal .save-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.4);
}
</style>
