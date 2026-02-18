/**
 * 技术指标计算工具模块
 * 包含所有技术指标的前端计算逻辑
 * 与后端 backend/utils/technical_indicators.py 保持一致
 */

// ==================== 基础指标计算 ====================

/**
 * 计算移动平均线 (MA)
 * @param {number[]} closes - 收盘价数组
 * @param {number} period - 周期
 * @returns {(number|null)[]} MA值数组
 */
export function calculateMA(closes, period) {
  const result = []
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      result.push(null)
    } else {
      let sum = 0
      for (let j = 0; j < period; j++) {
        sum += closes[i - j]
      }
      result.push(Number((sum / period).toFixed(3)))
    }
  }
  return result
}

/**
 * 计算指数移动平均线 (EMA)
 * @param {number[]} closes - 收盘价数组
 * @param {number} period - 周期
 * @returns {number[]} EMA值数组
 */
export function calculateEMA(closes, period) {
  const result = []
  const multiplier = 2 / (period + 1)
  
  for (let i = 0; i < closes.length; i++) {
    if (i === 0) {
      result.push(closes[i])
    } else {
      const ema = (closes[i] - result[i - 1]) * multiplier + result[i - 1]
      result.push(ema)
    }
  }
  
  return result
}

/**
 * 计算MACD指标
 * @param {number[]} closes - 收盘价数组
 * @param {number} fast - 快线周期 (默认12)
 * @param {number} slow - 慢线周期 (默认26)
 * @param {number} signal - 信号线周期 (默认9)
 * @returns {{DIF: (number|null)[], DEA: (number|null)[], MACD: (number|null)[]}}
 */
export function calculateMACD(closes, fast = 12, slow = 26, signal = 9) {
  const emaFast = calculateEMA(closes, fast)
  const emaSlow = calculateEMA(closes, slow)
  
  const dif = []
  for (let i = 0; i < closes.length; i++) {
    if (i < slow - 1) {
      dif.push(null)
    } else {
      dif.push(Number((emaFast[i] - emaSlow[i]).toFixed(3)))
    }
  }
  
  // 计算DEA (DIF的EMA)
  const difValues = dif.filter(v => v !== null)
  const deaValues = calculateEMA(difValues, signal)
  
  const dea = []
  const macd = []
  let deaIdx = 0
  
  for (let i = 0; i < closes.length; i++) {
    if (dif[i] === null) {
      dea.push(null)
      macd.push(null)
    } else {
      dea.push(Number(deaValues[deaIdx].toFixed(3)))
      macd.push(Number(((dif[i] - deaValues[deaIdx]) * 2).toFixed(3)))
      deaIdx++
    }
  }
  
  return { DIF: dif, DEA: dea, MACD: macd }
}

/**
 * 计算RSI相对强弱指标
 * @param {number[]} closes - 收盘价数组
 * @param {number} period - 周期 (默认14)
 * @returns {(number|null)[]} RSI值数组 (0-100)
 */
export function calculateRSI(closes, period = 14) {
  const result = []
  
  for (let i = 0; i < closes.length; i++) {
    if (i < period) {
      result.push(null)
    } else {
      let gains = 0
      let losses = 0
      for (let j = i - period + 1; j <= i; j++) {
        const change = closes[j] - closes[j - 1]
        if (change > 0) {
          gains += change
        } else {
          losses -= change
        }
      }
      
      const avgGain = gains / period
      const avgLoss = losses / period
      
      let rsi
      if (avgLoss === 0) {
        rsi = 100
      } else {
        const rs = avgGain / avgLoss
        rsi = 100 - (100 / (1 + rs))
      }
      
      result.push(Number(rsi.toFixed(2)))
    }
  }
  
  return result
}

/**
 * 计算KDJ随机指标
 * @param {number[]} highs - 最高价数组
 * @param {number[]} lows - 最低价数组
 * @param {number[]} closes - 收盘价数组
 * @param {number} period - 周期 (默认9)
 * @returns {{K: (number|null)[], D: (number|null)[], J: (number|null)[]}}
 */
export function calculateKDJ(highs, lows, closes, period = 9) {
  const kValues = []
  const dValues = []
  const jValues = []
  
  let prevK = 50
  let prevD = 50
  
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      kValues.push(null)
      dValues.push(null)
      jValues.push(null)
    } else {
      // 计算N日内最高价和最低价
      let highN = -Infinity
      let lowN = Infinity
      for (let j = i - period + 1; j <= i; j++) {
        highN = Math.max(highN, highs[j])
        lowN = Math.min(lowN, lows[j])
      }
      
      // 计算RSV
      let rsv
      if (highN === lowN) {
        rsv = 50
      } else {
        rsv = ((closes[i] - lowN) / (highN - lowN)) * 100
      }
      
      // 计算K, D, J
      const k = (2 / 3) * prevK + (1 / 3) * rsv
      const d = (2 / 3) * prevD + (1 / 3) * k
      const j = 3 * k - 2 * d
      
      kValues.push(Number(k.toFixed(2)))
      dValues.push(Number(d.toFixed(2)))
      jValues.push(Number(j.toFixed(2)))
      
      prevK = k
      prevD = d
    }
  }
  
  return { K: kValues, D: dValues, J: jValues }
}

/**
 * 计算布林带 (BOLL)
 * @param {number[]} closes - 收盘价数组
 * @param {number} period - 周期 (默认20)
 * @param {number} multiplier - 标准差倍数 (默认2)
 * @returns {{upper: (number|null)[], middle: (number|null)[], lower: (number|null)[]}}
 */
