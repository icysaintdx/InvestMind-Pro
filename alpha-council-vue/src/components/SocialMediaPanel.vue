<template>
  <div class="social-media-panel">
    <div class="panel-header">
      <h3 class="panel-title">
        <span class="icon">📱</span>
        社交媒体热度
      </h3>
      <button @click="refreshData" class="refresh-btn" :disabled="loading">
        <span v-if="!loading">🔄</span>
        <span v-else class="spinner-small"></span>
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="error" class="error-state">
      <p>❌ {{ error }}</p>
      <button @click="refreshData" class="retry-btn">重试</button>
    </div>

    <div v-else class="content">
      <!-- 微博股票热议 -->
      <div class="section">
        <h4 class="section-title">🔥 微博股票热议 (Top 10)</h4>
        <div class="hot-list">
          <div 
            v-for="(item, index) in weiboStockHot.slice(0, 10)" 
            :key="index"
            class="hot-item"
            :class="getRateClass(item.rate)"
          >
            <span class="rank">{{ index + 1 }}</span>
            <span class="name">{{ item.name }}</span>
            <span class="rate">{{ formatRate(item.rate) }}</span>
          </div>
        </div>
      </div>

      <!-- 百度热搜股票 -->
      <div class="section">
        <h4 class="section-title">🔍 百度热搜股票</h4>
        <div class="hot-list">
          <div 
            v-for="(item, index) in baiduHotSearch" 
            :key="index"
            class="hot-item"
          >
            <span class="rank">{{ index + 1 }}</span>
            <span class="name">{{ item['名称/代码'] || item.name }}</span>
            <span class="heat">🔥 {{ item['综合热度'] || item.heat }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import axios from 'axios'

export default {
  name: 'SocialMediaPanel',
  data() {
    return {
      loading: false,
      error: null,
      weiboStockHot: [],
      baiduHotSearch: [],
      autoRefreshInterval: null
    }
  },
  mounted() {
    this.loadData()
    // 每5分钟自动刷新
    this.autoRefreshInterval = setInterval(() => {
      this.loadData()
    }, 5 * 60 * 1000)
  },
  beforeUnmount() {
    if (this.autoRefreshInterval) {
      clearInterval(this.autoRefreshInterval)
    }
  },
  methods: {
    async loadData() {
      this.loading = true
      this.error = null
      
      try {
        const response = await axios.get('http://localhost:8000/api/akshare/social-media/all')
        const data = response.data.data
        
        this.weiboStockHot = data.weibo_stock_hot || []
        this.baiduHotSearch = data.baidu_hot_search || []
      } catch (err) {
        this.error = '加载失败: ' + (err.message || '未知错误')
        console.error('加载社交媒体数据失败:', err)
      } finally {
        this.loading = false
      }
    },
    refreshData() {
      this.loadData()
    },
    formatRate(rate) {
      if (rate === null || rate === undefined) return '-'
      const num = parseFloat(rate)
      return num > 0 ? `+${num.toFixed(2)}%` : `${num.toFixed(2)}%`
    },
    getRateClass(rate) {
      if (rate === null || rate === undefined) return ''
      const num = parseFloat(rate)
      if (num > 0) return 'positive'
      if (num < 0) return 'negative'
      return 'neutral'
    }
  }
}
</script>

<style scoped>
.social-media-panel {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.panel-title {
  font-size: 18px;
  font-weight: bold;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon {
  font-size: 24px;
}

.refresh-btn {
  background: rgba(59, 130, 246, 0.1);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 6px;
  padding: 6px 12px;
  color: #3b82f6;
  cursor: pointer;
  transition: all 0.2s;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.5);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.loading-state, .error-state {
  text-align: center;
  padding: 40px 20px;
  color: #94a3b8;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 4px solid rgba(59, 130, 246, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

.spinner-small {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(59, 130, 246, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.retry-btn {
  margin-top: 12px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 6px;
  padding: 8px 16px;
  cursor: pointer;
}

.content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.section {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 8px;
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 12px;
}

.hot-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.hot-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 6px;
  transition: all 0.2s;
}

.hot-item:hover {
  background: rgba(30, 41, 59, 0.8);
  transform: translateX(4px);
}

.rank {
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 4px;
  color: #3b82f6;
  font-weight: bold;
  font-size: 12px;
  flex-shrink: 0;
}

.name {
  flex: 1;
  color: #e2e8f0;
  font-weight: 500;
}

.rate, .heat {
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.positive .rate {
  color: #10b981;
}

.negative .rate {
  color: #ef4444;
}

.neutral .rate {
  color: #94a3b8;
}

.heat {
  color: #f59e0b;
}
</style>
