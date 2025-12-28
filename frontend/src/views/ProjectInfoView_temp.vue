<template>
  <div class="project-info-container">
    <!-- 头部 -->
    <div class="info-header">
      <div class="header-content">
        <h1 class="title">
          <span class="icon">🏆</span>
          InvestMindPro
        </h1>
        <p class="subtitle">新一代AI驱动的智能投资决策系统</p>
        <div class="badges">
          <span class="badge">v1.3.4</span>
          <span class="badge">21个智能体</span>
          <span class="badge">9大数据源</span>
          <span class="badge">4个AI模型</span>
        </div>
      </div>
    </div>

    <!-- 主要内容 -->
    <div class="info-content">
      <!-- 项目概述 -->
      <section class="info-section">
        <h2 class="section-title">📌 项目概述</h2>
        <p class="section-text">
          <strong>InvestMindPro（阿尔法议会）</strong>是一个革命性的AI驱动投资决策系统，
          通过<strong>21个专业AI智能体</strong>的协同工作，模拟真实投资机构的决策流程，
          为投资者提供<strong>全方位、多维度、深层次</strong>的投资分析和决策支持。
        </p>
      </section>

      <!-- 核心特性 -->
      <section class="info-section">
        <h2 class="section-title">🌟 核心特性</h2>
        <div class="features-grid">
          <div class="feature-card">
            <div class="feature-icon">🤖</div>
            <h3 class="feature-title">智能体协同</h3>
            <p class="feature-desc">21个专业AI智能体<br>4阶段递进分析</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🎨</div>
            <h3 class="feature-title">用户体验</h3>
            <p class="feature-desc">实时打字机效果<br>思维链可视化</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">🔧</div>
            <h3 class="feature-title">技术创新</h3>
            <p class="feature-desc">多模型动态切换<br>智能新闻过滤</p>
          </div>
          <div class="feature-card">
            <div class="feature-icon">📊</div>
            <h3 class="feature-title">数据整合</h3>
            <p class="feature-desc">9大数据源<br>360+新闻源</p>
          </div>
        </div>
      </section>

      <!-- 21个智能体 -->
      <section class="info-section">
        <h2 class="section-title">🤖 21个专业智能体</h2>
        
        <div class="agents-stage">
          <h3 class="stage-title">第一阶段：全维信息采集（8个）</h3>
          <div class="agents-grid">
            <div class="agent-item">📰 新闻舆情分析师</div>
            <div class="agent-item">💬 社交媒体分析师</div>
            <div class="agent-item">🇨🇳 中国市场专家</div>
            <div class="agent-item">🏭 行业研究专家</div>
            <div class="agent-item">🌍 宏观经济学家</div>
            <div class="agent-item">📈 技术分析师</div>
            <div class="agent-item">💰 资金流向分析师</div>
            <div class="agent-item">💼 基本面分析师</div>
          </div>
        </div>

        <div class="agents-stage">
          <h3 class="stage-title">第二阶段：多空辩论（5个）</h3>
          <div class="agents-grid">
            <div class="agent-item">🐂 看涨研究员</div>
            <div class="agent-item">🐻 看跌研究员</div>
            <div class="agent-item">👔 基本面总监</div>
            <div class="agent-item">⚡ 市场动能总监</div>
            <div class="agent-item">🎯 研究经理</div>
          </div>
        </div>

        <div class="agents-stage">
          <h3 class="stage-title">第三阶段：风控评估（6个）</h3>
          <div class="agents-grid">
            <div class="agent-item">🔥 激进风控师</div>
            <div class="agent-item">🛡️ 保守风控师</div>
            <div class="agent-item">⚖️ 中立风控师</div>
            <div class="agent-item">🌐 系统风险总监</div>
            <div class="agent-item">📊 组合风险总监</div>
            <div class="agent-item">🎖️ 风险经理</div>
          </div>
        </div>

        <div class="agents-stage">
          <h3 class="stage-title">第四阶段：最终决策（2个）</h3>
          <div class="agents-grid">
            <div class="agent-item">👑 投资决策总经理</div>
            <div class="agent-item">📢 白话解读员</div>
          </div>
        </div>
      </section>

      <!-- 系统数据 -->
      <section class="info-section">
        <h2 class="section-title">📊 系统数据</h2>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-number">21</div>
            <div class="stat-label">专业智能体</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">9</div>
            <div class="stat-label">数据源</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">360+</div>
            <div class="stat-label">新闻源</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">4</div>
            <div class="stat-label">AI模型</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">50K+</div>
            <div class="stat-label">代码行数</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">74</div>
            <div class="stat-label">文档数量</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">95%+</div>
            <div class="stat-label">成功率</div>
          </div>
          <div class="stat-card">
            <div class="stat-number">2-3分钟</div>
            <div class="stat-label">分析速度</div>
          </div>
        </div>
      </section>

      <!-- 技术亮点 -->
      <section class="info-section">
        <h2 class="section-title">💡 核心技术亮点</h2>
        <div class="highlights-grid">
          <div class="highlight-card">
            <div class="highlight-icon">🎯</div>
            <h3 class="highlight-title">智能新闻过滤</h3>
            <p class="highlight-desc">360条→83条<br>过滤率77%</p>
          </div>
          <div class="highlight-card">
            <div class="highlight-icon">🔄</div>
            <h3 class="highlight-title">网络容错</h3>
            <p class="highlight-desc">3次重试<br>指数退避</p>
          </div>
          <div class="highlight-card">
            <div class="highlight-icon">🧠</div>
            <h3 class="highlight-title">思维链可视化</h3>
            <p class="highlight-desc">CoT展示<br>透明决策</p>
          </div>
          <div class="highlight-card">
            <div class="highlight-icon">⚡</div>
            <h3 class="highlight-title">异步并发</h3>
            <p class="highlight-desc">8倍速度<br>高效处理</p>
          </div>
        </div>
      </section>

      <!-- 技术栈 -->
      <section class="info-section">
        <h2 class="section-title">🔧 技术栈</h2>
        <div class="tech-stack">
          <div class="tech-category">
            <h3 class="tech-category-title">后端技术</h3>
            <div class="tech-tags">
              <span class="tech-tag">FastAPI</span>
              <span class="tech-tag">Python 3.8+</span>
              <span class="tech-tag">Uvicorn</span>
              <span class="tech-tag">Pydantic</span>
              <span class="tech-tag">httpx</span>
              <span class="tech-tag">asyncio</span>
            </div>
          </div>
          <div class="tech-category">
            <h3 class="tech-category-title">前端技术</h3>
            <div class="tech-tags">
              <span class="tech-tag">Vue 3</span>
              <span class="tech-tag">Composition API</span>
              <span class="tech-tag">Vite</span>
              <span class="tech-tag">Axios</span>
              <span class="tech-tag">TailwindCSS</span>
            </div>
          </div>
          <div class="tech-category">
            <h3 class="tech-category-title">AI模型</h3>
            <div class="tech-tags">
              <span class="tech-tag">Gemini 2.0</span>
              <span class="tech-tag">DeepSeek</span>
              <span class="tech-tag">Qwen Plus</span>
              <span class="tech-tag">SiliconFlow</span>
            </div>
          </div>
        </div>
      </section>

      <!-- 页脚 -->
      <div class="info-footer">
        <p><strong>InvestMindPro - 让投资决策更智能！</strong></p>
        <p>版本: v1.3.4 | 最后更新: 2024-12-05</p>
        <p>文档总数: 74篇 | 代码行数: 50,000+</p>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'ProjectInfoView'
}
</script>

