<template>
  <div class="document-view">
    <!-- 固定表头 -->
    <div class="doc-header-fixed">
      <h1 class="doc-title">
        <span class="title-icon">📚</span>
        InvestMind Pro 文档中心
      </h1>
      <p class="doc-subtitle">核心逻辑、算法与智能体提示词完整文档</p>
    </div>

    <!-- 可滚动内容区 -->
    <div class="doc-container">
      <!-- 移动端侧边栏切换按钮 -->
      <button 
        class="mobile-sidebar-toggle"
        @click="sidebarOpen = !sidebarOpen"
        :class="{ 'sidebar-open': sidebarOpen }"
      >
        <span class="toggle-icon">{{ sidebarOpen ? '◀' : '▶' }}</span>
        <span class="toggle-text">目录</span>
      </button>
      
      <!-- 左侧文档列表 -->
      <div class="doc-sidebar" :class="{ 'mobile-open': sidebarOpen }">
        <div class="sidebar-header">
          <span class="header-icon">📑</span>
          <span class="header-text">文档目录</span>
        </div>
        
        <div class="doc-categories">
          <div v-if="loading" class="loading-state">
            <div class="loading-spinner">⏳</div>
            <div class="loading-text">加载文档列表...</div>
          </div>
          
          <div v-else-if="error" class="error-state">
            <div class="error-icon">❌</div>
            <div class="error-text">{{ error }}</div>
          </div>
          
          <div v-else class="doc-category" v-for="category in categories" :key="category.name">
            <div class="category-title">
              <span class="category-icon">{{ category.icon }}</span>
              {{ category.name }}
            </div>
            <div class="doc-list">
              <div
                v-for="doc in category.docs"
                :key="doc.path"
                :class="['doc-item', { active: currentDoc?.path === doc.path }]"
                @click="loadDocument(doc)"
              >
                <span class="doc-icon">{{ doc.icon }}</span>
                <span class="doc-name">{{ doc.name }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧文档内容 -->
      <div class="doc-content">
        <div v-if="!currentDoc" class="doc-empty">
          <div class="empty-icon">📄</div>
          <div class="empty-text">请从左侧选择要查看的文档</div>
        </div>
        
        <div v-else-if="loadingContent" class="doc-loading">
          <div class="loading-spinner">⏳</div>
          <div class="loading-text">加载文档内容...</div>
        </div>
        
        <div v-else class="doc-viewer">
          <div class="viewer-header">
            <div class="viewer-title">
              <span class="title-icon">{{ currentDoc.icon }}</span>
              <span class="title-text">{{ currentDoc.name }}</span>
            </div>
          </div>
          <div class="viewer-body" v-html="renderedContent"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { marked } from 'marked'
import axios from 'axios'

export default {
  name: 'DocumentView',
  setup() {
    const currentDoc = ref(null)
    const categories = ref([])
    const loading = ref(true)
    const loadingContent = ref(false)
    const error = ref(null)
    const documentContent = ref('')
    const sidebarOpen = ref(false)

    // 文档分类配置
    const categoryConfig = [
      {
        name: '智能体提示词',
        icon: '🤖',
        pattern: /智能体提示词/,
        defaultIcon: '📰'
      },
      {
        name: '核心逻辑与算法',
        icon: '⚙️',
        pattern: /核心逻辑与算法/,
        defaultIcon: '🔍'
      },
      {
        name: '项目介绍',
        icon: '📖',
        pattern: /项目介绍/,
        defaultIcon: '📄'
      }
    ]

    // 获取文档图标
    const getDocIcon = (filename) => {
      if (filename.includes('第1部分')) return '📰'
      if (filename.includes('第2部分')) return '🛡️'
      if (filename.includes('第3部分')) return '💹'
      if (filename.includes('概述')) return '🏆'
      if (filename.includes('智能体详解')) return '🎯'
      if (filename.includes('功能清单')) return '✨'
      if (filename.includes('技术亮点')) return '💡'
      if (filename.includes('总目录')) return '📑'
      return '📄'
    }

    // 加载文档列表
    const loadDocumentList = async () => {
      try {
        loading.value = true
        error.value = null
        
        // 调用后端API获取docs目录的文件列表
        const response = await axios.get('/api/documents/list')
        
        if (response.data && response.data.files) {
          const allFiles = response.data.files
          const categorizedFiles = new Set()
          
          // 按预定义分类组织文档
          const categorizedDocs = categoryConfig.map(cat => {
            const docs = allFiles
              .filter(file => cat.pattern.test(file))
              .map(file => {
                categorizedFiles.add(file)
                return {
                  name: file.replace(/^项目介绍-/, '').replace(/\.md$/, ''),
                  path: file,
                  icon: getDocIcon(file)
                }
              })
            
            return {
              name: cat.name,
              icon: cat.icon,
              docs: docs
            }
          }).filter(cat => cat.docs.length > 0)
          
          // 收集未分类的文档
          const uncategorizedDocs = allFiles
            .filter(file => !categorizedFiles.has(file))
            .map(file => ({
              name: file.replace(/\.md$/, ''),
              path: file,
              icon: '📄'
            }))
          
          // 如果有未分类的文档，添加"其他文档"分类
          if (uncategorizedDocs.length > 0) {
            categorizedDocs.push({
              name: '其他文档',
              icon: '📁',
              docs: uncategorizedDocs
            })
          }
          
          categories.value = categorizedDocs
          
          console.log(`✅ 加载了 ${allFiles.length} 个文档，分为 ${categorizedDocs.length} 个分类`)
        }
      } catch (err) {
        console.error('加载文档列表失败:', err)
        error.value = '无法加载文档列表，请确保后端服务正常运行'
      } finally {
        loading.value = false
      }
    }

    // 加载文档内容
    const loadDocument = async (doc) => {
      try {
        loadingContent.value = true
        currentDoc.value = doc
        documentContent.value = ''
        
        // 移动端自动关闭侧边栏
        if (window.innerWidth <= 768) {
          sidebarOpen.value = false
        }
        
        // 调用后端API读取文档内容
        const response = await axios.get(`/api/documents/read/${doc.path}`)
        
        if (response.data && response.data.content) {
          documentContent.value = response.data.content
        }
      } catch (err) {
        console.error('加载文档内容失败:', err)
        documentContent.value = `# 加载失败\n\n无法加载文档内容: ${err.message}`
      } finally {
        loadingContent.value = false
      }
    }

    // 渲染Markdown内容
    const renderedContent = computed(() => {
      if (!documentContent.value) return ''
      try {
        return marked(documentContent.value)
      } catch (error) {
        console.error('Markdown渲染错误:', error)
        return `<pre style="white-space: pre-wrap; word-wrap: break-word;">${documentContent.value}</pre>`
      }
    })

    // 组件挂载时加载文档列表
    onMounted(() => {
      loadDocumentList()
    })

    return {
      currentDoc,
      categories,
      loading,
      loadingContent,
      error,
      loadDocument,
      renderedContent,
      sidebarOpen
    }
  }
}
</script>

<style scoped>
.document-view {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
  overflow: hidden;
}

/* 固定表头 */
.doc-header-fixed {
  flex-shrink: 0;
  text-align: center;
  padding: 0rem 2rem 0rem;
  background: rgba(15, 23, 42, 0.95);
  border-bottom: 2px solid rgba(59, 130, 246, 0.3);
}

.doc-title {
  font-size: 2rem;
  font-weight: 700;
  color: white;
  margin-bottom: 0.5rem;
}

.title-icon {
  margin-right: 0.75rem;
}

.doc-subtitle {
  font-size: 1rem;
  color: #94a3b8;
}

.doc-container {
  flex: 1;
  display: grid;
  grid-template-columns: 350px 1fr;
  gap: 0;
  width: 100%;
  overflow: hidden;
}

.doc-sidebar {
  width: 350px;
  background: rgba(15, 23, 42, 0.95);
  border-right: 1px solid rgba(51, 65, 85, 0.5);
  padding: 1.5rem;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 1.125rem;
  font-weight: 600;
  color: white;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 2px solid rgba(59, 130, 246, 0.3);
}

.doc-category {
  margin-bottom: 1.5rem;
}

.category-title {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.875rem;
  font-weight: 600;
  color: #60a5fa;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
}

.doc-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.doc-item {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  background: rgba(30, 41, 59, 0.5);
  border: 1px solid transparent;
  border-radius: 8px;
  color: #cbd5e1;
  font-size: 0.875rem;
  cursor: pointer;
  transition: all 0.2s;
}

.doc-item:hover {
  background: rgba(51, 65, 85, 0.5);
  border-color: #3b82f6;
  color: white;
  transform: translateX(4px);
}

.doc-item.active {
  background: linear-gradient(135deg, rgba(59, 130, 246, 0.2), rgba(16, 185, 129, 0.2));
  border-color: #3b82f6;
  color: white;
}

.doc-content {
  flex: 1;
  background: rgba(15, 23, 42, 0.9);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.doc-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  background: rgba(30, 41, 59, 0.3);
  border: 2px dashed rgba(100, 116, 139, 0.3);
  border-radius: 12px;
  margin: 2rem;
  color: #64748b;
}

.empty-icon {
  font-size: 4rem;
  margin-bottom: 1rem;
}

.empty-text {
  font-size: 1.125rem;
}

.doc-viewer {
  color: #e2e8f0;
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
  overflow: hidden;
}

.viewer-header {
  flex-shrink: 0;
  padding: 1.5rem 2rem;
  background: rgba(15, 23, 42, 0.95);
  border-bottom: 2px solid rgba(59, 130, 246, 0.3);
}

.viewer-title {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  font-size: 1.5rem;
  font-weight: 700;
  color: white;
}

.viewer-body {
  flex: 1;
  padding: 2rem;
  overflow-y: auto;
  overflow-x: hidden;
  line-height: 1.8;
  min-height: 0;
}

/* 滚动条美化 */
.doc-sidebar::-webkit-scrollbar,
.viewer-body::-webkit-scrollbar {
  width: 8px;
}

.doc-sidebar::-webkit-scrollbar-track,
.viewer-body::-webkit-scrollbar-track {
  background: rgba(15, 23, 42, 0.5);
}

.doc-sidebar::-webkit-scrollbar-thumb,
.viewer-body::-webkit-scrollbar-thumb {
  background: rgba(59, 130, 246, 0.6);
  border-radius: 4px;
}

.doc-sidebar::-webkit-scrollbar-thumb:hover,
.viewer-body::-webkit-scrollbar-thumb:hover {
  background: rgba(59, 130, 246, 0.9);
}

/* 加载状态 */
.loading-state,
.error-state,
.doc-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 3rem;
  color: #94a3b8;
}

