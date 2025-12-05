<template>
  <div :class="['data-panel', 'left-panel', { 'panel-open': isOpen }]">
    <!-- 切换按钮 -->
    <button @click="togglePanel" class="panel-toggle left-toggle">
      <span class="toggle-icon">{{ isOpen ? '◀' : '▶' }}</span>
      <span class="toggle-text">股票数据</span>
    </button>

    <!-- 面板内容 -->
    <div class="panel-content">
      <div class="panel-header">
        <h3 class="panel-title">
          <span class="title-icon">📊</span>
          股票数据透明化
        </h3>
        <p class="panel-subtitle">实时数据获取与处理流程</p>
      </div>

      <div class="panel-body">
        <!-- 数据源状态 -->
        <div class="data-section">
          <div class="section-title">
            <span class="section-icon">🔌</span>
            数据源状态
          </div>
          <div class="data-sources">
            <div 
              v-for="source in dataSources" 
              :key="source.name"
              :class="['source-item', source.status]"
            >
              <span class="source-dot"></span>
              <span class="source-name">{{ source.name }}</span>
              <span class="source-status">{{ getStatusText(source.status) }}</span>
            </div>
          </div>
        </div>

        <!-- 数据流日志 -->
        <div class="data-section">
          <div class="section-title">
            <span class="section-icon">📝</span>
            数据流日志
            <button @click="clearLogs" class="clear-btn">清空</button>
          </div>
          <div class="log-container" ref="logContainer">
            <div 
              v-for="(log, index) in logs" 
              :key="index"
              :class="['log-item', log.type]"
            >
              <span class="log-time">{{ log.time }}</span>
              <span class="log-icon">{{ getLogIcon(log.type) }}</span>
              <span class="log-text">{{ log.message }}</span>
            </div>
            <div v-if="logs.length === 0" class="log-empty">
              等待数据获取...
            </div>
          </div>
        </div>

        <!-- 当前数据 -->
        <div class="data-section" v-if="currentData">
          <div class="section-title">
            <span class="section-icon">💰</span>
            当前数据
          </div>
          <div class="current-data">
            <div class="data-row">
              <span class="data-label">股票代码:</span>
              <span class="data-value">{{ currentData.symbol }}</span>
            </div>
            <div class="data-row">
              <span class="data-label">股票名称:</span>
              <span class="data-value">{{ currentData.name }}</span>
            </div>
            <div class="data-row">
              <span class="data-label">最新价格:</span>
              <span class="data-value highlight">¥{{ currentData.price }}</span>
            </div>
            <div class="data-row">
              <span class="data-label">涨跌幅:</span>
              <span :class="['data-value', getChangeClass(currentData.change)]">
                {{ formatChange(currentData.change) }}
              </span>
            </div>
            <div class="data-row">
              <span class="data-label">数据源:</span>
              <span class="data-value">{{ currentData.data_source }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch, nextTick } from 'vue'

export default {
  name: 'StockDataPanel',
  props: {
    stockData: {
      type: Object,
      default: null
    }
  },
  setup(props) {
    const isOpen = ref(false)
    const logs = ref([])
    const logContainer = ref(null)
    const currentData = ref(null)
    
    const dataSources = ref([
      { name: 'AKShare', status: 'active' },
      { name: '新浪财经', status: 'active' },
      { name: '聚合数据', status: 'standby' },
      { name: 'Tushare', status: 'standby' }
    ])

    const togglePanel = () => {
      isOpen.value = !isOpen.value
    }

    const addLog = (message, type = 'info') => {
      const now = new Date()
      const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
      
      logs.value.push({
        time,
        type,
        message
      })

      // 限制日志数量
      if (logs.value.length > 50) {
        logs.value.shift()
      }

      // 自动滚动到底部
      nextTick(() => {
        if (logContainer.value) {
          logContainer.value.scrollTop = logContainer.value.scrollHeight
        }
      })
    }

    const clearLogs = () => {
      logs.value = []
    }

    const getStatusText = (status) => {
      const statusMap = {
        active: '活跃',
        standby: '待命',
        error: '错误',
        disabled: '禁用'
      }
      return statusMap[status] || status
    }

    const getLogIcon = (type) => {
      const iconMap = {
        info: 'ℹ️',
        success: '✅',
        warning: '⚠️',
        error: '❌',
        fetch: '📡'
      }
      return iconMap[type] || 'ℹ️'
    }

    const getChangeClass = (change) => {
      if (!change && change !== 0) return ''
      // 确保change是字符串类型
      const changeStr = String(change)
      // 判断是正数还是负数
      const changeNum = parseFloat(changeStr)
      return changeNum >= 0 ? 'positive' : 'negative'
    }

    const formatChange = (change) => {
      if (!change && change !== 0) return '0.00%'
      // 确保是数字
      const changeNum = parseFloat(change)
      // 格式化为带符号的百分比
      return (changeNum >= 0 ? '+' : '') + changeNum.toFixed(2) + '%'
    }

    // 监听股票数据变化
    watch(() => props.stockData, (newData) => {
      if (newData) {
        currentData.value = newData
        addLog(`获取股票数据: ${newData.symbol} ${newData.name}`, 'fetch')
        addLog(`价格: ¥${newData.price} | 涨跌: ${newData.change}`, 'success')
        addLog(`数据源: ${newData.data_source || '未知'}`, 'info')
      }
    }, { deep: true })

    return {
      isOpen,
      logs,
      logContainer,
      currentData,
      dataSources,
      togglePanel,
      addLog,
      clearLogs,
      getStatusText,
      getLogIcon,
      getChangeClass,
      formatChange
    }
  }
}
</script>

