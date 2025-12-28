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
              <label :title="getParamDescription(key)">
                {{ getParamLabel(key) }}
                <span class="param-hint" v-if="getParamHint(key)">{{ getParamHint(key) }}</span>
              </label>
              <input
                v-model.number="strategyParams[key]"
                type="number"
                :step="getParamStep(key)"
                class="param-input"
                :placeholder="String(value)"
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
            step="100000"
            class="input-field"
          />
          <small>建议至少50万元（高价股如茅台需要更多资金）</small>
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
            :data="backtestResult.equity_curve"
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
import API_BASE_URL from '@/config/api.js'

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
      initialCapital: 500000  // 增加到50万，以支持高价股如茅台
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
        const response = await axios.get(`${API_BASE_URL}/api/backtest/strategies`)
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
        const response = await axios.post(`${API_BASE_URL}/api/backtest/quick`, {
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
            trades: (data.trades || []).map((t, index) => ({
              id: index,
              date: t.timestamp,
              type: t.side?.toUpperCase() || 'BUY',
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
      config.initialCapital = 500000  // 与默认值保持一致
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
        // 通用参数
        'suitable_period': '适用周期',
        'max_position': '最大仓位',
        'stop_loss': '止损比例',
        'take_profit': '止盈比例',
        'news_sensitivity': '新闻敏感度',
        'position_size': '仓位大小',
        'initial_capital': '初始资金',
        // EMA相关
        'ema_short': 'EMA短期',
        'ema_long': 'EMA长期',
        'ema_period': 'EMA周期',
        // ADX相关
        'adx_period': 'ADX周期',
        'adx_threshold': 'ADX阈值',
        // Vegas相关
        'vegas_width': 'Vegas宽度',
        'vegas_period': 'Vegas周期',
        // 止损止盈
        'stop_loss_pct': '止损比例(%)',
        'take_profit_pct': '止盈比例(%)',
        // 成交量
        'volume_threshold': '成交量阈值',
        'volume_ratio': '量比阈值',
        // RSI相关
        'rsi_period': 'RSI周期',
        'rsi_oversold': 'RSI超卖线',
        'rsi_overbought': 'RSI超买线',
        'rsi_exit': 'RSI出场线',
        // 马丁格尔
        'layer_step_pct': '加仓步长(%)',
        'max_layers': '最大加仓层数',
        // 盘整突破
        'consolidation_min': '最小盘整天数',
        'consolidation_max': '最大盘整天数',
        'consolidation_days': '盘整天数',
        // 持仓
        'max_hold_bars': '最长持仓K线数',
        'max_hold_days': '最长持仓天数',
        // MACD相关
        'macd_fast': 'MACD快线',
        'macd_slow': 'MACD慢线',
        'macd_signal': 'MACD信号线',
        // 布林带
        'bb_period': '布林带周期',
        'bb_std': '布林带标准差',
        // 海龟交易
        'entry_period': '入场周期',
        'exit_period': '出场周期',
        'atr_period': 'ATR周期',
        'atr_multiplier': 'ATR倍数',
        // 价值投资
        'pe_threshold': 'PE阈值',
        'pb_threshold': 'PB阈值',
        'roe_threshold': 'ROE阈值',
        'dividend_yield': '股息率阈值',
        // 其他
        'lookback_period': '回看周期',
        'signal_threshold': '信号阈值',
        'risk_factor': '风险系数',
        'momentum_period': '动量周期'
      }
      return labels[key] || key
    }

    // 参数描述（用于tooltip）
    const getParamDescription = (key) => {
      const descriptions = {
        'suitable_period': '策略适用的K线周期，如日线、周线等',
        'max_position': '单只股票最大持仓比例，0.3表示30%',
        'stop_loss': '止损触发比例，0.05表示亏损5%时止损',
        'take_profit': '止盈触发比例，0.15表示盈利15%时止盈',
        'news_sensitivity': '对新闻消息的敏感程度，越高越敏感',
        'ema_short': '短期指数移动平均线周期',
        'ema_long': '长期指数移动平均线周期',
        'adx_period': 'ADX指标计算周期，用于判断趋势强度',
        'adx_threshold': 'ADX阈值，超过此值认为趋势明显',
        'rsi_period': 'RSI相对强弱指标计算周期',
        'rsi_oversold': 'RSI超卖线，低于此值可能超卖',
        'rsi_overbought': 'RSI超买线，高于此值可能超买',
        'volume_threshold': '成交量放大倍数阈值',
        'max_layers': '马丁格尔策略最大加仓次数',
        'layer_step_pct': '每次加仓的价格下跌幅度'
      }
      return descriptions[key] || ''
    }

    // 参数提示（显示在标签旁）
    const getParamHint = (key) => {
      const hints = {
        'max_position': '(0-1)',
        'stop_loss': '(0-1)',
        'take_profit': '(0-1)',
        'news_sensitivity': '(0-1)',
        'stop_loss_pct': '(%)',
        'take_profit_pct': '(%)',
        'layer_step_pct': '(%)'
      }
      return hints[key] || ''
    }

    // 参数步进值
    const getParamStep = (key) => {
      if (key.includes('pct') || key.includes('position') || key.includes('loss') || key.includes('profit') || key.includes('sensitivity')) {
        return 0.01
      }
      if (key.includes('threshold') || key.includes('ratio')) {
        return 0.1
      }
      return 1
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
      getParamDescription,
      getParamHint,
      getParamStep,
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
  color: #f1f5f9;
}

.subtitle {
  color: rgba(148, 163, 184, 0.9);
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
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 16px;
  padding: 25px;
  box-shadow: 0 15px 35px rgba(15, 23, 42, 0.4);
  height: fit-content;
}

.config-panel h2 {
  margin: 0 0 20px;
  font-size: 20px;
  color: #f1f5f9;
}

.config-section {
  margin-bottom: 25px;
}

.config-section label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: rgba(226, 232, 240, 0.9);
}

.input-field {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 8px;
  font-size: 14px;
  background: rgba(30, 41, 59, 0.6);
  color: #e2e8f0;
}

.input-field:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.6);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
}

