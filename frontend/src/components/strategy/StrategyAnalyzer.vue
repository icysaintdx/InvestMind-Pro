<template>
  <div class="strategy-analyzer">
    <!-- 左侧：股票选择和K线图 -->
    <div class="left-panel">
      <div class="stock-selector">
        <h3>选择股票</h3>
        <el-autocomplete
          v-model="stockInput"
          :fetch-suggestions="searchStock"
          placeholder="输入股票代码或名称"
          @select="handleStockSelect"
          style="width: 100%"
        >
          <template #default="{ item }">
            <div class="stock-item">
              <span class="code">{{ item.code }}</span>
              <span class="name">{{ item.name }}</span>
            </div>
          </template>
        </el-autocomplete>
        
        <div v-if="selectedStock" class="selected-stock-info">
          <div class="stock-header">
            <span class="stock-name">{{ selectedStock.name }}</span>
            <span class="stock-code">{{ selectedStock.code }}</span>
          </div>
          <div class="stock-price">
            <span class="price" :class="priceChangeClass">{{ marketData.price?.toFixed(2) || '--' }}</span>
            <span class="change" :class="priceChangeClass">
              {{ marketData.change_pct >= 0 ? '+' : '' }}{{ marketData.change_pct?.toFixed(2) || '--' }}%
            </span>
          </div>
        </div>
      </div>
      
      <!-- K线图区域 -->
      <div class="kline-section">
        <div class="section-header">
          <h3>K线图</h3>
          <div class="kline-actions">
            <el-radio-group v-model="klinePeriod" size="small">
              <el-radio-button label="daily">日K</el-radio-button>
              <el-radio-button label="weekly">周K</el-radio-button>
              <el-radio-button label="monthly">月K</el-radio-button>
            </el-radio-group>
            <el-button size="small" @click="captureKline">
              <el-icon><Camera /></el-icon>
              截图分析
            </el-button>
          </div>
        </div>
        <div ref="klineChartRef" class="kline-chart"></div>
        
        <!-- 上传K线图 -->
        <div class="upload-kline">
          <el-upload
            :auto-upload="false"
            :show-file-list="false"
            accept="image/*"
            @change="handleKlineUpload"
          >
            <el-button size="small" type="text">
              <el-icon><Upload /></el-icon>
              上传K线图分析
            </el-button>
          </el-upload>
        </div>
      </div>
      
      <!-- 技术指标显示 -->
      <div class="indicators-section">
        <h3>技术指标</h3>
        <div class="indicator-grid">
          <div class="indicator-item" v-for="(value, key) in technicalIndicators" :key="key">
            <span class="indicator-name">{{ getIndicatorName(key) }}</span>
            <span class="indicator-value" :class="getIndicatorClass(key, value)">
              {{ formatIndicatorValue(key, value) }}
            </span>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 右侧：策略分析和信号 -->
    <div class="right-panel">
      <!-- 策略信息 -->
      <div class="strategy-info">
        <h3>当前策略: {{ strategy.name }}</h3>
        <p class="strategy-desc">{{ strategy.description }}</p>
        <div class="strategy-conditions">
          <h4>入场条件</h4>
          <div class="condition-list">
            <div 
              v-for="(ind, idx) in strategy.indicators?.required || []" 
              :key="idx"
              class="condition-item"
              :class="{ 'satisfied': conditionResults[ind.name]?.satisfied }"
            >
              <el-icon v-if="conditionResults[ind.name]?.satisfied"><Check /></el-icon>
              <el-icon v-else><Close /></el-icon>
              <span class="condition-text">
                {{ ind.name_cn || ind.name }} {{ ind.operator }} {{ ind.value }}
              </span>
              <span class="condition-value">
                (当前: {{ technicalIndicators[ind.name] ?? fundamentalData[ind.name] ?? '--' }})
              </span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 分析按钮 -->
      <div class="analyze-actions">
        <el-button 
          type="primary" 
          size="large" 
          @click="runAnalysis" 
          :loading="analyzing"
          :disabled="!selectedStock"
        >
          <el-icon><DataAnalysis /></el-icon>
          运行策略分析
        </el-button>
        <el-button @click="evaluateConditions" :disabled="!selectedStock">
          <el-icon><List /></el-icon>
          评估条件
        </el-button>
      </div>
      
      <!-- 分析结果 -->
      <div v-if="analysisResult" class="analysis-result">
        <div class="result-header" :class="signalClass">
          <div class="signal-badge">
            <el-icon v-if="analysisResult.signal === 'buy'"><Top /></el-icon>
            <el-icon v-else-if="analysisResult.signal === 'sell'"><Bottom /></el-icon>
            <el-icon v-else><Minus /></el-icon>
            <span>{{ signalText }}</span>
          </div>
          <div class="signal-metrics">
            <div class="metric">
              <span class="label">信号强度</span>
              <el-progress 
                :percentage="(analysisResult.signal_strength || 0) * 100" 
                :color="signalColor"
                :stroke-width="8"
              />
            </div>
            <div class="metric">
              <span class="label">置信度</span>
              <el-progress 
                :percentage="(analysisResult.confidence || 0) * 100" 
                :stroke-width="8"
              />
            </div>
          </div>
        </div>
        
        <!-- 推荐操作 -->
        <div class="recommended-action" v-if="analysisResult.recommended_action">
          <h4>推荐操作</h4>
          <div class="action-details">
            <div class="action-row">
              <span class="label">操作类型:</span>
              <el-tag :type="getActionTagType(analysisResult.recommended_action.action)">
                {{ getActionText(analysisResult.recommended_action.action) }}
              </el-tag>
            </div>
            <div class="action-row" v-if="analysisResult.recommended_action.target_price">
              <span class="label">目标价格:</span>
              <span class="value">¥{{ analysisResult.recommended_action.target_price?.toFixed(2) }}</span>
            </div>
            <div class="action-row" v-if="analysisResult.recommended_action.position_ratio">
              <span class="label">建议仓位:</span>
              <span class="value">{{ (analysisResult.recommended_action.position_ratio * 100).toFixed(0) }}%</span>
            </div>
            <div class="action-row" v-if="analysisResult.recommended_action.stop_loss_price">
              <span class="label">止损价:</span>
              <span class="value loss">¥{{ analysisResult.recommended_action.stop_loss_price?.toFixed(2) }}</span>
            </div>
            <div class="action-row" v-if="analysisResult.recommended_action.take_profit_price">
              <span class="label">止盈价:</span>
              <span class="value profit">¥{{ analysisResult.recommended_action.take_profit_price?.toFixed(2) }}</span>
            </div>
            <div class="action-row">
              <span class="label">紧急程度:</span>
              <el-tag :type="getUrgencyType(analysisResult.recommended_action.urgency)" size="small">
                {{ getUrgencyText(analysisResult.recommended_action.urgency) }}
              </el-tag>
            </div>
          </div>
        </div>
        
        <!-- 风险评估 -->
        <div class="risk-assessment" v-if="analysisResult.risk_assessment">
          <h4>风险评估</h4>
          <div class="risk-level">
            <span class="label">风险等级:</span>
            <el-tag :type="getRiskType(analysisResult.risk_assessment.risk_level)">
              {{ getRiskText(analysisResult.risk_assessment.risk_level) }}
            </el-tag>
          </div>
          <div class="risk-factors" v-if="analysisResult.risk_assessment.risk_factors?.length">
            <span class="label">风险因素:</span>
            <ul>
              <li v-for="(factor, idx) in analysisResult.risk_assessment.risk_factors" :key="idx">
                {{ factor }}
              </li>
            </ul>
          </div>
        </div>
        
        <!-- 分析推理 -->
        <div class="reasoning" v-if="analysisResult.reasoning">
          <h4>分析推理</h4>
          <p>{{ analysisResult.reasoning }}</p>
        </div>
        
        <!-- 总结 -->
        <div class="summary" v-if="analysisResult.summary">
          <el-alert :title="analysisResult.summary" :type="signalAlertType" :closable="false" />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { ElMessage } from 'element-plus'
