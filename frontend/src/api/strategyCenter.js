/**
 * 策略中心 API 调用模块
 * 提供策略管理、LLM解析、信号生成等功能
 */

import axios from 'axios'

const API_BASE = '/api/strategy-center'

/**
 * 获取所有策略列表
 * @param {Object} params - 查询参数
 * @param {string} params.category - 策略类别筛选
 * @param {string} params.source - 来源筛选: preset/custom/llm_parsed
 * @returns {Promise<Object>} 策略列表
 */
export async function getStrategies(params = {}) {
  try {
    const response = await axios.get(`${API_BASE}/strategies`, { params })
    // 适配后端返回格式
    if (response.data.success) {
      return {
        success: true,
        strategies: response.data.data || [],
        categories: formatCategories(response.data.categories),
        total: response.data.total || 0
      }
    }
    // 如果success为false，返回空数据
    return {
      success: false,
      strategies: [],
      categories: [],
      total: 0
    }
  } catch (error) {
    console.error('获取策略列表失败:', error)
    // 返回空数据而不是抛出错误，避免前端崩溃
    return {
      success: false,
      strategies: [],
      categories: [],
      total: 0,
      error: error.message
    }
  }
}

/**
 * 格式化分类数据
 */
function formatCategories(categories) {
  if (!categories || typeof categories !== 'object') return []
  try {
    return Object.entries(categories).map(([value, info]) => ({
      value,
      label: info?.name || value,
      icon: info?.icon || '📋',
      count: info?.count || 0
    }))
  } catch (error) {
    console.error('格式化分类数据失败:', error)
    return []
  }
}

/**
 * 获取策略详情
 * @param {string} strategyId - 策略ID
 * @returns {Promise<Object>} 策略详情
 */
export async function getStrategyDetail(strategyId) {
  try {
    const response = await axios.get(`${API_BASE}/strategies/${strategyId}`)
    if (response.data.success) {
      return {
        success: true,
        strategy: response.data.data
      }
    }
    return response.data
  } catch (error) {
    console.error('获取策略详情失败:', error)
    throw error
  }
}

/**
 * 创建自定义策略
 * @param {Object} strategyData - 策略数据
 * @returns {Promise<Object>} 创建结果
 */
export async function createStrategy(strategyData) {
  try {
    const response = await axios.post(`${API_BASE}/strategies`, strategyData)
    return response.data
  } catch (error) {
    console.error('创建策略失败:', error)
    throw error
  }
}

/**
 * 更新自定义策略
 * @param {string} strategyId - 策略ID
 * @param {Object} strategyData - 策略数据
 * @returns {Promise<Object>} 更新结果
 */
export async function updateStrategy(strategyId, strategyData) {
  try {
    const response = await axios.put(`${API_BASE}/strategies/${strategyId}`, strategyData)
    return response.data
  } catch (error) {
    console.error('更新策略失败:', error)
    throw error
  }
}

/**
 * 删除自定义策略
 * @param {string} strategyId - 策略ID
 * @returns {Promise<Object>} 删除结果
 */
export async function deleteStrategy(strategyId) {
  try {
    const response = await axios.delete(`${API_BASE}/strategies/${strategyId}`)
    return response.data
  } catch (error) {
    console.error('删除策略失败:', error)
    throw error
  }
}

/**
 * 使用LLM解析策略文本
 * @param {Object} parseData - 解析请求数据
 * @param {string} parseData.text - 用户输入的策略文本
 * @param {string} parseData.strategy_type - 策略类型提示
 * @returns {Promise<Object>} 解析结果
 */
export async function parseStrategyText(parseData) {
  try {
    const response = await axios.post(`${API_BASE}/parse`, parseData)
    if (response.data.success) {
      return {
        success: true,
        parsed_strategy: response.data.data
      }
    }
    return response.data
  } catch (error) {
    console.error('解析策略失败:', error)
    throw error
  }
}

