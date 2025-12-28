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
        <button @click="showNotificationSettings = true" class="btn-secondary">
          🔔 通知设置
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
      <div class="section-header clickable" @click="dataSourcesCollapsed = !dataSourcesCollapsed">
        <h2>
          <span class="collapse-icon">{{ dataSourcesCollapsed ? '▶' : '▼' }}</span>
          🔌 数据源状态
        </h2>
        <button @click.stop="openInterfaceTest" class="btn-secondary">检测连接</button>
      </div>
      <div v-show="!dataSourcesCollapsed" class="data-sources-grid">
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
        <div class="news-filters">
          <div class="sentiment-tabs">
            <button
              :class="['sentiment-tab', { active: sentimentFilter === 'non_neutral' }]"
              @click="sentimentFilter = 'non_neutral'"
            >
              🔥 有情绪 <span v-if="sentimentStats.positive + sentimentStats.negative > 0" class="tab-count">{{ sentimentStats.positive + sentimentStats.negative }}</span>
            </button>
            <button
              :class="['sentiment-tab positive', { active: sentimentFilter === 'positive' }]"
              @click="sentimentFilter = 'positive'"
            >
              😊 正面 <span v-if="sentimentStats.positive > 0" class="tab-count">{{ sentimentStats.positive }}</span>
            </button>
            <button
              :class="['sentiment-tab negative', { active: sentimentFilter === 'negative' }]"
              @click="sentimentFilter = 'negative'"
            >
              😟 负面 <span v-if="sentimentStats.negative > 0" class="tab-count">{{ sentimentStats.negative }}</span>
            </button>
            <button
              :class="['sentiment-tab', { active: sentimentFilter === 'all' }]"
              @click="sentimentFilter = 'all'"
            >
              全部
            </button>
          </div>
          <select v-model="newsSource" class="news-source-select">
            <option value="all">全部来源</option>
            <option value="东方财富">东方财富</option>
            <option value="财联社">财联社</option>
            <option value="央视新闻">央视新闻</option>
            <option value="同花顺">同花顺</option>
            <option value="富途牛牛">富途牛牛</option>
          </select>
        </div>
      </div>

      <div class="news-list">
        <!-- 新闻加载中状态 -->
        <div v-if="newsLoading && filteredNewsList.length === 0" class="loading-state">
          <div class="spinner"></div>
          <p>新闻正在后台加载中...</p>
        </div>
        <div v-else-if="filteredNewsList.length === 0" class="empty-state">
          <p>暂无{{ sentimentFilter === 'positive' ? '正面' : sentimentFilter === 'negative' ? '负面' : '' }}新闻数据</p>
        </div>
        <div
          v-for="(news, idx) in filteredNewsList"
          :key="`news-${idx}-${news.id || ''}`"
          :class="['news-item', `sentiment-${news.sentiment}`]"
        >
          <div class="news-header">
            <h3>
              <span :class="['sentiment-badge', news.sentiment]">
                {{ news.sentiment === 'positive' ? '😊' : news.sentiment === 'negative' ? '😟' : '😐' }}
              </span>
              <a v-if="news.url" :href="news.url" target="_blank" class="news-link">{{ news.title }}</a>
              <span v-else>{{ news.title }}</span>
            </h3>
            <span class="news-time">{{ formatTime(news.publishTime || news.pub_time) }}</span>
          </div>
          <div class="news-meta">
            <span class="news-source">{{ news.source }}</span>
            <span v-if="news.keywords?.length" class="news-keywords">
              关键词: {{ news.keywords.slice(0, 3).join(', ') }}
            </span>
            <span v-if="news.sentiment_score" :class="['news-score', news.sentiment]">
              情绪分: {{ news.sentiment_score }}
            </span>
          </div>
          <p class="news-summary">{{ news.summary || news.content }}</p>
          <a v-if="news.url" :href="news.url" target="_blank" class="news-read-more">阅读原文 →</a>
        </div>
      </div>
    </div>

    <!-- 添加监控对话框 -->
    <div v-if="showAddMonitor" class="modal-overlay" @click="showAddMonitor = false">
      <div class="modal-content" @click.stop>
        <h3>添加监控股票</h3>
        <div class="form-group">
          <label>股票代码</label>
          <StockSearchInput
            v-model="newMonitor.code"
            placeholder="输入股票代码或名称搜索"
            @select="onStockSelect"
          />
          <small v-if="selectedStockName" class="form-hint stock-selected">
            已选择: {{ selectedStockName }}
          </small>
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
          <label>保存周期</label>
          <select v-model="newMonitor.retention_days" class="input-field">
            <option :value="1">1天</option>
            <option :value="3">3天</option>
            <option :value="7">7天（默认）</option>
            <option :value="15">15天</option>
            <option :value="30">30天</option>
            <option :value="90">90天</option>
          </select>
          <small class="form-hint">超过该天数的历史数据将被自动清理</small>
        </div>
        <div class="form-group">
          <label>监控项目</label>
          <div class="checkbox-group">
            <label><input type="checkbox" v-model="newMonitor.items.news" /> 📰 新闻舆情</label>
            <label><input type="checkbox" v-model="newMonitor.items.risk" /> ⚠️ 风险分析</label>
            <label><input type="checkbox" v-model="newMonitor.items.sentiment" /> 😊 情绪分析</label>
            <label><input type="checkbox" v-model="newMonitor.items.suspend" /> 🚫 停复牌监控</label>
            <label><input type="checkbox" v-model="newMonitor.items.realtime" /> 📈 实时行情</label>
            <label><input type="checkbox" v-model="newMonitor.items.financial" /> 📊 财务数据</label>
            <label><input type="checkbox" v-model="newMonitor.items.capital" /> 💰 资金流向</label>
          </div>
        </div>
        <div class="modal-actions">
          <button @click="addMonitor" class="btn-primary">确认添加</button>
          <button @click="showAddMonitor = false" class="btn-secondary">取消</button>
        </div>
      </div>
    </div>

    <!-- 通知设置弹窗 -->
    <div v-if="showNotificationSettings" class="modal-overlay" @click="showNotificationSettings = false">
      <div class="modal-content notification-settings-modal" @click.stop>
        <div class="modal-header">
          <h3>🔔 通知设置</h3>
          <button @click="showNotificationSettings = false" class="close-btn">×</button>
        </div>

        <div class="notification-content">
          <!-- 通知渠道状态 -->
          <div class="notification-section">
            <h4>📡 通知渠道状态</h4>
            <div class="channels-grid">
              <div
                v-for="(channel, key) in notificationChannels"
                :key="key"
                :class="['channel-card', channel.configured ? 'configured' : 'not-configured']"
              >
                <div class="channel-icon">{{ channel.icon }}</div>
                <div class="channel-info">
                  <span class="channel-name">{{ channel.name }}</span>
                  <span class="channel-status">
                    {{ channel.configured ? '✅ 已配置' : '❌ 未配置' }}
                  </span>
                </div>
                <button
                  v-if="channel.configured"
                  @click="testNotificationChannel(key)"
                  class="btn-small"
                  :disabled="testingChannel === key"
                >
                  {{ testingChannel === key ? '测试中...' : '测试' }}
                </button>
              </div>
            </div>
          </div>

          <!-- 邮件配置 -->
          <div class="notification-section">
            <h4>📧 邮件通知配置</h4>
            <div class="config-form">
              <div class="form-row">
                <div class="form-group">
                  <label>SMTP服务器</label>
                  <input
                    v-model="notificationConfig.SMTP_HOST"
                    type="text"
                    placeholder="smtp.qq.com"
                    class="input-field"
                  />
                </div>
                <div class="form-group form-group-small">
                  <label>端口</label>
                  <input
                    v-model.number="notificationConfig.SMTP_PORT"
                    type="number"
                    placeholder="465"
                    class="input-field"
                  />
                </div>
                <div class="form-group form-group-small">
                  <label>SSL</label>
                  <select v-model="notificationConfig.SMTP_USE_SSL" class="input-field">
                    <option :value="true">是</option>
                    <option :value="false">否</option>
                  </select>
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>邮箱账号</label>
                  <input
                    v-model="notificationConfig.SMTP_USER"
                    type="email"
                    placeholder="your@qq.com"
                    class="input-field"
                  />
                </div>
                <div class="form-group">
                  <label>授权码/密码</label>
                  <input
                    v-model="notificationConfig.SMTP_PASSWORD"
                    type="password"
                    placeholder="SMTP授权码"
                    class="input-field"
                  />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>发件人地址（可选）</label>
                  <input
                    v-model="notificationConfig.SMTP_FROM"
                    type="email"
                    placeholder="留空则使用邮箱账号"
                    class="input-field"
                  />
                </div>
              </div>
              <div class="form-tips">
                <span class="tip-icon">💡</span>
                <span>QQ邮箱需要在设置中开启SMTP服务并获取授权码，163邮箱同样需要开启SMTP服务</span>
              </div>
            </div>
          </div>

          <!-- 企业微信配置 -->
          <div class="notification-section">
            <h4>💬 企业微信机器人配置</h4>
            <div class="config-form">
              <div class="form-group">
                <label>Webhook地址</label>
                <input
                  v-model="notificationConfig.WECHAT_WEBHOOK_URL"
                  type="text"
                  placeholder="https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx"
                  class="input-field"
                />
              </div>
              <div class="form-tips">
                <span class="tip-icon">💡</span>
                <span>在企业微信群中添加机器人获取Webhook地址</span>
              </div>
            </div>
          </div>

          <!-- 钉钉配置 -->
          <div class="notification-section">
            <h4>🔔 钉钉机器人配置</h4>
            <div class="config-form">
              <div class="form-row">
                <div class="form-group">
                  <label>Webhook地址</label>
                  <input
                    v-model="notificationConfig.DINGTALK_WEBHOOK_URL"
                    type="text"
                    placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx"
                    class="input-field"
                  />
                </div>
              </div>
              <div class="form-row">
                <div class="form-group">
                  <label>签名密钥（可选）</label>
                  <input
                    v-model="notificationConfig.DINGTALK_SECRET"
                    type="password"
                    placeholder="SECxxx"
                    class="input-field"
                  />
                </div>
              </div>
              <div class="form-tips">
                <span class="tip-icon">💡</span>
                <span>在钉钉群中添加自定义机器人获取Webhook地址，建议开启签名验证</span>
              </div>
            </div>
          </div>

          <!-- Server酱配置 -->
          <div class="notification-section">
            <h4>📱 Server酱配置</h4>
            <div class="config-form">
              <div class="form-group">
                <label>SendKey</label>
                <input
                  v-model="notificationConfig.SERVERCHAN_KEY"
                  type="password"
                  placeholder="SCTxxx"
                  class="input-field"
                />
              </div>
              <div class="form-tips">
                <span class="tip-icon">💡</span>
                <span>访问 <a href="https://sct.ftqq.com" target="_blank">sct.ftqq.com</a> 注册并获取SendKey</span>
              </div>
            </div>
          </div>

          <!-- Bark配置 -->
          <div class="notification-section">
            <h4>🍎 Bark配置（iOS推送）</h4>
            <div class="config-form">
              <div class="form-row">
                <div class="form-group">
                  <label>推送Key</label>
                  <input
                    v-model="notificationConfig.BARK_KEY"
                    type="password"
                    placeholder="your_bark_key"
                    class="input-field"
                  />
                </div>
                <div class="form-group">
                  <label>服务器地址（可选）</label>
                  <input
                    v-model="notificationConfig.BARK_SERVER"
                    type="text"
                    placeholder="https://api.day.app"
                    class="input-field"
                  />
                </div>
              </div>
              <div class="form-tips">
                <span class="tip-icon">💡</span>
                <span>在App Store下载Bark应用，打开应用获取推送Key</span>
              </div>
            </div>
          </div>

          <!-- 保存按钮 -->
          <div class="notification-section">
            <div class="config-actions">
              <button
                @click="saveNotificationConfig"
                class="btn-primary"
                :disabled="savingConfig"
              >
                {{ savingConfig ? '保存中...' : '💾 保存配置' }}
              </button>
              <button
                @click="loadNotificationConfig"
                class="btn-secondary"
                :disabled="savingConfig"
              >
                🔄 重新加载
              </button>
            </div>
          </div>

          <!-- 测试通知 -->
          <div class="notification-section">
            <h4>🧪 发送测试通知</h4>
            <div class="test-notification">
              <div class="form-group">
                <label>测试邮箱地址</label>
                <input
                  v-model="testEmail"
                  type="email"
                  placeholder="your@email.com"
                  class="input-field"
                />
              </div>
              <button
                @click="sendTestEmail"
                class="btn-primary"
                :disabled="!testEmail || sendingTestEmail"
              >
                {{ sendingTestEmail ? '发送中...' : '📧 发送测试邮件' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 接口测试弹窗 -->
    <div v-if="showInterfaceTest" class="modal-overlay" @click="showInterfaceTest = false">
      <div class="modal-content interface-test-modal" @click.stop>
        <div class="modal-header">
          <h3>🔌 接口连接测试</h3>
          <div class="header-actions">
            <span v-if="interfaceTestRunning" class="test-progress">
              测试进度: {{ interfaceTestProgress }}/{{ interfaceTestTotal }}
            </span>
            <button @click="showInterfaceTest = false" class="close-btn">×</button>
          </div>
        </div>

        <!-- 测试概览 -->
        <div class="test-overview">
          <div class="overview-stat">
            <span class="stat-icon">📊</span>
            <span class="stat-label">总接口</span>
            <span class="stat-value">{{ interfaceTestTotal }}</span>
          </div>
          <div class="overview-stat success">
            <span class="stat-icon">✅</span>
            <span class="stat-label">成功</span>
            <span class="stat-value">{{ interfaceTestSuccess }}</span>
          </div>
          <div class="overview-stat fail">
            <span class="stat-icon">❌</span>
            <span class="stat-label">失败</span>
            <span class="stat-value">{{ interfaceTestFail }}</span>
          </div>
          <div class="overview-stat">
            <span class="stat-icon">📈</span>
            <span class="stat-label">成功率</span>
            <span class="stat-value">{{ interfaceTestSuccessRate }}%</span>
          </div>
        </div>

        <!-- 进度条 -->
        <div v-if="interfaceTestRunning" class="test-progress-bar">
          <div
            class="progress-fill"
            :style="{ width: (interfaceTestProgress / interfaceTestTotal * 100) + '%' }"
          ></div>
        </div>

        <!-- 数据源分类测试结果 -->
        <div class="test-results-container">
          <div
            v-for="(source, sourceKey) in interfaceTestResults"
            :key="sourceKey"
            class="source-test-section"
          >
            <div
              class="source-test-header"
              @click="toggleSourceExpand(sourceKey)"
            >
              <span class="source-icon">{{ source.icon }}</span>
              <span class="source-name">{{ source.name }}</span>
              <span class="source-stats">
                <span class="stat-success">✅ {{ source.successCount || 0 }}</span>
                <span class="stat-fail">❌ {{ source.failCount || 0 }}</span>
                <span class="stat-pending" v-if="source.pendingCount > 0">⏳ {{ source.pendingCount }}</span>
              </span>
              <span class="expand-icon">{{ expandedSources[sourceKey] ? '▼' : '▶' }}</span>
            </div>

            <div v-if="expandedSources[sourceKey]" class="interface-test-list">
              <div
                v-for="(iface, idx) in source.interfaces"
                :key="idx"
                :class="['interface-test-item', iface.status]"
              >
                <span class="interface-name">{{ iface.name }}</span>
                <span class="interface-category">{{ iface.category }}</span>
                <span :class="['interface-status', iface.status]">
                  <span v-if="iface.status === 'testing'" class="testing-spinner"></span>
                  <span v-else-if="iface.status === 'success'">✅ {{ iface.elapsed }}s</span>
                  <span v-else-if="iface.status === 'error'">❌ 失败</span>
                  <span v-else-if="iface.status === 'timeout'">⏰ 超时</span>
                  <span v-else-if="iface.status === 'no_data'">⚪ 无数据</span>
                  <span v-else-if="iface.status === 'not_implemented'">🔧 未实现</span>
                  <span v-else>⏳ 等待</span>
                </span>
                <span v-if="iface.message" class="interface-message" :title="iface.message">
                  {{ iface.message }}
                </span>
              </div>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="modal-actions">
          <button
            @click="startInterfaceTest"
            class="btn-primary"
            :disabled="interfaceTestRunning"
          >
            {{ interfaceTestRunning ? '测试中...' : '🔄 重新测试' }}
          </button>
          <button @click="showInterfaceTest = false" class="btn-secondary">关闭</button>
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
          <div class="header-actions">
            <button @click="refreshCurrentStock" class="btn-secondary" :disabled="loadingComprehensive">
              <span v-if="!loadingComprehensive">🔄 刷新</span>
              <span v-else>⏳ 加载中...</span>
            </button>
            <button @click="showStockDetails = false" class="close-btn">×</button>
          </div>
        </div>

        <!-- 预警面板 - 始终显示在顶部 -->
        <div v-if="comprehensiveData?.alerts?.length > 0" class="alerts-panel">
          <h4>🚨 风险预警 ({{ comprehensiveData.alerts.length }})</h4>
          <div class="alerts-list">
            <div
              v-for="(alert, idx) in comprehensiveData.alerts"
              :key="idx"
              :class="['alert-item', alert.level]"
            >
              <div class="alert-header">
                <span class="alert-title">{{ alert.title }}</span>
                <span :class="['alert-level', alert.level]">{{ getAlertLevelText(alert.level) }}</span>
              </div>
              <p class="alert-message">{{ alert.message }}</p>
              <p class="alert-suggestion">💡 {{ alert.suggestion }}</p>
            </div>
          </div>
        </div>
        <div v-else class="no-alerts">
          <span>✅ 暂无风险预警</span>
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
            <span class="overview-label">风险评分</span>
            <span class="risk-score-value" :class="getRiskScoreClass(stockRisk.risk_score)">
              {{ stockRisk.risk_score || comprehensiveData?.risk_score || 0 }}分
            </span>
          </div>
          <div class="overview-item">
            <span class="overview-label">接口成功率</span>
            <span class="interface-rate">{{ getInterfaceSuccessRate() }}</span>
          </div>
          <div class="overview-item">
            <span class="overview-label">最后更新</span>
            <span>{{ formatTime(selectedStock?.lastUpdate) }}</span>
          </div>
        </div>

        <!-- 标签页切换 - 7个标签 -->
        <div class="detail-tabs">
          <button
            :class="['detail-tab', { active: detailTab === 'interface' }]"
            @click="detailTab = 'interface'"
          >
            📊 接口状态
          </button>
          <button
            :class="['detail-tab', { active: detailTab === 'basic' }]"
            @click="detailTab = 'basic'"
          >
            🏢 基础信息
          </button>
          <button
            :class="['detail-tab', { active: detailTab === 'market' }]"
            @click="detailTab = 'market'"
          >
            📈 行情数据
          </button>
          <button
            :class="['detail-tab', { active: detailTab === 'financial' }]"
            @click="detailTab = 'financial'"
          >
            💰 财务数据
          </button>
          <button
            :class="['detail-tab', { active: detailTab === 'capital' }]"
            @click="detailTab = 'capital'"
          >
            💹 资金流向
          </button>
          <button
            :class="['detail-tab', { active: detailTab === 'risk' }]"
            @click="detailTab = 'risk'"
          >
            ⚠️ 风险监控
          </button>
          <button
            :class="['detail-tab', { active: detailTab === 'news' }]"
            @click="detailTab = 'news'"
          >
            📰 新闻舆情 <span v-if="stockNews.length" class="tab-badge">{{ stockNews.length }}</span>
          </button>
        </div>

        <!-- 0. 接口状态TAB -->
        <div v-if="detailTab === 'interface'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="comprehensiveData?.interface_status" class="interface-status-panels">
            <div
              v-for="(category, categoryKey) in comprehensiveData.interface_status"
              :key="categoryKey"
              class="interface-category"
            >
              <div class="category-header">
                <span class="category-icon">{{ category.icon }}</span>
                <span class="category-name">{{ category.name }}</span>
                <span class="category-stats">
                  <span class="stat-success">✅ {{ category.success }}</span>
                  <span class="stat-failed">❌ {{ category.failed }}</span>
                  <span class="stat-nodata">⚪ {{ category.no_data }}</span>
                </span>
              </div>
              <div class="interface-list">
                <div
                  v-for="(info, interfaceName) in category.interfaces"
                  :key="interfaceName"
                  :class="['interface-item', info.status]"
                >
                  <span class="interface-name">{{ getInterfaceName(interfaceName) }}</span>
                  <span class="interface-status-label">{{ info.status_label }}</span>
                  <span v-if="info.count > 0" class="interface-count">{{ info.count }}条</span>
                  <span v-if="info.message" class="interface-message">{{ info.message }}</span>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <p>暂无数据</p>
            <p class="hint">请点击"立即更新"按钮获取数据</p>
          </div>
        </div>

        <!-- 1. 基础信息TAB -->
        <div v-if="detailTab === 'basic'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="comprehensiveData" class="comprehensive-panels">
            <!-- 公司信息 -->
            <div v-if="comprehensiveData.company_info?.status === 'success'" class="data-panel">
              <h4>🏢 公司基本信息</h4>
              <div class="info-grid-2col">
                <div><span class="label">董事长：</span>{{ comprehensiveData.company_info.data?.chairman || '-' }}</div>
                <div><span class="label">总经理：</span>{{ comprehensiveData.company_info.data?.manager || '-' }}</div>
                <div><span class="label">注册资本：</span>{{ comprehensiveData.company_info.data?.reg_capital || '-' }}万</div>
                <div><span class="label">员工数：</span>{{ comprehensiveData.company_info.data?.employees || '-' }}人</div>
                <div><span class="label">所在省份：</span>{{ comprehensiveData.company_info.data?.province || '-' }}</div>
                <div><span class="label">所在城市：</span>{{ comprehensiveData.company_info.data?.city || '-' }}</div>
              </div>
              <div v-if="comprehensiveData.company_info.data?.introduction" class="company-intro">
                <span class="label">公司简介：</span>
                <p>{{ comprehensiveData.company_info.data.introduction }}</p>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.company_info?.message || '无公司信息' }}</div>

            <!-- 管理层 -->
            <div v-if="comprehensiveData.managers?.status === 'success'" class="data-panel">
              <h4>👔 管理层</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>姓名</th><th>职务</th><th>学历</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in safeArray(comprehensiveData.managers, 10)" :key="idx">
                      <td>{{ item.name }}</td>
                      <td>{{ item.title }}</td>
                      <td>{{ item.edu || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.managers?.message || '无管理层信息' }}</div>

            <!-- 主营业务 -->
            <div v-if="comprehensiveData.main_business?.status === 'success'" class="data-panel">
              <h4>📋 主营业务构成</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>业务名称</th><th>营收占比</th><th>毛利率</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in safeArray(comprehensiveData.main_business, 10)" :key="idx">
                      <td>{{ item.bz_item }}</td>
                      <td>{{ (item.bz_sales_ratio * 100).toFixed(2) }}%</td>
                      <td>{{ (item.bz_profit_ratio * 100).toFixed(2) }}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.main_business?.message || '无主营业务数据' }}</div>
          </div>

          <div v-else class="empty-state"><p>暂无基础信息</p></div>
        </div>

        <!-- 2. 行情数据TAB -->
        <div v-if="detailTab === 'market'" class="detail-content">
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
                  <span class="value price-lg">{{ comprehensiveData.realtime.data?.price || '-' }}</span>
                </div>
                <div class="info-card">
                  <span class="label">涨跌幅</span>
                  <span :class="['value', (comprehensiveData.realtime.data?.pct_change || 0) >= 0 ? 'up' : 'down']">
                    {{ comprehensiveData.realtime.data?.pct_change || 0 }}%
                  </span>
                </div>
                <div class="info-card">
                  <span class="label">成交量</span>
                  <span class="value">{{ formatMoney(comprehensiveData.realtime.data?.volume) }}</span>
                </div>
                <div class="info-card">
                  <span class="label">成交额</span>
                  <span class="value">{{ formatMoney(comprehensiveData.realtime.data?.amount) }}</span>
                </div>
                <div class="info-card">
                  <span class="label">最高</span>
                  <span class="value">{{ comprehensiveData.realtime.data?.high || '-' }}</span>
                </div>
                <div class="info-card">
                  <span class="label">最低</span>
                  <span class="value">{{ comprehensiveData.realtime.data?.low || '-' }}</span>
                </div>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.realtime?.message || '无实时行情' }}</div>

            <!-- 涨跌停记录 -->
            <div v-if="comprehensiveData.limit_list?.status === 'success'" class="data-panel">
              <h4>🔴 涨跌停记录</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>日期</th><th>类型</th><th>涨跌幅</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in safeArray(comprehensiveData.limit_list, 10)" :key="idx">
                      <td>{{ item.trade_date }}</td>
                      <td>{{ item.limit }}</td>
                      <td :class="item.pct_change >= 0 ? 'up' : 'down'">{{ item.pct_change }}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.limit_list?.message || '近30天无涨跌停' }}</div>

            <!-- 龙虎榜 -->
            <div v-if="comprehensiveData.dragon_tiger?.status === 'success'" class="data-panel">
              <h4>🐉 龙虎榜</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>日期</th><th>上榜原因</th><th>净买入</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in (comprehensiveData.dragon_tiger.records || []).slice(0, 10)" :key="idx">
                      <td>{{ item.date }}</td>
                      <td>{{ item.reason }}</td>
                      <td :class="item.net >= 0 ? 'up' : 'down'">{{ formatMoney(item.net) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.dragon_tiger?.message || '近30天无龙虎榜' }}</div>

            <!-- 大宗交易 -->
            <div v-if="comprehensiveData.block_trade?.status === 'success'" class="data-panel">
              <h4>💼 大宗交易</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>日期</th><th>成交价</th><th>成交量</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in safeArray(comprehensiveData.block_trade, 10)" :key="idx">
                      <td>{{ item['交易日期'] || item.trade_date }}</td>
                      <td>{{ item['成交价'] || item.price }}</td>
                      <td>{{ item['成交量'] || item.vol }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.block_trade?.message || '近期无大宗交易' }}</div>
          </div>

          <div v-else class="empty-state"><p>暂无行情数据</p></div>
        </div>

        <!-- 3. 财务数据TAB -->
        <div v-if="detailTab === 'financial'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="comprehensiveData" class="comprehensive-panels">
            <!-- 利润表 -->
            <div v-if="comprehensiveData.financial?.income?.length" class="data-panel">
              <h4>💰 利润表</h4>
              <div class="financial-table">
                <table>
                  <thead>
                    <tr>
                      <th>报告期</th>
                      <th>营业收入</th>
                      <th>净利润</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in comprehensiveData.financial.income" :key="idx">
                      <td>{{ item.period || item.end_date }}</td>
                      <td>{{ formatMoney(item.total_revenue || item.revenue) }}</td>
                      <td>{{ formatMoney(item.net_profit || item.n_income) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">无利润表数据</div>

            <!-- 业绩预告 -->
            <div v-if="comprehensiveData.forecast?.status === 'success'" class="data-panel">
              <h4>📅 业绩预告</h4>
              <div class="forecast-cards">
                <div v-for="(item, idx) in [...(comprehensiveData.forecast.forecast || [])].slice(0, 3)" :key="idx" class="forecast-card">
                  <div class="forecast-period">{{ item.period || item.end_date }}</div>
                  <div class="forecast-type">{{ item.type }}</div>
                  <p class="forecast-text">{{ item.summary || '预计净利润变动' + item.profit_min + '% ~ ' + item.profit_max + '%' }}</p>
                </div>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.forecast?.message || '无业绩预告' }}</div>

            <!-- 审计意见 -->
            <div v-if="comprehensiveData.audit?.status === 'success'" class="data-panel">
              <h4>📋 审计意见</h4>
              <div class="audit-info">
                <div class="audit-item">
                  <span class="label">报告期：</span>
                  <span>{{ comprehensiveData.audit.period }}</span>
                </div>
                <div class="audit-item">
                  <span class="label">审计机构：</span>
                  <span>{{ comprehensiveData.audit.agency }}</span>
                </div>
                <div class="audit-item">
                  <span class="label">审计意见：</span>
                  <span :class="comprehensiveData.audit.is_standard ? 'safe' : 'danger'">
                    {{ comprehensiveData.audit.opinion }}
                  </span>
                </div>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.audit?.message || '无审计意见' }}</div>

            <!-- 分红送股 -->
            <div v-if="comprehensiveData.dividend?.status === 'success'" class="data-panel">
              <h4>🎁 分红送股</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>年度</th><th>每10股派息</th><th>登记日</th><th>除权日</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in (comprehensiveData.dividend.records || []).slice(0, 5)" :key="idx">
                      <td>{{ item.year }}</td>
                      <td>{{ item.cash_div }}元</td>
                      <td>{{ item.record_date || '-' }}</td>
                      <td>{{ item.ex_date || '-' }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.dividend?.message || '无分红数据' }}</div>
          </div>

          <div v-else class="empty-state"><p>无财务数据</p></div>
        </div>

        <!-- 4. 资金流向TAB -->
        <div v-if="detailTab === 'capital'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="comprehensiveData" class="comprehensive-panels">
            <!-- 融资融券趋势图 -->
            <div v-if="comprehensiveData.margin?.status === 'success'" class="data-panel chart-panel">
              <h4>📊 融资融券趋势</h4>
              <div ref="marginChartRef" class="chart-container"></div>
            </div>

            <!-- 沪深港通持股趋势图 -->
            <div v-if="comprehensiveData.hsgt_holding?.status === 'success'" class="data-panel chart-panel">
              <h4>🌏 沪深港通持股趋势</h4>
              <div ref="capitalFlowRef" class="chart-container"></div>
            </div>

            <!-- 融资融券 -->
            <div v-if="comprehensiveData.margin?.status === 'success'" class="data-panel">
              <h4>📊 融资融券</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>日期</th><th>融资余额</th><th>融券余额</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in safeArray(comprehensiveData.margin, 10)" :key="idx">
                      <td>{{ item.trade_date }}</td>
                      <td>{{ formatMoney(item.rzye) }}</td>
                      <td>{{ formatMoney(item.rqye) }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.margin?.message || '无融资融券数据' }}</div>

            <!-- 沪深港通持股 -->
            <div v-if="comprehensiveData.hsgt_holding?.status === 'success'" class="data-panel">
              <h4>🌏 沪深港通持股</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>日期</th><th>持股数量</th><th>持股市值</th><th>占流通股比</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in safeArray(comprehensiveData.hsgt_holding, 10)" :key="idx">
                      <td>{{ item.trade_date }}</td>
                      <td>{{ formatMoney(item.hold_vol) }}</td>
                      <td>{{ formatMoney(item.hold_amount) }}</td>
                      <td>{{ item.hold_ratio }}%</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.hsgt_holding?.message || '无沪深港通数据' }}</div>

            <!-- 股东增减持 -->
            <div v-if="comprehensiveData.holder_trade?.status === 'success'" class="data-panel">
              <h4>📄 股东增减持</h4>
              <div class="mini-table">
                <table>
                  <thead>
                    <tr><th>公告日</th><th>股东名称</th><th>变动数量</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(item, idx) in (comprehensiveData.holder_trade.records || []).slice(0, 10)" :key="idx">
                      <td>{{ item.date || item.ann_date }}</td>
                      <td>{{ item.holder }}</td>
                      <td :class="(item.volume || 0) >= 0 ? 'up' : 'down'">
                        {{ formatMoney(item.volume) }}股
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.holder_trade?.message || '无股东增减持数据' }}</div>

            <!-- 股权质押 -->
            <div v-if="comprehensiveData.pledge?.status === 'success'" class="data-panel">
              <h4>🔒 股权质押统计</h4>
              <div class="info-grid-3col">
                <div class="info-card">
                  <span class="label">质押比例</span>
                  <span :class="['value', (comprehensiveData.pledge.pledge_ratio || 0) > 50 ? 'danger' : 'safe']">
                    {{ comprehensiveData.pledge.pledge_ratio || 0 }}%
                  </span>
                </div>
                <div class="info-card">
                  <span class="label">质押笔数</span>
                  <span class="value">{{ comprehensiveData.pledge.pledge_count || 0 }}</span>
                </div>
                <div class="info-card">
                  <span class="label">统计日期</span>
                  <span class="value">{{ comprehensiveData.pledge.end_date || '-' }}</span>
                </div>
              </div>
            </div>
            <div v-else class="empty-hint">{{ comprehensiveData.pledge?.message || '无股权质押数据' }}</div>
          </div>

          <div v-else class="empty-state"><p>无资金流向数据</p></div>
        </div>

        <!-- 5. 风险监控TAB -->
        <div v-if="detailTab === 'risk'" class="detail-content">
          <div v-if="loadingComprehensive" class="loading-state">
            <div class="spinner"></div>
            <p>加载中...</p>
          </div>

          <div v-else-if="comprehensiveData || stockRisk.risk_score" class="risk-full-panel">
            <!-- 风险概览区域：雷达图 + 风险卡片并排 -->
            <div class="risk-overview-section">
              <!-- 风险雷达图 -->
              <div v-if="comprehensiveData" class="radar-container">
                <h4>📡 风险雷达图</h4>
                <div ref="riskRadarRef" class="radar-chart-box"></div>
              </div>

              <!-- 风险卡片网格 - 放在雷达图右侧 -->
              <div v-if="comprehensiveData" class="risk-cards-side">
                <!-- 第一行：ST状态 + 停复牌 -->
                <div class="risk-card" :class="comprehensiveData.st_status?.is_st ? 'danger' : 'safe'">
                  <h4>⚠️ ST状态</h4>
                  <div class="risk-status-value" :class="comprehensiveData.st_status?.is_st ? 'danger' : 'safe'">
                    {{ comprehensiveData.st_status?.is_st ? '⚠️ ST股票' : '✅ 正常' }}
                  </div>
                  <p class="risk-message">{{ comprehensiveData.st_status?.message || '正常状态' }}</p>
                </div>

                <div class="risk-card" :class="comprehensiveData.suspend?.status === 'has_suspend' ? 'warning' : 'safe'">
                  <h4>🚫 停复牌</h4>
                  <div class="risk-status-value" :class="comprehensiveData.suspend?.status === 'has_suspend' ? 'warning' : 'safe'">
                    {{ comprehensiveData.suspend?.status === 'has_suspend' ? '⚠️ 有停牌记录' : '✅ 正常交易' }}
                  </div>
                  <p class="risk-message">{{ comprehensiveData.suspend?.message || '正常交易' }}</p>
                </div>

                <!-- 第二行：股权质押 + 限售解禁 -->
                <div class="risk-card" :class="(comprehensiveData.pledge?.pledge_ratio || 0) > 50 ? 'danger' : 'safe'">
                  <h4>🔒 股权质押</h4>
                  <div class="pledge-value" :class="(comprehensiveData.pledge?.pledge_ratio || 0) > 50 ? 'danger' : ''">
                    {{ comprehensiveData.pledge?.pledge_ratio || 0 }}%
                  </div>
                  <p class="risk-message">
                    {{ (comprehensiveData.pledge?.pledge_ratio || 0) > 70 ? '⚠️ 质押比例极高，存在爆仓风险' :
                       (comprehensiveData.pledge?.pledge_ratio || 0) > 50 ? '⚠️ 质押比例较高' : '✅ 质押比例正常' }}
                  </p>
                </div>

                <div class="risk-card" :class="comprehensiveData.restricted?.status === 'success' ? 'warning' : 'safe'">
                  <h4>📅 限售解禁</h4>
                  <div class="risk-status-value">
                    {{ comprehensiveData.restricted?.count || 0 }} 批
                  </div>
                  <p class="risk-message">{{ comprehensiveData.restricted?.message || '无近期解禁' }}</p>
                </div>
              </div>
            </div>

            <!-- 风险评分（如果有） -->
            <div v-if="stockRisk.risk_score" class="risk-score-section">
              <div class="risk-score-container">
                <h4>📊 综合风险评分</h4>
                <div class="risk-score-display">
                  <div class="score-circle" :class="stockRisk.risk_level">
                    <span class="score-number">{{ stockRisk.risk_score || 0 }}</span>
                    <span class="score-unit">分</span>
                  </div>
                  <div :class="['risk-level-label', stockRisk.risk_level]">
                    {{ getRiskText(stockRisk.risk_level) }}
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div v-else class="empty-state">
            <p>暂无风险数据</p>
            <p class="hint">请点击"立即更新"按钮获取数据</p>
          </div>
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
                <h4
                  @click="openNewsLink(news)"
                  :class="{ 'clickable-title': news.url && news.url.length > 0 }"
                  :title="news.url && news.url.length > 0 ? '点击打开原文链接' : '暂无链接'"
                  v-html="highlightKeywords(news.title, selectedStock?.code, selectedStock?.name)"
                ></h4>
                <div class="news-meta">
                  <span class="news-type-tag">{{ getReportTypeLabel(news.report_type) }}</span>
                  <span class="news-time">{{ news.pub_time }}</span>
                  <a v-if="news.url && news.url.length > 0"
                     :href="news.url"
                     target="_blank"
                     class="news-link-btn"
                     @click.stop
                  >🔗 原文</a>
                </div>
              </div>

              <!-- 新闻内容 - 支持展开/收起 -->
              <div class="news-content-wrapper">
                <p
                  class="news-content"
                  :class="{ 'expanded': expandedNews[index] }"
                  v-html="highlightKeywords(news.content, selectedStock?.code, selectedStock?.name)"
                ></p>
                <button
                  v-if="news.content && news.content.length > 150"
                  class="expand-btn"
                  @click="toggleNewsExpand(index)"
                >
                  {{ expandedNews[index] ? '收起 ▲' : '展开全文 ▼' }}
                </button>
              </div>
              
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

    <!-- 全局加载遮罩 -->
    <div class="loading-overlay" v-if="isRefreshing">
      <div class="loading-spinner"></div>
      <p class="loading-text">{{ refreshingText }}</p>
      <div class="loading-progress" v-if="refreshingProgress > 0">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: refreshingProgress + '%' }"></div>
        </div>
        <span class="progress-text">{{ refreshingProgress }}%</span>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'
