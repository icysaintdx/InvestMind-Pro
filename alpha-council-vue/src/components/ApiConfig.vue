<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <!-- 头部 -->
      <div class="modal-header">
        <h2 class="modal-title">🔑 API 配置</h2>
        <button @click="close" class="close-btn">×</button>
      </div>
      
      <!-- 内容 -->
      <div class="modal-body">
        <!-- 状态指示器 -->
        <div class="status-section">
          <h3 class="section-title">连接状态</h3>
          <div class="status-grid">
            <div v-for="(status, key) in apiStatus" :key="key" class="status-item">
              <span class="status-dot" :class="getStatusClass(status)"></span>
              <span class="provider-name">{{ getProviderLabel(key) }}</span>
              <span class="status-text">{{ getStatusText(status) }}</span>
            </div>
          </div>
        </div>

        <!-- API密钥输入 -->
        <div class="keys-section">
          <h3 class="section-title">API密钥配置</h3>
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
                <span class="provider-icon">📊</span>
                聚合数据 API Key
              </label>
              <input 
                type="password" 
                v-model="localKeys.juhe" 
                placeholder="获取实时行情"
                class="key-input"
              >
              <button @click="testApi('juhe')" class="test-btn">测试</button>
            </div>
          </div>
        </div>

        <!-- 底部按钮 -->
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
  </div>
</template>

<script>
import { ref, watch } from 'vue'

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
    
    // 监听props变化
    watch(() => props.apiKeys, (newVal) => {
      localKeys.value = { ...newVal }
    }, { deep: true })

    const getProviderLabel = (key) => {
      const labels = {
        gemini: 'Gemini',
        deepseek: 'DeepSeek',
        qwen: '通义千问',
        siliconflow: '硅基流动',
        juhe: '聚合数据'
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
      emit('updateStatus', provider, 'testing')
      
      try {
        // 模拟API测试
        await new Promise(resolve => setTimeout(resolve, 1000))
        
        if (localKeys.value[provider]) {
          emit('updateStatus', provider, 'configured')
        } else {
          emit('updateStatus', provider, 'unconfigured')
        }
      } catch (error) {
        emit('updateStatus', provider, 'error')
      }
    }

    const saveConfig = () => {
      emit('save', localKeys.value)
      emit('close')
    }

    const loadFromEnv = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/config')
        if (response.ok) {
          const data = await response.json()
          if (data.api_keys) {
            localKeys.value = { ...data.api_keys }
          }
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
  padding: 1.5rem;
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
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
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
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 1rem;
}

/* 状态部分 */
.status-section {
  background: #0f172a;
  border-radius: 0.75rem;
  padding: 1.25rem;
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

/* 底部 */
.modal-footer {
  display: flex;
  gap: 1rem;
  padding-top: 1.5rem;
  border-top: 1px solid #334155;
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
</style>