import { 
  Camera, Upload, Check, Close, DataAnalysis, List, 
  Top, Bottom, Minus 
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import { strategyApi } from '@/api/strategy'
import { stockApi } from '@/api/stock'

const props = defineProps({
  strategy: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['signal-generated'])

// 状态
const stockInput = ref('')
const selectedStock = ref(null)
const klinePeriod = ref('daily')
const analyzing = ref(false)

const marketData = ref({})
const technicalIndicators = ref({})
const fundamentalData = ref({})
const conditionResults = ref({})
const analysisResult = ref(null)

const klineChartRef = ref(null)
let klineChart = null

// 计算属性
const priceChangeClass = computed(() => {
  if (!marketData.value.change_pct) return ''
  return marketData.value.change_pct >= 0 ? 'up' : 'down'
})

const signalClass = computed(() => {
  if (!analysisResult.value) return ''
  return `signal-${analysisResult.value.signal}`
})

const signalText = computed(() => {
  const map = { buy: '买入信号', sell: '卖出信号', hold: '持有观望' }
  return map[analysisResult.value?.signal] || '未知'
})

const signalColor = computed(() => {
  const map = { buy: '#67c23a', sell: '#f56c6c', hold: '#909399' }
  return map[analysisResult.value?.signal] || '#909399'
})

const signalAlertType = computed(() => {
  const map = { buy: 'success', sell: 'error', hold: 'info' }
  return map[analysisResult.value?.signal] || 'info'
})

// 搜索股票
const searchStock = async (query, cb) => {
  if (!query) {
    cb([])
    return
  }
  try {
    const res = await stockApi.search(query)
    cb(res.data || [])
  } catch (error) {
    cb([])
  }
}

// 选择股票
const handleStockSelect = async (item) => {
  selectedStock.value = item
  await loadStockData(item.code)
}

// 加载股票数据
const loadStockData = async (code) => {
  try {
    // 加载行情数据
    const quoteRes = await stockApi.getQuote(code)
    if (quoteRes.success) {
      marketData.value = quoteRes.data
    }
    
    // 加载技术指标
    const techRes = await stockApi.getTechnicalIndicators(code)
    if (techRes.success) {
      technicalIndicators.value = techRes.data
    }
    
    // 加载基本面数据
    const fundRes = await stockApi.getFundamentals(code)
    if (fundRes.success) {
      fundamentalData.value = fundRes.data
    }
    
    // 加载K线数据并绘图
    await loadKlineData(code)
    
    // 评估条件
    await evaluateConditions()
  } catch (error) {
    ElMessage.error('加载股票数据失败: ' + error.message)
  }
}

// 加载K线数据
const loadKlineData = async (code) => {
  try {
    const res = await stockApi.getKline(code, klinePeriod.value)
    if (res.success && res.data) {
      renderKlineChart(res.data)
    }
  } catch (error) {
    console.error('加载K线数据失败:', error)
  }
}

// 渲染K线图
const renderKlineChart = (data) => {
  if (!klineChartRef.value) return
  
  if (!klineChart) {
    klineChart = echarts.init(klineChartRef.value)
  }
  
  const dates = data.map(d => d.date)
  const ohlc = data.map(d => [d.open, d.close, d.low, d.high])
  const volumes = data.map(d => d.volume)
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    grid: [
      { left: '10%', right: '10%', top: '10%', height: '50%' },
      { left: '10%', right: '10%', top: '65%', height: '20%' }
    ],
    xAxis: [
      { type: 'category', data: dates, gridIndex: 0 },
      { type: 'category', data: dates, gridIndex: 1 }
    ],
    yAxis: [
      { scale: true, gridIndex: 0 },
      { scale: true, gridIndex: 1 }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: ohlc,
        itemStyle: {
          color: '#ef5350',
          color0: '#26a69a',
          borderColor: '#ef5350',
          borderColor0: '#26a69a'
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
            return ohlc[idx][1] >= ohlc[idx][0] ? '#ef5350' : '#26a69a'
          }
        }
      }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      { type: 'slider', xAxisIndex: [0, 1], start: 50, end: 100, top: '90%' }
    ]
  }
  
  klineChart.setOption(option)
}