.input-field::placeholder {
  color: rgba(148, 163, 184, 0.6);
}

.config-section small {
  display: block;
  margin-top: 5px;
  color: rgba(148, 163, 184, 0.7);
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
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 8px;
  background: rgba(30, 41, 59, 0.6);
  color: #e2e8f0;
}

.date-input:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.6);
}

.date-separator {
  color: rgba(148, 163, 184, 0.7);
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
  border: 2px solid rgba(148, 163, 184, 0.3);
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  background: rgba(30, 41, 59, 0.6);
}

.strategy-card:hover {
  border-color: rgba(59, 130, 246, 0.6);
  background: rgba(59, 130, 246, 0.1);
  transform: translateY(-2px);
}

.strategy-card.active {
  border-color: rgba(59, 130, 246, 0.8);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(139, 92, 246, 0.15));
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.2);
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
  color: #f1f5f9;
}

.strategy-desc {
  margin: 0 0 10px;
  color: rgba(226, 232, 240, 0.8);
  font-size: 13px;
}

.strategy-meta {
  display: flex;
  gap: 10px;
  align-items: center;
}

.tag {
  padding: 4px 10px;
  background: rgba(99, 102, 241, 0.2);
  border-radius: 6px;
  font-size: 12px;
  color: #a5b4fc;
}

.win-rate {
  color: #4ade80;
  font-size: 12px;
  font-weight: 600;
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
  cursor: help;
}

.param-hint {
  color: rgba(148, 163, 184, 0.7);
  font-size: 10px;
  margin-left: 4px;
}

.param-input {
  width: 100%;
  padding: 6px 8px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 6px;
  font-size: 13px;
  background: rgba(30, 41, 59, 0.6);
  color: #e2e8f0;
}

.param-input:focus {
  outline: none;
  border-color: rgba(59, 130, 246, 0.6);
  box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.1);
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
  border-radius: 10px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-primary:disabled {
  background: rgba(148, 163, 184, 0.3);
  color: rgba(148, 163, 184, 0.6);
  cursor: not-allowed;
}

