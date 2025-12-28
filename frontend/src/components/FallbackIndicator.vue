<template>
  <div v-if="showIndicator" class="fallback-indicator">
    <span
      :class="['fallback-tag', tagClass]"
      :title="tooltipContent"
    >
      <span class="tag-icon">{{ icon }}</span>
      <span class="tag-label">{{ label }}</span>
    </span>
  </div>
</template>

<script setup>
import { computed } from 'vue'

/* eslint-disable no-undef */
const props = defineProps({
  fallbackLevel: {
    type: Number,
    default: 0
  },
  showAlways: {
    type: Boolean,
    default: false
  }
})

const showIndicator = computed(() =>
  props.showAlways || props.fallbackLevel >= 0
)

const label = computed(() => {
  if (props.fallbackLevel === 99) return '默认响应'
  if (props.fallbackLevel === 3) return '最小化'
  if (props.fallbackLevel === 2) return '深度压缩'
  if (props.fallbackLevel === 1) return '轻度压缩'
  if (props.fallbackLevel === 0) return '原始请求'
  return `L${props.fallbackLevel}`
})

const icon = computed(() => {
  if (props.fallbackLevel === 99) return '⚠️'
  if (props.fallbackLevel === 3) return '🔻'
  if (props.fallbackLevel === 2) return '📉'
  if (props.fallbackLevel === 1) return '📊'
  if (props.fallbackLevel === 0) return '✅'
  return '❓'
})

const tagClass = computed(() => {
  if (props.fallbackLevel === 99) return 'tag-error'
  if (props.fallbackLevel === 3) return 'tag-warning'
  if (props.fallbackLevel === 2) return 'tag-info'
  if (props.fallbackLevel === 1) return 'tag-info-light'
  return 'tag-success'
})

const tooltipContent = computed(() => {
  if (props.fallbackLevel === 99) {
    return '⚠️ 默认响应：由于网络超时，使用了预设的保守建议'
  }
  if (props.fallbackLevel === 3) {
    return '🔻 最小化请求：提示词压缩到10%，仅保留最核心信息'
  }
  if (props.fallbackLevel === 2) {
    return '📉 深度压缩：提示词压缩到25%，保留关键要点'
  }
  if (props.fallbackLevel === 1) {
    return '📊 轻度压缩：提示词压缩到50%，保留重要信息'
  }
  return '✅ 原始请求：完整提示词，无压缩降级'
})
/* eslint-enable no-undef */
</script>

<style scoped>
.fallback-indicator {
  display: inline-flex;
  align-items: center;
  margin-left: 6px;
}

.fallback-tag {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 2px 8px;
  border-radius: 6px;
  font-size: 0.65rem;
  font-weight: 600;
  cursor: help;
  transition: all 0.2s ease;
  white-space: nowrap;
}

.fallback-tag:hover {
  transform: scale(1.05);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
}

.tag-icon {
  font-size: 0.7rem;
}

.tag-label {
  letter-spacing: 0.02em;
}

/* 原始请求 - 绿色 */
.tag-success {
  background: linear-gradient(135deg, rgba(34, 197, 94, 0.2) 0%, rgba(22, 163, 74, 0.2) 100%);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.4);
}

/* 轻度压缩 - 浅蓝色 */
.tag-info-light {
  background: linear-gradient(135deg, rgba(56, 189, 248, 0.2) 0%, rgba(14, 165, 233, 0.2) 100%);
  color: #38bdf8;
  border: 1px solid rgba(56, 189, 248, 0.4);
}

/* 深度压缩 - 蓝色 */
.tag-info {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2) 0%, rgba(37, 99, 235, 0.2) 100%);
  color: #3b82f6;
  border: 1px solid rgba(59, 130, 246, 0.4);
}

/* 最小化 - 橙色 */
.tag-warning {
  background: linear-gradient(135deg, rgba(251, 146, 60, 0.2) 0%, rgba(249, 115, 22, 0.2) 100%);
  color: #fb923c;
  border: 1px solid rgba(251, 146, 60, 0.4);
  animation: pulse-warning 2s infinite;
}

/* 默认响应 - 红色 */
.tag-error {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2) 0%, rgba(220, 38, 38, 0.2) 100%);
  color: #ef4444;
  border: 1px solid rgba(239, 68, 68, 0.4);
  animation: pulse-error 1.5s infinite;
}

@keyframes pulse-warning {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.7; }
}

@keyframes pulse-error {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.8; transform: scale(1.02); }
}
</style>
