<template>
  <div class="changelog-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-icon">📋</span>
          更新日志
        </h1>
        <div class="version-badge">
          <span class="badge-label">当前版本</span>
          <span class="badge-version">v{{ currentVersion }}</span>
          <span class="badge-codename">{{ codename }}</span>
        </div>
      </div>
      <p class="page-subtitle">记录 InvestMind Pro 的每一次进化</p>
    </div>

    <div class="changelog-container">
      <!-- 版本列表 -->
      <div v-for="version in versions" :key="version.version" class="version-block">
        <div class="version-header">
          <div class="version-info">
            <h2 class="version-number">v{{ version.version }}</h2>
            <span class="version-codename">{{ version.codename }}</span>
            <span class="version-date">{{ formatDate(version.date) }}</span>
          </div>
          <div v-if="version.version === currentVersion" class="current-badge">
            <span>当前版本</span>
          </div>
        </div>

        <!-- 新增功能 -->
        <div v-if="version.features && version.features.length" class="section">
          <h3 class="section-title">
            <span class="section-icon">🆕</span>
            新增功能
          </h3>
          <div v-for="(feature, idx) in version.features" :key="idx" class="item">
            <div class="item-header">
              <span class="item-icon">{{ feature.icon }}</span>
              <h4 class="item-title">{{ feature.title }}</h4>
              <span v-if="feature.star" class="star-badge">⭐</span>
            </div>
            <p class="item-description">{{ feature.description }}</p>
            <ul v-if="feature.details" class="item-details">
              <li v-for="(detail, dIdx) in feature.details" :key="dIdx">{{ detail }}</li>
            </ul>
            <div v-if="feature.files" class="item-files">
              <span class="files-label">相关文件:</span>
              <code v-for="(file, fIdx) in feature.files" :key="fIdx" class="file-tag">{{ file }}</code>
            </div>
          </div>
        </div>

        <!-- Bug 修复 -->
        <div v-if="version.bugfixes && version.bugfixes.length" class="section">
          <h3 class="section-title">
            <span class="section-icon">🐛</span>
            Bug 修复
          </h3>
          <div v-for="(bug, idx) in version.bugfixes" :key="idx" class="item">
            <div class="item-header">
              <span class="item-icon">{{ bug.icon }}</span>
              <h4 class="item-title">{{ bug.title }}</h4>
            </div>
            <p class="item-description"><strong>问题:</strong> {{ bug.problem }}</p>
            <p class="item-description"><strong>修复:</strong> {{ bug.fix }}</p>
            <div v-if="bug.files" class="item-files">
              <span class="files-label">相关文件:</span>
              <code v-for="(file, fIdx) in bug.files" :key="fIdx" class="file-tag">{{ file }}</code>
            </div>
          </div>
        </div>

        <!-- 文档更新 -->
        <div v-if="version.docs && version.docs.length" class="section">
          <h3 class="section-title">
            <span class="section-icon">📚</span>
            文档更新
          </h3>
          <ul class="docs-list">
            <li v-for="(doc, idx) in version.docs" :key="idx">
              <a :href="doc.link" target="_blank" class="doc-link">
                {{ doc.name }}
                <span v-if="doc.star" class="star-badge">⭐</span>
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ChangelogView',
  data() {
    return {
      currentVersion: '1.2.0',
      codename: '配置优化版',
      versions: [
        {
          version: '1.2.0',
          codename: '配置优化版',
          date: '2025-12-04T00:10:00',
          features: [
            {
              icon: '🔑',
              title: 'API 配置系统全面优化',
              star: true,
              description: '重构 API 配置模态框，支持自动加载、真实测试和数据渠道管理。',
              details: [
                '自动加载: 打开模态框自动从后端加载配置，无需手动点击',
                '真实测试: 测试按钮调用真实 API，返回详细响应示例',
                '滚动优化: 状态栏和按钮固定，配置项可滚动，主页面滚动禁用',
                '数据渠道: 支持聚合数据、FinnHub、Tushare、AKShare 等数据源配置'
              ],
              files: ['ApiConfig.vue', 'App.vue', 'server.py']
            },
            {
              icon: '📊',
              title: '顶部状态栏扩展',
              star: true,
              description: '扩展顶部状态栏，分组显示 AI API 和数据渠道状态。',
              details: [
                '分组显示: API 和数据分组，使用分隔符区分',
                '实时状态: 显示各个服务的连接状态（已配置/未配置/错误）',
                '悬停提示: 鼠标悬停显示完整名称'
              ],
              files: ['App.vue']
            },
            {
              icon: 'ℹ️',
              title: 'Agent 说明优化',
              description: 'Agent 卡片的信息图标使用原生浏览器 tooltip。',
              details: [
                '简单可靠: 使用 HTML title 属性，无需复杂实现',
                '悬停显示: 鼠标悬停即显示，移开自动消失',
                '详细说明: 包含每个 Agent 的工作原理和专业范畴'
              ],
              files: ['AgentCard.vue']
            }
          ],
          bugfixes: [
            {
              icon: '🔧',
              title: 'API 配置加载修复',
              problem: '打开配置模态框时不显示已保存的配置',
              fix: '后端返回实际的 API Keys，前端正确加载和显示',
              files: ['server.py', 'ApiConfig.vue']
            },
            {
              icon: '📜',
              title: '模态框滚动体验修复',
              problem: '滚动配置项时，底部按钮也会滚动消失；主页面也会滚动',
              fix: '状态栏和按钮固定，打开模态框时禁用主页面滚动',
              files: ['ApiConfig.vue']
            },
            {
              icon: '🔑',
              title: '数据渠道配置支持',
              problem: 'FinnHub 和 Tushare 配置不显示，测试按钮无效',
              fix: '添加 finnhub 和 tushare 到 API_KEYS，支持环境变量读取',
              files: ['server.py']
            }
          ],
          docs: [
            { name: 'API配置与状态栏优化完成报告.md', link: '#', star: true },
            { name: 'UI优化完成报告.md', link: '#', star: true },
            { name: 'UI问题修复报告.md', link: '#', star: true }
          ]
        },
        {
          version: '1.1.0',
          codename: '智能拟真版',
          date: '2025-12-03T23:00:00',
          features: [
            {
              icon: '🤖',
              title: '全流程拟真分析系统',
              star: true,
              description: '重构了投资分析的全流程，引入了21个专业分工的智能体。',
              details: [
                '流水线协同: 实现 Step 1.1 (情报) -> Step 1.2 (中观) -> Step 1.3 (深度) 的层级依赖执行',
                '动态指令: 后端支持接收前端注入的 custom_instruction',
                '智能回退: 当后端数据源不可用时，自动切换至高保真模拟数据',
                '去模板化: 强制智能体不复述基础行情，直接输出专业结论'
              ],
              files: ['AnalysisView.vue', 'server.py']
            },
            {
              icon: '🧠',
              title: '可视化思维链 (CoT)',
              star: true,
              description: '为不同角色的智能体定制了专属的思考步骤展示。',
              details: [
                '新闻分析师显示"爬取公告"',
                '技术分析师显示"计算MACD"',
                '增强专业感'
              ],
              files: ['AgentCard.vue']
            }
          ],
          bugfixes: [
            {
              icon: '🔌',
              title: '数据源连接修复',
              problem: '后端 API 连接不稳定导致分析中断',
              fix: '增加了数据验证层和模拟数据兜底机制',
              files: ['server.py']
            }
          ],
          docs: [
            { name: '前端重构完成报告.md', link: '#', star: true }
          ]
        }
      ]
    }
  },
  methods: {
    formatDate(dateString) {
      const date = new Date(dateString)
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
  }
}
</script>