import StockSearchInput from '@/components/StockSearchInput.vue'
import API_BASE_URL, { WS_BASE_URL } from '@/config/api.js'

export default {
  name: 'DataFlowView',
  components: {
    StockSearchInput
  },
  setup() {
    const API_BASE = `${API_BASE_URL}/api`
    
    // 状态数据
    const isRefreshing = ref(false)
    const refreshingText = ref('数据刷新中...')
    const refreshingProgress = ref(0)
    const showAddMonitor = ref(false)
    const showStockDetails = ref(false)
    const showNotificationSettings = ref(false)  // 通知设置弹窗
    const showInterfaceTest = ref(false)  // 接口测试弹窗
    const currentFilter = ref('全部')
    const newsSource = ref('all')
    const detailTab = ref('interface')  // interface, basic, market, financial, capital, risk, news
    const newsTypeFilter = ref('all')  // all, financial, announcement, news, policy, research

    // 通知相关状态
    const notificationChannels = ref({})
    const configGuide = ref({})
    const expandedGuide = ref(null)
    const testEmail = ref('')
    const testingChannel = ref(null)
    const sendingTestEmail = ref(false)
    const savingConfig = ref(false)
    const notificationConfig = ref({
      SMTP_HOST: '',
      SMTP_PORT: 465,
      SMTP_USER: '',
      SMTP_PASSWORD: '',
      SMTP_FROM: '',
      SMTP_USE_SSL: true,
      WECHAT_WEBHOOK_URL: '',
      DINGTALK_WEBHOOK_URL: '',
      DINGTALK_SECRET: '',
      SERVERCHAN_KEY: '',
      BARK_KEY: '',
      BARK_SERVER: ''
    })
    
    // 综合数据
    const loadingComprehensive = ref(false)
    const comprehensiveData = ref(null)

    // 分类加载状态（用于流式渲染）
    const categoryLoadingStates = ref({
      basic_info: { loading: false, loaded: false, data: null },
      market_data: { loading: false, loaded: false, data: null },
      financial_data: { loading: false, loaded: false, data: null },
      capital_flow: { loading: false, loaded: false, data: null },
      risk_monitor: { loading: false, loaded: false, data: null },
      news_sentiment: { loading: false, loaded: false, data: null }
    })

    // 请求取消控制器 - 用于取消正在进行的请求
    let abortController = null
    let sseEventSource = null  // SSE 连接
    let websocket = null  // WebSocket 连接

    // 正在请求的股票代码（防重机制）
    const pendingRequests = ref(new Set())

    // 加载状态细分
    const loadingStates = ref({
      comprehensive: false,
      news: false,
      risk: false
    })

    // 股票数据缓存 - key为股票代码，value为完整数据
    const stockDataCache = ref({})

    const monitoredStocks = ref([])
    const dataSources = ref([])
    const newsList = ref([])
    const sentimentFilter = ref('non_neutral')  // 默认显示有情绪的新闻
    const sentimentStats = ref({ positive: 0, negative: 0, neutral: 0 })
    const selectedStock = ref(null)
    const stockNews = ref([])
    const stockSentiment = ref({})
    const stockRisk = ref({})
    const toasts = ref([])  // Toast通知列表
    const expandedNews = ref({})  // 新闻展开状态

    // 接口测试相关状态
    const interfaceTestResults = ref({})  // 测试结果
    const interfaceTestRunning = ref(false)  // 是否正在测试
    const interfaceTestProgress = ref(0)  // 测试进度
    const interfaceTestTotal = ref(0)  // 总接口数
    const interfaceTestSuccess = ref(0)  // 成功数
    const interfaceTestFail = ref(0)  // 失败数
    const expandedSources = ref({})  // 数据源展开状态
    const dataSourcesCollapsed = ref(true)  // 数据源状态区域默认折叠
    let interfaceTestEventSource = null  // SSE 连接

    // 图表相关
    const marginChartRef = ref(null)  // 融资融券图表容器
    const riskRadarRef = ref(null)    // 风险雷达图容器
    const capitalFlowRef = ref(null)  // 资金流向图表容器
    let marginChart = null            // 融资融券图表实例
    let riskRadarChart = null         // 风险雷达图实例
    let capitalFlowChart = null       // 资金流向图表实例

    // 股票搜索相关
    const selectedStockName = ref('')

    const newMonitor = reactive({
      code: '',
      frequency: '1h',
      retention_days: 7,  // 新增：保存周期
      items: {
        news: true,
        risk: true,
        sentiment: true,
        suspend: false,
        realtime: true,     // 新增：实时行情
        financial: false,   // 新增：财务数据
        capital: false      // 新增：资金流
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
    
    // 每日统计数据
    const dailyStats = ref({
      monitoredStocks: 0,
      todayNews: 0,
      riskAlerts: 0,
      analysisTasks: 0,
      apiCalls: {}
    })

    // 加载每日统计
    const loadDailyStats = async () => {
      try {
        const response = await axios.get(`${API_BASE}/dataflow/daily-stats`)
        if (response.data.success) {
          dailyStats.value = response.data.stats
        }
      } catch (error) {
        console.error('加载每日统计失败:', error)
      }
    }

    // 加载通知渠道状态
    const loadNotificationChannels = async () => {
      try {
        const response = await axios.get(`${API_BASE}/notification/channels`)
        if (response.data.success) {
          notificationChannels.value = response.data.channels
        }
      } catch (error) {
        console.error('加载通知渠道失败:', error)
      }
    }

    // 加载配置指南
    const loadConfigGuide = async () => {
      try {
        const response = await axios.get(`${API_BASE}/notification/config-guide`)
        if (response.data.success) {
          configGuide.value = response.data.guide
        }
      } catch (error) {
        console.error('加载配置指南失败:', error)
      }
    }

    // 切换配置指南展开状态
    const toggleGuide = (key) => {
      expandedGuide.value = expandedGuide.value === key ? null : key
    }

    // 测试通知渠道
    const testNotificationChannel = async (channel) => {
      testingChannel.value = channel
      try {
        let response
        if (channel === 'email') {
          if (!testEmail.value) {
            showToast('请先输入测试邮箱地址', 'warning')
            testingChannel.value = null
            return
          }
          response = await axios.post(`${API_BASE}/notification/test/email`, {
            to_email: testEmail.value
          })
        } else {
          response = await axios.post(`${API_BASE}/notification/test/${channel}`)
        }

        if (response.data.success) {
          showToast(`${notificationChannels.value[channel]?.name || channel} 测试成功`, 'success')
        } else {
          showToast(`测试失败: ${response.data.message || '未知错误'}`, 'error')
        }
      } catch (error) {
        showToast(`测试失败: ${error.response?.data?.detail || error.message}`, 'error')
      } finally {
        testingChannel.value = null
      }
    }

    // 发送测试邮件
    const sendTestEmail = async () => {
      if (!testEmail.value) {
        showToast('请输入邮箱地址', 'warning')
        return
      }
      sendingTestEmail.value = true
      try {
        const response = await axios.post(`${API_BASE}/notification/test/email`, {
          to_email: testEmail.value
        })
        if (response.data.success) {
          showToast('测试邮件发送成功，请检查收件箱', 'success')
        } else {
          showToast(`发送失败: ${response.data.message}`, 'error')
        }
      } catch (error) {
        showToast(`发送失败: ${error.response?.data?.detail || error.message}`, 'error')
      } finally {
        sendingTestEmail.value = false
      }
    }

    // 加载通知配置
    const loadNotificationConfig = async () => {
      try {
        const response = await axios.get(`${API_BASE}/notification/config`)
        if (response.data.success) {
          const config = response.data.config
          // 更新配置（保留密码字段的脱敏值）
          notificationConfig.value = {
            SMTP_HOST: config.SMTP_HOST || '',
            SMTP_PORT: config.SMTP_PORT || 465,
            SMTP_USER: config.SMTP_USER || '',
            SMTP_PASSWORD: config.SMTP_PASSWORD || '',
            SMTP_FROM: config.SMTP_FROM || '',
            SMTP_USE_SSL: config.SMTP_USE_SSL !== false,
            WECHAT_WEBHOOK_URL: config.WECHAT_WEBHOOK_URL || '',
            DINGTALK_WEBHOOK_URL: config.DINGTALK_WEBHOOK_URL || '',
            DINGTALK_SECRET: config.DINGTALK_SECRET || '',
            SERVERCHAN_KEY: config.SERVERCHAN_KEY || '',
            BARK_KEY: config.BARK_KEY || '',
            BARK_SERVER: config.BARK_SERVER || ''
          }
          console.log('通知配置已加载')
        }
      } catch (error) {
        console.error('加载通知配置失败:', error)
      }
    }

    // 保存通知配置
    const saveNotificationConfig = async () => {
      savingConfig.value = true
      try {
        // 构建要保存的配置（过滤掉空值和脱敏的密码）
        const configToSave = {}
        const config = notificationConfig.value

        // 邮件配置
        if (config.SMTP_HOST) configToSave.SMTP_HOST = config.SMTP_HOST
        if (config.SMTP_PORT) configToSave.SMTP_PORT = config.SMTP_PORT
        if (config.SMTP_USER) configToSave.SMTP_USER = config.SMTP_USER
        if (config.SMTP_PASSWORD && config.SMTP_PASSWORD !== '******') {
          configToSave.SMTP_PASSWORD = config.SMTP_PASSWORD
        }
        if (config.SMTP_FROM) configToSave.SMTP_FROM = config.SMTP_FROM
        configToSave.SMTP_USE_SSL = config.SMTP_USE_SSL

        // 企业微信配置
        if (config.WECHAT_WEBHOOK_URL && !config.WECHAT_WEBHOOK_URL.includes('...')) {
          configToSave.WECHAT_WEBHOOK_URL = config.WECHAT_WEBHOOK_URL
        }

        // 钉钉配置
        if (config.DINGTALK_WEBHOOK_URL && !config.DINGTALK_WEBHOOK_URL.includes('...')) {
          configToSave.DINGTALK_WEBHOOK_URL = config.DINGTALK_WEBHOOK_URL
        }
        if (config.DINGTALK_SECRET && config.DINGTALK_SECRET !== '******') {
          configToSave.DINGTALK_SECRET = config.DINGTALK_SECRET
        }

        // Server酱配置
        if (config.SERVERCHAN_KEY && config.SERVERCHAN_KEY !== '******') {
          configToSave.SERVERCHAN_KEY = config.SERVERCHAN_KEY
        }

        // Bark配置
        if (config.BARK_KEY && config.BARK_KEY !== '******') {
          configToSave.BARK_KEY = config.BARK_KEY
        }
        if (config.BARK_SERVER) configToSave.BARK_SERVER = config.BARK_SERVER

        const response = await axios.post(`${API_BASE}/notification/config`, configToSave)
        if (response.data.success) {
          showToast('配置保存成功', 'success')
          // 重新加载通知渠道状态
          await loadNotificationChannels()
          // 重新加载配置
          await loadNotificationConfig()
        } else {
          showToast(`保存失败: ${response.data.message}`, 'error')
        }
      } catch (error) {
        showToast(`保存失败: ${error.response?.data?.detail || error.message}`, 'error')
      } finally {
        savingConfig.value = false
      }
    }

    // 计算属性（使用持久化的统计数据）
    const todayNewsCount = computed(() => dailyStats.value.todayNews || newsList.value.length)
    const riskAlertCount = computed(() => dailyStats.value.riskAlerts || 0)
    const analysisTaskCount = computed(() => dailyStats.value.analysisTasks || 0)

    // 根据情绪筛选新闻列表
    const filteredNewsList = computed(() => {
      let filtered = newsList.value
      // 按情绪筛选
      if (sentimentFilter.value === 'non_neutral') {
        filtered = filtered.filter(n => n.sentiment !== 'neutral')
      } else if (sentimentFilter.value === 'positive') {
        filtered = filtered.filter(n => n.sentiment === 'positive')
      } else if (sentimentFilter.value === 'negative') {
        filtered = filtered.filter(n => n.sentiment === 'negative')
      }
      // 按来源筛选
      if (newsSource.value && newsSource.value !== 'all') {
        filtered = filtered.filter(n => n.source === newsSource.value)
      }
      return filtered
    })

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

    // 接口测试成功率计算
    const interfaceTestSuccessRate = computed(() => {
      if (interfaceTestTotal.value === 0) return 0
      return Math.round((interfaceTestSuccess.value / interfaceTestTotal.value) * 100)
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
    
    // 新闻加载状态
    const newsLoading = ref(false)
    let newsPollingTimer = null

    const loadNews = async (isPolling = false) => {
      // 如果不是轮询调用，设置加载状态
      if (!isPolling) {
        newsLoading.value = true
      }

      try {
        // 获取所有新闻（不在API层筛选，在前端筛选以便显示统计）
        const response = await axios.get(`${API_BASE}/dataflow/news`, { params: { limit: 100 } })
        if (response.data.success) {
          // 检查是否正在后台加载
          if (response.data.loading) {
            // 后台正在加载，3秒后重试
            console.log('📰 新闻正在后台加载中，3秒后重试...')
            if (!newsPollingTimer) {
              newsPollingTimer = setTimeout(() => {
                newsPollingTimer = null
                loadNews(true)  // 轮询调用
              }, 3000)
            }
          } else {
            // 数据已就绪
            newsLoading.value = false
            newsList.value = response.data.news || []
            // 更新情绪统计
            if (response.data.sentiment_stats) {
              sentimentStats.value = response.data.sentiment_stats
            }
            console.log(`📰 新闻加载完成: ${newsList.value.length}条`)
          }
        }
      } catch (error) {
        console.error('加载新闻失败:', error)
        newsLoading.value = false
      }
    }
    
    // 更新刷新进度
    const updateRefreshProgress = (text, progress) => {
      refreshingText.value = text
      refreshingProgress.value = progress
    }

    // 刷新数据（不包含数据源状态，数据源状态只在页面加载时检测一次）
    const refreshAllData = async () => {
      isRefreshing.value = true
      refreshingProgress.value = 0
      try {
        // 步骤1: 加载监控股票
        updateRefreshProgress('正在加载监控股票...', 20)
        await loadMonitoredStocks()
        
        // 步骤2: 加载新闻
        updateRefreshProgress('正在加载新闻数据...', 50)
        await loadNews()
        
        // 步骤3: 加载统计数据
        updateRefreshProgress('正在加载统计数据...', 80)
        await loadDailyStats()
        
        updateRefreshProgress('数据刷新完成', 100)
      } finally {
        setTimeout(() => {
          isRefreshing.value = false
          refreshingProgress.value = 0
        }, 300)
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

    // ========== 接口测试相关方法 ==========

    // 打开接口测试弹窗
    const openInterfaceTest = () => {
      showInterfaceTest.value = true
      // 自动开始测试
      startInterfaceTest()
    }

    // 切换数据源展开状态
    const toggleSourceExpand = (sourceKey) => {
      expandedSources.value[sourceKey] = !expandedSources.value[sourceKey]
    }

    // 开始接口测试（使用 SSE 流式获取结果）
    const startInterfaceTest = () => {
      // 关闭之前的连接
      if (interfaceTestEventSource) {
        interfaceTestEventSource.close()
        interfaceTestEventSource = null
      }

      // 重置状态
      interfaceTestRunning.value = true
      interfaceTestProgress.value = 0
      interfaceTestTotal.value = 0
      interfaceTestSuccess.value = 0
      interfaceTestFail.value = 0
      interfaceTestResults.value = {}

      const url = `${API_BASE}/dataflow/interfaces/test/stream`
      console.log('🔌 开始接口测试:', url)

      const eventSource = new EventSource(url)
      interfaceTestEventSource = eventSource

      eventSource.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          console.log('📨 接口测试消息:', data.type)

          switch (data.type) {
            case 'start':
              interfaceTestTotal.value = data.total
              // 初始化数据源结构
              data.sources.forEach(sourceKey => {
                expandedSources.value[sourceKey] = false  // 默认折叠
              })
              break

            case 'source_start':
              // 初始化数据源
              interfaceTestResults.value[data.source] = {
                name: data.name,
                icon: data.icon,
                interfaces: [],
                successCount: 0,
                failCount: 0,
                pendingCount: data.count
              }
              break

            case 'test_start':
              // 添加正在测试的接口
              if (interfaceTestResults.value[data.source]) {
                interfaceTestResults.value[data.source].interfaces.push({
                  id: data.interface_id,
                  name: data.name,
                  category: data.category,
                  status: 'testing',
                  elapsed: 0,
                  message: ''
                })
              }
              break

            case 'test_result':
              // 更新测试结果
              interfaceTestProgress.value = data.progress

              if (interfaceTestResults.value[data.source]) {
                const source = interfaceTestResults.value[data.source]
                const iface = source.interfaces.find(i => i.id === data.interface_id)

                if (iface) {
                  iface.status = data.status
                  iface.elapsed = data.elapsed
                  iface.message = data.message
                }

                // 更新统计
                source.pendingCount = Math.max(0, (source.pendingCount || 0) - 1)

                if (data.status === 'success') {
                  source.successCount = (source.successCount || 0) + 1
                  interfaceTestSuccess.value++
                } else if (data.status === 'error' || data.status === 'timeout') {
                  source.failCount = (source.failCount || 0) + 1
                  interfaceTestFail.value++
                }
              }
              break

            case 'source_complete':
              console.log(`✅ ${data.name} 测试完成`)
              break

            case 'complete':
              interfaceTestRunning.value = false
              eventSource.close()
              interfaceTestEventSource = null
              showToast(`接口测试完成: ${data.success}/${data.total} 成功 (${data.success_rate}%)`, 'success')
              break
          }
        } catch (e) {
          console.error('解析接口测试消息失败:', e)
        }
      }

      eventSource.onerror = (error) => {
        console.error('接口测试 SSE 错误:', error)
        interfaceTestRunning.value = false
        eventSource.close()
        interfaceTestEventSource = null
        showToast('接口测试连接失败', 'error')
      }

      // 超时处理（10分钟）
      setTimeout(() => {
        if (interfaceTestRunning.value && eventSource.readyState !== EventSource.CLOSED) {
          console.warn('⏰ 接口测试超时')
          eventSource.close()
          interfaceTestEventSource = null
          interfaceTestRunning.value = false
          showToast('接口测试超时', 'warning')
        }
      }, 600000)
    }

    // 股票选择回调
    const onStockSelect = (stock) => {
      if (stock) {
        // 设置完整的股票代码（带后缀）
        newMonitor.code = stock.code
        selectedStockName.value = `${stock.name} (${stock.code})`
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
          // 立即关闭模态框和重置表单
          showAddMonitor.value = false
          newMonitor.code = ''
          selectedStockName.value = ''  // 清空选中的股票名称
          showToast('添加成功，后台正在获取数据...', 'success')

          // 刷新监控列表（后端已在后台执行数据获取，前端不需要再调用）
          loadMonitoredStocks()
        } else {
          showToast('添加失败: ' + (response.data.message || '未知错误'), 'error')
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
      // 防重检查
      if (pendingRequests.value.has(stock.code)) {
        showToast('该股票正在更新中，请稍候...', 'warning')
        return
      }

      try {
        showToast('正在更新数据...', 'info')

        // 直接获取并缓存数据
        await fetchAndCacheStockData(stock.code)

        await loadMonitoredStocks()
        await loadNews()  // 刷新新闻列表
        showToast('数据更新完成', 'success')
      } catch (error) {
        console.error('更新失败:', error)
        showToast('更新失败: ' + error.message, 'error')
      }
    }
    
    const viewDetails = async (stock) => {
      console.log('查看详情:', stock)
      selectedStock.value = stock
      showStockDetails.value = true

      // 1. 先检查前端内存缓存
      const cachedData = stockDataCache.value[stock.code]
      if (cachedData && cachedData.comprehensive) {
        comprehensiveData.value = cachedData.comprehensive
        stockNews.value = cachedData.news || []
        stockSentiment.value = cachedData.sentiment || {}
        stockRisk.value = cachedData.risk || {}
        console.log(`📊 使用前端缓存: ${stock.code}`)
        return
      }

      // 2. 【数据库优先】从数据库获取数据
      try {
        console.log(`🔄 从数据库加载数据: ${stock.code}`)
        loadingComprehensive.value = true

        // 使用新的数据库优先接口
        const response = await axios.get(`${API_BASE}/dataflow/stock/comprehensive/${stock.code}/from-db`)

        if (response.data.success && response.data.has_data) {
          console.log(`✅ 从数据库加载成功`)

          // 使用数据库数据
          const dbData = response.data.data || {}
          comprehensiveData.value = dbData
          stockNews.value = dbData.news || []
          stockSentiment.value = {
            success: true,
            overall_score: dbData.overall_score || 50,
            sentiment_summary: dbData.sentiment_summary || '暂无'
          }
          stockRisk.value = dbData.risk || {}

          // 保存到前端缓存
          stockDataCache.value[stock.code] = {
            comprehensive: dbData,
            news: stockNews.value,
            sentiment: stockSentiment.value,
            risk: stockRisk.value,
            timestamp: response.data.loaded_at || new Date().toISOString(),
            from_database: true
          }
        } else {
          // 3. 数据库无数据，尝试后端缓存
          console.log(`ℹ️ 数据库无数据，尝试后端缓存: ${stock.code}`)
          const cacheResponse = await axios.get(`${API_BASE}/dataflow/stock/cached/${stock.code}`)

          if (cacheResponse.data.success && cacheResponse.data.has_data) {
            const cached = cacheResponse.data.comprehensive || {}
            comprehensiveData.value = cached
            stockNews.value = cacheResponse.data.news || cached.news || []
            stockSentiment.value = {
              success: true,
              overall_score: cached.overall_score || 50,
              sentiment_summary: cached.sentiment_summary || '暂无'
            }
            stockRisk.value = cached.risk || {}
          } else {
            // 4. 无任何数据，显示空状态
            console.log(`ℹ️ 无缓存数据: ${stock.code}，请点击刷新按钮获取`)
            comprehensiveData.value = null
            stockNews.value = []
            stockSentiment.value = {}
            stockRisk.value = {}
            showToast('暂无数据，请点击刷新按钮获取', 'info')
          }
        }
      } catch (error) {
        console.error('获取数据失败:', error)
        // 显示空状态
        comprehensiveData.value = null
        stockNews.value = []
        stockSentiment.value = {}
        stockRisk.value = {}
      } finally {
        loadingComprehensive.value = false
      }
    }
        
    // 刷新当前查看的股票数据
    const refreshCurrentStock = async () => {
      if (!selectedStock.value) return

      const code = selectedStock.value.code

      // 防重检查
      if (pendingRequests.value.has(code)) {
        showToast('正在刷新中，请稍候...', 'warning')
        return
      }

      try {
        showToast('正在刷新数据...', 'info')
        await fetchAndCacheStockData(code)
        showToast('数据刷新完成', 'success')
      } catch (error) {
        console.error('刷新失败:', error)
        showToast('刷新失败: ' + error.message, 'error')
      }
    }

    // 轮询任务状态
    // eslint-disable-next-line no-unused-vars
    const pollTaskStatus = async (taskId, code, maxAttempts = 120, interval = 3000) => {
      console.log(`🔄 开始轮询任务状态: ${taskId}`)

      for (let attempt = 0; attempt < maxAttempts; attempt++) {
        try {
          const response = await axios.get(`${API_BASE}/dataflow/task/${taskId}/status`)
          const result = response.data

          if (!result.success) {
            console.warn(`⚠️ 任务查询失败: ${result.error}`)
            return null
          }

          console.log(`📊 任务状态: ${result.status} (${result.progress || 0}%)`)

          if (result.status === 'completed') {
            console.log(`✅ 任务完成: ${taskId}`)
            return result.data || result
          }

          if (result.status === 'failed') {
            console.error(`❌ 任务失败: ${result.error}`)
            return null
          }

          // 继续等待
          await new Promise(resolve => setTimeout(resolve, interval))
        } catch (error) {
          console.error(`轮询出错: ${error.message}`)
          // 继续尝试
          await new Promise(resolve => setTimeout(resolve, interval))
        }
      }

      console.warn(`⏰ 任务轮询超时: ${taskId}`)
      return null
    }

    // 流式获取综合数据（SSE）
    const fetchComprehensiveDataStream = (code) => {
      return new Promise((resolve, reject) => {
        // 关闭之前的 SSE 连接
        if (sseEventSource) {
          sseEventSource.close()
          sseEventSource = null
        }

        // 重置分类状态
        Object.keys(categoryLoadingStates.value).forEach(key => {
          categoryLoadingStates.value[key] = { loading: false, loaded: false, data: null }
        })

        const url = `${API_BASE}/dataflow/stock/comprehensive/${code}/stream`
        console.log(`🌊 开始流式获取数据: ${url}`)

        const eventSource = new EventSource(url)
        sseEventSource = eventSource

        const allData = {}
        let completed = false

        eventSource.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data)
            console.log(`📨 SSE 消息:`, data.type, data.category || '')

            switch (data.type) {
              case 'start':
                showToast(`开始获取 ${code} 数据...`, 'info')
                break

              case 'progress':
                // 标记分类正在加载
                if (data.category && categoryLoadingStates.value[data.category]) {
                  categoryLoadingStates.value[data.category].loading = true
                }
                break

              case 'category':
                // 分类数据到达，立即更新
                if (data.category && data.data) {
                  categoryLoadingStates.value[data.category] = {
                    loading: false,
                    loaded: true,
                    data: data.data
                  }
                  allData[data.category] = data.data

                  // 合并到 comprehensiveData
                  if (!comprehensiveData.value) {
                    comprehensiveData.value = { success: true }
                  }
                  // 将分类数据展开到 comprehensiveData
                  if (data.data.data) {
                    Object.assign(comprehensiveData.value, data.data.data)
                  }

                  console.log(`✅ ${data.data.name} 加载完成: ${data.data.success_count}/${data.data.total_count} 接口`)
                }
                break

              case 'complete': {
                completed = true
                eventSource.close()
                sseEventSource = null

                // 生成最终的 comprehensiveData
                const finalData = {
                  success: true,
                  ts_code: code,
                  timestamp: new Date().toISOString(),
                  interface_status: {},
                  alerts: [],
                  data_summary: {
                    total_time: data.total_time,
                    success_count: data.success_count,
                    total_count: data.total_count,
                    success_rate: data.success_rate
                  }
                }

                // 合并所有分类数据
                Object.values(allData).forEach(categoryData => {
                  if (categoryData.data) {
                    Object.assign(finalData, categoryData.data)
                  }
                })

                comprehensiveData.value = finalData
                showToast(`数据获取完成: ${data.success_count}/${data.total_count} 接口成功`, 'success')
                resolve(finalData)
                break
              }

              case 'error':
                console.error(`❌ 分类 ${data.category} 获取失败:`, data.error)
                if (data.category && categoryLoadingStates.value[data.category]) {
                  categoryLoadingStates.value[data.category] = {
                    loading: false,
                    loaded: true,
                    data: { error: data.error }
                  }
                }
                break
            }
          } catch (e) {
            console.error('解析 SSE 消息失败:', e)
          }
        }

        eventSource.onerror = (error) => {
          console.error('SSE 连接错误:', error)
          eventSource.close()
          sseEventSource = null

          if (!completed) {
            // 如果还没完成就出错，回退到普通请求
            console.log('🔄 SSE 失败，回退到普通请求')
            reject(new Error('SSE 连接失败'))
          }
        }

        // 超时处理（5分钟）
        setTimeout(() => {
          if (!completed && eventSource.readyState !== EventSource.CLOSED) {
            console.warn('⏰ SSE 超时，关闭连接')
            eventSource.close()
            sseEventSource = null
            reject(new Error('SSE 超时'))
          }
        }, 300000)
      })
    }

    // 获取并缓存股票数据（仅在添加监控、立即更新、定时刷新时调用）
    // 优化：使用 SSE 流式获取，边获取边渲染
    const fetchAndCacheStockData = async (code) => {
      // 防重检查：如果该股票正在请求中，直接返回
      if (pendingRequests.value.has(code)) {
        console.log(`⏳ ${code} 正在请求中，跳过重复请求`)
        return null
      }

      // 标记为正在请求
      pendingRequests.value.add(code)

      // 取消之前的请求（如果有）
      if (abortController) {
        abortController.abort()
        console.log('🚫 取消之前的请求')
      }
      abortController = new AbortController()
      const signal = abortController.signal

      try {
        loadingComprehensive.value = true
        loadingStates.value = { comprehensive: true, news: true, risk: true }
        console.log(`📊 开始获取 ${code} 的数据（流式模式）...`)
        const startTime = Date.now()

        const cacheData = {
          comprehensive: null,
          news: [],
          sentiment: {},
          risk: {},
          timestamp: new Date().toISOString()
        }

        // 并行请求：综合数据使用 SSE 流式获取，新闻和风险使用普通请求
        const [comprehensiveResult, newsResult, riskResult] = await Promise.all([
          // 1. 综合数据（SSE 流式获取）
          fetchComprehensiveDataStream(code)
            .then(data => {
              loadingStates.value.comprehensive = false
              return { success: true, ...data }
            })
            .catch(async error => {
              console.warn('SSE 失败，使用普通请求:', error.message)
              // 回退到普通请求
              try {
                const resp = await axios.get(`${API_BASE}/dataflow/stock/comprehensive/${code}`, {
                  signal,
                  params: { async_mode: false }  // 使用同步模式
                })
                loadingStates.value.comprehensive = false
                return resp.data
              } catch (e) {
                loadingStates.value.comprehensive = false
                return { success: false, error: e.message }
              }
            }),

          // 2. 新闻（已包含情绪分析）
          axios.get(`${API_BASE}/dataflow/stock/news/${code}`, {
            params: { limit: 50 },
            signal
          })
            .then(resp => {
              loadingStates.value.news = false
              return resp.data
            })
            .catch(error => {
              loadingStates.value.news = false
              if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') throw error
              console.error('新闻获取失败:', error.message)
              return { success: false, news: [], error: error.message }
            }),

          // 3. 风险分析
          axios.get(`${API_BASE}/dataflow/stock/risk/${code}`, { signal })
            .then(resp => {
              loadingStates.value.risk = false
              return resp.data
            })
            .catch(error => {
              loadingStates.value.risk = false
              if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') throw error
              console.error('风险分析失败:', error.message)
              return { success: false, error: error.message }
            })
        ])

        // 处理综合数据
        if (comprehensiveResult.success) {
          cacheData.comprehensive = comprehensiveResult
          console.log('📊 综合数据获取成功')
        }

        // 处理新闻数据（包含情绪分析）
        if (newsResult.success) {
          cacheData.news = newsResult.news || []
          // 从新闻数据中提取情绪分析结果
          cacheData.sentiment = {
            success: true,
            overall_score: newsResult.overall_score || 50,
            sentiment_summary: newsResult.sentiment_summary || {},
            news_count: cacheData.news.length
          }
          console.log(`📰 新闻获取: ${cacheData.news.length}条`)
        }

        // 处理风险数据
        if (riskResult.success) {
          cacheData.risk = riskResult
        }

        // 保存到缓存
        stockDataCache.value[code] = cacheData
        const elapsed = Date.now() - startTime
        console.log(`✅ 数据已缓存: ${code} (耗时 ${elapsed}ms)`)

        // 如果当前正在查看这个股票，更新显示
        if (selectedStock.value?.code === code) {
          comprehensiveData.value = cacheData.comprehensive
          stockNews.value = cacheData.news
          stockSentiment.value = cacheData.sentiment
          stockRisk.value = cacheData.risk
        }

        return cacheData
      } catch (error) {
        // 请求被取消，不做处理
        if (error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
          console.log('📛 请求已取消，忽略结果')
          return null
        }
        console.error('获取数据失败:', error)
        throw error
      } finally {
        // 清理防重标记
        pendingRequests.value.delete(code)
        loadingComprehensive.value = false
        loadingStates.value = { comprehensive: false, news: false, risk: false }
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

    // 获取风险评分样式类
    const getRiskScoreClass = (score) => {
      if (!score) return 'low'
      if (score >= 70) return 'high'
      if (score >= 40) return 'medium'
      return 'low'
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
      if (!sentiment) return '中性'
      const map = {
        positive: '正面',
        negative: '负面',
        neutral: '中性'
      }
      return map[sentiment] || '中性'
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

    // 新闻展开/收起切换
    const toggleNewsExpand = (index) => {
      expandedNews.value[index] = !expandedNews.value[index]
    }

    // 关键词高亮显示
    const highlightKeywords = (text, stockCode, stockName) => {
      if (!text) return ''

      // 构建关键词列表
      const keywords = []
      if (stockCode) {
        // 提取纯数字代码
        const code = stockCode.split('.')[0]
        keywords.push(code)
      }
      if (stockName) {
        keywords.push(stockName)
        // 添加简称（如"茅台"）
        if (stockName.length >= 4) {
          keywords.push(stockName.substring(2))
        }
      }

      if (keywords.length === 0) return text

      // 转义特殊字符
      const escapeRegExp = (str) => str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')

      // 构建正则表达式
      const pattern = keywords.map(escapeRegExp).join('|')
      const regex = new RegExp(`(${pattern})`, 'gi')

      // 替换为高亮标签
      return text.replace(regex, '<span class="keyword-highlight">$1</span>')
    }

    // 新增：获取预警等级文本
    const getAlertLevelText = (level) => {
      const map = {
        critical: '🔴 严重',
        high: '🟠 高',
        medium: '🟡 中',
        low: '🟢 低'
      }
      return map[level] || '未知'
    }

    // 新增：获取接口成功率
    const getInterfaceSuccessRate = () => {
      if (!comprehensiveData.value?.interface_status) return '0%'
      let total = 0
      let success = 0
      for (const category of Object.values(comprehensiveData.value.interface_status)) {
        total += category.total || 0
        success += category.success || 0
      }
      if (total === 0) return '0%'
      return Math.round((success / total) * 100) + '%'
    }

    // 获取接口中文名称（共48个接口 - Tushare 33个 + AKShare 15个）
    // 按文档 docs\数据接口说明.md 完整定义
    const getInterfaceName = (name) => {
      const map = {
        // ========== 基础信息 (4个 Tushare) ==========
        company_info: '公司信息 [stock_company]',
        managers: '管理层 [stk_managers]',
        manager_rewards: '管理层薪酬 [stk_rewards]',
        main_business: '主营业务 [fina_mainbz]',

        // ========== 行情数据 (7个 Tushare + 2个 AKShare) ==========
        realtime: '实时行情 [realtime_quote]',
        realtime_tick: '分时成交 [realtime_tick]',
        realtime_list: '全市场行情 [realtime_list]',
        limit_list: '涨跌停 [limit_list_d]',
        limit_list_ths: '涨跌停同花顺 [limit_list_ths]',
        dragon_tiger: '龙虎榜 [top_list]',
        top_inst: '机构龙虎榜 [top_inst]',
        dragon_tiger_ak: '龙虎榜AK [stock_lhb]',
        block_trade: '大宗交易 [stock_dzjy]',

        // ========== 财务数据 (5个 Tushare + 3个 AKShare) ==========
        financial: '财务报表 [income/balance/cashflow]',
        audit: '审计意见 [fina_audit]',
        forecast: '业绩预告 [forecast/express]',
        express: '业绩快报 [express]',
        dividend: '分红送股 [dividend]',
        audit_ak: '审计意见AK [stock_audit]',
        forecast_ak: '业绩预告AK [stock_yjyg_em]',
        financial_risk: '财务风险 [stock_financial_risk]',

        // ========== 资金流向 (9个 Tushare + 3个 AKShare) ==========
        margin: '融资融券 [margin]',
        margin_detail: '融资融券明细 [margin_detail]',
        hsgt_holding: '沪深股通 [hsgt_top10]',
        ggt_top10: '港股通十大 [ggt_top10]',
        hk_hold: '港资持股 [hk_hold]',
        moneyflow_hsgt: '北向资金 [moneyflow_hsgt]',
        holder_trade: '股东增减持 [stk_holdertrade]',
        pledge: '股权质押 [pledge_stat]',
        pledge_detail: '质押明细 [pledge_detail]',
        margin_ak: '融资融券AK [stock_margin]',
        holder_trade_ak: '股东增减持AK [stock_gdhs]',
        pledge_detail_ak: '质押明细AK [stock_gpzy]',

        // ========== 风险监控 (3个 Tushare + 4个 AKShare) ==========
        st_status: 'ST状态 [stock_st]',
        suspend: '停复牌 [suspend_d]',
        restricted: '限售解禁 [share_float]',
        st_status_ak: 'ST状态AK [stock_zh_a_st_em]',
        st_info_ak: 'ST详情AK [stock_st_info]',
        suspend_ak: '停复牌AK [stock_stop]',
        restricted_ak: '限售解禁AK [stock_restricted]',

        // ========== 新闻舆情 (1个 Tushare + 7个 AKShare) ==========
        announcements: '公告 [forecast/express]',
        news: '综合新闻聚合',
        news_em: '东财新闻 [stock_news_em]',
        news_sina: '新浪新闻 [stock_news_sina]',
        announcements_ak: '公告AK [stock_announcement]',
        market_news: '市场快讯 [stock_market_news]',
        cninfo_news: '巨潮资讯 [cninfo]',
        industry_policy: '行业政策 [stock_industry_policy]'
      }
      return map[name] || name
    }

    // ========== 图表初始化方法 ==========

    // 初始化融资融券趋势图
    const initMarginChart = () => {
      if (!marginChartRef.value) return

      if (marginChart) {
        marginChart.dispose()
      }

      marginChart = echarts.init(marginChartRef.value)

      // 安全获取数组数据
      let marginData = comprehensiveData.value?.margin?.data
      if (!marginData) {
        marginData = []
      } else if (!Array.isArray(marginData)) {
        marginData = Object.values(marginData)
      }
      if (marginData.length === 0) return

      // 反转数据使其按时间正序
      const sortedData = [...marginData].reverse()

      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          borderColor: 'rgba(99, 102, 241, 0.3)',
          textStyle: { color: '#e2e8f0' },
          formatter: (params) => {
            let result = `<div style="font-weight:bold;margin-bottom:5px">${params[0].axisValue}</div>`
            params.forEach(p => {
              result += `<div>${p.marker} ${p.seriesName}: ${formatMoney(p.value)}</div>`
            })
            return result
          }
        },
        legend: {
          data: ['融资余额', '融券余额'],
          textStyle: { color: '#94a3b8' },
          top: 5
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: 40,
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: sortedData.map(d => d.trade_date?.substring(5) || ''),
          axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.3)' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 }
        },
        yAxis: {
          type: 'value',
          axisLine: { show: false },
          splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.1)' } },
          axisLabel: {
            color: '#94a3b8',
            formatter: (v) => formatMoney(v)
          }
        },
        series: [
          {
            name: '融资余额',
            type: 'line',
            data: sortedData.map(d => d.rzye || 0),
            smooth: true,
            lineStyle: { color: '#3b82f6', width: 2 },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(59, 130, 246, 0.3)' },
                { offset: 1, color: 'rgba(59, 130, 246, 0.05)' }
              ])
            },
            itemStyle: { color: '#3b82f6' }
          },
          {
            name: '融券余额',
            type: 'line',
            data: sortedData.map(d => d.rqye || 0),
            smooth: true,
            lineStyle: { color: '#f59e0b', width: 2 },
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(245, 158, 11, 0.3)' },
                { offset: 1, color: 'rgba(245, 158, 11, 0.05)' }
              ])
            },
            itemStyle: { color: '#f59e0b' }
          }
        ]
      }

      marginChart.setOption(option)
    }

    // 初始化风险雷达图
    const initRiskRadarChart = () => {
      if (!riskRadarRef.value) return

      if (riskRadarChart) {
        riskRadarChart.dispose()
      }

      riskRadarChart = echarts.init(riskRadarRef.value)

      // 计算各项风险指标
      const data = comprehensiveData.value || {}

      // ST风险 (0-100)
      const stRisk = data.st_status?.is_st ? 100 : 0

      // 停牌风险 (0-100)
      const suspendRisk = data.suspend?.status === 'has_suspend' ? 60 : 0

      // 质押风险 (0-100)
      const pledgeRatio = data.pledge?.pledge_ratio || 0
      const pledgeRisk = Math.min(pledgeRatio * 1.5, 100)

      // 解禁风险 (0-100)
      const restrictedCount = data.restricted?.count || 0
      const restrictedRisk = Math.min(restrictedCount * 20, 100)

      // 审计风险 (0-100)
      const auditRisk = data.audit?.is_standard === false ? 80 : 0

      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          borderColor: 'rgba(99, 102, 241, 0.3)',
          textStyle: { color: '#e2e8f0' }
        },
        radar: {
          indicator: [
            { name: 'ST风险', max: 100 },
            { name: '停牌风险', max: 100 },
            { name: '质押风险', max: 100 },
            { name: '解禁风险', max: 100 },
            { name: '审计风险', max: 100 }
          ],
          center: ['50%', '55%'],
          radius: '65%',
          axisName: {
            color: '#94a3b8',
            fontSize: 11
          },
          splitArea: {
            areaStyle: {
              color: ['rgba(99, 102, 241, 0.05)', 'rgba(99, 102, 241, 0.1)']
            }
          },
          axisLine: {
            lineStyle: { color: 'rgba(148, 163, 184, 0.2)' }
          },
          splitLine: {
            lineStyle: { color: 'rgba(148, 163, 184, 0.2)' }
          }
        },
        series: [{
          type: 'radar',
          data: [{
            value: [stRisk, suspendRisk, pledgeRisk, restrictedRisk, auditRisk],
            name: '风险指标',
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: 'rgba(239, 68, 68, 0.4)' },
                { offset: 1, color: 'rgba(239, 68, 68, 0.1)' }
              ])
            },
            lineStyle: { color: '#ef4444', width: 2 },
            itemStyle: { color: '#ef4444' }
          }]
        }]
      }

      riskRadarChart.setOption(option)
    }

    // 初始化资金流向图表（北向资金/沪深港通）
    const initCapitalFlowChart = () => {
      if (!capitalFlowRef.value) return

      if (capitalFlowChart) {
        capitalFlowChart.dispose()
      }

      capitalFlowChart = echarts.init(capitalFlowRef.value)

      // 安全获取数组数据
      let hsgtData = comprehensiveData.value?.hsgt_holding?.data
      if (!hsgtData) {
        hsgtData = []
      } else if (!Array.isArray(hsgtData)) {
        // 如果是对象，尝试转换为数组
        hsgtData = Object.values(hsgtData)
      }
      if (hsgtData.length === 0) return

      // 反转数据使其按时间正序
      const sortedData = [...hsgtData].reverse()

      const option = {
        backgroundColor: 'transparent',
        tooltip: {
          trigger: 'axis',
          backgroundColor: 'rgba(15, 23, 42, 0.9)',
          borderColor: 'rgba(99, 102, 241, 0.3)',
          textStyle: { color: '#e2e8f0' },
          formatter: (params) => {
            let result = `<div style="font-weight:bold;margin-bottom:5px">${params[0].axisValue}</div>`
            params.forEach(p => {
              const unit = p.seriesName.includes('比') ? '%' : ''
              const value = p.seriesName.includes('比') ? p.value : formatMoney(p.value)
              result += `<div>${p.marker} ${p.seriesName}: ${value}${unit}</div>`
            })
            return result
          }
        },
        legend: {
          data: ['持股市值', '占流通股比'],
          textStyle: { color: '#94a3b8' },
          top: 5
        },
        grid: {
          left: '3%',
          right: '4%',
          bottom: '3%',
          top: 40,
          containLabel: true
        },
        xAxis: {
          type: 'category',
          data: sortedData.map(d => d.trade_date?.substring(5) || ''),
          axisLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.3)' } },
          axisLabel: { color: '#94a3b8', fontSize: 10 }
        },
        yAxis: [
          {
            type: 'value',
            name: '持股市值',
            position: 'left',
            axisLine: { show: false },
            splitLine: { lineStyle: { color: 'rgba(148, 163, 184, 0.1)' } },
            axisLabel: {
              color: '#94a3b8',
              formatter: (v) => formatMoney(v)
            }
          },
          {
            type: 'value',
            name: '占比(%)',
            position: 'right',
            axisLine: { show: false },
            splitLine: { show: false },
            axisLabel: {
              color: '#94a3b8',
              formatter: '{value}%'
            }
          }
        ],
        series: [
          {
            name: '持股市值',
            type: 'bar',
            data: sortedData.map(d => d.hold_amount || 0),
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#10b981' },
                { offset: 1, color: 'rgba(16, 185, 129, 0.3)' }
              ])
            },
            barWidth: '60%'
          },
          {
            name: '占流通股比',
            type: 'line',
            yAxisIndex: 1,
            data: sortedData.map(d => d.hold_ratio || 0),
            smooth: true,
            lineStyle: { color: '#f59e0b', width: 2 },
            itemStyle: { color: '#f59e0b' }
          }
        ]
      }

      capitalFlowChart.setOption(option)
    }

    // 销毁所有图表
    const disposeCharts = () => {
      if (marginChart) {
        marginChart.dispose()
        marginChart = null
      }
      if (riskRadarChart) {
        riskRadarChart.dispose()
        riskRadarChart = null
      }
      if (capitalFlowChart) {
        capitalFlowChart.dispose()
        capitalFlowChart = null
      }
    }

    // 监听 detailTab 变化，初始化对应图表
    watch(detailTab, async (newTab) => {
      await nextTick()
      if (newTab === 'capital') {
        initMarginChart()
        initCapitalFlowChart()
      } else if (newTab === 'risk') {
        initRiskRadarChart()
      }
    })

    // 监听 comprehensiveData 变化，更新图表
    watch(comprehensiveData, async () => {
      await nextTick()
      if (detailTab.value === 'capital') {
        initMarginChart()
        initCapitalFlowChart()
      } else if (detailTab.value === 'risk') {
        initRiskRadarChart()
      }
    }, { deep: true })

    // 监听监控股票列表变化，自动订阅新股票
    watch(monitoredStocks, (newStocks, oldStocks) => {
      if (!websocket || websocket.readyState !== WebSocket.OPEN) return

      // 找出新增的股票
      const oldCodes = new Set((oldStocks || []).map(s => s.code))
      const newCodes = newStocks.map(s => s.code)

      newCodes.forEach(code => {
        if (!oldCodes.has(code)) {
          subscribeStock(code)
          console.log(`📡 自动订阅新股票: ${code}`)
        }
      })
    }, { deep: true })

    // ========== WebSocket 连接管理 ==========

    // 连接 WebSocket
    const connectWebSocket = () => {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        return  // 已连接
      }

      const wsUrl = `${WS_BASE_URL}/ws/dataflow`
      console.log('🔌 连接 WebSocket:', wsUrl)

      websocket = new WebSocket(wsUrl)

      websocket.onopen = () => {
        console.log('✅ WebSocket 已连接')
        // 订阅所有监控股票
        monitoredStocks.value.forEach(stock => {
          subscribeStock(stock.code)
        })
      }

      websocket.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data)
          handleWebSocketMessage(message)
        } catch (e) {
          console.error('WebSocket 消息解析失败:', e)
        }
      }

      websocket.onclose = () => {
        console.log('⚠️ WebSocket 已断开，5秒后重连...')
        setTimeout(connectWebSocket, 5000)
      }

      websocket.onerror = (error) => {
        console.error('WebSocket 错误:', error)
      }
    }

    // 订阅股票更新
    const subscribeStock = (tsCode) => {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          action: 'subscribe',
          ts_code: tsCode
        }))
      }
    }

    // 取消订阅股票
    // eslint-disable-next-line no-unused-vars
    const unsubscribeStock = (tsCode) => {
      if (websocket && websocket.readyState === WebSocket.OPEN) {
        websocket.send(JSON.stringify({
          action: 'unsubscribe',
          ts_code: tsCode
        }))
      }
    }

    // 处理 WebSocket 消息
    const handleWebSocketMessage = (message) => {
      console.log('📨 WebSocket 消息:', message.type, message.event || '')

      switch (message.type) {
        case 'connected':
          console.log('WebSocket 连接确认:', message.client_id)
          break

        case 'subscribed':
          console.log('已订阅:', message.ts_code)
          break

        case 'stock_update':
          handleStockUpdate(message)
          break

        case 'pong':
          // 心跳响应
          break
      }
    }

    // 处理股票数据更新通知
    const handleStockUpdate = (message) => {
      const { event, ts_code, data } = message

      if (event === 'update_complete') {
        console.log(`✅ ${ts_code} 数据更新完成`)
        showToast(`${ts_code} 数据已更新`, 'success')

        // 清除前端缓存，下次查看时从数据库加载最新数据
        if (stockDataCache.value[ts_code]) {
          delete stockDataCache.value[ts_code]
        }

        // 如果当前正在查看这个股票，自动刷新
        if (selectedStock.value?.code === ts_code) {
          viewDetails(selectedStock.value)
        }

        // 刷新监控列表
        loadMonitoredStocks()
      } else if (event === 'update_progress') {
        console.log(`📊 ${ts_code} 更新进度: ${data?.progress}%`)
      } else if (event === 'update_error') {
        console.error(`❌ ${ts_code} 更新失败:`, data?.error)
        showToast(`${ts_code} 更新失败: ${data?.error}`, 'error')
      }
    }

    // 断开 WebSocket
    const disconnectWebSocket = () => {
      if (websocket) {
        websocket.close()
        websocket = null
      }
    }

    // 生命周期
    onMounted(() => {
      // 页面加载时检测一次数据源状态
      loadDataSources()
      // 加载其他数据
      refreshAllData()
      // 加载通知设置数据
      loadNotificationChannels()
      loadConfigGuide()
      loadNotificationConfig()
      // 每2分钟自动刷新监控股票和新闻（不刷新数据源状态）
      setInterval(refreshAllData, 120000)

      // 连接 WebSocket 接收实时更新通知
      connectWebSocket()

      // 窗口大小变化时重绘图表
      window.addEventListener('resize', () => {
        marginChart?.resize()
        riskRadarChart?.resize()
        capitalFlowChart?.resize()
      })
    })

    // 组件卸载时清理图表和WebSocket
    onUnmounted(() => {
      disposeCharts()
      disconnectWebSocket()
    })

    // 安全获取数组数据（处理 data 可能是对象或数组的情况）
    const safeArray = (obj, limit = 10) => {
      if (!obj) return []
      const data = obj.data
      if (Array.isArray(data)) {
        return data.slice(0, limit)
      }
      if (data && typeof data === 'object') {
        // 如果是对象，尝试转换为数组
        return Object.values(data).slice(0, limit)
      }
      return []
    }

    return {
      isRefreshing,
      refreshingText,
      refreshingProgress,
      showAddMonitor,
      showStockDetails,
      showNotificationSettings,  // 通知设置弹窗
      showInterfaceTest,  // 接口测试弹窗
      currentFilter,
      newsSource,
      detailTab,
      newsTypeFilter,
      monitoredStocks,
      dataSources,
      newsList,
      filteredNewsList,
      sentimentFilter,
      sentimentStats,
      newsLoading,  // 新闻加载状态
      selectedStock,
      stockNews,
      stockSentiment,
      stockRisk,
      toasts,  // 添加toasts
      expandedNews,  // 新闻展开状态
      // 接口测试相关
      interfaceTestResults,
      interfaceTestRunning,
      interfaceTestProgress,
      interfaceTestTotal,
      interfaceTestSuccess,
      interfaceTestFail,
      interfaceTestSuccessRate,
      expandedSources,
      dataSourcesCollapsed,
      openInterfaceTest,
      startInterfaceTest,
      toggleSourceExpand,
      // 图表相关
      marginChartRef,
      riskRadarRef,
      capitalFlowRef,
      // 通知相关
      notificationChannels,
      configGuide,
      expandedGuide,
      testEmail,
      testingChannel,
      sendingTestEmail,
      savingConfig,
      notificationConfig,
      toggleGuide,
      testNotificationChannel,
      sendTestEmail,
      loadNotificationConfig,
      saveNotificationConfig,
      newMonitor,
      selectedStockName,  // 选中的股票名称
      onStockSelect,  // 股票选择回调
      // 综合数据
      loadingComprehensive,
      comprehensiveData,
      categoryLoadingStates,  // 分类加载状态（流式渲染）
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
      refreshCurrentStock,  // 新增
      fetchAndCacheStockData,
      openNewsLink,
      toggleNewsExpand,  // 新闻展开切换
      highlightKeywords,  // 关键词高亮
      formatTime,
      formatMoney,  // 新增
      getStatusText,
      getRiskText,
      getRiskScoreClass,  // 风险评分样式
      getSentimentColor,
      getSentimentClass,
      getSentimentLabel,
      getReportTypeLabel,
      getUrgencyLabel,
      getNewsUrgencyClass,
      getTotalSentiment,
      getPercentage,
      // 新增方法
      getAlertLevelText,
      getInterfaceSuccessRate,
      getInterfaceName,
      safeArray  // 安全数组转换
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

/* 加载遮罩样式 */
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

.section-header.clickable {
  cursor: pointer;
  user-select: none;
}

.section-header.clickable:hover h2 {
  color: #60a5fa;
}

.section-header h2 {
  font-size: 1.5rem;
  color: #f1f5f9;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.collapse-icon {
  font-size: 0.8rem;
  color: #94a3b8;
  transition: transform 0.2s;
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
  font-size: 1rem;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.input-field:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.input-field::placeholder {
  color: #64748b;
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

.form-hint {
  display: block;
  margin-top: 0.5rem;
  font-size: 0.75rem;
  color: rgba(226, 232, 240, 0.6);
  font-style: italic;
}

.form-hint.stock-selected {
  color: #22c55e;
  font-style: normal;
  font-weight: 500;
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

/* 新闻筛选区域 */
.news-filters {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.sentiment-tabs {
  display: flex;
  gap: 0.5rem;
}

.sentiment-tab {
  padding: 0.4rem 0.8rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 6px;
  color: #94a3b8;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.sentiment-tab:hover {
  background: rgba(30, 41, 59, 0.8);
  color: #e2e8f0;
}

.sentiment-tab.active {
  background: rgba(59, 130, 246, 0.2);
  border-color: #3b82f6;
  color: #60a5fa;
}

.sentiment-tab.positive.active {
  background: rgba(34, 197, 94, 0.2);
  border-color: #22c55e;
  color: #4ade80;
}

.sentiment-tab.negative.active {
  background: rgba(239, 68, 68, 0.2);
  border-color: #ef4444;
  color: #f87171;
}

.tab-count {
  background: rgba(255, 255, 255, 0.1);
  padding: 0.1rem 0.4rem;
  border-radius: 10px;
  font-size: 0.75rem;
  margin-left: 0.3rem;
}

/* 新闻项情绪样式 */
.news-item.sentiment-positive {
  border-left: 3px solid #22c55e;
}

.news-item.sentiment-negative {
  border-left: 3px solid #ef4444;
}

.news-item.sentiment-neutral {
  border-left: 3px solid #64748b;
}

.sentiment-badge {
  margin-right: 0.5rem;
}

.news-keywords {
  color: #60a5fa;
  font-size: 0.8rem;
}

.news-score {
  font-size: 0.8rem;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

.news-score.positive {
  background: rgba(34, 197, 94, 0.2);
  color: #4ade80;
}

.news-score.negative {
  background: rgba(239, 68, 68, 0.2);
  color: #f87171;
}

.news-score.neutral {
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
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

.modal-header .header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
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

.news-link-btn {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  text-decoration: none;
  font-size: 0.8rem;
  transition: all 0.2s;
  cursor: pointer;
}

.news-link-btn:hover {
  background: rgba(16, 185, 129, 0.4);
  color: #34d399;
}

/* 新闻内容展开/收起 */
.news-content-wrapper {
  position: relative;
}

.news-content {
  color: rgba(226, 232, 240, 0.8);
  line-height: 1.6;
  margin: 0.75rem 0;
  max-height: 4.8em;  /* 约3行 */
  overflow: hidden;
  transition: max-height 0.3s ease;
}

.news-content.expanded {
  max-height: none;
}

.expand-btn {
  background: transparent;
  border: none;
  color: #60a5fa;
  cursor: pointer;
  font-size: 0.85rem;
  padding: 0.25rem 0;
  margin-top: 0.25rem;
  transition: color 0.2s;
}

.expand-btn:hover {
  color: #93c5fd;
}

/* 关键词高亮 */
.keyword-highlight {
  background: linear-gradient(135deg, rgba(251, 191, 36, 0.3), rgba(245, 158, 11, 0.3));
  color: #fbbf24;
  padding: 0 0.2rem;
  border-radius: 3px;
  font-weight: 500;
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

/* ========== 预警面板样式 ========== */
.alerts-panel {
  background: linear-gradient(135deg, rgba(239, 68, 68, 0.1), rgba(15, 23, 42, 0.5));
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 12px;
  padding: 1rem;
  margin-bottom: 1rem;
}

.alerts-panel h4 {
  margin: 0 0 1rem 0;
  color: #fca5a5;
  font-size: 1.1rem;
}

.alerts-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  max-height: 200px;
  overflow-y: auto;
}

.alert-item {
  background: rgba(15, 23, 42, 0.5);
  border-radius: 8px;
  padding: 0.75rem;
  border-left: 4px solid;
}

.alert-item.critical {
  border-left-color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.alert-item.high {
  border-left-color: #f59e0b;
  background: rgba(245, 158, 11, 0.1);
}

.alert-item.medium {
  border-left-color: #eab308;
  background: rgba(234, 179, 8, 0.1);
}

.alert-item.low {
  border-left-color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.alert-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
}

.alert-title {
  font-weight: 600;
  color: #e2e8f0;
}

.alert-level {
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.75rem;
  font-weight: 600;
}

.alert-level.critical {
  background: rgba(239, 68, 68, 0.2);
  color: #fca5a5;
}

.alert-level.high {
  background: rgba(245, 158, 11, 0.2);
  color: #fcd34d;
}

.alert-level.medium {
  background: rgba(234, 179, 8, 0.2);
  color: #fde047;
}

.alert-level.low {
  background: rgba(34, 197, 94, 0.2);
  color: #86efac;
}

.alert-message {
  color: rgba(226, 232, 240, 0.8);
  font-size: 0.9rem;
  margin: 0 0 0.5rem 0;
}

.alert-suggestion {
  color: rgba(226, 232, 240, 0.6);
  font-size: 0.85rem;
  margin: 0;
  font-style: italic;
}

.no-alerts {
  background: rgba(34, 197, 94, 0.1);
  border: 1px solid rgba(34, 197, 94, 0.3);
  border-radius: 8px;
  padding: 0.75rem 1rem;
  margin-bottom: 1rem;
  color: #86efac;
  text-align: center;
}

/* ========== 接口状态面板样式 ========== */
.interface-status-panels {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.interface-category {
  background: rgba(15, 23, 42, 0.3);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 12px;
  padding: 1rem;
}

.category-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 1rem;
  padding-bottom: 0.75rem;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.category-icon {
  font-size: 1.5rem;
}

.category-name {
  font-size: 1.1rem;
  font-weight: 600;
  color: #e2e8f0;
  flex: 1;
}

.category-stats {
  display: flex;
  gap: 0.75rem;
  font-size: 0.85rem;
}

.stat-success {
  color: #86efac;
}

.stat-failed {
  color: #fca5a5;
}

.stat-nodata {
  color: rgba(226, 232, 240, 0.5);
}

.interface-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 0.5rem;
}

.interface-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 0.75rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 6px;
  font-size: 0.85rem;
}

.interface-item.success,
.interface-item.normal,
.interface-item.has_suspend,
.interface-item.st_stock {
  border-left: 3px solid #22c55e;
}

.interface-item.error,
.interface-item.timeout {
  border-left: 3px solid #ef4444;
}

.interface-item.no_data,
.interface-item.deferred {
  border-left: 3px solid rgba(226, 232, 240, 0.3);
}

.interface-name {
  color: #e2e8f0;
  flex: 1;
}

.interface-status-label {
  font-size: 0.75rem;
}

.interface-count {
  color: #60a5fa;
  font-size: 0.75rem;
}

.interface-message {
  color: rgba(226, 232, 240, 0.5);
  font-size: 0.7rem;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.interface-rate {
  font-size: 1.2rem;
  font-weight: 600;
  color: #60a5fa;
}

.risk-score-value {
  font-size: 1.2rem;
  font-weight: 600;
}

.risk-score-value.low {
  color: #22c55e;
}

.risk-score-value.medium {
  color: #f59e0b;
}

.risk-score-value.high {
  color: #ef4444;
}

/* ========== 公司简介样式 ========== */
.company-intro {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

.company-intro p {
  color: rgba(226, 232, 240, 0.8);
  line-height: 1.6;
  margin: 0.5rem 0 0 0;
}

/* ========== 审计信息样式 ========== */
.audit-info {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1rem;
}

.audit-item {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.audit-item .safe {
  color: #86efac;
}

.audit-item .danger {
  color: #fca5a5;
}

/* ========== 风险卡片增强样式 ========== */
.risk-status-value {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
}

.risk-status-value.safe {
  color: #86efac;
}

.risk-status-value.danger {
  color: #fca5a5;
}

.risk-status-value.warning {
  color: #fcd34d;
}

.risk-message {
  color: rgba(226, 232, 240, 0.7);
  font-size: 0.9rem;
  margin: 0;
}

.risk-card.warning {
  border-color: rgba(245, 158, 11, 0.5);
  background: rgba(245, 158, 11, 0.1);
}

/* ========== 业绩预告类型样式 ========== */
.forecast-type {
  display: inline-block;
  padding: 0.15rem 0.5rem;
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-radius: 4px;
  font-size: 0.8rem;
  margin-bottom: 0.5rem;
}

/* ========== 值颜色样式 ========== */
.value.safe {
  color: #86efac !important;
}

.value.danger {
  color: #fca5a5 !important;
}

/* ========== 新闻链接样式 ========== */
.news-link {
  color: #60a5fa;
  text-decoration: none;
  transition: color 0.2s;
}

.news-link:hover {
  color: #93c5fd;
  text-decoration: underline;
}

.news-read-more {
  display: inline-block;
  margin-top: 0.5rem;
  color: #10b981;
  text-decoration: none;
  font-size: 0.85rem;
  transition: color 0.2s;
}

.news-read-more:hover {
  color: #34d399;
}

/* ========== 提示文字样式 ========== */
.empty-state .hint {
  color: rgba(148, 163, 184, 0.6);
  font-size: 0.85rem;
  margin-top: 0.5rem;
}

/* ========== 风险面板样式 ========== */
.risk-full-panel {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 风险概览区域 - 雷达图和风险卡片并排 */
.risk-overview-section {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  padding: 0 1rem;
}

.radar-container,
.risk-score-container {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 1.25rem;
}

/* 风险卡片侧边栏 - 2x2网格 */
.risk-cards-side {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.risk-cards-side .risk-card {
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
  padding: 16px;
  border-left: 3px solid #64748b;
}

.risk-cards-side .risk-card.safe {
  border-left-color: #22c55e;
}

.risk-cards-side .risk-card.warning {
  border-left-color: #f59e0b;
}

.risk-cards-side .risk-card.danger {
  border-left-color: #ef4444;
}

.risk-cards-side .risk-card h4 {
  margin: 0 0 8px 0;
  font-size: 0.85rem;
  color: #94a3b8;
}

.risk-cards-side .risk-status-value,
.risk-cards-side .pledge-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 4px;
}

.risk-cards-side .risk-status-value.safe,
.risk-cards-side .pledge-value:not(.danger) {
  color: #22c55e;
}

.risk-cards-side .risk-status-value.warning {
  color: #f59e0b;
}

.risk-cards-side .risk-status-value.danger,
.risk-cards-side .pledge-value.danger {
  color: #ef4444;
}

.risk-cards-side .risk-message {
  margin: 0;
  font-size: 0.75rem;
  color: #64748b;
}

/* 风险评分区域 - 单独一行 */
.risk-score-section {
  padding: 0 1rem;
}

.risk-score-section .risk-score-container {
  max-width: 400px;
  margin: 0 auto;
}

.radar-container h4,
.risk-score-container h4 {
  margin: 0 0 1rem 0;
  color: #e2e8f0;
  font-size: 1rem;
  text-align: center;
}

.radar-chart-box {
  width: 100%;
  height: 280px;
}

.risk-score-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 280px;
  gap: 1rem;
}

.score-circle {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(30, 41, 59, 0.8);
  border: 4px solid;
}

.score-circle.low {
  border-color: #22c55e;
  box-shadow: 0 0 20px rgba(34, 197, 94, 0.3);
}

.score-circle.medium {
  border-color: #f59e0b;
  box-shadow: 0 0 20px rgba(245, 158, 11, 0.3);
}

.score-circle.high {
  border-color: #ef4444;
  box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
}

.score-number {
  font-size: 3rem;
  font-weight: bold;
  color: #fff;
  line-height: 1;
}

.score-unit {
  font-size: 0.875rem;
  color: #94a3b8;
  margin-top: 0.25rem;
}

.risk-level-label {
  font-size: 1.25rem;
  font-weight: 600;
  padding: 0.5rem 1.5rem;
  border-radius: 20px;
}

.risk-level-label.low {
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
}

.risk-level-label.medium {
  background: rgba(245, 158, 11, 0.2);
  color: #f59e0b;
}

.risk-level-label.high {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
}

/* 响应式：小屏幕时垂直排列 */
@media (max-width: 900px) {
  .risk-overview-section {
    grid-template-columns: 1fr;
  }

  .risk-cards-side {
    grid-template-columns: 1fr 1fr;
  }

  .radar-chart-box {
    height: 250px;
  }

  .risk-score-display {
    height: auto;
    padding: 1.5rem 0;
  }
}

@media (max-width: 600px) {
  .risk-cards-side {
    grid-template-columns: 1fr;
  }
}

.risk-score-section {
  margin-top: 1rem;
}

/* ========== 通知设置弹窗样式 ========== */
.notification-settings-modal {
  max-width: 800px;
  width: 90vw;
  max-height: 85vh;
  overflow-y: auto;
}

.notification-content {
  padding: 1rem 0;
}

.notification-section {
  margin-bottom: 2rem;
}

.notification-section h4 {
  color: #e2e8f0;
  margin-bottom: 1rem;
  font-size: 1rem;
  border-bottom: 1px solid rgba(148, 163, 184, 0.2);
  padding-bottom: 0.5rem;
}

.channels-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 1rem;
}

.channel-card {
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 1rem;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 0.5rem;
  transition: all 0.3s ease;
}

.channel-card.configured {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.1);
}

.channel-card.not-configured {
  border-color: rgba(239, 68, 68, 0.3);
  opacity: 0.7;
}

.channel-icon {
  font-size: 2rem;
}

.channel-info {
  text-align: center;
}

.channel-name {
  display: block;
  color: #e2e8f0;
  font-weight: 500;
}

.channel-status {
  display: block;
  font-size: 0.75rem;
  color: rgba(148, 163, 184, 0.8);
  margin-top: 0.25rem;
}

.btn-small {
  padding: 0.25rem 0.75rem;
  font-size: 0.75rem;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
}

.btn-small:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
}

.btn-small:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.config-guide {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.guide-item {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 8px;
  overflow: hidden;
}

.guide-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.75rem 1rem;
  cursor: pointer;
  color: #e2e8f0;
  transition: background 0.2s;
}

.guide-header:hover {
  background: rgba(59, 130, 246, 0.1);
}

.toggle-icon {
  color: rgba(148, 163, 184, 0.6);
  font-size: 0.75rem;
}

.guide-content {
  padding: 1rem;
  border-top: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(15, 23, 42, 0.3);
}

.guide-content p {
  color: rgba(226, 232, 240, 0.8);
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.env-vars {
  margin-bottom: 1rem;
}

.env-vars h5 {
  color: #60a5fa;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.env-var {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
  padding: 0.5rem;
  background: rgba(15, 23, 42, 0.5);
  border-radius: 6px;
  margin-bottom: 0.5rem;
}

.env-var code {
  color: #fbbf24;
  font-family: 'Fira Code', monospace;
  font-size: 0.85rem;
}

.env-desc {
  color: rgba(226, 232, 240, 0.7);
  font-size: 0.8rem;
}

.env-example {
  color: rgba(148, 163, 184, 0.6);
  font-size: 0.75rem;
  font-style: italic;
}

.tips {
  margin-top: 1rem;
}

.tips h5 {
  color: #10b981;
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.tips ul {
  margin: 0;
  padding-left: 1.5rem;
}

.tips li {
  color: rgba(226, 232, 240, 0.7);
  font-size: 0.8rem;
  margin-bottom: 0.25rem;
}

.test-notification {
  display: flex;
  gap: 1rem;
  align-items: flex-end;
}

.test-notification .form-group {
  flex: 1;
  margin-bottom: 0;
}

.test-notification .btn-primary {
  white-space: nowrap;
}

/* 配置表单样式 */
.config-form {
  background: rgba(15, 23, 42, 0.4);
  border: 1px solid rgba(148, 163, 184, 0.2);
  border-radius: 12px;
  padding: 1rem;
}

.form-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}

.form-row:last-child {
  margin-bottom: 0;
}

.config-form .form-group {
  flex: 1;
  margin-bottom: 0;
}

.config-form .form-group-small {
  flex: 0 0 100px;
}

.config-form label {
  display: block;
  color: rgba(226, 232, 240, 0.8);
  font-size: 0.85rem;
  margin-bottom: 0.5rem;
}

.config-form .input-field {
  width: 100%;
  padding: 0.6rem 0.8rem;
  background: rgba(15, 23, 42, 0.6);
  border: 1px solid rgba(148, 163, 184, 0.3);
  border-radius: 8px;
  color: #e2e8f0;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.config-form .input-field:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
}

.config-form .input-field::placeholder {
  color: rgba(148, 163, 184, 0.5);
}

.config-form select.input-field {
  cursor: pointer;
}

.form-tips {
  display: flex;
  align-items: flex-start;
  gap: 0.5rem;
  margin-top: 0.75rem;
  padding: 0.5rem 0.75rem;
  background: rgba(59, 130, 246, 0.1);
  border-radius: 8px;
  border-left: 3px solid #3b82f6;
}

.form-tips .tip-icon {
  flex-shrink: 0;
}

.form-tips span {
  color: rgba(226, 232, 240, 0.7);
  font-size: 0.8rem;
  line-height: 1.4;
}

.form-tips a {
  color: #60a5fa;
  text-decoration: none;
}

.form-tips a:hover {
  text-decoration: underline;
}

.config-actions {
  display: flex;
  gap: 1rem;
  justify-content: center;
  padding: 1rem 0;
}

.config-actions .btn-primary,
.config-actions .btn-secondary {
  padding: 0.75rem 1.5rem;
  font-size: 0.95rem;
}

/* ========== 图表样式 ========== */
.chart-panel {
  margin-bottom: 1.5rem;
}

.chart-container {
  width: 100%;
  height: 280px;
  min-height: 250px;
}

.radar-panel {
  max-width: 500px;
  margin: 0 auto 1.5rem;
}

.radar-chart {
  height: 300px;
}

/* 图表响应式 */
@media (max-width: 768px) {
  .chart-container {
    height: 220px;
  }

  .radar-chart {
    height: 250px;
  }

  .radar-panel {
    max-width: 100%;
  }
}

/* ========== 接口测试弹窗样式 ========== */
.interface-test-modal {
  width: 90%;
  max-width: 900px;
  max-height: 85vh;
  display: flex;
  flex-direction: column;
}

.interface-test-modal .modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.interface-test-modal .header-actions {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.interface-test-modal .test-progress {
  color: #60a5fa;
  font-size: 0.9rem;
}

/* 测试概览 */
.test-overview {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 1rem;
  padding: 1rem 0;
  border-bottom: 1px solid rgba(71, 85, 105, 0.3);
}

.overview-stat {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.75rem;
  background: rgba(30, 41, 59, 0.5);
  border-radius: 8px;
}

.overview-stat .stat-icon {
  font-size: 1.5rem;
  margin-bottom: 0.25rem;
}

.overview-stat .stat-label {
  font-size: 0.75rem;
  color: rgba(226, 232, 240, 0.6);
  margin-bottom: 0.25rem;
}

.overview-stat .stat-value {
  font-size: 1.25rem;
  font-weight: 600;
  color: #e2e8f0;
}

.overview-stat.success .stat-value {
  color: #22c55e;
}

.overview-stat.fail .stat-value {
  color: #ef4444;
}

/* 进度条 */
.test-progress-bar {
  height: 4px;
  background: rgba(71, 85, 105, 0.3);
  border-radius: 2px;
  margin: 1rem 0;
  overflow: hidden;
}

.test-progress-bar .progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
  border-radius: 2px;
  transition: width 0.3s ease;
}

/* 测试结果容器 */
.test-results-container {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 0;
}

/* 数据源测试区块 */
.source-test-section {
  margin-bottom: 1rem;
  background: rgba(30, 41, 59, 0.3);
  border-radius: 8px;
  overflow: hidden;
}

.source-test-header {
  display: flex;
  align-items: center;
  padding: 0.75rem 1rem;
  background: rgba(51, 65, 85, 0.5);
  cursor: pointer;
  transition: background 0.2s;
}

.source-test-header:hover {
  background: rgba(51, 65, 85, 0.7);
}

.source-test-header .source-icon {
  font-size: 1.25rem;
  margin-right: 0.5rem;
}

.source-test-header .source-name {
  font-weight: 600;
  color: #e2e8f0;
  flex: 1;
}

.source-test-header .source-stats {
  display: flex;
  gap: 0.75rem;
  margin-right: 1rem;
  font-size: 0.85rem;
}

.source-stats .stat-success {
  color: #22c55e;
}

.source-stats .stat-fail {
  color: #ef4444;
}

.source-stats .stat-pending {
  color: #f59e0b;
}

.source-test-header .expand-icon {
  color: rgba(226, 232, 240, 0.6);
  font-size: 0.75rem;
}

/* 接口测试列表 */
.interface-test-list {
  padding: 0.5rem;
}

.interface-test-item {
  display: grid;
  grid-template-columns: 1fr 100px 100px auto;
  gap: 0.5rem;
  align-items: center;
  padding: 0.5rem 0.75rem;
  border-radius: 4px;
  margin-bottom: 0.25rem;
  background: rgba(15, 23, 42, 0.3);
  font-size: 0.85rem;
}

.interface-test-item:hover {
  background: rgba(15, 23, 42, 0.5);
}

.interface-test-item.success {
  border-left: 3px solid #22c55e;
}

.interface-test-item.error,
.interface-test-item.timeout {
  border-left: 3px solid #ef4444;
}

.interface-test-item.testing {
  border-left: 3px solid #6366f1;
  background: rgba(99, 102, 241, 0.1);
}

.interface-test-item.no_data {
  border-left: 3px solid #94a3b8;
}

.interface-test-item.not_implemented {
  border-left: 3px solid #f59e0b;
}

.interface-name {
  color: #e2e8f0;
  font-weight: 500;
}

.interface-category {
  color: rgba(226, 232, 240, 0.6);
  font-size: 0.75rem;
}

.interface-status {
  text-align: right;
}

.interface-status.success {
  color: #22c55e;
}

.interface-status.error,
.interface-status.timeout {
  color: #ef4444;
}

.interface-status.testing {
  color: #6366f1;
}

.interface-status.no_data {
  color: #94a3b8;
}

.interface-status.not_implemented {
  color: #f59e0b;
}

.interface-message {
  color: rgba(226, 232, 240, 0.5);
  font-size: 0.75rem;
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 测试中旋转动画 */
.testing-spinner {
  display: inline-block;
  width: 14px;
  height: 14px;
  border: 2px solid rgba(99, 102, 241, 0.3);
  border-top-color: #6366f1;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* 操作按钮 */
.interface-test-modal .modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding-top: 1rem;
  border-top: 1px solid rgba(71, 85, 105, 0.3);
}

/* 响应式 */
@media (max-width: 768px) {
  .test-overview {
    grid-template-columns: repeat(2, 1fr);
  }

  .interface-test-item {
    grid-template-columns: 1fr 80px;
  }

  .interface-category,
  .interface-message {
    display: none;
  }
}

/* ========== 移动端适配 ========== */
@media (max-width: 768px) {
  /* 主容器 */
  .dataflow-container {
    padding: 1rem;
  }

  /* 页面标题 */
  .page-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }

  .page-header h1 {
    font-size: 1.5rem;
  }

  .header-actions {
    width: 100%;
    flex-wrap: wrap;
  }

  .header-actions .btn-primary,
  .header-actions .btn-secondary {
    flex: 1;
    min-width: 100px;
    padding: 0.6rem 0.8rem;
    font-size: 0.85rem;
  }

  /* 统计卡片 */
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    margin-bottom: 1.5rem;
  }

  .stat-card {
    padding: 1rem;
    flex-direction: column;
    text-align: center;
    gap: 0.5rem;
  }

  .stat-icon {
    font-size: 1.75rem;
  }

  .stat-value {
    font-size: 1.5rem;
  }

  .stat-label {
    font-size: 0.75rem;
  }

  /* 数据源网格 */
  .data-sources-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .source-card {
    padding: 0.875rem;
  }

  /* 区块标题 */
  .section-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .section-header h2 {
    font-size: 1.25rem;
  }

  /* 过滤标签 */
  .filter-tabs {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .filter-tab {
    padding: 0.5rem 0.75rem;
    font-size: 0.8rem;
  }

  /* 股票表格 - 移动端横向滚动 */
  .stocks-table {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
  }

  .stocks-table .data-table {
    min-width: 700px;
  }

  .stocks-table th,
  .stocks-table td {
    padding: 8px 6px;
    font-size: 12px;
    white-space: nowrap;
  }

  .stocks-table .news-preview {
    max-width: 100px;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .stocks-table .action-buttons {
    flex-direction: column;
    gap: 4px;
  }

  .stocks-table .btn-small,
  .stocks-table .btn-danger-small {
    padding: 4px 8px;
    font-size: 11px;
  }

  /* 新闻列表 */
  .news-list {
    gap: 0.75rem;
  }

  .news-item {
    padding: 0.875rem;
  }

  .news-item h4 {
    font-size: 14px;
    line-height: 1.4;
  }

  .news-summary {
    font-size: 13px;
    line-height: 1.5;
  }

  .news-content {
    font-size: 13px;
    line-height: 1.5;
  }

  .news-meta {
    flex-wrap: wrap;
    gap: 0.5rem;
    font-size: 12px;
  }

  .news-source,
  .news-time,
  .news-sentiment {
    font-size: 11px;
  }

  /* 卡片通用 */
  .card {
    padding: 1rem;
    border-radius: 12px;
  }

  .section {
    margin-bottom: 1.5rem;
  }
}

/* 股票详情弹窗移动端适配 */
@media (max-width: 768px) {
  .stock-detail-modal {
    width: 100vw;
    max-width: 100vw;
    max-height: 100vh;
    border-radius: 0;
    margin: 0;
  }

  .modal-content {
    min-width: auto;
    max-width: 100%;
    padding: 1rem;
    border-radius: 0;
  }

  .modal-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .modal-header h3 {
    font-size: 1.25rem;
  }

  .modal-header .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .close-btn {
    position: absolute;
    top: 1rem;
    right: 1rem;
  }

  /* 详情概览 */
  .detail-overview {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.75rem;
    padding: 0.75rem;
  }

  .overview-item {
    gap: 0.25rem;
  }

  .overview-label {
    font-size: 0.75rem;
  }

  .sentiment-score {
    font-size: 1.25rem;
  }

  /* 详情标签页 */
  .detail-tabs {
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    gap: 0;
  }

  .detail-tabs::-webkit-scrollbar {
    display: none;
  }

  .detail-tab {
    padding: 0.6rem 1rem;
    font-size: 0.85rem;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .tab-badge {
    font-size: 0.65rem;
    padding: 0.1rem 0.4rem;
  }

  /* 详情内容 */
  .detail-content {
    min-height: 300px;
    max-height: calc(100vh - 280px);
  }

  /* 基础信息面板 - 移动端字体修复 */
  .data-panel h4 {
    font-size: 14px;
  }

  .info-grid-2col {
    grid-template-columns: 1fr;
    gap: 8px;
    font-size: 13px;
  }

  .info-grid-2col .label {
    font-size: 12px;
  }

  .company-intro {
    font-size: 13px;
    line-height: 1.5;
  }

  .info-grid-3col {
    grid-template-columns: 1fr 1fr;
    gap: 8px;
  }

  .info-card {
    padding: 10px;
  }

  .info-card .value {
    font-size: 16px;
  }

  .info-card .label {
    font-size: 11px;
  }

  /* 过滤栏 */
  .filter-bar {
    gap: 0.4rem;
  }

  .filter-btn {
    padding: 0.4rem 0.75rem;
    font-size: 0.75rem;
  }

  /* 新闻详情列表 */
  .news-detail-item {
    padding: 0.875rem;
  }

  .news-detail-header h4 {
    font-size: 0.95rem;
  }

  .news-detail-footer {
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  /* 风险概览 */
  .risk-overview-section {
    grid-template-columns: 1fr;
    gap: 1rem;
  }

  .risk-score-display {
    padding: 1rem 0;
  }

  .score-circle {
    width: 100px;
    height: 100px;
  }

  .score-number {
    font-size: 2rem;
  }

  .risk-level-label {
    font-size: 1rem;
    padding: 0.4rem 1rem;
  }

  /* 风险卡片 */
  .risk-cards-side {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  /* 图表 */
  .chart-container {
    height: 200px;
    min-height: 180px;
  }

  .radar-chart {
    height: 220px;
  }

  .radar-chart-box {
    height: 200px;
  }
}

/* 通知设置弹窗移动端适配 */
@media (max-width: 768px) {
  .notification-settings-modal {
    width: 100vw;
    max-width: 100vw;
    max-height: 100vh;
    border-radius: 0;
  }

  .notification-content {
    padding: 0.5rem 0;
  }

  .notification-section {
    margin-bottom: 1.5rem;
  }

  .notification-section h4 {
    font-size: 0.9rem;
  }

  .channels-grid {
    grid-template-columns: 1fr;
    gap: 0.75rem;
  }

  .channel-card {
    padding: 0.875rem;
    flex-direction: row;
    justify-content: space-between;
  }

  .channel-icon {
    font-size: 1.5rem;
  }

  .channel-info {
    text-align: left;
    flex: 1;
    margin-left: 0.75rem;
  }

  /* 配置表单 */
  .config-form {
    padding: 0.875rem;
  }

  .form-row {
    flex-direction: column;
    gap: 0.75rem;
  }

  .config-form .form-group-small {
    flex: 1;
  }

  .test-notification {
    flex-direction: column;
    gap: 0.75rem;
  }

  .config-actions {
    flex-direction: column;
    gap: 0.75rem;
  }

  .config-actions .btn-primary,
  .config-actions .btn-secondary {
    width: 100%;
  }

  /* 配置指南 */
  .guide-header {
    padding: 0.6rem 0.875rem;
    font-size: 0.9rem;
  }

  .guide-content {
    padding: 0.875rem;
  }

  .guide-content p {
    font-size: 0.85rem;
  }

  .env-var code {
    font-size: 0.75rem;
    word-break: break-all;
  }
}

/* 接口测试弹窗移动端适配 */
@media (max-width: 768px) {
  .interface-test-modal {
    width: 100vw;
    max-width: 100vw;
    max-height: 100vh;
    border-radius: 0;
  }

  .interface-test-modal .modal-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 0.75rem;
  }

  .interface-test-modal .header-actions {
    width: 100%;
    justify-content: space-between;
  }

  .test-overview {
    grid-template-columns: repeat(2, 1fr);
    gap: 0.5rem;
    padding: 0.75rem 0;
  }

  .overview-stat {
    padding: 0.5rem;
  }

  .overview-stat .stat-icon {
    font-size: 1.25rem;
  }

  .overview-stat .stat-label {
    font-size: 0.65rem;
  }

  .overview-stat .stat-value {
    font-size: 1rem;
  }

  /* 数据源测试区块 */
  .source-test-header {
    padding: 0.6rem 0.75rem;
    flex-wrap: wrap;
  }

  .source-test-header .source-name {
    font-size: 0.9rem;
  }

  .source-test-header .source-stats {
    font-size: 0.75rem;
    gap: 0.5rem;
  }

  /* 接口测试列表 */
  .interface-test-list {
    padding: 0.25rem;
  }

  .interface-test-item {
    grid-template-columns: 1fr auto;
    padding: 0.4rem 0.5rem;
    font-size: 0.8rem;
  }

  .interface-name {
    font-size: 0.8rem;
  }

  .interface-test-modal .modal-actions {
    flex-direction: column;
    gap: 0.5rem;
  }

  .interface-test-modal .modal-actions button {
    width: 100%;
  }
}

/* 添加监控弹窗移动端适配 */
@media (max-width: 768px) {
  .modal-overlay .modal-content {
    width: calc(100vw - 2rem);
    min-width: auto;
    max-width: calc(100vw - 2rem);
    padding: 1.25rem;
    margin: 1rem;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  .form-group label {
    font-size: 0.9rem;
  }

  .input-field {
    padding: 0.6rem;
    font-size: 0.9rem;
  }

  .checkbox-group {
    gap: 0.4rem;
  }

  .checkbox-group label {
    font-size: 0.85rem;
  }

  .modal-actions {
    flex-direction: column;
    gap: 0.75rem;
  }

  .modal-actions button {
    width: 100%;
    padding: 0.75rem;
  }
}

/* 超小屏幕适配 (< 480px) */
@media (max-width: 480px) {
  .dataflow-container {
    padding: 0.75rem;
  }

  .page-header h1 {
    font-size: 1.25rem;
  }

  .subtitle {
    font-size: 0.8rem;
  }

  .stats-grid {
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }

  .stat-card {
    padding: 0.75rem;
  }

  .stat-icon {
    font-size: 1.5rem;
  }

  .stat-value {
    font-size: 1.25rem;
  }

  .stat-label {
    font-size: 0.7rem;
  }

  .section-header h2 {
    font-size: 1.1rem;
  }

  .detail-overview {
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
  }

  .score-circle {
    width: 80px;
    height: 80px;
  }

  .score-number {
    font-size: 1.5rem;
  }

  .test-overview {
    grid-template-columns: 1fr 1fr;
  }
}

/* Toast通知移动端适配 */
@media (max-width: 768px) {
  .toast-container {
    top: auto;
    bottom: 20px;
    right: 10px;
    left: 10px;
  }

  .toast {
    min-width: auto;
    max-width: 100%;
    padding: 10px 15px;
    font-size: 0.85rem;
  }
}
</style>
