/**
 * 智能超时和重试工具
 * 提供分段超时检测和智能重试策略
 */

/**
 * 分段超时fetch
 * 每30秒检查一次是否有响应，而不是等待整个超时时间
 * 
 * @param {string} url - 请求URL
 * @param {object} options - fetch选项
 * @param {object} config - 配置
 * @param {number} config.segmentTimeout - 每段超时时间（毫秒）
 * @param {number} config.maxSegments - 最多等待段数
 * @param {number} config.maxRetries - 最多重试次数
 * @param {string} config.agentId - 智能体ID（用于日志）
 * @returns {Promise} fetch结果
 */
export async function fetchWithSmartTimeout(url, options = {}, config = {}) {
  const {
    segmentTimeout = 30000, // 30秒一段
    maxSegments = 4, // 最处4段 = 2分钟
    maxRetries = 3, // 最多重试3次
    agentId = 'unknown'
  } = config

  const totalTimeout = segmentTimeout * maxSegments

  for (let retry = 0; retry <= maxRetries; retry++) {
    const controller = new AbortController()
    const signal = controller.signal
    
    // 简单的超时定时器
    const timeoutId = setTimeout(() => {
      console.error(`[${agentId}] ❌ 超时 ${totalTimeout/1000}秒，中止请求`)
      controller.abort()
    }, totalTimeout)
    
    try {
      if (retry > 0) {
        const retryDelay = Math.min(2000 * Math.pow(2, retry - 1), 10000)
        console.log(`[${agentId}] 等待${retryDelay}ms后重试 (${retry}/${maxRetries})`)
        await new Promise(r => setTimeout(r, retryDelay))
      }
      
      // 发起请求
      console.log(`[${agentId}] 🚀 开始请求 (尝试 ${retry + 1}/${maxRetries + 1})`)
      const response = await fetch(url, {
        ...options,
        signal
      })
      
      // 成功，清理超时
      clearTimeout(timeoutId)
      console.log(`[${agentId}] ✅ 请求成功`)
      
      return response
      
    } catch (error) {
      // 清理超时
      clearTimeout(timeoutId)
      
      // 判断错误类型
      if (error.name === 'AbortError') {
        if (retry < maxRetries) {
          console.log(`[${agentId}] 🔄 超时，准备重试...`)
          continue
        } else {
          throw new Error(`请求超时 ${totalTimeout/1000}秒，已重试${maxRetries}次仍失败`)
        }
      }
      
      // 其他错误
      if (retry < maxRetries) {
        console.log(`[${agentId}] 🔄 请求失败: ${error.message}，准备重试...`)
        continue
      }
      
      throw error
    }
  }
}

/**
 * 智能重试策略
 * 根据错误类型决定是否重试和重试延迟
 */
export const RETRY_STRATEGIES = {
  'ReadTimeout': { shouldRetry: true, delay: 2000, maxRetries: 3 },
  'ConnectionError': { shouldRetry: true, delay: 5000, maxRetries: 2 },
  'NetworkError': { shouldRetry: true, delay: 3000, maxRetries: 3 },
  'APIError': { shouldRetry: false, delay: 0, maxRetries: 0 },
  'RateLimitError': { shouldRetry: true, delay: 10000, maxRetries: 1 },
  'AbortError': { shouldRetry: true, delay: 2000, maxRetries: 3 }
}

/**
 * 检测错误类型
 * @param {Error} error - 错误对象
 * @returns {string} 错误类型
 */
export function detectErrorType(error) {
  const message = error.message || ''
  const name = error.name || ''
  
  if (name === 'AbortError') return 'AbortError'
  if (message.includes('timeout') || message.includes('Timeout')) return 'ReadTimeout'
  if (message.includes('network') || message.includes('Network')) return 'NetworkError'
  if (message.includes('connection') || message.includes('Connection')) return 'ConnectionError'
  if (message.includes('rate limit') || message.includes('Rate limit')) return 'RateLimitError'
  if (message.includes('API') || message.includes('api')) return 'APIError'
  
  return 'UnknownError'
}

/**
 * 带智能重试的fetch
 * @param {string} url - 请求URL
 * @param {object} options - fetch选项
 * @param {string} agentId - 智能体ID
 * @returns {Promise} fetch结果
 */
export async function fetchWithSmartRetry(url, options = {}, agentId = 'unknown') {
  const MAX_ATTEMPTS = 10 // 最多尝试10次
  let retryCount = 0
  
  for (let attempt = 0; attempt < MAX_ATTEMPTS; attempt++) {
    try {
      const response = await fetch(url, options)
      return response
      
    } catch (error) {
      const errorType = detectErrorType(error)
      const strategy = RETRY_STRATEGIES[errorType] || { shouldRetry: false }
      
      console.log(`[${agentId}] ⚠️ 错误类型: ${errorType}`)
      
      if (!strategy.shouldRetry || retryCount >= strategy.maxRetries) {
        console.error(`[${agentId}] ❌ 不可重试或已达最大重试次数`)
        throw error
      }
      
      retryCount++
      console.log(`[${agentId}] 🔄 ${errorType}，等待${strategy.delay}ms后重试 (${retryCount}/${strategy.maxRetries})`)
      
      await new Promise(r => setTimeout(r, strategy.delay))
    }
  }
  
  throw new Error(`超过最大尝试次数 ${MAX_ATTEMPTS}`)
}

/**
 * 进度监控器
 * 定期报告等待进度
 */
export class ProgressMonitor {
  constructor(agentId, interval = 10000) {
    this.agentId = agentId
    this.interval = interval
    this.startTime = Date.now()
    this.timer = null
  }
  
  start() {
    this.timer = setInterval(() => {
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000)
      console.log(`[${this.agentId}] ⏳ 已等待 ${elapsed}秒...`)
    }, this.interval)
  }
  
  stop() {
    if (this.timer) {
      clearInterval(this.timer)
      this.timer = null
      const elapsed = Math.floor((Date.now() - this.startTime) / 1000)
      console.log(`[${this.agentId}] ✅ 完成，总耗时 ${elapsed}秒`)
    }
  }
}
