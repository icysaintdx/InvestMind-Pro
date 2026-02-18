<template>
  <div class="alert-notification-system">
    <!-- 整屏边框闪动效果 -->
    <div
      v-if="borderFlash.active"
      :class="['screen-border-flash', borderFlash.type]"
      :style="{ animationDuration: borderFlash.duration + 'ms' }"
    ></div>

    <!-- 吐司通知容器 -->
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast-item', toast.type]"
          @click="dismissToast(toast.id)"
        >
          <div class="toast-icon">
            <span v-if="toast.type === 'critical'">🚨</span>
            <span v-else-if="toast.type === 'high' || toast.type === 'warning'">⚠️</span>
            <span v-else-if="toast.type === 'success' || toast.type === 'positive'">✅</span>
            <span v-else-if="toast.type === 'info'">ℹ️</span>
            <span v-else>📢</span>
          </div>
          <div class="toast-content">
            <div class="toast-title">{{ toast.title }}</div>
            <div v-if="toast.message" class="toast-message">{{ toast.message }}</div>
          </div>
          <button class="toast-close" @click.stop="dismissToast(toast.id)">×</button>
          <div class="toast-progress" :style="{ animationDuration: toast.duration + 'ms' }"></div>
        </div>
      </TransitionGroup>
    </div>

    <!-- 弹窗通知 -->
    <Transition name="modal">
      <div v-if="modal.visible" class="alert-modal-overlay" @click.self="closeModal">
        <div :class="['alert-modal', modal.type]">
          <div class="modal-header">
            <div class="modal-icon">
              <span v-if="modal.type === 'critical'">🚨</span>
              <span v-else-if="modal.type === 'high' || modal.type === 'warning'">⚠️</span>
              <span v-else-if="modal.type === 'success' || modal.type === 'positive'">🎉</span>
              <span v-else>📢</span>
            </div>
            <h3 class="modal-title">{{ modal.title }}</h3>
            <button class="modal-close" @click="closeModal">×</button>
          </div>
          <div class="modal-body">
            <p class="modal-message">{{ modal.message }}</p>
            <div v-if="modal.details" class="modal-details">
              <div v-for="(value, key) in modal.details" :key="key" class="detail-item">
                <span class="detail-label">{{ key }}:</span>
                <span class="detail-value">{{ value }}</span>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button v-if="modal.showViewButton" class="modal-btn view-btn" @click="handleViewDetail">
              查看详情
            </button>
            <button class="modal-btn confirm-btn" @click="closeModal">
              我知道了
            </button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, onMounted, onUnmounted } from 'vue'

