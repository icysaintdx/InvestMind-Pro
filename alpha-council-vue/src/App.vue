<template>
  <div id="app" class="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
    <!-- 粒子背景 -->
    <ParticleBackground 
      v-if="particlesEnabled"
      :enabled="particlesEnabled"
      :particleCount="particleCount"
      :particleColor="particleColor"
      :speed="particleSpeed"
    />
    
    <!-- 头部导航 -->
    <header class="navbar">
      <div class="container-full px-4 h-16 flex items-center justify-between">
        <!-- 左侧：Logo -->
        <div class="flex items-center">
          <h1 class="text-xl font-bold text-white">
            <span class="text-2xl mr-2">🏅</span>
            InvestMind Pro
          </h1>
          <button 
            @click="showProjectInfo = true" 
            class="project-info-btn"
            title="项目介绍"
          >
            <span class="info-icon">ℹ️</span>
          </button>
          <button 
            @click="showDocuments = true" 
            class="doc-btn"
            title="文档中心"
          >
            <span class="doc-icon">📚</span>
          </button>
        </div>
        
        <!-- 中间：API状态指示器 -->
        <div class="api-status-bar">
          <!-- 后端连接状态 -->
          <span 
            :class="['backend-status', backendStatus]"
            :title="backendStatusText"
          >
            <span class="status-icon">●</span>
            <span class="status-text">{{ backendStatusText }}</span>
          </span>
          
          <span class="status-divider">|</span>
          
          <span class="status-label">API</span>
          <span 
            v-for="provider in ['gemini', 'deepseek', 'qwen', 'siliconflow']" 
            :key="provider"
            :class="['status-item', getStatusClass(apiStatus[provider])]"
            :title="getProviderName(provider)"
          >
            <span class="status-dot"></span>
            <span class="status-name">{{ getProviderShort(provider) }}</span>
          </span>
          <span class="status-divider">|</span>
          <span class="status-label">数据</span>
          <span 
            v-for="channel in ['juhe', 'finnhub', 'tushare', 'akshare']" 
            :key="channel"
            :class="['status-item', getStatusClass(dataChannelStatus[channel])]"
            :title="getDataChannelName(channel)"
          >
            <span class="status-dot"></span>
            <span class="status-name">{{ getDataChannelShort(channel) }}</span>
          </span>
        </div>

        <!-- 右侧控制按钮 -->
        <div class="nav-controls">
          <button @click="showHotRankModal = true" class="nav-btn hot-rank-btn" title="查看热榜">
            <span class="btn-icon">🔥</span>
            <span class="btn-text">热榜</span>
          </button>
          <button @click="showChangelog = true" class="nav-btn version-btn" :title="`版本 ${versionInfo.version} - ${versionInfo.codename}`">
            <span class="btn-icon">📋</span>
            <span class="btn-text">v{{ versionInfo.version }}</span>
          </button>
          <button @click="toggleConfigMode" class="nav-btn" :class="{ active: configMode }">
            <span class="btn-icon">⚙️</span>
            <span class="btn-text">配置模式</span>
          </button>
          <button @click="showModelManager = true" class="nav-btn">
            <span class="btn-icon">🎯</span>
            <span class="btn-text">模型</span>
          </button>
          <button @click="showApiConfig = true" class="nav-btn">
            <span class="btn-icon">🔑</span>
            <span class="btn-text">API</span>
          </button>
          <button @click="toggleStylePanel" class="nav-btn">
            <span class="btn-icon">🎨</span>
            <span class="btn-text">样式</span>
          </button>
        </div>
      </div>
    </header>
    
    <!-- 主内容区 -->
    <main class="pt-20 container mx-auto px-4 pb-8">
      <AnalysisView />
    </main>
    
    <!-- 更新日志模态框 -->
    <div v-if="showChangelog" class="modal-overlay" @click.self="showChangelog = false">
      <div class="changelog-modal">
        <button @click="showChangelog = false" class="modal-close-btn">×</button>
        <ChangelogView />
      </div>
    </div>

    <!-- 项目介绍模态框 -->
    <div v-if="showProjectInfo" class="modal-overlay" @click.self="showProjectInfo = false">
      <div class="project-info-modal">
        <button @click="showProjectInfo = false" class="modal-close-btn">×</button>
        <ProjectInfoView />
      </div>
    </div>

    <!-- 文档中心模态框 -->
    <div v-if="showDocuments" class="modal-overlay" @click.self="showDocuments = false">
      <div class="document-modal">
        <button @click="showDocuments = false" class="modal-close-btn">×</button>
        <DocumentView />
      </div>
    </div>

    <!-- 数据透明化面板 -->
    <StockDataPanel ref="stockDataPanel" :stockData="currentStockData" />
    <NewsDataPanel ref="newsDataPanel" />
    
    <!-- 热榜模态框 -->
    <HotRankModal :isOpen="showHotRankModal" @close="showHotRankModal = false" />
  </div>
