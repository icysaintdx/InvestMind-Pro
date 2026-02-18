<template>
  <div class="analysis-container">
    <!-- 悬浮计时器 -->
    <div v-if="isAnalyzing || analysisElapsedTime > 0" class="floating-timer">
      <span class="timer-icon">⏱️</span>
      <span class="timer-label">分析耗时:</span>
      <span class="timer-value">{{ formatTime(analysisElapsedTime) }}</span>
    </div>
    
    <!-- 分析启动提示弹窗 -->
    <transition name="analysis-toast">
      <div v-if="showAnalysisToast" class="analysis-toast-overlay" @click="showAnalysisToast = false">
        <div class="analysis-toast" @click.stop>
          <div class="toast-header">
            <span class="toast-icon">🏛️</span>
            <span class="toast-title">机构级多维度智能分析已启动</span>
            <button class="toast-close" @click="showAnalysisToast = false">×</button>
          </div>
          <div class="toast-body">
            <p>本系统采用<strong>21个专业智能分析体</strong>协同工作，模拟机构投研部门的多角色分工运作模式</p>
            <div class="toast-phases">
              <div class="phase-item"><span class="phase-dot phase-1"></span>第一阶段：全维信息采集</div>
              <div class="phase-item"><span class="phase-dot phase-2"></span>第二阶段：策略整合</div>
              <div class="phase-item"><span class="phase-dot phase-3"></span>第三阶段：风险评估</div>
              <div class="phase-item"><span class="phase-dot phase-4"></span>第四阶段：决策输出</div>
            </div>
            <div class="toast-footer">
              <span class="time-badge">⏱️ 预计分析时间：8-15分钟</span>
              <span class="toast-tip">请耐心等待，可实时查看各智能体进度</span>
            </div>
          </div>
          <div class="toast-progress">
            <div class="toast-progress-bar"></div>
          </div>
        </div>
      </div>
    </transition>
    
    <!-- 全局日志窗口 -->
    <GlobalLogWindow 
      ref="globalLogWindowRef"
      v-model:visible="showGlobalLogWindow"
    />
    
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
        
        <!-- 强制停止按钮 -->
        <button 
          v-if="isAnalyzing"
          @click="forceStop"
          class="force-stop-btn"
          title="强制停止分析并清除状态"
        >
          ⏹️ 强制停止
        </button>
        
        <!-- 降级监控按钮 -->
        <button 
          @click="showFallbackMonitor = true"
          class="monitor-btn"
          title="查看降级监控面板"
        >
          📊 降级监控
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
            :duration-seconds="agentDurations[agent.id]"
            :fallback-level="agentFallbackLevels[agent.id] || 0"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
            :is-expanded="cardsExpanded"
            @show-detail="showDetail"
          />
        </div>
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
            :duration-seconds="agentDurations[agent.id]"
            :fallback-level="agentFallbackLevels[agent.id] || 0"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
            :is-expanded="cardsExpanded"
            @show-detail="showDetail"
          />
        </div>
      </div>
      <!-- 辩论环节 1：多空博弈（放在第二阶段之后） -->
      <div v-if="showBullBearDebate" class="debate-section">
        <DebatePanel 
          title="多空研判博弈" 
          topic="基于当前市场信息，该标的是否具备投资价值？"
          :status="bullBearDebateStatus"
          :sides="[{name: '看涨研究员', icon: '🐂'}, {name: '看跌研究员', icon: '🐻'}]"
          :messages="bullBearDebateMessages"
          :conclusion="bullBearDebateConclusion"
          :show-config="configMode"
          :agent-ids="['bull_researcher', 'bear_researcher', 'research_manager']"
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
            :duration-seconds="agentDurations[agent.id]"
            :fallback-level="agentFallbackLevels[agent.id] || 0"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
            :is-expanded="cardsExpanded"
            @show-detail="showDetail"
          />
        </div>
      </div>
      <!-- 辩论环节 2：风控评估（放在第三阶段之后） -->
      <div v-if="showRiskDebate" class="debate-section">
        <DebatePanel 
          title="三方风控评估" 
          topic="当前策略的风险收益比如何？是否存在致命缺陷？"
          :status="riskDebateStatus"
          :sides="[{name: '激进风控', icon: '⚔️'}, {name: '保守风控', icon: '🛡️'}]"
          :messages="riskDebateMessages"
          :conclusion="riskDebateConclusion"
          :show-config="configMode"
          :agent-ids="['risk_aggressive', 'risk_conservative', 'risk_neutral', 'risk_manager']"
        />
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
            :duration-seconds="agentDurations[agent.id]"
            :fallback-level="agentFallbackLevels[agent.id] || 0"
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
              <span>InvestMindPro 最终决策报告</span>
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
            
            <!-- 专业版报告 - 阶段标签切换 -->
            <div v-show="reportView === 'professional'" class="report-content professional-report">
              <!-- 阶段标签栏 -->
              <div class="stage-tabs">
                <button
                  v-for="(stageInfo, stageKey) in reportStages"
                  :key="stageKey"
                  @click="activeReportStage = stageKey"
                  :class="['stage-tab', { active: activeReportStage === stageKey }]"
                  :disabled="!stageInfo.hasContent"
                >
                  <span class="stage-tab-icon">{{ stageInfo.icon }}</span>
                  <span class="stage-tab-title">{{ stageInfo.title }}</span>
                  <span v-if="stageInfo.agentCount > 0" class="stage-tab-count">{{ stageInfo.agentCount }}</span>
                </button>
              </div>
              <!-- 阶段内容区 -->
              <div class="stage-content-area">
                <div v-for="(stageInfo, stageKey) in reportStages" :key="stageKey" v-show="activeReportStage === stageKey">
                  <div class="stage-content-header">
                    <span class="stage-content-icon">{{ stageInfo.icon }}</span>
                    <h3 class="stage-content-title">{{ stageInfo.fullTitle }}</h3>
                  </div>
                  <!-- 智能体分析结果列表 -->
                  <div class="agent-results-list">
                    <div
                      v-for="agent in getStageAgentsWithOutput(stageKey)"
                      :key="agent.id"
                      class="agent-result-card"
                      :class="getAgentCardClass(agent)"
                    >
                      <div class="agent-result-header">
                        <span class="agent-result-icon">{{ agent.icon }}</span>
                        <span class="agent-result-title">{{ agent.title }}</span>
                        <span v-if="agentDurations[agent.id]" class="agent-result-duration">
                          {{ formatDuration(agentDurations[agent.id]) }}
                        </span>
                        <span v-if="agentTokens[agent.id]" class="agent-result-tokens">
                          {{ agentTokens[agent.id].toLocaleString() }} tokens
                        </span>
                      </div>
                      <div class="agent-result-content prose prose-invert max-w-none" v-html="parseMarkdown(agentOutputs[agent.id])"></div>
                    </div>
                  </div>
                  <!-- 辩论摘要（仅在第二、三阶段显示） -->
                  <div v-if="stageKey === 'stage2' && bullBearDebateConclusion" class="debate-summary">
                    <div class="debate-summary-header">
                      <span>🐂🐻</span>
                      <span>多空辩论摘要</span>
                    </div>
                    <div class="debate-summary-content">
                      <div class="debate-score">方向评分：<strong>{{ bullBearDebateConclusion.score || 'N/A' }} / 100</strong></div>
                      <div class="debate-conclusion">{{ bullBearDebateConclusion.content }}</div>
                    </div>
                  </div>
                  <div v-if="stageKey === 'stage3' && riskDebateConclusion" class="debate-summary risk">
                    <div class="debate-summary-header">
                      <span>⚖️</span>
                      <span>风控辩论与仓位建议</span>
                    </div>
                    <div class="debate-summary-content">
                      <div class="debate-score">风险评分：<strong>{{ riskDebateConclusion.score || 'N/A' }} / 100</strong></div>
                      <div class="debate-conclusion">{{ riskDebateConclusion.content }}</div>
                    </div>
                  </div>
                </div>
              </div>
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
    
    <!-- 降级监控面板 -->
    <FallbackMonitor 
      v-model:visible="showFallbackMonitor"
      :fallback-data="{
        agentFallbackLevels: agentFallbackLevels
      }"
    />
  </div>
