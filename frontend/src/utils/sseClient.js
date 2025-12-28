/**
 * SSE (Server-Sent Events) 客户端
 * 用于接收后端实时推送的事件
 */

import API_BASE_URL from '../config/api'

class SSEClient {
  constructor() {
    this.connections = new Map()
    this.reconnectAttempts = new Map()
    this.maxReconnectAttempts = 5
    this.reconnectDelay = 1000 // 初始重连延迟 1秒
  }

  /**
   * 获取 SSE 基础 URL
   */
  getBaseUrl() {
    return API_BASE_URL || ''
  }

  /**
   * 连接到任务进度流
   * @param {string} taskId - 任务ID
   * @param {Object} handlers - 事件处理器
   * @returns {EventSource}
   */
  connectTask(taskId, handlers = {}) {
    const url = `${this.getBaseUrl()}/api/sse/task/${taskId}`
    return this._connect(`task:${taskId}`, url, handlers)
  }

  /**
   * 连接到分析会话流
   * @param {string} sessionId - 会话ID
   * @param {Object} handlers - 事件处理器
   * @returns {EventSource}
   */
  connectAnalysis(sessionId, handlers = {}) {
    const url = `${this.getBaseUrl()}/api/sse/analysis/${sessionId}`
    return this._connect(`analysis:${sessionId}`, url, handlers)
  }

  /**
   * 连接到日志流
   * @param {string} sessionId - 会话ID
   * @param {Object} handlers - 事件处理器
   * @param {string} level - 日志级别过滤
   * @returns {EventSource}
   */
  connectLogs(sessionId, handlers = {}, level = null) {
    let url = `${this.getBaseUrl()}/api/sse/logs/${sessionId}`
    if (level) {
      url += `?level=${level}`
    }
    return this._connect(`logs:${sessionId}`, url, handlers)
  }

  /**
   * 内部连接方法
   * @private
   */
  _connect(key, url, handlers) {
    // 如果已存在连接，先断开
    this.disconnect(key)

    const eventSource = new EventSource(url)
    this.connections.set(key, eventSource)
    this.reconnectAttempts.set(key, 0)

    // 连接成功
    eventSource.addEventListener('connected', (e) => {
      console.log(`[SSE] Connected to ${key}`)
      this.reconnectAttempts.set(key, 0)
      handlers.onConnected?.(JSON.parse(e.data))
    })

    // 进度更新
    eventSource.addEventListener('progress', (e) => {
      const data = JSON.parse(e.data)
      handlers.onProgress?.(data)
    })

    // 任务开始
    eventSource.addEventListener('task_started', (e) => {
      const data = JSON.parse(e.data)
      handlers.onTaskStarted?.(data)
    })

    // 任务完成
    eventSource.addEventListener('task_completed', (e) => {
      const data = JSON.parse(e.data)
      handlers.onTaskCompleted?.(data)
      // 任务完成后自动断开
      this.disconnect(key)
    })

    // 任务失败
    eventSource.addEventListener('task_failed', (e) => {
      const data = JSON.parse(e.data)
      handlers.onTaskFailed?.(data)
      this.disconnect(key)
    })

    // Agent 事件
    eventSource.addEventListener('agent_start', (e) => {
      const data = JSON.parse(e.data)
      handlers.onAgentStart?.(data)
    })

    eventSource.addEventListener('agent_progress', (e) => {
      const data = JSON.parse(e.data)
      handlers.onAgentProgress?.(data)
    })

    eventSource.addEventListener('agent_complete', (e) => {
      const data = JSON.parse(e.data)
      handlers.onAgentComplete?.(data)
    })

    eventSource.addEventListener('agent_error', (e) => {
      const data = JSON.parse(e.data)
      handlers.onAgentError?.(data)
    })

    // 阶段事件
    eventSource.addEventListener('stage_start', (e) => {
      const data = JSON.parse(e.data)
      handlers.onStageStart?.(data)
    })

    eventSource.addEventListener('stage_complete', (e) => {
      const data = JSON.parse(e.data)
      handlers.onStageComplete?.(data)
    })

    // 日志事件
    eventSource.addEventListener('log', (e) => {
      const data = JSON.parse(e.data)
      handlers.onLog?.(data)
    })

    // 心跳
    eventSource.addEventListener('ping', () => {
      handlers.onPing?.()
    })

    // 通用消息
    eventSource.addEventListener('message', (e) => {
      try {
        const data = JSON.parse(e.data)
        handlers.onMessage?.(data)
      } catch {
        handlers.onMessage?.(e.data)
      }
    })

    // 错误处理
    eventSource.onerror = (error) => {
      console.error(`[SSE] Error on ${key}:`, error)
      handlers.onError?.(error)

      // 自动重连
      if (eventSource.readyState === EventSource.CLOSED) {
        const attempts = this.reconnectAttempts.get(key) || 0
        if (attempts < this.maxReconnectAttempts) {
          const delay = this.reconnectDelay * Math.pow(2, attempts)
          console.log(`[SSE] Reconnecting ${key} in ${delay}ms (attempt ${attempts + 1})`)
          this.reconnectAttempts.set(key, attempts + 1)
          setTimeout(() => {
            if (this.connections.get(key) === eventSource) {
              this._connect(key, url, handlers)
            }
          }, delay)
        } else {
          console.error(`[SSE] Max reconnect attempts reached for ${key}`)
          handlers.onMaxReconnect?.()
        }
      }
    }

    return eventSource
  }

  /**
   * 断开指定连接
   * @param {string} key - 连接标识
   */
  disconnect(key) {
    const conn = this.connections.get(key)
    if (conn) {
      conn.close()
      this.connections.delete(key)
      this.reconnectAttempts.delete(key)
      console.log(`[SSE] Disconnected from ${key}`)
    }
  }

  /**
   * 断开所有连接
   */
  disconnectAll() {
    for (const key of this.connections.keys()) {
      this.disconnect(key)
    }
  }

  /**
   * 检查连接状态
   * @param {string} key - 连接标识
   * @returns {boolean}
   */
  isConnected(key) {
    const conn = this.connections.get(key)
    return conn && conn.readyState === EventSource.OPEN
  }

  /**
   * 获取所有活跃连接
   * @returns {string[]}
   */
  getActiveConnections() {
    return Array.from(this.connections.keys()).filter(key => this.isConnected(key))
  }
}

// 导出单例
export const sseClient = new SSEClient()
export default sseClient
