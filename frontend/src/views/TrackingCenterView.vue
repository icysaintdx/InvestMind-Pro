<template>
  <div class="tracking-center-container">
    <div class="page-header">
      <div>
        <h1>🔄 跟踪验证中心</h1>
        <p class="subtitle">监控跟踪任务与验证报告，闭环验证策略效果</p>
      </div>
      <div class="header-actions">
        <button class="btn-secondary" @click="loadTrackingTasks" :disabled="loadingTasks">
          🔁 刷新任务
        </button>
        <button class="btn-secondary" @click="loadVerifications" :disabled="loadingVerifications">
          🧾 刷新验证
        </button>
      </div>
    </div>

    <div class="grid">
      <!-- 跟踪任务列表 -->
      <section class="card">
        <div class="section-header">
          <h2>📋 跟踪任务</h2>
          <span class="badge">{{ trackingTasks.length }}</span>
        </div>
        <div v-if="loadingTasks" class="loading-state">
          <div class="spinner"></div>
          <p>加载任务中...</p>
        </div>
        <div v-else-if="trackingTasks.length === 0" class="empty-state">
          <div class="empty-icon">📭</div>
          <p>暂无跟踪任务，建议在分析总结页面创建</p>
        </div>
        <div v-else class="task-list">
          <div
            v-for="task in trackingTasks"
            :key="task.task_id"
            class="task-item"
          >
            <div class="task-head">
              <div>
                <h3>{{ task.stock_code }}</h3>
                <p>{{ task.initial_analysis?.stock_name || '未命名' }}</p>
              </div>
              <span :class="['status-pill', task.status]">{{ getTaskStatus(task.status) }}</span>
            </div>
            <div class="task-meta">
              <div>
                <p class="meta-label">创建时间</p>
                <p class="meta-value">{{ formatDate(task.created_at) }}</p>
              </div>
              <div>
                <p class="meta-label">巡检次数</p>
                <p class="meta-value">{{ task.check_count }} / 触发 {{ task.trigger_count }}</p>
              </div>
              <div>
                <p class="meta-label">结束日期</p>
                <p class="meta-value">{{ formatDate(task.end_date) }}</p>
              </div>
            </div>
            <div class="task-actions">
              <button class="btn-secondary" @click="openTask(task)">详情</button>
              <button class="btn-secondary" @click="checkTask(task.task_id)">手动检查</button>
              <button
                class="btn-secondary"
                @click="toggleTask(task)"
              >
                {{ task.status === 'active' ? '暂停' : '恢复' }}
              </button>
            </div>
          </div>
        </div>
      </section>

      <!-- 验证报告 -->
      <section class="card">
        <div class="section-header">
          <h2>✅ 验证报告</h2>
          <div class="stats">
            <div>
              <p class="meta-label">累计验证</p>
              <p class="meta-value">{{ verificationStats.total_verifications }}</p>
            </div>
            <div>
              <p class="meta-label">成功率</p>
              <p class="meta-value">{{ formatPercent(verificationStats.success_rate) }}</p>
            </div>
            <div>
              <p class="meta-label">平均收益</p>
              <p class="meta-value">{{ (verificationStats.avg_profit_loss || 0).toFixed(2) }}%</p>
            </div>
          </div>
        </div>
        <div v-if="loadingVerifications" class="loading-state">
          <div class="spinner"></div>
          <p>加载验证记录中...</p>
        </div>
        <div v-else-if="verifications.length === 0" class="empty-state">
          <div class="empty-icon">🕓</div>
          <p>暂无验证记录，待跟踪任务触发后生成</p>
        </div>
        <div v-else class="verification-list">
          <div v-for="item in verifications" :key="item.verification_id" class="verification-item">
            <div class="verification-head">
              <strong>{{ item.decision_id }}</strong>
              <span :class="['result-pill', item.is_success ? 'success' : 'fail']">
                {{ item.is_success ? '成功' : '失败' }}
              </span>
            </div>
            <p class="verification-notes">{{ item.notes }}</p>
            <div class="result-meta">
              <div>
                <p class="meta-label">准确率</p>
                <p class="meta-value">{{ formatPercent(item.accuracy_rate) }}</p>
              </div>
              <div>
                <p class="meta-label">收益</p>
                <p class="meta-value">{{ item.profit_loss.toFixed(2) }}%</p>
              </div>
              <div>
                <p class="meta-label">时间</p>
                <p class="meta-value">{{ formatDate(item.timestamp) }}</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>

    <!-- 任务详情抽屉 -->
    <div v-if="showTaskDetail" class="drawer-overlay" @click.self="closeTask">
      <div class="drawer">
        <div class="drawer-header">
          <div>
            <h3>{{ activeTask.stock_code }}</h3>
            <p>{{ activeTask.initial_analysis?.stock_name || '未命名' }}</p>
          </div>
          <button class="close-btn" @click="closeTask">×</button>
        </div>
        <div class="drawer-section">
          <h4>基本信息</h4>
          <ul>
            <li>状态：{{ getTaskStatus(activeTask.status) }}</li>
            <li>创建时间：{{ formatDate(activeTask.created_at) }}</li>
            <li>结束时间：{{ formatDate(activeTask.end_date) }}</li>
            <li>触发条件：价格 {{ activeTask.trigger_condition?.price_change_threshold }}%，成交量 {{ activeTask.trigger_condition?.volume_change_threshold }}%</li>
          </ul>
        </div>
        <div class="drawer-section">
          <h4>最新LLM决策</h4>
          <div v-if="activeTask.decisions?.length" class="decision-list">
            <div v-for="record in activeTask.decisions.slice(-5).reverse()" :key="record.timestamp" class="decision-item">
              <div>
                <p class="meta-label">{{ formatDate(record.timestamp) }}</p>
                <p class="meta-value">决策：{{ record.decision }}</p>
              </div>
              <p class="decision-reason">{{ record.reason }}</p>
            </div>
          </div>
          <p v-else class="empty-text">暂无触发记录</p>
        </div>
        <div class="drawer-actions">
          <button class="btn-secondary" @click="checkTask(activeTask.task_id)">立即巡检</button>
          <button class="btn-primary" @click="closeTask">关闭</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'