// 截图K线图
const captureKline = async () => {
  if (!klineChart) {
    ElMessage.warning('请先加载K线图')
    return
  }
  
  const base64 = klineChart.getDataURL({
    type: 'png',
    pixelRatio: 2,
    backgroundColor: '#fff'
  })
  
  // 移除前缀
  const imageData = base64.replace(/^data:image\/\w+;base64,/, '')
  
  // 调用K线分析API
  analyzing.value = true
  try {
    const res = await strategyApi.analyzeKline(imageData, props.strategy.strategy_id)
    if (res.success) {
      ElMessage.success('K线分析完成')
      // 将分析结果合并到分析中
    }
  } catch (error) {
    ElMessage.error('K线分析失败: ' + error.message)
  } finally {
    analyzing.value = false
  }
}

// 上传K线图
const handleKlineUpload = async (file) => {
  const reader = new FileReader()
  reader.onload = async (e) => {
    const base64 = e.target.result.replace(/^data:image\/\w+;base64,/, '')
    analyzing.value = true
    try {
      const res = await strategyApi.analyzeKline(base64, props.strategy.strategy_id)
      if (res.success) {
        ElMessage.success('K线分析完成')
      }
    } catch (error) {
      ElMessage.error('K线分析失败: ' + error.message)
    } finally {
      analyzing.value = false
    }
  }
  reader.readAsDataURL(file.raw)
}

