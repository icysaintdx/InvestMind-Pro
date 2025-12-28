/**
 * 异步分析服务
 * 封装异步分析 API 调用和 SSE 实时更新
 */

import API_BASE_URL from '../config/api'
import { sseClient } from './sseClient'

class AsyncAnalysisService {
  constructor() {
    this.baseUrl = API_BASE_URL || ''
    this.currentSession = null
    this.currentTaskId = null
  }

  /**
   * 启动异步分析
   * @param {Object} options - 分析选项
   * @param {string} options.stockCode - 股票代码
   * @param {string} options.stockName - 股票名称
   * @param {number} options.depth - 分析深度 (1-4)
   * @param {Object} handlers - 事件处理器
   * @returns {Promise<Object>} - 返回 task_id 和 session_id
   */
  async startAnalysis(options, handlers = {}) {
    const { stockCode, stockName, depth = 2 } = options

    try {
      // 1. 调用后端启动异步分析
      const response = await fetch(`${this.baseUrl}/api/async-analysis/start`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          stock_code: stockCode,
          stock_name: stockName,
          depth: depth
        })
      })

      if (!response.ok) {
        throw new Error(`启动分析失败: ${response.status}`)
      }

      const data = await response.json()

      if (!data.success) {
        throw new Error(data.message || '启动分析失败')
      }

      this.currentTaskId = data.task_id
      this.currentSession = data.session_id

      // 2. 建立 SSE 连接
      this.connectSSE(data.session_id, handlers)

      return {
        taskId: data.task_id,
        sessionId: data.session_id,
        sseUrl: data.sse_url
      }

    } catch (error) {
      console.error('启动异步分析失败:', error)
      handlers.onError?.(error)
      throw error
    }
  }

  /**
   * 建立 SSE 连接
   * @param {string} sessionId - 会话ID
   * @param {Object} handlers - 事件处理器
   */
  connectSSE(sessionId, handlers) {
    sseClient.connectAnalysis(sessionId, {
      onConnected: (data) => {
        console.log('[AsyncAnalysis] SSE 连接成功', data)
        handlers.onConnected?.(data)
      },

      // Agent 事件
      onAgentStart: (data) => {
        console.log('[AsyncAnalysis] Agent 开始:', data.agent_id)
        handlers.onAgentStart?.(data)
      },

      onAgentProgress: (data) => {
        handlers.onAgentProgress?.(data)
      },

      onAgentComplete: (data) => {
        console.log('[AsyncAnalysis] Agent 完成:', data.agent_id)
        handlers.onAgentComplete?.(data)
      },

      onAgentError: (data) => {
        console.error('[AsyncAnalysis] Agent 错误:', data)
        handlers.onAgentError?.(data)
      },

      // 阶段事件
      onStageStart: (data) => {
        console.log('[AsyncAnalysis] 阶段开始:', data.stage)
        handlers.onStageStart?.(data)
      },

      onStageComplete: (data) => {
        console.log('[AsyncAnalysis] 阶段完成:', data.stage)
        handlers.onStageComplete?.(data)
      },

      // 日志事件
      onLog: (data) => {
        handlers.onLog?.(data)
      },

      // 分析完成
      onMessage: (data) => {
        if (data.event === 'analysis_complete') {
          console.log('[AsyncAnalysis] 分析完成')
          handlers.onComplete?.(data.data)
          // 断开 SSE 连接
          this.disconnect()
        }
      },

      onError: (error) => {
        console.error('[AsyncAnalysis] SSE 错误:', error)
        handlers.onError?.(error)
      },

      onMaxReconnect: () => {
        console.error('[AsyncAnalysis] SSE 重连失败')
        handlers.onError?.(new Error('SSE 连接失败'))
      }
    })
  }

  /**
   * 查询任务状态
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>}
   */
  async getTaskStatus(taskId = null) {
    const id = taskId || this.currentTaskId
    if (!id) {
      throw new Error('没有活跃的任务')
    }

    const response = await fetch(`${this.baseUrl}/api/async-analysis/task/${id}`)
    if (!response.ok) {
      throw new Error(`查询任务状态失败: ${response.status}`)
    }

    return await response.json()
  }

  /**
   * 获取分析结果
   * @param {string} sessionId - 会话ID
   * @returns {Promise<Object>}
   */
  async getResults(sessionId = null) {
    const id = sessionId || this.currentSession
    if (!id) {
      throw new Error('没有活跃的会话')
    }

    const response = await fetch(`${this.baseUrl}/api/async-analysis/session/${id}/results`)
    if (!response.ok) {
      throw new Error(`获取结果失败: ${response.status}`)
    }

    const data = await response.json()
    return data.data
  }

  /**
   * 获取特定 Agent 的结果
   * @param {string} agentId - Agent ID
   * @param {string} sessionId - 会话ID
   * @returns {Promise<Object>}
   */
  async getAgentResult(agentId, sessionId = null) {
    const id = sessionId || this.currentSession
    if (!id) {
      throw new Error('没有活跃的会话')
    }

    const response = await fetch(
      `${this.baseUrl}/api/async-analysis/session/${id}/agent/${agentId}`
    )
    if (!response.ok) {
      throw new Error(`获取 Agent 结果失败: ${response.status}`)
    }

    const data = await response.json()
    return data.data
  }

  /**
   * 取消任务
   * @param {string} taskId - 任务ID
   * @returns {Promise<Object>}
   */
  async cancelTask(taskId = null) {
    const id = taskId || this.currentTaskId
    if (!id) {
      throw new Error('没有活跃的任务')
    }

    const response = await fetch(`${this.baseUrl}/api/async-analysis/task/${id}/cancel`, {
      method: 'POST'
    })

    if (!response.ok) {
      throw new Error(`取消任务失败: ${response.status}`)
    }

    this.disconnect()
    return await response.json()
  }

  /**
   * 断开 SSE 连接
   */
  disconnect() {
    if (this.currentSession) {
      sseClient.disconnect(`analysis:${this.currentSession}`)
    }
    this.currentSession = null
    this.currentTaskId = null
  }

  /**
   * 检查是否有活跃的分析
   * @returns {boolean}
   */
  isActive() {
    return this.currentSession !== null
  }
}

// 导出单例
export const asyncAnalysisService = new AsyncAnalysisService()
export default asyncAnalysisService
