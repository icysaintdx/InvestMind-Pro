# InvestMind-Pro 智投顾问团

<div align="center">

![Version](https://img.shields.io/badge/version-2.5.0-blue.svg)
![Python](https://img.shields.io/badge/Python-3.8+-green.svg)
![Vue](https://img.shields.io/badge/Vue-3.2+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-yellow.svg)

**多智能体 AI 驱动的中国 A 股投资分析系统**

[功能特性](#-功能特性) • [快速开始](#-快速开始) • [系统架构](#-系统架构) • [更新日志](#-更新日志)

</div>

---

## 📖 项目简介

**InvestMind-Pro (智投顾问团)** 是一个基于多智能体协作的 AI 投资分析系统，专注于中国 A 股市场。系统采用 21 个专业 AI 智能体，通过 4 阶段协作分析流程，为投资者提供全方位的投资决策支持。

### 核心理念

- 🤖 **多智能体协作**: 模拟真实投资团队的分工协作
- 📊 **多维度分析**: 技术面、基本面、资金面、情绪面全覆盖
- ⚖️ **辩论式决策**: 多空博弈 + 三方风控，确保决策稳健
- 🔄 **实时监控**: 风险预警 + 数据流监控，及时响应市场变化

---

## ✨ 功能特性

### 🧠 21个专业AI智能体

| 阶段 | 智能体 | 职责 |
|------|--------|------|
| **阶段1: 情报收集** | 新闻分析师、技术分析师、基本面分析师、资金流向分析师、行业轮动分析师 | 多维度数据采集与初步分析 |
| **阶段2: 中观整合** | 研究部经理、风控部经理 | 汇总分析结果，形成初步建议 |
| **阶段3: 深度辩论** | 看涨研究员、看跌研究员、激进风控师、保守风控师、中立风控师 | 多空博弈，风险评估 |
| **阶段4: 最终决策** | 投资决策总经理 | 综合所有分析，输出最终建议 |

### 📈 核心功能模块

- **智能分析**: 一键启动21个智能体协作分析
- **多空辩论**: 看涨vs看跌研究员智能辩论
- **三方风控**: 激进/保守/中立三方风控评估
- **策略回测**: 20+交易策略，完整回测引擎
- **模拟交易**: 纸上交易系统，验证策略效果
- **数据流监控**: 实时监控多数据源状态
- **新闻聚合**: 多源新闻 + 情绪分析
- **风险预警**: ST状态、停复牌、股权质押等实时预警

### 📊 数据源支持

| 数据源 | 类型 | 说明 |
|--------|------|------|
| AKShare | 主数据源 | 免费、稳定、接口丰富 |
| Tushare | 辅助数据源 | 专业金融数据 |
| 聚合数据 | 备用数据源 | 多维度数据补充 |
| 东方财富 | 行情数据 | 实时行情、龙虎榜 |
| 新浪财经 | 新闻数据 | 财经新闻、公告 |

---

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 16+
- SQLite 3

### 安装步骤

#### 1. 克隆项目

```bash
git clone https://github.com/icysaintdx/InvestMind-Pro.git
cd InvestMind-Pro
```

#### 2. 后端安装

```bash
# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r backend/requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，配置 API Keys
```

#### 3. 前端安装

```bash
cd frontend
npm install
```

#### 4. 启动服务

```bash
# 启动后端 (在项目根目录)
python backend/server.py

# 启动前端 (在 frontend 目录)
npm run serve
```

#### 5. 访问系统

打开浏览器访问 `http://localhost:8080`

### Docker 部署

```bash
# 使用 docker-compose 一键部署
docker-compose up -d
```

---

## 🏗 系统架构

```
InvestMind-Pro/
├── backend/                    # Python FastAPI 后端
│   ├── api/                    # 30+ API路由文件
│   ├── agents/                 # 21个AI智能体
│   │   ├── analysts/           # 阶段1: 5个分析师
│   │   ├── managers/           # 阶段2: 2个管理者
│   │   ├── risk_mgmt/          # 阶段3: 3个风控辩论者
│   │   └── trader/             # 阶段4: 1个决策者
│   ├── dataflows/              # 数据流模块
│   │   ├── news/               # 新闻聚合模块
│   │   ├── risk/               # 风险监控模块
│   │   └── akshare/            # AKShare数据适配
│   ├── strategies/             # 20+交易策略
│   ├── backtest/               # 回测引擎
│   └── database/               # 数据库模型
├── frontend/                   # Vue 3 前端
│   ├── src/views/              # 页面组件
│   └── src/components/         # 可复用组件
└── docs/                       # 项目文档
```

### 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Vue 3 + Axios + ECharts |
| 后端 | Python FastAPI + SQLAlchemy |
| 数据库 | SQLite |
| AI模型 | Gemini / DeepSeek / Qwen / SiliconFlow / Ollama |

---

## 📝 更新日志

### v2.5.0 (当前版本)
- 🎆 新增数据流监控优化
- 🔧 修复多个数据源接口问题
- 📊 优化风险预警显示

### v1.8.0
- ⭐ LLM配置管理系统
- ⭐ 真实LLM服务集成 (Ollama/OpenAI/DeepSeek/Qwen)
- ⭐ 真实回测引擎对接
- ⭐ 策略库扩展 (5个策略)
- ⭐ 分层缓存体系 (L1/L2/L3)

### v1.7.0
- ⭐ 多级降级处理器
- ⭐ LLM智能文本摘要
- ⭐ 前端降级显示系统

### v1.6.0
- ⭐ 智能体配置系统
- ⭐ 智能依赖管理
- ⭐ 配置界面与工具

### v1.5.0
- ⭐ 多空研判博弈LLM接入
- ⭐ 三方风控评估LLM接入
- ⭐ 本地规则引擎兜底机制

[查看完整更新日志](CHANGELOG.md)

---

## 🔧 配置说明

### 环境变量配置

```bash
# AI API Keys
SILICONFLOW_API_KEY=your_key
DEEPSEEK_API_KEY=your_key
OPENAI_API_KEY=your_key

# 数据源 API Keys
TUSHARE_TOKEN=your_token
JUHE_API_KEY=your_key

# Ollama 配置 (本地模型)
OLLAMA_BASE_URL=http://localhost:11434
```

### 智能体配置

智能体配置文件位于 `backend/agent_configs.json`，支持：
- 模型选择
- 温度参数
- 超时设置
- 启用/禁用

---

## 📚 文档

- [项目概述](docs/PROJECT_OVERVIEW.md)
- [Docker部署指南](DOCKER_DEPLOYMENT_GUIDE.md)
- [API文档](docs/API文档.md)
- [数据源集成指南](docs/Tushare数据源集成指南.md)

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情

---

## ⚠️ 免责声明

本项目仅供学习和研究使用，不构成任何投资建议。投资有风险，入市需谨慎。

---

<div align="center">

**如果这个项目对你有帮助，请给一个 ⭐ Star！**

</div>