.btn-secondary {
  background: rgba(148, 163, 184, 0.15);
  color: #e2e8f0;
  border: 1px solid rgba(148, 163, 184, 0.3);
}

.btn-secondary:hover {
  background: rgba(148, 163, 184, 0.25);
  border-color: rgba(148, 163, 184, 0.5);
}

/* 结果面板样式 */
.result-panel {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 16px;
  padding: 25px;
  box-shadow: 0 15px 35px rgba(15, 23, 42, 0.4);
}

.metrics-cards h2 {
  margin: 0 0 20px;
  font-size: 20px;
  color: #f1f5f9;
}

.metrics-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
  margin-bottom: 30px;
}

.metric-card {
  padding: 15px;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  text-align: center;
}

.metric-label {
  font-size: 13px;
  color: rgba(148, 163, 184, 0.9);
  margin-bottom: 8px;
}

.metric-value {
  font-size: 24px;
  font-weight: bold;
  color: #f1f5f9;
}

.metric-value.positive {
  color: #4ade80;
}

.metric-value.negative {
  color: #f87171;
}

/* 图表区域 */
.chart-section {
  margin: 30px 0;
}

.chart-section h3 {
  margin: 0 0 15px;
  font-size: 18px;
  color: #f1f5f9;
}

/* 交易记录表格 */
.trades-section {
  margin-top: 30px;
}

