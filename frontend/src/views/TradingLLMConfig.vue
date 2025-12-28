<template>
  <div class="trading-llm-config">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>⚙️ 交易LLM配置</h1>
      <p class="subtitle">配置策略选择、交易决策、市场分析的LLM模型</p>
      <div class="note-box">
        <span class="note-icon">ℹ️</span>
        <span>这是专门用于回测/策略/交易功能的LLM配置，与21个智能分析体的配置完全独立</span>
      </div>
    </div>

    <!-- 配置卡片 -->
    <div class="config-cards">
      <!-- 策略选择器 -->
      <div class="config-card">
        <div class="card-header">
          <div class="card-title">
            <span class="card-icon">🎯</span>
            <span>策略选择器</span>
          </div>
          <label class="switch">
            <input type="checkbox" v-model="configs.strategy_selector.enabled" @change="saveConfig('strategy_selector')">
            <span class="slider"></span>
          </label>
        </div>
        <div class="card-body">
          <p class="card-desc">根据分析结果，LLM推荐最适合的交易策略</p>
          <div class="config-row">
            <label>模型</label>
            <select
              v-model="configs.strategy_selector.model"
              @change="saveConfig('strategy_selector')"
              :disabled="availableModelOptions.length === 0"
            >
              <option v-for="model in availableModelOptions" :key="model.name" :value="model.name">
                {{ model.label }}
              </option>
            </select>
            <p v-if="availableModelOptions.length === 0" class="config-hint">
              请先在模型管理中选择可用模型
            </p>
          </div>
          <div class="config-row">
            <button
              class="test-btn"
              @click="testLLM('strategy_selector')"
              :disabled="testingTask === 'strategy_selector'"
            >
              <span v-if="testingTask === 'strategy_selector'" class="loading-spinner"></span>
              {{ testingTask === 'strategy_selector' ? '测试中...' : '测试连接' }}
            </button>
            <span v-if="testResults.strategy_selector" :class="['test-result', testResults.strategy_selector.success ? 'success' : 'error']">
              {{ testResults.strategy_selector.message }}
            </span>
          </div>
        </div>
      </div>

      <!-- 交易决策器 -->
      <div class="config-card">
        <div class="card-header">
          <div class="card-title">
            <span class="card-icon">📈</span>
            <span>交易决策器</span>
          </div>
          <label class="switch">
            <input type="checkbox" v-model="configs.trade_decision.enabled" @change="saveConfig('trade_decision')">
            <span class="slider"></span>
          </label>
        </div>
        <div class="card-body">
          <p class="card-desc">分析市场情况，LLM决定买入/卖出/持有</p>
          <div class="config-row">
            <label>模型</label>
            <select
              v-model="configs.trade_decision.model"
              @change="saveConfig('trade_decision')"
              :disabled="availableModelOptions.length === 0"
            >
              <option v-for="model in availableModelOptions" :key="model.name" :value="model.name">
                {{ model.label }}
              </option>
            </select>
            <p v-if="availableModelOptions.length === 0" class="config-hint">
              请先在模型管理中选择可用模型
            </p>
          </div>
          <div class="config-row">
            <button
              class="test-btn"
              @click="testLLM('trade_decision')"
              :disabled="testingTask === 'trade_decision'"
            >
              <span v-if="testingTask === 'trade_decision'" class="loading-spinner"></span>
              {{ testingTask === 'trade_decision' ? '测试中...' : '测试连接' }}
            </button>
            <span v-if="testResults.trade_decision" :class="['test-result', testResults.trade_decision.success ? 'success' : 'error']">
              {{ testResults.trade_decision.message }}
            </span>
          </div>
        </div>
      </div>

      <!-- 市场分析器 -->
      <div class="config-card">
        <div class="card-header">
          <div class="card-title">
            <span class="card-icon">📊</span>
            <span>市场分析器</span>
          </div>
          <label class="switch">
            <input type="checkbox" v-model="configs.market_analyzer.enabled" @change="saveConfig('market_analyzer')">
            <span class="slider"></span>
          </label>
        </div>
        <div class="card-body">
          <p class="card-desc">持续跟踪时，分析最新行情和新闻</p>
          <div class="config-row">
            <label>模型</label>
            <select
              v-model="configs.market_analyzer.model"
              @change="saveConfig('market_analyzer')"
              :disabled="availableModelOptions.length === 0"
            >
              <option v-for="model in availableModelOptions" :key="model.name" :value="model.name">
                {{ model.label }}
              </option>
            </select>
            <p v-if="availableModelOptions.length === 0" class="config-hint">
              请先在模型管理中选择可用模型
            </p>
          </div>
          <div class="config-row">
            <button
              class="test-btn"
              @click="testLLM('market_analyzer')"
              :disabled="testingTask === 'market_analyzer'"
            >
              <span v-if="testingTask === 'market_analyzer'" class="loading-spinner"></span>
              {{ testingTask === 'market_analyzer' ? '测试中...' : '测试连接' }}
            </button>
            <span v-if="testResults.market_analyzer" :class="['test-result', testResults.market_analyzer.success ? 'success' : 'error']">
              {{ testResults.market_analyzer.message }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 保存提示 -->
    <div v-if="saveMessage" class="save-message" :class="saveSuccess ? 'success' : 'error'">
      {{ saveMessage }}
    </div>

    <!-- 策略管理 -->
    <div class="strategy-section">
      <div class="strategy-header">
        <div>
          <h2>📚 策略管理</h2>
          <p class="strategy-subtitle">查看当前系统内所有可用策略及其运行状态</p>
        </div>
        <div class="strategy-stats">
          <div class="stat-item">
            <span class="stat-label">策略总数</span>
            <span class="stat-value">{{ strategyStats.total }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-label">已激活</span>
            <span class="stat-value active">{{ strategyStats.active }}</span>
          </div>
        </div>
      </div>

      <div class="strategy-filters">
        <button
          v-for="category in strategyFilters"
          :key="category.value"
          :class="['filter-btn', { active: selectedCategory === category.value }]"
          @click="selectedCategory = category.value"
        >
          {{ category.label }}
          <span v-if="category.count !== undefined" class="filter-count">{{ category.count }}</span>
        </button>
      </div>

      <div v-if="strategyLoading" class="strategy-loading">
        <div class="spinner"></div>
        <p>加载策略信息中...</p>
      </div>

      <div v-else-if="strategyError" class="strategy-error">
        ⚠️ {{ strategyError }}
      </div>

      <div v-else class="strategy-grid">
        <div v-for="strategy in filteredStrategies" :key="strategy.id" class="strategy-card">
          <div class="strategy-card-header">
            <div>
              <h3>{{ strategy.name }}</h3>
              <p class="strategy-desc">{{ strategy.description }}</p>
            </div>
            <span :class="['status-badge', strategy.is_active ? 'on' : 'off']">
              {{ strategy.is_active ? '启用' : '停用' }}
            </span>
          </div>
          <div class="strategy-meta">
            <span class="tag">{{ formatCategory(strategy.category) }}</span>
            <span class="tag weight">权重 {{ (strategy.weight || 0).toFixed(2) }}</span>
          </div>
        </div>

        <div v-if="filteredStrategies.length === 0" class="strategy-empty">
          暂无符合条件的策略
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '@/config/api.js'

export default {
  name: 'TradingLLMConfig',
  setup() {
    const API_BASE = `${API_BASE_URL}/api/trading-llm-config`
    const AGENT_CONFIG_API = `${API_BASE_URL}/api/config/agents`

    const DEFAULT_MODEL_OPTIONS = [
      { name: 'deepseek-chat', label: 'DeepSeek Chat' },
      { name: 'deepseek-coder', label: 'DeepSeek Coder' },
      { name: 'Qwen/Qwen2.5-7B-Instruct', label: 'Qwen2.5-7B' }
    ]
    
    // 配置状态
    const configs = reactive({
      strategy_selector: {
        provider: 'deepseek',
        model: 'deepseek-chat',
        enabled: true
      },
      trade_decision: {
        provider: 'deepseek',
        model: 'deepseek-chat',
        enabled: true
      },
      market_analyzer: {
        provider: 'deepseek',
        model: 'deepseek-chat',
        enabled: true
      }
    })

    const availableModelOptions = ref([])
    const saveMessage = ref('')
    const saveSuccess = ref(false)
    const testingTask = ref('')
    const testResults = reactive({
      strategy_selector: null,
      trade_decision: null,
      market_analyzer: null
    })

    // 策略管理状态
    const strategies = ref([])
    const strategyLoading = ref(false)
    const strategyError = ref('')
    const selectedCategory = ref('all')
    const strategyStats = reactive({ total: 0, active: 0 })
    const strategyFilters = ref([
      { value: 'all', label: '全部策略', count: 0 },
      { value: 'value_investing', label: '价值投资', count: 0 },
      { value: 'technical', label: '技术分析', count: 0 },
      { value: 'folk_strategy', label: '民间策略', count: 0 },
      { value: 'ai_composite', label: 'AI合成策略', count: 0 },
      { value: 'trend_following', label: '趋势跟踪', count: 0 }
    ])

    const formatModelLabel = (modelName) => {
      if (!modelName || typeof modelName !== 'string') return '未命名模型'
      if (modelName.includes('/')) {
        const parts = modelName.split('/')
        return parts[parts.length - 1]
      }
      const labelMap = {
        'deepseek-chat': 'DeepSeek Chat',
        'deepseek-coder': 'DeepSeek Coder',
        'qwen-plus': '通义千问 Plus',
        'qwen-max': '通义千问 Max',
        'qwen-turbo': '通义千问 Turbo'
      }
      return labelMap[modelName] || modelName
    }

    const ensureModelSelected = (taskName) => {
      if (availableModelOptions.value.length === 0) return
      const currentModel = configs[taskName].model
      const exists = availableModelOptions.value.some(opt => opt.name === currentModel)
      if (!exists) {
        configs[taskName].model = availableModelOptions.value[0].name
      }
    }

    // 加载模型管理中已经选择的模型
    const loadAvailableModels = async () => {
      try {
        const response = await fetch(AGENT_CONFIG_API)
        if (response.ok) {
          const payload = await response.json()
          const data = payload.success ? payload.data : payload
          const models = data?.selectedModels || []
          if (models.length > 0) {
            availableModelOptions.value = models.map(name => ({
              name,
              label: formatModelLabel(name)
            }))
            return
          }
        }
      } catch (error) {
        console.error('加载模型列表失败:', error)
      }
      availableModelOptions.value = DEFAULT_MODEL_OPTIONS
    }

    // 加载配置
    const loadConfigs = async () => {
      try {
        const response = await axios.get(`${API_BASE}/tasks`)
        if (response.data.success) {
          response.data.tasks.forEach(task => {
            if (configs[task.task_name]) {
              configs[task.task_name] = {
                provider: task.provider,
                model: task.model,
                enabled: task.enabled
              }
              ensureModelSelected(task.task_name)
            }
          })
        }
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    }

    // 保存配置
    const saveConfig = async (taskName) => {
      try {
        const config = configs[taskName]
        await axios.put(`${API_BASE}/tasks/${taskName}`, {
          provider: config.provider,
          model: config.model,
          enabled: config.enabled
        })

        saveMessage.value = '保存成功'
        saveSuccess.value = true

        setTimeout(() => {
          saveMessage.value = ''
        }, 2000)
      } catch (error) {
        console.error('保存失败:', error)
        saveMessage.value = '保存失败: ' + (error.response?.data?.detail || error.message)
        saveSuccess.value = false

        setTimeout(() => {
          saveMessage.value = ''
        }, 3000)
      }
    }

    // 测试LLM连接
    const testLLM = async (taskName) => {
      testingTask.value = taskName
      testResults[taskName] = null

      try {
        const response = await axios.post(`${API_BASE}/tasks/${taskName}/test`)
        if (response.data.success) {
          testResults[taskName] = {
            success: true,
            message: `测试成功 (${response.data.elapsed_time || 0}s)`
          }
        } else {
          testResults[taskName] = {
            success: false,
            message: response.data.message || '测试失败'
          }
        }
      } catch (error) {
        console.error('测试失败:', error)
        testResults[taskName] = {
          success: false,
          message: error.response?.data?.detail || error.message || '连接失败'
        }
      } finally {
        testingTask.value = ''

        // 5秒后清除测试结果
        setTimeout(() => {
          testResults[taskName] = null
        }, 5000)
      }
    }

    const CATEGORY_MAP = {
      'value_investing': '价值投资',
      'technical': '技术分析',
      'folk_strategy': '民间策略',
      'ai_composite': 'AI合成策略',
      'trend_following': '趋势跟踪',
      'quantitative': '量化因子',
      'machine_learning': '机器学习'
    }

    const normalizeCategory = (category) => {
      if (!category) {
        return { value: 'unclassified', label: '未分类' }
      }
      const lower = String(category).toLowerCase()
      if (CATEGORY_MAP[lower]) {
        return { value: lower, label: CATEGORY_MAP[lower] }
      }
      const matched = Object.entries(CATEGORY_MAP).find(([, label]) => label === category)
      if (matched) {
        return { value: matched[0], label: matched[1] }
      }
      return { value: category, label: category }
    }

    const formatCategory = (value) => {
      return CATEGORY_MAP[value] || value || '未分类'
    }

    const applyStrategyData = (list, stats = {}) => {
      const mapped = list.map((item, index) => {
        const { value, label } = normalizeCategory(item.category)
        return {
          ...item,
          id: item.id || item.strategy_id || `strategy-${index}`,
          category: value,
          categoryLabel: label,
          is_active: item.is_active ?? item.isActive ?? false
        }
      })

      strategies.value = mapped
      strategyStats.total = stats.total ?? mapped.length
      strategyStats.active = stats.active ?? mapped.filter(s => s.is_active).length

      const counts = mapped.reduce((acc, item) => {
        acc[item.category] = (acc[item.category] || 0) + 1
        return acc
      }, {})

      strategyFilters.value = [
        { value: 'all', label: '全部策略', count: mapped.length },
        ...Object.entries(counts).map(([value, count]) => ({
          value,
          label: formatCategory(value),
          count
        }))
      ]
    }

    const loadStrategiesFromTrading = async () => {
      const response = await axios.get(`${API_BASE_URL}/api/strategy/list`)
      if (response.data?.success && response.data.total) {
        const rawStrategies = response.data.strategies || {}
        const list = Object.entries(rawStrategies).map(([id, info]) => ({
          id,
          ...info
        }))
        applyStrategyData(list, {
          total: response.data.total,
          active: response.data.active_count
        })
        return list.length > 0
      }
      return false
    }

    const loadStrategiesFromBacktest = async () => {
      const response = await axios.get(`${API_BASE_URL}/api/backtest/strategies`)
      if (response.data?.success && Array.isArray(response.data.strategies)) {
        applyStrategyData(response.data.strategies, {
          total: response.data.strategies.length,
          active: response.data.strategies.filter(item => item.is_active || item.isActive).length
        })
        return response.data.strategies.length > 0
      }
      return false
    }

    const loadStrategies = async () => {
      strategyLoading.value = true
      strategyError.value = ''
      try {
        let loaded = false
        try {
          loaded = await loadStrategiesFromTrading()
        } catch (error) {
          console.warn('策略系统接口不可用，尝试使用回测列表:', error)
        }

        if (!loaded) {
          const fallbackLoaded = await loadStrategiesFromBacktest()
          if (!fallbackLoaded) {
            strategyError.value = '无法获取策略列表'
          }
        }
      } catch (error) {
        console.error('加载策略信息失败:', error)
        strategyError.value = error.response?.data?.detail || error.message || '加载失败'
      } finally {
        strategyLoading.value = false
      }
    }

    const filteredStrategies = computed(() => {
      if (selectedCategory.value === 'all') {
        return strategies.value
      }
      return strategies.value.filter(strategy => strategy.category === selectedCategory.value)
    })

    const init = async () => {
      await loadAvailableModels()
      await loadConfigs()
      await loadStrategies()
    }

    onMounted(() => {
      init()
    })

    return {
      configs,
      saveMessage,
      saveSuccess,
      availableModelOptions,
      saveConfig,
      testLLM,
      testingTask,
      testResults,
      strategies,
      strategyStats,
      strategyFilters,
      selectedCategory,
      filteredStrategies,
      strategyLoading,
      strategyError,
      formatCategory
    }
  }
}
</script>

<style scoped>
.trading-llm-config {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.page-header {
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 28px;
  margin: 0 0 8px 0;
  color: white;
}

.subtitle {
  color: #999;
  margin: 0 0 12px 0;
}

.note-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  background: rgba(255, 193, 7, 0.1);
  border: 1px solid rgba(255, 193, 7, 0.3);
  border-radius: 8px;
  color: #ffc107;
  font-size: 14px;
}

.note-icon {
  font-size: 18px;
}

.config-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 20px;
}

.config-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  overflow: hidden;
  transition: all 0.3s;
}

.config-card:hover {
  border-color: rgba(255, 255, 255, 0.2);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: rgba(255, 255, 255, 0.03);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.card-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: white;
}

.card-icon {
  font-size: 22px;
}

.switch {
  position: relative;
  display: inline-block;
  width: 48px;
  height: 24px;
}

.switch input {
  opacity: 0;
  width: 0;
  height: 0;
}

.slider {
  position: absolute;
  cursor: pointer;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: #ccc;
  transition: .4s;
  border-radius: 24px;
}

.slider:before {
  position: absolute;
  content: "";
  height: 18px;
  width: 18px;
  left: 3px;
  bottom: 3px;
  background-color: white;
  transition: .4s;
  border-radius: 50%;
}

input:checked + .slider {
  background-color: #1890ff;
}

input:checked + .slider:before {
  transform: translateX(24px);
}

.card-body {
  padding: 20px;
}

.card-desc {
  color: #999;
  font-size: 14px;
  margin: 0 0 16px 0;
  line-height: 1.6;
}

.config-row {
  margin-bottom: 16px;
}

.config-row:last-child {
  margin-bottom: 0;
}

.config-row label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: white;
  font-size: 14px;
}

