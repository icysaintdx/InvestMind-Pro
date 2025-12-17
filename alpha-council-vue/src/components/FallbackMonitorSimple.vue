<template>
  <div v-if="visible" class="fallback-monitor-overlay" @click.self="handleClose">
    <div class="fallback-monitor-dialog">
      <div class="dialog-header">
        <h3>🔍 降级监控面板</h3>
        <button @click="handleClose" class="close-btn">×</button>
      </div>
      
      <div class="fallback-monitor-content">
        <!-- 统计概览 -->
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-title">总请求数</div>
            <div class="stat-value">{{ stats.total }}</div>
          </div>
          <div class="stat-card">
            <div class="stat-title">成功率</div>
            <div class="stat-value">{{ stats.successRate }}%</div>
          </div>
          <div class="stat-card compressed">
            <div class="stat-title">压缩响应</div>
            <div class="stat-value">{{ stats.compressed }}</div>
          </div>
          <div class="stat-card defaults">
            <div class="stat-title">默认响应</div>
            <div class="stat-value">{{ stats.defaults }}</div>
          </div>
        </div>
        
        <!-- 降级详情 -->
        <div class="section">
          <div class="section-header">
            <h4>降级历史记录</h4>
            <button @click="refreshStats" :disabled="loading" class="refresh-btn">
              {{ loading ? '刷新中...' : '刷新' }}
            </button>
          </div>
          
          <div class="table-container">
            <table class="data-table" v-if="recentFallbacks.length > 0">
              <thead>
                <tr>
                  <th>时间</th>
                  <th>智能体</th>
                  <th>降级级别</th>
                  <th>原因</th>
                  <th>耗时</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, index) in recentFallbacks" :key="index">
                  <td>{{ item.time }}</td>
                  <td>{{ item.agent }}</td>
                  <td>
                    <span :class="['level-badge', getLevelClass(item.level)]">
                      {{ getLevelText(item.level) }}
                    </span>
                  </td>
                  <td>{{ item.reason }}</td>
                  <td>{{ item.duration }}s</td>
                </tr>
              </tbody>
            </table>
            <div v-else class="no-data">暂无降级记录</div>
          </div>
        </div>
        
        <!-- 智能体统计 -->
        <div class="section">
          <h4>智能体降级统计</h4>
          <div class="table-container">
            <table class="data-table" v-if="agentStats.length > 0">
              <thead>
                <tr>
                  <th>智能体</th>
                  <th>总请求</th>
                  <th>正常</th>
                  <th>压缩</th>
                  <th>默认</th>
                  <th>成功率</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(agent, index) in agentStats" :key="index">
                  <td>{{ agent.name }}</td>
                  <td>{{ agent.total }}</td>
                  <td>{{ agent.normal }}</td>
                  <td>{{ agent.compressed }}</td>
                  <td>{{ agent.defaults }}</td>
                  <td>
                    <div class="progress-bar">
                      <div 
                        class="progress-fill" 
                        :style="{ width: agent.successRate + '%' }"
                        :class="getProgressClass(agent.successRate)"
                      >
                        {{ agent.successRate }}%
                      </div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
            <div v-else class="no-data">暂无统计数据</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
/* eslint-disable no-undef */
import { ref, watch, onMounted, onUnmounted } from 'vue'

// defineProps and defineEmits are compiler macros and don't need to be imported
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  fallbackData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:visible', 'close'])

const loading = ref(false)

const stats = ref({
  total: 0,
  successRate: 100,
  compressed: 0,
  defaults: 0
})

const recentFallbacks = ref([])
const agentStats = ref([])

const handleClose = () => {
  emit('update:visible', false)
  emit('close')
}

// 获取级别样式类
const getLevelClass = (level) => {
  if (level === 99) return 'level-danger'
  if (level >= 2) return 'level-warning'
  if (level === 1) return 'level-info'
  return 'level-success'
}

// 获取级别文本
const getLevelText = (level) => {
  if (level === 99) return '默认'
  if (level === 3) return '最小化'
  if (level === 2) return '深度压缩'
  if (level === 1) return '轻度压缩'
  if (level === 0) return '正常'
  return `L${level}`
}

// 获取进度条样式类
const getProgressClass = (percentage) => {
  if (percentage >= 95) return 'progress-excellent'
  if (percentage >= 80) return 'progress-good'
  if (percentage >= 60) return 'progress-warning'
  return 'progress-danger'
}

// 刷新统计数据
const refreshStats = async () => {
  loading.value = true
  
  try {
    // 从后端获取降级统计
    const response = await fetch('/api/fallback/stats')
    
    if (response.ok) {
      const data = await response.json()
      
      // 更新统计数据
      if (data.summary) {
        stats.value = data.summary
      }
      
      // 更新最近降级记录
      if (data.recent) {
        recentFallbacks.value = data.recent
      }
      
      // 更新智能体统计
      if (data.agents) {
        agentStats.value = data.agents
      }
      
      console.log('统计数据已更新')
    } else {
      // 使用模拟数据
      loadMockData()
    }
  } catch (error) {
    console.error('获取降级统计失败:', error)
    // 使用模拟数据
    loadMockData()
  } finally {
    loading.value = false
  }
}