.trades-section h3 {
  margin: 0 0 15px;
  font-size: 18px;
  color: #f1f5f9;
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
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.trades-table th {
  background: rgba(30, 41, 59, 0.6);
  font-weight: 500;
  color: rgba(148, 163, 184, 0.9);
  font-size: 13px;
}

.trades-table td {
  font-size: 14px;
  color: #e2e8f0;
}

.trades-table tr:hover {
  background: rgba(59, 130, 246, 0.05);
}

.trade-type {
  padding: 4px 10px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
}

.trade-type.buy {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.trade-type.sell {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.trade-reason {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.8);
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
  padding: 8px 14px;
  border: 1px solid rgba(148, 163, 184, 0.3);
  background: rgba(30, 41, 59, 0.6);
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  color: #e2e8f0;
  transition: all 0.2s;
}

.pagination button:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
}

.pagination button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.pagination span {
  color: rgba(148, 163, 184, 0.9);
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 60px 20px;
  border: 1px dashed rgba(148, 163, 184, 0.3);
  border-radius: 16px;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 20px;
}

.empty-state h3 {
  margin: 0 0 10px;
  color: #f1f5f9;
}

.empty-state p {
  color: rgba(148, 163, 184, 0.8);
  margin: 0;
}

/* 加载状态 */
.loading-state {
  text-align: center;
  padding: 60px 20px;
  border: 1px dashed rgba(148, 163, 184, 0.3);
  border-radius: 16px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(148, 163, 184, 0.3);
  border-top: 4px solid #60a5fa;
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
  color: #f1f5f9;
}

.loading-state p {
  color: rgba(148, 163, 184, 0.8);
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
  /* 主容器 */
  .backtest-container {
    padding: 12px;
  }

  /* 页面标题 */
  .page-header {
    margin-bottom: 20px;
  }

  .page-header h1 {
    font-size: 1.5rem;
  }

  .subtitle {
    font-size: 13px;
  }

  /* 配置面板 */
  .config-panel {
    padding: 16px;
    border-radius: 10px;
  }

  .config-panel h2 {
    font-size: 1.1rem;
    margin-bottom: 16px;
  }

  .config-section {
    margin-bottom: 20px;
  }

  .config-section label {
    font-size: 13px;
    margin-bottom: 6px;
  }

  .input-field {
    padding: 8px 10px;
    font-size: 14px;
  }

  .config-section small {
    font-size: 11px;
  }

  /* 日期选择 */
  .date-range {
    flex-direction: column;
    gap: 8px;
  }

  .date-input {
    width: 100%;
    padding: 8px 10px;
  }

  .date-separator {
    display: none;
  }

  /* 策略列表 */
  .strategy-list {
    max-height: 250px;
    gap: 10px;
  }

  .strategy-card {
    padding: 12px;
  }

  .strategy-icon {
    font-size: 20px;
  }

  .strategy-header h4 {
    font-size: 14px;
  }

  .strategy-desc {
    font-size: 12px;
    margin-bottom: 8px;
  }

  .strategy-meta {
    flex-wrap: wrap;
    gap: 6px;
  }

  .tag {
    font-size: 11px;
    padding: 2px 6px;
  }

  .win-rate {
    font-size: 11px;
  }

  /* 参数网格 */
  .params-grid {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .param-item label {
    font-size: 11px;
  }

  .param-input {
    padding: 6px 8px;
    font-size: 13px;
  }

  /* 按钮 */
  .action-buttons {
    flex-direction: column;
    gap: 10px;
    margin-top: 20px;
  }

  .btn-primary,
  .btn-secondary {
    padding: 12px 16px;
    font-size: 14px;
  }

  /* 结果面板 */
  .result-panel {
    padding: 16px;
    border-radius: 10px;
  }

  .metrics-cards h2 {
    font-size: 1.1rem;
    margin-bottom: 16px;
  }

  /* 指标网格 */
  .metrics-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
    margin-bottom: 20px;
  }

  .metric-card {
    padding: 12px;
    border-radius: 6px;
  }

  .metric-label {
    font-size: 11px;
    margin-bottom: 4px;
  }

  .metric-value {
    font-size: 1.25rem;
  }

  /* 图表区域 */
  .chart-section {
    margin: 20px 0;
  }

  .chart-section h3 {
    font-size: 1rem;
    margin-bottom: 12px;
  }

  /* 交易记录 */
  .trades-section {
    margin-top: 20px;
  }

  .trades-section h3 {
    font-size: 1rem;
    margin-bottom: 12px;
  }

  .trades-table {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .trades-table table {
    min-width: 600px;
  }

  .trades-table th,
  .trades-table td {
    padding: 8px 6px;
    font-size: 12px;
  }

  .trade-type {
    font-size: 11px;
    padding: 2px 6px;
  }

  .trade-reason {
    font-size: 11px;
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  /* 分页 */
  .pagination {
    gap: 10px;
    margin-top: 16px;
  }

  .pagination button {
    padding: 6px 10px;
    font-size: 12px;
  }

  .pagination span {
    font-size: 12px;
  }

  /* 空状态 */
  .empty-state {
    padding: 40px 16px;
  }

  .empty-icon {
    font-size: 48px;
    margin-bottom: 16px;
  }

  .empty-state h3 {
    font-size: 1rem;
  }

  .empty-state p {
    font-size: 13px;
  }

  /* 加载状态 */
  .loading-state {
    padding: 40px 16px;
  }

  .spinner {
    width: 32px;
    height: 32px;
    margin-bottom: 16px;
  }

  .loading-state h3 {
    font-size: 1rem;
  }

  .loading-state p {
    font-size: 13px;
  }
}

/* 超小屏幕适配 */
@media (max-width: 480px) {
  .backtest-container {
    padding: 8px;
  }

  .page-header h1 {
    font-size: 1.25rem;
  }

  .config-panel,
  .result-panel {
    padding: 12px;
  }

  .config-panel h2,
  .metrics-cards h2 {
    font-size: 1rem;
  }

  /* 指标网格改为2列 */
  .metrics-grid {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .metric-card {
    padding: 10px;
  }

  .metric-label {
    font-size: 10px;
  }

  .metric-value {
    font-size: 1.1rem;
  }

  /* 策略卡片 */
  .strategy-card {
    padding: 10px;
  }

  .strategy-header {
    gap: 8px;
  }

  .strategy-icon {
    font-size: 18px;
  }

  .strategy-header h4 {
    font-size: 13px;
  }

  .strategy-desc {
    font-size: 11px;
  }

  /* 表格进一步简化 */
  .trades-table th,
  .trades-table td {
    padding: 6px 4px;
    font-size: 11px;
  }

  /* 隐藏部分列 */
  .trades-table th:nth-child(5),
  .trades-table td:nth-child(5),
  .trades-table th:nth-child(7),
  .trades-table td:nth-child(7) {
    display: none;
  }
}
</style>