export function calculateBOLL(closes, period = 20, multiplier = 2) {
  const upper = []
  const middle = []
  const lower = []
  
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      upper.push(null)
      middle.push(null)
      lower.push(null)
    } else {
      // 计算中轨 (MA)
      let sum = 0
      for (let j = i - period + 1; j <= i; j++) {
        sum += closes[j]
      }
      const ma = sum / period
      
      // 计算标准差
      let squareSum = 0
      for (let j = i - period + 1; j <= i; j++) {
        squareSum += Math.pow(closes[j] - ma, 2)
      }
      const std = Math.sqrt(squareSum / period)
      
      middle.push(Number(ma.toFixed(3)))
      upper.push(Number((ma + multiplier * std).toFixed(3)))
      lower.push(Number((ma - multiplier * std).toFixed(3)))
    }
  }
  
  return { upper, middle, lower }
}

// ==================== 新增指标计算 ====================

/**
 * 计算MTM动量指标
 * MTM = 当日收盘价 - N日前收盘价
 * @param {number[]} closes - 收盘价数组
 * @param {number} period - 周期 (默认12)
 * @returns {(number|null)[]} MTM值数组
 */
export function calculateMTM(closes, period = 12) {
  const result = []
  
  for (let i = 0; i < closes.length; i++) {
    if (i < period) {
      result.push(null)
    } else {
      const mtm = closes[i] - closes[i - period]
      result.push(Number(mtm.toFixed(3)))
    }
  }
  
  return result
}

/**
 * 计算MTM及其均线
 * @param {number[]} closes - 收盘价数组
 * @param {number} mtmPeriod - MTM周期 (默认12)
 * @param {number} maPeriod - MTM均线周期 (默认6)
 * @returns {{MTM: (number|null)[], MTM_MA: (number|null)[]}}
 */
export function calculateMTMWithMA(closes, mtmPeriod = 12, maPeriod = 6) {
  const mtm = calculateMTM(closes, mtmPeriod)
  
  // 计算MTM的移动平均
  const mtmMA = []
  for (let i = 0; i < mtm.length; i++) {
    if (mtm[i] === null || i < mtmPeriod + maPeriod - 1) {
      mtmMA.push(null)
    } else {
      const validMTM = mtm.slice(i - maPeriod + 1, i + 1).filter(v => v !== null)
      if (validMTM.length === maPeriod) {
        const sum = validMTM.reduce((a, b) => a + b, 0)
        mtmMA.push(Number((sum / maPeriod).toFixed(3)))
      } else {
        mtmMA.push(null)
      }
    }
  }
  
  return { MTM: mtm, MTM_MA: mtmMA }
}

/**
 * 计算LWR威廉指标变体 (Larry Williams %R)
 * LWR = (N日内最高价 - 当日收盘价) / (N日内最高价 - N日内最低价) * 100
 * 注意: LWR2 < 30 = 超买; LWR2 > 70 = 超卖 (与RSI相反)
 * @param {number[]} highs - 最高价数组
 * @param {number[]} lows - 最低价数组
 * @param {number[]} closes - 收盘价数组
 * @param {number} period - 周期 (默认14)
 * @returns {{LWR1: (number|null)[], LWR2: (number|null)[]}}
 */
export function calculateLWR(highs, lows, closes, period = 14) {
  const lwr1 = []
  
  for (let i = 0; i < closes.length; i++) {
    if (i < period - 1) {
      lwr1.push(null)
    } else {
      let highN = -Infinity
      let lowN = Infinity
      for (let j = i - period + 1; j <= i; j++) {
        highN = Math.max(highN, highs[j])
        lowN = Math.min(lowN, lows[j])
      }
      
      if (highN === lowN) {
        lwr1.push(50)
      } else {
        const lwr = ((highN - closes[i]) / (highN - lowN)) * 100
        lwr1.push(Number(lwr.toFixed(2)))
      }
    }
  }
  
  // 计算LWR2 (LWR1的3日移动平均)
  const lwr2 = []
  for (let i = 0; i < lwr1.length; i++) {
    if (lwr1[i] === null || i < period + 1) {
      lwr2.push(null)
    } else {
      const validLWR = lwr1.slice(i - 2, i + 1).filter(v => v !== null)
      if (validLWR.length === 3) {
        const sum = validLWR.reduce((a, b) => a + b, 0)
        lwr2.push(Number((sum / 3).toFixed(2)))
      } else {
        lwr2.push(null)
      }
    }
  }
  
  return { LWR1: lwr1, LWR2: lwr2 }
}

/**
 * 计算OBV能量潮指标
 * OBV = 前一日OBV + (今日收盘价 > 昨日收盘价 ? 今日成交量 : -今日成交量)
 * @param {number[]} closes - 收盘价数组
 * @param {number[]} volumes - 成交量数组
 * @returns {number[]} OBV值数组
 */
export function calculateOBV(closes, volumes) {
  const result = [volumes[0]] // 第一天OBV等于成交量
  
  for (let i = 1; i < closes.length; i++) {
    let obv
    if (closes[i] > closes[i - 1]) {
      obv = result[i - 1] + volumes[i]
    } else if (closes[i] < closes[i - 1]) {
      obv = result[i - 1] - volumes[i]
    } else {
      obv = result[i - 1]
    }
    result.push(Math.round(obv))
  }
  
  return result
}