.config-row select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 6px;
  background: #1c1c2b;
  color: white;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.config-row select:hover {
  border-color: rgba(255, 255, 255, 0.3);
  background: rgba(255, 255, 255, 0.08);
}

.config-row select:focus {
  outline: none;
  border-color: #1890ff;
  background: #23233a;
}

.config-row select option {
  background: #1c1c2b;
  color: white;
}

.strategy-section {
  margin-top: 40px;
  padding: 24px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 16px;
}

.strategy-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.strategy-header h2 {
  margin: 0;
  color: white;
}

.strategy-subtitle {
  margin: 6px 0 0;
  color: #9aa0b0;
}

.strategy-stats {
  display: flex;
  gap: 16px;
}

.stat-item {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  padding: 10px 14px;
  min-width: 120px;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #9aa0b0;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: white;
}

.stat-value.active {
  color: #52c41a;
}

.strategy-filters {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 20px;
}

.filter-btn {
  padding: 8px 16px;
  border-radius: 999px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: rgba(255, 255, 255, 0.05);
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.filter-btn.active {
  background: #1890ff;
  border-color: #1890ff;
}

.filter-count {
  margin-left: 6px;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
}

.strategy-loading,
.strategy-error,
.strategy-empty {
  text-align: center;
  padding: 40px;
  color: #9aa0b0;
}

.strategy-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 16px;
}