</template>

<script>
import { defineComponent, ref, computed, provide, onMounted, onUnmounted } from 'vue'
import AnalysisView from './views/AnalysisView.vue'
import ChangelogView from './views/ChangelogView.vue'
import ProjectInfoView from './views/ProjectInfoView.vue'
import DocumentView from './views/DocumentView.vue'
import ParticleBackground from './components/ParticleBackground.vue'
import StockDataPanel from './components/StockDataPanel.vue'
import NewsDataPanel from './components/NewsDataPanel.vue'
import HotRankModal from './components/HotRankModal.vue'
import { getVersionInfo } from './data/changelog.js'

export default defineComponent({
  name: 'App',
  components: {
    AnalysisView,
    ChangelogView,
    ProjectInfoView,
    DocumentView,
    ParticleBackground,
    StockDataPanel,
    NewsDataPanel,
    HotRankModal
  },
  setup() {
    const configMode = ref(false)
    const showModelManager = ref(false)
    const showApiConfig = ref(false)
    const showStylePanel = ref(false)
    const showChangelog = ref(false)
    const showProjectInfo = ref(false)
    const showDocuments = ref(false)
    const showHotRankModal = ref(false)
    
    const versionInfo = ref(getVersionInfo())
    
    const apiStatus = ref({
      gemini: 'unconfigured',
      deepseek: 'unconfigured',
      qwen: 'unconfigured',
      siliconflow: 'unconfigured'
    })

    const apiKeys = ref({
      gemini: '',
      deepseek: '',
      qwen: '',
      siliconflow: ''
    })
    
    const dataChannelKeys = ref({
      juhe: '',
      finnhub: '',
      tushare: ''
    })

    const dataChannelStatus = ref({
      juhe: 'unconfigured',
      finnhub: 'unconfigured',
      tushare: 'unconfigured',
      akshare: 'configured'
    })

    // 后端连接状态
    const backendStatus = ref('checking') // checking, connected, disconnected, error
    const backendStatusText = computed(() => {
      switch (backendStatus.value) {
        case 'connected': return '后端正常'
        case 'disconnected': return '后端断开'
        case 'error': return '后端错误'
        default: return '检查中...'
      }
    })
    
    // 数据透明化
    const currentStockData = ref(null)
    const stockDataPanel = ref(null)
    const newsDataPanel = ref(null)
    
    // 粒子背景设置
    const particlesEnabled = ref(true)
    const particleCount = ref(80)
    const particleSpeed = ref(1)
    const particleColor = ref('#3b82f6')

    const toggleConfigMode = () => {
      configMode.value = !configMode.value
    }

    const toggleStylePanel = () => {
      showStylePanel.value = !showStylePanel.value
    }

    const getStatusClass = (status) => {
      return status === 'configured' ? 'status-configured' : 
             status === 'error' ? 'status-error' : 'status-unconfigured'
    }

    const getProviderName = (key) => {
      const names = {
        gemini: 'Gemini',
        deepseek: 'DeepSeek',
        qwen: '通义千问',
        siliconflow: '硅基流动'
      }
      return names[key] || key
    }

    const getProviderShort = (key) => {
      const shorts = {
        gemini: 'GM',
        deepseek: 'DS',
        qwen: 'QW',
        siliconflow: 'SF'
      }
      return shorts[key] || key.toUpperCase().slice(0, 2)
    }

    const getDataChannelName = (key) => {
      const names = {
        juhe: '聚合数据',
        finnhub: 'FinnHub',
        tushare: 'Tushare',
        akshare: 'AKShare'
      }
      return names[key] || key
    }

    const getDataChannelShort = (key) => {
      const shorts = {
        juhe: 'JH',
        finnhub: 'FH',
        tushare: 'TS',
        akshare: 'AK'
      }
      return shorts[key] || key.toUpperCase().slice(0, 2)
    }

    // 后端健康检查
    const checkBackendHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/', { 
          method: 'GET',
          signal: AbortSignal.timeout(10000) // 10秒超时，给AI请求留出时间
        })
        if (response.ok) {
          backendStatus.value = 'connected'
          return true
        } else {
          backendStatus.value = 'error'
          return false
        }
      } catch (error) {
        // 不要因为单次超时就认为后端断开
        // 只有连续多次失败才认为断开
        console.warn('后端健康检查超时，可能是正在处理AI请求')
        // 不修改状态，保持当前状态
        return false
      }
    }
    
    // 加载后端配置
    const loadBackendConfig = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/config')
        if (response.ok) {
          const data = await response.json()
          console.log('App加载后端配置:', data)
          backendStatus.value = 'connected' // 更新后端状态
          
          // 更新 AI API Keys 和状态
          if (data.api_keys) {
            // 只更新 AI API
            const aiProviders = ['gemini', 'deepseek', 'qwen', 'siliconflow']
            aiProviders.forEach(provider => {
              if (data.api_keys[provider]) {
                // 只显示部分API Key用于安全
                apiKeys.value[provider] = data.api_keys[provider].substring(0, 20) + '...'
                apiStatus.value[provider] = 'configured'
                console.log(`[App] ✅ ${provider} API已配置`)
              } else {
                apiStatus.value[provider] = 'not_configured'
                console.log(`[App] ⚠️ ${provider} API未配置`)
              }
            })
            
            // 更新数据渠道 Keys 和状态
            const dataProviders = ['juhe', 'finnhub', 'tushare']
            dataProviders.forEach(provider => {
              if (data.api_keys[provider]) {
                dataChannelKeys.value[provider] = data.api_keys[provider].substring(0, 20) + '...'
                dataChannelStatus.value[provider] = 'configured'
                console.log(`[App] ✅ ${provider} 数据源已配置`)
              } else {
                dataChannelStatus.value[provider] = 'not_configured'
                console.log(`[App] ⚠️ ${provider} 数据源未配置`)
              }
            })
          }
          
          // 检查环境变量格式
          if (data.GEMINI_API_KEY) {
            apiKeys.value.gemini = data.GEMINI_API_KEY
            apiStatus.value.gemini = 'configured'
          }
          if (data.DEEPSEEK_API_KEY) {
            apiKeys.value.deepseek = data.DEEPSEEK_API_KEY
            apiStatus.value.deepseek = 'configured'
          }
          if (data.DASHSCOPE_API_KEY) {
            apiKeys.value.qwen = data.DASHSCOPE_API_KEY
            apiStatus.value.qwen = 'configured'
          }
          if (data.SILICONFLOW_API_KEY) {
            apiKeys.value.siliconflow = data.SILICONFLOW_API_KEY
            apiStatus.value.siliconflow = 'configured'
          }
          if (data.JUHE_API_KEY) {
            dataChannelKeys.value.juhe = data.JUHE_API_KEY
            dataChannelStatus.value.juhe = 'configured'
          }
          if (data.FINNHUB_API_KEY) {
            dataChannelKeys.value.finnhub = data.FINNHUB_API_KEY
            dataChannelStatus.value.finnhub = 'configured'
          }
          if (data.TUSHARE_TOKEN) {
            dataChannelKeys.value.tushare = data.TUSHARE_TOKEN
            dataChannelStatus.value.tushare = 'configured'
          }
        } else {
          console.error('后端响应错误:', response.status)
          backendStatus.value = 'error'
        }
      } catch (error) {
        console.error('App加载配置失败:', error)
        backendStatus.value = 'disconnected'
        testBackendConnection()
      }
    }
    
    // 测试后端连接
    const testBackendConnection = async () => {
      try {
        const response = await fetch('http://localhost:8000/')
        console.log('后端连接状态:', response.ok ? '成功' : '失败')
      } catch (error) {
        console.error('无法连接到后端:', error)
      }
    }

    // 监听粒子背景更新事件
    const handleParticleUpdate = (event) => {
      const { enabled, count, speed, color } = event.detail
      particlesEnabled.value = enabled
      particleCount.value = count
      particleSpeed.value = speed
      particleColor.value = color
    }

    // 组件挂载时加载配置
    onMounted(() => {
      loadBackendConfig()
      
      // 定期检查后端健康状态（10秒一次）
      const healthCheckInterval = setInterval(checkBackendHealth, 10000)
      
      // 组件卸载时清理定时器
      onUnmounted(() => {
        clearInterval(healthCheckInterval)
      })
      
      // 从localStorage加载样式设置
      const savedStyles = localStorage.getItem('styleSettings')
      if (savedStyles) {
        const styles = JSON.parse(savedStyles)
        if (styles.particlesEnabled !== undefined) {
          particlesEnabled.value = styles.particlesEnabled
          particleCount.value = styles.particleCount || 80
          particleSpeed.value = styles.particleSpeed || 1
          particleColor.value = styles.particleColor || '#3b82f6'
        }
        
        // 应用背景渐变
        const app = document.querySelector('#app')
        if (app && styles.gradientStart && styles.gradientEnd) {
          app.style.background = `linear-gradient(${styles.gradientAngle || 135}deg, ${styles.gradientStart} 0%, ${styles.gradientEnd} 100%)`
        }
      }
      
      // 监听粒子更新事件
      window.addEventListener('updateParticles', handleParticleUpdate)
    })

    // 组件卸载时移除监听器
    onUnmounted(() => {
      window.removeEventListener('updateParticles', handleParticleUpdate)
    })

    // 保存 API 配置
    const saveApiConfig = async (keys) => {
      try {
        // 分离 AI API 和数据渠道
        const aiKeys = {}
        const dataKeys = {}
        
        Object.keys(keys).forEach(key => {
          if (['gemini', 'deepseek', 'qwen', 'siliconflow'].includes(key)) {
            aiKeys[key] = keys[key]
          } else if (['juhe', 'finnhub', 'tushare'].includes(key)) {
            dataKeys[key] = keys[key]
          }
        })
        
        // 更新本地状态
        apiKeys.value = { ...apiKeys.value, ...aiKeys }
        dataChannelKeys.value = { ...dataChannelKeys.value, ...dataKeys }
        
        // 保存到后端
        const response = await fetch('http://localhost:8000/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_keys: keys })
        })
        
        if (response.ok) {
          console.log('API配置保存成功')
          // 更新 AI API 状态
          Object.keys(aiKeys).forEach(provider => {
            apiStatus.value[provider] = aiKeys[provider] ? 'configured' : 'unconfigured'
          })
          // 更新数据渠道状态
          Object.keys(dataKeys).forEach(provider => {
            dataChannelStatus.value[provider] = dataKeys[provider] ? 'configured' : 'unconfigured'
          })
        } else {
          console.error('保存配置失败:', response.status)
        }
      } catch (error) {
        console.error('保存配置失败:', error)
      }
    }

    // 更新 API 状态
    const updateApiStatus = (provider, status) => {
      apiStatus.value[provider] = status
    }

    // 提供给子组件
    provide('configMode', configMode)
    provide('showModelManager', showModelManager)
    provide('showApiConfig', showApiConfig)
    provide('showStylePanel', showStylePanel)
    provide('apiStatus', apiStatus)
    provide('apiKeys', apiKeys)
    provide('dataChannelKeys', dataChannelKeys)
    provide('dataChannelStatus', dataChannelStatus)
    provide('saveApiConfig', saveApiConfig)
    provide('updateApiStatus', updateApiStatus)
    provide('currentStockData', currentStockData)
    provide('stockDataPanel', stockDataPanel)
    provide('newsDataPanel', newsDataPanel)

    return {
      configMode,
      showModelManager,
      showApiConfig,
      showStylePanel,
      showChangelog,
      showProjectInfo,
      showDocuments,
      showHotRankModal,
      versionInfo,
      backendStatus,
      backendStatusText,
      apiStatus,
      apiKeys,
      dataChannelKeys,
      dataChannelStatus,
      currentStockData,
      stockDataPanel,
      newsDataPanel,
      particlesEnabled,
      particleCount,
      particleSpeed,
      particleColor,
      toggleConfigMode,
      toggleStylePanel,
      getStatusClass,
      getProviderName,
      getProviderShort,
      getDataChannelName,
      getDataChannelShort,
      saveApiConfig,
      updateApiStatus
    }
  }
})
</script>

