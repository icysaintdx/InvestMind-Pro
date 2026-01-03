<template>
  <div class="api-monitor-container">
    <div class="monitor-header">
      <h1 class="page-title">
        <span class="title-icon">📡</span>
        API 接口监控
      </h1>
      <div class="header-actions">
        <div class="health-summary" v-if="summary">
          <span class="health-badge" :class="healthClass">
            {{ summary.ok_count }}/{{ summary.total }} 正常
          </span>
          <span class="health-percent">{{ healthPercent }}%</span>
        </div>
        <button @click="exportReport" class="export-btn" title="导出报告">
          📥 导出
        </button>
        <button @click="refreshAll" :disabled="loading" class="refresh-btn">
          <span :class="{ 'spin': loading }">🔄</span>
          {{ loading ? '检测中...' : '刷新全部' }}
        </button>
      </div>
    </div>

    <!-- 视图切换 -->
    <div class="view-tabs">
      <button :class="['tab-btn', { active: viewMode === 'category' }]" @click="viewMode = 'category'">
        📂 按分类
      </button>
      <button :class="['tab-btn', { active: viewMode === 'source' }]" @click="viewMode = 'source'">
        🔌 按数据源
      </button>
      <button :class="['tab-btn', { active: viewMode === 'type' }]" @click="viewMode = 'type'">
        📊 按类型
      </button>
    </div>

    <!-- 筛选器 -->
    <div class="filter-bar">
      <div class="filter-group">
        <label>分类筛选:</label>
        <select v-model="selectedCategory">
          <option value="">全部分类</option>
          <option v-for="cat in categories" :key="cat" :value="cat">{{ cat }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>数据源:</label>
        <select v-model="selectedSource">
          <option value="">全部数据源</option>
          <option v-for="src in sources" :key="src" :value="src">{{ src }}</option>
        </select>
      </div>
      <div class="filter-group">
        <label>状态筛选:</label>
        <select v-model="selectedStatus">
          <option value="">全部状态</option>
          <option value="OK">正常</option>
          <option value="WARN">警告</option>
          <option value="FAIL">失败</option>
          <option value="TIMEOUT">超时</option>
          <option value="N/A">不可用</option>
        </select>
      </div>
      <div class="filter-group checkboxes">
        <label>
          <input type="checkbox" v-model="includeAkshare" /> AKShare
        </label>
        <label>
          <input type="checkbox" v-model="includeInternal" /> 内部API
        </label>
        <label>
          <input type="checkbox" v-model="includeAi" /> AI服务
        </label>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-row">
      <div class="stat-card ok">
        <div class="stat-icon">✅</div>
        <div class="stat-info">
          <div class="stat-value">{{ statusCounts.OK || 0 }}</div>
          <div class="stat-label">正常</div>
        </div>
      </div>
      <div class="stat-card warn">
        <div class="stat-icon">⚠️</div>
        <div class="stat-info">
          <div class="stat-value">{{ statusCounts.WARN || 0 }}</div>
          <div class="stat-label">警告</div>
        </div>
      </div>
      <div class="stat-card fail">
        <div class="stat-icon">❌</div>
        <div class="stat-info">
          <div class="stat-value">{{ statusCounts.FAIL || 0 }}</div>
          <div class="stat-label">失败</div>
        </div>
      </div>
      <div class="stat-card timeout">
        <div class="stat-icon">⏱️</div>
        <div class="stat-info">
          <div class="stat-value">{{ statusCounts.TIMEOUT || 0 }}</div>
          <div class="stat-label">超时</div>
        </div>
      </div>
      <div class="stat-card na">
        <div class="stat-icon">🚫</div>
        <div class="stat-info">
          <div class="stat-value">{{ statusCounts['N/A'] || 0 }}</div>
          <div class="stat-label">不可用</div>
        </div>
      </div>
    </div>

    <!-- 分类展示 -->
    <div class="categories-container">
      <div v-for="(apis, groupName) in currentGroupedData" :key="groupName" class="category-section">
        <div class="category-header" @click="toggleCategory(groupName)">
          <span class="category-icon">{{ getGroupIcon(groupName) }}</span>
          <span class="category-name">{{ groupName }}</span>
          <span class="category-count">
            <span class="count-ok">{{ getGroupOkCount(apis) }}</span>
            /
            <span class="count-total">{{ apis.length }}</span>
          </span>
          <span class="category-toggle">{{ expandedCategories[groupName] ? '▼' : '▶' }}</span>
        </div>

        <div v-show="expandedCategories[groupName]" class="api-list">
          <div v-for="api in apis" :key="api.name + api.endpoint" class="api-item" :class="getStatusClass(api.status)">
            <!-- 状态 -->
            <div class="api-status">
              <span class="status-dot" :class="api.status"></span>
              <span class="status-text">{{ api.status }}</span>
            </div>

            <!-- 名称和端点 -->
            <div class="api-info">
              <div class="api-name">
                {{ api.name }}
                <span v-if="api.fallback_to" class="fallback-badge" :title="'降级到: ' + api.fallback_to">↓</span>
              </div>
              <div class="api-meta">
                <span class="api-source" v-if="api.source">{{ api.source }}</span>
                <span class="api-endpoint">{{ api.endpoint || '-' }}</span>
              </div>
            </div>

            <!-- 可用性 -->
            <div class="api-uptime">
              <span :class="getUptimeClass(api.uptime)">{{ api.uptime?.toFixed(1) || '100.0' }}%</span>
            </div>

            <!-- 延迟信息 - Ping和响应并排大字显示 -->
            <div class="api-latency">
              <div class="latency-row">
                <span class="latency-label">Ping:</span>
                <span v-if="api.ping_time > 0" class="latency-value" :class="getLatencyClass(api.ping_time)">
                  {{ api.ping_time.toFixed(0) }}ms
                </span>
                <span v-else class="latency-na">-</span>
              </div>
              <div class="latency-row">
                <span class="latency-label">响应:</span>
                <span v-if="api.latency > 0" class="latency-value" :class="getLatencyClass(api.latency)">
                  {{ api.latency.toFixed(0) }}ms
                </span>
                <span v-else class="latency-na">-</span>
              </div>
            </div>

            <!-- 历史状态条 -->
            <div class="api-history" v-if="api.history && api.history.length > 0">
              <div class="history-bar">
                <div
                  v-for="(h, idx) in api.history"
                  :key="idx"
                  class="history-point"
                  :class="h.status"
                  :title="formatHistoryPoint(h)"
                ></div>
              </div>
            </div>
            <div class="api-history" v-else>
              <div class="history-bar empty">
                <span class="no-history">暂无历史</span>
              </div>
            </div>

            <!-- 消息 - 完整显示 -->
            <div class="api-message" :title="api.message">
              {{ api.message || '-' }}
            </div>

            <!-- 操作 -->
            <div class="api-actions">
              <button @click="pingApi(api)" :disabled="pingingApi === api.name" class="ping-btn" title="Ping">
                <span :class="{ 'spin': pingingApi === api.name }">🔍</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 最后更新时间 -->
    <div class="footer-info">
      <span v-if="lastUpdate">最后更新: {{ formatTime(lastUpdate) }}</span>
      <span v-else>尚未检测</span>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '@/config/api.js'

// 全局缓存 - 用于页面切换后保留数据
const globalCache = {
  allApis: [],
  categories: [],
  sources: [],
  dataTypes: [],
  summary: null,
  lastUpdate: null,
  expandedCategories: {},
  isComplete: false  // 标记检测是否完成
}

export default {
  name: 'ApiMonitorView',
  setup() {
    const loading = ref(false)
    const pingingApi = ref(null)
    const lastUpdate = ref(globalCache.lastUpdate)
    const summary = ref(globalCache.summary)
    const allApis = ref([...globalCache.allApis])
    const categories = ref([...globalCache.categories])
    const sources = ref([...globalCache.sources])
    const dataTypes = ref([...globalCache.dataTypes])
    const expandedCategories = reactive({...globalCache.expandedCategories})
    const viewMode = ref('category')  // category, source, type
    const bySource = ref({})
    const byType = ref({})

    // 筛选条件
    const selectedCategory = ref('')
    const selectedSource = ref('')
    const selectedStatus = ref('')
    const includeAkshare = ref(true)
    const includeInternal = ref(true)
    const includeAi = ref(true)

    // 计算健康百分比
    const healthPercent = computed(() => {
      if (!summary.value || summary.value.total === 0) return 0
      return Math.round((summary.value.ok_count / summary.value.total) * 100)
    })

    const healthClass = computed(() => {
      const p = healthPercent.value
      if (p >= 90) return 'excellent'
      if (p >= 70) return 'good'
      if (p >= 50) return 'warning'
      return 'critical'
    })

    // 统计各状态数量
    const statusCounts = computed(() => {
      const counts = { OK: 0, WARN: 0, FAIL: 0, TIMEOUT: 0, 'N/A': 0 }
      allApis.value.forEach(api => {
        if (counts[api.status] !== undefined) {
          counts[api.status]++
        }
      })
      return counts
    })

    // 筛选后的API列表
    const filteredApis = computed(() => {
      return allApis.value.filter(api => {
        if (selectedStatus.value && api.status !== selectedStatus.value) return false
        if (selectedCategory.value && api.category !== selectedCategory.value) return false
        if (selectedSource.value && api.source !== selectedSource.value) return false
        return true
      })
    })

    // 当前分组数据
    const currentGroupedData = computed(() => {
      const result = {}
      filteredApis.value.forEach(api => {
        let key = ''
        if (viewMode.value === 'category') {
          key = api.category || '未分类'
        } else if (viewMode.value === 'source') {
          key = api.source || '未知来源'
        } else if (viewMode.value === 'type') {
          key = api.data_type || '未知类型'
        }
        if (!result[key]) {
          result[key] = []
        }
        result[key].push(api)
      })
      return result
    })

    // 获取分组图标
    const getGroupIcon = (name) => {
      const icons = {
        // 分类图标
        '市场新闻': '📰', '个股新闻': '📄', '行情接口': '📈', '资金数据': '💰',
        '公司数据': '🏢', '板块数据': '📊', '市场数据': '💹', '新闻服务': '📡',
        '系统服务': '⚙️', 'AI服务': '🤖', '智能分析': '🧠', '回测服务': '📉',
        // 数据源图标
        'AKShare': '📊', 'Tushare': '📈', '巨潮': '🏛️', '新浪': '🌐',
        '聚合': '🔗', 'FinnHub': '🌍', 'TDX': '💻', '内部': '🏠',
        'Google': '🔍', 'DeepSeek': '🔮', '阿里云': '☁️', 'SiliconFlow': '⚡',
        'OpenAI': '🤖', 'Anthropic': '🧠',
        // 类型图标
        '新闻': '📰', '公告': '📢', '行情': '📈', 'K线': '📊', '资金': '💰',
        '公司': '🏢', '财务': '💵', '板块': '📋', '龙虎榜': '🐉', '涨跌停': '📍',
        '情绪': '😊', '排行': '🏆', '状态': '📌', 'AI': '🤖', '系统': '⚙️',
        '分析': '🔬', '回测': '📉'
      }
      return icons[name] || '📋'
    }

    // 获取分组正常数量
    const getGroupOkCount = (apis) => {
      return apis.filter(a => a.status === 'OK').length
    }

    // 切换分类展开
    const toggleCategory = (name) => {
      expandedCategories[name] = !expandedCategories[name]
    }

    // 获取状态样式类
    const getStatusClass = (status) => {
      return {
        'status-ok': status === 'OK',
        'status-warn': status === 'WARN',
        'status-fail': status === 'FAIL',
        'status-timeout': status === 'TIMEOUT',
        'status-na': status === 'N/A'
      }
    }

    // 获取延迟样式类
    const getLatencyClass = (latency) => {
      if (latency < 500) return 'latency-fast'
      if (latency < 2000) return 'latency-normal'
      if (latency < 5000) return 'latency-slow'
      return 'latency-very-slow'
    }

    // 获取可用性样式类
    const getUptimeClass = (uptime) => {
      if (uptime >= 99) return 'uptime-excellent'
      if (uptime >= 95) return 'uptime-good'
      if (uptime >= 80) return 'uptime-warning'
      return 'uptime-critical'
    }

    // 格式化历史点
    const formatHistoryPoint = (h) => {
      if (!h) return ''
      const time = h.time ? new Date(h.time).toLocaleString('zh-CN') : ''
      return `${time}\n状态: ${h.status}\n延迟: ${h.latency?.toFixed(0) || 0}ms`
    }

    // 截断消息
    const truncateMessage = (msg) => {
      if (!msg) return '-'
      return msg.length > 40 ? msg.substring(0, 40) + '...' : msg
    }

    // 格式化时间
    const formatTime = (isoString) => {
      if (!isoString) return ''
      const d = new Date(isoString)
      return d.toLocaleString('zh-CN')
    }

    // 刷新全部 - 使用流式API
    const refreshAll = async () => {
      loading.value = true
      allApis.value = []  // 清空现有数据
      globalCache.isComplete = false  // 标记检测未完成

      try {
        const params = new URLSearchParams()
        params.append('include_akshare', includeAkshare.value)
        params.append('include_internal', includeInternal.value)
        params.append('include_ai', includeAi.value)
        params.append('include_datasources', 'true')
        params.append('include_tushare', 'true')
        params.append('include_tdx', 'true')
        params.append('include_sina', 'true')
        params.append('include_juhe', 'true')
        params.append('include_baostock', 'true')
        params.append('include_finnhub', 'true')
        params.append('include_cninfo', 'true')
        params.append('include_eastmoney', 'true')

        // 使用EventSource进行流式接收
        const eventSource = new EventSource(`${API_BASE_URL}/api/monitor/stream?${params.toString()}`)

        // 保存eventSource引用，以便页面切换时可以关闭
        window._apiMonitorEventSource = eventSource

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)

            if (data.type === 'start') {
              lastUpdate.value = data.timestamp
              globalCache.lastUpdate = data.timestamp
            } else if (data.type === 'result') {
              // 收到一个结果就添加到列表
              const api = data.data
              allApis.value.push(api)

              // 同步更新全局缓存
              globalCache.allApis = [...allApis.value]

              // 更新分类集合
              if (api.category && !categories.value.includes(api.category)) {
                categories.value.push(api.category)
                globalCache.categories = [...categories.value]
              }
              if (api.source && !sources.value.includes(api.source)) {
                sources.value.push(api.source)
                globalCache.sources = [...sources.value]
              }
              if (api.data_type && !dataTypes.value.includes(api.data_type)) {
                dataTypes.value.push(api.data_type)
                globalCache.dataTypes = [...dataTypes.value]
              }

              // 自动展开分类
              if (api.category && expandedCategories[api.category] === undefined) {
                expandedCategories[api.category] = true
                globalCache.expandedCategories[api.category] = true
              }

              // 更新统计
              updateSummary()
            } else if (data.type === 'end') {
              eventSource.close()
              window._apiMonitorEventSource = null
              loading.value = false
              lastUpdate.value = data.timestamp
              globalCache.lastUpdate = data.timestamp
              globalCache.isComplete = true  // 标记检测完成
            }
          } catch (e) {
            console.error('解析SSE数据失败:', e)
          }
        }

        eventSource.onerror = (error) => {
          console.error('SSE连接错误:', error)
          eventSource.close()
          window._apiMonitorEventSource = null
          loading.value = false
          globalCache.isComplete = true  // 即使出错也标记为完成
        }

      } catch (error) {
        console.error('获取API状态失败:', error)
        loading.value = false
        globalCache.isComplete = true
      }
    }

    // 更新统计信息
    const updateSummary = () => {
      const total = allApis.value.length
      const ok_count = allApis.value.filter(a => a.status === 'OK').length
      const warn_count = allApis.value.filter(a => a.status === 'WARN').length
      const fail_count = allApis.value.filter(a => a.status === 'FAIL' || a.status === 'TIMEOUT').length

      summary.value = {
        total,
        ok_count,
        warn_count,
        fail_count
      }
      globalCache.summary = summary.value
    }

    // Ping单个API
    const pingApi = async (api) => {
      pingingApi.value = api.name
      try {
        let apiName = ''
        if (api.category === 'AI服务' || api.data_type === 'AI') {
          apiName = `ai:${api.name.toLowerCase().split(' ')[0]}`
        } else if (api.source === '内部') {
          apiName = `internal:${api.endpoint}`
        } else {
          apiName = `akshare:${api.endpoint}`
        }

        const response = await axios.get(`${API_BASE_URL}/api/monitor/ping/${encodeURIComponent(apiName)}`)
        if (response.data) {
          // 更新该API的状态
          const idx = allApis.value.findIndex(a => a.name === api.name && a.endpoint === api.endpoint)
          if (idx !== -1) {
            allApis.value[idx] = { ...allApis.value[idx], ...response.data }
          }
        }
      } catch (error) {
        console.error('Ping失败:', error)
      } finally {
        pingingApi.value = null
      }
    }

    onMounted(() => {
      // 如果有缓存数据且检测已完成，则不自动重新检测
      if (globalCache.allApis.length > 0 && globalCache.isComplete) {
        // 恢复展开状态
        Object.keys(globalCache.expandedCategories).forEach(key => {
          expandedCategories[key] = globalCache.expandedCategories[key]
        })
        console.log('使用缓存数据，共', globalCache.allApis.length, '条记录')
      } else if (!window._apiMonitorEventSource) {
        // 没有缓存数据且没有正在进行的检测，则开始新检测
        refreshAll()
      } else {
        // 有正在进行的检测，标记为加载中
        loading.value = true
      }
    })

    // 页面卸载时关闭SSE连接（可选：设为false则后台继续执行）
    const closeOnUnmount = ref(true)  // 设为false则切换页面时后台继续执行

    onUnmounted(() => {
      if (closeOnUnmount.value && window._apiMonitorEventSource) {
        window._apiMonitorEventSource.close()
        window._apiMonitorEventSource = null
      }
    })

    // 导出报告功能
    const exportReport = () => {
      if (allApis.value.length === 0) {
        alert('暂无数据可导出')
        return
      }

      // 生成报告内容
      const now = new Date().toLocaleString('zh-CN')
      let report = `# API接口监控报告\n\n`
      report += `生成时间: ${now}\n\n`
      report += `## 总体概况\n\n`
      report += `- 总接口数: ${summary.value?.total || 0}\n`
      report += `- 正常: ${summary.value?.ok_count || 0}\n`
      report += `- 警告: ${summary.value?.warn_count || 0}\n`
      report += `- 失败: ${summary.value?.fail_count || 0}\n`
      report += `- 健康度: ${healthPercent.value}%\n\n`

      // 按分类输出
      report += `## 详细状态\n\n`
      for (const [category, apis] of Object.entries(currentGroupedData.value)) {
        const okCount = apis.filter(a => a.status === 'OK').length
        report += `### ${category} (${okCount}/${apis.length})\n\n`
        report += `| 接口名称 | 状态 | 可用性 | Ping | 响应 | 消息 |\n`
        report += `|---------|------|--------|------|------|------|\n`
        for (const api of apis) {
          const ping = api.ping_time > 0 ? `${api.ping_time.toFixed(0)}ms` : '-'
          const latency = api.latency > 0 ? `${api.latency.toFixed(0)}ms` : '-'
          const uptime = api.uptime?.toFixed(1) || '100.0'
          const msg = (api.message || '-').replace(/\|/g, '\\|').substring(0, 50)
          report += `| ${api.name} | ${api.status} | ${uptime}% | ${ping} | ${latency} | ${msg} |\n`
        }
        report += `\n`
      }

      // 问题接口汇总
      const problemApis = allApis.value.filter(a => a.status !== 'OK')
      if (problemApis.length > 0) {
        report += `## 问题接口汇总\n\n`
        report += `| 接口名称 | 状态 | 数据源 | 错误信息 |\n`
        report += `|---------|------|--------|----------|\n`
        for (const api of problemApis) {
          const msg = (api.message || '-').replace(/\|/g, '\\|')
          report += `| ${api.name} | ${api.status} | ${api.source || '-'} | ${msg} |\n`
        }
      }

      // 下载文件
      const blob = new Blob([report], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `API监控报告_${new Date().toISOString().slice(0, 10)}.md`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    }

    return {
      loading,
      pingingApi,
      lastUpdate,
      summary,
      allApis,
      categories,
      sources,
      dataTypes,
      expandedCategories,
      viewMode,
      selectedCategory,
      selectedSource,
      selectedStatus,
      includeAkshare,
      includeInternal,
      includeAi,
      healthPercent,
      healthClass,
      statusCounts,
      filteredApis,
      currentGroupedData,
      getGroupIcon,
      getGroupOkCount,
      toggleCategory,
      getStatusClass,
      getLatencyClass,
      getUptimeClass,
      formatHistoryPoint,
      truncateMessage,
      formatTime,
      refreshAll,
      pingApi,
      exportReport
    }
  }
}
</script>

