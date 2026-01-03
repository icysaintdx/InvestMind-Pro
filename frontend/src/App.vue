<template>
  <div id="app" class="min-h-screen bg-gradient-to-br from-slate-950 via-blue-950 to-slate-900">
    <!-- 粒子背景 -->
    <ParticleBackground 
      v-if="particlesEnabled"
      :enabled="particlesEnabled"
      :particleCount="particleCount"
      :particleColor="particleColor"
      :speed="particleSpeed"
    />
    
    <!-- 头部导航 - 新版精简设计 -->
    <header class="navbar-v2">
      <div class="navbar-v2-content">
        <!-- 左侧：Logo + 汉堡菜单(移动端) -->
        <div class="navbar-v2-left">
          <button @click="toggleMobileMenu" class="mobile-menu-btn">
            <span>☰</span>
          </button>
          <h1 class="logo" @click="currentView = 'analysis'">
            <span class="logo-icon">🏅</span>
            <span class="logo-text">InvestMind Pro</span>
          </h1>
          <span class="header-info-btn" @click="showProjectInfo = true" title="项目介绍">ℹ️</span>
          <span class="header-version-btn" @click="showChangelog = true" title="更新日志">v{{ versionInfo.version }}</span>
        </div>

        <!-- 右侧控制按钮 -->
        <div class="navbar-v2-right">
          <button @click="showHotRankModal = true" class="nav-v2-btn hot-btn" title="热榜">
            <span class="btn-icon">🔥</span>
            <span class="btn-label">热榜</span>
          </button>
          <button @click="showSettings = true" class="nav-v2-btn settings-btn" title="设置">
            <span class="btn-icon">⚙️</span>
            <span class="btn-label">设置</span>
          </button>
          <!-- Server状态悬浮 -->
          <div class="server-status-wrapper" @mouseenter="showServerStatus = true" @mouseleave="showServerStatus = false">
            <div :class="['server-status', backendStatus]">
              <span class="server-dot">●</span>
              <span class="server-text">Server</span>
            </div>
            <!-- 悬浮详情 -->
            <div v-show="showServerStatus" class="server-status-popup">
              <div class="popup-header">服务状态</div>
              <div class="popup-section">
                <div class="popup-label">后端连接</div>
                <div :class="['popup-status', backendStatus]">{{ backendStatusText }}</div>
              </div>
              <div class="popup-divider"></div>
              <div class="popup-section">
                <div class="popup-label">AI API</div>
                <div class="popup-items">
                  <span v-for="provider in ['gemini', 'deepseek', 'qwen', 'siliconflow']" :key="provider" :class="['popup-item', getStatusClass(apiStatus[provider])]">
                    <span class="item-dot">●</span>
                    <span class="item-name">{{ getProviderName(provider) }}</span>
                  </span>
                </div>
              </div>
              <div class="popup-divider"></div>
              <div class="popup-section">
                <div class="popup-label">数据源</div>
                <div class="popup-items">
                  <span v-for="channel in ['juhe', 'finnhub', 'tushare', 'akshare', 'cninfo']" :key="channel" :class="['popup-item', getStatusClass(dataChannelStatus[channel])]">
                    <span class="item-dot">●</span>
                    <span class="item-name">{{ getDataChannelName(channel) }}</span>
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 分组下拉导航 (折叠式) -->
    <nav v-if="menuMode === 'dropdown'" class="nav-v2-menu">
      <!-- 分析组 -->
      <div class="nav-group" @mouseenter="activeNavGroup = 'analysis'" @mouseleave="activeNavGroup = null">
        <button :class="['nav-group-btn', { active: isGroupActive('analysis') }]">
          <span class="group-icon">📊</span>
          <span class="group-text">分析</span>
          <span class="group-arrow">▼</span>
        </button>
        <div v-show="activeNavGroup === 'analysis'" class="nav-dropdown">
          <div class="nav-dropdown-inner">
            <button @click="currentView = 'analysis'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'analysis' }]">
              <span class="item-icon">📊</span>智能分析
            </button>
            <button @click="currentView = 'analysis-summary'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'analysis-summary' }]">
              <span class="item-icon">🧭</span>分析总结
            </button>
          </div>
        </div>
      </div>

      <!-- 交易组 -->
      <div class="nav-group" @mouseenter="activeNavGroup = 'trading'" @mouseleave="activeNavGroup = null">
        <button :class="['nav-group-btn', { active: isGroupActive('trading') }]">
          <span class="group-icon">📈</span>
          <span class="group-text">交易</span>
          <span class="group-arrow">▼</span>
        </button>
        <div v-show="activeNavGroup === 'trading'" class="nav-dropdown">
          <div class="nav-dropdown-inner">
            <button @click="currentView = 'backtest'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'backtest' }]">
              <span class="item-icon">📈</span>策略回测
            </button>
            <button @click="currentView = 'paper-trading'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'paper-trading' }]">
              <span class="item-icon">💼</span>模拟交易
            </button>
            <button @click="currentView = 'tracking-center'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'tracking-center' }]">
              <span class="item-icon">🔄</span>跟踪验证
            </button>
          </div>
        </div>
      </div>

      <!-- 市场组 -->
      <div class="nav-group" @mouseenter="activeNavGroup = 'market'" @mouseleave="activeNavGroup = null">
        <button :class="['nav-group-btn', { active: isGroupActive('market') }]">
          <span class="group-icon">💹</span>
          <span class="group-text">市场</span>
          <span class="group-arrow">▼</span>
        </button>
        <div v-show="activeNavGroup === 'market'" class="nav-dropdown">
          <div class="nav-dropdown-inner">
            <button @click="currentView = 'longhubang'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'longhubang' }]">
              <span class="item-icon">🐉</span>龙虎榜
            </button>
            <button @click="currentView = 'sector-rotation'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'sector-rotation' }]">
              <span class="item-icon">🔄</span>板块轮动
            </button>
            <button @click="currentView = 'sentiment'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'sentiment' }]">
              <span class="item-icon">💹</span>市场情绪
            </button>
            <button @click="currentView = 'unified-news'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'unified-news' }]">
              <span class="item-icon">📰</span>新闻中心
            </button>
            <button @click="currentView = 'market-data'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'market-data' }]">
              <span class="item-icon">📈</span>市场数据
            </button>
          </div>
        </div>
      </div>

      <!-- 工具组 -->
      <div class="nav-group" @mouseenter="activeNavGroup = 'tools'" @mouseleave="activeNavGroup = null">
        <button :class="['nav-group-btn', { active: isGroupActive('tools') }]">
          <span class="group-icon">🔧</span>
          <span class="group-text">工具</span>
          <span class="group-arrow">▼</span>
        </button>
        <div v-show="activeNavGroup === 'tools'" class="nav-dropdown">
          <div class="nav-dropdown-inner">
            <button @click="currentView = 'dataflow'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'dataflow' }]">
              <span class="item-icon">📊</span>数据流
            </button>
            <button @click="currentView = 'llm-config'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'llm-config' }]">
              <span class="item-icon">⚙️</span>LLM配置
            </button>
            <button @click="currentView = 'wencai'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'wencai' }]">
              <span class="item-icon">🔍</span>问财选股
            </button>
            <button @click="currentView = 'api-monitor'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'api-monitor' }]">
              <span class="item-icon">📡</span>接口监控
            </button>
          </div>
        </div>
      </div>

      <!-- 设置组 -->
      <div class="nav-group" @mouseenter="activeNavGroup = 'settings'" @mouseleave="activeNavGroup = null">
        <button :class="['nav-group-btn', { active: isGroupActive('settings') }]">
          <span class="group-icon">⚙️</span>
          <span class="group-text">设置</span>
          <span class="group-arrow">▼</span>
        </button>
        <div v-show="activeNavGroup === 'settings'" class="nav-dropdown">
          <div class="nav-dropdown-inner">
            <button @click="showApiConfig = true; activeNavGroup = null" class="dropdown-item">
              <span class="item-icon">🔑</span>API密钥配置
            </button>
            <button @click="showModelManager = true; activeNavGroup = null" class="dropdown-item">
              <span class="item-icon">🎯</span>模型管理
            </button>
            <button @click="showAgentConfig = true; activeNavGroup = null" class="dropdown-item">
              <span class="item-icon">🤖</span>智能体配置
            </button>
            <button @click="currentView = 'system-settings'; activeNavGroup = null" :class="['dropdown-item', { active: currentView === 'system-settings' }]">
              <span class="item-icon">🔧</span>系统设置
            </button>
            <div class="dropdown-divider"></div>
            <button @click="showDocuments = true; activeNavGroup = null" class="dropdown-item">
              <span class="item-icon">📚</span>文档中心
            </button>
            <button @click="showProjectInfo = true; activeNavGroup = null" class="dropdown-item">
              <span class="item-icon">ℹ️</span>项目介绍
            </button>
            <button @click="showChangelog = true; activeNavGroup = null" class="dropdown-item">
              <span class="item-icon">📋</span>更新日志
            </button>
          </div>
        </div>
      </div>

      <!-- 当前页面指示 -->
      <div class="current-page-indicator">
        <span class="indicator-icon">{{ getCurrentPageIcon() }}</span>
        <span class="indicator-text">{{ getCurrentPageName() }}</span>
      </div>
    </nav>

    <!-- 经典式平铺导航 -->
    <nav v-else class="nav-classic-menu">
      <button @click="currentView = 'analysis'" :class="['classic-tab', { active: currentView === 'analysis' }]">
        <span class="tab-icon">📊</span><span class="tab-text">智能分析</span>
      </button>
      <button @click="currentView = 'analysis-summary'" :class="['classic-tab', { active: currentView === 'analysis-summary' }]">
        <span class="tab-icon">🧭</span><span class="tab-text">分析总结</span>
      </button>
      <button @click="currentView = 'backtest'" :class="['classic-tab', { active: currentView === 'backtest' }]">
        <span class="tab-icon">📈</span><span class="tab-text">策略回测</span>
      </button>
      <button @click="currentView = 'paper-trading'" :class="['classic-tab', { active: currentView === 'paper-trading' }]">
        <span class="tab-icon">💼</span><span class="tab-text">模拟交易</span>
      </button>
      <button @click="currentView = 'tracking-center'" :class="['classic-tab', { active: currentView === 'tracking-center' }]">
        <span class="tab-icon">🔄</span><span class="tab-text">跟踪验证</span>
      </button>
      <button @click="currentView = 'longhubang'" :class="['classic-tab', { active: currentView === 'longhubang' }]">
        <span class="tab-icon">🐉</span><span class="tab-text">龙虎榜</span>
      </button>
      <button @click="currentView = 'sector-rotation'" :class="['classic-tab', { active: currentView === 'sector-rotation' }]">
        <span class="tab-icon">🔄</span><span class="tab-text">板块轮动</span>
      </button>
      <button @click="currentView = 'sentiment'" :class="['classic-tab', { active: currentView === 'sentiment' }]">
        <span class="tab-icon">💹</span><span class="tab-text">市场情绪</span>
      </button>
      <button @click="currentView = 'unified-news'" :class="['classic-tab', { active: currentView === 'unified-news' }]">
        <span class="tab-icon">📰</span><span class="tab-text">新闻中心</span>
      </button>
      <button @click="currentView = 'market-data'" :class="['classic-tab', { active: currentView === 'market-data' }]">
        <span class="tab-icon">📈</span><span class="tab-text">市场数据</span>
      </button>
      <button @click="currentView = 'dataflow'" :class="['classic-tab', { active: currentView === 'dataflow' }]">
        <span class="tab-icon">📊</span><span class="tab-text">数据流</span>
      </button>
      <button @click="currentView = 'llm-config'" :class="['classic-tab', { active: currentView === 'llm-config' }]">
        <span class="tab-icon">⚙️</span><span class="tab-text">LLM配置</span>
      </button>
      <button @click="currentView = 'wencai'" :class="['classic-tab', { active: currentView === 'wencai' }]">
        <span class="tab-icon">🔍</span><span class="tab-text">问财选股</span>
      </button>
      <button @click="currentView = 'api-monitor'" :class="['classic-tab', { active: currentView === 'api-monitor' }]">
        <span class="tab-icon">📡</span><span class="tab-text">接口监控</span>
      </button>
      <button @click="currentView = 'system-settings'" :class="['classic-tab', { active: currentView === 'system-settings' }]">
        <span class="tab-icon">🔧</span><span class="tab-text">系统设置</span>
      </button>
    </nav>

    <!-- 智能分析页面专属工具栏 -->
    <div v-if="currentView === 'analysis'" class="analysis-toolbar">
      <button @click="toggleLogWindow" :class="['toolbar-btn', { active: showLogWindow }]" title="实时日志">
        <span class="btn-icon">📡</span>
        <span class="btn-text">日志</span>
      </button>
      <button @click="showHistory = true" class="toolbar-btn" title="分析历史">
        <span class="btn-icon">📊</span>
        <span class="btn-text">历史</span>
      </button>
      <button @click="showAgentConfig = true" class="toolbar-btn" title="智能体配置">
        <span class="btn-icon">🤖</span>
        <span class="btn-text">智能体</span>
      </button>
      <button @click="toggleConfigMode" :class="['toolbar-btn', { active: configMode }]" title="配置模式">
        <span class="btn-icon">⚙️</span>
        <span class="btn-text">配置模式</span>
      </button>
    </div>

    <!-- 移动端菜单 -->
    <div v-if="showMobileMenu" class="mobile-menu-overlay" @click="showMobileMenu = false">
      <div class="mobile-menu" @click.stop>
        <div class="mobile-menu-header">
          <span class="mobile-menu-title">导航菜单</span>
          <button @click="showMobileMenu = false" class="mobile-menu-close">✕</button>
        </div>
        <div class="mobile-menu-content">
          <!-- 分析 -->
          <div class="mobile-menu-group">
            <div class="mobile-group-title">📊 分析</div>
            <button @click="currentView = 'analysis'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'analysis' }]">智能分析</button>
            <button @click="currentView = 'analysis-summary'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'analysis-summary' }]">分析总结</button>
          </div>
          <!-- 交易 -->
          <div class="mobile-menu-group">
            <div class="mobile-group-title">📈 交易</div>
            <button @click="currentView = 'backtest'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'backtest' }]">策略回测</button>
            <button @click="currentView = 'paper-trading'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'paper-trading' }]">模拟交易</button>
            <button @click="currentView = 'tracking-center'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'tracking-center' }]">跟踪验证</button>
          </div>
          <!-- 市场 -->
          <div class="mobile-menu-group">
            <div class="mobile-group-title">💹 市场</div>
            <button @click="currentView = 'longhubang'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'longhubang' }]">龙虎榜</button>
            <button @click="currentView = 'sector-rotation'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'sector-rotation' }]">板块轮动</button>
            <button @click="currentView = 'sentiment'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'sentiment' }]">市场情绪</button>
            <button @click="currentView = 'unified-news'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'unified-news' }]">新闻中心</button>
            <button @click="currentView = 'market-data'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'market-data' }]">市场数据</button>
          </div>
          <!-- 工具 -->
          <div class="mobile-menu-group">
            <div class="mobile-group-title">🔧 工具</div>
            <button @click="currentView = 'dataflow'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'dataflow' }]">数据流</button>
            <button @click="currentView = 'llm-config'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'llm-config' }]">LLM配置</button>
            <button @click="currentView = 'wencai'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'wencai' }]">问财选股</button>
            <button @click="currentView = 'api-monitor'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'api-monitor' }]">接口监控</button>
          </div>
          <!-- 设置 -->
          <div class="mobile-menu-group">
            <div class="mobile-group-title">⚙️ 设置</div>
            <button @click="showApiConfig = true; showMobileMenu = false" class="mobile-menu-item">API密钥配置</button>
            <button @click="showModelManager = true; showMobileMenu = false" class="mobile-menu-item">模型管理</button>
            <button @click="showAgentConfig = true; showMobileMenu = false" class="mobile-menu-item">智能体配置</button>
            <button @click="currentView = 'system-settings'; showMobileMenu = false" :class="['mobile-menu-item', { active: currentView === 'system-settings' }]">系统设置</button>
            <div class="mobile-menu-divider"></div>
            <button @click="showDocuments = true; showMobileMenu = false" class="mobile-menu-item">文档中心</button>
            <button @click="showProjectInfo = true; showMobileMenu = false" class="mobile-menu-item">项目介绍</button>
            <button @click="showChangelog = true; showMobileMenu = false" class="mobile-menu-item">更新日志</button>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 主内容区 -->
    <main class="pt-32 container mx-auto px-4 pb-8">
      <AnalysisView v-if="currentView === 'analysis'" />
      <AnalysisSummaryView 
        v-if="currentView === 'analysis-summary'"
        @goto-backtest="handleGotoBacktest"
        @goto-paper-trading="handleGotoPaperTrading"
        @goto-tracking="handleGotoTracking"
        @goto-analysis="() => currentView = 'analysis'"
      />
      <DataFlowView v-if="currentView === 'dataflow'" />
      <BacktestView 
        v-if="currentView === 'backtest'"
        :integrationContext="integrationContext"
      />
      <PaperTradingView 
        v-if="currentView === 'paper-trading'"
        :integrationContext="integrationContext"
      />
      <TrackingCenterView 
        v-if="currentView === 'tracking-center'"
        :integrationContext="integrationContext"
      />
      <LLMConfigView v-if="currentView === 'llm-config'" />
      <LonghubangView v-if="currentView === 'longhubang'" />
      <WencaiSelectorView v-if="currentView === 'wencai'" />
      <SectorRotationView v-if="currentView === 'sector-rotation'" />
      <MarketSentimentView v-if="currentView === 'sentiment'" />
      <UnifiedNewsView v-if="currentView === 'unified-news'" />
      <MarketDataView v-if="currentView === 'market-data'" />
      <SystemSettingsView v-if="currentView === 'system-settings'" @show-project-info="showProjectInfo = true" @show-changelog="showChangelog = true" />
      <ApiMonitorView v-if="currentView === 'api-monitor'" />
    </main>
    
    <!-- 更新日志模态框 -->
    <div v-if="showChangelog" class="modal-overlay" @click.self="showChangelog = false">
      <div class="changelog-modal">
        <button @click="showChangelog = false" class="modal-close-btn">×</button>
        <ChangelogView />
      </div>
    </div>

    <!-- 项目介绍模态框 -->
    <div v-if="showProjectInfo" class="modal-overlay" @click.self="showProjectInfo = false">
      <div class="project-info-modal">
        <button @click="showProjectInfo = false" class="modal-close-btn">×</button>
        <ProjectInfoView />
      </div>
    </div>

    <!-- 文档中心模态框 -->
    <div v-if="showDocuments" class="modal-overlay" @click.self="showDocuments = false">
      <div class="document-modal">
        <button @click="showDocuments = false" class="modal-close-btn">×</button>
        <DocumentView />
      </div>
    </div>
    
    <!-- 历史记录模态框 -->
    <div v-if="showHistory" class="modal-overlay" @click.self="showHistory = false">
      <div class="history-modal">
        <button @click="showHistory = false" class="modal-close-btn">×</button>
        <HistoryView />
      </div>
    </div>

    <!-- 数据透明化面板 -->
    <StockDataPanel ref="stockDataPanel" :stockData="currentStockData" />
    <NewsDataPanel ref="newsDataPanel" />
    
    <!-- 热榜模态框 -->
    <HotRankModal :isOpen="showHotRankModal" @close="showHotRankModal = false" />
    
    <!-- 智能体配置面板 -->
    <AgentConfigPanel :visible="showAgentConfig" @close="showAgentConfig = false" @save="handleAgentConfigSave" />

    <!-- 模型管理面板 -->
    <ModelManager :visible="showModelManager" @close="showModelManager = false" @save="handleModelSave" />

    <!-- API配置面板 -->
    <ApiConfig :visible="showApiConfig" :apiKeys="apiKeys" :apiStatus="apiStatus" @close="showApiConfig = false" @save="handleApiSave" @updateStatus="updateApiStatus" />

    <!-- 样式配置面板 -->
    <StyleConfig :visible="showStylePanel" :styles="styleSettings" @close="showStylePanel = false" @save="handleStyleSave" />

    <!-- 设置面板 -->
    <div v-if="showSettings" class="settings-overlay" @click.self="showSettings = false">
      <div class="settings-panel">
        <div class="settings-header">
          <h2 class="settings-title">⚙️ 设置</h2>
          <button @click="showSettings = false" class="settings-close">✕</button>
        </div>
        <div class="settings-content">
          <!-- 配置类 -->
          <div class="settings-section">
            <div class="section-label">配置</div>
            <button @click="showApiConfig = true; showSettings = false" class="settings-item">
              <span class="item-icon">🔑</span>
              <span class="item-text">API密钥配置</span>
              <span class="item-arrow">›</span>
            </button>
            <button @click="showModelManager = true; showSettings = false" class="settings-item">
              <span class="item-icon">🎯</span>
              <span class="item-text">模型管理</span>
              <span class="item-arrow">›</span>
            </button>
            <button @click="showAgentConfig = true; showSettings = false" class="settings-item">
              <span class="item-icon">🤖</span>
              <span class="item-text">智能体配置</span>
              <span class="item-arrow">›</span>
            </button>
            <button @click="toggleStylePanel(); showSettings = false" class="settings-item">
              <span class="item-icon">🎨</span>
              <span class="item-text">界面样式</span>
              <span class="item-arrow">›</span>
            </button>
          </div>
          <!-- 帮助类 -->
          <div class="settings-section">
            <div class="section-label">帮助</div>
            <button @click="showDocuments = true; showSettings = false" class="settings-item">
              <span class="item-icon">📚</span>
              <span class="item-text">文档中心</span>
              <span class="item-arrow">›</span>
            </button>
            <button @click="showProjectInfo = true; showSettings = false" class="settings-item">
              <span class="item-icon">ℹ️</span>
              <span class="item-text">项目介绍</span>
              <span class="item-arrow">›</span>
            </button>
            <button @click="showChangelog = true; showSettings = false" class="settings-item">
              <span class="item-icon">📋</span>
              <span class="item-text">更新日志</span>
              <span class="item-desc">v{{ versionInfo.version }}</span>
              <span class="item-arrow">›</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { defineComponent, ref, reactive, computed, provide, onMounted, onUnmounted } from 'vue'
