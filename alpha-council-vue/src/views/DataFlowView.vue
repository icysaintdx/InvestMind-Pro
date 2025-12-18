<template>
  <div class="dataflow-container">
    <!-- Toast通知系统 -->
    <div class="toast-container">
      <div 
        v-for="toast in toasts" 
        :key="toast.id"
        :class="['toast', toast.type]"
      >
        <span class="toast-icon">{{ toast.icon }}</span>
        <span class="toast-message">{{ toast.message }}</span>
      </div>
    </div>

    <!-- 页面标题 -->
    <div class="page-header">
      <div>
        <h1>📊 数据流监控中心</h1>
        <p class="subtitle">实时监控股票数据流、新闻舆情与风险分析</p>
      </div>
      <div class="header-actions">
        <button @click="refreshAllData" class="btn-primary" :disabled="isRefreshing">
          <span v-if="!isRefreshing">🔄 全部刷新</span>
          <span v-else>⏳ 刷新中...</span>
        </button>
        <button @click="showAddMonitor = true" class="btn-primary">
          ➕ 添加监控股票
        </button>
      </div>
    </div>

    <!-- 数据统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📈</div>
        <div class="stat-content">
          <div class="stat-label">监控股票数</div>
          <div class="stat-value">{{ monitoredStocks.length }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">📰</div>
        <div class="stat-content">
          <div class="stat-label">今日新闻</div>
          <div class="stat-value">{{ todayNewsCount }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">⚠️</div>
        <div class="stat-content">
          <div class="stat-label">风险预警</div>
          <div class="stat-value risk">{{ riskAlertCount }}</div>
        </div>
      </div>
      <div class="stat-card">
        <div class="stat-icon">🤖</div>
        <div class="stat-content">
          <div class="stat-label">AI分析任务</div>
          <div class="stat-value">{{ analysisTaskCount }}</div>
        </div>
      </div>
    </div>

    <!-- 数据源状态 -->
    <div class="card section">
      <div class="section-header">
        <h2>🔌 数据源状态</h2>
        <button @click="checkDataSources" class="btn-secondary">检测连接</button>
      </div>
      <div class="data-sources-grid">
        <div 
          v-for="source in dataSources" 
          :key="source.id"
          :class="['source-card', source.status]"
        >
          <div class="source-header">
            <span class="source-name">{{ source.name }}</span>
            <span :class="['status-badge', source.status]">
              {{ getStatusText(source.status) }}
            </span>
          </div>
          <div class="source-info">
            <div class="info-row">
              <span class="label">类型：</span>
              <span>{{ source.type }}</span>
            </div>
            <div class="info-row">
              <span class="label">今日调用：</span>
              <span>{{ source.todayCalls }} 次</span>
            </div>
            <div class="info-row">
              <span class="label">最后更新：</span>
              <span>{{ formatTime(source.lastUpdate) }}</span>
            </div>
            <div v-if="source.error" class="error-message">
              ⚠️ {{ source.error }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 监控股票列表 -->
    <div class="card section">
      <div class="section-header">
        <h2>👀 监控股票</h2>
        <div class="filter-tabs">
          <button 
            v-for="tab in ['全部', '高风险', '中风险', '低风险']"
            :key="tab"
            :class="['filter-tab', { active: currentFilter === tab }]"
            @click="currentFilter = tab"
          >
            {{ tab }}
          </button>
        </div>
      </div>
      
      <div v-if="filteredStocks.length === 0" class="empty-state">
        <p>暂无监控股票，点击右上角"添加监控股票"开始监控</p>
      </div>
      
      <div v-else class="stocks-table">
        <table class="data-table">
          <thead>
            <tr>
              <th>股票代码</th>
              <th>股票名称</th>
              <th>情绪得分</th>
              <th>风险等级</th>
              <th>最新新闻</th>
              <th>更新频率</th>
              <th>最后更新</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="stock in filteredStocks" :key="stock.code">
              <td class="code">{{ stock.code }}</td>
              <td>{{ stock.name }}</td>
              <td>
                <div class="sentiment-score">
                  <div class="score-bar">
                    <div 
                      class="score-fill" 
                      :style="{ width: stock.sentimentScore + '%', backgroundColor: getSentimentColor(stock.sentimentScore) }"
                    ></div>
                  </div>
                  <span>{{ stock.sentimentScore }}</span>
                </div>
              </td>
              <td>
                <span :class="['risk-badge', stock.riskLevel]">
                  {{ getRiskText(stock.riskLevel) }}
                </span>
              </td>
              <td class="news-preview">{{ stock.latestNews || '暂无新闻' }}</td>
              <td>{{ stock.updateFrequency }}</td>
              <td>{{ formatTime(stock.lastUpdate) }}</td>
              <td>
                <div class="action-buttons">
                  <button @click="viewDetails(stock)" class="btn-small">详情</button>
                  <button @click="updateNow(stock)" class="btn-small">立即更新</button>
                  <button @click="removeMonitor(stock)" class="btn-danger-small">移除</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 新闻流 -->
    <div class="card section">
      <div class="section-header">
        <h2>📰 实时新闻流</h2>
        <select v-model="newsSource" class="news-source-select">
          <option value="all">全部来源</option>
          <option value="tushare">Tushare</option>
          <option value="akshare">AKShare</option>
          <option value="eastmoney">东方财富</option>
        </select>
      </div>
      
      <div class="news-list">
        <div v-if="newsList.length === 0" class="empty-state">
          <p>暂无新闻数据</p>
        </div>
        <div 
          v-for="news in newsList" 
          :key="news.id"
          class="news-item"
        >
          <div class="news-header">
            <h3>{{ news.title }}</h3>
            <span class="news-time">{{ formatTime(news.publishTime) }}</span>
          </div>
          <div class="news-meta">
            <span class="news-source">{{ news.source }}</span>
            <span class="news-stocks">相关股票: {{ news.relatedStocks.join(', ') }}</span>
            <span :class="['news-sentiment', getSentimentClass(news.sentiment)]">
              情绪: {{ news.sentiment }}
            </span>
          </div>
          <p class="news-summary">{{ news.summary }}</p>
        </div>
      </div>
    </div>

    <!-- 添加监控对话框 -->
    <div v-if="showAddMonitor" class="modal-overlay" @click="showAddMonitor = false">
      <div class="modal-content" @click.stop>
        <h3>添加监控股票</h3>
        <div class="form-group">
          <label>股票代码</label>
          <input 
            v-model="newMonitor.code" 
            placeholder="如：600519.SH"
            class="input-field"
          />
        </div>
        <div class="form-group">
          <label>更新频率</label>
          <select v-model="newMonitor.frequency" class="input-field">
            <option value="5m">每5分钟</option>
            <option value="15m">每15分钟</option>
            <option value="30m">每30分钟</option>
            <option value="1h">每小时</option>
            <option value="1d">每天</option>
          </select>
        </div>
        <div class="form-group">
          <label>监控项目</label>
          <div class="checkbox-group">
            <label><input type="checkbox" v-model="newMonitor.items.news" /> 新闻舆情</label>
            <label><input type="checkbox" v-model="newMonitor.items.risk" /> 风险分析</label>
            <label><input type="checkbox" v-model="newMonitor.items.sentiment" /> 情绪分析</label>
            <label><input type="checkbox" v-model="newMonitor.items.suspend" /> 停复牌监控</label>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="addMonitor" class="btn-primary">确认添加</button>
          <button @click="showAddMonitor = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 股票详情弹窗 -->
    <div v-if="showStockDetails" class="modal-overlay" @click="showStockDetails = false">
      <div class="modal-content stock-detail-modal" @click.stop>
        <div class="modal-header">
          <div>
            <h3>📊 {{ selectedStock?.name || selectedStock?.code }} 详细数据</h3>
            <p class="stock-code">{{ selectedStock?.code }}</p>
          </div>
          <button @click="showStockDetails = false" class="close-btn">×</button>
        </div>

        <!-- 数据概览 -->
        <div class="detail-overview">
          <div class="overview-item">
            <span class="overview-label">风险等级</span>
            <span :class="['risk-badge', selectedStock?.riskLevel]">
              {{ getRiskText(selectedStock?.riskLevel) }}
            </span>
          </div>
          <div class="overview-item">
            <span class="overview-label">情绪评分</span>
            <span class="sentiment-score" :style="{ color: getSentimentColor(selectedStock?.sentimentScore) }">
              {{ selectedStock?.sentimentScore || 50 }}分
            </span>
          </div>
          <div class="overview-item">
            <span class="overview-label">最后更新</span>
            <span>{{ formatTime(selectedStock?.lastUpdate) }}</span>
          </div>
        </div>

        <!-- 标签页切换 - 改为6大类 -->
        <div class="detail-tabs">
          <button 
            :class="['detail-tab', { active: detailTab === 'realtime' }]"
            @click="detailTab = 'realtime'"
          >
            📈 实时数据
          </button>
          <button 
            :class="['detail-tab', { active: detailTab === 'financial' }]"
            @click="detailTab = 'financial'"
          >
            💰 财务数据
          </button>
          <button 
            :class="['detail-tab', { active: detailTab === 'risk' }]"
            @click="detailTab = 'risk'"
          >
            ⚠️ 风险监控
          </button>
          <button 
            :class="['detail-tab', { active: detailTab === 'equity' }]"
            @click="detailTab = 'equity'"
          >
            🏢 股权变动
          </button>
          <button 
            :class="['detail-tab', { active: detailTab === 'governance' }]"
            @click="detailTab = 'governance'"
          >
            👔 公司治理
          </button>
          <button 
            :class="['detail-tab', { active: detailTab === 'news' }]"
            @click="detailTab = 'news'"
          >
            📰 新闻舆情 <span v-if="stockNews.length" class="tab-badge">{{ stockNews.length }}</span>
          </button>
        </div>

        <!-- 1. 实时数据TAB -->
        <div v-if="detailTab === 'realtime'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>
          
          <div v-else-if="comprehensiveData" class="comprehensive-panels">
            <!-- 实时行情 -->
            <div v-if="comprehensiveData.realtime?.status === 'success'" class="data-panel">
              <h4>📈 实时行情</h4>
              <div class="info-grid-3col">
                <div class="info-card">
                  <span class="label">最新价</span>
                  <span class="value price-lg">{{ comprehensiveData.realtime.data.price }}</span>
                </div>
                <div class="info-card">
                  <span class="label">涨跌幅</span>
                  <span :class="['value', comprehensiveData.realtime.data.pct_change >= 0 ? 'up' : 'down']">
                    {{ comprehensiveData.realtime.data.pct_change }}%
                  </span>
                </div>
                <div class="info-card">
                  <span class="label">成交量</span>
                  <span class="value">{{ formatMoney(comprehensiveData.realtime.data.volume) }}</span>
                </div>
              </div>
            </div>

            <!-- 涨跌停 -->
            <div v-if="comprehensiveData.limit_list?.status === 'success'" class="data-panel">
              <h4>🔴 涨跌停记录</h4>
              <div class="mini-table">
                <table>
                  <tr v-for="(item, idx) in comprehensiveData.limit_list.data.slice(0, 5)" :key="idx">
                    <td>{{ item.trade_date }}</td>
                    <td>{{ item.limit }}</td>
                    <td>{{ item.pct_change }}%</td>
                  </tr>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.limit_list?.message }}</div>
          </div>
          
          <div v-else class="empty-state"><p>暂无数据</p></div>
        </div>

        <!-- 2. 财务数据TAB -->
        <div v-if="detailTab === 'financial'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>
          
          <div v-else-if="comprehensiveData?.financial" class="comprehensive-panels">
            <!-- 利润表 -->
            <div v-if="comprehensiveData.financial.income?.length" class="data-panel">
              <h4>💰 利润表</h4>
              <div class="financial-table">
                <table>
                  <thead>
                    <tr>
                      <th>报告期</th>
                      <th>营业收入</th>
                      <th>净利润</th>
                      <th>净利率</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in comprehensiveData.financial.income" :key="idx">
                      <td>{{ item.end_date }}</td>
                      <td>{{ formatMoney(item.revenue) }}</td>
                      <td>{{ formatMoney(item.n_income) }}</td>
                      <td>{{ (item.netprofit_margin * 100).toFixed(2) }}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 业绩预告 -->
            <div v-if="comprehensiveData.forecast?.status === 'success'" class="data-panel">
              <h4>📅 业绩预告</h4>
              <div class="forecast-cards">
                <div v-for="(item, idx) in [...(comprehensiveData.forecast.forecast || [])].slice(0, 3)" :key="idx" class="forecast-card">
                  <div class="forecast-period">{{ item.end_date }}</div>
                  <p class="forecast-text">{{ item.summary || item.notice_content }}</p>
                </div>
              </div>
            </div>
          </div>
          
          <div v-else class="empty-state"><p>无财务数据</p></div>
        </div>

        <!-- 3. 风险监控TAB -->
        <div v-if="detailTab === 'risk'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>
          
          <div v-else-if="comprehensiveData" class="risk-cards-grid">
            <!-- ST状态 -->
            <div class="risk-card" :class="comprehensiveData.st_status?.is_st ? 'danger' : 'safe'">
              <h4>⚠️ ST状态</h4>
              <div class="risk-badge" :class="comprehensiveData.st_status?.is_st ? 'danger' : 'safe'">
                {{ comprehensiveData.st_status?.message }}
              </div>
            </div>

            <!-- 停复牌 -->
            <div class="risk-card">
              <h4>🚫 停复牌</h4>
              <p>{{ comprehensiveData.suspend?.message }}</p>
            </div>

            <!-- 股权质押 -->
            <div class="risk-card" :class="comprehensiveData.pledge?.pledge_ratio > 50 ? 'danger' : 'safe'">
              <h4>🔒 股权质押</h4>
              <div class="pledge-value">{{ comprehensiveData.pledge?.pledge_ratio || 0 }}%</div>
            </div>

            <!-- 融资融券 -->
            <div v-if="comprehensiveData.margin?.status === 'success'" class="risk-card full-width">
              <h4>📊 融资融券</h4>
              <div class="mini-table">
                <table>
                  <tr v-for="(item, idx) in comprehensiveData.margin.data.slice(0, 5)" :key="idx">
                    <td>{{ item.trade_date }}</td>
                    <td>{{ formatMoney(item.rzye) }}</td>
                    <td>{{ formatMoney(item.rqye) }}</td>
                  </tr>
                </table>
              </div>
            </div>
          </div>
          
          <div v-else class="empty-state"><p>无风险数据</p></div>
        </div>

        <!-- 4. 股权变动TAB -->
        <div v-if="detailTab === 'equity'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>
          
          <div v-else-if="comprehensiveData" class="comprehensive-panels">
            <!-- 分红送股 -->
            <div v-if="comprehensiveData.dividend?.status === 'success'" class="data-panel">
              <h4>🎁 分红送股</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>实施日期</th><th>每10股派息</th><th>每10股转增</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in comprehensiveData.dividend.records.slice(0, 5)" :key="idx">
                      <td>{{ item.ex_date }}</td>
                      <td>{{ item.cash_div }}元</td>
                      <td>{{ item.add_share || 0 }}股</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 股东增减持 -->
            <div v-if="comprehensiveData.holder_trade?.status === 'success'" class="data-panel">
              <h4>📄 股东增减持</h4>
              <div class="mini-table">
                <table>
                  <tbody>
                    <tr v-for="(item, idx) in comprehensiveData.holder_trade.records.slice(0, 5)" :key="idx">
                      <td>{{ item.ann_date }}</td>
                      <td>{{ item.holder_name }}</td>
                      <td :class="item.change_vol > 0 ? 'up' : 'down'">
                        {{ (item.change_vol / 10000).toFixed(2) }}万股
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          <div v-else class="empty-state"><p>无股权变动数据</p></div>
        </div>

        <!-- 5. 公司治理TAB -->
        <div v-if="detailTab === 'governance'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>
          
          <div v-else-if="comprehensiveData" class="comprehensive-panels">
            <!-- 公司信息 -->
            <div v-if="comprehensiveData.company_info?.status === 'success'" class="data-panel">
              <h4>🏢 公司基本信息</h4>
              <div class="info-grid-2col">
                <div><span class="label">董事长：</span>{{ comprehensiveData.company_info.data.chairman }}</div>
                <div><span class="label">总经理：</span>{{ comprehensiveData.company_info.data.manager }}</div>
                <div><span class="label">注册资本：</span>{{ comprehensiveData.company_info.data.reg_capital }}万</div>
                <div><span class="label">员工数：</span>{{ comprehensiveData.company_info.data.employees }}人</div>
              </div>
            </div>

            <!-- 管理层 -->
            <div v-if="comprehensiveData.managers?.status === 'success'" class="data-panel">
              <h4>👔 管理层</h4>
              <div class="mini-table">
                <table>
                  <tbody>
                    <tr v-for="(item, idx) in comprehensiveData.managers.data.slice(0, 10)" :key="idx">
                      <td>{{ item.name }}</td>
                      <td>{{ item.title }}</td>
                      <td>{{ item.edu }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 龙虎榜 -->
            <div v-if="comprehensiveData.dragon_tiger?.status === 'success'" class="data-panel">
              <h4>🐉 龙虎榜</h4>
              <div class="mini-table">
                <table>
                  <tbody>
                    <tr v-for="(item, idx) in comprehensiveData.dragon_tiger.records.slice(0, 5)" :key="idx">
                      <td>{{ item.date }}</td>
                      <td>{{ item.reason }}</td>
                      <td :class="item.net > 0 ? 'up' : 'down'">
                        {{ (item.net / 10000).toFixed(2) }}万
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 大宗交易 -->
            <div v-if="comprehensiveData.block_trade?.status === 'success'" class="data-panel">
              <h4>💼 大宗交易</h4>
              <div class="mini-table">
                <table>
                  <tbody>
                    <tr v-for="(item, idx) in comprehensiveData.block_trade.data.slice(0, 5)" :key="idx">
                      <td>{{ item.交易日期 }}</td>
                      <td>{{ item.成交价 }}</td>
                      <td>{{ item.成交量 }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>
          
          <div v-else class="empty-state"><p>无公司治理数据</p></div>
        </div>

        <!-- 新闻舆情页面 -->
        <div v-if="detailTab === 'news'" class="detail-content">
          <!-- 新闻类型筛选 -->
          <div class="filter-bar">
            <button 
              v-for="type in [
                { value: 'all', label: '全部' },
                { value: 'financial', label: '📈 财报' },
                { value: 'announcement', label: '📢 公告' },
                { value: 'news', label: '📰 新闻' },
                { value: 'policy', label: '🏛️ 政策' },
                { value: 'research', label: '🔍 研报' }
              ]"
              :key="type.value"
              :class="['filter-btn', { active: newsTypeFilter === type.value }]"
              @click="newsTypeFilter = type.value"
            >
              {{ type.label }}
            </button>
          </div>

          <!-- 新闻列表 -->
          <div class="news-detail-list">
            <div v-if="filteredStockNews.length === 0" class="empty-state">
              <p>暂无此类型新闻</p>
            </div>
            <div 
              v-for="(news, index) in filteredStockNews" 
              :key="index"
              :class="['news-detail-item', getNewsUrgencyClass(news)]"
            >
              <!-- 紧急标签 -->
              <div v-if="news.urgency === 'critical' || news.urgency === 'high'" class="urgency-badge">
                {{ news.urgency === 'critical' ? '⚠️ 特别重大' : '🔴 重要' }}
              </div>
              
              <div class="news-detail-header">
                <h4 @click="openNewsLink(news)" :class="{ 'clickable-title': news.url }">{{ news.title }}</h4>
                <div class="news-meta">
                  <span class="news-type-tag">{{ getReportTypeLabel(news.report_type) }}</span>
                  <span class="news-time">{{ news.pub_time }}</span>
                </div>
              </div>
              
              <p class="news-content">{{ news.content }}</p>
              
              <div class="news-detail-footer">
                <span class="news-source">📰 {{ news.source }}</span>
                <span :class="['sentiment-indicator', getSentimentClass(news.sentiment)]">
                  情绪: {{ getSentimentLabel(news.sentiment) }} ({{ news.score }})
                </span>
                <span class="urgency-level">
                  紧急度: {{ getUrgencyLabel(news.urgency) }}
                </span>
              </div>
              
              <!-- 关键词高亮 -->
              <div v-if="news.keywords && news.keywords.length > 0" class="keywords">
                <span v-for="keyword in news.keywords.slice(0, 5)" :key="keyword" class="keyword-tag">
                  {{ keyword }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 风险分析页面 -->
        <div v-if="detailTab === 'risk'" class="detail-content">
          <div class="risk-analysis">
            <div class="risk-score-panel">
              <div class="risk-score-big">
                <div class="score-value">{{ stockRisk.risk_score || 0 }}</div>
                <div class="score-label">风险评分</div>
              </div>
              <div :class="['risk-level-big', stockRisk.risk_level]">
                {{ getRiskText(stockRisk.risk_level) }}
              </div>
            </div>

            <!-- 风险细分 -->
            <div class="risk-breakdown">
              <h4>🔍 风险细分项</h4>
              
              <!-- 停复牌风险 -->
              <div class="risk-item">
                <div class="risk-item-header">
                  <span>🚫 停复牌状态</span>
                  <span :class="['risk-status', stockRisk.suspend_info?.is_suspended ? 'danger' : 'safe']">
                    {{ stockRisk.suspend_info?.is_suspended ? '已停牌' : '正常交易' }}
                  </span>
                </div>
                <p v-if="stockRisk.suspend_info?.reason" class="risk-reason">
                  原因: {{ stockRisk.suspend_info.reason }}
                </p>
              </div>

              <!-- ST状态 -->
              <div class="risk-item">
                <div class="risk-item-header">
                  <span>⚠️ ST状态</span>
                  <span :class="['risk-status', stockRisk.st_info?.is_st ? 'warning' : 'safe']">
                    {{ stockRisk.st_info?.is_st ? 'ST股票' : '非ST股票' }}
                  </span>
                </div>
                <p v-if="stockRisk.st_info?.st_type" class="risk-reason">
                  类型: {{ stockRisk.st_info.st_type }}
                </p>
              </div>

              <!-- 实时行情 -->
              <div v-if="stockRisk.realtime_data" class="risk-item">
                <div class="risk-item-header">
                  <span>📊 实时行情</span>
                </div>
                <div class="realtime-data">
                  <div class="data-row">
                    <span>最新价:</span>
                    <span class="data-value">{{ stockRisk.realtime_data.price }}</span>
                  </div>
                  <div class="data-row">
                    <span>涨跌幅:</span>
                    <span :class="['data-value', stockRisk.realtime_data.change_pct > 0 ? 'positive' : 'negative']">
                      {{ stockRisk.realtime_data.change_pct }}%
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 情绪分析页面 -->
        <div v-if="detailTab === 'sentiment'" class="detail-content">
          <div class="sentiment-analysis">
            <!-- 总体情绪 -->
            <div class="sentiment-overview">
              <div class="sentiment-score-panel">
                <div class="sentiment-score-big" :style="{ color: getSentimentColor(stockSentiment.overall_score) }">
                  {{ stockSentiment.overall_score || 50 }}
                </div>
                <div class="sentiment-label">{{ getSentimentLabel(stockSentiment.overall_sentiment) }}</div>
              </div>
            </div>

            <!-- 情绪分布 -->
            <div class="sentiment-distribution">
              <h4>📊 情绪分布</h4>
              <div class="distribution-bars">
                <div class="bar-item">
                  <span class="bar-label">正面</span>
                  <div class="bar-container">
                    <div 
                      class="bar positive" 
                      :style="{ width: getPercentage(stockSentiment.positive_count, getTotalSentiment()) + '%' }"
                    ></div>
                  </div>
                  <span class="bar-value">{{ stockSentiment.positive_count || 0 }}</span>
                </div>
                <div class="bar-item">
                  <span class="bar-label">中性</span>
                  <div class="bar-container">
                    <div 
                      class="bar neutral" 
                      :style="{ width: getPercentage(stockSentiment.neutral_count, getTotalSentiment()) + '%' }"
                    ></div>
                  </div>
                  <span class="bar-value">{{ stockSentiment.neutral_count || 0 }}</span>
                </div>
                <div class="bar-item">
                  <span class="bar-label">负面</span>
                  <div class="bar-container">
                    <div 
                      class="bar negative" 
                      :style="{ width: getPercentage(stockSentiment.negative_count, getTotalSentiment()) + '%' }"
                    ></div>
                  </div>
                  <span class="bar-value">{{ stockSentiment.negative_count || 0 }}</span>
                </div>
              </div>
            </div>

            <!-- 紧急度统计 -->
            <div v-if="stockSentiment.urgency_stats" class="urgency-stats">
              <h4>⚡ 紧急度统计</h4>
              <div class="stats-grid">
                <div v-for="(count, level) in stockSentiment.urgency_stats" :key="level" class="stat-item">
                  <span class="stat-label">{{ getUrgencyLabel(level) }}</span>
                  <span class="stat-value">{{ count }}</span>
                </div>
              </div>
            </div>

            <!-- 报告类型统计 -->
            <div v-if="stockSentiment.report_type_stats" class="report-type-stats">
              <h4>📋 报告类型统计</h4>
              <div class="stats-grid">
                <div v-for="(count, type) in stockSentiment.report_type_stats" :key="type" class="stat-item">
                  <span class="stat-label">{{ getReportTypeLabel(type) }}</span>
                  <span class="stat-value">{{ count }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 数据过期提示 -->
        <div class="data-notice">
          📅 服务器仅保存1天历史数据，请及时备份重要信息
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import axios from 'axios'

export default {
  name: 'DataFlowView',
  setup() {
    const API_BASE = 'http://localhost:8000/api'
    
    // 状态数据
    const isRefreshing = ref(false)
    const showAddMonitor = ref(false)
    const showStockDetails = ref(false)
    const currentFilter = ref('全部')
    const newsSource = ref('all')
    const detailTab = ref('realtime')  // realtime, financial, risk, equity, governance, news
    const newsTypeFilter = ref('all')  // all, financial, announcement, news, policy, research
    
    // 综合数据
    const loadingComprehensive = ref(false)
    const comprehensiveData = ref(null)
    
    const monitoredStocks = ref([])
    const dataSources = ref([])
    const newsList = ref([])
    const selectedStock = ref(null)
    const stockNews = ref([])
    const stockSentiment = ref({})
    const stockRisk = ref({})
    const toasts = ref([])  // Toast通知列表
    
    const newMonitor = reactive({
      code: '',
      frequency: '1h',
      items: {
        news: true,
        risk: true,
        sentiment: true,
        suspend: false
      }
    })
    
    // Toast通知系统
    const showToast = (message, type = 'info') => {
      const icons = {
        success: '✅',
        error: '❌',
        warning: '⚠️',
        info: 'ℹ️'
      }
      
      const toast = {
        id: Date.now(),
        message,
        type,
        icon: icons[type] || icons.info
      }
      
      toasts.value.push(toast)
      
      // 3秒后自动移除
      setTimeout(() => {
        const index = toasts.value.findIndex(t => t.id === toast.id)
        if (index > -1) {
          toasts.value.splice(index, 1)
        }
      }, 3000)
    }
    
    // 计算属性
    const todayNewsCount = computed(() => newsList.value.length)
    const riskAlertCount = computed(() => 
      monitoredStocks.value.filter(s => s.riskLevel === 'high').length
    )
    const analysisTaskCount = computed(() => 
      monitoredStocks.value.reduce((sum, s) => sum + (s.pendingTasks || 0), 0)
    )
    
    const filteredStocks = computed(() => {
      if (currentFilter.value === '全部') return monitoredStocks.value
      const riskMap = {
        '高风险': 'high',
        '中风险': 'medium',
        '低风险': 'low'
      }
      return monitoredStocks.value.filter(s => s.riskLevel === riskMap[currentFilter.value])
    })
    
    const filteredStockNews = computed(() => {
      if (newsTypeFilter.value === 'all') return stockNews.value
      return stockNews.value.filter(news => news.report_type === newsTypeFilter.value)
    })
    
    // 方法
    const loadMonitoredStocks = async () => {
      try {
        const response = await axios.get(`${API_BASE}/dataflow/monitored-stocks`)
        if (response.data.success) {
          monitoredStocks.value = response.data.stocks
        }
      } catch (error) {
        console.error('加载监控股票失败:', error)
      }
    }
    
    const loadDataSources = async () => {
      try {
        const response = await axios.get(`${API_BASE}/dataflow/sources/status`)
        if (response.data.success) {
          dataSources.value = response.data.sources
        }
      } catch (error) {
        console.error('加载数据源状态失败:', error)
      }
    }
    
    const loadNews = async () => {
      try {
        const params = newsSource.value === 'all' ? {} : { source: newsSource.value }
        const response = await axios.get(`${API_BASE}/dataflow/news`, { params })
        if (response.data.success) {
          newsList.value = response.data.news
        }
      } catch (error) {
        console.error('加载新闻失败:', error)
      }
    }
    
    const refreshAllData = async () => {
      isRefreshing.value = true
      try {
        await Promise.all([
          loadMonitoredStocks(),
          loadDataSources(),
          loadNews()
        ])
      } finally {
        isRefreshing.value = false
      }
    }
    
    const checkDataSources = async () => {
      try {
        const response = await axios.post(`${API_BASE}/dataflow/sources/check`)
        if (response.data.success) {
          await loadDataSources()
          showToast('数据源检测完成', 'success')
        }
      } catch (error) {
        console.error('检测数据源失败:', error)
        showToast('检测失败: ' + error.message, 'error')
      }
    }
    
    const addMonitor = async () => {
      if (!newMonitor.code) {
        showToast('请输入股票代码', 'warning')
        return
      }
      
      try {
        const response = await axios.post(`${API_BASE}/dataflow/monitor/add`, newMonitor)
        if (response.data.success) {
          showAddMonitor.value = false
          newMonitor.code = ''
          await loadMonitoredStocks()
          showToast('添加成功', 'success')
        }
      } catch (error) {
        console.error('添加监控失败:', error)
        showToast('添加失败: ' + (error.response?.data?.detail || error.message), 'error')
      }
    }
    
    const removeMonitor = async (stock) => {
      if (!confirm(`确定移除 ${stock.name}(${stock.code}) 的监控？`)) return
      
      try {
        const response = await axios.post(`${API_BASE}/dataflow/monitor/remove`, {
          code: stock.code
        })
        if (response.data.success) {
          await loadMonitoredStocks()
        }
      } catch (error) {
        console.error('移除监控失败:', error)
        showToast('移除失败: ' + error.message, 'error')
      }
    }
    
    const updateNow = async (stock) => {
      try {
        const response = await axios.post(`${API_BASE}/dataflow/monitor/update`, {
          code: stock.code
        })
        if (response.data.success) {
          showToast('更新任务已提交', 'success')
          await loadMonitoredStocks()
          await loadNews()  // 刷新新闻列表
        }
      } catch (error) {
        console.error('更新失败:', error)
        showToast('更新失败: ' + error.message, 'error')
      }
    }
    
    const viewDetails = (stock) => {
      console.log('查看详情:', stock)
      selectedStock.value = stock
      showStockDetails.value = true
      // 加载详细数据
      loadStockDetails(stock.code)
    }
    
    const loadStockDetails = async (code) => {
      try {
        // 加载综合数据
        loadingComprehensive.value = true
        
        // 1. 获取综合数据
        try {
          const comprehensiveResp = await fetch(`/api/dataflow/stock/comprehensive/${code}`)
          const comprehensiveResult = await comprehensiveResp.json()
          
          if (comprehensiveResult.success) {
            comprehensiveData.value = comprehensiveResult
            console.log('📊 综合数据加载成功')
          }
        } catch (error) {
          console.error('综合数据加载失败:', error)
        } finally {
          loadingComprehensive.value = false
        }
        
        // 2. 获取新闻详情  
        const newsResp = await fetch(`/api/dataflow/stock/news/${code}?limit=20`)
        const newsData = await newsResp.json()
        
        if (newsData.success) {
          stockNews.value = newsData.news || []
          console.log(`加载新闻: ${stockNews.value.length}条`)
        } else {
          stockNews.value = []
          showToast('新闻加载失败: ' + (newsData.detail || '未知错误'), 'error')
        }
        
        // 获取情绪分析
        const sentimentResp = await fetch(`/api/dataflow/stock/sentiment/${code}`)
        const sentimentData = await sentimentResp.json()
        
        if (sentimentData.success) {
          stockSentiment.value = sentimentData
          console.log(`情绪分析: ${sentimentData.overall_score}分`)
        } else {
          stockSentiment.value = {}
          showToast('情绪分析失败', 'error')
        }
        
        // 获取风险分析
        const riskResp = await fetch(`/api/dataflow/stock/risk/${code}`)
        const riskData = await riskResp.json()
        
        if (riskData.success) {
          stockRisk.value = riskData
          console.log(`风险等级: ${riskData.risk_level}`)
        } else {
          stockRisk.value = {}
        }
      } catch (error) {
        console.error('加载详情失败:', error)
        showToast('加载详情失败: ' + error.message, 'error')
      }
    }
    
    // 工具方法
    const formatTime = (timestamp) => {
      if (!timestamp) return '未知'
      const date = new Date(timestamp)
      const now = new Date()
      const diff = now - date
      
      if (diff < 60000) return '刚刚'
      if (diff < 3600000) return Math.floor(diff / 60000) + '分钟前'
      if (diff < 86400000) return Math.floor(diff / 3600000) + '小时前'
      return date.toLocaleDateString()
    }
    
    const getStatusText = (status) => {
      const map = {
        online: '在线',
        offline: '离线',
        error: '错误',
        checking: '检测中'
      }
      return map[status] || '未知'
    }
    
    const getRiskText = (level) => {
      const map = {
        high: '高风险',
        medium: '中风险',
        low: '低风险',
        none: '无风险'
      }
      return map[level] || '未知'
    }
    
    const getSentimentColor = (score) => {
      if (score >= 70) return '#10b981'
      if (score >= 40) return '#f59e0b'
      return '#ef4444'
    }
    
    const getSentimentClass = (sentiment) => {
      if (sentiment === 'positive' || sentiment > 0) return 'positive'
      if (sentiment === 'negative' || sentiment < 0) return 'negative'
      return 'neutral'
    }
    
    const formatMoney = (value) => {
      if (!value) return '0'
      const num = parseFloat(value)
      if (num >= 100000000) return (num / 100000000).toFixed(2) + '亿'
      if (num >= 10000) return (num / 10000).toFixed(2) + '万'
      return num.toFixed(2)
    }
    
    const getSentimentLabel = (sentiment) => {
      const map = {
        positive: '正面',
        negative: '负面',
        neutral: '中性'
      }
      return map[sentiment] || '未知'
    }
    
    const getReportTypeLabel = (type) => {
      const map = {
        financial: '📈 财务报告',
        announcement: '📢 公告',
        news: '📰 新闻',
        policy: '🏛️ 政策',
        research: '🔍 研报',
        unknown: '📋 其他'
      }
      return map[type] || '📋 其他'
    }
    
    const getUrgencyLabel = (urgency) => {
      const map = {
        critical: '特别重大',
        high: '重要',
        medium: '一般',
        low: '普通'
      }
      return map[urgency] || '普通'
    }
    
    const getNewsUrgencyClass = (news) => {
      if (news.urgency === 'critical') return 'critical-news'
      if (news.urgency === 'high') return 'important-news'
      return ''
    }
    
    const getTotalSentiment = () => {
      const total = (stockSentiment.value.positive_count || 0) + 
                    (stockSentiment.value.neutral_count || 0) + 
                    (stockSentiment.value.negative_count || 0)
      return total || 1
    }
    
    const getPercentage = (value, total) => {
      if (!total || total === 0) return 0
      return Math.round((value / total) * 100)
    }

    const openNewsLink = (news) => {
      if (news.url) {
        window.open(news.url, '_blank')
      }
    }

    // 生命周期
    onMounted(() => {
      refreshAllData()
      // 每30秒自动刷新
      setInterval(refreshAllData, 30000)
    })
    
    return {
      isRefreshing,
      showAddMonitor,
      showStockDetails,
      currentFilter,
      newsSource,
      detailTab,
      newsTypeFilter,
      monitoredStocks,
      dataSources,
      newsList,
      selectedStock,
      stockNews,
      stockSentiment,
      stockRisk,
      toasts,  // 添加toasts
      newMonitor,
      // 综合数据
      loadingComprehensive,
      comprehensiveData,
      todayNewsCount,
      riskAlertCount,
      analysisTaskCount,
      filteredStocks,
      filteredStockNews,
      refreshAllData,
      checkDataSources,
      addMonitor,
      removeMonitor,
      updateNow,
      viewDetails,
      loadStockDetails,
      openNewsLink,
      formatTime,
      formatMoney,  // 新增
      getStatusText,
      getRiskText,
      getSentimentColor,
      getSentimentClass,
      getSentimentLabel,
      getReportTypeLabel,
      getUrgencyLabel,
      getNewsUrgencyClass,
      getTotalSentiment,
      getPercentage
    }
  }
}
</script>

<style scoped>
/* Toast通知系统 */
.toast-container {
  position: fixed;
  top: 80px;
  right: 20px;
  z-index: 10000;
  display: flex;
  flex-direction: column;
  gap: 10px;
  pointer-events: none;
}

.toast {
  padding: 12px 20px;
  border-radius: 8px;
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 250px;
  max-width: 400px;
  pointer-events: auto;
  animation: slideIn 0.3s ease-out;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

.toast.success {
  border-color: #10b981;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.2), rgba(15, 23, 42, 0.95));
}

.toast.error {
  border-color: #ef4444;
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.2), rgba(15, 23, 42, 0.95));
}

.toast.warning {
  border-color: #f59e0b;
  background: linear-gradient(135deg, rgba(245, 158, 11, 0.2), rgba(15, 23, 42, 0.95));
}

.toast.info {
  border-color: #3b82f6;
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(15, 23, 42, 0.95));
}

.toast-icon {
  font-size: 1.2rem;
}

.toast-message {
  color: #e2e8f0;
  font-size: 0.9rem;
  flex: 1;
}

/* 美化滚动条 */
::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.3);
  border-radius: 4px;
}

