/**
 * 分析状态持久化管理 v2.0
 *
 * 设计原则：
 * 1. 单一数据源：只使用一个 localStorage key
 * 2. 后端优先：后端数据库是真实状态，localStorage 只是缓存
 * 3. 状态同步：定期与后端同步，确保一致性
 * 4. 优雅降级：网络问题时使用本地缓存
 */

const STORAGE_KEY = 'InvestMindPro_analysis_state'
const SESSION_KEY = 'InvestMindPro_session_id'
const SESSION_TIMEOUT = 30 * 60 * 1000 // 30分钟超时
const FORCE_STOPPED_KEY = 'InvestMindPro_force_stopped'

/**
 * 保存分析状态到 localStorage
 */
export function saveAnalysisState(state) {
  try {
    // 如果已被强制停止，不保存
    if (localStorage.getItem(FORCE_STOPPED_KEY) === 'true') {
      console.log('[状态持久化] 已被强制停止，跳过保存')
      return
    }

    const stateToSave = {
      ...state,
      timestamp: Date.now(),
      version: '2.0'
    }
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stateToSave))
    console.log('[状态持久化] 已保存分析状态')
  } catch (error) {
    console.error('[状态持久化] 保存失败:', error)
  }
}

/**
 * 从 localStorage 恢复分析状态
 */
export function loadAnalysisState() {
  try {
    // 如果已被强制停止，不恢复
    if (localStorage.getItem(FORCE_STOPPED_KEY) === 'true') {
      console.log('[状态持久化] 检测到强制停止标记，不恢复状态')
      return null
    }

    const saved = localStorage.getItem(STORAGE_KEY)
    if (!saved) {
      console.log('[状态持久化] 无保存的状态')
      return null
    }

    const state = JSON.parse(saved)

    // 检查是否超时
    const elapsed = Date.now() - state.timestamp
    if (elapsed > SESSION_TIMEOUT) {
      console.log('[状态持久化] 状态已超时，清除')
      clearAnalysisState()
      return null
    }

    console.log('[状态持久化] 成功恢复状态，已运行:', Math.floor(elapsed / 1000), '秒')
    return state
  } catch (error) {
    console.error('[状态持久化] 恢复失败:', error)
    return null
  }
}

/**
 * 清除保存的状态
 */
export function clearAnalysisState() {
  try {
    localStorage.removeItem(STORAGE_KEY)
    console.log('[状态持久化] 已清除状态')
  } catch (error) {
    console.error('[状态持久化] 清除失败:', error)
  }
}

/**
 * 完全清除所有分析相关的存储（用于强制停止）
 */
export function forceCleanAllState() {
  try {
    // 设置强制停止标记（防止页面刷新时恢复）
    localStorage.setItem(FORCE_STOPPED_KEY, 'true')

    // 清除所有相关存储
    localStorage.removeItem(STORAGE_KEY)
    localStorage.removeItem(SESSION_KEY)

    // 兼容旧版本的 key
    localStorage.removeItem('analysis_state')
    localStorage.removeItem('current_session_id')

    console.log('[状态持久化] 已强制清除所有状态')
  } catch (error) {
    console.error('[状态持久化] 强制清除失败:', error)
  }
}

/**
 * 清除强制停止标记（开始新分析时调用）
 */
export function clearForceStopFlag() {
  localStorage.removeItem(FORCE_STOPPED_KEY)
  console.log('[状态持久化] 已清除强制停止标记')
}

/**
 * 检查是否被强制停止
 */
export function isForceStoppedState() {
  return localStorage.getItem(FORCE_STOPPED_KEY) === 'true'
}

/**
 * 检查是否有正在进行的分析
 */
export function hasActiveAnalysis() {
  if (isForceStoppedState()) {
    return false
  }
  const state = loadAnalysisState()
  return state && state.isAnalyzing
}

/**
 * 保存会话 ID
 */
export function saveSessionId(sessionId) {
  localStorage.setItem(SESSION_KEY, sessionId)
}

/**
 * 获取会话 ID
 */
export function getSessionId() {
  if (isForceStoppedState()) {
    return null
  }
  return localStorage.getItem(SESSION_KEY)
}

/**
 * 清除会话 ID
 */
export function clearSessionId() {
  localStorage.removeItem(SESSION_KEY)
}

/**
 * 创建分析会话ID
 */
export function createSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}

/**
 * 标记分析完成（清除所有临时状态）
 */
export function markAnalysisComplete() {
  clearAnalysisState()
  clearSessionId()
  clearForceStopFlag()
  console.log('[状态持久化] 分析完成，已清除所有临时状态')
}