import AnalysisView from './views/AnalysisView.vue'
import AnalysisSummaryView from './views/AnalysisSummaryView.vue'
import DataFlowView from './views/DataFlowView.vue'
import BacktestView from './views/BacktestView.vue'
import PaperTradingView from './views/PaperTradingView.vue'
import TrackingCenterView from './views/TrackingCenterView.vue'
import LLMConfigView from './views/TradingLLMConfig.vue'
import ChangelogView from './views/ChangelogView.vue'
import ProjectInfoView from './views/ProjectInfoView.vue'
import DocumentView from './views/DocumentView.vue'
import HistoryView from './views/HistoryView.vue'
import LonghubangView from './views/LonghubangView.vue'
import WencaiSelectorView from './views/WencaiSelectorView.vue'
import SectorRotationView from './views/SectorRotationView.vue'
import MarketSentimentView from './views/MarketSentimentView.vue'
import UnifiedNewsView from './views/UnifiedNewsView.vue'
import MarketDataView from './views/MarketDataView.vue'
import SystemSettingsView from './views/SystemSettingsView.vue'
import ApiMonitorView from './views/ApiMonitorView.vue'
import ParticleBackground from './components/ParticleBackground.vue'
import StockDataPanel from './components/StockDataPanel.vue'
import NewsDataPanel from './components/NewsDataPanel.vue'
import HotRankModal from './components/HotRankModal.vue'
import AgentConfigPanel from './components/AgentConfigPanel.vue'
import ModelManager from './components/ModelManager.vue'
import ApiConfig from './components/ApiConfig.vue'
import StyleConfig from './components/StyleConfig.vue'
import { getVersionInfo } from './data/changelog.js'