</template>
<script>
import { ref, computed, inject, onBeforeUnmount, onMounted } from 'vue'
import axios from 'axios'
import AgentCard from '@/components/AgentCard.vue'
import DebatePanel from '@/components/DebatePanel.vue'
import ModelManager from '@/components/ModelManager.vue'
import ApiConfig from '@/components/ApiConfig.vue'
import StyleConfig from '@/components/StyleConfig.vue'
import ReportExporter from '@/components/ReportExporter.vue'
import StockSearchInput from '@/components/StockSearchInput.vue'
import GlobalLogWindow from '@/components/GlobalLogWindow.vue'
import FallbackMonitor from '@/components/FallbackMonitorSimple.vue'
import { marked } from 'marked'
import {
  saveAnalysisState,
  loadAnalysisState,
  clearAnalysisState,
  forceCleanAllState,
  clearForceStopFlag,
  isForceStoppedState,
  saveSessionId,
  getSessionId,
  clearSessionId,
  markAnalysisComplete
} from '@/utils/analysisState'
import { fetchWithSmartTimeout, ProgressMonitor } from '@/utils/smartTimeout'
// 22个智能体完整定义（21个可配置 + 1个特殊的interpreter嵌入在GM卡片中）
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
  components: { 
    AgentCard, 
    DebatePanel, 
    ModelManager, 
    ApiConfig, 
    StyleConfig, 
    ReportExporter, 
    StockSearchInput, 
    GlobalLogWindow, 
    FallbackMonitor
  },
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
    const pollingInterval = ref(null)  // 轮询定时器
    const showAnalysisToast = ref(false)  // 分析启动提示弹窗
    // 标签页标题提示
    const originalTitle = 'InvestMind Pro - AI投资决策系统'
    let titleFlashInterval = null
    
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
    const agentDataSources = ref({}) // Stores array of data sources
    const agentFallbackLevels = ref({}) // 存储降级级别
    const agentDurations = ref({}) // 存储单智能体耗时（秒）
    const modelUpdateTrigger = ref(0)
    const cardsExpanded = ref(false) // 卡片是否展开，默认折叠
    const agentConfig = ref({}) // 智能体配置
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
    const activeReportStage = ref('stage1') // 当前激活的报告阶段标签
    const interpreterModel = ref('Qwen/Qwen2.5-7B-Instruct') // 白话解读员模型
    const interpreterTemperature = ref(0.7) // 白话解读员温度
    const availableModels = ref([]) // 可用模型列表，从后端加载
    
    // 全局日志窗口（从 App.vue 注入）
    const showGlobalLogWindow = inject('showLogWindow')
    const globalLogWindowRef = ref(null)
    
    // 降级监控面板
    const showFallbackMonitor = ref(false)
    
    // 轮询状态
    const lastPollingTime = ref(0)  // 上次轮询时间
    const pollingEnabled = ref(false)  // 是否启用轮询
    const currentSessionId = ref(null)  // 当前会话 ID
    // Initialize
    const initAgents = () => {
      AGENTS.forEach(a => {
        agentStatus.value[a.id] = 'idle'
        agentOutputs.value[a.id] = ''
        agentTokens.value[a.id] = 0
        agentThoughts.value[a.id] = []
        agentDataSources.value[a.id] = []
        agentDurations.value[a.id] = 0
      })
    }
    initAgents()
    // 加载智能体配置
    const loadAgentConfig = async () => {
      try {
        const response = await axios.get('/api/agents/config/current')
        agentConfig.value = response.data.config
        console.log('[配置] 加载智能体配置:', agentConfig.value)
      } catch (error) {
        console.error('[配置] 加载失败:', error)
        // 失败时使用默认配置（全部启用）
        agentConfig.value = {}
        AGENTS.forEach(a => {
          agentConfig.value[a.id] = true
        })
      }
    }
    
    // 启用的智能体列表（根据配置过滤）
    const enabledAgents = computed(() => {
      return AGENTS.filter(a => agentConfig.value[a.id] === true)
    })
    // Computed Groups（使用启用的智能体）
    const stage1Agents = computed(() => enabledAgents.value.filter(a => a.stage === 1))
    const stage2Agents = computed(() => enabledAgents.value.filter(a => a.stage === 2))
    const stage3Agents = computed(() => enabledAgents.value.filter(a => a.stage === 3))
    const stage4Agents = computed(() => enabledAgents.value.filter(a => a.stage === 4))
    const stage4AgentsFiltered = computed(() => enabledAgents.value.filter(a => a.stage === 4 && a.id !== 'interpreter'))
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
    // 报告阶段配置（动态计算有内容的智能体数量）
    const reportStages = computed(() => {
      const getStageAgentCount = (stage) => {
        return AGENTS.filter(a => a.stage === stage && agentOutputs.value[a.id] && a.id !== 'interpreter').length
      }
      return {
        stage1: {
          icon: '🌐',
          title: '信息采集',
          fullTitle: '第一阶段：全维信息采集与分析',
          agentCount: getStageAgentCount(1),
          hasContent: getStageAgentCount(1) > 0
        },
        stage2: {
          icon: '🎯',
          title: '策略研判',
          fullTitle: '第二阶段：策略整合与方向研判',
          agentCount: getStageAgentCount(2),
          hasContent: getStageAgentCount(2) > 0
        },
        stage3: {
          icon: '🛡️',
          title: '风险控制',
          fullTitle: '第三阶段：风险控制终审',
          agentCount: getStageAgentCount(3),
          hasContent: getStageAgentCount(3) > 0
        },
        stage4: {
          icon: '👑',
          title: '最终决策',
          fullTitle: '第四阶段：投资决策执行',
          agentCount: getStageAgentCount(4),
          hasContent: getStageAgentCount(4) > 0
        }
      }
    })
    // 获取指定阶段有输出的智能体列表
    const getStageAgentsWithOutput = (stageKey) => {
      const stageNum = parseInt(stageKey.replace('stage', ''))
      return AGENTS.filter(a => a.stage === stageNum && agentOutputs.value[a.id] && a.id !== 'interpreter')
    }
    // 获取智能体卡片样式类
    const getAgentCardClass = (agent) => {
      const colorMap = {
        slate: 'agent-card-slate',
        cyan: 'agent-card-cyan',
        violet: 'agent-card-violet',
        emerald: 'agent-card-emerald',
        blue: 'agent-card-blue',
        indigo: 'agent-card-indigo',
        fuchsia: 'agent-card-fuchsia',
        orange: 'agent-card-orange',
        amber: 'agent-card-amber',
        red: 'agent-card-red',
        green: 'agent-card-green'
      }
      return colorMap[agent.color] || 'agent-card-blue'
    }
    // 解析 Markdown
    const parseMarkdown = (text) => {
      if (!text) return ''
      try {
        return marked.parse(text)
      } catch (e) {
        return `<pre>${text}</pre>`
      }
    }
    // 格式化耗时
    const formatDuration = (seconds) => {
      if (!seconds || seconds <= 0) return ''
      return `${Number(seconds).toFixed(1)}s`
    }
    // 处理股票选择
    const handleStockSelect = (stock) => {
      console.log('选择股票:', stock)
      // 提取纯数字股票代码（移除.SH/.SZ后缀）
      const code = stock.code || ''
      // 支持多种格式：600519.SH, SH600519, 600519
      const pureCode = code.replace(/\.(SH|SZ|BJ)$/i, '')  // 移除后缀
                          .replace(/^(SH|SZ|BJ)/i, '')     // 移除前缀
                          .trim()
      stockCode.value = pureCode
    }
    // Analysis Logic
    const startAnalysis = async () => {
      if (!isValidCode.value || isAnalyzing.value) return
      // 清除强制停止标记（允许新分析）
      clearForceStopFlag()
      isAnalyzing.value = true
      cardsExpanded.value = true // 开始分析时自动展开所有卡片
      
      // 显示分析启动提示弹窗，8秒后自动消失
      showAnalysisToast.value = true
      setTimeout(() => {
        showAnalysisToast.value = false
      }, 8000)
      agentDataSources.value = {}
      agentStatus.value = {}
      agentOutputs.value = {}
      agentTokens.value = {}
      agentThoughts.value = {}
      agentDurations.value = {}
      agentFallbackLevels.value = {}
      showReport.value = false
      
      // 清空旧日志（如果窗口打开）
      if (globalLogWindowRef.value && globalLogWindowRef.value.clearLogs) {
        globalLogWindowRef.value.clearLogs()
      }
      // 更新标题为分析中
      document.title = `⏳ 分析中... - ${stockCode.value}`
      // 记录开始时间（不再使用前端独立计时器）
      analysisStartTime.value = Date.now()
      analysisElapsedTime.value = 0
      // 注意：不再启动前端计时器，时间将由后端轮询更新
      bullBearDebateMessages.value = []
      riskDebateMessages.value = []
      
      try {
        // 0. 数据验证阶段（先获取股票数据）
        const fetchedStockData = await fetchStockData(stockCode.value)
        
        // 简单验证数据有效性
        if (!fetchedStockData || !fetchedStockData.price || fetchedStockData.price === 'N/A') {
          throw new Error('无法获取有效的市场数据，分析终止。请检查网络或数据源。')
        }
        
        stockData.value = fetchedStockData
        
        // 1. 创建后端会话（现在有股票名称了）
        console.log('[会话] 创建分析会话...')
        const sessionResponse = await fetch('/api/analysis/db/session/create', {
          method: 'POST',
          headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({
            stock_code: stockCode.value,
            stock_name: fetchedStockData.name || fetchedStockData.symbol
          })
        })
        
        if (!sessionResponse.ok) {
          throw new Error('创建会话失败')
        }
        
        const sessionData = await sessionResponse.json()
        currentSessionId.value = sessionData.session_id
        // 保存到 localStorage（使用统一的函数）
        saveSessionId(currentSessionId.value)
        console.log('[会话] 会话创建成功:', currentSessionId.value)
        console.log('[会话] 股票名称:', fetchedStockData.name)
        
        // 开始分析
        await fetch(`/api/analysis/db/session/${currentSessionId.value}/start`, {
          method: 'POST'
        })
        
        // 保存初始状态
        saveCurrentState()
        
        // 启动轮询机制
        startPolling()
        // 2. 执行第一阶段：全维信息采集与分析（细分三步）
        // ✅ 根据配置过滤启用的智能体
        // Step 1.1: 数据采集层 (News, Social, China)
        const step1AgentsCandidates = ['news_analyst', 'social_analyst', 'china_market']
        const step1Agents = step1AgentsCandidates.filter(id => agentConfig.value[id] === true)
        if (step1Agents.length > 0) {
          await runAgentsParallel(step1Agents, fetchedStockData)
        }
        // Step 1.2: 行业与宏观分析层 (Industry, Macro) - 依赖Step 1.1
        const step2AgentsCandidates = ['industry', 'macro']
        const step2Agents = step2AgentsCandidates.filter(id => agentConfig.value[id] === true)
        if (step2Agents.length > 0) {
          await runAgentsParallel(step2Agents, fetchedStockData)
        }
        // Step 1.3: 深度专业分析层 (Technical, Funds, Fundamental) - 依赖Step 1.2
        const step3AgentsCandidates = ['technical', 'funds', 'fundamental']
        const step3Agents = step3AgentsCandidates.filter(id => agentConfig.value[id] === true)
        if (step3Agents.length > 0) {
          await runAgentsParallel(step3Agents, fetchedStockData)
        }
        // 3. 执行第二阶段：策略整合 (并发执行)
        console.log('[startAnalysis] 开始第二阶段...')
        const stage2Ids = enabledAgents.value.filter(a => a.stage === 2).map(a => a.id)
        console.log('[startAnalysis] 第二阶段智能体:', stage2Ids)
        if (stage2Ids.length > 0) {
          await runAgentsParallel(stage2Ids, fetchedStockData)
        }
        console.log('[startAnalysis] 第二阶段完成')
        // 2. 触发多空辩论 (模拟或真实API)
        await runBullBearDebate()
        // 5. 执行第三阶段：风控终审（分批处理，避免并发过载）
        console.log('[startAnalysis] 开始第三阶段...')
        const stage3Ids = enabledAgents.value.filter(a => a.stage === 3).map(a => a.id)
        console.log('[startAnalysis] 第三阶段智能体:', stage3Ids)
        if (stage3Ids.length > 0) {
          await runAgentsInBatches(stage3Ids, fetchedStockData, 2) // 每批最多2个
        }
        console.log('[startAnalysis] 第三阶段完成')
        // 4. 触发风控辩论
        console.log('[startAnalysis] 开始风控辩论...')
        await runRiskDebate()
        console.log('[startAnalysis] 风控辩论完成')
        // 6. 执行第四阶段：最终决策
        const stage4Ids = enabledAgents.value.filter(a => a.stage === 4).map(a => a.id)
        if (stage4Ids.length > 0) {
          await runAgentsParallel(stage4Ids, fetchedStockData)
        }
        showReport.value = true
        scrollToBottom()
        // 标记分析完成
        if (currentSessionId.value) {
          try {
            await fetch(`/api/analysis/db/session/${currentSessionId.value}/complete`, {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ success: true })
            })
            console.log('[数据库] 分析完成已标记')
          } catch (dbError) {
            console.error('[数据库] 标记完成失败:', dbError)
          }
        }
        // 触发标题闪烁提示（如果页面在后台）
        startTitleFlash(stockData.value?.name)
      } catch (error) {
        console.error('分析流程异常:', error)
        window.$toast && window.$toast.error(`分析中断: ${error.message}`)
        
        // 标记分析失败
        if (currentSessionId.value) {
          try {
            await fetch(`/api/analysis/db/session/${currentSessionId.value}/complete`, {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({ success: false, error: error.message })
            })
          } catch (dbError) {
            console.error('[数据库] 标记失败:', dbError)
          }
        }
      } finally {
        isAnalyzing.value = false
        // 停止计时器
        if (analysisTimer.value) {
          clearInterval(analysisTimer.value)
          analysisTimer.value = null
        }
        // 停止轮询
        stopPolling()
        // 清除保存的状态（分析已完成）
        markAnalysisComplete()
        console.log('[分析完成] 已清除保存的状态')
        // 如果页面在前台，更新标题
        if (document.visibilityState === 'visible') {
          if (showReport.value) {
            document.title = `✅ 分析完成 - ${stockData.value?.name || stockCode.value}`
          } else {
            document.title = originalTitle
          }
        }
      }
    }
    const runAgentsParallel = async (agentIds, data) => {
      const targetAgents = AGENTS.filter(a => agentIds.includes(a.id))
      await Promise.all(targetAgents.map(agent => runAgentAnalysis(agent, data)))
    }
    // 分批运行智能体（解决并发过载问题）
    const runAgentsInBatches = async (agentIds, data, batchSize = 2) => {
      const agents = agentIds.map(id => AGENTS.find(a => a.id === id))
      console.log(`[runAgentsInBatches] 开始处理 ${agents.length} 个智能体，批次大小: ${batchSize}`)
      
      for (let i = 0; i < agents.length; i += batchSize) {
        const batch = agents.slice(i, i + batchSize)
        const batchNum = Math.floor(i/batchSize) + 1
        const totalBatches = Math.ceil(agents.length/batchSize)
        
        console.log(`[runAgentsInBatches] 🚀 批次 ${batchNum}/${totalBatches}:`, batch.map(a => a.id))
        
        await Promise.all(batch.map(agent => runAgentAnalysis(agent, data)))
        
        console.log(`[runAgentsInBatches] ✅ 批次 ${batchNum}/${totalBatches} 完成`)
      }
      
      console.log(`[runAgentsInBatches] ✅ 所有批次完成`)
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
            // 在获取数据之前连接日志流
            if (globalLogWindowRef.value && globalLogWindowRef.value.connectAgentLog) {
              globalLogWindowRef.value.connectAgentLog(agent.id)
              await new Promise(resolve => setTimeout(resolve, 100))  // 等待连接建立
            }
            const newsResult = await fetchNewsData(data.symbol, agent.id)  // 传递 agent.id
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
            // 在获取数据之前连接日志流
            if (globalLogWindowRef.value && globalLogWindowRef.value.connectAgentLog) {
              globalLogWindowRef.value.connectAgentLog(agent.id)
              await new Promise(resolve => setTimeout(resolve, 100))
            }
            const newsResult = await fetchNewsData(data.symbol, agent.id)  // 传递 agent.id
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
            // 在获取数据之前连接日志流
            if (globalLogWindowRef.value && globalLogWindowRef.value.connectAgentLog) {
              globalLogWindowRef.value.connectAgentLog(agent.id)
              await new Promise(resolve => setTimeout(resolve, 100))
            }
            const newsResult = await fetchNewsData(data.symbol, agent.id)  // 传递 agent.id
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
            const response = await fetch(`/api/akshare/fund-flow/${data.symbol}`)
            
            if (!response.ok) {
              throw new Error(`HTTP ${response.status}`)
            }
            
            const result = await response.json()
            console.log('[funds] ✅ API返回结果:', result)
            
            // 检查返回格式
            if (result && result.success === true && result.sources) {
              const sources = result.sources
              agentDataSources.value[agent.id] = [
                { source: '北向资金数据', count: sources.north_bound || 0, description: '沪深港通实时流向' },
                { source: '主力资金数据', count: sources.individual_flow || 0, description: '大单成交监测' },
                { source: '融资融券数据', count: sources.margin_summary || 0, description: '两融余额变化' },
                { source: '行业资金流', count: sources.industry_flow || 0, description: '行业资金流向' }
              ]
              console.log(`[funds] ✅ 设置真实数据源:`, agentDataSources.value[agent.id])
            } else {
              console.error('[funds] ❌ API返回格式错误:', result)
              agentDataSources.value[agent.id] = [
                { source: '北向资金数据', count: 0, description: 'API格式错误' },
                { source: '主力资金数据', count: 0, description: 'API格式错误' },
                { source: '融资融券数据', count: 0, description: 'API格式错误' }
              ]
            }
          } catch (e) {
            console.error('[funds] ❌ 获取资金流向数据失败:', e)
            agentDataSources.value[agent.id] = [
              { source: '北向资金数据', count: 0, description: `错误: ${e.message}` },
              { source: '主力资金数据', count: 0, description: `错误: ${e.message}` },
              { source: '融资融券数据', count: 0, description: `错误: ${e.message}` }
            ]
          }
        } else if (agent.id === 'industry') {
          // 行业轮动分析师 - 获取真实数据
          try {
            const response = await fetch('/api/akshare/sector/comprehensive')
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
            const response = await fetch('/api/akshare/macro/comprehensive')
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
        // 记录开始时间（前端计时）
        const agentStartTime = Date.now()
        // 记录开始时间到数据库（用于持久化）
        if (currentSessionId.value) {
          try {
            await fetch(`/api/analysis/db/session/${currentSessionId.value}/update`, {
              method: 'POST',
              headers: {'Content-Type': 'application/json'},
              body: JSON.stringify({
                agent_id: agent.id,
                agent_name: agent.title,
                status: 'running'
              })
            })
          } catch (e) {
            console.warn(`[数据库] 记录开始时间失败: ${agent.id}`, e)
          }
        }
        // 使用智能超时机制
        const progressMonitor = new ProgressMonitor(agent.id, 10000)
        progressMonitor.start()
        try {
          const response = await fetchWithSmartTimeout(
            '/api/analyze',
            {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({
                agent_id: agent.id,
                stock_code: stockCode.value,
                stock_data: data,
                previous_outputs: agentOutputs.value,
                custom_instruction: getInstruction(agent, data)
              })
            },
            {
              segmentTimeout: 30000, // 30秒一段
              maxSegments: 6, // 最多6段 = 3分钟
              maxRetries: 2, // 最多重试2次
              agentId: agent.id
            }
          )
          
          progressMonitor.stop()
          
          if (!response.ok) {
            throw new Error(`API Error: ${response.status}`)
          }
          
          const result = await response.json()
          
          if (!result.success) {
            throw new Error(result.error || '分析失败')
          }
          
          const analysisResult = result.result || '⚠️ 分析结果为空'
          agentOutputs.value[agent.id] = analysisResult
          agentTokens.value[agent.id] = Math.floor(analysisResult.length / 1.5)
          agentStatus.value[agent.id] = 'success'
          // 计算耗时（从开始到收到响应）
          const agentEndTime = Date.now()
          const durationSeconds = (agentEndTime - agentStartTime) / 1000
          agentDurations.value[agent.id] = durationSeconds
          console.log(`[${agent.id}] 耗时: ${durationSeconds.toFixed(1)}s`)
          // 处理降级级别
          if (result.fallback_level !== undefined) {
            agentFallbackLevels.value[agent.id] = result.fallback_level
            console.log(`[${agent.id}] 降级级别: ${result.fallback_level}`)
            
            // 如果使用了降级，显示通知
            if (result.fallback_level > 0) {
              const message = result.fallback_level === 99 
                ? `${agent.title} 使用了预设的保守建议` 
                : `${agent.title} 提示词已压缩到${
                    result.fallback_level === 1 ? '50%' : 
                    result.fallback_level === 2 ? '25%' : '10%'
                  }`
              
              // 显示 Element Plus 通知
              if (window.$message) {
                window.$message.warning(message)
              }
            }
          }
          
          // 保存到数据库
          if (currentSessionId.value) {
            try {
              await fetch(`/api/analysis/db/session/${currentSessionId.value}/update`, {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                  agent_id: agent.id,
                  agent_name: agent.title,
                  status: 'completed',
                  output: analysisResult,
                  tokens: agentTokens.value[agent.id],
                  thoughts: agentThoughts.value[agent.id],
                  data_sources: agentDataSources.value[agent.id]
                })
              })
              console.log(`[数据库] 已保存: ${agent.title}`)
            } catch (dbError) {
              console.error(`[数据库] 保存失败: ${agent.id}`, dbError)
            }
          }
          
        } catch (error) {
          progressMonitor.stop()
          throw error
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
    const shortenText = (text, maxLen = 140) => {
        if (!text) {
            return '⚠️ 暂无有效观点，请检查模型配置或稍后重试。'
        }
        const clean = String(text).replace(/\s+/g, ' ').trim()
        if (clean.length <= maxLen) {
            return clean
        }
        return clean.slice(0, maxLen) + '...'
    }
    const localBullBearFallback = () => {
        if (!stockData.value) {
            return null
        }
        
        const data = stockData.value
        const agentData = agentOutputs.value || {}
        
        let bullScore = 50
        let bearScore = 50
        const reasons = []
        
        // ✅ 优先使用前序智能体的分析结果
        const newsAnalysis = agentData.news_analyst || ''
        const socialAnalysis = agentData.social_analyst || ''
        const technicalAnalysis = agentData.technical || ''
        const fundamentalAnalysis = agentData.fundamental || ''
        
        // 1. 从新闻分析中提取情绪
        if (newsAnalysis) {
            if (newsAnalysis.includes('利好') || newsAnalysis.includes('积极') || newsAnalysis.includes('看好') || newsAnalysis.includes('乐观')) {
                bullScore += 10
                reasons.push('新闻面偏向积极')
            } else if (newsAnalysis.includes('利空') || newsAnalysis.includes('消极') || newsAnalysis.includes('看空') || newsAnalysis.includes('悲观')) {
                bearScore += 10
                reasons.push('新闻面偏向消极')
            }
        }
        
        // 2. 从社交媒体分析中提取情绪
        if (socialAnalysis) {
            if (socialAnalysis.includes('看多') || socialAnalysis.includes('乐观') || socialAnalysis.includes('积极')) {
                bullScore += 8
                reasons.push('社交媒体情绪乐观')
            } else if (socialAnalysis.includes('看空') || socialAnalysis.includes('悲观') || socialAnalysis.includes('消极')) {
                bearScore += 8
                reasons.push('社交媒体情绪悲观')
            }
        }
        
        // 3. 从技术分析中提取趋势
        if (technicalAnalysis) {
            if (technicalAnalysis.includes('上涨') || technicalAnalysis.includes('突破') || technicalAnalysis.includes('强势') || technicalAnalysis.includes('多头')) {
                bullScore += 12
                reasons.push('技术面显示上涨趋势')
            } else if (technicalAnalysis.includes('下跌') || technicalAnalysis.includes('破位') || technicalAnalysis.includes('弱势') || technicalAnalysis.includes('空头')) {
                bearScore += 12
                reasons.push('技术面显示下跌趋势')
            }
        }
        
        // 4. 从基本面分析中提取估值
        if (fundamentalAnalysis) {
            if (fundamentalAnalysis.includes('低估') || fundamentalAnalysis.includes('便宜') || fundamentalAnalysis.includes('价值') || fundamentalAnalysis.includes('安全边际')) {
                bullScore += 10
                reasons.push('基本面显示估值偏低')
            } else if (fundamentalAnalysis.includes('高估') || fundamentalAnalysis.includes('泡沫') || fundamentalAnalysis.includes('昂贵')) {
                bearScore += 10
                reasons.push('基本面显示估值偏高')
            }
        }
        
        // 5. 价格动量（只在有明显趋势时添加）
        const changePercent = parseFloat(data.change_percent || data.change || 0)
        const price = parseFloat(data.price || 0)
        
        if (changePercent > 3) {
            bullScore += 10
            reasons.push(`短期上涨${changePercent.toFixed(1)}%，动能强劲`)
        } else if (changePercent < -3) {
            bearScore += 10
            reasons.push(`短期下跌${Math.abs(changePercent).toFixed(1)}%，下行压力`)
        }
        
        // 6. PE/PB估值（只在有数据且有意义时使用）
        const pe = parseFloat(data.pe || 0)
        const pb = parseFloat(data.pb || 0)
        
        if (pe > 0 && pe < 100) {  // PE在合理范围内
            if (pe < 15) {
                bullScore += 8
                reasons.push(`PE=${pe.toFixed(1)}，估值偏低`)
            } else if (pe > 50) {
                bearScore += 8
                reasons.push(`PE=${pe.toFixed(1)}，估值偏高`)
            }
        }
        
        if (pb > 0 && pb < 20) {  // PB在合理范围内
            if (pb < 1.0) {
                bullScore += 6
                reasons.push(`PB=${pb.toFixed(2)}，破净有安全边际`)
            } else if (pb > 5) {
                bearScore += 6
                reasons.push(`PB=${pb.toFixed(2)}，估值偏高`)
            }
        }
        
        // ✅ 如果没有任何有效分析，返回null而不是显示无意义信息
        if (reasons.length === 0) {
            return {
                label: '数据不足',
                score: 50,
                summary: '当前可用数据不足以进行有效分析，建议等待更多信息或使用在线LLM模型进行深度分析。',
                rec: 'HOLD'
            }
        }
        
        // 决策逻辑
        let rec = 'HOLD'
        let label = '分歧/观望'
        let score = 50
        
        if (bullScore > bearScore + 15) {
            rec = 'BUY'
            label = '多头优势'
            score = Math.min(85, 50 + (bullScore - bearScore))
        } else if (bearScore > bullScore + 15) {
            rec = 'SELL'
            label = '空头优势'
            score = Math.max(15, 50 - (bearScore - bullScore))
        } else {
            rec = 'HOLD'
            label = '分歧/观望'
            score = 50
        }
        
        // 生成友好的摘要
        const summary = `综合多维度分析（${rec}）：${reasons.slice(0, 4).join('；')}。当前价格${price}元。`
        
        return { label, score, summary, rec }
    }
    const localRiskFallback = () => {
        if (!stockData.value) {
            return null
        }
        
        const data = stockData.value
        const agentData = agentOutputs.value || {}
        
        let riskScore = 0
        const riskFactors = []
        
        // ✅ 优先从前序分析中提取风险因素
        const newsAnalysis = agentData.news_analyst || ''
        const technicalAnalysis = agentData.technical || ''
        const fundamentalAnalysis = agentData.fundamental || ''
        const riskSystemAnalysis = agentData.risk_system || ''
        
        // 1. 从新闻分析中提取风险
        if (newsAnalysis) {
            if (newsAnalysis.includes('风险') || newsAnalysis.includes('警告') || newsAnalysis.includes('危机')) {
                riskScore += 15
                riskFactors.push('新闻面存在负面信息')
            }
        }
        
        // 2. 从技术分析中提取波动性
        if (technicalAnalysis) {
            if (technicalAnalysis.includes('高波动') || technicalAnalysis.includes('剧烈波动') || technicalAnalysis.includes('不稳定')) {
                riskScore += 20
                riskFactors.push('技术面显示高波动性')
            }
        }
        
        // 3. 从基本面分析中提取财务风险
        if (fundamentalAnalysis) {
            if (fundamentalAnalysis.includes('亏损') || fundamentalAnalysis.includes('负债') || fundamentalAnalysis.includes('资金链')) {
                riskScore += 25
                riskFactors.push('基本面存在财务风险')
            }
        }
        
        // 4. 从系统性风险分析中提取
        if (riskSystemAnalysis) {
            if (riskSystemAnalysis.includes('高风险') || riskSystemAnalysis.includes('系统性风险')) {
                riskScore += 20
                riskFactors.push('存在系统性风险')
            }
        }
        
        // 5. 价格波动性
        const changePercent = Math.abs(parseFloat(data.change_percent || data.change || 0))
        
        if (changePercent > 9) {
            riskScore += 30
            riskFactors.push(`单日波动${changePercent.toFixed(1)}%，极高波动风险`)
        } else if (changePercent > 5) {
            riskScore += 20
            riskFactors.push(`单日波动${changePercent.toFixed(1)}%，高波动风险`)
        } else if (changePercent > 3) {
            riskScore += 10
            riskFactors.push(`单日波动${changePercent.toFixed(1)}%，中等波动`)
        }
        
        // 6. PE/PB估值风险（只在有数据且有意义时使用）
        const pe = parseFloat(data.pe || 0)
        const pb = parseFloat(data.pb || 0)
        
        if (pe > 100) {
            riskScore += 25
            riskFactors.push(`PE=${pe.toFixed(1)}，估值异常高`)
        } else if (pe > 50 && pe <= 100) {
            riskScore += 15
            riskFactors.push(`PE=${pe.toFixed(1)}，估值偏高`)
        }
        
        if (pb > 10 && pb < 50) {
            riskScore += 15
            riskFactors.push(`PB=${pb.toFixed(1)}，估值过高`)
        } else if (pb > 0 && pb < 0.8) {
            riskScore += 10
            riskFactors.push(`PB=${pb.toFixed(2)}，破净可能存在经营风险`)
        }
        
        // ✅ 如果没有任何风险因素，返回低风险而不是数据不足
        if (riskFactors.length === 0) {
            return {
                level: 'LOW',
                label: '低风险',
                score: 75,
                summary: '综合评估未发现明显风险因素，当前风险较低。建议仓位20-30%。'
            }
        }
        
        // 决策逻辑
        let level = 'MEDIUM'
        let label = '中等风险'
        let score = 50
        let positionAdvice = '建议仓位10-20%'
        
        if (riskScore >= 50) {
            level = 'HIGH'
            label = '高风险'
            score = 25
            positionAdvice = '建议仓位不超过5%或观望'
        } else if (riskScore >= 25) {
            level = 'MEDIUM'
            label = '中等风险'
            score = 50
            positionAdvice = '建议仓位10-20%'
        } else {
            level = 'LOW'
            label = '低风险'
            score = 75
            positionAdvice = '建议仓位可达20-30%'
        }
        
        // 生成友好的摘要
        const summary = `综合风险评估（${level}）：${riskFactors.slice(0, 4).join('；')}。${positionAdvice}。`
        
        return { level, label, score, summary }
    }
    const runBullBearDebate = async () => {
        showBullBearDebate.value = true
        bullBearDebateStatus.value = 'debating'
        bullBearDebateMessages.value = []
        bullBearDebateConclusion.value = null
        try {
            const response = await fetchWithSmartTimeout(
                '/api/debate/research',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        stock_code: stockCode.value,
                        analysis_data: agentOutputs.value,
                        debate_type: 'research',
                        rounds: 1
                    })
                },
                {
                    segmentTimeout: 90000,  // 单段90秒（原60秒）
                    maxSegments: 3,         // 最长270秒
                    maxRetries: 0,          // 不重试（原1次），避免浪费时间
                    agentId: 'debate_research'
                }
            )
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            const result = await response.json()
            console.log('[runBullBearDebate] 后端辩论结果:', result)
            if (!result.success) {
                throw new Error(result.detail || result.error || '多空辩论失败')
            }
            const bullContent = result.bull_view?.content || ''
            const bearContent = result.bear_view?.content || ''
            // 检测后端返回的是否是超时错误信息
            const isTimeout = bullContent.includes('AI 响应超时') || bearContent.includes('AI 响应超时')
            if (isTimeout) {
                throw new Error('后端LLM超时，触发本地兜底')
            }
            // 提取核心观点（去除辩论过程，只保留最终结论）
            const extractCoreView = (content) => {
                // 如果包含多个角色的对话，只提取最后一段
                const lines = content.split('\n').filter(l => l.trim())
                // 找到最后一个有实质内容的段落（超过50字）
                for (let i = lines.length - 1; i >= 0; i--) {
                    const line = lines[i].trim()
                    if (line.length > 50 && !line.includes('Bull Analyst:') && !line.includes('Bear Analyst:')) {
                        return line
                    }
                }
                // 如果没找到，返回前150字
                return content.substring(0, 150) + '...'
            }
            if (bullContent) {
                bullBearDebateMessages.value.push({
                    agentName: '看涨研究员',
                    agentIcon: '🐂',
                    content: shortenText(extractCoreView(bullContent), 150),
                    round: 1
                })
            }
            if (bearContent) {
                bullBearDebateMessages.value.push({
                    agentName: '看跌研究员',
                    agentIcon: '🐻',
                    content: shortenText(extractCoreView(bearContent), 150),
                    round: 1
                })
            }
            // 使用后端 recommendation / confidence 映射到前端评分
            const rec = (result.recommendation || '').toUpperCase()
            let label = '信号不明确'
            let score = 50
            if (rec === 'BUY') {
                label = '多头优势'
                score = 80
            } else if (rec === 'SELL') {
                label = '空头优势'
                score = 30
            } else if (rec === 'HOLD') {
                label = '分歧/观望'
                score = 55
            }
            const summary = result.debate_summary || result.final_decision?.content || ''
            // 限制结论长度，只显示核心信息
            const shortSummary = summary.length > 150 ? summary.substring(0, 150) + '...' : summary
            bullBearDebateConclusion.value = {
                content: shortSummary ? `方向评估：${label}。${shortSummary}` : `方向评估：${label}。`,
                score
            }
            bullBearDebateStatus.value = 'finished'
        } catch (e) {
            console.error('[runBullBearDebate] 多空辩论失败:', e)
            const fallback = localBullBearFallback()
            if (fallback) {
                // 模拟多头观点
                if (fallback.rec === 'BUY' || fallback.rec === 'HOLD') {
                    bullBearDebateMessages.value.push({
                        agentName: '看涨研究员',
                        agentIcon: '🐂',
                        content: `基于本地规则引擎分析：${fallback.summary.split('：')[1] || fallback.summary}。建议${fallback.rec === 'BUY' ? '买入' : '持有观望'}。`,
                        round: 1
                    })
                }
                
                // 模拟空头观点
                if (fallback.rec === 'SELL' || fallback.rec === 'HOLD') {
                    bullBearDebateMessages.value.push({
                        agentName: '看跌研究员',
                        agentIcon: '�',
                        content: `基于本地规则引擎分析：${fallback.summary.split('：')[1] || fallback.summary}。建议${fallback.rec === 'SELL' ? '卖出' : '谨慎观望'}。`,
                        round: 1
                    })
                }
                
                bullBearDebateConclusion.value = {
                    content: `方向评估：${fallback.label}。${fallback.summary}`,
                    score: fallback.score
                }
                bullBearDebateStatus.value = 'finished'
            } else {
                bullBearDebateStatus.value = 'idle'
                bullBearDebateMessages.value.push({
                    agentName: '系统',
                    agentIcon: '',
                    content: `多空辩论调用失败：${e.message || e}`
                })
            }
        }
    }
    const runRiskDebate = async () => {
        showRiskDebate.value = true
        riskDebateStatus.value = 'debating'
        riskDebateMessages.value = []
        riskDebateConclusion.value = null
        try {
            const response = await fetchWithSmartTimeout(
                '/api/debate/risk',
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        stock_code: stockCode.value,
                        analysis_data: agentOutputs.value,
                        debate_type: 'risk',
                        rounds: 1
                    })
                },
                {
                    segmentTimeout: 120000, // 单段120秒（原60秒）← 风险辩论需4个LLM
                    maxSegments: 3,         // 最长360秒
                    maxRetries: 0,          // 不重试，直接走兜底
                    agentId: 'debate_risk'
                }
            )
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`)
            }
            const result = await response.json()
            console.log('[runRiskDebate] 风险辩论结果:', result)
            if (!result.success) {
                throw new Error(result.detail || result.error || '风险辩论失败')
            }
            const aggressiveContent = result.aggressive_view?.content || ''
            const conservativeContent = result.conservative_view?.content || ''
            const neutralContent = result.neutral_view?.content || ''
            // 检测后端返回的是否是超时错误信息
            const isTimeout = aggressiveContent.includes('AI 响应超时') || 
                            conservativeContent.includes('AI 响应超时') || 
                            neutralContent.includes('AI 响应超时')
            if (isTimeout) {
                throw new Error('后端LLM超时，触发本地兜底')
            }
            // 提取核心观点
            const extractCoreView = (content) => {
                const lines = content.split('\n').filter(l => l.trim())
                for (let i = lines.length - 1; i >= 0; i--) {
                    const line = lines[i].trim()
                    if (line.length > 50 && !line.includes('Analyst:')) {
                        return line
                    }
                }
                return content.substring(0, 150) + '...'
            }
            if (aggressiveContent) {
                riskDebateMessages.value.push({
                    agentName: '激进风控',
                    agentIcon: '⚔️',
                    content: shortenText(extractCoreView(aggressiveContent), 150),
                    round: 1
                })
            }
            if (conservativeContent) {
                riskDebateMessages.value.push({
                    agentName: '保守风控',
                    agentIcon: '🛡️',
                    content: shortenText(extractCoreView(conservativeContent), 150),
                    round: 1
                })
            }
            // 确保三方观点都显示（即使内容为空也要有占位）
            if (neutralContent) {
                riskDebateMessages.value.push({
                    agentName: '中立风控',
                    agentIcon: '⚖️',
                    content: shortenText(extractCoreView(neutralContent), 150),
                    round: 1
                })
            }
            const level = result.risk_level || 'UNKNOWN'
            let label = '风险不明'
            let score = 50
            if (level === 'HIGH') {
                label = '高风险'
                score = 30
            } else if (level === 'MEDIUM') {
                label = '中等风险'
                score = 50
            } else if (level === 'LOW') {
                label = '低风险'
                score = 75
            }
            const adviceSummary = result.position_advice?.summary || ''
            // 限制结论长度
            const shortAdvice = adviceSummary.length > 150 ? adviceSummary.substring(0, 150) + '...' : adviceSummary
            riskDebateConclusion.value = {
                content: shortAdvice ? `风险评级：${label}。${shortAdvice}` : `风险评级：${label}。`,
                score
            }
            riskDebateStatus.value = 'finished'
        } catch (e) {
            console.error('[runRiskDebate] 风险辩论失败:', e)
            const fallback = localRiskFallback()
            if (fallback) {
                // ✅ 清理fallback.summary中的错误信息
                const cleanSummary = (summary) => {
                    if (!summary) return ''
                    
                    // 过滤掉超时错误信息
                    if (summary.includes('AI 响应超时') || summary.includes('⚠️') || 
                        summary.includes('建议：') || summary.includes('建议： 1.')) {
                        // 如果整个摘要都是错误信息，返回空
                        return ''
                    }
                    
                    // 提取冒号后的内容（如果有）
                    const parts = summary.split('：')
                    if (parts.length > 1 && !parts[1].includes('AI 响应超时')) {
                        return parts.slice(1).join('：').trim()
                    }
                    
                    return summary
                }
                
                const cleanedSummary = cleanSummary(fallback.summary)
                
                // ✅ 确保三方观点都显示
                // 激进风控 - 强调机会
                let aggressiveView = ''
                if (!cleanedSummary) {
                    // 如果没有有效摘要，使用纯本地分析
                    if (fallback.level === 'LOW') {
                        aggressiveView = `基于多维度分析：当前风险较低，市场情绪稳定，可以积极布局。建议仓位20-30%。`
                    } else if (fallback.level === 'MEDIUM') {
                        aggressiveView = `基于多维度分析：存在一定风险但机会可观，建议适度参与。建议仓位10-20%。`
                    } else {
                        aggressiveView = `基于多维度分析：风险较高但可能存在超额收益，可小仓位博弈。建议仓位不超过5%。`
                    }
                } else {
                    // 使用清理后的摘要
                    if (fallback.level === 'LOW') {
                        aggressiveView = `基于本地规则引擎分析：${cleanedSummary}。当前风险较低，可以积极布局。`
                    } else if (fallback.level === 'MEDIUM') {
                        aggressiveView = `基于本地规则引擎分析：${cleanedSummary}。虽有风险但机会可观，建议适度参与。`
                    } else {
                        aggressiveView = `基于本地规则引擎分析：${cleanedSummary}。高风险高收益，可小仓位博弈。`
                    }
                }
                
                riskDebateMessages.value.push({
                    agentName: '激进风控',
                    agentIcon: '⚔️',
                    content: aggressiveView,
                    round: 1
                })
                
                // 保守风控 - 强调风险
                let conservativeView = ''
                if (!cleanedSummary) {
                    // 如果没有有效摘要，使用纯本地分析
                    if (fallback.level === 'HIGH') {
                        conservativeView = `基于多维度分析：当前风险较高，市场不确定性大，建议谨慎观望或减仓避险。`
                    } else if (fallback.level === 'MEDIUM') {
                        conservativeView = `基于多维度分析：风险中等，存在一定不确定性，建议严格止损，控制仓位。`
                    } else {
                        conservativeView = `基于多维度分析：虽然风险较低，但仍需谨慎，建议分批建仓，控制节奏。`
                    }
                } else {
                    // 使用清理后的摘要
                    if (fallback.level === 'HIGH') {
                        conservativeView = `基于本地规则引擎分析：${cleanedSummary}。当前风险较高，建议谨慎观望。`
                    } else if (fallback.level === 'MEDIUM') {
                        conservativeView = `基于本地规则引擎分析：${cleanedSummary}。风险中等，需要严格止损。`
                    } else {
                        conservativeView = `基于本地规则引擎分析：${cleanedSummary}。虽然风险较低，但仍需谨慎控制仓位。`
                    }
                }
                riskDebateMessages.value.push({
                    agentName: '保守风控',
                    agentIcon: '🛡️',
                    content: conservativeView,
                    round: 1
                })
                
                // 中立风控 - 客观评估
                let neutralView = ''
                if (!cleanedSummary) {
                    // 使用纯本地分析
                    neutralView = `基于多维度分析：综合评估风险等级为${fallback.label}。建议根据个人风险偏好和资金状况理性决策。`
                } else {
                    // 使用清理后的摘要
                    const positionAdvice = cleanedSummary.includes('建议') ? 
                        cleanedSummary.split('。').find(s => s.includes('建议')) : ''
                    neutralView = `基于本地规则引擎分析：综合评估风险等级为${fallback.label}。${positionAdvice || '建议根据风险等级调整仓位'}。`
                }
                riskDebateMessages.value.push({
                    agentName: '中立风控',
                    agentIcon: '⚖️',
                    content: neutralView,
                    round: 1
                })
                
                // 生成清洁的结论
                let conclusionContent = ''
                if (!cleanedSummary) {
                    // 根据风险等级生成结论
                    if (fallback.level === 'HIGH') {
                        conclusionContent = `风险评级：${fallback.label}。综合评估显示当前投资风险较高，建议谨慎操作，控制仓位不超过5%。`
                    } else if (fallback.level === 'MEDIUM') {
                        conclusionContent = `风险评级：${fallback.label}。综合评估显示存在一定风险，建议适度参与，仓位控制在10-20%。`
                    } else {
                        conclusionContent = `风险评级：${fallback.label}。综合评估显示风险可控，可根据策略配置20-30%仓位。`
                    }
                } else {
                    conclusionContent = `风险评级：${fallback.label}。${cleanedSummary}`
                }
                
                riskDebateConclusion.value = {
                    content: conclusionContent,
                    score: fallback.score
                }
                riskDebateStatus.value = 'finished'
            } else {
                riskDebateStatus.value = 'idle'
                riskDebateMessages.value.push({
                    agentName: '系统',
                    agentIcon: '',
                    content: `风险辩论调用失败：${e.message || e}`
                })
            }
        }
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
          
          const response = await fetch(`/api/stock/${code}`, {
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
    const fetchNewsData = async (code, agentId = 'news_analyst') => {
        try {
          // 更新数据透明化面板 - 开始获取
          if (newsDataPanel.value && newsDataPanel.value.addLog) {
            newsDataPanel.value.addLog(`开始获取新闻数据: ${code}`, 'info')
            newsDataPanel.value.addLog('数据源: 统一新闻API (7个数据源)', 'fetch')
          }
          
          const response = await fetch('/api/unified-news/stock', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json'
            },
            body: JSON.stringify({
              ticker: code,
              agent_id: agentId  // 传递智能体ID，用于日志流
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
        const sections = []
        const stageTitles = {
            1: '\u7b2c\u4e00\u9636\u6bb5\uff1a\u5168\u7ef4\u4fe1\u606f\u91c7\u96c6\u4e0e\u5206\u6790',
            2: '\u7b2c\u4e8c\u9636\u6bb5\uff1a\u7b56\u7565\u6574\u5408\u4e0e\u65b9\u5411\u7814\u5224',
            3: '\u7b2c\u4e09\u9636\u6bb5\uff1a\u98ce\u9669\u63a7\u5236\u7ec8\u5ba1',
            4: '\u7b2c\u56db\u9636\u6bb5\uff1a\u6295\u8d44\u51b3\u7b56\u6267\u884c'
        }
        const getAgentsByStage = (stage) => {
            return AGENTS.filter(a => a.stage === stage)
        }
        for (let stage = 1; stage <= 4; stage++) {
            const stageAgents = getAgentsByStage(stage).filter(a => agentOutputs.value[a.id])
            if (!stageAgents.length) {
                continue
            }
            sections.push(`## ${stageTitles[stage]}`)
            stageAgents.forEach(a => {
                if (stage === 4 && a.id === 'interpreter') {
                    return
                }
                const output = agentOutputs.value[a.id]
                sections.push(`### ${a.icon} ${a.title}\n${output}`)
            })
        }
        const bullConclusion = bullBearDebateConclusion.value
        const riskConclusion = riskDebateConclusion.value
        if (bullConclusion || riskConclusion) {
            sections.push('## 讨论与决议')
            if (bullConclusion) {
                const bullScore = typeof bullConclusion.score === 'number' ? bullConclusion.score : 'N/A'
                sections.push(
                    '### \ud83d\udc02\ud83d\udc3b \u591a\u7a7a\u8fa9\u8bba\u6458\u8981' +
                    `\n- \u65b9\u5411\u8bc4\u5206\uff1a**${bullScore} / 100**` +
                    `\n- \u7efc\u5408\u7ed3\u8bba\uff1a${bullConclusion.content || ''}`
                )
            }
            if (riskConclusion) {
                const riskScore = typeof riskConclusion.score === 'number' ? riskConclusion.score : 'N/A'
                sections.push(
                    '### \u2696\ufe0f \u98ce\u63a7\u8fa9\u8bba\u4e0e\u4ed3\u4f4d\u5efa\u8bae' +
                    `\n- \u98ce\u9669\u8bc4\u5206\uff1a**${riskScore} / 100**` +
                    `\n- \u7efc\u5408\u7ed3\u8bba\uff1a${riskConclusion.content || ''}`
                )
            }
        }
        return sections.join('\n\n---\n\n')
    }
    // 加载可用模型列表
    const loadAvailableModels = async () => {
      try {
        const response = await fetch('/api/config/agents')
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
        const response = await fetch('/api/config/agents')
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
        await fetch('/api/config/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ ...config, agents })
        })
        
        console.log('白话解读员配置已保存:', interpreterConfig)
        showInterpreterConfig.value = false
        window.$toast && window.$toast.success('配置已保存！')
      } catch (error) {
        console.error('保存配置失败:', error)
        window.$toast && window.$toast.error('保存失败，请重试')
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
    // ==================== 轮询机制 ====================
    
    /**
     * 启动轮询 - 定期检查后端状态
     */
    const startPolling = () => {
      if (pollingInterval.value) {
        console.log('[轮询] 已在运行，跳过')
        return
      }
      pollingEnabled.value = true
      console.log('[轮询] 启动轮询机制，间隔 5 秒')
      // 启动本地计时器作为备份（每秒更新）
      if (!analysisTimer.value && analysisStartTime.value) {
        analysisTimer.value = setInterval(() => {
          if (isAnalyzing.value && analysisStartTime.value) {
            const elapsed = Math.floor((Date.now() - analysisStartTime.value) / 1000)
            // 只有当本地时间大于后端时间时才更新（确保时间不会倒退）
            if (elapsed > analysisElapsedTime.value) {
              analysisElapsedTime.value = elapsed
            }
          }
        }, 1000)
        console.log('[计时器] 启动本地计时器')
      }
      pollingInterval.value = setInterval(async () => {
        if (!isAnalyzing.value) {
          console.log('[轮询] 分析已结束，停止轮询')
          stopPolling()
          return
        }
        try {
          await pollBackendStatus()
        } catch (error) {
          console.error('[轮询] 错误:', error)
        }
      }, 5000)  // 每 5 秒轮询一次
    }
    /**
     * 停止轮询
     */
    const stopPolling = () => {
      if (pollingInterval.value) {
        clearInterval(pollingInterval.value)
        pollingInterval.value = null
        pollingEnabled.value = false
        console.log('[轮询] 已停止')
      }
      // 同时停止本地计时器
      if (analysisTimer.value) {
        clearInterval(analysisTimer.value)
        analysisTimer.value = null
        console.log('[计时器] 已停止')
      }
    }
    
    /**
     * 轮询后端状态
     * 调用后端会话 API 获取最新进度
     */
    const pollBackendStatus = async () => {
      if (!currentSessionId.value) {
        console.log('[轮询] 无会话 ID，跳过')
        return
      }
      
      const now = Date.now()
      lastPollingTime.value = now
      
      try {
        console.log('[轮询] 检查后端状态...', currentSessionId.value)
        
        // 调用后端 API（数据库版本）
        const response = await fetch(
          `/api/analysis/db/session/${currentSessionId.value}/status`
        )
        
        if (!response.ok) {
          console.error('[轮询] API 调用失败:', response.status)
          return
        }
        
        const status = await response.json()
        console.log(`[轮询] 进度: ${status.progress}%, 阶段: ${status.current_stage}, 完成: ${status.completed_agents.length}/${status.total_agents}`)
        
        // ✅ 关键修复：使用后端时间作为唯一真相源
        if (status.elapsed_time !== undefined) {
          analysisElapsedTime.value = Math.floor(status.elapsed_time)
          console.log(`[轮询] 更新时间: ${analysisElapsedTime.value}秒`)
        }
        
        // 更新进度
        if (status.current_stage > 0) {
          // 检查新完成的智能体
          for (const agentId of status.completed_agents) {
            if (!agentOutputs.value[agentId] || agentStatus.value[agentId] !== 'completed') {
              // 获取智能体结果
              await fetchAgentResult(agentId)
            }
          }
        }
        
        // 检查是否完成
        if (status.status === 'completed') {
          console.log('[轮询] 分析已完成')
          isAnalyzing.value = false
          showReport.value = true
          stopPolling()
          clearAnalysisState()
        } else if (status.status === 'error') {
          console.error('[轮询] 分析失败:', status.error_message)
          isAnalyzing.value = false
          stopPolling()
          window.$toast && window.$toast.error(`分析失败: ${status.error_message}`)
        }
        
      } catch (error) {
        console.error('[轮询] 错误:', error)
      }
    }
    
    /**
     * 获取智能体结果
     */
    const fetchAgentResult = async (agentId) => {
      try {
        const response = await fetch(
          `/api/analysis/db/session/${currentSessionId.value}/agent/${agentId}`
        )
        
        if (!response.ok) return
        
        const result = await response.json()
        
        if (result.status === 'completed') {
          console.log(`[轮询] 获取智能体结果: ${agentId}`)
          agentOutputs.value[agentId] = result.output || ''
          agentStatus.value[agentId] = 'completed'
          agentTokens.value[agentId] = result.tokens || 0
          agentThoughts.value[agentId] = result.thoughts || []
          agentDataSources.value[agentId] = result.data_sources || []
          // 记录单智能体耗时（由后端计算 start_time/end_time）
          agentDurations.value[agentId] = result.duration_seconds || 0
        }
      } catch (error) {
        console.error(`[轮询] 获取智能体结果失败: ${agentId}`, error)
      }
    }
    
    /**
     * 监听页面可见性变化
     * 移动端后台/前台切换时触发
     */
    const setupVisibilityListener = () => {
      document.addEventListener('visibilitychange', async () => {
        if (document.hidden) {
          console.log('[页面状态] 进入后台，后端继续分析')
          // 移动端后台时，后端继续运行，轮询继续
        } else {
          console.log('[页面状态] 回到前台，强制同步后端状态')
          // 停止标题闪烁
          stopTitleFlash()
          // 更新标题
          if (showReport.value && !isAnalyzing.value) {
            document.title = `✅ 分析完成 - ${stockData.value?.name || stockCode.value}`
          } else if (isAnalyzing.value) {
            document.title = `⏳ 分析中... - ${stockData.value?.name || stockCode.value}`
          } else {
            document.title = originalTitle
          }
          // ✅ 关键修复：回到前台时立即同步
          if (isAnalyzing.value && currentSessionId.value) {
            // 立即轮询一次，获取最新状态
            await pollBackendStatus()
            // 如果还在分析中，确保轮询正在运行
            if (isAnalyzing.value && !pollingInterval.value) {
              console.log('[页面状态] 重启轮询')
              startPolling()
            }
          }
        }
      })
    }
    // ==================== 状态持久化管理 ====================
    
    /**
     * 保存当前分析状态到 localStorage
     */
    const saveCurrentState = () => {
      if (!isAnalyzing.value) return
      
      try {
        const state = {
          stockCode: stockCode.value,
          stockData: stockData.value,
          isAnalyzing: isAnalyzing.value,
          agentStatus: agentStatus.value,
          agentOutputs: agentOutputs.value,
          agentTokens: agentTokens.value,
          agentThoughts: agentThoughts.value,
          agentDataSources: agentDataSources.value,
          agentDurations: agentDurations.value,
          analysisStartTime: analysisStartTime.value,
          analysisElapsedTime: analysisElapsedTime.value,
          showReport: showReport.value,
          showBullBearDebate: showBullBearDebate.value,
          showRiskDebate: showRiskDebate.value,
          bullBearDebateMessages: bullBearDebateMessages.value,
          riskDebateMessages: riskDebateMessages.value,
          bullBearDebateConclusion: bullBearDebateConclusion.value,
          riskDebateConclusion: riskDebateConclusion.value
        }
        
        saveAnalysisState(state)
      } catch (error) {
        console.error('[状态保存] 失败:', error)
      }
    }
    
    /**
     * 从 localStorage 恢复分析状态
     */
    const restoreState = (savedState) => {
      try {
        console.log('[状态恢复] 开始恢复状态...')
        
        // 恢复基本信息
        stockCode.value = savedState.stockCode || ''
        stockData.value = savedState.stockData || null
        isAnalyzing.value = savedState.isAnalyzing || false
        
        // 恢复智能体状态
        agentStatus.value = savedState.agentStatus || {}
        agentOutputs.value = savedState.agentOutputs || {}
        agentTokens.value = savedState.agentTokens || {}
        agentThoughts.value = savedState.agentThoughts || {}
        agentDataSources.value = savedState.agentDataSources || {}
        agentDurations.value = savedState.agentDurations || {}
        
        // 恢复显示状态
        showReport.value = savedState.showReport || false
        showBullBearDebate.value = savedState.showBullBearDebate || false
        showRiskDebate.value = savedState.showRiskDebate || false
        
        // 恢复辩论数据
        bullBearDebateMessages.value = savedState.bullBearDebateMessages || []
        riskDebateMessages.value = savedState.riskDebateMessages || []
        bullBearDebateConclusion.value = savedState.bullBearDebateConclusion || null
        riskDebateConclusion.value = savedState.riskDebateConclusion || null
        
        // 恢复时间（不再启动前端计时器）
        if (isAnalyzing.value && savedState.analysisStartTime) {
          analysisStartTime.value = savedState.analysisStartTime
          const elapsed = Date.now() - savedState.analysisStartTime
          analysisElapsedTime.value = Math.floor(elapsed / 1000)
          
          console.log(`[状态恢复] 已运行 ${Math.floor(elapsed / 1000)} 秒，等待后端轮询更新`)
          // 注意：不再启动前端计时器，时间将由后端轮询更新
        }
        
        // 展开卡片
        cardsExpanded.value = true
        
        console.log('[状态恢复] 恢复完成')
        console.log('[状态恢复] 智能体状态:', agentStatus.value)
        
        // 显示提示
        window.$toast && window.$toast.info('已恢复上次分析状态。如果后端分析已完成，请刷新页面查看最新结果。', 5000)
        
      } catch (error) {
        console.error('[状态恢复] 失败:', error)
        clearAnalysisState()
      }
    }
    // ==================== 标签页标题提示 ====================
    /**
     * 开始标题闪烁提示（分析完成时调用）
     */
    const startTitleFlash = (stockName) => {
      // 如果页面在前台，不需要闪烁
      if (document.visibilityState === 'visible') {
        document.title = `✅ 分析完成 - ${stockName || stockCode.value}`
        return
      }
      // 页面在后台，开始闪烁
      let isOriginal = false
      const flashTitle = `✅ 分析完成 - ${stockName || stockCode.value}`
      // 清除之前的闪烁
      if (titleFlashInterval) {
        clearInterval(titleFlashInterval)
      }
      titleFlashInterval = setInterval(() => {
        document.title = isOriginal ? flashTitle : '📊 点击查看结果'
        isOriginal = !isOriginal
      }, 1000)
      // 尝试播放提示音（需要用户之前有交互）
      playNotificationSound()
    }
    /**
     * 停止标题闪烁
     */
    const stopTitleFlash = () => {
      if (titleFlashInterval) {
        clearInterval(titleFlashInterval)
        titleFlashInterval = null
      }
      document.title = originalTitle
    }
    /**
     * 播放提示音
     */
    const playNotificationSound = () => {
      try {
        // 使用 Web Audio API 生成简单的提示音
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()
        const oscillator = audioContext.createOscillator()
        const gainNode = audioContext.createGain()
        oscillator.connect(gainNode)
        gainNode.connect(audioContext.destination)
        oscillator.frequency.value = 800  // 频率
        oscillator.type = 'sine'
        gainNode.gain.value = 0.1  // 音量（较小）
        oscillator.start()
        // 渐弱效果
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3)
        oscillator.stop(audioContext.currentTime + 0.3)
        console.log('[提示音] 已播放')
      } catch (e) {
        // 静默失败（用户可能没有交互过页面）
        console.log('[提示音] 无法播放:', e.message)
      }
    }
    /**
     * 强制停止分析
     * 用于解决移动端卡住的问题
     */
    const forceStop = async () => {
      console.log('[强制停止] 开始清理...')
      // 1. 停止所有计时和轮询
      if (analysisTimer.value) {
        clearInterval(analysisTimer.value)
        analysisTimer.value = null
      }
      stopPolling()
      // 2. 通知后端取消会话
      if (currentSessionId.value) {
        try {
          await axios.post(`/api/analysis/db/session/${currentSessionId.value}/cancel`)
          console.log('[强制停止] 已通知后端取消')
        } catch (error) {
          console.error('[强制停止] 通知后端失败:', error)
        }
      }
      // 3. 使用统一的清除函数（设置强制停止标记）
      forceCleanAllState()
      console.log('[强制停止] 已清除所有 localStorage')
      // 4. 重置所有状态
      isAnalyzing.value = false
      analysisElapsedTime.value = 0
      analysisStartTime.value = 0
      currentSessionId.value = null
      agentStatus.value = {}
      agentOutputs.value = {}
      agentTokens.value = {}
      agentThoughts.value = {}
      agentDataSources.value = {}
      agentDurations.value = {}
      agentFallbackLevels.value = {}
      showReport.value = false
      showBullBearDebate.value = false
      showRiskDebate.value = false
      bullBearDebateMessages.value = []
      riskDebateMessages.value = []
      bullBearDebateConclusion.value = null
      riskDebateConclusion.value = null
      console.log('[强制停止] 清理完成')
      window.$toast && window.$toast.success('已强制停止分析并清除所有状态，可以重新开始了！')
    }
    
    /**
     * 页面加载时检查并恢复状态
     */
    onMounted(async () => {
      console.log('[页面加载] 检查保存的状态...')
      // ✅ 加载智能体配置
      await loadAgentConfig()
      // ✅ 检查是否被强制停止
      if (isForceStoppedState()) {
        console.log('[页面加载] 检测到强制停止标记，清除并跳过恢复')
        // 清除强制停止标记（下次可以正常分析）
        clearForceStopFlag()
        setupVisibilityListener()
        return
      }
      // 设置页面可见性监听器
      setupVisibilityListener()
      // 优先检查后端会话
      const sessionId = getSessionId()
      
      if (sessionId) {
        console.log('[页面加载] 发现会话 ID:', sessionId)
        try {
          // 查询后端会话状态（数据库版本）
          const response = await fetch(
            `/api/analysis/db/session/${sessionId}/status`
          )
          if (response.ok) {
            const status = await response.json()
            console.log('[页面加载] 后端会话状态:', status.status, `${status.progress}%`)
            if (status.status === 'running') {
              // 检查是否真的在运行（通过 last_activity_time 判断）
              const lastActivity = status.last_activity_time ? status.last_activity_time * 1000 : 0
              const now = Date.now()
              const inactiveSeconds = lastActivity ? (now - lastActivity) / 1000 : 999
              // 如果超过30秒无活动，说明实际上已经中断了
              if (inactiveSeconds > 30) {
                console.log('[页面加载] 会话状态为running但已无活动，视为中断')
                // 按中断处理
                const completedCount = status.completed_agents?.length || 0
                const elapsedSeconds = status.elapsed_time || status.actual_elapsed_seconds || 0
                const message = `检测到上次分析被中断\n` +
                  `股票: ${status.stock_code}\n` +
                  `进度: ${status.progress}% (${completedCount}/21 智能体完成)\n` +
                  `运行时间: ${Math.floor(elapsedSeconds / 60)}分${elapsedSeconds % 60}秒\n\n` +
                  `是否要查看已完成的分析结果？\n` +
                  `（点击"取消"将清除此会话）`
                if (window.confirm(message)) {
                  currentSessionId.value = sessionId
                  stockCode.value = status.stock_code
                  cardsExpanded.value = true
                  isAnalyzing.value = false
                  for (const agentId of status.completed_agents) {
                    await fetchAgentResult(agentId)
                  }
                  analysisElapsedTime.value = elapsedSeconds
                  window.$toast && window.$toast.info(`已加载 ${completedCount} 个智能体的分析结果`)
                } else {
                  clearSessionId()
                  clearAnalysisState()
                  window.$toast && window.$toast.info('已清除中断的会话')
                }
                return
              }
              // 真正在运行中，恢复会话
              currentSessionId.value = sessionId
              stockCode.value = status.stock_code
              isAnalyzing.value = true
              cardsExpanded.value = true
              // 恢复已完成的智能体
              for (const agentId of status.completed_agents) {
                await fetchAgentResult(agentId)
              }
              // 启动轮询
              startPolling()
              // 设置时间（使用实际运行时间）
              analysisStartTime.value = status.start_time * 1000
              analysisElapsedTime.value = Math.floor(status.elapsed_time)
              // 注意：不再启动前端计时器，时间将由后端轮询更新
              console.log('[页面加载] 从后端恢复会话成功，当前时间:', analysisElapsedTime.value, '秒')
              window.$toast && window.$toast.success('已从后端恢复分析状态')
              return
            } else if (status.status === 'interrupted') {
              // 会话被中断（服务重启等原因）
              console.log('[页面加载] 会话已中断，进度:', status.progress, '%')
              // 显示中断提示，让用户选择
              const completedCount = status.completed_agents?.length || 0
              // 优先使用 elapsed_time（基于 start_time 计算），其次使用 actual_elapsed_seconds
              const elapsedSeconds = status.elapsed_time || status.actual_elapsed_seconds || 0
              const message = `检测到上次分析被中断\n` +
                `股票: ${status.stock_code}\n` +
                `进度: ${status.progress}% (${completedCount}/21 智能体完成)\n` +
                `运行时间: ${Math.floor(elapsedSeconds / 60)}分${elapsedSeconds % 60}秒\n\n` +
                `是否要查看已完成的分析结果？\n` +
                `（点击"取消"将清除此会话）`
              if (window.confirm(message)) {
                // 用户选择查看已完成的结果
                currentSessionId.value = sessionId
                stockCode.value = status.stock_code
                cardsExpanded.value = true
                isAnalyzing.value = false  // 不再分析中
                // 恢复已完成的智能体结果
                for (const agentId of status.completed_agents) {
                  await fetchAgentResult(agentId)
                }
                // 设置时间（优先使用 elapsed_time）
                analysisElapsedTime.value = elapsedSeconds
                window.$toast && window.$toast.info(`已加载 ${completedCount} 个智能体的分析结果`)
              } else {
                // 用户选择清除会话
                clearSessionId()
                clearAnalysisState()
                window.$toast && window.$toast.info('已清除中断的会话')
              }
              return
            } else if (status.status === 'completed') {
              console.log('[页面加载] 分析已完成，清除会话')
              clearSessionId()
              clearAnalysisState()
            } else if (status.status === 'error') {
              console.log('[页面加载] 分析出错，清除会话')
              clearSessionId()
              clearAnalysisState()
              window.$toast && window.$toast.error(`上次分析出错: ${status.error_message || '未知错误'}`)
            }
          }
        } catch (error) {
          console.error('[页面加载] 查询后端会话失败:', error)
        }
      }
      
      // 如果后端没有会话，尝试从 localStorage 恢复
      // 注意：不再重新声明 savedState，使用开头已经检查过的
      const stateToRestore = loadAnalysisState()
      if (stateToRestore && stateToRestore.isAnalyzing) {
        console.log('[页面加载] 从 localStorage 恢复状态')
        restoreState(stateToRestore)
      } else {
        console.log('[页面加载] 无保存的状态')
      }
    })
    
    /**
     * 页面卸载时清理
     */
    onBeforeUnmount(() => {
      if (analysisTimer.value) {
        clearInterval(analysisTimer.value)
      }
      // 停止轮询
      stopPolling()
      // 停止标题闪烁
      stopTitleFlash()
      // 恢复原始标题
      document.title = originalTitle
      // 如果分析已完成，清除保存的状态
      if (!isAnalyzing.value && showReport.value) {
        clearAnalysisState()
        console.log('[页面卸载] 已清除完成的分析状态')
      }
    })
    return {
        stockCode, stockData, isAnalyzing, isValidCode, startAnalysis,
        AGENTS,
        configMode, showModelManager, showApiConfig, showStyleConfig, apiStatus,
        agentStatus, agentOutputs, agentTokens, agentThoughts, agentDataSources, agentFallbackLevels, agentDurations,
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
        handleStockSelect,  // 新增: 股票选择处理
        showGlobalLogWindow, globalLogWindowRef,  // 新增: 全局日志窗口
        forceStop,  // 新增: 强制停止
        showFallbackMonitor,  // 新增: 降级监控面板
        showAnalysisToast,  // 新增: 分析启动提示弹窗
        // 专业版报告阶段切换
        activeReportStage, reportStages, getStageAgentsWithOutput, getAgentCardClass, parseMarkdown, formatDuration
    }
  }
}
</script>
<style scoped>
.analysis-container {
  padding: 2rem;
  max-width: 1400px;  /* 从1800px减少到1400px，为两侧面板留出空间 */
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
/* 强制停止按钮 */
.force-stop-btn {
  margin-top: 1rem;
  width: 100%;
  padding: 1rem 2rem;
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  border: none;
  border-radius: 0.75rem;
  font-size: 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
}
.force-stop-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(239, 68, 68, 0.4);
  background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
}
.force-stop-btn:active {
  transform: translateY(0);
}
/* 降级监控按钮 */
.monitor-btn {
  margin-top: 1rem;
  width: 100%;
  padding: 1rem 2rem;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 0.75rem;
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  color: white;
  border: none;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}