/**
 * 计算BBI多空均线指标
 * BBI = (MA3 + MA6 + MA12 + MA24) / 4
 * @param {number[]} closes - 收盘价数组
 * @returns {(number|null)[]} BBI值数组
 */
export function calculateBBI(closes) {
  const ma3 = calculateMA(closes, 3)
  const ma6 = calculateMA(closes, 6)
  const ma12 = calculateMA(closes, 12)
  const ma24 = calculateMA(closes, 24)
  
  const result = []
  for (let i = 0; i < closes.length; i++) {
    if (ma24[i] === null || ma12[i] === null || ma6[i] === null || ma3[i] === null) {
      result.push(null)
    } else {
      const bbi = (ma3[i] + ma6[i] + ma12[i] + ma24[i]) / 4
      result.push(Number(bbi.toFixed(3)))
    }
  }
  
  return result
}

// ==================== 综合指标计算 ====================

/**
 * 计算六脉神剑综合指标
 * 融合 MACD、KDJ、RSI、LWR、BBI、MTM 六个指标
 * @param {number[]} closes - 收盘价数组
 * @param {number[]} highs - 最高价数组
 * @param {number[]} lows - 最低价数组
 * @param {number[]} volumes - 成交量数组
 * @returns {Object} 包含所有指标及综合信号的对象
 */
export function calculateSixPulseIndicator(closes, highs, lows, volumes) {
  const macd = calculateMACD(closes)
  const kdj = calculateKDJ(highs, lows, closes)
  const rsi = calculateRSI(closes)
  const lwr = calculateLWR(highs, lows, closes)
  const bbi = calculateBBI(closes)
  const mtm = calculateMTMWithMA(closes)
  
  // 计算综合信号
  const signals = []
  for (let i = 0; i < closes.length; i++) {
    let bullishCount = 0
    let bearishCount = 0
    
    // MACD信号
    if (macd.MACD[i] !== null) {
      if (macd.DIF[i] > macd.DEA[i]) {
        bullishCount++
      } else {
        bearishCount++
      }
    }
    
    // KDJ信号
    if (kdj.K[i] !== null) {
      if (kdj.K[i] > kdj.D[i]) {
        bullishCount++
      } else {
        bearishCount++
      }
    }
    
    // RSI信号
    if (rsi[i] !== null) {
      if (rsi[i] > 50) {
        bullishCount++
      } else {
        bearishCount++
      }
    }
    
    // LWR信号 (注意: LWR < 30 超买, > 70 超卖)
    if (lwr.LWR2[i] !== null) {
      if (lwr.LWR2[i] < 50) {
        bullishCount++
      } else {
        bearishCount++
      }
    }
    
    // BBI信号
    if (bbi[i] !== null) {
      if (closes[i] > bbi[i]) {
        bullishCount++
      } else {
        bearishCount++
      }
    }
    
    // MTM信号
    if (mtm.MTM[i] !== null) {
      if (mtm.MTM[i] > 0) {
        bullishCount++
      } else {
        bearishCount++
      }
    }
    
    signals.push({
      bullish: bullishCount,
      bearish: bearishCount,
      signal: bullishCount >= 4 ? 'BUY' : (bearishCount >= 4 ? 'SELL' : 'HOLD')
    })
  }
  
  return {
    MACD: macd,
    KDJ: kdj,
    RSI: rsi,
    LWR: lwr,
    BBI: bbi,
    MTM: mtm,
    signals
  }
}

/**
 * 计算所有技术指标
 * @param {Object[]} klines - K线数据数组
 * @returns {Object} 包含所有指标的对象
 */
export function calculateAllIndicators(klines) {
  if (!klines || klines.length === 0) {
    return {}
  }
  
  // 提取数据
  const dates = klines.map(k => k.date || k.time || '')
  const opens = klines.map(k => Number(k.open) || 0)
  const highs = klines.map(k => Number(k.high) || 0)
  const lows = klines.map(k => Number(k.low) || 0)
  const closes = klines.map(k => Number(k.close) || 0)
  const volumes = klines.map(k => Number(k.volume) || 0)
  
  return {
    dates,
    // 均线
    MA5: calculateMA(closes, 5),
    MA10: calculateMA(closes, 10),
    MA20: calculateMA(closes, 20),
    MA60: calculateMA(closes, 60),
    // MACD
    MACD: calculateMACD(closes),
    // RSI
    RSI: calculateRSI(closes),
    // KDJ
    KDJ: calculateKDJ(highs, lows, closes),
    // 布林带
    BOLL: calculateBOLL(closes),
    // MTM动量
    MTM: calculateMTMWithMA(closes),
    // LWR威廉
    LWR: calculateLWR(highs, lows, closes),
    // OBV能量潮
    OBV: calculateOBV(closes, volumes),
    // BBI多空均线
    BBI: calculateBBI(closes),
    // 六脉神剑综合指标
    SIX_PULSE: calculateSixPulseIndicator(closes, highs, lows, volumes)
  }
}

// ==================== 信号检测 ====================

/**
 * 检测均线金叉/死叉
 * @param {(number|null)[]} maShort - 短期均线
 * @param {(number|null)[]} maLong - 长期均线
 * @param {string[]} dates - 日期数组
 * @param {number} shortPeriod - 短期周期
 * @param {number} longPeriod - 长期周期
 * @returns {Object[]} 信号数组
 */
