<template>
  <div class="unified-news-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-icon">📰</span>
          统一新闻中心
        </h1>
        <p class="page-subtitle">整合多源财经新闻，支持多维度分类与情绪分析</p>
      </div>
      <div class="header-actions">
        <button @click="refreshAllNews" class="refresh-btn" :disabled="loading">
          <span class="btn-icon" :class="{ 'spinning': loading }">🔄</span>
          {{ loading ? '刷新中...' : '刷新全部' }}
        </button>
        <button @click="showSourceConfig = true" class="config-btn">
          <span class="btn-icon">⚙️</span>
          数据源配置
        </button>
      </div>
    </div>

    <!-- 统计概览 -->
    <div class="stats-overview">
      <div class="stat-card">
        <div class="stat-icon">📊</div>
        <div class="stat-content">
          <div class="stat-value">{{ statistics.total_count || 0 }}</div>
          <div class="stat-label">新闻总数</div>
        </div>
      </div>
      <div class="stat-card positive">
        <div class="stat-icon">📈</div>
        <div class="stat-content">
          <div class="stat-value">{{ statistics.positive_count || 0 }}</div>
          <div class="stat-label">积极新闻</div>
        </div>
      </div>
      <div class="stat-card negative">
        <div class="stat-icon">📉</div>
        <div class="stat-content">
          <div class="stat-value">{{ statistics.negative_count || 0 }}</div>
          <div class="stat-label">消极新闻</div>
        </div>
      </div>
      <div class="stat-card neutral">
        <div class="stat-icon">➖</div>
        <div class="stat-content">
          <div class="stat-value">{{ statistics.neutral_count || 0 }}</div>
          <div class="stat-label">中性新闻</div>
        </div>
      </div>
      <div class="stat-card sources">
        <div class="stat-icon">🔗</div>
        <div class="stat-content">
          <div class="stat-value">{{ Object.keys(sourceStatus).length }}</div>
          <div class="stat-label">数据源</div>
        </div>
      </div>
    </div>

    <!-- 筛选器 -->
    <div class="filter-section">
      <div class="filter-row">
        <div class="filter-group">
          <label class="filter-label">市场</label>
          <div class="filter-buttons">
            <button 
              v-for="market in markets" 
              :key="market.value"
              @click="filters.market = market.value"
              :class="['filter-btn', { active: filters.market === market.value }]"
            >
              {{ market.label }}
            </button>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">类型</label>
          <div class="filter-buttons">
            <button 
              v-for="type in newsTypes" 
              :key="type.value"
              @click="filters.news_type = type.value"
              :class="['filter-btn', { active: filters.news_type === type.value }]"
            >
              {{ type.label }}
            </button>
          </div>
        </div>

        <div class="filter-group">
          <label class="filter-label">情绪</label>
          <div class="filter-buttons">
            <button 
              v-for="sentiment in sentiments" 
              :key="sentiment.value"
              @click="filters.sentiment = sentiment.value"
              :class="['filter-btn', sentiment.class, { active: filters.sentiment === sentiment.value }]"
            >
              {{ sentiment.label }}
            </button>
          </div>
        </div>
      </div>

      <div class="filter-row">
        <div class="filter-group">
          <label class="filter-label">数据源</label>
          <div class="filter-buttons source-buttons">
            <button 
              @click="filters.source = null"
              :class="['filter-btn', { active: !filters.source }]"
            >
              全部 ({{ statistics.total_count || 0 }})
            </button>
            <button 
              v-for="source in availableSources" 
              :key="source.id"
              @click="filters.source = source.id"
              :class="['filter-btn', { active: filters.source === source.id }]"
            >
              <span class="source-status" :class="source.status"></span>
              {{ source.name }} ({{ getSourceCount(source.name) }})
            </button>
          </div>
        </div>

        <div class="filter-group search-group">
          <label class="filter-label">搜索</label>
          <div class="search-input-wrapper">
            <input 
              v-model="filters.keyword"
              type="text"
              placeholder="输入关键词搜索..."
              class="search-input"
              @keyup.enter="searchNews"
            />
            <button @click="searchNews" class="search-btn">🔍</button>
          </div>
        </div>

        <div class="filter-group stock-group">
          <label class="filter-label">股票</label>
          <div class="search-input-wrapper">
            <input 
              v-model="filters.stock_code"
              type="text"
              placeholder="输入股票代码..."
              class="search-input"
              @keyup.enter="fetchStockNews"
            />
            <button @click="fetchStockNews" class="search-btn">📈</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 新闻列表 -->
    <div class="news-content">
      <div v-if="loading" class="loading-state">
        <div class="loading-spinner"></div>
        <p>正在加载新闻数据...</p>
      </div>

      <div v-else-if="filteredNews.length === 0" class="empty-state">
        <div class="empty-icon">📭</div>
        <h3>暂无新闻数据</h3>
        <p>请尝试调整筛选条件或刷新数据</p>
        <button @click="refreshAllNews" class="refresh-btn">
          <span class="btn-icon">🔄</span>
          刷新数据
        </button>
      </div>

      <div v-else class="news-list">
        <div 
          v-for="news in paginatedNews" 
          :key="news.id"
          class="news-card"
          :class="getSentimentClass(news.sentiment)"
          @click="showNewsDetail(news)"
        >
          <div class="news-header">
            <div class="news-source">
              <span class="source-icon">{{ getSourceIcon(news.source) }}</span>
              <span class="source-name">{{ news.source_name || news.source }}</span>
            </div>
            <div class="news-time">{{ formatTime(news.publish_time) }}</div>
          </div>
          
          <h3 class="news-title">{{ news.title }}</h3>
          
          <p class="news-summary" v-if="news.summary">{{ news.summary }}</p>
          
          <div class="news-footer">
            <div class="news-tags">
              <span class="tag market-tag" v-if="news.market">{{ getMarketLabel(news.market) }}</span>
              <span class="tag type-tag" v-if="news.news_type">{{ getTypeLabel(news.news_type) }}</span>
              <span class="tag sentiment-tag" :class="getSentimentClass(news.sentiment)">
                {{ getSentimentLabel(news.sentiment) }}
              </span>
              <span class="tag stock-tag" v-for="stock in (news.related_stocks || []).slice(0, 3)" :key="stock">
                {{ stock }}
              </span>
            </div>
            <div class="news-actions">
              <button @click.stop="openNewsUrl(news.url)" class="action-btn" v-if="news.url">🔗</button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="filteredNews.length > pageSize" class="pagination">
        <button @click="currentPage = 1" :disabled="currentPage === 1" class="page-btn">首页</button>
        <button @click="currentPage--" :disabled="currentPage === 1" class="page-btn">上一页</button>
        <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 页</span>
        <button @click="currentPage++" :disabled="currentPage === totalPages" class="page-btn">下一页</button>
        <button @click="currentPage = totalPages" :disabled="currentPage === totalPages" class="page-btn">末页</button>
      </div>
    </div>

    <!-- 新闻详情模态框 -->
    <div v-if="selectedNews" class="modal-overlay" @click.self="selectedNews = null">
      <div class="news-detail-modal">
        <button @click="selectedNews = null" class="modal-close-btn">×</button>
        
        <div class="detail-header">
          <div class="detail-source">
            <span class="source-icon">{{ getSourceIcon(selectedNews.source) }}</span>
            <span class="source-name">{{ selectedNews.source_name || selectedNews.source }}</span>
          </div>
          <div class="detail-time">{{ formatTime(selectedNews.publish_time) }}</div>
        </div>
        
        <h2 class="detail-title">{{ selectedNews.title }}</h2>
        
        <div class="detail-tags">
          <span class="tag market-tag" v-if="selectedNews.market">{{ getMarketLabel(selectedNews.market) }}</span>
          <span class="tag type-tag" v-if="selectedNews.news_type">{{ getTypeLabel(selectedNews.news_type) }}</span>
          <span class="tag sentiment-tag" :class="getSentimentClass(selectedNews.sentiment)">
            {{ getSentimentLabel(selectedNews.sentiment) }} ({{ ((selectedNews.sentiment_score || 0) * 100).toFixed(0) }}%)
          </span>
        </div>
        
        <div class="detail-content">
          <p v-if="selectedNews.summary" class="detail-summary">{{ selectedNews.summary }}</p>
          <div v-if="selectedNews.content" class="detail-body" v-html="selectedNews.content"></div>
        </div>
        
        <div class="detail-stocks" v-if="selectedNews.related_stocks && selectedNews.related_stocks.length">
          <h4>相关股票</h4>
          <div class="stock-list">
            <span class="stock-tag" v-for="stock in selectedNews.related_stocks" :key="stock">{{ stock }}</span>
          </div>
        </div>
        
        <div class="detail-actions">
          <button @click="openNewsUrl(selectedNews.url)" class="action-btn primary" v-if="selectedNews.url">
            🔗 查看原文
          </button>
        </div>
      </div>
    </div>

    <!-- 数据源配置模态框 -->
    <div v-if="showSourceConfig" class="modal-overlay" @click.self="showSourceConfig = false">
      <div class="source-config-modal">
        <button @click="showSourceConfig = false" class="modal-close-btn">×</button>
        
        <h2 class="modal-title">数据源配置</h2>
        
        <div class="source-list">
          <div v-for="source in allSources" :key="source.id" class="source-item">
            <div class="source-info">
              <span class="source-icon">{{ getSourceIcon(source.id) }}</span>
              <div class="source-details">
                <span class="source-name">{{ source.name }}</span>
                <span class="source-desc">{{ source.description }}</span>
              </div>
            </div>
            <div class="source-status-info">
              <span class="news-count-badge">{{ getSourceCount(source.name) }} 条</span>
              <span class="status-badge" :class="source.status">
                {{ source.status === 'healthy' ? '正常' : source.status === 'degraded' ? '降级' : '离线' }}
              </span>
              <span class="priority-badge">优先级: {{ source.priority }}</span>
            </div>
          </div>
        </div>
        
        <div class="config-actions">
          <button @click="testAllSources" class="test-btn" :disabled="testingSource">
            {{ testingSource ? '测试中...' : '测试所有数据源' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, computed, onMounted } from 'vue'
import API_BASE_URL from '../config/api.js'

export default defineComponent({
  name: 'UnifiedNewsView',
  setup() {
    const loading = ref(false)
    const newsList = ref([])
    const statistics = ref({})
    const sourceStatus = ref({})
    const selectedNews = ref(null)
    const showSourceConfig = ref(false)
    const testingSource = ref(false)
    const currentPage = ref(1)
    const pageSize = ref(20)

    const filters = reactive({
      market: null,
      news_type: null,
      sentiment: null,
      source: null,
      keyword: '',
      stock_code: ''
    })

    const markets = [
      { value: null, label: '全部' },
      { value: 'A股', label: 'A股' },
      { value: '港股', label: '港股' },
      { value: '美股', label: '美股' },
      { value: '全球', label: '全球' }
    ]

    const newsTypes = [
      { value: null, label: '全部' },
      { value: '公司新闻', label: '公司' },
      { value: '行业新闻', label: '行业' },
      { value: '宏观经济', label: '宏观' },
      { value: '政策法规', label: '政策' },
      { value: '市场动态', label: '市场' },
      { value: '快讯', label: '快讯' }
    ]

    const sentiments = [
      { value: null, label: '全部', class: '' },
      { value: 'positive', label: '积极', class: 'positive' },
      { value: 'neutral', label: '中性', class: 'neutral' },
      { value: 'negative', label: '消极', class: 'negative' }
    ]

    const allSources = ref([
      { id: 'akshare_eastmoney', name: '东方财富', description: 'AKShare东方财富新闻', priority: 1, status: 'unknown' },
      { id: 'akshare_futu', name: '富途', description: 'AKShare富途全球资讯', priority: 2, status: 'unknown' },
      { id: 'akshare_ths', name: '同花顺', description: 'AKShare同花顺全球资讯', priority: 3, status: 'unknown' },
      { id: 'akshare_sina', name: '新浪财经', description: 'AKShare新浪财经', priority: 4, status: 'unknown' },
      { id: 'akshare_cctv', name: '央视财经', description: 'AKShare央视财经', priority: 5, status: 'unknown' },
      { id: 'akshare_cls', name: '财联社', description: 'AKShare财联社快讯', priority: 6, status: 'unknown' },
      { id: 'wencai', name: '问财', description: '同花顺问财新闻', priority: 7, status: 'unknown' }
    ])

    const availableSources = computed(() => {
      return allSources.value.filter(s => s.status === 'healthy' || s.status === 'degraded' || s.status === 'unknown')
    })

    const filteredNews = computed(() => {
      let result = [...newsList.value]
      if (filters.market) result = result.filter(n => n.market === filters.market)
      if (filters.news_type) result = result.filter(n => n.news_type === filters.news_type)
      if (filters.sentiment) result = result.filter(n => n.sentiment === filters.sentiment)
      if (filters.source) result = result.filter(n => n.source === filters.source || n.source_name === getSourceNameById(filters.source))
      if (filters.keyword) {
        const keyword = filters.keyword.toLowerCase()
        result = result.filter(n => 
          (n.title && n.title.toLowerCase().includes(keyword)) ||
          (n.summary && n.summary.toLowerCase().includes(keyword))
        )
      }
      return result
    })

    const totalPages = computed(() => Math.ceil(filteredNews.value.length / pageSize.value))

    const paginatedNews = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      return filteredNews.value.slice(start, start + pageSize.value)
    })

    // 根据数据源ID获取数据源名称
    const getSourceNameById = (sourceId) => {
      const source = allSources.value.find(s => s.id === sourceId)
      return source ? source.name : sourceId
    }

    // 获取数据源的新闻数量
    const getSourceCount = (sourceName) => {
      const sourceCounts = statistics.value.source_counts || {}
      return sourceCounts[sourceName] || 0
    }

    const fetchNews = async () => {
      loading.value = true
      try {
        const params = new URLSearchParams()
        if (filters.market) params.append('market', filters.market)
        if (filters.news_type) params.append('news_type', filters.news_type)
        if (filters.sentiment) params.append('sentiment', filters.sentiment)
        if (filters.source) params.append('source', filters.source)
        params.append('limit', '200')

        const response = await fetch(`${API_BASE_URL}/api/unified-news/list?${params}`)
        const data = await response.json()
        if (data.success) {
          newsList.value = data.data || []
          statistics.value = data.statistics || {}
        }
      } catch (error) {
        console.error('获取新闻失败:', error)
      } finally {
        loading.value = false
      }
    }

    const fetchStockNews = async () => {
      if (!filters.stock_code) return
      loading.value = true
      try {
        const response = await fetch(`${API_BASE_URL}/api/unified-news/stock/${filters.stock_code}`)
        const data = await response.json()
        if (data.success) {
          newsList.value = data.data || []
          statistics.value = data.statistics || {}
        }
      } catch (error) {
        console.error('获取股票新闻失败:', error)
      } finally {
        loading.value = false
      }
    }

    const searchNews = async () => {
      if (!filters.keyword) {
        fetchNews()
        return
      }
      loading.value = true
      try {
        const response = await fetch(`${API_BASE_URL}/api/unified-news/search?keyword=${encodeURIComponent(filters.keyword)}`)
        const data = await response.json()
        if (data.success) newsList.value = data.data || []
      } catch (error) {
        console.error('搜索新闻失败:', error)
      } finally {
        loading.value = false
      }
    }

    const refreshAllNews = async () => {
      loading.value = true
      try {
        await fetch(`${API_BASE_URL}/api/unified-news/refresh`, { method: 'POST' })
        await fetchNews()
        await fetchStatistics()
        await fetchSourceStatus()
      } catch (error) {
        console.error('刷新新闻失败:', error)
      } finally {
        loading.value = false
      }
    }

    const fetchStatistics = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/unified-news/statistics`)
        const data = await response.json()
        if (data.success) statistics.value = data.data || data
      } catch (error) {
        console.error('获取统计失败:', error)
      }
    }

    const fetchSourceStatus = async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/api/unified-news/sources`)
        const data = await response.json()
        if (data.success) {
          sourceStatus.value = data.data || {}
          allSources.value.forEach(source => {
            const status = sourceStatus.value[source.id]
            if (status) source.status = status.status || 'unknown'
          })
        }
      } catch (error) {
        console.error('获取数据源状态失败:', error)
      }
    }

    const testAllSources = async () => {
      testingSource.value = true
      try {
        const response = await fetch(`${API_BASE_URL}/api/unified-news/health`)
        const data = await response.json()
        if (data.success) {
          Object.entries(data.sources || {}).forEach(([id, info]) => {
            const source = allSources.value.find(s => s.id === id)
            if (source) source.status = info.status
          })
        }
      } catch (error) {
        console.error('测试数据源失败:', error)
      } finally {
        testingSource.value = false
      }
    }

    const showNewsDetail = (news) => { selectedNews.value = news }
    const openNewsUrl = (url) => { if (url) window.open(url, '_blank') }

    const formatTime = (time) => {
      if (!time) return ''
      const date = new Date(time)
      const now = new Date()
      const diff = now - date
      if (diff < 60000) return '刚刚'
      if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
      if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
      if (diff < 604800000) return `${Math.floor(diff / 86400000)}天前`
      return date.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
    }

    const getSourceIcon = (source) => {
      const icons = {
        'akshare_eastmoney': '📊', 'akshare_cls': '⚡', 'akshare_sina': '📰',
        'akshare_cctv': '📺', 'akshare_futu': '🌐', 'akshare_ths': '📈',
        'wencai': '🔍', 'tushare': '📈', 'finnhub': '🌐', 'default': '📄'
      }
      return icons[source] || icons.default
    }

    const getMarketLabel = (market) => market || '未知'
    const getTypeLabel = (type) => type || '其他'
    const getSentimentLabel = (sentiment) => ({ 'positive': '积极', 'neutral': '中性', 'negative': '消极' }[sentiment] || '未知')
    const getSentimentClass = (sentiment) => sentiment || 'neutral'

    onMounted(() => {
      fetchNews()
      fetchStatistics()
      fetchSourceStatus()
    })

    return {
      loading, newsList, statistics, sourceStatus, selectedNews, showSourceConfig, testingSource,
      currentPage, pageSize, filters, markets, newsTypes, sentiments, allSources, availableSources,
      filteredNews, totalPages, paginatedNews, fetchNews, fetchStockNews, searchNews, refreshAllNews,
      testAllSources, showNewsDetail, openNewsUrl, formatTime, getSourceIcon, getMarketLabel,
      getTypeLabel, getSentimentLabel, getSentimentClass, getSourceCount, getSourceNameById
    }
  }
})
</script>

<style scoped src="./UnifiedNewsView-styles.css"></style>