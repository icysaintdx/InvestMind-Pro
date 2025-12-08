<template>
  <div 
    v-if="visible" 
    class="global-log-window" 
    :class="{ 'minimized': isMinimized }"
    :style="windowStyle"
    ref="windowRef"
  >
    <!-- 标题栏 -->
    <div 
      class="log-header"
      @mousedown="startDrag"
    >
      <div class="header-left">
        <span class="log-icon">📡</span>
        <span class="log-title">实时日志</span>
        <span v-if="totalLogs > 0" class="log-count">{{ totalLogs }}条</span>
      </div>
      <div class="header-right">
        <button @click="clearLogs" class="header-btn" title="清空日志">
          🗑️
        </button>
        <button @click="toggleMinimize" class="header-btn" title="最小化/展开">
          {{ isMinimized ? '▲' : '▼' }}
        </button>
        <button @click="close" class="header-btn" title="关闭">
          ✕
        </button>
      </div>
    </div>

    <!-- 日志内容区 -->
    <div v-show="!isMinimized" class="log-content">
      <!-- 智能体标签页 -->
      <div class="agent-tabs">
        <button
          v-for="agent in activeAgents"
          :key="agent.id"
          @click="currentAgent = agent.id"
          :class="['agent-tab', { active: currentAgent === agent.id }]"
        >
          <span class="agent-icon">{{ agent.icon }}</span>
          <span class="agent-name">{{ agent.name }}</span>
          <span v-if="agent.logCount > 0" class="agent-count">{{ agent.logCount }}</span>
        </button>
      </div>

      <!-- 日志消息列表 -->
      <div class="log-messages" ref="logMessagesRef">
        <div
          v-for="(log, index) in currentLogs"
          :key="index"
          :class="['log-message', `log-${log.type}`]"
        >
          <span class="log-time">{{ formatTime(log.timestamp) }}</span>
          <span class="log-icon">{{ getLogIcon(log.type) }}</span>
          <span class="log-text">{{ log.message }}</span>
        </div>
        <div v-if="currentLogs.length === 0" class="log-empty">
          <span class="spinner"></span>
          <span>等待日志...</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, nextTick, onBeforeUnmount } from 'vue'

