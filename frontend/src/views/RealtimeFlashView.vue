<template>
  <div class="realtime-flash-page">
    <div class="header">
      <h2>⚡ 实时快讯</h2>
      <p class="desc">聚合金十(JIN10) + 汇通(FX678) 实时快讯，支持自动刷新与降级提示。</p>
    </div>

    <div class="controls card">
      <div class="row">
        <label>来源筛选</label>
        <select v-model="source" @change="loadLatest">
          <option value="all">全部</option>
          <option value="jin10">金十</option>
          <option value="fx678">汇通</option>
        </select>

        <label>条数</label>
        <select v-model.number="limit" @change="loadLatest">
          <option :value="20">20</option>
          <option :value="50">50</option>
          <option :value="100">100</option>
        </select>

        <label class="switch">
          <input type="checkbox" v-model="autoRefresh" />
          <span>自动刷新（{{ refreshSeconds }}s）</span>
        </label>

        <button class="btn" @click="runOnce" :disabled="runningOnce">{{ runningOnce ? '执行中...' : '立即抓取一次' }}</button>
        <button class="btn btn-secondary" @click="loadLatest">手动刷新</button>
      </div>

      <div class="status-row">
        <span class="badge" :class="healthOk ? 'ok' : 'warn'">{{ healthOk ? '服务正常' : '服务异常/降级' }}</span>
        <span>最近执行: {{ stats.last_run?.at || '-' }}</span>
        <span v-if="stats.last_run?.degraded" class="warn-text">降级: {{ (stats.last_run?.degrade_reasons || []).join(' | ') || '外部源不可达' }}</span>
      </div>

      <div v-if="errorMsg" class="error-box">{{ errorMsg }}</div>
    </div>

    <div class="layout">
      <div class="list card">
        <div class="list-title">快讯列表（{{ items.length }}）</div>
        <div v-if="loading" class="loading">加载中...</div>
        <div v-else-if="items.length === 0" class="empty">
          暂无可展示数据。
          <div v-if="stats.last_run?.degraded" class="warn-text">当前处于降级模式：外部源不可达时会显示此提示，请稍后重试或检查网络/代理。</div>
        </div>

        <div v-else class="news-list">
          <div class="news-item" v-for="it in items" :key="`${it.id}-${it.publish_time}`">
            <div class="meta">
              <span class="source" :class="it.source_key">{{ sourceName(it.source_key) }}</span>
              <span class="time">{{ fmtTime(it.publish_time) }}</span>
            </div>
            <div class="title">{{ it.title }}</div>
            <a v-if="it.url" :href="it.url" target="_blank" rel="noopener noreferrer" class="link">原文链接</a>
          </div>
        </div>
      </div>

      <div class="iframe card">
        <div class="list-title">来源站点（配置接线）</div>
        <div class="row iframe-row">
          <button class="btn btn-secondary" @click="activeProvider = 'jin10'">金十</button>
          <button class="btn btn-secondary" @click="activeProvider = 'fx678'">汇通</button>
          <a v-if="activeIframeUrl" :href="activeIframeUrl" target="_blank" rel="noopener noreferrer">新窗口打开</a>
        </div>

        <iframe
          v-if="activeIframeUrl"
          :src="activeIframeUrl"
          class="embed"
          referrerpolicy="no-referrer-when-downgrade"
          @error="iframeError = true"
        />
        <div v-if="iframeError" class="warn-text">该站点可能禁止 iframe 嵌入，请点击“新窗口打开”。</div>
      </div>
    </div>
  </div>
</template>

<script>
import { onMounted, onUnmounted, ref, computed, watch } from 'vue'

