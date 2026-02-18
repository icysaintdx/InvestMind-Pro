// 策略中心视图 - 脚本部分
// 这个文件包含完整的script和style部分

export const scriptContent = `
<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import * as echarts from 'echarts'
import axios from 'axios'
import { 
  getStrategies, 
  getStrategyDetail, 
  createStrategy, 
  updateStrategy, 
  deleteStrategy as deleteStrategyApi,
  parseStrategyText, 
  generateSignal as generateSignalApi,
  STRATEGY_CATEGORIES,
  INDICATOR_TYPES,
  TRADING_ACTIONS
} from '@/api/strategyCenter'
import { getKlineData, calculateIndicators } from '@/api/stock'

export default {
  name: 'StrategyCenterView',
  setup() {
    // 状态
    const strategies = ref([])
    const categories = ref([])
    const selectedCategory = ref(null)
    const selectedStrategy = ref(null)
    const isLoading = ref(false)
    const isGenerating = ref(false)
    const isParsing = ref(false)
    const availableModels = ref([])

    // K线图相关
    const chartContainer = ref(null)
    const chartInstance = ref(null)
    const chartStockCode = ref('')
    const chartPeriod = ref('daily')
    const chartData = ref(null)
    const isLoadingChart = ref(false)
    const currentIndicators = ref({})

    // 模态框
    const showParseModal = ref(false)
    const showCreateModal = ref(false)
    const editingStrategy = ref(null)

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

    // 计算属性
    const filteredStrategies = computed(() => {
      if (!selectedCategory.value) return strategies.value
      return strategies.value.filter(s => s.category === selectedCategory.value)
    })

    // 方法
    const loadStrategies = async () => {
      isLoading.value = true
      try {
        const result = await getStrategies()
        if (result.success) {
          strategies.value = result.strategies
          categories.value = result.categories
        }
      } catch (error) {
        console.error('加载策略失败:', error)
      } finally {
        isLoading.value = false
      }
    }

    const loadAvailableModels = async () => {
      try {
        const response = await axios.get('/api/config/agents')
        if (response.data) {
          const models = []
          if (response.data.selected_models) {
            response.data.selected_models.forEach(m => {
              models.push({ id: m.id || m.name, name: m.name || m.id })
            })
          }
          if (models.length === 0) {
            models.push(
              { id: 'deepseek-chat', name: 'DeepSeek Chat' },
              { id: 'qwen-plus', name: '通义千问 Plus' },
              { id: 'gpt-4', name: 'GPT-4' }
            )
          }
          availableModels.value = models
          if (models.length > 0) {
            signalForm.value.model = models[0].id
          }
        }
      } catch (error) {
        console.error('加载模型列表失败:', error)
        availableModels.value = [
          { id: 'deepseek-chat', name: 'DeepSeek Chat' },
          { id: 'qwen-plus', name: '通义千问 Plus' }
        ]
        signalForm.value.model = 'deepseek-chat'
      }
    }

    const selectStrategy = async (strategy) => {
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

    const loadChartData = async () => {
      if (!chartStockCode.value) return
      
      isLoadingChart.value = true
      try {
        const result = await getKlineData(chartStockCode.value, {
          period: chartPeriod.value,
          count: 120
        })
        
        if (result.success && result.data) {
          chartData.value = result.data
          signalForm.value.stockCode = chartStockCode.value
          
          await nextTick()
          renderChart(result.data.kline)
        }
      } catch (error) {
        console.error('加载K线数据失败:', error)
      } finally {
        isLoadingChart.value = false
      }
    }

    const renderChart = (klineData) => {
      if (!chartContainer.value || !klineData?.length) return
      
      const indicators = calculateIndicators(klineData, ['MA', 'MACD', 'RSI', 'BOLL', 'Volume'])
      
      const lastIdx = klineData.length - 1
      currentIndicators.value = {
        MA5: indicators.MA5?.[lastIdx],
        MA10: indicators.MA10?.[lastIdx],
        MA20: indicators.MA20?.[lastIdx],
        RSI: indicators.RSI?.[lastIdx],
        MACD: indicators.MACD?.MACD?.[lastIdx]
      }
      
      if (!chartInstance.value) {
        chartInstance.value = echarts.init(chartContainer.value)
      }
      
      const dates = klineData.map(d => d.date)
      const ohlc = klineData.map(d => [d.open, d.close, d.low, d.high])
      const volumes = klineData.map((d, i) => ({
        value: d.volume,
        itemStyle: { color: d.close >= d.open ? '#ef4444' : '#10b981' }
      }))
      
      const option = {
        backgroundColor: 'transparent',
        animation: false,
        tooltip: {
          trigger: 'axis',
          axisPointer: { type: 'cross' },
          backgroundColor: 'rgba(30, 41, 59, 0.9)',
          borderColor: 'rgba(51, 65, 85, 0.5)',
          textStyle: { color: '#e2e8f0' }
        },
        legend: {
          data: ['K线', 'MA5', 'MA10', 'MA20'],
          top: 10,
          textStyle: { color: '#94a3b8' }
        },
        grid: [
          { left: '10%', right: '8%', top: '15%', height: '50%' },
          { left: '10%', right: '8%', top: '70%', height: '15%' }
        ],
        xAxis: [
          {
            type: 'category',
            data: dates,
            gridIndex: 0,
            axisLine: { lineStyle: { color: '#334155' } },
            axisLabel: { color: '#64748b' }
          },
          {
            type: 'category',
            data: dates,
            gridIndex: 1,
            axisLine: { lineStyle: { color: '#334155' } },
            axisLabel: { show: false }
          }
        ],
        yAxis: [
          {
            type: 'value',
            gridIndex: 0,
            splitLine: { lineStyle: { color: 'rgba(51, 65, 85, 0.3)' } },
            axisLine: { lineStyle: { color: '#334155' } },
            axisLabel: { color: '#64748b' }
          },
          {
            type: 'value',
            gridIndex: 1,
            splitLine: { show: false },
            axisLine: { lineStyle: { color: '#334155' } },
            axisLabel: { show: false }
          }
        ],
        dataZoom: [
          { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
          { type: 'slider', xAxisIndex: [0, 1], start: 50, end: 100, height: 20, bottom: 5 }
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            data: ohlc,
            xAxisIndex: 0,
            yAxisIndex: 0,
            itemStyle: {
              color: '#ef4444',
              color0: '#10b981',
              borderColor: '#ef4444',
              borderColor0: '#10b981'
            }
          },
          {
            name: 'MA5',
            type: 'line',
            data: indicators.MA5,
            xAxisIndex: 0,
            yAxisIndex: 0,
            smooth: true,
            lineStyle: { width: 1, color: '#f59e0b' },
            symbol: 'none'
          },
          {
            name: 'MA10',
            type: 'line',
            data: indicators.MA10,
            xAxisIndex: 0,
            yAxisIndex: 0,
            smooth: true,
            lineStyle: { width: 1, color: '#3b82f6' },
            symbol: 'none'
          },
          {
            name: 'MA20',
            type: 'line',
            data: indicators.MA20,
            xAxisIndex: 0,
            yAxisIndex: 0,
            smooth: true,
            lineStyle: { width: 1, color: '#8b5cf6' },
            symbol: 'none'
          },
          {
            name: '成交量',
            type: 'bar',
            data: volumes,
            xAxisIndex: 1,
            yAxisIndex: 1
          }
        ]
      }
      
      chartInstance.value.setOption(option)
    }

    const generateSignal = async () => {
      if (!signalForm.value.stockCode || !selectedStrategy.value) return
      
      isGenerating.value = true
      signalResult.value = null
      
      try {
        const result = await generateSignalApi({
          stock_code: signalForm.value.stockCode,
          strategy_id: selectedStrategy.value.id,
          include_chart: signalForm.value.includeChart,
          include_news: signalForm.value.includeNews
        })
        
        if (result.success) {
          signalResult.value = result.signal
        }
      } catch (error) {
        console.error('生成信号失败:', error)
      } finally {
        isGenerating.value = false
      }
    }

    const parseStrategy = async () => {
      if (!parseText.value) return
      
      isParsing.value = true
      try {
        const result = await parseStrategyText({ text: parseText.value })
        if (result.success && result.parsed_strategy) {
          strategyForm.value = {
            ...result.parsed_strategy,
            source: 'llm_parsed'
          }
          showParseModal.value = false
          showCreateModal.value = true
        }
      } catch (error) {
        console.error('解析策略失败:', error)
      } finally {
        isParsing.value = false
      }
    }

    const saveStrategy = async () => {
      try {
        let result
        if (editingStrategy.value) {
          result = await updateStrategy(editingStrategy.value.id, strategyForm.value)
        } else {
          result = await createStrategy(strategyForm.value)
        }
        
        if (result.success) {
          showCreateModal.value = false
          editingStrategy.value = null
          resetForm()
          await loadStrategies()
        }
      } catch (error) {
        console.error('保存策略失败:', error)
      }
    }

    const editStrategy = () => {
      if (!selectedStrategy.value) return
      editingStrategy.value = selectedStrategy.value
      strategyForm.value = { ...selectedStrategy.value }
      showCreateModal.value = true
    }

    const deleteStrategy = async () => {
      if (!selectedStrategy.value || selectedStrategy.value.source === 'preset') return
      
      if (confirm('确定要删除这个策略吗？')) {
        try {
          const result = await deleteStrategyApi(selectedStrategy.value.id)
          if (result.success) {
            selectedStrategy.value = null
            await loadStrategies()
          }
        } catch (error) {
          console.error('删除策略失败:', error)
        }
      }
    }

    const resetForm = () => {
      strategyForm.value = {
        name: '',
        description: '',
        category: 'custom',
        indicators: [],
        entry_conditions: [],
        exit_conditions: [],
        risk_params: { stop_loss: 0.05, take_profit: 0.15, max_position: 0.3 }
      }
      parseText.value = ''
    }

    const getSourceLabel = (source) => {
      const labels = { preset: '预设', custom: '自定义', llm_parsed: 'AI解析' }
      return labels[source] || source
    }

    const getIndicatorTypeLabel = (type) => {
      return INDICATOR_TYPES[type]?.label || type
    }

    const getActionIcon = (action) => {
      return TRADING_ACTIONS[action]?.icon || '⏸️'
    }

    const getActionText = (action) => {
      return TRADING_ACTIONS[action]?.label || action
    }

    const getRSIClass = (rsi) => {
      if (!rsi) return ''
      if (rsi > 70) return 'overbought'
      if (rsi < 30) return 'oversold'
      return 'neutral'
    }

    const handleResize = () => {
      if (chartInstance.value) {
        chartInstance.value.resize()
      }
    }

    onMounted(() => {
      loadStrategies()
      loadAvailableModels()
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
      if (chartInstance.value) {
        chartInstance.value.dispose()
      }
    })

    return {
      strategies, categories, selectedCategory, selectedStrategy, filteredStrategies,
      isLoading, isGenerating, isParsing, availableModels,
      chartContainer, chartStockCode, chartPeriod, chartData, isLoadingChart, currentIndicators,
      showParseModal, showCreateModal, editingStrategy,
      parseText, strategyForm, signalForm, signalResult,
      loadStrategies, selectStrategy, loadChartData, generateSignal, parseStrategy,
      saveStrategy, editStrategy, deleteStrategy,
      getSourceLabel, getIndicatorTypeLabel, getActionIcon, getActionText, getRSIClass
    }
  }
}
<\/script>
`