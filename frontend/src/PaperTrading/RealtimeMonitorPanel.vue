<template>
  <div class="monitor-panel">
    <!-- 面板标题 -->
    <div class="panel-header">
      <div class="header-left">
        <h3>🎯 实时盯盘监控</h3>
        <span :class="['status-badge', statusClass]">
          {{ statusText }}
        </span>
      </div>
      <div class="header-right">
        <button 
          v-if="!isRunning" 
          @click="startMonitoring" 
          class="btn-primary"
          :disabled="loading"
        >
          ▶️ 启动监控
        </button>
        <button 
          v-else 
          @click="stopMonitoring" 
          class="btn-danger"
          :disabled="loading"
        >
          ⏹️ 停止监控
        </button>
        <button @click="showConfigDialog = true" class="btn-secondary">
          ⚙️ 配置
        </button>
      </div>
    </div>

    <!-- 监控统计 -->
    <div class="monitor-stats" v-if="status">
      <div class="stat-card">
        <div class="stat-label">监控股票</div>
        <div class="stat-value">{{ status.monitored_stocks?.length || 0 }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">监控间隔</div>
        <div class="stat-value">{{ config.monitor_interval || 300 }}秒</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">今日触发</div>
        <div class="stat-value">{{ todayTriggers }}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">下次检查</div>
        <div class="stat-value">{{ nextCheckTime }}</div>
      </div>
    </div>

    <!-- 监控股票列表 -->
    <div class="monitored-stocks">
      <div class="section-header">
        <h4>📊 监控列表</h4>
        <button @click="showAddStockDialog = true" class="btn-small">
          ➕ 添加股票
        </button>
      </div>
      
      <div v-if="!monitoredStocks.length" class="empty-state">
        <p>暂无监控股票，请添加股票开始监控</p>
      </div>
      
      <div v-else class="stock-list">
        <div 
          v-for="stock in monitoredStocks" 
          :key="stock.stock_code"
          class="stock-item"
        >
          <div class="stock-info">
            <span class="stock-code">{{ stock.stock_code }}</span>
            <span class="stock-name">{{ stock.stock_name || '未知' }}</span>
          </div>
          <div class="stock-price" :class="getPriceClass(stock)">
            <span class="current-price">¥{{ formatPrice(stock.current_price) }}</span>
            <span class="price-change">{{ formatChange(stock.change_pct) }}%</span>
          </div>
          <div class="stock-thresholds">
            <span class="threshold stop-loss" title="止损线">
              ↓ {{ stock.stop_loss_pct || config.default_stop_loss }}%
            </span>
            <span class="threshold take-profit" title="止盈线">
              ↑ {{ stock.take_profit_pct || config.default_take_profit }}%
            </span>
          </div>
          <div class="stock-actions">
            <button @click="removeStock(stock.stock_code)" class="btn-icon" title="移除">
              ❌
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 最近事件 -->
    <div class="recent-events">
      <div class="section-header">
        <h4>📢 最近事件</h4>
        <button @click="clearEvents" class="btn-small btn-text">清空</button>
      </div>
      
      <div v-if="!recentEvents.length" class="empty-state">
        <p>暂无监控事件</p>
      </div>
      
      <div v-else class="event-list">
        <div 
          v-for="(event, index) in recentEvents" 
          :key="index"
          :class="['event-item', event.type]"
        >
          <div class="event-icon">
            {{ getEventIcon(event.type) }}
          </div>
          <div class="event-content">
            <div class="event-title">{{ event.title }}</div>
            <div class="event-message">{{ event.message }}</div>
            <div class="event-time">{{ formatEventTime(event.timestamp) }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 配置对话框 -->
    <div v-if="showConfigDialog" class="modal-overlay" @click="showConfigDialog = false">
      <div class="modal-content" @click.stop>
        <h3>⚙️ 监控配置</h3>
        
        <div class="form-group">
          <label>监控间隔（秒）</label>
          <input 
            v-model.number="configForm.monitor_interval" 
            type="number"
            min="60"
            max="3600"
            class="input-field"
          />
          <small>建议 300-600 秒，最小 60 秒</small>
        </div>
        
        <div class="form-group">
          <label>默认止损比例（%）</label>
          <input 
            v-model.number="configForm.default_stop_loss" 
            type="number"
            min="1"
            max="50"
            step="0.5"
            class="input-field"
          />
        </div>
        
        <div class="form-group">
          <label>默认止盈比例（%）</label>
          <input 
            v-model.number="configForm.default_take_profit" 
            type="number"
            min="1"
            max="100"
            step="0.5"
            class="input-field"
          />
        </div>
        
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="configForm.auto_trade" />
            启用自动交易（AI决策后自动执行）
          </label>
        </div>
        
        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="configForm.auto_start" />
            服务启动时自动开始监控
          </label>
        </div>
        
        <div class="modal-actions">
          <button @click="saveConfig" class="btn-primary" :disabled="saving">
            {{ saving ? '保存中...' : '保存配置' }}
          </button>
          <button @click="showConfigDialog = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 添加股票对话框 -->
    <div v-if="showAddStockDialog" class="modal-overlay" @click="showAddStockDialog = false">
      <div class="modal-content" @click.stop>
        <h3>➕ 添加监控股票</h3>
        
        <div class="form-group">
          <label>股票代码</label>
          <input 
            v-model="addStockForm.stock_code" 
            placeholder="如：600519"
            class="input-field"
          />
        </div>
        
        <div class="form-group">
          <label>止损比例（%）</label>
          <input 
            v-model.number="addStockForm.stop_loss_pct" 
            type="number"
            min="1"
            max="50"
            step="0.5"
            class="input-field"
            :placeholder="`默认 ${config.default_stop_loss}%`"
          />
        </div>
        
        <div class="form-group">
          <label>止盈比例（%）</label>
          <input 
            v-model.number="addStockForm.take_profit_pct" 
            type="number"
            min="1"
            max="100"
            step="0.5"
            class="input-field"
            :placeholder="`默认 ${config.default_take_profit}%`"
          />
        </div>
        
        <div class="modal-actions">
          <button @click="addStock" class="btn-primary" :disabled="adding">
            {{ adding ? '添加中...' : '添加' }}
          </button>
          <button @click="showAddStockDialog = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '@/config/api.js'

export default {
  name: 'RealtimeMonitorPanel',
  
  setup() {
    const API_BASE = `${API_BASE_URL}/api/realtime-monitor`
    
    // 状态
    const status = ref(null)
    const config = ref({
      monitor_interval: 300,
      default_stop_loss: 5,
      default_take_profit: 10,
      auto_trade: true,
      auto_start: false
    })
    const loading = ref(false)
    const saving = ref(false)
    const adding = ref(false)
    
    // 对话框
    const showConfigDialog = ref(false)
    const showAddStockDialog = ref(false)
    
    // 表单
    const configForm = reactive({
      monitor_interval: 300,
      default_stop_loss: 5,
      default_take_profit: 10,
      auto_trade: true,
      auto_start: false
    })
    
    const addStockForm = reactive({
      stock_code: '',
      stop_loss_pct: null,
      take_profit_pct: null
    })
    
    // 事件列表
    const recentEvents = ref([])
    
    // WebSocket 连接
    let ws = null
    let reconnectTimer = null
    
    // 计算属性
    const isRunning = computed(() => status.value?.is_running || false)
    
    const statusClass = computed(() => {
      if (!status.value) return 'offline'
      if (status.value.is_running) return 'running'
      return 'stopped'
    })
    
    const statusText = computed(() => {
      if (!status.value) return '未连接'
      if (status.value.is_running) return '监控中'
      return '已停止'
    })
    
    const monitoredStocks = computed(() => {
      return status.value?.monitored_stocks || []
    })
    
    const todayTriggers = computed(() => {
      // 统计今日触发次数
      const today = new Date().toDateString()
      return recentEvents.value.filter(e => 
        new Date(e.timestamp).toDateString() === today &&
        (e.type === 'stop_loss' || e.type === 'take_profit')
      ).length
    })
    
    const nextCheckTime = computed(() => {
      if (!status.value?.is_running || !status.value?.last_check_time) {
        return '--'
      }
      const lastCheck = new Date(status.value.last_check_time)
      const nextCheck = new Date(lastCheck.getTime() + (config.value.monitor_interval || 300) * 1000)
      const now = new Date()
      const diff = Math.max(0, Math.floor((nextCheck - now) / 1000))
      if (diff > 60) {
        return `${Math.floor(diff / 60)}分${diff % 60}秒`
      }
      return `${diff}秒`
    })
    
    // 方法
    const loadStatus = async () => {
      try {
        const response = await axios.get(`${API_BASE}/status`)
        if (response.data.success) {
          status.value = response.data.data
          // 同步配置
          if (response.data.data.config) {
            Object.assign(config.value, response.data.data.config)
            Object.assign(configForm, response.data.data.config)
          }
        }
      } catch (error) {
        console.error('获取监控状态失败:', error)
      }
    }
    
    const startMonitoring = async () => {
      loading.value = true
      try {
        const response = await axios.post(`${API_BASE}/start`)
        if (response.data.success) {
          await loadStatus()
          addEvent('info', '监控已启动', '实时盯盘监控服务已开始运行')
        } else {
          alert('启动失败: ' + response.data.message)
        }
      } catch (error) {
        console.error('启动监控失败:', error)
        alert('启动失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        loading.value = false
      }
    }
    
    const stopMonitoring = async () => {
      loading.value = true
      try {
        const response = await axios.post(`${API_BASE}/stop`)
        if (response.data.success) {
          await loadStatus()
          addEvent('info', '监控已停止', '实时盯盘监控服务已停止')
        }
      } catch (error) {
        console.error('停止监控失败:', error)
        alert('停止失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        loading.value = false
      }
    }
    
    const saveConfig = async () => {
      saving.value = true
      try {
        const response = await axios.post(`${API_BASE}/config`, configForm)
        if (response.data.success) {
          Object.assign(config.value, configForm)
          showConfigDialog.value = false
          addEvent('info', '配置已保存', '监控配置已更新')
        }
      } catch (error) {
        console.error('保存配置失败:', error)
        alert('保存失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        saving.value = false
      }
    }
    
    const addStock = async () => {
      if (!addStockForm.stock_code) {
        alert('请输入股票代码')
        return
      }
      
      adding.value = true
      try {
        const response = await axios.post(`${API_BASE}/stocks`, {
          stock_code: addStockForm.stock_code,
          stop_loss_pct: addStockForm.stop_loss_pct || config.value.default_stop_loss,
          take_profit_pct: addStockForm.take_profit_pct || config.value.default_take_profit
        })
        
        if (response.data.success) {
          await loadStatus()
          showAddStockDialog.value = false
          // 重置表单
          addStockForm.stock_code = ''
          addStockForm.stop_loss_pct = null
          addStockForm.take_profit_pct = null
          addEvent('info', '股票已添加', `${addStockForm.stock_code} 已加入监控列表`)
        }
      } catch (error) {
        console.error('添加股票失败:', error)
        alert('添加失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        adding.value = false
      }
    }
    
    const removeStock = async (stockCode) => {
      if (!confirm(`确定要移除 ${stockCode} 的监控吗？`)) return
      
      try {
        const response = await axios.delete(`${API_BASE}/stocks/${stockCode}`)
        if (response.data.success) {
          await loadStatus()
          addEvent('info', '股票已移除', `${stockCode} 已从监控列表移除`)
        }
      } catch (error) {
        console.error('移除股票失败:', error)
        alert('移除失败: ' + (error.response?.data?.detail || error.message))
      }
    }
    
    // WebSocket 连接
    const connectWebSocket = () => {
      const wsUrl = API_BASE_URL.replace('http', 'ws') + '/api/realtime-monitor/ws'
      
      try {
        ws = new WebSocket(wsUrl)
        
        ws.onopen = () => {
          console.log('WebSocket 已连接')
          addEvent('info', '连接成功', '实时监控 WebSocket 已连接')
        }
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            handleWebSocketMessage(data)
          } catch (e) {
            console.error('解析 WebSocket 消息失败:', e)
          }
        }
        
        ws.onclose = () => {
          console.log('WebSocket 已断开')
          // 5秒后重连
          reconnectTimer = setTimeout(connectWebSocket, 5000)
        }
        
        ws.onerror = (error) => {
          console.error('WebSocket 错误:', error)
        }
      } catch (error) {
        console.error('WebSocket 连接失败:', error)
      }
    }
    
    const handleWebSocketMessage = (data) => {
      switch (data.type) {
        case 'status_update':
          status.value = data.data
          break
        case 'price_update':
          // 更新股票价格
          if (status.value?.monitored_stocks) {
            const stock = status.value.monitored_stocks.find(
              s => s.stock_code === data.stock_code
            )
            if (stock) {
              stock.current_price = data.price
              stock.change_pct = data.change_pct
            }
          }
          break
        case 'stop_loss':
          addEvent('stop_loss', '止损触发', data.message)
          break
        case 'take_profit':
          addEvent('take_profit', '止盈触发', data.message)
          break
        case 'ai_decision':
          addEvent('ai_decision', 'AI 决策', data.message)
          break
        case 'trade_executed':
          addEvent('trade', '交易执行', data.message)
          break
        case 'error':
          addEvent('error', '错误', data.message)
          break
      }
    }
    
    // 事件管理
    const addEvent = (type, title, message) => {
      recentEvents.value.unshift({
        type,
        title,
        message,
        timestamp: new Date().toISOString()
      })
      // 最多保留 50 条
      if (recentEvents.value.length > 50) {
        recentEvents.value.pop()
      }
    }
    
    const clearEvents = () => {
      recentEvents.value = []
    }
    
    // 格式化函数
    const formatPrice = (price) => {
      if (price == null) return '--'
      return Number(price).toFixed(2)
    }
    
    const formatChange = (change) => {
      if (change == null) return '--'
      const value = Number(change).toFixed(2)
      return change >= 0 ? `+${value}` : value
    }
    
    const getPriceClass = (stock) => {
      if (!stock.change_pct) return ''
      return stock.change_pct >= 0 ? 'price-up' : 'price-down'
    }
    
    const getEventIcon = (type) => {
      const icons = {
        'info': 'ℹ️',
        'stop_loss': '🔴',
        'take_profit': '🟢',
        'ai_decision': '🤖',
        'trade': '💰',
        'error': '⚠️'
      }
      return icons[type] || '📌'
    }
    
    const formatEventTime = (timestamp) => {
      const date = new Date(timestamp)
      return date.toLocaleTimeString('zh-CN')
    }
    
    // 定时刷新状态
    let statusTimer = null
    
    onMounted(() => {
      loadStatus()
      // 每 30 秒刷新一次状态
      statusTimer = setInterval(loadStatus, 30000)
      // 连接 WebSocket
      connectWebSocket()
    })
    
    onUnmounted(() => {
      if (statusTimer) {
        clearInterval(statusTimer)
      }
      if (reconnectTimer) {
        clearTimeout(reconnectTimer)
      }
      if (ws) {
        ws.close()
      }
    })
    
    return {
      // 状态
      status,
      config,
      loading,
      saving,
      adding,
      isRunning,
      statusClass,
      statusText,
      monitoredStocks,
      todayTriggers,
      nextCheckTime,
      recentEvents,
      
      // 对话框
      showConfigDialog,
      showAddStockDialog,
      
      // 表单
      configForm,
      addStockForm,
      
      // 方法
      startMonitoring,
      stopMonitoring,
      saveConfig,
      addStock,
      removeStock,
      clearEvents,
      
      // 格式化
      formatPrice,
      formatChange,
      getPriceClass,
      getEventIcon,
      formatEventTime
    }
  }
}
</script>

<style scoped>
.monitor-panel {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-left h3 {
  margin: 0;
  color: white;
  font-size: 18px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 500;
}

.status-badge.running {
  background: rgba(82, 196, 26, 0.2);
  color: #52c41a;
  border: 1px solid rgba(82, 196, 26, 0.3);
}

.status-badge.stopped {
  background: rgba(255, 77, 79, 0.2);
  color: #ff4d4f;
  border: 1px solid rgba(255, 77, 79, 0.3);
}

.status-badge.offline {
  background: rgba(153, 153, 153, 0.2);
  color: #999;
  border: 1px solid rgba(153, 153, 153, 0.3);
}

.header-right {
  display: flex;
  gap: 8px;
}

/* 监控统计 */
.monitor-stats {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.stat-card {
  background: rgba(255, 255, 255, 0.03);
  padding: 12px;
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  color: #999;
  font-size: 12px;
  margin-bottom: 4px;
}

.stat-value {
  color: white;
  font-size: 20px;
  font-weight: bold;
}

/* 监控股票列表 */
.monitored-stocks,
.recent-events {
  margin-bottom: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h4 {
  margin: 0;
  color: white;
  font-size: 14px;
}

.stock-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.stock-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  transition: background 0.2s;
}

.stock-item:hover {
  background: rgba(255, 255, 255, 0.06);
}

.stock-info {
  flex: 1;
  min-width: 120px;
}

.stock-code {
  color: white;
  font-weight: 600;
  margin-right: 8px;
}

.stock-name {
  color: #999;
  font-size: 12px;
}

.stock-price {
  min-width: 100px;
  text-align: right;
}

.current-price {
  display: block;
  font-weight: 600;
}

.price-change {
  font-size: 12px;
}

.price-up .current-price,
.price-up .price-change {
  color: #ff4d4f;
}

.price-down .current-price,
.price-down .price-change {
  color: #52c41a;
}

.stock-thresholds {
  display: flex;
  gap: 8px;
  min-width: 120px;
}

.threshold {
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
}

.threshold.stop-loss {
  background: rgba(255, 77, 79, 0.1);
  color: #ff4d4f;
}

.threshold.take-profit {
  background: rgba(82, 196, 26, 0.1);
  color: #52c41a;
}

.stock-actions {
  display: flex;
  gap: 4px;
}

/* 事件列表 */
.event-list {
  max-height: 300px;
  overflow-y: auto;
}

.event-item {
  display: flex;
  gap: 12px;
  padding: 10px;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 8px;
  margin-bottom: 8px;
}

.event-item.stop_loss {
  border-left: 3px solid #ff4d4f;
}

.event-item.take_profit {
  border-left: 3px solid #52c41a;
}

.event-item.ai_decision {
  border-left: 3px solid #1890ff;
}

.event-item.trade {
  border-left: 3px solid #faad14;
}

.event-item.error {
  border-left: 3px solid #ff7875;
}

.event-icon {
  font-size: 20px;
}

.event-content {
  flex: 1;
}

.event-title {
  color: white;
  font-weight: 500;
  margin-bottom: 2px;
}

.event-message {
  color: #999;
  font-size: 13px;
}

.event-time {
  color: #666;
  font-size: 11px;
  margin-top: 4px;
}

/* 空状态 */
.empty-state {
  text-align: center;
  padding: 30px;
  color: #999;
}

/* 按钮样式 */
.btn-primary,
.btn-secondary,
.btn-danger {
  padding: 8px 16px;
  border-radius: 6px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.btn-primary {
  background: #1890ff;
  color: white;
}

.btn-primary:hover:not(:disabled) {
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

.btn-danger:hover:not(:disabled) {
  background: #ff7875;
}

.btn-small {
  padding: 4px 12px;
  font-size: 12px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 4px;
  cursor: pointer;
}

.btn-small:hover {
  background: rgba(255, 255, 255, 0.15);
}

.btn-text {
  background: transparent;
  border: none;
  color: #999;
}

.btn-text:hover {
  color: white;
}

.btn-icon {
  padding: 4px 8px;
  background: transparent;
  border: none;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.btn-icon:hover {
  opacity: 1;
}

button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
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
  box-sizing: border-box;
}

.input-field:focus {
  outline: none;
  border-color: #1890ff;
}

.form-group small {
  display: block;
  margin-top: 4px;
  color: #999;
  font-size: 12px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 20px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .monitor-panel {
    padding: 12px;
  }

  .panel-header {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }

  .header-right {
    width: 100%;
    justify-content: flex-start;
  }

  .monitor-stats {
    grid-template-columns: repeat(2, 1fr);
    gap: 8px;
  }

  .stat-card {
    padding: 10px;
  }

  .stat-value {
    font-size: 16px;
  }

  .stock-item {
    flex-wrap: wrap;
    gap: 8px;
  }

  .stock-info {
    min-width: 100%;
  }

  .stock-price {
    min-width: auto;
  }

  .stock-thresholds {
    min-width: auto;
  }

  .modal-content {
    min-width: auto;
    max-width: calc(100vw - 32px);
    width: calc(100vw - 32px);
    padding: 16px;
  }

  .modal-actions {
    flex-direction: column;
  }

  .modal-actions button {
    width: 100%;
  }
}

@media (max-width: 480px) {
  .monitor-stats {
    grid-template-columns: 1fr 1fr;
  }

  .header-left h3 {
    font-size: 16px;
  }

  .btn-primary,
  .btn-secondary,
  .btn-danger {
    padding: 8px 12px;
    font-size: 12px;
  }
}
</style>