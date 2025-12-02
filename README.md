# 🏅 InvestMind Pro - 智投顾问团

> 基于多智能体协同的智能投资分析系统

## 📋 项目简介

**InvestMind Pro（智投顾问团）** 是一个集成了10个专业AI智能体的股票投资分析系统。通过多层级、多角度的协同分析，为投资决策提供全方位的专业支持。

## ✨ 核心特性

- **🤖 10个专业智能体**：覆盖宏观、行业、技术、资金、基本面等多个维度
- **📊 4阶段递进分析**：从基础分析到风控评估，层层深入
- **🎯 智能决策整合**：投资决策总经理统筹全局，输出专业报告
- **🚀 多模型支持**：支持Gemini、DeepSeek、Qwen、SiliconFlow等多个AI模型
- **📈 实时数据分析**：整合聚合数据、Finnhub、Tushare等多个数据源
- **💡 美观的UI界面**：基于Vue3的现代化前端界面
- **📥 报告导出**：支持Markdown、HTML、PDF多种格式导出

## 🏗️ 系统架构

### 智能体层级

```
第一阶段：专业分析师（5个）
├── 🌍 宏观政策分析师
├── 🏭 行业轮动分析师  
├── 📈 技术分析专家
├── 💰 资金流向分析师
└── 💼 基本面估值分析师

第二阶段：经理团队（2个）
├── 👔 基本面研究总监
└── ⚡ 市场动能总监

第三阶段：风控团队（2个）
├── ⚠️ 系统性风险总监
└── ⚖️ 组合风险总监

第四阶段：总经理决策（1个）
└── 👑 投资决策总经理
```

## 🚀 快速开始

### 环境要求

- Python 3.8+
- Node.js 14+
- npm 或 yarn

### 安装步骤

1. **克隆项目**
```bash
git clone https://github.com/yourusername/investmind-pro.git
cd investmind-pro
```

2. **配置环境变量**
```bash
# 复制环境变量模板
cp .env.example .env

# 编辑.env文件，填入你的API密钥
# - Gemini API Key
# - DeepSeek API Key
# - 聚合数据 API Key
# - SiliconFlow API Key
# - 其他数据源API Key
```

3. **安装依赖**
```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装前端依赖
cd alpha-council-vue
npm install
```

4. **启动系统**

Windows用户：
```bash
# 一键启动前后端
start.bat
```

Mac/Linux用户：
```bash
# 启动后端
python backend/server.py

# 新终端启动前端
cd alpha-council-vue
npm run serve
```

5. **访问系统**
- 前端界面: http://localhost:8080
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 📖 使用说明

1. **输入股票代码**：在主界面输入6位股票代码（如：000001）
2. **点击分析**：系统自动启动10个智能体进行分析
3. **查看结果**：实时显示各智能体的分析结果
4. **生成报告**：所有分析完成后自动生成综合报告
5. **导出报告**：支持导出为MD/HTML/PDF格式

## 🛠️ 技术栈

### 后端
- **框架**：FastAPI
- **AI模型**：Gemini、DeepSeek、Qwen、SiliconFlow
- **数据源**：聚合数据、Finnhub、Tushare
- **异步处理**：asyncio、httpx

### 前端
- **框架**：Vue 3
- **UI组件**：自定义组件
- **状态管理**：Composition API
- **HTTP客户端**：Axios
- **样式**：TailwindCSS

## 📁 项目结构

```
InvestMind-Pro/
├── backend/                # 后端代码
│   ├── server.py          # FastAPI主程序
│   ├── agent_configs.json # 智能体配置
│   └── static/            # 静态资源
├── alpha-council-vue/      # Vue前端
│   ├── src/
│   │   ├── components/    # Vue组件
│   │   ├── views/         # 页面视图
│   │   └── App.vue        # 主应用
│   └── public/            # 公共资源
├── docs/                  # 项目文档
├── scripts/               # 脚本工具
├── .env                   # 环境变量
└── README.md             # 项目说明
```

## 🔑 API配置

系统支持多个AI模型和数据源，需要在`.env`文件中配置相应的API密钥：

| 服务 | 用途 | 获取地址 |
|------|------|----------|
| Gemini | AI分析模型 | https://aistudio.google.com/app/apikey |
| DeepSeek | AI分析模型 | https://platform.deepseek.com/api_keys |
| Qwen | AI分析模型（可选） | https://dashscope.console.aliyun.com/apiKey |
| 聚合数据 | 股票数据源 | https://www.juhe.cn/ |
| SiliconFlow | AI模型平台 | https://siliconflow.cn/account/ak |
| Finnhub | 国际市场数据（可选） | https://finnhub.io/dashboard |
| Tushare | A股数据（可选） | https://tushare.pro/register |

## 📊 功能特性

### 已实现
- ✅ 10智能体协同分析
- ✅ 多模型动态切换
- ✅ 实时打字机效果
- ✅ 综合报告生成
- ✅ 多格式报告导出
- ✅ 响应式UI设计
- ✅ API状态监控
- ✅ 样式自定义配置

### 开发中
- 🚧 历史记录保存
- 🚧 批量股票分析
- 🚧 策略回测系统
- 🚧 实时行情推送
- 🚧 投资组合管理

## 🤝 贡献指南

欢迎提交Issue和Pull Request！

## 📄 许可证

MIT License

## 🙏 致谢

感谢所有AI模型提供商和数据源提供商的支持。

---

**InvestMind Pro - 让投资决策更智能！** 🚀
