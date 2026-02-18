"""
信号检测模块
检测各种交易信号，包括：
- 均线金叉/死叉
- MACD金叉/死叉
- KDJ金叉/死叉
- 量价背离
- 超买超卖信号
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class SignalType(Enum):
    """信号类型"""

    GOLDEN_CROSS = "golden_cross"  # 金叉
    DEATH_CROSS = "death_cross"  # 死叉
    OVERBOUGHT = "overbought"  # 超买
    OVERSOLD = "oversold"  # 超卖
    DIVERGENCE_BULL = "divergence_bull"  # 底背离（看涨）
    DIVERGENCE_BEAR = "divergence_bear"  # 顶背离（看跌）
    VOLUME_PRICE_UP = "volume_price_up"  # 量价齐升
    VOLUME_PRICE_DOWN = "volume_price_down"  # 量价齐跌
    VOLUME_DIVERGENCE = "volume_divergence"  # 量价背离


@dataclass
class SignalResult:
    """信号检测结果"""

    name: str  # 信号名称
    name_en: str  # 英文名称
    signal_type: SignalType  # 信号类型
    direction: str  # 方向: bullish/bearish
    index: int  # 出现位置索引
    date: str  # 出现日期
    confidence: float  # 置信度 (0-1)
    description: str  # 描述
    price: float  # 关键价格
    importance: str  # 重要性: high/medium/low
    indicator: str  # 相关指标


# ==================== 均线信号检测 ====================


def detect_ma_cross(
    ma_short: List[Optional[float]],
    ma_long: List[Optional[float]],
    dates: List[str],
    short_period: int = 5,
    long_period: int = 20,
) -> List[SignalResult]:
    """
    检测均线金叉/死叉

    Args:
        ma_short: 短期均线数据
        ma_long: 长期均线数据
        dates: 日期列表
        short_period: 短期均线周期
        long_period: 长期均线周期

    Returns:
        信号列表
    """
    results = []

    for i in range(1, len(ma_short)):
        if ma_short[i] is None or ma_long[i] is None:
            continue
        if ma_short[i - 1] is None or ma_long[i - 1] is None:
            continue

        prev_diff = ma_short[i - 1] - ma_long[i - 1]
        curr_diff = ma_short[i] - ma_long[i]

        # 金叉：短期均线从下向上穿越长期均线
        if prev_diff <= 0 and curr_diff > 0:
            results.append(
                SignalResult(
                    name=f"MA{short_period}/MA{long_period}金叉",
                    name_en=f"MA{short_period}/MA{long_period} Golden Cross",
                    signal_type=SignalType.GOLDEN_CROSS,
                    direction="bullish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.75,
                    description=f"MA{short_period}上穿MA{long_period}，明确上涨信号",
                    price=ma_short[i],
                    importance="high",
                    indicator="MA",
                )
            )

        # 死叉：短期均线从上向下穿越长期均线
        elif prev_diff >= 0 and curr_diff < 0:
            results.append(
                SignalResult(
                    name=f"MA{short_period}/MA{long_period}死叉",
                    name_en=f"MA{short_period}/MA{long_period} Death Cross",
                    signal_type=SignalType.DEATH_CROSS,
                    direction="bearish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.75,
                    description=f"MA{short_period}下穿MA{long_period}，明确下跌信号",
                    price=ma_short[i],
                    importance="high",
                    indicator="MA",
                )
            )

    return results


# ==================== MACD信号检测 ====================


def detect_macd_cross(
    dif: List[Optional[float]],
    dea: List[Optional[float]],
    macd: List[Optional[float]],
    dates: List[str],
) -> List[SignalResult]:
    """
    检测MACD金叉/死叉

    Args:
        dif: DIF线数据
        dea: DEA线数据
        macd: MACD柱数据
        dates: 日期列表

    Returns:
        信号列表
    """
    results = []

    for i in range(1, len(dif)):
        if dif[i] is None or dea[i] is None:
            continue
        if dif[i - 1] is None or dea[i - 1] is None:
            continue

        prev_diff = dif[i - 1] - dea[i - 1]
        curr_diff = dif[i] - dea[i]

        # MACD金叉
        if prev_diff <= 0 and curr_diff > 0:
            # 判断是否在零轴上方（更强信号）
            above_zero = dif[i] > 0 and dea[i] > 0
            confidence = 0.85 if above_zero else 0.7

            results.append(
                SignalResult(
                    name="MACD金叉",
                    name_en="MACD Golden Cross",
                    signal_type=SignalType.GOLDEN_CROSS,
                    direction="bullish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=confidence,
                    description="DIF上穿DEA，中期上涨信号"
                    + ("（零轴上方，信号更强）" if above_zero else ""),
                    price=dif[i],
                    importance="high",
                    indicator="MACD",
                )
            )

        # MACD死叉
        elif prev_diff >= 0 and curr_diff < 0:
            below_zero = dif[i] < 0 and dea[i] < 0
            confidence = 0.85 if below_zero else 0.7

            results.append(
                SignalResult(
                    name="MACD死叉",
                    name_en="MACD Death Cross",
                    signal_type=SignalType.DEATH_CROSS,
                    direction="bearish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=confidence,
                    description="DIF下穿DEA，中期下跌信号"
                    + ("（零轴下方，信号更强）" if below_zero else ""),
                    price=dif[i],
                    importance="high",
                    indicator="MACD",
                )
            )

    return results


# ==================== KDJ信号检测 ====================


def detect_kdj_cross(
    k: List[Optional[float]],
    d: List[Optional[float]],
    j: List[Optional[float]],
    dates: List[str],
) -> List[SignalResult]:
    """
    检测KDJ金叉/死叉及超买超卖

    Args:
        k: K线数据
        d: D线数据
        j: J线数据
        dates: 日期列表

    Returns:
        信号列表
    """
    results = []

    for i in range(1, len(k)):
        if k[i] is None or d[i] is None:
            continue
        if k[i - 1] is None or d[i - 1] is None:
            continue

        prev_diff = k[i - 1] - d[i - 1]
        curr_diff = k[i] - d[i]

        # KDJ金叉
        if prev_diff <= 0 and curr_diff > 0:
            # 低位金叉更有效
            is_low = k[i] < 30
            confidence = 0.75 if is_low else 0.55

            results.append(
                SignalResult(
                    name="KDJ金叉",
                    name_en="KDJ Golden Cross",
                    signal_type=SignalType.GOLDEN_CROSS,
                    direction="bullish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=confidence,
                    description="K线上穿D线"
                    + ("，低位金叉信号较强" if is_low else "，注意可能骗线"),
                    price=k[i],
                    importance="low" if not is_low else "medium",
                    indicator="KDJ",
                )
            )

        # KDJ死叉
        elif prev_diff >= 0 and curr_diff < 0:
            is_high = k[i] > 70
            confidence = 0.75 if is_high else 0.55

            results.append(
                SignalResult(
                    name="KDJ死叉",
                    name_en="KDJ Death Cross",
                    signal_type=SignalType.DEATH_CROSS,
                    direction="bearish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=confidence,
                    description="K线下穿D线"
                    + ("，高位死叉信号较强" if is_high else "，注意可能骗线"),
                    price=k[i],
                    importance="low" if not is_high else "medium",
                    indicator="KDJ",
                )
            )

        # J值超买超卖
        if j[i] is not None:
            if j[i] > 100:
                results.append(
                    SignalResult(
                        name="KDJ超买",
                        name_en="KDJ Overbought",
                        signal_type=SignalType.OVERBOUGHT,
                        direction="bearish",
                        index=i,
                        date=dates[i] if i < len(dates) else "",
                        confidence=0.6,
                        description=f"J值={j[i]:.1f}>100，短期超买",
                        price=j[i],
                        importance="low",
                        indicator="KDJ",
                    )
                )
            elif j[i] < 0:
                results.append(
                    SignalResult(
                        name="KDJ超卖",
                        name_en="KDJ Oversold",
                        signal_type=SignalType.OVERSOLD,
                        direction="bullish",
                        index=i,
                        date=dates[i] if i < len(dates) else "",
                        confidence=0.6,
                        description=f"J值={j[i]:.1f}<0，短期超卖",
                        price=j[i],
                        importance="low",
                        indicator="KDJ",
                    )
                )

    return results


# ==================== RSI信号检测 ====================


def detect_rsi_signals(
    rsi: List[Optional[float]], dates: List[str]
) -> List[SignalResult]:
    """
    检测RSI超买超卖信号

    Args:
        rsi: RSI数据
        dates: 日期列表

    Returns:
        信号列表
    """
    results = []

    for i in range(len(rsi)):
        if rsi[i] is None:
            continue

        if rsi[i] > 70:
            results.append(
                SignalResult(
                    name="RSI超买",
                    name_en="RSI Overbought",
                    signal_type=SignalType.OVERBOUGHT,
                    direction="bearish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.6,
                    description=f"RSI={rsi[i]:.1f}>70，价格过涨，但可能钝化",
                    price=rsi[i],
                    importance="medium",
                    indicator="RSI",
                )
            )
        elif rsi[i] < 30:
            results.append(
                SignalResult(
                    name="RSI超卖",
                    name_en="RSI Oversold",
                    signal_type=SignalType.OVERSOLD,
                    direction="bullish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.6,
                    description=f"RSI={rsi[i]:.1f}<30，价格过跌，但可能钝化",
                    price=rsi[i],
                    importance="medium",
                    indicator="RSI",
                )
            )

    return results


# ==================== LWR信号检测 ====================


def detect_lwr_signals(
    lwr2: List[Optional[float]], dates: List[str]
) -> List[SignalResult]:
    """
    检测LWR威廉指标信号
    注意：LWR2 < 30 = 超买; LWR2 > 70 = 超卖（与RSI相反）

    Args:
        lwr2: LWR2数据
        dates: 日期列表

    Returns:
        信号列表
    """
    results = []

    for i in range(len(lwr2)):
        if lwr2[i] is None:
            continue

        if lwr2[i] < 30:
            results.append(
                SignalResult(
                    name="LWR超买",
                    name_en="LWR Overbought",
                    signal_type=SignalType.OVERBOUGHT,
                    direction="bearish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.55,
                    description=f"LWR2={lwr2[i]:.1f}<30，超买区域，信号灵敏但准确性低",
                    price=lwr2[i],
                    importance="low",
                    indicator="LWR",
                )
            )
        elif lwr2[i] > 70:
            results.append(
                SignalResult(
                    name="LWR超卖",
                    name_en="LWR Oversold",
                    signal_type=SignalType.OVERSOLD,
                    direction="bullish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.55,
                    description=f"LWR2={lwr2[i]:.1f}>70，超卖区域，信号灵敏但准确性低",
                    price=lwr2[i],
                    importance="low",
                    indicator="LWR",
                )
            )

    return results


# ==================== 量价信号检测 ====================


def detect_volume_price_signals(
    closes: List[float], volumes: List[float], dates: List[str], lookback: int = 5
) -> List[SignalResult]:
    """
    检测量价关系信号

    Args:
        closes: 收盘价列表
        volumes: 成交量列表
        dates: 日期列表
        lookback: 回看周期

    Returns:
        信号列表
    """
    results = []

    for i in range(lookback, len(closes)):
        # 计算价格变化
        price_change = (closes[i] - closes[i - lookback]) / closes[i - lookback]

        # 计算成交量变化
        avg_volume_prev = sum(volumes[i - lookback : i]) / lookback
        volume_change = (volumes[i] - avg_volume_prev) / max(avg_volume_prev, 1)

        # 量价齐升
        if price_change > 0.02 and volume_change > 0.3:
            results.append(
                SignalResult(
                    name="量价齐升",
                    name_en="Volume Price Up",
                    signal_type=SignalType.VOLUME_PRICE_UP,
                    direction="bullish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.7,
                    description=f"价格上涨{price_change * 100:.1f}%，成交量放大{volume_change * 100:.0f}%，趋势延续",
                    price=closes[i],
                    importance="medium",
                    indicator="VOLUME",
                )
            )

        # 量价齐跌
        elif price_change < -0.02 and volume_change > 0.3:
            results.append(
                SignalResult(
                    name="量价齐跌",
                    name_en="Volume Price Down",
                    signal_type=SignalType.VOLUME_PRICE_DOWN,
                    direction="bearish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.7,
                    description=f"价格下跌{abs(price_change) * 100:.1f}%，成交量放大{volume_change * 100:.0f}%，趋势延续",
                    price=closes[i],
                    importance="medium",
                    indicator="VOLUME",
                )
            )

        # 量价背离（价涨量缩）
        elif price_change > 0.02 and volume_change < -0.2:
            results.append(
                SignalResult(
                    name="量价背离(价涨量缩)",
                    name_en="Volume Price Divergence (Up)",
                    signal_type=SignalType.VOLUME_DIVERGENCE,
                    direction="bearish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.65,
                    description=f"价格上涨{price_change * 100:.1f}%但成交量萎缩{abs(volume_change) * 100:.0f}%，可能反转",
                    price=closes[i],
                    importance="medium",
                    indicator="VOLUME",
                )
            )

        # 量价背离（价跌量缩）
        elif price_change < -0.02 and volume_change < -0.2:
            results.append(
                SignalResult(
                    name="量价背离(价跌量缩)",
                    name_en="Volume Price Divergence (Down)",
                    signal_type=SignalType.VOLUME_DIVERGENCE,
                    direction="bullish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.65,
                    description=f"价格下跌{abs(price_change) * 100:.1f}%但成交量萎缩{abs(volume_change) * 100:.0f}%，可能反转",
                    price=closes[i],
                    importance="medium",
                    indicator="VOLUME",
                )
            )

    return results


# ==================== MTM信号检测 ====================


def detect_mtm_signals(
    mtm: List[Optional[float]], mtm_ma: List[Optional[float]], dates: List[str]
) -> List[SignalResult]:
    """
    检测MTM动量指标信号

    Args:
        mtm: MTM数据
        mtm_ma: MTM均线数据
        dates: 日期列表

    Returns:
        信号列表
    """
    results = []

    for i in range(1, len(mtm)):
        if mtm[i] is None or mtm_ma[i] is None:
            continue
        if mtm[i - 1] is None or mtm_ma[i - 1] is None:
            continue

        prev_diff = mtm[i - 1] - mtm_ma[i - 1]
        curr_diff = mtm[i] - mtm_ma[i]

        # MTM上穿均线
        if prev_diff <= 0 and curr_diff > 0:
            results.append(
                SignalResult(
                    name="MTM突破均线",
                    name_en="MTM Cross Above MA",
                    signal_type=SignalType.GOLDEN_CROSS,
                    direction="bullish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.6,
                    description="MTM上穿均线，趋势加速",
                    price=mtm[i],
                    importance="medium",
                    indicator="MTM",
                )
            )

        # MTM下穿均线
        elif prev_diff >= 0 and curr_diff < 0:
            results.append(
                SignalResult(
                    name="MTM跌破均线",
                    name_en="MTM Cross Below MA",
                    signal_type=SignalType.DEATH_CROSS,
                    direction="bearish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.6,
                    description="MTM下穿均线，趋势减速",
                    price=mtm[i],
                    importance="medium",
                    indicator="MTM",
                )
            )

    return results


# ==================== BBI信号检测 ====================


def detect_bbi_signals(
    closes: List[float], bbi: List[Optional[float]], dates: List[str]
) -> List[SignalResult]:
    """
    检测BBI多空均线信号

    Args:
        closes: 收盘价列表
        bbi: BBI数据
        dates: 日期列表

    Returns:
        信号列表
    """
    results = []

    for i in range(1, len(closes)):
        if bbi[i] is None or bbi[i - 1] is None:
            continue

        prev_diff = closes[i - 1] - bbi[i - 1]
        curr_diff = closes[i] - bbi[i]

        # 价格上穿BBI
        if prev_diff <= 0 and curr_diff > 0:
            results.append(
                SignalResult(
                    name="价格上穿BBI",
                    name_en="Price Cross Above BBI",
                    signal_type=SignalType.GOLDEN_CROSS,
                    direction="bullish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.65,
                    description="价格上穿BBI多空均线，多头趋势",
                    price=closes[i],
                    importance="medium",
                    indicator="BBI",
                )
            )

        # 价格下穿BBI
        elif prev_diff >= 0 and curr_diff < 0:
            results.append(
                SignalResult(
                    name="价格下穿BBI",
                    name_en="Price Cross Below BBI",
                    signal_type=SignalType.DEATH_CROSS,
                    direction="bearish",
                    index=i,
                    date=dates[i] if i < len(dates) else "",
                    confidence=0.65,
                    description="价格下穿BBI多空均线，空头趋势",
                    price=closes[i],
                    importance="medium",
                    indicator="BBI",
                )
            )

    return results


# ==================== 综合信号检测 ====================


def detect_all_signals(klines: List[Dict], indicators: Dict) -> List[SignalResult]:
    """
    检测所有交易信号

    Args:
        klines: K线数据列表
        indicators: 指标数据字典（来自calculate_all_indicators）

    Returns:
        所有信号列表
    """
    results = []

    if not klines or not indicators:
        return results

    dates = indicators.get("dates", [])
    closes = [float(k.get("close", 0)) for k in klines]
    volumes = [float(k.get("volume", 0)) for k in klines]

    # 均线金叉死叉
    ma5 = indicators.get("MA5", [])
    ma10 = indicators.get("MA10", [])
    ma20 = indicators.get("MA20", [])
    ma60 = indicators.get("MA60", [])

    if ma5 and ma10:
        results.extend(detect_ma_cross(ma5, ma10, dates, 5, 10))
    if ma5 and ma20:
        results.extend(detect_ma_cross(ma5, ma20, dates, 5, 20))
    if ma10 and ma60:
        results.extend(detect_ma_cross(ma10, ma60, dates, 10, 60))

    # MACD信号
    macd_data = indicators.get("MACD", {})
    if macd_data:
        results.extend(
            detect_macd_cross(
                macd_data.get("DIF", []),
                macd_data.get("DEA", []),
                macd_data.get("MACD", []),
                dates,
            )
        )

    # KDJ信号
    kdj_data = indicators.get("KDJ", {})
    if kdj_data:
        results.extend(
            detect_kdj_cross(
                kdj_data.get("K", []),
                kdj_data.get("D", []),
                kdj_data.get("J", []),
                dates,
            )
        )

    # RSI信号
    rsi = indicators.get("RSI", [])
    if rsi:
        results.extend(detect_rsi_signals(rsi, dates))

    # LWR信号
    lwr_data = indicators.get("LWR", {})
    if lwr_data:
        results.extend(detect_lwr_signals(lwr_data.get("LWR2", []), dates))

    # MTM信号
    mtm_data = indicators.get("MTM", {})
    if mtm_data:
        results.extend(
            detect_mtm_signals(
                mtm_data.get("MTM", []), mtm_data.get("MTM_MA", []), dates
            )
        )

    # BBI信号
    bbi = indicators.get("BBI", [])
    if bbi:
        results.extend(detect_bbi_signals(closes, bbi, dates))

    # 量价信号
    if closes and volumes:
        results.extend(detect_volume_price_signals(closes, volumes, dates))

    # 按索引排序
    results.sort(key=lambda x: x.index)

    return results


def get_recent_signals(
    klines: List[Dict], indicators: Dict, lookback: int = 5
) -> List[SignalResult]:
    """
    获取最近N根K线的信号

    Args:
        klines: K线数据列表
        indicators: 指标数据字典
        lookback: 回看K线数量

    Returns:
        最近的信号列表
    """
    all_signals = detect_all_signals(klines, indicators)

    if not all_signals:
        return []

    min_index = len(klines) - lookback
    return [s for s in all_signals if s.index >= min_index]


def get_signal_summary(signals: List[SignalResult]) -> Dict:
    """
    获取信号汇总

    Args:
        signals: 信号列表

    Returns:
        信号汇总字典
    """
    bullish_count = sum(1 for s in signals if s.direction == "bullish")
    bearish_count = sum(1 for s in signals if s.direction == "bearish")

    high_importance = [s for s in signals if s.importance == "high"]

    return {
        "total": len(signals),
        "bullish": bullish_count,
        "bearish": bearish_count,
        "high_importance_signals": [
            {
                "name": s.name,
                "direction": s.direction,
                "date": s.date,
                "description": s.description,
            }
            for s in high_importance
        ],
        "recommendation": "BUY"
        if bullish_count > bearish_count + 2
        else ("SELL" if bearish_count > bullish_count + 2 else "HOLD"),
        "confidence": max(s.confidence for s in signals) if signals else 0,
    }
