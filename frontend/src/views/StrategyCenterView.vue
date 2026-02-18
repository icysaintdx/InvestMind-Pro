<template>
  <div class="strategy-center">
    <!-- 页面标题 -->
    <div class="page-header">
      <div class="header-left">
        <h1 class="page-title"><span class="title-icon">🎯</span>策略中心</h1>
        <p class="page-desc">智能策略管理与自动交易 | 共 {{ strategies?.length || 0 }} 个策略 | {{ runningPlansCount }} 个计划运行中</p>
      </div>
      <div class="header-actions">
        <!-- 实时刷新状态指示器 -->
        <div class="realtime-status" :class="{ trading: tradingStatus?.isTrading, refreshing: isAutoRefreshing }">
          <span class="status-dot" :class="{ active: realtimeRefreshEnabled && tradingStatus?.isTrading }"></span>
          <span class="status-text">{{ getRefreshStatusText() }}</span>
          <button @click="toggleRealtimeRefresh" class="refresh-toggle-btn" :title="realtimeRefreshEnabled ? '关闭实时刷新' : '开启实时刷新'">
            {{ realtimeRefreshEnabled ? '🔄' : '⏸️' }}
          </button>
          <button @click="manualRefresh" class="manual-refresh-btn" title="立即刷新" :disabled="isAutoRefreshing">
            🔃
          </button>
        </div>
        <button @click="showParseModal = true" class="action-btn parse-btn">
          <span class="btn-icon">🤖</span><span class="btn-text">AI解析策略</span>
        </button>
        <button @click="showCreateModal = true" class="action-btn create-btn">
          <span class="btn-icon">➕</span><span class="btn-text">创建策略</span>
        </button>
      </div>
    </div>

    <!-- 第一排：K线图区域（全宽） -->
    <div class="chart-row">
      <div class="chart-section">
        <div class="section-header">
          <h2 class="section-title">📊 K线图分析</h2>
          <div class="chart-controls">
            <input v-model="chartStockCode" type="text" placeholder="股票代码" class="stock-input" @keyup.enter="loadChartData" />
            <div class="period-buttons">
              <button v-for="period in periods" :key="period.value" @click="selectPeriod(period.value)"
                :class="['period-btn', { active: chartPeriod === period.value }]">{{ period.label }}</button>
            </div>
            <button @click="loadChartData" class="load-btn">
              <span v-if="isLoadingChart" class="loading-icon">⏳</span><span v-else>加载</span>
            </button>
          </div>
        </div>

<div class="indicator-toggles">
          <span class="toggle-label">均线：</span>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.ma5" @change="renderChart" /><span class="toggle-text ma5">MA5</span></label>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.ma20" @change="renderChart" /><span class="toggle-text ma20">MA20</span></label>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.ma60" @change="renderChart" /><span class="toggle-text ma60">MA60</span></label>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.boll" @change="renderChart" /><span class="toggle-text boll">布林带</span></label>
          <span class="toggle-divider">|</span>
          <span class="toggle-label">副图：</span>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.macd" @change="renderChart" /><span class="toggle-text macd">MACD</span></label>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.rsi" @change="renderChart" /><span class="toggle-text rsi">RSI</span></label>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.kdj" @change="renderChart" /><span class="toggle-text kdj">KDJ</span></label>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.sixPulse" @change="renderChart" /><span class="toggle-text sixpulse">⚔️六脉神剑</span></label>
          <span class="toggle-divider">|</span>
          <span class="toggle-label">标注：</span>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.showSignals" @change="renderChart" /><span class="toggle-text signals">信号</span></label>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.showPatterns" @change="renderChart" /><span class="toggle-text patterns">形态</span></label>
          <label class="toggle-item"><input type="checkbox" v-model="indicatorToggles.showLargeOrders" @change="renderChart" /><span class="toggle-text largeorders">🏛️机构大单</span></label>
        </div>

        <!-- K线图工具栏 -->
        <div class="chart-toolbar">
          <div class="toolbar-group">
            <span class="toolbar-label">标记工具：</span>
            <button @click="showPriceMarkerModal = true" class="toolbar-btn" title="添加价格标记">📍 添加标记</button>
            <button @click="autoDetectKeyLevels" class="toolbar-btn highlight" title="自动识别关键点位">🔍 自动识别</button>
          </div>
          <div class="toolbar-group">
            <span class="toolbar-label">快捷标记：</span>
            <button @click="addSupportLine(chartData[chartData.length-1]?.close)" class="toolbar-btn support" title="添加支撑位">📉 支撑位</button>
            <button @click="addResistanceLine(chartData[chartData.length-1]?.close)" class="toolbar-btn resistance" title="添加压力位">📈 压力位</button>
          </div>
          <div class="toolbar-group">
            <button @click="captureChart" class="toolbar-btn" title="保存截图">📷 截图</button>
            <button @click="clearMarkers" class="toolbar-btn danger" title="清除所有标记">🗑️ 清除</button>
          </div>
        </div>

        <div class="chart-container" :style="{ height: chartHeight + 'px' }">
          <div class="kline-chart" ref="chartContainer" :style="{ height: chartHeight + 'px' }"></div>
          <div v-if="isLoadingChart" class="chart-overlay chart-loading"><div class="spinner"></div><p>加载K线数据中...</p></div>
          <div v-else-if="chartError" class="chart-overlay chart-error"><p>⚠️ {{ chartError }}</p></div>
          <div v-else-if="!chartData || chartData.length === 0" class="chart-overlay chart-empty"><span class="empty-icon">📈</span><p>输入股票代码加载K线图</p></div>
        </div>

