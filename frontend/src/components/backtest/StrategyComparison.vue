<template>
  <div class="comparison-container">
    <div class="comparison-header">
      <h2>📊 策略对比分析</h2>
      <button @click="$emit('close')" class="close-btn">✕</button>
    </div>

    <div class="comparison-content">
      <!-- 策略选择 -->
      <div class="strategy-selector">
        <h3>选择对比策略</h3>
        <div class="strategy-checkboxes">
          <label v-for="strategy in availableStrategies" :key="strategy.id" class="checkbox-item">
            <input 
              type="checkbox" 
              :value="strategy.id"
              v-model="selectedStrategyIds"
              :disabled="selectedStrategyIds.length >= 4 && !selectedStrategyIds.includes(strategy.id)"
            />
            <span>{{ strategy.name }}</span>
          </label>
        </div>
        <small>最多选择4个策略进行对比</small>
      </div>

      <!-- 对比结果 -->
      <div v-if="comparisonResults.length > 0" class="comparison-results">
        <!-- 性能指标对比表 -->
        <div class="metrics-table">
          <h3>📈 关键指标对比</h3>
          <table>
            <thead>
              <tr>
                <th>策略名称</th>
                <th>总收益率</th>
                <th>年化收益率</th>
                <th>最大回撤</th>
                <th>夏普比率</th>
                <th>胜率</th>
                <th>盈亏比</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="result in comparisonResults" :key="result.strategyId">
                <td>
                  <div class="strategy-name">
                    <span class="color-dot" :style="{background: result.color}"></span>
                    {{ result.strategyName }}
                  </div>
                </td>
                <td :class="getValueClass(result.metrics.totalReturn)">
                  {{ formatPercent(result.metrics.totalReturn) }}
                </td>
                <td :class="getValueClass(result.metrics.annualReturn)">
                  {{ formatPercent(result.metrics.annualReturn) }}
                </td>
                <td class="negative">
                  {{ formatPercent(result.metrics.maxDrawdown) }}
                </td>
                <td>{{ result.metrics.sharpeRatio.toFixed(2) }}</td>
                <td>{{ formatPercent(result.metrics.winRate) }}</td>
                <td>{{ result.metrics.profitFactor.toFixed(2) }}</td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 净值曲线对比图 -->
        <div class="curve-comparison">
          <h3>📉 净值曲线对比</h3>
          <canvas ref="comparisonChart"></canvas>
        </div>

        <!-- 雷达图对比 -->
        <div class="radar-comparison">
          <h3>🎯 综合评分雷达图</h3>
          <canvas ref="radarChart"></canvas>
        </div>

        <!-- 交易统计对比 -->
        <div class="trade-stats">
          <h3>📊 交易统计</h3>
          <div class="stats-grid">
            <div v-for="result in comparisonResults" :key="result.strategyId" class="stat-card">
              <h4>
                <span class="color-dot" :style="{background: result.color}"></span>
                {{ result.strategyName }}
              </h4>
              <div class="stat-row">
                <span class="stat-label">总交易次数:</span>
                <span class="stat-value">{{ result.metrics.totalTrades }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">盈利次数:</span>
                <span class="stat-value positive">{{ result.metrics.winTrades }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">亏损次数:</span>
                <span class="stat-value negative">{{ result.metrics.lossTrades }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">平均持仓天数:</span>
                <span class="stat-value">{{ result.metrics.avgHoldingDays?.toFixed(1) || '-' }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">最大连续盈利:</span>
                <span class="stat-value">{{ result.metrics.maxConsecutiveWins || 0 }}</span>
              </div>
              <div class="stat-row">
                <span class="stat-label">最大连续亏损:</span>
                <span class="stat-value">{{ result.metrics.maxConsecutiveLosses || 0 }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 加载状态 -->
      <div v-if="isLoading" class="loading-state">
        <div class="spinner"></div>
        <p>正在运行策略对比...</p>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="comparison-footer">
      <button @click="runComparison" :disabled="selectedStrategyIds.length < 2 || isLoading" class="btn-primary">
        运行对比
      </button>
      <button @click="exportResults" :disabled="comparisonResults.length === 0" class="btn-secondary">
        导出报告
      </button>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'StrategyComparison',
  props: {
    stockCode: {
      type: String,
      required: true
    },
    dateRange: {
      type: Array,
      required: true
    },
    initialCapital: {
      type: Number,
      default: 100000
    }
  },
  emits: ['close'],
  setup(props) {
    const availableStrategies = ref([])
    const selectedStrategyIds = ref([])
    const comparisonResults = ref([])
    const isLoading = ref(false)
    
    const comparisonChart = ref(null)
    const radarChart = ref(null)

    // 策略颜色
    const strategyColors = [
      '#4CAF50',
      '#2196F3',
      '#FF9800',
      '#9C27B0'
    ]

    // 加载可用策略
    const loadStrategies = async () => {
      try {
        const response = await axios.get('/api/backtest/strategies')
        availableStrategies.value = response.data.strategies
      } catch (error) {
        console.error('加载策略失败:', error)
      }
    }

    // 运行对比
    const runComparison = async () => {
      if (selectedStrategyIds.value.length < 2) {
        alert('请至少选择2个策略进行对比')
        return
      }

      isLoading.value = true
      comparisonResults.value = []

      try {
        const response = await axios.post('/api/backtest/compare', {
          stock_code: props.stockCode,
          strategy_ids: selectedStrategyIds.value,
          start_date: props.dateRange[0],
          end_date: props.dateRange[1],
          initial_capital: props.initialCapital
        })

        // 处理结果并分配颜色
        comparisonResults.value = response.data.results.map((result, index) => ({
          ...result,
          color: strategyColors[index % strategyColors.length]
        }))

        // 绘制图表
        drawComparisonChart()
        drawRadarChart()

      } catch (error) {
        console.error('策略对比失败:', error)
        alert('策略对比失败：' + (error.response?.data?.detail || error.message))
      } finally {
        isLoading.value = false
      }
    }

    // 绘制净值曲线对比图
    const drawComparisonChart = () => {
      if (!comparisonChart.value || comparisonResults.value.length === 0) return

      const canvas = comparisonChart.value
      const ctx = canvas.getContext('2d')
      const rect = canvas.getBoundingClientRect()
      
      canvas.width = rect.width
      canvas.height = rect.height
      
      // 清空画布
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      const padding = { top: 20, right: 20, bottom: 40, left: 60 }
      const chartWidth = canvas.width - padding.left - padding.right
      const chartHeight = canvas.height - padding.top - padding.bottom
      
      // 找出所有数据的范围
      let minValue = Infinity
      let maxValue = -Infinity
      let maxLength = 0
      
      comparisonResults.value.forEach(result => {
        if (result.equityCurve) {
          const values = result.equityCurve.map(d => d.value)
          minValue = Math.min(minValue, ...values)
          maxValue = Math.max(maxValue, ...values)
          maxLength = Math.max(maxLength, result.equityCurve.length)
        }
      })
      
      const valueRange = maxValue - minValue
      
      // 绘制网格
      ctx.strokeStyle = '#f0f0f0'
      ctx.lineWidth = 1
      
      for (let i = 0; i <= 5; i++) {
        const y = padding.top + (chartHeight / 5) * i
        ctx.beginPath()
        ctx.moveTo(padding.left, y)
        ctx.lineTo(padding.left + chartWidth, y)
        ctx.stroke()
      }
      
      // 绘制坐标轴
      ctx.strokeStyle = '#333'
      ctx.lineWidth = 2
      
      ctx.beginPath()
      ctx.moveTo(padding.left, padding.top)
      ctx.lineTo(padding.left, padding.top + chartHeight)
      ctx.lineTo(padding.left + chartWidth, padding.top + chartHeight)
      ctx.stroke()
      
      // 绘制每个策略的曲线
      comparisonResults.value.forEach((result) => {
        if (!result.equityCurve) return
        
        ctx.strokeStyle = result.color
        ctx.lineWidth = 2
        ctx.beginPath()
        
        result.equityCurve.forEach((point, i) => {
          const x = padding.left + (chartWidth / (maxLength - 1)) * i
          const y = padding.top + chartHeight - ((point.value - minValue) / valueRange) * chartHeight
          
          if (i === 0) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        })
        
        ctx.stroke()
      })
    }

    // 绘制雷达图
    const drawRadarChart = () => {
      if (!radarChart.value || comparisonResults.value.length === 0) return

      const canvas = radarChart.value
      const ctx = canvas.getContext('2d')
      const rect = canvas.getBoundingClientRect()
      
      canvas.width = rect.width
      canvas.height = rect.height
      
      const centerX = canvas.width / 2
      const centerY = canvas.height / 2
      const radius = Math.min(centerX, centerY) - 40
      
      // 定义维度
      const dimensions = [
        { label: '收益率', key: 'totalReturn' },
        { label: '夏普比率', key: 'sharpeRatio' },
        { label: '胜率', key: 'winRate' },
        { label: '稳定性', key: 'stability' },
        { label: '回撤控制', key: 'drawdownControl' }
      ]
      
      const numDimensions = dimensions.length
      const angleStep = (Math.PI * 2) / numDimensions
      
      // 清空画布
      ctx.clearRect(0, 0, canvas.width, canvas.height)
      
      // 绘制网格
      ctx.strokeStyle = '#e0e0e0'
      ctx.lineWidth = 1
      
      for (let level = 1; level <= 5; level++) {
        ctx.beginPath()
        for (let i = 0; i <= numDimensions; i++) {
          const angle = angleStep * i - Math.PI / 2
          const x = centerX + Math.cos(angle) * (radius * level / 5)
          const y = centerY + Math.sin(angle) * (radius * level / 5)
          
          if (i === 0) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        }
        ctx.stroke()
      }
      
      // 绘制轴线和标签
      ctx.strokeStyle = '#999'
      ctx.fillStyle = '#666'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'
      
      dimensions.forEach((dim, i) => {
        const angle = angleStep * i - Math.PI / 2
        const x = centerX + Math.cos(angle) * radius
        const y = centerY + Math.sin(angle) * radius
        
        ctx.beginPath()
        ctx.moveTo(centerX, centerY)
        ctx.lineTo(x, y)
        ctx.stroke()
        
        // 绘制标签
        const labelX = centerX + Math.cos(angle) * (radius + 20)
        const labelY = centerY + Math.sin(angle) * (radius + 20)
        ctx.fillText(dim.label, labelX, labelY)
      })
      
      // 绘制数据
      comparisonResults.value.forEach((result) => {
        const values = dimensions.map(dim => {
          const value = result.metrics[dim.key]
          if (dim.key === 'stability') {
            return 1 - (result.metrics.volatility || 0)
          } else if (dim.key === 'drawdownControl') {
            return 1 - Math.abs(result.metrics.maxDrawdown || 0)
          }
          return Math.min(1, Math.max(0, value || 0))
        })
        
        ctx.strokeStyle = result.color
        ctx.fillStyle = result.color + '30'
        ctx.lineWidth = 2
        
        ctx.beginPath()
        values.forEach((value, i) => {
          const angle = angleStep * i - Math.PI / 2
          const x = centerX + Math.cos(angle) * (radius * value)
          const y = centerY + Math.sin(angle) * (radius * value)
          
          if (i === 0) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        })
        ctx.closePath()
        ctx.fill()
        ctx.stroke()
      })
    }

    // 导出结果
    const exportResults = () => {
      if (comparisonResults.value.length === 0) return
      
      // 构建CSV内容
      let csv = '策略名称,总收益率,年化收益率,最大回撤,夏普比率,胜率,盈亏比,总交易次数\n'
      
      comparisonResults.value.forEach(result => {
        csv += `${result.strategyName},`
        csv += `${(result.metrics.totalReturn * 100).toFixed(2)}%,`
        csv += `${(result.metrics.annualReturn * 100).toFixed(2)}%,`
        csv += `${(result.metrics.maxDrawdown * 100).toFixed(2)}%,`
        csv += `${result.metrics.sharpeRatio.toFixed(2)},`
        csv += `${(result.metrics.winRate * 100).toFixed(2)}%,`
        csv += `${result.metrics.profitFactor.toFixed(2)},`
        csv += `${result.metrics.totalTrades}\n`
      })
      
      // 下载文件
      const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
      const link = document.createElement('a')
      link.href = URL.createObjectURL(blob)
      link.download = `策略对比_${props.stockCode}_${new Date().toISOString().split('T')[0]}.csv`
      link.click()
    }

    // 工具函数
    const formatPercent = (value) => {
      if (!value && value !== 0) return '-'
      return (value * 100).toFixed(2) + '%'
    }

    const getValueClass = (value) => {
      if (!value) return ''
      return value > 0 ? 'positive' : value < 0 ? 'negative' : ''
    }

    onMounted(() => {
      loadStrategies()
    })

    return {
      availableStrategies,
      selectedStrategyIds,
      comparisonResults,
      isLoading,
      comparisonChart,
      radarChart,
      runComparison,
      exportResults,
      formatPercent,
      getValueClass
    }
  }
}
</script>

<style scoped>
.comparison-container {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 90%;
  max-width: 1200px;
  max-height: 90vh;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0,0,0,0.15);
  display: flex;
  flex-direction: column;
  z-index: 1000;
}

.comparison-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #e0e0e0;
}

.comparison-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: #f5f5f5;
  border-radius: 50%;
  cursor: pointer;
  font-size: 18px;
  color: #666;
  transition: all 0.3s;
}

.close-btn:hover {
  background: #e0e0e0;
}

.comparison-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.strategy-selector {
  margin-bottom: 30px;
}

.strategy-selector h3 {
  margin: 0 0 15px;
  font-size: 16px;
  color: #333;
}

.strategy-checkboxes {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 10px;
}

.checkbox-item {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-item input {
  cursor: pointer;
}

.checkbox-item span {
  font-size: 14px;
  color: #666;
}

/* 对比结果样式 */
.comparison-results {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.metrics-table {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.metrics-table h3 {
  margin: 0 0 15px;
  font-size: 16px;
  color: #333;
}

.metrics-table table {
  width: 100%;
  border-collapse: collapse;
}

.metrics-table th,
.metrics-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
}

.metrics-table th {
  background: white;
  font-weight: 500;
  color: #666;
  font-size: 13px;
}

.metrics-table td {
  background: white;
  font-size: 14px;
  color: #333;
}

.strategy-name {
  display: flex;
  align-items: center;
  gap: 8px;
}

.color-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.positive {
  color: #4CAF50;
}

.negative {
  color: #f44336;
}

/* 图表样式 */
.curve-comparison,
.radar-comparison {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.curve-comparison h3,
.radar-comparison h3 {
  margin: 0 0 15px;
  font-size: 16px;
  color: #333;
}

.curve-comparison canvas {
  width: 100%;
  height: 300px;
  background: white;
  border-radius: 4px;
}

.radar-comparison canvas {
  width: 100%;
  height: 300px;
  background: white;
  border-radius: 4px;
}

/* 交易统计 */
.trade-stats {
  background: #f8f9fa;
  padding: 20px;
  border-radius: 8px;
}

.trade-stats h3 {
  margin: 0 0 15px;
  font-size: 16px;
  color: #333;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 15px;
}

.stat-card {
  background: white;
  padding: 15px;
  border-radius: 6px;
  border: 1px solid #e0e0e0;
}

.stat-card h4 {
  margin: 0 0 12px;
  font-size: 14px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.stat-row {
  display: flex;
  justify-content: space-between;
  padding: 6px 0;
  border-bottom: 1px solid #f0f0f0;
}

.stat-row:last-child {
  border-bottom: none;
}

.stat-label {
  font-size: 13px;
  color: #666;
}

.stat-value {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

/* 加载状态 */
.loading-state {
  text-align: center;
  padding: 40px;
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

/* 页脚 */
.comparison-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #e0e0e0;
}

.btn-primary,
.btn-secondary {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
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

.btn-secondary:hover:not(:disabled) {
  background: #e8e8e8;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
