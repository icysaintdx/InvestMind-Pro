<template>
  <div class="longhubang-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>龙虎榜分析</h1>
      <p class="subtitle">机构席位、游资动向、主力资金追踪</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="date-selector">
        <label>选择日期：</label>
        <input type="date" v-model="selectedDate" @change="fetchDailyData" />
      </div>
      <div class="quick-actions">
        <button class="btn btn-primary" @click="fetchDailyData" :disabled="loading">
          <span v-if="loading">加载中...</span>
          <span v-else>刷新数据</span>
        </button>
        <button class="btn btn-secondary" @click="fetchRecentData">
          近5日汇总
        </button>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards" v-if="summary">
      <div class="stat-card">
        <div class="stat-value">{{ summary.total_stocks || 0 }}</div>
        <div class="stat-label">上榜股票数</div>
      </div>
      <div class="stat-card buy">
        <div class="stat-value">{{ formatMoney(summary.total_buy) }}</div>
        <div class="stat-label">机构买入总额</div>
      </div>
      <div class="stat-card sell">
        <div class="stat-value">{{ formatMoney(summary.total_sell) }}</div>
        <div class="stat-label">机构卖出总额</div>
      </div>
      <div class="stat-card" :class="summary.net_buy > 0 ? 'buy' : 'sell'">
        <div class="stat-value">{{ formatMoney(summary.net_buy) }}</div>
        <div class="stat-label">净买入额</div>
      </div>
    </div>

    <!-- 标签页 -->
    <div class="tabs">
      <button
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-btn', { active: activeTab === tab.key }]"
        @click="activeTab = tab.key"
      >
        {{ tab.label }}
      </button>
    </div>

    <!-- 龙虎榜列表 -->
    <div class="content-section" v-show="activeTab === 'daily'">
      <div class="section-header">
        <h2>今日龙虎榜</h2>
        <span class="data-time">数据时间: {{ dataTime }}</span>
      </div>

      <div class="table-container" v-if="dailyData.length > 0">
        <table class="data-table">
          <thead>
            <tr>
              <th>股票代码</th>
              <th>股票名称</th>
              <th>收盘价</th>
              <th>涨跌幅</th>
              <th>上榜原因</th>
              <th>买入额(万)</th>
              <th>卖出额(万)</th>
              <th>净买入(万)</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in dailyData" :key="item.stock_code || item.code">
              <td class="code">{{ item.stock_code || item.code }}</td>
              <td class="name">{{ item.stock_name || item.name }}</td>
              <td>{{ item.close_price?.toFixed(2) || '-' }}</td>
              <td :class="item.change_pct > 0 ? 'up' : 'down'">
                {{ item.change_pct?.toFixed(2) || '-' }}%
              </td>
              <td class="reason">{{ item.reason || '-' }}</td>
              <td class="buy">{{ formatNumber(item.lhb_buy_amount || item.buy_amount) }}</td>
              <td class="sell">{{ formatNumber(item.lhb_sell_amount || item.sell_amount) }}</td>
              <td :class="(item.lhb_net_amount || item.net_amount) > 0 ? 'buy' : 'sell'">
                {{ formatNumber(item.lhb_net_amount || item.net_amount) }}
              </td>
              <td>
                <button class="btn-small" @click="viewDetail(item.stock_code || item.code)">详情</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="empty-state" v-else-if="!loading">
        <p>暂无龙虎榜数据</p>
      </div>
    </div>

    <!-- 机构统计 -->
    <div class="content-section" v-show="activeTab === 'institution'">
      <div class="section-header">
        <h2>机构席位统计</h2>
      </div>

      <div class="table-container" v-if="institutionData.length > 0">
        <table class="data-table">
          <thead>
            <tr>
              <th>机构名称</th>
              <th>买入次数</th>
              <th>卖出次数</th>
              <th>买入总额(万)</th>
              <th>卖出总额(万)</th>
              <th>净买入(万)</th>
              <th>胜率</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in institutionData" :key="item.name">
              <td class="name">{{ item.name }}</td>
              <td>{{ item.buy_count || 0 }}</td>
              <td>{{ item.sell_count || 0 }}</td>
              <td class="buy">{{ formatNumber(item.buy_amount) }}</td>
              <td class="sell">{{ formatNumber(item.sell_amount) }}</td>
              <td :class="item.net_amount > 0 ? 'buy' : 'sell'">
                {{ formatNumber(item.net_amount) }}
              </td>
              <td>{{ item.win_rate?.toFixed(1) || '-' }}%</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="empty-state" v-else-if="!loading">
        <p>暂无机构统计数据</p>
      </div>
    </div>

    <!-- 营业部统计 -->
    <div class="content-section" v-show="activeTab === 'traders'">
      <div class="section-header">
        <h2>知名游资统计</h2>
      </div>

      <div class="table-container" v-if="tradersData.length > 0">
        <table class="data-table">
          <thead>
            <tr>
              <th>营业部名称</th>
              <th>上榜次数</th>
              <th>买入总额(万)</th>
              <th>卖出总额(万)</th>
              <th>净买入(万)</th>
              <th>关联股票</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in tradersData" :key="item.name">
              <td class="name trader-name">{{ item.name }}</td>
              <td>{{ item.count || 0 }}</td>
              <td class="buy">{{ formatNumber(item.buy_amount) }}</td>
              <td class="sell">{{ formatNumber(item.sell_amount) }}</td>
              <td :class="item.net_amount > 0 ? 'buy' : 'sell'">
                {{ formatNumber(item.net_amount) }}
              </td>
              <td class="stocks">{{ item.stocks?.join(', ') || '-' }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="empty-state" v-else-if="!loading">
        <p>暂无营业部统计数据</p>
      </div>
    </div>

    <!-- 个股详情弹窗 -->
    <div class="modal-overlay" v-if="showDetail" @click.self="showDetail = false">
      <div class="modal-content">
        <div class="modal-header">
          <h3>{{ detailData.name }} ({{ detailData.code }}) 龙虎榜详情</h3>
          <button class="close-btn" @click="showDetail = false">&times;</button>
        </div>
        <div class="modal-body" v-if="detailData.detail">
          <div class="detail-section">
            <h4>买入席位</h4>
            <table class="detail-table">
              <thead>
                <tr>
                  <th>席位名称</th>
                  <th>买入额(万)</th>
                  <th>占比</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(seat, idx) in detailData.detail.buy_seats" :key="'buy-'+idx">
                  <td>{{ seat.name }}</td>
                  <td class="buy">{{ formatNumber(seat.amount) }}</td>
                  <td>{{ seat.ratio?.toFixed(2) }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="detail-section">
            <h4>卖出席位</h4>
            <table class="detail-table">
              <thead>
                <tr>
                  <th>席位名称</th>
                  <th>卖出额(万)</th>
                  <th>占比</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(seat, idx) in detailData.detail.sell_seats" :key="'sell-'+idx">
                  <td>{{ seat.name }}</td>
                  <td class="sell">{{ formatNumber(seat.amount) }}</td>
                  <td>{{ seat.ratio?.toFixed(2) }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="modal-body" v-else>
          <p>加载中...</p>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div class="loading-overlay" v-if="loading">
      <div class="loading-spinner"></div>
      <p class="loading-text">{{ loadingText }}</p>
      <div class="loading-progress" v-if="loadingProgress > 0">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: loadingProgress + '%' }"></div>
        </div>
        <span class="progress-text">{{ loadingProgress }}%</span>
      </div>
    </div>
  </div>
</template>

<script>
import API_BASE_URL from '@/config/api'

export default {
  name: 'LonghubangView',
  data() {
    return {
      loading: false,
      loadingText: '数据加载中...',
      loadingProgress: 0,
      selectedDate: this.getToday(),
      activeTab: 'daily',
      tabs: [
        { key: 'daily', label: '今日龙虎榜' },
        { key: 'institution', label: '机构统计' },
        { key: 'traders', label: '游资统计' }
      ],
      dailyData: [],
      institutionData: [],
      tradersData: [],
      summary: null,
      dataTime: '',
      showDetail: false,
      detailData: {}
    }
  },
  mounted() {
    this.fetchDailyData()
  },
  methods: {
    getToday() {
      const today = new Date()
      return today.toISOString().split('T')[0]
    },

    updateProgress(text, progress) {
      this.loadingText = text
      this.loadingProgress = progress
    },

    async fetchDailyData() {
      this.loading = true
      this.loadingProgress = 0
      try {
        // 步骤1: 获取龙虎榜数据
        this.updateProgress('正在获取龙虎榜数据...', 10)
        const date = this.selectedDate.replace(/-/g, '')
        const response = await fetch(`${API_BASE_URL}/api/longhubang/daily?date=${date}`)
        const result = await response.json()

        if (result.success) {
          this.dailyData = result.data || []
          this.dataTime = result.timestamp || ''
        }
        this.updateProgress('龙虎榜数据加载完成', 25)

        // 步骤2: 获取汇总数据
        this.updateProgress('正在获取汇总统计...', 40)
        await this.fetchSummary()
        this.updateProgress('汇总统计加载完成', 55)

        // 步骤3: 获取机构数据
        this.updateProgress('正在获取机构统计...', 70)
        await this.fetchInstitutionData()
        this.updateProgress('机构统计加载完成', 85)

        // 步骤4: 获取游资数据
        this.updateProgress('正在获取游资统计...', 90)
        await this.fetchTradersData()
        this.updateProgress('全部数据加载完成', 100)

      } catch (error) {
        console.error('获取龙虎榜数据失败:', error)
        this.updateProgress('加载失败: ' + error.message, 0)
      } finally {
        setTimeout(() => {
          this.loading = false
          this.loadingProgress = 0
        }, 300)
      }
    },

    async fetchRecentData() {
      this.loading = true
      this.loadingProgress = 0
      try {
        this.updateProgress('正在获取近5日龙虎榜数据...', 20)
        const response = await fetch(`${API_BASE_URL}/api/longhubang/recent?days=5`)
        const result = await response.json()

        if (result.success) {
          this.dailyData = result.data || []
          this.dataTime = '近5日汇总'
          this.updateProgress('近5日数据加载完成', 100)
        }
      } catch (error) {
        console.error('获取近期数据失败:', error)
        this.updateProgress('加载失败: ' + error.message, 0)
      } finally {
        setTimeout(() => {
          this.loading = false
          this.loadingProgress = 0
        }, 300)
      }
    },

    async fetchSummary() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/longhubang/summary`)
        const result = await response.json()

        if (result.success) {
          this.summary = result.data || {}
        }
      } catch (error) {
        console.error('获取汇总数据失败:', error)
      }
    },

    async fetchInstitutionData() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/longhubang/institution`)
        const result = await response.json()

        if (result.success) {
          this.institutionData = result.data || []
        }
      } catch (error) {
        console.error('获取机构数据失败:', error)
      }
    },

    async fetchTradersData() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/longhubang/traders`)
        const result = await response.json()

        if (result.success) {
          this.tradersData = result.data || []
        }
      } catch (error) {
        console.error('获取营业部数据失败:', error)
      }
    },

    async viewDetail(code) {
      if (!code || code === 'undefined') {
        console.error('无效的股票代码')
        return
      }
      
      this.showDetail = true
      const stockItem = this.dailyData.find(d => (d.stock_code || d.code) === code)
      this.detailData = {
        code,
        name: stockItem?.stock_name || stockItem?.name || code
      }

      try {
        const response = await fetch(`${API_BASE_URL}/api/longhubang/stock/${code}`)
        const result = await response.json()

        if (result.success) {
          this.detailData.detail = result.data || {
            buy_seats: result.buy_seats || [],
            sell_seats: result.sell_seats || []
          }
        } else {
          this.detailData.detail = { buy_seats: [], sell_seats: [] }
          console.warn('获取详情失败:', result.message)
        }
      } catch (error) {
        console.error('获取详情失败:', error)
        this.detailData.detail = { buy_seats: [], sell_seats: [] }
      }
    },

    formatNumber(num) {
      if (!num && num !== 0) return '-'
      return (num / 10000).toFixed(2)
    },

    formatMoney(num) {
      if (!num && num !== 0) return '-'
      const wan = num / 10000
      if (Math.abs(wan) >= 10000) {
        return (wan / 10000).toFixed(2) + '亿'
      }
      return wan.toFixed(2) + '万'
    }
  }
}
</script>

<style scoped>
.longhubang-view {
  padding: 20px;
  max-width: 1400px;
  margin: 0 auto;
  color: #e0e0e0;
}

.page-header {
  margin-bottom: 24px;
}

.page-header h1 {
  font-size: 28px;
  color: #fff;
  margin: 0 0 8px 0;
}

.subtitle {
  color: #888;
  margin: 0;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 16px;
  background: #1a1a2e;
  border-radius: 8px;
}

.date-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.date-selector input {
  padding: 8px 12px;
  border: 1px solid #333;
  border-radius: 4px;
  background: #0d0d1a;
  color: #fff;
}

.quick-actions {
  display: flex;
  gap: 10px;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

.btn-secondary {
  background: #2a2a4a;
  color: #fff;
  border: 1px solid #444;
}

.btn-secondary:hover {
  background: #3a3a5a;
}

.stats-cards {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.stat-card {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-card.buy {
  border-left: 4px solid #f44336;
}

.stat-card.sell {
  border-left: 4px solid #4caf50;
}

.stat-value {
  font-size: 24px;
  font-weight: bold;
  color: #fff;
  margin-bottom: 8px;
}

.stat-label {
  font-size: 14px;
  color: #888;
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 20px;
  background: #1a1a2e;
  padding: 4px;
  border-radius: 8px;
}

.tab-btn {
  flex: 1;
  padding: 12px 20px;
  border: none;
  background: transparent;
  color: #888;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s;
}

.tab-btn.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: #fff;
}

.tab-btn:hover:not(.active) {
  background: #2a2a4a;
  color: #fff;
}

.content-section {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 20px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-header h2 {
  font-size: 18px;
  color: #fff;
  margin: 0;
}

.data-time {
  font-size: 12px;
  color: #666;
}

.table-container {
  overflow-x: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 12px;
  text-align: left;
  border-bottom: 1px solid #2a2a4a;
}

.data-table th {
  background: #0d0d1a;
  color: #888;
  font-weight: 500;
  white-space: nowrap;
}

.data-table td {
  color: #e0e0e0;
}

.data-table tr:hover {
  background: #252540;
}

.code {
  font-family: monospace;
  color: #667eea;
}

.name {
  font-weight: 500;
}

.trader-name {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.reason {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.stocks {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.up, .buy {
  color: #f44336;
}

.down, .sell {
  color: #4caf50;
}

.btn-small {
  padding: 4px 12px;
  font-size: 12px;
  border: 1px solid #667eea;
  background: transparent;
  color: #667eea;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-small:hover {
  background: #667eea;
  color: #fff;
}

.empty-state {
  text-align: center;
  padding: 40px;
  color: #666;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.8);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: #1a1a2e;
  border-radius: 12px;
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #2a2a4a;
}

.modal-header h3 {
  margin: 0;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  color: #888;
  font-size: 24px;
  cursor: pointer;
}

.close-btn:hover {
  color: #fff;
}

.modal-body {
  padding: 20px;
  overflow-y: auto;
  max-height: calc(80vh - 60px);
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h4 {
  color: #888;
  margin: 0 0 12px 0;
  font-size: 14px;
}

.detail-table {
  width: 100%;
  border-collapse: collapse;
}

.detail-table th,
.detail-table td {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid #2a2a4a;
}

.detail-table th {
  color: #666;
  font-weight: 500;
}

/* 加载状态 */
.loading-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 1001;
}

.loading-spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #333;
  border-top-color: #667eea;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.loading-text {
  margin-top: 16px;
  color: #e0e0e0;
  font-size: 14px;
}

.loading-progress {
  margin-top: 16px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.progress-bar {
  width: 200px;
  height: 6px;
  background: #333;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
  border-radius: 3px;
  transition: width 0.3s ease;
}

.progress-text {
  color: #667eea;
  font-size: 12px;
  font-weight: 500;
  min-width: 40px;
}

@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }

  .action-bar {
    flex-direction: column;
    gap: 16px;
  }
}
</style>
