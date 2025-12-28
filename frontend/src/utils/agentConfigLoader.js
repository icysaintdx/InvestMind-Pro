/**
 * 智能体配置加载工具
 * 用于在分析流程中根据配置动态启用/禁用智能体
 */

import axios from 'axios'

/**
 * 加载智能体配置
 * @returns {Promise<Object>} 配置对象 { agent_id: boolean }
 */
export async function loadAgentConfig() {
  try {
    const response = await axios.get('/api/agents/config/current')
    if (response.data && response.data.success) {
      return response.data.config
    }
    return null
  } catch (error) {
    console.error('加载智能体配置失败:', error)
    return null
  }
}

/**
 * 根据配置过滤智能体列表
 * @param {Array} agents - 智能体列表
 * @param {Object} config - 配置对象
 * @returns {Array} 过滤后的智能体列表
 */
export function filterAgentsByConfig(agents, config) {
  if (!config) {
    // 如果没有配置，返回所有智能体
    return agents
  }
  
  return agents.filter(agent => {
    // 如果配置中没有该智能体，默认启用
    if (config[agent.id] === undefined) {
      return true
    }
    return config[agent.id] === true
  })
}

/**
 * 检查智能体是否启用
 * @param {string} agentId - 智能体ID
 * @param {Object} config - 配置对象
 * @returns {boolean} 是否启用
 */
export function isAgentEnabled(agentId, config) {
  if (!config) {
    return true
  }
  return config[agentId] !== false
}

/**
 * 获取启用的智能体数量
 * @param {Object} config - 配置对象
 * @returns {number} 启用的智能体数量
 */
export function getEnabledAgentCount(config) {
  if (!config) {
    return 0
  }
  return Object.values(config).filter(v => v === true).length
}

/**
 * 获取配置影响信息
 * @returns {Promise<Object>} 影响信息
 */
export async function getConfigImpact() {
  try {
    const response = await axios.get('/api/agents/config/impact')
    if (response.data && response.data.success) {
      return response.data.impact
    }
    return null
  } catch (error) {
    console.error('获取配置影响失败:', error)
    return null
  }
}

/**
 * 应用配置方案
 * @param {string} profileName - 方案名称 (minimal/balanced/complete)
 * @returns {Promise<Object>} 应用结果
 */
export async function applyProfile(profileName) {
  try {
    const response = await axios.post(`/api/agents/config/profile/${profileName}`)
    if (response.data && response.data.success) {
      return {
        success: true,
        config: response.data.config,
        impact: response.data.impact,
        message: response.data.message
      }
    }
    return { success: false, message: '应用方案失败' }
  } catch (error) {
    console.error('应用配置方案失败:', error)
    return { 
      success: false, 
      message: error.response?.data?.detail || '应用方案失败' 
    }
  }
}

/**
 * 保存配置
 * @param {Object} config - 配置对象
 * @returns {Promise<Object>} 保存结果
 */
export async function saveAgentConfig(config) {
  try {
    const response = await axios.post('/api/agents/config/apply', {
      enabled: config
    })
    if (response.data && response.data.success) {
      return {
        success: true,
        impact: response.data.impact,
        message: response.data.message
      }
    }
    return { success: false, message: '保存配置失败' }
  } catch (error) {
    console.error('保存配置失败:', error)
    return { 
      success: false, 
      message: error.response?.data?.detail?.message || '保存配置失败' 
    }
  }
}

/**
 * 获取配置方案列表
 * @returns {Promise<Object>} 方案列表
 */
export async function getProfiles() {
  try {
    const response = await axios.get('/api/agents/config/profiles')
    if (response.data && response.data.success) {
      return response.data.profiles
    }
    return null
  } catch (error) {
    console.error('获取配置方案失败:', error)
    return null
  }
}

/**
 * 按优先级获取智能体
 * @param {string} priority - 优先级 (core/important/optional)
 * @returns {Promise<Array>} 智能体列表
 */
export async function getAgentsByPriority(priority) {
  try {
    const response = await axios.get(`/api/agents/config/priority/${priority}`)
    if (response.data && response.data.success) {
      return response.data.agents
    }
    return []
  } catch (error) {
    console.error(`获取${priority}智能体失败:`, error)
    return []
  }
}

/**
 * 创建配置变更监听器
 * @param {Function} callback - 配置变更回调函数
 * @returns {Function} 取消监听函数
 */
export function watchConfigChanges(callback) {
  let intervalId = null
  let lastConfig = null
  
  const checkChanges = async () => {
    const config = await loadAgentConfig()
    if (config && JSON.stringify(config) !== JSON.stringify(lastConfig)) {
      lastConfig = config
      callback(config)
    }
  }
  
  // 每5秒检查一次配置变更
  intervalId = setInterval(checkChanges, 5000)
  
  // 立即执行一次
  checkChanges()
  
  // 返回取消监听函数
  return () => {
    if (intervalId) {
      clearInterval(intervalId)
    }
  }
}