export default defineComponent({
  name: 'App',
  components: {
    AnalysisView,
    AnalysisSummaryView,
    DataFlowView,
    BacktestView,
    PaperTradingView,
    TrackingCenterView,
    LLMConfigView,
    ChangelogView,
    ProjectInfoView,
    DocumentView,
    HistoryView,
    LonghubangView,
    WencaiSelectorView,
    SectorRotationView,
    MarketSentimentView,
    UnifiedNewsView,
    MarketDataView,
    SystemSettingsView,
    ApiMonitorView,
    ParticleBackground,
    StockDataPanel,
    NewsDataPanel,
    HotRankModal,
    AgentConfigPanel,
    ModelManager,
    ApiConfig,
    StyleConfig
  },
  setup() {
    const currentView = ref('analysis')  // 当前视图
    const configMode = ref(false)
    const showModelManager = ref(false)
    const showApiConfig = ref(false)
    const showStylePanel = ref(false)
    const showChangelog = ref(false)
    const showProjectInfo = ref(false)
    const showDocuments = ref(false)
    const showHotRankModal = ref(false)
    const showLogWindow = ref(false)  // 全局日志窗口显示状态
    const showHistory = ref(false)  // 历史记录显示状态
    const showAgentConfig = ref(false)  // 智能体配置面板显示状态
    const showSettings = ref(false)  // 设置面板显示状态
    const showServerStatus = ref(false)  // Server状态悬浮显示
    const showMobileMenu = ref(false)  // 移动端菜单显示状态
    const activeNavGroup = ref(null)  // 当前激活的导航分组
    
    const versionInfo = ref(getVersionInfo())
    
    const apiStatus = ref({
      gemini: 'unconfigured',
      deepseek: 'unconfigured',
      qwen: 'unconfigured',
      siliconflow: 'unconfigured'
    })

    const apiKeys = ref({
      gemini: '',
      deepseek: '',
      qwen: '',
      siliconflow: ''
    })
    
    const dataChannelKeys = ref({
      juhe: '',
      finnhub: '',
      tushare: ''
    })

    const dataChannelStatus = ref({
      juhe: 'unconfigured',
      finnhub: 'unconfigured',
      tushare: 'unconfigured',
      akshare: 'configured',
      cninfo: 'unconfigured'
    })

    const integrationContext = reactive({
      stockCode: '',
      sessionId: '',
      analysis: null
    })

    // 后端连接状态
    const backendStatus = ref('checking') // checking, connected, disconnected, error
    const backendStatusText = computed(() => {
      switch (backendStatus.value) {
        case 'connected': return '后端正常'
        case 'disconnected': return '后端断开'
        case 'error': return '后端错误'
        default: return '检查中...'
      }
    })
    
    // 数据透明化
    const currentStockData = ref(null)
    const stockDataPanel = ref(null)
    const newsDataPanel = ref(null)
    
    // 粒子背景设置
    const particlesEnabled = ref(true)
    const particleCount = ref(80)
    const particleSpeed = ref(1)
    const particleColor = ref('#3b82f6')

    // 菜单模式设置
    const menuMode = ref('dropdown')  // 'dropdown' 折叠式 | 'classic' 经典式

    const toggleConfigMode = () => {
      configMode.value = !configMode.value
    }

    const toggleStylePanel = () => {
      showStylePanel.value = !showStylePanel.value
    }

    // 移动端菜单切换
    const toggleMobileMenu = () => {
      showMobileMenu.value = !showMobileMenu.value
    }

    // 判断导航分组是否激活
    const isGroupActive = (group) => {
      const groupPages = {
        analysis: ['analysis', 'analysis-summary'],
        trading: ['backtest', 'paper-trading', 'tracking-center'],
        market: ['longhubang', 'sector-rotation', 'sentiment', 'unified-news', 'market-data'],
        tools: ['dataflow', 'llm-config', 'wencai', 'api-monitor'],
        settings: ['system-settings']
      }
      return groupPages[group]?.includes(currentView.value)
    }

    // 获取当前页面图标
    const getCurrentPageIcon = () => {
      const icons = {
        'analysis': '📊',
        'analysis-summary': '🧭',
        'backtest': '📈',
        'paper-trading': '💼',
        'tracking-center': '🔄',
        'longhubang': '🐉',
        'sector-rotation': '🔄',
        'sentiment': '💹',
        'unified-news': '📰',
        'market-data': '📈',
        'dataflow': '📊',
        'llm-config': '⚙️',
        'wencai': '🔍',
        'api-monitor': '📡',
        'system-settings': '🔧'
      }
      return icons[currentView.value] || '📊'
    }

    // 获取当前页面名称
    const getCurrentPageName = () => {
      const names = {
        'analysis': '智能分析',
        'analysis-summary': '分析总结',
        'backtest': '策略回测',
        'paper-trading': '模拟交易',
        'tracking-center': '跟踪验证',
        'longhubang': '龙虎榜',
        'sector-rotation': '板块轮动',
        'sentiment': '市场情绪',
        'unified-news': '新闻中心',
        'market-data': '市场数据',
        'dataflow': '数据流',
        'llm-config': 'LLM配置',
        'wencai': '问财选股',
        'api-monitor': '接口监控',
        'system-settings': '系统设置'
      }
      return names[currentView.value] || '智能分析'
    }

    const getStatusClass = (status) => {
      return status === 'configured' ? 'status-configured' : 
             status === 'error' ? 'status-error' : 'status-unconfigured'
    }

    const getProviderName = (key) => {
      const names = {
        gemini: 'Gemini',
        deepseek: 'DeepSeek',
        qwen: '通义千问',
        siliconflow: '硅基流动'
      }
      return names[key] || key
    }

    const getProviderShort = (key) => {
      const shorts = {
        gemini: 'GM',
        deepseek: 'DS',
        qwen: 'QW',
        siliconflow: 'SF'
      }
      return shorts[key] || key.toUpperCase().slice(0, 2)
    }

    const getDataChannelName = (key) => {
      const names = {
        juhe: '聚合数据',
        finnhub: 'FinnHub',
        tushare: 'Tushare',
        akshare: 'AKShare',
        cninfo: '巨潮资讯'
      }
      return names[key] || key
    }

    const getDataChannelShort = (key) => {
      const shorts = {
        juhe: 'JH',
        finnhub: 'FH',
        tushare: 'TS',
        akshare: 'AK',
        cninfo: 'CN'
      }
      return shorts[key] || key.toUpperCase().slice(0, 2)
    }

    // 后端健康检查
    const checkBackendHealth = async () => {
      try {
        const response = await fetch('http://localhost:8000/', { 
          method: 'GET',
          signal: AbortSignal.timeout(10000) // 10秒超时，给AI请求留出时间
        })
        if (response.ok) {
          backendStatus.value = 'connected'
          return true
        } else {
          backendStatus.value = 'error'
          return false
        }
      } catch (error) {
        // 不要因为单次超时就认为后端断开
        // 只有连续多次失败才认为断开
        console.warn('后端健康检查超时，可能是正在处理AI请求')
        // 不修改状态，保持当前状态
        return false
      }
    }
    
    // 加载后端配置
    const loadBackendConfig = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/config')
        if (response.ok) {
          const data = await response.json()
          console.log('App加载后端配置:', data)
          backendStatus.value = 'connected' // 更新后端状态
          
          // 更新 AI API Keys 和状态
          if (data.api_keys) {
            // 只更新 AI API
            const aiProviders = ['gemini', 'deepseek', 'qwen', 'siliconflow']
            aiProviders.forEach(provider => {
              if (data.api_keys[provider]) {
                // 只显示部分API Key用于安全
                apiKeys.value[provider] = data.api_keys[provider].substring(0, 20) + '...'
                apiStatus.value[provider] = 'configured'
                console.log(`[App] ✅ ${provider} API已配置`)
              } else {
                apiStatus.value[provider] = 'not_configured'
                console.log(`[App] ⚠️ ${provider} API未配置`)
              }
            })
            
            // 更新数据渠道 Keys 和状态
            const dataProviders = ['juhe', 'finnhub', 'tushare']
            dataProviders.forEach(provider => {
              if (data.api_keys[provider]) {
                dataChannelKeys.value[provider] = data.api_keys[provider].substring(0, 20) + '...'
                dataChannelStatus.value[provider] = 'configured'
                console.log(`[App] ✅ ${provider} 数据源已配置`)
              } else {
                dataChannelStatus.value[provider] = 'not_configured'
                console.log(`[App] ⚠️ ${provider} 数据源未配置`)
              }
            })
          }
          
          // 检查环境变量格式
          if (data.GEMINI_API_KEY) {
            apiKeys.value.gemini = data.GEMINI_API_KEY
            apiStatus.value.gemini = 'configured'
          }
          if (data.DEEPSEEK_API_KEY) {
            apiKeys.value.deepseek = data.DEEPSEEK_API_KEY
            apiStatus.value.deepseek = 'configured'
          }
          if (data.DASHSCOPE_API_KEY) {
            apiKeys.value.qwen = data.DASHSCOPE_API_KEY
            apiStatus.value.qwen = 'configured'
          }
          if (data.SILICONFLOW_API_KEY) {
            apiKeys.value.siliconflow = data.SILICONFLOW_API_KEY
            apiStatus.value.siliconflow = 'configured'
          }
          if (data.JUHE_API_KEY) {
            dataChannelKeys.value.juhe = data.JUHE_API_KEY
            dataChannelStatus.value.juhe = 'configured'
          }
          if (data.FINNHUB_API_KEY) {
            dataChannelKeys.value.finnhub = data.FINNHUB_API_KEY
            dataChannelStatus.value.finnhub = 'configured'
          }
          if (data.TUSHARE_TOKEN) {
            dataChannelKeys.value.tushare = data.TUSHARE_TOKEN
            dataChannelStatus.value.tushare = 'configured'
          }
          // 检查巨潮API配置
          if (data.CNINFO_ACCESS_KEY || data.api_keys?.cninfo_access_key) {
            dataChannelStatus.value.cninfo = 'configured'
          }
        } else {
          console.error('后端响应错误:', response.status)
          backendStatus.value = 'error'
        }
      } catch (error) {
        console.error('App加载配置失败:', error)
        backendStatus.value = 'disconnected'
        testBackendConnection()
      }
    }
    
    // 测试后端连接
    const testBackendConnection = async () => {
      try {
        const response = await fetch('http://localhost:8000/')
        console.log('后端连接状态:', response.ok ? '成功' : '失败')
      } catch (error) {
        console.error('无法连接到后端:', error)
      }
    }

    // 监听粒子背景更新事件
    const handleParticleUpdate = (event) => {
      const { enabled, count, speed, color } = event.detail
      particlesEnabled.value = enabled
      particleCount.value = count
      particleSpeed.value = speed
      particleColor.value = color
    }

    // 监听样式更新事件（包括菜单模式）
    const handleStyleUpdate = (event) => {
      const styles = event.detail
      if (styles.menuMode) {
        menuMode.value = styles.menuMode
      }
    }

    // 组件挂载时加载配置
    onMounted(() => {
      loadBackendConfig()
      
      // 定期检查后端健康状态（10秒一次）
      const healthCheckInterval = setInterval(checkBackendHealth, 10000)
      
      // 组件卸载时清理定时器
      onUnmounted(() => {
        clearInterval(healthCheckInterval)
      })
      
      // 从localStorage加载样式设置
      const savedStyles = localStorage.getItem('styleSettings')
      if (savedStyles) {
        const styles = JSON.parse(savedStyles)
        if (styles.particlesEnabled !== undefined) {
          particlesEnabled.value = styles.particlesEnabled
          particleCount.value = styles.particleCount || 80
          particleSpeed.value = styles.particleSpeed || 1
          particleColor.value = styles.particleColor || '#3b82f6'
        }

        // 加载菜单模式
        if (styles.menuMode) {
          menuMode.value = styles.menuMode
        }

        // 应用背景渐变
        const app = document.querySelector('#app')
        if (app && styles.gradientStart && styles.gradientEnd) {
          app.style.background = `linear-gradient(${styles.gradientAngle || 135}deg, ${styles.gradientStart} 0%, ${styles.gradientEnd} 100%)`
        }
      }
      
      // 监听粒子更新事件
      window.addEventListener('updateParticles', handleParticleUpdate)
      // 监听样式更新事件
      window.addEventListener('updateStyles', handleStyleUpdate)
    })

    // 组件卸载时移除监听器
    onUnmounted(() => {
      window.removeEventListener('updateParticles', handleParticleUpdate)
      window.removeEventListener('updateStyles', handleStyleUpdate)
    })

    // 保存 API 配置
    const saveApiConfig = async (keys) => {
      try {
        // 分离 AI API 和数据渠道
        const aiKeys = {}
        const dataKeys = {}
        
        Object.keys(keys).forEach(key => {
          if (['gemini', 'deepseek', 'qwen', 'siliconflow'].includes(key)) {
            aiKeys[key] = keys[key]
          } else if (['juhe', 'finnhub', 'tushare'].includes(key)) {
            dataKeys[key] = keys[key]
          }
        })
        
        // 更新本地状态
        apiKeys.value = { ...apiKeys.value, ...aiKeys }
        dataChannelKeys.value = { ...dataChannelKeys.value, ...dataKeys }
        
        // 保存到后端
        const response = await fetch('http://localhost:8000/api/config', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ api_keys: keys })
        })
        
        if (response.ok) {
          console.log('API配置保存成功')
          // 更新 AI API 状态
          Object.keys(aiKeys).forEach(provider => {
            apiStatus.value[provider] = aiKeys[provider] ? 'configured' : 'unconfigured'
          })
          // 更新数据渠道状态
          Object.keys(dataKeys).forEach(provider => {
            dataChannelStatus.value[provider] = dataKeys[provider] ? 'configured' : 'unconfigured'
          })
        } else {
          console.error('保存配置失败:', response.status)
        }
      } catch (error) {
        console.error('保存配置失败:', error)
      }
    }

    // 更新 API 状态
    const updateApiStatus = (provider, status) => {
      apiStatus.value[provider] = status
    }

    // 切换日志窗口
    const toggleLogWindow = () => {
      showLogWindow.value = !showLogWindow.value
    }
    
    // 提供给子组件
    provide('configMode', configMode)
    provide('showModelManager', showModelManager)
    provide('showApiConfig', showApiConfig)
    provide('showStylePanel', showStylePanel)
    provide('showLogWindow', showLogWindow)  // 提供日志窗口状态
    provide('apiStatus', apiStatus)
    provide('apiKeys', apiKeys)
    provide('dataChannelKeys', dataChannelKeys)
    provide('dataChannelStatus', dataChannelStatus)
    provide('saveApiConfig', saveApiConfig)
    provide('updateApiStatus', updateApiStatus)
    provide('currentStockData', currentStockData)
    provide('stockDataPanel', stockDataPanel)
    provide('newsDataPanel', newsDataPanel)

    // 处理智能体配置保存
    const updateIntegrationContext = (session) => {
      integrationContext.stockCode = session?.stock_code || ''
      integrationContext.sessionId = session?.session_id || ''
      integrationContext.analysis = session || null
    }

    const handleGotoBacktest = (session) => {
      updateIntegrationContext(session)
      currentView.value = 'backtest'
    }

    const handleGotoPaperTrading = (session) => {
      updateIntegrationContext(session)
      currentView.value = 'paper-trading'
    }

    const handleGotoTracking = (session) => {
      updateIntegrationContext(session)
      currentView.value = 'tracking-center'
    }

    const handleAgentConfigSave = (config) => {
      console.log('智能体配置已保存:', config)
      // 配置已在AgentConfigPanel组件中通过API保存
      // 这里可以添加额外的处理逻辑，比如显示成功提示
    }

    // 样式设置
    const styleSettings = ref({
      cardOpacity: 95,
      cardBlur: 10,
      borderWidth: 1,
      gradientStart: '#0f172a',
      gradientEnd: '#1e293b',
      gradientAngle: 135,
      particlesEnabled: true,
      particleCount: 80,
      particleSpeed: 1,
      particleColor: '#3b82f6',
      menuMode: 'dropdown'
    })

    // 处理模型保存
    const handleModelSave = (models) => {
      console.log('模型配置已保存:', models)
    }

    // 处理API配置保存
    const handleApiSave = async (keys) => {
      await saveApiConfig(keys)
    }

    // 处理样式保存
    const handleStyleSave = (styles) => {
      styleSettings.value = { ...styles }
      // 应用背景渐变
      const app = document.querySelector('#app')
      if (app && styles.gradientStart && styles.gradientEnd) {
        app.style.background = `linear-gradient(${styles.gradientAngle || 135}deg, ${styles.gradientStart} 0%, ${styles.gradientEnd} 100%)`
      }
      // 更新菜单模式
      if (styles.menuMode) {
        menuMode.value = styles.menuMode
      }
    }

    return {
      currentView,
      configMode,
      showModelManager,
      showApiConfig,
      showStylePanel,
      showChangelog,
      showProjectInfo,
      showDocuments,
      showHotRankModal,
      showLogWindow,
      showHistory,
      showAgentConfig,
      showSettings,
      showServerStatus,
      showMobileMenu,
      activeNavGroup,
      integrationContext,
      versionInfo,
      backendStatus,
      backendStatusText,
      apiStatus,
      apiKeys,
      dataChannelKeys,
      dataChannelStatus,
      currentStockData,
      stockDataPanel,
      newsDataPanel,
      particlesEnabled,
      particleCount,
      particleSpeed,
      particleColor,
      menuMode,
      toggleConfigMode,
      toggleStylePanel,
      toggleLogWindow,
      toggleMobileMenu,
      isGroupActive,
      getCurrentPageIcon,
      getCurrentPageName,
      getStatusClass,
      getProviderName,
      getProviderShort,
      getDataChannelName,
      getDataChannelShort,
      saveApiConfig,
      updateApiStatus,
      handleAgentConfigSave,
      handleModelSave,
      handleApiSave,
      handleStyleSave,
      styleSettings,
      handleGotoBacktest,
      handleGotoPaperTrading,
      handleGotoTracking
    }
  }
})
</script>

