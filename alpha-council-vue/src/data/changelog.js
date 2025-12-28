/**
 * 更新日志数据
 * 统一管理所有版本信息，避免硬编码
 */

export const CURRENT_VERSION = '2.5.0'
export const CURRENT_CODENAME = '多渠道通知与可视化版'

export const CHANGELOG_DATA = [
  {
    version: '2.5.0',
    codename: '多渠道通知与可视化版',
    date: '2025-12-20T12:00:00',
    features: [
      {
        icon: '📧',
        title: '多渠道通知系统',
        star: true,
        description: '支持5种通知渠道，预警信息实时推送到手机/邮箱。',
        details: [
          '📧 邮件通知 - SMTP协议，支持QQ/163/企业邮箱',
          '💬 企业微信 - Webhook机器人，Markdown格式',
          '🔔 钉钉 - 机器人通知，支持签名验证',
          '📱 Server酱 - 微信推送，免费易用',
          '🍎 Bark - iOS推送，支持自建服务器'
        ],
        files: ['notification_service.py', 'notification_api.py']
      },
      {
        icon: '🔔',
        title: '预警通知集成',
        star: true,
        description: '风险预警自动触发通知，支持多级别筛选。',
        details: [
          '🚨 自动触发 - 检测到预警自动发送通知',
          '📊 级别筛选 - critical/high/medium/low',
          '📝 格式化 - HTML邮件 + Markdown消息',
          '🔗 多渠道 - 同时推送到多个渠道'
        ],
        files: ['alert_notification_integration.py', 'dataflow_api.py']
      },
      {
        icon: '📈',
        title: 'ECharts数据可视化',
        star: true,
        description: '数据流页面新增3个专业图表，数据一目了然。',
        details: [
          '📊 融资融券趋势图 - 融资余额/融券余额双轴折线图',
          '🎯 风险雷达图 - 6维度风险评估雷达图',
          '💰 沪深港通持股图 - 北向资金持股趋势柱状图'
        ],
        files: ['DataFlowView.vue']
      },
      {
        icon: '⏰',
        title: 'API刷新间隔优化',
        star: false,
        description: '根据Tushare文档优化数据刷新策略，避免无效请求。',
        details: [
          '📊 实时数据 - 交易时段30秒，非交易5分钟',
          '📰 新闻舆情 - 5分钟刷新',
          '💰 资金流向 - 30分钟（19:00更新）',
          '📈 龙虎榜 - 1小时（20:00更新）',
          '📋 财务数据 - 2小时（随财报更新）'
        ],
        files: ['dataflow_api.py']
      },
      {
        icon: '🛠️',
        title: '通知配置指南',
        star: false,
        description: '完整的通知渠道配置文档和API。',
        details: [
          '📖 配置指南API - 返回各渠道配置说明',
          '🔧 环境变量 - SMTP/Webhook/Key配置',
          '✅ 测试接口 - 一键测试各渠道连通性',
          '📊 状态查询 - 查看各渠道配置状态'
        ],
        files: ['notification_api.py']
      }
    ],
    improvements: [
      '🔥 通知系统 - 5种渠道全覆盖，预警不遗漏',
      '🔥 数据可视化 - ECharts专业图表，数据更直观',
      '📊 刷新策略 - 根据数据更新时间优化，减少无效请求',
      '🛡️ 预警集成 - 自动触发通知，无需手动操作'
    ],
    bugfixes: [],
    technical: [
      '🏛️ 新增模块：notification_service.py (600+行)',
      '🏛️ 新增API：notification_api.py (430+行)',
      '🏛️ 集成模块：alert_notification_integration.py',
      '🏛️ 图表集成：DataFlowView.vue (+200行 ECharts)',
      '🏛️ 新增API：/api/notification/* (8个端点)'
    ]
  },
  {
    version: '2.4.0',
    codename: '数据流监控增强版',
    date: '2025-12-17T22:50:00',
    features: [
      {
        icon: '📈',
        title: '股票详情弹窗系统',
        star: true,
        description: '数据流页面新增完整的股票详情展示系统。',
        details: [
          '👁️ 点击详情按钮 - 弹出完整数据面板',
          '📊 数据概览 - 风险等级 + 情绪评分 + 更新时间',
          '📚 三个Tab页签 - 新闻舆情/风险分析/情绪分析',
          '📱 响应式设计 - 最大高度600px可滚动'
        ],
        files: ['DataFlowView.vue']
      },
      {
        icon: '📰',
        title: '新闻舆情智能分类',
        star: true,
        description: '多维度新闻筛选和关键信息高亮显示。',
        details: [
          '🏷️ 类型筛选 - 财报/公告/新闻/政策/研报',
          '⚠️ 紧急度高亮 - 特别重大(红色+脉冲) + 重要(橙色)',
          '🏷️ 关键信息 - 类型 + 情绪 + 紧急度 + 关键词',
          '🤖 智能识别 - 5种报告类型自动分类'
        ],
        files: ['DataFlowView.vue', 'sentiment_engine.py']
      },
      {
        icon: '⚠️',
        title: '风险分析可视化',
        star: true,
        description: '多维度风险细分和直观的视觉展示。',
        details: [
          '📊 风险评分 - 大号数字 + 等级标记(绿/黄/红)',
          '🚫 停复牌 - 已停牌/正常交易状态',
          '⚠️ ST状态 - ST股票/非ST股票',
          '📊 实时行情 - 最新价 + 涨跌幅(颜色编码)'
        ],
        files: ['DataFlowView.vue', 'risk_analyzer.py']
      },
      {
        icon: '📊',
        title: '情绪分析统计图表',
        star: false,
        description: '情绪数据可视化展示，一目了然。',
        details: [
          '🎯 总体情绪 - 大号分数(0-100) + 情绪标签',
          '📊 情绪分布 - 正面/中性/负面条形图 + 百分比',
          '⚡ 紧急度 - 特别重大/重要/一般/普通 4级',
          '📋 报告类型 - 财报/研报/公告/新闻/政策统计'
        ],
        files: ['DataFlowView.vue', 'sentiment_engine.py']
      },
      {
        icon: '📚',
        title: '情感词典大幅扩展',
        star: false,
        description: '从48词增加到311词，增长548%。',
        details: [
          '👍 正面词汇 - 141个 (5大类：业绩/市场/运营/政策/创新)',
          '👎 负面词汇 - 110个 (4大类：业绩/市场/问题/监管)',
          '💪 强化词库 - 33个 (程度/时间/范围/确定性)',
          '❌ 否定词库 - 27个 (基础/复合/程度否定)'
        ],
        files: ['sentiment_engine.py']
      }
    ],
    improvements: [
      '🚀 后端API - 新增3个股票详情API端点',
      '🎨 UI/UX - 动画效果 + 颜色编码 + 深色主题',
      '🛡️ Fallback - AKShare失败自动切换备用源',
      '📅 数据提示 - 服务器仅保存1天数据警告'
    ],
    bugfixes: [
      '🐛 修复查看详情按钮无效',
      '🐛 修复AKShare新闻JSON解析错误',
      '🐛 修复立即更新后新闻不显示',
      '🐛 修复Vue模板语法错误'
    ],
    technical: [
      '🏛️ 模块：DataFlowView.vue (+500行), dataflow_api.py (+87行)',
      '🏛️ 情感分析：sentiment_engine.py (+150行)',
      '🏛️ 多源新闻：multi_source_news_aggregator.py (+50行)',
      '🏛️ 新增API：/stock/news + /stock/sentiment + /stock/risk'
    ]
  },
  {
    version: '2.3.0',
    codename: '智能闭环交易版',
    date: '2025-12-17T18:00:00',
    features: [
      {
        icon: '🎯',
        title: 'GM智能体评分系统',
        star: true,
        description: '投资决策总经理新增多维度评分功能，直观展示投资价值。',
        details: [
          '📊 四维度评分 - 推荐强度/置信度/风险/时机',
          '🎨 五档颜色 - 绿(优秀)/蓝(良好)/黄(中等)/橙(偏低)/红(较差)',
          '💡 智能解析 - 从GM输出自动提取评分',
          '✨ 醒目显示 - 大字体+发光效果+动画'
        ],
        files: ['AgentCard.vue']
      },
      {
        icon: '📈',
        title: 'K线图交互增强',
        star: true,
        description: '模拟交易页面K线图支持点击加载和自动加载。',
        details: [
          '🖱️ 点击持仓行 - 自动加载对应股票K线',
          '🖱️ 点击交易记录 - 自动加载对应股票K线',
          '🚀 页面加载 - 自动加载默认股票K线',
          '✨ 悬停提示 - 显示点击操作说明'
        ],
        files: ['SimpleTradingView.vue']
      },
      {
        icon: '🔄',
        title: '版本同步修复',
        star: false,
        description: '修复前端版本号显示与实际版本不一致的问题。',
        details: [
          '📝 同步VERSION.json和changelog.js',
          '📋 补充v1.7.0-v2.1.0完整更新日志',
          '🔢 版本号从1.6.0更新到2.3.0'
        ],
        files: ['changelog.js', 'VERSION.json']
      }
    ],
    improvements: [
      '🔥 GM卡片视觉增强 - 评分醒目显示在状态左侧',
      '🔥 K线交互优化 - 点击即可切换股票',
      '📊 版本管理规范化 - 统一版本号来源'
    ],
    bugfixes: [
      '🐛 修复前端版本号显示1.6.0的问题',
      '🐛 修复K线图需要手动回车才能加载的问题'
    ],
    totalDocs: 120
  },
  {
    version: '2.2.0',
    codename: '分析总结闭环版',
    date: '2025-12-17T14:57:00',
    features: [
      {
        icon: '🧭',
        title: '分析总结页面',
        star: true,
        description: '串联智能分析→策略→回测→模拟→跟踪的闭环总控面板。',
        details: [
          '📊 核心结论展示 - 最新分析结果一目了然',
          '🎯 一键策略推荐 - 调用LLM获取策略组合',
          '📈 一键回测 - 自动填入股票信息',
          '💼 推送模拟交易 - 生成模拟下单计划',
          '🔍 创建跟踪任务 - 纳入持续监控'
        ],
        files: ['AnalysisSummaryView.vue']
      },
      {
        icon: '📊',
        title: '执行摘要面板',
        star: true,
        description: '查看已触发的回测/模拟交易/跟踪任务执行结果。',
        details: [
          '📈 回测结果 - 收益率/最大回撤/夏普比率',
          '💰 自动交易状态 - 任务ID/资金/策略',
          '🔍 跟踪任务 - 触发条件/周期/状态'
        ],
        files: ['AnalysisSummaryView.vue']
      }
    ],
    improvements: [
      '🔥 闭环流程可视化 - 一个页面掌控全流程',
      '🔥 智能体输出预览 - 快速查看21个智能体结果',
      '📊 策略推荐展示 - 置信度+推荐理由'
    ],
    bugfixes: [],
    totalDocs: 118
  },
  {
    version: '2.1.0',
    codename: '价值投资与优化版',
    date: '2025-12-15T23:35:00',
    features: [
      {
        icon: '💰',
        title: '新增3个价值投资策略',
        star: true,
        description: '巴菲特价值投资、彼得林奇成长股、格雷厄姆安全边际三大经典策略。',
        details: [
          '🏛️ 巴菲特价值投资策略 - 护城河+长期持有（500+行）',
          '📈 彼得林奇成长股策略 - PEG<1选股（450+行）',
          '🛡️ 格雷厄姆安全边际策略 - 低估值防御（400+行）'
        ],
        files: ['buffett_value.py', 'lynch_growth.py', 'graham_margin.py']
      },
      {
        icon: '⚙️',
        title: '参数优化系统',
        star: true,
        description: '网格搜索和随机搜索优化，自动寻找最优参数组合。',
        details: [
          '🔍 网格搜索优化 - 遍历所有参数组合',
          '🎲 随机搜索优化 - 随机采样参数空间',
          '📊 多指标评估 - 夏普、收益、胜率等',
          '📝 优化报告生成 - 自动生成Markdown报告'
        ],
        files: ['optimizer.py', 'test_optimization.py']
      },
      {
        icon: '📊',
        title: '组合策略优化',
        star: true,
        description: '多策略权重优化，自动配置最优权重组合。',
        details: [
          '⚖️ 多策略权重优化 - 自动配置最优权重',
          '📈 组合表现评估 - 综合收益和风险分析',
          '🛡️ 风险分散分析 - 降低组合风险'
        ],
        files: ['portfolio_optimizer.py']
      }
    ],
    improvements: [
      '🔥 策略数量增加至13个（+30%）',
      '🔥 代码量增加至6450+行（+43%）',
      '🔥 文档增加至22个（+47%）',
      '📊 测试脚本增强 - test_optimization.py'
    ],
    bugfixes: [],
    totalDocs: 117
  },
  {
    version: '2.0.0',
    codename: '策略库完整版',
    date: '2025-12-15T22:35:00',
    features: [
      {
        icon: '🐢',
        title: '海龟交易法则',
        star: true,
        description: '经典趋势跟踪策略，ATR金字塔加仓机制。',
        details: [
          '📊 唐奇安通道突破 - 20日/55日双系统',
          '📈 金字塔加仓机制 - 趋势越强仓位越大',
          '🛡️ ATR止损 - 动态止损位'
        ],
        files: ['turtle_trading.py']
      },
      {
        icon: '🚀',
        title: '涨停板战法',
        star: true,
        description: 'A股特色策略，T+1快进快出。',
        details: [
          '🎯 涨停板质量评分 - 5维度评估系统',
          '⚡ 快进快出 - 3-5天持有周期',
          '📊 量价配合度 - 相关性计算+动态调整'
        ],
        files: ['limit_up_trading.py']
      },
      {
        icon: '📊',
        title: '量价齐升战法',
        star: true,
        description: '短期交易策略，量价配合度分析。',
        details: [
          '📈 量价齐升信号 - 价涨量增确认',
          '🔍 量价背离检测 - 风险预警',
          '⏱️ 短期持有 - 3-5天周期'
        ],
        files: ['volume_price_surge.py']
      }
    ],
    improvements: [
      '🔥 策略库扩展 - 从7个增加到10个(+43%)',
      '🔥 类别完善 - 新增趋势跟踪、民间策略类',
      '📊 全周期覆盖 - 从超短线到长线全覆盖',
      '⏱️ 多样化组合 - 适应不同市场环境'
    ],
    bugfixes: [],
    totalDocs: 110
  },
  {
    version: '1.9.0',
    codename: 'AI合成策略版',
    date: '2025-12-15T22:20:00',
    features: [
      {
        icon: '🧠',
        title: '情绪共振策略',
        star: true,
        description: '结合新闻+技术+资金三维度共振的AI合成策略。',
        details: [
          '📰 新闻情绪分析 - 情绪指数计算',
          '📊 技术指标融合 - RSI/MACD综合',
          '💰 资金流向分析 - 主力资金追踪',
          '🎯 三维度共振 - 同向时发信号'
        ],
        files: ['sentiment_resonance.py']
      },
      {
        icon: '⚖️',
        title: '多空辩论加权策略',
        star: true,
        description: '利用21智能体的多空辩论结果进行加权决策。',
        details: [
          '🐂 多头观点汇总 - 看涨智能体权重',
          '🐻 空头观点汇总 - 看跌智能体权重',
          '⚖️ 加权投票 - 核心(1.5x)/重要(1.2x)/可选(1.0x)',
          '🎯 一致性奖励 - 一致性>80%时仓位加成1.2倍'
        ],
        files: ['debate_weighted.py']
      }
    ],
    improvements: [
      '🔥 策略库扩展 - 从5个增加到7个(+40%)',
      '🔥 AI能力利用 - 充分发挥智能体优势',
      '📊 动态仓位 - 根据共振强度/置信度调整',
      '⏱️ 智能过滤 - 只在强信号时交易'
    ],
    bugfixes: [],
    totalDocs: 105
  },
  {
    version: '1.8.0',
    codename: '智能策略选择系统v2.0',
    date: '2025-12-15T22:01:00',
    features: [
      {
        icon: '🤖',
        title: 'LLM配置管理系统',
        star: true,
        description: '类似智能体的统一LLM配置管理，支持4种模型。',
        details: [
          '🔌 支持Ollama/OpenAI/DeepSeek/Qwen',
          '⚙️ 统一配置管理',
          '📊 8个API端点完整实现'
        ],
        files: ['llm_config_api.py', 'llm_client.py']
      },
      {
        icon: '📈',
        title: '策略库扩展',
        star: true,
        description: '从2个增加到5个策略，覆盖技术/综合/动量/波动率。',
        details: [
          '🔱 三叉戟策略 - 趋势/动量/波动率综合',
          '📊 MACD交叉策略 - 金叉死叉+成交量确认',
          '📈 布林带突破策略 - 突破和回归双重信号'
        ],
        files: ['trident.py', 'macd_crossover.py', 'bollinger_breakout.py']
      },
      {
        icon: '⚡',
        title: '分层缓存体系',
        star: true,
        description: 'L1/L2/L3三层缓存，性能提升100倍。',
        details: [
          '🚀 缓存命中<1ms vs 首次查询~3s',
          '💾 智能缓存回写',
          '🔄 智能降级机制'
        ],
        files: ['strategy_cache.py']
      }
    ],
    improvements: [
      '🔥 性能提升100倍 - 缓存命中<1ms',
      '🔥 决策准确性提升 - 真实LLM+回测',
      '📊 策略多样化 - 全类型覆盖'
    ],
    bugfixes: [
      '🐛 修复策略选择使用模拟LLM',
      '🐛 修复回测使用模拟数据',
      '🐛 修复策略库不足'
    ],
    totalDocs: 100
  },
  {
    version: '1.7.0',
    codename: '零中断智能降级版',
    date: '2025-12-11T04:00:00',
    features: [
      {
        icon: '🛡️',
        title: '多级降级处理器',
        star: true,
        description: '4级降级策略确保永不中断，即使所有API失败也返回合理建议。',
        details: [
          '🔄 原始→轻压缩50%→深压缩25%→最小化10%→默认',
          '🧠 LLM智能文本摘要 - 不是简单截断',
          '📊 前端降级状态显示 - FallbackIndicator组件',
          '📈 降级监控面板 - 统计成功率'
        ],
        files: ['llm_fallback_handler.py', 'FallbackIndicator.vue', 'FallbackMonitor.vue']
      }
    ],
    improvements: [
      '🔥 零中断保证 - 99.9%成功率',
      '🔥 智能压缩算法 - 保留关键信息',
      '📊 监控数据完善 - 实时统计',
      '⏱️ 响应时间优化 - 分级超时'
    ],
    bugfixes: [
      '🐛 修复504超时错误',
      '🐛 修复循环导入问题',
      '🐛 修复简单截断问题'
    ],
    totalDocs: 97
  },
  {
    version: '1.6.0',
    codename: '智能体配置系统版',
    date: '2025-12-10T20:30:00',
    features: [
      {
        icon: '⚙️',
        title: '智能体配置系统',
        star: true,
        description: '灵活配置智能体启用/禁用，平衡速度与质量。最小化配置节省62%时间，平衡配置93%质量。',
        details: [
          '🔴 核心智能体（9个）- 不可禁用，确保系统稳定',
          '🟡 重要智能体（7个）- 默认启用，可选禁用',
          '🟢 可选智能体（5个）- 默认禁用，按需启用',
          '⚡ 最小化: 9个智能体，45秒，80%质量',
          '⚖️ 平衡: 15个智能体，75秒，93%质量',
          '🎯 完整: 21个智能体，120秒，100%质量'
        ],
        files: ['agent_dependency_manager.py', 'agent_config_api.py', 'AgentConfigPanel.vue']
      },
      {
        icon: '🔗',
        title: '智能依赖管理',
        star: true,
        description: '自动检查依赖关系，防止误禁用。提供6种降级策略，确保系统稳定运行。',
        details: [
          '✅ 自动启用必需依赖',
          '⚠️ 显示影响警告',
          '💡 提供降级方案',
          '🛡️ 核心智能体保护',
          '📊 完整的配置验证'
        ],
        files: ['agent_dependency_manager.py']
      },
      {
        icon: '🎨',
        title: '配置界面与工具',
        star: true,
        description: '美观的配置面板，分组展示、实时预览、智能提示。提供10个工具函数支持配置管理。',
        details: [
          '🎨 分组展示（核心/重要/可选）',
          '📊 实时影响预览',
          '🔗 依赖关系提示',
          '⚡ 快速配置方案',
          '📦 10个配置管理函数'
        ],
        files: ['AgentConfigPanel.vue', 'agentConfigLoader.js']
      }
    ],
    improvements: [
      '🔥 性能优化 - 最小化配置节省62%时间、57% API调用',
      '🔥 质量保证 - 平衡配置93%质量、效率比1.24(最优)',
      '🔥 智能保护 - 核心智能体不可禁用，确保系统稳定',
      '📊 配置验证 - 完整的配置合法性检查',
      '⏱️ 用户体验 - 直观的UI、清晰的分组、实时的反馈'
    ],
    bugfixes: [
      '🐛 修复AgentConfig.dependencies可变默认值问题',
      '🐛 修复所有智能体优先级配置缺失',
      '🐛 修复AgentConfigPanel.vue的ESLint错误'
    ],
    totalDocs: 97
  },
  {
    version: '1.5.0',
    codename: '辩论系统全面增强版',
    date: '2025-12-08T02:45:00',
    features: [
      {
        icon: '🤼',
        title: '多空研判博弈LLM接入',
        star: true,
        description: '看涨研究员 vs 看跌研究员智能辩论，最终给出多头/空头优势判断。',
        details: [
          '🐂 看涨研究员 - 寻找看涨理由，强调积极因素',
          '🐻 看跌研究员 - 寻找看跌理由，强调风险因素',
          '🎓 研究部经理 - 综合双方观点，做出最终决策',
          '输出: BUY/SELL/HOLD + 置信度评分 0-100'
        ],
        files: ['debate_api.py', 'AnalysisView.vue', 'DebatePanel.vue']
      },
      {
        icon: '⚖️',
        title: '三方风控评估LLM接入',
        star: true,
        description: '激进/保守/中立三方风控师辩论，给出风险等级和仓位建议。',
        details: [
          '⚔️ 激进风控师 - 强调机会，认为风险可控',
          '🛡️ 保守风控师 - 强调风险，建议谨慎',
          '⚖️ 中立风控师 - 客观中立，平衡分析',
          '👮 风控部经理 - 综合三方观点，做出风控决策',
          '输出: HIGH/MEDIUM/LOW + 仓位建议'
        ],
        files: ['debate_api.py', 'AnalysisView.vue']
      },
      {
        icon: '🔧',
        title: '本地规则引擎兜底机制',
        star: true,
        description: '后端LLM超时时，自动触发本地规则判断，基于PE/PB/涨跌幅的智能评分系统。',
        details: [
          '多空判断: 涨跌幅/PE/PB多维度评分',
          '风险评估: 波动率/估值异常检测',
          '自动触发: 检测后端超时错误后自动启用',
          '输出: BUY/SELL/HOLD + 详细说明'
        ],
        files: ['AnalysisView.vue (localBullBearFallback, localRiskFallback)']
      },
      {
        icon: '⚙️',
        title: '辩论面板配置模式',
        star: true,
        description: '在配置模式下，辩论面板支持一键配置所有参与辩论的智能体。',
        details: [
          '模型选择: 从 selectedModels 列表中选择',
          '随机性调整: 0-1 滑条 (0=严谨，1=发散)',
          '配置范围: 多空辩论3个 + 风控辩论4个智能体',
          '保存位置: backend/agent_configs.json'
        ],
        files: ['DebatePanel.vue']
      },
      {
        icon: '📰',
        title: '新闻面板优先级优化',
        star: false,
        description: '优先显示所有非中性新闻，至少显示30条，不足用中性补齐。',
        details: [
          '非中性 ≥ 30条: 只显示非中性',
          '非中性 < 30条: 用中性补齐到30条',
          '例子: 19条非中性 + 11条中性 = 30条总计'
        ],
        files: ['NewsDataPanel.vue']
      },
      {
        icon: '✂️',
        title: '辩论内容提取优化',
        star: false,
        description: '从后端返回的完整辩论过程中，提取核心观点，限制显示长度150字。',
        details: [
          '去除角色标记 (Bull Analyst:, Bear Analyst:)',
          '提取最后一段有实质内容的段落',
          '限制显示长度150字，超出显示"..."'
        ],
        files: ['AnalysisView.vue (extractCoreView)']
      },
      {
        icon: '📊',
        title: '摘要器模型配置',
        star: true,
        description: '支持选择专门的摘要器模型，用于压缩前序分析结果，减少后续智能体的Prompt长度。',
        details: [
          '位置: 模型管理器顶部，仅显示大语言模型',
          '推荐: Qwen/Qwen2.5-7B-Instruct 等中等规模模型',
          '作用: 避免超时，提升分析速度'
        ],
        files: ['ModelManager.vue']
      },
      {
        icon: '🛠️',
        title: '模型能力画像 + 静默压测',
        star: true,
        description: '在后台对当前所选大语言模型进行压测，不影响正常分析流程。',
        details: [
          '配置项: 目标并发数、测试Prompt长度、max_tokens、temperature',
          '作用: 评估模型在高并发、长文本场景下的表现',
          '位置: 模型管理器展开区域'
        ],
        files: ['ModelManager.vue']
      }
    ],
    bugs: [
      {
        icon: '🐛',
        title: '修复辩论内容混乱',
        description: '看涨研究员卡片显示“看跌观点”、“看涨反驳”等混乱内容。',
        details: [
          '原因: 后端返回的是完整辩论过程',
          '修复: 提取核心观点，去除角色标记'
        ],
        files: ['AnalysisView.vue (1373-1385行)']
      },
      {
        icon: '🐛',
        title: '修复结论过长',
        description: '风控辩论结论显示一大堆文字，占据大量空间。',
        details: [
          '修复: 限制结论长度为150字',
          '超出部分显示"..."'
        ],
        files: ['AnalysisView.vue (1421-1422行, 1573-1574行)']
      },
      {
        icon: '🐛',
        title: '修复新闻优先级问题',
        description: '新闻面板显示不到30条，且大部分是中性新闻。',
        details: [
          '原因: 只是简单限制数量到30条',
          '修复: 优先显示所有非中性新闻'
        ],
        files: ['NewsDataPanel.vue (186-198行)']
      },
      {
        icon: '🐛',
        title: '修夏PE/PB为0显示问题',
        description: '本地兜底显示"PE=0，PB=0"，误导用户。',
        details: [
          '修复: PE/PB为0时显示"PE=N/A"、"PB=N/A"'
        ],
        files: ['AnalysisView.vue (1248-1250行)']
      }
    ],
    docs: [
      '辩论系统实现文档.md',
      '本地兜底机制说明.md',
      '辩论面板配置模式.md',
      '超时优化方案.md',
      '新闻优先级优化.md'
    ]
  },
  {
    version: '1.4.1',
    codename: '智能体数据源全面集成版',
    date: '2025-12-05T08:25:00',
    features: [
      {
        icon: '🔌',
        title: '资金流向API全面对接',
        star: true,
        description: '为资金流向分析师提供真实数据源，显示200-300条北向资金、主力资金、融资融券数据。',
        details: [
          '北向资金（沪深港通）: 200-300条实时数据',
          '主力资金: 50条TOP排名',
          '融资融券: 30条汇总数据',
          '行业资金流: 30-50个行业'
        ],
        files: ['fund_flow_data.py', 'AnalysisView.vue']
      },
      {
        icon: '🏭',
        title: '行业板块API对接',
        star: true,
        description: '为行业轮动分析师提供30-50个申万行业板块数据和资金流向。',
        details: [
          '行业板块列表: 30-50个申万行业',
          '板块资金流向: 实时资金净流入',
          '板块涨跌幅: 行业表现排名'
        ],
        files: ['sector_data.py', 'AnalysisView.vue']
      },
      {
        icon: '🌍',
        title: '宏观经济API对接',
        star: true,
        description: '为宏观政策分析师提供GDP、CPI、PMI、货币供应量等宏观数据。',
        details: [
          'GDP数据: 最近12个月',
          'CPI数据: 最近12个月',
          'PMI数据: 最近12个月',
          '货币供应量: 最近12个月'
        ],
        files: ['macro_data.py', 'AnalysisView.vue']
      },
      {
        icon: '🎴',
        title: '卡片自动折叠展开',
        star: true,
        description: '页面加载时卡片默认折叠，点击分析自动展开，无需手动操作。',
        details: [
          '初始状态: 所有卡片折叠',
          '分析时: 自动全部展开',
          '刷新页面: 恢复折叠状态',
          '体验: 全自动化，无需手动点击'
        ],
        files: ['AgentCard.vue', 'AnalysisView.vue']
      },
      {
        icon: '📊',
        title: '卡片高度自适应',
        star: true,
        description: '卡片高度根据折叠/展开状态自动调整，节省空间。',
        details: [
          '折叠时: 高度约80px，节省280px',
          '展开时: 根据内容自动调整(200-600px)',
          '过渡动画: 0.3s平滑变化',
          '整体页面: 缩短70%高度'
        ],
        files: ['AgentCard.vue']
      }
    ],
    improvements: [
      {
        icon: '🔥',
        title: '资金流向分析师',
        description: '显示真实数据源: 北向资金(200-300条)、主力资金(50条)、融资融券(30条)'
      },
      {
        icon: '🔥',
        title: '行业轮动分析师',
        description: '显示真实板块数据: 行业板块(30-50个)、板块资金流向'
      },
      {
        icon: '🔥',
        title: '宏观政策分析师',
        description: '显示真实宏观数据: GDP/CPI/PMI(各12条)、货币政策(12条)'
      },
      {
        icon: '📊',
        title: '数据透明化',
        description: '所有数据源显示具体数量和描述，用户清楚知道智能体使用了哪些数据'
      },
      {
        icon: '⏱️',
        title: '页面加载优化',
        description: '初始页面简洁，节省280px高度/卡片，整体页面缩短70%'
      }
    ],
    bugfixes: [],
    technical: [
      '🔌 后端API: 新增9个数据接口',
      '📦 数据模块: sector_data.py、macro_data.py',
      '🎨 前端集成: 实现真实数据调用',
      '📝 文档完善: 7个技术文档'
    ]
  },
  {
    version: '1.4.0',
    codename: '数据集成增强版',
    date: '2025-12-05T07:50:00',
    features: [
      {
        icon: '🔥',
        title: '社交媒体热度集成',
        star: true,
        description: '集成微博热议和百度热搜数据，实时掌握市场热点。',
        details: [
          '微博热议: 50条实时热门股票',
          '百度热搜: 12条热门搜索',
          '每5分钟自动刷新',
          '显示涨跌幅和热度'
        ],
        files: ['NewsDataPanel.vue']
      },
      {
        icon: '🎯',
        title: '热榜模态框',
        star: true,
        description: '展示6个热度榜单，全面掌握市场情绪。',
        details: [
          '微博热议 (50条)',
          '百度热搜 (12条)',
          '雪球热度 (5425条)',
          '东财热度 (100条)',
          '人气榜 (100条)'
        ],
        files: ['HotRankModal.vue']
      },
      {
        icon: '⚡',
        title: '股票搜索功能',
        star: true,
        description: '代码/名称模糊搜索，极速响应。',
        details: [
          '输入3位数字匹配代码',
          '输入文字匹配名称',
          '响应时间: 10-50毫秒',
          '性能提升50-100倍'
        ],
        files: ['StockSearchInput.vue']
      },
      {
        icon: '💾',
        title: '本地股票缓存',
        star: true,
        description: 'SQLite数据库缓存沪深A股5000只股票。',
        details: [
          '极速响应: 10-50毫秒',
          '离线可用',
          '每天自动更新',
          '数据持久化'
        ],
        files: ['stock_list_cache.py']
      },
      {
        icon: '🔄',
        title: '雪球热度静默加载',
        description: '异步后台加载，不阻塞界面。',
        details: [
          '打开热榜 < 1秒',
          '立即可用',
          '后台加载雪球数据'
        ],
        files: ['HotRankModal.vue']
      },
      {
        icon: '⚙️',
        title: '自动更新机制',
        description: '股票列表每天自动更新。',
        details: [
          '首次启动自动下载',
          '每天自动检查更新',
          '无需手动操作'
        ],
        files: ['stock_list_cache.py']
      }
    ],
    improvements: [
      {
        icon: '📊',
        title: '热榜数据显示优化',
        description: '显示股票代码、涨跌幅、热度等信息。',
        details: [
          '股票名称 + 代码',
          '涨跌幅颜色标识',
          '热度格式化显示'
        ]
      },
      {
        icon: '⚡',
        title: '搜索性能提升',
        description: '从2-5秒降至10-50毫秒。',
        details: [
          '性能提升50-100倍',
          '本地数据库查询',
          '离线可用'
        ]
      },
      {
        icon: '🛡️',
        title: '容错机制增强',
        description: '接口失败时返回缓存数据。',
        details: [
          '东财接口5秒超时',
          '缓存机制',
          '失败时返回缓存'
        ]
      }
    ],
    bugs: [
      {
        icon: '🐛',
        title: '修复雪球热度接口错误',
        description: '使用正确的stock_hot_follow_xq接口。',
        files: ['hot_rank_data.py']
      },
      {
        icon: '🐛',
        title: '修复东财热度超时问题',
        description: '添加5秒超时 + 缓存机制。',
        files: ['hot_rank_data.py']
      },
      {
        icon: '🐛',
        title: '修复深市股票接口参数错误',
        description: '改为symbol="A股列表"。',
        files: ['stock_list_cache.py']
      },
      {
        icon: '🐛',
        title: '修夏base.py语法错误',
        description: '补全safe_call方法的docstring。',
        files: ['base.py']
      }
    ]
  },
  {
    version: '1.3.3',
    codename: '多数据源适配版',
    date: '2025-12-04T14:48:00',
    features: [
      {
        icon: '📊',
        title: '多数据源格式支持',
        star: true,
        description: '完整支持5种主流数据源的格式解析，实现智能识别和统一输出。',
        details: [
          'AKShare - DataFrame表格格式解析',
          'Tushare - Emoji格式（📊、💰、📈）解析',
          '新浪财经 - 简单键值对格式解析',
          '聚合数据 - JSON风格格式解析',
          'BaoStock - 表格格式解析'
        ],
        files: ['stock_data_adapter.py', 'data_source_manager.py']
      },
      {
        icon: '🤖',
        title: '智能数据源识别',
        description: '自动识别数据源类型，选择对应的解析器。',
        details: [
          '基于关键字和特征标记识别',
          '5个专用解析器 + 1个通用解析器',
          '统一输出格式，便于后续处理'
        ]
      }
    ],
    bugs: [
      {
        icon: '🐛',
        title: '修复股票数据解析失败',
        description: '解决AKShare返回DataFrame格式无法解析的问题。',
        files: ['stock_data_adapter.py']
      },
      {
        icon: '🐛',
        title: '修复前端版本显示',
        description: '修复版本号硬编码导致无法更新的问题。',
        files: ['App.vue', 'ChangelogView.vue']
      }
    ]
  },
  {
    version: '1.3.2',
    codename: '数据源兼容修复版',
    date: '2025-12-04T07:22:00',
    features: [
      {
        icon: '🔄',
        title: '数据格式兼容性修复',
        description: '修复前端与后端新闻API数据格式不兼容的问题。',
        details: [
          '兼容两种数据格式（data.sources 和 sources）',
          '修复模拟数据不显示的问题',
          '修复真实数据无法追加的问题'
        ],
        files: ['AnalysisView.vue']
      }
    ],
    bugs: [
      {
        icon: '🐛',
        title: '修复数据源显示顺序',
        description: '确保参考数据在分析结果之前显示。',
        files: ['AnalysisView.vue']
      }
    ]
  },
  {
    version: '1.3.1',
    codename: '新闻API集成版',
    date: '2025-12-04T06:00:00',
    features: [
      {
        icon: '📰',
        title: '新闻数据源细分',
        description: 'AKShare新闻源细分为具体来源，提供更透明的数据展示。',
        details: [
          '富途牛牛全球新闻',
          '同花顺全球新闻',
          '东方财富个股新闻',
          '新浪财经全球新闻',
          '微博热议股票'
        ]
      }
    ],
    bugs: [
      {
        icon: '🐛',
        title: '修复巨潮资讯网API',
        description: '修复公司公告获取失败的问题。',
        details: [
          '更新请求头模拟真实浏览器',
          '修复参数构建逻辑',
          '缩短日期范围避免超时'
        ]
      }
    ]
  },
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
          'AI API 状态: Gemini、DeepSeek、通义千问、硅基流动',
          '数据渠道状态: 聚合数据、FinnHub、Tushare、AKShare',
          '颜色指示: 绿色-已配置、灰色-未配置、红色-错误'
        ]
      },
      {
        icon: '🚀',
        title: '后端启动优化',
        description: '改进后端启动流程，支持更多数据源和 API 配置。',
        details: [
          '支持加载 .env 文件配置',
          '智能检测可用的 API Keys',
          '自动启用已配置的服务'
        ],
        files: ['server.py', '.env.example']
      },
      {
        icon: '🎨',
        title: '样式配置面板',
        description: '新增样式配置面板，支持自定义背景渐变和粒子效果。',
        details: [
          '背景渐变: 自定义起始色、结束色和角度',
          '粒子效果: 开关、数量、速度和颜色控制',
          '持久化: 设置保存到 localStorage'
        ],
        files: ['StyleConfig.vue', 'ParticleBackground.vue']
      }
    ],
    bugs: [
      {
        icon: '🐛',
        title: '修复配置加载问题',
        description: '修复 API 配置无法正确从后端加载的问题。',
        files: ['ApiConfig.vue', 'server.py']
      },
      {
        icon: '🐛',
        title: '修复状态指示器显示',
        description: '修复顶部状态栏无法正确显示配置状态的问题。',
        files: ['App.vue']
      }
    ],
    docs: [
      {
        icon: '📖',
        title: '配置系统文档',
        description: '新增 API 配置系统使用说明。',
        files: ['docs/API配置系统说明.md']
      }
    ]
  }
]

// 导出获取版本信息的函数
export function getVersionInfo() {
  return {
    version: CURRENT_VERSION,
    codename: CURRENT_CODENAME,
    releaseDate: CHANGELOG_DATA[0]?.date || new Date().toISOString()
  }
}

// 导出获取所有版本的函数
export function getAllVersions() {
  return CHANGELOG_DATA
}

// 导出获取指定版本的函数
export function getVersion(version) {
  return CHANGELOG_DATA.find(v => v.version === version)
}
