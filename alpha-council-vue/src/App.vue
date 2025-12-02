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
      <div class="container mx-auto px-4 h-16 flex items-center justify-between">
        <div class="flex items-center space-x-6">
          <h1 class="text-xl font-bold text-white">
            <span class="text-2xl mr-2">🏅</span>
            InvestMind Pro
          </h1>
          
          <!-- API状态指示器 -->
          <div class="api-status-bar">
            <span 
              v-for="(status, key) in apiStatus" 
              :key="key"
              class="status-indicator"
              :class="getStatusClass(status)"
              :title="getProviderName(key)"
            >
              <span class="status-dot"></span>
              <span class="status-name">{{ getProviderShort(key) }}</span>
            </span>
          </div>

          <nav class="flex space-x-4">
            <a href="#" class="text-white hover:text-gray-300">📊 分析中心</a>
            <a href="#" class="text-white hover:text-gray-300">🤖 模型管理</a>
            <a href="#" class="text-white hover:text-gray-300">⚙️ 设置</a>
          </nav>
        </div>

        <!-- 右侧控制按钮 -->
        <div class="nav-controls">
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
  </div>
</template>

<script>
import { defineComponent, ref, provide, onMounted, onUnmounted } from 'vue'
import AnalysisView from './views/AnalysisView.vue'
import ParticleBackground from './components/ParticleBackground.vue'

export default defineComponent({
  name: 'App',
  components: {
    AnalysisView,
    ParticleBackground
  },
  setup() {
    const configMode = ref(false)
    const showModelManager = ref(false)
    const showApiConfig = ref(false)
    const showStylePanel = ref(false)
    
    const apiStatus = ref({
      gemini: 'unconfigured',
      deepseek: 'unconfigured',
      qwen: 'unconfigured',
      siliconflow: 'unconfigured',
      juhe: 'unconfigured'
    })

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
        siliconflow: '硅基流动',
        juhe: '聚合数据'
      }
      return names[key] || key
    }

    const getProviderShort = (key) => {
      const shorts = {
        gemini: 'GM',
        deepseek: 'DS',
        qwen: 'QW',
        siliconflow: 'SF',
        juhe: 'JH'
      }
      return shorts[key] || key.toUpperCase().slice(0, 2)
    }

    // 加载后端配置
    const loadBackendConfig = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/config')
        if (response.ok) {
          const data = await response.json()
          console.log('App加载后端配置:', data)
          
          // 更新API状态 - 检查.env文件中的配置
          const apiProviders = ['gemini', 'deepseek', 'qwen', 'siliconflow', 'juhe']
          apiProviders.forEach(provider => {
            // 检查环境变量配置
            if (data[`${provider}_api_key`] || data.api_keys?.[provider]) {
              apiStatus.value[provider] = 'configured'
            }
          })
          
          // 检查其他可能的配置格式
          if (data.GEMINI_API_KEY) apiStatus.value.gemini = 'configured'
          if (data.DEEPSEEK_API_KEY) apiStatus.value.deepseek = 'configured'
          if (data.DASHSCOPE_API_KEY) apiStatus.value.qwen = 'configured'
          if (data.SILICONFLOW_API_KEY) apiStatus.value.siliconflow = 'configured'
          if (data.JUHE_API_KEY) apiStatus.value.juhe = 'configured'
        } else {
          console.error('后端响应错误:', response.status)
        }
      } catch (error) {
        console.error('App加载配置失败:', error)
        // 尝试测试连接
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

    // 提供给子组件
    provide('configMode', configMode)
    provide('showModelManager', showModelManager)
    provide('showApiConfig', showApiConfig)
    provide('showStylePanel', showStylePanel)
    provide('apiStatus', apiStatus)

    return {
      configMode,
      showModelManager,
      showApiConfig,
      showStylePanel,
      apiStatus,
      particlesEnabled,
      particleCount,
      particleSpeed,
      particleColor,
      toggleConfigMode,
      toggleStylePanel,
      getStatusClass,
      getProviderName,
      getProviderShort
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
.container { max-width: 1280px; margin: 0 auto; }
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

/* API状态指示器 */
.api-status-bar {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  padding: 0 1rem;
  border-left: 1px solid #334155;
  border-right: 1px solid #334155;
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

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: #64748b;
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
</style>
