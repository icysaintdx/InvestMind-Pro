<template>
  <div class="history-container">
    <div class="history-header">
      <h1>📊 分析历史</h1>
      <p class="subtitle">查看所有历史分析记录和统计数据</p>
    </div>
    
    <!-- 搜索和筛选 -->
    <div class="search-section">
      <div class="search-box">
        <input 
          v-model="searchCode" 
          type="text" 
          placeholder="输入股票代码搜索（如：600000）"
          @keyup.enter="searchByCode"
          class="search-input"
        />
        <button @click="searchByCode" class="search-btn">🔍 搜索</button>
        <button @click="loadRecent" class="reset-btn">🔄 显示全部</button>
      </div>
    </div>
    
    <!-- 统计概览 -->
    <div class="stats-section" v-if="stats">
      <div class="stat-card">
        <div class="stat-icon">📈</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.total_count || 0 }}</div>
          <div class="stat-label">总分析次数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">✅</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.status_distribution?.completed || 0 }}</div>
          <div class="stat-label">成功完成</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">⏱️</div>
        <div class="stat-content">
          <div class="stat-value">{{ formatSeconds(stats.avg_duration_seconds) }}</div>
          <div class="stat-label">平均耗时</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon">❌</div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.status_distribution?.error || 0 }}</div>
          <div class="stat-label">失败次数</div>
        </div>
      </div>
    </div>
    
    <!-- 历史记录列表 -->
    <div class="history-list">
      <div class="list-header">
        <h2>{{ listTitle }}</h2>
        <span class="count">共 {{ sessions.length }} 条记录</span>
      </div>
      
      <div v-if="loading" class="loading">
        <div class="spinner"></div>
        <p>加载中...</p>
      </div>
      
      <div v-else-if="sessions.length === 0" class="empty">
        <div class="empty-icon">📭</div>
        <p>暂无历史记录</p>
        <button @click="$router.push('/')" class="start-btn">开始第一次分析</button>
      </div>
      
      <div v-else class="sessions-grid">
        <SessionHistoryCard
          v-for="session in sessions"
          :key="session.session_id"
          :session="session"
          @view-detail="viewDetail"
          @reanalyze="reanalyze"
        />
      </div>
    </div>
    
    <!-- 详情弹窗 -->
    <div v-if="showDetail" class="modal-overlay" @click="closeDetail">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h2>📋 分析详情</h2>
          <button @click="closeDetail" class="close-btn">✕</button>
        </div>
        
        <div class="modal-body" v-if="detailSession">
          <div class="detail-section">
            <h3>基本信息</h3>
            <div class="detail-grid">
              <div class="detail-item">
                <span class="detail-label">股票代码:</span>
                <span class="detail-value">{{ detailSession.stock_code }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">股票名称:</span>
                <span class="detail-value">{{ detailSession.stock_name || '-' }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">状态:</span>
                <span class="detail-value">{{ getStatusText(detailSession.status) }}</span>
              </div>
              <div class="detail-item">
                <span class="detail-label">进度:</span>
                <span class="detail-value">{{ detailSession.progress }}%</span>
              </div>
            </div>
          </div>
          
          <div class="detail-section" v-if="agentResults.length > 0">
            <h3>智能体结果 ({{ agentResults.length }}/21)</h3>
            <div class="agents-list">
              <div 
                v-for="agent in agentResults" 
                :key="agent.agent_id"
                class="agent-item"
              >
                <div class="agent-header">
                  <span class="agent-name">{{ agent.agent_name }}</span>
                  <span class="agent-tokens">{{ agent.tokens }} tokens</span>
                </div>
                <div class="agent-output">{{ agent.output?.substring(0, 200) }}...</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import SessionHistoryCard from '@/components/SessionHistoryCard.vue'

export default {
  name: 'HistoryView',
  components: {
    SessionHistoryCard
  },
  setup() {
    const loading = ref(false)
    const sessions = ref([])
    const stats = ref(null)
    const searchCode = ref('')
    const listTitle = ref('最近分析')
    
    const showDetail = ref(false)
    const detailSession = ref(null)
    const agentResults = ref([])
    
    // 加载最近分析
    const loadRecent = async () => {
      loading.value = true
      listTitle.value = '最近分析'
      searchCode.value = ''
      
      try {
        const response = await fetch('/api/analysis/db/history/recent?limit=20')
        const data = await response.json()
        sessions.value = data.sessions || []
      } catch (error) {
        console.error('加载历史失败:', error)
        alert('加载失败，请检查后端服务')
      } finally {
        loading.value = false
      }
    }
    
    // 按股票代码搜索
    const searchByCode = async () => {
      if (!searchCode.value.trim()) {
        loadRecent()
        return
      }
      
      loading.value = true
      listTitle.value = `股票 ${searchCode.value} 的历史`
      
      try {
        const response = await fetch(
          `/api/analysis/db/history/stock/${searchCode.value}?limit=20`
        )
        const data = await response.json()
        sessions.value = data.sessions || []
      } catch (error) {
        console.error('搜索失败:', error)
        alert('搜索失败')
      } finally {
        loading.value = false
      }
    }
    
    // 加载统计数据
    const loadStats = async () => {
      try {
        const response = await fetch('/api/analysis/db/stats/overview?days=30')
        const data = await response.json()
        stats.value = data.analysis
      } catch (error) {
        console.error('加载统计失败:', error)
      }
    }
    
    // 查看详情
    const viewDetail = async (session) => {
      try {
        const response = await fetch(
          `/api/analysis/db/history/session/${session.session_id}/full`
        )
        const data = await response.json()
        
        detailSession.value = data.session
        agentResults.value = data.agent_results || []
        showDetail.value = true
      } catch (error) {
        console.error('加载详情失败:', error)
        alert('加载详情失败')
      }
    }
    
    // 关闭详情
    const closeDetail = () => {
      showDetail.value = false
      detailSession.value = null
      agentResults.value = []
    }
    
    // 重新分析
    const reanalyze = (session) => {
      // 由于没有 router，直接关闭弹窗并提示用户
      alert(`请在主页面输入股票代码 ${session.stock_code} 进行分析`)
      // 可以通过 emit 事件通知父组件
    }
    
    // 格式化秒数
    const formatSeconds = (seconds) => {
      if (!seconds) return '-'
      if (seconds < 60) return `${seconds}秒`
      return `${Math.floor(seconds / 60)}分钟`
    }
    
    // 获取状态文本
    const getStatusText = (status) => {
      const map = {
        'created': '已创建',
        'running': '运行中',
        'completed': '已完成',
        'error': '失败'
      }
      return map[status] || status
    }
    
    // 初始化
    onMounted(() => {
      loadRecent()
      loadStats()
    })
    
    return {
      loading,
      sessions,
      stats,
      searchCode,
      listTitle,
      showDetail,
      detailSession,
      agentResults,
      loadRecent,
      searchByCode,
      viewDetail,
      closeDetail,
      reanalyze,
      formatSeconds,
      getStatusText
    }
  }
}
</script>

<style scoped>
.history-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: 100vh;
}

.history-header {
  text-align: center;
  margin-bottom: 3rem;
}

.history-header h1 {
  font-size: 2.5rem;
  margin-bottom: 0.5rem;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}

.subtitle {
  color: rgba(255, 255, 255, 0.6);
  font-size: 1.1rem;
}

.search-section {
  margin-bottom: 2rem;
}

.search-box {
  display: flex;
  gap: 1rem;
  max-width: 800px;
  margin: 0 auto;
}

.search-input {
  flex: 1;
  padding: 0.75rem 1rem;
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  color: white;
  font-size: 1rem;
}

.search-btn,
.reset-btn {
  padding: 0.75rem 1.5rem;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.search-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.search-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
}

.reset-btn {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
  border: 1px solid #9ca3af;
}

.reset-btn:hover {
  background: rgba(156, 163, 175, 0.3);
}

.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: rgba(30, 41, 59, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #3b82f6;
}

.stat-label {
  font-size: 0.875rem;
  color: rgba(255, 255, 255, 0.6);
}

.history-list {
  background: rgba(30, 41, 59, 0.4);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  padding: 2rem;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.list-header h2 {
  font-size: 1.5rem;
}

.count {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.875rem;
}

.loading {
  text-align: center;
  padding: 3rem;
}

.spinner {
  width: 50px;
  height: 50px;
  border: 4px solid rgba(59, 130, 246, 0.2);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 1rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty {
  text-align: center;
  padding: 3rem;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.start-btn {
  margin-top: 1rem;
  padding: 0.75rem 2rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.start-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
}

.sessions-grid {
  display: grid;
  gap: 1rem;
}

/* 弹窗样式 */
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
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  max-width: 900px;
  width: 90%;
  max-height: 80vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.close-btn {
  background: none;
  border: none;
  color: white;
  font-size: 1.5rem;
  cursor: pointer;
  padding: 0.5rem;
}

.modal-body {
  padding: 1.5rem;
  overflow-y: auto;
}

.detail-section {
  margin-bottom: 2rem;
}

.detail-section h3 {
  margin-bottom: 1rem;
  color: #3b82f6;
}

.detail-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.detail-item {
  display: flex;
  gap: 0.5rem;
}

.detail-label {
  color: rgba(255, 255, 255, 0.6);
  min-width: 100px;
}

.detail-value {
  color: white;
}

.agents-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.agent-item {
  background: rgba(30, 41, 59, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.5rem;
  padding: 1rem;
}

.agent-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.agent-name {
  font-weight: 500;
  color: #3b82f6;
}

.agent-tokens {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.875rem;
}

.agent-output {
  color: rgba(255, 255, 255, 0.8);
  font-size: 0.875rem;
  line-height: 1.5;
}
</style>