export default defineComponent({
  name: 'AlertNotification',
  emits: ['view-detail'],
  setup(props, { emit }) {
    // 吐司通知列表
    const toasts = ref([])
    let toastIdCounter = 0

    // 弹窗状态
    const modal = reactive({
      visible: false,
      type: 'info',
      title: '',
      message: '',
      details: null,
      showViewButton: false,
      alertData: null
    })

    // 边框闪动状态
    const borderFlash = reactive({
      active: false,
      type: 'warning',
      duration: 3000
    })

    // 显示吐司通知
    const showToast = (options) => {
      const toast = {
        id: ++toastIdCounter,
        type: options.type || 'info',
        title: options.title || '通知',
        message: options.message || '',
        duration: options.duration || 5000
      }

      toasts.value.push(toast)

      // 自动移除
      setTimeout(() => {
        dismissToast(toast.id)
      }, toast.duration)

      // 播放声音（如果启用）
      if (options.sound !== false) {
        playAlertSound(toast.type)
      }
    }

    // 关闭吐司
    const dismissToast = (id) => {
      const index = toasts.value.findIndex(t => t.id === id)
      if (index > -1) {
        toasts.value.splice(index, 1)
      }
    }

    // 显示弹窗
    const showModal = (options) => {
      modal.visible = true
      modal.type = options.type || 'info'
      modal.title = options.title || '预警通知'
      modal.message = options.message || ''
      modal.details = options.details || null
      modal.showViewButton = options.showViewButton || false
      modal.alertData = options.alertData || null

      // 播放声音
      if (options.sound !== false) {
        playAlertSound(modal.type)
      }
    }

    // 关闭弹窗
    const closeModal = () => {
      modal.visible = false
    }

    // 查看详情
    const handleViewDetail = () => {
      emit('view-detail', modal.alertData)
      closeModal()
    }

    // 触发边框闪动
    const triggerBorderFlash = (type = 'warning', duration = 3000) => {
      borderFlash.active = false
      // 强制重新触发动画
      setTimeout(() => {
        borderFlash.type = type
        borderFlash.duration = duration
        borderFlash.active = true

        setTimeout(() => {
          borderFlash.active = false
        }, duration)
      }, 10)
    }

    // 播放预警声音
    const playAlertSound = (type) => {
      try {
        // 使用 Web Audio API 生成简单的提示音
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()
        const oscillator = audioContext.createOscillator()
        const gainNode = audioContext.createGain()

        oscillator.connect(gainNode)
        gainNode.connect(audioContext.destination)

        // 根据类型设置不同的音调
        if (type === 'critical') {
          oscillator.frequency.value = 880 // 高音
          oscillator.type = 'square'
          gainNode.gain.value = 0.3
        } else if (type === 'high' || type === 'warning') {
          oscillator.frequency.value = 660
          oscillator.type = 'triangle'
          gainNode.gain.value = 0.2
        } else if (type === 'success' || type === 'positive') {
          oscillator.frequency.value = 523.25 // C5
          oscillator.type = 'sine'
          gainNode.gain.value = 0.15
        } else {
          oscillator.frequency.value = 440
          oscillator.type = 'sine'
          gainNode.gain.value = 0.1
        }

        oscillator.start()
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3)
        oscillator.stop(audioContext.currentTime + 0.3)
      } catch (e) {
        // 忽略音频播放错误
        console.warn('无法播放提示音:', e)
      }
    }

    // 处理预警事件
    const handleAlert = (alert) => {
      const level = alert.alert_level || alert.level || 'medium'
      const isPositive = alert.is_positive || alert.type === 'positive'

      // 根据预警级别决定通知方式
      if (level === 'critical') {
        // 紧急预警：弹窗 + 边框闪动 + 吐司
        triggerBorderFlash('critical', 5000)
        showModal({
          type: 'critical',
          title: '🚨 紧急预警',
          message: alert.title || alert.message,
          details: {
            '股票': alert.stock_name || alert.ts_code,
            '时间': formatTime(alert.alert_time || alert.time),
            '详情': alert.message || alert.description
          },
          showViewButton: true,
          alertData: alert
        })
        showToast({
          type: 'critical',
          title: '紧急预警',
          message: alert.title,
          duration: 8000
        })
      } else if (level === 'high') {
        // 高级预警：边框闪动 + 吐司
        triggerBorderFlash('high', 3000)
        showToast({
          type: 'high',
          title: '⚠️ 高级预警',
          message: `${alert.stock_name || alert.ts_code}: ${alert.title}`,
          duration: 6000
        })
      } else if (isPositive || level === 'positive') {
        // 利好消息：绿色边框闪动 + 吐司
        triggerBorderFlash('positive', 2000)
        showToast({
          type: 'positive',
          title: '✅ 利好消息',
          message: `${alert.stock_name || alert.ts_code}: ${alert.title}`,
          duration: 5000
        })
      } else {
        // 普通预警：仅吐司
        showToast({
          type: 'info',
          title: '📢 新预警',
          message: `${alert.stock_name || alert.ts_code}: ${alert.title}`,
          duration: 4000
        })
      }
    }

    // 格式化时间
    const formatTime = (timestamp) => {
      if (!timestamp) return ''
      const date = new Date(timestamp)
      return date.toLocaleString('zh-CN', {
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      })
    }

    // 监听全局预警事件
    const handleGlobalAlert = (event) => {
      handleAlert(event.detail)
    }

    onMounted(() => {
      window.addEventListener('stock-alert', handleGlobalAlert)
    })

    onUnmounted(() => {
      window.removeEventListener('stock-alert', handleGlobalAlert)
    })

    // 暴露方法供外部调用
    return {
      toasts,
      modal,
      borderFlash,
      showToast,
      dismissToast,
      showModal,
      closeModal,
      handleViewDetail,
      triggerBorderFlash,
      handleAlert
    }
  }
})
</script>

<style scoped>
/* 整屏边框闪动效果 */
.screen-border-flash {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9999;
  animation: borderFlash ease-out forwards;
}

.screen-border-flash.critical {
  box-shadow: inset 0 0 100px rgba(239, 68, 68, 0.8),
              inset 0 0 200px rgba(239, 68, 68, 0.4),
              inset 0 0 300px rgba(239, 68, 68, 0.2);
  animation-name: borderFlashCritical;
}

