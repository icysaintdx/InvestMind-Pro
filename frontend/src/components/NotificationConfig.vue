<template>
  <div v-if="visible" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <!-- 头部 -->
      <div class="modal-header">
        <h2 class="modal-title">🔔 通知服务配置</h2>
        <button @click="close" class="close-btn">&times;</button>
      </div>

      <!-- 状态指示器 -->
      <div class="status-section-fixed">
        <h3 class="section-title">通知渠道状态</h3>
        <div class="status-grid">
          <div v-for="(channel, key) in channelStatus" :key="key" class="status-item">
            <span class="status-dot" :class="channel.configured ? 'configured' : 'unconfigured'"></span>
            <span class="channel-icon">{{ channel.icon }}</span>
            <span class="channel-name">{{ channel.name }}</span>
            <span class="status-text">{{ channel.configured ? '已配置' : '未配置' }}</span>
          </div>
        </div>
      </div>

      <!-- 可滚动内容 -->
      <div class="modal-body">
        <!-- 邮件配置 -->
        <div class="config-section">
          <div class="section-header">
            <h3 class="section-title">📧 邮件通知</h3>
            <button class="test-btn" @click="testChannel('email')" :disabled="testing.email">
              {{ testing.email ? '测试中...' : '发送测试' }}
            </button>
          </div>
          <div class="config-grid">
            <div class="config-item">
              <label>SMTP服务器</label>
              <input v-model="config.SMTP_HOST" placeholder="smtp.qq.com" />
            </div>
            <div class="config-item">
              <label>SMTP端口</label>
              <input v-model.number="config.SMTP_PORT" type="number" placeholder="465" />
            </div>
            <div class="config-item">
              <label>用户名(邮箱)</label>
              <input v-model="config.SMTP_USER" placeholder="your@qq.com" />
            </div>
            <div class="config-item">
              <label>密码/授权码</label>
              <input v-model="config.SMTP_PASSWORD" type="password" placeholder="授权码" />
            </div>
            <div class="config-item">
              <label>发件人地址</label>
              <input v-model="config.SMTP_FROM" placeholder="可选，默认使用用户名" />
            </div>
            <div class="config-item checkbox-item">
              <label>
                <input type="checkbox" v-model="config.SMTP_USE_SSL" />
                使用SSL加密
              </label>
            </div>
          </div>
          <div class="config-item full-width">
            <label>测试收件人</label>
            <input v-model="testEmail" placeholder="输入测试邮箱地址" />
          </div>
        </div>

        <!-- 企业微信配置 -->
        <div class="config-section">
          <div class="section-header">
            <h3 class="section-title">💬 企业微信机器人</h3>
            <button class="test-btn" @click="testChannel('wechat')" :disabled="testing.wechat">
              {{ testing.wechat ? '测试中...' : '发送测试' }}
            </button>
          </div>
          <div class="config-grid">
            <div class="config-item full-width">
              <label>Webhook地址</label>
              <input v-model="config.WECHAT_WEBHOOK_URL" placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx" />
            </div>
          </div>
          <p class="config-tip">在企业微信群中添加机器人获取Webhook地址</p>
        </div>

        <!-- 钉钉配置 -->
        <div class="config-section">
          <div class="section-header">
            <h3 class="section-title">🔔 钉钉机器人</h3>
            <button class="test-btn" @click="testChannel('dingtalk')" :disabled="testing.dingtalk">
              {{ testing.dingtalk ? '测试中...' : '发送测试' }}
            </button>
          </div>
          <div class="config-grid">
            <div class="config-item full-width">
              <label>Webhook地址</label>
              <input v-model="config.DINGTALK_WEBHOOK_URL" placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx" />
            </div>
            <div class="config-item full-width">
              <label>签名密钥(可选)</label>
              <input v-model="config.DINGTALK_SECRET" type="password" placeholder="SECxxx" />
            </div>
          </div>
          <p class="config-tip">建议开启签名验证提高安全性</p>
        </div>

        <!-- Server酱配置 -->
        <div class="config-section">
          <div class="section-header">
            <h3 class="section-title">📱 Server酱</h3>
            <button class="test-btn" @click="testChannel('serverchan')" :disabled="testing.serverchan">
              {{ testing.serverchan ? '测试中...' : '发送测试' }}
            </button>
          </div>
          <div class="config-grid">
            <div class="config-item full-width">
              <label>SendKey</label>
              <input v-model="config.SERVERCHAN_KEY" type="password" placeholder="SCTxxx" />
            </div>
          </div>
          <p class="config-tip">访问 <a href="https://sct.ftqq.com" target="_blank">sct.ftqq.com</a> 注册获取</p>
        </div>

        <!-- Bark配置 -->
        <div class="config-section">
          <div class="section-header">
            <h3 class="section-title">🍎 Bark (iOS)</h3>
            <button class="test-btn" @click="testChannel('bark')" :disabled="testing.bark">
              {{ testing.bark ? '测试中...' : '发送测试' }}
            </button>
          </div>
          <div class="config-grid">
            <div class="config-item">
              <label>推送Key</label>
              <input v-model="config.BARK_KEY" type="password" placeholder="your_bark_key" />
            </div>
            <div class="config-item">
              <label>服务器地址(可选)</label>
              <input v-model="config.BARK_SERVER" placeholder="https://api.day.app" />
            </div>
          </div>
          <p class="config-tip">在App Store下载Bark应用获取推送Key</p>
        </div>
      </div>

      <!-- 底部操作 -->
      <div class="modal-footer">
        <button class="btn-secondary" @click="close">取消</button>
        <button class="btn-primary" @click="saveConfig" :disabled="saving">
          {{ saving ? '保存中...' : '保存配置' }}
        </button>
      </div>

      <!-- Toast提示 -->
      <div v-if="toast.show" class="toast" :class="toast.type">
        {{ toast.message }}
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, onMounted, watch } from 'vue'
import API_BASE_URL from '@/config/api'

