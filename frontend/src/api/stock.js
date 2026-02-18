/**
 * 股票数据 API 调用模块
 * 提供K线数据、行情数据、指标计算等功能
 * 使用 /api/kline/data 接口，支持TDX、AKShare等多数据源
 */

import axios from 'axios'
import API_BASE_URL from '@/config/api.js'

const API_BASE = API_BASE_URL

/**
 * 获取股票K线数据
 * 使用 /api/kline/data 接口，支持TDX优先的多数据源
 * @param {string} stockCode - 股票代码
 * @param {Object} options - 选项
 * @param {string} options.period - 周期: daily/weekly/monthly/60/30/15/5/1
 * @param {number} options.count - 获取数量
 * @param {string} options.adjust - 复权类型: qfq/hfq/空
 * @param {string} options.source - 数据源: auto/tdx/akshare/tushare
 * @returns {Promise<Object>} K线数据
 */
export async function getKlineData(stockCode, options = {}) {
  try {
    const { 
      period = 'daily', 
      count = 200, 
      adjust = 'qfq',
      source = 'auto'  // 默认auto，优先使用TDX
    } = options
    
    // 转换周期格式
    const periodMap = {
      'daily': 'daily',
      'weekly': 'weekly',
      'monthly': 'monthly',
      '60min': '60',
      '30min': '30',
      '15min': '15',
      '5min': '5',
      '1min': '1'
    }
    const apiPeriod = periodMap[period] || period
    
    console.log(`📊 请求K线数据: ${stockCode}, 周期: ${apiPeriod}, 数据源: ${source}`)
    
    const response = await axios.get(`${API_BASE}/api/kline/data`, {
      params: {
        symbol: stockCode,
        period: apiPeriod,
        adjust,
        source,
        limit: count
      }
    })
    
    if (response.data.success) {
      const klineData = response.data.data || []
      console.log(`✅ K线数据获取成功: ${klineData.length}条, 数据源: ${response.data.source}`)
      
      // 转换数据格式以兼容现有代码
      const formattedData = klineData.map(item => ({
        date: item.time || item.date,
        open: parseFloat(item.open) || 0,
        high: parseFloat(item.high) || 0,
        low: parseFloat(item.low) || 0,
        close: parseFloat(item.close) || 0,
        volume: parseFloat(item.volume) || 0,
        amount: parseFloat(item.amount) || 0
      }))
      
      return {
        success: true,
        source: response.data.source,
        data: {
          code: stockCode,
          name: getStockName(stockCode),
          kline: formattedData
        }
      }
    } else {
      throw new Error(response.data.message || '获取K线数据失败')
    }
  } catch (error) {
    console.error('❌ 获取K线数据失败:', error)
    // 返回模拟数据用于开发
    console.log('⚠️ 使用模拟数据')
    return generateMockKlineData(stockCode, options.count || 120)
  }
}

/**
 * 获取股票实时行情
 * 使用 /api/kline/realtime 接口
 * @param {string} stockCode - 股票代码
 * @param {string} source - 数据源: auto/tdx/akshare
 * @returns {Promise<Object>} 实时行情
 */
export async function getRealtimeQuote(stockCode, source = 'auto') {
  try {
    console.log(`📈 请求实时行情: ${stockCode}`)
    
    const response = await axios.get(`${API_BASE}/api/kline/realtime`, {
      params: { 
        symbol: stockCode,
        source
      }
    })
    
    if (response.data.success) {
      const quote = response.data.data
      console.log(`✅ 实时行情获取成功: ${stockCode}, 数据源: ${response.data.source}`)
      
      return {
        success: true,
        source: response.data.source,
        data: {
          code: stockCode,
          name: quote.name || getStockName(stockCode),
          price: quote.price,
          change: quote.change,
          changePercent: quote.change_pct,
          open: quote.open,
          high: quote.high,
          low: quote.low,
          volume: quote.volume,
          amount: quote.amount,
          preClose: quote.pre_close,
          turnover: quote.turnover,
          time: new Date().toISOString()
        }
      }
    } else {
      throw new Error(response.data.message || '获取实时行情失败')
    }
  } catch (error) {
    console.error('❌ 获取实时行情失败:', error)
    return generateMockQuote(stockCode)
  }
}

/**
 * 获取股票基本信息
 * @param {string} stockCode - 股票代码
 * @returns {Promise<Object>} 股票信息
 */
