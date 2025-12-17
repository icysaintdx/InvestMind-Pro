<template>
  <div class="backtest-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>📈 策略回测系统</h1>
      <p class="subtitle">测试交易策略的历史表现，优化参数提升收益</p>
    </div>

    <!-- 主要内容区 -->
    <div class="content-wrapper">
      <!-- 左侧配置面板 -->
      <div class="config-panel">
        <h2>⚙️ 回测配置</h2>
        
        <!-- 股票选择 -->
        <div class="config-section">
          <label>股票代码</label>
          <input 
            v-model="config.stockCode" 
            placeholder="如：600519（贵州茅台）"
            class="input-field"
          />
          <small>支持A股、港股、美股</small>
        </div>

        <!-- 时间范围 -->
        <div class="config-section">
          <label>回测期间</label>
          <div class="date-range">
            <input 
              type="date" 
              v-model="config.startDate"
              class="date-input"
            />
            <span class="date-separator">至</span>
            <input 
              type="date" 
              v-model="config.endDate"
              class="date-input"
            />
          </div>
        </div>

        <!-- 策略选择 -->
        <div class="config-section">
          <label>选择策略</label>
          <div class="strategy-list">
            <div 
              v-for="strategy in strategies" 
              :key="strategy.id"
              :class="['strategy-card', { active: config.strategyId === strategy.id }]"
              @click="selectStrategy(strategy)"
            >
              <div class="strategy-header">
                <span class="strategy-icon">{{ strategy.icon }}</span>
                <h4>{{ strategy.name }}</h4>
              </div>
              <p class="strategy-desc">{{ strategy.description }}</p>
              <div class="strategy-meta">
                <span class="tag">{{ strategy.categoryLabel || formatCategory(strategy.category) }}</span>
                <span class="win-rate" v-if="strategy.avgWinRate">
                  胜率 {{ (strategy.avgWinRate * 100).toFixed(1) }}%
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 策略参数 -->
        <div class="config-section" v-if="selectedStrategy">
          <label>策略参数</label>
          <div class="params-grid">
            <div v-for="(value, key) in selectedStrategy.parameters" :key="key" class="param-item">
              <label>{{ getParamLabel(key) }}</label>
              <input 
                v-model.number="strategyParams[key]" 
                type="number"
                class="param-input"
              />
            </div>
          </div>
        </div>

        <!-- 资金设置 -->
        <div class="config-section">
          <label>初始资金</label>
          <input 
            v-model.number="config.initialCapital" 
            type="number"
            step="10000"
            class="input-field"
          />
          <small>建议至少10万元模拟资金</small>
        </div>

        <!-- 执行按钮 -->
        <div class="action-buttons">
          <button 
            @click="runBacktest" 
            :disabled="isRunning"
            class="btn-primary"
          >
            <span v-if="!isRunning">🚀 开始回测</span>
            <span v-else>⏳ 运行中...</span>
          </button>
          <button 
            @click="resetConfig" 
            class="btn-secondary"
          >
            重置配置
          </button>
        </div>
      </div>

      <!-- 右侧结果展示 -->
      <div class="result-panel">
        <!-- 性能指标卡片 -->
        <div v-if="backtestResult" class="metrics-cards">
          <h2>📊 回测结果</h2>
          
          <div class="metrics-grid">
            <div class="metric-card">
              <div class="metric-label">总收益率</div>
              <div :class="['metric-value', getColorClass(backtestResult.metrics.totalReturn)]">
                {{ formatPercent(backtestResult.metrics.totalReturn) }}
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-label">年化收益率</div>
              <div :class="['metric-value', getColorClass(backtestResult.metrics.annualReturn)]">
                {{ formatPercent(backtestResult.metrics.annualReturn) }}
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-label">最大回撤</div>
              <div class="metric-value negative">
                {{ formatPercent(backtestResult.metrics.maxDrawdown) }}
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-label">夏普比率</div>
              <div class="metric-value">
                {{ backtestResult.metrics.sharpeRatio.toFixed(2) }}
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-label">胜率</div>
              <div class="metric-value">
                {{ formatPercent(backtestResult.metrics.winRate) }}
              </div>
            </div>
            
            <div class="metric-card">
              <div class="metric-label">盈亏比</div>
              <div class="metric-value">
                {{ backtestResult.metrics.profitFactor.toFixed(2) }}
              </div>
            </div>
          </div>
        </div>

        <!-- 净值曲线 -->
        <div v-if="backtestResult" class="chart-section">
          <h3>📈 净值曲线</h3>
          <EquityCurve 
            :data="backtestResult.equityCurve"
            :trades="backtestResult.trades"
          />
        </div>

        <!-- 交易记录表格 -->
        <div v-if="backtestResult && backtestResult.trades" class="trades-section">
          <h3>📝 交易记录</h3>
          <div class="trades-table">
            <table>
              <thead>
                <tr>
                  <th>日期</th>
                  <th>类型</th>
                  <th>价格</th>
                  <th>数量</th>
                  <th>金额</th>
                  <th>收益率</th>
                  <th>原因</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="trade in displayTrades" :key="trade.id">
                  <td>{{ formatDate(trade.date) }}</td>
                  <td>
                    <span :class="['trade-type', trade.type.toLowerCase()]">
                      {{ trade.type === 'BUY' ? '买入' : '卖出' }}
                    </span>
                  </td>
                  <td>¥{{ trade.price.toFixed(2) }}</td>
                  <td>{{ trade.quantity }}</td>
                  <td>¥{{ formatAmount(trade.amount) }}</td>
                  <td :class="getColorClass(trade.returnRate)">
                    {{ trade.returnRate ? formatPercent(trade.returnRate) : '-' }}
                  </td>
                  <td class="trade-reason">{{ trade.reason || '-' }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- 分页 -->
          <div class="pagination" v-if="totalPages > 1">
            <button @click="currentPage--" :disabled="currentPage === 1">上一页</button>
            <span>第 {{ currentPage }} / {{ totalPages }} 页</span>
            <button @click="currentPage++" :disabled="currentPage === totalPages">下一页</button>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="!backtestResult && !isRunning" class="empty-state">
          <div class="empty-icon">📊</div>
          <h3>开始您的第一次回测</h3>
          <p>选择股票和策略，点击"开始回测"查看历史表现</p>
        </div>

        <!-- 加载状态 -->
        <div v-if="isRunning" class="loading-state">
          <div class="spinner"></div>
          <h3>正在运行回测...</h3>
          <p>{{ loadingMessage }}</p>
        </div>
      </div>
    </div>

    <!-- 策略对比 -->
    <StrategyComparison 
      v-if="comparisonMode"
      :strategies="selectedStrategies"
      :stockCode="config.stockCode"
      :dateRange="[config.startDate, config.endDate]"
    />
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import EquityCurve from '../components/backtest/EquityCurve.vue'
import StrategyComparison from '../components/backtest/StrategyComparison.vue'

export default {
  name: 'BacktestView',
  components: {
    EquityCurve,
    StrategyComparison
  },
  setup() {
    // 配置
    const config = reactive({
      stockCode: '600519',
      startDate: getDefaultStartDate(),
      endDate: getDefaultEndDate(),
      strategyId: null,
      initialCapital: 100000
    })

    // 策略列表
    const strategies = ref([])
    const selectedStrategy = ref(null)
    const strategyParams = reactive({})

    // 状态
    const isRunning = ref(false)
    const loadingMessage = ref('准备数据...')
    const backtestResult = ref(null)
    const comparisonMode = ref(false)

    // 交易记录分页
    const currentPage = ref(1)
    const pageSize = 10
    
    const displayTrades = computed(() => {
      if (!backtestResult.value?.trades) return []
      const start = (currentPage.value - 1) * pageSize
      return backtestResult.value.trades.slice(start, start + pageSize)
    })

    const totalPages = computed(() => {
      if (!backtestResult.value?.trades) return 1
      return Math.ceil(backtestResult.value.trades.length / pageSize)
    })

    // 加载策略列表
    const CATEGORY_MAP = {
      technical: '技术分析',
      value_investing: '价值投资',
      folk_strategy: '民间策略',
      ai_composite: 'AI合成策略',
      trend_following: '趋势跟踪'
    }

    const formatCategory = (value) => CATEGORY_MAP[value] || value || '未分类'

    const getStrategyIcon = (category) => {
      const icons = {
        technical: '📊',
        value_investing: '💎',
        folk_strategy: '🎯',
        ai_composite: '🤖',
        trend_following: '📈'
      }
      return icons[category] || '📋'
    }

    const normalizeStrategies = (list = []) => list.map((item, index) => ({
      ...item,
      id: item.id || item.strategy_id || `strategy-${index}`,
      icon: item.icon || getStrategyIcon(item.category),
      categoryLabel: item.categoryLabel || formatCategory(item.category)
    }))

    const loadStrategies = async () => {
      try {
        console.log('🔍 开始加载策略列表...')
        const response = await axios.get('http://localhost:8000/api/backtest/strategies')
        console.log('📦 API响应:', response.data)
        
        if (response.data && response.data.success && response.data.strategies) {
          strategies.value = normalizeStrategies(response.data.strategies)
          console.log(`✅ 成功加载${strategies.value.length}个策略`)
        } else {
          console.error('❌ API返回格式不正确:', response.data)
        }
      } catch (error) {
        console.error('❌ 加载策略失败:', error)
        alert('加载策略列表失败，请确保后端服务器正在运行')
      }
    }

    // 选择策略
    const selectStrategy = (strategy) => {
      config.strategyId = strategy.id
      selectedStrategy.value = strategy
      Object.keys(strategyParams).forEach(key => {
        delete strategyParams[key]
      })
      
      // 初始化策略参数
      if (strategy.parameters) {
        Object.keys(strategy.parameters).forEach(key => {
          strategyParams[key] = strategy.parameters[key]
        })
      }
    }

    // 运行回测
    const runBacktest = async () => {
      if (!config.stockCode || !config.strategyId) {
        alert('请填写股票代码并选择策略')
        return
      }

      isRunning.value = true
      loadingMessage.value = '准备数据...'
      backtestResult.value = null
      currentPage.value = 1

      try {
        console.log('🚀 开始回测:', {
          stock_code: config.stockCode,
          strategy_id: config.strategyId,
          start_date: config.startDate,
          end_date: config.endDate
        })
        
        // 调用快速回测API
        loadingMessage.value = '运行策略...'
        const response = await axios.post('http://localhost:8000/api/backtest/quick', {
          stock_code: config.stockCode,
          strategy_id: config.strategyId,
          start_date: config.startDate,
          end_date: config.endDate,
          initial_capital: config.initialCapital,
          strategy_params: strategyParams
        })

        console.log('📦 回测响应:', response.data)
        
        loadingMessage.value = '计算指标...'
        
        // 处理响应数据
        if (response.data) {
          // 转换数据格式（下划线转驼峰）
          const data = response.data
          
          backtestResult.value = {
            summary: data.summary || {},
            metrics: {
              totalReturn: data.metrics?.total_return || 0,
              annualReturn: data.metrics?.annual_return || 0,
              maxDrawdown: data.metrics?.max_drawdown || 0,
              sharpeRatio: data.metrics?.sharpe_ratio || 0,
              winRate: data.metrics?.win_rate || 0,
              totalTrades: data.metrics?.total_trades || 0,
              profitFactor: data.metrics?.profit_factor || 0
            },
            equity_curve: data.equity_curve || [],
            trades: (data.trades || []).map(t => ({
              timestamp: t.timestamp,
              side: t.side,
              price: t.price,
              quantity: t.quantity,
              amount: t.price * t.quantity,
              commission: t.commission,
              returnRate: t.return_rate || null,
              reason: t.reason || ''
            }))
          }
          
          console.log('✅ 回测完成:', backtestResult.value)
        } else {
          console.error('❌ 响应格式不正确:', response.data)
          alert('回测完成但数据格式不正确')
        }
        
      } catch (error) {
        console.error('❌ 回测失败:', error)
        const errorMsg = error.response?.data?.detail || error.message || '未知错误'
        alert('回测失败：' + errorMsg)
      } finally {
        isRunning.value = false
      }
    }

    // 重置配置
    const resetConfig = () => {
      config.stockCode = '600519'
      config.startDate = getDefaultStartDate()
      config.endDate = getDefaultEndDate()
      config.strategyId = null
      config.initialCapital = 100000
      selectedStrategy.value = null
      backtestResult.value = null
    }

    // 工具函数
    const formatPercent = (value) => {
      if (!value && value !== 0) return '-'
      return (value * 100).toFixed(2) + '%'
    }

    const formatAmount = (value) => {
      if (!value) return '0'
      return value.toLocaleString('zh-CN', { minimumFractionDigits: 2 })
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleDateString('zh-CN')
    }

    const getColorClass = (value) => {
      if (!value) return ''
      return value > 0 ? 'positive' : value < 0 ? 'negative' : ''
    }

    const getParamLabel = (key) => {
      const labels = {
        'ema_short': 'EMA短期',
        'ema_long': 'EMA长期',
        'adx_period': 'ADX周期',
        'adx_threshold': 'ADX阈值',
        'vegas_width': 'Vegas宽度',
        'stop_loss_pct': '止损比例',
        'take_profit_pct': '止盈比例',
        'position_size': '仓位大小',
        'volume_threshold': '成交量阈值',
        'rsi_period': 'RSI周期',
        'rsi_oversold': 'RSI超卖',
        'rsi_overbought': 'RSI超买',
        'rsi_exit': 'RSI出场',
        'layer_step_pct': '加仓步长',
        'max_layers': '最大层数',
        'consolidation_min': '最小盘整日',
        'consolidation_max': '最大盘整日',
        'max_hold_bars': '最长持仓K数',
        'suitable_period': '适用周期'
      }
      return labels[key] || key
    }

    function getDefaultStartDate() {
      const date = new Date()
      date.setMonth(date.getMonth() - 6)
      return date.toISOString().split('T')[0]
    }

    function getDefaultEndDate() {
      return new Date().toISOString().split('T')[0]
    }

    // 生命周期
    onMounted(() => {
      loadStrategies()
    })

    return {
      config,
      strategies,
      selectedStrategy,
      strategyParams,
      isRunning,
      loadingMessage,
      backtestResult,
      comparisonMode,
      currentPage,
      displayTrades,
      totalPages,
      selectStrategy,
      runBacktest,
      resetConfig,
      formatPercent,
      formatAmount,
      formatDate,
      getColorClass,
      getParamLabel,
      formatCategory
    }
  }
}
</script>

<style scoped>
.backtest-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 28px;
  margin: 0 0 10px;
  color: #333;
}