<style>
/* Tailwind CSS 将通过配置引入 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Tailwind-like utility classes (临时使用，后续安装Tailwind) */
.min-h-screen { min-height: 100vh; }
.bg-gradient-to-br { background: linear-gradient(to bottom right, #0f172a, #1e3a8a, #0f172a); }
.from-slate-950 { --tw-gradient-from: #020617; }
.via-blue-950 { --tw-gradient-via: #172554; }
.to-slate-900 { --tw-gradient-to: #0f172a; }
.fixed { position: fixed; }
.top-0 { top: 0; }
.w-full { width: 100%; }
.z-50 { z-index: 50; }
.backdrop-blur-md { backdrop-filter: blur(12px); }
.bg-slate-900\/70 { background-color: rgba(15, 23, 42, 0.7); }
.border-b { border-bottom-width: 1px; }
.border-slate-700\/50 { border-color: rgba(51, 65, 85, 0.5); }
.container {
  max-width: 1280px;
  margin: 0 auto;
}

.container-full {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}
.mx-auto { margin-left: auto; margin-right: auto; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.h-16 { height: 4rem; }
.space-x-4 > * + * { margin-left: 1rem; }
.space-x-6 > * + * { margin-left: 1.5rem; }
.text-2xl { font-size: 1.5rem; }
.text-xl { font-size: 1.25rem; }
.text-lg { font-size: 1.125rem; }
.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.pt-20 { padding-top: 5rem; }
.pb-8 { padding-bottom: 2rem; }
.mr-2 { margin-right: 0.5rem; }
.mt-1 { margin-top: 0.25rem; }
.pl-8 { padding-left: 2rem; }
.text-white { color: #ffffff; }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
.mb-6 { margin-bottom: 1.5rem; }
.mb-4 { margin-bottom: 1rem; }
.gap-2 { gap: 0.5rem; }
.gap-4 { gap: 1rem; }
.space-y-8 > * + * { margin-top: 2rem; }
.text-slate-300 { color: #cbd5e1; }
.text-slate-400 { color: #94a3b8; }
.text-slate-500 { color: #64748b; }
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.uppercase { text-transform: uppercase; }
.tracking-wide { letter-spacing: 0.05em; }
.whitespace-nowrap { white-space: nowrap; }
.font-mono { font-family: 'Consolas', monospace; }
.leading-relaxed { line-height: 1.625; }

/* 导航栏固定 */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

/* API状态指示器 */
.api-status-bar {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  padding: 0.5rem 1rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid #334155;
  border-radius: 0.5rem;
}

.status-group {
  display: flex;
  gap: 0.375rem;
  align-items: center;
}

.group-label {
  font-size: 0.625rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 0.25rem;
}

.status-divider {
  width: 1px;
  height: 1.25rem;
  background: #334155;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 0.375rem;
  font-size: 0.75rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 0.375rem;
  font-size: 0.75rem;
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: #64748b;
  flex-shrink: 0;
}

.status-configured .status-dot {
  background: #10b981;
  box-shadow: 0 0 4px rgba(16, 185, 129, 0.5);
}

.status-error .status-dot {
  background: #ef4444;
  box-shadow: 0 0 4px rgba(239, 68, 68, 0.5);
}

.status-name {
  color: #94a3b8;
  font-weight: 500;
}

/* 后端连接状态 */
.backend-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.backend-status .status-icon {
  font-size: 0.625rem;
  animation: pulse 2s ease-in-out infinite;
}

.backend-status.checking {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

.backend-status.connected {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.backend-status.connected .status-icon {
  animation: none;
}

.backend-status.disconnected {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.backend-status.disconnected .status-icon {
  animation: blink 1s ease-in-out infinite;
}

.backend-status.error {
  background: rgba(251, 146, 60, 0.15);
  color: #fb923c;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes blink {
  0%, 50%, 100% { opacity: 1; }
  25%, 75% { opacity: 0.3; }
}

/* 导航栏控制按钮 */
.nav-controls {
  display: flex;
  gap: 0.5rem;
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.375rem;
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: rgba(51, 65, 85, 0.5);
  color: white;
  border-color: #475569;
}

.nav-btn.active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-color: #3b82f6;
}

.nav-btn.hot-rank-btn {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.nav-btn.hot-rank-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #ef4444;
}

.nav-btn.version-btn {
  background: rgba(16, 185, 129, 0.1);
  border-color: #10b981;
  color: #10b981;
}

.nav-btn.version-btn:hover {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10b981;
  color: #10b981;
}

.btn-icon {
  font-size: 0.875rem;
}

.btn-text {
  display: none;
}

@media (min-width: 768px) {
  .btn-text {
    display: inline;
  }
}

/* 响应式网格布局 */
@media (min-width: 640px) {
  .sm\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (min-width: 768px) {
  .md\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (min-width: 1024px) {
  .lg\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .lg\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .lg\:grid-cols-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
}
@media (min-width: 1280px) {
  .xl\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .xl\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
@media (min-width: 1536px) {
  .\\2xl\:grid-cols-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
}

/* 背景动画 */
.bg-gradient-to-br.from-slate-950.via-blue-950.to-slate-900 {
  background: linear-gradient(135deg, #020617 0%, #172554 50%, #0f172a 100%);
  background-size: 400% 400%;
  animation: gradient-shift 15s ease infinite;
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* 导航链接样式 */
.nav-link {
  color: #cbd5e1;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.nav-link:hover {
  color: #60a5fa;
  transform: translateY(-1px);
}

.nav-link.router-link-active {
  color: #3b82f6;
}

/* 渐变文本 */
.bg-gradient-to-r {
  background: linear-gradient(to right, #60a5fa, #06b6d4);
  -webkit-background-clip: text;
  background-clip: text;
}

.bg-clip-text {
  -webkit-text-fill-color: transparent;
}

.text-transparent {
  color: transparent;
}

/* 更新日志模态框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  overflow: hidden;
}

.changelog-modal {
  position: relative;
  width: 100%;
  max-width: 1400px;
  max-height: 90vh;
  overflow-y: auto;
  background: transparent;
}

.modal-close-btn {
  position: fixed;
  top: 2rem;
  right: 2rem;
  width: 3rem;
  height: 3rem;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 101;
  transition: all 0.2s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.modal-close-btn:hover {
  background: rgba(220, 38, 38, 1);
  transform: scale(1.1);
}

/* 项目介绍按钮 */
.project-info-btn {
  margin-left: 0.75rem;
  width: 2rem;
  height: 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.project-info-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.5);
}

.project-info-btn .info-icon {
  font-size: 1.2rem;
  filter: brightness(1.2);
}

/* 文档按钮 */
.doc-btn {
  margin-left: 0.5rem;
  width: 2rem;
  height: 2rem;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.doc-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.5);
}

.doc-btn .doc-icon {
  font-size: 1.2rem;
  filter: brightness(1.2);
}

/* 项目介绍模态框 */
.project-info-modal {
  position: relative;
  width: 100%;
  max-width: 1200px;
  max-height: 90vh;
  overflow-y: auto;
  background: rgba(15, 23, 42, 0.98);
  border-radius: 20px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

/* 滚动条美化 */
.project-info-modal::-webkit-scrollbar {
  width: 8px;
}

.project-info-modal::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 10px;
}

.project-info-modal::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
}

.project-info-modal::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
}

/* 文档中心模态框 */
.document-modal {
  position: relative;
  width: 95vw;
  max-width: 1800px;
  height: 90vh;
  background: transparent;
  border-radius: 20px;
  overflow: hidden;
}

.document-modal::-webkit-scrollbar {
  width: 8px;
}

.document-modal::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 10px;
}

.document-modal::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  border-radius: 10px;
}

.document-modal::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
}
</style>
