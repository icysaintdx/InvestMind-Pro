<template>
  <div class="trading-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>💼 模拟交易</h1>
      <p class="subtitle">虚拟资金练习交易，零风险学习投资</p>
      <div class="action-buttons">
        <!-- 实时刷新状态指示器 -->
        <div class="realtime-status" :class="{ trading: tradingStatus?.isTrading, refreshing: isAutoRefreshing }">
          <span class="status-dot" :class="{ active: realtimeRefreshEnabled && tradingStatus?.isTrading }"></span>
          <span class="status-text">{{ getRefreshStatusText() }}</span>
          <button @click="toggleRealtimeRefresh" class="refresh-toggle-btn" :title="realtimeRefreshEnabled ? '关闭实时刷新' : '开启实时刷新'">
            {{ realtimeRefreshEnabled ? '🔄' : '⏸️' }}
          </button>
          <button @click="manualRefresh" class="manual-refresh-btn" title="立即刷新" :disabled="isAutoRefreshing">
            🔃
          </button>
        </div>
        <button @click="loadPortfolio" class="btn-secondary">🔄 刷新</button>
        <button @click="showTradeDialog = true" class="btn-primary">📈 买入/卖出</button>
        <button @click="resetAccount" class="btn-danger">♻️ 重置账户</button>
      </div>
    </div>

    <!-- 风险提示 -->
    <div class="risk-alert">
      <div class="alert-icon">⚠️</div>
      <div class="alert-content">
        <strong>模拟交易提示：</strong>
        本功能使用虚拟资金，不涉及真实交易。模拟环境与实盘存在差异，请勿将模拟结果作为实盘投资依据。
      </div>
    </div>

    <!-- 账户总览 -->
    <div v-if="portfolio" class="account-overview">
      <div class="overview-card">
        <div class="card-label">总资产</div>
        <div class="card-value">¥{{ formatAmount(portfolio.total_value) }}</div>
      </div>
      <div class="overview-card">
        <div class="card-label">可用资金</div>
        <div class="card-value">¥{{ formatAmount(portfolio.cash_balance) }}</div>
      </div>
      <div class="overview-card">
        <div class="card-label">持仓市值</div>
        <div class="card-value">¥{{ formatAmount(portfolio.positions_value) }}</div>
      </div>
      <div class="overview-card">
        <div class="card-label">总盈亏</div>
        <div :class="['card-value', getProfitClass(portfolio.total_profit_loss)]">
          ¥{{ formatAmount(portfolio.total_profit_loss) }}
        </div>
      </div>
      <div class="overview-card">
        <div class="card-label">收益率</div>
        <div :class="['card-value', getProfitClass(portfolio.total_profit_loss_rate)]">
          {{ portfolio.total_profit_loss_rate.toFixed(2) }}%
        </div>
      </div>
    </div>

    <!-- K线图 -->
    <div class="kline-section">
      <div class="kline-header">
        <h3>📈 K线图分析</h3>
        <div class="kline-controls">
          <input
            v-model="klineStock"
            placeholder="输入股票代码"
            class="kline-input"
            @keyup.enter="loadKlineData"
          />
          <div class="period-buttons">
            <button
              v-for="period in periods"
              :key="period.value"
              @click="selectPeriod(period.value)"
              :class="['period-btn', { active: klinePeriod === period.value }]"
            >
              {{ period.label }}
            </button>
          </div>
          <button @click="loadKlineData" class="load-btn">
            <span v-if="klineLoading">⏳</span><span v-else>加载</span>
          </button>
        </div>
      </div>

<!-- 技术指标开关 -->
      <div class="indicator-toggles">
        <span class="toggle-label">均线：</span>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.ma5" @change="renderKlineChart" />
          <span class="toggle-text ma5">MA5</span>
        </label>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.ma20" @change="renderKlineChart" />
          <span class="toggle-text ma20">MA20</span>
        </label>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.ma60" @change="renderKlineChart" />
          <span class="toggle-text ma60">MA60</span>
        </label>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.boll" @change="renderKlineChart" />
          <span class="toggle-text boll">布林带</span>
        </label>
        <span class="toggle-divider">|</span>
        <span class="toggle-label">副图：</span>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.macd" @change="renderKlineChart" />
          <span class="toggle-text macd">MACD</span>
        </label>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.rsi" @change="renderKlineChart" />
          <span class="toggle-text rsi">RSI</span>
        </label>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.kdj" @change="renderKlineChart" />
          <span class="toggle-text kdj">KDJ</span>
        </label>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.sixPulse" @change="renderKlineChart" />
          <span class="toggle-text sixpulse">⚔️六脉神剑</span>
        </label>
        <span class="toggle-divider">|</span>
        <span class="toggle-label">标注：</span>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.showSignals" @change="renderKlineChart" />
          <span class="toggle-text signals">信号</span>
        </label>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.showPatterns" @change="renderKlineChart" />
          <span class="toggle-text patterns">形态</span>
        </label>
        <label class="toggle-item">
          <input type="checkbox" v-model="indicators.showLargeOrders" @change="renderKlineChart" />
          <span class="toggle-text largeorders">🏛️机构大单</span>
        </label>
      </div>

      <!-- K线图工具栏 -->
      <div class="chart-toolbar">
        <div class="toolbar-group">
          <span class="toolbar-label">标记工具：</span>
          <button @click="showPriceMarkerModal = true" class="toolbar-btn" title="添加价格标记">📍 添加标记</button>
          <button @click="autoDetectKeyLevels" class="toolbar-btn highlight" title="自动识别关键点位">🔍 自动识别</button>
        </div>
        <div class="toolbar-group">
          <span class="toolbar-label">快捷标记：</span>
          <button @click="addSupportLine" class="toolbar-btn support" title="添加支撑位">📉 支撑位</button>
          <button @click="addResistanceLine" class="toolbar-btn resistance" title="添加压力位">📈 压力位</button>
        </div>
        <div class="toolbar-group">
          <button @click="captureChart" class="toolbar-btn" title="保存截图">📷 截图</button>
          <button @click="clearAllMarkers" class="toolbar-btn danger" title="清除所有标记">🗑️ 清除</button>
        </div>
      </div>

      <div class="kline-chart-wrapper" :style="{ height: chartHeight + 'px' }">
        <div class="kline-chart" ref="klineChart" :style="{ height: chartHeight + 'px', minHeight: chartHeight + 'px' }"></div>
        <div v-if="klineLoading" class="kline-overlay kline-loading">
          <div class="spinner"></div>
          <p>加载K线数据中...</p>
        </div>
        <div v-else-if="klineError" class="kline-overlay kline-error">
          <p>⚠️ {{ klineError }}</p>
        </div>
        <div v-else-if="klineData.length === 0" class="kline-overlay kline-empty">
          <span class="empty-icon">📈</span>
          <p>输入股票代码加载K线图</p>
        </div>
      </div>

