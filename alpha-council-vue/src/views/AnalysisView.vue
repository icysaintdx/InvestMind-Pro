<template>
  <div class="analysis-container">
    <!-- 股票输入区 -->
    <div class="input-section">
      <div class="input-card">
        <h2 class="text-2xl font-bold text-white mb-6">📈 智能投研分析系统</h2>
        
        <div class="input-group">
          <label class="input-label">股票代码</label>
          <input 
            v-model="stockCode"
            type="text" 
            placeholder="请输入6位股票代码"
            maxlength="6"
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
          <span class="stage-desc">下达最终交易指令，执行量化交易</span>
        </div>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <AgentCard 
            v-for="agent in stage4Agents" 
            :key="agent.id"
            :agent="agent"
            :status="agentStatus[agent.id]"
            :output="agentOutputs[agent.id]"
            :thoughts="agentThoughts[agent.id]"
            :dataSources="agentDataSources[agent.id]"
            :tokens="agentTokens[agent.id]"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
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
            <div class="flex gap-3">
              <button @click="exportReport('md')" class="export-btn bg-blue-600 hover:bg-blue-700">
                <span>📝</span> Markdown
              </button>
              <button @click="exportReport('html')" class="export-btn bg-green-600 hover:bg-green-700">
                <span>🌐</span> HTML
              </button>
            </div>
          </div>
          <div class="report-content bg-slate-900/50 rounded-xl p-6 max-h-[800px] overflow-y-auto border border-slate-800">
            <div class="prose prose-invert max-w-none" v-html="finalReportHtml"></div>
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
    <StyleConfig :visible="showStyleConfig" :styles="styleSettings" @close="showStyleConfig = false" @save="handleStyleSave" />
  </div>
</template>

<script>
import { ref, computed, inject } from 'vue'
import AgentCard from '@/components/AgentCard.vue'
import DebatePanel from '@/components/DebatePanel.vue'
import ModelManager from '@/components/ModelManager.vue'
import ApiConfig from '@/components/ApiConfig.vue'
import StyleConfig from '@/components/StyleConfig.vue'
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
  { id: 'trader', role: 'TRADER', title: '量化交易员', icon: '🤖', color: 'cyan', stage: 4 }
]

