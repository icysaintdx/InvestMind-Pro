<template>
  <div class="strategy-view">
    <!-- 顶部工具栏 -->
    <div class="toolbar">
      <div class="toolbar-left">
        <el-input
          v-model="stockCode"
          placeholder="输入股票代码"
          style="width: 150px"
          @keyup.enter="loadStockData"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
        <el-button type="primary" @click="loadStockData" :loading="loading.stock">
          加载数据
        </el-button>
        <el-divider direction="vertical" />
        <el-select v-model="selectedPeriod" placeholder="周期" style="width: 100px">
          <el-option label="日线" value="daily" />
          <el-option label="周线" value="weekly" />
          <el-option label="月线" value="monthly" />
          <el-option label="60分钟" value="60min" />
          <el-option label="30分钟" value="30min" />
        </el-select>
      </div>
      <div class="toolbar-right">
        <el-button @click="showParseDialog = true">
          <el-icon><Document /></el-icon>
          解析策略
        </el-button>
        <el-button @click="showStrategyDrawer = true">
          <el-icon><Setting /></el-icon>
          策略管理
        </el-button>
        <el-button type="success" @click="runAnalysis" :loading="loading.analysis" :disabled="!selectedStrategy">
          <el-icon><VideoPlay /></el-icon>
          执行分析
        </el-button>
      </div>
    </div>

    <!-- 主内容区 -->
    <div class="main-content">
      <!-- 左侧：K线图和指标 -->
      <div class="chart-section">
        <div class="chart-header">
          <div class="stock-info" v-if="stockInfo">
            <span class="stock-name">{{ stockInfo.name }}</span>
            <span class="stock-code">{{ stockInfo.code }}</span>
            <span class="stock-price" :class="priceChangeClass">
              {{ stockInfo.price }}
              <span class="change">{{ stockInfo.change > 0 ? '+' : '' }}{{ stockInfo.change }}%</span>
            </span>
          </div>
          <div class="indicator-toggles">
            <el-checkbox-group v-model="activeIndicators" size="small">
              <el-checkbox-button label="MA">均线</el-checkbox-button>
              <el-checkbox-button label="MACD">MACD</el-checkbox-button>
              <el-checkbox-button label="KDJ">KDJ</el-checkbox-button>
              <el-checkbox-button label="RSI">RSI</el-checkbox-button>
              <el-checkbox-button label="BOLL">布林带</el-checkbox-button>
              <el-checkbox-button label="VOL">成交量</el-checkbox-button>
            </el-checkbox-group>
          </div>
        </div>
        
        <!-- K线图容器 -->
        <div class="chart-container" ref="chartContainer">
          <div id="kline-chart" style="width: 100%; height: 500px;"></div>
        </div>
        
        <!-- 图表工具栏 -->
        <div class="chart-tools">
          <el-button-group size="small">
            <el-button @click="chartTool = 'cursor'" :type="chartTool === 'cursor' ? 'primary' : ''">
              光标
            </el-button>
            <el-button @click="chartTool = 'line'" :type="chartTool === 'line' ? 'primary' : ''">
              趋势线
            </el-button>
            <el-button @click="chartTool = 'horizontal'" :type="chartTool === 'horizontal' ? 'primary' : ''">
              水平线
            </el-button>
          </el-button-group>
          <el-button size="small" @click="captureChart">
            <el-icon><Camera /></el-icon>
            截图分析
          </el-button>
          <el-button size="small" @click="clearAnnotations">
            <el-icon><Delete /></el-icon>
            清除标注
          </el-button>
        </div>
      </div>

      <!-- 右侧：策略和分析结果 -->
      <div class="analysis-section">
        <!-- 当前策略 -->
        <el-card class="strategy-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>当前策略</span>
              <el-button link type="primary" @click="showStrategySelector = true">
                更换策略
              </el-button>
            </div>
          </template>
          <div v-if="selectedStrategy" class="selected-strategy">
            <div class="strategy-icon">{{ selectedStrategy.icon }}</div>
            <div class="strategy-info">
              <div class="strategy-name">{{ selectedStrategy.name }}</div>
              <div class="strategy-category">
                <el-tag size="small" :type="getCategoryType(selectedStrategy.category)">
                  {{ getCategoryName(selectedStrategy.category) }}
                </el-tag>
              </div>
              <div class="strategy-desc">{{ selectedStrategy.description }}</div>
            </div>
          </div>
          <el-empty v-else description="请选择策略" :image-size="60" />
        </el-card>

        <!-- 分析结果 -->
        <el-card class="result-card" shadow="hover" v-if="analysisResult">
          <template #header>
            <div class="card-header">
              <span>分析结果</span>
              <span class="result-time">{{ analysisResult.timestamp }}</span>
            </div>
          </template>
          
          <!-- 交易信号 -->
          <div class="signal-section">
            <div class="signal-badge" :style="{ backgroundColor: getSignalColor(analysisResult.signal) }">
              {{ getSignalText(analysisResult.signal) }}
            </div>
            <div class="confidence">
              置信度: {{ formatConfidence(analysisResult.confidence) }}
            </div>
          </div>

          <!-- 交易指令 -->
          <div class="trade-instruction" v-if="analysisResult.trade_instruction">
            <el-descriptions :column="2" size="small" border>
              <el-descriptions-item label="操作">
                <el-tag :type="getActionType(analysisResult.trade_instruction.action)">
                  {{ getSignalText(analysisResult.trade_instruction.action) }}
                </el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="建议价格">
                {{ analysisResult.trade_instruction.price || '-' }}
              </el-descriptions-item>
              <el-descriptions-item label="仓位比例">
                {{ formatPercent(analysisResult.trade_instruction.quantity_pct) }}
              </el-descriptions-item>
              <el-descriptions-item label="止损价">
                <span class="stop-loss">{{ analysisResult.trade_instruction.stop_loss || '-' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="止盈价">
                <span class="take-profit">{{ analysisResult.trade_instruction.take_profit || '-' }}</span>
              </el-descriptions-item>
              <el-descriptions-item label="风险等级">
                <el-tag :type="getRiskType(analysisResult.risk_assessment?.level)">
                  {{ analysisResult.risk_assessment?.level || '-' }}
                </el-tag>
              </el-descriptions-item>
            </el-descriptions>
            <div class="trade-reason" v-if="analysisResult.trade_instruction.reason">
              <strong>交易理由：</strong>
              {{ analysisResult.trade_instruction.reason }}
            </div>
          </div>

          <!-- 关键价位 -->
          <div class="key-levels" v-if="analysisResult.key_levels">
            <div class="level-group">
              <span class="level-label">支撑位：</span>
              <el-tag v-for="level in analysisResult.key_levels.support" :key="'s'+level" size="small" type="success">
                {{ level }}
              </el-tag>
            </div>
            <div class="level-group">
              <span class="level-label">阻力位：</span>
              <el-tag v-for="level in analysisResult.key_levels.resistance" :key="'r'+level" size="small" type="danger">
                {{ level }}
              </el-tag>
            </div>
          </div>

          <!-- 详细分析 -->
          <el-collapse v-model="activeCollapse">
            <el-collapse-item title="技术面分析" name="technical">
              {{ analysisResult.analysis?.technical || '暂无' }}
            </el-collapse-item>
            <el-collapse-item title="基本面分析" name="fundamental">
              {{ analysisResult.analysis?.fundamental || '暂无' }}
            </el-collapse-item>
            <el-collapse-item title="风险评估" name="risk">
              <div v-if="analysisResult.risk_assessment">
                <div class="risk-factors" v-if="analysisResult.risk_assessment.factors?.length">
                  <strong>风险因素：</strong>
                  <ul>
                    <li v-for="(factor, idx) in analysisResult.risk_assessment.factors" :key="idx">
                      {{ factor }}
                    </li>
                  </ul>
                </div>
                <div class="risk-suggestions" v-if="analysisResult.risk_assessment.suggestions?.length">
                  <strong>控制建议：</strong>
                  <ul>
                    <li v-for="(suggestion, idx) in analysisResult.risk_assessment.suggestions" :key="idx">
                      {{ suggestion }}
                    </li>
                  </ul>
                </div>
              </div>
            </el-collapse-item>
          </el-collapse>
        </el-card>

        <!-- 历史信号 -->
        <el-card class="history-card" shadow="hover">
          <template #header>
            <div class="card-header">
              <span>历史信号</span>
              <el-button link type="primary" @click="loadSignalHistory">刷新</el-button>
            </div>
          </template>
          <el-timeline v-if="signalHistory.length > 0">
            <el-timeline-item
              v-for="signal in signalHistory"
              :key="signal.id"
              :timestamp="signal.timestamp"
              :color="getSignalColor(signal.signal)"
            >
              <div class="history-item">
                <span class="history-signal">{{ getSignalText(signal.signal) }}</span>
                <span class="history-symbol">{{ signal.symbol }}</span>
                <span class="history-confidence">{{ formatConfidence(signal.confidence) }}</span>
              </div>
            </el-timeline-item>
          </el-timeline>
          <el-empty v-else description="暂无历史信号" :image-size="40" />
        </el-card>
      </div>
    </div>

    <!-- 策略选择器对话框 -->
    <el-dialog v-model="showStrategySelector" title="选择策略" width="800px">
      <div class="strategy-selector">
        <el-tabs v-model="selectorTab">
          <el-tab-pane label="我的策略" name="my">
            <el-table :data="myStrategies" @row-click="selectStrategy" highlight-current-row style="cursor: pointer;">
              <el-table-column prop="icon" label="" width="50">
                <template #default="{ row }">
                  <span class="strategy-icon-small">{{ row.icon }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="策略名称" />
              <el-table-column prop="category" label="分类" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ getCategoryName(row.category) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" show-overflow-tooltip />
            </el-table>
          </el-tab-pane>
          <el-tab-pane label="预设策略" name="preset">
            <div class="preset-categories">
              <el-radio-group v-model="presetCategory" size="small">
                <el-radio-button label="">全部</el-radio-button>
                <el-radio-button label="technical">技术分析</el-radio-button>
                <el-radio-button label="fundamental">价值投资</el-radio-button>
                <el-radio-button label="institutional">机构跟踪</el-radio-button>
                <el-radio-button label="folk">民间战法</el-radio-button>
                <el-radio-button label="ai">AI策略</el-radio-button>
              </el-radio-group>
            </div>
            <el-table :data="filteredPresetStrategies" @row-click="selectPresetStrategy" highlight-current-row style="cursor: pointer;">
              <el-table-column prop="icon" label="" width="50">
                <template #default="{ row }">
                  <span class="strategy-icon-small">{{ row.icon }}</span>
                </template>
              </el-table-column>
              <el-table-column prop="name" label="策略名称" />
              <el-table-column prop="category" label="分类" width="100">
                <template #default="{ row }">
                  <el-tag size="small">{{ getCategoryName(row.category) }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column prop="description" label="描述" show-overflow-tooltip />
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button size="small" type="primary" @click.stop="importStrategy(row)">
                    导入
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
          </el-tab-pane>
        </el-tabs>
      </div>
    </el-dialog>

    <!-- 策略管理抽屉 -->
    <el-drawer v-model="showStrategyDrawer" title="策略管理" size="600px">
      <div class="drawer-content">
        <el-button type="primary" @click="showParseDialog = true" style="margin-bottom: 16px;">
          <el-icon><Plus /></el-icon>
          添加新策略
        </el-button>
        <el-table :data="myStrategies" style="width: 100%">
          <el-table-column prop="icon" label="" width="50">
            <template #default="{ row }">
              <span class="strategy-icon-small">{{ row.icon }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="name" label="策略名称" />
          <el-table-column prop="category" label="分类" width="100">
            <template #default="{ row }">
              <el-tag size="small">{{ getCategoryName(row.category) }}</el-tag>
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150">
            <template #default="{ row }">
              <el-button size="small" @click="selectStrategy(row)">使用</el-button>
              <el-button size="small" type="danger" @click="deleteStrategyConfirm(row)">删除</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </el-drawer>

    <!-- 策略解析对话框 -->
    <el-dialog v-model="showParseDialog" title="解析策略文本" width="700px">
      <el-form label-position="top">
        <el-form-item label="策略描述">
          <el-input
            v-model="parseText"
            type="textarea"
            :rows="10"
            placeholder="请输入策略描述，例如：
当MACD金叉且RSI小于70时买入，
当MACD死叉或RSI大于80时卖出，
止损5%，止盈15%"
          />
        </el-form-item>
        <el-form-item label="选择模型">
          <el-select v-model="parseModelId" placeholder="选择分析模型" style="width: 100%">
            <el-option
              v-for="model in availableModels"
              :key="model.id"
              :label="model.name"
              :value="model.id"
            />
          </el-select>
          <div class="model-tip" v-if="!availableModels.length">
            <el-text type="warning">请先在模型管理中配置模型</el-text>
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showParseDialog = false">取消</el-button>
        <el-button type="primary" @click="parseStrategy" :loading="loading.parse" :disabled="!parseModelId">
          解析策略
        </el-button>
        <el-button type="success" @click="parseAndSave" :loading="loading.parse" :disabled="!parseModelId">
          解析并保存
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  Search, Setting, VideoPlay, Camera, Delete, Document, Plus
} from '@element-plus/icons-vue'
import * as echarts from 'echarts'
import {
  getStrategies,
  deleteStrategy,
  analyzeStock,
  analyzeWithImage,
  getStrategySignals,
  getPresetStrategies,
  importPresetStrategy,
  parseStrategyText,
  parseAndSaveStrategy
} from '@/api/strategy'

// ==================== 响应式数据 ====================

const stockCode = ref('')
const stockInfo = ref(null)
const selectedPeriod = ref('daily')

const chartContainer = ref(null)
let chartInstance = null
const activeIndicators = ref(['MA', 'VOL'])
const chartTool = ref('cursor')

const selectedStrategy = ref(null)
const myStrategies = ref([])
const presetStrategies = ref([])
const presetCategory = ref('')

const analysisResult = ref(null)
const signalHistory = ref([])
const activeCollapse = ref(['technical'])

const showStrategySelector = ref(false)
const showStrategyDrawer = ref(false)
const showParseDialog = ref(false)
const selectorTab = ref('my')
const loading = ref({
  stock: false,
  analysis: false,
  parse: false
})

const parseText = ref('')
const parseModelId = ref('')
const availableModels = ref([
  { id: 'deepseek', name: 'DeepSeek' },
  { id: 'qwen', name: '通义千问' },
  { id: 'gpt4', name: 'GPT-4' }
])

// ==================== 计算属性 ====================

const priceChangeClass = computed(() => {
  if (!stockInfo.value) return ''
  return stockInfo.value.change >= 0 ? 'price-up' : 'price-down'
})

const filteredPresetStrategies = computed(() => {
  if (!presetCategory.value) return presetStrategies.value
  return presetStrategies.value.filter(s => s.category === presetCategory.value)
})

// ==================== 方法 ====================

function getCategoryName(category) {
  const map = {
    technical: '技术分析',
    fundamental: '价值投资',
    institutional: '机构跟踪',
    folk: '民间战法',
    ai: 'AI策略'
  }
  return map[category] || category
}

function getCategoryType(category) {
  const map = {
    technical: 'primary',
    fundamental: 'success',
    institutional: 'warning',
    folk: 'info',
    ai: 'danger'
  }
  return map[category] || 'info'
}

function getSignalColor(signal) {
  const map = { BUY: '#52c41a', SELL: '#f5222d', HOLD: '#faad14' }
  return map[signal] || '#1890ff'
}

function getSignalText(signal) {
  const map = { BUY: '买入', SELL: '卖出', HOLD: '持有' }
  return map[signal] || signal
}

function formatConfidence(confidence) {
  return `${(confidence * 100).toFixed(1)}%`
}

function formatPercent(value) {
  if (!value) return '-'
  return `${(value * 100).toFixed(0)}%`
}

function getActionType(action) {
  const map = { BUY: 'success', SELL: 'danger', HOLD: 'warning' }
  return map[action] || 'info'
}

function getRiskType(level) {
  const map = { LOW: 'success', MEDIUM: 'warning', HIGH: 'danger' }
  return map[level] || 'info'
}

async function loadStockData() {
  if (!stockCode.value) {
    ElMessage.warning('请输入股票代码')
    return
  }
  
  loading.value.stock = true
  try {
    // 模拟数据
    stockInfo.value = {
      code: stockCode.value,
      name: '示例股票',
      price: 25.68,
      change: 2.35
    }
    initChart()
    ElMessage.success('数据加载成功')
  } catch (error) {
    ElMessage.error('加载数据失败: ' + error.message)
  } finally {
    loading.value.stock = false
  }
}

function initChart() {
  if (chartInstance) {
    chartInstance.dispose()
  }
  
  const chartDom = document.getElementById('kline-chart')
  if (!chartDom) return
  
  chartInstance = echarts.init(chartDom)
  
  // 生成模拟K线数据
  const dates = []
  const data = []
  const volumes = []
  let basePrice = 25
  
  for (let i = 0; i < 60; i++) {
    const date = new Date()
    date.setDate(date.getDate() - (60 - i))
    dates.push(date.toISOString().split('T')[0])
    
    const open = basePrice + (Math.random() - 0.5) * 2
    const close = open + (Math.random() - 0.5) * 2
    const high = Math.max(open, close) + Math.random() * 0.5
    const low = Math.min(open, close) - Math.random() * 0.5
    
    data.push([open.toFixed(2), close.toFixed(2), low.toFixed(2), high.toFixed(2)])
    volumes.push(Math.floor(Math.random() * 10000000))
    basePrice = close
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['K线', 'MA5', 'MA10', 'MA20']
    },
    grid: [
      { left: '10%', right: '8%', top: '10%', height: '50%' },
      { left: '10%', right: '8%', top: '65%', height: '20%' }
    ],
    xAxis: [
      { type: 'category', data: dates, boundaryGap: false },
      { type: 'category', gridIndex: 1, data: dates, boundaryGap: false, axisLabel: { show: false } }
    ],
    yAxis: [
      { scale: true },
      { scale: true, gridIndex: 1, splitNumber: 2 }
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1], start: 50, end: 100 },
      { show: true, xAxisIndex: [0, 1], type: 'slider', top: '90%', start: 50, end: 100 }
    ],
    series: [
      {
        name: 'K线',
        type: 'candlestick',
        data: data,
        itemStyle: {
          color: '#ef232a',
          color0: '#14b143',
          borderColor: '#ef232a',
          borderColor0: '#14b143'
        }
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: volumes,
        itemStyle: {
          color: function(params) {
            const klineData = data[params.dataIndex]
            return parseFloat(klineData[1]) >= parseFloat(klineData[0]) ? '#ef232a' : '#14b143'
          }
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
  
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
}

async function captureChart() {
  if (!chartInstance) {
    ElMessage.warning('请先加载股票数据')
    return
  }
  
  if (!selectedStrategy.value) {
    ElMessage.warning('请先选择策略')
    return
  }
  
  try {
    const imageData = chartInstance.getDataURL({
      type: 'png',
      pixelRatio: 2,
      backgroundColor: '#fff'
    })
    
    const response = await fetch(imageData)
    const blob = await response.blob()
    
    const formData = new FormData()
    formData.append('strategy_id', selectedStrategy.value.id)
    formData.append('symbol', stockCode.value)
    formData.append('image', blob, 'chart.png')
    
    loading.value.analysis = true
    const result = await analyzeWithImage(formData)
    
    if (result.success) {
      analysisResult.value = result.data
      ElMessage.success('图像分析完成')
    }
  } catch (error) {
    ElMessage.error('截图分析失败: ' + error.message)
  } finally {
    loading.value.analysis = false
  }
}

function clearAnnotations() {
  ElMessage.info('标注已清除')
}

async function runAnalysis() {
  if (!selectedStrategy.value) {
    ElMessage.warning('请先选择策略')
    return
  }
  
  if (!stockCode.value) {
    ElMessage.warning('请先输入股票代码')
    return
  }
  
  loading.value.analysis = true
  try {
    const response = await analyzeStock({
      strategy_id: selectedStrategy.value.id,
      symbol: stockCode.value,
      include_news: true,
      include_chart: false
    })
    
    if (response.success) {
      analysisResult.value = response.data
      ElMessage.success('分析完成')
    }
  } catch (error) {
    ElMessage.error('分析失败: ' + error.message)
  } finally {
    loading.value.analysis = false
  }
}

function selectStrategy(row) {
  selectedStrategy.value = row
  showStrategySelector.value = false
  showStrategyDrawer.value = false
  ElMessage.success(`已选择策略: ${row.name}`)
}

function selectPresetStrategy(row) {
  selectedStrategy.value = row
  showStrategySelector.value = false
  ElMessage.success(`已选择预设策略: ${row.name}`)
}

async function importStrategy(strategy) {
  try {
    await ElMessageBox.confirm(`确定要导入策略"${strategy.name}"吗？`, '确认导入')
    const response = await importPresetStrategy(strategy.name)
    if (response.success) {
      ElMessage.success('策略导入成功')
      loadMyStrategies()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('导入失败: ' + error.message)
    }
  }
}

async function deleteStrategyConfirm(strategy) {
  try {
    await ElMessageBox.confirm(`确定要删除策略"${strategy.name}"吗？`, '确认删除', { type: 'warning' })
    const response = await deleteStrategy(strategy.id)
    if (response.success) {
      ElMessage.success('策略删除成功')
      loadMyStrategies()
      if (selectedStrategy.value?.id === strategy.id) {
        selectedStrategy.value = null
      }
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + error.message)
    }
  }
}

async function loadMyStrategies() {
  try {
    const response = await getStrategies()
    if (response.success) {
      myStrategies.value = response.data
    }
  } catch (error) {
    console.error('加载策略失败:', error)
  }
}

async function loadPresetStrategies() {
  try {
    const response = await getPresetStrategies()
    if (response.success) {
      presetStrategies.value = response.data
    }
  } catch (error) {
    console.error('加载预设策略失败:', error)
  }
}

async function loadSignalHistory() {
  if (!selectedStrategy.value) return
  
  try {
    const response = await getStrategySignals(selectedStrategy.value.id, { page_size: 10 })
    if (response.success) {
      signalHistory.value = response.data
    }
  } catch (error) {
    console.error('加载信号历史失败:', error)
  }
}
async function parseStrategy() {
  if (!parseText.value.trim()) {
    ElMessage.warning('请输入策略描述')
    return
  }
  
  loading.value.parse = true
  try {
    const response = await parseStrategyText({
      text: parseText.value,
      model_id: parseModelId.value
    })
    
    if (response.success) {
      ElMessage.success('策略解析成功')
      console.log('解析结果:', response.data)
    }
  } catch (error) {
    ElMessage.error('解析失败: ' + error.message)
  } finally {
    loading.value.parse = false
  }
}

async function parseAndSave() {
  if (!parseText.value.trim()) {
    ElMessage.warning('请输入策略描述')
    return
  }
  
  loading.value.parse = true
  try {
    const response = await parseAndSaveStrategy({
      text: parseText.value,
      model_id: parseModelId.value
    })
    
    if (response.success) {
      ElMessage.success('策略解析并保存成功')
      showParseDialog.value = false
      parseText.value = ''
      loadMyStrategies()
    }
  } catch (error) {
    ElMessage.error('解析保存失败: ' + error.message)
  } finally {
    loading.value.parse = false
  }
}

// ==================== 生命周期 ====================

onMounted(() => {
  loadMyStrategies()
  loadPresetStrategies()
})

onUnmounted(() => {
  if (chartInstance) {
    chartInstance.dispose()
  }
  window.removeEventListener('resize', () => {})
})

// 监听策略变化，加载信号历史
watch(selectedStrategy, (newVal) => {
  if (newVal) {
    loadSignalHistory()
  }
})
</script>

<style scoped>
.strategy-view {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fff;
  border-bottom: 1px solid #e4e7ed;
}

.toolbar-left,
.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.main-content {
  flex: 1;
  display: flex;
  gap: 16px;
  padding: 16px;
  overflow: hidden;
}

.chart-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  min-width: 0;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.stock-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.stock-name {
  font-size: 18px;
  font-weight: 600;
}

.stock-code {
  color: #909399;
}

.stock-price {
  font-size: 20px;
  font-weight: 600;
}

.stock-price.price-up {
  color: #f5222d;
}

.stock-price.price-down {
  color: #52c41a;
}

.stock-price .change {
  font-size: 14px;
  margin-left: 8px;
}

.chart-container {
  flex: 1;
  min-height: 400px;
}

.chart-tools {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-top: 12px;
  border-top: 1px solid #e4e7ed;
}

.analysis-section {
  width: 400px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow-y: auto;
}

.strategy-card,
.result-card,
.history-card {
  flex-shrink: 0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-time {
  font-size: 12px;
  color: #909399;
}

.selected-strategy {
  display: flex;
  gap: 12px;
}

.strategy-icon {
  font-size: 32px;
}

.strategy-info {
  flex: 1;
}

.strategy-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.strategy-category {
  margin-bottom: 8px;
}

.strategy-desc {
  font-size: 13px;
  color: #606266;
  line-height: 1.5;
}

.signal-section {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
}

.signal-badge {
  padding: 8px 24px;
  border-radius: 4px;
  color: #fff;
  font-size: 18px;
  font-weight: 600;
}

.confidence {
  font-size: 14px;
  color: #606266;
}

.trade-instruction {
  margin-bottom: 16px;
}

.trade-reason {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
}

.stop-loss {
  color: #52c41a;
}

.take-profit {
  color: #f5222d;
}

.key-levels {
  margin-bottom: 16px;
}

.level-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.level-label {
  font-size: 13px;
  color: #606266;
  min-width: 60px;
}

.history-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.history-signal {
  font-weight: 600;
}

.history-symbol {
  color: #606266;
}

.history-confidence {
  color: #909399;
  font-size: 12px;
}

.strategy-selector {
  min-height: 400px;
}

.preset-categories {
  margin-bottom: 16px;
}

.strategy-icon-small {
  font-size: 20px;
}

.drawer-content {
  padding: 0 16px;
}

.model-tip {
  margin-top: 8px;
}

.risk-factors,
.risk-suggestions {
  margin-bottom: 12px;
}

.risk-factors ul,
.risk-suggestions ul {
  margin: 8px 0 0 20px;
  padding: 0;
}

.risk-factors li,
.risk-suggestions li {
  margin-bottom: 4px;
  color: #606266;
}
</style>
  