<style scoped>
.changelog-page {
  min-height: 100vh;
  padding: 2rem;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
}

.page-header {
  max-width: 1200px;
  margin: 0 auto 3rem;
  text-align: center;
}

.header-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rem;
  margin-bottom: 1rem;
}

.page-title {
  font-size: 2.5rem;
  font-weight: bold;
  color: white;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin: 0;
}

.title-icon {
  font-size: 2.5rem;
}

.version-badge {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(59, 130, 246, 0.2);
  border: 1px solid #3b82f6;
  border-radius: 0.5rem;
}

.badge-label {
  font-size: 0.75rem;
  color: #94a3b8;
}

.badge-version {
  font-size: 1.25rem;
  font-weight: bold;
  color: #60a5fa;
}

.badge-codename {
  font-size: 0.875rem;
  color: #e2e8f0;
}

.page-subtitle {
  font-size: 1.125rem;
  color: #94a3b8;
  margin: 0;
}

.changelog-container {
  max-width: 1200px;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 3rem;
}

.version-block {
  background: #1e293b;
  border: 1px solid #334155;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
}

.version-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 2rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid #334155;
}

.version-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.version-number {
  font-size: 2rem;
  font-weight: bold;
  color: #60a5fa;
  margin: 0;
}

.version-codename {
  padding: 0.25rem 0.75rem;
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  border-radius: 0.375rem;
  font-size: 0.875rem;
  font-weight: 500;
}

.version-date {
  color: #94a3b8;
  font-size: 0.875rem;
}

.current-badge {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #3b82f6, #8b5cf6);
  color: white;
  border-radius: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  box-shadow: 0 2px 4px rgba(59, 130, 246, 0.3);
}

.section {
  margin-bottom: 2rem;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: #e2e8f0;
  margin-bottom: 1rem;
}

.section-icon {
  font-size: 1.5rem;
}

.item {
  background: #0f172a;
  border: 1px solid #334155;
  border-radius: 0.75rem;
  padding: 1.5rem;
  margin-bottom: 1rem;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
}

.item-icon {
  font-size: 1.5rem;
}

.item-title {
  font-size: 1.125rem;
  font-weight: 600;
  color: #e2e8f0;
  margin: 0;
}

.star-badge {
  font-size: 1rem;
}

.item-description {
  color: #cbd5e1;
  line-height: 1.6;
  margin-bottom: 0.75rem;
}

.item-details {
  list-style: none;
  padding: 0;
  margin: 0.75rem 0;
}

.item-details li {
  padding: 0.5rem 0 0.5rem 1.5rem;
  color: #94a3b8;
  position: relative;
}

.item-details li::before {
  content: '▸';
  position: absolute;
  left: 0;
  color: #3b82f6;
}

.item-files {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.5rem;
  margin-top: 0.75rem;
}

.files-label {
  font-size: 0.75rem;
  color: #64748b;
  font-weight: 500;
}

.file-tag {
  padding: 0.25rem 0.5rem;
  background: rgba(100, 116, 139, 0.2);
  color: #94a3b8;
  border-radius: 0.25rem;
  font-size: 0.75rem;
  font-family: 'Consolas', monospace;
}

.docs-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.docs-list li {
  padding: 0.5rem 0;
}

.doc-link {
  color: #60a5fa;
  text-decoration: none;
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  transition: color 0.2s;
}

.doc-link:hover {
  color: #93c5fd;
  text-decoration: underline;
}
</style>