<div class="indicator-display" v-if="chartData && chartData.length > 0">
          <span class="ind-label">MA5:</span><span class="ind-value ma5">{{ currentIndicators.MA5?.toFixed(2) || '-' }}</span>
          <span class="ind-label">MA10:</span><span class="ind-value ma10">{{ currentIndicators.MA10?.toFixed(2) || '-' }}</span>
          <span class="ind-label">MA20:</span><span class="ind-value ma20">{{ currentIndicators.MA20?.toFixed(2) || '-' }}</span>
          <span class="ind-divider">|</span>
          <span class="ind-label">RSI:</span><span :class="['ind-value', getRSIClass(currentIndicators.RSI)]">{{ currentIndicators.RSI?.toFixed(1) || '-' }}</span>
          <span class="ind-label">MACD:</span><span :class="['ind-value', currentIndicators.MACD > 0 ? 'positive' : 'negative']">{{ currentIndicators.MACD?.toFixed(3) || '-' }}</span>
          <span class="ind-divider" v-if="dataSource">|</span>
          <span class="ind-label" v-if="dataSource">数据源:</span><span class="ind-value data-source" v-if="dataSource">{{ dataSource }}</span>
          <span class="ind-label" style="margin-left: 8px;">成交量:</span>
          <span :class="['ind-value', getVolumeClass()]">{{ getVolumeStatus() }}</span>
          <!-- 信号汇总 -->
          <template v-if="signalSummary && signalSummary.total > 0">
            <span class="ind-divider">|</span>
            <span class="ind-label">信号:</span>
            <span class="signal-count bullish">📈{{ signalSummary.bullish }}</span>
            <span class="signal-count bearish">📉{{ signalSummary.bearish }}</span>
            <span :class="['signal-recommendation', signalSummary.recommendation.toLowerCase()]">
              {{ signalSummary.recommendation === 'BUY' ? '🟢看多' : (signalSummary.recommendation === 'SELL' ? '🔴看空' : '⚪观望') }}
            </span>
          </template>
        </div>
        
        <!-- 六脉神剑综合指标面板 -->
        <div class="six-pulse-panel" v-if="sixPulseIndicators && sixPulseIndicators.length > 0">
          <div class="panel-header-mini">
            <h3 class="panel-title-mini">⚔️ 六脉神剑综合指标</h3>
            <span class="panel-subtitle">融合6大核心指标的多维度共振分析</span>
          </div>
          <div class="pulse-indicators">
            <div class="pulse-item" v-for="(item, idx) in sixPulseIndicators" :key="idx" :title="item.description">
              <span class="pulse-name">{{ item.name }}</span>
              <span class="pulse-value">{{ item.value }}</span>
              <span :class="['pulse-status', item.status]">{{ item.statusText }}</span>
            </div>
          </div>
          <div class="pulse-summary">
            <span class="bullish-count">📈 多头: {{ sixPulseSummary.bullish }}</span>
            <span class="bearish-count">📉 空头: {{ sixPulseSummary.bearish }}</span>
            <span :class="['signal-badge', sixPulseSummary.signal.toLowerCase()]">
              {{ sixPulseSummary.signalText }}
            </span>
          </div>
          <div class="pulse-hint">
            <span class="hint-text">💡 当≥4个指标同时发出多头/空头信号时，趋势确定性≥90%</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 第二排：策略列表 + 右侧双面板 -->
    <div class="main-content">
      <!-- 左侧：策略列表 -->
      <div class="strategy-panel">
        <div class="panel-header">
          <h2 class="panel-title">📋 策略列表</h2>
        </div>
        <div class="category-filter">
          <button v-for="cat in categories" :key="cat.value"
            @click="selectedCategory = cat.value === selectedCategory ? null : cat.value"
            :class="['category-btn', { active: selectedCategory === cat.value }]">
            <span class="cat-icon">{{ cat.icon }}</span>
            <span class="cat-label">{{ cat.label }}</span>
            <span class="cat-count">{{ cat.count }}</span>
          </button>
        </div>

        <div class="strategy-list">
          <div v-for="strategy in filteredStrategies" :key="strategy.id"
            @click="selectStrategy(strategy)"
            :class="['strategy-card', { active: selectedStrategy?.id === strategy.id }]">
            <div class="card-header">
              <span class="strategy-icon">{{ strategy.icon || '📊' }}</span>
              <div class="strategy-info">
                <h3 class="strategy-name">{{ strategy.name }}</h3>
                <span :class="['strategy-source', strategy.source]">{{ getSourceLabel(strategy.source) }}</span>
              </div>
            </div>
            <p class="strategy-desc">{{ strategy.description }}</p>
            <div class="strategy-meta">
              <span class="meta-item"><span class="meta-icon">📈</span>{{ strategy.indicators?.length || 0 }} 指标</span>
              <span class="meta-item" v-if="strategy.avg_win_rate"><span class="meta-icon">🎯</span>{{ (strategy.avg_win_rate * 100).toFixed(0) }}% 胜率</span>
            </div>
            <!-- 快捷创建计划按钮 -->
            <button v-if="selectedStrategy?.id === strategy.id" @click.stop="openCreatePlanModal(strategy)" class="quick-plan-btn">
              <span>⚡</span> 创建交易计划
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧：双面板布局 -->
      <div class="right-panels">
        <!-- 上方：交易计划面板 -->
        <div class="trading-plan-panel">
          <div class="panel-header">
            <h2 class="panel-title">🤖 交易计划</h2>
            <button @click="openCreatePlanModal(selectedStrategy)" :disabled="!selectedStrategy" class="create-plan-btn">
              <span>➕</span> 新建计划
            </button>
          </div>

          <!-- 运行中的计划列表 -->
          <div class="plans-section">
            <h3 class="sub-title">运行中的计划 ({{ runningPlans.length }})</h3>
            <div class="plans-list" v-if="runningPlans.length > 0">
              <div v-for="plan in runningPlans" :key="plan.plan_id" class="plan-card running">
                <div class="plan-header">
                  <div class="plan-info">
                    <span class="plan-stock">{{ plan.stock_name || plan.stock_code }}</span>
                    <span class="plan-strategy">{{ plan.strategy_name }}</span>
                  </div>
                  <span :class="['plan-status', plan.status]">{{ getStatusLabel(plan.status) }}</span>
                </div>
                <div class="plan-stats">
                  <div class="stat-item">
                    <span class="stat-label">信号</span>
                    <span class="stat-value">{{ plan.signals_generated }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">成交</span>
                    <span class="stat-value">{{ plan.trades_executed }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-label">盈亏</span>
                    <span :class="['stat-value', plan.total_profit_loss >= 0 ? 'profit' : 'loss']">
                      {{ plan.total_profit_loss >= 0 ? '+' : '' }}{{ plan.total_profit_loss?.toFixed(2) || '0.00' }}
                    </span>
                  </div>
                </div>
                <div class="plan-actions">
                  <button @click="pausePlan(plan.plan_id)" class="plan-btn pause" title="暂停">⏸️</button>
                  <button @click="stopPlan(plan.plan_id)" class="plan-btn stop" title="停止">⏹️</button>
                  <button @click="viewPlanDetail(plan)" class="plan-btn detail" title="详情">📋</button>
                </div>
              </div>
            </div>
            <div v-else class="empty-plans">
              <span class="empty-icon">🤖</span>
              <p>暂无运行中的计划</p>
            </div>
          </div>

          <!-- 已暂停/停止的计划 -->
          <div class="plans-section stopped-plans" v-if="stoppedPlans.length > 0">
            <h3 class="sub-title">已停止的计划 ({{ stoppedPlans.length }})</h3>
            <div class="plans-list">
              <div v-for="plan in stoppedPlans" :key="plan.plan_id" class="plan-card stopped">
                <div class="plan-header">
                  <div class="plan-info">
                    <span class="plan-stock">{{ plan.stock_name || plan.stock_code }}</span>
                    <span class="plan-strategy">{{ plan.strategy_name }}</span>
                  </div>
                  <span :class="['plan-status', plan.status]">{{ getStatusLabel(plan.status) }}</span>
                </div>
                <div class="plan-actions">
                  <button @click="startPlan(plan.plan_id)" class="plan-btn start" title="启动">▶️</button>
                  <button @click="deletePlan(plan.plan_id)" class="plan-btn delete" title="删除">🗑️</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 下方：策略详情面板 -->
        <div class="strategy-detail-panel">
          <div class="panel-header">
            <h2 class="panel-title">📊 策略详情</h2>
          </div>

          <div class="strategy-detail-content" v-if="selectedStrategy">
            <div class="detail-header">
              <span class="strategy-icon-large">{{ selectedStrategy.icon || '📊' }}</span>
              <div class="detail-title">
                <h3>{{ selectedStrategy.name }}</h3>
                <span :class="['strategy-source', selectedStrategy.source]">{{ getSourceLabel(selectedStrategy.source) }}</span>
              </div>
            </div>
            <p class="detail-desc">{{ selectedStrategy.description }}</p>

            <div class="detail-sections">
              <!-- 使用指标 -->
              <div class="detail-section">
                <h4 class="section-label">使用指标</h4>
                <div class="indicator-tags">
                  <span v-for="(ind, idx) in selectedStrategy.indicators" :key="idx" class="indicator-tag">
                    {{ ind.name }}
                  </span>
                </div>
              </div>

              <!-- 入场条件 -->
              <div class="detail-section" v-if="selectedStrategy.entry_conditions?.length">
                <h4 class="section-label">🟢 入场条件</h4>
                <div class="condition-list">
                  <div v-for="(cond, idx) in selectedStrategy.entry_conditions" :key="idx" class="condition-item entry">{{ cond.description }}</div>
                </div>
              </div>

              <!-- 出场条件 -->
              <div class="detail-section" v-if="selectedStrategy.exit_conditions?.length">
                <h4 class="section-label">🔴 出场条件</h4>
                <div class="condition-list">
                  <div v-for="(cond, idx) in selectedStrategy.exit_conditions" :key="idx" class="condition-item exit">{{ cond.description }}</div>
                </div>
              </div>

              <!-- 风险参数 -->
              <div class="detail-section" v-if="selectedStrategy.risk_params">
                <h4 class="section-label">⚠️ 风险参数</h4>
                <div class="risk-params">
                  <div class="risk-item"><span class="risk-label">止损</span><span class="risk-value loss">{{ (selectedStrategy.risk_params.stop_loss * 100).toFixed(1) }}%</span></div>
                  <div class="risk-item"><span class="risk-label">止盈</span><span class="risk-value profit">{{ (selectedStrategy.risk_params.take_profit * 100).toFixed(1) }}%</span></div>
                  <div class="risk-item"><span class="risk-label">最大仓位</span><span class="risk-value">{{ (selectedStrategy.risk_params.max_position * 100).toFixed(0) }}%</span></div>
                </div>
              </div>
            </div>

            <!-- 信号生成区 -->
            <div class="signal-section">
              <h4 class="section-label">🎯 生成交易信号</h4>
              <div class="signal-form">
                <div class="form-row">
                  <input v-model="signalForm.stockCode" type="text" placeholder="股票代码" class="form-input" />
                  <button @click="generateSignal" :disabled="!signalForm.stockCode || isGenerating" class="generate-btn">
                    <span v-if="isGenerating">⏳</span><span v-else>🚀</span>
                    {{ isGenerating ? '生成中...' : '生成信号' }}
                  </button>
                </div>
              </div>

              <div v-if="signalResult && signalResult.action" class="signal-result">
                <div :class="['signal-action', (signalResult.action || 'hold').toLowerCase()]">
                  <span class="action-icon">{{ getActionIcon(signalResult.action) }}</span>
                  <span class="action-text">{{ getActionText(signalResult.action) }}</span>
                </div>
                <div class="signal-metrics">
                  <div class="metric"><span class="metric-label">置信度</span><span class="metric-value">{{ (signalResult.confidence * 100).toFixed(0) }}%</span></div>
                </div>
              </div>
            </div>
          </div>

          <div class="empty-strategy" v-else>
            <span class="empty-icon">👈</span>
            <p>从左侧选择策略查看详情</p>
          </div>
        </div>
      </div>
    </div>

    <!-- AI解析策略模态框 -->
    <div v-if="showParseModal" class="modal-overlay" @click.self="showParseModal = false">
      <div class="modal-content parse-modal">
        <div class="modal-header"><h2>🤖 AI解析策略</h2><button @click="showParseModal = false" class="close-btn">✕</button></div>
        <div class="modal-body">
          <p class="modal-desc">输入您的交易策略描述，AI将自动解析并转换为标准化格式</p>
          <textarea v-model="parseText" placeholder="例如：当MACD金叉且RSI低于30时买入，当RSI高于70或MACD死叉时卖出，止损5%，止盈15%..." class="parse-textarea" rows="8"></textarea>
          <div class="modal-actions">
            <button @click="showParseModal = false" class="cancel-btn">取消</button>
            <button @click="parseStrategy" :disabled="!parseText || isParsing" class="confirm-btn">{{ isParsing ? '解析中...' : '开始解析' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建/编辑策略模态框 -->
    <div v-if="showCreateModal" class="modal-overlay" @click.self="showCreateModal = false">
      <div class="modal-content create-modal">
        <div class="modal-header"><h2>{{ editingStrategy ? '✏️ 编辑策略' : '➕ 创建策略' }}</h2><button @click="showCreateModal = false" class="close-btn">✕</button></div>
        <div class="modal-body">
          <div class="form-group"><label>策略名称</label><input v-model="strategyForm.name" type="text" placeholder="输入策略名称" class="form-input" /></div>
          <div class="form-group"><label>策略描述</label><textarea v-model="strategyForm.description" placeholder="描述策略的核心思想" class="form-textarea" rows="3"></textarea></div>
          <div class="form-group"><label>策略类别</label>
            <select v-model="strategyForm.category" class="form-select">
              <option value="technical">技术分析</option><option value="value_investing">价值投资</option>
              <option value="trend_following">趋势跟踪</option><option value="folk_strategy">民间策略</option>
              <option value="institutional">机构持仓</option><option value="custom">自定义</option>
            </select>
          </div>
          <div class="modal-actions">
            <button @click="showCreateModal = false" class="cancel-btn">取消</button>
            <button @click="saveStrategy" :disabled="!strategyForm.name" class="confirm-btn">{{ editingStrategy ? '保存修改' : '创建策略' }}</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 价格标记模态框 -->
    <div v-if="showPriceMarkerModal" class="modal-overlay" @click.self="showPriceMarkerModal = false">
      <div class="modal-content marker-modal">
        <div class="modal-header"><h2>📍 添加价格标记</h2><button @click="showPriceMarkerModal = false" class="close-btn">✕</button></div>
        <div class="modal-body">
          <p class="modal-desc">在K线图上添加关键价格点位标记</p>
          
          <div class="form-group">
            <label>标记类型</label>
            <div class="marker-type-grid">
              <button @click="priceMarkerForm.type = 'support'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'support' }]">
                <span class="type-icon">📉</span><span class="type-label">支撑位</span>
              </button>
              <button @click="priceMarkerForm.type = 'resistance'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'resistance' }]">
                <span class="type-icon">📈</span><span class="type-label">压力位</span>
              </button>
              <button @click="priceMarkerForm.type = 'high'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'high' }]">
                <span class="type-icon">🔺</span><span class="type-label">高点</span>
              </button>
              <button @click="priceMarkerForm.type = 'low'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'low' }]">
                <span class="type-icon">🔻</span><span class="type-label">低点</span>
              </button>
              <button @click="priceMarkerForm.type = 'buy'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'buy' }]">
                <span class="type-icon">🟢</span><span class="type-label">买入点</span>
              </button>
              <button @click="priceMarkerForm.type = 'sell'" :class="['marker-type-btn', { active: priceMarkerForm.type === 'sell' }]">
                <span class="type-icon">🔴</span><span class="type-label">卖出点</span>
              </button>
            </div>
          </div>
          
          <div class="form-group">
            <label>价格</label>
            <input v-model="priceMarkerForm.price" type="number" step="0.01" placeholder="输入价格" class="form-input" />
          </div>
          
          <div class="form-group">
            <label>标签（可选）</label>
            <input v-model="priceMarkerForm.label" type="text" placeholder="自定义标签文字" class="form-input" />
          </div>
          
          <div class="modal-actions">
            <button @click="showPriceMarkerModal = false" class="cancel-btn">取消</button>
            <button @click="addPriceMarkerFromForm" :disabled="!priceMarkerForm.price" class="confirm-btn">添加标记</button>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建交易计划模态框 -->
    <div v-if="showCreatePlanModal" class="modal-overlay" @click.self="showCreatePlanModal = false">
      <div class="modal-content plan-modal">
        <div class="modal-header">
          <h2>⚡ 创建交易计划</h2>
          <button @click="showCreatePlanModal = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body">
          <div class="plan-form-header">
            <div class="plan-strategy-info">
              <span class="strategy-icon">{{ planForm.strategy?.icon || '📊' }}</span>
              <div>
                <h3>{{ planForm.strategy?.name || '未选择策略' }}</h3>
                <p>{{ planForm.strategy?.description }}</p>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>股票代码 <span class="required">*</span></label>
            <input v-model="planForm.stockCode" type="text" placeholder="输入股票代码，如 600519" class="form-input" />
          </div>

          <div class="form-group">
            <label>股票名称</label>
            <input v-model="planForm.stockName" type="text" placeholder="股票名称（可选）" class="form-input" />
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>分配资金</label>
              <input v-model.number="planForm.allocatedCapital" type="number" min="1000" step="1000" class="form-input" />
            </div>
            <div class="form-group">
              <label>最大仓位</label>
              <div class="input-with-suffix">
                <input v-model.number="planForm.maxPositionRatio" type="number" min="1" max="100" class="form-input" />
                <span class="suffix">%</span>
              </div>
            </div>
          </div>

          <div class="form-row">
            <div class="form-group">
              <label>止损比例</label>
              <div class="input-with-suffix">
                <input v-model.number="planForm.stopLossPct" type="number" min="1" max="50" step="0.5" class="form-input" />
                <span class="suffix">%</span>
              </div>
            </div>
            <div class="form-group">
              <label>止盈比例</label>
              <div class="input-with-suffix">
                <input v-model.number="planForm.takeProfitPct" type="number" min="1" max="100" step="0.5" class="form-input" />
                <span class="suffix">%</span>
              </div>
            </div>
          </div>

          <div class="form-group">
            <label>检查间隔（秒）</label>
            <input v-model.number="planForm.checkInterval" type="number" min="10" max="300" step="10" class="form-input" />
          </div>

          <div class="form-group">
            <label>决策模式</label>
            <div class="decision-mode-options">
              <label class="radio-option" :class="{ active: planForm.decisionMode === 'rule_only' }">
                <input type="radio" v-model="planForm.decisionMode" value="rule_only" />
                <span class="option-icon">📐</span>
                <span class="option-text">
                  <strong>纯规则</strong>
                  <small>规则触发即执行</small>
                </span>
              </label>
              <label class="radio-option" :class="{ active: planForm.decisionMode === 'rule_ai' }">
                <input type="radio" v-model="planForm.decisionMode" value="rule_ai" />
                <span class="option-icon">🤖</span>
                <span class="option-text">
                  <strong>规则+AI</strong>
                  <small>AI二次确认</small>
                </span>
              </label>
              <label class="radio-option" :class="{ active: planForm.decisionMode === 'ai_only' }">
                <input type="radio" v-model="planForm.decisionMode" value="ai_only" />
                <span class="option-icon">🧠</span>
                <span class="option-text">
                  <strong>纯AI</strong>
                  <small>AI自主判断</small>
                </span>
              </label>
            </div>
          </div>

          <div class="form-group">
            <label class="checkbox-label">
              <input type="checkbox" v-model="planForm.autoStart" />
              <span>创建后立即启动</span>
            </label>
          </div>

          <div class="modal-actions">
            <button @click="showCreatePlanModal = false" class="cancel-btn">取消</button>
            <button @click="createTradingPlan" :disabled="!planForm.stockCode || isCreatingPlan" class="confirm-btn">
              {{ isCreatingPlan ? '创建中...' : '创建计划' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 计划详情模态框 -->
    <div v-if="showPlanDetailModal" class="modal-overlay" @click.self="showPlanDetailModal = false">
      <div class="modal-content plan-detail-modal">
        <div class="modal-header">
          <h2>📋 计划详情</h2>
          <button @click="showPlanDetailModal = false" class="close-btn">✕</button>
        </div>
        <div class="modal-body" v-if="selectedPlanDetail">
          <div class="plan-detail-header">
            <div class="plan-basic-info">
              <h3>{{ selectedPlanDetail.stock_name || selectedPlanDetail.stock_code }}</h3>
              <span :class="['status-badge', selectedPlanDetail.status]">{{ getStatusLabel(selectedPlanDetail.status) }}</span>
            </div>
            <p class="plan-strategy-name">策略: {{ selectedPlanDetail.strategy_name }}</p>
          </div>

          <div class="plan-detail-grid">
            <div class="detail-item">
              <span class="label">分配资金</span>
              <span class="value">¥{{ selectedPlanDetail.initial_capital?.toLocaleString() }}</span>
            </div>
            <div class="detail-item">
              <span class="label">最大仓位</span>
              <span class="value">{{ (selectedPlanDetail.max_position_ratio * 100).toFixed(0) }}%</span>
            </div>
            <div class="detail-item">
              <span class="label">止损</span>
              <span class="value loss">{{ (selectedPlanDetail.stop_loss_pct * 100).toFixed(1) }}%</span>
            </div>
            <div class="detail-item">
              <span class="label">止盈</span>
              <span class="value profit">{{ (selectedPlanDetail.take_profit_pct * 100).toFixed(1) }}%</span>
            </div>
            <div class="detail-item">
              <span class="label">信号数</span>
              <span class="value">{{ selectedPlanDetail.signals_generated }}</span>
            </div>
            <div class="detail-item">
              <span class="label">成交数</span>
              <span class="value">{{ selectedPlanDetail.trades_executed }}</span>
            </div>
            <div class="detail-item">
              <span class="label">累计盈亏</span>
              <span :class="['value', selectedPlanDetail.total_profit_loss >= 0 ? 'profit' : 'loss']">
                {{ selectedPlanDetail.total_profit_loss >= 0 ? '+' : '' }}¥{{ selectedPlanDetail.total_profit_loss?.toFixed(2) }}
              </span>
            </div>
            <div class="detail-item">
              <span class="label">当前持仓</span>
              <span class="value">{{ selectedPlanDetail.current_position }}股</span>
            </div>
          </div>

          <div class="plan-indicators" v-if="selectedPlanDetail.last_indicators && Object.keys(selectedPlanDetail.last_indicators).length > 0">
            <h4>最新指标</h4>
            <div class="indicators-grid">
              <div v-for="(value, key) in selectedPlanDetail.last_indicators" :key="key" class="indicator-item">
                <span class="ind-name">{{ key }}</span>
                <span class="ind-value">{{ typeof value === 'number' ? value.toFixed(2) : value }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { useStrategyCenter } from './StrategyCenterView_logic.js'

export default {
  name: 'StrategyCenterView',
  setup() {
    return useStrategyCenter()
  }
}
</script>

<style src="./StrategyCenterView.css" scoped></style>