// 评估条件
const evaluateConditions = async () => {
  if (!selectedStock.value) return
  
  try {
    const allIndicators = { ...technicalIndicators.value, ...fundamentalData.value }
    const res = await strategyApi.evaluateConditions(props.strategy.strategy_id, allIndicators)
    if (res.success) {
      // 转换为以指标名为key的对象
      const results = {}
      for (const r of res.data.condition_results || []) {
        results[r.indicator] = r
      }
      conditionResults.value = results
    }
  } catch (error) {
    console.error('评估条件失败:', error)
  }
}

// 运行分析
const runAnalysis = async () => {
  if (!selectedStock.value) {
    ElMessage.warning('请先选择股票')
    return
  }
  
  analyzing.value = true
  try {
    const res = await strategyApi.generateSignal({
      strategy_id: props.strategy.strategy_id,
      stock_code: selectedStock.value.code,
      stock_name: selectedStock.value.name,
      market_data: marketData.value,
      technical_indicators: technicalIndicators.value,
      fundamental_data: fundamentalData.value
    })
    
    if (res.success) {
      analysisResult.value = res.data
      emit('signal-generated', res.data)
      ElMessage.success('分析完成')
    }
  } catch (error) {
    ElMessage.error('分析失败: ' + error.message)
  } finally {
    analyzing.value = false
  }
}

// 辅助函数
const getIndicatorName = (key) => {
  const names = {
    MA5: '5日均线', MA10: '10日均线', MA20: '20日均线', MA60: '60日均线',
    MACD_DIF: 'MACD DIF', MACD_DEA: 'MACD DEA',
    RSI: 'RSI', KDJ_K: 'KDJ K', KDJ_D: 'KDJ D',
    PE: '市盈率', PB: '市净率', ROE: 'ROE'
  }
  return names[key] || key
}

const formatIndicatorValue = (key, value) => {
  if (value === null || value === undefined) return '--'
  if (typeof value === 'number') {
    return value.toFixed(2)
  }
  return value
}

const getIndicatorClass = (key, value) => {
  // 根据指标类型和值返回样式类
  return ''
}

const getActionTagType = (action) => {
  const map = { buy: 'success', sell: 'danger', hold: 'info' }
  return map[action] || 'info'
}

const getActionText = (action) => {
  const map = { buy: '买入', sell: '卖出', hold: '持有' }
  return map[action] || action
}

const getUrgencyType = (urgency) => {
  const map = { high: 'danger', medium: 'warning', low: 'info' }
  return map[urgency] || 'info'
}

const getUrgencyText = (urgency) => {
  const map = { high: '紧急', medium: '一般', low: '不急' }
  return map[urgency] || urgency
}

const getRiskType = (level) => {
  const map = { high: 'danger', medium: 'warning', low: 'success' }
  return map[level] || 'info'
}

const getRiskText = (level) => {
  const map = { high: '高风险', medium: '中等风险', low: '低风险' }
  return map[level] || level
}

// 监听K线周期变化
watch(klinePeriod, () => {
  if (selectedStock.value) {
    loadKlineData(selectedStock.value.code)
  }
})

// 生命周期
onMounted(() => {
  window.addEventListener('resize', () => {
    klineChart?.resize()
  })
})

onUnmounted(() => {
  klineChart?.dispose()
})
</script>

