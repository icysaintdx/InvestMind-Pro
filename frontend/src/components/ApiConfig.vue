<template>
  <div v-if="visible" class="modal-overlay" @click.self="close" @wheel.prevent>
    <div class="modal-container">
      <!-- 头部 -->
      <div class="modal-header">
        <h2 class="modal-title">🔑 API 配置</h2>
        <button @click="close" class="close-btn">×</button>
      </div>
      
      <!-- 状态指示器（固定不滚动） -->
      <div class="status-section-fixed">
        <h3 class="section-title">连接状态</h3>
        <div class="status-grid">
          <div v-for="(status, key) in apiStatus" :key="key" class="status-item">
            <span class="status-dot" :class="getStatusClass(status)"></span>
            <span class="provider-name">{{ getProviderLabel(key) }}</span>
            <span class="status-text">{{ getStatusText(status) }}</span>
          </div>
        </div>
      </div>
      
      <!-- 可滚动内容 -->
      <div class="modal-body">

        <!-- AI 模型 API配置 -->
        <div class="keys-section">
          <h3 class="section-title">AI 模型 API配置</h3>
          <div class="keys-grid">
            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">🌟</span>
                Gemini API Key
              </label>
              <input 
                type="password" 
                v-model="localKeys.gemini" 
                placeholder="用于宏观/行业分析"
                class="key-input"
              >
              <button @click="testApi('gemini')" class="test-btn">测试</button>
            </div>

            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">🧠</span>
                DeepSeek API Key
              </label>
              <input 
                type="password" 
                v-model="localKeys.deepseek" 
                placeholder="用于深度分析"
                class="key-input"
              >
              <button @click="testApi('deepseek')" class="test-btn">测试</button>
            </div>

            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">🎯</span>
                通义千问 API Key
              </label>
              <input 
                type="password" 
                v-model="localKeys.qwen" 
                placeholder="用于专业分析"
                class="key-input"
              >
              <button @click="testApi('qwen')" class="test-btn">测试</button>
            </div>

            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">💎</span>
                硅基流动 API Key
              </label>
              <input 
                type="password" 
                v-model="localKeys.siliconflow" 
                placeholder="支持50+模型"
                class="key-input"
              >
              <button @click="testApi('siliconflow')" class="test-btn">测试</button>
            </div>

            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">🚀</span>
                Minimax API Key (kirocpa中转)
              </label>
              <input 
                type="password" 
                v-model="localKeys.minimax" 
                placeholder="MiniMax M2/M2.1 中转 (kirocpa.zeabur.app)"
                class="key-input"
              >
              <button @click="testApi('minimax')" class="test-btn">测试</button>
            </div>
          </div>
        </div>

        <!-- 数据渠道配置 -->
        <div class="keys-section">
          <div class="flex items-center justify-between mb-3">
            <h3 class="section-title mb-0">数据渠道配置</h3>
            <span class="text-xs text-slate-500">ℹ️ 用于获取实时行情、新闻、财报等数据</span>
          </div>
          <div class="keys-grid">
            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">📊</span>
                聚合数据 API Key
              </label>
              <input 
                type="password" 
                v-model="localKeys.juhe" 
                placeholder="A股实时行情数据"
                class="key-input"
              >
              <button @click="testApi('juhe')" class="test-btn">测试</button>
            </div>

            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">🌎</span>
                FinnHub API Key
                <span class="config-badge">已配置</span>
              </label>
              <input 
                type="password" 
                v-model="localKeys.finnhub" 
                placeholder="国际金融数据（免费版每月60次请求）"
                class="key-input"
              >
              <button @click="testApi('finnhub')" class="test-btn">测试</button>
            </div>

            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">📊</span>
                Tushare Token
                <span class="config-badge">已配置</span>
              </label>
              <input 
                type="password" 
                v-model="localKeys.tushare" 
                placeholder="A股专业数据（需注册积分解锁）"
                class="key-input"
              >
              <button @click="testApi('tushare')" class="test-btn">测试</button>
            </div>

            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">💹</span>
                AKShare
                <span class="config-badge success">免费</span>
              </label>
              <input
                type="text"
                value="开源金融数据库（无需配置，直接可用）"
                class="key-input"
                disabled
              >
              <button @click="testApi('akshare')" class="test-btn">测试</button>
            </div>

            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">📰</span>
                巨潮资讯 Access Key
              </label>
              <input
                type="password"
                v-model="localKeys.cninfo_access_key"
                placeholder="巨潮资讯API Access Key"
                class="key-input"
              >
              <button @click="testApi('cninfo')" class="test-btn">测试</button>
            </div>

            <div class="key-item">
              <label class="key-label">
                <span class="provider-icon">🔐</span>
                巨潮资讯 Secret Key
              </label>
              <input
                type="password"
                v-model="localKeys.cninfo_secret_key"
                placeholder="巨潮资讯API Secret Key"
                class="key-input"
              >
            </div>
          </div>
        </div>
      </div>
      
      <!-- 底部按钮（固定不滚动） -->
      <div class="modal-footer">
        <button @click="saveConfig" class="save-btn primary">
          💾 保存配置
        </button>
        <button @click="loadFromEnv" class="save-btn secondary">
          📥 从环境变量加载
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import API_BASE_URL from '@/config/api.js'