/**
 * 生成交易信号
 * @param {Object} signalData - 信号生成请求数据
 * @param {string} signalData.stock_code - 股票代码
 * @param {string} signalData.strategy_id - 策略ID
 * @param {boolean} signalData.include_chart - 是否包含K线图分析
 * @param {boolean} signalData.include_news - 是否包含新闻分析
 * @param {string} signalData.timeframe - 时间周期
 * @returns {Promise<Object>} 交易信号
 */
export async function generateSignal(signalData) {
  try {
    const response = await axios.post(`${API_BASE}/signal/generate`, signalData)
    if (response.data.success) {
      // 转换信号格式
      const data = response.data.data
      return {
        success: true,
        signal: {
          action: data.signal_type,
          strength: data.confidence,
          confidence: data.confidence,
          entry_price: data.price_target,
          stop_loss: data.stop_loss,
          take_profit: data.take_profit,
          position_size: data.position_size,
          reasons: [data.reasoning],
          indicators: data.indicators_status
        }
      }
    }
    return response.data
  } catch (error) {
    console.error('生成信号失败:', error)
    throw error
  }
}

/**
 * 获取可用指标列表
 * @returns {Promise<Object>} 指标列表
 */
export async function getAvailableIndicators() {
  try {
    const response = await axios.get(`${API_BASE}/indicators`)
    return response.data
  } catch (error) {
    console.error('获取指标列表失败:', error)
    throw error
  }
}

/**
 * 获取策略统计信息
 * @returns {Promise<Object>} 统计信息
 */
export async function getStrategyStats() {
  try {
    const response = await axios.get(`${API_BASE}/stats`)
    return response.data
  } catch (error) {
    console.error('获取策略统计失败:', error)
    throw error
  }
}

// 策略类别映射 (包含新增的机构持仓类别)
export const STRATEGY_CATEGORIES = {
  technical: { label: '技术分析', icon: '📊', color: '#1890ff' },
  value_investing: { label: '价值投资', icon: '💎', color: '#52c41a' },
  trend_following: { label: '趋势跟踪', icon: '🐢', color: '#722ed1' },
  ai_composite: { label: 'AI合成策略', icon: '🤖', color: '#eb2f96' },
  folk_strategy: { label: '民间策略', icon: '🚀', color: '#fa8c16' },
  institutional: { label: '机构持仓', icon: '🏛️', color: '#13c2c2' },
  custom: { label: '自定义策略', icon: '📝', color: '#8c8c8c' }
}

// 指标类型映射
export const INDICATOR_TYPES = {
  technical: { label: '技术指标', color: '#1890ff' },
  fundamental: { label: '基本面指标', color: '#52c41a' },
  sentiment: { label: '情绪指标', color: '#eb2f96' },
  flow: { label: '资金流向', color: '#fa8c16' },
  institutional: { label: '机构持仓', color: '#13c2c2' },
  ai: { label: 'AI指标', color: '#722ed1' }
}

// 操作符映射
export const OPERATORS = {
  '>': '大于',
  '<': '小于',
  '==': '等于',
  '>=': '大于等于',
  '<=': '小于等于',
  'cross_above': '上穿',
  'cross_below': '下穿'
}

// 交易动作映射
export const TRADING_ACTIONS = {
  BUY: { label: '买入', color: '#52c41a', icon: '📈' },
  SELL: { label: '卖出', color: '#f5222d', icon: '📉' },
  HOLD: { label: '持有', color: '#faad14', icon: '⏸️' }
}

export default {
  getStrategies,
  getStrategyDetail,
  createStrategy,
  updateStrategy,
  deleteStrategy,
  parseStrategyText,
  generateSignal,
  getAvailableIndicators,
  getStrategyStats,
  STRATEGY_CATEGORIES,
  INDICATOR_TYPES,
  OPERATORS,
  TRADING_ACTIONS
}