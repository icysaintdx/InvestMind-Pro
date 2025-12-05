<template>
  <div class="landing-page">
    <!-- 背景特效 -->
    <div class="bg-effects">
      <div class="glow-orb orb-1"></div>
      <div class="glow-orb orb-2"></div>
      <div class="grid-overlay"></div>
    </div>

    <!-- 导航栏 -->
    <nav class="landing-nav">
      <div class="nav-brand">
        <span class="brand-icon">🏅</span>
        <span class="brand-text">InvestMind <span class="highlight">Pro</span></span>
      </div>
      <div class="nav-links">
        <a href="#features" class="nav-link">核心特性</a>
        <a href="#agents" class="nav-link">智能体矩阵</a>
        <a href="#tech" class="nav-link">技术架构</a>
      </div>
    </nav>

    <!-- Hero 区域 -->
    <header class="hero-section">
      <div class="hero-content">
        <div class="version-badge">
          <span class="badge-dot"></span>
          v1.3.4 全新发布
        </div>
        <h1 class="hero-title">
          下一代 AI 驱动的<br>
          <span class="gradient-text">智能投资决策系统</span>
        </h1>
        <p class="hero-subtitle">
          21个专业智能体协同工作 · 9大实时数据源聚合 · 4阶段深度递进分析
        </p>
        
        <div class="hero-stats">
          <div class="stat-item">
            <span class="stat-num">21</span>
            <span class="stat-label">智能体</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-num">9</span>
            <span class="stat-label">数据源</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-num">360+</span>
            <span class="stat-label">新闻源</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat-item">
            <span class="stat-num">4</span>
            <span class="stat-label">AI模型</span>
          </div>
        </div>
      </div>
      
      <!-- 视觉展示区 -->
      <div class="hero-visual">
        <div class="glass-card main-card">
          <div class="card-header">
            <div class="dot red"></div>
            <div class="dot yellow"></div>
            <div class="dot green"></div>
            <span class="card-title">Investment Analysis Protocol</span>
          </div>
          <div class="card-body">
            <div class="typing-effect">
              > Initializing InvestMind Pro System...<br>
              > Connecting to global data sources...<br>
              > Activating 21 AI agents...<br>
              > <span class="success">System Ready. Analysis in progress.</span>
            </div>
            <div class="wave-container">
              <div class="wave"></div>
              <div class="wave"></div>
              <div class="wave"></div>
            </div>
          </div>
        </div>
      </div>
    </header>

    <!-- 核心特性 -->
    <section id="features" class="section features-section">
      <h2 class="section-title">重塑投资决策流程</h2>
      <div class="features-grid">
        <div class="feature-card">
          <div class="feature-icon">🧠</div>
          <h3>多智能体协同</h3>
          <p>告别单一视角。21个专业角色分工协作，从宏观到微观，从技术到基本面，全方位扫描投资机会。</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">⚖️</div>
          <h3>多空辩论机制</h3>
          <p>引入看涨与看跌研究员的对抗辩论，模拟真实投研会议，深入挖掘逻辑漏洞，拒绝盲目乐观。</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">🛡️</div>
          <h3>三方风控评估</h3>
          <p>激进、保守、中立三方风控视角，量化评估系统性风险与组合风险，为资金安全保驾护航。</p>
        </div>
        <div class="feature-card">
          <div class="feature-icon">⚡</div>
          <h3>智能新闻过滤</h3>
          <p>独创情绪过滤算法，从360+条海量资讯中智能提炼83条高价值信息，信息密度提升300%。</p>
        </div>
      </div>
    </section>

    <!-- 智能体矩阵 -->
    <section id="agents" class="section agents-section">
      <h2 class="section-title">21个超级智能体矩阵</h2>
      <div class="agents-container">
        <!-- 阶段 1 -->
        <div class="agent-group">
          <div class="group-header">
            <span class="step-num">01</span>
            <h3>全维信息采集</h3>
          </div>
          <div class="agent-list">
            <div class="agent-chip">📰 新闻舆情</div>
            <div class="agent-chip">💬 社交媒体</div>
            <div class="agent-chip">🇨🇳 中国市场</div>
            <div class="agent-chip">🏭 行业研究</div>
            <div class="agent-chip">🌍 宏观经济</div>
            <div class="agent-chip">📈 技术分析</div>
            <div class="agent-chip">💰 资金流向</div>
            <div class="agent-chip">💼 基本面</div>
          </div>
        </div>
        
        <div class="flow-arrow">↓</div>

        <!-- 阶段 2 -->
        <div class="agent-group">
          <div class="group-header">
            <span class="step-num">02</span>
            <h3>多空辩论研判</h3>
          </div>
          <div class="agent-list highlight">
            <div class="agent-chip bull">🐂 看涨研究员</div>
            <div class="agent-chip bear">🐻 看跌研究员</div>
            <div class="agent-chip">👔 基本面总监</div>
            <div class="agent-chip">⚡ 市场动能总监</div>
            <div class="agent-chip core">🎯 研究经理</div>
          </div>
        </div>

        <div class="flow-arrow">↓</div>

        <!-- 阶段 3 -->
        <div class="agent-group">
          <div class="group-header">
            <span class="step-num">03</span>
            <h3>全景风控评估</h3>
          </div>
          <div class="agent-list">
            <div class="agent-chip fire">🔥 激进风控</div>
            <div class="agent-chip shield">🛡️ 保守风控</div>
            <div class="agent-chip scale">⚖️ 中立风控</div>
            <div class="agent-chip">🌐 系统风险</div>
            <div class="agent-chip">📊 组合风险</div>
            <div class="agent-chip core">🎖️ 风险经理</div>
          </div>
        </div>

        <div class="flow-arrow">↓</div>

        <!-- 阶段 4 -->
        <div class="agent-group final-stage">
          <div class="group-header">
            <span class="step-num">04</span>
            <h3>最终决策输出</h3>
          </div>
          <div class="agent-list final">
            <div class="agent-chip king">👑 投资决策总经理</div>
            <div class="agent-chip speaker">📢 白话解读员</div>
          </div>
        </div>
      </div>
    </section>

    <!-- 技术架构 -->
    <section id="tech" class="section tech-section">
      <h2 class="section-title">硬核技术栈</h2>
      <div class="tech-grid">
        <div class="tech-category">
          <h3>Backend Core</h3>
          <div class="tech-tags">
            <span>Python 3.8+</span>
            <span>FastAPI</span>
            <span>Uvicorn</span>
            <span>AsyncIO</span>
            <span>Pandas</span>
          </div>
        </div>
        <div class="tech-category">
          <h3>Frontend UX</h3>
          <div class="tech-tags">
            <span>Vue 3</span>
            <span>Composition API</span>
            <span>Vite</span>
            <span>TailwindCSS</span>
          </div>
        </div>
        <div class="tech-category">
          <h3>AI Engine</h3>
          <div class="tech-tags">
            <span>Gemini 2.0</span>
            <span>DeepSeek</span>
            <span>Qwen Plus</span>
            <span>SiliconFlow</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 页脚 -->
    <footer class="landing-footer">
      <div class="footer-content">
        <div class="footer-brand">
          <h3>InvestMind Pro</h3>
          <p>让投资决策更智能、更专业、更透明。</p>
        </div>
        <div class="footer-info">
          <p>Version 1.3.4</p>
          <p>© 2024 InvestMind Pro Team. All rights reserved.</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
