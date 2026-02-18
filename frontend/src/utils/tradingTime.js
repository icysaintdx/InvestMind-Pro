/**
 * 交易时间判断工具模块
 * 用于判断当前是否在A股交易时间内，控制实时数据刷新行为
 */

// A股交易时间配置
const TRADING_CONFIG = {
  // 上午交易时段
  morning: {
    start: { hour: 9, minute: 30 },
    end: { hour: 11, minute: 30 }
  },
  // 下午交易时段
  afternoon: {
    start: { hour: 13, minute: 0 },
    end: { hour: 15, minute: 0 }
  },
  // 时区：北京时间 UTC+8
  timezone: 'Asia/Shanghai'
}

// 刷新间隔配置（毫秒）
export const REFRESH_INTERVALS = {
  // K线数据刷新间隔
  kline: {
    trading: 30000,      // 交易时间内：30秒
    nonTrading: 300000   // 非交易时间：5分钟
  },
  // 持仓数据刷新间隔
  portfolio: {
    trading: 10000,      // 交易时间内：10秒
    nonTrading: 60000    // 非交易时间：1分钟
  },
  // 策略计划状态刷新间隔
  strategyPlan: {
    trading: 15000,      // 交易时间内：15秒
    nonTrading: 60000    // 非交易时间：1分钟
  },
  // 市场数据刷新间隔
  marketData: {
    trading: 5000,       // 交易时间内：5秒
    nonTrading: 60000    // 非交易时间：1分钟
  }
}

/**
 * 获取当前北京时间
 * @returns {Date} 北京时间的Date对象
 */
export function getBeijingTime() {
  const now = new Date()
  // 获取UTC时间戳，然后加上8小时得到北京时间
  const utcTime = now.getTime() + now.getTimezoneOffset() * 60000
  const beijingTime = new Date(utcTime + 8 * 3600000)
  return beijingTime
}

/**
 * 判断是否为工作日（周一到周五）
 * @param {Date} date - 日期对象（北京时间）
 * @returns {boolean} 是否为工作日
 */
export function isWeekday(date = null) {
  const d = date || getBeijingTime()
  const day = d.getDay()
  return day >= 1 && day <= 5
}

/**
 * 判断当前时间是否在指定时段内
 * @param {Object} session - 时段配置 { start: {hour, minute}, end: {hour, minute} }
 * @param {Date} date - 日期对象（北京时间）
 * @returns {boolean} 是否在时段内
 */
function isInSession(session, date) {
  const hour = date.getHours()
  const minute = date.getMinutes()
  const currentMinutes = hour * 60 + minute
  const startMinutes = session.start.hour * 60 + session.start.minute
  const endMinutes = session.end.hour * 60 + session.end.minute
  return currentMinutes >= startMinutes && currentMinutes <= endMinutes
}

/**
 * 判断当前是否为A股交易时间
 * 交易时间：周一至周五 9:30-11:30, 13:00-15:00
 * @returns {boolean} 是否为交易时间
 */
export function isTradingTime() {
  const now = getBeijingTime()
  
  // 非工作日不交易
  if (!isWeekday(now)) {
    return false
  }
  
  // 检查是否在上午或下午交易时段
  const inMorning = isInSession(TRADING_CONFIG.morning, now)
  const inAfternoon = isInSession(TRADING_CONFIG.afternoon, now)
  
  return inMorning || inAfternoon
}

/**
 * 获取当前交易状态详情
 * @returns {Object} 交易状态详情
 */