.strategy-card {
  background: rgba(0, 0, 0, 0.2);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.strategy-card-header {
  display: flex;
  justify-content: space-between;
  gap: 12px;
}

.strategy-card h3 {
  margin: 0;
  color: white;
}

.strategy-desc {
  margin: 4px 0 0;
  color: #9aa0b0;
  font-size: 13px;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
}

.status-badge.on {
  background: rgba(82, 196, 26, 0.15);
  color: #52c41a;
}

.status-badge.off {
  background: rgba(255, 77, 79, 0.15);
  color: #ff7875;
}

.strategy-meta {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.tag {
  padding: 4px 8px;
  border-radius: 6px;
  background: rgba(255, 255, 255, 0.1);
  color: white;
  font-size: 12px;
}

.tag.weight {
  background: rgba(24, 144, 255, 0.15);
  color: #69c0ff;
}

.test-btn {
  padding: 8px 16px;
  border: 1px solid #1890ff;
  border-radius: 6px;
  background: transparent;
  color: #1890ff;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.test-btn:hover:not(:disabled) {
  background: rgba(24, 144, 255, 0.1);
}

.test-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.loading-spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(24, 144, 255, 0.3);
  border-top-color: #1890ff;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.test-result {
  margin-left: 12px;
  font-size: 13px;
}

.test-result.success {
  color: #52c41a;
}

.test-result.error {
  color: #ff4d4f;
}

.config-hint {
  margin: 8px 0 0;
  font-size: 12px;
  color: #999;
}

.save-message {
  position: fixed;
  top: 20px;
  right: 20px;
  padding: 12px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  z-index: 1000;
  animation: slideIn 0.3s ease-out;
}

.save-message.success {
  background: #52c41a;
  color: white;
}

.save-message.error {
  background: #ff4d4f;
  color: white;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