<style>
/* Tailwind CSS 将通过配置引入 */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

/* ========================================
   全局滚动条美化
   ======================================== */

/* 全局滚动条样式 - 适用于所有元素 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.3);
  border-radius: 10px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  border: 2px solid transparent;
  background-clip: padding-box;
  transition: all 0.3s ease;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
  background-clip: padding-box;
}

::-webkit-scrollbar-corner {
  background: rgba(15, 23, 42, 0.3);
}

/* Firefox 滚动条样式 */
* {
  scrollbar-width: thin;
  scrollbar-color: #667eea rgba(15, 23, 42, 0.3);
}

/* 细滚动条变体 - 用于小型容器 */
.scrollbar-thin::-webkit-scrollbar {
  width: 6px;
  height: 6px;
}

.scrollbar-thin::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 6px;
}

/* 隐藏滚动条但保留滚动功能 */
.scrollbar-hidden::-webkit-scrollbar {
  display: none;
}

.scrollbar-hidden {
  -ms-overflow-style: none;
  scrollbar-width: none;
}

/* 绿色主题滚动条 - 用于成功/确认类区域 */
.scrollbar-green::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.scrollbar-green::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
}

/* 红色主题滚动条 - 用于警告/错误类区域 */
.scrollbar-red::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
}

.scrollbar-red::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
}

