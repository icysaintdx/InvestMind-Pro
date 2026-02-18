/**
 * 策略中心视图逻辑
 * 包含K线图渲染、策略管理、信号生成等功能
 */

import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import API_BASE_URL from '@/config/api.js'
import { 
  isTradingTime, 
  getTradingStatus, 
  getRefreshInterval,
  createAdaptiveRefreshTimer,
  REFRESH_INTERVALS 
} from '@/utils/tradingTime.js'
import { 
  getStrategies, 
  getStrategyDetail, 
  createStrategy, 
  updateStrategy, 
  deleteStrategy as deleteStrategyApi,
  parseStrategyText, 
  generateSignal as generateSignalApi,
  INDICATOR_TYPES,
  TRADING_ACTIONS
} from '@/api/strategyCenter'
import { calculateIndicators } from '@/api/stock'
import { 
  calculateAllIndicators, 
  detectAllSignals, 
  detectAllPatterns,
  getRecentSignals,
  getRecentPatterns,
  getSignalSummary
} from '@/utils/technicalIndicators'

export function useStrategyCenter() {
  // 状态
  const strategies = ref([])
  const categories = ref([])
  const selectedCategory = ref(null)
  const selectedStrategy = ref(null)
  const isLoading = ref(false)
  const isGenerating = ref(false)
  const isParsing = ref(false)
  const availableModels = ref([])
  const modelLoadError = ref('')

  // K线图相关
  const chartContainer = ref(null)
  let chartInstance = null
  const chartStockCode = ref('600519')
  const chartPeriod = ref('daily')
  const chartData = ref([])
  const isLoadingChart = ref(false)
  const chartError = ref('')
  const currentIndicators = ref({})
  const dataSource = ref('')
  
  // K线图高级功能
  const isDrawingMode = ref(false)
  const drawingTool = ref(null)
  const chartMarkers = ref([])
  const chartDrawings = ref([])
  
// 技术指标开关
  const indicatorToggles = reactive({
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
  const chartHeight = computed(function() {
    return 520
  })
  
  // 信号和形态数据
  const detectedSignals = ref([])
  const detectedPatterns = ref([])
  const signalSummary = ref(null)
  
  // 六脉神剑综合指标数据
  const sixPulseData = ref(null)
  const sixPulseIndicators = ref([])
  const sixPulseSummary = ref({ bullish: 0, bearish: 0, signal: 'HOLD', signalText: '观望' })
  // 六脉神剑副图数据（每根K线的6个指标状态）
  const sixPulseChartData = ref([])
  
  // 机构大单数据
  const largeOrderSignals = ref([])
  
  // ==================== 实时刷新相关状态 ====================
  const realtimeRefreshEnabled = ref(true)  // 是否启用实时刷新
  const tradingStatus = ref(null)           // 当前交易状态
  const klineRefreshTimer = ref(null)       // K线刷新定时器
  const planRefreshTimer = ref(null)        // 计划刷新定时器
  const refreshCountdown = ref(0)           // 刷新倒计时（秒）
  const lastRefreshTime = ref(null)         // 上次刷新时间
  const isAutoRefreshing = ref(false)       // 是否正在自动刷新
  let countdownInterval = null              // 倒计时定时器
  
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

  // 模态框
  const showParseModal = ref(false)
  const showCreateModal = ref(false)
  const editingStrategy = ref(null)
  const showPriceMarkerModal = ref(false)

  // 表单
  const parseText = ref('')
  const strategyForm = ref({
    name: '',
    description: '',
    category: 'custom',
    indicators: [],
    entry_conditions: [],
    exit_conditions: [],
    risk_params: { stop_loss: 0.05, take_profit: 0.15, max_position: 0.3 }
  })
  const signalForm = ref({
    stockCode: '',
    model: '',
    includeChart: true,
    includeNews: true
  })
  const signalResult = ref(null)
  const priceMarkerForm = ref({
    price: '',
    label: '',
    type: 'support',
    color: '#f59e0b'
  })

  // ==================== 交易计划相关状态 ====================
  const tradingPlans = ref([])
  const showCreatePlanModal = ref(false)
  const showPlanDetailModal = ref(false)
  const selectedPlanDetail = ref(null)
  const isCreatingPlan = ref(false)
  const planForm = ref({
    strategy: null,
    stockCode: '',
    stockName: '',
    allocatedCapital: 100000,
    maxPositionRatio: 30,
    stopLossPct: 5,
    takeProfitPct: 15,
    checkInterval: 30,
    decisionMode: 'rule_only',
    autoStart: true
  })

  // 计算属性：运行中的计划
  const runningPlans = computed(function() {
    return tradingPlans.value.filter(function(p) {
      return p.status === 'running' || p.status === 'paused'
    })
  })

  // 计算属性：已停止的计划
  const stoppedPlans = computed(function() {
    return tradingPlans.value.filter(function(p) {
      return p.status === 'stopped' || p.status === 'pending'
    })
  })

  // 计算属性：运行中计划数量
  const runningPlansCount = computed(function() {
    return tradingPlans.value.filter(function(p) {
      return p.status === 'running'
    }).length
  })

  // 计算属性
  const filteredStrategies = computed(function() {
    if (!selectedCategory.value) return strategies.value
    return strategies.value.filter(function(s) { return s.category === selectedCategory.value })
  })

  // 加载策略列表
  const loadStrategies = async function() {
    isLoading.value = true
    try {
      const result = await getStrategies()
      if (result.success) {
        strategies.value = result.strategies || []
        categories.value = result.categories || []
      }
    } catch (error) {
      console.error('加载策略失败:', error)
      strategies.value = []
      categories.value = []
    } finally {
      isLoading.value = false
    }
  }

  // 加载可用模型 - 只从模型管理API加载，不使用默认模型
  const loadAvailableModels = async function() {
    modelLoadError.value = ''
    try {
      const response = await axios.get(API_BASE_URL + '/api/config/agents')
      console.log('📦 模型配置API响应:', response.data)
      
      if (response.data && response.data.success && response.data.data) {
        const configData = response.data.data
        const models = []
        
        // selectedModels 是字符串数组（模型名称列表）
        if (configData.selectedModels && Array.isArray(configData.selectedModels)) {
          configData.selectedModels.forEach(function(modelName) {
            if (modelName && typeof modelName === 'string' && modelName.trim()) {
              var provider = 'siliconflow'
              var displayName = modelName
              
              if (modelName.indexOf('/') !== -1) {
                provider = 'siliconflow'
                displayName = modelName.split('/').pop() || modelName
              } else if (modelName.indexOf('gemini') === 0) {
                provider = 'gemini'
              } else if (modelName.indexOf('deepseek') === 0) {
                provider = 'deepseek'
              } else if (modelName.indexOf('qwen') === 0) {
                provider = 'qwen'
              }
              
              models.push({ 
                id: modelName, 
                name: displayName,
                fullName: modelName,
                provider: provider
              })
            }
          })
        }
        
        // 也检查 summarizerModel
        if (configData.summarizerModel && typeof configData.summarizerModel === 'string') {
          var summarizerName = configData.summarizerModel
          var exists = models.some(function(m) { return m.id === summarizerName })
          if (!exists && summarizerName.trim()) {
            var sProvider = 'siliconflow'
            var sDisplayName = summarizerName
            
            if (summarizerName.indexOf('/') !== -1) {
              sProvider = 'siliconflow'
              sDisplayName = summarizerName.split('/').pop() || summarizerName
            } else if (summarizerName.indexOf('gemini') === 0) {
              sProvider = 'gemini'
            } else if (summarizerName.indexOf('deepseek') === 0) {
              sProvider = 'deepseek'
            } else if (summarizerName.indexOf('qwen') === 0) {
              sProvider = 'qwen'
            }
            
            models.push({
              id: summarizerName,
              name: sDisplayName,
              fullName: summarizerName,
              provider: sProvider
            })
          }
        }
        
        console.log('📊 解析到的模型列表:', models)

        if (models.length === 0) {
          modelLoadError.value = '请先在模型管理中配置可用模型'
        }

        availableModels.value = models

        if (models.length > 0) {
          // 尝试从localStorage加载上次选择的模型
          var savedModel = localStorage.getItem('strategy_center_selected_model')
          if (savedModel && models.some(function(m) { return m.id === savedModel })) {
            signalForm.value.model = savedModel
          } else {
            signalForm.value.model = models[0].id
          }
        } else {
          signalForm.value.model = ''
        }
      } else {
        modelLoadError.value = '模型配置加载失败，请检查后端服务'
        availableModels.value = []
        signalForm.value.model = ''
      }
    } catch (error) {
      console.error('加载模型列表失败:', error)
      modelLoadError.value = '加载模型列表失败，请检查网络连接'
      availableModels.value = []
      signalForm.value.model = ''
    }
  }

  // 选择策略
  const selectStrategy = async function(strategy) {
    try {
      const result = await getStrategyDetail(strategy.id)
      if (result.success) {
        selectedStrategy.value = result.strategy
        signalResult.value = null
      }
    } catch (error) {
      console.error('获取策略详情失败:', error)
      selectedStrategy.value = strategy
    }
  }
  
  // 选择周期
  const selectPeriod = function(period) {
    chartPeriod.value = period
    loadChartData()
  }

  // 加载K线数据
  const loadChartData = async function() {
    if (!chartStockCode.value) {
      chartError.value = '请输入股票代码'
      return
    }
    
    isLoadingChart.value = true
    chartError.value = ''
    
    try {
      const response = await axios.get(API_BASE_URL + '/api/kline/data', {
        params: {
          symbol: chartStockCode.value,
          period: chartPeriod.value,
          adjust: 'qfq',
          source: 'auto',
          limit: 200
        }
      })
      
      if (response.data.success) {
        const klineData = response.data.data || []
        dataSource.value = response.data.source
        
        if (klineData.length === 0) {
          chartError.value = '没有获取到K线数据'
          chartData.value = []
        } else {
          chartData.value = klineData.map(function(item) {
            return {
              date: item.time || item.date,
              open: parseFloat(item.open) || 0,
              high: parseFloat(item.high) || 0,
              low: parseFloat(item.low) || 0,
              close: parseFloat(item.close) || 0,
              volume: parseFloat(item.volume) || 0
            }
          })
          
          signalForm.value.stockCode = chartStockCode.value
          
const indicators = calculateIndicators(chartData.value, ['MA', 'MACD', 'RSI', 'BOLL', 'KDJ'])
          const lastIdx = chartData.value.length - 1
          currentIndicators.value = {
            MA5: indicators.MA5 ? indicators.MA5[lastIdx] : null,
            MA10: indicators.MA10 ? indicators.MA10[lastIdx] : null,
            MA20: indicators.MA20 ? indicators.MA20[lastIdx] : null,
            MA60: indicators.MA60 ? indicators.MA60[lastIdx] : null,
            RSI: indicators.RSI ? indicators.RSI[lastIdx] : null,
            MACD: indicators.MACD && indicators.MACD.MACD ? indicators.MACD.MACD[lastIdx] : null
          }
          
          // 检测交易信号和K线形态
          try {
            const allIndicators = calculateAllIndicators(chartData.value)
            detectedSignals.value = detectAllSignals(chartData.value, allIndicators)
            detectedPatterns.value = detectAllPatterns(chartData.value)
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
                  value: allIndicators.SIX_PULSE.LWR.LWR2[lastIdx]?.toFixed(1) || '-',
                  status: allIndicators.SIX_PULSE.LWR.LWR2[lastIdx] < 50 ? 'bullish' : 'bearish',
                  statusText: allIndicators.SIX_PULSE.LWR.LWR2[lastIdx] < 30 ? '超买' : (allIndicators.SIX_PULSE.LWR.LWR2[lastIdx] > 70 ? '超卖' : (allIndicators.SIX_PULSE.LWR.LWR2[lastIdx] < 50 ? '多头' : '空头')),
                  description: 'LWR<50为多头，>50为空头'
                },
                {
                  name: 'BBI',
                  value: allIndicators.SIX_PULSE.BBI[lastIdx]?.toFixed(2) || '-',
                  status: chartData.value[lastIdx].close > allIndicators.SIX_PULSE.BBI[lastIdx] ? 'bullish' : 'bearish',
                  statusText: chartData.value[lastIdx].close > allIndicators.SIX_PULSE.BBI[lastIdx] ? '多头' : '空头',
                  description: '价格在BBI上方为多头，下方为空头'
                },
                {
                  name: 'MTM',
                  value: allIndicators.SIX_PULSE.MTM.MTM[lastIdx]?.toFixed(2) || '-',
                  status: allIndicators.SIX_PULSE.MTM.MTM[lastIdx] > 0 ? 'bullish' : 'bearish',
                  statusText: allIndicators.SIX_PULSE.MTM.MTM[lastIdx] > 0 ? '多头' : '空头',
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
              
              // 构建六脉神剑副图数据（每根K线的6个指标状态）
              sixPulseChartData.value = allIndicators.SIX_PULSE.signals.map((sig, idx) => {
                const sp = allIndicators.SIX_PULSE
                return {
                  // 每个指标：1=多头，-1=空头
                  macd: sp.MACD.DIF[idx] > sp.MACD.DEA[idx] ? 1 : -1,
                  kdj: sp.KDJ.K[idx] > sp.KDJ.D[idx] ? 1 : -1,
                  rsi: sp.RSI[idx] > 50 ? 1 : -1,
                  lwr: sp.LWR.LWR2[idx] < 50 ? 1 : -1,
                  bbi: chartData.value[idx]?.close > sp.BBI[idx] ? 1 : -1,
                  mtm: sp.MTM.MTM[idx] > 0 ? 1 : -1,
                  bullish: sig?.bullish || 0,
                  bearish: sig?.bearish || 0
                }
              })
            }
            
            // 识别机构大单（基于成交量异常）
            largeOrderSignals.value = detectLargeOrders(chartData.value)
            console.log('识别到机构大单:', largeOrderSignals.value.length, '个')
          } catch (err) {
            console.error('信号检测失败:', err)
          }
          
          await nextTick()
          renderChart()
        }
      } else {
        chartError.value = response.data.message || '获取数据失败'
      }
    } catch (error) {
      chartError.value = '加载失败: ' + error.message
    } finally {
      isLoadingChart.value = false
    }
  }

  // 计算移动平均线
  const calculateMA = function(data, period) {
    const result = []
    for (var i = 0; i < data.length; i++) {
      if (i < period - 1) {
        result.push(null)
      } else {
        var sum = 0
        for (var j = 0; j < period; j++) {
          sum += Number(data[i - j].close) || 0
        }
        result.push((sum / period).toFixed(2))
      }
    }
    return result
  }
  
  // 计算布林带
  const calculateBoll = function(data, period, multiplier) {
    period = period || 20
    multiplier = multiplier || 2
    const upper = [], middle = [], lower = []
    
    for (var i = 0; i < data.length; i++) {
      if (i < period - 1) {
        upper.push(null)
        middle.push(null)
        lower.push(null)
      } else {
        var sum = 0
        for (var j = 0; j < period; j++) {
          sum += Number(data[i - j].close) || 0
        }
        var ma = sum / period
        
        var squareSum = 0
        for (var k = 0; k < period; k++) {
          var diff = (Number(data[i - k].close) || 0) - ma
          squareSum += diff * diff
        }
        var std = Math.sqrt(squareSum / period)
        
        middle.push(ma.toFixed(2))
        upper.push((ma + multiplier * std).toFixed(2))
        lower.push((ma - multiplier * std).toFixed(2))
      }
    }
    
    return { upper: upper, middle: middle, lower: lower }
  }
  
  // 计算MACD
  const calculateMACD = function(data) {
    const dif = [], dea = [], macd = []
    
    var calcEMA = function(prices, period) {
      const result = []
      var mult = 2 / (period + 1)
      for (var i = 0; i < prices.length; i++) {
        if (i === 0) result.push(prices[i])
        else result.push((prices[i] - result[i - 1]) * mult + result[i - 1])
      }
      return result
    }
    
    var closes = data.map(function(d) { return Number(d.close) || 0 })
    var ema12 = calcEMA(closes, 12)
    var ema26 = calcEMA(closes, 26)
    
    for (var i = 0; i < data.length; i++) {
      if (i < 25) {
        dif.push(null)
        dea.push(null)
        macd.push(null)
      } else {
        dif.push((ema12[i] - ema26[i]).toFixed(3))
      }
    }
    
    var difValues = dif.filter(function(v) { return v !== null }).map(function(v) { return parseFloat(v) })
    var deaData = calcEMA(difValues, 9)
    
    var deaIdx = 0
    for (var j = 0; j < data.length; j++) {
      if (dif[j] !== null) {
        dea[j] = deaData[deaIdx].toFixed(3)
        macd[j] = ((parseFloat(dif[j]) - parseFloat(dea[j])) * 2).toFixed(3)
        deaIdx++
      }
    }
    
    return { DIF: dif, DEA: dea, MACD: macd }
  }
  
  // 计算RSI
  const calculateRSI = function(data, period) {
    period = period || 14
    const result = []
    for (var i = 0; i < data.length; i++) {
      if (i < period) {
        result.push(null)
      } else {
        var gains = 0, losses = 0
        for (var j = i - period + 1; j <= i; j++) {
          var change = (Number(data[j].close) || 0) - (Number(data[j - 1].close) || 0)
          if (change > 0) gains += change
          else losses -= change
        }
        var avgGain = gains / period
        var avgLoss = losses / period
        var rs = avgLoss === 0 ? 100 : avgGain / avgLoss
        result.push((100 - 100 / (1 + rs)).toFixed(2))
      }
    }
    return result
  }
  
  // 计算KDJ
  const calculateKDJ = function(data, period) {
    period = period || 9
    const K = [], D = [], J = []
    var prevK = 50, prevD = 50
    
    for (var i = 0; i < data.length; i++) {
      if (i < period - 1) {
        K.push(null)
        D.push(null)
        J.push(null)
      } else {
        var high = -Infinity, low = Infinity
        for (var j = i - period + 1; j <= i; j++) {
          high = Math.max(high, Number(data[j].high) || 0)
          low = Math.min(low, Number(data[j].low) || 0)
        }
        
        var close = Number(data[i].close) || 0
        var rsv = high === low ? 50 : ((close - low) / (high - low)) * 100
        
        var kVal = (2 / 3) * prevK + (1 / 3) * rsv
        var dVal = (2 / 3) * prevD + (1 / 3) * kVal
        var jVal = 3 * kVal - 2 * dVal
        
        K.push(kVal.toFixed(2))
        D.push(dVal.toFixed(2))
        J.push(jVal.toFixed(2))
        
        prevK = kVal
        prevD = dVal
      }
    }
    
    return { K: K, D: D, J: J }
  }

// 获取周期标签
  const getPeriodLabel = function(period) {
    var labels = { '1': '1分钟', '5': '5分钟', '10': '10分钟', '15': '15分钟', '30': '30分钟', '60': '60分钟', 'daily': '日线', 'weekly': '周线', 'monthly': '月线' }
    return labels[period] || period
  }

  // 生成信号标记点数据
  const getSignalMarkPoints = function(signals, dates, klineData) {
    if (!signals || signals.length === 0) return []
    
    // 只显示最近30根K线内的重要信号
    const minIndex = Math.max(0, klineData.length - 30)
    const recentSignals = signals.filter(function(s) {
      return s.index >= minIndex && (s.importance === 'high' || s.importance === 'medium')
    })
    
    return recentSignals.map(function(signal) {
      const kline = klineData[signal.index]
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
        },
        // 存储完整信息用于tooltip
        _signalInfo: {
          name: signal.name,
          description: signal.description || '',
          confidence: signal.confidence || 0,
          date: signal.date || dates[signal.index],
          indicator: signal.indicator || ''
        }
      }
    }).filter(function(p) { return p !== null })
  }
  
  // 生成形态标记点数据
  const getPatternMarkPoints = function(patterns, dates, klineData) {
    if (!patterns || patterns.length === 0) return []
    
    // 只显示最近30根K线内的重要形态
    const minIndex = Math.max(0, klineData.length - 30)
    const recentPatterns = patterns.filter(function(p) {
      return p.index >= minIndex && (p.importance === 'high' || p.importance === 'medium')
    })
    
    return recentPatterns.map(function(pattern) {
      const kline = klineData[pattern.index]
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
        },
        // 存储完整信息用于tooltip
        _patternInfo: {
          name: pattern.name,
          nameEn: pattern.nameEn || '',
          description: pattern.description || '',
          confidence: pattern.confidence || 0,
          date: pattern.date || dates[pattern.index]
        }
      }
    }).filter(function(p) { return p !== null })
  }

  // 渲染K线图
  const renderChart = function() {
    if (!chartContainer.value || chartData.value.length === 0) return
    
    try {
      var dom = chartContainer.value
      if (!chartInstance) {
        chartInstance = echarts.init(dom)
      } else {
        chartInstance.clear()
        chartInstance.resize()
      }
      
      var dates = chartData.value.map(function(item) { return item.date })
      var values = chartData.value.map(function(item) {
        return [Number(item.open), Number(item.close), Number(item.low), Number(item.high)]
      })
      var volumes = chartData.value.map(function(item) { return Number(item.volume) || 0 })
      
      var ma5Data = indicatorToggles.ma5 ? calculateMA(chartData.value, 5) : []
      var ma20Data = indicatorToggles.ma20 ? calculateMA(chartData.value, 20) : []
      var ma60Data = indicatorToggles.ma60 ? calculateMA(chartData.value, 60) : []
      var bollData = indicatorToggles.boll ? calculateBoll(chartData.value, 20, 2) : { upper: [], middle: [], lower: [] }
      var macdData = indicatorToggles.macd ? calculateMACD(chartData.value) : { DIF: [], DEA: [], MACD: [] }
      var rsiData = indicatorToggles.rsi ? calculateRSI(chartData.value) : []
      var kdjData = indicatorToggles.kdj ? calculateKDJ(chartData.value) : { K: [], D: [], J: [] }
      
      var legendData = ['K线', '成交量']
      if (indicatorToggles.ma5) legendData.push('MA5')
      if (indicatorToggles.ma20) legendData.push('MA20')
      if (indicatorToggles.ma60) legendData.push('MA60')
      
      // 动态计算grid布局 - 填满整个图表区域
      var gridCount = 2 // K线 + 成交量
      
      if (indicatorToggles.macd) gridCount++
      if (indicatorToggles.rsi || indicatorToggles.kdj) gridCount++
      if (indicatorToggles.sixPulse) gridCount++
      
      // 预留空间：顶部8%用于标题/图例，底部6%用于dataZoom
      var topReserved = 8
      var bottomReserved = 6
      
      // 根据副图数量分配高度
      var klineHeight, volumeHeight, subChartHeight
      
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
      
      var currentTop = topReserved
      var gridIdx = 2
      
      var grids = [
        { left: '1%', right: '1%', top: currentTop + '%', height: klineHeight + '%', containLabel: true }
      ]
      currentTop += klineHeight + 1
      
      grids.push({ left: '1%', right: '1%', top: currentTop + '%', height: volumeHeight + '%', containLabel: true })
      currentTop += volumeHeight + 1
      
      if (indicatorToggles.macd) {
        grids.push({ left: '1%', right: '1%', top: currentTop + '%', height: subChartHeight + '%', containLabel: true })
        currentTop += subChartHeight + 1
        gridIdx++
      }
      if (indicatorToggles.rsi || indicatorToggles.kdj) {
        grids.push({ left: '1%', right: '1%', top: currentTop + '%', height: subChartHeight + '%', containLabel: true })
        currentTop += subChartHeight + 1
        gridIdx++
      }
      if (indicatorToggles.sixPulse) {
        grids.push({ left: '1%', right: '1%', top: currentTop + '%', height: subChartHeight + '%', containLabel: true })
        currentTop += subChartHeight + 1
      }
      
      var xAxisArr = [
        { type: 'category', data: dates, gridIndex: 0, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { color: '#64748b', fontSize: 10 }, boundaryGap: true },
        { type: 'category', data: dates, gridIndex: 1, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { show: false }, boundaryGap: true }
      ]
      
      var xAxisIdx = 2
      if (indicatorToggles.macd) {
        xAxisArr.push({ type: 'category', data: dates, gridIndex: xAxisIdx, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { show: false }, boundaryGap: true })
        xAxisIdx++
      }
      
      if (indicatorToggles.rsi || indicatorToggles.kdj) {
        xAxisArr.push({ type: 'category', data: dates, gridIndex: xAxisIdx, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { show: false }, boundaryGap: true })
        xAxisIdx++
      }
      
      if (indicatorToggles.sixPulse) {
        xAxisArr.push({ type: 'category', data: dates, gridIndex: xAxisIdx, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { color: '#64748b', fontSize: 10 }, boundaryGap: true })
      }
      
      var yAxisArr = [
        { scale: true, gridIndex: 0, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)' } }, axisLine: { lineStyle: { color: '#334155' } }, axisLabel: { color: '#64748b' } },
        { scale: true, gridIndex: 1, splitNumber: 2, axisLabel: { show: false }, axisLine: { show: false }, axisTick: { show: false }, splitLine: { show: false } }
      ]
      
      var yAxisIdx = 2
      if (indicatorToggles.macd) {
        yAxisArr.push({ scale: true, gridIndex: yAxisIdx, splitNumber: 2, axisLabel: { color: '#64748b', fontSize: 10 }, axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } } })
        yAxisIdx++
      }
      
      if (indicatorToggles.rsi || indicatorToggles.kdj) {
        yAxisArr.push({ scale: true, gridIndex: yAxisIdx, splitNumber: 2, min: 0, max: 100, axisLabel: { color: '#64748b', fontSize: 10 }, axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } } })
        yAxisIdx++
      }
      
      if (indicatorToggles.sixPulse) {
        yAxisArr.push({ scale: true, gridIndex: yAxisIdx, splitNumber: 2, min: -6, max: 6, axisLabel: { show: false }, axisLine: { show: false }, splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.2)' } } })
      }
      
var seriesArr = [
        {
          name: 'K线', type: 'candlestick', data: values,
          itemStyle: { color: '#ef5350', color0: '#26a69a', borderColor: '#ef5350', borderColor0: '#26a69a' },
          markPoint: { 
            data: [
              // 用户手动添加的标记
              ...chartMarkers.value.map(function(m) { 
                return { name: m.label, coord: [m.date, m.price], value: m.label, itemStyle: { color: m.color || '#f59e0b' } } 
              }),
              // 自动检测的信号标记
              ...(indicatorToggles.showSignals ? getSignalMarkPoints(detectedSignals.value, dates, chartData.value) : []),
              // 自动检测的形态标记
              ...(indicatorToggles.showPatterns ? getPatternMarkPoints(detectedPatterns.value, dates, chartData.value) : []),
              // 机构大单标记
              ...(indicatorToggles.showLargeOrders ? getLargeOrderMarkPoints(largeOrderSignals.value, dates, chartData.value) : [])
            ],
            symbolSize: 30,
            label: { show: true, fontSize: 10, color: '#fff' }
          },
          markLine: { silent: true, data: chartDrawings.value.filter(function(d) { return d.type === 'hline' }).map(function(d) { return { yAxis: d.price, lineStyle: { color: d.color || '#f59e0b', type: 'dashed' }, label: { formatter: d.label || String(d.price.toFixed(2)) } } }) }
        },
        {
          name: '成交量', type: 'bar', xAxisIndex: 1, yAxisIndex: 1, data: volumes,
          itemStyle: { 
            color: function(params) { 
              const idx = params.dataIndex
              const isUp = chartData.value[idx].close >= chartData.value[idx].open
              // 计算成交量是否异常放大（超过5日均量的1.5倍）
              if (idx >= 5) {
                let avgVol = 0
                for (let i = idx - 5; i < idx; i++) {
                  avgVol += chartData.value[i].volume
                }
                avgVol /= 5
                const isLargeVolume = chartData.value[idx].volume > avgVol * 1.5
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
            data: (function() {
              const marks = []
              for (let i = 5; i < chartData.value.length; i++) {
                let avgVol = 0
                for (let j = i - 5; j < i; j++) {
                  avgVol += chartData.value[j].volume
                }
                avgVol /= 5
                // 放量超过2倍
                if (chartData.value[i].volume > avgVol * 2) {
                  marks.push({
                    coord: [dates[i], chartData.value[i].volume],
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
      
      if (indicatorToggles.ma5) seriesArr.push({ name: 'MA5', type: 'line', data: ma5Data, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#f5d742' } })
      if (indicatorToggles.ma20) seriesArr.push({ name: 'MA20', type: 'line', data: ma20Data, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#42a5f5' } })
      if (indicatorToggles.ma60) seriesArr.push({ name: 'MA60', type: 'line', data: ma60Data, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ab47bc' } })
      
      if (indicatorToggles.boll) {
        seriesArr.push(
          { name: 'BOLL上轨', type: 'line', data: bollData.upper, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800', type: 'dashed' } },
          { name: 'BOLL中轨', type: 'line', data: bollData.middle, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800' } },
          { name: 'BOLL下轨', type: 'line', data: bollData.lower, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800', type: 'dashed' } }
        )
      }
      
      if (indicatorToggles.macd) {
        seriesArr.push(
          { name: 'DIF', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: macdData.DIF, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#42a5f5' } },
          { name: 'DEA', type: 'line', xAxisIndex: 2, yAxisIndex: 2, data: macdData.DEA, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800' } },
          { name: 'MACD柱', type: 'bar', xAxisIndex: 2, yAxisIndex: 2, data: macdData.MACD, itemStyle: { color: function(params) { return parseFloat(params.data) >= 0 ? '#ef5350' : '#26a69a' } } }
        )
      }
      
      var rsiKdjAxisIndex = indicatorToggles.macd ? 3 : 2
      if (indicatorToggles.rsi) {
        seriesArr.push({
          name: 'RSI', type: 'line', xAxisIndex: rsiKdjAxisIndex, yAxisIndex: rsiKdjAxisIndex, data: rsiData, smooth: true, showSymbol: false,
          lineStyle: { width: 1, color: '#ab47bc' },
          markLine: { silent: true, data: [{ yAxis: 70, lineStyle: { color: '#ef5350', type: 'dashed' } }, { yAxis: 30, lineStyle: { color: '#26a69a', type: 'dashed' } }] }
        })
      }
      
      if (indicatorToggles.kdj) {
        seriesArr.push(
          { name: 'K', type: 'line', xAxisIndex: rsiKdjAxisIndex, yAxisIndex: rsiKdjAxisIndex, data: kdjData.K, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#42a5f5' } },
          { name: 'D', type: 'line', xAxisIndex: rsiKdjAxisIndex, yAxisIndex: rsiKdjAxisIndex, data: kdjData.D, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#ff9800' } },
          { name: 'J', type: 'line', xAxisIndex: rsiKdjAxisIndex, yAxisIndex: rsiKdjAxisIndex, data: kdjData.J, smooth: true, showSymbol: false, lineStyle: { width: 1, color: '#e91e63' } }
        )
      }
      
      // 六脉神剑副图 - 堆叠柱状图
      if (indicatorToggles.sixPulse && sixPulseChartData.value && sixPulseChartData.value.length > 0) {
        // 计算六脉神剑副图的坐标轴索引
        var sixPulseAxisIndex = 2
        if (indicatorToggles.macd) sixPulseAxisIndex++
        if (indicatorToggles.rsi || indicatorToggles.kdj) sixPulseAxisIndex++
        
        // 六脉神剑6个指标的颜色定义
        var sixPulseColors = {
          macd: '#42a5f5',   // 蓝色 - MACD
          kdj: '#ff9800',    // 橙色 - KDJ
          rsi: '#ab47bc',    // 紫色 - RSI
          lwr: '#26a69a',    // 青色 - LWR
          bbi: '#f5d742',    // 黄色 - BBI
          mtm: '#e91e63'     // 粉色 - MTM
        }
        
        // 为每个指标创建堆叠柱状图数据
        // 多头信号为正值，空头信号为负值
        var macdBarData = sixPulseChartData.value.map(function(d) { return d ? d.macd : 0 })
        var kdjBarData = sixPulseChartData.value.map(function(d) { return d ? d.kdj : 0 })
        var rsiBarData = sixPulseChartData.value.map(function(d) { return d ? d.rsi : 0 })
        var lwrBarData = sixPulseChartData.value.map(function(d) { return d ? d.lwr : 0 })
        var bbiBarData = sixPulseChartData.value.map(function(d) { return d ? d.bbi : 0 })
        var mtmBarData = sixPulseChartData.value.map(function(d) { return d ? d.mtm : 0 })
        
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
              color: function(params) {
                return params.data >= 0 ? sixPulseColors.macd : 'rgba(66, 165, 245, 0.5)'
              }
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
              color: function(params) {
                return params.data >= 0 ? sixPulseColors.kdj : 'rgba(255, 152, 0, 0.5)'
              }
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
              color: function(params) {
                return params.data >= 0 ? sixPulseColors.rsi : 'rgba(171, 71, 188, 0.5)'
              }
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
              color: function(params) {
                return params.data >= 0 ? sixPulseColors.lwr : 'rgba(38, 166, 154, 0.5)'
              }
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
              color: function(params) {
                return params.data >= 0 ? sixPulseColors.bbi : 'rgba(245, 215, 66, 0.5)'
              }
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
              color: function(params) {
                return params.data >= 0 ? sixPulseColors.mtm : 'rgba(233, 30, 99, 0.5)'
              }
            }
          }
        )
        
        // 添加零轴线
        seriesArr.push({
          name: '六脉零轴',
          type: 'line',
          xAxisIndex: sixPulseAxisIndex,
          yAxisIndex: sixPulseAxisIndex,
          data: dates.map(function() { return 0 }),
          showSymbol: false,
          lineStyle: { width: 1, color: 'rgba(148, 163, 184, 0.5)', type: 'dashed' }
        })
      }
      
var option = {
        backgroundColor: 'transparent',
        title: {
          text: chartStockCode.value + '  ' + getPeriodLabel(chartPeriod.value),
          subtext: dataSource.value ? '数据源: ' + dataSource.value : '',
          left: '40%',top:'1%',
          textStyle: { color: '#e2e8f0', fontSize: 14, fontWeight: 600 },
          subtextStyle: { color: '#64748b', fontSize: 11 }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          backgroundColor: 'rgba(30, 41, 59, 0.95)',
          borderColor: 'rgba(51, 65, 85, 0.5)',
          textStyle: { color: '#e2e8f0' }
        },
        legend: { data: legendData, textStyle: { color: '#94a3b8', fontSize: 11 }, top: 5, right: '40%', itemGap: 8, itemWidth: 14, itemHeight: 10 },
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
      console.error('渲染K线图失败:', error)
      chartError.value = '渲染图表失败'
    }
  }

  // 添加价格标记
  const addMarker = function(date, price, label, color) {
    chartMarkers.value.push({ date: date, price: price, label: label, color: color || '#f59e0b' })
    renderChart()
  }
  
  // 添加水平线
  const addHorizontalLine = function(price, label, color) {
    chartDrawings.value.push({ type: 'hline', price: price, label: label, color: color || '#f59e0b' })
    renderChart()
  }
  
  // 添加支撑线
  const addSupportLine = function(price, label) {
    addHorizontalLine(price, label || '支撑位', '#26a69a')
  }
  
  // 添加阻力线
  const addResistanceLine = function(price, label) {
    addHorizontalLine(price, label || '阻力位', '#ef5350')
  }
  
  // 标记高点
  const markHighPoint = function() {
    if (chartData.value.length === 0) return
    var maxHigh = -Infinity, maxIdx = 0
    chartData.value.forEach(function(item, idx) {
      if (item.high > maxHigh) {
        maxHigh = item.high
        maxIdx = idx
      }
    })
    addMarker(chartData.value[maxIdx].date, maxHigh, '高点', '#ef5350')
  }
  
  // 标记低点
  const markLowPoint = function() {
    if (chartData.value.length === 0) return
    var minLow = Infinity, minIdx = 0
    chartData.value.forEach(function(item, idx) {
      if (item.low < minLow) {
        minLow = item.low
        minIdx = idx
      }
    })
    addMarker(chartData.value[minIdx].date, minLow, '低点', '#26a69a')
  }
  
  // 标记买点
  const markBuyPoint = function(date, price) {
    addMarker(date, price, '买入', '#26a69a')
  }
  
  // 标记卖点
  const markSellPoint = function(date, price) {
    addMarker(date, price, '卖出', '#ef5350')
  }
  
  // 自动检测关键价位
  const autoDetectKeyLevels = function() {
    if (chartData.value.length < 20) return
    
    var recentData = chartData.value.slice(-60)
    var highs = recentData.map(function(d) { return d.high })
    var lows = recentData.map(function(d) { return d.low })
    
    var maxHigh = Math.max.apply(null, highs)
    var minLow = Math.min.apply(null, lows)
    
    addResistanceLine(maxHigh, '近期高点')
    addSupportLine(minLow, '近期低点')
    
    var midLevel = (maxHigh + minLow) / 2
    addHorizontalLine(midLevel, '中轴线', '#64748b')
  }
  
  // 清除所有标记
  const clearAllMarkers = function() {
    chartMarkers.value = []
    chartDrawings.value = []
    renderChart()
  }
  
  // 获取成交量状态
  const getVolumeStatus = function() {
    if (!chartData.value || chartData.value.length < 6) return '数据不足'
    const lastIdx = chartData.value.length - 1
    const currentVol = chartData.value[lastIdx].volume
    
    // 计算5日均量
    let avgVol = 0
    for (let i = lastIdx - 5; i < lastIdx; i++) {
      avgVol += chartData.value[i].volume
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
  const getVolumeClass = function() {
    if (!chartData.value || chartData.value.length < 6) return ''
    const lastIdx = chartData.value.length - 1
    const currentVol = chartData.value[lastIdx].volume
    
    let avgVol = 0
    for (let i = lastIdx - 5; i < lastIdx; i++) {
      avgVol += chartData.value[i].volume
    }
    avgVol /= 5
    
    const ratio = currentVol / avgVol
    if (ratio > 1.5) return 'volume-up'
    if (ratio < 0.7) return 'volume-down'
    return ''
  }
  
  // 识别机构大单（基于成交量和价格变化）
  const detectLargeOrders = function(klineData) {
    if (!klineData || klineData.length < 10) return []
    
    const signals = []
    
    for (let i = 5; i < klineData.length; i++) {
      const current = klineData[i]
      const currentVol = current.volume
      const priceChange = (current.close - current.open) / current.open
      
      // 计算5日均量
      let avgVol = 0
      for (let j = i - 5; j < i; j++) {
        avgVol += klineData[j].volume
      }
      avgVol /= 5
      
      const volRatio = currentVol / avgVol
      
      // 机构大单买入信号：放量上涨（成交量>2倍均量 且 涨幅>1%）
      if (volRatio > 2 && priceChange > 0.01) {
        // 检查是否连续放量（更可靠的机构信号）
        let consecutiveLargeVol = 0
        for (let k = i; k >= Math.max(0, i - 2); k--) {
          let kAvgVol = 0
          for (let m = k - 5; m < k && m >= 0; m++) {
            kAvgVol += klineData[m]?.volume || 0
          }
          kAvgVol = kAvgVol / 5 || 1
          if (klineData[k].volume > kAvgVol * 1.5) {
            consecutiveLargeVol++
          }
        }
        
        signals.push({
          index: i,
          date: current.date,
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
          date: current.date,
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
    
    // 只返回最近20个信号
    return signals.slice(-20)
  }
  
  // 生成机构大单标记点
  const getLargeOrderMarkPoints = function(signals, dates, klineData) {
    if (!signals || signals.length === 0) return []
    
    // 只显示最近15根K线内的信号
    const minIndex = Math.max(0, klineData.length - 15)
    const recentSignals = signals.filter(s => s.index >= minIndex)
    
    return recentSignals.map(function(signal) {
      const kline = klineData[signal.index]
      if (!kline) return null
      
      const isBuy = signal.type === 'buy'
      const price = isBuy ? kline.low * 0.99 : kline.high * 1.01
      
      return {
        name: signal.name,
        coord: [dates[signal.index], price],
        value: isBuy ? '机买' : '机卖',
        symbol: 'rect',
        symbolSize: [30, 16],
        itemStyle: { 
          color: isBuy ? '#fbbf24' : '#f472b6',
          borderColor: '#fff',
          borderWidth: 1
        },
        label: {
          show: true,
          position: 'inside',
          formatter: isBuy ? '机买' : '机卖',
          fontSize: 9,
          color: '#000',
          fontWeight: 'bold'
        },
        emphasis: {
          label: {
            show: true,
            formatter: function() {
              return signal.name + '\n' + signal.description + '\n置信度: ' + (signal.confidence * 100).toFixed(0) + '%'
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
  
  // 切换绘图模式
  const toggleDrawingMode = function(tool) {
    if (drawingTool.value === tool) {
      isDrawingMode.value = false
      drawingTool.value = null
    } else {
      isDrawingMode.value = true
      drawingTool.value = tool
    }
  }
  
  // 打开价格标记模态框
  const openPriceMarkerModal = function() {
    if (chartData.value.length > 0) {
      priceMarkerForm.value.price = chartData.value[chartData.value.length - 1].close
    }
    showPriceMarkerModal.value = true
  }
  
  // 添加自定义价格标记
  const addCustomPriceMarker = function() {
    var price = parseFloat(priceMarkerForm.value.price)
    if (isNaN(price)) return
    
    if (priceMarkerForm.value.type === 'support') {
      addSupportLine(price, priceMarkerForm.value.label || '支撑位')
    } else if (priceMarkerForm.value.type === 'resistance') {
      addResistanceLine(price, priceMarkerForm.value.label || '阻力位')
    } else {
      addHorizontalLine(price, priceMarkerForm.value.label, priceMarkerForm.value.color)
    }
    
    showPriceMarkerModal.value = false
    priceMarkerForm.value = { price: '', label: '', type: 'support', color: '#f59e0b' }
  }
  
  // 获取K线截图
  const getChartScreenshot = async function() {
    if (!chartInstance) return null
    try {
      return chartInstance.getDataURL({ type: 'png', pixelRatio: 2, backgroundColor: '#1e293b' })
    } catch (error) {
      console.error('获取截图失败:', error)
      return null
    }
  }

  // 解析策略文本
  const handleParseStrategy = async function() {
    if (!parseText.value.trim()) return
    
    isParsing.value = true
    try {
      const result = await parseStrategyText(parseText.value)
      if (result.success) {
        strategyForm.value = {
          name: result.strategy.name || '',
          description: result.strategy.description || '',
          category: 'custom',
          indicators: result.strategy.indicators || [],
          entry_conditions: result.strategy.entry_conditions || [],
          exit_conditions: result.strategy.exit_conditions || [],
          risk_params: result.strategy.risk_params || { stop_loss: 0.05, take_profit: 0.15, max_position: 0.3 }
        }
        showParseModal.value = false
        showCreateModal.value = true
        parseText.value = ''
      }
    } catch (error) {
      console.error('解析策略失败:', error)
    } finally {
      isParsing.value = false
    }
  }

  // 保存策略
  const saveStrategy = async function() {
    try {
      var result
      if (editingStrategy.value) {
        result = await updateStrategy(editingStrategy.value.id, strategyForm.value)
      } else {
        result = await createStrategy(strategyForm.value)
      }
      
      if (result.success) {
        showCreateModal.value = false
        editingStrategy.value = null
        resetStrategyForm()
        await loadStrategies()
      }
    } catch (error) {
      console.error('保存策略失败:', error)
    }
  }

  // 编辑策略
  const editStrategy = function(strategy) {
    editingStrategy.value = strategy
    strategyForm.value = {
      name: strategy.name,
      description: strategy.description || '',
      category: strategy.category || 'custom',
      indicators: strategy.indicators || [],
      entry_conditions: strategy.entry_conditions || [],
      exit_conditions: strategy.exit_conditions || [],
      risk_params: strategy.risk_params || { stop_loss: 0.05, take_profit: 0.15, max_position: 0.3 }
    }
    showCreateModal.value = true
  }

  // 删除策略
  const deleteStrategy = async function(strategy) {
    if (!confirm('确定要删除策略 "' + strategy.name + '" 吗？')) return
    
    try {
      const result = await deleteStrategyApi(strategy.id)
      if (result.success) {
        if (selectedStrategy.value && selectedStrategy.value.id === strategy.id) {
          selectedStrategy.value = null
        }
        await loadStrategies()
      }
    } catch (error) {
      console.error('删除策略失败:', error)
    }
  }

  // 重置表单
  const resetStrategyForm = function() {
    strategyForm.value = {
      name: '',
      description: '',
      category: 'custom',
      indicators: [],
      entry_conditions: [],
      exit_conditions: [],
      risk_params: { stop_loss: 0.05, take_profit: 0.15, max_position: 0.3 }
    }
  }

  // 生成交易信号
  const generateSignal = async function() {
    if (!selectedStrategy.value) {
      alert('请先选择一个策略')
      return
    }
    if (!signalForm.value.stockCode) {
      alert('请输入股票代码')
      return
    }
    if (!signalForm.value.model) {
      alert('请选择分析模型')
      return
    }
    
    isGenerating.value = true
    signalResult.value = null
    
    try {
      // 保存用户选择的模型到localStorage
      localStorage.setItem('strategy_center_selected_model', signalForm.value.model)

      var chartScreenshot = null
      if (signalForm.value.includeChart) {
        chartScreenshot = await getChartScreenshot()
      }

      const result = await generateSignalApi({
        strategy_id: selectedStrategy.value.id,
        stock_code: signalForm.value.stockCode,
        model: signalForm.value.model,
        include_chart: signalForm.value.includeChart,
        include_news: signalForm.value.includeNews,
        chart_screenshot: chartScreenshot,
        indicators: currentIndicators.value
      })
      
      if (result.success) {
        signalResult.value = result.signal
        
        if (result.signal && result.signal.markers) {
          result.signal.markers.forEach(function(marker) {
            if (marker.type === 'buy') {
              markBuyPoint(marker.date, marker.price)
            } else if (marker.type === 'sell') {
              markSellPoint(marker.date, marker.price)
            }
          })
        }
      }
    } catch (error) {
      console.error('生成信号失败:', error)
      signalResult.value = { error: '生成信号失败: ' + error.message }
    } finally {
      isGenerating.value = false
    }
  }

  // 获取来源标签
  const getSourceLabel = function(source) {
    var labels = {
      'preset': '预设策略',
      'custom': '自定义',
      'llm_parsed': 'AI解析'
    }
    return labels[source] || source
  }
  
  // 获取指标类型标签
  const getIndicatorTypeLabel = function(type) {
    var labels = {
      'trend': '趋势',
      'momentum': '动量',
      'volatility': '波动',
      'volume': '成交量',
      'price': '价格'
    }
    return labels[type] || type
  }
  
  // 获取RSI样式类
  const getRSIClass = function(rsi) {
    if (!rsi) return ''
    if (rsi > 70) return 'overbought'
    if (rsi < 30) return 'oversold'
    return 'neutral'
  }
  
  // 获取操作图标
  const getActionIcon = function(action) {
    var icons = {
      'BUY': '📈',
      'SELL': '📉',
      'HOLD': '⏸️',
      'buy': '📈',
      'sell': '📉',
      'hold': '⏸️'
    }
    return icons[action] || '❓'
  }
  
  // 获取操作文本
  const getActionText = function(action) {
    var texts = {
      'BUY': '买入',
      'SELL': '卖出',
      'HOLD': '持有',
      'buy': '买入',
      'sell': '卖出',
      'hold': '持有'
    }
    return texts[action] || action
  }
  
  // 解析策略（模板中使用的名称）
  const parseStrategy = async function() {
    return handleParseStrategy()
  }
  
  // 截图保存
  const captureChart = async function() {
    var screenshot = await getChartScreenshot()
    if (screenshot) {
      var link = document.createElement('a')
      link.download = chartStockCode.value + '_' + chartPeriod.value + '_' + new Date().toISOString().slice(0, 10) + '.png'
      link.href = screenshot
      link.click()
    }
  }
  
  // 清除标记（模板中使用的名称）
  const clearMarkers = function() {
    return clearAllMarkers()
  }
  
  // 从表单添加价格标记
  const addPriceMarkerFromForm = function() {
    var price = parseFloat(priceMarkerForm.value.price)
    if (isNaN(price)) return
    
    var type = priceMarkerForm.value.type
    var label = priceMarkerForm.value.label
    
    if (type === 'support') {
      addSupportLine(price, label || '支撑位')
    } else if (type === 'resistance') {
      addResistanceLine(price, label || '阻力位')
    } else if (type === 'high') {
      markHighPoint()
    } else if (type === 'low') {
      markLowPoint()
    } else if (type === 'buy' && chartData.value.length > 0) {
      markBuyPoint(chartData.value[chartData.value.length - 1].date, price)
    } else if (type === 'sell' && chartData.value.length > 0) {
      markSellPoint(chartData.value[chartData.value.length - 1].date, price)
    } else {
      addHorizontalLine(price, label, priceMarkerForm.value.color)
    }

    showPriceMarkerModal.value = false
    priceMarkerForm.value = { price: '', label: '', type: 'support', color: '#f59e0b' }
  }

  // ==================== 交易计划相关方法 ====================

  // 加载交易计划列表
  const loadTradingPlans = async function() {
    try {
      const response = await axios.get(API_BASE_URL + '/api/strategy-center/plans')
      if (response.data && response.data.success) {
        tradingPlans.value = response.data.data || []
      }
    } catch (error) {
      console.error('加载交易计划失败:', error)
    }
  }

  // 打开创建计划模态框
  const openCreatePlanModal = function(strategy) {
    if (!strategy) return
    planForm.value = {
      strategy: strategy,
      stockCode: chartStockCode.value || '',
      stockName: '',
      allocatedCapital: 100000,
      maxPositionRatio: strategy.risk_params?.max_position ? strategy.risk_params.max_position * 100 : 30,
      stopLossPct: strategy.risk_params?.stop_loss ? strategy.risk_params.stop_loss * 100 : 5,
      takeProfitPct: strategy.risk_params?.take_profit ? strategy.risk_params.take_profit * 100 : 15,
      checkInterval: 30,
      decisionMode: 'rule_only',
      autoStart: true
    }
    showCreatePlanModal.value = true
  }

  // 创建交易计划
  const createTradingPlan = async function() {
    if (!planForm.value.stockCode || !planForm.value.strategy) return

    isCreatingPlan.value = true
    try {
      const response = await axios.post(API_BASE_URL + '/api/strategy-center/plans', {
        strategy_id: planForm.value.strategy.id,
        strategy_name: planForm.value.strategy.name,
        strategy_config: planForm.value.strategy,
        stock_code: planForm.value.stockCode,
        stock_name: planForm.value.stockName,
        allocated_capital: planForm.value.allocatedCapital,
        max_position_ratio: planForm.value.maxPositionRatio / 100,
        decision_mode: planForm.value.decisionMode,
        check_interval: planForm.value.checkInterval,
        stop_loss_pct: planForm.value.stopLossPct / 100,
        take_profit_pct: planForm.value.takeProfitPct / 100,
        auto_start: planForm.value.autoStart
      })

      if (response.data && response.data.success) {
        showCreatePlanModal.value = false
        await loadTradingPlans()
        alert('交易计划创建成功！')
      } else {
        alert('创建失败: ' + (response.data?.message || '未知错误'))
      }
    } catch (error) {
      console.error('创建交易计划失败:', error)
      alert('创建失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      isCreatingPlan.value = false
    }
  }

  // 启动计划
  const startPlan = async function(planId) {
    try {
      const response = await axios.post(API_BASE_URL + '/api/strategy-center/plans/' + planId + '/start')
      if (response.data && response.data.success) {
        await loadTradingPlans()
      }
    } catch (error) {
      console.error('启动计划失败:', error)
      alert('启动失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 暂停计划
  const pausePlan = async function(planId) {
    try {
      const response = await axios.post(API_BASE_URL + '/api/strategy-center/plans/' + planId + '/pause')
      if (response.data && response.data.success) {
        await loadTradingPlans()
      }
    } catch (error) {
      console.error('暂停计划失败:', error)
      alert('暂停失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 停止计划
  const stopPlan = async function(planId) {
    if (!confirm('确定要停止此计划吗？')) return
    try {
      const response = await axios.post(API_BASE_URL + '/api/strategy-center/plans/' + planId + '/stop')
      if (response.data && response.data.success) {
        await loadTradingPlans()
      }
    } catch (error) {
      console.error('停止计划失败:', error)
      alert('停止失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 删除计划
  const deletePlan = async function(planId) {
    if (!confirm('确定要删除此计划吗？此操作不可恢复。')) return
    try {
      const response = await axios.delete(API_BASE_URL + '/api/strategy-center/plans/' + planId)
      if (response.data && response.data.success) {
        await loadTradingPlans()
      }
    } catch (error) {
      console.error('删除计划失败:', error)
      alert('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 查看计划详情
  const viewPlanDetail = function(plan) {
    selectedPlanDetail.value = plan
    showPlanDetailModal.value = true
  }

  // 获取状态标签
  const getStatusLabel = function(status) {
    const labels = {
      'running': '运行中',
      'paused': '已暂停',
      'stopped': '已停止',
      'pending': '待启动'
    }
    return labels[status] || status
  }

  // ==================== 实时刷新相关方法 ====================
  
  // 更新交易状态
  const updateTradingStatus = function() {
    tradingStatus.value = getTradingStatus()
  }
  
  // 静默刷新K线数据（不显示loading状态）
  const silentRefreshKlineData = async function() {
    if (!chartStockCode.value || chartData.value.length === 0) return
    
    isAutoRefreshing.value = true
    
    try {
      const response = await axios.get(API_BASE_URL + '/api/kline/data', {
        params: {
          symbol: chartStockCode.value,
          period: chartPeriod.value,
          adjust: 'qfq',
          source: 'auto',
          limit: 200
        }
      })
      
      if (response.data.success) {
        const klineData = response.data.data || []
        dataSource.value = response.data.source
        
        if (klineData.length > 0) {
          chartData.value = klineData.map(function(item) {
            return {
              date: item.time || item.date,
              open: parseFloat(item.open) || 0,
              high: parseFloat(item.high) || 0,
              low: parseFloat(item.low) || 0,
              close: parseFloat(item.close) || 0,
              volume: parseFloat(item.volume) || 0
            }
          })
          
          // 更新指标
          const indicators = calculateIndicators(chartData.value, ['MA', 'MACD', 'RSI', 'BOLL', 'KDJ'])
          const lastIdx = chartData.value.length - 1
          currentIndicators.value = {
            MA5: indicators.MA5 ? indicators.MA5[lastIdx] : null,
            MA10: indicators.MA10 ? indicators.MA10[lastIdx] : null,
            MA20: indicators.MA20 ? indicators.MA20[lastIdx] : null,
            MA60: indicators.MA60 ? indicators.MA60[lastIdx] : null,
            RSI: indicators.RSI ? indicators.RSI[lastIdx] : null,
            MACD: indicators.MACD && indicators.MACD.MACD ? indicators.MACD.MACD[lastIdx] : null
          }
          
          // 重新检测信号
          try {
            const allIndicators = calculateAllIndicators(chartData.value)
            detectedSignals.value = detectAllSignals(chartData.value, allIndicators)
            detectedPatterns.value = detectAllPatterns(chartData.value)
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
                  value: allIndicators.SIX_PULSE.LWR.LWR2[lastIdx]?.toFixed(1) || '-',
                  status: allIndicators.SIX_PULSE.LWR.LWR2[lastIdx] < 50 ? 'bullish' : 'bearish',
                  statusText: allIndicators.SIX_PULSE.LWR.LWR2[lastIdx] < 30 ? '超买' : (allIndicators.SIX_PULSE.LWR.LWR2[lastIdx] > 70 ? '超卖' : (allIndicators.SIX_PULSE.LWR.LWR2[lastIdx] < 50 ? '多头' : '空头')),
                  description: 'LWR<50为多头，>50为空头'
                },
                {
                  name: 'BBI',
                  value: allIndicators.SIX_PULSE.BBI[lastIdx]?.toFixed(2) || '-',
                  status: chartData.value[lastIdx].close > allIndicators.SIX_PULSE.BBI[lastIdx] ? 'bullish' : 'bearish',
                  statusText: chartData.value[lastIdx].close > allIndicators.SIX_PULSE.BBI[lastIdx] ? '多头' : '空头',
                  description: '价格在BBI上方为多头，下方为空头'
                },
                {
                  name: 'MTM',
                  value: allIndicators.SIX_PULSE.MTM.MTM[lastIdx]?.toFixed(2) || '-',
                  status: allIndicators.SIX_PULSE.MTM.MTM[lastIdx] > 0 ? 'bullish' : 'bearish',
                  statusText: allIndicators.SIX_PULSE.MTM.MTM[lastIdx] > 0 ? '多头' : '空头',
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
                  lwr: sp.LWR.LWR2[idx] < 50 ? 1 : -1,
                  bbi: chartData.value[idx]?.close > sp.BBI[idx] ? 1 : -1,
                  mtm: sp.MTM.MTM[idx] > 0 ? 1 : -1,
                  bullish: sig?.bullish || 0,
                  bearish: sig?.bearish || 0
                }
              })
            }
            
            largeOrderSignals.value = detectLargeOrders(chartData.value)
          } catch (err) {
            console.error('信号检测失败:', err)
          }
          
          // 重新渲染图表
          await nextTick()
          renderChart()
          
          lastRefreshTime.value = new Date()
          console.log('[实时刷新] K线数据已更新:', chartStockCode.value, new Date().toLocaleTimeString())
        }
      }
    } catch (error) {
      console.error('[实时刷新] K线数据刷新失败:', error)
    } finally {
      isAutoRefreshing.value = false
    }
  }
  
  // 启动K线实时刷新
  const startKlineRefresh = function() {
    if (klineRefreshTimer.value) {
      klineRefreshTimer.value.stop()
    }
    
    klineRefreshTimer.value = createAdaptiveRefreshTimer(
      silentRefreshKlineData,
      'kline',
      {
        immediate: false,
        onStatusChange: function(status) {
          tradingStatus.value = status
          console.log('[实时刷新] 交易状态变化:', status.statusText)
        }
      }
    )
    
    // 启动倒计时显示
    startCountdown()
    
    console.log('[实时刷新] K线刷新定时器已启动')
  }
  
  // 停止K线实时刷新
  const stopKlineRefresh = function() {
    if (klineRefreshTimer.value) {
      klineRefreshTimer.value.stop()
      klineRefreshTimer.value = null
    }
    stopCountdown()
    console.log('[实时刷新] K线刷新定时器已停止')
  }
  
  // 启动计划状态刷新
  const startPlanRefresh = function() {
    if (planRefreshTimer.value) {
      planRefreshTimer.value.stop()
    }
    
    planRefreshTimer.value = createAdaptiveRefreshTimer(
      loadTradingPlans,
      'strategyPlan',
      {
        immediate: false,
        onStatusChange: function(status) {
          tradingStatus.value = status
        }
      }
    )
    
    console.log('[实时刷新] 计划刷新定时器已启动')
  }
  
  // 停止计划状态刷新
  const stopPlanRefresh = function() {
    if (planRefreshTimer.value) {
      planRefreshTimer.value.stop()
      planRefreshTimer.value = null
    }
    console.log('[实时刷新] 计划刷新定时器已停止')
  }
  
  // 启动倒计时显示
  const startCountdown = function() {
    stopCountdown()
    countdownInterval = setInterval(function() {
      if (klineRefreshTimer.value) {
        refreshCountdown.value = Math.ceil(klineRefreshTimer.value.countdown / 1000)
      }
      updateTradingStatus()
    }, 1000)
  }
  
  // 停止倒计时
  const stopCountdown = function() {
    if (countdownInterval) {
      clearInterval(countdownInterval)
      countdownInterval = null
    }
    refreshCountdown.value = 0
  }
  
  // 切换实时刷新
  const toggleRealtimeRefresh = function() {
    realtimeRefreshEnabled.value = !realtimeRefreshEnabled.value
    
    if (realtimeRefreshEnabled.value) {
      startKlineRefresh()
      startPlanRefresh()
    } else {
      stopKlineRefresh()
      stopPlanRefresh()
    }
  }
  
  // 手动刷新
  const manualRefresh = async function() {
    await silentRefreshKlineData()
    await loadTradingPlans()
    
    // 重置定时器
    if (klineRefreshTimer.value) {
      klineRefreshTimer.value.refresh()
    }
  }
  
  // 获取刷新状态文本
  const getRefreshStatusText = function() {
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

  // 窗口大小变化处理
  const handleResize = function() {
    if (chartInstance) {
      chartInstance.resize()
    }
  }

  // 生命周期
  onMounted(async function() {
    await loadStrategies()
    await loadAvailableModels()
    await loadChartData()
    await loadTradingPlans()
    window.addEventListener('resize', handleResize)
    
    // 初始化交易状态
    updateTradingStatus()
    
    // 启动实时刷新
    if (realtimeRefreshEnabled.value) {
      startKlineRefresh()
      startPlanRefresh()
    }
    
    console.log('[策略中心] 初始化完成，交易状态:', tradingStatus.value?.statusText)
  })
  
  onUnmounted(function() {
    window.removeEventListener('resize', handleResize)
    
    // 停止所有定时器
    stopKlineRefresh()
    stopPlanRefresh()
    stopCountdown()
    
    if (chartInstance) {
      chartInstance.dispose()
      chartInstance = null
    }
    
    console.log('[策略中心] 组件已卸载，定时器已清理')
  })

  // 返回
  return {
    // 状态
    strategies,
    categories,
    selectedCategory,
    selectedStrategy,
    isLoading,
    isGenerating,
    isParsing,
    availableModels,
    modelLoadError,

// K线图
    chartContainer,
    chartStockCode,
    chartPeriod,
    chartData,
    isLoadingChart,
    chartError,
    currentIndicators,
    dataSource,
    periods,
    indicatorToggles,
    chartHeight,
    isDrawingMode,
    drawingTool,
    chartMarkers,
    chartDrawings,
    
    // 信号和形态
    detectedSignals,
    detectedPatterns,
    signalSummary,
    
    // 六脉神剑综合指标
    sixPulseData,
    sixPulseIndicators,
    sixPulseSummary,
    sixPulseChartData,
    
    // 机构大单
    largeOrderSignals,
    
    // 实时刷新状态
    realtimeRefreshEnabled,
    tradingStatus,
    refreshCountdown,
    lastRefreshTime,
    isAutoRefreshing,

    // 模态框
    showParseModal,
    showCreateModal,
    editingStrategy,
    showPriceMarkerModal,
    showCreatePlanModal,
    showPlanDetailModal,

    // 表单
    parseText,
    strategyForm,
    signalForm,
    signalResult,
    priceMarkerForm,
    planForm,

    // 交易计划
    tradingPlans,
    runningPlans,
    stoppedPlans,
    runningPlansCount,
    selectedPlanDetail,
    isCreatingPlan,

    // 计算属性
    filteredStrategies,

    // 方法
    loadStrategies,
    loadAvailableModels,
    selectStrategy,
    selectPeriod,
    loadChartData,
    renderChart,
    addMarker,
    addHorizontalLine,
    addSupportLine,
    addResistanceLine,
    markHighPoint,
    markLowPoint,
    markBuyPoint,
    markSellPoint,
    autoDetectKeyLevels,
    clearAllMarkers,
    getVolumeStatus,
    getVolumeClass,
    toggleDrawingMode,
    openPriceMarkerModal,
    addCustomPriceMarker,
    getChartScreenshot,
    handleParseStrategy,
    saveStrategy,
    editStrategy,
    deleteStrategy,
    resetStrategyForm,
    generateSignal,

    // 交易计划方法
    loadTradingPlans,
    openCreatePlanModal,
    createTradingPlan,
    startPlan,
    pausePlan,
    stopPlan,
    deletePlan,
    viewPlanDetail,
    getStatusLabel,
    
    // 实时刷新方法
    toggleRealtimeRefresh,
    manualRefresh,
    getRefreshStatusText,
    startKlineRefresh,
    stopKlineRefresh,

// 辅助方法
    getSourceLabel,
    getIndicatorTypeLabel,
    getRSIClass,
    getActionIcon,
    getActionText,
    parseStrategy,
    captureChart,
    clearMarkers,
    addPriceMarkerFromForm,
    getSignalMarkPoints,
    getPatternMarkPoints,

    // 常量
    INDICATOR_TYPES,
    TRADING_ACTIONS
  }
}
