<template>
  <div class="analysis-container">
    <!-- 股票输入区 -->
    <div class="input-section">
      <div class="input-card">
        <h2 class="text-2xl font-bold text-white mb-6">📈 智能投研分析系统</h2>
        
        <div class="input-group">
          <label class="input-label">股票代码</label>
          <input 
            v-model="stockCode"
            type="text" 
            placeholder="请输入6位股票代码"
            maxlength="6"
            class="stock-input"
            @keyup.enter="startAnalysis"
          />
        </div>

        <button 
          @click="startAnalysis"
          :disabled="isAnalyzing || !isValidCode"
          class="analyze-btn"
        >
          <span v-if="!isAnalyzing">🚀 开始分析</span>
          <span v-else class="flex items-center">
            <span class="spinner"></span>
            分析中...
          </span>
        </button>
      </div>
    </div>

    <!-- 智能体网格 - 按4个阶段分组显示 -->
    <div class="agents-container space-y-8">
      <!-- 第一阶段：分析师团队 -->
      <div>
        <h3 class="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <span class="text-2xl">📊</span>
          <span>第一阶段 - 并行专业分析</span>
        </h3>
        <div class="stage1-grid">
          <AgentCard 
            v-for="agent in stage1Agents" 
            :key="agent.id"
            :agent="agent"
            :status="agentStatus[agent.id] || 'idle'"
            :output="agentOutputs[agent.id]"
            :tokens="agentTokens[agent.id]"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
          />
        </div>
      </div>

      <!-- 第二阶段：经理团队 -->
      <div>
        <h3 class="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <span class="text-2xl">👔</span>
          <span>第二阶段 - 策略整合</span>
        </h3>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <AgentCard 
            v-for="agent in stage2Agents" 
            :key="agent.id"
            :agent="agent"
            :status="agentStatus[agent.id] || 'idle'"
            :output="agentOutputs[agent.id]"
            :tokens="agentTokens[agent.id]"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
          />
        </div>
      </div>

      <!-- 第三阶段：风控团队 -->
      <div>
        <h3 class="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <span class="text-2xl">⚠️</span>
          <span>第三阶段 - 风控评估</span>
        </h3>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <AgentCard 
            v-for="agent in stage3Agents" 
            :key="agent.id"
            :agent="agent"
            :status="agentStatus[agent.id] || 'idle'"
            :output="agentOutputs[agent.id]"
            :tokens="agentTokens[agent.id]"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
          />
        </div>
      </div>

      <!-- 第四阶段：总经理决策 -->
      <div>
        <h3 class="text-lg font-semibold text-slate-300 mb-4 flex items-center gap-2">
          <span class="text-2xl">👑</span>
          <span>第四阶段 - 最终决策</span>
        </h3>
        <div class="grid grid-cols-1 gap-4">
          <AgentCard 
            v-for="agent in stage4Agents" 
            :key="agent.id"
            :agent="agent"
            :status="agentStatus[agent.id] || 'idle'"
            :output="agentOutputs[agent.id]"
            :tokens="agentTokens[agent.id]"
            :show-config="configMode"
            :model-update-trigger="modelUpdateTrigger"
          />
        </div>
      </div>

      <!-- 综合分析报告 -->
      <div v-if="showReport" class="mt-6">
        <div class="bg-slate-800/50 backdrop-blur-sm rounded-2xl p-6 border border-slate-700">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-2xl font-bold text-white flex items-center gap-2">
              <span>📊</span>
              <span>综合分析报告</span>
            </h2>
            <div class="flex gap-2">
              <button 
                @click="exportReport('md')" 
                class="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm flex items-center gap-1.5 transition-colors"
                title="导出 Markdown"
              >
                <span>📝</span> MD
              </button>
              <button 
                @click="exportReport('html')" 
                class="px-3 py-1.5 bg-green-600 hover:bg-green-700 text-white rounded-lg text-sm flex items-center gap-1.5 transition-colors"
                title="导出 HTML"
              >
                <span>🌐</span> HTML
              </button>
              <button 
                @click="exportReport('pdf')" 
                class="px-3 py-1.5 bg-purple-600 hover:bg-purple-700 text-white rounded-lg text-sm flex items-center gap-1.5 transition-colors"
                title="导出 PDF"
              >
                <span>📄</span> PDF
              </button>
            </div>
          </div>
          <div class="report-content bg-slate-900/50 rounded-lg p-4 max-h-[600px] overflow-y-auto">
            <div class="text-sm leading-relaxed text-white whitespace-pre-wrap" style="font-family: 'Microsoft YaHei', sans-serif;">
              <!-- 股票信息 -->
              <div v-if="stockCode" class="mb-4">
                <h3 class="text-lg font-semibold text-blue-400 mb-2">📈 股票信息</h3>
                <p class="text-gray-300">股票代码: {{ stockCode }}</p>
                <pre v-if="stockData" class="mt-2 text-gray-400">{{ stockData }}</pre>
              </div>
              
              <div class="border-t border-slate-700 my-4"></div>
              
              <!-- 各智能体分析结果 -->
              <div v-for="agent in allAgents" :key="agent.id" class="mb-4">
                <h3 class="text-lg font-semibold mb-2 flex items-center gap-2">
                  <span>{{ agent.icon }}</span>
                  <span :class="getAgentColorClass(agent.color)">{{ agent.title }}</span>
                </h3>
                <div class="pl-8 text-gray-300" v-html="formatReportText(agentOutputs[agent.id] || '等待分析...')"></div>
                <div class="border-t border-slate-700/50 mt-3"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 模型管理弹窗 -->
    <ModelManager 
      :visible="showModelManager"
      @close="showModelManager = false"
      @save="handleModelSave"
    />

    <!-- API配置弹窗 -->
    <ApiConfig 
      :visible="showApiConfig"
      :apiKeys="apiKeys"
      :apiStatus="apiStatus"
      @close="showApiConfig = false"
      @save="handleApiSave"
      @updateStatus="updateApiStatus"
    />

    <!-- 样式配置弹窗 -->
    <StyleConfig 
      :visible="showStyleConfig"
      :styles="styleSettings"
      @close="showStyleConfig = false"
      @save="handleStyleSave"
    />
  </div>