export function detectMACross(maShort, maLong, dates, shortPeriod = 5, longPeriod = 20) {
  const signals = []
  
  for (let i = 1; i < maShort.length; i++) {
    if (maShort[i] === null || maLong[i] === null) continue
    if (maShort[i - 1] === null || maLong[i - 1] === null) continue
    
    const prevDiff = maShort[i - 1] - maLong[i - 1]
    const currDiff = maShort[i] - maLong[i]
    
    // 金叉
    if (prevDiff <= 0 && currDiff > 0) {
      signals.push({
        name: `MA${shortPeriod}/MA${longPeriod}金叉`,
        type: 'golden_cross',
        direction: 'bullish',
        index: i,
        date: dates[i] || '',
        confidence: 0.75,
        description: `MA${shortPeriod}上穿MA${longPeriod}，明确上涨信号`,
        price: maShort[i],
        importance: 'high',
        indicator: 'MA'
      })
    }
    // 死叉
    else if (prevDiff >= 0 && currDiff < 0) {
      signals.push({
        name: `MA${shortPeriod}/MA${longPeriod}死叉`,
        type: 'death_cross',
        direction: 'bearish',
        index: i,
        date: dates[i] || '',
        confidence: 0.75,
        description: `MA${shortPeriod}下穿MA${longPeriod}，明确下跌信号`,
        price: maShort[i],
        importance: 'high',
        indicator: 'MA'
      })
    }
  }
  
  return signals
}

/**
 * 检测MACD金叉/死叉
 * @param {(number|null)[]} dif - DIF线
 * @param {(number|null)[]} dea - DEA线
 * @param {string[]} dates - 日期数组
 * @returns {Object[]} 信号数组
 */
export function detectMACDCross(dif, dea, dates) {
  const signals = []
  
  for (let i = 1; i < dif.length; i++) {
    if (dif[i] === null || dea[i] === null) continue
    if (dif[i - 1] === null || dea[i - 1] === null) continue
    
    const prevDiff = dif[i - 1] - dea[i - 1]
    const currDiff = dif[i] - dea[i]
    
    // MACD金叉
    if (prevDiff <= 0 && currDiff > 0) {
      const aboveZero = dif[i] > 0 && dea[i] > 0
      signals.push({
        name: 'MACD金叉',
        type: 'golden_cross',
        direction: 'bullish',
        index: i,
        date: dates[i] || '',
        confidence: aboveZero ? 0.85 : 0.7,
        description: 'DIF上穿DEA，中期上涨信号' + (aboveZero ? '（零轴上方，信号更强）' : ''),
        price: dif[i],
        importance: 'high',
        indicator: 'MACD'
      })
    }
    // MACD死叉
    else if (prevDiff >= 0 && currDiff < 0) {
      const belowZero = dif[i] < 0 && dea[i] < 0
      signals.push({
        name: 'MACD死叉',
        type: 'death_cross',
        direction: 'bearish',
        index: i,
        date: dates[i] || '',
        confidence: belowZero ? 0.85 : 0.7,
        description: 'DIF下穿DEA，中期下跌信号' + (belowZero ? '（零轴下方，信号更强）' : ''),
        price: dif[i],
        importance: 'high',
        indicator: 'MACD'
      })
    }
  }
  
  return signals
}

/**
 * 检测所有交易信号
 * @param {Object[]} klines - K线数据
 * @param {Object} indicators - 指标数据
 * @returns {Object[]} 所有信号
 */
export function detectAllSignals(klines, indicators) {
  const signals = []
  const dates = indicators.dates || []
  
  // 均线金叉死叉
  if (indicators.MA5 && indicators.MA10) {
    signals.push(...detectMACross(indicators.MA5, indicators.MA10, dates, 5, 10))
  }
  if (indicators.MA5 && indicators.MA20) {
    signals.push(...detectMACross(indicators.MA5, indicators.MA20, dates, 5, 20))
  }
  if (indicators.MA10 && indicators.MA60) {
    signals.push(...detectMACross(indicators.MA10, indicators.MA60, dates, 10, 60))
  }
  
  // MACD信号
  if (indicators.MACD) {
    signals.push(...detectMACDCross(indicators.MACD.DIF, indicators.MACD.DEA, dates))
  }
  
  // 按索引排序
  signals.sort((a, b) => a.index - b.index)
  
  return signals
}

/**
 * 获取最近N根K线的信号
 * @param {Object[]} klines - K线数据
 * @param {Object} indicators - 指标数据
 * @param {number} lookback - 回看数量
 * @returns {Object[]} 最近的信号
 */
export function getRecentSignals(klines, indicators, lookback = 5) {
  const allSignals = detectAllSignals(klines, indicators)
  const minIndex = klines.length - lookback
  return allSignals.filter(s => s.index >= minIndex)
}

// ==================== K线形态识别 ====================

/**
 * 判断是否为十字星
 * @param {number} open - 开盘价
 * @param {number} high - 最高价
 * @param {number} low - 最低价
 * @param {number} close - 收盘价
 * @param {number} threshold - 实体占振幅的比例阈值
 * @returns {boolean}
 */
export function isDoji(open, high, low, close, threshold = 0.1) {
  const body = Math.abs(close - open)
  const range = high - low
  if (range === 0) return false
  return (body / range) < threshold
}

/**
 * 判断是否为锤子线
 * @param {number} open - 开盘价
 * @param {number} high - 最高价
 * @param {number} low - 最低价
 * @param {number} close - 收盘价
 * @returns {boolean}
 */
