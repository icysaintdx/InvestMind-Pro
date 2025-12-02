<template>
  <div class="typewriter-container" ref="typewriterRef">
    <span v-html="formattedText"></span>
    <span v-if="isTyping" class="cursor">|</span>
  </div>
</template>

<script>
import { ref, onMounted, onUnmounted, watch, nextTick, computed } from 'vue'

export default {
  name: 'TypeWriter',
  props: {
    text: {
      type: String,
      required: true
    },
    speed: {
      type: Number,
      default: 20 // 毫秒/字符
    }
  },
  emits: ['complete'],
  setup(props, { emit }) {
    const displayText = ref('')
    const isTyping = ref(false)
    const typewriterRef = ref(null)
    let typingTimer = null
    let currentIndex = 0

    // 格式化文本，将换行符转换为<br>
    const formattedText = computed(() => {
      return displayText.value.replace(/\n/g, '<br>')
    })

    // 获取滚动容器（分析输出的父容器）
    const getScrollContainer = () => {
      if (!typewriterRef.value) return null
      
      // 从当前typewriter元素向上查找card-content容器
      let element = typewriterRef.value.parentElement
      while (element) {
        if (element.classList.contains('card-content')) {
          return element
        }
        element = element.parentElement
      }
      return null
    }

    // 滚动到底部
    const scrollToBottom = () => {
      const container = getScrollContainer()
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    }

    // 滚动到顶部
    const scrollToTop = () => {
      const container = getScrollContainer()
      if (container) {
        container.scrollTo({
          top: 0,
          behavior: 'smooth'
        })
      }
    }

    const startTyping = () => {
      if (!props.text) return
      
      isTyping.value = true
      displayText.value = ''
      currentIndex = 0
      
      typingTimer = setInterval(() => {
        if (currentIndex < props.text.length) {
          displayText.value += props.text[currentIndex]
          currentIndex++
          
          // 打字时持续滚动到底部
          nextTick(() => {
            scrollToBottom()
          })
        } else {
          stopTyping()
          
          // 完成后延迟500ms滚动到顶部
          setTimeout(() => {
            scrollToTop()
          }, 500)
          
          emit('complete')
        }
      }, props.speed + Math.random() * 10) // 添加随机性让打字效果更自然
    }

    const stopTyping = () => {
      if (typingTimer) {
        clearInterval(typingTimer)
        typingTimer = null
      }
      isTyping.value = false
    }

    // 监听文本变化，重新开始打字
    watch(() => props.text, (newText) => {
      if (newText) {
        stopTyping()
        startTyping()
      }
    })

    onMounted(() => {
      startTyping()
    })

    onUnmounted(() => {
      stopTyping()
    })

    return {
      displayText,
      formattedText,
      isTyping,
      typewriterRef
    }
  }
}
</script>

<style scoped>
.typewriter-container {
  display: inline;
}

.cursor {
  display: inline-block;
  animation: blink 1s infinite;
  color: #60a5fa;
  font-weight: bold;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
</style>
