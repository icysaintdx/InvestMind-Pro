<template>
  <div class="changelog-page">
    <div class="page-header">
      <div class="header-content">
        <h1 class="page-title">
          <span class="title-icon">🚀</span>
          更新日志
        </h1>
        <div class="version-badge">
          <span class="badge-label">当前版本</span>
          <span class="badge-version">v{{ currentVersion }}</span>
          <span class="badge-codename">{{ codename }}</span>
        </div>
      </div>
      <p class="page-subtitle">追踪 InvestMind Pro 的每一步进化</p>
    </div>
    
    <div class="changelog-container">
      <div v-for="version in versions" :key="version.version" class="version-block">
        <div class="version-header">
          <div class="version-info">
            <h2 class="version-number">v{{ version.version }}</h2>
            <span class="version-codename">{{ version.codename }}</span>
            <span class="version-date">{{ formatDate(version.date) }}</span>
          </div>
          <div v-if="version.version === currentVersion" class="current-badge">
            当前版本
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
        <div v-if="version.bugs && version.bugs.length" class="section">
          <h3 class="section-title">
            <span class="section-icon">🐛</span>
            问题修复
          </h3>
          <div v-for="(bug, idx) in version.bugs" :key="idx" class="item">
            <div class="item-header">
              <span class="item-icon">{{ bug.icon || '🔧' }}</span>
              <h4 class="item-title">{{ bug.title }}</h4>
            </div>
            <p v-if="bug.description" class="item-description">{{ bug.description }}</p>
            <ul v-if="bug.details" class="item-details">
              <li v-for="(detail, dIdx) in bug.details" :key="dIdx">{{ detail }}</li>
            </ul>
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
              <a :href="doc.link" class="doc-link">
                {{ doc.name || doc.title }}
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
// 导入统一的更新日志数据
import { CURRENT_VERSION, CURRENT_CODENAME, getAllVersions } from '../data/changelog.js'

export default {
  name: 'ChangelogView',
  data() {
    return {
      currentVersion: CURRENT_VERSION,
      codename: CURRENT_CODENAME,
      versions: getAllVersions()
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
  color: #60a5fa;
}

.item-files {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-top: 1rem;
  flex-wrap: wrap;
}

.files-label {
  font-size: 0.875rem;
  color: #64748b;
  font-weight: 500;
}

.file-tag {
  padding: 0.25rem 0.5rem;
  background: rgba(59, 130, 246, 0.1);
  color: #60a5fa;
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
  transition: all 0.2s;
}

.doc-link:hover {
  color: #93c5fd;
  transform: translateX(4px);
}
</style>
