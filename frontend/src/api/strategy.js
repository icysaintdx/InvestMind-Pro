/**
 * 策略中心API模块
 * 提供策略的CRUD操作、分析执行、信号生成等接口
 */

import request from '@/utils/request'

// ==================== 策略CRUD接口 ====================

/**
 * 获取策略列表
 * @param {Object} params - 查询参数
 * @param {string} params.category - 策略分类
 * @param {boolean} params.is_active - 是否激活
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 */
export function getStrategies(params = {}) {
  return request({
    url: '/api/strategy/list',
    method: 'get',
    params
  })
}

/**
 * 获取策略分类
 */
export function getCategories() {
  return request({
    url: '/api/strategy/categories',
    method: 'get'
  })
}

/**
 * 获取单个策略详情
 * @param {number} strategyId - 策略ID
 */
export function getStrategy(strategyId) {
  return request({
    url: `/api/strategy/${strategyId}`,
    method: 'get'
  })
}

/**
 * 创建新策略
 * @param {Object} data - 策略数据
 */
export function createStrategy(data) {
  return request({
    url: '/api/strategy/create',
    method: 'post',
    data
  })
}

/**
 * 更新策略
 * @param {number} strategyId - 策略ID
 * @param {Object} data - 更新数据
 */
export function updateStrategy(strategyId, data) {
  return request({
    url: `/api/strategy/${strategyId}`,
    method: 'put',
    data
  })
}

/**
 * 删除策略
 * @param {number} strategyId - 策略ID
 */
export function deleteStrategy(strategyId) {
  return request({
    url: `/api/strategy/${strategyId}`,
    method: 'delete'
  })
}

// ==================== 策略解析接口 ====================

/**
 * 解析策略文本
 * @param {Object} data - 解析请求
 * @param {string} data.text - 策略描述文本
 * @param {string} data.model_id - 模型ID（可选）
 */
export function parseStrategyText(data) {
  return request({
    url: '/api/strategy/parse',
    method: 'post',
    data
  })
}

/**
 * 解析策略文本并保存
 * @param {Object} data - 解析请求
 * @param {string} data.text - 策略描述文本
 * @param {string} data.model_id - 模型ID（可选）
 */
export function parseAndSaveStrategy(data) {
  return request({
    url: '/api/strategy/parse-and-save',
    method: 'post',
    data
  })
}

// ==================== 策略分析接口 ====================

/**
 * 使用策略分析股票
 * @param {Object} data - 分析请求
 * @param {number} data.strategy_id - 策略ID
 * @param {string} data.symbol - 股票代码
 * @param {string} data.model_id - 模型ID（可选）
 * @param {boolean} data.include_news - 是否包含新闻分析
 * @param {boolean} data.include_chart - 是否包含图表分析
 */
export function analyzeStock(data) {
  return request({
    url: '/api/strategy/analyze',
    method: 'post',
    data
  })
}

/**
 * 使用K线图截图进行分析
 * @param {FormData} formData - 包含图片和参数的表单数据
 */