.loading-spinner,
.error-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  animation: pulse 2s ease-in-out infinite;
}

.loading-text,
.error-text {
  font-size: 1rem;
  text-align: center;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.viewer-body :deep(h1) {
  font-size: 1.75rem;
  font-weight: 700;
  color: white;
  margin: 1.5rem 0 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 2px solid rgba(59, 130, 246, 0.3);
}

.viewer-body :deep(h2) {
  font-size: 1.35rem;
  font-weight: 600;
  color: #60a5fa;
  margin: 1.25rem 0 0.75rem;
}

.viewer-body :deep(h3) {
  font-size: 1.15rem;
  font-weight: 600;
  color: #10b981;
  margin: 1rem 0 0.5rem;
}

.viewer-body :deep(p) {
  margin: 1rem 0;
  color: #cbd5e1;
}

.viewer-body :deep(code) {
  background: rgba(30, 41, 59, 0.8);
  padding: 0.25rem 0.5rem;
  border-radius: 4px;
  font-family: 'Consolas', monospace;
  font-size: 0.875rem;
  color: #10b981;
}

.viewer-body :deep(pre) {
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(51, 65, 85, 0.5);
  border-radius: 8px;
  padding: 1.5rem;
  overflow-x: auto;
  margin: 1.5rem 0;
}

.viewer-body :deep(pre code) {
  background: none;
  padding: 0;
  color: #e2e8f0;
}

.viewer-body :deep(table) {
  width: 100%;
  border-collapse: collapse;
  margin: 1.5rem 0;
}

.viewer-body :deep(th),
.viewer-body :deep(td) {
  border: 1px solid rgba(51, 65, 85, 0.5);
  padding: 0.75rem;
  text-align: left;
}

.viewer-body :deep(th) {
  background: rgba(59, 130, 246, 0.2);
  color: white;
  font-weight: 600;
}

.viewer-body :deep(tr:hover) {
  background: rgba(51, 65, 85, 0.3);
}

.viewer-body :deep(ul),
.viewer-body :deep(ol) {
  margin: 1rem 0;
  padding-left: 2rem;
}

.viewer-body :deep(li) {
  margin: 0.5rem 0;
  color: #cbd5e1;
}

.viewer-body :deep(blockquote) {
  border-left: 4px solid #3b82f6;
  padding-left: 1rem;
  margin: 1.5rem 0;
  color: #94a3b8;
  font-style: italic;
}

.viewer-body :deep(hr) {
  border: none;
  border-top: 1px solid rgba(51, 65, 85, 0.5);
  margin: 2rem 0;
}

/* 移动端侧边栏切换按钮 */
.mobile-sidebar-toggle {
  display: none;
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .doc-header-fixed {
    padding: 0.75rem 1rem;
  }
  
  .doc-title {
    font-size: 1.125rem;
  }
  
  .doc-subtitle {
    font-size: 0.75rem;
  }
  
  .mobile-sidebar-toggle {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.25rem;
    position: fixed;
    top: 6rem;
    left: 0.5rem;
    padding: 0.5rem 0.375rem;
    background: rgba(15, 23, 42, 0.98);
    border: 1px solid rgba(59, 130, 246, 0.6);
    border-radius: 0.375rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
    z-index: 1100;
    cursor: pointer;
    transition: all 0.3s ease;
  }
  
  .mobile-sidebar-toggle:hover {
    background: rgba(59, 130, 246, 0.3);
    border-color: rgba(59, 130, 246, 0.8);
  }
  
  .mobile-sidebar-toggle .toggle-icon {
    font-size: 1rem;
    color: #60a5fa;
  }
  
  .mobile-sidebar-toggle .toggle-text {
    font-size: 0.625rem;
    color: #94a3b8;
    writing-mode: vertical-rl;
  }
  
  .mobile-sidebar-toggle.sidebar-open .toggle-icon {
    color: #10b981;
  }
  
  .doc-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    bottom: 0;
    width: 80vw;
    max-width: 300px;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    z-index: 1090;
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.3);
  }
  
  .doc-sidebar.mobile-open {
    transform: translateX(0);
  }
  
  .doc-content {
    width: 100%;
    margin-left: 0;
    padding: 0.5rem;
  }
  
  .doc-viewer {
    padding: 0;
  }
  
  .viewer-body {
    padding: 1rem 0.5rem;
  }
}
</style>