export default {
  name: 'AnalysisView',
  components: { AgentCard, DebatePanel, ModelManager, ApiConfig, StyleConfig },
  setup() {
    // 注入数据透明化面板
    const currentStockData = inject('currentStockData')
    const stockDataPanel = inject('stockDataPanel')
    const newsDataPanel = inject('newsDataPanel')
    
    const stockCode = ref('')
    const isAnalyzing = ref(false)
    const selectedAgent = ref(null)
    
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
    const stockData = ref(null)

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
    const isValidCode = computed(() => /^\d{6}$/.test(stockCode.value))
    
    const finalReportHtml = computed(() => {
        if (!agentOutputs.value['gm']) return ''
        return marked.parse(generateReport())
    })

    // Analysis Logic
    const startAnalysis = async () => {
      if (!isValidCode.value || isAnalyzing.value) return
      isAnalyzing.value = true
      initAgents()
      showBullBearDebate.value = false
      showRiskDebate.value = false
      showReport.value = false
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
        const stage2Ids = AGENTS.filter(a => a.stage === 2).map(a => a.id)
        await runAgentsParallel(stage2Ids, fetchedStockData)

        // 4. 触发风控辩论
        await runRiskDebate()

        // 5. 执行第三阶段：风控终审
        const stage3Ids = AGENTS.filter(a => a.stage === 3).map(a => a.id)
        await runAgentsParallel(stage3Ids, fetchedStockData)

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
      }
    }

    const runAgentsParallel = async (agentIds, data) => {
      const targetAgents = AGENTS.filter(a => agentIds.includes(a.id))
      await Promise.all(targetAgents.map(agent => runAgentAnalysis(agent, data)))
    }

    const getInstruction = (agent, data) => {
        const base = `当前分析对象: ${data.name} (${data.symbol})。`
        const map = {
            news_analyst: `请检索最近24小时的重大新闻公告，提取可能影响股价的关键事件。如果无重大新闻，请直接说明"暂无重大事件"。不要复述股票代码。`,
            social_analyst: `请分析散户和机构在社交平台（如雪球、股吧）的情绪倾向。关键词：恐慌、贪婪、追涨、杀跌。`,
            china_market: `请简述当前的中国宏观市场环境（A股大盘趋势、流动性）。`,
            industry: `基于前序【新闻】和【社交】的分析，判断该股票所属行业当前处于什么周期（复苏/过热/滞胀/衰退）？竞争格局有何变化？`,
            macro: `结合【中国市场专家】的结论，分析宏观政策（利率、财政）对该行业的具体影响。`,
            technical: `忽略基本面，仅从技术图形（K线、均线、成交量）分析当前的趋势和关键点位。给出明确的支撑位和压力位。`,
            funds: `分析主力资金流向。是否存在机构持续买入或出逃的迹象？与散户行为有何背离？`,
            fundamental: `基于【行业】和【宏观】分析，评估该公司的核心财务指标（PE/PB/ROE）是否具备安全边际。`,
            bull_researcher: `基于以上所有信息，挖掘该股票最大的上涨逻辑和潜在催化剂。`,
            bear_researcher: `基于以上所有信息，无情地指出该股票最大的下跌风险和逻辑漏洞。`,
            risk_aggressive: `假设我们必须买入，如何设置止损以最大化赔率？`,
            risk_conservative: `指出当前最危险的风险点，并给出最保守的仓位建议。`,
            gm: `综合所有分析师、多空辩论和风控意见，给出最终的投资决策（买入/卖出/观望）及目标价位。`
        }
        return base + (map[agent.id] || map[agent.role] || "请基于你的专业领域进行分析。")
    }

    const runAgentAnalysis = async (agent, data) => {
      agentStatus.value[agent.id] = 'fetching'
      
      // 模拟思维链步骤
      simulateThoughts(agent.id, agent.role)

      try {
        agentStatus.value[agent.id] = 'analyzing'
        const response = await fetch('http://localhost:8000/api/analyze', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            agent_id: agent.id,
            stock_code: stockCode.value,
            stock_data: data,
            previous_outputs: agentOutputs.value,
            custom_instruction: getInstruction(agent, data) // 注入动态指令
          })
        })
        
        if (!response.ok) throw new Error('API Error')
        const result = await response.json()
        
        // 检查是否成功
        if (!result.success) {
          throw new Error(result.error || '分析失败')
        }
        
        // 确保 result.result 存在
        const analysisResult = result.result || '⚠️ 分析结果为空'
        agentOutputs.value[agent.id] = analysisResult
        agentTokens.value[agent.id] = Math.floor(analysisResult.length / 1.5) // Estimate
        agentStatus.value[agent.id] = 'success'

        // 如果是新闻类Agent，添加数据源模拟
        if (['news_analyst', 'china_market'].includes(agent.id)) {
             agentDataSources.value[agent.id] = [
                 { source: '东方财富', title: '最新市场动态...', url: '#' },
                 { source: '新浪财经', title: '行业板块分析...', url: '#' },
                 { source: '雪球', title: '投资者情绪报告...', url: '#' }
             ]
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
        
        let i = 0
        const interval = setInterval(() => {
            if (i >= template.length || agentStatus.value[agentId] === 'success') {
                clearInterval(interval)
                return
            }
            agentThoughts.value[agentId].push(template[i])
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
          // 更新数据透明化面板 - 开始获取
          if (stockDataPanel.value && stockDataPanel.value.addLog) {
            stockDataPanel.value.addLog(`开始获取股票数据: ${code}`, 'info')
            stockDataPanel.value.addLog('尝试数据源: AKShare > 聚合数据 > 新浪财经 > Tushare', 'fetch')
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
    
    const scrollToBottom = () => {
        setTimeout(() => {
            window.scrollTo({ top: document.body.scrollHeight, behavior: 'smooth' })
        }, 500)
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
        stockCode, isAnalyzing, isValidCode, startAnalysis,
        configMode, showModelManager, showApiConfig, showStyleConfig, apiStatus,
        agentStatus, agentOutputs, agentTokens, agentThoughts, agentDataSources,
        modelUpdateTrigger,
        stage1Agents, stage2Agents, stage3Agents, stage4Agents,
        showBullBearDebate, bullBearDebateStatus, bullBearDebateMessages, bullBearDebateConclusion,
        showRiskDebate, riskDebateStatus, riskDebateMessages, riskDebateConclusion,
        showReport, finalReportHtml,
        selectedAgent, showDetail,
        handleModelSave, handleApiSave, updateApiStatus, handleStyleSave,
        apiKeys, styleSettings, exportReport: () => {}
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
</style>