<style scoped>
.api-monitor-container {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1.5rem;
}

.monitor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  color: #e2e8f0;
  margin: 0;
}

.title-icon {
  font-size: 1.75rem;
}

.header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.health-summary {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.health-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 1rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.health-badge.excellent { background: rgba(16, 185, 129, 0.2); color: #10b981; }
.health-badge.good { background: rgba(59, 130, 246, 0.2); color: #3b82f6; }
.health-badge.warning { background: rgba(245, 158, 11, 0.2); color: #f59e0b; }
.health-badge.critical { background: rgba(239, 68, 68, 0.2); color: #ef4444; }

.health-percent {
  font-size: 1.25rem;
  font-weight: 600;
  color: #e2e8f0;
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.5rem;
  color: #60a5fa;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.3);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(16, 185, 129, 0.2);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 0.5rem;
  color: #10b981;
  cursor: pointer;
  transition: all 0.2s;
}

.export-btn:hover {
  background: rgba(16, 185, 129, 0.3);
}

.spin {
  display: inline-block;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

/* 视图切换 */
.view-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.tab-btn {
  padding: 0.5rem 1rem;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.5rem;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: rgba(51, 65, 85, 0.5);
  color: #e2e8f0;
}

.tab-btn.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: #3b82f6;
}

/* 筛选器 */
.filter-bar {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  padding: 1rem;
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.75rem;
  margin-bottom: 1.5rem;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.filter-group.checkboxes {
  gap: 1rem;
}

.filter-group label {
  color: #94a3b8;
  font-size: 0.875rem;
  display: flex;
  align-items: center;
  gap: 0.25rem;
  cursor: pointer;
}

.filter-group select {
  padding: 0.375rem 0.75rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.375rem;
  color: #e2e8f0;
  font-size: 0.875rem;
}

.filter-group input[type="checkbox"] {
  accent-color: #3b82f6;
}

/* 统计卡片 */
.stats-row {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.75rem;
}

.stat-card.ok { border-left: 3px solid #10b981; }
.stat-card.warn { border-left: 3px solid #f59e0b; }
.stat-card.fail { border-left: 3px solid #ef4444; }
.stat-card.timeout { border-left: 3px solid #8b5cf6; }
.stat-card.na { border-left: 3px solid #64748b; }

.stat-icon {
  font-size: 1.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  color: #e2e8f0;
}

.stat-label {
  font-size: 0.75rem;
  color: #64748b;
}

/* 分类区域 */
.categories-container {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.category-section {
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.75rem;
  overflow: hidden;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.3);
  cursor: pointer;
  transition: background 0.2s;
}

.category-header:hover {
  background: rgba(15, 23, 42, 0.5);
}

.category-icon {
  font-size: 1.25rem;
}

.category-name {
  flex: 1;
  font-size: 1rem;
  font-weight: 500;
  color: #e2e8f0;
}

.category-count {
  font-size: 0.875rem;
  color: #64748b;
}

.count-ok {
  color: #10b981;
}

.category-toggle {
  color: #64748b;
  font-size: 0.75rem;
}

/* API列表 */
.api-list {
  padding: 0.5rem;
}

.api-item {
  display: grid;
  grid-template-columns: 70px 1.5fr 60px 100px 100px 2fr 40px;
  gap: 0.5rem;
  align-items: center;
  padding: 0.75rem 1rem;
  border-radius: 0.5rem;
  margin-bottom: 0.25rem;
  transition: background 0.2s;
}

.api-item:hover {
  background: rgba(51, 65, 85, 0.3);
}

.api-item.status-ok { border-left: 3px solid #10b981; }
.api-item.status-warn { border-left: 3px solid #f59e0b; }
.api-item.status-fail { border-left: 3px solid #ef4444; }
.api-item.status-timeout { border-left: 3px solid #8b5cf6; }
.api-item.status-na { border-left: 3px solid #64748b; }

.api-status {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.OK { background: #10b981; }
.status-dot.WARN { background: #f59e0b; }
.status-dot.FAIL { background: #ef4444; }
.status-dot.TIMEOUT { background: #8b5cf6; }
.status-dot.N\/A { background: #64748b; }

.status-text {
  font-size: 0.75rem;
  color: #94a3b8;
}

.api-info {
  min-width: 0;
}

.api-name {
  font-size: 0.875rem;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.fallback-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
  border-radius: 50%;
  font-size: 0.625rem;
  cursor: help;
}

.api-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.75rem;
}

.api-source {
  padding: 0.125rem 0.375rem;
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-radius: 0.25rem;
}

.api-endpoint {
  color: #64748b;
  font-family: monospace;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 历史状态条 */
.api-history {
  min-width: 120px;
}

.history-bar {
  display: flex;
  gap: 2px;
  height: 20px;
  align-items: center;
}

.history-bar.empty {
  justify-content: center;
}

.no-history {
  font-size: 0.625rem;
  color: #64748b;
}

.history-point {
  width: 4px;
  height: 16px;
  border-radius: 2px;
  transition: height 0.2s;
}

.history-point:hover {
  height: 20px;
}

.history-point.OK { background: #10b981; }
.history-point.WARN { background: #f59e0b; }
.history-point.FAIL { background: #ef4444; }
.history-point.TIMEOUT { background: #8b5cf6; }
.history-point.N\/A { background: #64748b; }

/* 可用性 */
.api-uptime {
  text-align: center;
  font-size: 0.875rem;
  font-weight: 600;
}

.uptime-excellent { color: #10b981; }
.uptime-good { color: #60a5fa; }
.uptime-warning { color: #f59e0b; }
.uptime-critical { color: #ef4444; }

/* 延迟 */
.api-latency {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.latency-row {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.latency-label {
  font-size: 0.75rem;
  color: #64748b;
  min-width: 32px;
}

.latency-value {
  font-size: 0.875rem;
  font-weight: 600;
}

.latency-fast { color: #10b981; }
.latency-normal { color: #60a5fa; }
.latency-slow { color: #f59e0b; }
.latency-very-slow { color: #ef4444; }
.latency-na { color: #64748b; font-size: 0.875rem; }

.api-message {
  font-size: 0.75rem;
  color: #94a3b8;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  line-height: 1.4;
  max-height: 2.8em;
}

.api-actions {
  display: flex;
  justify-content: center;
}

.ping-btn {
  padding: 0.25rem 0.5rem;
  background: transparent;
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.ping-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.3);
}

.ping-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 底部信息 */
.footer-info {
  text-align: center;
  padding: 1rem;
  color: #64748b;
  font-size: 0.875rem;
}

/* 响应式 */
@media (max-width: 1400px) {
  .api-item {
    grid-template-columns: 60px 1.2fr 55px 90px 90px 1.5fr 40px;
  }
}

@media (max-width: 1200px) {
  .api-item {
    grid-template-columns: 60px 1fr 50px 85px 80px 40px;
  }
  .api-message {
    display: none;
  }
}

@media (max-width: 900px) {
  .stats-row {
    grid-template-columns: repeat(3, 1fr);
  }

  .api-item {
    grid-template-columns: 50px 1fr 50px 80px 40px;
  }

  .api-history {
    display: none;
  }
}

@media (max-width: 600px) {
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .filter-bar {
    flex-direction: column;
  }

  .view-tabs {
    flex-wrap: wrap;
  }

  .api-item {
    grid-template-columns: 1fr 70px 40px;
  }

  .api-status, .api-uptime {
    display: none;
  }
}
</style>