export async function getStockInfo(stockCode) {
  try {
    const response = await axios.get(`${API_BASE}/api/stock/info`, {
      params: { code: stockCode }
    })
    return response.data
  } catch (error) {
    console.error('获取股票信息失败:', error)
    return {
      success: true,
      data: {
        code: stockCode,
        name: getStockName(stockCode),
        market: stockCode.startsWith('6') ? 'SH' : 'SZ'
      }
    }
  }
}

/**
 * 获取可用数据源状态
 * @returns {Promise<Object>} 数据源状态
 */
export async function getDataSourcesStatus() {
  try {
    const response = await axios.get(`${API_BASE}/api/kline/sources`)
    return response.data
  } catch (error) {
    console.error('获取数据源状态失败:', error)
    return { success: false, sources: [] }
  }
}

/**
 * 计算技术指标
 * @param {Array} klineData - K线数据
 * @param {Array} indicators - 要计算的指标列表
 * @returns {Object} 指标数据
 */
export function calculateIndicators(klineData, indicators = ['MA', 'MACD', 'RSI', 'BOLL', 'KDJ']) {
  const result = {}
  
  if (!klineData || klineData.length === 0) {
    return result
  }
  
  if (indicators.includes('MA')) {
    result.MA5 = calculateMA(klineData, 5)
    result.MA10 = calculateMA(klineData, 10)
    result.MA20 = calculateMA(klineData, 20)
    result.MA60 = calculateMA(klineData, 60)
  }
  
  if (indicators.includes('MACD')) {
    result.MACD = calculateMACD(klineData)
  }
  
  if (indicators.includes('RSI')) {
    result.RSI = calculateRSI(klineData, 14)
  }
  
  if (indicators.includes('BOLL')) {
    result.BOLL = calculateBOLL(klineData, 20, 2)
  }
  
  if (indicators.includes('KDJ')) {
    result.KDJ = calculateKDJ(klineData, 9, 3, 3)
  }
  
  if (indicators.includes('Volume')) {
    result.VolumeMA5 = calculateVolumeMA(klineData, 5)
    result.VolumeMA10 = calculateVolumeMA(klineData, 10)
  }
  
  return result
}

// ==================== 指标计算函数 ====================

function calculateMA(data, period) {
  const result = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < period; j++) {
        sum += data[i - j].close
      }
      result.push(sum / period)
    }
  }
  return result
}

function calculateMACD(data, fast = 12, slow = 26, signal = 9) {
  const emaFast = calculateEMA(data.map(d => d.close), fast)
  const emaSlow = calculateEMA(data.map(d => d.close), slow)
  
  const dif = []
  for (let i = 0; i < data.length; i++) {
    if (emaFast[i] !== null && emaSlow[i] !== null) {
      dif.push(emaFast[i] - emaSlow[i])
    } else {
      dif.push(null)
    }
  }
  
  const dea = calculateEMA(dif.filter(d => d !== null), signal)
  const macd = []
  
  let deaIdx = 0
  for (let i = 0; i < dif.length; i++) {
    if (dif[i] !== null && deaIdx < dea.length) {
      macd.push((dif[i] - dea[deaIdx]) * 2)
      deaIdx++
    } else {
      macd.push(null)
    }
  }
  
  return { DIF: dif, DEA: dea, MACD: macd }
}

function calculateEMA(data, period) {
  const result = []
  const multiplier = 2 / (period + 1)
  
  for (let i = 0; i < data.length; i++) {
    if (data[i] === null) {
      result.push(null)
      continue
    }
    
    if (i === 0) {
      result.push(data[i])
    } else if (result[i - 1] === null) {
      result.push(data[i])
    } else {
      result.push((data[i] - result[i - 1]) * multiplier + result[i - 1])
    }
  }
  
  return result
}

function calculateRSI(data, period = 14) {
  const result = []
  const gains = []
  const losses = []
  
  for (let i = 0; i < data.length; i++) {
    if (i === 0) {
      gains.push(0)
      losses.push(0)
      result.push(null)
      continue
    }
    
    const change = data[i].close - data[i - 1].close
    gains.push(change > 0 ? change : 0)
    losses.push(change < 0 ? -change : 0)
    
    if (i < period) {
      result.push(null)
    } else {
      let avgGain = 0
      let avgLoss = 0
      
      for (let j = 0; j < period; j++) {
        avgGain += gains[i - j]
        avgLoss += losses[i - j]
      }
      
      avgGain /= period
      avgLoss /= period
      
      if (avgLoss === 0) {
        result.push(100)
      } else {
        const rs = avgGain / avgLoss
        result.push(100 - (100 / (1 + rs)))
      }
    }
  }
  
  return result
}