export default {
  name: 'TrackingCenterView',
  setup() {
    const trackingTasks = ref([])
    const verifications = ref([])
    const verificationStats = ref({
      total_verifications: 0,
      success_rate: 0,
      avg_profit_loss: 0
    })
    const loadingTasks = ref(false)
    const loadingVerifications = ref(false)
    const showTaskDetail = ref(false)
    const activeTask = ref(null)

    const loadTrackingTasks = async () => {
      loadingTasks.value = true
      try {
        const response = await fetch('/api/tracking/tasks')
        const data = await response.json()
        trackingTasks.value = data.tasks || []
      } catch (err) {
        console.error('[TrackingCenter] loadTrackingTasks error:', err)
      } finally {
        loadingTasks.value = false
      }
    }

    const loadVerifications = async () => {
      loadingVerifications.value = true
      try {
        const response = await fetch('/api/verification/verifications')
        const data = await response.json()
        verifications.value = data.verifications || []
        verificationStats.value = data.stats || verificationStats.value
      } catch (err) {
        console.error('[TrackingCenter] loadVerifications error:', err)
      } finally {
        loadingVerifications.value = false
      }
    }

    const openTask = (task) => {
      activeTask.value = task
      showTaskDetail.value = true
    }

    const closeTask = () => {
      showTaskDetail.value = false
      activeTask.value = null
    }

    const checkTask = async (taskId) => {
      try {
        const response = await fetch(`/api/tracking/task/${taskId}/check`, {
          method: 'POST'
        })
        const data = await response.json()
        window.$toast?.success(data.result?.reason || '巡检完成')
        await loadTrackingTasks()
      } catch (err) {
        console.error('[TrackingCenter] checkTask error:', err)
        window.$toast?.error('巡检失败')
      }
    }

    const toggleTask = async (task) => {
      const action = task.status === 'active' ? 'pause' : 'resume'
      try {
        await fetch(`/api/tracking/task/${task.task_id}/${action}`, {
          method: 'POST'
        })
        await loadTrackingTasks()
      } catch (err) {
        console.error('[TrackingCenter] toggleTask error:', err)
      }
    }

    const formatDate = (value) => {
      if (!value) return '-'
      return new Date(value).toLocaleString('zh-CN')
    }

    const formatPercent = (value) => {
      if (value === null || value === undefined) return '-'
      return `${(value * 100).toFixed(2)}%`
    }

    const getTaskStatus = (status) => {
      const map = {
        active: '进行中',
        paused: '已暂停',
        completed: '已完成'
      }
      return map[status] || status
    }

    onMounted(() => {
      loadTrackingTasks()
      loadVerifications()
    })

    return {
      trackingTasks,
      verifications,
      verificationStats,
      loadingTasks,
      loadingVerifications,
      showTaskDetail,
      activeTask,
      loadTrackingTasks,
      loadVerifications,
      openTask,
      closeTask,
      checkTask,
      toggleTask,
      formatDate,
      formatPercent,
      getTaskStatus
    }
  }
}
</script>

