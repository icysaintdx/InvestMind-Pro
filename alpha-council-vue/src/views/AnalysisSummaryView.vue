<template>
  <div class="analysis-summary-container">
    <div class="page-header">
      <div>
        <h1>🧭 分析总结</h1>
        <p class="subtitle">串联智能分析 → 策略 → 回测 → 模拟 → 跟踪的闭环总控面板</p>
      </div>
      <div class="header-actions">
        <button class="btn-secondary" @click="loadLatestAnalysis" :disabled="loading">
          🔄 刷新
        </button>
      </div>
    </div>

    <div v-if="error" class="error-banner">
      <span>⚠️ {{ error }}</span>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>正在获取最新分析...</p>
    </div>

    <div v-else-if="!latestSession" class="empty-state">
      <div class="empty-icon">📭</div>
      <h3>暂无可展示的分析记录</h3>
      <p>请先在“智能分析”页面完成一次分析，或稍后刷新</p>
      <button class="btn-primary" @click="$emit('goto-analysis')">立即前往智能分析</button>
    </div>

    <div v-else class="content-grid">
      <!-- 核心结论 -->
      <section class="card highlight-card">
        <header>
          <div>
            <p class="section-label">最新分析</p>
            <h2>{{ latestSession.stock_code }} · {{ latestSession.stock_name || '未命名' }}</h2>
          </div>
          <span class="status-chip" :class="`status-${latestSession.status}`">{{ getStatusText(latestSession.status) }}</span>
        </header>
        <div class="session-meta">
          <div class="meta-item" v-for="item in sessionMeta" :key="item.label">
            <p class="meta-label">{{ item.label }}</p>
            <p class="meta-value">{{ item.value }}</p>
          </div>
        </div>
        <div class="summary-block" v-if="analysisHighlights.length">
          <h3>综合要点</h3>
          <ul>
            <li v-for="point in analysisHighlights" :key="point">
              {{ point }}
            </li>
          </ul>
        </div>
        <div v-else class="summary-placeholder">
          <p>⏳ 等待智能体输出同步到数据库...</p>
        </div>
      </section>

      <!-- 后续动作 -->
      <section class="card actions-card">
        <h3>📌 下一步动作</h3>
        <p class="card-desc">根据分析结果发起策略回路，保持闭环一致性</p>
        <div class="action-list">
          <button class="action-item" @click="handleStrategySelection" :disabled="loadingStrategy">
            <div>
              <h4>智能策略推荐</h4>
              <p>调用策略选择LLM，获取可执行策略组合</p>
            </div>
            <span>{{ loadingStrategy ? '⏳' : '➡️' }}</span>
          </button>
          <button class="action-item" @click="handleBacktest" :disabled="loadingBacktest">
            <div>
              <h4>一键回测</h4>
              <p>跳转到策略回测并自动填入股票信息</p>
            </div>
            <span>{{ loadingBacktest ? '⏳' : '➡️' }}</span>
          </button>
          <button class="action-item" @click="handlePaperTrading" :disabled="loadingPaperTrading">
            <div>
              <h4>推送到模拟交易</h4>
              <p>将推荐策略生成模拟下单计划</p>
            </div>
            <span>{{ loadingPaperTrading ? '⏳' : '➡️' }}</span>
          </button>
          <button class="action-item" @click="handleCreateTracking" :disabled="loadingTracking">
            <div>
              <h4>创建跟踪任务</h4>
              <p>将本次结论纳入持续监控，触发LLM巡检</p>
            </div>
            <span>{{ loadingTracking ? '⏳' : '➡️' }}</span>
          </button>
        </div>
      </section>

      <!-- 策略推荐结果 -->
      <section v-if="strategyRecommendations.length || loadingStrategy" class="card strategy-card">
        <div class="section-header">
          <h3>🎯 策略推荐</h3>
          <span class="badge" v-if="strategyRecommendations.length">{{ strategyRecommendations.length }} 个策略</span>
        </div>
        <p class="card-desc" v-if="strategyReasoning">{{ strategyReasoning }}</p>
        <div v-if="loadingStrategy && !strategyRecommendations.length" class="loading-inline">
          <div class="spinner"></div>
          <p>策略选择中...</p>
        </div>
        <div v-else-if="strategyRecommendations.length" class="strategy-grid">
          <div
            v-for="(strategy, index) in strategyRecommendations"
            :key="strategy.strategy_id"
            class="strategy-chip"
            :class="getMedalClass(index)"
          >
            <!-- 奖牌标签 -->
            <div class="medal-badge" :class="getMedalClass(index)">
              <span class="medal-icon">{{ getMedalIcon(index) }}</span>
              <span class="medal-text">{{ getMedalText(index) }}</span>
            </div>
            <!-- 策略头部 -->
            <div class="chip-header">
              <h4 class="strategy-name">{{ strategy.strategy_name }}</h4>
              <div class="confidence-badge">
                <span class="confidence-label">置信度</span>
                <span class="confidence-value">{{ (strategy.confidence * 100).toFixed(1) }}%</span>
              </div>
            </div>
            <!-- 置信度进度条 -->
            <div class="confidence-bar-wrapper">
              <div class="confidence-bar" :style="{ width: (strategy.confidence * 100) + '%' }"></div>
            </div>
            <!-- 推荐理由 -->
            <div class="chip-reason">
              <span class="reason-label">推荐理由</span>
              <p class="reason-text">{{ strategy.reason }}</p>
            </div>
            <!-- 参数配置 -->
            <div v-if="strategy.parameters && Object.keys(strategy.parameters).length" class="chip-params">
              <span class="params-label">参数配置</span>
              <div class="params-grid">
                <div v-for="(value, key) in strategy.parameters" :key="key" class="param-item">
                  <span class="param-key">{{ formatParamKey(key) }}</span>
                  <span class="param-value">{{ value }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <!-- 执行摘要 -->
      <section v-if="hasExecutionDigest" class="card execution-card">
        <div class="section-header">
          <h3>🔧 执行摘要</h3>
          <span class="badge" v-if="backtestDigest">回测完成</span>
        </div>

        <!-- 回测结果详情 -->
        <div v-if="backtestDigest" class="backtest-detail">
          <!-- 策略信息头部 -->
          <div class="backtest-header">
            <div class="strategy-info">
              <h4>{{ backtestDigest.strategyId }}</h4>
              <span class="backtest-time">{{ formatDateTime(backtestDigest.generatedAt) }}</span>
            </div>
            <div class="confidence-display" v-if="primaryStrategy">
              <span class="conf-label">置信度</span>
              <span class="conf-value">{{ (primaryStrategy.confidence * 100).toFixed(1) }}%</span>
            </div>
          </div>

          <!-- 四个区块网格 -->
          <div class="backtest-grid">
            <!-- 核心指标 -->
            <div class="backtest-block metrics-block">
              <div class="block-header">
                <span class="block-icon">📊</span>
                <span class="block-title">核心指标</span>
              </div>
              <div class="block-content">
                <div class="metric-row">
                  <span class="metric-label">总收益率</span>
                  <span class="metric-value" :class="getValueClass(backtestDigest.metrics.totalReturn)">
                    {{ formatPercent(backtestDigest.metrics.totalReturn) }}
                  </span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">年化收益</span>
                  <span class="metric-value" :class="getValueClass(backtestDigest.metrics.annualReturn)">
                    {{ formatPercent(backtestDigest.metrics.annualReturn) }}
                  </span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">夏普比率</span>
                  <span class="metric-value">{{ (backtestDigest.metrics.sharpeRatio || 0).toFixed(2) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">最大回撤</span>
                  <span class="metric-value negative">{{ formatPercent(backtestDigest.metrics.maxDrawdown) }}</span>
                </div>
              </div>
            </div>

            <!-- 交易统计 -->
            <div class="backtest-block trades-block">
              <div class="block-header">
                <span class="block-icon">📈</span>
                <span class="block-title">交易统计</span>
              </div>
              <div class="block-content">
                <div class="metric-row">
                  <span class="metric-label">总交易次数</span>
                  <span class="metric-value">{{ backtestDigest.metrics.totalTrades || backtestDigest.metrics.total_trades || 0 }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">胜率</span>
                  <span class="metric-value">{{ formatPercent(backtestDigest.metrics.winRate || backtestDigest.metrics.win_rate) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">盈亏比</span>
                  <span class="metric-value">{{ (backtestDigest.metrics.profitFactor || backtestDigest.metrics.profit_factor || 0).toFixed(2) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">平均持仓</span>
                  <span class="metric-value">{{ backtestDigest.metrics.avgHoldingDays || backtestDigest.metrics.avg_holding_days || '-' }} 天</span>
                </div>
              </div>
            </div>

            <!-- 回测参数 -->
            <div class="backtest-block params-block">
              <div class="block-header">
                <span class="block-icon">⚙️</span>
                <span class="block-title">回测参数</span>
              </div>
              <div class="block-content">
                <div class="metric-row">
                  <span class="metric-label">初始资金</span>
                  <span class="metric-value">¥{{ formatAmount(100000) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">回测周期</span>
                  <span class="metric-value">1年</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">手续费率</span>
                  <span class="metric-value">0.03%</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">滑点设置</span>
                  <span class="metric-value">0.1%</span>
                </div>
              </div>
            </div>

            <!-- 风险评估 -->
            <div class="backtest-block risk-block">
              <div class="block-header">
                <span class="block-icon">⚠️</span>
                <span class="block-title">风险评估</span>
              </div>
              <div class="block-content">
                <div class="metric-row">
                  <span class="metric-label">波动率</span>
                  <span class="metric-value">{{ formatPercent(backtestDigest.metrics.volatility) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">最大连亏</span>
                  <span class="metric-value">{{ backtestDigest.metrics.maxConsecutiveLosses || backtestDigest.metrics.max_consecutive_losses || 0 }} 次</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">风险等级</span>
                  <span class="metric-value" :class="getRiskClass(backtestDigest.metrics)">{{ getRiskLevel(backtestDigest.metrics) }}</span>
                </div>
                <div class="metric-row">
                  <span class="metric-label">建议仓位</span>
                  <span class="metric-value">{{ getSuggestedPosition(backtestDigest.metrics) }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 快速评价 -->
          <div class="quick-evaluation">
            <div class="eval-header">
              <span class="eval-icon">💡</span>
              <span class="eval-title">快速评价</span>
            </div>
            <!-- 风险等级渐变条 -->
            <div class="risk-bar-container">
              <div class="risk-bar-gradient"></div>
              <div class="risk-bar-indicator" :style="{ left: getRiskBarPosition(backtestDigest.metrics) + '%' }">
                <span class="risk-indicator-dot"></span>
              </div>
              <div class="risk-bar-labels">
                <span>低风险</span>
                <span>中风险</span>
                <span>高风险</span>
              </div>
            </div>
            <div class="eval-content">
              <div class="eval-item" :class="getEvalClass('return', backtestDigest.metrics)">
                <span class="eval-label">收益表现</span>
                <span class="eval-value">{{ getReturnEval(backtestDigest.metrics) }}</span>
              </div>
              <div class="eval-item" :class="getEvalClass('risk', backtestDigest.metrics)">
                <span class="eval-label">风险控制</span>
                <span class="eval-value">{{ getRiskEval(backtestDigest.metrics) }}</span>
              </div>
              <div class="eval-item" :class="getEvalClass('stability', backtestDigest.metrics)">
                <span class="eval-label">稳定性</span>
                <span class="eval-value">{{ getStabilityEval(backtestDigest.metrics) }}</span>
              </div>
              <div class="eval-item" :class="getEvalClass('overall', backtestDigest.metrics)">
                <span class="eval-label">综合评分</span>
                <span class="eval-value">{{ getOverallEval(backtestDigest.metrics) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- 模拟交易和跟踪任务 -->
        <div v-if="autoTradingTask || trackingTask" class="other-tasks">
          <div class="task-item" v-if="autoTradingTask">
            <div class="task-header">
              <span class="task-icon">🤖</span>
              <strong>自动模拟交易</strong>
              <span class="task-time">{{ formatDateTime(autoTradingTask.created_at) }}</span>
            </div>
            <div class="task-details">
              <span>任务ID: {{ autoTradingTask.task_id }}</span>
              <span>初始资金: ¥{{ formatAmount(autoTradingTask.initial_capital) }}</span>
              <span>状态: {{ autoTradingTask.status }}</span>
            </div>
          </div>
          <div class="task-item" v-if="trackingTask">
            <div class="task-header">
              <span class="task-icon">👁️</span>
              <strong>跟踪任务</strong>
              <span class="task-time">{{ formatDateTime(trackingTask.created_at) }}</span>
            </div>
            <div class="task-details">
              <span>任务ID: {{ trackingTask.task_id }}</span>
              <span>状态: {{ getTaskStatusText(trackingTask.status) }}</span>
              <span>周期: {{ trackingTask.duration_days }} 天</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 智能体输出预览 -->
      <section class="card agents-card">
        <div class="section-header">
          <h3>🧠 智能体输出预览</h3>
          <span>{{ agentResults.length }}/21</span>
        </div>
        <div class="agents-list">
          <div 
            v-for="agent in agentResults" 
            :key="agent.agent_id" 
            class="agent-chip"
          >
            <div class="agent-head">
              <strong>{{ agent.agent_name }}</strong>
              <span class="badge">{{ agent.tokens || 0 }} tokens</span>
            </div>
            <p class="agent-output">{{ agent.output ? agent.output.slice(0, 160) + (agent.output.length > 160 ? '...' : '') : '尚未完成' }}</p>
          </div>
        </div>
      </section>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'

export default {
  name: 'AnalysisSummaryView',
  emits: ['goto-analysis', 'goto-backtest', 'goto-paper-trading', 'goto-tracking'],
  setup(props, { emit }) {
    const loading = ref(false)
    const error = ref('')
    const latestSession = ref(null)
    const agentResults = ref([])

    const loadingStrategy = ref(false)
    const loadingBacktest = ref(false)
    const loadingPaperTrading = ref(false)
    const loadingTracking = ref(false)

    const strategyRecommendations = ref([])
    const strategyReasoning = ref('')
    const backtestDigest = ref(null)
    const autoTradingTask = ref(null)
    const trackingTask = ref(null)

    const loadLatestAnalysis = async () => {
      loading.value = true
      error.value = ''
      try {
        const response = await fetch('/api/analysis/db/history/recent?limit=1')
        if (!response.ok) throw new Error('无法获取最近的分析记录')
        const data = await response.json()
        const session = data.sessions?.[0]
        latestSession.value = session || null

        if (session) {
          await loadSessionDetails(session.session_id)
        } else {
          agentResults.value = []
        }
      } catch (err) {
        console.error('[AnalysisSummary] loadLatestAnalysis error:', err)
        error.value = err.message || '加载失败'
      } finally {
        loading.value = false
      }
    }

    const loadSessionDetails = async (sessionId) => {
      try {
        const response = await fetch(`/api/analysis/db/history/session/${sessionId}/full`)
        if (!response.ok) throw new Error('无法获取分析详情')
        const data = await response.json()
        agentResults.value = data.agent_results || []
      } catch (err) {
        console.error('[AnalysisSummary] loadSessionDetails error:', err)
        error.value = err.message || '详情加载失败'
      }
    }

    const getStatusText = (status) => {
      const map = {
        created: '已创建',
        running: '运行中',
        completed: '已完成',
        error: '失败'
      }
      return map[status] || status
    }

    const sessionMeta = computed(() => {
      if (!latestSession.value) return []
      const createdAt = latestSession.value.created_at
        ? new Date(latestSession.value.created_at).toLocaleString('zh-CN')
        : '-'
      return [
        { label: '分析时间', value: createdAt },
        { label: '进度', value: `${latestSession.value.progress || 0}%` },
        { label: '阶段', value: latestSession.value.current_stage || '-' }
      ]
    })

    const analysisHighlights = computed(() => {
      if (!agentResults.value.length) return []
      const highlights = agentResults.value
        .filter(item => item.output)
        .slice(0, 4)
        .map(item => `${item.agent_name}：${item.output.replace(/\n/g, ' ').slice(0, 80)}...`)
      return highlights
    })

    const strategyCount = computed(() => strategyRecommendations.value.length)
    const primaryStrategy = computed(() => strategyRecommendations.value[0] || null)
    const hasExecutionDigest = computed(() => {
      return Boolean(backtestDigest.value || autoTradingTask.value || trackingTask.value)
    })

    const normalizePercentValue = (value) => {
      if (value === null || value === undefined) return null
      if (typeof value === 'number') {
        const abs = Math.abs(value)
        return abs > 1 ? value : value * 100
      }
      const parsed = parseFloat(value.toString().replace('%', ''))
      return Number.isNaN(parsed) ? null : parsed
    }

    const formatPercent = (value) => {
      const normalized = normalizePercentValue(value)
      if (normalized === null) return '-'
      return `${normalized.toFixed(2)}%`
    }

    const formatAmount = (value) => {
      if (value === null || value === undefined || Number.isNaN(value)) return '-'
      const num = typeof value === 'number' ? value : parseFloat(value)
      if (Number.isNaN(num)) return '-'
      return num.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    const formatDateTime = (value) => {
      if (!value) return '-'
      const date = new Date(value)
      return Number.isNaN(date.getTime()) ? '-' : date.toLocaleString('zh-CN', { hour12: false })
    }

    const getTaskStatusText = (status) => {
      const map = {
        active: '进行中',
        paused: '已暂停',
        completed: '已完成'
      }
      return map[status] || status || '未知'
    }

    const guardSession = () => {
      if (!latestSession.value) {
        window.$toast?.info('暂无分析记录，请先完成一次智能分析')
        return false
      }
      return true
    }

    const showToast = (type, message) => {
      if (window.$toast && typeof window.$toast[type] === 'function') {
        window.$toast[type](message)
      } else {
        console[type === 'error' ? 'error' : 'log'](message)
      }
    }

    const buildAnalysisPayload = () => {
      const session = latestSession.value
      if (!session) return null
      const summary = session.analysis_summary
        || analysisHighlights.value.join('\n')
        || '暂无分析总结，建议尽快运行一次完整分析。'

      const safeNumber = (value) => {
        if (value === null || value === undefined) return null
        const num = typeof value === 'number' ? value : parseFloat(value)
        return Number.isNaN(num) ? null : num
      }

      return {
        stock_code: session.stock_code,
        stock_name: session.stock_name || '',
        analysis_summary: summary,
        technical_score: safeNumber(session.technical_score ?? session.metrics?.technical_score),
        fundamental_score: safeNumber(session.fundamental_score ?? session.metrics?.fundamental_score),
        sentiment_score: safeNumber(session.sentiment_score ?? session.metrics?.sentiment_score),
        risk_level: session.risk_level || '未评估',
        investment_advice: session.investment_advice || session.final_recommendation || ''
      }
    }

    const getRiskPreference = (session) => {
      return session?.risk_preference || 'moderate'
    }

    const resolveStrategyId = () => {
      return primaryStrategy.value?.strategy_id || 'vegas_adx'
    }

    const formatDateForRequest = (date) => date.toISOString().slice(0, 10)

    const getDefaultDateRange = () => {
      const end = new Date()
      const start = new Date()
      start.setFullYear(end.getFullYear() - 1)
      return {
        start: formatDateForRequest(start),
        end: formatDateForRequest(end)
      }
    }

    const handleStrategySelection = async () => {
      if (!guardSession()) return
      if (loadingStrategy.value) return
      const analysisPayload = buildAnalysisPayload()
      if (!analysisPayload) return
      loadingStrategy.value = true
      try {
        const response = await fetch('/api/strategy-selection/select', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            analysis_result: analysisPayload,
            risk_preference: getRiskPreference(latestSession.value),
            max_recommendations: 3
          })
        })

        const data = await response.json()
        if (!response.ok || data.success === false) {
          throw new Error(data.detail || '策略推荐失败')
        }

        strategyRecommendations.value = data.recommendations || []
        strategyReasoning.value = data.reasoning || ''
        showToast('success', '策略推荐完成')
      } finally {
        loadingStrategy.value = false
      }
    }

    const handleBacktest = async () => {
      if (!guardSession() || loadingBacktest.value) return
      const session = latestSession.value
      const strategyId = resolveStrategyId()
      const { start, end } = getDefaultDateRange()
      loadingBacktest.value = true
      try {
        const response = await fetch('/api/backtest/quick', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stock_code: session.stock_code,
            strategy_name: strategyId,
            start_date: start,
            end_date: end,
            initial_capital: 100000,
            strategy_params: primaryStrategy.value?.parameters || {},
            risk_params: {}
          })
        })

        const data = await response.json()
        if (!response.ok || data.success === false) {
          throw new Error(data.detail || '回测失败')
        }

        // 转换后端返回的下划线格式为驼峰格式
        const rawMetrics = data.metrics || {}
        backtestDigest.value = {
          generatedAt: new Date().toISOString(),
          strategyId,
          metrics: {
            totalReturn: rawMetrics.total_return ?? rawMetrics.totalReturn,
            maxDrawdown: rawMetrics.max_drawdown ?? rawMetrics.maxDrawdown,
            sharpeRatio: rawMetrics.sharpe_ratio ?? rawMetrics.sharpeRatio ?? 0,
            annualReturn: rawMetrics.annual_return ?? rawMetrics.annualReturn,
            winRate: rawMetrics.win_rate ?? rawMetrics.winRate,
            totalTrades: rawMetrics.total_trades ?? rawMetrics.totalTrades,
            // 保留原始数据以备其他用途
            ...rawMetrics
          },
          summary: data.summary || {}
        }
        showToast('success', '回测完成，可在下方查看摘要')
      } catch (err) {
        showToast('error', err.message || '回测失败')
      } finally {
        loadingBacktest.value = false
      }
    }

    const handlePaperTrading = async () => {
      if (!guardSession() || loadingPaperTrading.value) return
      const analysisPayload = buildAnalysisPayload()
      if (!analysisPayload) return
      loadingPaperTrading.value = true
      try {
        const response = await fetch('/api/auto-trading/start', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stock_code: latestSession.value.stock_code,
            analysis_result: analysisPayload,
            strategy_id: resolveStrategyId(),
            initial_capital: 100000,
            auto_select_strategy: !primaryStrategy.value,
            risk_preference: getRiskPreference(latestSession.value)
          })
        })

        const data = await response.json()
        if (!response.ok || data.success === false) {
          throw new Error(data.detail || '自动交易任务创建失败')
        }

        autoTradingTask.value = data.task
        showToast('success', '自动模拟交易任务已创建')
      } catch (err) {
        showToast('error', err.message || '模拟交易创建失败')
      } finally {
        loadingPaperTrading.value = false
      }
    }

    const handleCreateTracking = async () => {
      if (!guardSession() || loadingTracking.value) return
      const analysisPayload = buildAnalysisPayload()
      if (!analysisPayload) return
      loadingTracking.value = true
      try {
        const response = await fetch('/api/tracking/create', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            stock_code: latestSession.value.stock_code,
            analysis_result: analysisPayload,
            strategy_id: resolveStrategyId(),
            auto_trading_task_id: autoTradingTask.value?.task_id,
            duration_days: 30
          })
        })

        const data = await response.json()
        if (!response.ok || data.success === false) {
          throw new Error(data.detail || '跟踪任务创建失败')
        }

        trackingTask.value = data.task
        showToast('success', '跟踪任务已创建')
      } catch (err) {
        showToast('error', err.message || '跟踪任务创建失败')
      } finally {
        loadingTracking.value = false
      }
    }

    // ==================== 策略推荐辅助方法 ====================
    const getMedalClass = (index) => {
      const classes = ['gold', 'silver', 'bronze']
      return classes[index] || 'bronze'
    }

    const getMedalIcon = (index) => {
      const icons = ['🥇', '🥈', '🥉']
      return icons[index] || '🏅'
    }

    const getMedalText = (index) => {
      const texts = ['首选策略', '备选策略', '第三策略']
      return texts[index] || `第${index + 1}策略`
    }

    const formatParamKey = (key) => {
      const keyMap = {
        'trend_period': '趋势周期',
        'momentum_period': '动量周期',
        'volatility_threshold': '波动率阈值',
        'macd_fast': 'MACD快线',
        'macd_slow': 'MACD慢线',
        'macd_signal': '信号线周期',
        'volume_threshold': '成交量阈值',
        'bollinger_period': '布林带周期',
        'bollinger_std': '标准差倍数',
        'breakout_threshold': '突破阈值',
        'rsi_period': 'RSI周期',
        'rsi_overbought': 'RSI超买',
        'rsi_oversold': 'RSI超卖',
        'atr_period': 'ATR周期',
        'atr_multiplier': 'ATR倍数',
        'stop_loss': '止损比例',
        'take_profit': '止盈比例',
        'position_size': '仓位大小'
      }
      return keyMap[key] || key
    }

    // ==================== 回测评估辅助方法 ====================
    const getValueClass = (value) => {
      if (value === null || value === undefined) return ''
      const num = normalizePercentValue(value)
      if (num === null) return ''
      return num >= 0 ? 'positive' : 'negative'
    }

    const getRiskLevel = (metrics) => {
      const maxDrawdown = Math.abs(normalizePercentValue(metrics.maxDrawdown) || 0)
      if (maxDrawdown < 10) return '低风险'
      if (maxDrawdown < 20) return '中等风险'
      if (maxDrawdown < 30) return '较高风险'
      return '高风险'
    }

    const getRiskClass = (metrics) => {
      const maxDrawdown = Math.abs(normalizePercentValue(metrics.maxDrawdown) || 0)
      if (maxDrawdown < 10) return 'low-risk'
      if (maxDrawdown < 20) return 'medium-risk'
      return 'high-risk'
    }

    const getRiskBarPosition = (metrics) => {
      const maxDrawdown = Math.abs(normalizePercentValue(metrics.maxDrawdown) || 0)
      // 将回撤映射到0-100的位置，0%回撤=0位置(绿色)，40%+回撤=100位置(红色)
      return Math.min(100, Math.max(0, (maxDrawdown / 40) * 100))
    }

    const getSuggestedPosition = (metrics) => {
      const maxDrawdown = Math.abs(normalizePercentValue(metrics.maxDrawdown) || 0)
      const sharpe = metrics.sharpeRatio || 0
      if (sharpe > 1.5 && maxDrawdown < 15) return '60-80%'
      if (sharpe > 1 && maxDrawdown < 20) return '40-60%'
      if (sharpe > 0.5 && maxDrawdown < 30) return '20-40%'
      return '10-20%'
    }

    const getReturnEval = (metrics) => {
      const totalReturn = normalizePercentValue(metrics.totalReturn) || 0
      if (totalReturn > 30) return '优秀'
      if (totalReturn > 15) return '良好'
      if (totalReturn > 0) return '一般'
      return '较差'
    }

    const getRiskEval = (metrics) => {
      const maxDrawdown = Math.abs(normalizePercentValue(metrics.maxDrawdown) || 0)
      if (maxDrawdown < 10) return '优秀'
      if (maxDrawdown < 20) return '良好'
      if (maxDrawdown < 30) return '一般'
      return '较差'
    }

    const getStabilityEval = (metrics) => {
      const sharpe = metrics.sharpeRatio || 0
      if (sharpe > 1.5) return '优秀'
      if (sharpe > 1) return '良好'
      if (sharpe > 0.5) return '一般'
      return '较差'
    }

    const getOverallEval = (metrics) => {
      const totalReturn = normalizePercentValue(metrics.totalReturn) || 0
      const maxDrawdown = Math.abs(normalizePercentValue(metrics.maxDrawdown) || 0)
      const sharpe = metrics.sharpeRatio || 0

      let score = 0
      if (totalReturn > 20) score += 2
      else if (totalReturn > 10) score += 1

      if (maxDrawdown < 15) score += 2
      else if (maxDrawdown < 25) score += 1

      if (sharpe > 1) score += 2
      else if (sharpe > 0.5) score += 1

      if (score >= 5) return 'A级'
      if (score >= 4) return 'B级'
      if (score >= 2) return 'C级'
      return 'D级'
    }

    const getEvalClass = (type, metrics) => {
      let eval_result
      switch (type) {
        case 'return': eval_result = getReturnEval(metrics); break
        case 'risk': eval_result = getRiskEval(metrics); break
        case 'stability': eval_result = getStabilityEval(metrics); break
        case 'overall': eval_result = getOverallEval(metrics); break
        default: return ''
      }
      if (eval_result === '优秀' || eval_result === 'A级') return 'eval-excellent'
      if (eval_result === '良好' || eval_result === 'B级') return 'eval-good'
      if (eval_result === '一般' || eval_result === 'C级') return 'eval-average'
      return 'eval-poor'
    }

    onMounted(() => {
      loadLatestAnalysis()
    })

    return {
      loading,
      error,
      latestSession,
      agentResults,
      sessionMeta,
      analysisHighlights,
      strategyRecommendations,
      strategyReasoning,
      strategyCount,
      primaryStrategy,
      backtestDigest,
      autoTradingTask,
      trackingTask,
      hasExecutionDigest,
      loadingStrategy,
      loadingBacktest,
      loadingPaperTrading,
      loadingTracking,
      loadLatestAnalysis,
      getStatusText,
      handleStrategySelection,
      handleBacktest,
      handlePaperTrading,
      handleCreateTracking,
      formatPercent,
      formatAmount,
      formatDateTime,
      getTaskStatusText,
      // 新增方法
      getMedalClass,
      getMedalIcon,
      getMedalText,
      formatParamKey,
      getValueClass,
      getRiskLevel,
      getRiskClass,
      getRiskBarPosition,
      getSuggestedPosition,
      getReturnEval,
      getRiskEval,
      getStabilityEval,
      getOverallEval,
      getEvalClass
    }
  }
}
</script>

<style scoped>
.analysis-summary-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: calc(100vh - 160px);
  color: #e2e8f0; /* 设置默认文字颜色 */
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  margin-bottom: 0.25rem;
  color: #f1f5f9; /* 标题颜色 */
}

.subtitle {
  color: rgba(255, 255, 255, 0.65);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-primary,
.btn-secondary {
  border: none;
  border-radius: 12px;
  padding: 0.65rem 1.25rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #fff;
}

.btn-secondary {
  background: rgba(148, 163, 184, 0.15);
  color: #e2e8f0;
}

.btn-primary:disabled,
.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.error-banner {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.4);
  padding: 0.75rem 1rem;
  border-radius: 12px;
  margin-bottom: 1.5rem;
}

.loading-state,
.empty-state {
  border: 1px dashed rgba(148, 163, 184, 0.3);
  border-radius: 16px;
  padding: 3rem;
  text-align: center;
  color: rgba(226, 232, 240, 0.8);
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(148, 163, 184, 0.3);
  border-top-color: #60a5fa;
  border-radius: 50%;
  margin: 0 auto 1rem;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 0.75rem;
}

.content-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.card {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 18px;
  padding: 1.5rem;
  box-shadow: 0 15px 35px rgba(15, 23, 42, 0.4);
  color: #e2e8f0; /* 卡片文字颜色 */
}

.highlight-card header,
.section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.highlight-card h2,
.section-header h3,
.card h3,
.card h4 {
  color: #f1f5f9; /* 标题颜色 */
}

.section-label {
  font-size: 0.85rem;
  letter-spacing: 0.05em;
  color: rgba(148, 163, 184, 0.8);
}

.status-chip {
  border-radius: 999px;
  padding: 0.25rem 0.85rem;
  font-size: 0.9rem;
}

.status-completed {
  background: rgba(34, 197, 94, 0.15);
  color: #4ade80;
}

.status-running {
  background: rgba(59, 130, 246, 0.15);
  color: #93c5fd;
}

.status-error {
  background: rgba(239, 68, 68, 0.15);
  color: #fca5a5;
}

.session-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
  gap: 1rem;
  margin: 1.5rem 0;
}

.meta-label {
  font-size: 0.8rem;
  color: rgba(148, 163, 184, 0.8);
}

.meta-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #f1f5f9; /* 数值颜色 */
}

.summary-block ul {
  margin: 1rem 0 0;
  padding-left: 1.5rem;
  color: #e2e8f0; /* 列表颜色 */
}

.summary-block li {
  color: #e2e8f0; /* 列表项颜色 */
  margin-bottom: 0.5rem;
}

.summary-placeholder {
  border: 1px dashed rgba(148, 163, 184, 0.3);
  border-radius: 12px;
  padding: 1rem;
  color: rgba(226, 232, 240, 0.8);
  text-align: center;
}

.actions-card {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.card-desc {
  color: rgba(148, 163, 184, 0.9);
}

.action-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.action-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-radius: 14px;
  padding: 1rem 1.25rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(30, 41, 59, 0.6);
  color: #e2e8f0; /* 按钮文字颜色 */
  cursor: pointer;
  transition: border-color 0.2s, transform 0.2s;
}

.action-item h4,
.action-item p {
  color: #e2e8f0; /* 确保内部文字颜色 */
}

.action-item:hover {
  border-color: rgba(99, 102, 241, 0.8);
  transform: translateY(-2px);
}

.action-item:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.agents-card {
  grid-column: 1 / -1;
}

.agents-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1rem;
  margin-top: 1rem;
  max-height: 420px;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.agent-chip {
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 14px;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.4);
}