function calculateBOLL(data, period = 20, multiplier = 2) {
  const middle = calculateMA(data, period)
  const upper = []
  const lower = []
  
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      upper.push(null)
      lower.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < period; j++) {
        sum += Math.pow(data[i - j].close - middle[i], 2)
      }
      const std = Math.sqrt(sum / period)
      upper.push(middle[i] + multiplier * std)
      lower.push(middle[i] - multiplier * std)
    }
  }
  
  return { upper, middle, lower }
}

function calculateKDJ(data, n = 9, m1 = 3, m2 = 3) {
  const K = []
  const D = []
  const J = []
  
  for (let i = 0; i < data.length; i++) {
    if (i < n - 1) {
      K.push(50)
      D.push(50)
      J.push(50)
      continue
    }
    
    let high = data[i].high
    let low = data[i].low
    
    for (let j = 1; j < n; j++) {
      high = Math.max(high, data[i - j].high)
      low = Math.min(low, data[i - j].low)
    }
    
    const rsv = high === low ? 50 : ((data[i].close - low) / (high - low)) * 100
    
    const prevK = i > 0 ? K[i - 1] : 50
    const prevD = i > 0 ? D[i - 1] : 50
    
    const k = (2 / 3) * prevK + (1 / 3) * rsv
    const d = (2 / 3) * prevD + (1 / 3) * k
    const j = 3 * k - 2 * d
    
    K.push(k)
    D.push(d)
    J.push(j)
  }
  
  return { K, D, J }
}

function calculateVolumeMA(data, period) {
  const result = []
  for (let i = 0; i < data.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < period; j++) {
        sum += data[i - j].volume
      }
      result.push(sum / period)
    }
  }
  return result
}

// ==================== 模拟数据生成 ====================

function generateMockKlineData(stockCode, count = 120) {
  const data = []
  let basePrice = 20 + Math.random() * 30
  const now = new Date()
  
  for (let i = count - 1; i >= 0; i--) {
    const date = new Date(now)
    date.setDate(date.getDate() - i)
    
    // 跳过周末
    if (date.getDay() === 0 || date.getDay() === 6) continue
    
    const change = (Math.random() - 0.5) * 2
    const open = basePrice
    const close = basePrice + change
    const high = Math.max(open, close) + Math.random() * 0.5
    const low = Math.min(open, close) - Math.random() * 0.5
    const volume = Math.floor(1000000 + Math.random() * 5000000)
    
    data.push({
      date: date.toISOString().split('T')[0],
      open: parseFloat(open.toFixed(2)),
      high: parseFloat(high.toFixed(2)),
      low: parseFloat(low.toFixed(2)),
      close: parseFloat(close.toFixed(2)),
      volume
    })
    
    basePrice = close
  }
  
  return {
    success: true,
    source: 'mock',
    data: {
      code: stockCode,
      name: getStockName(stockCode),
      kline: data
    }
  }
}

function generateMockQuote(stockCode) {
  const price = 20 + Math.random() * 30
  const change = (Math.random() - 0.5) * 4
  
  return {
    success: true,
    source: 'mock',
    data: {
      code: stockCode,
      name: getStockName(stockCode),
      price: parseFloat(price.toFixed(2)),
      change: parseFloat(change.toFixed(2)),
      changePercent: parseFloat((change / price * 100).toFixed(2)),
      open: parseFloat((price - Math.random()).toFixed(2)),
      high: parseFloat((price + Math.random() * 2).toFixed(2)),
      low: parseFloat((price - Math.random() * 2).toFixed(2)),
      volume: Math.floor(1000000 + Math.random() * 5000000),
      amount: Math.floor(50000000 + Math.random() * 100000000),
      time: new Date().toISOString()
    }
  }
}

function getStockName(code) {
  const stockNames = {
    '000001': '平安银行',
    '000002': '万科A',
    '000063': '中兴通讯',
    '000333': '美的集团',
    '000651': '格力电器',
    '000858': '五粮液',
    '002415': '海康威视',
    '002594': '比亚迪',
    '300750': '宁德时代',
    '600000': '浦发银行',
    '600036': '招商银行',
    '600519': '贵州茅台',
    '600900': '长江电力',
    '601318': '中国平安',
    '601398': '工商银行'
  }
  return stockNames[code] || `股票${code}`
}

export default {
  getKlineData,
  getRealtimeQuote,
  getStockInfo,
  getDataSourcesStatus,
  calculateIndicators
}