::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.6), rgba(139, 92, 246, 0.6));
  border-radius: 4px;
  transition: background 0.3s;
}

::-webkit-scrollbar-thumb:hover {
  background: linear-gradient(180deg, rgba(99, 102, 241, 0.8), rgba(139, 92, 246, 0.8));
}

.dataflow-container {
  padding: 2rem;
  max-width: 1600px;
  margin: 0 auto;
  min-height: calc(100vh - 160px);
  color: #e2e8f0;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
}

.page-header h1 {
  font-size: 2rem;
  margin-bottom: 0.25rem;
  color: #f1f5f9;
}

.subtitle {
  color: rgba(226, 232, 240, 0.7);
}

.header-actions {
  display: flex;
  gap: 0.75rem;
}

/* 统计卡片 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2rem;
}

.stat-card {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 16px;
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
}

.stat-icon {
  font-size: 2.5rem;
}

.stat-content {
  flex: 1;
}

.stat-label {
  font-size: 0.875rem;
  color: rgba(226, 232, 240, 0.7);
  margin-bottom: 0.25rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: 700;
  color: #f1f5f9;
}

.stat-value.risk {
  color: #ef4444;
}

/* 卡片 */
.card {
  background: rgba(15, 23, 42, 0.65);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 18px;
  padding: 1.5rem;
  box-shadow: 0 15px 35px rgba(15, 23, 42, 0.4);
  color: #e2e8f0;
}