</template>

<script>
import { ref, computed, onMounted, inject } from 'vue'
import AgentCard from '@/components/AgentCard.vue'
import ModelManager from '@/components/ModelManager.vue'
import ApiConfig from '@/components/ApiConfig.vue'
import StyleConfig from '@/components/StyleConfig.vue'

// 智能体配置（与原系统保持一致）
const AGENTS = [
  // 第一阶段：5个专业分析师
  { id: 'macro', role: 'MACRO', title: '宏观政策分析师', icon: '🌍', color: 'slate', stage: 1 },
  { id: 'industry', role: 'INDUSTRY', title: '行业轮动分析师', icon: '🏭', color: 'cyan', stage: 1 },
  { id: 'technical', role: 'TECHNICAL', title: '技术分析专家', icon: '📈', color: 'violet', stage: 1 },
  { id: 'funds', role: 'FUNDS', title: '资金流向分析师', icon: '💰', color: 'emerald', stage: 1 },
  { id: 'fundamental', role: 'FUNDAMENTAL', title: '基本面估值分析师', icon: '💼', color: 'blue', stage: 1 },
  
  // 第二阶段：2个经理团队
  { id: 'manager_fundamental', role: 'MANAGER_FUNDAMENTAL', title: '基本面研究总监', icon: '👔', color: 'indigo', stage: 2 },
  { id: 'manager_momentum', role: 'MANAGER_MOMENTUM', title: '市场动能总监', icon: '⚡', color: 'fuchsia', stage: 2 },
  
  // 第三阶段：2个风控团队
  { id: 'risk_system', role: 'RISK_SYSTEM', title: '系统性风险总监', icon: '⚠️', color: 'orange', stage: 3 },
  { id: 'risk_portfolio', role: 'RISK_PORTFOLIO', title: '组合风险总监', icon: '⚖️', color: 'amber', stage: 3 },
  
  // 第四阶段：总经理
  { id: 'gm', role: 'GM', title: '投资决策总经理', icon: '👑', color: 'red', stage: 4 }
]