.screen-border-flash.high,
.screen-border-flash.warning {
  box-shadow: inset 0 0 80px rgba(245, 158, 11, 0.7),
              inset 0 0 160px rgba(245, 158, 11, 0.3),
              inset 0 0 240px rgba(245, 158, 11, 0.15);
  animation-name: borderFlashWarning;
}

.screen-border-flash.positive,
.screen-border-flash.success {
  box-shadow: inset 0 0 80px rgba(16, 185, 129, 0.7),
              inset 0 0 160px rgba(16, 185, 129, 0.3),
              inset 0 0 240px rgba(16, 185, 129, 0.15);
  animation-name: borderFlashPositive;
}

.screen-border-flash.info {
  box-shadow: inset 0 0 60px rgba(59, 130, 246, 0.6),
              inset 0 0 120px rgba(59, 130, 246, 0.3),
              inset 0 0 180px rgba(59, 130, 246, 0.1);
  animation-name: borderFlashInfo;
}

@keyframes borderFlashCritical {
  0% { opacity: 0; }
  10% { opacity: 1; }
  20% { opacity: 0.3; }
  30% { opacity: 1; }
  40% { opacity: 0.3; }
  50% { opacity: 1; }
  60% { opacity: 0.5; }
  70% { opacity: 0.8; }
  80% { opacity: 0.4; }
  90% { opacity: 0.2; }
  100% { opacity: 0; }
}

@keyframes borderFlashWarning {
  0% { opacity: 0; }
  15% { opacity: 1; }
  30% { opacity: 0.4; }
  45% { opacity: 1; }
  60% { opacity: 0.6; }
  80% { opacity: 0.3; }
  100% { opacity: 0; }
}

@keyframes borderFlashPositive {
  0% { opacity: 0; }
  20% { opacity: 1; }
  40% { opacity: 0.5; }
  60% { opacity: 0.8; }
  80% { opacity: 0.3; }
  100% { opacity: 0; }
}

@keyframes borderFlashInfo {
  0% { opacity: 0; }
  25% { opacity: 0.8; }
  50% { opacity: 0.4; }
  75% { opacity: 0.6; }
  100% { opacity: 0; }
}

/* 吐司容器 */
.toast-container {
  position: fixed;
  top: 5rem;
  right: 1rem;
  z-index: 9998;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-width: 400px;
  width: 100%;
  pointer-events: none;
}

/* 吐司项 */
.toast-item {
  position: relative;
  display: flex;
  align-items: flex-start;
  gap: 0.75rem;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.75rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  backdrop-filter: blur(12px);
  cursor: pointer;
  pointer-events: auto;
  overflow: hidden;
  transition: all 0.3s ease;
}

.toast-item:hover {
  transform: translateX(-4px);
  box-shadow: 0 15px 50px rgba(0, 0, 0, 0.5);
}

.toast-item.critical {
  border-color: rgba(239, 68, 68, 0.6);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.15), rgba(15, 23, 42, 0.95));
}

.toast-item.high,
.toast-item.warning {
  border-color: rgba(245, 158, 11, 0.6);
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.15), rgba(15, 23, 42, 0.95));
}

.toast-item.success,
.toast-item.positive {
  border-color: rgba(16, 185, 129, 0.6);
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(15, 23, 42, 0.95));
}

.toast-item.info {
  border-color: rgba(59, 130, 246, 0.6);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.15), rgba(15, 23, 42, 0.95));
}

.toast-icon {
  font-size: 1.5rem;
  flex-shrink: 0;
}

.toast-content {
  flex: 1;
  min-width: 0;
}

.toast-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: white;
  margin-bottom: 0.25rem;
}

.toast-message {
  font-size: 0.8rem;
  color: #94a3b8;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.toast-close {
  position: absolute;
  top: 0.5rem;
  right: 0.5rem;
  width: 1.5rem;
  height: 1.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #64748b;
  font-size: 1rem;
  cursor: pointer;
  border-radius: 0.25rem;
  transition: all 0.2s;
}

.toast-close:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