export default {
  name: 'RealtimeFlashView',
  setup() {
    const source = ref('all')
    const limit = ref(50)
    const items = ref([])
    const loading = ref(false)
    const runningOnce = ref(false)
    const autoRefresh = ref(true)
    const refreshSeconds = ref(30)
    const errorMsg = ref('')
    const healthOk = ref(true)
    const stats = ref({ last_run: {} })
    const timer = ref(null)

    const iframeConfig = ref({ enabled: true, providers: {}, default_provider: 'jin10' })
    const activeProvider = ref('jin10')
    const iframeError = ref(false)

    const sourceName = (key) => {
      if (key === 'jin10') return '金十'
      if (key === 'fx678') return '汇通'
      return key || '未知'
    }

    const fmtTime = (t) => {
      if (!t) return '-'
      return String(t).replace('T', ' ').slice(0, 19)
    }

    const apiBase = () => `http://${window.location.hostname}:8000`

    const activeIframeUrl = computed(() => {
      const p = iframeConfig.value?.providers?.[activeProvider.value]
      return p?.iframe_url || ''
    })

    const loadIframeConfig = async () => {
      try {
        const resp = await fetch(`${apiBase()}/api/realtime-flash/iframe-config`)
        const data = await resp.json()
        iframeConfig.value = data.config || iframeConfig.value
        refreshSeconds.value = Number(iframeConfig.value.refresh_seconds || 30)
        activeProvider.value = iframeConfig.value.default_provider || 'jin10'
      } catch (e) {
        // 配置不可用时不阻塞主体
        console.warn('iframe config load failed', e)
      }
    }

    const loadHealth = async () => {
      try {
        const resp = await fetch(`${apiBase()}/api/realtime-flash/health`)
        const data = await resp.json()
        healthOk.value = !!data.ok
      } catch (e) {
        healthOk.value = false
      }
    }

    const loadStats = async () => {
      try {
        const resp = await fetch(`${apiBase()}/api/realtime-flash/stats`)
        const data = await resp.json()
        stats.value = data || { last_run: {} }
      } catch (e) {
        console.warn('stats load failed', e)
      }
    }

    const loadLatest = async () => {
      loading.value = true
      errorMsg.value = ''
      try {
        const q = new URLSearchParams({ limit: String(limit.value), source: source.value })
        const resp = await fetch(`${apiBase()}/api/realtime-flash/latest?${q.toString()}`)
        const data = await resp.json()
        items.value = data.items || []
      } catch (e) {
        errorMsg.value = `拉取快讯失败：${e?.message || e}`
      } finally {
        loading.value = false
      }
    }

    const runOnce = async () => {
      runningOnce.value = true
      errorMsg.value = ''
      try {
        const resp = await fetch(`${apiBase()}/api/realtime-flash/run-once`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ max_items: limit.value, ws_wait_seconds: 4 })
        })
        const data = await resp.json()
        if (!resp.ok || !data.ok) {
          throw new Error(data?.detail?.error || data?.message || 'run-once failed')
        }
        if (data.degraded) {
          errorMsg.value = `降级提示：${(data.degrade_reasons || []).join(' | ') || '外部源不可达'}`
        }
      } catch (e) {
        errorMsg.value = `执行 run-once 失败：${e?.message || e}`
      } finally {
        runningOnce.value = false
        await Promise.all([loadLatest(), loadStats(), loadHealth()])
      }
    }

    const restartTimer = () => {
      if (timer.value) {
        clearInterval(timer.value)
        timer.value = null
      }
      if (autoRefresh.value) {
        timer.value = setInterval(async () => {
          await Promise.all([loadLatest(), loadStats(), loadHealth()])
        }, Math.max(5, Number(refreshSeconds.value || 30)) * 1000)
      }
    }

    watch(autoRefresh, restartTimer)
    watch(refreshSeconds, restartTimer)

    onMounted(async () => {
      await loadIframeConfig()
      await Promise.all([loadHealth(), loadStats(), loadLatest()])
      restartTimer()
    })

    onUnmounted(() => {
      if (timer.value) clearInterval(timer.value)
    })

    return {
      source,
      limit,
      items,
      loading,
      runningOnce,
      autoRefresh,
      refreshSeconds,
      errorMsg,
      healthOk,
      stats,
      sourceName,
      fmtTime,
      loadLatest,
      runOnce,
      activeProvider,
      activeIframeUrl,
      iframeError,
    }
  }
}
</script>

<style scoped>
.realtime-flash-page { color: #e2e8f0; }
.header { margin-bottom: 12px; }
.desc { color: #94a3b8; font-size: 13px; }
.card {
  background: rgba(15, 23, 42, 0.7);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 12px;
  margin-bottom: 12px;
}
.row { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.status-row { margin-top: 10px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; font-size: 12px; color: #cbd5e1; }
.switch { display: inline-flex; gap: 6px; align-items: center; }
.btn {
  background: #2563eb;
  color: #fff;
  border: none;
  border-radius: 8px;
  padding: 6px 12px;
  cursor: pointer;
}
.btn:disabled { opacity: 0.6; cursor: not-allowed; }
.btn-secondary { background: #334155; }
.badge { padding: 2px 8px; border-radius: 999px; font-size: 12px; }
.badge.ok { background: rgba(34,197,94,.2); color: #86efac; }
.badge.warn { background: rgba(251,191,36,.2); color: #fde68a; }
.error-box { margin-top: 8px; background: rgba(239,68,68,.15); color: #fecaca; padding: 8px; border-radius: 8px; }
.layout { display: grid; grid-template-columns: 1.2fr 1fr; gap: 12px; }
.list-title { font-size: 14px; font-weight: 600; margin-bottom: 8px; }
.news-list { max-height: 650px; overflow: auto; }
.news-item { border-bottom: 1px solid rgba(148,163,184,.12); padding: 10px 0; }
.meta { display: flex; gap: 8px; font-size: 12px; color: #94a3b8; margin-bottom: 4px; }
.source { padding: 1px 6px; border-radius: 999px; }
.source.jin10 { background: rgba(59,130,246,.2); color: #93c5fd; }
.source.fx678 { background: rgba(16,185,129,.2); color: #86efac; }
.title { line-height: 1.5; }
.link { color: #93c5fd; font-size: 12px; }
.warn-text { color: #fbbf24; font-size: 12px; }
.embed { width: 100%; height: 700px; border: 0; border-radius: 8px; background: #020617; }
.iframe-row { margin-bottom: 8px; }
@media (max-width: 1200px) {
  .layout { grid-template-columns: 1fr; }
  .embed { height: 520px; }
}
</style>
