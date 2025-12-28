<template>
  <div class="wencai-view">
    <!-- 页面标题 -->
    <div class="page-header">
      <h1>🔍 问财选股</h1>
      <p class="subtitle">基于同花顺问财的智能选股系统，支持自然语言查询</p>
    </div>

    <!-- 查询区域 -->
    <div class="query-section">
      <div class="query-input-wrapper">
        <input v-model="queryText" type="text" class="query-input" 
          placeholder="输入选股条件，如：连续3天涨停、市盈率小于20..."
          @keyup.enter="executeQuery"/>
        <button class="btn btn-primary" @click="executeQuery" :disabled="loading">
          {{ loading ? '查询中...' : '开始选股' }}
        </button>
      </div>
      <div class="query-tips">
        <span class="tip-label">热门查询：</span>
        <span class="tip-item" @click="setQuery('今日涨停')">今日涨停</span>
        <span class="tip-item" @click="setQuery('连续3天涨停')">连续涨停</span>
        <span class="tip-item" @click="setQuery('市盈率小于20')">低市盈率</span>
      </div>
    </div>

    <!-- 精选策略区域 -->
    <div class="strategies-section">
      <h2>⭐ 精选策略 <span class="badge">推荐</span></h2>
      <p class="section-desc">来自 aiagents-stock 项目的5个精选选股策略</p>
      
      <div class="featured-settings">
        <span class="settings-label">📊 精选数量：</span>
        <div class="topn-options">
          <button v-for="n in [3, 5, 10, 15, 20]" :key="n" class="topn-btn"
            :class="{ active: featuredTopN === n }" @click="setFeaturedTopN(n)">
            Top {{ n }}
          </button>
        </div>
        <div class="topn-slider">
          <input type="range" v-model.number="featuredTopN" min="3" max="20" class="slider"/>
          <span class="slider-value">{{ featuredTopN }} 只</span>
        </div>
      </div>
      
      <div class="strategy-grid featured-grid">
        <div v-for="strategy in featuredStrategies" :key="strategy.id"
          class="strategy-card featured-card" :class="{ active: selectedStrategy === strategy.id }"
          @click="selectFeaturedStrategy(strategy)">
          <div class="strategy-icon">{{ strategy.icon }}</div>
          <div class="strategy-info">
            <h3>{{ strategy.name }}</h3>
            <p class="strategy-desc">{{ strategy.description }}</p>
            <div class="strategy-conditions">
              <span v-for="(cond, idx) in strategy.conditions.slice(0, 3)" :key="idx" class="condition-tag">{{ cond }}</span>
            </div>
          </div>
          <span class="featured-badge">精选</span>
        </div>
      </div>
    </div>

    <!-- 常用策略区域 -->
    <div class="strategies-section">
      <h2>📋 常用策略</h2>
      <div class="strategy-grid">
        <div v-for="strategy in commonStrategies" :key="strategy.id"
          class="strategy-card" :class="{ active: selectedStrategy === strategy.id }"
          @click="selectStrategy(strategy)">
          <div class="strategy-icon">{{ strategy.icon }}</div>
          <div class="strategy-info">
            <h3>{{ strategy.name }}</h3>
            <p>{{ strategy.description }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 结果区域 -->
    <div class="results-section" v-if="results.length > 0 || loading">
      <div class="section-header">
        <h2>📊 选股结果</h2>
        <span class="query-time" v-if="queryTime">查询耗时: {{ queryTime }}ms</span>
      </div>
      
      <div class="options-bar" v-if="results.length > 0">
        <span class="result-count">共 {{ totalCount }} 条结果，显示 {{ results.length }} 条</span>
        <div class="featured-info" v-if="isFeaturedQuery">
          <span class="featured-label">⭐ 精选 Top {{ featuredTopN }}</span>
        </div>
      </div>
      
      <!-- 策略说明 -->
      <div class="strategy-explanation" v-if="currentStrategyExplanation">
        <div class="explanation-header" @click="toggleExplanation">
          <span class="explanation-icon">💡</span>
          <span>策略说明：{{ currentStrategyName }}</span>
          <span class="toggle-icon">{{ showExplanation ? '▼' : '▶' }}</span>
        </div>
        <div class="explanation-content" v-show="showExplanation" v-html="currentStrategyExplanation"></div>
      </div>
      
      <!-- 数据表格 -->
      <div class="table-container">
        <table class="data-table" v-if="results.length > 0">
          <thead>
            <tr>
              <th>序号</th>
              <th v-for="col in displayColumns" :key="col">{{ getColumnLabel(col) }}</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(row, index) in results" :key="index">
              <td>{{ index + 1 }}</td>
              <td v-for="col in displayColumns" :key="col" :class="getCellClass(col, row[col])">
                {{ formatCellValue(col, row[col]) }}
              </td>
              <td><button class="btn-small" @click="analyzeStock(row)">分析</button></td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="empty-state" v-if="results.length === 0 && !loading">
        <div class="empty-icon">📭</div>
        <p>未找到符合条件的股票</p>
      </div>
    </div>

    <!-- 初始状态 -->
    <div class="initial-state" v-if="results.length === 0 && !loading && !hasQueried">
      <div class="initial-icon">🎯</div>
      <p>选择一个策略或输入查询条件开始选股</p>
    </div>

    <!-- 服务状态 -->
    <div class="service-status" :class="serviceAvailable ? 'available' : 'unavailable'">
      <span class="status-dot"></span>
      <span>{{ serviceAvailable ? '问财服务正常' : '问财服务不可用' }}</span>
    </div>

    <!-- 加载遮罩 -->
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
import axios from 'axios'

// 精选策略配置
const FEATURED_STRATEGIES = [
  {
    id: 'featured_zhuli', name: '主力选股', icon: '🐋',
    description: '追踪主力资金动向，捕捉机构布局机会',
    query: '非ST，主力净流入大于5000万，量比大于1.5，换手率大于3%，涨跌幅大于2%，沪深A股',
    conditions: ['主力净流入>5000万', '量比>1.5', '换手率>3%', '涨跌幅>2%'],
    explanation: '<b>选股条件：</b>排除ST/停牌/退市，主力净流入>5000万，量比>1.5，换手率>3%，涨跌幅>2%<br/><b>量化策略：</b>单股≤30%，止损-8%~-10%，止盈+15%~+20%，中短期波段<br/><b>买卖时机：</b>主力持续流入+放量突破时买入，主力流出或达止盈止损位卖出'
  },
  {
    id: 'featured_dijia', name: '低价擒牛', icon: '🐂',
    description: '低价股中寻找潜力牛股，小资金撬动大收益',
    query: '非ST，股价小于10元，总市值小于100亿，涨跌幅大于3%，量比大于2，换手率大于5%，沪深A股',
    conditions: ['股价<10元', '市值<100亿', '涨跌幅>3%', '量比>2', '换手率>5%'],
    explanation: '<b>选股条件：</b>股价<10元，市值<100亿，涨跌幅>3%，量比>2，换手率>5%<br/><b>量化策略：</b>100万资金，满仓，单股≤40%，最多4只，持股5天，MA5下穿MA20卖出<br/><b>买卖时机：</b>低价放量突破时买入，5日均线下穿20日均线时清仓'
  },
  {
    id: 'featured_xiaoshizhi', name: '小市值策略', icon: '💎',
    description: '聚焦小市值高弹性标的，捕捉超额收益',
    query: '非ST，总市值小于50亿，涨跌幅大于2%，量比大于1.5，换手率大于3%，沪深A股',
    conditions: ['市值<50亿', '涨跌幅>2%', '量比>1.5', '换手率>3%'],
    explanation: '<b>选股条件：</b>市值<50亿，涨跌幅>2%，量比>1.5，换手率>3%<br/><b>量化策略：</b>10万资金，满仓，单股≤30%，最多4只，持股5天，MA5下穿MA20卖出<br/><b>买卖时机：</b>小市值股放量启动时买入，5日均线下穿20日均线时清仓'
  },
  {
    id: 'featured_jingli', name: '净利增长', icon: '📈',
    description: '筛选业绩高增长股票，价值投资首选',
    query: '非ST，净利润同比增长率大于30%，营收同比增长率大于20%，市盈率小于50，沪深A股',
    conditions: ['净利润增长>30%', '营收增长>20%', '市盈率<50'],
    explanation: '<b>选股条件：</b>净利润同比>30%，营收同比>20%，市盈率<50<br/><b>量化策略：</b>价值成长型，持股1-6个月，单股≤25%，止损-10%<br/><b>买卖时机：</b>业绩预告确认增长时买入，增速放缓或估值过高时减仓'
  },
  {
    id: 'featured_fangliang', name: '放量突破', icon: '🚀',
    description: '捕捉放量突破形态，把握主升浪行情',
    query: '非ST，量比大于2，换手率大于3%，涨跌幅大于3%，创20日新高，沪深A股',
    conditions: ['量比>2', '换手率>3%', '涨跌幅>3%', '创20日新高'],
    explanation: '<b>选股条件：</b>量比>2，换手率>3%，涨跌幅>3%，创20日新高<br/><b>量化策略：</b>短线追涨，持股3-5天，单股≤20%，跌破突破日最低价止损<br/><b>买卖时机：</b>放量突破确认后买入，缩量滞涨或跌破5日均线时离场'
  }
]

// 常用策略配置
const COMMON_STRATEGIES = [
  { id: 'zhangting', name: '涨停板', icon: '🔥', description: '今日涨停的股票', query: '涨停，沪深A股，非ST' },
  { id: 'lianban', name: '连板股', icon: '⚡', description: '连续涨停的强势股', query: '连续涨停天数大于2，沪深A股，非ST' },
  { id: 'dipexigou', name: '低PE优质股', icon: '💰', description: '市盈率低于15的优质股', query: '市盈率小于15，市盈率大于0，净利润同比增长率大于10%，沪深A股，非ST' },
  { id: 'gaohuan', name: '高换手活跃股', icon: '🔄', description: '换手率超过10%的活跃股', query: '换手率大于10%，成交额大于5亿，沪深A股，非ST' },
  { id: 'chuang60xingao', name: '创新高', icon: '📊', description: '创60日新高的股票', query: '创60日新高，涨跌幅大于2%，沪深A股，非ST' },
  { id: 'macd_gold', name: 'MACD金叉', icon: '✨', description: 'MACD金叉的技术形态股', query: 'MACD金叉，量比大于1，沪深A股，非ST' }
]

// 列优先级
const COLUMN_PRIORITY = {
  '股票代码': 1, 'code': 1, '股票简称': 2, 'name': 2, '最新价': 3, '现价': 3, 'close': 3,
  '涨跌幅': 4, 'change_pct': 4, '换手率': 5, 'turnover_rate': 5, '成交额': 6, 'amount': 6,
  '量比': 7, 'volume_ratio': 7, '市值': 8, '总市值': 8, 'market_cap': 8, '市盈率': 9, 'pe': 9
}

// 不重要的列
const UNIMPORTANT_COLS = ['market', '市场', 'exchange', '交易所', 'list_date', '上市日期', 'update_time', 'id', 'index', '序号', 'Unnamed']

export default {
  name: 'WencaiSelectorView',
  data() {
    return {
      queryText: '', loading: false, results: [], columns: [], totalCount: 0, queryTime: null,
      topN: 50, featuredTopN: 5, selectedStrategy: null, hasQueried: false, serviceAvailable: true,
      isFeaturedQuery: false, currentStrategyName: '', currentStrategyExplanation: '', showExplanation: true,
      featuredStrategies: FEATURED_STRATEGIES,
      commonStrategies: COMMON_STRATEGIES,
      loadingText: '正在查询...',
      loadingProgress: 0
    }
  },
  computed: {
    displayColumns() {
      if (!this.columns || this.columns.length === 0) return []
      let filtered = this.columns.filter(col => !UNIMPORTANT_COLS.some(uc => col.toLowerCase().includes(uc.toLowerCase())))
      filtered.sort((a, b) => (COLUMN_PRIORITY[a] || 100) - (COLUMN_PRIORITY[b] || 100))
      return filtered.slice(0, 10)
    }
  },
  mounted() { this.checkServiceStatus() },
  methods: {
    getColumnLabel(col) {
      // 标准列名映射
      const map = {
        'code': '股票代码', 'name': '股票简称', 'close': '最新价',
        'change_pct': '涨跌幅(%)', 'turnover_rate': '换手率(%)',
        'amount': '成交额', 'volume_ratio': '量比', 'market_cap': '总市值', 'pe': '市盈率',
        '股票代码': '代码', '股票简称': '名称'
      }
      if (map[col]) return map[col]
      
      // 智能提取列名核心部分（去除日期等后缀）
      let cleanCol = col
      // 移除日期后缀，如 [2025-12-27] 或 [20251227]
      cleanCol = cleanCol.replace(/\[\d{4}[-/]?\d{2}[-/]?\d{2}\]/g, '')
      // 移除时间后缀
      cleanCol = cleanCol.replace(/\[\d{2}:\d{2}(:\d{2})?\]/g, '')
      // 移除括号中的日期描述
      cleanCol = cleanCol.replace(/\(.*?\d{4}.*?\)/g, '')
      // 清理多余空格
      cleanCol = cleanCol.trim()
      
      // 常见列名简化
      const simplifyMap = {
        '涨停明细数据': '涨停明细',
        '涨跌幅:前复权': '涨跌幅',
        '最新价:前复权': '最新价',
        '成交额:前复权': '成交额',
        '换手率:前复权': '换手率',
        '量比:前复权': '量比',
        '总市值:前复权': '总市值',
        '流通市值:前复权': '流通市值',
        '市盈率:前复权': '市盈率',
        '市净率:前复权': '市净率'
      }
      
      for (const [key, value] of Object.entries(simplifyMap)) {
        if (cleanCol.includes(key)) {
          return value
        }
      }
      
      // 如果还是太长，截断显示
      return cleanCol.length > 12 ? cleanCol.substring(0, 12) + '...' : cleanCol
    },
    setFeaturedTopN(n) {
      this.featuredTopN = n
      if (this.isFeaturedQuery && this.selectedStrategy) {
        const s = this.featuredStrategies.find(x => x.id === this.selectedStrategy)
        if (s) this.selectFeaturedStrategy(s)
      }
    },
    toggleExplanation() { this.showExplanation = !this.showExplanation },
    updateProgress(text, progress) {
      this.loadingText = text
      this.loadingProgress = progress
    },
    async checkServiceStatus() {
      try { const r = await axios.get('/api/wencai/status'); this.serviceAvailable = r.data.available }
      catch { this.serviceAvailable = false }
    },
    setQuery(q) { this.queryText = q; this.executeQuery() },
    selectStrategy(s) {
      this.selectedStrategy = s.id; this.queryText = s.query; this.isFeaturedQuery = false
      this.currentStrategyName = s.name; this.currentStrategyExplanation = ''; this.executeQuery()
    },
    selectFeaturedStrategy(s) {
      this.selectedStrategy = s.id; this.queryText = s.query; this.isFeaturedQuery = true
      this.currentStrategyName = s.name; this.currentStrategyExplanation = s.explanation
      this.showExplanation = true; this.executeQuery()
    },
    async executeQuery() {
      if (!this.queryText.trim()) { alert('请输入查询条件'); return }
      this.loading = true; this.hasQueried = true; this.loadingProgress = 0
      const start = Date.now()
      try {
        // 步骤1: 准备查询
        this.updateProgress('正在解析查询条件...', 10)
        await new Promise(resolve => setTimeout(resolve, 100))
        
        // 步骤2: 发送请求
        this.updateProgress('正在连接问财服务...', 30)
        const top_n = this.isFeaturedQuery ? this.featuredTopN : this.topN
        
        // 步骤3: 等待响应
        this.updateProgress('正在获取选股结果...', 50)
        const r = await axios.post('/api/wencai/query', { query: this.queryText, top_n: top_n })
        
        // 步骤4: 处理数据
        this.updateProgress('正在处理数据...', 80)
        this.queryTime = Date.now() - start
        if (r.data.success) {
          this.results = r.data.data || []; this.columns = r.data.columns || []
          this.totalCount = r.data.total || r.data.count || this.results.length
          this.updateProgress('查询完成', 100)
        } else { 
          alert('查询失败: ' + (r.data.message || '未知错误')); this.results = []
          this.updateProgress('查询失败', 0)
        }
      } catch (e) { 
        alert('查询出错: ' + (e.response?.data?.message || e.message)); this.results = []
        this.updateProgress('查询出错: ' + e.message, 0)
      }
      finally { 
        setTimeout(() => {
          this.loading = false
          this.loadingProgress = 0
        }, 300)
      }
    },
    getCellClass(col, val) {
      const c = col.toLowerCase()
      if (c.includes('code') || c.includes('代码')) return 'code'
      if (c.includes('name') || c.includes('简称')) return 'name'
      if (c.includes('涨跌') || c.includes('change')) {
        const n = parseFloat(val); if (!isNaN(n)) return n > 0 ? 'up' : n < 0 ? 'down' : ''
      }
      return ''
    },
    formatCellValue(col, val) {
      if (val === null || val === undefined) return '-'
      
      // 处理对象类型（如涨停明细数据）
      if (typeof val === 'object') {
        // 如果是数组，显示数量
        if (Array.isArray(val)) {
          return `[${val.length}条]`
        }
        // 如果是对象，尝试提取关键信息
        if (val.time || val.涨停时间) {
          return val.time || val.涨停时间
        }
        if (val.price || val.涨停价) {
          return val.price || val.涨停价
        }
        // 其他对象显示为JSON摘要
        const keys = Object.keys(val)
        if (keys.length === 0) return '-'
        if (keys.length <= 2) {
          return keys.map(k => `${k}:${val[k]}`).join(', ')
        }
        return `{${keys.length}项}`
      }
      
      // 处理字符串类型
      if (typeof val === 'string') {
        // 如果是很长的字符串（可能是JSON或复杂数据），截断显示
        if (val.length > 50) {
          // 尝试解析为JSON
          try {
            const parsed = JSON.parse(val)
            if (Array.isArray(parsed)) {
              return `[${parsed.length}条]`
            }
            if (typeof parsed === 'object') {
              return `{${Object.keys(parsed).length}项}`
            }
          } catch {
            // 不是JSON，直接截断
            return val.substring(0, 30) + '...'
          }
        }
        return val
      }
      
      const c = col.toLowerCase()
      
      // 处理百分比类型
      if (c.includes('涨跌幅') || c.includes('换手率') || c.includes('change') || c.includes('rate') || c.includes('增长')) {
        const n = parseFloat(val)
        if (!isNaN(n)) return n.toFixed(2) + '%'
      }
      
      // 处理金额类型
      if (c.includes('成交额') || c.includes('市值') || c.includes('amount') || c.includes('cap') || c.includes('净流入') || c.includes('资金')) {
        const n = parseFloat(val)
        if (!isNaN(n)) {
          if (Math.abs(n) >= 1e8) return (n / 1e8).toFixed(2) + '亿'
          if (Math.abs(n) >= 1e4) return (n / 1e4).toFixed(2) + '万'
        }
      }
      
      // 处理价格类型
      if (c.includes('价') || c.includes('price')) {
        const n = parseFloat(val)
        if (!isNaN(n)) return n.toFixed(2)
      }
      
      // 处理量比类型
      if (c.includes('量比') || c.includes('volume_ratio')) {
        const n = parseFloat(val)
        if (!isNaN(n)) return n.toFixed(2)
      }
      
      return val
    },
    analyzeStock(row) {
      const code = row['股票代码'] || row['code'] || row['代码']
      const name = row['股票简称'] || row['name'] || row['名称']
      if (code) {
        localStorage.setItem('analyzeStock', JSON.stringify({ code, name }))
        window.dispatchEvent(new CustomEvent('navigateToAnalysis', { detail: { code, name } }))
      }
    }
  }
}
</script>

<style src="./WencaiSelectorView-styles.css"></style>