<style scoped>
.project-info-container {
  padding: 2rem;
  color: #fff;
}

/* 头部 */
.info-header {
  text-align: center;
  padding: 3rem 2rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 15px;
  margin-bottom: 2rem;
}

.header-content .title {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 1rem;
}

.header-content .icon {
  font-size: 3.5rem;
}

.header-content .subtitle {
  font-size: 1.5rem;
  margin-bottom: 1.5rem;
  opacity: 0.95;
}

.badges {
  display: flex;
  justify-content: center;
  gap: 0.75rem;
  flex-wrap: wrap;
}

.badge {
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  font-size: 0.9rem;
  backdrop-filter: blur(10px);
}

/* 内容区域 */
.info-content {
  max-width: 1000px;
  margin: 0 auto;
}

.info-section {
  margin-bottom: 3rem;
}

.section-title {
  font-size: 2rem;
  margin-bottom: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.section-text {
  font-size: 1.1rem;
  line-height: 1.8;
  color: #cbd5e1;
}

/* 特性网格 */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.feature-card {
  padding: 1.5rem;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
  background: rgba(102, 126, 234, 0.15);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
}

.feature-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #667eea;
}

.feature-desc {
  font-size: 0.9rem;
  color: #94a3b8;
  line-height: 1.6;
}

/* 智能体展示 */
.agents-stage {
  margin-bottom: 2rem;
}

.stage-title {
  font-size: 1.3rem;
  margin-bottom: 1rem;
  color: #667eea;
}

.agents-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 1rem;
}

.agent-item {
  padding: 1rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 10px;
  text-align: center;
  font-size: 0.95rem;
  transition: all 0.3s ease;
}

.agent-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 20px rgba(102, 126, 234, 0.4);
}

/* 统计数据 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.stat-card {
  padding: 1.5rem;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  text-align: center;
}

.stat-number {
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 0.9rem;
  opacity: 0.9;
}

/* 技术亮点 */
.highlights-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 1.5rem;
  margin-top: 1.5rem;
}

.highlight-card {
  padding: 1.5rem;
  background: rgba(102, 126, 234, 0.1);
  border: 1px solid rgba(102, 126, 234, 0.3);
  border-radius: 12px;
  text-align: center;
  transition: all 0.3s ease;
}

.highlight-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 30px rgba(102, 126, 234, 0.3);
}

.highlight-icon {
  font-size: 2.5rem;
  margin-bottom: 1rem;
}

.highlight-title {
  font-size: 1.1rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: #667eea;
}

.highlight-desc {
  font-size: 0.9rem;
  color: #94a3b8;
  line-height: 1.6;
}

/* 技术栈 */
.tech-stack {
  margin-top: 1.5rem;
}

.tech-category {
  margin-bottom: 1.5rem;
}

.tech-category-title {
  font-size: 1.2rem;
  margin-bottom: 0.75rem;
  color: #667eea;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.tech-tag {
  padding: 0.5rem 1rem;
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
  border-radius: 20px;
  font-size: 0.9rem;
}

/* 页脚 */
.info-footer {
  text-align: center;
  padding: 2rem;
  margin-top: 3rem;
  border-top: 1px solid rgba(102, 126, 234, 0.3);
  color: #94a3b8;
}

.info-footer p {
  margin-bottom: 0.5rem;
}

.info-footer strong {
  color: #667eea;
  font-size: 1.1rem;
}

/* 响应式 */
@media (max-width: 768px) {
  .header-content .title {
    font-size: 2rem;
  }

  .header-content .subtitle {
    font-size: 1.2rem;
  }

  .features-grid,
  .agents-grid,
  .stats-grid,
  .highlights-grid {
    grid-template-columns: 1fr;
  }
}
</style>