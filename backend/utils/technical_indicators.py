"""
技术指标计算模块
包含所有技术指标的计算逻辑，支持K线图表指标.md中定义的全部指标
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class KlineData:
    """K线数据结构"""

    date: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: float = 0.0


# ==================== 基础指标计算 ====================


def calculate_ma(closes: List[float], period: int) -> List[Optional[float]]:
    """
    计算移动平均线 (MA)

    Args:
        closes: 收盘价列表
        period: 周期

    Returns:
        MA值列表
    """
    result = []
    for i in range(len(closes)):
        if i < period - 1:
            result.append(None)
        else:
            ma = sum(closes[i - period + 1 : i + 1]) / period
            result.append(round(ma, 3))
    return result


def calculate_ema(closes: List[float], period: int) -> List[float]:
    """
    计算指数移动平均线 (EMA)

    Args:
        closes: 收盘价列表
        period: 周期

    Returns:
        EMA值列表
    """
    result = []
    multiplier = 2 / (period + 1)

    for i, close in enumerate(closes):
        if i == 0:
            result.append(close)
        else:
            ema = (close - result[i - 1]) * multiplier + result[i - 1]
            result.append(ema)

    return result


def calculate_macd(
    closes: List[float], fast: int = 12, slow: int = 26, signal: int = 9
) -> Dict[str, List[Optional[float]]]:
    """
    计算MACD指标

    Args:
        closes: 收盘价列表
        fast: 快线周期 (默认12)
        slow: 慢线周期 (默认26)
        signal: 信号线周期 (默认9)

    Returns:
        包含DIF, DEA, MACD的字典
    """
    ema_fast = calculate_ema(closes, fast)
    ema_slow = calculate_ema(closes, slow)

    dif = []
    for i in range(len(closes)):
        if i < slow - 1:
            dif.append(None)
        else:
            dif.append(round(ema_fast[i] - ema_slow[i], 3))

    # 计算DEA (DIF的EMA)
    dif_values = [v for v in dif if v is not None]
    dea_values = calculate_ema(dif_values, signal)

    dea = []
    macd = []
    dea_idx = 0

    for i in range(len(closes)):
        if dif[i] is None:
            dea.append(None)
            macd.append(None)
        else:
            dea.append(round(dea_values[dea_idx], 3))
            macd.append(round((dif[i] - dea_values[dea_idx]) * 2, 3))
            dea_idx += 1

    return {"DIF": dif, "DEA": dea, "MACD": macd}


def calculate_rsi(closes: List[float], period: int = 14) -> List[Optional[float]]:
    """
    计算RSI相对强弱指标

    Args:
        closes: 收盘价列表
        period: 周期 (默认14)

    Returns:
        RSI值列表 (0-100)
    """
    result = []

    for i in range(len(closes)):
        if i < period:
            result.append(None)
        else:
            gains = 0
            losses = 0
            for j in range(i - period + 1, i + 1):
                change = closes[j] - closes[j - 1]
                if change > 0:
                    gains += change
                else:
                    losses -= change

            avg_gain = gains / period
            avg_loss = losses / period

            if avg_loss == 0:
                rsi = 100
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))

            result.append(round(rsi, 2))

    return result


def calculate_kdj(
    highs: List[float], lows: List[float], closes: List[float], period: int = 9
) -> Dict[str, List[Optional[float]]]:
    """
    计算KDJ随机指标

    Args:
        highs: 最高价列表
        lows: 最低价列表
        closes: 收盘价列表
        period: 周期 (默认9)

    Returns:
        包含K, D, J的字典
    """
    k_values = []
    d_values = []
    j_values = []

    prev_k = 50
    prev_d = 50

    for i in range(len(closes)):
        if i < period - 1:
            k_values.append(None)
            d_values.append(None)
            j_values.append(None)
        else:
            # 计算N日内最高价和最低价
            high_n = max(highs[i - period + 1 : i + 1])
            low_n = min(lows[i - period + 1 : i + 1])

            # 计算RSV
            if high_n == low_n:
                rsv = 50
            else:
                rsv = (closes[i] - low_n) / (high_n - low_n) * 100

            # 计算K, D, J
            k = (2 / 3) * prev_k + (1 / 3) * rsv
            d = (2 / 3) * prev_d + (1 / 3) * k
            j = 3 * k - 2 * d

            k_values.append(round(k, 2))
            d_values.append(round(d, 2))
            j_values.append(round(j, 2))

            prev_k = k
            prev_d = d

    return {"K": k_values, "D": d_values, "J": j_values}


def calculate_boll(
    closes: List[float], period: int = 20, multiplier: float = 2
) -> Dict[str, List[Optional[float]]]:
    """
    计算布林带 (BOLL)

    Args:
        closes: 收盘价列表
        period: 周期 (默认20)
        multiplier: 标准差倍数 (默认2)

    Returns:
        包含upper, middle, lower的字典
    """
    upper = []
    middle = []
    lower = []

    for i in range(len(closes)):
        if i < period - 1:
            upper.append(None)
            middle.append(None)
            lower.append(None)
        else:
            # 计算中轨 (MA)
            ma = sum(closes[i - period + 1 : i + 1]) / period

            # 计算标准差
            variance = (
                sum((closes[j] - ma) ** 2 for j in range(i - period + 1, i + 1))
                / period
            )
            std = variance**0.5

            middle.append(round(ma, 3))
            upper.append(round(ma + multiplier * std, 3))
            lower.append(round(ma - multiplier * std, 3))

    return {"upper": upper, "middle": middle, "lower": lower}


# ==================== 新增指标计算 ====================


def calculate_mtm(closes: List[float], period: int = 12) -> List[Optional[float]]:
    """
    计算MTM动量指标
    MTM = 当日收盘价 - N日前收盘价

    Args:
        closes: 收盘价列表
        period: 周期 (默认12)

    Returns:
        MTM值列表
    """
    result = []

    for i in range(len(closes)):
        if i < period:
            result.append(None)
        else:
            mtm = closes[i] - closes[i - period]
            result.append(round(mtm, 3))

    return result


def calculate_mtm_ma(
    closes: List[float], mtm_period: int = 12, ma_period: int = 6
) -> Dict[str, List[Optional[float]]]:
    """
    计算MTM及其均线

    Args:
        closes: 收盘价列表
        mtm_period: MTM周期 (默认12)
        ma_period: MTM均线周期 (默认6)

    Returns:
        包含MTM和MTM_MA的字典
    """
    mtm = calculate_mtm(closes, mtm_period)

    # 计算MTM的移动平均
    mtm_ma = []
    for i in range(len(mtm)):
        if mtm[i] is None or i < mtm_period + ma_period - 1:
            mtm_ma.append(None)
        else:
            valid_mtm = [v for v in mtm[i - ma_period + 1 : i + 1] if v is not None]
            if len(valid_mtm) == ma_period:
                mtm_ma.append(round(sum(valid_mtm) / ma_period, 3))
            else:
                mtm_ma.append(None)

    return {"MTM": mtm, "MTM_MA": mtm_ma}


def calculate_lwr(
    highs: List[float], lows: List[float], closes: List[float], period: int = 14
) -> Dict[str, List[Optional[float]]]:
    """
    计算LWR威廉指标变体 (Larry Williams %R)
    LWR = (N日内最高价 - 当日收盘价) / (N日内最高价 - N日内最低价) * 100
    LWR2 = LWR的3日移动平均

    注意: LWR2 < 30 = 超买; LWR2 > 70 = 超卖 (与RSI相反)

    Args:
        highs: 最高价列表
        lows: 最低价列表
        closes: 收盘价列表
        period: 周期 (默认14)

    Returns:
        包含LWR1和LWR2的字典
    """
    lwr1 = []

    for i in range(len(closes)):
        if i < period - 1:
            lwr1.append(None)
        else:
            high_n = max(highs[i - period + 1 : i + 1])
            low_n = min(lows[i - period + 1 : i + 1])

            if high_n == low_n:
                lwr1.append(50)
            else:
                lwr = (high_n - closes[i]) / (high_n - low_n) * 100
                lwr1.append(round(lwr, 2))

    # 计算LWR2 (LWR1的3日移动平均)
    lwr2 = []
    for i in range(len(lwr1)):
        if lwr1[i] is None or i < period + 1:
            lwr2.append(None)
        else:
            valid_lwr = [v for v in lwr1[i - 2 : i + 1] if v is not None]
            if len(valid_lwr) == 3:
                lwr2.append(round(sum(valid_lwr) / 3, 2))
            else:
                lwr2.append(None)

    return {"LWR1": lwr1, "LWR2": lwr2}


def calculate_obv(closes: List[float], volumes: List[float]) -> List[float]:
    """
    计算OBV能量潮指标
    OBV = 前一日OBV + (今日收盘价 > 昨日收盘价 ? 今日成交量 : -今日成交量)

    Args:
        closes: 收盘价列表
        volumes: 成交量列表

    Returns:
        OBV值列表
    """
    result = [volumes[0]]  # 第一天OBV等于成交量

    for i in range(1, len(closes)):
        if closes[i] > closes[i - 1]:
            obv = result[i - 1] + volumes[i]
        elif closes[i] < closes[i - 1]:
            obv = result[i - 1] - volumes[i]
        else:
            obv = result[i - 1]
        result.append(round(obv, 0))

    return result


def calculate_bbi(closes: List[float]) -> List[Optional[float]]:
    """
    计算BBI多空均线指标
    BBI = (MA3 + MA6 + MA12 + MA24) / 4

    Args:
        closes: 收盘价列表

    Returns:
        BBI值列表
    """
    ma3 = calculate_ma(closes, 3)
    ma6 = calculate_ma(closes, 6)
    ma12 = calculate_ma(closes, 12)
    ma24 = calculate_ma(closes, 24)

    result = []
    for i in range(len(closes)):
        if ma24[i] is None or ma12[i] is None or ma6[i] is None or ma3[i] is None:
            result.append(None)
        else:
            bbi = (float(ma3[i]) + float(ma6[i]) + float(ma12[i]) + float(ma24[i])) / 4
            result.append(round(bbi, 3))

    return result


# ==================== 综合指标计算 ====================


def calculate_six_pulse_indicator(
    closes: List[float], highs: List[float], lows: List[float], volumes: List[float]
) -> Dict[str, any]:
    """
    计算六脉神剑综合指标
    融合 MACD、KDJ、RSI、LWR、BBI、MTM 六个指标

    Args:
        closes: 收盘价列表
        highs: 最高价列表
        lows: 最低价列表
        volumes: 成交量列表

    Returns:
        包含所有指标及综合信号的字典
    """
    macd = calculate_macd(closes)
    kdj = calculate_kdj(highs, lows, closes)
    rsi = calculate_rsi(closes)
    lwr = calculate_lwr(highs, lows, closes)
    bbi = calculate_bbi(closes)
    mtm = calculate_mtm_ma(closes)

    # 计算综合信号
    signals = []
    for i in range(len(closes)):
        bullish_count = 0
        bearish_count = 0

        # MACD信号
        if macd["MACD"][i] is not None:
            if macd["DIF"][i] > macd["DEA"][i]:
                bullish_count += 1
            else:
                bearish_count += 1

        # KDJ信号
        if kdj["K"][i] is not None:
            if kdj["K"][i] > kdj["D"][i]:
                bullish_count += 1
            else:
                bearish_count += 1

        # RSI信号
        if rsi[i] is not None:
            if rsi[i] > 50:
                bullish_count += 1
            else:
                bearish_count += 1

        # LWR信号 (注意: LWR < 30 超买, > 70 超卖)
        if lwr["LWR2"][i] is not None:
            if lwr["LWR2"][i] < 50:
                bullish_count += 1
            else:
                bearish_count += 1

        # BBI信号
        if bbi[i] is not None:
            if closes[i] > bbi[i]:
                bullish_count += 1
            else:
                bearish_count += 1

        # MTM信号
        if mtm["MTM"][i] is not None:
            if mtm["MTM"][i] > 0:
                bullish_count += 1
            else:
                bearish_count += 1

        signals.append(
            {
                "bullish": bullish_count,
                "bearish": bearish_count,
                "signal": "BUY"
                if bullish_count >= 4
                else ("SELL" if bearish_count >= 4 else "HOLD"),
            }
        )

    return {
        "MACD": macd,
        "KDJ": kdj,
        "RSI": rsi,
        "LWR": lwr,
        "BBI": bbi,
        "MTM": mtm,
        "signals": signals,
    }


def calculate_all_indicators(klines: List[Dict]) -> Dict[str, any]:
    """
    计算所有技术指标

    Args:
        klines: K线数据列表，每个元素包含 date, open, high, low, close, volume

    Returns:
        包含所有指标的字典
    """
    if not klines:
        return {}

    # 提取数据
    dates = [k.get("date") or k.get("time", "") for k in klines]
    opens = [float(k.get("open", 0)) for k in klines]
    highs = [float(k.get("high", 0)) for k in klines]
    lows = [float(k.get("low", 0)) for k in klines]
    closes = [float(k.get("close", 0)) for k in klines]
    volumes = [float(k.get("volume", 0)) for k in klines]

    return {
        "dates": dates,
        # 均线
        "MA5": calculate_ma(closes, 5),
        "MA10": calculate_ma(closes, 10),
        "MA20": calculate_ma(closes, 20),
        "MA60": calculate_ma(closes, 60),
        # MACD
        "MACD": calculate_macd(closes),
        # RSI
        "RSI": calculate_rsi(closes),
        # KDJ
        "KDJ": calculate_kdj(highs, lows, closes),
        # 布林带
        "BOLL": calculate_boll(closes),
        # MTM动量
        "MTM": calculate_mtm_ma(closes),
        # LWR威廉
        "LWR": calculate_lwr(highs, lows, closes),
        # OBV能量潮
        "OBV": calculate_obv(closes, volumes),
        # BBI多空均线
        "BBI": calculate_bbi(closes),
        # 六脉神剑综合指标
        "SIX_PULSE": calculate_six_pulse_indicator(closes, highs, lows, volumes),
    }
