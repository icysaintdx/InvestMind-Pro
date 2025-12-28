<template>
  <div class="market-data-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>市场数据</h1>
      <p class="subtitle">实时行情、热点板块、涨跌排行</p>
    </div>

    <!-- 顶部统计卡片 -->
    <div class="stats-cards" v-if="overview">
      <div class="stat-card">
        <div class="stat-value">{{ overview.total_stocks || 0 }}</div>
        <div class="stat-label">股票总数</div>
      </div>
      <div class="stat-card buy">
        <div class="stat-value">{{ overview.up_count || 0 }}</div>
        <div class="stat-label">上涨家数</div>
      </div>
      <div class="stat-card sell">
        <div class="stat-value">{{ overview.down_count || 0 }}</div>
        <div class="stat-label">下跌家数</div>
      </div>
      <div class="stat-card">
        <div class="stat-value">{{ overview.flat_count || 0 }}</div>
        <div class="stat-label">平盘家数</div>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="main-content">
      <!-- 左侧面板 -->
      <div class="left-panel">
        <!-- 热点板块 -->
        <div class="content-section">
          <div class="section-header">
            <h2>热点板块</h2>
            <button class="btn-refresh" @click="fetchHotSectors" :disabled="loading.sectors">
              {{ loading.sectors ? '刷新中...' : '刷新' }}
            </button>
          </div>
          <div class="tabs">
            <button :class="['tab-btn', { active: sectorType === 'industry' }]" @click="sectorType = 'industry'; fetchHotSectors()">行业板块</button>
            <button :class="['tab-btn', { active: sectorType === 'concept' }]" @click="sectorType = 'concept'; fetchHotSectors()">概念板块</button>
          </div>
          <div class="sector-list" v-if="hotSectors.length > 0">
            <div class="sector-item" v-for="sector in hotSectors" :key="sector.name" @click="selectSector(sector)">
              <div class="sector-name">{{ sector.name }}</div>
              <div class="sector-change" :class="sector.change_pct > 0 ? 'up' : 'down'">
                {{ sector.change_pct > 0 ? '+' : '' }}{{ sector.change_pct?.toFixed(2) }}%
              </div>
            </div>
          </div>
          <div class="empty-state" v-else-if="!loading.sectors">暂无数据</div>
        </div>

        <!-- 板块成分股 -->
        <div class="content-section" v-if="selectedSector">
          <div class="section-header">
            <h2>{{ selectedSector.name }} 成分股</h2>
            <button class="btn-close" @click="selectedSector = null">&times;</button>
          </div>
          <div class="table-container" v-if="sectorStocks.length > 0">
            <table class="data-table compact">
              <thead>
                <tr>
                  <th>代码</th>
                  <th>名称</th>
                  <th>涨跌幅</th>
                  <th>现价</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="stock in sectorStocks" :key="stock.code" @click="selectStock(stock.code, stock.name)" class="clickable">
                  <td class="code">{{ stock.code }}</td>
                  <td class="name">{{ stock.name }}</td>
                  <td :class="stock.change_pct > 0 ? 'up' : 'down'">{{ stock.change_pct?.toFixed(2) }}%</td>
                  <td>{{ stock.price?.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="loading-inline" v-else-if="loading.sectorStocks">加载中...</div>
        </div>
      </div>

      <!-- 中间面板 -->
      <div class="center-panel">
        <!-- 涨跌排行标签页 -->
        <div class="content-section">
          <div class="tabs">
            <button :class="['tab-btn', { active: rankType === 'gainers' }]" @click="rankType = 'gainers'">涨幅榜</button>
            <button :class="['tab-btn', { active: rankType === 'losers' }]" @click="rankType = 'losers'">跌幅榜</button>
            <button :class="['tab-btn', { active: rankType === 'amount' }]" @click="rankType = 'amount'">成交额榜</button>
          </div>

          <!-- 涨幅榜 -->
          <div class="table-container" v-show="rankType === 'gainers'">
            <table class="data-table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>代码</th>
                  <th>名称</th>
                  <th>涨跌幅</th>
                  <th>现价</th>
                  <th>成交额</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(stock, idx) in topGainers" :key="stock.code" @click="selectStock(stock.code, stock.name)" class="clickable">
                  <td class="rank">{{ idx + 1 }}</td>
                  <td class="code">{{ stock.code }}</td>
                  <td class="name">{{ stock.name }}</td>
                  <td class="up">+{{ stock.change_pct?.toFixed(2) }}%</td>
                  <td>{{ stock.price?.toFixed(2) }}</td>
                  <td>{{ formatAmount(stock.amount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 跌幅榜 -->
          <div class="table-container" v-show="rankType === 'losers'">
            <table class="data-table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>代码</th>
                  <th>名称</th>
                  <th>涨跌幅</th>
                  <th>现价</th>
                  <th>成交额</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(stock, idx) in topLosers" :key="stock.code" @click="selectStock(stock.code, stock.name)" class="clickable">
                  <td class="rank">{{ idx + 1 }}</td>
                  <td class="code">{{ stock.code }}</td>
                  <td class="name">{{ stock.name }}</td>
                  <td class="down">{{ stock.change_pct?.toFixed(2) }}%</td>
                  <td>{{ stock.price?.toFixed(2) }}</td>
                  <td>{{ formatAmount(stock.amount) }}</td>
                </tr>
              </tbody>
            </table>
          </div>

          <!-- 成交额榜 -->
          <div class="table-container" v-show="rankType === 'amount'">
            <table class="data-table">
              <thead>
                <tr>
                  <th>排名</th>
                  <th>代码</th>
                  <th>名称</th>
                  <th>成交额</th>
                  <th>涨跌幅</th>
                  <th>现价</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(stock, idx) in topAmount" :key="stock.code" @click="selectStock(stock.code, stock.name)" class="clickable">
                  <td class="rank">{{ idx + 1 }}</td>
                  <td class="code">{{ stock.code }}</td>
                  <td class="name">{{ stock.name }}</td>
                  <td class="amount">{{ formatAmount(stock.amount) }}</td>
                  <td :class="stock.change_pct > 0 ? 'up' : 'down'">{{ stock.change_pct > 0 ? '+' : '' }}{{ stock.change_pct?.toFixed(2) }}%</td>
                  <td>{{ stock.price?.toFixed(2) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- 右侧面板 - 个股详情 -->
      <div class="right-panel" v-if="selectedStock">
        <!-- 五档盘口 -->
        <div class="content-section">
          <div class="section-header">
            <h2>{{ selectedStock.name }} ({{ selectedStock.code }})</h2>
            <button class="btn-close" @click="selectedStock = null">&times;</button>
          </div>
          <div class="bid-ask-panel" v-if="bidAskData">
            <div class="bid-ask-header">
              <span class="current-price" :class="bidAskData.change > 0 ? 'up' : 'down'">
                {{ bidAskData.price?.toFixed(2) }}
              </span>
              <span class="change" :class="bidAskData.change > 0 ? 'up' : 'down'">
                {{ bidAskData.change > 0 ? '+' : '' }}{{ bidAskData.change?.toFixed(2) }}
                ({{ bidAskData.change_pct > 0 ? '+' : '' }}{{ bidAskData.change_pct?.toFixed(2) }}%)
              </span>
            </div>
            <table class="bid-ask-table">
              <tbody>
                <tr v-for="i in 5" :key="'ask'+i" class="ask-row">
                  <td class="label">卖{{ 6-i }}</td>
                  <td class="price down">{{ bidAskData['ask_price'+(6-i)]?.toFixed(2) }}</td>
                  <td class="volume">{{ bidAskData['ask_vol'+(6-i)] }}</td>
                </tr>
                <tr class="divider"><td colspan="3"></td></tr>
                <tr v-for="i in 5" :key="'bid'+i" class="bid-row">
                  <td class="label">买{{ i }}</td>
                  <td class="price up">{{ bidAskData['bid_price'+i]?.toFixed(2) }}</td>
                  <td class="volume">{{ bidAskData['bid_vol'+i] }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <div class="loading-inline" v-else-if="loading.bidAsk">加载盘口数据...</div>
        </div>

        <!-- 成交明细 -->
        <div class="content-section">
          <div class="section-header">
            <h2>成交明细</h2>
            <button class="btn-refresh" @click="fetchTransactions" :disabled="loading.transactions">刷新</button>
          </div>
          <div class="transactions-list" v-if="transactions.length > 0">
            <div class="transaction-item" v-for="(tx, idx) in transactions" :key="idx">
              <span class="tx-time">{{ tx.time }}</span>
              <span class="tx-price" :class="tx.type === 'B' ? 'up' : 'down'">{{ tx.price?.toFixed(2) }}</span>
              <span class="tx-volume">{{ tx.volume }}</span>
              <span class="tx-type" :class="tx.type === 'B' ? 'up' : 'down'">{{ tx.type === 'B' ? '买' : '卖' }}</span>
            </div>
          </div>
          <div class="loading-inline" v-else-if="loading.transactions">加载成交明细...</div>
          <div class="empty-state" v-else>暂无成交数据</div>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div class="loading-overlay" v-if="loading.overview">
      <div class="loading-spinner"></div>
      <p class="loading-text">加载市场数据...</p>
    </div>
  </div>
</template>

<script>
import API_BASE_URL from '@/config/api'

export default {
  name: 'MarketDataView',
  data() {
    return {
      loading: {
        overview: false,
        sectors: false,
        sectorStocks: false,
        bidAsk: false,
        transactions: false
      },
      overview: null,
      sectorType: 'industry',
      hotSectors: [],
      selectedSector: null,
      sectorStocks: [],
      rankType: 'gainers',
      topGainers: [],
      topLosers: [],
      topAmount: [],
      selectedStock: null,
      bidAskData: null,
      transactions: []
    }
  },
  mounted() {
    this.fetchAllData()
  },
  methods: {
    async fetchAllData() {
      this.loading.overview = true
      try {
        await Promise.all([
          this.fetchOverview(),
          this.fetchHotSectors(),
          this.fetchTopGainers(),
          this.fetchTopLosers(),
          this.fetchTopAmount()
        ])
      } finally {
        this.loading.overview = false
      }
    },

    async fetchOverview() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/market/overview`)
        const result = await response.json()
        if (result.success) {
          this.overview = result.data
        }
      } catch (error) {
        console.error('获取市场概览失败:', error)
      }
    },

    async fetchHotSectors() {
      this.loading.sectors = true
      try {
        const response = await fetch(`${API_BASE_URL}/api/market/hot-sectors?type=${this.sectorType}`)
        const result = await response.json()
        if (result.success) {
          this.hotSectors = result.data || []
        }
      } catch (error) {
        console.error('获取热点板块失败:', error)
      } finally {
        this.loading.sectors = false
      }
    },

    async selectSector(sector) {
      this.selectedSector = sector
      this.loading.sectorStocks = true
      try {
        const response = await fetch(`${API_BASE_URL}/api/market/sector-stocks/${encodeURIComponent(sector.name)}`)
        const result = await response.json()
        if (result.success) {
          this.sectorStocks = result.data || []
        }
      } catch (error) {
        console.error('获取板块成分股失败:', error)
      } finally {
        this.loading.sectorStocks = false
      }
    },

    async fetchTopGainers() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/market/top-gainers`)
        const result = await response.json()
        if (result.success) {
          this.topGainers = result.data || []
        }
      } catch (error) {
        console.error('获取涨幅榜失败:', error)
      }
    },

    async fetchTopLosers() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/market/top-losers`)
        const result = await response.json()
        if (result.success) {
          this.topLosers = result.data || []
        }
      } catch (error) {
        console.error('获取跌幅榜失败:', error)
      }
    },

    async fetchTopAmount() {
      try {
        const response = await fetch(`${API_BASE_URL}/api/market/top-amount`)
        const result = await response.json()
        if (result.success) {
          this.topAmount = result.data || []
        }
      } catch (error) {
        console.error('获取成交额榜失败:', error)
      }
    },

    async selectStock(code, name) {
      this.selectedStock = { code, name }
      await Promise.all([
        this.fetchBidAsk(),
        this.fetchTransactions()
      ])
    },

    async fetchBidAsk() {
      if (!this.selectedStock) return
      this.loading.bidAsk = true
      this.bidAskData = null
      try {
        const response = await fetch(`${API_BASE_URL}/api/market/bid-ask/${this.selectedStock.code}`)
        const result = await response.json()
        if (result.success) {
          this.bidAskData = result.data
        }
      } catch (error) {
        console.error('获取盘口数据失败:', error)
      } finally {
        this.loading.bidAsk = false
      }
    },

    async fetchTransactions() {
      if (!this.selectedStock) return
      this.loading.transactions = true
      this.transactions = []
      try {
        const response = await fetch(`${API_BASE_URL}/api/market/transactions/${this.selectedStock.code}`)
        const result = await response.json()
        if (result.success) {
          this.transactions = result.data || []
        }
      } catch (error) {
        console.error('获取成交明细失败:', error)
      } finally {
        this.loading.transactions = false
      }
    },

    formatAmount(amount) {
      if (!amount && amount !== 0) return '-'
      if (amount >= 100000000) {
        return (amount / 100000000).toFixed(2) + '亿'
      } else if (amount >= 10000) {
        return (amount / 10000).toFixed(2) + '万'
      }
      return amount.toFixed(2)
    }
  }
}
</script>

<style scoped>
.market-data-view {
  padding: 20px;
  max-width: 1600px;
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

.main-content {
  display: grid;
  grid-template-columns: 280px 1fr 320px;
  gap: 20px;
}

.main-content.no-detail {
  grid-template-columns: 280px 1fr;
}

.left-panel, .center-panel, .right-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.content-section {
  background: #1a1a2e;
  border-radius: 12px;
  padding: 16px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.section-header h2 {
  font-size: 16px;
  color: #fff;
  margin: 0;
}

.btn-refresh {
  padding: 4px 12px;
  font-size: 12px;
  border: 1px solid #667eea;
  background: transparent;
  color: #667eea;
  border-radius: 4px;
  cursor: pointer;
}

.btn-refresh:hover {
  background: #667eea;
  color: #fff;
}

.btn-refresh:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-close {
  background: none;
  border: none;
  color: #888;
  font-size: 20px;
  cursor: pointer;
  padding: 0 4px;
}

.btn-close:hover {
  color: #fff;
}

.tabs {
  display: flex;
  gap: 4px;
  margin-bottom: 12px;
  background: #0d0d1a;
  padding: 4px;
  border-radius: 6px;
}

.tab-btn {
  flex: 1;
  padding: 8px 12px;
  border: none;
  background: transparent;
  color: #888;
  cursor: pointer;
  border-radius: 4px;
  font-size: 13px;
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

.sector-list {
  max-height: 400px;
  overflow-y: auto;
}

.sector-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background 0.2s;
}

.sector-item:hover {
  background: #252540;
}

.sector-name {
  font-size: 14px;
  color: #e0e0e0;
}

.sector-change {
  font-size: 14px;
  font-weight: 500;
}

.table-container {
  overflow-x: auto;
  max-height: 500px;
  overflow-y: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table.compact {
  font-size: 13px;
}

.data-table th,
.data-table td {
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid #2a2a4a;
}

.data-table th {
  background: #0d0d1a;
  color: #888;
  font-weight: 500;
  white-space: nowrap;
  position: sticky;
  top: 0;
}

.data-table td {
  color: #e0e0e0;
}

.data-table tr.clickable {
  cursor: pointer;
}

.data-table tr.clickable:hover {
  background: #252540;
}

.code {
  font-family: monospace;
  color: #667eea;
}

.name {
  font-weight: 500;
}

.rank {
  color: #888;
  font-weight: bold;
}

.amount {
  color: #ffc107;
}

.up {
  color: #f44336;
}

.down {
  color: #4caf50;
}

.bid-ask-panel {
  padding: 12px;
}

.bid-ask-header {
  text-align: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #2a2a4a;
}

.current-price {
  font-size: 28px;
  font-weight: bold;
  display: block;
  margin-bottom: 4px;
}

.change {
  font-size: 14px;
}

.bid-ask-table {
  width: 100%;
  border-collapse: collapse;
}

.bid-ask-table td {
  padding: 6px 8px;
  font-size: 13px;
}

.bid-ask-table .label {
  color: #888;
  width: 40px;
}

.bid-ask-table .price {
  text-align: center;
}

.bid-ask-table .volume {
  text-align: right;
  color: #888;
}

.bid-ask-table .divider td {
  padding: 4px;
  border-bottom: 1px dashed #2a2a4a;
}

.transactions-list {
  max-height: 300px;
  overflow-y: auto;
}

.transaction-item {
  display: flex;
  justify-content: space-between;
  padding: 6px 8px;
  font-size: 12px;
  border-bottom: 1px solid #1a1a2e;
}

.transaction-item:hover {
  background: #252540;
}

.tx-time {
  color: #888;
  width: 60px;
}

.tx-price {
  width: 60px;
  text-align: right;
}

.tx-volume {
  width: 60px;
  text-align: right;
  color: #888;
}

.tx-type {
  width: 30px;
  text-align: center;
  font-weight: 500;
}

.empty-state {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 14px;
}

.loading-inline {
  text-align: center;
  padding: 20px;
  color: #667eea;
  font-size: 14px;
}

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

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }

  .stats-cards {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