export default {
  name: 'GlobalLogWindow',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  setup(props, { emit }) {
    const isMinimized = ref(false)
    const currentAgent = ref('all')
    const logMessagesRef = ref(null)
    const windowRef = ref(null)
    const eventSources = ref({}) // 存储所有 SSE 连接
    const agentLogs = ref({}) // 存储各智能体的日志
    
    // 窗口位置和尺寸
    const windowPosition = ref({ x: 20, y: 80 })
    const windowSize = ref({ width: 320, height: 450 })
    const isDragging = ref(false)
    const dragStart = ref({ x: 0, y: 0 })
    
    // 智能体配置
    const agentConfigs = {
      'news_analyst': { name: '新闻分析师', icon: '📰' },
      'social_analyst': { name: '社交分析师', icon: '💬' },
      'china_market': { name: '中国市场', icon: '🇨🇳' },
      'industry': { name: '行业分析', icon: '🏭' },
      'macro': { name: '宏观分析', icon: '🌍' },
      'technical': { name: '技术分析', icon: '📈' },
      'funds': { name: '资金流向', icon: '💰' },
      'fundamental': { name: '基本面', icon: '📊' }
    }

    // 窗口样式
    const windowStyle = computed(() => ({
      left: `${windowPosition.value.x}px`,
      top: `${windowPosition.value.y}px`,
      width: `${windowSize.value.width}px`,
      maxHeight: `${windowSize.value.height}px`
    }))
    
    // 拖拽功能
    const startDrag = (e) => {
      isDragging.value = true
      dragStart.value = {
        x: e.clientX - windowPosition.value.x,
        y: e.clientY - windowPosition.value.y
      }
      
      document.addEventListener('mousemove', onDrag)
      document.addEventListener('mouseup', stopDrag)
      e.preventDefault()
    }
    
    const onDrag = (e) => {
      if (!isDragging.value) return
      
      windowPosition.value = {
        x: e.clientX - dragStart.value.x,
        y: e.clientY - dragStart.value.y
      }
    }
    
    const stopDrag = () => {
      isDragging.value = false
      document.removeEventListener('mousemove', onDrag)
      document.removeEventListener('mouseup', stopDrag)
    }
    
    // 活跃的智能体（有日志的）
    const activeAgents = computed(() => {
      const agents = [{ id: 'all', name: '全部', icon: '📋', logCount: totalLogs.value }]
      
      for (const [agentId, logs] of Object.entries(agentLogs.value)) {
        if (logs.length > 0) {
          const config = agentConfigs[agentId] || { name: agentId, icon: '🤖' }
          agents.push({
            id: agentId,
            name: config.name,
            icon: config.icon,
            logCount: logs.length
          })
        }
      }
      
      return agents
    })

    // 当前显示的日志
    const currentLogs = computed(() => {
      if (currentAgent.value === 'all') {
        // 合并所有日志并按时间排序
        const allLogs = []
        for (const logs of Object.values(agentLogs.value)) {
          allLogs.push(...logs)
        }
        return allLogs.sort((a, b) => new Date(a.timestamp) - new Date(b.timestamp))
      } else {
        return agentLogs.value[currentAgent.value] || []
      }
    })

    // 总日志数
    const totalLogs = computed(() => {
      let total = 0
      for (const logs of Object.values(agentLogs.value)) {
        total += logs.length
      }
      return total
    })

    // 建立 SSE 连接
    const connectAgent = (agentId) => {
      if (eventSources.value[agentId]) {
        console.log(`[GlobalLogWindow] ${agentId} 已连接，跳过`)
        return
      }

      const url = `http://localhost:8000/api/agent-logs/stream/${agentId}`
      console.log(`[GlobalLogWindow] 连接到: ${url}`)

      const eventSource = new EventSource(url)
      eventSources.value[agentId] = eventSource

      // 初始化日志数组
      if (!agentLogs.value[agentId]) {
        agentLogs.value[agentId] = []
      }

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)

          if (data.type === 'end') {
            console.log(`[GlobalLogWindow] ${agentId} 日志流结束`)
            eventSource.close()
            delete eventSources.value[agentId]
            return
          }

          if (data.type === 'connected') {
            console.log(`[GlobalLogWindow] ${agentId} 已连接`)
            return
          }

          // 添加日志
          agentLogs.value[agentId].push({
            type: data.type,
            message: data.message,
            timestamp: data.timestamp,
            agentId: agentId
          })

          // 限制日志数量（每个智能体最多100条）
          if (agentLogs.value[agentId].length > 100) {
            agentLogs.value[agentId].shift()
          }

          // 自动滚动到底部
          nextTick(() => {
            scrollToBottom()
          })

        } catch (error) {
          console.error(`[GlobalLogWindow] ${agentId} 解析错误:`, error)
        }
      }

      eventSource.onerror = (error) => {
        console.error(`[GlobalLogWindow] ${agentId} 连接错误:`, error)
        eventSource.close()
        delete eventSources.value[agentId]
      }
    }

    // 断开 SSE 连接
    const disconnectAgent = (agentId) => {
      if (eventSources.value[agentId]) {
        console.log(`[GlobalLogWindow] 断开: ${agentId}`)
        eventSources.value[agentId].close()
        delete eventSources.value[agentId]
      }
    }

    // 断开所有连接
    const disconnectAll = () => {
      for (const agentId in eventSources.value) {
        disconnectAgent(agentId)
      }
    }

    // 清空日志
    const clearLogs = () => {
      agentLogs.value = {}
      currentAgent.value = 'all'
    }

    // 切换最小化
    const toggleMinimize = () => {
      isMinimized.value = !isMinimized.value
    }

    // 关闭窗口
    const close = () => {
      disconnectAll()
      clearLogs()
      emit('update:visible', false)
    }

    // 滚动到底部
    const scrollToBottom = () => {
      const container = logMessagesRef.value
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    }

    // 格式化时间
    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      const hours = String(date.getHours()).padStart(2, '0')
      const minutes = String(date.getMinutes()).padStart(2, '0')
      const seconds = String(date.getSeconds()).padStart(2, '0')
      return `${hours}:${minutes}:${seconds}`
    }

    // 获取日志图标
    const getLogIcon = (type) => {
      const icons = {
        'info': 'ℹ️',
        'success': '✅',
        'error': '❌',
        'progress': '🔍',
        'warning': '⚠️'
      }
      return icons[type] || '💬'
    }

    // 监听 visible 变化
    watch(() => props.visible, (newVal) => {
      if (!newVal) {
        disconnectAll()
        clearLogs()
      }
    })

    // 组件销毁前清理
    onBeforeUnmount(() => {
      disconnectAll()
    })

    // 暴露方法给父组件
    const connectAgentLog = (agentId) => {
      connectAgent(agentId)
    }

    const disconnectAgentLog = (agentId) => {
      disconnectAgent(agentId)
    }

    return {
      isMinimized,
      currentAgent,
      logMessagesRef,
      windowRef,
      windowStyle,
      startDrag,
      activeAgents,
      currentLogs,
      totalLogs,
      clearLogs,
      toggleMinimize,
      close,
      formatTime,
      getLogIcon,
      connectAgentLog,
      disconnectAgentLog
    }
  }
}
</script>

<style scoped>
.global-log-window {
  position: fixed;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 6px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(6px);
  z-index: 1000;
  display: flex;
  flex-direction: column;
  transition: opacity 0.2s ease;
  user-select: none;
}

.global-log-window.minimized {
  max-height: 50px;
}

/* 标题栏 */
.log-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
  background: rgba(30, 41, 59, 0.2);
  border-radius: 6px 6px 0 0;
  cursor: move;
  user-select: none;
}

