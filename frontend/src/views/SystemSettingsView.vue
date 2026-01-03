<template>
  <div class="settings-container">
    <h1 class="page-title">
      <span class="title-icon">⚙️</span>
      系统设置
      <span class="title-actions">
        <span class="info-btn" @click="$emit('show-project-info')" title="项目介绍">ℹ️</span>
        <span class="version-btn" @click="$emit('show-changelog')" title="更新日志">v{{ version }}</span>
      </span>
    </h1>
    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.id" :class="['tab-btn', { active: activeTab === tab.id }]" @click="activeTab = tab.id">{{ tab.name }}</button>
    </div>

    <!-- 数据存储设置 -->
    <div v-show="activeTab === 'storage'" class="settings-section">
      <h2>📦 数据存储设置</h2>
      <div class="setting-item"><label>新闻保留天数</label><input type="number" v-model.number="settings.newsRetentionDays" min="1" max="365" /><span class="hint">超过此天数的新闻将被清理</span></div>
      <div class="setting-item"><label>分析记录保留天数</label><input type="number" v-model.number="settings.analysisRetentionDays" min="1" max="365" /><span class="hint">智能分析结果的保留时间</span></div>
      <div class="setting-item"><label>交易记录保留天数</label><input type="number" v-model.number="settings.tradingRetentionDays" min="1" max="365" /><span class="hint">模拟交易记录的保留时间</span></div>
      <div class="setting-item"><label>自动清理</label><button :class="['toggle-btn', settings.autoCleanup ? 'enabled' : 'disabled']" @click="settings.autoCleanup = !settings.autoCleanup">{{ settings.autoCleanup ? '已开启' : '已关闭' }}</button></div>
      <div class="setting-item"><button class="btn-warning" @click="manualCleanup" :disabled="cleaning">{{ cleaning ? '清理中...' : '立即清理' }}</button><span class="hint">手动触发数据清理</span></div>
    </div>

    <!-- 数据源配置 -->
    <div v-show="activeTab === 'datasource'" class="settings-section">
      <h2>🔌 数据源配置</h2>

      <!-- 数据源列表 -->
      <div class="subsection">
        <h3>数据源状态</h3>
        <div class="source-list">
          <div v-for="(source, key) in dataSources" :key="key" class="source-card">
            <div class="source-header">
              <span class="source-name">{{ source.name }}</span>
              <button
                :class="['toggle-btn', source.enabled ? 'enabled' : 'disabled']"
                @click="toggleSource(key, !source.enabled); source.enabled = !source.enabled"
              >
                {{ source.enabled ? '已启用' : '已禁用' }}
              </button>
            </div>
            <div class="source-stats">
              <span :class="['health-badge', getHealthClass(sourceHealth[key])]">
                {{ sourceHealth[key]?.health_score?.toFixed(0) || '--' }}分
              </span>
              <span class="stat-item">{{ sourceHealth[key]?.avg_response_time || '--' }}</span>
              <span class="stat-item">成功率 {{ sourceHealth[key]?.success_rate || '--' }}</span>
            </div>
            <div class="source-desc">{{ source.description }}</div>
          </div>
        </div>
        <div class="action-row">
          <button class="btn-secondary" @click="testAllSources" :disabled="testingAll">
            {{ testingAll ? '测试中...' : '测试所有数据源' }}
          </button>
          <button class="btn-secondary" @click="loadSourceHealth">刷新状态</button>
        </div>
      </div>

      <!-- 数据类别配置 -->
      <div class="subsection">
        <h3>数据类别配置</h3>
        <div class="category-list">
          <div v-for="(cat, key) in dataCategories" :key="key" class="category-item">
            <div class="cat-info">
              <span class="cat-name">{{ cat.name }}</span>
              <span class="cat-desc">{{ cat.description }}</span>
            </div>
            <div class="cat-config">
              <select v-model="cat.primary" @change="updateCategoryPrimary(key, cat.primary)" class="source-select">
                <option v-for="src in cat.sources" :key="src" :value="src">{{ getSourceName(src) }}</option>
              </select>
              <div class="cache-config">
                <label>缓存</label>
                <input type="number" v-model.number="cat.cache_ttl" min="0" class="cache-input" @change="updateCacheTTL(key, cat.cache_ttl)" />
                <span class="cache-unit">秒</span>
              </div>
            </div>
            <button class="btn-test" @click="testCategory(key)" :disabled="testingCategory === key">
              {{ testingCategory === key ? '...' : '测试' }}
            </button>
          </div>
        </div>
      </div>

      <!-- 测试结果 -->
      <div v-if="testResults.length > 0" class="subsection">
        <h3>测试结果</h3>
        <div class="test-results">
          <div v-for="(result, idx) in testResults" :key="idx" class="test-result-item">
            <span class="result-source">{{ getSourceName(result.source) }}</span>
            <span :class="['result-status', result.success ? 'success' : 'error']">
              {{ result.success ? '成功' : '失败' }}
            </span>
            <span class="result-time">{{ result.response_time_ms?.toFixed(0) || '--' }}ms</span>
            <span v-if="result.error" class="result-error">{{ result.error }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 系统信息 -->
    <div v-show="activeTab === 'system'" class="settings-section">
      <h2>📊 系统信息</h2>

      <!-- 数据统计 -->
      <div class="subsection">
        <h3>数据统计</h3>
        <div class="stats-grid">
          <div class="stat-card"><div class="stat-value">{{ sysInfo.dataSourceCount || 5 }}</div><div class="stat-label">数据源</div></div>
          <div class="stat-card"><div class="stat-value">{{ sysInfo.interfaceCount || 0 }}</div><div class="stat-label">接口数量</div></div>
          <div class="stat-card"><div class="stat-value">{{ sysInfo.categoryCount || 0 }}</div><div class="stat-label">数据类别</div></div>
          <div class="stat-card"><div class="stat-value">{{ dbStats.newsCount || 0 }}</div><div class="stat-label">新闻记录</div></div>
          <div class="stat-card"><div class="stat-value">{{ dbStats.analysisCount || 0 }}</div><div class="stat-label">分析记录</div></div>
          <div class="stat-card"><div class="stat-value">{{ dbStats.tradingCount || 0 }}</div><div class="stat-label">交易记录</div></div>
        </div>
      </div>

      <!-- 存储信息 -->
      <div class="subsection">
        <h3>存储信息</h3>
        <div class="stats-grid">
          <div class="stat-card"><div class="stat-value">{{ formatSize(dbStats.dbSize || 0) }}</div><div class="stat-label">数据库大小</div></div>
          <div class="stat-card"><div class="stat-value">{{ formatSize(sysInfo.cacheSize || 0) }}</div><div class="stat-label">缓存大小</div></div>
          <div class="stat-card"><div class="stat-value">{{ formatSize(sysInfo.logSize || 0) }}</div><div class="stat-label">日志大小</div></div>
        </div>
      </div>

      <!-- 运行状态 -->
      <div class="subsection">
        <h3>运行状态</h3>
        <div class="stats-grid">
          <div class="stat-card"><div class="stat-value">{{ sysInfo.uptime || '--' }}</div><div class="stat-label">运行时间</div></div>
          <div class="stat-card"><div class="stat-value">{{ formatSize(sysInfo.memoryUsage || 0) }}</div><div class="stat-label">内存占用</div></div>
          <div class="stat-card"><div class="stat-value">{{ sysInfo.cpuUsage || '--' }}%</div><div class="stat-label">CPU使用</div></div>
          <div class="stat-card"><div class="stat-value">{{ sysInfo.pythonVersion || '--' }}</div><div class="stat-label">Python版本</div></div>
          <div class="stat-card"><div class="stat-value">{{ sysInfo.akshareVersion || '--' }}</div><div class="stat-label">AKShare版本</div></div>
          <div class="stat-card"><div class="stat-value">{{ sysInfo.requestCount || 0 }}</div><div class="stat-label">今日请求</div></div>
        </div>
      </div>

      <div class="action-row">
        <button class="btn-secondary" @click="loadSystemInfo">刷新信息</button>
      </div>
    </div>

    <div class="actions"><button class="btn-primary" @click="saveSettings" :disabled="saving">{{ saving ? '保存中...' : '保存设置' }}</button></div>
  </div>
</template>
<script>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import API_BASE_URL from '@/config/api.js'
import { CURRENT_VERSION } from '@/data/changelog.js'

export default {
  name: 'SystemSettingsView',
  emits: ['show-project-info', 'show-changelog'],
  setup() {
    const activeTab = ref('storage')
    const saving = ref(false)
    const cleaning = ref(false)
    const testingAll = ref(false)
    const testingCategory = ref('')
    const version = ref(CURRENT_VERSION)

    const tabs = [
      { id: 'storage', name: '数据存储' },
      { id: 'datasource', name: '数据源' },
      { id: 'system', name: '系统信息' }
    ]

    const settings = reactive({
      newsRetentionDays: 30,
      analysisRetentionDays: 90,
      tradingRetentionDays: 365,
      autoCleanup: true
    })

    const dbStats = reactive({})
    const sysInfo = reactive({})
    const dataSources = reactive({})
    const dataCategories = reactive({})
    const sourceHealth = reactive({})
    const testResults = ref([])

    // 加载设置
    const loadSettings = async () => {
      try {
        const r = await axios.get(API_BASE_URL + '/api/system/settings')
        if (r.data.success) Object.assign(settings, r.data.data)
      } catch (e) { console.error('加载设置失败:', e) }
    }

    // 加载数据库统计
    const loadDbStats = async () => {
      try {
        const r = await axios.get(API_BASE_URL + '/api/system/db-stats')
        if (r.data.success) Object.assign(dbStats, r.data.data)
      } catch (e) { console.error('加载数据库统计失败:', e) }
    }

    // 加载系统信息
    const loadSystemInfo = async () => {
      try {
        const r = await axios.get(API_BASE_URL + '/api/system/info')
        if (r.data.success) Object.assign(sysInfo, r.data.data)
      } catch (e) { console.error('加载系统信息失败:', e) }
    }

    // 加载数据源配置
    const loadDataSourceConfig = async () => {
      try {
        const r = await axios.get(API_BASE_URL + '/api/datasource/config')
        if (r.data.success && r.data.data) {
          Object.assign(dataSources, r.data.data.data_sources || {})
          Object.assign(dataCategories, r.data.data.data_categories || {})
        }
      } catch (e) { console.error('加载数据源配置失败:', e) }
    }

    // 加载数据源健康状态
    const loadSourceHealth = async () => {
      try {
        const r = await axios.get(API_BASE_URL + '/api/datasource/health')
        if (r.data.success) Object.assign(sourceHealth, r.data.data || {})
      } catch (e) { console.error('加载健康状态失败:', e) }
    }

    // 保存设置
    const saveSettings = async () => {
      saving.value = true
      try {
        await axios.post(API_BASE_URL + '/api/system/settings', settings)
        alert('设置已保存')
      } catch (e) {
        alert('保存失败: ' + e.message)
      } finally {
        saving.value = false
      }
    }

    // 手动清理
    const manualCleanup = async () => {
      if (!confirm('确定要立即清理过期数据吗？')) return
      cleaning.value = true
      try {
        await axios.post(API_BASE_URL + '/api/system/cleanup')
        alert('清理完成')
        loadDbStats()
      } catch (e) {
        alert('清理失败')
      } finally {
        cleaning.value = false
      }
    }

    // 切换数据源启用状态
    const toggleSource = async (source, enabled) => {
      try {
        const endpoint = enabled ? 'enable' : 'disable'
        await axios.post(API_BASE_URL + `/api/datasource/source/${source}/${endpoint}`)
      } catch (e) {
        console.error('切换数据源状态失败:', e)
        dataSources[source].enabled = !enabled
      }
    }

    // 测试所有数据源
    const testAllSources = async () => {
      testingAll.value = true
      testResults.value = []
      try {
        const r = await axios.post(API_BASE_URL + '/api/datasource/test-all')
        if (r.data.success && r.data.data) {
          testResults.value = Object.values(r.data.data)
        }
        loadSourceHealth()
      } catch (e) {
        console.error('测试失败:', e)
      } finally {
        testingAll.value = false
      }
    }

    // 测试指定类别
    const testCategory = async (category) => {
      testingCategory.value = category
      testResults.value = []
      try {
        const r = await axios.post(API_BASE_URL + '/api/datasource/test-category', { category })
        if (r.data.success && r.data.results) {
          testResults.value = r.data.results
        }
      } catch (e) {
        console.error('测试失败:', e)
      } finally {
        testingCategory.value = ''
      }
    }

    // 更新类别主数据源
    const updateCategoryPrimary = async (category, primary) => {
      try {
        await axios.put(API_BASE_URL + `/api/datasource/config/category/${category}`, { primary })
      } catch (e) {
        console.error('更新失败:', e)
      }
    }

    // 更新缓存时效
    const updateCacheTTL = async (category, cache_ttl) => {
      try {
        await axios.put(API_BASE_URL + `/api/datasource/config/category/${category}`, { cache_ttl })
      } catch (e) {
        console.error('更新失败:', e)
      }
    }

    // 获取数据源名称
    const getSourceName = (key) => {
      const names = {
        tdx: '通达信',
        tushare: 'Tushare',
        akshare: 'AKShare',
        sina: '新浪财经',
        juhe: '聚合数据',
        cninfo: '巨潮',
        eastmoney: '东方财富',
        tencent: '腾讯财经'
      }
      return names[key] || key
    }

    // 获取健康状态样式
    const getHealthClass = (health) => {
      if (!health || !health.health_score) return 'unknown'
      const score = health.health_score
      if (score >= 80) return 'good'
      if (score >= 60) return 'warning'
      return 'bad'
    }

    // 格式化文件大小
    const formatSize = (b) => {
      if (b < 1024) return b + ' B'
      if (b < 1048576) return (b / 1024).toFixed(1) + ' KB'
      if (b < 1073741824) return (b / 1048576).toFixed(1) + ' MB'
      return (b / 1073741824).toFixed(2) + ' GB'
    }

    onMounted(() => {
      loadSettings()
      loadDbStats()
      loadSystemInfo()
      loadDataSourceConfig()
      loadSourceHealth()
    })

    return {
      activeTab, tabs, settings, dbStats, sysInfo, dataSources, dataCategories,
      sourceHealth, testResults, saving, cleaning, testingAll, testingCategory, version,
      loadSettings, loadDbStats, loadSystemInfo, loadSourceHealth, saveSettings,
      manualCleanup, toggleSource, testAllSources, testCategory,
      updateCategoryPrimary, updateCacheTTL, getSourceName, getHealthClass, formatSize
    }
  }
}
</script>
<style scoped>
.settings-container { max-width: 1000px; margin: 0 auto; padding: 2rem; }
.page-title { display: flex; align-items: center; gap: 0.5rem; font-size: 1.5rem; color: #e2e8f0; margin-bottom: 1.5rem; }
.title-icon { font-size: 1.75rem; }
.title-actions { margin-left: auto; display: flex; align-items: center; gap: 0.75rem; }
.info-btn { cursor: pointer; font-size: 1.25rem; opacity: 0.7; transition: opacity 0.2s; }
.info-btn:hover { opacity: 1; }
.version-btn { cursor: pointer; padding: 0.25rem 0.5rem; background: rgba(59,130,246,0.2); border: 1px solid rgba(59,130,246,0.3); border-radius: 0.25rem; color: #60a5fa; font-size: 0.875rem; transition: all 0.2s; }
.version-btn:hover { background: rgba(59,130,246,0.3); }
.tabs { display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }
.tab-btn { padding: 0.5rem 1rem; background: rgba(30,41,59,0.5); border: 1px solid rgba(51,65,85,0.5); border-radius: 0.5rem; color: #94a3b8; cursor: pointer; transition: all 0.2s; }
.tab-btn:hover { background: rgba(51,65,85,0.5); color: #e2e8f0; }
.tab-btn.active { background: rgba(59,130,246,0.2); border-color: #3b82f6; color: #3b82f6; }
.settings-section { background: rgba(30,41,59,0.3); border: 1px solid rgba(51,65,85,0.5); border-radius: 0.75rem; padding: 1.5rem; margin-bottom: 1rem; }
.settings-section h2 { font-size: 1.1rem; color: #e2e8f0; margin-bottom: 1rem; padding-bottom: 0.5rem; border-bottom: 1px solid rgba(51,65,85,0.3); }
.subsection { margin-bottom: 1.5rem; }
.subsection h3 { font-size: 0.95rem; color: #94a3b8; margin-bottom: 0.75rem; }
.setting-item { display: flex; align-items: center; gap: 1rem; margin-bottom: 0.75rem; flex-wrap: wrap; }
.setting-item label:first-child { min-width: 160px; color: #e2e8f0; }
.setting-item input[type="text"], .setting-item input[type="password"], .setting-item input[type="number"] { padding: 0.5rem 0.75rem; background: rgba(15,23,42,0.5); border: 1px solid rgba(51,65,85,0.5); border-radius: 0.375rem; color: #e2e8f0; width: 200px; }
.setting-item input:focus { outline: none; border-color: #3b82f6; }
.setting-item button { padding: 0.5rem 1rem; background: #3b82f6; color: white; border: none; border-radius: 0.375rem; cursor: pointer; transition: all 0.2s; }
.setting-item button:hover:not(:disabled) { background: #2563eb; }
.setting-item button:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-warning { background: rgba(245,158,11,0.2) !important; color: #f59e0b !important; border: 1px solid rgba(245,158,11,0.3) !important; }
.btn-warning:hover:not(:disabled) { background: rgba(245,158,11,0.3) !important; }
.btn-secondary { padding: 0.5rem 1rem; background: rgba(51,65,85,0.5); color: #e2e8f0; border: 1px solid rgba(71,85,105,0.5); border-radius: 0.375rem; cursor: pointer; transition: all 0.2s; }
.btn-secondary:hover:not(:disabled) { background: rgba(71,85,105,0.5); }
.btn-secondary:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-test { padding: 0.25rem 0.75rem; background: rgba(59,130,246,0.2); color: #60a5fa; border: 1px solid rgba(59,130,246,0.3); border-radius: 0.25rem; cursor: pointer; font-size: 0.75rem; }
.btn-test:hover:not(:disabled) { background: rgba(59,130,246,0.3); }
.btn-test:disabled { opacity: 0.5; }
.hint { font-size: 0.75rem; color: #64748b; }
.stats-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(140px, 1fr)); gap: 1rem; }
.stat-card { padding: 1rem; background: rgba(15,23,42,0.5); border-radius: 0.5rem; text-align: center; }
.stat-value { font-size: 1.25rem; font-weight: 600; color: #3b82f6; }
.stat-label { font-size: 0.75rem; color: #94a3b8; margin-top: 0.25rem; }
.actions { margin-top: 1.5rem; }
.btn-primary { padding: 0.5rem 1.5rem; background: #3b82f6; color: white; border: none; border-radius: 0.375rem; cursor: pointer; transition: all 0.2s; }
.btn-primary:hover:not(:disabled) { background: #2563eb; }
.btn-primary:disabled { opacity: 0.5; cursor: not-allowed; }
.action-row { display: flex; gap: 0.75rem; margin-top: 1rem; }

/* 数据源列表 */
.source-list { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 1rem; }
.source-card { padding: 1rem; background: rgba(15,23,42,0.5); border: 1px solid rgba(51,65,85,0.3); border-radius: 0.5rem; position: relative; }
.source-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
.source-name { font-weight: 600; color: #e2e8f0; }
.toggle-btn { padding: 0.25rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; cursor: pointer; border: none; transition: all 0.2s; }
.toggle-btn.enabled { background: rgba(16,185,129,0.2); color: #10b981; }
.toggle-btn.disabled { background: rgba(100,116,139,0.2); color: #94a3b8; }
.toggle-btn:hover { opacity: 0.8; }
.source-stats { display: flex; gap: 0.5rem; align-items: center; margin-bottom: 0.5rem; flex-wrap: wrap; }
.health-badge { padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; font-weight: 500; }
.health-badge.good { background: rgba(16,185,129,0.2); color: #10b981; }
.health-badge.warning { background: rgba(245,158,11,0.2); color: #f59e0b; }
.health-badge.bad { background: rgba(239,68,68,0.2); color: #ef4444; }
.health-badge.unknown { background: rgba(100,116,139,0.2); color: #94a3b8; }
.stat-item { font-size: 0.75rem; color: #94a3b8; }
.source-desc { font-size: 0.75rem; color: #64748b; }

/* 数据类别配置 */
.category-list { display: flex; flex-direction: column; gap: 0.75rem; }
.category-item { display: flex; align-items: center; gap: 1rem; padding: 0.75rem; background: rgba(15,23,42,0.3); border-radius: 0.375rem; }
.cat-info { flex: 1; min-width: 150px; }
.cat-name { font-weight: 500; color: #e2e8f0; display: block; }
.cat-desc { font-size: 0.75rem; color: #64748b; }
.cat-config { display: flex; align-items: center; gap: 1rem; }
.source-select { padding: 0.375rem 0.5rem; background: rgba(15,23,42,0.5); border: 1px solid rgba(51,65,85,0.5); border-radius: 0.25rem; color: #e2e8f0; font-size: 0.875rem; }
.cache-config { display: flex; align-items: center; gap: 0.25rem; }
.cache-config label { font-size: 0.75rem; color: #94a3b8; }
.cache-input { width: 70px; padding: 0.25rem 0.5rem; background: rgba(15,23,42,0.5); border: 1px solid rgba(51,65,85,0.5); border-radius: 0.25rem; color: #e2e8f0; font-size: 0.875rem; text-align: right; }
.cache-unit { font-size: 0.75rem; color: #64748b; }

/* 测试结果 */
.test-results { display: flex; flex-direction: column; gap: 0.5rem; }
.test-result-item { display: flex; align-items: center; gap: 1rem; padding: 0.5rem 0.75rem; background: rgba(15,23,42,0.3); border-radius: 0.25rem; }
.result-source { min-width: 80px; font-weight: 500; color: #e2e8f0; }
.result-status { padding: 0.125rem 0.5rem; border-radius: 0.25rem; font-size: 0.75rem; }
.result-status.success { background: rgba(16,185,129,0.2); color: #10b981; }
.result-status.error { background: rgba(239,68,68,0.2); color: #ef4444; }
.result-time { font-size: 0.875rem; color: #94a3b8; }
.result-error { font-size: 0.75rem; color: #ef4444; flex: 1; text-align: right; }
</style>