<!-- 指标显示区域 -->
      <div class="indicator-display" v-if="klineData.length > 0">
        <span class="ind-label">MA5:</span><span class="ind-value ma5">{{ currentIndicators.MA5?.toFixed(2) || '-' }}</span>
        <span class="ind-label">MA10:</span><span class="ind-value ma10">{{ currentIndicators.MA10?.toFixed(2) || '-' }}</span>
        <span class="ind-label">MA20:</span><span class="ind-value ma20">{{ currentIndicators.MA20?.toFixed(2) || '-' }}</span>
        <span class="ind-divider">|</span>
        <span class="ind-label">RSI:</span><span :class="['ind-value', getRSIClass(currentIndicators.RSI)]">{{ currentIndicators.RSI?.toFixed(1) || '-' }}</span>
        <span class="ind-label">MACD:</span><span :class="['ind-value', currentIndicators.MACD > 0 ? 'positive' : 'negative']">{{ currentIndicators.MACD?.toFixed(3) || '-' }}</span>
        <span class="ind-divider" v-if="dataSource">|</span>
        <span class="ind-label" v-if="dataSource">数据源:</span><span class="ind-value data-source" v-if="dataSource">{{ dataSource }}</span>
        <span class="ind-label" style="margin-left: 8px;">成交量:</span>
        <span :class="['ind-value', getVolumeClass()]">{{ getVolumeStatus() }}</span>
        <!-- 信号汇总 -->
        <template v-if="signalSummary && signalSummary.total > 0">
          <span class="ind-divider">|</span>
          <span class="ind-label">信号:</span>
          <span class="signal-count bullish">📈{{ signalSummary.bullish }}</span>
          <span class="signal-count bearish">📉{{ signalSummary.bearish }}</span>
          <span :class="['signal-recommendation', signalSummary.recommendation.toLowerCase()]">
            {{ signalSummary.recommendation === 'BUY' ? '🟢看多' : (signalSummary.recommendation === 'SELL' ? '🔴看空' : '⚪观望') }}
          </span>
        </template>
        <!-- 当前订单信息 -->
        <template v-if="currentOrderInfo">
          <span class="ind-divider">|</span>
          <span class="ind-label">当前订单:</span>
          <span class="ind-value order-stock">{{ currentOrderInfo.stock_name }}</span>
          <span class="ind-value order-action">{{ currentOrderInfo.action === 'BUY' ? '买入' : '卖出' }}</span>
        </template>
      </div>
      
      <!-- 六脉神剑综合指标面板 -->
      <div class="six-pulse-panel" v-if="sixPulseIndicators && sixPulseIndicators.length > 0">
        <div class="panel-header-mini">
          <h3 class="panel-title-mini">⚔️ 六脉神剑综合指标</h3>
          <span class="panel-subtitle">融合6大核心指标的多维度共振分析</span>
        </div>
        <div class="pulse-indicators">
          <div class="pulse-item" v-for="(item, idx) in sixPulseIndicators" :key="idx" :title="item.description">
            <span class="pulse-name">{{ item.name }}</span>
            <span class="pulse-value">{{ item.value }}</span>
            <span :class="['pulse-status', item.status]">{{ item.statusText }}</span>
          </div>
        </div>
        <div class="pulse-summary">
          <span class="bullish-count">📈 多头: {{ sixPulseSummary.bullish }}</span>
          <span class="bearish-count">📉 空头: {{ sixPulseSummary.bearish }}</span>
          <span :class="['signal-badge', sixPulseSummary.signal.toLowerCase()]">
            {{ sixPulseSummary.signalText }}
          </span>
        </div>
        <div class="pulse-hint">
          <span class="hint-text">💡 当≥4个指标同时发出多头/空头信号时，趋势确定性≥90%</span>
        </div>
      </div>
    </div>

    <!-- 价格标记模态框 -->
    <div v-if="showPriceMarkerModal" class="modal-overlay" @click.self="showPriceMarkerModal = false">
      <div class="modal-content marker-modal">
        <div class="modal-header">
          <h3>📍 添加价格标记</h3>
          <button @click="showPriceMarkerModal = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <p class="modal-desc">在K线图上添加关键价格点位标记</p>

          <div class="form-group">
            <label>标记类型</label>
            <div class="marker-type-grid">
              <button @click="priceMarkerForm.type = 'support'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'support' }]">
                <span class="type-icon">📉</span><span class="type-label">支撑位</span>
              </button>
              <button @click="priceMarkerForm.type = 'resistance'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'resistance' }]">
                <span class="type-icon">📈</span><span class="type-label">压力位</span>
              </button>
              <button @click="priceMarkerForm.type = 'high'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'high' }]">
                <span class="type-icon">🔺</span><span class="type-label">高点</span>
              </button>
              <button @click="priceMarkerForm.type = 'low'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'low' }]">
                <span class="type-icon">🔻</span><span class="type-label">低点</span>
              </button>
              <button @click="priceMarkerForm.type = 'buy'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'buy' }]">
                <span class="type-icon">🟢</span><span class="type-label">买入点</span>
              </button>
              <button @click="priceMarkerForm.type = 'sell'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'sell' }]">
                <span class="type-icon">🔴</span><span class="type-label">卖出点</span>
              </button>
            </div>
          </div>

          <div class="form-group">
            <label>价格</label>
            <input v-model="priceMarkerForm.price" type="number" step="0.01" placeholder="输入价格" class="input-field" />
          </div>

          <div class="form-group">
            <label>标签（可选）</label>
            <input v-model="priceMarkerForm.label" type="text" placeholder="自定义标签文字" class="input-field" />
          </div>

          <div class="modal-actions">
            <button @click="showPriceMarkerModal = false" class="btn-secondary">取消</button>
            <button @click="addPriceMarkerFromForm" :disabled="!priceMarkerForm.price" class="btn-primary">添加标记</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 持仓列表 -->
    <div class="positions-section">
      <h3>📊 持仓列表</h3>
      <div v-if="!portfolio || portfolio.positions.length === 0" class="empty-state">
        <p>暂无持仓</p>
      </div>
      <div v-else class="table-wrapper">
        <table class="data-table">
          <thead>
            <tr>
              <th>股票代码</th>
              <th>股票名称</th>
              <th>持仓数量</th>
              <th>成本价</th>
              <th>现价</th>
              <th>市值</th>
              <th>盈亏</th>
              <th>收益率</th>
              <th>持有天数</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="position in portfolio.positions"
              :key="position.stock_code"
              @click="loadStockKline(position.stock_code)"
              class="clickable-row"
              :title="`点击查看 ${position.stock_code} K线图`"
            >
            <td>{{ position.stock_code }}</td>
            <td>{{ position.stock_name }}</td>
            <td>{{ position.quantity }}</td>
            <td>¥{{ position.avg_cost.toFixed(2) }}</td>
            <td>¥{{ position.current_price.toFixed(2) }}</td>
            <td>¥{{ formatAmount(position.market_value) }}</td>
            <td :class="getProfitClass(position.profit_loss_rate)">
              ¥{{ formatAmount(position.profit_loss) }}
            </td>
            <td :class="getProfitClass(position.profit_loss_rate)">
              {{ position.profit_loss_rate.toFixed(2) }}%
            </td>
            <td>{{ position.holding_days }}天</td>
            <td>
              <button 
                @click="quickSell(position)" 
                class="btn-danger-small"
              >
                卖出
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      </div>
    </div>

    <!-- 交易记录和策略日志并排布局 -->
    <div class="trades-logs-row">
      <!-- 交易记录 -->
      <div class="trades-section">
        <h3>📝 交易记录</h3>
        <div v-if="trades.length === 0" class="empty-state">
          <p>暂无交易记录</p>
        </div>
        <div v-else class="table-wrapper">
          <table class="data-table compact">
            <thead>
              <tr>
                <th>时间</th>
                <th>代码</th>
                <th>方向</th>
                <th>数量</th>
                <th>价格</th>
                <th>来源</th>
              </tr>
            </thead>
          <tbody>
            <tr
              v-for="trade in trades"
              :key="trade.trade_id"
              @click="loadStockKline(trade.stock_code)"
              class="clickable-row"
              :title="`点击查看 ${trade.stock_code} K线图`"
            >
              <td>{{ formatTimeShort(trade.timestamp) }}</td>
              <td>{{ trade.stock_code }}</td>
              <td :class="trade.action === 'BUY' ? 'text-success' : 'text-danger'">
                {{ trade.action === 'BUY' ? '买' : '卖' }}
              </td>
              <td>{{ trade.quantity }}</td>
              <td>¥{{ trade.price.toFixed(2) }}</td>
              <td>
                <span :class="['source-badge', trade.source || 'manual']">
                  {{ getSourceLabel(trade.source) }}
                </span>
              </td>
            </tr>
          </tbody>
        </table>
        </div>
      </div>

      <!-- 策略交易日志 -->
      <div class="trade-logs-section">
        <div class="logs-header">
          <h3>📋 策略日志</h3>
          <div class="logs-controls">
            <select v-model="logFilter.type" class="log-filter-select" @change="loadTradeLogs">
              <option value="">全部</option>
              <option value="signal">信号</option>
              <option value="order">订单</option>
              <option value="execution">成交</option>
              <option value="risk">风控</option>
            </select>
            <button @click="loadTradeLogs" class="btn-refresh-small">🔄</button>
          </div>
        </div>
        <div v-if="tradeLogs.length === 0" class="empty-state">
          <p>暂无交易日志</p>
        </div>
        <div v-else class="logs-list">
          <div v-for="log in tradeLogs" :key="log.log_id" :class="['log-item', log.log_type]">
            <div class="log-header">
              <span :class="['log-type-badge', log.log_type]">{{ getLogTypeLabel(log.log_type) }}</span>
              <span class="log-time">{{ formatTimeShort(log.timestamp) }}</span>
            </div>
            <div class="log-content">
              <span v-if="log.stock_code" class="log-stock">{{ log.stock_code }}</span>
              <span class="log-message">{{ log.message }}</span>
            </div>
            <div class="log-details" v-if="log.direction || log.price">
              <span v-if="log.direction" :class="['log-direction', log.direction === 'BUY' ? 'buy' : 'sell']">
                {{ log.direction === 'BUY' ? '买' : '卖' }}
              </span>
              <span v-if="log.quantity" class="log-quantity">{{ log.quantity }}股</span>
              <span v-if="log.price" class="log-price">¥{{ log.price.toFixed(2) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 交易对话框 -->
    <div v-if="showTradeDialog" class="modal-overlay" @click="showTradeDialog = false">
      <div class="modal-content" @click.stop>
        <h3>{{ tradeForm.action === 'BUY' ? '买入' : '卖出' }}股票</h3>
        
        <div class="trade-tabs">
          <button 
            :class="['tab-btn', { active: tradeForm.action === 'BUY' }]"
            @click="tradeForm.action = 'BUY'"
          >
            买入
          </button>
          <button 
            :class="['tab-btn', { active: tradeForm.action === 'SELL' }]"
            @click="tradeForm.action = 'SELL'"
          >
            卖出
          </button>
        </div>

        <div class="form-group">
          <label>股票代码</label>
          <input 
            v-model="tradeForm.stock_code" 
            placeholder="如：600519"
            class="input-field"
          />
        </div>
        <div class="form-group">
          <label>数量（股）</label>
          <input 
            v-model.number="tradeForm.quantity" 
            type="number"
            placeholder="100"
            class="input-field"
          />
          <small>A股最小100股（1手）</small>
        </div>
        <div class="form-group">
          <label>价格（元）</label>
          <input 
            v-model.number="tradeForm.price" 
            type="number"
            step="0.01"
            placeholder="市价"
            class="input-field"
          />
        </div>
        
        <div class="trade-info">
          <p>预计金额: ¥{{ formatAmount((tradeForm.price || 0) * tradeForm.quantity) }}</p>
          <p>预计手续费: ¥{{ formatAmount((tradeForm.price || 0) * tradeForm.quantity * 0.0003) }}</p>
        </div>

        <div class="modal-actions">
          <button @click="executeTrade" class="btn-primary">
            {{ tradeForm.action === 'BUY' ? '买入' : '卖出' }}
          </button>
          <button @click="showTradeDialog = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import API_BASE_URL from '@/config/api.js'
import { 
  calculateAllIndicators, 
  detectAllSignals, 
  detectAllPatterns,
  getSignalSummary
} from '@/utils/technicalIndicators'
import { 
  isTradingTime, 
  getTradingStatus, 
  getRefreshInterval,
  createAdaptiveRefreshTimer 
} from '@/utils/tradingTime.js'

export default {
  name: 'SimpleTradingView',
  components: {
  },
  setup() {
    const API_BASE = `${API_BASE_URL}/api/trading`
    const KLINE_API = `${API_BASE_URL}/api/kline`

    // 状态
    const portfolio = ref(null)
    const trades = ref([])
    const tradeLogs = ref([])
    const showTradeDialog = ref(false)

    // 日志筛选
    const logFilter = reactive({
      type: '',
      source: ''
    })

    // K线图状态
    const klineStock = ref('600519')
    const klinePeriod = ref('daily')
    const klineData = ref([])
    const klineLoading = ref(false)
    const klineError = ref('')
    const klineChart = ref(null)
    let chartInstance = null
    const dataSource = ref('')
    const currentIndicators = ref({})
    const currentOrderInfo = ref(null)  // 当前订单信息

    // 标记相关
    const chartMarkers = ref([])
    const chartDrawings = ref([])
    const showPriceMarkerModal = ref(false)
    const priceMarkerForm = ref({
      price: '',
      label: '',
      type: 'support'
    })
    
    // ==================== 实时刷新相关状态 ====================
    const realtimeRefreshEnabled = ref(true)  // 是否启用实时刷新
    const tradingStatus = ref(null)           // 当前交易状态
    const klineRefreshTimer = ref(null)       // K线刷新定时器
    const portfolioRefreshTimer = ref(null)   // 持仓刷新定时器
    const refreshCountdown = ref(0)           // 刷新倒计时（秒）
    const lastRefreshTime = ref(null)         // 上次刷新时间
    const isAutoRefreshing = ref(false)       // 是否正在自动刷新
    let countdownInterval = null              // 倒计时定时器

// 技术指标开关
    const indicators = reactive({
      ma5: true,
      ma20: true,
      ma60: false,
      boll: false,
      macd: false,
      rsi: false,
      kdj: false,
      sixPulse: true,  // 六脉神剑副图
      showSignals: true,  // 显示交易信号
      showPatterns: true,  // 显示K线形态
      showLargeOrders: true  // 显示机构大单
    })
    
    // 固定图表高度（保持界面稳定，切换指标时不跳动）
    const chartHeight = computed(() => 520)
    
    // 信号和形态数据
    const detectedSignals = ref([])
    const detectedPatterns = ref([])
    const signalSummary = ref(null)
    
    // 六脉神剑综合指标数据
    const sixPulseData = ref(null)
    const sixPulseIndicators = ref([])
    const sixPulseSummary = ref({ bullish: 0, bearish: 0, signal: 'HOLD', signalText: '观望' })
    const sixPulseChartData = ref([])
    
    // 机构大单数据
    const largeOrderSignals = ref([])

    // 周期选项
    const periods = [
      { value: '1', label: '1分' },
      { value: '5', label: '5分' },
      { value: '10', label: '10分' },
      { value: '15', label: '15分' },
      { value: '30', label: '30分' },
      { value: '60', label: '60分' },
      { value: 'daily', label: '日线' },
      { value: 'weekly', label: '周线' },
      { value: 'monthly', label: '月线' }
    ]

    // 表单
    const tradeForm = reactive({
      action: 'BUY',
      stock_code: '',
      quantity: 100,
      price: 100,
      order_type: 'LIMIT'
    })
    
    // 加载组合
    const loadPortfolio = async () => {
      try {
        console.log('🔍 加载投资组合...')
        const response = await axios.get(`${API_BASE}/portfolio`)
        console.log('📦 API响应:', response.data)
        
        if (response.data.success) {
          portfolio.value = response.data.portfolio
          console.log(`✅ 加载成功`)
        }
      } catch (error) {
        console.error('❌ 加载失败:', error)
        alert('加载失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 加载交易历史
    const loadTrades = async () => {
      try {
        const response = await axios.get(`${API_BASE}/history?limit=50`)
        if (response.data.success) {
          trades.value = response.data.trades
        }
      } catch (error) {
        console.error('加载交易历史失败:', error)
      }
    }

    // 加载策略交易日志
    const loadTradeLogs = async () => {
      try {
        const params = new URLSearchParams()
        params.append('limit', '100')
        if (logFilter.type) params.append('log_type', logFilter.type)
        if (logFilter.source) params.append('source', logFilter.source)

        const response = await axios.get(`${API_BASE_URL}/api/strategy-center/logs?${params.toString()}`)
        if (response.data.success) {
          tradeLogs.value = response.data.data || []
        }
      } catch (error) {
        console.error('加载交易日志失败:', error)
        tradeLogs.value = []
      }
    }

    // 获取来源标签
    const getSourceLabel = (source) => {
      const labels = {
        'manual': '手动',
        'auto': '自动',
        'strategy': '策略'
      }
      return labels[source] || '手动'
    }

    // 获取日志类型标签
    const getLogTypeLabel = (logType) => {
      const labels = {
        'signal': '信号',
        'order': '订单',
        'execution': '成交',
        'risk': '风控',
        'system': '系统'
      }
      return labels[logType] || logType
    }
    
    // 执行交易
    const executeTrade = async () => {
      if (!tradeForm.stock_code || !tradeForm.quantity || !tradeForm.price) {
        alert('请填写完整信息')
        return
      }
      
      try {
        const response = await axios.post(`${API_BASE}/execute`, {
          stock_code: tradeForm.stock_code,
          action: tradeForm.action,
          quantity: tradeForm.quantity,
          price: tradeForm.price,
          order_type: tradeForm.order_type
        })
        
        if (response.data.success) {
          alert('交易成功！')
          showTradeDialog.value = false
          // 重置表单
          tradeForm.stock_code = ''
          tradeForm.quantity = 100
          tradeForm.price = 100
          // 刷新数据
          await loadPortfolio()
          await loadTrades()
        }
      } catch (error) {
        console.error('交易失败:', error)
        alert('交易失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // 快速卖出
    const quickSell = (position) => {
      tradeForm.action = 'SELL'
      tradeForm.stock_code = position.stock_code
      tradeForm.quantity = position.quantity
      tradeForm.price = position.current_price
      showTradeDialog.value = true
    }
    
    // 重置账户
    const resetAccount = async () => {
      if (!confirm('确定要重置账户吗？所有数据将被清空！')) return
      
      try {
        await axios.post(`${API_BASE}/reset`)
        alert('账户已重置')
        await loadPortfolio()
        await loadTrades()
      } catch (error) {
        console.error('重置失败:', error)
        alert('重置失败: ' + error.message)
      }
    }
    
    // 格式化函数
    const formatAmount = (amount) => {
      return amount.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }
    
    const formatTime = (timestamp) => {
      return new Date(timestamp).toLocaleString('zh-CN')
    }

    const formatTimeShort = (timestamp) => {
      const date = new Date(timestamp)
      return `${(date.getMonth() + 1).toString().padStart(2, '0')}-${date.getDate().toString().padStart(2, '0')} ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
    }
    
    const getProfitClass = (value) => {
      if (value > 0) return 'text-success'
      if (value < 0) return 'text-danger'
      return ''
    }
    
    // 计算移动平均线
    const calculateMA = (data, period) => {
      const result = []
      for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
          result.push(null)
        } else {
          let sum = 0
          for (let j = 0; j < period; j++) {
            sum += Number(data[i - j].close) || 0
          }
          result.push((sum / period).toFixed(2))
        }
      }
      return result
    }
    
    // 计算布林带
    const calculateBoll = (data, period = 20, multiplier = 2) => {
      const upper = []
      const middle = []
      const lower = []

      for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
          upper.push(null)
          middle.push(null)
          lower.push(null)
        } else {
          // 计算中轨（MA20）
          let sum = 0
          for (let j = 0; j < period; j++) {
            sum += Number(data[i - j].close) || 0
          }
          const ma = sum / period

          // 计算标准差
          let squareSum = 0
          for (let j = 0; j < period; j++) {
            const diff = (Number(data[i - j].close) || 0) - ma
            squareSum += diff * diff
          }
          const std = Math.sqrt(squareSum / period)

          middle.push(ma.toFixed(2))
          upper.push((ma + multiplier * std).toFixed(2))
          lower.push((ma - multiplier * std).toFixed(2))
        }
      }

      return { upper, middle, lower }
    }

    // 计算MACD
    const calculateMACD = (data) => {
      const dif = [], dea = [], macd = []

      const calcEMA = (prices, period) => {
        const result = []
        const mult = 2 / (period + 1)
        for (let i = 0; i < prices.length; i++) {
          if (i === 0) result.push(prices[i])
          else result.push((prices[i] - result[i - 1]) * mult + result[i - 1])
        }
        return result
      }

      const closes = data.map(d => Number(d.close) || 0)
      const ema12 = calcEMA(closes, 12)
      const ema26 = calcEMA(closes, 26)

      for (let i = 0; i < data.length; i++) {
        if (i < 25) {
          dif.push(null)
          dea.push(null)
          macd.push(null)
        } else {
          dif.push((ema12[i] - ema26[i]).toFixed(3))
        }
      }

      const difValues = dif.filter(v => v !== null).map(v => parseFloat(v))
      const deaData = calcEMA(difValues, 9)

      let deaIdx = 0
      for (let j = 0; j < data.length; j++) {
        if (dif[j] !== null) {
          dea[j] = deaData[deaIdx].toFixed(3)
          macd[j] = ((parseFloat(dif[j]) - parseFloat(dea[j])) * 2).toFixed(3)
          deaIdx++
        }
      }

      return { DIF: dif, DEA: dea, MACD: macd }
    }

    // 计算RSI
    const calculateRSI = (data, period = 14) => {
      const result = []
      for (let i = 0; i < data.length; i++) {
        if (i < period) {
          result.push(null)
        } else {
          let gains = 0, losses = 0
          for (let j = i - period + 1; j <= i; j++) {
            const change = (Number(data[j].close) || 0) - (Number(data[j - 1].close) || 0)
            if (change > 0) gains += change
            else losses -= change
          }
          const avgGain = gains / period
          const avgLoss = losses / period
          const rs = avgLoss === 0 ? 100 : avgGain / avgLoss
          result.push((100 - 100 / (1 + rs)).toFixed(2))
        }
      }
      return result
    }

    // 计算KDJ
    const calculateKDJ = (data, period = 9) => {
      const K = [], D = [], J = []
      let prevK = 50, prevD = 50

      for (let i = 0; i < data.length; i++) {
        if (i < period - 1) {
          K.push(null)
          D.push(null)
          J.push(null)
        } else {
          let high = -Infinity, low = Infinity
          for (let j = i - period + 1; j <= i; j++) {
            high = Math.max(high, Number(data[j].high) || 0)
            low = Math.min(low, Number(data[j].low) || 0)
          }

          const close = Number(data[i].close) || 0
          const rsv = high === low ? 50 : ((close - low) / (high - low)) * 100

          const kVal = (2 / 3) * prevK + (1 / 3) * rsv
          const dVal = (2 / 3) * prevD + (1 / 3) * kVal
          const jVal = 3 * kVal - 2 * dVal

          K.push(kVal.toFixed(2))
          D.push(dVal.toFixed(2))
          J.push(jVal.toFixed(2))

          prevK = kVal
          prevD = dVal
        }
      }

      return { K, D, J }
    }
    
    // 选择周期
    const selectPeriod = (period) => {
      klinePeriod.value = period
      loadKlineData()
    }
    
    // 加载K线数据
    const loadKlineData = async () => {
      if (!klineStock.value) {
        klineError.value = '请输入股票代码'
        return
      }

      console.log('开始加载K线数据:', klineStock.value, klinePeriod.value)
      klineLoading.value = true
      klineError.value = ''

      try {
        const url = `${KLINE_API}/data`
        const params = {
          symbol: klineStock.value,
          period: klinePeriod.value,
          adjust: 'qfq',
          limit: 200
        }
        console.log('请求URL:', url)
        console.log('请求参数:', params)

        const response = await axios.get(url, { params })

        console.log('API响应:', response.data)

        if (response.data.success) {
          // 统一字段名映射，确保 date 字段存在
          klineData.value = response.data.data.map(item => ({
            date: item.time || item.date,
            time: item.time || item.date,
            open: parseFloat(item.open) || 0,
            high: parseFloat(item.high) || 0,
            low: parseFloat(item.low) || 0,
            close: parseFloat(item.close) || 0,
            volume: parseFloat(item.volume) || 0
          }))
          dataSource.value = response.data.source || 'akshare'
          console.log('获取到数据条数:', klineData.value.length)

          if (klineData.value.length === 0) {
            klineError.value = '没有获取到K线数据，请检查股票代码是否正确'
          } else {
            // 计算当前指标值
            const lastIdx = klineData.value.length - 1
            const ma5Data = calculateMA(klineData.value, 5)
            const ma10Data = calculateMA(klineData.value, 10)
            const ma20Data = calculateMA(klineData.value, 20)
            const rsiData = calculateRSI(klineData.value)
            const macdData = calculateMACD(klineData.value)

currentIndicators.value = {
              MA5: ma5Data[lastIdx] ? parseFloat(ma5Data[lastIdx]) : null,
              MA10: ma10Data[lastIdx] ? parseFloat(ma10Data[lastIdx]) : null,
              MA20: ma20Data[lastIdx] ? parseFloat(ma20Data[lastIdx]) : null,
              RSI: rsiData[lastIdx] ? parseFloat(rsiData[lastIdx]) : null,
              MACD: macdData.MACD[lastIdx] ? parseFloat(macdData.MACD[lastIdx]) : null
            }
            
            // 检测交易信号和K线形态
            try {
              const allIndicators = calculateAllIndicators(klineData.value)
              detectedSignals.value = detectAllSignals(klineData.value, allIndicators)
              detectedPatterns.value = detectAllPatterns(klineData.value)
              signalSummary.value = getSignalSummary([...detectedSignals.value, ...detectedPatterns.value.map(p => ({
                ...p,
                direction: p.type === 'bullish' ? 'bullish' : (p.type === 'bearish' ? 'bearish' : 'neutral')
              }))])
              console.log('检测到信号:', detectedSignals.value.length, '个, 形态:', detectedPatterns.value.length, '个')
              
              // 处理六脉神剑综合指标数据
              if (allIndicators.SIX_PULSE) {
                sixPulseData.value = allIndicators.SIX_PULSE
                const lastSignal = allIndicators.SIX_PULSE.signals[lastIdx]
                
                // 构建六脉神剑指标显示数据
                sixPulseIndicators.value = [
                  {
                    name: 'MACD',
                    value: allIndicators.SIX_PULSE.MACD.MACD[lastIdx]?.toFixed(3) || '-',
                    status: allIndicators.SIX_PULSE.MACD.DIF[lastIdx] > allIndicators.SIX_PULSE.MACD.DEA[lastIdx] ? 'bullish' : 'bearish',
                    statusText: allIndicators.SIX_PULSE.MACD.DIF[lastIdx] > allIndicators.SIX_PULSE.MACD.DEA[lastIdx] ? '多头' : '空头',
                    description: 'DIF与DEA的关系判断趋势方向'
                  },
                  {
                    name: 'KDJ',
                    value: `K:${allIndicators.SIX_PULSE.KDJ.K[lastIdx]?.toFixed(1) || '-'}`,
                    status: allIndicators.SIX_PULSE.KDJ.K[lastIdx] > allIndicators.SIX_PULSE.KDJ.D[lastIdx] ? 'bullish' : 'bearish',
                    statusText: allIndicators.SIX_PULSE.KDJ.K[lastIdx] > allIndicators.SIX_PULSE.KDJ.D[lastIdx] ? '多头' : '空头',
                    description: 'K线与D线的交叉判断买卖点'
                  },
                  {
                    name: 'RSI',
                    value: allIndicators.SIX_PULSE.RSI[lastIdx]?.toFixed(1) || '-',
                    status: allIndicators.SIX_PULSE.RSI[lastIdx] > 50 ? 'bullish' : 'bearish',
                    statusText: allIndicators.SIX_PULSE.RSI[lastIdx] > 70 ? '超买' : (allIndicators.SIX_PULSE.RSI[lastIdx] < 30 ? '超卖' : (allIndicators.SIX_PULSE.RSI[lastIdx] > 50 ? '多头' : '空头')),
                    description: 'RSI>50为多头区域，<50为空头区域'
                  },
                  {
                    name: 'LWR',
                    value: allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx]?.toFixed(1) || '-',
                    status: (allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx] || 50) < 50 ? 'bullish' : 'bearish',
                    statusText: (allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx] || 50) < 30 ? '超买' : ((allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx] || 50) > 70 ? '超卖' : ((allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx] || 50) < 50 ? '多头' : '空头')),
                    description: 'LWR<50为多头，>50为空头'
                  },
                  {
                    name: 'BBI',
                    value: allIndicators.SIX_PULSE.BBI?.[lastIdx]?.toFixed(2) || '-',
                    status: klineData.value[lastIdx].close > (allIndicators.SIX_PULSE.BBI?.[lastIdx] || 0) ? 'bullish' : 'bearish',
                    statusText: klineData.value[lastIdx].close > (allIndicators.SIX_PULSE.BBI?.[lastIdx] || 0) ? '多头' : '空头',
                    description: '价格在BBI上方为多头，下方为空头'
                  },
                  {
                    name: 'MTM',
                    value: allIndicators.SIX_PULSE.MTM?.MTM?.[lastIdx]?.toFixed(2) || '-',
                    status: (allIndicators.SIX_PULSE.MTM?.MTM?.[lastIdx] || 0) > 0 ? 'bullish' : 'bearish',
                    statusText: (allIndicators.SIX_PULSE.MTM?.MTM?.[lastIdx] || 0) > 0 ? '多头' : '空头',
                    description: 'MTM>0表示上涨动能，<0表示下跌动能'
                  }
                ]
                
                // 六脉神剑综合信号
                sixPulseSummary.value = {
                  bullish: lastSignal?.bullish || 0,
                  bearish: lastSignal?.bearish || 0,
                  signal: lastSignal?.signal || 'HOLD',
                  signalText: lastSignal?.signal === 'BUY' ? '🟢 买入' : (lastSignal?.signal === 'SELL' ? '🔴 卖出' : '⚪ 观望')
                }
                console.log('六脉神剑信号:', sixPulseSummary.value)
                
                // 构建六脉神剑副图数据
                sixPulseChartData.value = allIndicators.SIX_PULSE.signals.map((sig, idx) => {
                  const sp = allIndicators.SIX_PULSE
                  return {
                    macd: sp.MACD.DIF[idx] > sp.MACD.DEA[idx] ? 1 : -1,
                    kdj: sp.KDJ.K[idx] > sp.KDJ.D[idx] ? 1 : -1,
                    rsi: sp.RSI[idx] > 50 ? 1 : -1,
                    lwr: (sp.LWR?.LWR2?.[idx] || 50) < 50 ? 1 : -1,
                    bbi: klineData.value[idx]?.close > (sp.BBI?.[idx] || 0) ? 1 : -1,
                    mtm: (sp.MTM?.MTM?.[idx] || 0) > 0 ? 1 : -1,
                    bullish: sig?.bullish || 0,
                    bearish: sig?.bearish || 0
                  }
                })
              }
              
              // 识别机构大单
              largeOrderSignals.value = detectLargeOrders(klineData.value)
              console.log('识别到机构大单:', largeOrderSignals.value.length, '个')
            } catch (err) {
              console.error('信号检测失败:', err)
            }

            await nextTick()
            requestAnimationFrame(() => {
              renderKlineChart()
            })
          }
        } else {
          klineError.value = '获取数据失败'
        }
      } catch (error) {
        console.error('K线数据加载失败:', error)
        console.error('错误详情:', error.response)
        klineError.value = '加载失败: ' + (error.response?.data?.detail || error.message)
      } finally {
        klineLoading.value = false
      }
    }
    
    // 渲染K线图
    const renderKlineChart = () => {
      if (!klineChart.value || klineData.value.length === 0) return

      try {
        const dom = klineChart.value
        const existedInstance = echarts.getInstanceByDom(dom)
        if (existedInstance && existedInstance !== chartInstance) {
          chartInstance = existedInstance
        }

        if (!chartInstance) {
          chartInstance = echarts.init(dom)
        } else if (chartInstance.getDom() !== dom) {
          chartInstance.dispose()
          chartInstance = echarts.init(dom)
        } else {
          chartInstance.clear()
          chartInstance.resize()
        }

        // 准备数据
        const dates = klineData.value.map(item => item.time || item.date)
        const values = klineData.value.map(item => [
          Number(item.open) || 0,
          Number(item.close) || 0,
          Number(item.low) || 0,
          Number(item.high) || 0
        ])
        const volumes = klineData.value.map(item => Number(item.volume) || 0)

        // 计算技术指标
        const ma5Data = indicators.ma5 ? calculateMA(klineData.value, 5) : []
        const ma20Data = indicators.ma20 ? calculateMA(klineData.value, 20) : []
        const ma60Data = indicators.ma60 ? calculateMA(klineData.value, 60) : []
        const bollData = indicators.boll ? calculateBoll(klineData.value, 20, 2) : { upper: [], middle: [], lower: [] }
        const macdData = indicators.macd ? calculateMACD(klineData.value) : { DIF: [], DEA: [], MACD: [] }
        const rsiData = indicators.rsi ? calculateRSI(klineData.value) : []
        const kdjData = indicators.kdj ? calculateKDJ(klineData.value) : { K: [], D: [], J: [] }

        // 构建图例数据
        const legendData = ['K线', '成交量']
        if (indicators.ma5) legendData.push('MA5')
        if (indicators.ma20) legendData.push('MA20')
        if (indicators.ma60) legendData.push('MA60')

        // 动态计算grid布局 - 填满整个图表区域
        let gridCount = 2 // K线 + 成交量
        
        if (indicators.macd) gridCount++
        if (indicators.rsi || indicators.kdj) gridCount++
        if (indicators.sixPulse) gridCount++
        
        // 预留空间：顶部8%用于标题/图例，底部6%用于dataZoom
        const topReserved = 8
        const bottomReserved = 6
        const availableHeight = 100 - topReserved - bottomReserved // 86%
        
        // 根据副图数量分配高度
        let klineHeight, volumeHeight, subChartHeight
        
        if (gridCount === 2) {
          // 只有K线和成交量
          klineHeight = 70
          volumeHeight = 16
        } else if (gridCount === 3) {
          // 1个副图
          klineHeight = 58
          volumeHeight = 13
          subChartHeight = 13
        } else if (gridCount === 4) {
          // 2个副图
          klineHeight = 50
          volumeHeight = 11
          subChartHeight = 11
        } else {
          // 3个副图（含六脉神剑）
          klineHeight = 44
          volumeHeight = 10
          subChartHeight = 9
        }
        
        let currentTop = topReserved
        
        const grids = [
          { left: '1%', right: '1%', top: currentTop + '%', height: klineHeight + '%', containLabel: true }
        ]
        currentTop += klineHeight + 1
        
        grids.push({ left: '1%', right: '1%', top: currentTop + '%', height: volumeHeight + '%', containLabel: true })
        currentTop += volumeHeight + 1
        
        if (indicators.macd) {
          grids.push({ left: '1%', right: '1%', top: currentTop + '%', height: subChartHeight + '%', containLabel: true })
          currentTop += subChartHeight + 1
        }
        if (indicators.rsi || indicators.kdj) {
          grids.push({ left: '1%', right: '1%', top: currentTop + '%', height: subChartHeight + '%', containLabel: true })
          currentTop += subChartHeight + 1
        }
        if (indicators.sixPulse) {
          grids.push({ left: '1%', right: '1%', top: currentTop + '%', height: subChartHeight + '%', containLabel: true })
          currentTop += subChartHeight + 1
        }

        // 构建xAxis - 与策略中心保持一致
        const xAxisArr = [
          { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { color: '#64748b', fontSize: 10 }, boundaryGap: true },
          { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { show: false }, boundaryGap: true }
        ]
        
        let xAxisIdx = 2
        if (indicators.macd) {
          xAxisArr.push({ type: 'category', data: dates, gridIndex: xAxisIdx, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { show: false }, boundaryGap: true })
          xAxisIdx++
        }
        
        if (indicators.rsi || indicators.kdj) {
          xAxisArr.push({ type: 'category', data: dates, gridIndex: xAxisIdx, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { show: false }, boundaryGap: true })
          xAxisIdx++
        }
        
        if (indicators.sixPulse) {
          xAxisArr.push({ type: 'category', data: dates, gridIndex: xAxisIdx, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { color: '#64748b', fontSize: 10 }, boundaryGap: true })
        }

        // 构建yAxis - 与策略中心保持一致
        const yAxisArr = [
          { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)' } }, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { color: '#64748b' } },
          { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { show: false }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { show: false } }
        ]
        
        let yAxisIdx = 2
        if (indicators.macd) {
          yAxisArr.push({ scale: true, gridIndex: yAxisIdx, splitNumber: 2, axisLabel: { color: '#64748b', fontSize: 10 }, axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } } })
          yAxisIdx++
        }
        
        if (indicators.rsi || indicators.kdj) {
          yAxisArr.push({ scale: true, gridIndex: yAxisIdx, splitNumber: 2, min: 0, max: 100, axisLabel: { color: '#64748b', fontSize: 10 }, axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } } })
          yAxisIdx++
        }
        
        if (indicators.sixPulse) {
          yAxisArr.push({ scale: true, gridIndex: yAxisIdx, splitNumber: 2, min: -6, max: 6, axisLabel: { show: false }, axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } } })
        }

        // 构建series - K线和成交量（与策略中心保持一致）
        const seriesArr = [
          {
            name: 'K线',
            type: 'candlestick',
            data: values,
            itemStyle: { color: '#ef5350', color0: '#26a69a', borderColor: '#ef5350', borderColor0: '#26a69a' },
            markPoint: {
              data: [
                // 用户手动添加的标记
                ...chartMarkers.value.map(m => ({
                  name: m.label,
                  coord: [m.date, m.price],
                  value: m.label,
                  itemStyle: { color: m.color || '#f59e0b' },
                  label: { show: true, formatter: m.label, color: '#fff', fontSize: 10 }
                })),
                // 自动检测的信号标记
                ...(indicators.showSignals ? getSignalMarkPoints(detectedSignals.value, dates, klineData.value) : []),
                // 自动检测的形态标记
                ...(indicators.showPatterns ? getPatternMarkPoints(detectedPatterns.value, dates, klineData.value) : []),
                // 机构大单标记
                ...(indicators.showLargeOrders ? getLargeOrderMarkPoints(largeOrderSignals.value, dates, klineData.value) : [])
              ],
              symbolSize: 30,
              label: { show: true, fontSize: 10, color: '#fff' }
            },
            markLine: {
              silent: true,
              data: chartDrawings.value.filter(d => d.type === 'hline').map(d => ({
                yAxis: d.price,
                lineStyle: { color: d.color || '#f59e0b', type: 'dashed' },
                label: { formatter: d.label || d.price.toFixed(2), color: d.color || '#f59e0b' }
              }))
            }
          },
          {
            name: '成交量',
            type: 'bar',
            xAxisIndex: 1,
            yAxisIndex: 1,
            data: volumes,
            itemStyle: {
              color: (params) => {
                const idx = params.dataIndex
                const isUp = klineData.value[idx].close >= klineData.value[idx].open
                // 计算成交量是否异常放大（超过5日均量的1.5倍）
                if (idx >= 5) {
                  let avgVol = 0
                  for (let i = idx - 5; i < idx; i++) {
                    avgVol += klineData.value[i].volume
                  }
                  avgVol /= 5
                  const isLargeVolume = klineData.value[idx].volume > avgVol * 1.5
                  if (isLargeVolume) {
                    // 放量时使用更亮的颜色
                    return isUp ? '#ff6b6b' : '#20c997'
                  }
                }
                return isUp ? '#ef5350' : '#26a69a'
              }
            },
            // 成交量异常标记
            markPoint: {
              data: (() => {
                const marks = []
                for (let i = 5; i < klineData.value.length; i++) {
                  let avgVol = 0
                  for (let j = i - 5; j < i; j++) {
                    avgVol += klineData.value[j].volume
                  }
                  avgVol /= 5
                  // 放量超过2倍
                  if (klineData.value[i].volume > avgVol * 2) {
                    marks.push({
                      coord: [dates[i], klineData.value[i].volume],
                      value: '放量',
                      symbol: 'pin',
                      symbolSize: 25,
                      itemStyle: { color: '#f59e0b' },
                      label: { show: true, formatter: '放量', fontSize: 8, color: '#fff' }
                    })
                  }
                }
                // 只显示最近10个放量点
                return marks.slice(-10)
              })()
            }
          }
        ]

        // 均线
        if (indicators.ma5) seriesArr.push({ name: 'MA5', type: 'line', data: ma5Data, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#f5d742' } })
        if (indicators.ma20) seriesArr.push({ name: 'MA20', type: 'line', data: ma20Data, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#42a5f5' } })
        if (indicators.ma60) seriesArr.push({ name: 'MA60', type: 'line', data: ma60Data, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ab47bc' } })

        // 布林带
        if (indicators.boll) {
          seriesArr.push(
            { name: 'BOLL上轨', type: 'line', data: bollData.upper, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800', type: 'dashed' } },
            { name: 'BOLL中轨', type: 'line', data: bollData.middle, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800' } },
            { name: 'BOLL下轨', type: 'line', data: bollData.lower, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800', type: 'dashed' } }
          )
        }

        // MACD副图
        if (indicators.macd) {
          seriesArr.push(
            { name: 'DIF', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: macdData.DIF, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#42a5f5' } },
            { name: 'DEA', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: macdData.DEA, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800' } },
            { name: 'MACD柱', type: 'bar', xAxisIndex: 2, yAxisIndex: 2, data: macdData.MACD, itemStyle: { color: (params) => parseFloat(params.data) >= 0 ? '#ef5350' : '#26a69a' } }
          )
        }

        // RSI/KDJ副图 - 动态计算坐标轴索引
        let rsiKdjAxisIndex = 2
        if (indicators.macd) rsiKdjAxisIndex++
        
        if (indicators.rsi) {
          seriesArr.push({
            name: 'RSI',
            type: 'line',
            xAxisIndex: rsiKdjAxisIndex,
            yAxisIndex: rsiKdjAxisIndex,
            data: rsiData,
            smooth: true,
            showSymbol: false,
            lineStyle: { width: 1, color: '#ab47bc' },
            markLine: { silent: true, data: [{ yAxis: 70, lineStyle: { color: '#ef5350', type: 'dashed' } }, { yAxis: 30, lineStyle: { color: '#26a69a', type: 'dashed' } }] }
          })
        }

        if (indicators.kdj) {
          seriesArr.push(
            { name: 'K', type: 'line', xAxisIndex: rsiKdjAxisIndex, yAxisIndex: rsiKdjAxisIndex, data: kdjData.K, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#42a5f5' } },
            { name: 'D', type: 'line', xAxisIndex: rsiKdjAxisIndex, yAxisIndex: rsiKdjAxisIndex, data: kdjData.D, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800' } },
            { name: 'J', type: 'line', xAxisIndex: rsiKdjAxisIndex, yAxisIndex: rsiKdjAxisIndex, data: kdjData.J, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#e91e63' } }
          )
        }
        
        // 六脉神剑副图 - 堆叠柱状图
        if (indicators.sixPulse && sixPulseChartData.value && sixPulseChartData.value.length > 0) {
          // 计算六脉神剑副图的坐标轴索引
          let sixPulseAxisIndex = 2
          if (indicators.macd) sixPulseAxisIndex++
          if (indicators.rsi || indicators.kdj) sixPulseAxisIndex++
          
          // 六脉神剑6个指标的颜色定义
          const sixPulseColors = {
            macd: '#42a5f5',   // 蓝色 - MACD
            kdj: '#ff9800',    // 橙色 - KDJ
            rsi: '#ab47bc',    // 紫色 - RSI
            lwr: '#26a69a',    // 青色 - LWR
            bbi: '#f5d742',    // 黄色 - BBI
            mtm: '#e91e63'     // 粉色 - MTM
          }
          
          // 为每个指标创建堆叠柱状图数据
          const macdBarData = sixPulseChartData.value.map(d => d ? d.macd : 0)
          const kdjBarData = sixPulseChartData.value.map(d => d ? d.kdj : 0)
          const rsiBarData = sixPulseChartData.value.map(d => d ? d.rsi : 0)
          const lwrBarData = sixPulseChartData.value.map(d => d ? d.lwr : 0)
          const bbiBarData = sixPulseChartData.value.map(d => d ? d.bbi : 0)
          const mtmBarData = sixPulseChartData.value.map(d => d ? d.mtm : 0)
          
          // 添加六脉神剑堆叠柱状图系列
          seriesArr.push(
            {
              name: 'MACD信号',
              type: 'bar',
              xAxisIndex: sixPulseAxisIndex,
              yAxisIndex: sixPulseAxisIndex,
              stack: 'sixPulse',
              data: macdBarData,
              barWidth: '60%',
              itemStyle: { 
                color: (params) => params.data >= 0 ? sixPulseColors.macd : 'rgba(66, 165, 245, 0.5)'
              }
            },
            {
              name: 'KDJ信号',
              type: 'bar',
              xAxisIndex: sixPulseAxisIndex,
              yAxisIndex: sixPulseAxisIndex,
              stack: 'sixPulse',
              data: kdjBarData,
              barWidth: '60%',
              itemStyle: { 
                color: (params) => params.data >= 0 ? sixPulseColors.kdj : 'rgba(255, 152, 0, 0.5)'
              }
            },
            {
              name: 'RSI信号',
              type: 'bar',
              xAxisIndex: sixPulseAxisIndex,
              yAxisIndex: sixPulseAxisIndex,
              stack: 'sixPulse',
              data: rsiBarData,
              barWidth: '60%',
              itemStyle: { 
                color: (params) => params.data >= 0 ? sixPulseColors.rsi : 'rgba(171, 71, 188, 0.5)'
              }
            },
            {
              name: 'LWR信号',
              type: 'bar',
              xAxisIndex: sixPulseAxisIndex,
              yAxisIndex: sixPulseAxisIndex,
              stack: 'sixPulse',
              data: lwrBarData,
              barWidth: '60%',
              itemStyle: { 
                color: (params) => params.data >= 0 ? sixPulseColors.lwr : 'rgba(38, 166, 154, 0.5)'
              }
            },
            {
              name: 'BBI信号',
              type: 'bar',
              xAxisIndex: sixPulseAxisIndex,
              yAxisIndex: sixPulseAxisIndex,
              stack: 'sixPulse',
              data: bbiBarData,
              barWidth: '60%',
              itemStyle: { 
                color: (params) => params.data >= 0 ? sixPulseColors.bbi : 'rgba(245, 215, 66, 0.5)'
              }
            },
            {
              name: 'MTM信号',
              type: 'bar',
              xAxisIndex: sixPulseAxisIndex,
              yAxisIndex: sixPulseAxisIndex,
              stack: 'sixPulse',
              data: mtmBarData,
              barWidth: '60%',
              itemStyle: { 
                color: (params) => params.data >= 0 ? sixPulseColors.mtm : 'rgba(233, 30, 99, 0.5)'
              }
            }
          )
          
          // 添加零轴线
          seriesArr.push({
            name: '六脉零轴',
            type: 'line',
            xAxisIndex: sixPulseAxisIndex,
            yAxisIndex: sixPulseAxisIndex,
            data: dates.map(() => 0),
            showSymbol: false,
            lineStyle: { width: 1, color: 'rgba(148, 163, 184, 0.5)', type: 'dashed' }
          })
        }

        const option = {
          backgroundColor: 'transparent',
          title: {
            text: `${klineStock.value} - ${getPeriodLabel(klinePeriod.value)}`,
            subtext: dataSource.value ? `数据源: ${dataSource.value}` : '',
            left: '40%',top:'1%',
            textStyle: { color: '#e2e8f0', fontSize: 16 },
            subtextStyle: { color: '#64748b', fontSize: 12 }
          },
          tooltip: {
            trigger: 'axis',
            axisPointer: { type: 'cross' },
            backgroundColor: 'rgba(30, 41, 59, 0.95)',
            borderColor: 'rgba(51, 65, 85, 0.5)',
            textStyle: { color: '#e2e8f0' }
          },
          legend: { data: legendData, textStyle: { color: '#94a3b8' }, top: 5, right: '30%', itemGap: 8, itemWidth: 14, itemHeight: 10 },
          toolbox: {
            show: true,
            feature: {
              saveAsImage: { title: '保存截图', pixelRatio: 2 },
              dataZoom: { title: { zoom: '框选缩放', back: '还原' } },
              restore: { title: '还原' }
            },
            right: 20, top: 5, iconStyle: { borderColor: '#94a3b8' }
          },
          grid: grids,
          xAxis: xAxisArr,
          yAxis: yAxisArr,
          dataZoom: [
            { type: 'inside', xAxisIndex: [0, 1, 2, 3, 4, 5], start: 60, end: 100 },
            { show: true, xAxisIndex: [0, 1, 2, 3, 4, 5], type: 'slider', bottom: '1%', height: 20, start: 60, end: 100, textStyle: { color: '#94a3b8' }, borderColor: '#334155', fillerColor: 'rgba(59, 130, 246, 0.2)' }
          ],
          series: seriesArr
        }

        chartInstance.setOption(option)
      } catch (error) {
        console.error('K线图渲染失败:', error)
        klineError.value = '图表渲染失败: ' + error.message
      }
    }
    
    // 获取周期标签
    const getPeriodLabel = (period) => {
      const labels = {
        '1': '1分钟',
        '5': '5分钟',
        '15': '15分钟',
        '30': '30分钟',
        '60': '60分钟',
        'daily': '日线',
        'weekly': '周线',
        'monthly': '月线'
      }
      return labels[period] || period
    }

// 获取RSI样式类
    const getRSIClass = (rsi) => {
      if (!rsi) return ''
      if (rsi > 70) return 'overbought'
      if (rsi < 30) return 'oversold'
      return 'neutral'
    }
    
    // 获取成交量状态
    const getVolumeStatus = () => {
      if (!klineData.value || klineData.value.length < 6) return '数据不足'
      const lastIdx = klineData.value.length - 1
      const currentVol = klineData.value[lastIdx].volume
      
      let avgVol = 0
      for (let i = lastIdx - 5; i < lastIdx; i++) {
        avgVol += klineData.value[i].volume
      }
      avgVol /= 5
      
      const ratio = currentVol / avgVol
      if (ratio > 2) return '🔥 大幅放量 (' + (ratio * 100).toFixed(0) + '%)'
      if (ratio > 1.5) return '📈 明显放量 (' + (ratio * 100).toFixed(0) + '%)'
      if (ratio > 1.2) return '↗️ 温和放量'
      if (ratio < 0.5) return '📉 大幅缩量'
      if (ratio < 0.8) return '↘️ 温和缩量'
      return '➡️ 量能平稳'
    }
    
    // 获取成交量样式类
    const getVolumeClass = () => {
      if (!klineData.value || klineData.value.length < 6) return ''
      const lastIdx = klineData.value.length - 1
      const currentVol = klineData.value[lastIdx].volume
      
      let avgVol = 0
      for (let i = lastIdx - 5; i < lastIdx; i++) {
        avgVol += klineData.value[i].volume
      }
      avgVol /= 5
      
      const ratio = currentVol / avgVol
      if (ratio > 1.5) return 'volume-up'
      if (ratio < 0.7) return 'volume-down'
      return ''
    }
    
    // 识别机构大单（基于成交量和价格变化）
    const detectLargeOrders = (klineDataArr) => {
      if (!klineDataArr || klineDataArr.length < 10) return []
      
      const signals = []
      
      for (let i = 5; i < klineDataArr.length; i++) {
        const current = klineDataArr[i]
        const currentVol = current.volume
        const priceChange = (current.close - current.open) / current.open
        
        // 计算5日均量
        let avgVol = 0
        for (let j = i - 5; j < i; j++) {
          avgVol += klineDataArr[j].volume
        }
        avgVol /= 5
        
        const volRatio = currentVol / avgVol
        
        // 机构大单买入信号：放量上涨（成交量>2倍均量 且 涨幅>1%）
        if (volRatio > 2 && priceChange > 0.01) {
          let consecutiveLargeVol = 0
          for (let k = i; k >= Math.max(0, i - 2); k--) {
            let kAvgVol = 0
            for (let m = k - 5; m < k && m >= 0; m++) {
              kAvgVol += klineDataArr[m]?.volume || 0
            }
            kAvgVol = kAvgVol / 5 || 1
            if (klineDataArr[k].volume > kAvgVol * 1.5) {
              consecutiveLargeVol++
            }
          }
          
          signals.push({
            index: i,
            date: current.time || current.date,
            type: 'buy',
            direction: 'bullish',
            price: current.high,
            volume: currentVol,
            volRatio: volRatio,
            priceChange: priceChange,
            confidence: consecutiveLargeVol >= 2 ? 0.85 : 0.7,
            name: consecutiveLargeVol >= 2 ? '机构连续买入' : '机构大单买入',
            description: `成交量${volRatio.toFixed(1)}倍均量，涨幅${(priceChange * 100).toFixed(1)}%` + 
                         (consecutiveLargeVol >= 2 ? '，连续放量' : '')
          })
        }
        // 机构大单卖出信号：放量下跌（成交量>2倍均量 且 跌幅>1%）
        else if (volRatio > 2 && priceChange < -0.01) {
          signals.push({
            index: i,
            date: current.time || current.date,
            type: 'sell',
            direction: 'bearish',
            price: current.low,
            volume: currentVol,
            volRatio: volRatio,
            priceChange: priceChange,
            confidence: 0.75,
            name: '机构大单卖出',
            description: `成交量${volRatio.toFixed(1)}倍均量，跌幅${(Math.abs(priceChange) * 100).toFixed(1)}%`
          })
        }
      }
      
      return signals.slice(-20)
    }
    
    // 生成信号标记点数据
    const getSignalMarkPoints = (signals, dates, klineDataArr) => {
      if (!signals || signals.length === 0) return []
      
      const minIndex = Math.max(0, klineDataArr.length - 30)
      const recentSignals = signals.filter(s => s.index >= minIndex && (s.importance === 'high' || s.importance === 'medium'))
      
      return recentSignals.map(signal => {
        const kline = klineDataArr[signal.index]
        if (!kline) return null
        
        const isBullish = signal.direction === 'bullish'
        const price = isBullish ? kline.low * 0.995 : kline.high * 1.005
        
        return {
          name: signal.name,
          coord: [dates[signal.index], price],
          value: signal.name.substring(0, 4),
          symbol: isBullish ? 'triangle' : 'pin',
          symbolSize: signal.importance === 'high' ? 20 : 15,
          symbolRotate: isBullish ? 0 : 180,
          itemStyle: { 
            color: isBullish ? '#26a69a' : '#ef5350',
            borderColor: '#fff',
            borderWidth: 1
          },
          label: {
            show: true,
            position: isBullish ? 'bottom' : 'top',
            formatter: signal.name.substring(0, 4),
            fontSize: 9,
            color: isBullish ? '#26a69a' : '#ef5350'
          },
          // 悬浮提示信息
          emphasis: {
            label: {
              show: true,
              formatter: function() {
                return signal.name + '\n' + (signal.description || '') + '\n置信度: ' + ((signal.confidence || 0) * 100).toFixed(0) + '%'
              },
              fontSize: 11,
              backgroundColor: 'rgba(30, 41, 59, 0.95)',
              padding: [6, 10],
              borderRadius: 4,
              color: '#e2e8f0'
            }
          }
        }
      }).filter(p => p !== null)
    }
    
    // 生成形态标记点数据
    const getPatternMarkPoints = (patterns, dates, klineDataArr) => {
      if (!patterns || patterns.length === 0) return []
      
      const minIndex = Math.max(0, klineDataArr.length - 30)
      const recentPatterns = patterns.filter(p => p.index >= minIndex && (p.importance === 'high' || p.importance === 'medium'))
      
      return recentPatterns.map(pattern => {
        const kline = klineDataArr[pattern.index]
        if (!kline) return null
        
        const isBullish = pattern.type === 'bullish'
        const isBearish = pattern.type === 'bearish'
        const price = isBullish ? kline.low * 0.99 : (isBearish ? kline.high * 1.01 : kline.close)
        
        return {
          name: pattern.name,
          coord: [dates[pattern.index], price],
          value: pattern.name.substring(0, 2),
          symbol: 'diamond',
          symbolSize: pattern.importance === 'high' ? 18 : 14,
          itemStyle: { 
            color: isBullish ? '#4ade80' : (isBearish ? '#f87171' : '#fbbf24'),
            borderColor: '#fff',
            borderWidth: 1
          },
          label: {
            show: true,
            position: isBullish ? 'bottom' : 'top',
            formatter: pattern.name.substring(0, 2),
            fontSize: 9,
            color: isBullish ? '#4ade80' : (isBearish ? '#f87171' : '#fbbf24')
          },
          // 悬浮提示信息
          emphasis: {
            label: {
              show: true,
              formatter: function() {
                return pattern.name + '\n' + (pattern.description || '') + '\n置信度: ' + ((pattern.confidence || 0) * 100).toFixed(0) + '%'
              },
              fontSize: 11,
              backgroundColor: 'rgba(30, 41, 59, 0.95)',
              padding: [6, 10],
              borderRadius: 4,
              color: '#e2e8f0'
            }
          }
        }
      }).filter(p => p !== null)
    }
    
    // 生成机构大单标记点数据
    const getLargeOrderMarkPoints = (orders, dates, klineDataArr) => {
      if (!orders || orders.length === 0) return []
      
      const minIndex = Math.max(0, klineDataArr.length - 30)
      const recentOrders = orders.filter(o => o.index >= minIndex)
      
      return recentOrders.map(order => {
        const kline = klineDataArr[order.index]
        if (!kline) return null
        
        const isBuy = order.type === 'buy'
        const price = isBuy ? kline.low * 0.985 : kline.high * 1.015
        
        return {
          name: order.name,
          coord: [dates[order.index], price],
          value: isBuy ? '🏛️买' : '🏛️卖',
          symbol: 'rect',
          symbolSize: [30, 16],
          itemStyle: { 
            color: isBuy ? 'rgba(38, 166, 154, 0.9)' : 'rgba(239, 83, 80, 0.9)',
            borderColor: isBuy ? '#26a69a' : '#ef5350',
            borderWidth: 1
          },
          label: {
            show: true,
            position: 'inside',
            formatter: isBuy ? '机构买' : '机构卖',
            fontSize: 8,
            color: '#fff'
          },
          // 悬浮提示信息
          emphasis: {
            label: {
              show: true,
              formatter: function() {
                return order.name + '\n' + (order.description || '') + '\n置信度: ' + ((order.confidence || 0) * 100).toFixed(0) + '%'
              },
              fontSize: 11,
              backgroundColor: 'rgba(30, 41, 59, 0.95)',
              padding: [6, 10],
              borderRadius: 4,
              color: '#e2e8f0'
            }
          }
        }
      }).filter(p => p !== null)
    }

    // 添加标记点
    const addMarker = (date, price, label, color) => {
      chartMarkers.value.push({ date, price, label, color: color || '#f59e0b' })
      renderKlineChart()
    }

    // 添加水平线
    const addHorizontalLine = (price, label, color) => {
      chartDrawings.value.push({ type: 'hline', price, label, color: color || '#f59e0b' })
      renderKlineChart()
    }

    // 添加支撑线
    const addSupportLine = () => {
      if (klineData.value.length === 0) return
      const recentData = klineData.value.slice(-60)
      const minLow = Math.min(...recentData.map(d => d.low))
      addHorizontalLine(minLow, '支撑位', '#26a69a')
    }

    // 添加阻力线
    const addResistanceLine = () => {
      if (klineData.value.length === 0) return
      const recentData = klineData.value.slice(-60)
      const maxHigh = Math.max(...recentData.map(d => d.high))
      addHorizontalLine(maxHigh, '压力位', '#ef5350')
    }

    // 自动检测关键价位
    const autoDetectKeyLevels = () => {
      if (klineData.value.length < 20) return

      const recentData = klineData.value.slice(-60)
      const highs = recentData.map(d => d.high)
      const lows = recentData.map(d => d.low)

      const maxHigh = Math.max(...highs)
      const minLow = Math.min(...lows)

      addHorizontalLine(maxHigh, '近期高点', '#ef5350')
      addHorizontalLine(minLow, '近期低点', '#26a69a')

      const midLevel = (maxHigh + minLow) / 2
      addHorizontalLine(midLevel, '中轴线', '#64748b')
    }

    // 清除所有标记
    const clearAllMarkers = () => {
      chartMarkers.value = []
      chartDrawings.value = []
      renderKlineChart()
    }

    // 从表单添加价格标记
    const addPriceMarkerFromForm = () => {
      const price = parseFloat(priceMarkerForm.value.price)
      if (isNaN(price)) return

      const type = priceMarkerForm.value.type
      const label = priceMarkerForm.value.label

      if (type === 'support') {
        addHorizontalLine(price, label || '支撑位', '#26a69a')
      } else if (type === 'resistance') {
        addHorizontalLine(price, label || '压力位', '#ef5350')
      } else if (type === 'buy' && klineData.value.length > 0) {
        addMarker(klineData.value[klineData.value.length - 1].time, price, label || '买入', '#26a69a')
      } else if (type === 'sell' && klineData.value.length > 0) {
        addMarker(klineData.value[klineData.value.length - 1].time, price, label || '卖出', '#ef5350')
      } else if (type === 'high') {
        const maxIdx = klineData.value.reduce((maxI, item, i, arr) => item.high > arr[maxI].high ? i : maxI, 0)
        addMarker(klineData.value[maxIdx].time, klineData.value[maxIdx].high, label || '高点', '#ef5350')
      } else if (type === 'low') {
        const minIdx = klineData.value.reduce((minI, item, i, arr) => item.low < arr[minI].low ? i : minI, 0)
        addMarker(klineData.value[minIdx].time, klineData.value[minIdx].low, label || '低点', '#26a69a')
      } else {
        addHorizontalLine(price, label, '#f59e0b')
      }

      showPriceMarkerModal.value = false
      priceMarkerForm.value = { price: '', label: '', type: 'support' }
    }

    // 截图保存
    const captureChart = () => {
      if (!chartInstance) return
      try {
        const screenshot = chartInstance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#1e293b' })
        const link = document.createElement('a')
        link.download = `${klineStock.value}_${klinePeriod.value}_${new Date().toISOString().slice(0, 10)}.png`
        link.href = screenshot
        link.click()
      } catch (error) {
        console.error('截图失败:', error)
      }
    }

    // 根据订单自动标注买入点和连线到最近交易日
    const markOrderPoints = (stockCode, orderInfo) => {
      if (!orderInfo || klineData.value.length === 0) return

      // 清除之前的标记
      chartMarkers.value = []
      chartDrawings.value = []

      // 查找该股票的所有买入交易记录
      const stockTrades = trades.value.filter(t => t.stock_code === stockCode && t.action === 'BUY')

      stockTrades.forEach(trade => {
        // 找到交易日期对应的K线数据索引
        const tradeDate = trade.timestamp.split('T')[0]
        const klineIndex = klineData.value.findIndex(k => {
          const kDate = (k.time || k.date).split(' ')[0]
          return kDate === tradeDate || kDate.replace(/-/g, '') === tradeDate.replace(/-/g, '')
        })

        if (klineIndex >= 0) {
          // 添加买入点标记
          const klineItem = klineData.value[klineIndex]
          chartMarkers.value.push({
            date: klineItem.time || klineItem.date,
            price: trade.price,
            label: `买入 ¥${trade.price.toFixed(2)}`,
            color: '#26a69a'
          })

          // 添加从买入点到最近交易日的连线
          const lastKline = klineData.value[klineData.value.length - 1]
          const lastDate = lastKline.time || lastKline.date
          const lastPrice = lastKline.close

          // 计算盈亏
          const profitRate = ((lastPrice - trade.price) / trade.price * 100).toFixed(2)
          const profitColor = lastPrice >= trade.price ? '#26a69a' : '#ef5350'

          // 添加最近价格标记
          chartMarkers.value.push({
            date: lastDate,
            price: lastPrice,
            label: `现价 ¥${lastPrice.toFixed(2)} (${profitRate}%)`,
            color: profitColor
          })

          // 添加水平参考线（买入价格线）
          chartDrawings.value.push({
            type: 'hline',
            price: trade.price,
            label: `成本 ¥${trade.price.toFixed(2)}`,
            color: '#f59e0b'
          })
        }
      })

      // 重新渲染图表
      renderKlineChart()
    }

    // 加载指定股票的K线（供点击持仓/交易记录使用）- 增强版带订单标注
    const loadStockKline = async (stockCode, orderInfo = null) => {
      if (!stockCode) return

      klineStock.value = stockCode
      currentOrderInfo.value = orderInfo

      // 先加载K线数据
      await loadKlineData()

      // 如果有订单信息，自动标注
      if (orderInfo || portfolio.value) {
        // 查找该股票的持仓信息
        const position = portfolio.value?.positions?.find(p => p.stock_code === stockCode)
        if (position) {
          currentOrderInfo.value = {
            stock_code: position.stock_code,
            stock_name: position.stock_name,
            action: 'BUY',
            price: position.avg_cost
          }
          markOrderPoints(stockCode, currentOrderInfo.value)
        }
      }
    }

    // ==================== 实时刷新相关方法 ====================
    
    // 更新交易状态
    const updateTradingStatus = () => {
      tradingStatus.value = getTradingStatus()
    }
    
    // 静默刷新K线数据（不显示loading状态）
    const silentRefreshKlineData = async () => {
      if (!klineStock.value || klineData.value.length === 0) return
      
      isAutoRefreshing.value = true
      
      try {
        const url = `${KLINE_API}/data`
        const params = {
          symbol: klineStock.value,
          period: klinePeriod.value,
          adjust: 'qfq',
          limit: 200
        }

        const response = await axios.get(url, { params })

        if (response.data.success) {
          klineData.value = response.data.data.map(item => ({
            date: item.time || item.date,
            time: item.time || item.date,
            open: parseFloat(item.open) || 0,
            high: parseFloat(item.high) || 0,
            low: parseFloat(item.low) || 0,
            close: parseFloat(item.close) || 0,
            volume: parseFloat(item.volume) || 0
          }))
          dataSource.value = response.data.source || 'akshare'

          if (klineData.value.length > 0) {
            // 更新指标
            const lastIdx = klineData.value.length - 1
            const ma5Data = calculateMA(klineData.value, 5)
            const ma10Data = calculateMA(klineData.value, 10)
            const ma20Data = calculateMA(klineData.value, 20)
            const rsiData = calculateRSI(klineData.value)
            const macdData = calculateMACD(klineData.value)

            currentIndicators.value = {
              MA5: ma5Data[lastIdx] ? parseFloat(ma5Data[lastIdx]) : null,
              MA10: ma10Data[lastIdx] ? parseFloat(ma10Data[lastIdx]) : null,
              MA20: ma20Data[lastIdx] ? parseFloat(ma20Data[lastIdx]) : null,
              RSI: rsiData[lastIdx] ? parseFloat(rsiData[lastIdx]) : null,
              MACD: macdData.MACD[lastIdx] ? parseFloat(macdData.MACD[lastIdx]) : null
            }
            
            // 重新检测信号
            try {
              const allIndicators = calculateAllIndicators(klineData.value)
              detectedSignals.value = detectAllSignals(klineData.value, allIndicators)
              detectedPatterns.value = detectAllPatterns(klineData.value)
              signalSummary.value = getSignalSummary([...detectedSignals.value, ...detectedPatterns.value.map(p => ({
                ...p,
                direction: p.type === 'bullish' ? 'bullish' : (p.type === 'bearish' ? 'bearish' : 'neutral')
              }))])
              
              // 更新六脉神剑数据
              if (allIndicators.SIX_PULSE) {
                sixPulseData.value = allIndicators.SIX_PULSE
                const lastSignal = allIndicators.SIX_PULSE.signals[lastIdx]
                
                sixPulseIndicators.value = [
                  {
                    name: 'MACD',
                    value: allIndicators.SIX_PULSE.MACD.MACD[lastIdx]?.toFixed(3) || '-',
                    status: allIndicators.SIX_PULSE.MACD.DIF[lastIdx] > allIndicators.SIX_PULSE.MACD.DEA[lastIdx] ? 'bullish' : 'bearish',
                    statusText: allIndicators.SIX_PULSE.MACD.DIF[lastIdx] > allIndicators.SIX_PULSE.MACD.DEA[lastIdx] ? '多头' : '空头',
                    description: 'DIF与DEA的关系判断趋势方向'
                  },
                  {
                    name: 'KDJ',
                    value: `K:${allIndicators.SIX_PULSE.KDJ.K[lastIdx]?.toFixed(1) || '-'}`,
                    status: allIndicators.SIX_PULSE.KDJ.K[lastIdx] > allIndicators.SIX_PULSE.KDJ.D[lastIdx] ? 'bullish' : 'bearish',
                    statusText: allIndicators.SIX_PULSE.KDJ.K[lastIdx] > allIndicators.SIX_PULSE.KDJ.D[lastIdx] ? '多头' : '空头',
                    description: 'K线与D线的交叉判断买卖点'
                  },
                  {
                    name: 'RSI',
                    value: allIndicators.SIX_PULSE.RSI[lastIdx]?.toFixed(1) || '-',
                    status: allIndicators.SIX_PULSE.RSI[lastIdx] > 50 ? 'bullish' : 'bearish',
                    statusText: allIndicators.SIX_PULSE.RSI[lastIdx] > 70 ? '超买' : (allIndicators.SIX_PULSE.RSI[lastIdx] < 30 ? '超卖' : (allIndicators.SIX_PULSE.RSI[lastIdx] > 50 ? '多头' : '空头')),
                    description: 'RSI>50为多头区域，<50为空头区域'
                  },
                  {
                    name: 'LWR',
                    value: allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx]?.toFixed(1) || '-',
                    status: (allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx] || 50) < 50 ? 'bullish' : 'bearish',
                    statusText: (allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx] || 50) < 30 ? '超买' : ((allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx] || 50) > 70 ? '超卖' : ((allIndicators.SIX_PULSE.LWR?.LWR2?.[lastIdx] || 50) < 50 ? '多头' : '空头')),
                    description: 'LWR<50为多头，>50为空头'
                  },
                  {
                    name: 'BBI',
                    value: allIndicators.SIX_PULSE.BBI?.[lastIdx]?.toFixed(2) || '-',
                    status: klineData.value[lastIdx].close > (allIndicators.SIX_PULSE.BBI?.[lastIdx] || 0) ? 'bullish' : 'bearish',
                    statusText: klineData.value[lastIdx].close > (allIndicators.SIX_PULSE.BBI?.[lastIdx] || 0) ? '多头' : '空头',
                    description: '价格在BBI上方为多头，下方为空头'
                  },
                  {
                    name: 'MTM',
                    value: allIndicators.SIX_PULSE.MTM?.MTM?.[lastIdx]?.toFixed(2) || '-',
                    status: (allIndicators.SIX_PULSE.MTM?.MTM?.[lastIdx] || 0) > 0 ? 'bullish' : 'bearish',
                    statusText: (allIndicators.SIX_PULSE.MTM?.MTM?.[lastIdx] || 0) > 0 ? '多头' : '空头',
                    description: 'MTM>0表示上涨动能，<0表示下跌动能'
                  }
                ]
                
                sixPulseSummary.value = {
                  bullish: lastSignal?.bullish || 0,
                  bearish: lastSignal?.bearish || 0,
                  signal: lastSignal?.signal || 'HOLD',
                  signalText: lastSignal?.signal === 'BUY' ? '🟢 买入' : (lastSignal?.signal === 'SELL' ? '🔴 卖出' : '⚪ 观望')
                }
                
                sixPulseChartData.value = allIndicators.SIX_PULSE.signals.map((sig, idx) => {
                  const sp = allIndicators.SIX_PULSE
                  return {
                    macd: sp.MACD.DIF[idx] > sp.MACD.DEA[idx] ? 1 : -1,
                    kdj: sp.KDJ.K[idx] > sp.KDJ.D[idx] ? 1 : -1,
                    rsi: sp.RSI[idx] > 50 ? 1 : -1,
                    lwr: (sp.LWR?.LWR2?.[idx] || 50) < 50 ? 1 : -1,
                    bbi: klineData.value[idx]?.close > (sp.BBI?.[idx] || 0) ? 1 : -1,
                    mtm: (sp.MTM?.MTM?.[idx] || 0) > 0 ? 1 : -1,
                    bullish: sig?.bullish || 0,
                    bearish: sig?.bearish || 0
                  }
                })
              }
              
              largeOrderSignals.value = detectLargeOrders(klineData.value)
            } catch (err) {
              console.error('信号检测失败:', err)
            }

            await nextTick()
            renderKlineChart()
            
            lastRefreshTime.value = new Date()
            console.log('[实时刷新] K线数据已更新:', klineStock.value, new Date().toLocaleTimeString())
          }
        }
      } catch (error) {
        console.error('[实时刷新] K线数据刷新失败:', error)
      } finally {
        isAutoRefreshing.value = false
      }
    }
    
    // 静默刷新持仓数据
    const silentRefreshPortfolio = async () => {
      try {
        const response = await axios.get(`${API_BASE}/portfolio`)
        if (response.data.success) {
          portfolio.value = response.data.portfolio
          console.log('[实时刷新] 持仓数据已更新:', new Date().toLocaleTimeString())
        }
      } catch (error) {
        console.error('[实时刷新] 持仓数据刷新失败:', error)
      }
    }
    
    // 启动K线实时刷新
    const startKlineRefresh = () => {
      if (klineRefreshTimer.value) {
        klineRefreshTimer.value.stop()
      }
      
      klineRefreshTimer.value = createAdaptiveRefreshTimer(
        silentRefreshKlineData,
        'kline',
        {
          immediate: false,
          onStatusChange: (status) => {
            tradingStatus.value = status
            console.log('[实时刷新] 交易状态变化:', status.statusText)
          }
        }
      )
      
      startCountdown()
      console.log('[实时刷新] K线刷新定时器已启动')
    }
    
    // 停止K线实时刷新
    const stopKlineRefresh = () => {
      if (klineRefreshTimer.value) {
        klineRefreshTimer.value.stop()
        klineRefreshTimer.value = null
      }
      stopCountdown()
      console.log('[实时刷新] K线刷新定时器已停止')
    }
    
    // 启动持仓实时刷新
    const startPortfolioRefresh = () => {
      if (portfolioRefreshTimer.value) {
        portfolioRefreshTimer.value.stop()
      }
      
      portfolioRefreshTimer.value = createAdaptiveRefreshTimer(
        silentRefreshPortfolio,
        'portfolio',
        {
          immediate: false,
          onStatusChange: (status) => {
            tradingStatus.value = status
          }
        }
      )
      
      console.log('[实时刷新] 持仓刷新定时器已启动')
    }
    
    // 停止持仓实时刷新
    const stopPortfolioRefresh = () => {
      if (portfolioRefreshTimer.value) {
        portfolioRefreshTimer.value.stop()
        portfolioRefreshTimer.value = null
      }
      console.log('[实时刷新] 持仓刷新定时器已停止')
    }
    
    // 启动倒计时显示
    const startCountdown = () => {
      stopCountdown()
      countdownInterval = setInterval(() => {
        if (klineRefreshTimer.value) {
          refreshCountdown.value = Math.ceil(klineRefreshTimer.value.countdown / 1000)
        }
        updateTradingStatus()
      }, 1000)
    }
    
    // 停止倒计时
    const stopCountdown = () => {
      if (countdownInterval) {
        clearInterval(countdownInterval)
        countdownInterval = null
      }
      refreshCountdown.value = 0
    }
    
    // 切换实时刷新
    const toggleRealtimeRefresh = () => {
      realtimeRefreshEnabled.value = !realtimeRefreshEnabled.value
      
      if (realtimeRefreshEnabled.value) {
        startKlineRefresh()
        startPortfolioRefresh()
      } else {
        stopKlineRefresh()
        stopPortfolioRefresh()
      }
    }
    
    // 手动刷新
    const manualRefresh = async () => {
      await silentRefreshKlineData()
      await silentRefreshPortfolio()
      await loadTrades()
      
      if (klineRefreshTimer.value) {
        klineRefreshTimer.value.refresh()
      }
    }
    
    // 获取刷新状态文本
    const getRefreshStatusText = () => {
      if (!realtimeRefreshEnabled.value) {
        return '实时刷新已关闭'
      }
      if (isAutoRefreshing.value) {
        return '正在刷新...'
      }
      if (tradingStatus.value?.isTrading) {
        return `交易中 · ${refreshCountdown.value}秒后刷新`
      }
      return `${tradingStatus.value?.statusText || '休市'} · ${refreshCountdown.value}秒后刷新`
    }

    // 初始化
    onMounted(async () => {
      loadPortfolio()
      loadTrades()
      loadTradeLogs()
      // 自动加载默认股票的K线图
      await nextTick()
      if (klineStock.value) {
        loadKlineData()
      }
      
      // 初始化交易状态
      updateTradingStatus()
      
      // 启动实时刷新
      if (realtimeRefreshEnabled.value) {
        startKlineRefresh()
        startPortfolioRefresh()
      }
      
      console.log('[模拟交易] 初始化完成，交易状态:', tradingStatus.value?.statusText)
    })
    
    onUnmounted(() => {
      // 停止所有定时器
      stopKlineRefresh()
      stopPortfolioRefresh()
      stopCountdown()
      
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
      
      console.log('[模拟交易] 组件已卸载，定时器已清理')
    })
    
    return {
      portfolio,
      trades,
      tradeLogs,
      logFilter,
      showTradeDialog,
      tradeForm,
      loadPortfolio,
      loadTradeLogs,
      executeTrade,
      quickSell,
      resetAccount,
      formatAmount,
      formatTime,
      formatTimeShort,
      getProfitClass,
      getSourceLabel,
      getLogTypeLabel,
      // K线图
      klineStock,
      klinePeriod,
      klineData,
      klineLoading,
      klineError,
      klineChart,
      periods,
      selectPeriod,
      loadKlineData,
      loadStockKline,
      // 技术指标
      indicators,
      chartHeight,
      renderKlineChart,
      // 新增功能
      dataSource,
      currentIndicators,
      currentOrderInfo,
      getRSIClass,
      getVolumeStatus,
      getVolumeClass,
      // 信号和形态数据
      detectedSignals,
      detectedPatterns,
      signalSummary,
      // 六脉神剑数据
      sixPulseData,
      sixPulseIndicators,
      sixPulseSummary,
      sixPulseChartData,
      // 机构大单数据
      largeOrderSignals,
      // 标记功能
      chartMarkers,
      chartDrawings,
      showPriceMarkerModal,
      priceMarkerForm,
      addMarker,
      addHorizontalLine,
      addSupportLine,
      addResistanceLine,
      autoDetectKeyLevels,
      clearAllMarkers,
      addPriceMarkerFromForm,
      captureChart,
      markOrderPoints,
      // 实时刷新
      realtimeRefreshEnabled,
      tradingStatus,
      refreshCountdown,
      lastRefreshTime,
      isAutoRefreshing,
      toggleRealtimeRefresh,
      manualRefresh,
      getRefreshStatusText
    }
  }
}
</script>

<style scoped>
.trading-container {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
  color: white;
}

.subtitle {
  color: #999;
  margin: 0 0 16px 0;
}

.action-buttons {
  display: flex;
  gap: 12px;
}

.risk-alert {
  display: flex;
  gap: 12px;
  padding: 16px;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 8px;
  margin-bottom: 20px;
}

.alert-icon {
  font-size: 24px;
}

.alert-content {
  flex: 1;
  line-height: 1.6;
  color: #ffc107;
}

.account-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.overview-card {
  background: rgba(255, 255, 255, 0.05);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.card-label {
  color: #999;
  font-size: 14px;
  margin-bottom: 8px;
}

.card-value {
  font-size: 24px;
  font-weight: bold;
  color: white;
}

.positions-section,
.trades-section {
  background: rgba(255, 255, 255, 0.05);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 20px;
}

.positions-section h3,
.trades-section h3 {
  color: white;
  margin: 0 0 16px 0;
}

.table-wrapper {
  width: 100%;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  color: white;
}

.data-table th {
  background: rgba(255, 255, 255, 0.05);
  font-weight: 600;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #999;
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #1a1a2e;
  padding: 24px;
  border-radius: 12px;
  min-width: 400px;
  max-width: 500px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-content h3 {
  color: white;
  margin: 0 0 20px 0;
}

.form-group {
  margin-bottom: 16px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: white;
}

.input-field {
  width: 100%;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  font-size: 14px;
  background: rgba(255, 255, 255, 0.05);
  color: white;
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #999;
  font-size: 12px;
}

.trade-tabs {
  display: flex;
  gap: 8px;
  margin-bottom: 20px;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  color: white;
}

.tab-btn.active {
  background: #1890ff;
  border-color: #1890ff;
}

.trade-info {
  background: rgba(255, 255, 255, 0.05);
  padding: 12px;
  border-radius: 6px;
  margin-bottom: 16px;
  color: white;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}

.btn-primary,
.btn-secondary,
.btn-danger {
  padding: 10px 24px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover {
  background: #40a9ff;
}

.btn-secondary {
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.btn-secondary:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-danger {
  background: #ff4d4f;
  color: white;
}

.btn-danger:hover {
  background: #ff7875;
}

.btn-monitor {
  background: rgba(114, 46, 209, 0.2);
  color: #a855f7;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.btn-monitor:hover {
  background: rgba(114, 46, 209, 0.3);
  border-color: rgba(168, 85, 247, 0.5);
}

.btn-monitor.active {
  background: #7c3aed;
  color: white;
  border-color: #7c3aed;
}

.btn-danger-small {
  padding: 4px 12px;
  background: #ff4d4f;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.text-success {
  color: #52c41a;
}

.text-danger {
  color: #ff4d4f;
}

/* 可点击行样式 */
.clickable-row {
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.clickable-row:hover {
  background: rgba(24, 144, 255, 0.15) !important;
}

.clickable-row:active {
  background: rgba(24, 144, 255, 0.25) !important;
}

/* K线图样式 */
.kline-section {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 30px;
}

.kline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

/* 技术指标开关 */
.indicator-toggles {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  margin-bottom: 16px;
  flex-wrap: wrap;
}

.toggle-label {
  color: #888;
  font-size: 14px;
  margin-right: 8px;
}

.toggle-item {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
  user-select: none;
}

.toggle-item input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
  accent-color: #1890ff;
}

.toggle-text {
  font-size: 13px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 4px;
  transition: all 0.3s;
}

.toggle-text.ma5 {
  color: #f5d742;
  background: rgba(245, 215, 66, 0.1);
}

.toggle-text.ma20 {
  color: #42a5f5;
  background: rgba(66, 165, 245, 0.1);
}

.toggle-text.ma60 {
  color: #ab47bc;
  background: rgba(171, 71, 188, 0.1);
}

.toggle-text.boll {
  color: #ff9800;
  background: rgba(255, 152, 0, 0.1);
}

.toggle-item:hover .toggle-text {
  filter: brightness(1.2);
}

.kline-header h3 {
  margin: 0;
  color: white;
  font-size: 20px;
}

.kline-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.period-buttons {
  display: flex;
  gap: 8px;
}

.period-btn {
  padding: 6px 16px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.period-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  border-color: rgba(255, 255, 255, 0.3);
}

.period-btn.active {
  background: #1890ff;
  border-color: #1890ff;
  color: white;
}

.kline-input {
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: white;
  font-size: 14px;
  width: 150px;
}

.kline-input:focus {
  outline: none;
  border-color: #1890ff;
}

.kline-select {
  padding: 8px 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: white;
  font-size: 14px;
  cursor: pointer;
}

.kline-select:focus {
  outline: none;
  border-color: #1890ff;
}

.btn-secondary-small {
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  color: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-secondary-small:hover {
  background: rgba(255, 255, 255, 0.15);
  border-color: rgba(255, 255, 255, 0.3);
}

.kline-chart {
  width: 100%;
}

.kline-chart-wrapper {
  position: relative;
}

.kline-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  border-radius: 12px;
}

.kline-loading,
.kline-error,
.kline-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
  color: #999;
}

.kline-loading .spinner {
  width: 40px;
  height: 40px;
  border: 3px solid rgba(255, 255, 255, 0.1);
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 10px;
}

.kline-error {
  color: #ff4d4f;
}

/* 加载按钮 */
.load-btn {
  padding: 8px 16px;
  background: #3b82f6;
  border: none;
  border-radius: 6px;
  color: white;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.load-btn:hover {
  background: #2563eb;
}

/* 分隔符 */
.toggle-divider {
  color: #334155;
  margin: 0 4px;
}

/* MACD/RSI/KDJ 指标样式 */
.toggle-text.macd {
  color: #42a5f5;
  background: rgba(66, 165, 245, 0.1);
}

.toggle-text.rsi {
  color: #ab47bc;
  background: rgba(171, 71, 188, 0.1);
}

.toggle-text.kdj {
  color: #e91e63;
  background: rgba(233, 30, 99, 0.1);
}

/* K线图工具栏 */
.chart-toolbar {
  display: flex;
  gap: 12px;
  margin-top: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.toolbar-group {
  display: flex;
  align-items: center;
  gap: 8px;
}

.toolbar-label {
  font-size: 12px;
  color: #64748b;
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  background: rgba(51, 65, 85, 0.3);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 6px;
  color: #94a3b8;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
  color: #60a5fa;
}

.toolbar-btn.highlight {
  background: rgba(139, 92, 246, 0.2);
  border-color: rgba(139, 92, 246, 0.5);
  color: #a78bfa;
}

.toolbar-btn.highlight:hover {
  background: rgba(139, 92, 246, 0.3);
}

.toolbar-btn.support {
  background: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.4);
  color: #34d399;
}

.toolbar-btn.support:hover {
  background: rgba(16, 185, 129, 0.25);
}

.toolbar-btn.resistance {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.4);
  color: #f87171;
}

.toolbar-btn.resistance:hover {
  background: rgba(239, 68, 68, 0.25);
}

.toolbar-btn.danger {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #f87171;
}

.toolbar-btn.danger:hover {
  background: rgba(239, 68, 68, 0.2);
}

/* 指标显示区域 */
.indicator-display {
  margin-top: 12px;
  padding: 12px;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 8px;
}

.indicator-row {
  display: flex;
  gap: 16px;
  margin-bottom: 6px;
  flex-wrap: wrap;
}

.indicator-row:last-child {
  margin-bottom: 0;
}

.ind-label {
  font-size: 12px;
  color: #64748b;
}

.ind-value {
  font-size: 14px;
  font-weight: 500;
  color: white;
  margin-right: 12px;
}

.ind-value.ma5 { color: #f5d742; }
.ind-value.ma10 { color: #3b82f6; }
.ind-value.ma20 { color: #42a5f5; }
.ind-value.positive { color: #10b981; }
.ind-value.negative { color: #ef4444; }
.ind-value.overbought { color: #ef4444; }
.ind-value.oversold { color: #10b981; }
.ind-value.neutral { color: #f59e0b; }
.ind-value.data-source { color: #8b5cf6; }
.ind-value.order-stock { color: #60a5fa; margin-left: 8px; }
.ind-value.order-action { color: #10b981; }

.order-info {
  margin-left: 16px;
}

/* 空状态图标 */
.empty-icon {
  font-size: 48px;
  opacity: 0.5;
  margin-bottom: 8px;
}

/* 价格标记模态框 */
.marker-modal {
  max-width: 500px;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.modal-header h3 {
  margin: 0;
}

.close-btn {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(51, 65, 85, 0.5);
  border: none;
  border-radius: 6px;
  color: #94a3b8;
  font-size: 16px;
  cursor: pointer;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.modal-body {
  padding: 0;
}

.modal-desc {
  color: #94a3b8;
  margin: 0 0 16px 0;
  font-size: 14px;
}

/* 标记类型网格 */
.marker-type-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8px;
  margin-top: 8px;
}

.marker-type-btn {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 12px 8px;
  background: rgba(51, 65, 85, 0.3);
  border: 2px solid transparent;
  border-radius: 8px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.marker-type-btn:hover {
  background: rgba(51, 65, 85, 0.5);
  color: white;
}

.marker-type-btn.active {
  border-color: #3b82f6;
  background: rgba(59, 130, 246, 0.15);
  color: white;
}

.type-icon {
  font-size: 24px;
}

.type-label {
  font-size: 12px;
  font-weight: 500;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 来源标签样式 */
.source-badge {
  display: inline-block;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.source-badge.manual {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

.source-badge.auto {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.source-badge.strategy {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

/* 交易记录和日志并排布局 */
.trades-logs-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

.trades-logs-row .trades-section,
.trades-logs-row .trade-logs-section {
  background: rgba(255, 255, 255, 0.05);
  padding: 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 0;
  max-height: 350px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.trades-logs-row .trades-section h3,
.trades-logs-row .trade-logs-section h3 {
  color: white;
  margin: 0 0 12px 0;
  font-size: 15px;
}

.trades-logs-row .table-wrapper {
  flex: 1;
  overflow-y: auto;
}

/* 紧凑表格样式 */
.data-table.compact th,
.data-table.compact td {
  padding: 8px 6px;
  font-size: 12px;
}

.data-table.compact th {
  font-size: 11px;
  white-space: nowrap;
}

/* 刷新按钮 */
.btn-refresh-small {
  padding: 4px 8px;
  background: rgba(51, 65, 85, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.8);
  border-radius: 4px;
  color: #94a3b8;
  cursor: pointer;
  font-size: 12px;
}

.btn-refresh-small:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
  color: #60a5fa;
}

/* 策略交易日志区域 */
.trade-logs-section {
  background: rgba(255, 255, 255, 0.05);
  padding: 20px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  margin-bottom: 20px;
}

.logs-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.logs-header h3 {
  color: white;
  margin: 0;
}

.logs-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.log-filter-select {
  padding: 6px 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.05);
  color: white;
  font-size: 13px;
  cursor: pointer;
}

.log-filter-select:focus {
  outline: none;
  border-color: #1890ff;
}

.logs-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
  flex: 1;
  overflow-y: auto;
}

.log-item {
  padding: 8px 10px;
  background: rgba(15, 23, 42, 0.4);
  border-radius: 6px;
  border-left: 3px solid #64748b;
}

.log-item.signal {
  border-left-color: #3b82f6;
}

.log-item.order {
  border-left-color: #f59e0b;
}

.log-item.execution {
  border-left-color: #10b981;
}

.log-item.risk {
  border-left-color: #ef4444;
}

.log-item.system {
  border-left-color: #8b5cf6;
}

.log-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.log-type-badge {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 500;
}

.log-type-badge.signal {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.log-type-badge.order {
  background: rgba(245, 158, 11, 0.2);
  color: #fbbf24;
}

.log-type-badge.execution {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
}

.log-type-badge.risk {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.log-type-badge.system {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.log-source-badge {
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
  font-weight: 500;
}

.log-source-badge.manual {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

.log-source-badge.auto {
  background: rgba(139, 92, 246, 0.2);
  color: #a78bfa;
}

.log-time {
  font-size: 11px;
  color: #64748b;
  margin-left: auto;
}

.log-content {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-bottom: 4px;
}

.log-stock {
  font-weight: 600;
  color: #60a5fa;
  font-size: 13px;
}

.log-strategy {
  font-size: 12px;
  color: #a78bfa;
  padding: 1px 6px;
  background: rgba(139, 92, 246, 0.1);
  border-radius: 4px;
}

.log-message {
  font-size: 13px;
  color: #e2e8f0;
}

.log-details {
  display: flex;
  gap: 12px;
  align-items: center;
  margin-top: 6px;
  padding-top: 6px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.log-direction {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.log-direction.buy {
  background: rgba(16, 185, 129, 0.2);
  color: #34d399;
}

.log-direction.sell {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.log-quantity {
  font-size: 12px;
  color: #94a3b8;
}

.log-price {
  font-size: 12px;
  color: white;
  font-weight: 500;
}

.log-confidence {
  font-size: 11px;
  color: #64748b;
}

/* 滚动条样式 */
.logs-list::-webkit-scrollbar {
  width: 6px;
}

.logs-list::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
  border-radius: 3px;
}

.logs-list::-webkit-scrollbar-thumb {
  background: rgba(51, 65, 85, 0.8);
  border-radius: 3px;
}

/* ========== 移动端适配 ========== */
@media (max-width: 768px) {
  .trading-container {
    padding: 12px;
  }

  .page-header h1 {
    font-size: 1.4rem;
  }

  .subtitle {
    font-size: 13px;
  }

  .action-buttons {
    flex-wrap: wrap;
    gap: 8px;
  }

  .action-buttons button {
    flex: 1;
    min-width: 80px;
    padding: 8px 10px;
    font-size: 12px;
  }

  /* 风险提示 */
  .risk-alert {
    padding: 12px;
    font-size: 13px;
  }

  .alert-icon {
    font-size: 20px;
  }

  /* 账户总览 */
  .account-overview {
    grid-template-columns: repeat(2, 1fr);
    gap: 10px;
  }

  .overview-card {
    padding: 12px;
  }

  .card-label {
    font-size: 12px;
  }

  .card-value {
    font-size: 18px;
  }

  /* K线图区域 */
  .kline-section {
    padding: 12px;
    margin-bottom: 16x;
  }

  .kline-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .kline-header h3 {
    font-size: 16px;
  }

  .kline-controls {
    width: 100%;
    flex-direction: column;
    gap: 8px;
  }

  .kline-input {
    width: 100%;
  }

  .period-buttons {
    width: 100%;
    flex-wrap: wrap;
    gap: 6px;
  }

  .period-btn {
    flex: 1;
    min-width: 40px;
    padding: 6px 8px;
    font-size: 12px;
    text-align: center;
  }

  .kline-chart {
    height: 400px;
    min-height: 350px;
  }

  /* 持仓和交易记录区域 */
  .positions-section,
  .trades-section {
    padding: 12px;
    margin-bottom: 16px;
    overflow: hidden;
  }

  .positions-section h3,
  .trades-section h3 {
    font-size: 16px;
    margin-bottom: 12px;
  }

  /* 表格横向滚动 */
  .table-wrapper {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    width: 100%;
    margin: 0 -12px;
    padding: 0 12px;
  }

  .data-table {
    min-width: 700px;
  }

  .data-table th,
  .data-table td {
    padding: 8px 6px;
    font-size: 12px;
    white-space: nowrap;
  }

  .btn-danger-small {
    padding: 4px 8px;
    font-size: 11px;
  }

  /* 弹窗 */
  .modal-content {
    min-width: auto;
    max-width: calc(100vw - 32px);
    width: calc(100vw - 32px);
    padding: 16px;
  }

  .modal-content h3 {
    font-size: 18px;
  }

  .form-group label {
    font-size: 14px;
  }

  .input-field {
    padding: 8px;
    font-size: 14px;
  }

  .trade-tabs {
    gap: 6px;
  }

  .tab-btn {
    padding: 8px;
    font-size: 13px;
  }

  .modal-actions {
    flex-direction: column;
    gap: 8px;
  }

  .modal-actions button {
    width: 100%;
  }

  .btn-primary,
  .btn-secondary,
  .btn-danger {
    padding: 10px 16px;
    font-size: 14px;
  }

  /* 交易记录和日志并排布局移动端适配 */
  .trades-logs-row {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .trades-logs-row .trades-section,
  .trades-logs-row .trade-logs-section {
    max-height: 280px;
  }

  .trades-logs-row .data-table.compact {
    min-width: auto;
  }

  /* 交易日志区域移动端适配 */
  .trade-logs-section {
    padding: 12px;
  }

  .logs-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }

  .logs-controls {
    width: 100%;
    flex-wrap: wrap;
  }

  .log-filter-select {
    flex: 1;
    min-width: 100px;
  }

  .logs-list {
    max-height: 300px;
  }

  .log-item {
    padding: 10px;
  }

  .log-header {
    flex-wrap: wrap;
  }

  .log-time {
    width: 100%;
    margin-left: 0;
    margin-top: 4px;
  }

  .log-details {
    flex-wrap: wrap;
    gap: 8px;
  }
}

@media (max-width: 480px) {
  .trading-container {
    padding: 8px;
  }

  .page-header h1 {
    font-size: 1.2rem;
  }

  .action-buttons {
    flex-direction: column;
    gap: 6px;
  }

  .action-buttons button {
    width: 100%;
    padding: 10px;
  }

  /* 账户总览 */
  .account-overview {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .overview-card {
    padding: 10px;
  }

  .card-label {
    font-size: 11px;
  }

  .card-value {
    font-size: 16px;
  }

  /* K线图 */
  .kline-section {
    padding: 10px;
  }

  .kline-header h3 {
    font-size: 14px;
  }

  .period-btn {
    padding: 5px 6px;
    font-size: 11px;
  }

  .kline-chart {
    height: 350px;
    min-height: 300px;
  }

  /* 表格 */
  .data-table th,
  .data-table td {
    padding: 6px 4px;
    font-size: 11px;
  }

  .positions-section,
  .trades-section {
    padding: 10px;
  }

  .positions-section h3,
  .trades-section h3 {
    font-size: 14px;
  }
}

/* ==================== 六脉神剑综合指标面板样式 ==================== */
.six-pulse-panel {
  background: linear-gradient(135deg, rgba(30, 41, 59, 0.95), rgba(15, 23, 42, 0.95));
  border: 1px solid rgba(245, 158, 11, 0.3);
  border-radius: 12px;
  padding: 16px;
  margin-top: 16px;
  box-shadow: 0 4px 20px rgba(245, 158, 11, 0.1);
}

.panel-header-mini {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid rgba(245, 158, 11, 0.2);
}

.panel-title-mini {
  font-size: 1.1rem;
  font-weight: 700;
  background: linear-gradient(135deg, #f59e0b, #fbbf24);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  margin: 0;
}

.panel-subtitle {
  font-size: 0.75rem;
  color: #94a3b8;
}

.pulse-indicators {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 10px;
}

.pulse-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 12px 8px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 8px;
  cursor: help;
  transition: all 0.3s ease;
}

.pulse-item:hover {
  background: rgba(15, 23, 42, 0.9);
  border-color: rgba(245, 158, 11, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.pulse-name {
  font-size: 0.8rem;
  font-weight: 700;
  color: #e2e8f0;
  letter-spacing: 0.5px;
}

.pulse-value {
  font-size: 0.85rem;
  color: #94a3b8;
  font-family: 'Monaco', 'Consolas', monospace;
}

.pulse-status {
  font-size: 0.75rem;
  padding: 4px 10px;
  border-radius: 6px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.pulse-status.bullish {
  background: linear-gradient(135deg, rgba(38, 166, 154, 0.25), rgba(16, 185, 129, 0.25));
  color: #26a69a;
  border: 1px solid rgba(38, 166, 154, 0.4);
}

.pulse-status.bearish {
  background: linear-gradient(135deg, rgba(239, 83, 80, 0.25), rgba(244, 67, 54, 0.25));
  color: #ef5350;
  border: 1px solid rgba(239, 83, 80, 0.4);
}

.pulse-summary {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 24px;
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid rgba(245, 158, 11, 0.2);
}

.bullish-count, .bearish-count {
  font-size: 0.9rem;
  font-weight: 600;
}

.bullish-count {
  color: #26a69a;
}

.bearish-count {
  color: #ef5350;
}

.signal-badge {
  font-size: 0.9rem;
  font-weight: 700;
  padding: 6px 16px;
  border-radius: 8px;
  letter-spacing: 0.5px;
}

.signal-badge.buy {
  background: linear-gradient(135deg, rgba(38, 166, 154, 0.35), rgba(16, 185, 129, 0.35));
  color: #26a69a;
  border: 1px solid rgba(38, 166, 154, 0.6);
  box-shadow: 0 2px 8px rgba(38, 166, 154, 0.3);
}

.signal-badge.sell {
  background: linear-gradient(135deg, rgba(239, 83, 80, 0.35), rgba(244, 67, 54, 0.35));
  color: #ef5350;
  border: 1px solid rgba(239, 83, 80, 0.6);
  box-shadow: 0 2px 8px rgba(239, 83, 80, 0.3);
}

.signal-badge.hold {
  background: rgba(100, 116, 139, 0.35);
  color: #94a3b8;
  border: 1px solid rgba(100, 116, 139, 0.6);
}

.pulse-hint {
  margin-top: 12px;
  text-align: center;
}

.hint-text {
  font-size: 0.75rem;
  color: #64748b;
  font-style: italic;
}

/* 六脉神剑开关样式增强 */
.toggle-text.sixpulse {
  color: #f59e0b;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(239, 68, 68, 0.15));
  border: 1px solid rgba(245, 158, 11, 0.4);
  font-weight: 600;
}

/* 六脉神剑面板响应式 */
@media (max-width: 1200px) {
  .pulse-indicators {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 768px) {
  .six-pulse-panel {
    padding: 12px;
    margin-top: 12px;
  }
  
  .pulse-indicators {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }
  
  .pulse-item {
    padding: 10px 6px;
  }
  
  .pulse-name {
    font-size: 0.75rem;
  }
  
  .pulse-value {
    font-size: 0.8rem;
  }
  
  .pulse-status {
    font-size: 0.7rem;
    padding: 3px 8px;
  }
  
  .pulse-summary {
    gap: 16px;
    flex-wrap: wrap;
  }
  
  .signal-badge {
    font-size: 0.85rem;
    padding: 5px 12px;
  }
}

@media (max-width: 480px) {
  .pulse-indicators {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .panel-header-mini {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
}

/* 实时刷新状态指示器 */
.realtime-status {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 8px;
  font-size: 0.8rem;
  color: #94a3b8;
  transition: all 0.3s;
}

.realtime-status.trading {
  border-color: rgba(16, 185, 129, 0.5);
  background: rgba(16, 185, 129, 0.1);
}

.realtime-status.refreshing {
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(59, 130, 246, 0.1);
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
  transition: all 0.3s;
}

.status-dot.active {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.6);
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.7; transform: scale(1.1); }
}

.status-text {
  flex: 1;
  white-space: nowrap;
}

.refresh-toggle-btn,
.manual-refresh-btn {
  padding: 4px 8px;
  background: rgba(51, 65, 85, 0.3);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 4px;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-toggle-btn:hover,
.manual-refresh-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
}

.manual-refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