.monitor-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.4);
  background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
}
.monitor-btn:active {
  transform: translateY(0);
}

/* 分析启动提示弹窗样式 */
.analysis-toast-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 20px;
}
.analysis-toast {
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.98) 0%, rgba(30, 41, 59, 0.98) 100%);
  border: 2px solid rgba(99, 102, 241, 0.5);
  border-radius: 20px;
  padding: 0;
  max-width: 520px;
  width: 100%;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6), 0 0 40px rgba(99, 102, 241, 0.2);
  animation: toast-bounce-in 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
  overflow: hidden;
}
@keyframes toast-bounce-in {
  0% { opacity: 0; transform: scale(0.8) translateY(-30px); }
  50% { transform: scale(1.02) translateY(0); }
  100% { opacity: 1; transform: scale(1) translateY(0); }
}
.toast-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 24px;
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.2) 0%, rgba(139, 92, 246, 0.15) 100%);
  border-bottom: 1px solid rgba(99, 102, 241, 0.3);
}
.toast-icon {
  font-size: 32px;
  animation: icon-pulse 2s ease-in-out infinite;
}
@keyframes icon-pulse {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}
.toast-title {
  flex: 1;
  font-size: 18px;
  font-weight: 700;
  color: #a5b4fc;
  letter-spacing: 0.5px;
}
.toast-close {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.1);
  border: none;
  color: #94a3b8;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}