// 无需额外逻辑，纯展示页面
</script>

<style scoped>
/* 全局变量 */
:root {
  --primary-color: #6366f1;
  --secondary-color: #8b5cf6;
  --bg-dark: #0f172a;
  --text-light: #f8fafc;
  --glass-bg: rgba(255, 255, 255, 0.05);
  --glass-border: rgba(255, 255, 255, 0.1);
}

.landing-page {
  font-family: 'Inter', system-ui, sans-serif;
  color: var(--text-light);
  background-color: var(--bg-dark);
  min-height: 100vh;
  overflow-x: hidden;
  position: relative;
  padding-bottom: 4rem;
}

/* 背景特效 */
.bg-effects {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
}

.glow-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.4;
}

.orb-1 {
  top: -10%;
  left: -10%;
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, var(--primary-color), transparent);
  animation: float 10s infinite ease-in-out;
}

.orb-2 {
  bottom: -10%;
  right: -10%;
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, var(--secondary-color), transparent);
  animation: float 12s infinite ease-in-out reverse;
}

.grid-overlay {
  position: absolute;
  width: 100%;
  height: 100%;
  background-image: 
    linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
  background-size: 50px 50px;
  mask-image: radial-gradient(circle at center, black 40%, transparent 100%);
}

/* 导航栏 */
.landing-nav {
  position: relative;
  z-index: 10;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1.5rem 4rem;
  backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--glass-border);
}

