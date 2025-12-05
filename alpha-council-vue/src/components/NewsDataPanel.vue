<template>
  <div :class="['data-panel', 'right-panel', { 'panel-open': isOpen }]">
    <!-- 切换按钮 -->
    <button @click="togglePanel" class="panel-toggle right-toggle">
      <span class="toggle-icon">{{ isOpen ? '▶' : '◀' }}</span>
      <span class="toggle-text">新闻舆情</span>
    </button>

    <!-- 面板内容 -->
    <div class="panel-content">
      <div class="panel-header">
        <h3 class="panel-title">
          <span class="title-icon">📰</span>
          新闻舆情透明化
        </h3>
        <p class="panel-subtitle">实时新闻采集与情绪分析</p>
      </div>

      <div class="panel-body">
        <!-- 采集状态 -->
        <div class="data-section">
          <div class="section-title">
            <span class="section-icon">🕷️</span>
            采集状态
          </div>
          <div class="crawl-stats">
            <div class="stat-item">
              <span class="stat-label">新闻总数</span>
              <span class="stat-value">{{ stats.totalNews }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">正面</span>
              <span class="stat-value positive">{{ stats.positive }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">中性</span>
              <span class="stat-value neutral">{{ stats.neutral }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">负面</span>
              <span class="stat-value negative">{{ stats.negative }}</span>
            </div>
          </div>
        </div>

        <!-- 新闻流 -->
        <div class="data-section">
          <div class="section-title">
            <span class="section-icon">📡</span>
            新闻流
            <button @click="clearNews" class="clear-btn">清空</button>
          </div>
          <div class="news-container" ref="newsContainer">
            <div 
              v-for="(news, index) in newsList" 
              :key="index"
              :class="['news-item', news.sentiment]"
            >
              <div class="news-header">
                <span class="news-source">{{ news.source }}</span>
                <span class="news-time">{{ news.time }}</span>
              </div>
              <div class="news-title">{{ news.title }}</div>
              <div class="news-summary" v-if="news.summary">
                {{ news.summary }}
              </div>
              <div class="news-tags" v-if="news.tags && news.tags.length">
                <span 
                  v-for="tag in news.tags" 
                  :key="tag"
                  class="news-tag"
                >
                  #{{ tag }}
                </span>
              </div>
              <div class="news-sentiment">
                <span class="sentiment-icon">{{ getSentimentIcon(news.sentiment) }}</span>
                <span class="sentiment-text">{{ getSentimentText(news.sentiment) }}</span>
                <span class="sentiment-score">{{ news.score }}</span>
              </div>
            </div>
            <div v-if="newsList.length === 0" class="news-empty">
              等待新闻采集...
            </div>
          </div>
        </div>

        <!-- 社交媒体热度 -->
        <div class="data-section">
          <div class="section-title">
            <span class="section-icon">📱</span>
            社交媒体热度
          </div>
          <div class="social-media-content">
            <div v-if="socialMediaLoading" class="loading-state">
              <span class="spinner-small"></span> 加载中...
            </div>
            <div v-else-if="socialMediaError" class="error-state">
              ❌ {{ socialMediaError }}
            </div>
            <div v-else>
              <!-- 微博股票热议 Top 5 -->
              <div class="social-section">
                <div class="social-subtitle">🔥 微博热议</div>
                <div class="social-list">
                  <div 
                    v-for="(item, index) in weiboStockHot.slice(0, 5)" 
                    :key="index"
                    class="social-item"
                    :class="getRateClass(item.rate)"
                  >
                    <span class="rank">{{ index + 1 }}</span>
                    <span class="name">
                      {{ item.name }}
                      <span class="code" v-if="item.code">({{ item.code }})</span>
                    </span>
                    <span class="rate">{{ formatRate(item.rate) }}</span>
                  </div>
                </div>
              </div>
              <!-- 百度热搜 Top 5 -->
              <div class="social-section">
                <div class="social-subtitle">🔍 百度热搜</div>
                <div class="social-list">
                  <div 
                    v-for="(item, index) in baiduHotSearch.slice(0, 5)" 
                    :key="index"
                    class="social-item"
                  >
                    <span class="rank">{{ index + 1 }}</span>
                    <span class="name">
                      {{ item['名称/代码'] || item.name }}
                      <span class="code" v-if="item['代码'] || item.code">({{ item['代码'] || item.code }})</span>
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, nextTick, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'

export default {
  name: 'NewsDataPanel',
  setup() {
    const isOpen = ref(false)
    const newsList = ref([])
    const newsContainer = ref(null)
    
    const stats = ref({
      totalNews: 0,
      positive: 0,
      neutral: 0,
      negative: 0
    })

    const keywords = ref([])
    
    // 社交媒体数据
    const socialMediaLoading = ref(false)
    const socialMediaError = ref(null)
    const weiboStockHot = ref([])
    const baiduHotSearch = ref([])
    let autoRefreshInterval = null

    const togglePanel = () => {
      isOpen.value = !isOpen.value
    }

    const addNews = (newsData) => {
      newsList.value.unshift(newsData)
      
      // 更新统计
      stats.value.totalNews++
      if (newsData.sentiment === 'positive') stats.value.positive++
      else if (newsData.sentiment === 'neutral') stats.value.neutral++
      else if (newsData.sentiment === 'negative') stats.value.negative++

      // 限制新闻数量
      if (newsList.value.length > 30) {
        newsList.value.pop()
      }

      // 自动滚动到顶部
      nextTick(() => {
        if (newsContainer.value) {
          newsContainer.value.scrollTop = 0
        }
      })
    }

    const clearNews = () => {
      newsList.value = []
      stats.value = {
        totalNews: 0,
        positive: 0,
        neutral: 0,
        negative: 0
      }
    }

    const getSentimentIcon = (sentiment) => {
      const iconMap = {
        positive: '😊',
        neutral: '😐',
        negative: '😟'
      }
      return iconMap[sentiment] || '😐'
    }

    const getSentimentText = (sentiment) => {
      const textMap = {
        positive: '正面',
        neutral: '中性',
        negative: '负面'
      }
      return textMap[sentiment] || '中性'
    }

    // 模拟添加新闻（用于测试）
    const simulateNews = () => {
      const sources = ['新浪财经', '东方财富', '财联社', '证券时报', '雪球']
      const sentiments = ['positive', 'neutral', 'negative']
      const tags = ['业绩', '政策', '行业', '技术', '市场']
      
      const now = new Date()
      const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}`
      
      addNews({
        source: sources[Math.floor(Math.random() * sources.length)],
        time,
        title: '示例新闻标题 - 公司发布最新财报',
        summary: '公司本季度营收同比增长15%，净利润增长20%...',
        tags: [tags[Math.floor(Math.random() * tags.length)]],
        sentiment: sentiments[Math.floor(Math.random() * sentiments.length)],
        score: (Math.random() * 2 - 1).toFixed(2)
      })
    }
    
    // 加载社交媒体数据
    const loadSocialMediaData = async () => {
      socialMediaLoading.value = true
      socialMediaError.value = null
      
      try {
        const response = await axios.get('http://localhost:8000/api/akshare/social-media/all')
        const data = response.data.data
        
        weiboStockHot.value = data.weibo_stock_hot || []
        baiduHotSearch.value = data.baidu_hot_search || []
      } catch (err) {
        socialMediaError.value = '加载失败'
        console.error('加载社交媒体数据失败:', err)
      } finally {
        socialMediaLoading.value = false
      }
    }
    
    const formatRate = (rate) => {
      if (rate === null || rate === undefined) return '-'
      const num = parseFloat(rate)
      return num > 0 ? `+${num.toFixed(2)}%` : `${num.toFixed(2)}%`
    }
    
    const getRateClass = (rate) => {
      if (rate === null || rate === undefined) return ''
      const num = parseFloat(rate)
      if (num > 0) return 'positive'
      if (num < 0) return 'negative'
      return 'neutral'
    }
    
    // 生命周期
    onMounted(() => {
      loadSocialMediaData()
      // 每5分钟自动刷新
      autoRefreshInterval = setInterval(() => {
        loadSocialMediaData()
      }, 5 * 60 * 1000)
    })
    
    onBeforeUnmount(() => {
      if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval)
      }
    })

    return {
      isOpen,
      newsList,
      newsContainer,
      stats,
      keywords,
      togglePanel,
      addNews,
      clearNews,
      getSentimentIcon,
      getSentimentText,
      simulateNews,
      socialMediaLoading,
      socialMediaError,
      weiboStockHot,
      baiduHotSearch,
      formatRate,
      getRateClass
    }
  }
}
</script>

<style scoped>
.data-panel {
  position: fixed;
  top: 5rem;
  bottom: 2rem;
  width: 420px;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(51, 65, 85, 0.8);
  border-radius: 0.75rem;
  backdrop-filter: blur(12px);
  transition: transform 0.3s ease;
  z-index: 40;
  display: flex;
  flex-direction: column;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
}

.right-panel {
  right: 1rem;
  transform: translateX(100%);
}

.right-panel.panel-open {
  transform: translateX(0);
}

.panel-toggle {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(51, 65, 85, 0.8);
  padding: 0.75rem 0.5rem;
  border-radius: 0.5rem 0 0 0.5rem;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  color: #94a3b8;
  font-size: 0.75rem;
  z-index: 1;
}

.right-toggle {
  left: -2.5rem;
}

.panel-toggle:hover {
  background: rgba(51, 65, 85, 0.8);
  color: white;
}

.toggle-icon {
  font-size: 1rem;
}

.toggle-text {
  writing-mode: vertical-rl;
  font-weight: 500;
}

.panel-content {
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.panel-header {
  padding: 1.5rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: white;
  margin: 0;
}

.title-icon {
  font-size: 1.25rem;
}

.panel-subtitle {
  margin: 0.5rem 0 0 0;
  font-size: 0.75rem;
  color: #94a3b8;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.panel-body::-webkit-scrollbar {
  width: 6px;
}

.panel-body::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
  border-radius: 3px;
}

.panel-body::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.5);
  border-radius: 3px;
}

.panel-body::-webkit-scrollbar-thumb:hover {
  background: rgba(100, 116, 139, 0.7);
}

.data-section {
  background: rgba(30, 41, 59, 0.3);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.5rem;
  padding: 1rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 0.75rem;
}

.section-icon {
  font-size: 1rem;
}

.clear-btn {
  margin-left: auto;
  padding: 0.25rem 0.5rem;
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.25rem;
  color: #ef4444;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.clear-btn:hover {
  background: rgba(239, 68, 68, 0.3);
}

.crawl-stats {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.5rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 0.375rem;
}

.stat-label {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #e2e8f0;
}

.stat-value.positive {
  color: #10b981;
}

.stat-value.neutral {
  color: #f59e0b;
}

.stat-value.negative {
  color: #ef4444;
}

.news-container {
  max-height: 500px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.news-container::-webkit-scrollbar {
  width: 4px;
}

.news-container::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.3);
}

.news-container::-webkit-scrollbar-thumb {
  background: rgba(100, 116, 139, 0.3);
  border-radius: 2px;
}

.news-item {
  padding: 0.75rem;
  background: rgba(15, 23, 42, 0.5);
  border-left: 3px solid #64748b;
  border-radius: 0.375rem;
  animation: slideIn 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.news-item.positive {
  border-left-color: #10b981;
}

.news-item.neutral {
  border-left-color: #f59e0b;
}

.news-item.negative {
  border-left-color: #ef4444;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.news-source {
  font-size: 0.7rem;
  color: #3b82f6;
  font-weight: 500;
}

.news-time {
  font-size: 0.7rem;
  color: #64748b;
  font-family: monospace;
}

.news-title {
  font-size: 0.875rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 0.5rem;
  line-height: 1.4;
}

.news-summary {
  font-size: 0.75rem;
  color: #94a3b8;
  line-height: 1.5;
  margin-bottom: 0.5rem;
}

.news-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
  margin-bottom: 0.5rem;
}

.news-tag {
  padding: 0.125rem 0.5rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.25rem;
  font-size: 0.7rem;
  color: #3b82f6;
}

.news-sentiment {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding-top: 0.5rem;
  border-top: 1px solid rgba(51, 65, 85, 0.3);
  font-size: 0.75rem;
}

.sentiment-icon {
  font-size: 1rem;
}

.sentiment-text {
  color: #94a3b8;
}

.sentiment-score {
  margin-left: auto;
  font-family: monospace;
  font-weight: 600;
  color: #e2e8f0;
}

.news-empty {
  text-align: center;
  color: #64748b;
  padding: 2rem 1rem;
  font-size: 0.875rem;
}

.keywords-cloud {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  padding: 0.5rem;
}

.keyword-tag {
  padding: 0.375rem 0.75rem;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.375rem;
  color: #3b82f6;
  font-weight: 500;
  transition: all 0.2s;
  cursor: pointer;
}

.keyword-tag:hover {
  background: rgba(59, 130, 246, 0.25);
  transform: translateY(-2px);
}

.keyword-tag.size-1 {
  font-size: 0.75rem;
}

.keyword-tag.size-2 {
  font-size: 0.875rem;
}

.keyword-tag.size-3 {
  font-size: 1rem;
}

.keywords-empty {
  width: 100%;
  text-align: center;
  color: #64748b;
  padding: 1rem;
  font-size: 0.875rem;
}

/* 社交媒体样式 */
.social-media-content {
  font-size: 0.875rem;
}

.loading-state, .error-state {
  text-align: center;
  padding: 1rem;
  color: #94a3b8;
  font-size: 0.875rem;
}

.spinner-small {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(59, 130, 246, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.social-section {
  margin-bottom: 1rem;
}

.social-section:last-child {
  margin-bottom: 0;
}

.social-subtitle {
  font-size: 0.75rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
  font-weight: 600;
}

.social-list {
  display: flex;
  flex-direction: column;
  gap: 0.375rem;
}

.social-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 0.375rem;
  transition: all 0.2s;
}

.social-item:hover {
  background: rgba(30, 41, 59, 0.8);
  transform: translateX(2px);
}

.social-item .rank {
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 0.25rem;
  color: #3b82f6;
  font-weight: bold;
  font-size: 0.7rem;
  flex-shrink: 0;
}

.social-item .name {
  flex: 1;
  color: #e2e8f0;
  font-size: 0.8rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.social-item .name .code {
  color: #94a3b8;
  font-size: 0.7rem;
  font-weight: 400;
  margin-left: 4px;
}

.social-item .rate {
  font-weight: 600;
  font-size: 0.75rem;
  flex-shrink: 0;
}

.social-item.positive .rate {
  color: #10b981;
}

.social-item.negative .rate {
  color: #ef4444;
}

.social-item.neutral .rate {
  color: #94a3b8;
}
</style>