export function isHammer(open, high, low, close) {
  const body = Math.abs(close - open)
  const range = high - low
  if (range === 0 || body === 0) return false
  
  const upperShadow = high - Math.max(open, close)
  const lowerShadow = Math.min(open, close) - low
  
  return (body / range) < 0.3 && lowerShadow >= body * 2 && upperShadow < body * 0.5
}

/**
 * 判断是否为射击之星
 * @param {number} open - 开盘价
 * @param {number} high - 最高价
 * @param {number} low - 最低价
 * @param {number} close - 收盘价
 * @returns {boolean}
 */
export function isShootingStar(open, high, low, close) {
  const body = Math.abs(close - open)
  const range = high - low
  if (range === 0 || body === 0) return false
  
  const upperShadow = high - Math.max(open, close)
  const lowerShadow = Math.min(open, close) - low
  
  return (body / range) < 0.3 && upperShadow >= body * 2 && lowerShadow < body * 0.5
}

/**
 * 检测双针探顶形态
 * @param {Object[]} klines - K线数据
 * @param {number} index - 当前索引
 * @returns {Object|null}
 */
export function detectDoubleNeedleTop(klines, index) {
  if (index < 1) return null
  
  const curr = klines[index]
  const prev = klines[index - 1]
  
  const currHigh = Number(curr.high)
  const currClose = Number(curr.close)
  const currOpen = Number(curr.open)
  const prevHigh = Number(prev.high)
  const prevClose = Number(prev.close)
  const prevOpen = Number(prev.open)
  
  const currUpperShadow = currHigh - Math.max(currOpen, currClose)
  const prevUpperShadow = prevHigh - Math.max(prevOpen, prevClose)
  const currBody = Math.abs(currClose - currOpen)
  const prevBody = Math.abs(prevClose - prevOpen)
  
  if (currUpperShadow > currBody && prevUpperShadow > prevBody &&
      Math.abs(currHigh - prevHigh) / Math.max(currHigh, prevHigh) < 0.02) {
    return {
      name: '双针探顶',
      nameEn: 'Double Needle Top',
      type: 'bearish',
      index,
      date: curr.date || curr.time || '',
      confidence: 0.75,
      description: '高位连续2根长上影线，最高价接近，上涨见顶信号',
      price: Math.max(currHigh, prevHigh),
      importance: 'high'
    }
  }
  return null
}

/**
 * 检测双针探底形态
 * @param {Object[]} klines - K线数据
 * @param {number} index - 当前索引
 * @returns {Object|null}
 */
export function detectDoubleNeedleBottom(klines, index) {
  if (index < 1) return null
  
  const curr = klines[index]
  const prev = klines[index - 1]
  
  const currLow = Number(curr.low)
  const currClose = Number(curr.close)
  const currOpen = Number(curr.open)
  const prevLow = Number(prev.low)
  const prevClose = Number(prev.close)
  const prevOpen = Number(prev.open)
  
  const currLowerShadow = Math.min(currOpen, currClose) - currLow
  const prevLowerShadow = Math.min(prevOpen, prevClose) - prevLow
  const currBody = Math.abs(currClose - currOpen)
  const prevBody = Math.abs(prevClose - prevOpen)
  
  if (currLowerShadow > currBody && prevLowerShadow > prevBody &&
      Math.abs(currLow - prevLow) / Math.max(currLow, prevLow, 0.01) < 0.02) {
    return {
      name: '双针探底',
      nameEn: 'Double Needle Bottom',
      type: 'bullish',
      index,
      date: curr.date || curr.time || '',
      confidence: 0.75,
      description: '低位连续2根长下影线，最低价接近，下跌见底信号',
      price: Math.min(currLow, prevLow),
      importance: 'high'
    }
  }
  return null
}

/**
 * 检测三阳不过阴形态
 * @param {Object[]} klines - K线数据
 * @param {number} index - 当前索引
 * @returns {Object|null}
 */
export function detectThreeYangNotOverYin(klines, index) {
  if (index < 3) return null
  
  const k0 = klines[index - 3]
  const k1 = klines[index - 2]
  const k2 = klines[index - 1]
  const k3 = klines[index]
  
  const k0Open = Number(k0.open)
  const k0Close = Number(k0.close)
  const k0High = Number(k0.high)
  
  // k0必须是阴线
  if (k0Close >= k0Open) return null
  
  // k1, k2, k3必须都是阳线
  for (const k of [k1, k2, k3]) {
    if (Number(k.close) <= Number(k.open)) return null
  }
  
  // 3根阳线都未突破阴线最高点
  const k1High = Number(k1.high)
  const k2High = Number(k2.high)
  const k3High = Number(k3.high)
  
  if (k1High < k0High && k2High < k0High && k3High < k0High) {
    return {
      name: '三阳不过阴',
      nameEn: 'Three Yang Not Over Yin',
      type: 'bearish',
      index,
      date: k3.date || k3.time || '',
      confidence: 0.8,
      description: '长阴后3阳未破阴顶，空方主导，暴跌信号',
      price: k0High,
      importance: 'high'
    }
  }
  return null
}

/**
 * 检测三阴不过阳形态
 * @param {Object[]} klines - K线数据
 * @param {number} index - 当前索引
 * @returns {Object|null}
 */