/* 金色主题滚动条 - 用于高亮/重要区域 */
.scrollbar-gold::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

.scrollbar-gold::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #d97706 0%, #f59e0b 100%);
}

/* 青色主题滚动条 - 用于信息类区域 */
.scrollbar-cyan::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
}

.scrollbar-cyan::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #0891b2 0%, #06b6d4 100%);
}

#app {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
}

/* Tailwind-like utility classes (临时使用，后续安装Tailwind) */
.min-h-screen { min-height: 100vh; }
.bg-gradient-to-br { background: linear-gradient(to bottom right, #0f172a, #1e3a8a, #0f172a); }
.from-slate-950 { --tw-gradient-from: #020617; }
.via-blue-950 { --tw-gradient-via: #172554; }
.to-slate-900 { --tw-gradient-to: #0f172a; }
.fixed { position: fixed; }
.top-0 { top: 0; }
.w-full { width: 100%; }
.z-50 { z-index: 50; }
.backdrop-blur-md { backdrop-filter: blur(12px); }
.bg-slate-900\/70 { background-color: rgba(15, 23, 42, 0.7); }
.border-b { border-bottom-width: 1px; }
.border-slate-700\/50 { border-color: rgba(51, 65, 85, 0.5); }
.navbar-content {
  width: 100%;
  height: 4rem;
  padding: 0 1rem;
  display: grid;
  grid-template-columns: minmax(auto, max-content) 1fr minmax(auto, max-content);  /* 防止左右两侧被压缩 */
  gap: 1rem;
  align-items: center;
}

.container-full {
  width: 100%;
  max-width: 100%;
  margin: 0 auto;
}
.mx-auto { margin-left: auto; margin-right: auto; }
.px-4 { padding-left: 1rem; padding-right: 1rem; }
.flex { display: flex; }
.items-center { align-items: center; }
.justify-between { justify-content: space-between; }
.h-16 { height: 4rem; }
.space-x-4 > * + * { margin-left: 1rem; }
.space-x-6 > * + * { margin-left: 1.5rem; }
.text-2xl { font-size: 1.5rem; }
.text-xl { font-size: 1.25rem; }
.text-lg { font-size: 1.125rem; }
.font-bold { font-weight: 700; }
.font-semibold { font-weight: 600; }
.pt-20 { padding-top: 5rem; }
.pb-8 { padding-bottom: 2rem; }
.mr-2 { margin-right: 0.5rem; }
.mt-1 { margin-top: 0.25rem; }
.pl-8 { padding-left: 2rem; }
.text-white { color: #ffffff; }
.text-sm { font-size: 0.875rem; }
.text-xs { font-size: 0.75rem; }
.mb-6 { margin-bottom: 1.5rem; }
.mb-4 { margin-bottom: 1rem; }
.gap-2 { gap: 0.5rem; }
.gap-4 { gap: 1rem; }
.space-y-8 > * + * { margin-top: 2rem; }
.text-slate-300 { color: #cbd5e1; }
.text-slate-400 { color: #94a3b8; }
.text-slate-500 { color: #64748b; }
.grid { display: grid; }
.grid-cols-1 { grid-template-columns: repeat(1, minmax(0, 1fr)); }
.uppercase { text-transform: uppercase; }
.tracking-wide { letter-spacing: 0.05em; }
.whitespace-nowrap { white-space: nowrap; }
.font-mono { font-family: 'Consolas', monospace; }
.leading-relaxed { line-height: 1.625; }

/* 导航栏固定 */
.navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  height: 4rem;  /* 固定高度 */
}

/* API状态指示器 */
.api-status-bar {
  display: flex;
  gap: 0.75rem;
  align-items: center;
  justify-content: center;  /* 居中显示 */
  padding: 0.5rem 1rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid #334155;
  border-radius: 0.5rem;
  flex-wrap: nowrap;  /* 禁止换行 */
  white-space: nowrap; /* 文字不换行 */
  overflow-x: auto;    /* 在空间不足时显示滚动条 */
  max-width: 100%;     /* 限制最大宽度 */
}

/* API状态栏使用细滚动条 */
.api-status-bar::-webkit-scrollbar {
  height: 6px;  /* 水平滚动条使用height */
}

.status-group {
  display: flex;
  gap: 0.375rem;
  align-items: center;
}

.group-label {
  font-size: 0.625rem;
  color: #64748b;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-right: 0.25rem;
}

.status-divider {
  width: 1px;
  height: 1.25rem;
  background: #334155;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 0.375rem;
  font-size: 0.75rem;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 0.375rem;
  font-size: 0.75rem;
}

.status-dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: #64748b;
  flex-shrink: 0;
}

.status-configured .status-dot {
  background: #10b981;
  box-shadow: 0 0 4px rgba(16, 185, 129, 0.5);
}

.status-error .status-dot {
  background: #ef4444;
  box-shadow: 0 0 4px rgba(239, 68, 68, 0.5);
}

.status-name {
  color: #94a3b8;
  font-weight: 500;
}

/* 后端连接状态 */
.backend-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.25rem 0.625rem;
  border-radius: 0.375rem;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.3s ease;
}

.backend-status .status-icon {
  font-size: 0.625rem;
  animation: pulse 2s ease-in-out infinite;
}

.backend-status.checking {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
}

.backend-status.connected {
  background: rgba(16, 185, 129, 0.15);
  color: #10b981;
}

.backend-status.connected .status-icon {
  animation: none;
}

.backend-status.disconnected {
  background: rgba(239, 68, 68, 0.15);
  color: #ef4444;
}

.backend-status.disconnected .status-icon {
  animation: blink 1s ease-in-out infinite;
}

.backend-status.error {
  background: rgba(251, 146, 60, 0.15);
  color: #fb923c;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

@keyframes blink {
  0%, 50%, 100% { opacity: 1; }
  25%, 75% { opacity: 0.3; }
}

/* 导航栏控制按钮 */
.nav-controls {
  display: flex;
  gap: 0.5rem;
  flex-shrink: 0;  /* 防止按钮组被压缩 */
  justify-self: end;  /* 右对齐 */
}

.nav-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.375rem;
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-btn:hover {
  background: rgba(51, 65, 85, 0.5);
  color: white;
  border-color: #475569;
}

.nav-btn.active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-color: #3b82f6;
}

.nav-btn.hot-rank-btn {
  background: rgba(239, 68, 68, 0.1);
  border-color: #ef4444;
  color: #ef4444;
}

.nav-btn.hot-rank-btn:hover {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #ef4444;
}

.nav-btn.version-btn {
  background: rgba(16, 185, 129, 0.1);
  border-color: #10b981;
  color: #10b981;
}

.nav-btn.version-btn:hover {
  background: rgba(16, 185, 129, 0.2);
  border-color: #10b981;
  color: #10b981;
}

.btn-icon {
  font-size: 0.875rem;
}

.btn-text {
  display: none;
}

@media (min-width: 768px) {
  .btn-text {
    display: inline;
  }
}

/* 响应式网格布局 */
@media (min-width: 640px) {
  .sm\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (min-width: 768px) {
  .md\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
}
@media (min-width: 1024px) {
  .lg\:grid-cols-2 { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .lg\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .lg\:grid-cols-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
}
@media (min-width: 1280px) {
  .xl\:grid-cols-3 { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .xl\:grid-cols-4 { grid-template-columns: repeat(4, minmax(0, 1fr)); }
}
@media (min-width: 1536px) {
  .\\2xl\:grid-cols-5 { grid-template-columns: repeat(5, minmax(0, 1fr)); }
}

/* 背景动画 */
.bg-gradient-to-br.from-slate-950.via-blue-950.to-slate-900 {
  background: linear-gradient(135deg, #020617 0%, #172554 50%, #0f172a 100%);
  background-size: 400% 400%;
  animation: gradient-shift 15s ease infinite;
}

@keyframes gradient-shift {
  0% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
  100% { background-position: 0% 50%; }
}

/* 导航链接样式 */
.nav-link {
  color: #cbd5e1;
  text-decoration: none;
  font-weight: 500;
  transition: all 0.2s;
  display: flex;
  align-items: center;
}

.nav-link:hover {
  color: #60a5fa;
  transform: translateY(-1px);
}

.nav-link.router-link-active {
  color: #3b82f6;
}

/* 渐变文本 */
.bg-gradient-to-r {
  background: linear-gradient(to right, #60a5fa, #06b6d4);
  -webkit-background-clip: text;
  background-clip: text;
}

.bg-clip-text {
  -webkit-text-fill-color: transparent;
}

.text-transparent {
  color: transparent;
}

/* 更新日志模态框 */
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(8px);
  z-index: 100;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 2rem;
  overflow: hidden;
}

.changelog-modal {
  position: relative;
  width: 100%;
  max-width: 1400px;
  max-height: 90vh;
  overflow-y: auto;
  background: transparent;
}

.modal-close-btn {
  position: fixed;
  top: 2rem;
  right: 2rem;
  width: 3rem;
  height: 3rem;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 2rem;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 101;
  transition: all 0.2s;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
}

.modal-close-btn:hover {
  background: rgba(220, 38, 38, 1);
  transform: scale(1.1);
}

/* 项目介绍按钮 */
.project-info-btn {
  margin-left: 0.75rem;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
  flex-shrink: 0;
}

.project-info-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.5);
}

.project-info-btn .info-icon {
  font-size: 1.2rem;
  filter: brightness(1.2);
}

/* 文档按钮 */
.doc-btn,
.log-btn,
.history-btn {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(71, 85, 105, 0.5);
  border-radius: 50%;
  cursor: pointer;
  transition: all 0.3s ease;
  margin-left: 0.5rem;
  flex-shrink: 0;
}

.doc-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.5);
}

.doc-btn .doc-icon {
  font-size: 1.2rem;
  filter: brightness(1.2);
}

.log-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
}

.log-btn.active {
  background: linear-gradient(135deg, #06b6d4, #0891b2);
  transform: scale(1.05);
  z-index: 1000;
}

.log-btn .log-icon {
  font-size: 1.2rem;
  filter: brightness(1.2);
}

/* 历史记录按钮 */
.history-btn {
  margin-left: 0.5rem;
  width: 2rem;
  height: 2rem;
  border-radius: 0.5rem;
  background: linear-gradient(135deg, rgba(139, 92, 246, 0.2) 0%, rgba(124, 58, 237, 0.2) 100%);
  border: 1px solid rgba(139, 92, 246, 0.3);
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(139, 92, 246, 0.3);
}

.history-btn:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.5);
}

.history-btn .history-icon {
  font-size: 1.2rem;
  filter: brightness(1.2);
}

/* 历史记录模态框 */
.history-modal {
  background: rgba(15, 23, 42, 0.98);
  backdrop-filter: blur(20px);
  border-radius: 1rem;
  width: 95vw;
  max-width: 1400px;
  height: 90vh;
  overflow-y: auto;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  border: 1px solid rgba(255, 255, 255, 0.1);
  position: relative;
}

/* 项目介绍模态框 */
.project-info-modal {
  position: relative;
  width: 100%;
  max-width: 1200px;
  max-height: 90vh;
  overflow-y: auto;
  background: rgba(15, 23, 42, 0.98);
  border-radius: 20px;
  border: 1px solid rgba(102, 126, 234, 0.3);
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.5);
}

/* 文档中心模态框 */
.document-modal {
  position: relative;
  width: 95vw;
  max-width: 1800px;
  height: 90vh;
  background: transparent;
  border-radius: 20px;
  overflow: hidden;
}

/* 文档中心使用绿色主题滚动条 */
.document-modal::-webkit-scrollbar-thumb {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
}

.document-modal::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(135deg, #059669 0%, #10b981 100%);
}

/* ========================================
   移动端响应式优化
   ======================================== */
/* 中等屏幕优化 */
@media (max-width: 1200px) {
  .navbar-content {
    grid-template-columns: auto 1fr auto;
    gap: 0.5rem;
  }
  
  .api-status-bar {
    font-size: 0.7rem;
    padding: 0.4rem 0.6rem;
  }
  
  .status-item {
    padding: 0.15rem 0.3rem;
    font-size: 0.65rem;
  }
  
  .status-name {
    font-size: 0.65rem;
  }
  
  .nav-btn {
    padding: 0.3rem 0.6rem;
    font-size: 0.8rem;
  }
  
  .btn-text {
    display: inline !important;
  }
}

@media (max-width: 768px) {
  /* 导航栏优化 */
  .navbar {
    height: 3.5rem;  /* 减少高度 */
  }
  
  .navbar-content {
    grid-template-columns: auto 1fr auto;  /* 恢复三列布局 */
    padding: 0.5rem;
    gap: 0.25rem;  /* 减小间隔 */
  }
  
  /* 隐藏标题 */
  .navbar h1 {
    display: none;
  }
  
  /* 左侧按钮组 - 只显示图标 */
  .navbar .flex.items-center {
    gap: 0.25rem;  /* 减小间隔 */
  }
  
  .project-info-btn,
  .doc-btn,
  .log-btn,
  .history-btn {
    width: 2rem;
    height: 2rem;
    margin-left: 0;
    padding: 0;
  }
  
  /* API 状态栏在移动端隐藏 */
  .api-status-bar {
    display: none;
  }
  
  /* 右侧按钮组 - 只显示图标 */
  .nav-controls {
    gap: 0.25rem;  /* 减小间隔 */
    flex-wrap: nowrap;
  }
  
  .nav-btn {
    padding: 0.5rem;  /* 减小内边距 */
    min-width: 2.5rem;
    height: 2.5rem;
  }
  
  .btn-icon {
    font-size: 1.2rem;  /* 放大图标 */
  }
  
  /* 隐藏按钮文字 */
  .btn-text {
    display: none !important;
  }
}

/* 更小屏幕优化 */
@media (max-width: 480px) {
  .navbar {
    height: 3rem;
  }
  
  .navbar-content {
    padding: 0.25rem 0.5rem;
    gap: 0.15rem;
  }
  
  .navbar .flex.items-center {
    gap: 0.15rem;
  }
  
  .project-info-btn,
  .doc-btn,
  .log-btn,
  .history-btn {
    width: 1.75rem;
    height: 1.75rem;
  }
  
  .nav-btn {
    padding: 0.4rem;
    min-width: 2rem;
    height: 2rem;
  }
  
  .btn-icon {
    font-size: 1rem;
  }
  
  .nav-controls {
    gap: 0.15rem;
  }
  
  /* 模态框优化 */
  .modal-overlay {
    padding: 0;
  }
  
  .project-info-modal,
  .document-modal {
    width: 100vw;
    height: 100vh;
    max-width: 100vw;
    max-height: 100vh;
    border-radius: 0;
  }
  
  .modal-close-btn {
    top: 1rem;
    right: 1rem;
    width: 3rem;
    height: 3rem;
    font-size: 2rem;
    z-index: 1000;
  }
}

/* 选项卡导航样式 */
.tab-navigation {
  position: fixed;
  top: 4rem;
  left: 0;
  right: 0;
  z-index: 40;
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  padding: 0 1rem;
  display: flex;
  gap: 1rem;
  height: 3rem;
  align-items: center;
  justify-content: center;
}

.tab-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1.5rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.5rem;
  color: #94a3b8;
  font-size: 0.95rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  white-space: nowrap;
}

.tab-btn:hover {
  background: rgba(51, 65, 85, 0.3);
  color: #e2e8f0;
}

.tab-btn.active {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border-color: #3b82f6;
  color: white;
}

.tab-icon {
  font-size: 1.1rem;
}

.tab-text {
  font-size: 0.9rem;
}

/* 调整主内容区域 */
.pt-32 {
  padding-top: 8rem; /* 调整为顶部导航+选项卡的总高度 */
}

/* 模拟交易占位样式 */
.paper-trading-placeholder {
  text-align: center;
  padding: 4rem 2rem;
  color: #94a3b8;
}

.paper-trading-placeholder h2 {
  font-size: 2rem;
  margin-bottom: 1rem;
  color: #e2e8f0;
}

.paper-trading-placeholder p {
  font-size: 1.1rem;
}

/* ========================================
   新版导航样式 V2
   ======================================== */

/* 顶部导航栏 V2 */
.navbar-v2 {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 50;
  background: rgba(15, 23, 42, 0.95);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  height: 3.5rem;
}

.navbar-v2-content {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 100%;
  padding: 0 1rem;
  max-width: 100%;
}

.navbar-v2-left {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.header-info-btn {
  cursor: pointer;
  font-size: 1.125rem;
  opacity: 0.7;
  transition: opacity 0.2s;
  margin-left: 0.25rem;
}

.header-info-btn:hover {
  opacity: 1;
}

.header-version-btn {
  cursor: pointer;
  padding: 0.25rem 0.5rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.25rem;
  color: #60a5fa;
  font-size: 0.75rem;
  font-weight: 500;
  transition: all 0.2s;
}

.header-version-btn:hover {
  background: rgba(59, 130, 246, 0.3);
}

.mobile-menu-btn {
  display: none;
  padding: 0.5rem;
  background: transparent;
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.375rem;
  color: #94a3b8;
  font-size: 1.25rem;
  cursor: pointer;
  transition: all 0.2s;
}

.mobile-menu-btn:hover {
  background: rgba(51, 65, 85, 0.5);
  color: white;
}

.logo {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  cursor: pointer;
  transition: opacity 0.2s;
}

.logo:hover {
  opacity: 0.8;
}

.logo-icon {
  font-size: 1.5rem;
}

.logo-text {
  font-size: 1.125rem;
  font-weight: 700;
  color: white;
}

.navbar-v2-right {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.nav-v2-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.75rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.375rem;
  color: #94a3b8;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-v2-btn:hover {
  background: rgba(51, 65, 85, 0.5);
  color: white;
}

.nav-v2-btn.hot-btn {
  background: rgba(239, 68, 68, 0.1);
  border-color: rgba(239, 68, 68, 0.3);
  color: #ef4444;
}

.nav-v2-btn.hot-btn:hover {
  background: rgba(239, 68, 68, 0.2);
}

.nav-v2-btn.settings-btn:hover {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.btn-label {
  font-weight: 500;
}

/* Server状态 */
.server-status-wrapper {
  position: relative;
}

.server-status {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  background: rgba(30, 41, 59, 0.8);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.375rem;
  font-size: 0.75rem;
  cursor: default;
  transition: all 0.2s;
}

.server-dot {
  font-size: 0.625rem;
}

.server-text {
  color: #94a3b8;
  font-weight: 500;
}

.server-status.checking {
  color: #94a3b8;
}

.server-status.connected {
  border-color: rgba(16, 185, 129, 0.3);
}

.server-status.connected .server-dot {
  color: #10b981;
}

.server-status.disconnected {
  border-color: rgba(239, 68, 68, 0.3);
}

.server-status.disconnected .server-dot {
  color: #ef4444;
}

.server-status.error {
  border-color: rgba(251, 146, 60, 0.3);
}

.server-status.error .server-dot {
  color: #fb923c;
}

/* Server状态悬浮弹窗 */
.server-status-popup {
  position: absolute;
  top: 100%;
  right: 0;
  margin-top: 0.5rem;
  width: 280px;
  background: rgba(15, 23, 42, 0.98);
  border: 1px solid rgba(51, 65, 85, 0.8);
  border-radius: 0.5rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  z-index: 100;
  overflow: hidden;
}

.popup-header {
  padding: 0.75rem 1rem;
  background: rgba(30, 41, 59, 0.5);
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  font-size: 0.875rem;
  font-weight: 600;
  color: white;
}

.popup-section {
  padding: 0.75rem 1rem;
}

.popup-label {
  font-size: 0.75rem;
  color: #64748b;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.popup-status {
  font-size: 0.875rem;
  font-weight: 500;
}

.popup-status.connected {
  color: #10b981;
}

.popup-status.disconnected {
  color: #ef4444;
}

.popup-status.checking {
  color: #94a3b8;
}

.popup-divider {
  height: 1px;
  background: rgba(51, 65, 85, 0.5);
}

.popup-items {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.popup-item {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.25rem 0.5rem;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 0.25rem;
  font-size: 0.75rem;
}

.popup-item .item-dot {
  font-size: 0.5rem;
}

.popup-item .item-name {
  color: #94a3b8;
}

.popup-item.status-configured .item-dot {
  color: #10b981;
}

.popup-item.status-configured .item-name {
  color: #e2e8f0;
}

.popup-item.status-unconfigured .item-dot {
  color: #64748b;
}

.popup-item.status-error .item-dot {
  color: #ef4444;
}

/* 分组下拉导航 */
.nav-v2-menu {
  position: fixed;
  top: 3.5rem;
  left: 0;
  right: 0;
  z-index: 40;
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  height: 2.75rem;
  display: flex;
  align-items: center;
  padding: 0 1rem;
  gap: 0.5rem;
}

.nav-group {
  position: relative;
}

.nav-group-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 1rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.375rem;
  color: #94a3b8;
  font-size: 0.875rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.nav-group-btn:hover {
  background: rgba(51, 65, 85, 0.3);
  color: #e2e8f0;
}

.nav-group-btn.active {
  background: rgba(59, 130, 246, 0.15);
  border-color: rgba(59, 130, 246, 0.3);
  color: #60a5fa;
}

.group-icon {
  font-size: 1rem;
}

.group-text {
  font-size: 0.875rem;
}

.group-arrow {
  font-size: 0.625rem;
  margin-left: 0.25rem;
  transition: transform 0.2s;
}

.nav-group:hover .group-arrow {
  transform: rotate(180deg);
}

/* 下拉菜单 */
.nav-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  padding-top: 4px; /* 用padding代替margin，保持鼠标悬停区域连续 */
  min-width: 160px;
  z-index: 50;
}

.nav-dropdown > button,
.nav-dropdown > div {
  background: rgba(15, 23, 42, 0.98);
}

.nav-dropdown > button:first-child,
.nav-dropdown > div:first-child {
  border-top-left-radius: 0.5rem;
  border-top-right-radius: 0.5rem;
}

.nav-dropdown > button:last-child,
.nav-dropdown > div:last-child {
  border-bottom-left-radius: 0.5rem;
  border-bottom-right-radius: 0.5rem;
}

.nav-dropdown-inner {
  background: rgba(15, 23, 42, 0.98);
  border: 1px solid rgba(51, 65, 85, 0.8);
  border-radius: 0.5rem;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

.nav-dropdown-inner .dropdown-divider {
  height: 1px;
  margin: 0.5rem 0;
  background: rgba(51, 65, 85, 0.5);
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  width: 100%;
  padding: 0.625rem 1rem;
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 0.875rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.dropdown-item:hover {
  background: rgba(51, 65, 85, 0.5);
  color: white;
}

.dropdown-item.active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.dropdown-item .item-icon {
  font-size: 1rem;
}

.dropdown-divider {
  height: 1px;
  margin: 0.5rem 0;
  background: rgba(51, 65, 85, 0.5);
}

/* 当前页面指示器 */
.current-page-indicator {
  margin-left: auto;
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.375rem 0.75rem;
  background: rgba(59, 130, 246, 0.15);
  border: 1px solid rgba(59, 130, 246, 0.3);
  border-radius: 0.375rem;
}

.indicator-icon {
  font-size: 1rem;
}

.indicator-text {
  font-size: 0.875rem;
  font-weight: 500;
  color: #60a5fa;
}

/* 智能分析页面专属工具栏 */
.analysis-toolbar {
  position: fixed;
  top: 6.25rem;
  right: 1rem;
  z-index: 35;
  display: flex;
  gap: 0.375rem;
  padding: 0.375rem;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 0.5rem;
  backdrop-filter: blur(8px);
}

.toolbar-btn {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  padding: 0.375rem 0.625rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.25rem;
  color: #94a3b8;
  font-size: 0.75rem;
  cursor: pointer;
  transition: all 0.2s;
}

.toolbar-btn:hover {
  background: rgba(51, 65, 85, 0.5);
  color: white;
}

.toolbar-btn.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: rgba(59, 130, 246, 0.3);
  color: #60a5fa;
}

.toolbar-btn .btn-icon {
  font-size: 0.875rem;
}

.toolbar-btn .btn-text {
  font-size: 0.75rem;
  font-weight: 500;
}

/* 设置面板 */
.settings-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 100;
  display: flex;
  justify-content: flex-end;
}

.settings-panel {
  width: 320px;
  max-width: 100%;
  height: 100%;
  background: rgba(15, 23, 42, 0.98);
  border-left: 1px solid rgba(51, 65, 85, 0.5);
  display: flex;
  flex-direction: column;
  animation: slideInRight 0.3s ease;
}

@keyframes slideInRight {
  from {
    transform: translateX(100%);
  }
  to {
    transform: translateX(0);
  }
}

.settings-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

.settings-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: white;
  margin: 0;
}

.settings-close {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 1.25rem;
  cursor: pointer;
  border-radius: 0.25rem;
  transition: all 0.2s;
}

.settings-close:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.settings-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.settings-section {
  margin-bottom: 1.5rem;
}

.settings-section .section-label {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  padding: 0 0.5rem;
}

.settings-item {
  display: flex;
  align-items: center;
  width: 100%;
  padding: 0.75rem;
  background: transparent;
  border: none;
  border-radius: 0.5rem;
  color: #e2e8f0;
  font-size: 0.875rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.settings-item:hover {
  background: rgba(51, 65, 85, 0.3);
}

.settings-item .item-icon {
  font-size: 1.125rem;
  margin-right: 0.75rem;
}

.settings-item .item-text {
  flex: 1;
}

.settings-item .item-desc {
  font-size: 0.75rem;
  color: #64748b;
  margin-right: 0.5rem;
}

.settings-item .item-arrow {
  color: #64748b;
  font-size: 1rem;
}

/* 移动端菜单 */
.mobile-menu-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(4px);
  z-index: 100;
}

.mobile-menu {
  position: absolute;
  top: 0;
  left: 0;
  width: 280px;
  max-width: 85%;
  height: 100%;
  background: rgba(15, 23, 42, 0.98);
  border-right: 1px solid rgba(51, 65, 85, 0.5);
  display: flex;
  flex-direction: column;
  animation: slideInLeft 0.3s ease;
}

@keyframes slideInLeft {
  from {
    transform: translateX(-100%);
  }
  to {
    transform: translateX(0);
  }
}

.mobile-menu-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1rem;
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
}

.mobile-menu-title {
  font-size: 1rem;
  font-weight: 600;
  color: white;
}

.mobile-menu-close {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  border: none;
  color: #94a3b8;
  font-size: 1.25rem;
  cursor: pointer;
  border-radius: 0.25rem;
}

.mobile-menu-close:hover {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.mobile-menu-content {
  flex: 1;
  overflow-y: auto;
  padding: 1rem;
}

.mobile-menu-group {
  margin-bottom: 1.5rem;
}

.mobile-group-title {
  font-size: 0.75rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.5rem;
  padding: 0 0.5rem;
}

.mobile-menu-item {
  display: block;
  width: 100%;
  padding: 0.75rem;
  background: transparent;
  border: none;
  border-radius: 0.375rem;
  color: #e2e8f0;
  font-size: 0.875rem;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.mobile-menu-item:hover {
  background: rgba(51, 65, 85, 0.3);
}

.mobile-menu-item.active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
}

.mobile-menu-divider {
  height: 1px;
  margin: 0.5rem 0;
  background: rgba(51, 65, 85, 0.5);
}

/* 调整主内容区域 - 新版导航 */
.pt-32 {
  padding-top: 7rem; /* 顶栏3.5rem + 导航栏2.75rem + 间距 */
}

/* 移动端响应式 - 新版导航 */
@media (max-width: 768px) {
  .mobile-menu-btn {
    display: flex;
  }

  .logo-text {
    display: none;
  }

  .nav-v2-btn .btn-label {
    display: none;
  }

  .nav-v2-menu {
    display: none;
  }

  .analysis-toolbar {
    top: 4rem;
    right: 0.5rem;
    left: 0.5rem;
    justify-content: center;
  }

  .toolbar-btn .btn-text {
    display: none;
  }

  .current-page-indicator {
    display: none;
  }

  .pt-32 {
    padding-top: 5rem;
  }

  /* 智能分析页面需要更多顶部空间 */
  .analysis-toolbar + .pt-32,
  .analysis-toolbar ~ main {
    padding-top: 7rem;
  }
}

@media (max-width: 480px) {
  .navbar-v2 {
    height: 3rem;
  }

  .logo-icon {
    font-size: 1.25rem;
  }

  .nav-v2-btn {
    padding: 0.375rem 0.5rem;
  }

  .server-status {
    padding: 0.25rem 0.5rem;
  }

  .server-text {
    display: none;
  }

  .settings-panel {
    width: 100%;
  }

  .pt-32 {
    padding-top: 4rem;
  }
}

/* ========================================
   经典式平铺导航样式
   ======================================== */
.nav-classic-menu {
  position: fixed;
  top: 3.5rem;
  left: 0;
  right: 0;
  z-index: 40;
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid rgba(51, 65, 85, 0.5);
  height: auto;
  min-height: 2.75rem;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  padding: 0.375rem 1rem;
  gap: 0.375rem;
  overflow-x: auto;
}

.classic-tab {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  background: transparent;
  border: 1px solid transparent;
  border-radius: 0.375rem;
  color: #94a3b8;
  font-size: 0.8125rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
  white-space: nowrap;
}

.classic-tab:hover {
  background: rgba(51, 65, 85, 0.3);
  color: #e2e8f0;
}

.classic-tab.active {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border-color: #3b82f6;
  color: white;
}

.classic-tab .tab-icon {
  font-size: 0.9375rem;
}

.classic-tab .tab-text {
  font-size: 0.8125rem;
}

/* 经典式菜单响应式 */
@media (max-width: 1200px) {
  .nav-classic-menu {
    padding: 0.25rem 0.5rem;
    gap: 0.25rem;
  }

  .classic-tab {
    padding: 0.375rem 0.625rem;
    font-size: 0.75rem;
  }

  .classic-tab .tab-icon {
    font-size: 0.875rem;
  }

  .classic-tab .tab-text {
    font-size: 0.75rem;
  }
}

@media (max-width: 768px) {
  .nav-classic-menu {
    display: none;
  }
}
</style>
