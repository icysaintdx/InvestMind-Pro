<template>
  <div class="equity-curve-container">
    <canvas ref="chartCanvas"></canvas>
    
    <!-- 图例 -->
    <div class="chart-legend">
      <div class="legend-item">
        <span class="legend-color equity"></span>
        <span>净值曲线</span>
      </div>
      <div class="legend-item">
        <span class="legend-color benchmark"></span>
        <span>基准收益</span>
      </div>
      <div class="legend-item">
        <span class="legend-marker buy">▲</span>
        <span>买入信号</span>
      </div>
      <div class="legend-item">
        <span class="legend-marker sell">▼</span>
        <span>卖出信号</span>
      </div>
    </div>

    <!-- 统计信息 -->
    <div class="chart-stats" v-if="statistics">
      <div class="stat-item">
        <span class="stat-label">期初净值:</span>
        <span class="stat-value">¥{{ formatAmount(statistics.initialValue) }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">期末净值:</span>
        <span class="stat-value">¥{{ formatAmount(statistics.finalValue) }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">最高净值:</span>
        <span class="stat-value">¥{{ formatAmount(statistics.maxValue) }}</span>
      </div>
      <div class="stat-item">
        <span class="stat-label">最大回撤:</span>
        <span class="stat-value negative">{{ formatPercent(statistics.maxDrawdown) }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'

export default {
  name: 'EquityCurve',
  props: {
    data: {
      type: Array,
      required: true
    },
    trades: {
      type: Array,
      default: () => []
    },
    showBenchmark: {
      type: Boolean,
      default: true
    }
  },
  setup(props) {
    const chartCanvas = ref(null)
    let animationId = null
    // eslint-disable-next-line no-unused-vars
    let chart = null

    // 计算统计信息
    const statistics = computed(() => {
      if (!props.data || props.data.length === 0) return null

      const values = props.data.map(d => d.value || d.equity || d.portfolio_value || 0)
      const initialValue = values[0]
      const finalValue = values[values.length - 1]
      const maxValue = Math.max(...values)
      
      // 计算最大回撤
      let maxDrawdown = 0
      let peak = values[0]
      
      for (const value of values) {
        if (value > peak) {
          peak = value
        }
        const drawdown = (peak - value) / peak
        if (drawdown > maxDrawdown) {
          maxDrawdown = drawdown
        }
      }
      
      return {
        initialValue,
        finalValue,
        maxValue,
        maxDrawdown
      }
    })

    // 绘制图表
    const drawChart = () => {
      if (!chartCanvas.value) return
      
      const canvas = chartCanvas.value
      const ctx = canvas.getContext('2d')
      const rect = canvas.getBoundingClientRect()
      
      // 设置画布大小
      canvas.width = rect.width * window.devicePixelRatio
      canvas.height = rect.height * window.devicePixelRatio
      ctx.scale(window.devicePixelRatio, window.devicePixelRatio)
      
      // 清空画布
      ctx.clearRect(0, 0, rect.width, rect.height)
      
      if (!props.data || props.data.length === 0) {
        drawEmptyState(ctx, rect)
        return
      }
      
      // 计算绘图参数
      const padding = { top: 20, right: 20, bottom: 40, left: 70 }
      const chartWidth = rect.width - padding.left - padding.right
      const chartHeight = rect.height - padding.top - padding.bottom
      
      // 数据范围
      const values = props.data.map(d => d.value || d.equity || d.portfolio_value || 0)
      const minValue = Math.min(...values) * 0.95
      const maxValue = Math.max(...values) * 1.05
      const valueRange = maxValue - minValue
      
      // 绘制网格
      drawGrid(ctx, padding, chartWidth, chartHeight)
      
      // 绘制坐标轴
      drawAxes(ctx, padding, chartWidth, chartHeight, minValue, maxValue, props.data)
      
      // 绘制净值曲线
      drawEquityCurve(ctx, padding, chartWidth, chartHeight, props.data, minValue, valueRange)
      
      // 绘制基准线（如果有）
      if (props.showBenchmark && props.data[0]?.benchmark) {
        drawBenchmarkCurve(ctx, padding, chartWidth, chartHeight, props.data, minValue, valueRange)
      }
      
      // 绘制交易信号
      if (props.trades && props.trades.length > 0) {
        drawTradeSignals(ctx, padding, chartWidth, chartHeight, props.trades, props.data, minValue, valueRange)
      }
    }

    // 绘制空状态
    const drawEmptyState = (ctx, rect) => {
      ctx.fillStyle = '#999'
      ctx.font = '14px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText('暂无数据', rect.width / 2, rect.height / 2)
    }

    // 绘制网格
    const drawGrid = (ctx, padding, width, height) => {
      ctx.strokeStyle = '#f0f0f0'
      ctx.lineWidth = 1
      
      // 横向网格线
      for (let i = 0; i <= 5; i++) {
        const y = padding.top + (height / 5) * i
        ctx.beginPath()
        ctx.moveTo(padding.left, y)
        ctx.lineTo(padding.left + width, y)
        ctx.stroke()
      }
      
      // 纵向网格线
      for (let i = 0; i <= 6; i++) {
        const x = padding.left + (width / 6) * i
        ctx.beginPath()
        ctx.moveTo(x, padding.top)
        ctx.lineTo(x, padding.top + height)
        ctx.stroke()
      }
    }

    // 绘制坐标轴
    const drawAxes = (ctx, padding, width, height, minValue, maxValue, data) => {
      ctx.strokeStyle = '#333'
      ctx.lineWidth = 2
      
      // Y轴
      ctx.beginPath()
      ctx.moveTo(padding.left, padding.top)
      ctx.lineTo(padding.left, padding.top + height)
      ctx.stroke()
      
      // X轴
      ctx.beginPath()
      ctx.moveTo(padding.left, padding.top + height)
      ctx.lineTo(padding.left + width, padding.top + height)
      ctx.stroke()
      
      // Y轴标签
      ctx.fillStyle = '#666'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'right'
      
      for (let i = 0; i <= 5; i++) {
        const value = minValue + ((maxValue - minValue) / 5) * (5 - i)
        const y = padding.top + (height / 5) * i
        ctx.fillText(formatAxisValue(value), padding.left - 10, y + 4)
      }
      
      // X轴标签
      ctx.textAlign = 'center'
      const step = Math.max(1, Math.floor(data.length / 6))
      
      for (let i = 0; i < data.length; i += step) {
        const x = padding.left + (width / (data.length - 1)) * i
        const date = new Date(data[i].date)
        const label = `${date.getMonth() + 1}/${date.getDate()}`
        ctx.fillText(label, x, padding.top + height + 20)
      }
    }

    // 绘制净值曲线
    const drawEquityCurve = (ctx, padding, width, height, data, minValue, valueRange) => {
      ctx.strokeStyle = '#4CAF50'
      ctx.lineWidth = 2
      ctx.lineJoin = 'round'

      ctx.beginPath()
      data.forEach((point, index) => {
        const x = padding.left + (width / (data.length - 1)) * index
        const value = point.value || point.equity || point.portfolio_value || 0
        const y = padding.top + height - ((value - minValue) / valueRange) * height
        
        if (index === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      })
      ctx.stroke()
      
      // 绘制渐变填充
      const gradient = ctx.createLinearGradient(0, padding.top, 0, padding.top + height)
      gradient.addColorStop(0, 'rgba(76, 175, 80, 0.3)')
      gradient.addColorStop(1, 'rgba(76, 175, 80, 0.05)')
      
      ctx.fillStyle = gradient
      ctx.beginPath()
      data.forEach((point, index) => {
        const x = padding.left + (width / (data.length - 1)) * index
        const value = point.value || point.equity || point.portfolio_value || 0
        const y = padding.top + height - ((value - minValue) / valueRange) * height
        
        if (index === 0) {
          ctx.moveTo(x, y)
        } else {
          ctx.lineTo(x, y)
        }
      })
      ctx.lineTo(padding.left + width, padding.top + height)
      ctx.lineTo(padding.left, padding.top + height)
      ctx.closePath()
      ctx.fill()
    }

    // 绘制基准曲线
    const drawBenchmarkCurve = (ctx, padding, width, height, data, minValue, valueRange) => {
      ctx.strokeStyle = '#FF9800'
      ctx.lineWidth = 1.5
      ctx.setLineDash([5, 5])
      
      ctx.beginPath()
      data.forEach((point, index) => {
        if (point.benchmark) {
          const x = padding.left + (width / (data.length - 1)) * index
          const y = padding.top + height - ((point.benchmark - minValue) / valueRange) * height
          
          if (index === 0) {
            ctx.moveTo(x, y)
          } else {
            ctx.lineTo(x, y)
          }
        }
      })
      ctx.stroke()
      ctx.setLineDash([])
    }

    // 绘制交易信号
    const drawTradeSignals = (ctx, padding, width, height, trades, data, minValue, valueRange) => {
      trades.forEach(trade => {
        // 找到对应的数据点
        const dataIndex = data.findIndex(d => {
          const dataDate = new Date(d.date).toDateString()
          const tradeDate = new Date(trade.date).toDateString()
          return dataDate === tradeDate
        })
        
        if (dataIndex >= 0) {
          const x = padding.left + (width / (data.length - 1)) * dataIndex
          const value = data[dataIndex].value || data[dataIndex].equity || data[dataIndex].portfolio_value || 0
          const y = padding.top + height - ((value - minValue) / valueRange) * height
          
          // 绘制三角形标记
          ctx.fillStyle = trade.type === 'BUY' ? '#4CAF50' : '#f44336'
          ctx.beginPath()
          
          if (trade.type === 'BUY') {
            // 向上三角形
            ctx.moveTo(x, y - 10)
            ctx.lineTo(x - 5, y - 20)
            ctx.lineTo(x + 5, y - 20)
          } else {
            // 向下三角形
            ctx.moveTo(x, y + 10)
            ctx.lineTo(x - 5, y + 20)
            ctx.lineTo(x + 5, y + 20)
          }
          
          ctx.closePath()
          ctx.fill()
        }
      })
    }

    // 格式化轴值
    const formatAxisValue = (value) => {
      if (value >= 10000) {
        return (value / 10000).toFixed(1) + '万'
      }
      return value.toFixed(0)
    }

    // 格式化金额
    const formatAmount = (value) => {
      return value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
    }

    // 格式化百分比
    const formatPercent = (value) => {
      return (value * 100).toFixed(2) + '%'
    }

    // 监听窗口大小变化
    const handleResize = () => {
      drawChart()
    }

    onMounted(() => {
      drawChart()
      window.addEventListener('resize', handleResize)
    })

    onUnmounted(() => {
      window.removeEventListener('resize', handleResize)
      if (animationId) {
        cancelAnimationFrame(animationId)
      }
    })

    // 监听数据变化
    watch(() => props.data, () => {
      drawChart()
    }, { deep: true })

    return {
      chartCanvas,
      statistics,
      formatAmount,
      formatPercent
    }
  }
}
</script>

<style scoped>
.equity-curve-container {
  position: relative;
  width: 100%;
}

canvas {
  width: 100%;
  height: 400px;
  display: block;
}

.chart-legend {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 15px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #666;
}

.legend-color {
  width: 20px;
  height: 3px;
  border-radius: 2px;
}

.legend-color.equity {
  background: #4CAF50;
}

.legend-color.benchmark {
  background: #FF9800;
  background-image: repeating-linear-gradient(
    90deg,
    #FF9800,
    #FF9800 5px,
    transparent 5px,
    transparent 10px
  );
}

.legend-marker {
  font-size: 16px;
}

.legend-marker.buy {
  color: #4CAF50;
}

.legend-marker.sell {
  color: #f44336;
}

.chart-stats {
  display: flex;
  justify-content: space-around;
  margin-top: 20px;
  padding: 15px;
  background: white;
  border: 1px solid #e0e0e0;
  border-radius: 6px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 5px;
}

.stat-label {
  font-size: 12px;
  color: #999;
}

.stat-value {
  font-size: 16px;
  font-weight: 500;
  color: #333;
}

.stat-value.negative {
  color: #f44336;
}
</style>