/* 吐司进度条 */
.toast-progress {
  position: absolute;
  bottom: 0;
  left: 0;
  height: 3px;
  background: linear-gradient(90deg, #3b82f6, #60a5fa);
  animation: toastProgress linear forwards;
}

.toast-item.critical .toast-progress {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.toast-item.high .toast-progress,
.toast-item.warning .toast-progress {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.toast-item.success .toast-progress,
.toast-item.positive .toast-progress {
  background: linear-gradient(90deg, #10b981, #34d399);
}

@keyframes toastProgress {
  from { width: 100%; }
  to { width: 0%; }
}

/* 吐司动画 */
.toast-enter-active {
  animation: toastIn 0.3s ease;
}

.toast-leave-active {
  animation: toastOut 0.3s ease;
}

@keyframes toastIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes toastOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}

/* 弹窗遮罩 */
.alert-modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(8px);
  z-index: 10000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
}

/* 弹窗 */
.alert-modal {
  width: 100%;
  max-width: 480px;
  background: rgba(15, 23, 42, 0.98);
  border: 2px solid rgba(51, 65, 85, 0.5);
  border-radius: 1rem;
  box-shadow: 0 25px 80px rgba(0, 0, 0, 0.6);
  overflow: hidden;
}

.alert-modal.critical {
  border-color: rgba(239, 68, 68, 0.6);
  box-shadow: 0 25px 80px rgba(239, 68, 68, 0.3);
}

.alert-modal.high,
.alert-modal.warning {
  border-color: rgba(245, 158, 11, 0.6);
  box-shadow: 0 25px 80px rgba(245, 158, 11, 0.2);
}

.alert-modal.success,
.alert-modal.positive {
  border-color: rgba(16, 185, 129, 0.6);
  box-shadow: 0 25px 80px rgba(16, 185, 129, 0.2);
}

.modal-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 1.25rem 1.5rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

.alert-modal.critical .modal-header {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), transparent);
}

.alert-modal.high .modal-header,
.alert-modal.warning .modal-header {
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), transparent);
}

.alert-modal.success .modal-header,
.alert-modal.positive .modal-header {
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), transparent);
}

.modal-icon {
  font-size: 2rem;
}

.modal-title {
  flex: 1;
  font-size: 1.25rem;
  font-weight: 600;
  color: white;
  margin: 0;
}

.modal-close {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 1.5rem;
  cursor: pointer;
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.modal-close:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.modal-body {
  padding: 1.5rem;
}

.modal-message {
  font-size: 1rem;
  color: #e2e8f0;
  line-height: 1.6;
  margin: 0 0 1rem 0;
}

.modal-details {
  background: rgba(30, 41, 59, 0.5);
  border-radius: 0.5rem;
  padding: 1rem;
}

.detail-item {
  display: flex;
  gap: 0.5rem;
  padding: 0.5rem 0;
  border-bottom: 1px solid rgba(51, 65, 85, 0.3);
}

.detail-item:last-child {
  border-bottom: none;
}

.detail-label {
  font-size: 0.85rem;
  color: #64748b;
  min-width: 60px;
}

.detail-value {
  font-size: 0.85rem;
  color: #e2e8f0;
  flex: 1;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 0.75rem;
  padding: 1rem 1.5rem;
  border-top: 1px solid rgba(51, 65, 85, 0.5);
  background: rgba(30, 41, 59, 0.3);
}

.modal-btn {
  padding: 0.625rem 1.25rem;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.view-btn {
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.5);
  color: #60a5fa;
}

.view-btn:hover {
  background: rgba(59, 130, 246, 0.3);
}

.confirm-btn {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
}

.confirm-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.4);
}

/* 弹窗动画 */
.modal-enter-active {
  animation: modalIn 0.3s ease;
}

.modal-leave-active {
  animation: modalOut 0.2s ease;
}

@keyframes modalIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes modalOut {
  from {
    opacity: 1;
  }
  to {
    opacity: 0;
  }
}

.modal-enter-active .alert-modal {
  animation: modalContentIn 0.3s ease;
}

.modal-leave-active .alert-modal {
  animation: modalContentOut 0.2s ease;
}

@keyframes modalContentIn {
  from {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
  to {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
}

@keyframes modalContentOut {
  from {
    opacity: 1;
    transform: scale(1) translateY(0);
  }
  to {
    opacity: 0;
    transform: scale(0.9) translateY(-20px);
  }
}

/* 响应式 */
@media (max-width: 640px) {
  .toast-container {
    right: 0.5rem;
    left: 0.5rem;
    max-width: none;
  }

  .alert-modal-overlay {
    padding: 1rem;
  }

  .alert-modal {
    max-width: 100%;
  }
}
</style>
