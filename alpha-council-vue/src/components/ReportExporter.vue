<template>
  <div class="report-exporter">
    <button @click="exportReport('html')" class="export-btn export-btn-html" :disabled="isExporting">
      <span v-if="!isExporting">🌐 HTML</span>
      <span v-else>⏳ 生成中...</span>
    </button>
    <button @click="exportReport('md')" class="export-btn export-btn-md" :disabled="isExporting">
      <span v-if="!isExporting">📝 Markdown</span>
      <span v-else>⏳ 生成中...</span>
    </button>
    <button @click="exportReport('pdf')" class="export-btn export-btn-pdf" :disabled="isExporting" title="即将支持">
      <span v-if="!isExporting">📄 PDF</span>
      <span v-else>⏳ 生成中...</span>
    </button>
  </div>
</template>

<script>
export default {
  name: 'ReportExporter',
  props: {
    stockCode: String,
    stockName: String,
    agents: Array,
    agentOutputs: Object
  },
  data() {
    return {
      isExporting: false
    }
  },
  methods: {
    async exportReport(format = 'html') {
      this.isExporting = true
      
      try {
        let content, mimeType, extension
        
        switch (format) {
          case 'html':
            content = this.generateHTMLReport()
            mimeType = 'text/html;charset=utf-8'
            extension = 'html'
            break
          case 'md':
            content = this.generateMarkdownReport()
            mimeType = 'text/markdown;charset=utf-8'
            extension = 'md'
            break
          case 'pdf':
            alert('PDF导出功能即将上线，请先使用HTML或Markdown格式')
            this.isExporting = false
            return
          default:
            throw new Error('不支持的格式')
        }
        
        // 创建Blob
        const blob = new Blob([content], { type: mimeType })
        
        // 创建下载链接
        const url = URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `${this.stockName || this.stockCode}_投研报告_${new Date().toISOString().split('T')[0]}.${extension}`
        
        // 触发下载
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        
        // 释放URL
        URL.revokeObjectURL(url)
        
        console.log(`${format.toUpperCase()}报告导出成功`)
      } catch (error) {
        console.error('报告导出失败:', error)
        alert('报告导出失败，请重试')
      } finally {
        this.isExporting = false
      }
    },
    
    generateHTMLReport() {
      const timestamp = new Date().toLocaleString('zh-CN')
      
      // 按阶段分组
      const stages = {
        '第一阶段：全维信息采集与分析': ['news_analyst', 'social_analyst', 'china_market'],
        '第二阶段：多维度深度研判': ['industry', 'macro'],
        '第三阶段：量化技术与资金分析': ['technical', 'funds', 'fundamental'],
        '第四阶段：多空博弈与风险评估': ['bull_researcher', 'bear_researcher', 'risk_aggressive', 'risk_conservative']
      }
      
      let content = ''
      
      for (const [stageName, agentIds] of Object.entries(stages)) {
        content += `
          <div class="stage-section">
            <h2 class="stage-title">${stageName}</h2>
            <div class="agents-grid">
        `
        
        agentIds.forEach(agentId => {
          const agent = this.agents.find(a => a.id === agentId)
          if (!agent) return
          
          const output = this.agentOutputs[agentId] || '暂无分析结果'
          
          content += `
            <div class="agent-card">
              <div class="agent-header">
                <span class="agent-icon">${agent.icon}</span>
                <span class="agent-title">${agent.title}</span>
              </div>
              <div class="agent-content">
                ${this.formatOutput(output)}
              </div>
            </div>
          `
        })
        
        content += `
            </div>
          </div>
        `
      }
      
      return `
<!DOCTYPE html>
<html lang="zh-CN">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>${this.stockName || this.stockCode} - 智能投研分析报告</title>
  <style>
    * {
      margin: 0;
      padding: 0;
      box-sizing: border-box;
    }
    
    body {
      font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      padding: 2rem;
      line-height: 1.6;
    }
    
    .report-container {
      max-width: 1200px;
      margin: 0 auto;
      background: white;
      border-radius: 16px;
      box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
      overflow: hidden;
    }
    
    .report-header {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 3rem 2rem;
      text-align: center;
    }
    
    .report-title {
      font-size: 2.5rem;
      font-weight: bold;
      margin-bottom: 1rem;
    }
    
    .report-meta {
      font-size: 1rem;
      opacity: 0.9;
    }
    
    .report-body {
      padding: 2rem;
    }
    
    .stage-section {
      margin-bottom: 3rem;
    }
    
    .stage-title {
      font-size: 1.8rem;
      color: #667eea;
      margin-bottom: 1.5rem;
      padding-bottom: 0.5rem;
      border-bottom: 3px solid #667eea;
    }
    
    .agents-grid {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
      gap: 1.5rem;
    }
    
    .agent-card {
      background: #f8f9fa;
      border-radius: 12px;
      padding: 1.5rem;
      box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
      transition: transform 0.2s;
    }
    
    .agent-card:hover {
      transform: translateY(-4px);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
    }
    
    .agent-header {
      display: flex;
      align-items: center;
      gap: 0.75rem;
      margin-bottom: 1rem;
      padding-bottom: 0.75rem;
      border-bottom: 2px solid #e9ecef;
    }
    
    .agent-icon {
      font-size: 2rem;
    }
    
    .agent-title {
      font-size: 1.25rem;
      font-weight: bold;
      color: #333;
    }
    
    .agent-content {
      color: #555;
      white-space: pre-wrap;
      word-wrap: break-word;
    }
    
    .report-footer {
      background: #f8f9fa;
      padding: 2rem;
      text-align: center;
      color: #666;
      border-top: 1px solid #e9ecef;
    }
    
    @media print {
      body {
        background: white;
        padding: 0;
      }
      
      .report-container {
        box-shadow: none;
      }
      
      .agent-card {
        page-break-inside: avoid;
      }
    }
  </style>
</head>
<body>
  <div class="report-container">
    <div class="report-header">
      <h1 class="report-title">📊 ${this.stockName || this.stockCode} 智能投研分析报告</h1>
      <div class="report-meta">
        <p>股票代码: ${this.stockCode}</p>
        <p>生成时间: ${timestamp}</p>
        <p>分析智能体: ${this.agents.length}个</p>
      </div>
    </div>
    
    <div class="report-body">
      ${content}
    </div>
    
    <div class="report-footer">
      <p>本报告由 InvestMind Pro 智能投研系统自动生成</p>
      <p>仅供参考，不构成投资建议</p>
    </div>
  </div>
</body>
</html>
      `
    },
    
    generateMarkdownReport() {
      const timestamp = new Date().toLocaleString('zh-CN')
      
      // 按阶段分组
      const stages = {
        '第一阶段：全维信息采集与分析': ['news_analyst', 'social_analyst', 'china_market'],
        '第二阶段：多维度深度研判': ['industry', 'macro'],
        '第三阶段：量化技术与资金分析': ['technical', 'funds', 'fundamental'],
        '第四阶段：多空博弈与风险评估': ['bull_researcher', 'bear_researcher', 'risk_aggressive', 'risk_conservative']
      }
      
      let markdown = `# 📊 ${this.stockName || this.stockCode} 智能投研分析报告\n\n`
      markdown += `**股票代码**: ${this.stockCode}\n\n`
      markdown += `**生成时间**: ${timestamp}\n\n`
      markdown += `**分析智能体**: ${this.agents.length}个\n\n`
      markdown += `---\n\n`
      
      for (const [stageName, agentIds] of Object.entries(stages)) {
        markdown += `## ${stageName}\n\n`
        
        agentIds.forEach(agentId => {
          const agent = this.agents.find(a => a.id === agentId)
          if (!agent) return
          
          const output = this.agentOutputs[agentId] || '暂无分析结果'
          
          markdown += `### ${agent.icon} ${agent.title}\n\n`
          markdown += `${output}\n\n`
          markdown += `---\n\n`
        })
      }
      
      markdown += `\n\n---\n\n`
      markdown += `*本报告由 InvestMind Pro 智能投研系统自动生成*\n\n`
      markdown += `*仅供参考，不构成投资建议*\n`
      
      return markdown
    },
    
    formatOutput(text) {
      // 将换行符转换为<br>，保持格式
      return text
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/\n/g, '<br>')
    }
  }
}
</script>

<style scoped>
.report-exporter {
  display: flex;
  gap: 0.75rem;
}

.export-btn {
  color: white;
  border: none;
  padding: 0.5rem 1.25rem;
  border-radius: 6px;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.export-btn-html {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  box-shadow: 0 2px 8px rgba(16, 185, 129, 0.3);
}

.export-btn-html:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(16, 185, 129, 0.5);
}

.export-btn-md {
  background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.export-btn-md:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.5);
}

.export-btn-pdf {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  box-shadow: 0 2px 8px rgba(239, 68, 68, 0.3);
}

.export-btn-pdf:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(239, 68, 68, 0.5);
}

.export-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}
</style>
