/**
 * 分析状态持久化管理
 * 用于在页面刷新或后台运行时保持分析状态
 */

const STORAGE_KEY = 'alphacouncil_analysis_state'
const SESSION_TIMEOUT = 30 * 60 * 1000 // 30分钟超时

/**
 * 保存分析状态到 localStorage
 */
export function saveAnalysisState(state) {
  try {
    const stateToSave = {
      ...state,
      timestamp: Date.now(),
      version: '1.0'
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
 * 检查是否有正在进行的分析
 */
export function hasActiveAnalysis() {
  const state = loadAnalysisState()
  return state && state.isAnalyzing
}

/**
 * 创建分析会话ID
 */
export function createSessionId() {
  return `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
}
