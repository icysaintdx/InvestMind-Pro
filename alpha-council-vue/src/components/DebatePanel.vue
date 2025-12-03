<template>
  <div class="debate-panel">
    <div class="debate-header">
      <div class="flex items-center justify-between mb-2">
        <h3 class="text-lg font-bold text-white flex items-center gap-2">
          <span class="text-2xl">⚖️</span>
          {{ title }}
        </h3>
        <span class="status-badge" :class="status">
          {{ statusText }}
        </span>
      </div>
      <div class="text-sm text-slate-400">{{ topic }}</div>
    </div>

    <div class="debate-content">
      <!-- 辩论双方展示 -->
      <div class="sides-header" v-if="sides.length > 0">
        <div class="side left">
          <span class="side-icon">{{ sides[0].icon }}</span>
          <span class="side-name text-red-400">{{ sides[0].name }}</span>
        </div>
        <div class="vs-badge">VS</div>
        <div class="side right">
          <span class="side-name text-green-400">{{ sides[1].name }}</span>
          <span class="side-icon">{{ sides[1].icon }}</span>
        </div>
      </div>

      <!-- 辩论记录流 -->
      <div class="debate-stream" ref="streamContainer">
        <transition-group name="message-fade">
          <div 
            v-for="(msg, index) in messages" 
            :key="index" 
            class="debate-message"
            :class="getMessageClass(msg)"
          >
            <div class="message-avatar">
              {{ msg.agentIcon }}
            </div>
            <div class="message-bubble">
              <div class="message-sender">{{ msg.agentName }}</div>
              <div class="message-text">{{ msg.content }}</div>
              <div class="message-meta" v-if="msg.round">Round {{ msg.round }}</div>
            </div>
          </div>
        </transition-group>
        
        <!-- 加载指示器 -->
        <div v-if="status === 'debating'" class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    </div>

    <!-- 结论区域 -->
    <div v-if="conclusion" class="debate-footer">
      <div class="conclusion-box">
        <div class="conclusion-title">
          <span>🏆 最终结论</span>
          <span class="conclusion-score" :class="getScoreClass(conclusion.score)">
            评分: {{ conclusion.score }}/100
          </span>
        </div>
        <div class="conclusion-text">
          {{ conclusion.content }}
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'DebatePanel',
  props: {
    title: {
      type: String,
      default: '智能博弈'
    },
    topic: {
      type: String,
      default: '等待辩论主题...'
    },
    status: {
      type: String,
      default: 'idle' // idle, debating, finished
    },
    sides: {
      type: Array,
      default: () => [] // [{name: '多头', icon: '🐂'}, {name: '空头', icon: '🐻'}]
    },
    messages: {
      type: Array,
      default: () => []
    },
    conclusion: {
      type: Object,
      default: null // { content: '...', score: 85 }
    }
  },
  computed: {
    statusText() {
      const map = {
        'idle': '准备中',
        'debating': '激烈辩论中',
        'finished': '辩论结束'
      }
      return map[this.status] || this.status
    }
  },
  updated() {
    this.scrollToBottom()
  },
  methods: {
    getMessageClass(msg) {
      if (this.sides.length < 2) return 'left'
      // 假设 sides[0] 是左方，sides[1] 是右方
      if (msg.agentName === this.sides[0].name) return 'message-left'
      if (msg.agentName === this.sides[1].name) return 'message-right'
      return 'message-center'
    },
    getScoreClass(score) {
      if (score >= 70) return 'text-green-400'
      if (score >= 40) return 'text-yellow-400'
      return 'text-red-400'
    },
    scrollToBottom() {
      const container = this.$refs.streamContainer
      if (container) {
        container.scrollTop = container.scrollHeight
      }
    }
  }
}
</script>

<style scoped>
.debate-panel {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 0.75rem;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 400px;
  backdrop-filter: blur(10px);
}

.debate-header {
  padding: 1rem;
  background: rgba(30, 41, 59, 0.5);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.status-badge {
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  border-radius: 9999px;
  background: rgba(255, 255, 255, 0.1);
  color: #94a3b8;
}

.status-badge.debating {
  background: rgba(234, 179, 8, 0.2);
  color: #fcd34d;
  animation: pulse 2s infinite;
}

.status-badge.finished {
  background: rgba(16, 185, 129, 0.2);
  color: #6ee7b7;
}

.sides-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 2rem;
  background: rgba(0, 0, 0, 0.2);
}

.side {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-weight: bold;
}

.side-icon {
  font-size: 1.5rem;
}

.vs-badge {
  font-weight: 900;
  font-style: italic;
  color: #6366f1;
  font-size: 1.25rem;
}

.debate-stream {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
  scroll-behavior: smooth;
}

.debate-message {
  display: flex;
  gap: 0.75rem;
  max-width: 80%;
  align-items: flex-start;
}

.message-left {
  align-self: flex-start;
  flex-direction: row;
}

.message-right {
  align-self: flex-end;
  flex-direction: row-reverse;
}

.message-center {
  align-self: center;
  max-width: 90%;
  background: rgba(255, 255, 255, 0.05);
  padding: 0.5rem 1rem;
  border-radius: 0.5rem;
}

.message-avatar {
  font-size: 1.5rem;
  background: rgba(255, 255, 255, 0.1);
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.message-bubble {
  background: rgba(30, 41, 59, 0.8);
  padding: 0.75rem;
  border-radius: 0.75rem;
  position: relative;
  border: 1px solid rgba(255, 255, 255, 0.05);
}

.message-left .message-bubble {
  border-top-left-radius: 0;
  border-left: 2px solid rgba(239, 68, 68, 0.5); /* Red tint for left/bear */
}

.message-right .message-bubble {
  border-top-right-radius: 0;
  border-right: 2px solid rgba(34, 197, 94, 0.5); /* Green tint for right/bull */
}

.message-sender {
  font-size: 0.75rem;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 0.25rem;
}

.message-text {
  font-size: 0.875rem;
  color: #e2e8f0;
  line-height: 1.5;
  white-space: pre-wrap;
}

.message-meta {
  font-size: 0.65rem;
  color: #64748b;
  margin-top: 0.25rem;
  text-align: right;
}

.debate-footer {
  padding: 1rem;
  background: rgba(15, 23, 42, 0.8);
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.conclusion-box {
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 0.5rem;
  padding: 1rem;
}

.conclusion-title {
  display: flex;
  justify-content: space-between;
  font-weight: bold;
  color: #818cf8;
  margin-bottom: 0.5rem;
}

.conclusion-text {
  font-size: 0.875rem;
  color: #c7d2fe;
  line-height: 1.6;
}

/* Animations */
.message-fade-enter-active, .message-fade-leave-active {
  transition: all 0.5s ease;
}
.message-fade-enter-from, .message-fade-leave-to {
  opacity: 0;
  transform: translateY(20px);
}

.typing-indicator {
  display: flex;
  gap: 4px;
  padding: 0.5rem;
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  margin-left: 3rem;
}

.typing-indicator span {
  width: 6px;
  height: 6px;
  background: #94a3b8;
  border-radius: 50%;
  animation: bounce 1.4s infinite ease-in-out both;
}

.typing-indicator span:nth-child(1) { animation-delay: -0.32s; }
.typing-indicator span:nth-child(2) { animation-delay: -0.16s; }

@keyframes bounce {
  0%, 80%, 100% { transform: scale(0); }
  40% { transform: scale(1); }
}
</style>
