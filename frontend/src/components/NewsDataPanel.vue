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
        <!-- 搜索框 -->
        <div class="search-box">
          <input
            v-model="searchQuery"
            @keyup.enter="searchNews"
            placeholder="输入股票代码搜索新闻..."
            class="search-input"
          />
          <button @click="searchNews" class="search-btn">搜索</button>
        </div>
      </div>

      <div class="panel-body">
        <!-- 情绪趋势指示器 -->
        <div class="data-section sentiment-trend-section">
          <div class="section-title">
            <span class="section-icon">📊</span>
            情绪趋势
            <span :class="['trend-badge', sentimentTrend]">
              {{ getTrendText(sentimentTrend) }}
            </span>
          </div>
          <div class="trend-bar">
            <div class="trend-segment positive" :style="{ width: trendPercentages.positive + '%' }"></div>
            <div class="trend-segment neutral" :style="{ width: trendPercentages.neutral + '%' }"></div>
            <div class="trend-segment negative" :style="{ width: trendPercentages.negative + '%' }"></div>
          </div>
          <div class="trend-labels">
            <span class="trend-label positive">正面 {{ trendPercentages.positive }}%</span>
            <span class="trend-label neutral">中性 {{ trendPercentages.neutral }}%</span>
            <span class="trend-label negative">负面 {{ trendPercentages.negative }}%</span>
          </div>
        </div>

        <!-- 采集状态 -->
        <div class="data-section">
          <div class="section-title">
            <span class="section-icon">🕷️</span>
            采集状态
            <button @click="refreshNews" class="sync-btn" :disabled="isLoading">
              {{ isLoading ? '加载中...' : '刷新' }}
            </button>
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
          <!-- 数据源统计 -->
          <div v-if="sourceStats.length > 0" class="source-stats">
            <div class="source-title">数据源分布</div>
            <div class="source-list">
              <span v-for="source in sourceStats" :key="source.name" class="source-tag">
                {{ source.name }}: {{ source.count }}
              </span>
            </div>
          </div>
        </div>

        <!-- 筛选器 -->
        <div class="data-section filter-section">
          <div class="section-title">
            <span class="section-icon">🔍</span>
            筛选
          </div>
          <div class="filter-row">
            <select v-model="filterSentiment" class="filter-select">
              <option value="">全部情绪</option>
              <option value="positive">正面</option>
              <option value="neutral">中性</option>
              <option value="negative">负面</option>
            </select>
            <select v-model="filterSource" class="filter-select">
              <option value="">全部来源</option>
              <option value="eastmoney">东方财富</option>
              <option value="futu">富途</option>
              <option value="sina">新浪财经</option>
              <option value="tonghuashun">同花顺</option>
              <option value="cls">财联社</option>
            </select>
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
              v-for="(news, index) in filteredNewsList"
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
                <span v-if="news.urgency" :class="['urgency-badge', news.urgency]">
                  {{ getUrgencyText(news.urgency) }}
                </span>
              </div>
            </div>
            <div v-if="filteredNewsList.length === 0" class="news-empty">
              {{ isLoading ? '正在加载新闻...' : (searchQuery ? '未找到匹配的新闻' : '等待新闻采集...') }}
            </div>
          </div>
        </div>

        <!-- 社交媒体热度 -->
        <div class="data-section">
          <div class="section-title">
            <span class="section-icon">📱</span>
            社交媒体热度
            <span v-if="socialMediaLoading" class="loading-indicator">
              <span class="spinner-tiny"></span>
            </span>
          </div>
          <div class="social-media-content">
            <div v-if="socialMediaError" class="error-state">
              ❌ {{ socialMediaError }}
            </div>
            <div v-else-if="weiboStockHot.length === 0 && baiduHotSearch.length === 0" class="empty-state">
              暂无数据
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
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import axios from 'axios'
import API_BASE_URL from '@/config/api.js'