export default {
  name: 'ApiConfig',
  props: {
    visible: {
      type: Boolean,
      default: false
    },
    apiKeys: {
      type: Object,
      default: () => ({})
    },
    apiStatus: {
      type: Object,
      default: () => ({})
    }
  },
  emits: ['close', 'save', 'updateStatus'],
  setup(props, { emit }) {
    const localKeys = ref({ ...props.apiKeys })
    
    // 监听prop变化
    watch(() => props.apiKeys, (newVal) => {
      localKeys.value = { ...newVal }
    }, { deep: true })

    // 监听 visible 变化，当模态框打开时自动加载配置
    watch(() => props.visible, (newVal) => {
      if (newVal) {
        loadFromEnv()
        // 禁用主页面滚动
        document.body.style.overflow = 'hidden'
      } else {
        // 恢复主页面滚动
        document.body.style.overflow = ''
      }
    })

    const getProviderLabel = (key) => {
      const labels = {
        gemini: 'Gemini',
        deepseek: 'DeepSeek',
        qwen: '通义千问',
        siliconflow: '硅基流动',
        juhe: '聚合数据',
        finnhub: 'FinnHub',
        tushare: 'Tushare',
        akshare: 'AKShare'
      }
      return labels[key] || key
    }

    const getStatusClass = (status) => {
      return {
        configured: 'status-success',
        unconfigured: 'status-default',
        error: 'status-error',
        testing: 'status-testing'
      }[status] || 'status-default'
    }

    const getStatusText = (status) => {
      return {
        configured: '已配置',
        unconfigured: '未配置',
        error: '连接失败',
        testing: '测试中...'
      }[status] || '未知'
    }

    const testApi = async (provider) => {
      // AKShare 不需要 API Key
      if (provider !== 'akshare' && !localKeys.value[provider]) {
        window.$toast && window.$toast.warning(`请先输入 ${getProviderLabel(provider)} 的 API Key`)
        return
      }

      emit('updateStatus', provider, 'testing')
      
      try {
        // 调用后端测试接口
        const response = await fetch(`${API_BASE_URL}/api/test/${provider}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_key: localKeys.value[provider] })
        })
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
        
        const result = await response.json()
        
        if (result.success) {
          emit('updateStatus', provider, 'configured')
          // 显示详细的测试结果
          let message = `✅ ${result.message}\n`
          if (result.test_response) {
            message += `\n响应示例:\n${result.test_response}`
          }
          window.$toast && window.$toast.success(message)
        } else {
          emit('updateStatus', provider, 'error')
          window.$toast && window.$toast.error(`${getProviderLabel(provider)} 测试失败: ${result.error || '未知错误'}`)
        }
      } catch (error) {
        emit('updateStatus', provider, 'error')
        console.error(`Test ${provider} error:`, error)
        window.$toast && window.$toast.error(`${getProviderLabel(provider)} 测试失败: ${error.message}`, 5000)
      }
    }

    const saveConfig = () => {
      emit('save', localKeys.value)
      emit('close')
    }

    const loadFromEnv = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/config`)
        if (response.ok) {
          const data = await response.json()
          console.log('ApiConfig 加载配置:', data)
          
          // 合并 api_keys
          if (data.api_keys) {
            localKeys.value = { ...localKeys.value, ...data.api_keys }
          }
          
          // 检查环境变量格式的配置
          if (data.FINNHUB_API_KEY) {
            localKeys.value.finnhub = data.FINNHUB_API_KEY
          }
          if (data.TUSHARE_TOKEN) {
            localKeys.value.tushare = data.TUSHARE_TOKEN
          }
          if (data.JUHE_API_KEY) {
            localKeys.value.juhe = data.JUHE_API_KEY
          }
          
          console.log('ApiConfig 加载后的 keys:', localKeys.value)
        }
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    }

    const close = () => {
      emit('close')
    }

    return {
      localKeys,
      getProviderLabel,
      getStatusClass,
      getStatusText,
      testApi,
      saveConfig,
      loadFromEnv,
      close
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  backdrop-filter: blur(8px);
  z-index: 50;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}

.modal-container {
  background: #1e293b;
  border-radius: 1rem;
  max-width: 56rem;
  width: 100%;
  max-height: 85vh;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  border: 1px solid #475569;
  box-shadow: 0 20px 40px rgba(0, 0, 0, 0.4);
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem 1.5rem 1rem;
  border-bottom: 1px solid #334155;
}

.modal-title {
  font-size: 1.5rem;
  font-weight: bold;
  color: white;
}

.close-btn {
  color: #94a3b8;
  font-size: 2rem;
  background: none;
  border: none;
  cursor: pointer;
  transition: color 0.2s;
}

.close-btn:hover {
  color: white;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 2rem;
  padding: 0 1.5rem;
}

.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: #1e293b;
}

.modal-body::-webkit-scrollbar-thumb {
  background: #475569;
  border-radius: 4px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: #64748b;
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 1rem;
}

/* 固定状态区域 */
.status-section-fixed {
  background: #0f172a;
  border-radius: 0.75rem;
  padding: 1.25rem;
  margin: 0 1.5rem 1rem;
  flex-shrink: 0;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem;
  background: #1e293b;
  border-radius: 0.5rem;
  border: 1px solid #334155;
}

.status-dot {
  width: 0.75rem;
  height: 0.75rem;
  border-radius: 50%;
  flex-shrink: 0;
}

.status-dot.status-default {
  background: #64748b;
}

.status-dot.status-success {
  background: #10b981;
  box-shadow: 0 0 8px rgba(16, 185, 129, 0.5);
}

.status-dot.status-error {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.5);
}

.status-dot.status-testing {
  background: #fbbf24;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.provider-name {
  font-weight: 500;
  color: #e2e8f0;
  font-size: 0.875rem;
}

.status-text {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-left: auto;
}

/* 密钥部分 */
.keys-section {
  background: #0f172a;
  border-radius: 0.75rem;
  padding: 1.25rem;
}

.keys-grid {
  display: flex;
  flex-direction: column;
  gap: 1.25rem;
}

.key-item {
  display: grid;
  grid-template-columns: 180px 1fr auto;
  align-items: center;
  gap: 1rem;
}

.key-label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #e2e8f0;
  font-size: 0.875rem;
  font-weight: 500;
}

