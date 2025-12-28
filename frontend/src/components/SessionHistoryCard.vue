<template>
  <div class="history-card" :class="`status-${session.status}`">
    <div class="card-header">
      <div class="stock-info">
        <span class="stock-code">{{ session.stock_code }}</span>
        <span class="stock-name" v-if="session.stock_name">{{ session.stock_name }}</span>
      </div>
      <div class="status-badge" :class="`status-${session.status}`">
        {{ statusText }}
      </div>
    </div>
    
    <div class="card-body">
      <div class="info-row">
        <span class="label">📅 时间:</span>
        <span class="value">{{ formatDate(session.created_at) }}</span>
      </div>
      
      <div class="info-row">
        <span class="label">⏱️ 耗时:</span>
        <span class="value">{{ formatDuration(session) }}</span>
      </div>
      
      <div class="info-row">
        <span class="label">📊 进度:</span>
        <div class="progress-bar">
          <div class="progress-fill" :style="{width: session.progress + '%'}"></div>
          <span class="progress-text">{{ session.progress }}%</span>
        </div>
      </div>
      
      <div class="info-row" v-if="session.error_message">
        <span class="label">⚠️ 错误:</span>
        <span class="value error">{{ session.error_message }}</span>
      </div>
    </div>
    
    <div class="card-footer">
      <button @click="$emit('view-detail', session)" class="btn-detail">
        📋 查看详情
      </button>
      <button @click="$emit('reanalyze', session)" class="btn-reanalyze">
        🔄 重新分析
      </button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'SessionHistoryCard',
  props: {
    session: {
      type: Object,
      required: true
    }
  },
  emits: ['view-detail', 'reanalyze'],
  computed: {
    statusText() {
      const map = {
        'created': '已创建',
        'running': '运行中',
        'completed': '已完成',
        'error': '失败'
      }
      return map[this.session.status] || this.session.status
    }
  },
  methods: {
    formatDate(dateStr) {
      if (!dateStr) return '-'
      const date = new Date(dateStr)
      return date.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    },
    formatDuration(session) {
      if (!session.start_time) return '-'
      
      const start = new Date(session.start_time * 1000)
      const end = session.end_time ? new Date(session.end_time * 1000) : new Date()
      const seconds = Math.floor((end - start) / 1000)
      
      if (seconds < 60) return `${seconds}秒`
      if (seconds < 3600) return `${Math.floor(seconds / 60)}分钟`
      return `${Math.floor(seconds / 3600)}小时${Math.floor((seconds % 3600) / 60)}分钟`
    }
  }
}
</script>

<style scoped>
.history-card {
  background: rgba(30, 41, 59, 0.6);
  backdrop-filter: blur(12px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
  transition: all 0.3s;
}

.history-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.3);
  border-color: rgba(59, 130, 246, 0.5);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.stock-info {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.stock-code {
  font-size: 1.25rem;
  font-weight: bold;
  color: #3b82f6;
}

.stock-name {
  font-size: 1rem;
  color: rgba(255, 255, 255, 0.7);
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.status-badge.status-completed {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  border: 1px solid #22c55e;
}

.status-badge.status-running {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  border: 1px solid #3b82f6;
  animation: pulse 2s ease-in-out infinite;
}

.status-badge.status-error {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid #ef4444;
}

.status-badge.status-created {
  background: rgba(156, 163, 175, 0.2);
  color: #9ca3af;
  border: 1px solid #9ca3af;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.card-body {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-bottom: 1rem;
}

.info-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.label {
  min-width: 80px;
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.875rem;
}

.value {
  color: rgba(255, 255, 255, 0.9);
  font-size: 0.875rem;
}

.value.error {
  color: #ef4444;
}

.progress-bar {
  flex: 1;
  height: 1.5rem;
  background: rgba(15, 23, 42, 0.8);
  border-radius: 0.5rem;
  position: relative;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #3b82f6, #2563eb);
  transition: width 0.3s;
}

.progress-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: white;
  font-size: 0.75rem;
  font-weight: 500;
}

.card-footer {
  display: flex;
  gap: 0.75rem;
}

.btn-detail,
.btn-reanalyze {
  flex: 1;
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  border: none;
}

.btn-detail {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  border: 1px solid #3b82f6;
}

.btn-detail:hover {
  background: rgba(59, 130, 246, 0.3);
  transform: translateY(-1px);
}

.btn-reanalyze {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  border: 1px solid #22c55e;
}

.btn-reanalyze:hover {
  background: rgba(34, 197, 94, 0.3);
  transform: translateY(-1px);
}
</style>
