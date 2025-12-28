<template>
  <div class="sentiment-view">
    <div class="page-header"><h1>市场情绪分析</h1><p class="subtitle">恐慌贪婪指数、涨跌停统计、北向资金</p></div>
    <div class="fear-greed-section" v-if="fearGreed.score">
      <div class="fear-greed-gauge">
        <div class="gauge-value" :style="{color: fearGreed.color}">{{ fearGreed.score }}</div>
        <div class="gauge-label">{{ fearGreed.level }}</div>
        <div class="gauge-desc">{{ fearGreed.interpretation }}</div>
      </div>
    </div>
    <div class="stats-grid">
      <div class="stat-card" v-if="marketStats.total_count">
        <h3>市场涨跌</h3>
        <div class="stat-row"><span>总股票数</span><span>{{ marketStats.total_count }}</span></div>
        <div class="stat-row up"><span>上涨</span><span>{{ marketStats.up_count }} ({{ marketStats.up_ratio }}%)</span></div>
        <div class="stat-row down"><span>下跌</span><span>{{ marketStats.down_count }} ({{ marketStats.down_ratio }}%)</span></div>
        <div class="stat-row"><span>平盘</span><span>{{ marketStats.flat_count }}</span></div>
      </div>
      <div class="stat-card" v-if="limitStats.limit_up_count !== undefined">
        <h3>涨跌停统计</h3>
        <div class="stat-row limit-up"><span>涨停</span><span>{{ limitStats.limit_up_count }}</span></div>
        <div class="stat-row limit-down"><span>跌停</span><span>{{ limitStats.limit_down_count }}</span></div>
        <div class="stat-row"><span>涨停占比</span><span>{{ limitStats.limit_ratio }}%</span></div>
        <div class="interpretation">{{ limitStats.interpretation }}</div>
      </div>
      <div class="stat-card" v-if="northFlow.north_net_inflow !== undefined">
        <h3>北向资金</h3>
        <div class="stat-row" :class="northFlow.north_net_inflow > 0 ? 'up' : 'down'"><span>净流入</span><span>{{ formatMoney(northFlow.north_net_inflow) }}</span></div>
        <div class="stat-row"><span>沪股通</span><span>{{ formatMoney(northFlow.hgt_net_inflow) }}</span></div>
        <div class="stat-row"><span>深股通</span><span>{{ formatMoney(northFlow.sgt_net_inflow) }}</span></div>
        <div class="interpretation">{{ northFlow.interpretation }}</div>
      </div>
      <div class="stat-card" v-if="marginTrading.margin_balance">
        <h3>融资融券</h3>
        <div class="stat-row"><span>融资余额</span><span>{{ formatMoney(marginTrading.margin_balance) }}</span></div>
        <div class="stat-row"><span>融券余额</span><span>{{ formatMoney(marginTrading.short_balance) }}</span></div>
        <div class="interpretation">{{ marginTrading.interpretation }}</div>
      </div>
    </div>
    <div class="limit-stocks" v-if="limitStats.limit_up_stocks?.length">
      <h3>今日涨停股</h3>
      <div class="stock-tags">
        <span v-for="s in limitStats.limit_up_stocks" :key="s.code" class="stock-tag up">{{ s.name }}</span>
      </div>
    </div>
    <div class="stock-query">
      <h3>个股情绪查询</h3>
      <div class="query-input">
        <input v-model="stockCode" placeholder="输入股票代码" @keyup.enter="queryStock" />
        <button @click="queryStock" :disabled="!stockCode || stockLoading">{{ stockLoading ? '查询中...' : '查询' }}</button>
      </div>
      <div class="stock-result" v-if="stockSentiment.success">
        <div class="arbr-data" v-if="stockSentiment.arbr_data?.latest_ar">
          <h4>ARBR指标</h4>
          <div class="arbr-values">
            <span>AR: {{ stockSentiment.arbr_data.latest_ar }}</span>
            <span>BR: {{ stockSentiment.arbr_data.latest_br }}</span>
          </div>
          <div class="arbr-signal">{{ stockSentiment.arbr_data.signals?.overall_signal }}</div>
          <div class="arbr-interp" v-for="(i, idx) in stockSentiment.arbr_data.interpretation" :key="idx">{{ i }}</div>
        </div>
        <div class="turnover-data" v-if="stockSentiment.turnover_data?.turnover_rate">
          <h4>换手率: {{ stockSentiment.turnover_data.turnover_rate }}%</h4>
          <p>{{ stockSentiment.turnover_data.interpretation }}</p>
        </div>
      </div>
    </div>
    <button class="btn-refresh" @click="fetchData" :disabled="loading">{{ loading ? '刷新中...' : '刷新数据' }}</button>
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
import API_BASE_URL from "@/config/api"
export default {
  name: "MarketSentimentView",
  data() { 
    return { 
      loading: false, 
      loadingText: '数据加载中...',
      loadingProgress: 0,
      stockLoading: false, 
      stockCode: "", 
      fearGreed: {}, 
      marketStats: {}, 
      limitStats: {}, 
      northFlow: {}, 
      marginTrading: {}, 
      stockSentiment: {} 
    } 
  },
  mounted() { this.fetchData() },
  methods: {
    updateProgress(text, progress) {
      this.loadingText = text
      this.loadingProgress = progress
    },
    async fetchData() { 
      this.loading = true
      this.loadingProgress = 0
      try { 
        // 步骤1: 开始获取数据
        this.updateProgress('正在连接服务器...', 10)
        await new Promise(resolve => setTimeout(resolve, 100))
        
        // 步骤2: 获取市场情绪数据
        this.updateProgress('正在获取恐慌贪婪指数...', 25)
        const r = await fetch(API_BASE_URL+"/api/sentiment/market")
        
        // 步骤3: 解析数据
        this.updateProgress('正在解析市场涨跌数据...', 50)
        const d = await r.json()
        
        // 步骤4: 处理各项数据
        if(d.success) { 
          this.updateProgress('正在处理涨跌停统计...', 65)
          this.fearGreed = d.fear_greed_index||{}
          this.marketStats = d.market_stats||{}
          
          this.updateProgress('正在处理北向资金数据...', 80)
          this.limitStats = d.limit_stats||{}
          this.northFlow = d.north_flow||{}
          
          this.updateProgress('正在处理融资融券数据...', 90)
          this.marginTrading = d.margin_trading||{}
          
          this.updateProgress('全部数据加载完成', 100)
        } else {
          this.updateProgress('数据加载失败', 0)
        }
      } catch(e){
        console.error(e)
        this.updateProgress('加载出错: ' + e.message, 0)
      } finally { 
        setTimeout(() => {
          this.loading = false
          this.loadingProgress = 0
        }, 300)
      } 
    },
    async queryStock() { if(!this.stockCode) return; this.stockLoading = true; try { const r = await fetch(API_BASE_URL+"/api/sentiment/stock/"+this.stockCode); this.stockSentiment = await r.json() } catch(e){console.error(e)} finally { this.stockLoading = false } },
    formatMoney(n) { if(!n&&n!==0)return"-"; if(Math.abs(n)>=1e8)return(n/1e8).toFixed(2)+"亿"; if(Math.abs(n)>=1e4)return(n/1e4).toFixed(2)+"万"; return n.toFixed(2) }
  }
}
</script>
<style scoped>
.sentiment-view{padding:20px;max-width:1200px;margin:0 auto;color:#e0e0e0}
.page-header{margin-bottom:24px}.page-header h1{font-size:28px;color:#fff;margin:0 0 8px}.subtitle{color:#888;margin:0}
.fear-greed-section{background:#1a1a2e;border-radius:12px;padding:30px;margin-bottom:24px;text-align:center}
.gauge-value{font-size:64px;font-weight:bold}.gauge-label{font-size:24px;margin:8px 0}.gauge-desc{color:#888;font-size:14px}
.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-bottom:24px}
.stat-card{background:#1a1a2e;border-radius:12px;padding:20px}
.stat-card h3{font-size:16px;color:#fff;margin:0 0 16px;border-bottom:1px solid #2a2a4a;padding-bottom:12px}
.stat-row{display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #2a2a4a}
.stat-row.up{color:#f44336}.stat-row.down{color:#4caf50}.stat-row.limit-up{color:#ff6b6b}.stat-row.limit-down{color:#51cf66}
.interpretation{margin-top:12px;padding:10px;background:#0d0d1a;border-radius:6px;font-size:13px;color:#888}
.limit-stocks{background:#1a1a2e;border-radius:12px;padding:20px;margin-bottom:24px}
.limit-stocks h3{font-size:16px;color:#fff;margin:0 0 16px}
.stock-tags{display:flex;flex-wrap:wrap;gap:8px}
.stock-tag{padding:6px 12px;border-radius:16px;font-size:13px}
.stock-tag.up{background:rgba(244,67,54,.2);color:#f44336}
.stock-query{background:#1a1a2e;border-radius:12px;padding:20px;margin-bottom:24px}
.stock-query h3{font-size:16px;color:#fff;margin:0 0 16px}
.query-input{display:flex;gap:12px;margin-bottom:16px}
.query-input input{flex:1;padding:12px;border:1px solid #333;border-radius:6px;background:#0d0d1a;color:#fff}
.query-input button{padding:12px 24px;background:linear-gradient(135deg,#667eea,#764ba2);border:none;border-radius:6px;color:#fff;cursor:pointer}
.query-input button:disabled{opacity:.5}
.stock-result{background:#0d0d1a;border-radius:8px;padding:16px}
.arbr-data h4,.turnover-data h4{color:#667eea;margin:0 0 12px}
.arbr-values{display:flex;gap:24px;font-size:18px;margin-bottom:8px}
.arbr-signal{color:#ff9800;font-weight:bold;margin-bottom:8px}
.arbr-interp{font-size:13px;color:#888;margin:4px 0}
.btn-refresh{padding:12px 24px;border:1px solid #667eea;background:transparent;color:#667eea;border-radius:6px;cursor:pointer}
.btn-refresh:hover{background:#667eea;color:#fff}.btn-refresh:disabled{opacity:.5}
.loading-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.7);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:1001}
.loading-spinner{width:40px;height:40px;border:3px solid #333;border-top-color:#667eea;border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-text{margin-top:16px;color:#e0e0e0;font-size:14px}
.loading-progress{margin-top:16px;display:flex;align-items:center;gap:12px}
.progress-bar{width:200px;height:6px;background:#333;border-radius:3px;overflow:hidden}
.progress-fill{height:100%;background:linear-gradient(90deg,#667eea 0%,#764ba2 100%);border-radius:3px;transition:width 0.3s ease}
.progress-text{color:#667eea;font-size:12px;font-weight:500;min-width:40px}
</style>