.agent-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.badge {
  font-size: 0.75rem;
  color: rgba(148, 163, 184, 0.9);
}

.agent-output {
  font-size: 0.9rem;
  color: rgba(226, 232, 240, 0.85);
}

@media (max-width: 1024px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

/* ==================== 策略推荐样式 ==================== */
.strategy-card {
  grid-column: 1 / -1;
  display: block !important;
}

.strategy-card .section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.25rem;
  margin-top: 1rem;
}

@media (max-width: 1200px) {
  .strategy-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .strategy-grid {
    grid-template-columns: 1fr;
  }
}

.strategy-chip {
  border-radius: 14px;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.6);
  display: block;
  position: relative;
  transition: transform 0.2s, box-shadow 0.2s;
}

.strategy-chip:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.3);
}

/* 金牌 - 首选策略 */
.strategy-chip.gold {
  border: 2px solid #fbbf24;
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
  box-shadow: 0 4px 16px rgba(251, 191, 36, 0.2);
}

/* 银牌 - 备选策略 */
.strategy-chip.silver {
  border: 2px solid #94a3b8;
  background: linear-gradient(135deg, rgba(148, 163, 184, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
  box-shadow: 0 4px 16px rgba(148, 163, 184, 0.15);
}

/* 铜牌 - 第三策略 */
.strategy-chip.bronze {
  border: 2px solid #cd7f32;
  background: linear-gradient(135deg, rgba(205, 127, 50, 0.15) 0%, rgba(15, 23, 42, 0.6) 100%);
  box-shadow: 0 4px 16px rgba(205, 127, 50, 0.15);
}

/* 奖牌标签 */
.medal-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
  padding: 0.25rem 0.6rem;
  border-radius: 16px;
  font-size: 0.75rem;
  font-weight: 600;
  margin-bottom: 0.6rem;
}

.medal-badge.gold {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
  color: #1e1b4b;
}

.medal-badge.silver {
  background: linear-gradient(135deg, #e2e8f0, #94a3b8);
  color: #1e293b;
}

.medal-badge.bronze {
  background: linear-gradient(135deg, #cd7f32, #b8860b);
  color: #1e1b4b;
}

.medal-icon {
  font-size: 0.85rem;
}

.medal-text {
  letter-spacing: 0.02em;
}

/* 策略头部 */
.chip-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 0.6rem;
}

.strategy-name {
  font-size: 1rem;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}

.confidence-badge {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 0.1rem;
}

.confidence-label {
  font-size: 0.65rem;
  color: rgba(148, 163, 184, 0.8);
}

.confidence-value {
  font-size: 1rem;
  font-weight: 700;
  color: #60a5fa;
}

/* 置信度进度条 */
.confidence-bar-wrapper {
  height: 5px;
  background: rgba(30, 41, 59, 0.8);
  border-radius: 3px;
  overflow: hidden;
  margin-bottom: 0.6rem;
}

.confidence-bar {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #8b5cf6, #ec4899);
  border-radius: 3px;
  transition: width 0.3s ease;
}

/* 推荐理由 */
.chip-reason {
  margin-bottom: 0.6rem;
}

.reason-label {
  display: block;
  font-size: 0.7rem;
  color: rgba(148, 163, 184, 0.8);
  margin-bottom: 0.25rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.reason-text {
  font-size: 0.8rem;
  color: rgba(226, 232, 240, 0.9);
  line-height: 1.5;
  margin: 0;
}

/* 参数配置 */
.chip-params {
  border-top: 1px solid rgba(148, 163, 184, 0.15);
  padding-top: 0.6rem;
}

.params-label {
  display: block;
  font-size: 0.7rem;
  color: rgba(148, 163, 184, 0.8);
  margin-bottom: 0.35rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.params-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.35rem;
}

.param-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: rgba(30, 41, 59, 0.6);
  padding: 0.3rem 0.5rem;
  border-radius: 5px;
  font-size: 0.75rem;
}

.param-key {
  color: rgba(148, 163, 184, 0.9);
}

.param-value {
  color: #f1f5f9;
  font-weight: 600;
}

/* ==================== 执行摘要样式 ==================== */
.execution-card {
  grid-column: 1 / -1;
}

.backtest-detail {
  margin-top: 1rem;
}

.backtest-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 1.25rem;
  background: rgba(30, 41, 59, 0.6);
  border-radius: 12px;
  margin-bottom: 1.25rem;
}

.strategy-info h4 {
  font-size: 1.1rem;
  color: #f1f5f9;
  margin: 0 0 0.25rem 0;
}

.backtest-time {
  font-size: 0.8rem;
  color: rgba(148, 163, 184, 0.8);
}

.confidence-display {
  text-align: right;
}

.conf-label {
  display: block;
  font-size: 0.7rem;
  color: rgba(148, 163, 184, 0.8);
}

.conf-value {
  font-size: 1.25rem;
  font-weight: 700;
  color: #60a5fa;
}

/* 四个区块网格 */
.backtest-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 1.25rem;
}