.nav-brand {
  font-size: 1.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.highlight {
  color: var(--primary-color);
  background: linear-gradient(to right, #6366f1, #a855f7);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.nav-links {
  display: flex;
  gap: 2rem;
}

.nav-link {
  color: #94a3b8;
  text-decoration: none;
  font-weight: 500;
  transition: color 0.3s;
}

.nav-link:hover {
  color: #fff;
}

/* Hero 区域 */
.hero-section {
  position: relative;
  z-index: 10;
  padding: 6rem 4rem;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 4rem;
  align-items: center;
  max-width: 1440px;
  margin: 0 auto;
}

.version-badge {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background: rgba(99, 102, 241, 0.1);
  border: 1px solid rgba(99, 102, 241, 0.2);
  border-radius: 99px;
  color: #818cf8;
  font-size: 0.875rem;
  font-weight: 500;
  margin-bottom: 1.5rem;
}

.badge-dot {
  width: 8px;
  height: 8px;
  background: #818cf8;
  border-radius: 50%;
  box-shadow: 0 0 10px #818cf8;
}

.hero-title {
  font-size: 4rem;
  line-height: 1.1;
  font-weight: 800;
  margin-bottom: 1.5rem;
}

.gradient-text {
  background: linear-gradient(135deg, #fff 0%, #94a3b8 100%);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.hero-subtitle {
  font-size: 1.25rem;
  color: #94a3b8;
  margin-bottom: 3rem;
  line-height: 1.6;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 2rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
}

.stat-num {
  font-size: 2rem;
  font-weight: 700;
  color: #fff;
}

.stat-label {
  font-size: 0.875rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.stat-divider {
  width: 1px;
  height: 40px;
  background: rgba(255, 255, 255, 0.1);
}

/* 视觉卡片 */
.glass-card {
  background: rgba(23, 23, 23, 0.6);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 1rem;
  overflow: hidden;
  box-shadow: 0 25px 50px -12px rgba(0, 0, 0, 0.5);
  transform: perspective(1000px) rotateY(-5deg) rotateX(2deg);
  transition: transform 0.5s ease;
}

.glass-card:hover {
  transform: perspective(1000px) rotateY(0) rotateX(0);
}

.card-header {
  padding: 1rem;
  background: rgba(255, 255, 255, 0.05);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.red { background: #ef4444; }
.yellow { background: #eab308; }
.green { background: #22c55e; }

.card-title {
  margin-left: 0.5rem;
  font-size: 0.875rem;
  color: #94a3b8;
  font-family: monospace;
}

.card-body {
  padding: 2rem;
  min-height: 300px;
  font-family: monospace;
  color: #22c55e;
  position: relative;
}

.typing-effect {
  line-height: 1.8;
}

.success {
  color: #4ade80;
  text-shadow: 0 0 10px rgba(74, 222, 128, 0.5);
}

/* Section 通用 */
.section {
  position: relative;
  z-index: 10;
  padding: 6rem 4rem;
  max-width: 1280px;
  margin: 0 auto;
}

.section-title {
  font-size: 2.5rem;
  font-weight: 700;
  text-align: center;
  margin-bottom: 4rem;
  background: linear-gradient(to right, #fff, #94a3b8);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

/* Features */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}

.feature-card {
  padding: 2rem;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  transition: all 0.3s ease;
}

.feature-card:hover {
  background: rgba(255, 255, 255, 0.05);
  transform: translateY(-5px);
}

.feature-icon {
  font-size: 3rem;
  margin-bottom: 1.5rem;
}

.feature-card h3 {
  font-size: 1.25rem;
  margin-bottom: 1rem;
  color: #fff;
}

.feature-card p {
  color: #94a3b8;
  line-height: 1.6;
}

/* Agents 流程图 */
.agents-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2rem;
}

.agent-group {
  width: 100%;
  max-width: 900px;
  padding: 2rem;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(255, 255, 255, 0.05);
  border-radius: 1rem;
  position: relative;
}

.group-header {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.step-num {
  font-size: 3rem;
  font-weight: 900;
  color: rgba(255, 255, 255, 0.05);
  position: absolute;
  top: 1rem;
  right: 1rem;
  line-height: 1;
}

.agent-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.75rem;
}

.agent-chip {
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 0.5rem;
  font-size: 0.875rem;
  color: #cbd5e1;
  border: 1px solid transparent;
  transition: all 0.3s;
}

.agent-chip:hover {
  background: rgba(99, 102, 241, 0.1);
  border-color: rgba(99, 102, 241, 0.3);
  color: #fff;
}

.flow-arrow {
  font-size: 1.5rem;
  color: rgba(255, 255, 255, 0.2);
}

/* 特殊智能体样式 */
.agent-chip.bull { color: #ef4444; background: rgba(239, 68, 68, 0.1); }
.agent-chip.bear { color: #22c55e; background: rgba(34, 197, 94, 0.1); }
.agent-chip.core { border: 1px solid rgba(255, 255, 255, 0.2); font-weight: 600; }
.agent-chip.king { 
  background: linear-gradient(135deg, rgba(234, 179, 8, 0.1), rgba(234, 179, 8, 0.05));
  border: 1px solid rgba(234, 179, 8, 0.3);
  color: #facc15;
  font-weight: 700;
}

/* 技术栈 */
.tech-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 2rem;
}

.tech-category {
  text-align: center;
}

.tech-category h3 {
  font-size: 1.1rem;
  margin-bottom: 1.5rem;
  color: #64748b;
  text-transform: uppercase;
  letter-spacing: 0.1em;
}

.tech-tags {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 1rem;
}

.tech-tags span {
  padding: 0.5rem 1rem;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 99px;
  font-size: 0.875rem;
  color: #e2e8f0;
}

/* 页脚 */
.landing-footer {
  margin-top: 4rem;
  padding: 4rem;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  background: rgba(0, 0, 0, 0.2);
}

.footer-content {
  max-width: 1280px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.footer-brand h3 {
  font-size: 1.5rem;
  margin-bottom: 0.5rem;
  color: #fff;
}

.footer-brand p {
  color: #64748b;
}

.footer-info {
  text-align: right;
  color: #475569;
  font-size: 0.875rem;
}

@keyframes float {
  0%, 100% { transform: translate(0, 0); }
  50% { transform: translate(20px, -20px); }
}

@media (max-width: 768px) {
  .hero-section {
    grid-template-columns: 1fr;
    padding: 4rem 1.5rem;
  }
  
  .hero-title {
    font-size: 2.5rem;
  }
  
  .landing-nav {
    padding: 1rem 1.5rem;
  }
  
  .nav-links {
    display: none;
  }
  
  .footer-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 2rem;
  }
  
  .footer-info {
    text-align: left;
  }
}
</style>