.log-header:active {
  cursor: grabbing;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.log-icon {
  font-size: 14px;
}

.log-title {
  font-size: 12px;
  font-weight: 500;
  color: #94a3b8;
}

.log-count {
  font-size: 10px;
  color: #64748b;
  background: rgba(71, 85, 105, 0.3);
  padding: 1px 6px;
  border-radius: 8px;
}

.header-right {
  display: flex;
  gap: 4px;
}

.header-btn {
  width: 22px;
  height: 22px;
  border: none;
  background: rgba(71, 85, 105, 0.2);
  color: #64748b;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
}

.header-btn:hover {
  background: rgba(71, 85, 105, 0.5);
  color: #e2e8f0;
}

/* 日志内容区 */
.log-content {
  display: flex;
  flex-direction: column;
  flex: 1;
  overflow: hidden;
}

/* 智能体标签页 */
.agent-tabs {
  display: flex;
  gap: 3px;
  padding: 4px 8px;
  overflow-x: auto;
  border-bottom: 1px solid rgba(71, 85, 105, 0.2);
  background: rgba(30, 41, 59, 0.2);
}

.agent-tabs::-webkit-scrollbar {
  height: 4px;
}

.agent-tabs::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
}

.agent-tabs::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.5);
  border-radius: 2px;
}

.agent-tab {
  display: flex;
  align-items: center;
  gap: 3px;
  padding: 4px 8px;
  border: none;
  background: rgba(71, 85, 105, 0.15);
  color: #64748b;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 11px;
  white-space: nowrap;
}

.agent-tab:hover {
  background: rgba(71, 85, 105, 0.4);
  color: #e2e8f0;
}

.agent-tab.active {
  background: rgba(59, 130, 246, 0.3);
  color: #60a5fa;
  font-weight: 600;
}

.agent-icon {
  font-size: 14px;
}

.agent-name {
  font-size: 12px;
}

.agent-count {
  font-size: 10px;
  background: rgba(59, 130, 246, 0.2);
  padding: 1px 6px;
  border-radius: 8px;
}

/* 日志消息列表 */
.log-messages {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.log-messages::-webkit-scrollbar {
  width: 6px;
}

.log-messages::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
  border-radius: 3px;
}

.log-messages::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.5);
  border-radius: 3px;
}

.log-messages::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.7);
}

.log-message {
  display: flex;
  align-items: flex-start;
  gap: 6px;
  padding: 5px 8px;
  border-radius: 4px;
  font-size: 11px;
  line-height: 1.3;
  animation: slideIn 0.2s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.log-time {
  flex-shrink: 0;
  font-size: 9px;
  color: #475569;
  font-family: 'Courier New', monospace;
  min-width: 50px;
}

.log-icon {
  flex-shrink: 0;
  font-size: 14px;
}

.log-text {
  flex: 1;
  word-break: break-word;
  color: #e2e8f0;
}

/* 日志类型样式 */
.log-info {
  background: rgba(59, 130, 246, 0.1);
  border-left: 3px solid rgba(59, 130, 246, 0.5);
}

.log-success {
  background: rgba(34, 197, 94, 0.1);
  border-left: 3px solid rgba(34, 197, 94, 0.5);
}

.log-error {
  background: rgba(239, 68, 68, 0.1);
  border-left: 3px solid rgba(239, 68, 68, 0.5);
}

.log-progress {
  background: rgba(251, 191, 36, 0.1);
  border-left: 3px solid rgba(251, 191, 36, 0.5);
}

.log-warning {
  background: rgba(251, 146, 60, 0.1);
  border-left: 3px solid rgba(251, 146, 60, 0.5);
}

.log-empty {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 40px 20px;
  color: #64748b;
  font-size: 13px;
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(59, 130, 246, 0.3);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .global-log-window {
    top: 60px !important;
    left: 0.5rem !important;
    right: 0.5rem !important;
    width: calc(100vw - 1rem) !important;
    max-width: calc(100vw - 1rem) !important;
    max-height: 40vh;
  }
  
  .global-log-window.minimized {
    max-height: 40px;
  }
  
  .log-header {
    padding: 0.5rem;
  }
  
  .log-title {
    font-size: 0.75rem;
  }
  
  .log-count {
    font-size: 0.625rem;
    padding: 0.125rem 0.375rem;
  }
  
  .agent-tabs {
    padding: 0.5rem;
    gap: 0.375rem;
    overflow-x: auto;
    flex-wrap: nowrap;
  }
  
  .agent-tab {
    padding: 0.375rem 0.5rem;
    font-size: 0.625rem;
    white-space: nowrap;
  }
  
  .log-messages {
    padding: 0.5rem;
    gap: 0.375rem;
  }
  
  .log-message {
    padding: 0.375rem;
    font-size: 0.625rem;
  }
  
  .header-btn {
    width: 1.75rem;
    height: 1.75rem;
    font-size: 0.875rem;
  }
}
</style>