.subtitle {
  color: #666;
  font-size: 16px;
  margin: 0;
}

.content-wrapper {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 30px;
}

/* 配置面板样式 */
.config-panel {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
  height: fit-content;
}

.config-panel h2 {
  margin: 0 0 20px;
  font-size: 20px;
  color: #333;
}

.config-section {
  margin-bottom: 25px;
}

.config-section label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #555;
}

.input-field {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
}

.input-field:focus {
  outline: none;
  border-color: #4CAF50;
}

.config-section small {
  display: block;
  margin-top: 5px;
  color: #999;
  font-size: 12px;
}

.date-range {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
}

.date-separator {
  color: #999;
}

/* 策略卡片样式 */
.strategy-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-height: 300px;
  overflow-y: auto;
}

.strategy-card {
  padding: 15px;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.strategy-card:hover {
  border-color: #4CAF50;
  background: #f9fff9;
}

.strategy-card.active {
  border-color: #4CAF50;
  background: #e8f5e9;
}

.strategy-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.strategy-icon {
  font-size: 24px;
}

.strategy-header h4 {
  margin: 0;
  font-size: 16px;
  color: #333;
}

.strategy-desc {
  margin: 0 0 10px;
  color: #666;
  font-size: 13px;
}

.strategy-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.tag {
  padding: 3px 8px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.win-rate {
  color: #4CAF50;
  font-size: 12px;
  font-weight: 500;
}

/* 参数网格 */
.params-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.param-item label {
  display: block;
  margin-bottom: 4px;
  font-size: 12px;
  color: #666;
}

.param-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid #ddd;
  border-radius: 4px;
  font-size: 13px;
}

/* 按钮样式 */
.action-buttons {
  display: flex;
  gap: 12px;
  margin-top: 30px;
}

.btn-primary,
.btn-secondary {
  flex: 1;
  padding: 12px 20px;
  border: none;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: #4CAF50;
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: #45a049;
}

.btn-primary:disabled {
  background: #ccc;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f5f5f5;
  color: #666;
}

.btn-secondary:hover {
  background: #e8e8e8;
}

/* 结果面板样式 */
.result-panel {
  background: white;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.metrics-cards h2 {
  margin: 0 0 20px;
  font-size: 20px;
  color: #333;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 30px;
}

.metric-card {
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  text-align: center;
}

.metric-label {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #333;
}

.metric-value.positive {
  color: #4CAF50;
}

.metric-value.negative {
  color: #f44336;
}

/* 图表区域 */
.chart-section {
  margin: 30px 0;
}

.chart-section h3 {
  margin: 0 0 15px;
  font-size: 18px;
  color: #333;
}

/* 交易记录表格 */
.trades-section {
  margin-top: 30px;
}

.trades-section h3 {
  margin: 0 0 15px;
  font-size: 18px;
  color: #333;
}

.trades-table {
  overflow-x: auto;
}

.trades-table table {
  width: 100%;
  border-collapse: collapse;
}

.trades-table th,
.trades-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.trades-table th {
  background: #f8f9fa;
  font-weight: 500;
  color: #666;
  font-size: 13px;
}

.trades-table td {
  font-size: 14px;
  color: #333;
}

.trade-type {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.trade-type.buy {
  background: #e8f5e9;
  color: #4CAF50;
}

.trade-type.sell {
  background: #ffebee;
  color: #f44336;
}

.trade-reason {
  font-size: 12px;
  color: #666;
}

/* 分页 */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 15px;
  margin-top: 20px;
}

.pagination button {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.pagination button:hover:not(:disabled) {
  background: #f5f5f5;
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  margin: 0 0 10px;
  color: #333;
}

.empty-state p {
  color: #666;
  margin: 0;
}

/* 加载状态 */
.loading-state {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid #f3f3f3;
  border-top: 4px solid #4CAF50;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.loading-state h3 {
  margin: 0 0 10px;
  color: #333;
}

.loading-state p {
  color: #666;
  margin: 0;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-wrapper {
    grid-template-columns: 1fr;
  }
  
  .config-panel {
    margin-bottom: 20px;
  }
  
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 768px) {
  .metrics-grid {
    grid-template-columns: 1fr;
  }
  
  .params-grid {
    grid-template-columns: 1fr;
  }
}
</style>
