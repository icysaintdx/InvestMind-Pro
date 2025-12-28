<template>
  <div v-if="isOpen" class="modal-overlay" @click.self="close">
    <div class="modal-container">
      <!-- 头部 -->
      <div class="modal-header">
        <h2 class="modal-title">
          <span class="icon">🔥</span>
          热榜
        </h2>
        <button @click="close" class="close-btn">✕</button>
      </div>

      <!-- 标签页 -->
      <div class="tabs">
        <button
          v-for="tab in tabs"
          :key="tab.id"
          :class="['tab-btn', { active: activeTab === tab.id }]"
          @click="activeTab = tab.id"
        >
          {{ tab.name }}
          <span v-if="getTabCount(tab.id)" class="tab-badge">{{ getTabCount(tab.id) }}</span>
        </button>
      </div>

      <!-- 内容区 -->
      <div class="modal-body">
        <div v-if="loading" class="loading-state">
          <div class="spinner"></div>
          <p>加载中...</p>
        </div>

        <div v-else-if="error" class="error-state">
          <p>❌ {{ error }}</p>
          <button @click="loadAllData" class="retry-btn">重试</button>
        </div>

        <div v-else class="content">
          <!-- 微博股票热议 -->
          <div v-show="activeTab === 'weibo'" class="rank-list">
            <div v-if="weiboStockHot.length === 0" class="empty-state">暂无数据</div>
            <div
              v-for="(item, index) in weiboStockHot"
              :key="index"
              class="rank-item"
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

          <!-- 百度热搜 -->
          <div v-show="activeTab === 'baidu'" class="rank-list">
            <div v-if="baiduHotSearch.length === 0" class="empty-state">暂无数据</div>
            <div
              v-for="(item, index) in baiduHotSearch"
              :key="index"
              class="rank-item"
              :class="getRateClass(parseFloat(item['涨跌幅'] || '0'))"
            >
              <span class="rank">{{ index + 1 }}</span>
              <span class="name">{{ item['名称/代码'] || item.name }}</span>
              <span class="rate">{{ item['涨跌幅'] || '-' }}</span>
              <span class="heat">🔥{{ formatNumber(item['综合热度'] || 0) }}</span>
            </div>
          </div>

          <!-- 雪球热度 -->
          <div v-show="activeTab === 'xueqiu'" class="rank-list">
            <div v-if="xueqiuHot.length === 0" class="empty-state">
              <span class="spinner-small"></span>
              <p>加载中...</p>
            </div>
            <div
              v-for="(item, index) in xueqiuHot"
              :key="index"
              class="rank-item"
            >
              <span class="rank">{{ index + 1 }}</span>
              <span class="name">
                {{ item['股票简称'] || item['股票名称'] || item.name }}
                <span class="code" v-if="item['股票代码'] || item.code">({{ item['股票代码'] || item.code }})</span>
              </span>
              <span class="value">¥{{ item['最新价'] || item.value || '-' }}</span>
            </div>
          </div>

          <!-- 东财热度 -->
          <div v-show="activeTab === 'eastmoney'" class="rank-list">
            <div v-if="eastmoneyHot.length === 0" class="empty-state">暂无数据</div>
            <div
              v-for="(item, index) in eastmoneyHot"
              :key="index"
              class="rank-item"
            >
              <span class="rank">{{ index + 1 }}</span>
              <span class="name">
                {{ item['股票名称'] || item.name }}
                <span class="code" v-if="item['代码'] || item.code">({{ item['代码'] || item.code }})</span>
              </span>
              <span class="value">¥{{ item['最新价'] || item.value || '-' }}</span>
            </div>
          </div>

          <!-- 个股人气榜 -->
          <div v-show="activeTab === 'popularity'" class="rank-list">
            <div v-if="popularityRank.length === 0" class="empty-state">暂无数据</div>
            <div
              v-for="(item, index) in popularityRank"
              :key="index"
              class="rank-item"
            >
              <span class="rank">{{ index + 1 }}</span>
              <span class="name">
                {{ item['股票名称'] || item.name }}
                <span class="code" v-if="item['代码'] || item.code">({{ item['代码'] || item.code }})</span>
              </span>
              <span class="popularity">#{{ item['当前排名'] || item.rank || '-' }}</span>
            </div>
          </div>

          <!-- 所有榜单 -->
          <div v-show="activeTab === 'all'" class="all-ranks">
            <div class="rank-section">
              <h3 class="section-title">🔥 微博热议 (Top 10)</h3>
              <div class="rank-list compact">
                <div
                  v-for="(item, index) in weiboStockHot.slice(0, 10)"
                  :key="index"
                  class="rank-item"
                  :class="getRateClass(item.rate)"
                >
                  <span class="rank">{{ index + 1 }}</span>
                  <span class="name">{{ item.name }}</span>
                  <span class="rate">{{ formatRate(item.rate) }}</span>
                </div>
              </div>
            </div>

            <div class="rank-section">
              <h3 class="section-title">🔍 百度热搜 (Top 10)</h3>
              <div class="rank-list compact">
                <div
                  v-for="(item, index) in baiduHotSearch.slice(0, 10)"
                  :key="index"
                  class="rank-item"
                >
                  <span class="rank">{{ index + 1 }}</span>
                  <span class="name">{{ item['名称/代码'] || item.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部 -->
      <div class="modal-footer">
        <button @click="loadAllData" class="refresh-btn" :disabled="loading">
          <span v-if="!loading">🔄 刷新</span>
          <span v-else>加载中...</span>
        </button>
        <span class="update-time">更新时间: {{ updateTime }}</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, watch } from 'vue'
import axios from 'axios'
import API_BASE_URL from '@/config/api.js'

export default {
  name: 'HotRankModal',
  props: {
    isOpen: {
      type: Boolean,
      default: false
    }
  },
  emits: ['close'],
  setup(props, { emit }) {
    const activeTab = ref('all')
    const loading = ref(false)
    const error = ref(null)
    const updateTime = ref('')

    // 数据
    const weiboStockHot = ref([])
    const baiduHotSearch = ref([])
    const xueqiuHot = ref([])
    const eastmoneyHot = ref([])
    const popularityRank = ref([])

    const tabs = [
      { id: 'all', name: '所有' },
      { id: 'weibo', name: '微博热议' },
      { id: 'baidu', name: '百度热搜' },
      { id: 'xueqiu', name: '雪球热度' },
      { id: 'eastmoney', name: '东财热度' },
      { id: 'popularity', name: '人气榜' }
    ]

    const getTabCount = (tabId) => {
      const counts = {
        weibo: weiboStockHot.value.length,
        baidu: baiduHotSearch.value.length,
        xueqiu: xueqiuHot.value.length,
        eastmoney: eastmoneyHot.value.length,
        popularity: popularityRank.value.length
      }
      return counts[tabId] || 0
    }

    const loadAllData = async () => {
      loading.value = true
      error.value = null

      try {
        // 先加载快速数据
        const response = await axios.get(`${API_BASE_URL}/api/akshare/hot-rank/all`)
        const data = response.data.data

        weiboStockHot.value = data.weibo_stock_hot || []
        baiduHotSearch.value = data.baidu_hot_search || []
        eastmoneyHot.value = data.eastmoney_hot_rank || []
        popularityRank.value = data.popularity_rank || []
        
        // 雪球热度先设置为空，页面可以立即使用
        xueqiuHot.value = data.xueqiu_hot || []

        updateTime.value = new Date().toLocaleTimeString('zh-CN')
        loading.value = false
        
        // 如果雪球数据为空，异步加载（不阻塞界面）
        if (!xueqiuHot.value || xueqiuHot.value.length === 0) {
          loadXueqiuData()
        }
      } catch (err) {
        error.value = '加载失败: ' + (err.message || '未知错误')
        console.error('加载热榜数据失败:', err)
        loading.value = false
      }
    }
    
    // 异步加载雪球数据（静默加载）
    const loadXueqiuData = async () => {
      try {
        const response = await axios.get(`${API_BASE_URL}/api/akshare/hot-rank/xueqiu`)
        if (response.data.success) {
          xueqiuHot.value = response.data.data || []
          console.log('✅ 雪球热度加载完成:', xueqiuHot.value.length, '条')
        }
      } catch (err) {
        console.warn('⚠️ 雪球热度加载失败:', err)
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
    
    const formatNumber = (num) => {
      if (!num) return '0'
      const n = parseInt(num)
      if (n >= 10000) {
        return (n / 10000).toFixed(1) + '万'
      }
      return n.toString()
    }

    const close = () => {
      emit('close')
    }

    // 监听打开状态
    watch(() => props.isOpen, (newVal) => {
      if (newVal) {
        loadAllData()
      }
    })

    return {
      activeTab,
      loading,
      error,
      updateTime,
      tabs,
      weiboStockHot,
      baiduHotSearch,
      xueqiuHot,
      eastmoneyHot,
      popularityRank,
      getTabCount,
      loadAllData,
      formatRate,
      getRateClass,
      formatNumber,
      close
    }
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.75);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.modal-container {
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border-radius: 16px;
  width: 90%;
  max-width: 900px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(59, 130, 246, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 24px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.modal-title {
  font-size: 24px;
  font-weight: bold;
  color: #fff;
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
}

.icon {
  font-size: 28px;
}

.close-btn {
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 8px;
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ef4444;
  font-size: 20px;
  cursor: pointer;
  transition: all 0.2s;
}

.close-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  transform: scale(1.1);
}

.tabs {
  display: flex;
  gap: 8px;
  padding: 16px 24px;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  overflow-x: auto;
}

.tab-btn {
  padding: 8px 16px;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 8px;
  color: #94a3b8;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 14px;
}

.tab-btn:hover {
  background: rgba(30, 41, 59, 0.8);
  border-color: rgba(59, 130, 246, 0.3);
}

.tab-btn.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: #60a5fa;
}

.tab-badge {
  background: rgba(59, 130, 246, 0.3);
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: 600;
}

.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.loading-state,
.error-state {
  text-align: center;
  padding: 60px 20px;
  color: #94a3b8;
}

.spinner {
  width: 48px;
  height: 48px;
  border: 4px solid rgba(59, 130, 246, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.retry-btn {
  margin-top: 16px;
  padding: 10px 20px;
  background: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}

.retry-btn:hover {
  background: #2563eb;
  transform: translateY(-2px);
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rank-list.compact {
  gap: 6px;
}

.rank-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  transition: all 0.2s;
}

.rank-list.compact .rank-item {
  padding: 8px;
}

.rank-item:hover {
  background: rgba(30, 41, 59, 0.8);
  transform: translateX(4px);
}

.rank {
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(59, 130, 246, 0.2);
  border-radius: 6px;
  color: #3b82f6;
  font-weight: bold;
  font-size: 14px;
  flex-shrink: 0;
}

.rank-list.compact .rank {
  width: 24px;
  height: 24px;
  font-size: 12px;
}

.name {
  flex: 1;
  color: #e2e8f0;
  font-weight: 500;
  font-size: 15px;
}

.name .code {
  color: #94a3b8;
  font-size: 13px;
  font-weight: 400;
  margin-left: 4px;
}

.rank-list.compact .name {
  font-size: 13px;
}

.rate,
.heat,
.value,
.change,
.popularity {
  font-weight: 600;
  font-size: 14px;
  flex-shrink: 0;
}

.rank-item.positive .rate {
  color: #10b981;
}

.rank-item.negative .rate {
  color: #ef4444;
}

.rank-item.neutral .rate {
  color: #94a3b8;
}

.heat {
  color: #f59e0b;
}

.value {
  color: #8b5cf6;
}

.popularity {
  color: #f59e0b;
}

.change.up {
  color: #10b981;
}

.change.down {
  color: #ef4444;
}

.empty-state {
  text-align: center;
  padding: 60px 20px;
  color: #64748b;
  font-size: 15px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
}

.empty-state .spinner-small {
  width: 24px;
  height: 24px;
  border: 3px solid rgba(59, 130, 246, 0.1);
  border-top-color: #3b82f6;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.all-ranks {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 24px;
}

.rank-section {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 12px;
  padding: 16px;
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 12px;
}

.modal-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.refresh-btn {
  padding: 8px 16px;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 8px;
  color: #60a5fa;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
}

.refresh-btn:hover:not(:disabled) {
  background: rgba(59, 130, 246, 0.3);
  transform: translateY(-2px);
}

.refresh-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.update-time {
  font-size: 13px;
  color: #64748b;
}

/* 滚动条美化 */
.modal-body::-webkit-scrollbar {
  width: 8px;
}

.modal-body::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 10px;
}

.modal-body::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-radius: 10px;
  transition: background 0.3s ease;
}

.modal-body::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
}

.tabs-container::-webkit-scrollbar {
  height: 6px;
}

.tabs-container::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 10px;
}

.tabs-container::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  border-radius: 10px;
  transition: background 0.3s ease;
}

.tabs-container::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
}
</style>