@media (max-width: 1200px) {
  .backtest-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .backtest-grid {
    grid-template-columns: 1fr;
  }
}

.backtest-block {
  background: rgba(30, 41, 59, 0.5);
  border-radius: 12px;
  padding: 0.85rem;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

/* 核心指标块 - 蓝色主题 */
.backtest-block.metrics-block {
  border-left: 3px solid #3b82f6;
}

/* 交易统计块 - 绿色主题 */
.backtest-block.trades-block {
  border-left: 3px solid #4ade80;
}

/* 回测参数块 - 紫色主题 */
.backtest-block.params-block {
  border-left: 3px solid #8b5cf6;
}

/* 风险评估块 - 橙色主题 */
.backtest-block.risk-block {
  border-left: 3px solid #f59e0b;
}

.block-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
  padding-bottom: 0.4rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.block-icon {
  font-size: 0.9rem;
}

.block-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #f1f5f9;
}

.block-content {
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.metric-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.metric-label {
  font-size: 0.75rem;
  color: rgba(148, 163, 184, 0.9);
}

.metric-value {
  font-size: 0.85rem;
  font-weight: 600;
  color: #f1f5f9;
}

.metric-value.positive {
  color: #4ade80;
}

.metric-value.negative {
  color: #f87171;
}

.metric-value.low-risk {
  color: #4ade80;
}

.metric-value.medium-risk {
  color: #fbbf24;
}

.metric-value.high-risk {
  color: #f87171;
}

/* 风险等级渐变条 */
.risk-bar-container {
  position: relative;
  margin-bottom: 0.6rem;
  padding-bottom: 1rem;
}

.risk-bar-gradient {
  height: 6px;
  background: linear-gradient(90deg, #4ade80 0%, #fbbf24 50%, #f87171 100%);
  border-radius: 3px;
}

.risk-bar-indicator {
  position: absolute;
  top: -3px;
  transform: translateX(-50%);
  transition: left 0.3s ease;
}

.risk-indicator-dot {
  display: block;
  width: 12px;
  height: 12px;
  background: #fff;
  border: 2px solid #1e293b;
  border-radius: 50%;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
}

.risk-bar-labels {
  display: flex;
  justify-content: space-between;
  margin-top: 0.2rem;
  font-size: 0.65rem;
  color: rgba(148, 163, 184, 0.8);
}

/* 快速评价 */
.quick-evaluation {
  background: rgba(30, 41, 59, 0.5);
  border-radius: 12px;
  padding: 0.85rem;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.eval-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.6rem;
}

.eval-icon {
  font-size: 0.9rem;
}

.eval-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #f1f5f9;
}

.eval-content {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 0.5rem;
}

@media (max-width: 768px) {
  .eval-content {
    grid-template-columns: repeat(2, 1fr);
  }
}

.eval-item {
  text-align: center;
  padding: 0.6rem 0.5rem;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.4);
  transition: transform 0.2s;
}