.provider-icon {
  font-size: 1.125rem;
}

.key-input {
  padding: 0.625rem 0.875rem;
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 0.5rem;
  color: white;
  font-size: 0.875rem;
  font-family: monospace;
}

.key-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.test-btn {
  padding: 0.625rem 1rem;
  background: #334155;
  color: #e2e8f0;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.test-btn:hover {
  background: #475569;
}

/* 配置徽章 */
.config-badge {
  display: inline-block;
  padding: 0.125rem 0.5rem;
  background: #334155;
  color: #94a3b8;
  font-size: 0.625rem;
  border-radius: 0.25rem;
  margin-left: 0.5rem;
  font-weight: 500;
}

.config-badge.success {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

/* 底部 */
.modal-footer {
  display: flex;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #334155;
  flex-shrink: 0;
}

.save-btn {
  padding: 0.75rem 1.5rem;
  border: none;
  border-radius: 0.5rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.save-btn.primary {
  background: #3b82f6;
  color: white;
}

.save-btn.primary:hover {
  background: #2563eb;
}

.save-btn.secondary {
  background: #334155;
  color: #e2e8f0;
}

.save-btn.secondary:hover {
  background: #475569;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .modal-container {
    width: 100vw;
    height: 100vh;
    max-height: 100vh;
    border-radius: 0;
    margin: 0;
  }
  
  .modal-body {
    max-height: calc(100vh - 200px);
    overflow-y: auto;
    -webkit-overflow-scrolling: touch;
    padding: 0 1rem;
  }
  
  .status-section-fixed {
    padding: 1rem;
  }
  
  .status-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }
  
  .keys-grid {
    gap: 1rem;
  }
  
  .key-item {
    flex-direction: column;
    align-items: stretch;
    gap: 0.5rem;
  }
  
  .key-label {
    font-size: 0.9rem;
  }
  
  .key-input {
    width: 100%;
  }
  
  .test-btn {
    width: 100%;
    margin-top: 0.5rem;
  }
  
  .section-title {
    font-size: 1rem;
  }
  
  .modal-footer {
    padding: 1rem;
    gap: 0.5rem;
  }
  
  .save-btn {
    flex: 1;
    padding: 0.75rem;
  }
}

@media (max-width: 480px) {
  .modal-body {
    padding: 0 0.75rem;
  }
  
  .status-section-fixed {
    padding: 0.75rem;
  }
  
  .section-title {
    font-size: 0.95rem;
  }
  
  .provider-name {
    font-size: 0.85rem;
  }
  
  .status-text {
    font-size: 0.75rem;
  }
}
</style>
