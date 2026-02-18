<template>
  <div class="auto-trade-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>智能交易计划</h1>
      <div class="header-actions">
        <el-tag :type="monitorStatus.is_running ? 'success' : 'info'" size="large">
          {{ monitorStatus.is_running ? '监控运行中' : '监控已停止' }}
        </el-tag>
        <el-button type="primary" @click="showCreateDialog = true">
          <el-icon><Plus /></el-icon>
          新建计划
        </el-button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <el-card class="stat-card">
        <div class="stat-value">{{ plans.length }}</div>
        <div class="stat-label">总计划数</div>
      </el-card>
      <el-card class="stat-card running">
        <div class="stat-value">{{ runningPlans.length }}</div>
        <div class="stat-label">运行中</div>
      </el-card>
      <el-card class="stat-card">
        <div class="stat-value">{{ totalTrades }}</div>
        <div class="stat-label">总交易次数</div>
      </el-card>
      <el-card class="stat-card" :class="totalProfitLoss >= 0 ? 'profit' : 'loss'">
        <div class="stat-value">{{ totalProfitLoss >= 0 ? '+' : '' }}{{ totalProfitLoss.toFixed(2) }}</div>
        <div class="stat-label">累计盈亏</div>
      </el-card>
    </div>

    <!-- 交易计划列表 -->
    <div class="plans-container">
      <el-card v-for="plan in plans" :key="plan.plan_id" class="plan-card" :class="plan.status">
        <template #header>
          <div class="plan-header">
            <div class="plan-title">
              <span class="strategy-name">{{ plan.strategy_name }}</span>
              <span class="stock-info">{{ plan.stock_name }}({{ plan.stock_code }})</span>
            </div>
            <el-tag :type="getStatusType(plan.status)" size="small">
              {{ getStatusText(plan.status) }}
            </el-tag>
          </div>
        </template>

        <div class="plan-content">
          <!-- 持仓信息 -->
          <div class="position-info" v-if="plan.current_position > 0">
            <div class="info-row">
              <span class="label">持仓:</span>
              <span class="value">{{ plan.current_position }}股</span>
            </div>
            <div class="info-row">
              <span class="label">成本:</span>
              <span class="value">¥{{ plan.avg_cost.toFixed(2) }}</span>
            </div>
            <div class="info-row">
              <span class="label">现价:</span>
              <span class="value">¥{{ plan.current_price.toFixed(2) }}</span>
            </div>
            <div class="info-row" :class="plan.unrealized_pnl >= 0 ? 'profit' : 'loss'">
              <span class="label">盈亏:</span>
              <span class="value">{{ plan.unrealized_pnl >= 0 ? '+' : '' }}{{ plan.unrealized_pnl_pct }}%</span>
            </div>
          </div>

          <!-- 条件状态 -->
          <div class="conditions-status">
            <div class="condition-group" v-if="plan.current_position === 0">
              <div class="group-title">入场条件:</div>
              <div class="condition-list">
                <div
                  v-for="(cond, idx) in plan.entry_conditions_status"
                  :key="idx"
                  class="condition-item"
                  :class="{ met: cond.met }"
                >
                  <el-icon v-if="cond.met"><Check /></el-icon>
                  <el-icon v-else><Clock /></el-icon>
                  <span>{{ cond.description }}</span>
                </div>
              </div>
            </div>
            <div class="condition-group" v-else>
              <div class="group-title">出场条件:</div>
              <div class="condition-list">
                <div
                  v-for="(cond, idx) in plan.exit_conditions_status"
                  :key="idx"
                  class="condition-item"
                  :class="{ met: cond.met }"
                >
                  <el-icon v-if="cond.met"><Check /></el-icon>
                  <el-icon v-else><Clock /></el-icon>
                  <span>{{ cond.description }}</span>
                </div>
              </div>
            </div>
          </div>

          <!-- 统计信息 -->
          <div class="plan-stats">
            <div class="stat-item">
              <span class="label">信号数:</span>
              <span class="value">{{ plan.signals_generated }}</span>
            </div>
            <div class="stat-item">
              <span class="label">交易数:</span>
              <span class="value">{{ plan.trades_executed }}</span>
            </div>
            <div class="stat-item" :class="plan.total_profit_loss >= 0 ? 'profit' : 'loss'">
              <span class="label">盈亏:</span>
              <span class="value">{{ plan.total_profit_loss >= 0 ? '+' : '' }}{{ plan.total_profit_loss.toFixed(2) }}</span>
            </div>
          </div>

          <!-- 最后检查时间 -->
          <div class="last-check" v-if="plan.last_check_at">
            最后检查: {{ formatTime(plan.last_check_at) }}
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="plan-actions">
          <el-button
            v-if="plan.status !== 'running'"
            type="success"
            size="small"
            @click="startPlan(plan.plan_id)"
          >
            启动
          </el-button>
          <el-button
            v-if="plan.status === 'running'"
            type="warning"
            size="small"
            @click="pausePlan(plan.plan_id)"
          >
            暂停
          </el-button>
          <el-button
            v-if="plan.status === 'running' || plan.status === 'paused'"
            type="danger"
            size="small"
            @click="stopPlan(plan.plan_id)"
          >
            停止
          </el-button>
          <el-button
            type="info"
            size="small"
            @click="showPlanDetail(plan)"
          >
            详情
          </el-button>
          <el-button
            type="danger"
            size="small"
            plain
            @click="deletePlan(plan.plan_id)"
          >
            删除
          </el-button>
        </div>
      </el-card>

      <!-- 空状态 -->
      <el-empty v-if="plans.length === 0" description="暂无交易计划">
        <el-button type="primary" @click="showCreateDialog = true">创建第一个计划</el-button>
      </el-empty>
    </div>

    <!-- 创建计划对话框 -->
    <el-dialog v-model="showCreateDialog" title="创建交易计划" width="600px">
      <el-form :model="createForm" label-width="100px">
        <el-form-item label="选择策略">
          <el-select v-model="createForm.strategy_id" placeholder="请选择策略" @change="onStrategyChange">
            <el-option
              v-for="strategy in presetStrategies"
              :key="strategy.id"
              :label="strategy.name"
              :value="strategy.id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="股票代码">
          <el-input v-model="createForm.stock_code" placeholder="如: 000001" />
        </el-form-item>
        <el-form-item label="股票名称">
          <el-input v-model="createForm.stock_name" placeholder="如: 平安银行" />
        </el-form-item>
        <el-form-item label="计划资金">
          <el-input-number v-model="createForm.initial_capital" :min="10000" :step="10000" />
        </el-form-item>
        <el-form-item label="最大仓位">
          <el-slider v-model="createForm.max_position_ratio" :min="0.1" :max="1" :step="0.1" :format-tooltip="val => (val * 100).toFixed(0) + '%'" />
        </el-form-item>
        <el-form-item label="入场模式">
          <el-radio-group v-model="createForm.entry_mode">
            <el-radio label="rule_only">仅规则</el-radio>
            <el-radio label="rule_llm">规则+AI确认</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="出场模式">
          <el-radio-group v-model="createForm.exit_mode">
            <el-radio label="rule_only">仅规则</el-radio>
            <el-radio label="rule_llm">规则+AI确认</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="检查间隔">
          <el-input-number v-model="createForm.check_interval" :min="10" :max="300" /> 秒
        </el-form-item>
        <el-form-item label="止损比例">
          <el-slider v-model="createForm.stop_loss_pct" :min="0.01" :max="0.2" :step="0.01" :format-tooltip="val => (val * 100).toFixed(0) + '%'" />
        </el-form-item>
        <el-form-item label="止盈比例">
          <el-slider v-model="createForm.take_profit_pct" :min="0.05" :max="0.5" :step="0.01" :format-tooltip="val => (val * 100).toFixed(0) + '%'" />
        </el-form-item>
        <el-form-item label="立即启动">
          <el-switch v-model="createForm.auto_start" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="createPlan">创建</el-button>
      </template>
    </el-dialog>

    <!-- 计划详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="计划详情" width="700px">
      <div v-if="selectedPlan" class="plan-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="策略名称">{{ selectedPlan.strategy_name }}</el-descriptions-item>
          <el-descriptions-item label="股票">{{ selectedPlan.stock_name }}({{ selectedPlan.stock_code }})</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(selectedPlan.status)">{{ getStatusText(selectedPlan.status) }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="计划资金">¥{{ selectedPlan.initial_capital.toLocaleString() }}</el-descriptions-item>
          <el-descriptions-item label="最大仓位">{{ (selectedPlan.max_position_ratio * 100).toFixed(0) }}%</el-descriptions-item>
          <el-descriptions-item label="检查间隔">{{ selectedPlan.check_interval }}秒</el-descriptions-item>
          <el-descriptions-item label="止损">{{ (selectedPlan.stop_loss_pct * 100).toFixed(0) }}%</el-descriptions-item>
          <el-descriptions-item label="止盈">{{ (selectedPlan.take_profit_pct * 100).toFixed(0) }}%</el-descriptions-item>
          <el-descriptions-item label="入场模式">{{ selectedPlan.entry_mode === 'rule_only' ? '仅规则' : '规则+AI' }}</el-descriptions-item>
          <el-descriptions-item label="出场模式">{{ selectedPlan.exit_mode === 'rule_only' ? '仅规则' : '规则+AI' }}</el-descriptions-item>
        </el-descriptions>

        <el-divider>持仓信息</el-divider>
        <el-descriptions :column="2" border v-if="selectedPlan.current_position > 0">
          <el-descriptions-item label="持仓数量">{{ selectedPlan.current_position }}股</el-descriptions-item>
          <el-descriptions-item label="持仓成本">¥{{ selectedPlan.avg_cost.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="当前价格">¥{{ selectedPlan.current_price.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="浮动盈亏">
            <span :class="selectedPlan.unrealized_pnl >= 0 ? 'profit' : 'loss'">
              {{ selectedPlan.unrealized_pnl >= 0 ? '+' : '' }}{{ selectedPlan.unrealized_pnl_pct }}%
            </span>
          </el-descriptions-item>
          <el-descriptions-item label="止损价">¥{{ selectedPlan.stop_loss_price.toFixed(2) }}</el-descriptions-item>
          <el-descriptions-item label="止盈价">¥{{ selectedPlan.take_profit_price.toFixed(2) }}</el-descriptions-item>
        </el-descriptions>
        <el-empty v-else description="暂无持仓" :image-size="60" />

        <el-divider>指标数据</el-divider>
        <div class="indicators-grid">
          <div v-for="(value, key) in selectedPlan.last_indicators" :key="key" class="indicator-item">
            <span class="indicator-name">{{ key }}</span>
            <span class="indicator-value">{{ typeof value === 'number' ? value.toFixed(4) : value }}</span>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Plus, Check, Clock } from '@element-plus/icons-vue'
import axios from 'axios'

const API_BASE = '/api/auto-trade'

// 状态
const plans = ref([])
const presetStrategies = ref([])
const monitorStatus = ref({ is_running: false })
const showCreateDialog = ref(false)
const showDetailDialog = ref(false)
const selectedPlan = ref(null)
const ws = ref(null)

// 创建表单
const createForm = ref({
  strategy_id: '',
  strategy_name: '',
  strategy_config: {},
  stock_code: '',
  stock_name: '',
  initial_capital: 100000,
  max_position_ratio: 0.3,
  entry_mode: 'rule_only',
  exit_mode: 'rule_only',
  check_interval: 30,
  stop_loss_pct: 0.05,
  take_profit_pct: 0.15,
  auto_start: false
})

// 计算属性
const runningPlans = computed(() => plans.value.filter(p => p.status === 'running'))
const totalTrades = computed(() => plans.value.reduce((sum, p) => sum + p.trades_executed, 0))
const totalProfitLoss = computed(() => plans.value.reduce((sum, p) => sum + p.total_profit_loss, 0))

// 方法
const getStatusType = (status) => {
  const types = {
    pending: 'info',
    running: 'success',
    paused: 'warning',
    stopped: 'danger',
    completed: 'primary'
  }
  return types[status] || 'info'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待启动',
    running: '运行中',
    paused: '已暂停',
    stopped: '已停止',
    completed: '已完成'
  }
  return texts[status] || status
}

const formatTime = (timeStr) => {
  if (!timeStr) return ''
  const date = new Date(timeStr)
  return date.toLocaleTimeString()
}

const loadPlans = async () => {
  try {
    const res = await axios.get(`${API_BASE}/plans`)
    if (res.data.success) {
      plans.value = res.data.data
    }
  } catch (error) {
    console.error('加载计划失败:', error)
  }
}

const loadPresetStrategies = async () => {
  try {
    const res = await axios.get(`${API_BASE}/strategies/preset`)
    if (res.data.success) {
      presetStrategies.value = res.data.data
    }
  } catch (error) {
    console.error('加载预设策略失败:', error)
  }
}

const loadMonitorStatus = async () => {
  try {
    const res = await axios.get(`${API_BASE}/monitor/status`)
    if (res.data.success) {
      monitorStatus.value = res.data.data
    }
  } catch (error) {
    console.error('加载监控状态失败:', error)
  }
}

const onStrategyChange = (strategyId) => {
  const strategy = presetStrategies.value.find(s => s.id === strategyId)
  if (strategy) {
    createForm.value.strategy_name = strategy.name
    createForm.value.strategy_config = strategy
  }
}

const createPlan = async () => {
  if (!createForm.value.strategy_id || !createForm.value.stock_code) {
    ElMessage.warning('请选择策略和输入股票代码')
    return
  }

  try {
    const res = await axios.post(`${API_BASE}/plans`, createForm.value)
    if (res.data.success) {
      ElMessage.success('创建成功')
      showCreateDialog.value = false
      loadPlans()
      // 重置表单
      createForm.value = {
        strategy_id: '',
        strategy_name: '',
        strategy_config: {},
        stock_code: '',
        stock_name: '',
        initial_capital: 100000,
        max_position_ratio: 0.3,
        entry_mode: 'rule_only',
        exit_mode: 'rule_only',
        check_interval: 30,
        stop_loss_pct: 0.05,
        take_profit_pct: 0.15,
        auto_start: false
      }
    }
  } catch (error) {
    ElMessage.error('创建失败: ' + (error.response?.data?.detail || error.message))
  }
}

const startPlan = async (planId) => {
  try {
    const res = await axios.post(`${API_BASE}/plans/${planId}/start`)
    if (res.data.success) {
      ElMessage.success('计划已启动')
      loadPlans()
    }
  } catch (error) {
    ElMessage.error('启动失败: ' + (error.response?.data?.detail || error.message))
  }
}

const pausePlan = async (planId) => {
  try {
    const res = await axios.post(`${API_BASE}/plans/${planId}/pause`)
    if (res.data.success) {
      ElMessage.success('计划已暂停')
      loadPlans()
    }
  } catch (error) {
    ElMessage.error('暂停失败: ' + (error.response?.data?.detail || error.message))
  }
}

const stopPlan = async (planId) => {
  try {
    await ElMessageBox.confirm('确定要停止该计划吗？', '确认')
    const res = await axios.post(`${API_BASE}/plans/${planId}/stop`)
    if (res.data.success) {
      ElMessage.success('计划已停止')
      loadPlans()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('停止失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

const deletePlan = async (planId) => {
  try {
    await ElMessageBox.confirm('确定要删除该计划吗？此操作不可恢复', '确认删除', { type: 'warning' })
    const res = await axios.delete(`${API_BASE}/plans/${planId}`)
    if (res.data.success) {
      ElMessage.success('删除成功')
      loadPlans()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败: ' + (error.response?.data?.detail || error.message))
    }
  }
}

const showPlanDetail = (plan) => {
  selectedPlan.value = plan
  showDetailDialog.value = true
}

// WebSocket连接
const connectWebSocket = () => {
  const wsUrl = `ws://${window.location.host}${API_BASE}/ws`
  ws.value = new WebSocket(wsUrl)

  ws.value.onopen = () => {
    console.log('[WebSocket] 已连接')
  }

  ws.value.onmessage = (event) => {
    const message = JSON.parse(event.data)

    if (message.type === 'status_update') {
      // 更新计划状态
      const planData = message.data
      const index = plans.value.findIndex(p => p.plan_id === planData.plan_id)
      if (index >= 0) {
        plans.value[index] = planData
      }
    } else if (message.type === 'trade_executed') {
      // 交易执行通知
      const tradeData = message.data
      ElMessage({
        type: tradeData.action === 'BUY' ? 'success' : 'warning',
        message: `${tradeData.action === 'BUY' ? '买入' : '卖出'} ${tradeData.stock_code} ${tradeData.quantity}股 @ ¥${tradeData.price}`,
        duration: 5000
      })
      loadPlans()
    }
  }

  ws.value.onclose = () => {
    console.log('[WebSocket] 已断开，5秒后重连...')
    setTimeout(connectWebSocket, 5000)
  }

  ws.value.onerror = (error) => {
    console.error('[WebSocket] 错误:', error)
  }
}

// 生命周期
onMounted(() => {
  loadPlans()
  loadPresetStrategies()
  loadMonitorStatus()
  connectWebSocket()
})

onUnmounted(() => {
  if (ws.value) {
    ws.value.close()
  }
})
</script>

<style scoped>
.auto-trade-view {
  padding: 20px;
  background: #f5f7fa;
  min-height: 100vh;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
  font-size: 24px;
  color: #303133;
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 20px;
}

.stat-card {
  text-align: center;
  padding: 20px;
}

.stat-card .stat-value {
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.stat-card .stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 8px;
}

.stat-card.running .stat-value {
  color: #67c23a;
}

.stat-card.profit .stat-value {
  color: #f56c6c;
}

.stat-card.loss .stat-value {
  color: #67c23a;
}

.plans-container {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.plan-card {
  border-left: 4px solid #909399;
}

.plan-card.running {
  border-left-color: #67c23a;
}

.plan-card.paused {
  border-left-color: #e6a23c;
}

.plan-card.stopped {
  border-left-color: #f56c6c;
}

.plan-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.plan-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.strategy-name {
  font-weight: bold;
  font-size: 16px;
}

.stock-info {
  font-size: 14px;
  color: #606266;
}

.plan-content {
  padding: 10px 0;
}

.position-info {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 8px;
  margin-bottom: 12px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  color: #909399;
}

.info-row .value {
  font-weight: 500;
}

.info-row.profit .value {
  color: #f56c6c;
}

.info-row.loss .value {
  color: #67c23a;
}

.conditions-status {
  margin-bottom: 12px;
}

.group-title {
  font-size: 14px;
  color: #606266;
  margin-bottom: 8px;
}

.condition-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.condition-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: #909399;
}

.condition-item.met {
  color: #67c23a;
}

.plan-stats {
  display: flex;
  gap: 20px;
  padding: 10px 0;
  border-top: 1px solid #ebeef5;
}

.stat-item {
  display: flex;
  gap: 8px;
}

.stat-item .label {
  color: #909399;
}

.stat-item.profit .value {
  color: #f56c6c;
}

.stat-item.loss .value {
  color: #67c23a;
}

.last-check {
  font-size: 12px;
  color: #c0c4cc;
  margin-top: 8px;
}

.plan-actions {
  display: flex;
  gap: 8px;
  padding-top: 12px;
  border-top: 1px solid #ebeef5;
}

.plan-detail .profit {
  color: #f56c6c;
}

.plan-detail .loss {
  color: #67c23a;
}

.indicators-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.indicator-item {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.indicator-name {
  color: #606266;
  font-size: 13px;
}

.indicator-value {
  font-weight: 500;
  font-family: monospace;
}
</style>