export function getTradingStatus() {
  const now = getBeijingTime()
  const hour = now.getHours()
  const minute = now.getMinutes()
  const currentMinutes = hour * 60 + minute
  const isWeekdayNow = isWeekday(now)
  
  // 各时段的分钟数
  const morningStart = TRADING_CONFIG.morning.start.hour * 60 + TRADING_CONFIG.morning.start.minute
  const morningEnd = TRADING_CONFIG.morning.end.hour * 60 + TRADING_CONFIG.morning.end.minute
  const afternoonStart = TRADING_CONFIG.afternoon.start.hour * 60 + TRADING_CONFIG.afternoon.start.minute
  const afternoonEnd = TRADING_CONFIG.afternoon.end.hour * 60 + TRADING_CONFIG.afternoon.end.minute
  
  let status = 'closed'
  let statusText = '休市'
  let nextOpenTime = null
  let timeToNextOpen = null
  
  if (!isWeekdayNow) {
    // 周末
    status = 'weekend'
    statusText = '周末休市'
    // 计算到下周一开盘的时间
    const daysUntilMonday = (8 - now.getDay()) % 7 || 7
    nextOpenTime = new Date(now)
    nextOpenTime.setDate(nextOpenTime.getDate() + daysUntilMonday)
    nextOpenTime.setHours(9, 30, 0, 0)
  } else if (currentMinutes < morningStart) {
    // 早盘前
    status = 'pre_market'
    statusText = '盘前'
    nextOpenTime = new Date(now)
    nextOpenTime.setHours(9, 30, 0, 0)
  } else if (currentMinutes >= morningStart && currentMinutes <= morningEnd) {
    // 上午交易时段
    status = 'trading'
    statusText = '交易中（上午）'
  } else if (currentMinutes > morningEnd && currentMinutes < afternoonStart) {
    // 午休
    status = 'lunch_break'
    statusText = '午间休市'
    nextOpenTime = new Date(now)
    nextOpenTime.setHours(13, 0, 0, 0)
  } else if (currentMinutes >= afternoonStart && currentMinutes <= afternoonEnd) {
    // 下午交易时段
    status = 'trading'
    statusText = '交易中（下午）'
  } else {
    // 收盘后
    status = 'after_hours'
    statusText = '已收盘'
    // 计算到下一个交易日开盘的时间
    nextOpenTime = new Date(now)
    nextOpenTime.setDate(nextOpenTime.getDate() + 1)
    // 如果明天是周末，跳到周一
    while (nextOpenTime.getDay() === 0 || nextOpenTime.getDay() === 6) {
      nextOpenTime.setDate(nextOpenTime.getDate() + 1)
    }
    nextOpenTime.setHours(9, 30, 0, 0)
  }
  
  // 计算距离下次开盘的时间
  if (nextOpenTime) {
    timeToNextOpen = nextOpenTime.getTime() - now.getTime()
  }
  
  return {
    isTrading: status === 'trading',
    status,
    statusText,
    currentTime: now,
    currentTimeStr: `${hour.toString().padStart(2, '0')}:${minute.toString().padStart(2, '0')}`,
    nextOpenTime,
    timeToNextOpen,
    timeToNextOpenStr: timeToNextOpen ? formatDuration(timeToNextOpen) : null
  }
}

/**
 * 格式化时间间隔
 * @param {number} ms - 毫秒数
 * @returns {string} 格式化的时间字符串
 */
function formatDuration(ms) {
  const seconds = Math.floor(ms / 1000)
  const minutes = Math.floor(seconds / 60)
  const hours = Math.floor(minutes / 60)
  const days = Math.floor(hours / 24)
  
  if (days > 0) {
    return `${days}天${hours % 24}小时`
  } else if (hours > 0) {
    return `${hours}小时${minutes % 60}分钟`
  } else if (minutes > 0) {
    return `${minutes}分钟`
  } else {
    return `${seconds}秒`
  }
}

/**
 * 获取适当的刷新间隔
 * @param {string} type - 数据类型：'kline' | 'portfolio' | 'strategyPlan' | 'marketData'
 * @returns {number} 刷新间隔（毫秒）
 */
export function getRefreshInterval(type) {
  const intervals = REFRESH_INTERVALS[type]
  if (!intervals) {
    console.warn(`未知的刷新类型: ${type}，使用默认间隔`)
    return 30000
  }
  return isTradingTime() ? intervals.trading : intervals.nonTrading
}

/**
 * 创建自适应刷新定时器
 * 根据交易时间自动调整刷新频率
 * @param {Function} callback - 刷新回调函数
 * @param {string} type - 数据类型
 * @param {Object} options - 配置选项
 * @returns {Object} 定时器控制对象
 */