<style scoped>
.data-panel {
  position: fixed;
  top: 5rem;
  bottom: 2rem;
  width: 380px;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(51, 65, 85, 0.8);
  border-radius: 0.75rem;
  backdrop-filter: blur(12px);
  transition: transform 0.3s ease;
  z-index: 40;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.left-panel {
  left: 1rem;
  transform: translateX(-100%);
}

.left-panel.panel-open {
  transform: translateX(0);
}

.panel-toggle {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(51, 65, 85, 0.8);
  padding: 0.75rem 0.5rem;
  border-radius: 0 0.5rem 0.5rem 0;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: #94a3b8;
  font-size: 0.75rem;
  z-index: 1;
}

.left-toggle {
  right: -2.5rem;
}

.panel-toggle:hover {
  background: rgba(51, 65, 85, 0.8);
  color: white;
}

.toggle-icon {
  font-size: 1rem;
}

.toggle-text {
  writing-mode: vertical-rl;
  font-weight: 500;
}

.panel-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.panel-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: white;
  margin: 0;
}

.title-icon {
  font-size: 1.25rem;
}

.panel-subtitle {
  margin: 0.5rem 0 0 0;
  font-size: 0.75rem;
  color: #94a3b8;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.panel-body::-webkit-scrollbar {
  width: 6px;
}

.panel-body::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
  border-radius: 3px;
}

.panel-body::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.5);
  border-radius: 3px;
}

.panel-body::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.7);
}

.data-section {
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.5rem;
  padding: 1rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 0.75rem;
}

.section-icon {
  font-size: 1rem;
}

.clear-btn {
  margin-left: auto;
  padding: 0.25rem 0.5rem;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.25rem;
  color: #ef4444;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

.data-sources {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.source-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 0.375rem;
  font-size: 0.75rem;
}

.source-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #64748b;
}

.source-item.active .source-dot {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

.source-item.standby .source-dot {
  background: #f59e0b;
}

.source-item.error .source-dot {
  background: #ef4444;
}

.source-name {
  flex: 1;
  color: #e2e8f0;
  font-weight: 500;
}

.source-status {
  color: #94a3b8;
  font-size: 0.7rem;
}

.log-container {
  max-height: 300px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.log-container::-webkit-scrollbar {
  width: 4px;
}

.log-container::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.3);
}

.log-container::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.3);
  border-radius: 2px;
}

.log-item {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(15, 23, 42, 0.5);
  border-left: 2px solid #64748b;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-10px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.log-item.success {
  border-left-color: #10b981;
}

.log-item.warning {
  border-left-color: #f59e0b;
}

.log-item.error {
  border-left-color: #ef4444;
}

.log-item.fetch {
  border-left-color: #3b82f6;
}

.log-time {
  color: #64748b;
  font-family: monospace;
  font-size: 0.7rem;
  flex-shrink: 0;
}

.log-icon {
  flex-shrink: 0;
}

.log-text {
  color: #cbd5e1;
  line-height: 1.4;
}

.log-empty {
  text-align: center;
  color: #64748b;
  padding: 2rem 1rem;
  font-size: 0.875rem;
}

.current-data {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.data-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 0.375rem;
  font-size: 0.8125rem;
}

.data-label {
  color: #94a3b8;
}

.data-value {
  color: #e2e8f0;
  font-weight: 500;
}

.data-value.highlight {
  color: #3b82f6;
  font-size: 1rem;
  font-weight: 600;
}

.data-value.positive {
  color: #10b981;
}

.data-value.negative {
  color: #ef4444;
}
</style>