export default {
  name: 'AnalysisView',
  components: {
    AgentCard,
    ModelManager,
    ApiConfig,
    StyleConfig
  },
  setup() {
    const stockCode = ref('')
    const isAnalyzing = ref(false)
    
    // 从父组件inject共享状态
    const configMode = inject('configMode')
    const showModelManager = inject('showModelManager')
    const showApiConfig = inject('showApiConfig')
    const showStyleConfig = inject('showStylePanel')
    const apiStatus = inject('apiStatus')
    
    const agentStatus = ref({})
    const agentOutputs = ref({})
    const agentTokens = ref({})
    
    // 用于触发AgentCard重新加载模型的标记
    const modelUpdateTrigger = ref(0)
    const apiKeys = ref({
      gemini: '',
      deepseek: '',
      qwen: '',
      siliconflow: '',
      juhe: ''
    })
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
      particleColor: '#3b82f6'
    })

    // 初始化所有智能体状态为idle
    AGENTS.forEach(agent => {
      agentStatus.value[agent.id] = 'idle'
      agentOutputs.value[agent.id] = ''
      agentTokens.value[agent.id] = 0
    })

    // 按阶段分组智能体
    const stage1Agents = computed(() => AGENTS.filter(a => a.stage === 1))
    const stage2Agents = computed(() => AGENTS.filter(a => a.stage === 2))
    const stage3Agents = computed(() => AGENTS.filter(a => a.stage === 3))
    const stage4Agents = computed(() => AGENTS.filter(a => a.stage === 4))

    const isValidCode = computed(() => {
      return /^\d{6}$/.test(stockCode.value)
    })

    const startAnalysis = async () => {
      if (!isValidCode.value || isAnalyzing.value) return

      isAnalyzing.value = true
      showReport.value = false // 重置报告显示
      stockData.value = '' // 重置股票数据
      
      // 重置所有智能体状态
      AGENTS.forEach(agent => {
        agentStatus.value[agent.id] = 'idle'
        agentOutputs.value[agent.id] = ''
        agentTokens.value[agent.id] = 0
      })

      try {
        // 获取股票数据
        const fetchedStockData = await fetchStockData(stockCode.value)
        stockData.value = JSON.stringify(fetchedStockData, null, 2) // 保存股票数据
        
        // 按阶段执行分析
        for (let stage = 1; stage <= 4; stage++) {
          const stageAgents = AGENTS.filter(a => a.stage === stage)
          
          // 并行执行同一阶段的智能体
          await Promise.all(stageAgents.map(async (agent) => {
            agentStatus.value[agent.id] = 'loading'
            
            try {
              const result = await analyzeWithAgent(agent, stockCode.value, fetchedStockData)
              agentOutputs.value[agent.id] = result
              agentStatus.value[agent.id] = 'success'
              
              // 如果是GM完成，显示报告
              if (agent.id === 'gm') {
                showReport.value = true
                // 滚动到报告位置
                setTimeout(() => {
                  const reportEl = document.querySelector('.report-content')
                  if (reportEl) {
                    reportEl.scrollIntoView({ behavior: 'smooth' })
                  }
                }, 500)
              }
            } catch (error) {
              agentOutputs.value[agent.id] = `分析失败: ${error.message}`
              agentStatus.value[agent.id] = 'error'
            }
          }))
        }
      } catch (error) {
        console.error('分析失败:', error)
        alert('分析失败: ' + error.message)
      } finally {
        isAnalyzing.value = false
      }
    }

    // API调用函数
    const fetchStockData = async (code) => {
      const response = await fetch(`http://localhost:8000/api/stock/${code}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          symbol: code,
          apiKey: null  // 使用后端默认的API Key
        })
      })
      if (!response.ok) throw new Error('获取股票数据失败')
      return response.json()
    }

    const analyzeWithAgent = async (agent, code, stockData) => {
      const response = await fetch('http://localhost:8000/api/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          agent_id: agent.id,
          stock_code: code,
          stock_data: stockData,
          previous_outputs: agentOutputs.value
        })
      })
      
      if (!response.ok) throw new Error(`${agent.title}分析失败`)
      const data = await response.json()
      return data.result
    }

    // 切换配置模式
    const toggleConfigMode = () => {
      configMode.value = !configMode.value
    }

    // 处理模型保存
    const handleModelSave = async (selectedModels) => {
      console.log('保存选中的模型:', selectedModels)
      
      try {
        // 从后端加载现有配置
        const loadResponse = await fetch('http://localhost:8000/api/config/agents')
        let configData = { agents: [], selectedModels: [] }
        
        if (loadResponse.ok) {
          const data = await loadResponse.json()
          if (data.data) {
            configData = data.data
          }
        }
        
        // 更新selectedModels
        configData.selectedModels = selectedModels
        
        // 保存到后端
        const saveResponse = await fetch('http://localhost:8000/api/config/agents', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(configData)
        })
        
        if (saveResponse.ok) {
          console.log('模型选择已保存到后端文件')
          // 触发所有AgentCard重新加载模型列表
          modelUpdateTrigger.value++
        } else {
          console.error('保存模型选择失败')
        }
      } catch (error) {
        console.error('保存模型选择出错:', error)
      }
    }

    // 处理API配置保存
    const handleApiSave = (keys) => {
      apiKeys.value = keys
      // 保存到localStorage或后端
      localStorage.setItem('apiKeys', JSON.stringify(keys))
    }

    // 更新API状态
    const updateApiStatus = (provider, status) => {
      apiStatus.value[provider] = status
    }

    // 处理样式配置保存
    const handleStyleSave = (styles) => {
      styleSettings.value = styles
      // 应用样式到页面
      applyStyles(styles)
      // 保存到localStorage
      localStorage.setItem('styleSettings', JSON.stringify(styles))
    }

    // 应用样式到页面
    const applyStyles = (styles) => {
      // 应用卡片样式
      const cards = document.querySelectorAll('.agent-card')
      cards.forEach(card => {
        card.style.opacity = styles.cardOpacity / 100
        card.style.backdropFilter = `blur(${styles.cardBlur}px)`
        card.style.borderWidth = `${styles.borderWidth}px`
      })
      
      // 应用背景渐变
      const app = document.querySelector('#app')
      if (app) {
        app.style.background = `linear-gradient(${styles.gradientAngle}deg, ${styles.gradientStart} 0%, ${styles.gradientEnd} 100%)`
      }
      
      // 更新粒子背景设置（通过事件通知父组件）
      window.dispatchEvent(new CustomEvent('updateParticles', {
        detail: {
          enabled: styles.particlesEnabled,
          count: styles.particleCount,
          speed: styles.particleSpeed,
          color: styles.particleColor
        }
      }))
    }

    // 加载后端配置
    const loadBackendConfig = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/config')
        if (response.ok) {
          const data = await response.json()
          console.log('后端配置:', data)
          
          // 更新API密钥
          if (data.api_keys) {
            Object.keys(data.api_keys).forEach(key => {
              if (data.api_keys[key]) {
                apiKeys.value[key] = data.api_keys[key]
                apiStatus.value[key] = 'configured'
              }
            })
          }
          
          // 更新模型配置
          if (data.model_configs) {
            // 这里可以处理模型配置
            console.log('模型配置:', data.model_configs)
          }
        } else {
          console.error('后端响应错误:', response.status)
        }
      } catch (error) {
        console.error('加载配置失败:', error)
      }
    }

    // 组件挂载时加载配置
    onMounted(() => {
      loadBackendConfig()
      
      // 加载保存的样式设置
      const savedStyles = localStorage.getItem('styleSettings')
      if (savedStyles) {
        try {
          const styles = JSON.parse(savedStyles)
          styleSettings.value = { ...styleSettings.value, ...styles }
          // 应用样式
          setTimeout(() => applyStyles(styleSettings.value), 500)
        } catch (e) {
          console.error('加载样式设置失败:', e)
        }
      }
    })

    // 格式化报告文本
    const formatReportText = (text) => {
      if (!text) return ''
      return text.replace(/\n/g, '<br>')
    }

    // 获取智能体颜色类
    const getAgentColorClass = (color) => {
      const colorMap = {
        slate: 'text-slate-400',
        cyan: 'text-cyan-400',
        violet: 'text-violet-400',
        emerald: 'text-emerald-400',
        blue: 'text-blue-400',
        indigo: 'text-indigo-400',
        fuchsia: 'text-fuchsia-400',
        orange: 'text-orange-400',
        amber: 'text-amber-400',
        red: 'text-red-400'
      }
      return colorMap[color] || 'text-gray-400'
    }

    // 导出报告
    const exportReport = (format) => {
      const report = generateReport()
      const timestamp = new Date().toISOString().replace(/[:.]/g, '-').substring(0, 19)
      const filename = `InvestMind_Report_${stockCode.value}_${timestamp}`
      
      if (format === 'md') {
        downloadMarkdown(report, filename)
      } else if (format === 'html') {
        downloadHTML(report, filename)
      } else if (format === 'pdf') {
        downloadPDF(report, filename)
      }
    }

    // 生成报告内容
    const generateReport = () => {
      let report = `# InvestMind Pro 智投顾问团分析报告\n\n`
      report += `**股票代码**: ${stockCode.value}\n`
      report += `**报告时间**: ${new Date().toLocaleString('zh-CN')}\n\n`
      
      if (stockData.value) {
        report += `## 📈 股票信息\n\n`
        report += `\`\`\`\n${stockData.value}\n\`\`\`\n\n`
      }
      
      report += `---\n\n`
      
      AGENTS.forEach(agent => {
        report += `## ${agent.icon} ${agent.title}\n\n`
        report += agentOutputs.value[agent.id] || '等待分析...'
        report += `\n\n---\n\n`
      })
      
      return report
    }

    // 下载Markdown
    const downloadMarkdown = (content, filename) => {
      const blob = new Blob([content], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}.md`
      link.click()
      URL.revokeObjectURL(url)
    }

    // 下载HTML
    const downloadHTML = (markdownContent, filename) => {
      const htmlContent = `<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${filename}</title>
  <style>
    body { font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; max-width: 900px; margin: 0 auto; padding: 20px; background: #f5f5f5; }
    h1 { color: #333; border-bottom: 2px solid #3b82f6; padding-bottom: 10px; }
    h2 { color: #555; margin-top: 30px; }
    pre { background: #1e293b; color: #e2e8f0; padding: 15px; border-radius: 5px; overflow-x: auto; }
    hr { border: none; border-top: 1px solid #ddd; margin: 30px 0; }
  </style>
</head>
<body>
  ${markdownToHTML(markdownContent)}
</body>
</html>`
      
      const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${filename}.html`
      link.click()
      URL.revokeObjectURL(url)
    }

    // 简单的Markdown转HTML
    const markdownToHTML = (markdown) => {
      return markdown
        .replace(/^# (.*$)/gim, '<h1>$1</h1>')
        .replace(/^## (.*$)/gim, '<h2>$1</h2>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\n/g, '<br>')
        .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
        .replace(/---/g, '<hr>')
    }

    // 下载PDF (需要使用第三方库或浏览器打印功能)
    const downloadPDF = (markdownContent, filename) => {
      const htmlContent = markdownToHTML(markdownContent)
      const printWindow = window.open('', '_blank')
      printWindow.document.write(`
        <!DOCTYPE html>
        <html>
        <head>
          <title>${filename}</title>
          <style>
            body { font-family: 'Microsoft YaHei', sans-serif; line-height: 1.6; padding: 20px; }
            h1 { color: #333; }
            h2 { color: #555; margin-top: 20px; }
            pre { background: #f0f0f0; padding: 10px; border-radius: 5px; }
            @media print { body { padding: 0; } }
          </style>
        </head>
        <body>
          <h1>InvestMind Pro 智投顾问团分析报告</h1>
          ${htmlContent}
        </body>
        </html>
      `)
      printWindow.document.close()
      printWindow.focus()
      setTimeout(() => {
        printWindow.print()
      }, 250)
    }

    // 所有智能体
    const allAgents = computed(() => AGENTS)
    const stockData = ref('')
    const showReport = ref(false)

    return {
      stockCode,
      stockData,
      isAnalyzing,
      configMode,
      showModelManager,
      showApiConfig,
      showStyleConfig,  // 添加样式配置面板显示状态
      showReport,
      modelUpdateTrigger,
      agentStatus,
      agentOutputs,
      agentTokens,
      apiKeys,
      apiStatus,
      styleSettings,
      stage1Agents,
      stage2Agents,
      stage3Agents,
      stage4Agents,
      allAgents,
      isValidCode,
      startAnalysis,
      toggleConfigMode,
      handleModelSave,
      handleApiSave,
      updateApiStatus,
      handleStyleSave,
      formatReportText,
      getAgentColorClass,
      exportReport
    }
  }
}
</script>

<style scoped>
.analysis-container {
  min-height: calc(100vh - 5rem);
  padding: 2rem 1rem;
  position: relative;
  max-width: 1600px;
  margin: 0 auto;
}

/* 右上角控制按钮 */
.top-controls {
  position: fixed;
  top: 5.5rem;
  right: 2rem;
  display: flex;
  gap: 0.5rem;
  z-index: 40;
}

.control-btn {
  display: flex;
  align-items: center;
  gap: 0.375rem;
  padding: 0.5rem 0.875rem;
  background: rgba(30, 41, 59, 0.95);
  backdrop-filter: blur(10px);
  border: 1px solid #334155;
  border-radius: 0.5rem;
  color: #94a3b8;
  font-size: 0.75rem;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.2s;
}

.control-btn:hover {
  background: rgba(51, 65, 85, 0.95);
  color: #e2e8f0;
  border-color: #475569;
}

.control-btn.active {
  background: rgba(59, 130, 246, 0.2);
  color: #60a5fa;
  border-color: #3b82f6;
}

.btn-icon {
  font-size: 1rem;
}

.btn-text {
  display: none;
}

@media (min-width: 768px) {
  .btn-text {
    display: inline;
  }
}

.input-section {
  margin-bottom: 3rem;
}

.input-card {
  background: rgba(30, 41, 59, 0.5);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 1rem;
  padding: 2rem;
  max-width: 600px;
  margin: 0 auto;
}

.input-group {
  margin-bottom: 1.5rem;
}

.input-label {
  display: block;
  color: #94a3b8;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 0.5rem;
}

.stock-input {
  width: 100%;
  padding: 0.75rem 1rem;
  background: rgba(15, 23, 42, 0.5);
  border: 1px solid rgba(71, 85, 105, 0.3);
  border-radius: 0.5rem;
  color: white;
  font-size: 1.125rem;
  transition: all 0.2s;
}

.stock-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.analyze-btn {
  width: 100%;
  padding: 0.875rem;
  background: linear-gradient(135deg, #3b82f6, #0ea5e9);
  color: white;
  font-weight: 600;
  font-size: 1.125rem;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
}

.analyze-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(59, 130, 246, 0.3);
}

.analyze-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 智能体网格布局 */
.stage1-grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 1rem;
}

/* 响应式调整 */
@media (max-width: 1400px) {
  .stage1-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 900px) {
  .stage1-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 600px) {
  .stage1-grid {
    grid-template-columns: 1fr;
  }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-top-color: white;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-right: 0.5rem;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 报告区域样式 */
.report-content {
  position: relative;
}

.report-content::-webkit-scrollbar {
  width: 8px;
}

.report-content::-webkit-scrollbar-track {
  background: rgba(30, 41, 59, 0.3);
  border-radius: 4px;
}

.report-content::-webkit-scrollbar-thumb {
  background: rgba(71, 85, 105, 0.5);
  border-radius: 4px;
}

.report-content::-webkit-scrollbar-thumb:hover {
  background: rgba(71, 85, 105, 0.7);
}
</style>
