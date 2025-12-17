<template>
  <div class="trading-container">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>💼 模拟交易</h1>
      <p class="subtitle">虚拟资金练习交易，零风险学习投资</p>
      <div class="action-buttons">
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
        <h3>📈 K线图</h3>
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
        </div>
      </div>
      <div class="kline-chart-wrapper">
        <div class="kline-chart" ref="klineChart"></div>
        <div v-if="klineLoading" class="kline-overlay kline-loading">
          <div class="spinner"></div>
          <p>加载K线数据中...</p>
        </div>
        <div v-else-if="klineError" class="kline-overlay kline-error">
          <p>⚠️ {{ klineError }}</p>
        </div>
        <div v-else-if="klineData.length === 0" class="kline-overlay kline-empty">
          <p>暂无K线数据，请输入股票代码并点击加载</p>
        </div>
      </div>
    </div>

    <!-- 持仓列表 -->
    <div class="positions-section">
      <h3>📊 持仓列表</h3>
      <div v-if="!portfolio || portfolio.positions.length === 0" class="empty-state">
        <p>暂无持仓</p>
      </div>
      <table v-else class="data-table">
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

    <!-- 交易记录 -->
    <div class="trades-section">
      <h3>📝 交易记录</h3>
      <div v-if="trades.length === 0" class="empty-state">
        <p>暂无交易记录</p>
      </div>
      <table v-else class="data-table">
        <thead>
          <tr>
            <th>时间</th>
            <th>股票代码</th>
            <th>股票名称</th>
            <th>方向</th>
            <th>数量</th>
            <th>价格</th>
            <th>金额</th>
            <th>手续费</th>
            <th>状态</th>
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
            <td>{{ formatTime(trade.timestamp) }}</td>
            <td>{{ trade.stock_code }}</td>
            <td>{{ trade.stock_name }}</td>
            <td :class="trade.action === 'BUY' ? 'text-success' : 'text-danger'">
              {{ trade.action === 'BUY' ? '买入' : '卖出' }}
            </td>
            <td>{{ trade.quantity }}</td>
            <td>¥{{ trade.price.toFixed(2) }}</td>
            <td>¥{{ formatAmount(trade.amount) }}</td>
            <td>¥{{ trade.commission.toFixed(2) }}</td>
            <td>{{ trade.status }}</td>
          </tr>
        </tbody>
      </table>
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
import { ref, reactive, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

export default {
  name: 'SimpleTradingView',
  setup() {
    const API_BASE = 'http://localhost:8000/api/trading'
    const KLINE_API = 'http://localhost:8000/api/kline'
    
    // 状态
    const portfolio = ref(null)
    const trades = ref([])
    const showTradeDialog = ref(false)
    
    // K线图状态
    const klineStock = ref('600519')
    const klinePeriod = ref('daily')
    const klineData = ref([])
    const klineLoading = ref(false)
    const klineError = ref('')
    const klineChart = ref(null)
    let chartInstance = null
    
    // 周期选项
    const periods = [
      { value: '1', label: '1分' },
      { value: '5', label: '5分' },
      { value: '15', label: '15分' },
      { value: '30', label: '30分' },
      { value: '60', label: '60分' },
      { value: 'daily', label: '日线' }
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
    
    const getProfitClass = (value) => {
      if (value > 0) return 'text-success'
      if (value < 0) return 'text-danger'
      return ''
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
          klineData.value = response.data.data
          console.log('获取到数据条数:', klineData.value.length)
          
          if (klineData.value.length === 0) {
            klineError.value = '没有获取到K线数据，请检查股票代码是否正确'
          } else {
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
      console.log('renderKlineChart被调用')
      console.log('klineChart.value:', klineChart.value)
      console.log('klineData.value.length:', klineData.value.length)
      
      if (!klineChart.value) {
        console.error('图表容器不存在！')
        klineError.value = '图表容器初始化失败，请刷新页面重试'
        return
      }
      
      if (klineData.value.length === 0) {
        console.error('数据为空！')
        return
      }
      
      try {
        console.log('开始渲染K线图...')
        
        const dom = klineChart.value
        const existedInstance = echarts.getInstanceByDom(dom)
        if (existedInstance && existedInstance !== chartInstance) {
          console.log('检测到遗留实例，准备复用')
          chartInstance = existedInstance
        }
        
        if (!chartInstance) {
          chartInstance = echarts.init(dom)
          console.log('ECharts实例已创建')
        } else if (chartInstance.getDom() !== dom) {
          console.log('DOM已变化，重新初始化实例')
          chartInstance.dispose()
          chartInstance = echarts.init(dom)
        } else {
          chartInstance.clear()
          chartInstance.resize()
          console.log('ECharts实例已复用')
        }
        
        // 准备数据
        const dates = klineData.value.map(item => {
          // 处理日期格式
          if (typeof item.time === 'string') {
            return item.time
          } else if (item.time instanceof Date) {
            return item.time.toISOString().split('T')[0]
          }
          return String(item.time)
        })
        
        const values = klineData.value.map(item => {
          // 确保数值类型
          return [
            Number(item.open) || 0,
            Number(item.close) || 0,
            Number(item.low) || 0,
            Number(item.high) || 0
          ]
        })
        
        const volumes = klineData.value.map(item => Number(item.volume) || 0)
        
        console.log('数据准备完成:', {
          dates: dates.length,
          values: values.length,
          volumes: volumes.length,
          sampleDate: dates[0],
          sampleValue: values[0]
        })
      
      // 配置项
      const option = {
        backgroundColor: 'transparent',
        title: {
          text: `${klineStock.value} - ${getPeriodLabel(klinePeriod.value)}`,
          left: 'center',
          textStyle: {
            color: '#fff'
          }
        },
        tooltip: {
          trigger: 'axis',
          axisPointer: {
            type: 'cross'
          },
          backgroundColor: 'rgba(0, 0, 0, 0.8)',
          borderColor: '#777',
          textStyle: {
            color: '#fff'
          }
        },
        legend: {
          data: ['K线', '成交量'],
          textStyle: {
            color: '#fff'
          }
        },
        grid: [
          {
            left: '10%',
            right: '10%',
            top: '15%',
            height: '50%'
          },
          {
            left: '10%',
            right: '10%',
            top: '70%',
            height: '15%'
          }
        ],
        xAxis: [
          {
            type: 'category',
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: { lineStyle: { color: '#777' } },
            axisLabel: { color: '#fff' },
            splitLine: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          },
          {
            type: 'category',
            gridIndex: 1,
            data: dates,
            scale: true,
            boundaryGap: false,
            axisLine: { lineStyle: { color: '#777' } },
            axisLabel: { show: false },
            splitLine: { show: false },
            min: 'dataMin',
            max: 'dataMax'
          }
        ],
        yAxis: [
          {
            scale: true,
            splitArea: { show: false },
            axisLine: { lineStyle: { color: '#777' } },
            axisLabel: { color: '#fff' },
            splitLine: { lineStyle: { color: 'rgba(255, 255, 255, 0.1)' } }
          },
          {
            scale: true,
            gridIndex: 1,
            splitNumber: 2,
            axisLabel: { show: false },
            axisLine: { show: false },
            axisTick: { show: false },
            splitLine: { show: false }
          }
        ],
        dataZoom: [
          {
            type: 'inside',
            xAxisIndex: [0, 1],
            start: 50,
            end: 100
          },
          {
            show: true,
            xAxisIndex: [0, 1],
            type: 'slider',
            bottom: '5%',
            start: 50,
            end: 100,
            textStyle: {
              color: '#fff'
            }
          }
        ],
        series: [
          {
            name: 'K线',
            type: 'candlestick',
            data: values,
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
              color: function(params) {
                const dataIndex = params.dataIndex
                const open = klineData.value[dataIndex].open
                const close = klineData.value[dataIndex].close
                return close >= open ? '#ef5350' : '#26a69a'
              }
            }
          }
        ]
      }
      
      chartInstance.setOption(option)
      console.log('K线图渲染完成')
      
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
        'daily': '日线'
      }
      return labels[period] || period
    }
    
    // 加载指定股票的K线（供点击持仓/交易记录使用）
    const loadStockKline = (stockCode) => {
      if (stockCode) {
        klineStock.value = stockCode
        loadKlineData()
      }
    }

    // 初始化
    onMounted(async () => {
      loadPortfolio()
      loadTrades()
      // 自动加载默认股票的K线图
      await nextTick()
      if (klineStock.value) {
        loadKlineData()
      }
    })
    
    onUnmounted(() => {
      if (chartInstance) {
        chartInstance.dispose()
        chartInstance = null
      }
    })
    
    return {
      portfolio,
      trades,
      showTradeDialog,
      tradeForm,
      loadPortfolio,
      executeTrade,
      quickSell,
      resetAccount,
      formatAmount,
      formatTime,
      getProfitClass,
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
      loadStockKline
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
  margin-bottom: 20px;
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
  height: 500px;
  min-height: 500px;
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

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