// 加载模拟数据
const loadMockData = () => {
  // 使用 props.fallbackData 或生成模拟数据
  const data = props.fallbackData
  
  if (data.agentFallbackLevels) {
    // 计算统计数据
    const levels = Object.values(data.agentFallbackLevels)
    const total = levels.length
    const compressed = levels.filter(l => l > 0 && l < 99).length
    const defaults = levels.filter(l => l === 99).length
    const normal = levels.filter(l => l === 0).length
    
    stats.value = {
      total,
      successRate: total > 0 ? Math.round((normal / total) * 100) : 100,
      compressed,
      defaults
    }
    
    // 生成最近记录
    const now = new Date()
    recentFallbacks.value = Object.entries(data.agentFallbackLevels)
      .filter(([, level]) => level > 0)
      .map(([agentId, level], index) => ({
        time: new Date(now - index * 60000).toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'}),
        agent: agentId,
        level,
        reason: level === 99 ? '超时' : '负载高',
        duration: Math.round(10 + Math.random() * 20)
      }))
    
    // 生成智能体统计
    const agentMap = {}
    Object.entries(data.agentFallbackLevels).forEach(([agentId, level]) => {
      if (!agentMap[agentId]) {
        agentMap[agentId] = {
          name: agentId,
          total: 0,
          normal: 0,
          compressed: 0,
          defaults: 0
        }
      }
      
      agentMap[agentId].total++
      if (level === 0) agentMap[agentId].normal++
      else if (level === 99) agentMap[agentId].defaults++
      else agentMap[agentId].compressed++
    })
    
    agentStats.value = Object.values(agentMap).map(agent => ({
      ...agent,
      successRate: agent.total > 0 ? Math.round((agent.normal / agent.total) * 100) : 100
    }))
  }
}

// 监听可见性变化
watch(() => props.visible, (newVal) => {
  if (newVal) {
    refreshStats()
  }
})

onMounted(() => {
  // 定期刷新（如果对话框打开）
  const interval = setInterval(() => {
    if (props.visible) {
      refreshStats()
    }
  }, 30000) // 30秒刷新一次
  
  // 清理定时器
  onUnmounted(() => {
    clearInterval(interval)
  })
})
/* eslint-enable no-undef */
</script>

<style scoped>
.fallback-monitor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.fallback-monitor-dialog {
  background: #1e293b;
  border-radius: 12px;
  width: 90%;
  max-width: 900px;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.5);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.dialog-header h3 {
  margin: 0;
  color: #fff;
  font-size: 1.25rem;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 2rem;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.fallback-monitor-content {
  padding: 1.5rem;
  overflow-y: auto;
  flex: 1;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  padding: 1.25rem;
  text-align: center;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.stat-card.compressed {
  background: rgba(59, 130, 246, 0.1);
  border-color: rgba(59, 130, 246, 0.3);
}

.stat-card.defaults {
  background: rgba(251, 146, 60, 0.1);
  border-color: rgba(251, 146, 60, 0.3);
}

.stat-title {
  color: #94a3b8;
  font-size: 0.875rem;
  margin-bottom: 0.5rem;
}

.stat-value {
  color: #fff;
  font-size: 1.75rem;
  font-weight: bold;
}

.section {
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section h4 {
  color: #fff;
  margin: 0 0 1rem 0;
}

.refresh-btn {
  padding: 0.5rem 1rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.5);
  color: #3b82f6;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover {
  background: rgba(59, 130, 246, 0.3);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.table-container {
  background: rgba(0, 0, 0, 0.3);
  border-radius: 8px;
  overflow: hidden;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th {
  background: rgba(0, 0, 0, 0.5);
  color: #94a3b8;
  padding: 0.75rem;
  text-align: left;
  font-weight: 500;
  font-size: 0.875rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.data-table td {
  color: #e2e8f0;
  padding: 0.75rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
}

.data-table tbody tr:hover {
  background: rgba(255, 255, 255, 0.05);
}

.level-badge {
  display: inline-block;
  padding: 0.25rem 0.75rem;
  border-radius: 9999px;
  font-size: 0.75rem;
  font-weight: 500;
}

.level-success {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.level-info {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.level-warning {
  background: rgba(251, 146, 60, 0.2);
  color: #fb923c;
}

.level-danger {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.progress-bar {
  width: 100px;
  height: 20px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 0.75rem;
  color: #fff;
  font-weight: 500;
  transition: width 0.3s ease;
}

.progress-excellent {
  background: #22c55e;
}

.progress-good {
  background: #3b82f6;
}

.progress-warning {
  background: #fb923c;
}

.progress-danger {
  background: #ef4444;
}

.no-data {
  padding: 2rem;
  text-align: center;
  color: #64748b;
}

@media (max-width: 768px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .fallback-monitor-dialog {
    width: 95%;
    max-height: 90vh;
  }
}</style>