export default {
  name: 'NotificationConfig',
  props: {
    visible: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close', 'save'],
  setup(props, { emit }) {
    const config = reactive({
      SMTP_HOST: '',
      SMTP_PORT: 465,
      SMTP_USER: '',
      SMTP_PASSWORD: '',
      SMTP_FROM: '',
      SMTP_USE_SSL: true,
      WECHAT_WEBHOOK_URL: '',
      DINGTALK_WEBHOOK_URL: '',
      DINGTALK_SECRET: '',
      SERVERCHAN_KEY: '',
      BARK_KEY: '',
      BARK_SERVER: ''
    })

    const channelStatus = reactive({
      email: { name: '邮件', icon: '📧', configured: false },
      wechat: { name: '企业微信', icon: '💬', configured: false },
      dingtalk: { name: '钉钉', icon: '🔔', configured: false },
      serverchan: { name: 'Server酱', icon: '📱', configured: false },
      bark: { name: 'Bark', icon: '🍎', configured: false }
    })

    const testing = reactive({
      email: false,
      wechat: false,
      dingtalk: false,
      serverchan: false,
      bark: false
    })

    const saving = ref(false)
    const testEmail = ref('')
    const toast = reactive({
      show: false,
      type: 'success',
      message: ''
    })

    const showToast = (type, message) => {
      toast.type = type
      toast.message = message
      toast.show = true
      setTimeout(() => {
        toast.show = false
      }, 3000)
    }

    const loadConfig = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/notification/config`)
        const result = await response.json()
        if (result.success && result.config) {
          Object.keys(result.config).forEach(key => {
            if (Object.prototype.hasOwnProperty.call(config, key)) {
              config[key] = result.config[key]
            }
          })
        }
        await loadChannelStatus()
      } catch (error) {
        console.error('加载通知配置失败:', error)
      }
    }

    const loadChannelStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/notification/channels`)
        const result = await response.json()
        if (result.success && result.channels) {
          Object.keys(result.channels).forEach(key => {
            if (channelStatus[key]) {
              channelStatus[key].configured = result.channels[key].configured
            }
          })
        }
      } catch (error) {
        console.error('加载渠道状态失败:', error)
      }
    }

    const saveConfig = async () => {
      saving.value = true
      try {
        const response = await fetch(`${API_BASE_URL}/api/notification/config`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(config)
        })
        const result = await response.json()
        if (result.success) {
          showToast('success', '配置保存成功')
          await loadChannelStatus()
          emit('save', config)
        } else {
          showToast('error', result.message || '保存失败')
        }
      } catch (error) {
        showToast('error', '保存配置失败: ' + error.message)
      } finally {
        saving.value = false
      }
    }

    const testChannel = async (channel) => {
      testing[channel] = true
      try {
        let url = `${API_BASE_URL}/api/notification/test/${channel}`
        let options = { method: 'POST', headers: { 'Content-Type': 'application/json' } }

        if (channel === 'email') {
          if (!testEmail.value) {
            showToast('error', '请输入测试邮箱地址')
            return
          }
          options.body = JSON.stringify({ to_email: testEmail.value })
        }

        const response = await fetch(url, options)
        const result = await response.json()

        if (result.success) {
          showToast('success', `${channelStatus[channel].name}测试成功`)
        } else {
          showToast('error', result.detail || result.message || '测试失败')
        }
      } catch (error) {
        showToast('error', '测试失败: ' + error.message)
      } finally {
        testing[channel] = false
      }
    }

    const close = () => {
      emit('close')
    }

    watch(() => props.visible, (newVal) => {
      if (newVal) {
        loadConfig()
      }
    })

    onMounted(() => {
      if (props.visible) {
        loadConfig()
      }
    })

    return {
      config,
      channelStatus,
      testing,
      saving,
      testEmail,
      toast,
      saveConfig,
      testChannel,
      close
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

.modal-container {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 20px;
  width: 100%;
  max-width: 700px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  border: 1px solid rgba(255, 255, 255, 0.1);
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.modal-title {
  font-size: 1.5rem;
  font-weight: 700;
  color: #f1f5f9;
  margin: 0;
}

.close-btn {
  background: none;
  border: none;
  color: #94a3b8;
  font-size: 2rem;
  cursor: pointer;
  line-height: 1;
  padding: 0;
  transition: color 0.2s;
}

.close-btn:hover {
  color: #ef4444;
}

.status-section-fixed {
  padding: 1rem 1.5rem;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.section-title {
  font-size: 1rem;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0 0 0.75rem 0;
}

.status-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  font-size: 0.85rem;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.status-dot.configured {
  background: #10b981;
  box-shadow: 0 0 6px rgba(16, 185, 129, 0.5);
}

.status-dot.unconfigured {
  background: #64748b;
}

.channel-icon {
  font-size: 1rem;
}

.channel-name {
  color: #e2e8f0;
  font-weight: 500;
}

.status-text {
  color: #94a3b8;
  font-size: 0.75rem;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.config-section {
  background: rgba(30, 41, 59, 0.3);
  border-radius: 12px;
  padding: 1.25rem;
  margin-bottom: 1rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-header .section-title {
  margin: 0;
}

.config-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.config-item.full-width {
  grid-column: span 2;
}

.config-item.checkbox-item {
  flex-direction: row;
  align-items: center;
}

.config-item.checkbox-item label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
}

.config-item label {
  font-size: 0.85rem;
  color: #94a3b8;
  font-weight: 500;
}

.config-item input[type="text"],
.config-item input[type="password"],
.config-item input[type="number"] {
  padding: 0.75rem 1rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 0.9rem;
  transition: border-color 0.2s;
}

.config-item input:focus {
  outline: none;
  border-color: #3b82f6;
}

.config-item input::placeholder {
  color: #64748b;
}

.config-tip {
  margin: 0.75rem 0 0 0;
  font-size: 0.8rem;
  color: #64748b;
}

.config-tip a {
  color: #3b82f6;
  text-decoration: none;
}

.config-tip a:hover {
  text-decoration: underline;
}

.test-btn {
  padding: 0.5rem 1rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  color: #60a5fa;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.test-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.3);
}

.test-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.btn-primary,
.btn-secondary {
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  border: none;
}

.btn-primary {
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: rgba(148, 163, 184, 0.15);
  color: #e2e8f0;
}

.btn-secondary:hover {
  background: rgba(148, 163, 184, 0.25);
}

.toast {
  position: absolute;
  bottom: 6rem;
  left: 50%;
  transform: translateX(-50%);
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
  font-size: 0.9rem;
  font-weight: 500;
  animation: slideUp 0.3s ease;
}

.toast.success {
  background: rgba(16, 185, 129, 0.9);
  color: #fff;
}

.toast.error {
  background: rgba(239, 68, 68, 0.9);
  color: #fff;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateX(-50%) translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateX(-50%) translateY(0);
  }
}

/* 滚动条美化 */
.modal-body::-webkit-scrollbar {
  width: 6px;
}

.modal-body::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: rgba(148, 163, 184, 0.3);
  border-radius: 3px;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: rgba(148, 163, 184, 0.5);
}

@media (max-width: 640px) {
  .modal-overlay {
    padding: 1rem;
  }

  .config-grid {
    grid-template-columns: 1fr;
  }

  .config-item.full-width {
    grid-column: span 1;
  }

  .status-grid {
    flex-direction: column;
  }
}
</style>