export function analyzeWithImage(formData) {
  return request({
    url: '/api/strategy/analyze-with-image',
    method: 'post',
    data: formData,
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

// ==================== 信号历史接口 ====================

/**
 * 获取策略的历史信号
 * @param {number} strategyId - 策略ID
 * @param {Object} params - 查询参数
 * @param {string} params.symbol - 股票代码
 * @param {string} params.start_date - 开始日期
 * @param {string} params.end_date - 结束日期
 * @param {number} params.page - 页码
 * @param {number} params.page_size - 每页数量
 */
export function getStrategySignals(strategyId, params = {}) {
  return request({
    url: `/api/strategy/signals/${strategyId}`,
    method: 'get',
    params
  })
}

// ==================== 预设策略接口 ====================

/**
 * 获取预设策略列表
 * @param {string} category - 策略分类（可选）
 */
export function getPresetStrategies(category = null) {
  return request({
    url: '/api/strategy/preset/list',
    method: 'get',
    params: category ? { category } : {}
  })
}

/**
 * 导入预设策略
 * @param {string} name - 预设策略名称
 */
export function importPresetStrategy(name) {
  return request({
    url: `/api/strategy/preset/import/${encodeURIComponent(name)}`,
    method: 'post'
  })
}

/**
 * 导入所有预设策略
 */
export function importAllPresetStrategies() {
  return request({
    url: '/api/strategy/preset/import-all',
    method: 'post'
  })
}

// ==================== 辅助函数 ====================

/**
 * 格式化策略数据用于显示
 * @param {Object} strategy - 策略数据
 */
export function formatStrategyForDisplay(strategy) {
  return {
    ...strategy,
    categoryName: getCategoryName(strategy.category),
    indicatorCount: strategy.indicators?.length || 0,
    entryConditionCount: strategy.entry_conditions?.length || 0,
    exitConditionCount: strategy.exit_conditions?.length || 0,
    riskLevel: getRiskLevel(strategy.risk_params)
  }
}

/**
 * 获取分类名称
 * @param {string} category - 分类代码
 */
export function getCategoryName(category) {
  const categoryMap = {
    technical: '技术分析',
    fundamental: '价值投资',
    institutional: '机构跟踪',
    folk: '民间战法',
    ai: 'AI策略'
  }
  return categoryMap[category] || category
}

/**
 * 获取分类图标
 * @param {string} category - 分类代码
 */
export function getCategoryIcon(category) {
  const iconMap = {
    technical: '📊',
    fundamental: '📚',
    institutional: '🏛️',
    folk: '🎯',
    ai: '🤖'
  }
  return iconMap[category] || '📋'
}

/**
 * 获取风险等级
 * @param {Object} riskParams - 风险参数
 */
export function getRiskLevel(riskParams) {
  if (!riskParams) return 'medium'
  
  const stopLoss = riskParams.stop_loss || 0.05
  const maxPosition = riskParams.max_position || 0.3
  
  if (stopLoss <= 0.03 && maxPosition <= 0.2) {
    return 'low'
  } else if (stopLoss >= 0.1 || maxPosition >= 0.5) {
    return 'high'
  }
  return 'medium'
}

/**
 * 获取信号颜色
 * @param {string} signal - 信号类型
 */
export function getSignalColor(signal) {
  const colorMap = {
    BUY: '#52c41a',
    SELL: '#f5222d',
    HOLD: '#faad14'
  }
  return colorMap[signal] || '#1890ff'
}

/**
 * 获取信号文本
 * @param {string} signal - 信号类型
 */
export function getSignalText(signal) {
  const textMap = {
    BUY: '买入',
    SELL: '卖出',
    HOLD: '持有'
  }
  return textMap[signal] || signal
}

/**
 * 格式化置信度
 * @param {number} confidence - 置信度（0-1）
 */
export function formatConfidence(confidence) {
  return `${(confidence * 100).toFixed(1)}%`
}

/**
 * 验证策略数据
 * @param {Object} strategy - 策略数据
 */
export function validateStrategy(strategy) {
  const errors = []
  
  if (!strategy.name || strategy.name.trim() === '') {
    errors.push('策略名称不能为空')
  }
  
  if (!strategy.category) {
    errors.push('请选择策略分类')
  }
  
  if (!strategy.indicators || strategy.indicators.length === 0) {
    errors.push('至少需要配置一个指标')
  }
  
  if (!strategy.entry_conditions || strategy.entry_conditions.length === 0) {
    errors.push('至少需要配置一个入场条件')
  }
  
  if (!strategy.exit_conditions || strategy.exit_conditions.length === 0) {
    errors.push('至少需要配置一个出场条件')
  }
  
  return {
    valid: errors.length === 0,
    errors
  }
}

export default {
  getStrategies,
  getCategories,
  getStrategy,
  createStrategy,
  updateStrategy,
  deleteStrategy,
  parseStrategyText,
  parseAndSaveStrategy,
  analyzeStock,
  analyzeWithImage,
  getStrategySignals,
  getPresetStrategies,
  importPresetStrategy,
  importAllPresetStrategies,
  formatStrategyForDisplay,
  getCategoryName,
  getCategoryIcon,
  getRiskLevel,
  getSignalColor,
  getSignalText,
  formatConfidence,
  validateStrategy
}