export function detectThreeYinNotOverYang(klines, index) {
  if (index < 3) return null
  
  const k0 = klines[index - 3]
  const k1 = klines[index - 2]
  const k2 = klines[index - 1]
  const k3 = klines[index]
  
  const k0Open = Number(k0.open)
  const k0Close = Number(k0.close)
  const k0Low = Number(k0.low)
  
  // k0必须是阳线
  if (k0Close <= k0Open) return null
  
  // k1, k2, k3必须都是阴线
  for (const k of [k1, k2, k3]) {
    if (Number(k.close) >= Number(k.open)) return null
  }
  
  // 3根阴线都未跌破阳线最低点
  const k1Low = Number(k1.low)
  const k2Low = Number(k2.low)
  const k3Low = Number(k3.low)
  
  if (k1Low > k0Low && k2Low > k0Low && k3Low > k0Low) {
    return {
      name: '三阴不过阳',
      nameEn: 'Three Yin Not Over Yang',
      type: 'bullish',
      index,
      date: k3.date || k3.time || '',
      confidence: 0.8,
      description: '长阳后3阴未破阳底，多方主导，暴涨信号',
      price: k0Low,
      importance: 'high'
    }
  }
  return null
}

/**
 * 检测十字星
 * @param {Object[]} klines - K线数据
 * @param {number} index - 当前索引
 * @returns {Object|null}
 */
export function detectDoji(klines, index) {
  if (index < 0 || index >= klines.length) return null
  
  const k = klines[index]
  const open = Number(k.open)
  const high = Number(k.high)
  const low = Number(k.low)
  const close = Number(k.close)
  
  if (isDoji(open, high, low, close)) {
    return {
      name: '十字星',
      nameEn: 'Doji',
      type: 'neutral',
      index,
      date: k.date || k.time || '',
      confidence: 0.5,
      description: '开盘价≈收盘价，多空分歧大，需结合位置判断',
      price: close,
      importance: 'low'
    }
  }
  return null
}

/**
 * 检测锤子线或吊线
 * @param {Object[]} klines - K线数据
 * @param {number} index - 当前索引
 * @param {number} lookback - 回看周期
 * @returns {Object|null}
 */
export function detectHammerOrHanging(klines, index, lookback = 10) {
  if (index < lookback) return null
  
  const k = klines[index]
  const open = Number(k.open)
  const high = Number(k.high)
  const low = Number(k.low)
  const close = Number(k.close)
  
  if (!isHammer(open, high, low, close)) return null
  
  // 判断是高位还是低位
  let sum = 0
  for (let i = index - lookback; i < index; i++) {
    sum += Number(klines[i].close)
  }
  const avgClose = sum / lookback
  
  if (close > avgClose * 1.05) {
    return {
      name: '高位吊线',
      nameEn: 'Hanging Man',
      type: 'bearish',
      index,
      date: k.date || k.time || '',
      confidence: 0.6,
      description: '高位小实体+长下影，上涨底气不足',
      price: close,
      importance: 'medium'
    }
  } else if (close < avgClose * 0.95) {
    return {
      name: '低位锤线',
      nameEn: 'Hammer',
      type: 'bullish',
      index,
      date: k.date || k.time || '',
      confidence: 0.6,
      description: '低位小实体+长下影，下跌动能衰竭',
      price: close,
      importance: 'medium'
    }
  }
  return null
}

/**
 * 检测上升受阻形态
 * @param {Object[]} klines - K线数据
 * @param {number} index - 当前索引
 * @returns {Object|null}
 */
export function detectRisingResistance(klines, index) {
  if (index < 2) return null
  
  const curr = klines[index]
  const prev = klines[index - 1]
  
  const currOpen = Number(curr.open)
  const currClose = Number(curr.close)
  const currHigh = Number(curr.high)
  const prevOpen = Number(prev.open)
  const prevClose = Number(prev.close)
  
  // 当前是阳线
  if (currClose <= currOpen) return null
  
  const currBody = currClose - currOpen
  const prevBody = Math.abs(prevClose - prevOpen)
  const currUpperShadow = currHigh - currClose
  
  if (currBody < prevBody * 0.7 && currUpperShadow > currBody) {
    return {
      name: '上升受阻',
      nameEn: 'Rising Resistance',
      type: 'bearish',
      index,
      date: curr.date || curr.time || '',
      confidence: 0.6,
      description: '阳线实体缩小+长上影，趋势动能衰减，可能回调',
      price: currHigh,
      importance: 'medium'
    }
  }
  return null
}

/**
 * 检测下跌受阻形态
 * @param {Object[]} klines - K线数据
 * @param {number} index - 当前索引
 * @returns {Object|null}
 */
export function detectFallingSupport(klines, index) {
  if (index < 2) return null
  
  const curr = klines[index]
  const prev = klines[index - 1]
  
  const currOpen = Number(curr.open)
  const currClose = Number(curr.close)
  const currLow = Number(curr.low)
  const prevOpen = Number(prev.open)
  const prevClose = Number(prev.close)
  
  // 当前是阴线
  if (currClose >= currOpen) return null
  
  const currBody = currOpen - currClose
  const prevBody = Math.abs(prevClose - prevOpen)
  const currLowerShadow = currClose - currLow
  
  if (currBody < prevBody * 0.7 && currLowerShadow > currBody) {
    return {
      name: '下跌受阻',
      nameEn: 'Falling Support',
      type: 'bullish',
      index,
      date: curr.date || curr.time || '',
      confidence: 0.6,
      description: '阴线实体缩小+长下影，趋势动能衰减，可能反弹',
      price: currLow,
      importance: 'medium'
    }
  }
  return null
}

