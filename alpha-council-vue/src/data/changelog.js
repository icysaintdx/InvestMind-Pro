/**
 * 更新日志数据
 * 统一管理所有版本信息，避免硬编码
 */

export const CURRENT_VERSION = '1.5.0'
export const CURRENT_CODENAME = '辩论系统全面增强版'

export const CHANGELOG_DATA = [
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
