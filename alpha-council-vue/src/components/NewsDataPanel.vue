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

        <!-- 关键词云 -->
        <div class="data-section">
          <div class="section-title">
            <span class="section-icon">🔥</span>
            热门关键词
          </div>
          <div class="keywords-cloud">
            <span 
              v-for="keyword in keywords" 
              :key="keyword.text"
              :class="['keyword-tag', `size-${keyword.size}`]"
            >
              {{ keyword.text }}
            </span>
            <div v-if="keywords.length === 0" class="keywords-empty">
              暂无关键词
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, nextTick } from 'vue'

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
      simulateNews
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
</style>