/**
 * 检测所有K线形态
 * @param {Object[]} klines - K线数据
 * @returns {Object[]} 形态数组
 */
export function detectAllPatterns(klines) {
  const patterns = []
  
  if (!klines || klines.length < 5) return patterns
  
  for (let i = 0; i < klines.length; i++) {
    // 单K线形态
    const doji = detectDoji(klines, i)
    if (doji) patterns.push(doji)
    
    const hammer = detectHammerOrHanging(klines, i)
    if (hammer) patterns.push(hammer)
    
    // 组合K线形态
    const doubleTop = detectDoubleNeedleTop(klines, i)
    if (doubleTop) patterns.push(doubleTop)
    
    const doubleBottom = detectDoubleNeedleBottom(klines, i)
    if (doubleBottom) patterns.push(doubleBottom)
    
    const threeYang = detectThreeYangNotOverYin(klines, i)
    if (threeYang) patterns.push(threeYang)
    
    const threeYin = detectThreeYinNotOverYang(klines, i)
    if (threeYin) patterns.push(threeYin)
    
    const risingRes = detectRisingResistance(klines, i)
    if (risingRes) patterns.push(risingRes)
    
    const fallingSup = detectFallingSupport(klines, i)
    if (fallingSup) patterns.push(fallingSup)
  }
  
  // 按索引排序
  patterns.sort((a, b) => a.index - b.index)
  
  return patterns
}

/**
 * 获取最近N根K线的形态
 * @param {Object[]} klines - K线数据
 * @param {number} lookback - 回看数量
 * @returns {Object[]} 最近的形态
 */
export function getRecentPatterns(klines, lookback = 5) {
  const allPatterns = detectAllPatterns(klines)
  const minIndex = klines.length - lookback
  return allPatterns.filter(p => p.index >= minIndex)
}

// ==================== 更多信号检测 ====================

/**
 * 检测KDJ金叉/死叉
 * @param {(number|null)[]} k - K线
 * @param {(number|null)[]} d - D线
 * @param {(number|null)[]} j - J线
 * @param {string[]} dates - 日期数组
 * @returns {Object[]} 信号数组
 */
export function detectKDJCross(k, d, j, dates) {
  const signals = []
  
  for (let i = 1; i < k.length; i++) {
    if (k[i] === null || d[i] === null) continue
    if (k[i - 1] === null || d[i - 1] === null) continue
    
    const prevDiff = k[i - 1] - d[i - 1]
    const currDiff = k[i] - d[i]
    
    // KDJ金叉
    if (prevDiff <= 0 && currDiff > 0) {
      const isLow = k[i] < 30
      signals.push({
        name: 'KDJ金叉',
        type: 'golden_cross',
        direction: 'bullish',
        index: i,
        date: dates[i] || '',
        confidence: isLow ? 0.75 : 0.55,
        description: 'K线上穿D线' + (isLow ? '，低位金叉信号较强' : '，注意可能骗线'),
        price: k[i],
        importance: isLow ? 'medium' : 'low',
        indicator: 'KDJ'
      })
    }
    // KDJ死叉
    else if (prevDiff >= 0 && currDiff < 0) {
      const isHigh = k[i] > 70
      signals.push({
        name: 'KDJ死叉',
        type: 'death_cross',
        direction: 'bearish',
        index: i,
        date: dates[i] || '',
        confidence: isHigh ? 0.75 : 0.55,
        description: 'K线下穿D线' + (isHigh ? '，高位死叉信号较强' : '，注意可能骗线'),
        price: k[i],
        importance: isHigh ? 'medium' : 'low',
        indicator: 'KDJ'
      })
    }
    
    // J值超买超卖
    if (j[i] !== null) {
      if (j[i] > 100) {
        signals.push({
          name: 'KDJ超买',
          type: 'overbought',
          direction: 'bearish',
          index: i,
          date: dates[i] || '',
          confidence: 0.6,
          description: `J值=${j[i].toFixed(1)}>100，短期超买`,
          price: j[i],
          importance: 'low',
          indicator: 'KDJ'
        })
      } else if (j[i] < 0) {
        signals.push({
          name: 'KDJ超卖',
          type: 'oversold',
          direction: 'bullish',
          index: i,
          date: dates[i] || '',
          confidence: 0.6,
          description: `J值=${j[i].toFixed(1)}<0，短期超卖`,
          price: j[i],
          importance: 'low',
          indicator: 'KDJ'
        })
      }
    }
  }
  
  return signals
}

/**
 * 检测RSI超买超卖信号
 * @param {(number|null)[]} rsi - RSI数据
 * @param {string[]} dates - 日期数组
 * @returns {Object[]} 信号数组
 */
export function detectRSISignals(rsi, dates) {
  const signals = []
  
  for (let i = 0; i < rsi.length; i++) {
    if (rsi[i] === null) continue
    
    if (rsi[i] > 70) {
      signals.push({
        name: 'RSI超买',
        type: 'overbought',
        direction: 'bearish',
        index: i,
        date: dates[i] || '',
        confidence: 0.6,
        description: `RSI=${rsi[i].toFixed(1)}>70，价格过涨，但可能钝化`,
        price: rsi[i],
        importance: 'medium',
        indicator: 'RSI'
      })
    } else if (rsi[i] < 30) {
      signals.push({
        name: 'RSI超卖',
        type: 'oversold',
        direction: 'bullish',
        index: i,
        date: dates[i] || '',
        confidence: 0.6,
        description: `RSI=${rsi[i].toFixed(1)}<30，价格过跌，但可能钝化`,
        price: rsi[i],
        importance: 'medium',
        indicator: 'RSI'
      })
    }
  }
  
  return signals
}