export function createAdaptiveRefreshTimer(callback, type, options = {}) {
  const {
    immediate = true,           // 是否立即执行一次
    onStatusChange = null,      // 交易状态变化回调
    enabled = true              // 是否启用
  } = options
  
  let timerId = null
  let isRunning = false
  let lastStatus = null
  let countdown = 0
  let countdownTimerId = null
  
  // 获取当前应该使用的间隔
  const getCurrentInterval = () => getRefreshInterval(type)
  
  // 执行刷新
  const doRefresh = async () => {
    if (!isRunning) return
    
    try {
      await callback()
    } catch (error) {
      console.error(`[AdaptiveRefresh] ${type} 刷新失败:`, error)
    }
    
    // 检查交易状态是否变化
    const currentStatus = getTradingStatus()
    if (lastStatus && lastStatus.isTrading !== currentStatus.isTrading) {
      console.log(`[AdaptiveRefresh] 交易状态变化: ${lastStatus.statusText} -> ${currentStatus.statusText}`)
      if (onStatusChange) {
        onStatusChange(currentStatus)
      }
    }
    lastStatus = currentStatus
    
    // 设置下一次刷新
    scheduleNext()
  }
  
  // 安排下一次刷新
  const scheduleNext = () => {
    if (!isRunning) return
    
    const interval = getCurrentInterval()
    countdown = interval
    
    // 清除旧的定时器
    if (timerId) {
      clearTimeout(timerId)
    }
    if (countdownTimerId) {
      clearInterval(countdownTimerId)
    }
    
    // 设置新的定时器
    timerId = setTimeout(doRefresh, interval)
    
    // 设置倒计时更新
    countdownTimerId = setInterval(() => {
      countdown = Math.max(0, countdown - 1000)
    }, 1000)
  }
  
  // 启动定时器
  const start = () => {
    if (isRunning) return
    
    isRunning = true
    lastStatus = getTradingStatus()
    
    console.log(`[AdaptiveRefresh] 启动 ${type} 刷新定时器，当前状态: ${lastStatus.statusText}`)
    
    if (immediate) {
      doRefresh()
    } else {
      scheduleNext()
    }
  }
  
  // 停止定时器
  const stop = () => {
    isRunning = false
    
    if (timerId) {
      clearTimeout(timerId)
      timerId = null
    }
    if (countdownTimerId) {
      clearInterval(countdownTimerId)
      countdownTimerId = null
    }
    
    console.log(`[AdaptiveRefresh] 停止 ${type} 刷新定时器`)
  }
  
  // 立即刷新一次
  const refresh = () => {
    if (isRunning) {
      // 重置定时器
      if (timerId) {
        clearTimeout(timerId)
      }
      doRefresh()
    }
  }
  
  // 获取状态
  const getStatus = () => ({
    isRunning,
    countdown,
    countdownStr: formatDuration(countdown),
    interval: getCurrentInterval(),
    tradingStatus: getTradingStatus()
  })
  
  // 如果启用，自动启动
  if (enabled) {
    start()
  }
  
  return {
    start,
    stop,
    refresh,
    getStatus,
    get isRunning() { return isRunning },
    get countdown() { return countdown }
  }
}

/**
 * Vue 3 Composition API 的实时刷新 Hook
 * @param {Function} fetchFn - 数据获取函数
 * @param {string} type - 数据类型
 * @param {Object} options - 配置选项
 * @returns {Object} 响应式状态和控制方法
 */
export function useRealtimeRefresh(fetchFn, type, options = {}) {
  // 这个函数需要在 Vue 组件中使用，返回的是普通对象
  // 实际的响应式处理在组件中完成
  return {
    createTimer: () => createAdaptiveRefreshTimer(fetchFn, type, options),
    getInterval: () => getRefreshInterval(type),
    isTradingTime,
    getTradingStatus
  }
}

// 导出配置供外部使用
export { TRADING_CONFIG }

export default {
  isTradingTime,
  getTradingStatus,
  getRefreshInterval,
  createAdaptiveRefreshTimer,
  useRealtimeRefresh,
  getBeijingTime,
  isWeekday,
  REFRESH_INTERVALS,
  TRADING_CONFIG
}