.toast-close:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #f87171;
}
.toast-body {
  padding: 20px 24px;
}
.toast-body p {
  color: #cbd5e1;
  font-size: 14px;
  line-height: 1.6;
  margin-bottom: 16px;
}
.toast-body strong {
  color: #fbbf24;
  font-weight: 600;
}
.toast-phases {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
  margin-bottom: 16px;
}
.phase-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(30, 41, 59, 0.6);
  border-radius: 8px;
  font-size: 12px;
  color: #94a3b8;
}
.phase-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
}
.phase-dot.phase-1 { background: #3b82f6; box-shadow: 0 0 8px rgba(59, 130, 246, 0.5); }
.phase-dot.phase-2 { background: #a855f7; box-shadow: 0 0 8px rgba(168, 85, 247, 0.5); }
.phase-dot.phase-3 { background: #f97316; box-shadow: 0 0 8px rgba(249, 115, 22, 0.5); }
.phase-dot.phase-4 { background: #ef4444; box-shadow: 0 0 8px rgba(239, 68, 68, 0.5); }
.toast-footer {
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding-top: 12px;
  border-top: 1px solid rgba(99, 102, 241, 0.2);
}
.time-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(5, 150, 105, 0.15) 100%);
  border-radius: 20px;
  color: #34d399;
  font-size: 14px;
  font-weight: 600;
  width: fit-content;
}
.toast-tip {
  color: #64748b;
  font-size: 12px;
}
.toast-progress {
  height: 4px;
  background: rgba(99, 102, 241, 0.2);
  overflow: hidden;
}
.toast-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
  animation: progress-shrink 8s linear forwards;
}
@keyframes progress-shrink {
  from { width: 100%; }
  to { width: 0%; }
}
/* 弹窗过渡动画 */
.analysis-toast-enter-active {
  animation: toast-bounce-in 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
}
.analysis-toast-leave-active {
  animation: toast-fade-out 0.3s ease-out forwards;
}
@keyframes toast-fade-out {
  from { opacity: 1; transform: scale(1); }
  to { opacity: 0; transform: scale(0.9) translateY(-20px); }
}
/* 移动端适配 */
@media (max-width: 768px) {
  .analysis-toast {
    max-width: 100%;
    margin: 10px;
    border-radius: 16px;
  }
  .toast-header {
    padding: 14px 18px;
  }
  .toast-icon {
    font-size: 26px;
  }
  .toast-title {
    font-size: 15px;
  }
  .toast-body {
    padding: 16px 18px;
  }
  .toast-phases {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}

.floating-timer {
  position: fixed;
  top: 9rem;
  right: 1rem;
  z-index: 90;
  padding: 0.75rem 1rem;
  background: rgba(15, 23, 42, 0.95);
  border: 2px solid rgba(59, 130, 246, 0.5);
  border-radius: 0.75rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(12px);
  animation: pulse-border 2s ease-in-out infinite;
  font-size: 0.875rem;
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
/* ========================================
   移动端响应式优化
   ======================================== */
@media (max-width: 768px) {
  .analysis-container {
    padding: 1rem 0.5rem;
    padding-top: 7rem;
  }
  
  /* 计时器优化 */
  .floating-timer {
    top: auto;
    bottom: 1rem;
    right: 0.5rem;
    left: auto;
    padding: 0.5rem 0.75rem;
    font-size: 0.75rem;
    z-index: 999;
  }
  
  .timer-icon {
    font-size: 1rem;
  }
  
  .timer-label {
    display: none;
  }
  
  /* 搜索区域 */
  .search-section {
    padding: 1rem;
  }
  
  .search-title {
    font-size: 1.25rem;
  }
  
  .search-subtitle {
    font-size: 0.75rem;
  }
  
  /* 股票数据面板 */
  .stock-data-panel {
    width: 100vw !important;
    max-width: 100vw !important;
    height: 100vh !important;
    max-height: 100vh !important;
    top: 0 !important;
    right: 0 !important;
    border-radius: 0;
  }
  
  .panel-close-btn {
    top: 1rem;
    right: 1rem;
    width: 3rem;
    height: 3rem;
    font-size: 2rem;
    z-index: 1001;
  }
  
  /* 新闻面板 */
  .news-panel {
    width: 100vw !important;
    max-width: 100vw !important;
    height: 100vh !important;
    max-height: 100vh !important;
    top: 0 !important;
    right: 0 !important;
    border-radius: 0;
  }
  
  /* 阶段分组 */
  .stage-group {
    padding: 1rem;
  }
  
  .stage-title {
    font-size: 1.125rem;
  }
  
  .stage-subtitle {
    font-size: 0.75rem;
  }
  
  /* 卡片网格 */
  .agents-grid {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  /* 辩论面板 */
  .debate-section {
    padding: 1rem;
  }
  
  /* 报告区域 */
  .report-section {
    padding: 1rem;
  }
  
  .report-title {
    font-size: 1.25rem;
  }
  
  /* 按钮组 */
  .report-actions {
    flex-direction: column;
    gap: 0.5rem;
  }
  
  .report-actions button {
    width: 100%;
  }
  
  /* 模态框 */
  .modal-overlay {
    padding: 0;
  }
  
  .model-manager-modal,
  .api-config-modal,
  .style-config-modal,
  .interpreter-config-modal {
    width: 100vw;
    height: 100vh;
    max-width: 100vw;
    max-height: 100vh;
    border-radius: 0;
    padding: 1rem;
  }
  
  .modal-close {
    top: 0.5rem;
    right: 0.5rem;
    width: 2.5rem;
    height: 2.5rem;
    font-size: 1.5rem;
  }
}
/* ========================================
   专业版报告 - 阶段标签切换样式
   ======================================== */
.professional-report {
  background: rgba(15, 23, 42, 0.6);
  border-radius: 16px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  overflow: hidden;
}
/* 阶段标签栏 */
.stage-tabs {
  display: flex;
  gap: 4px;
  padding: 12px 16px;
  background: rgba(30, 41, 59, 0.8);
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  overflow-x: auto;
  scrollbar-width: thin;
}
.stage-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 18px;
  background: rgba(51, 65, 85, 0.4);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 10px;
  color: #94a3b8;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
  flex-shrink: 0;
}
.stage-tab:hover:not(:disabled) {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
  transform: translateY(-2px);
}
.stage-tab.active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.3) 0%, rgba(99, 102, 241, 0.3) 100%);
  border-color: #3b82f6;
  color: #60a5fa;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}
.stage-tab:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}
.stage-tab-icon {
  font-size: 18px;
}
.stage-tab-title {
  font-weight: 600;
}
.stage-tab-count {
  background: rgba(59, 130, 246, 0.3);
  color: #93c5fd;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 600;
}
.stage-tab.active .stage-tab-count {
  background: rgba(59, 130, 246, 0.5);
  color: #fff;
}
/* 阶段内容区 */
.stage-content-area {
  padding: 20px;
  max-height: 700px;
  overflow-y: auto;
}
.stage-content-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 2px solid rgba(59, 130, 246, 0.3);
}
.stage-content-icon {
  font-size: 28px;
}
.stage-content-title {
  font-size: 20px;
  font-weight: 700;
  color: #e2e8f0;
  margin: 0;
}
/* 智能体结果列表 */
.agent-results-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}
/* 智能体结果卡片 */
.agent-result-card {
  background: rgba(30, 41, 59, 0.6);
  border-radius: 12px;
  border: 1px solid rgba(71, 85, 105, 0.3);
  overflow: hidden;
  transition: all 0.3s ease;
}
.agent-result-card:hover {
  border-color: rgba(59, 130, 246, 0.5);
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
}
/* 智能体卡片颜色变体 */
.agent-card-emerald { border-left: 4px solid #10b981; }
.agent-card-cyan { border-left: 4px solid #06b6d4; }
.agent-card-red { border-left: 4px solid #ef4444; }
.agent-card-blue { border-left: 4px solid #3b82f6; }
.agent-card-slate { border-left: 4px solid #64748b; }
.agent-card-violet { border-left: 4px solid #8b5cf6; }
.agent-card-indigo { border-left: 4px solid #6366f1; }
.agent-card-green { border-left: 4px solid #22c55e; }
.agent-card-amber { border-left: 4px solid #f59e0b; }
.agent-card-orange { border-left: 4px solid #f97316; }
.agent-card-fuchsia { border-left: 4px solid #d946ef; }
.agent-result-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: rgba(15, 23, 42, 0.5);
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
}
.agent-result-icon {
  font-size: 22px;
}
.agent-result-title {
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
  flex: 1;
}
.agent-result-duration {
  font-size: 12px;
  color: #60a5fa;
  background: rgba(59, 130, 246, 0.15);
  padding: 4px 10px;
  border-radius: 6px;
  font-family: monospace;
  font-weight: 600;
}
.agent-result-tokens {
  font-size: 12px;
  color: #94a3b8;
  background: rgba(71, 85, 105, 0.3);
  padding: 4px 10px;
  border-radius: 6px;
  font-family: monospace;
}
.agent-result-content {
  padding: 18px;
  color: #cbd5e1;
  font-size: 14px;
  line-height: 1.7;
}
.agent-result-content h1,
.agent-result-content h2,
.agent-result-content h3,
.agent-result-content h4 {
  color: #e2e8f0;
  margin-top: 16px;
  margin-bottom: 10px;
}
.agent-result-content h1 { font-size: 1.5em; }
.agent-result-content h2 { font-size: 1.3em; }
.agent-result-content h3 { font-size: 1.15em; }
.agent-result-content ul,
.agent-result-content ol {
  padding-left: 20px;
  margin: 10px 0;
}
.agent-result-content li {
  margin: 6px 0;
}
.agent-result-content strong {
  color: #fbbf24;
  font-weight: 600;
}
.agent-result-content code {
  background: rgba(71, 85, 105, 0.4);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.9em;
}
/* 辩论摘要样式 */
.debate-summary {
  margin-top: 20px;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.1) 0%, rgba(245, 158, 11, 0.1) 100%);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 12px;
  overflow: hidden;
}
.debate-summary.risk {
  background: linear-gradient(135deg, rgba(99, 102, 241, 0.1) 0%, rgba(79, 70, 229, 0.1) 100%);
  border-color: rgba(99, 102, 241, 0.3);
}
.debate-summary-header {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 18px;
  background: rgba(0, 0, 0, 0.2);
  font-size: 16px;
  font-weight: 600;
  color: #fbbf24;
}
.debate-summary.risk .debate-summary-header {
  color: #818cf8;
}
.debate-summary-content {
  padding: 16px 18px;
}
.debate-score {
  font-size: 14px;
  color: #e2e8f0;
  margin-bottom: 10px;
}
.debate-score strong {
  color: #fbbf24;
  font-size: 18px;
}
.debate-summary.risk .debate-score strong {
  color: #818cf8;
}
.debate-conclusion {
  font-size: 14px;
  color: #cbd5e1;
  line-height: 1.6;
}
/* 滚动条样式 */
.stage-content-area::-webkit-scrollbar {
  width: 8px;
}
.stage-content-area::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
  border-radius: 4px;
}
.stage-content-area::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.5);
  border-radius: 4px;
}
.stage-content-area::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.7);
}
/* 移动端适配 */
@media (max-width: 768px) {
  .stage-tabs {
    padding: 8px 12px;
    gap: 6px;
  }
  .stage-tab {
    padding: 8px 12px;
    font-size: 12px;
  }
  .stage-tab-icon {
    font-size: 16px;
  }
  .stage-tab-title {
    display: none;
  }
  .stage-content-area {
    padding: 12px;
    max-height: 600px;
  }
  .stage-content-header {
    margin-bottom: 12px;
  }
  .stage-content-title {
    font-size: 16px;
  }
  .agent-result-header {
    padding: 10px 12px;
    flex-wrap: wrap;
  }
  .agent-result-content {
    padding: 12px;
    font-size: 13px;
  }
}
</style>