/**
 * 检测量价信号
 * @param {number[]} closes - 收盘价数组
 * @param {number[]} volumes - 成交量数组
 * @param {string[]} dates - 日期数组
 * @param {number} lookback - 回看周期
 * @returns {Object[]} 信号数组
 */
export function detectVolumePriceSignals(closes, volumes, dates, lookback = 5) {
  const signals = []
  
  for (let i = lookback; i < closes.length; i++) {
    const priceChange = (closes[i] - closes[i - lookback]) / closes[i - lookback]
    
    let avgVolumePrev = 0
    for (let j = i - lookback; j < i; j++) {
      avgVolumePrev += volumes[j]
    }
    avgVolumePrev /= lookback
    
    const volumeChange = (volumes[i] - avgVolumePrev) / Math.max(avgVolumePrev, 1)
    
    // 量价齐升
    if (priceChange > 0.02 && volumeChange > 0.3) {
      signals.push({
        name: '量价齐升',
        type: 'volume_price_up',
        direction: 'bullish',
        index: i,
        date: dates[i] || '',
        confidence: 0.7,
        description: `价格上涨${(priceChange * 100).toFixed(1)}%，成交量放大${(volumeChange * 100).toFixed(0)}%，趋势延续`,
        price: closes[i],
        importance: 'medium',
        indicator: 'VOLUME'
      })
    }
    // 量价齐跌
    else if (priceChange < -0.02 && volumeChange > 0.3) {
      signals.push({
        name: '量价齐跌',
        type: 'volume_price_down',
        direction: 'bearish',
        index: i,
        date: dates[i] || '',
        confidence: 0.7,
        description: `价格下跌${(Math.abs(priceChange) * 100).toFixed(1)}%，成交量放大${(volumeChange * 100).toFixed(0)}%，趋势延续`,
        price: closes[i],
        importance: 'medium',
        indicator: 'VOLUME'
      })
    }
    // 量价背离（价涨量缩）
    else if (priceChange > 0.02 && volumeChange < -0.2) {
      signals.push({
        name: '量价背离(价涨量缩)',
        type: 'volume_divergence',
        direction: 'bearish',
        index: i,
        date: dates[i] || '',
        confidence: 0.65,
        description: `价格上涨${(priceChange * 100).toFixed(1)}%但成交量萎缩${(Math.abs(volumeChange) * 100).toFixed(0)}%，可能反转`,
        price: closes[i],
        importance: 'medium',
        indicator: 'VOLUME'
      })
    }
    // 量价背离（价跌量缩）
    else if (priceChange < -0.02 && volumeChange < -0.2) {
      signals.push({
        name: '量价背离(价跌量缩)',
        type: 'volume_divergence',
        direction: 'bullish',
        index: i,
        date: dates[i] || '',
        confidence: 0.65,
        description: `价格下跌${(Math.abs(priceChange) * 100).toFixed(1)}%但成交量萎缩${(Math.abs(volumeChange) * 100).toFixed(0)}%，可能反转`,
        price: closes[i],
        importance: 'medium',
        indicator: 'VOLUME'
      })
    }
  }
  
  return signals
}

/**
 * 获取信号汇总
 * @param {Object[]} signals - 信号数组
 * @returns {Object} 汇总信息
 */
export function getSignalSummary(signals) {
  const bullishCount = signals.filter(s => s.direction === 'bullish').length
  const bearishCount = signals.filter(s => s.direction === 'bearish').length
  const highImportance = signals.filter(s => s.importance === 'high')
  
  return {
    total: signals.length,
    bullish: bullishCount,
    bearish: bearishCount,
    highImportanceSignals: highImportance.map(s => ({
      name: s.name,
      direction: s.direction,
      date: s.date,
      description: s.description
    })),
    recommendation: bullishCount > bearishCount + 2 ? 'BUY' : 
                    (bearishCount > bullishCount + 2 ? 'SELL' : 'HOLD'),
    confidence: signals.length > 0 ? Math.max(...signals.map(s => s.confidence)) : 0
  }
}

export default {
  calculateMA,
  calculateEMA,
  calculateMACD,
  calculateRSI,
  calculateKDJ,
  calculateBOLL,
  calculateMTM,
  calculateMTMWithMA,
  calculateLWR,
  calculateOBV,
  calculateBBI,
  calculateSixPulseIndicator,
  calculateAllIndicators,
  detectMACross,
  detectMACDCross,
  detectAllSignals,
  getRecentSignals,
  // K线形态识别
  isDoji,
  isHammer,
  isShootingStar,
  detectDoubleNeedleTop,
  detectDoubleNeedleBottom,
  detectThreeYangNotOverYin,
  detectThreeYinNotOverYang,
  detectDoji,
  detectHammerOrHanging,
  detectRisingResistance,
  detectFallingSupport,
  detectAllPatterns,
  getRecentPatterns,
  // 更多信号检测
  detectKDJCross,
  detectRSISignals,
  detectVolumePriceSignals,
  getSignalSummary
}