.section {
  margin-bottom: 2rem;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
}

.section-header h2 {
  font-size: 1.5rem;
  color: #f1f5f9;
}

/* 数据源网格 */
.data-sources-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 1rem;
}

.source-card {
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 1rem;
}

.source-card.online {
  border-color: rgba(16, 185, 129, 0.3);
}

.source-card.offline {
  border-color: rgba(239, 68, 68, 0.3);
}

.source-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
}

.source-name {
  font-weight: 600;
  color: #f1f5f9;
}

.status-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
}

.status-badge.online {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.status-badge.offline {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.source-info .info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
}

.source-info .label {
  color: rgba(226, 232, 240, 0.7);
}

.error-message {
  color: #ef4444;
  font-size: 0.875rem;
  margin-top: 0.5rem;
}

/* 过滤标签 */
.filter-tabs {
  display: flex;
  gap: 0.5rem;
}

.filter-tab {
  padding: 0.5rem 1rem;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: transparent;
  color: #e2e8f0;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
}

.filter-tab.active {
  background: rgba(99, 102, 241, 0.2);
  border-color: rgba(99, 102, 241, 0.4);
  color: #a5b4fc;
}

/* 表格 */
.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
}

.data-table th {
  background: rgba(15, 23, 42, 0.5);
  color: #f1f5f9;
  font-weight: 600;
}

