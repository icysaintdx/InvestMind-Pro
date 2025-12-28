<template>
  <Transition name="toast-fade">
    <div v-if="visible" :class="['toast', `toast-${type}`]">
      <span class="toast-icon">{{ icon }}</span>
      <span class="toast-message">{{ message }}</span>
    </div>
  </Transition>
</template>

<script>
export default {
  name: 'Toast',
  data() {
    return {
      visible: false,
      message: '',
      type: 'info',
      duration: 3000,
      timer: null
    }
  },
  computed: {
    icon() {
      const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
      }
      return icons[this.type] || icons.info
    }
  },
  methods: {
    show(options = {}) {
      if (typeof options === 'string') {
        options = { message: options }
      }
      
      this.message = options.message || ''
      this.type = options.type || 'info'
      this.duration = options.duration !== undefined ? options.duration : 3000
      
      // 清除之前的定时器
      if (this.timer) {
        clearTimeout(this.timer)
      }
      
      this.visible = true
      
      // 自动隐藏
      if (this.duration > 0) {
        this.timer = setTimeout(() => {
          this.hide()
        }, this.duration)
      }
    },
    
    hide() {
      this.visible = false
      if (this.timer) {
        clearTimeout(this.timer)
        this.timer = null
      }
    },
    
    success(message, duration) {
      this.show({ message, type: 'success', duration })
    },
    
    error(message, duration) {
      this.show({ message, type: 'error', duration })
    },
    
    warning(message, duration) {
      this.show({ message, type: 'warning', duration })
    },
    
    info(message, duration) {
      this.show({ message, type: 'info', duration })
    }
  },
  
  beforeUnmount() {
    if (this.timer) {
      clearTimeout(this.timer)
    }
  }
}
</script>

<style scoped>
.toast {
  position: fixed;
  top: 20px;
  left: 50%;
  transform: translateX(-50%);
  padding: 12px 24px;
  background: rgba(15, 23, 42, 0.95);
  border-radius: 8px;
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  gap: 12px;
  z-index: 9999;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  max-width: 80vw;
}

.toast-icon {
  font-size: 20px;
  line-height: 1;
}

.toast-message {
  color: #fff;
  font-size: 14px;
  line-height: 1.5;
  max-width: 500px;
  word-wrap: break-word;
}

/* 类型样式 */
.toast-success {
  border-color: rgba(34, 197, 94, 0.3);
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.1), rgba(15, 23, 42, 0.95));
}

.toast-error {
  border-color: rgba(239, 68, 68, 0.3);
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(15, 23, 42, 0.95));
}

.toast-warning {
  border-color: rgba(251, 146, 60, 0.3);
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.1), rgba(15, 23, 42, 0.95));
}

.toast-info {
  border-color: rgba(59, 130, 246, 0.3);
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.1), rgba(15, 23, 42, 0.95));
}

/* 动画 */
.toast-fade-enter-active,
.toast-fade-leave-active {
  transition: all 0.3s ease;
}

.toast-fade-enter-from {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

.toast-fade-leave-to {
  opacity: 0;
  transform: translateX(-50%) translateY(-20px);
}

/* 移动端适配 */
@media (max-width: 640px) {
  .toast {
    max-width: 90vw;
    padding: 10px 16px;
  }
  
  .toast-message {
    font-size: 13px;
  }
}
</style>
