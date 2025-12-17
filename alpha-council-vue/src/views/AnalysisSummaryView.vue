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
          <span class="badge" v-if="strategyRecommendations.length">{{ strategyRecommendations.length }}</span>
        </div>
        <p class="card-desc" v-if="strategyReasoning">{{ strategyReasoning }}</p>
        <div v-if="loadingStrategy && !strategyRecommendations.length" class="loading-inline">
          <div class="spinner"></div>
          <p>策略选择中...</p>
        </div>
        <div v-else-if="strategyRecommendations.length" class="strategy-grid">
          <div
            v-for="strategy in strategyRecommendations"
            :key="strategy.strategy_id"
            class="strategy-chip"
            :class="{ primary: strategy.strategy_id === primaryStrategy?.strategy_id }"
          >
            <div class="chip-head">
              <strong>{{ strategy.strategy_name }}</strong>
              <span class="confidence">置信度 {{ (strategy.confidence * 100).toFixed(1) }}%</span>
            </div>
            <p class="chip-reason">{{ strategy.reason }}</p>
            <div v-if="strategy.parameters && Object.keys(strategy.parameters).length" class="chip-params">
              <span v-for="(value, key) in strategy.parameters" :key="key">{{ key }}: {{ value }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 执行摘要 -->
      <section v-if="hasExecutionDigest" class="card execution-card">
        <div class="section-header">
          <h3>🔧 执行摘要</h3>
          <p class="card-desc">查看已触发的回测 / 模拟交易 / 跟踪任务</p>
        </div>
        <div class="execution-grid">
          <div class="execution-item" v-if="backtestDigest">
            <div class="execution-head">
              <strong>最新回测</strong>
              <span>{{ formatDateTime(backtestDigest.generatedAt) }}</span>
            </div>
            <ul class="execution-metrics">
              <li>策略：{{ backtestDigest.strategyId }}</li>
              <li>总收益率：{{ formatPercent(backtestDigest.metrics.totalReturn) }}</li>
              <li>最大回撤：{{ formatPercent(backtestDigest.metrics.maxDrawdown) }}</li>
              <li>夏普比率：{{ (backtestDigest.metrics.sharpeRatio || 0).toFixed(2) }}</li>
            </ul>
          </div>
          <div class="execution-item" v-if="autoTradingTask">
            <div class="execution-head">
              <strong>自动模拟交易</strong>
              <span>{{ formatDateTime(autoTradingTask.created_at) }}</span>
            </div>
            <ul class="execution-metrics">
              <li>任务ID：{{ autoTradingTask.task_id }}</li>
              <li>初始资金：¥{{ formatAmount(autoTradingTask.initial_capital) }}</li>
              <li>状态：{{ autoTradingTask.status }}</li>
              <li>策略：{{ autoTradingTask.strategy_id || '自动选择' }}</li>
            </ul>
          </div>
          <div class="execution-item" v-if="trackingTask">
            <div class="execution-head">
              <strong>跟踪任务</strong>
              <span>{{ formatDateTime(trackingTask.created_at) }}</span>
            </div>
            <ul class="execution-metrics">
              <li>任务ID：{{ trackingTask.task_id }}</li>
              <li>状态：{{ getTaskStatusText(trackingTask.status) }}</li>
              <li>触发条件：价格±{{ trackingTask.trigger_condition?.price_change_threshold }}%</li>
              <li>周期：{{ trackingTask.duration_days }} 天</li>
            </ul>
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
      getTaskStatusText
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
</style>
