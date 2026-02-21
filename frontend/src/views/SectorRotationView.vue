<template>
  <div class="sector-view">
    <div class="page-header"><h1>板块轮动分析</h1><p class="subtitle">行业板块、概念板块轮动追踪</p></div>
    <div class="tabs">
      <button v-for="tab in tabs" :key="tab.key" :class="['tab-btn', { active: activeTab === tab.key }]" @click="switchTab(tab.key)">{{ tab.label }}</button>
      <button class="btn-refresh" @click="refreshCurrentTab" :disabled="loading">刷新</button>
    </div>
    <div class="content-section" v-show="activeTab === 'industry'">
      <h2>行业板块 <span class="data-count" v-if="industrySectors.length">({{ industrySectors.length }})</span></h2>
      <table class="data-table" v-if="industrySectors.length">
        <thead><tr><th>板块</th><th>涨跌幅</th><th>换手率</th><th>领涨股</th></tr></thead>
        <tbody><tr v-for="item in industrySectors" :key="item.name"><td>{{ item.name }}</td><td :class="item.change_pct > 0 ? 'up' : 'down'">{{ item.change_pct?.toFixed(2) }}%</td><td>{{ item.turnover?.toFixed(2) }}%</td><td>{{ item.top_stock }}</td></tr></tbody>
      </table>
      <div class="empty-state" v-else>
        <div class="empty-icon">📊</div>
        <p>暂无数据，点击刷新按钮加载</p>
      </div>
    </div>
    <div class="content-section" v-show="activeTab === 'concept'">
      <h2>概念板块 <span class="data-count" v-if="conceptSectors.length">({{ conceptSectors.length }})</span></h2>
      <table class="data-table" v-if="conceptSectors.length">
        <thead><tr><th>板块</th><th>涨跌幅</th><th>换手率</th><th>领涨股</th></tr></thead>
        <tbody><tr v-for="item in conceptSectors" :key="item.name"><td>{{ item.name }}</td><td :class="item.change_pct > 0 ? 'up' : 'down'">{{ item.change_pct?.toFixed(2) }}%</td><td>{{ item.turnover?.toFixed(2) }}%</td><td>{{ item.top_stock }}</td></tr></tbody>
      </table>
      <div class="empty-state" v-else>
        <div class="empty-icon">📊</div>
        <p>暂无数据，点击刷新按钮加载</p>
      </div>
    </div>
    <div class="content-section" v-show="activeTab === 'fund-flow'">
      <h2>资金流向 <span class="data-count" v-if="fundFlowData.length">({{ fundFlowData.length }})</span></h2>
      <table class="data-table" v-if="fundFlowData.length">
        <thead><tr><th>行业</th><th>涨跌幅</th><th>主力净流入</th><th>净占比</th></tr></thead>
        <tbody><tr v-for="item in fundFlowData" :key="item.sector"><td>{{ item.sector }}</td><td :class="item.change_pct > 0 ? 'up' : 'down'">{{ item.change_pct?.toFixed(2) }}%</td><td :class="item.main_net_inflow > 0 ? 'up' : 'down'">{{ formatMoney(item.main_net_inflow) }}</td><td>{{ item.main_net_inflow_pct?.toFixed(2) }}%</td></tr></tbody>
      </table>
      <div class="empty-state" v-else>
        <div class="empty-icon">💰</div>
        <p>暂无数据，点击刷新按钮加载</p>
      </div>
    </div>
    <div class="content-section" v-show="activeTab === 'heat'">
      <h2>板块热度</h2>
      <div class="heat-grid" v-if="heatData.hottest.length || heatData.heating.length || heatData.cooling.length">
        <div class="heat-col"><h3>最热</h3><div v-for="item in heatData.hottest" :key="item.sector" class="heat-item">{{ item.sector }} - {{ item.heat_score }}</div></div>
        <div class="heat-col"><h3>升温</h3><div v-for="item in heatData.heating" :key="item.sector" class="heat-item">{{ item.sector }} - {{ item.heat_score }}</div></div>
        <div class="heat-col"><h3>降温</h3><div v-for="item in heatData.cooling" :key="item.sector" class="heat-item">{{ item.sector }} - {{ item.heat_score }}</div></div>
      </div>
      <div class="empty-state" v-else>
        <div class="empty-icon">🔥</div>
        <p>暂无数据，点击刷新按钮加载</p>
      </div>
    </div>
    <div class="content-section" v-show="activeTab === 'rotation'">
      <h2>轮动信号</h2>
      <div class="rotation-grid" v-if="rotationData.current_strong.length || rotationData.potential.length || rotationData.declining.length">
        <div class="rotation-col strong"><h3>强势</h3><div v-for="item in rotationData.current_strong" :key="item.sector" class="rotation-item">{{ item.sector }} {{ item.change_pct?.toFixed(2) }}%</div></div>
        <div class="rotation-col potential"><h3>潜力</h3><div v-for="item in rotationData.potential" :key="item.sector" class="rotation-item">{{ item.sector }} {{ item.change_pct?.toFixed(2) }}%</div></div>
        <div class="rotation-col declining"><h3>衰退</h3><div v-for="item in rotationData.declining" :key="item.sector" class="rotation-item">{{ item.sector }} {{ item.change_pct?.toFixed(2) }}%</div></div>
      </div>
      <div class="empty-state" v-else>
        <div class="empty-icon">🔄</div>
        <p>暂无数据，点击刷新按钮加载</p>
      </div>
    </div>
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
  name: "SectorRotationView",
  data() { 
    return { 
      loading: false, 
      loadingText: '数据加载中...',
      loadingProgress: 0,
      activeTab: "industry", 
      loadedTabs: new Set(), // 跟踪已加载的标签页
      tabs: [
        {key:"industry",label:"行业板块"},
        {key:"concept",label:"概念板块"},
        {key:"fund-flow",label:"资金流向"},
        {key:"heat",label:"板块热度"},
        {key:"rotation",label:"轮动信号"}
      ], 
      industrySectors: [], 
      conceptSectors: [], 
      fundFlowData: [], 
      heatData: {hottest:[],heating:[],cooling:[]}, 
      rotationData: {current_strong:[],potential:[],declining:[]} 
    } 
  },
  mounted() { 
    // 懒加载：只加载当前激活的标签页
    this.loadTabData(this.activeTab) 
  },
  methods: {
    updateProgress(text, progress) {
      this.loadingText = text
      this.loadingProgress = progress
    },
    // 切换标签页
    switchTab(tabKey) {
      this.activeTab = tabKey
      // 如果该标签页未加载过数据，则加载
      if (!this.loadedTabs.has(tabKey)) {
        this.loadTabData(tabKey)
      }
    },
    // 根据标签页加载对应数据
    async loadTabData(tabKey) {
      this.loading = true
      this.loadingProgress = 0
      try {
        switch(tabKey) {
          case 'industry':
            this.updateProgress('正在获取行业板块数据...', 30)
            await this.fetchIndustry()
            break
          case 'concept':
            this.updateProgress('正在获取概念板块数据...', 30)
            await this.fetchConcept()
            break
          case 'fund-flow':
            this.updateProgress('正在获取资金流向数据...', 30)
            await this.fetchFundFlow()
            break
          case 'heat':
            this.updateProgress('正在获取板块热度数据...', 30)
            await this.fetchHeat()
            break
          case 'rotation':
            this.updateProgress('正在获取轮动信号数据...', 30)
            await this.fetchRotation()
            break
        }
        // 标记该标签页已加载
        this.loadedTabs.add(tabKey)
        this.updateProgress('加载完成', 100)
      } catch(e) {
        console.error(`加载 ${tabKey} 数据失败:`, e)
      } finally { 
        setTimeout(() => {
          this.loading = false
          this.loadingProgress = 0
        }, 300)
      }
    },
    // 刷新当前标签页
    refreshCurrentTab() {
      this.loadedTabs.delete(this.activeTab)
      this.loadTabData(this.activeTab)
    },
    async fetchIndustry() { 
      try { 
        const r = await fetch(API_BASE_URL+"/api/sector-rotation/industry-sectors"); 
        const d = await r.json(); 
        if(d.success) this.industrySectors = d.data||[] 
      } catch(e){console.error(e)} 
    },
    async fetchConcept() { 
      try { 
        const r = await fetch(API_BASE_URL+"/api/sector-rotation/concept-sectors"); 
        const d = await r.json(); 
        if(d.success) this.conceptSectors = d.data||[] 
      } catch(e){console.error(e)} 
    },
    async fetchFundFlow() { 
      try { 
        const r = await fetch(API_BASE_URL+"/api/sector-rotation/fund-flow"); 
        const d = await r.json(); 
        if(d.success) this.fundFlowData = d.data||[] 
      } catch(e){console.error(e)} 
    },
    async fetchHeat() { 
      try { 
        const r = await fetch(API_BASE_URL+"/api/sector-rotation/analysis/heat"); 
        const d = await r.json(); 
        if(d.success) this.heatData = {hottest:d.hottest||[],heating:d.heating||[],cooling:d.cooling||[]} 
      } catch(e){console.error(e)} 
    },
    async fetchRotation() { 
      try { 
        const r = await fetch(API_BASE_URL+"/api/sector-rotation/analysis/rotation"); 
        const d = await r.json(); 
        if(d.success) this.rotationData = {current_strong:d.current_strong||[],potential:d.potential||[],declining:d.declining||[]} 
      } catch(e){console.error(e)} 
    },
    formatMoney(n) { 
      if(!n&&n!==0)return"-"; 
      if(Math.abs(n)>=1e8)return(n/1e8).toFixed(2)+"亿"; 
      if(Math.abs(n)>=1e4)return(n/1e4).toFixed(2)+"万"; 
      return n.toFixed(2) 
    }
  }
}
</script>
<style scoped>
.sector-view{padding:20px;max-width:1400px;margin:0 auto;color:#e0e0e0}
.page-header{margin-bottom:24px}.page-header h1{font-size:28px;color:#fff;margin:0 0 8px}.subtitle{color:#888;margin:0}
.tabs{display:flex;gap:4px;margin-bottom:20px;background:#1a1a2e;padding:4px;border-radius:8px;flex-wrap:wrap}
.tab-btn{padding:12px 20px;border:none;background:transparent;color:#888;cursor:pointer;border-radius:6px;transition:all 0.2s}
.tab-btn.active{background:linear-gradient(135deg,#667eea,#764ba2);color:#fff}
.tab-btn:hover:not(.active){background:#2a2a4a;color:#fff}
.btn-refresh{margin-left:auto;padding:12px 20px;border:1px solid #667eea;background:transparent;color:#667eea;border-radius:6px;cursor:pointer;transition:all 0.2s}
.btn-refresh:hover{background:#667eea;color:#fff}.btn-refresh:disabled{opacity:.5;cursor:not-allowed}
.content-section{background:#1a1a2e;border-radius:12px;padding:20px;margin-bottom:20px;min-height:200px}
.content-section h2{font-size:18px;color:#fff;margin:0 0 16px;display:flex;align-items:center;gap:8px}
.data-count{font-size:14px;color:#667eea;font-weight:normal}
.data-table{width:100%;border-collapse:collapse}
.data-table th,.data-table td{padding:12px;text-align:left;border-bottom:1px solid #2a2a4a}
.data-table th{background:#0d0d1a;color:#888}.data-table td{color:#e0e0e0}
.data-table tr:hover{background:#252540}
.up{color:#f44336}.down{color:#4caf50}
.heat-grid,.rotation-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:20px}
.heat-col,.rotation-col{background:#0d0d1a;border-radius:8px;padding:16px}
.heat-col h3,.rotation-col h3{font-size:16px;color:#fff;margin:0 0 16px}
.heat-item,.rotation-item{padding:10px 12px;background:#1a1a2e;border-radius:6px;margin-bottom:8px;color:#e0e0e0}
.rotation-col.strong{border-top:3px solid #f44336}.rotation-col.potential{border-top:3px solid #ff9800}.rotation-col.declining{border-top:3px solid #4caf50}

/* 空状态样式 */
.empty-state{display:flex;flex-direction:column;align-items:center;justify-content:center;padding:60px 20px;color:#888}
.empty-icon{font-size:48px;margin-bottom:16px;opacity:0.5}
.empty-state p{margin:0;font-size:14px}

.loading-overlay{position:fixed;top:0;left:0;right:0;bottom:0;background:rgba(0,0,0,.7);display:flex;flex-direction:column;align-items:center;justify-content:center;z-index:1001}
.loading-spinner{width:40px;height:40px;border:3px solid #333;border-top-color:#667eea;border-radius:50%;animation:spin 1s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.loading-text{margin-top:16px;color:#e0e0e0;font-size:14px}
.loading-progress{margin-top:16px;display:flex;align-items:center;gap:12px}
.progress-bar{width:200px;height:6px;background:#333;border-radius:3px;overflow:hidden}
.progress-fill{height:100%;background:linear-gradient(90deg,#667eea 0%,#764ba2 100%);border-radius:3px;transition:width 0.3s ease}
.progress-text{color:#667eea;font-size:12px;font-weight:500;min-width:40px}
@media(max-width:768px){.heat-grid,.rotation-grid{grid-template-columns:1fr}}
</style>