.eval-item:hover {
  transform: scale(1.02);
}

.eval-label {
  display: block;
  font-size: 0.7rem;
  color: rgba(148, 163, 184, 0.8);
  margin-bottom: 0.2rem;
}

.eval-value {
  font-size: 0.95rem;
  font-weight: 700;
}

.eval-item.eval-excellent {
  background: rgba(74, 222, 128, 0.1);
  border: 1px solid rgba(74, 222, 128, 0.3);
}

.eval-item.eval-excellent .eval-value {
  color: #4ade80;
}

.eval-item.eval-good {
  background: rgba(96, 165, 250, 0.1);
  border: 1px solid rgba(96, 165, 250, 0.3);
}

.eval-item.eval-good .eval-value {
  color: #60a5fa;
}

.eval-item.eval-average {
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.eval-item.eval-average .eval-value {
  color: #fbbf24;
}

.eval-item.eval-poor {
  background: rgba(248, 113, 113, 0.1);
  border: 1px solid rgba(248, 113, 113, 0.3);
}

.eval-item.eval-poor .eval-value {
  color: #f87171;
}

/* 其他任务 */
.other-tasks {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1rem;
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid rgba(148, 163, 184, 0.15);
}

.task-item {
  background: rgba(30, 41, 59, 0.5);
  border-radius: 12px;
  padding: 1rem;
  border: 1px solid rgba(148, 163, 184, 0.1);
}

.task-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.task-icon {
  font-size: 1rem;
}

.task-header strong {
  color: #f1f5f9;
  flex: 1;
}

.task-time {
  font-size: 0.75rem;
  color: rgba(148, 163, 184, 0.8);
}

.task-details {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.task-details span {
  font-size: 0.8rem;
  color: rgba(226, 232, 240, 0.85);
  background: rgba(15, 23, 42, 0.4);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
}

.loading-inline {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 2rem;
  color: rgba(226, 232, 240, 0.8);
}

.loading-inline .spinner {
  width: 32px;
  height: 32px;
  margin-bottom: 0.75rem;
}
</style>