<style scoped lang="scss">
.strategy-analyzer {
  display: flex;
  gap: 24px;
  height: 700px;
  
  .left-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
    
    .stock-selector {
      h3 {
        margin: 0 0 12px 0;
        font-size: 14px;
      }
      
      .selected-stock-info {
        margin-top: 12px;
        padding: 12px;
        background: #f5f7fa;
        border-radius: 4px;
        
        .stock-header {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          
          .stock-name {
            font-weight: 600;
          }
          
          .stock-code {
            color: #999;
            font-size: 12px;
          }
        }
        
        .stock-price {
          .price {
            font-size: 24px;
            font-weight: 600;
            margin-right: 12px;
          }
          
          .change {
            font-size: 14px;
          }
          
          .up {
            color: #f56c6c;
          }
          
          .down {
            color: #67c23a;
          }
        }
      }
    }
    
    .kline-section {
      .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        h3 {
          margin: 0;
          font-size: 14px;
        }
        
        .kline-actions {
          display: flex;
          gap: 8px;
        }
      }
      
      .kline-chart {
        height: 300px;
        background: #fafafa;
        border-radius: 4px;
      }
      
      .upload-kline {
        margin-top: 8px;
        text-align: center;
      }
    }
    
    .indicators-section {
      h3 {
        margin: 0 0 12px 0;
        font-size: 14px;
      }
      
      .indicator-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 8px;
        
        .indicator-item {
          display: flex;
          justify-content: space-between;
          padding: 8px;
          background: #f5f7fa;
          border-radius: 4px;
          font-size: 12px;
          
          .indicator-name {
            color: #666;
          }
          
          .indicator-value {
            font-weight: 600;
          }
        }
      }
    }
  }
  
  .right-panel {
    width: 450px;
    display: flex;
    flex-direction: column;
    gap: 16px;
    overflow-y: auto;
    
    .strategy-info {
      h3 {
        margin: 0 0 8px 0;
        font-size: 16px;
      }
      
      .strategy-desc {
        color: #666;
        font-size: 13px;
        margin: 0 0 16px 0;
      }
      
      .strategy-conditions {
        h4 {
          margin: 0 0 8px 0;
          font-size: 13px;
          color: #333;
        }
        
        .condition-list {
          .condition-item {
            display: flex;
            align-items: center;
            gap: 8px;
            padding: 8px;
            margin-bottom: 4px;
            background: #fef0f0;
            border-radius: 4px;
            font-size: 12px;
            
            &.satisfied {
              background: #f0f9eb;
            }
            
            .el-icon {
              font-size: 14px;
            }
            
            .condition-value {
              color: #999;
              margin-left: auto;
            }
          }
        }
      }
    }
    
    .analyze-actions {
      display: flex;
      gap: 12px;
    }
    
    .analysis-result {
      .result-header {
        padding: 16px;
        border-radius: 8px;
        margin-bottom: 16px;
        
        &.signal-buy {
          background: linear-gradient(135deg, #f0f9eb 0%, #e1f3d8 100%);
        }
        
        &.signal-sell {
          background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%);
        }
        
        &.signal-hold {
          background: linear-gradient(135deg, #f4f4f5 0%, #e9e9eb 100%);
        }
        
        .signal-badge {
          display: flex;
          align-items: center;
          gap: 8px;
          font-size: 20px;
          font-weight: 600;
          margin-bottom: 12px;
          
          .el-icon {
            font-size: 24px;
          }
        }
        
        .signal-metrics {
          display: flex;
          gap: 24px;
          
          .metric {
            flex: 1;
            
            .label {
              display: block;
              font-size: 12px;
              color: #666;
              margin-bottom: 4px;
            }
          }
        }
      }
      
      .recommended-action, .risk-assessment, .reasoning {
        padding: 12px;
        background: #f5f7fa;
        border-radius: 4px;
        margin-bottom: 12px;
        
        h4 {
          margin: 0 0 12px 0;
          font-size: 13px;
        }
        
        .action-details {
          .action-row {
            display: flex;
            align-items: center;
            margin-bottom: 8px;
            
            .label {
              width: 80px;
              color: #666;
              font-size: 12px;
            }
            
            .value {
              font-weight: 600;
              
              &.profit {
                color: #67c23a;
              }
              
              &.loss {
                color: #f56c6c;
              }
            }
          }
        }
        
        .risk-level {
          display: flex;
          align-items: center;
          gap: 8px;
          margin-bottom: 8px;
          
          .label {
            color: #666;
            font-size: 12px;
          }
        }
        
        .risk-factors {
          .label {
            display: block;
            color: #666;
            font-size: 12px;
            margin-bottom: 4px;
          }
          
          ul {
            margin: 0;
            padding-left: 20px;
            font-size: 12px;
          }
        }
        
        p {
          margin: 0;
          font-size: 13px;
          line-height: 1.6;
        }
      }
      
      .summary {
        margin-top: 12px;
      }
    }
  }
}

.stock-item {
  display: flex;
  gap: 12px;
  
  .code {
    color: #409eff;
    font-weight: 500;
  }
  
  .name {
    color: #666;
  }
}
</style>