.data-table td.code {
  font-family: monospace;
  color: #a5b4fc;
}

.sentiment-score {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.score-bar {
  flex: 1;
  height: 8px;
  background: rgba(148, 163, 184, 0.2);
  border-radius: 4px;
  overflow: hidden;
}

.score-fill {
  height: 100%;
  transition: width 0.3s;
}

.risk-badge {
  padding: 0.25rem 0.75rem;
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 600;
}

.risk-badge.high {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.risk-badge.medium {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.risk-badge.low {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.news-preview {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 新闻列表 */
.news-list {
  max-height: 600px;
  overflow-y: auto;
}

.news-item {
  border-bottom: 1px solid rgba(148, 163, 184, 0.1);
  padding: 1rem 0;
}

.news-item:last-child {
  border-bottom: none;
}

.news-header {
  display: flex;
  justify-content: space-between;
  align-items: start;
  margin-bottom: 0.5rem;
}

.news-header h3 {
  color: #f1f5f9;
  font-size: 1rem;
  flex: 1;
}

.news-time {
  color: rgba(226, 232, 240, 0.6);
  font-size: 0.875rem;
}

.news-meta {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.875rem;
  color: rgba(226, 232, 240, 0.7);
}

.news-sentiment.positive {
  color: #10b981;
}

.news-sentiment.negative {
  color: #ef4444;
}

.news-summary {
  color: rgba(226, 232, 240, 0.8);
  line-height: 1.5;
}

/* 按钮 */
.btn-primary,
.btn-secondary,
.btn-small,
.btn-danger-small {
  border: none;
  border-radius: 8px;
  padding: 0.5rem 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: opacity 0.2s;
}

.btn-primary {
  background: linear-gradient(135deg, #38bdf8, #6366f1);
  color: #fff;
}

.btn-secondary {
  background: rgba(148, 163, 184, 0.15);
  color: #e2e8f0;
}

.btn-small {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  background: rgba(99, 102, 241, 0.2);
  color: #a5b4fc;
}

.btn-danger-small {
  padding: 0.25rem 0.75rem;
  font-size: 0.875rem;
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

/* 模态框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: rgba(15, 23, 42, 0.95);
  border: 1px solid rgba(99, 102, 241, 0.3);
  border-radius: 16px;
  padding: 2rem;
  min-width: 500px;
  max-width: 90%;
}

.modal-content h3 {
  color: #f1f5f9;
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  color: #f1f5f9;
}

.input-field {
  width: 100%;
  padding: 0.75rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  color: #e2e8f0;
}

.checkbox-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.checkbox-group label {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: #e2e8f0;
}

.modal-actions {
  display: flex;
  gap: 1rem;
  justify-content: flex-end;
  margin-top: 2rem;
}

.empty-state {
  text-align: center;
  padding: 3rem;
  color: rgba(226, 232, 240, 0.6);
}

.news-source-select {
  padding: 0.5rem 1rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  color: #e2e8f0;
}

/* 股票详情弹窗样式 */
.stock-detail-modal {
  max-width: 1200px;
  width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
}

.modal-header h3 {
  margin: 0;
  font-size: 1.5rem;
  color: #e2e8f0;
}

.stock-code {
  font-size: 0.9rem;
  color: rgba(226, 232, 240, 0.7);
  margin-top: 0.25rem;
}

.close-btn {
  background: transparent;
  border: none;
  font-size: 2rem;
  color: #e2e8f0;
  cursor: pointer;
  padding: 0;
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.close-btn:hover {
  color: #3b82f6;
  transform: rotate(90deg);
}

.detail-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 8px;
}

.overview-item {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.overview-label {
  font-size: 0.85rem;
  color: rgba(226, 232, 240, 0.6);
}

.sentiment-score {
  font-size: 1.5rem;
  font-weight: bold;
}

.detail-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1.5rem;
  border-bottom: 2px solid rgba(148, 163, 184, 0.2);
}

.detail-tab {
  padding: 0.75rem 1.5rem;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: rgba(226, 232, 240, 0.7);
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
  position: relative;
}

.detail-tab:hover {
  color: #3b82f6;
}

.detail-tab.active {
  color: #3b82f6;
  border-bottom-color: #3b82f6;
}

.tab-badge {
  display: inline-block;
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  padding: 0.15rem 0.5rem;
  border-radius: 12px;
  font-size: 0.75rem;
  margin-left: 0.5rem;
}

.detail-content {
  min-height: 400px;
  max-height: 600px;
  overflow-y: auto;
}

.filter-bar {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.filter-btn {
  padding: 0.5rem 1rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 6px;
  color: rgba(226, 232, 240, 0.7);
  cursor: pointer;
  transition: all 0.3s;
}

.filter-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
}

.filter-btn.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: #3b82f6;
}

.news-detail-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.news-detail-item {
  padding: 1rem;
  background: rgba(15, 23, 42, 0.3);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  transition: all 0.3s;
  position: relative;
}

.news-detail-item:hover {
  border-color: rgba(59, 130, 246, 0.5);
  background: rgba(15, 23, 42, 0.5);
}

.news-detail-item.critical-news {
  border-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
  animation: pulse 2s infinite;
}

.news-detail-item.important-news {
  border-color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.8; }
}

.urgency-badge {
  position: absolute;
  top: -0.5rem;
  right: 1rem;
  padding: 0.25rem 0.75rem;
  background: #ef4444;
  color: white;
  border-radius: 12px;
  font-size: 0.75rem;
  font-weight: bold;
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.news-detail-header {
  margin-bottom: 0.75rem;
}

.news-detail-header h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #e2e8f0;
  line-height: 1.4;
}

.news-detail-header h4.clickable-title {
  cursor: pointer;
  color: #60a5fa;
  transition: color 0.2s;
}

.news-detail-header h4.clickable-title:hover {
  color: #3b82f6;
  text-decoration: underline;
}

.news-meta {
  display: flex;
  gap: 1rem;
  font-size: 0.85rem;
  color: rgba(226, 232, 240, 0.6);
}

.news-type-tag {
  background: rgba(59, 130, 246, 0.2);
  color: #3b82f6;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

.news-content {
  color: rgba(226, 232, 240, 0.8);
  line-height: 1.6;
  margin: 0.75rem 0;
}

.news-detail-footer {
  display: flex;
  gap: 1rem;
  margin-top: 0.75rem;
  font-size: 0.85rem;
  padding-top: 0.75rem;
  border-top: 1px solid rgba(148, 163, 184, 0.1);
}

.sentiment-indicator {
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
}

.sentiment-indicator.positive {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.sentiment-indicator.negative {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.sentiment-indicator.neutral {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.urgency-level {
  color: rgba(226, 232, 240, 0.7);
}

/* 新增：综合数据面板样式 */
.comprehensive-panels {
  display: flex;
  flex-direction: column;
  gap: 20px;
  padding: 20px;
}

.data-panel {
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid rgba(71, 85, 105, 0.3);
}

.data-panel h4 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #e2e8f0;
  font-weight: 600;
}

/* 信息网格 */
.info-grid-2col {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  color: #cbd5e1;
  font-size: 14px;
}

.info-grid-3col {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.info-card {
  background: rgba(51, 65, 85, 0.3);
  border-radius: 6px;
  padding: 16px;
  text-align: center;
}

.info-card .label {
  display: block;
  color: rgba(226, 232, 240, 0.6);
  font-size: 12px;
  margin-bottom: 8px;
}

.info-card .value {
  display: block;
  color: #e2e8f0;
  font-size: 20px;
  font-weight: 600;
}

.price-lg {
  font-size: 24px !important;
  color: #60a5fa;
}

/* 迷你表格 */
.mini-table {
  width: 100%;
  overflow-x: auto;
}

.mini-table table {
  width: 100%;
  border-collapse: collapse;
}

.mini-table td,
.mini-table th {
  padding: 10px;
  text-align: left;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  color: #cbd5e1;
  font-size: 13px;
}

.mini-table th {
  color: #e2e8f0;
  font-weight: 600;
  background: rgba(51, 65, 85, 0.3);
}

.mini-table tr:last-child td {
  border-bottom: none;
}

/* 财务表格 */
.financial-table table {
  width: 100%;
  border-collapse: collapse;
}

.financial-table th,
.financial-table td {
  padding: 12px;
  text-align: right;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
  color: #cbd5e1;
}

.financial-table th {
  color: #e2e8f0;
  font-weight: 600;
  background: rgba(51, 65, 85, 0.3);
}

.financial-table th:first-child,
.financial-table td:first-child {
  text-align: left;
}

/* 业绩预告卡片 */
.forecast-cards {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.forecast-card {
  background: rgba(51, 65, 85, 0.3);
  border-radius: 6px;
  padding: 16px;
  border-left: 3px solid #60a5fa;
}

.forecast-period {
  color: #60a5fa;
  font-weight: 600;
  margin-bottom: 8px;
}

.forecast-text {
  color: #cbd5e1;
  font-size: 14px;
  line-height: 1.6;
  margin: 0;
}

/* 风险卡片网格 */
.risk-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 16px;
  padding: 20px;
}

.risk-card {
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  padding: 20px;
  border: 1px solid rgba(71, 85, 105, 0.3);
}

.risk-card.danger {
  border-color: rgba(239, 68, 68, 0.5);
  background: rgba(127, 29, 29, 0.2);
}

.risk-card.safe {
  border-color: rgba(34, 197, 94, 0.5);
  background: rgba(20, 83, 45, 0.2);
}

.risk-card.full-width {
  grid-column: 1 / -1;
}

.risk-card h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  color: #e2e8f0;
}

.risk-badge {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 4px;
  font-weight: 600;
  font-size: 14px;
}

.risk-badge.danger {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.risk-badge.safe {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
}

.pledge-value {
  font-size: 32px;
  font-weight: 700;
  color: #e2e8f0;
  text-align: center;
  margin-top: 12px;
}

/* 空状态 */
.empty-state,
.empty-hint {
  text-align: center;
  padding: 40px;
  color: rgba(226, 232, 240, 0.5);
  font-size: 14px;
}

.loading-state {
  text-align: center;
  padding: 60px 20px;
}

.spinner {
  border: 3px solid rgba(96, 165, 250, 0.2);
  border-top-color: #60a5fa;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 16px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 涨跌颜色 */
.up {
  color: #22c55e !important;
}

.down {
  color: #ef4444 !important;
}

.keywords {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-top: 0.75rem;
}

.keyword-tag {
  background: rgba(59, 130, 246, 0.15);
  color: #60a5fa;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
}

/* 风险分析样式 */
.risk-analysis {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.risk-score-panel {
  display: flex;
  align-items: center;
  gap: 2rem;
  padding: 1.5rem;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.5), rgba(30, 41, 59, 0.3));
  border-radius: 8px;
}

.risk-score-big {
  text-align: center;
}

.score-value {
  font-size: 3rem;
  font-weight: bold;
  color: #e2e8f0;
  line-height: 1;
}

.score-label {
  font-size: 0.9rem;
  color: rgba(226, 232, 240, 0.6);
  margin-top: 0.5rem;
}

.risk-level-big {
  font-size: 1.5rem;
  font-weight: bold;
  padding: 0.75rem 1.5rem;
  border-radius: 8px;
}

.risk-level-big.high {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.risk-level-big.medium {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.risk-level-big.low {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.risk-breakdown h4 {
  margin: 0 0 1rem 0;
  color: #e2e8f0;
}

.risk-item {
  padding: 1rem;
  background: rgba(15, 23, 42, 0.3);
  border-radius: 8px;
  margin-bottom: 1rem;
}

.risk-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-weight: 500;
  color: #e2e8f0;
}

.risk-status {
  padding: 0.25rem 0.75rem;
  border-radius: 4px;
  font-size: 0.85rem;
}

.risk-status.safe {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
}

.risk-status.warning {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.risk-status.danger {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

.risk-reason {
  color: rgba(226, 232, 240, 0.7);
  font-size: 0.9rem;
  margin: 0.5rem 0 0 0;
}

.realtime-data {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.data-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 4px;
}

.data-value {
  font-weight: bold;
  color: #e2e8f0;
}

.data-value.positive {
  color: #10b981;
}

.data-value.negative {
  color: #ef4444;
}

/* 情绪分析样式 */
.sentiment-analysis {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.sentiment-overview {
  text-align: center;
  padding: 2rem;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.5), rgba(30, 41, 59, 0.3));
  border-radius: 8px;
}

.sentiment-score-big {
  font-size: 4rem;
  font-weight: bold;
  line-height: 1;
}

.sentiment-label {
  font-size: 1.2rem;
  margin-top: 0.5rem;
  color: rgba(226, 232, 240, 0.8);
}

.sentiment-distribution h4,
.urgency-stats h4,
.report-type-stats h4 {
  margin: 0 0 1rem 0;
  color: #e2e8f0;
}

.distribution-bars {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.bar-item {
  display: grid;
  grid-template-columns: 80px 1fr 60px;
  align-items: center;
  gap: 1rem;
}

.bar-label {
  color: #e2e8f0;
}

.bar-container {
  background: rgba(15, 23, 42, 0.5);
  height: 24px;
  border-radius: 4px;
  overflow: hidden;
}

.bar {
  height: 100%;
  transition: width 0.5s;
}

.bar.positive {
  background: linear-gradient(90deg, #10b981, #34d399);
}

.bar.neutral {
  background: linear-gradient(90deg, #f59e0b, #fbbf24);
}

.bar.negative {
  background: linear-gradient(90deg, #ef4444, #f87171);
}

.bar-value {
  color: #e2e8f0;
  font-weight: bold;
  text-align: right;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 1rem;
}

.stat-item {
  padding: 1rem;
  background: rgba(15, 23, 42, 0.3);
  border-radius: 8px;
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 0.85rem;
  color: rgba(226, 232, 240, 0.6);
  margin-bottom: 0.5rem;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: bold;
  color: #e2e8f0;
}

.data-notice {
  margin-top: 1.5rem;
  padding: 1rem;
  background: rgba(245, 158, 11, 0.1);
  border-left: 4px solid #f59e0b;
  border-radius: 4px;
  color: rgba(226, 232, 240, 0.8);
  font-size: 0.9rem;
}
</style>