<style scoped>
.tracking-center-container {
  padding: 2rem;
  max-width: 1400px;
  margin: 0 auto;
  min-height: calc(100vh - 160px);
  color: #e2e8f0; /* 设置默认文字颜色 */
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  margin-bottom: 0.25rem;
  color: #f1f5f9; /* 标题颜色 */
}

.subtitle {
  color: rgba(226, 232, 240, 0.7);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

.btn-primary,
.btn-secondary {
  border: none;
  border-radius: 12px;
  padding: 0.6rem 1.1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #38bdf8, #6366f1);
  color: #fff;
}

.btn-secondary {
  background: rgba(148, 163, 184, 0.15);
  color: #e2e8f0;
}

.grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 1.5rem;
}

.card {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 18px;
  padding: 1.5rem;
  box-shadow: 0 15px 35px rgba(15, 23, 42, 0.4);
  color: #e2e8f0; /* 卡片文字颜色 */
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.badge {
  border-radius: 999px;
  padding: 0.25rem 0.75rem;
  background: rgba(99, 102, 241, 0.15);
  color: #a5b4fc;
}

.section-header h2 {
  color: #f1f5f9; /* 标题颜色 */
}

.task-head h3 {
  color: #f1f5f9; /* 任务标题颜色 */
}

.task-head p {
  color: #cbd5e1; /* 任务副标题颜色 */
}

.loading-state,
.empty-state {
  border: 1px dashed rgba(148, 163, 184, 0.3);
  border-radius: 16px;
  padding: 2rem;
  text-align: center;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(148, 163, 184, 0.3);
  border-top-color: #60a5fa;
  border-radius: 50%;
  margin: 0 auto 1rem;
  animation: spin 1s linear infinite;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.task-item {
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 16px;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.5);
}

.task-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}

.status-pill {
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  font-size: 0.85rem;
}

.status-pill.active { color: #4ade80; background: rgba(74, 222, 128, 0.1); }
.status-pill.paused { color: #facc15; background: rgba(250, 204, 21, 0.1); }
.status-pill.completed { color: #a5b4fc; background: rgba(165, 180, 252, 0.1); }

.task-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.meta-label {
  font-size: 0.8rem;
  color: rgba(148, 163, 184, 0.8);
}

.meta-value {
  font-weight: 600;
  color: #f1f5f9; /* 数据值颜色 */
}

.task-actions {
  display: flex;
  gap: 0.75rem;
}

.stats {
  display: flex;
  gap: 1rem;
  justify-content: space-between;
}

.verification-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  max-height: 600px;
  overflow-y: auto;
}

.verification-item {
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 16px;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.5);
}

.verification-head {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.result-pill {
  border-radius: 999px;
  padding: 0.2rem 0.6rem;
  font-size: 0.85rem;
}

.result-pill.success { color: #4ade80; background: rgba(74, 222, 128, 0.1); }
.result-pill.fail { color: #f87171; background: rgba(248, 113, 113, 0.15); }

.result-meta {
  display: flex;
  gap: 1rem;
  flex-wrap: wrap;
  margin-top: 0.75rem;
}

.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.75);
  display: flex;
  justify-content: flex-end;
  z-index: 1000;
}

.drawer {
  width: 420px;
  height: 100%;
  background: #0f172a;
  padding: 1.5rem;
  overflow-y: auto;
}

.drawer-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.close-btn {
  border: none;
  background: transparent;
  font-size: 1.5rem;
  color: #e2e8f0;
  cursor: pointer;
}

.drawer-section {
  margin-bottom: 1.5rem;
}

.drawer-section ul {
  padding-left: 1.25rem;
}

.decision-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.decision-item {
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 0.75rem;
}

.decision-reason {
  color: rgba(226, 232, 240, 0.85);
}

.drawer-actions {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@media (max-width: 1100px) {
  .grid {
    grid-template-columns: 1fr;
  }
}
</style>