export default {
  name: 'NewsDataPanel',
  setup() {
    const isOpen = ref(false)
    const newsList = ref([])
    const newsContainer = ref(null)
    const isLoading = ref(false)

    const stats = ref({
      totalNews: 0,
      positive: 0,
      neutral: 0,
      negative: 0
    })

    const sourceStats = ref([])
    const keywords = ref([])

    // 新增：搜索和筛选
    const searchQuery = ref('')
    const filterSentiment = ref('')
    const filterSource = ref('')

    // 新增：情绪趋势
    const sentimentTrend = ref('neutral')

    // 社交媒体数据
    const socialMediaLoading = ref(false)
    const socialMediaError = ref(null)
    const weiboStockHot = ref([])
    const baiduHotSearch = ref([])

    // 计算属性：情绪趋势百分比
    const trendPercentages = computed(() => {
      const total = stats.value.totalNews || 1
      return {
        positive: Math.round((stats.value.positive / total) * 100),
        neutral: Math.round((stats.value.neutral / total) * 100),
        negative: Math.round((stats.value.negative / total) * 100)
      }
    })

    // 计算属性：筛选后的新闻列表
    const filteredNewsList = computed(() => {
      let result = newsList.value

      // 按情绪筛选
      if (filterSentiment.value) {
        result = result.filter(n => n.sentiment === filterSentiment.value)
      }

      // 按来源筛选
      if (filterSource.value) {
        result = result.filter(n => n.sourceKey && n.sourceKey.includes(filterSource.value))
      }

      return result
    })

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

      // 更新情绪趋势
      updateSentimentTrend()

      // 优先显示非中性新闻，至少显示30条
      const nonNeutralNews = newsList.value.filter(n => n.sentiment !== 'neutral')
      const neutralNews = newsList.value.filter(n => n.sentiment === 'neutral')

      // 如果非中性新闻 >= 30条，只显示非中性
      if (nonNeutralNews.length >= 30) {
        newsList.value = nonNeutralNews
      }
      // 如果非中性新闻 < 30条，用中性补齐到30条
      else {
        const needNeutral = 30 - nonNeutralNews.length
        newsList.value = [...nonNeutralNews, ...neutralNews.slice(0, needNeutral)]
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
      sourceStats.value = []
      sentimentTrend.value = 'neutral'
    }

    const updateSentimentTrend = () => {
      const { positive, negative } = stats.value
      if (positive > negative * 1.5) {
        sentimentTrend.value = 'bullish'
      } else if (negative > positive * 1.5) {
        sentimentTrend.value = 'bearish'
      } else {
        sentimentTrend.value = 'neutral'
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

    const getTrendText = (trend) => {
      const textMap = {
        bullish: '看涨',
        bearish: '看跌',
        neutral: '中性'
      }
      return textMap[trend] || '中性'
    }

    const getUrgencyText = (urgency) => {
      const textMap = {
        critical: '紧急',
        high: '重要',
        medium: '一般',
        low: '低'
      }
      return textMap[urgency] || ''
    }

    // 转换新闻数据格式
    const transformNewsItem = (item) => {
      // 简单的情绪分析（基于标题关键词）
      let sentiment = 'neutral'
      const title = item.title || ''
      const positiveKeywords = ['涨', '上涨', '大涨', '暴涨', '利好', '突破', '新高', '增长', '盈利', '超预期']
      const negativeKeywords = ['跌', '下跌', '大跌', '暴跌', '利空', '下滑', '新低', '亏损', '下降', '不及预期']
      
      for (const keyword of positiveKeywords) {
        if (title.includes(keyword)) {
          sentiment = 'positive'
          break
        }
      }
      if (sentiment === 'neutral') {
        for (const keyword of negativeKeywords) {
          if (title.includes(keyword)) {
            sentiment = 'negative'
            break
          }
        }
      }

      return {
        title: item.title,
        summary: item.content?.substring(0, 150) || '',
        source: item.source || '未知来源',
        sourceKey: item.source_key || '',
        time: item.pub_time ? new Date(item.pub_time).toLocaleString('zh-CN') : '',
        sentiment: sentiment,
        score: sentiment === 'positive' ? 75 : (sentiment === 'negative' ? 25 : 50),
        urgency: null,
        tags: [],
        url: item.url
      }
    }

    // 搜索新闻（按股票代码）
    const searchNews = async () => {
      if (!searchQuery.value.trim()) {
        // 如果搜索框为空，加载市场新闻
        loadMarketNews()
        return
      }

      isLoading.value = true
      try {
        const response = await axios.post(`${API_BASE_URL}/api/unified-news/stock`, {
          stock_code: searchQuery.value.trim(),
          limit: 50
        })

        if (response.data.success && response.data.data) {
          const newsData = response.data.data
          newsList.value = newsData.news.map(transformNewsItem)
          
          // 更新统计
          updateStatsFromList()
          
          // 更新数据源统计
          if (newsData.source_stats) {
            sourceStats.value = Object.entries(newsData.source_stats).map(([name, count]) => ({
              name,
              count
            }))
          }
        }
      } catch (err) {
        console.error('搜索新闻失败:', err)
      } finally {
        isLoading.value = false
      }
    }

    // 刷新新闻
    const refreshNews = () => {
      if (searchQuery.value.trim()) {
        searchNews()
      } else {
        loadMarketNews()
      }
    }

    // 加载市场新闻
    const loadMarketNews = async () => {
      isLoading.value = true
      try {
        const response = await axios.get(`${API_BASE_URL}/api/unified-news/market`, {
          params: { limit: 50 }
        })

        if (response.data.success && response.data.data) {
          const newsData = response.data.data
          newsList.value = newsData.news.map(transformNewsItem)
          
          // 更新统计
          updateStatsFromList()
          
          // 更新数据源统计
          if (newsData.source_stats) {
            sourceStats.value = Object.entries(newsData.source_stats).map(([name, count]) => ({
              name,
              count
            }))
          }
        }
      } catch (err) {
        console.error('加载市场新闻失败:', err)
      } finally {
        isLoading.value = false
      }
    }

    // 从列表更新统计
    const updateStatsFromList = () => {
      stats.value = {
        totalNews: newsList.value.length,
        positive: newsList.value.filter(n => n.sentiment === 'positive').length,
        neutral: newsList.value.filter(n => n.sentiment === 'neutral').length,
        negative: newsList.value.filter(n => n.sentiment === 'negative').length
      }
      updateSentimentTrend()
    }

    // 加载社交媒体数据
    const loadSocialMediaData = async () => {
      socialMediaLoading.value = true
      socialMediaError.value = null

      try {
        const response = await axios.get(`${API_BASE_URL}/api/akshare/social-media/all`)
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
      // 加载市场新闻和社交媒体数据
      loadMarketNews()
      loadSocialMediaData()
    })

    return {
      isOpen,
      newsList,
      filteredNewsList,
      newsContainer,
      stats,
      sourceStats,
      keywords,
      searchQuery,
      filterSentiment,
      filterSource,
      isLoading,
      sentimentTrend,
      trendPercentages,
      togglePanel,
      addNews,
      clearNews,
      getSentimentIcon,
      getSentimentText,
      getTrendText,
      getUrgencyText,
      searchNews,
      refreshNews,
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

.section-title.clickable {
  cursor: pointer;
  user-select: none;
}

.section-title.clickable:hover {
  color: #60a5fa;
}

.collapse-icon {
  font-size: 0.7rem;
  color: #94a3b8;
}

.loading-indicator {
  margin-left: auto;
}

.spinner-tiny {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid rgba(96, 165, 250, 0.3);
  border-top-color: #60a5fa;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
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

/* 数据源统计 */
.source-stats {
  margin-top: 0.75rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(51, 65, 85, 0.3);
}

.source-title {
  font-size: 0.7rem;
  color: #94a3b8;
  margin-bottom: 0.5rem;
}

.source-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.375rem;
}

.source-tag {
  padding: 0.25rem 0.5rem;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.25rem;
  font-size: 0.7rem;
  color: #60a5fa;
}

/* 搜索框样式 */
.search-box {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.search-input {
  flex: 1;
  padding: 0.5rem 0.75rem;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.375rem;
  color: #e2e8f0;
  font-size: 0.8rem;
}

.search-input::placeholder {
  color: #64748b;
}

.search-input:focus {
  outline: none;
  border-color: #3b82f6;
}

.search-btn {
  padding: 0.5rem 1rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.375rem;
  color: #3b82f6;
  font-size: 0.8rem;
  cursor: pointer;
  transition: all 0.2s;
}

.search-btn:hover {
  background: rgba(59, 130, 246, 0.3);
}

/* 情绪趋势样式 */
.sentiment-trend-section {
  padding: 0.75rem;
}

.trend-badge {
  margin-left: auto;
  padding: 0.25rem 0.5rem;
  border-radius: 0.25rem;
  font-size: 0.7rem;
  font-weight: 600;
}

.trend-badge.bullish {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.trend-badge.bearish {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.trend-badge.neutral {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.trend-bar {
  display: flex;
  height: 8px;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(30, 41, 59, 0.5);
  margin-bottom: 0.5rem;
}

.trend-segment {
  transition: width 0.3s ease;
}

.trend-segment.positive {
  background: #10b981;
}

.trend-segment.neutral {
  background: #f59e0b;
}

.trend-segment.negative {
  background: #ef4444;
}

.trend-labels {
  display: flex;
  justify-content: space-between;
  font-size: 0.7rem;
}

.trend-label {
  display: flex;
  align-items: center;
  gap: 0.25rem;
}

.trend-label.positive {
  color: #10b981;
}

.trend-label.neutral {
  color: #f59e0b;
}

.trend-label.negative {
  color: #ef4444;
}

/* 筛选器样式 */
.filter-section {
  padding: 0.75rem;
}

.filter-row {
  display: flex;
  gap: 0.5rem;
}

.filter-select {
  flex: 1;
  padding: 0.375rem 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.375rem;
  color: #e2e8f0;
  font-size: 0.75rem;
  cursor: pointer;
}

.filter-select:focus {
  outline: none;
  border-color: #3b82f6;
}

/* 同步按钮样式 */
.sync-btn {
  margin-left: auto;
  padding: 0.25rem 0.5rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.25rem;
  color: #3b82f6;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.sync-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.3);
}

.sync-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 紧急程度标签 */
.urgency-badge {
  margin-left: auto;
  padding: 0.125rem 0.375rem;
  border-radius: 0.25rem;
  font-size: 0.65rem;
  font-weight: 500;
}

.urgency-badge.critical {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.urgency-badge.high {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.urgency-badge.medium {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
}

.urgency-badge.low {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
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

/* 社交媒体样式 */
.social-media-content {
  font-size: 0.875rem;
}

.loading-state, .error-state, .empty-state {
  text-align: center;
  padding: 1rem;
  color: #94a3b8;
  font-size: 0.875rem;
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

/* 移动端响应式 */
@media (max-width: 768px) {
  .data-panel {
    top: 0;
    bottom: 0;
    right: 0;
    width: 100vw;
    max-width: 100vw;
    border-radius: 0;
    z-index: 1040;
  }
  
  .data-panel.panel-open {
    z-index: 1060;
  }
  
  .right-panel {
    transform: translateX(100%);
  }
  
  .right-panel.panel-open {
    transform: translateX(0);
  }
  
  /* 切换按钮 - 移动端紧凑 */
  .right-toggle {
    top: 15rem;
    left: -1.5rem;
    padding: 0.375rem 0.25rem;
    background: rgba(15, 23, 42, 0.98);
    border: 1px solid rgba(16, 185, 129, 0.6);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.3);
    z-index: 10;
    transform: none;
    position: absolute;
  }
  
  /* 面板打开时，按钮移到内部 */
  .right-panel.panel-open .right-toggle {
    left: 0.5rem;
    border-radius: 0.375rem;
  }
  
  .panel-toggle:hover {
    background: rgba(16, 185, 129, 0.3);
    border-color: rgba(16, 185, 129, 0.8);
  }
  
  .toggle-icon {
    font-size: 0.875rem;
  }
  
  .toggle-text {
    font-size: 0.625rem;
    font-weight: 500;
  }
  
  .panel-header {
    padding: 1rem;
  }
  
  .panel-title {
    font-size: 1rem;
  }
  
  .panel-subtitle {
    font-size: 0.75rem;
  }
  
  .panel-body {
    padding: 1rem;
  }
  
  .panel-content {
    position: relative;
    z-index: 1;
  }
}
</style>
