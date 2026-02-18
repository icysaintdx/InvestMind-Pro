"""
K线形态识别模块
识别各种K线形态和图表形态，包括：
- 单K线形态：十字星、锤子线、吊线等
- 组合K线形态：双针探顶/探底、三阳不过阴等
- 图表形态：头肩顶/底等
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum


class PatternType(Enum):
    """形态类型"""

    BULLISH = "bullish"  # 看涨
    BEARISH = "bearish"  # 看跌
    NEUTRAL = "neutral"  # 中性
    REVERSAL = "reversal"  # 反转


@dataclass
class PatternResult:
    """形态识别结果"""

    name: str  # 形态名称
    name_en: str  # 英文名称
    type: PatternType  # 形态类型
    index: int  # 出现位置索引
    date: str  # 出现日期
    confidence: float  # 置信度 (0-1)
    description: str  # 描述
    price: float  # 关键价格
    importance: str  # 重要性: high/medium/low


# ==================== 单K线形态识别 ====================


def is_doji(
    open_price: float, high: float, low: float, close: float, threshold: float = 0.1
) -> bool:
    """
    判断是否为十字星
    特征：开盘价≈收盘价，实体极小

    Args:
        threshold: 实体占振幅的比例阈值
    """
    body = abs(close - open_price)
    range_hl = high - low

    if range_hl == 0:
        return False

    return (body / range_hl) < threshold


def is_hammer(
    open_price: float,
    high: float,
    low: float,
    close: float,
    body_ratio: float = 0.3,
    shadow_ratio: float = 2.0,
) -> bool:
    """
    判断是否为锤子线（低位出现看涨）
    特征：小实体 + 长下影线 + 几乎无上影线
    """
    body = abs(close - open_price)
    range_hl = high - low

    if range_hl == 0 or body == 0:
        return False

    upper_shadow = high - max(open_price, close)
    lower_shadow = min(open_price, close) - low

    # 实体小于振幅的30%
    # 下影线至少是实体的2倍
    # 上影线很小
    return (
        body / range_hl < body_ratio
        and lower_shadow >= body * shadow_ratio
        and upper_shadow < body * 0.5
    )


def is_hanging_man(
    open_price: float,
    high: float,
    low: float,
    close: float,
    body_ratio: float = 0.3,
    shadow_ratio: float = 2.0,
) -> bool:
    """
    判断是否为吊线（高位出现看跌）
    形态与锤子线相同，但出现在高位
    """
    return is_hammer(open_price, high, low, close, body_ratio, shadow_ratio)


def is_shooting_star(
    open_price: float,
    high: float,
    low: float,
    close: float,
    body_ratio: float = 0.3,
    shadow_ratio: float = 2.0,
) -> bool:
    """
    判断是否为射击之星（高位出现看跌）
    特征：小实体 + 长上影线 + 几乎无下影线
    """
    body = abs(close - open_price)
    range_hl = high - low

    if range_hl == 0 or body == 0:
        return False

    upper_shadow = high - max(open_price, close)
    lower_shadow = min(open_price, close) - low

    return (
        body / range_hl < body_ratio
        and upper_shadow >= body * shadow_ratio
        and lower_shadow < body * 0.5
    )


def is_inverted_hammer(
    open_price: float,
    high: float,
    low: float,
    close: float,
    body_ratio: float = 0.3,
    shadow_ratio: float = 2.0,
) -> bool:
    """
    判断是否为倒锤子线（低位出现看涨）
    形态与射击之星相同，但出现在低位
    """
    return is_shooting_star(open_price, high, low, close, body_ratio, shadow_ratio)


# ==================== 组合K线形态识别 ====================


def detect_double_needle_top(
    klines: List[Dict], index: int, tolerance: float = 0.02
) -> Optional[PatternResult]:
    """
    识别双针探顶形态
    特征：高位连续2根长上影线K线，最高价接近

    Args:
        klines: K线数据列表
        index: 当前索引
        tolerance: 最高价接近的容差比例
    """
    if index < 1:
        return None

    curr = klines[index]
    prev = klines[index - 1]

    curr_high = float(curr.get("high", 0))
    curr_close = float(curr.get("close", 0))
    curr_open = float(curr.get("open", 0))
    prev_high = float(prev.get("high", 0))
    prev_close = float(prev.get("close", 0))
    prev_open = float(prev.get("open", 0))

    # 计算上影线长度
    curr_upper_shadow = curr_high - max(curr_open, curr_close)
    prev_upper_shadow = prev_high - max(prev_open, prev_close)
    curr_body = abs(curr_close - curr_open)
    prev_body = abs(prev_close - prev_open)

    # 条件：两根K线都有长上影线，且最高价接近
    if (
        curr_upper_shadow > curr_body
        and prev_upper_shadow > prev_body
        and abs(curr_high - prev_high) / max(curr_high, prev_high) < tolerance
    ):
        return PatternResult(
            name="双针探顶",
            name_en="Double Needle Top",
            type=PatternType.BEARISH,
            index=index,
            date=curr.get("date") or curr.get("time", ""),
            confidence=0.75,
            description="高位连续2根长上影线，最高价接近，上涨见顶信号",
            price=max(curr_high, prev_high),
            importance="high",
        )

    return None


def detect_double_needle_bottom(
    klines: List[Dict], index: int, tolerance: float = 0.02
) -> Optional[PatternResult]:
    """
    识别双针探底形态
    特征：低位连续2根长下影线K线，最低价接近
    """
    if index < 1:
        return None

    curr = klines[index]
    prev = klines[index - 1]

    curr_low = float(curr.get("low", 0))
    curr_close = float(curr.get("close", 0))
    curr_open = float(curr.get("open", 0))
    prev_low = float(prev.get("low", 0))
    prev_close = float(prev.get("close", 0))
    prev_open = float(prev.get("open", 0))

    # 计算下影线长度
    curr_lower_shadow = min(curr_open, curr_close) - curr_low
    prev_lower_shadow = min(prev_open, prev_close) - prev_low
    curr_body = abs(curr_close - curr_open)
    prev_body = abs(prev_close - prev_open)

    if (
        curr_lower_shadow > curr_body
        and prev_lower_shadow > prev_body
        and abs(curr_low - prev_low) / max(curr_low, prev_low, 0.01) < tolerance
    ):
        return PatternResult(
            name="双针探底",
            name_en="Double Needle Bottom",
            type=PatternType.BULLISH,
            index=index,
            date=curr.get("date") or curr.get("time", ""),
            confidence=0.75,
            description="低位连续2根长下影线，最低价接近，下跌见底信号",
            price=min(curr_low, prev_low),
            importance="high",
        )

    return None


def detect_three_yang_not_over_yin(
    klines: List[Dict], index: int
) -> Optional[PatternResult]:
    """
    识别三阳不过阴形态
    特征：一根长阴线后，连续3根阳线未能突破阴线最高点
    """
    if index < 3:
        return None

    # 获取前4根K线
    k0 = klines[index - 3]  # 长阴线
    k1 = klines[index - 2]  # 第1根阳线
    k2 = klines[index - 1]  # 第2根阳线
    k3 = klines[index]  # 第3根阳线

    # 判断k0是否为长阴线
    k0_open = float(k0.get("open", 0))
    k0_close = float(k0.get("close", 0))
    k0_high = float(k0.get("high", 0))

    if k0_close >= k0_open:  # 不是阴线
        return None

    # 判断后3根是否都是阳线
    for k in [k1, k2, k3]:
        if float(k.get("close", 0)) <= float(k.get("open", 0)):
            return None

    # 判断3根阳线是否都未突破阴线最高点
    k1_high = float(k1.get("high", 0))
    k2_high = float(k2.get("high", 0))
    k3_high = float(k3.get("high", 0))

    if k1_high < k0_high and k2_high < k0_high and k3_high < k0_high:
        return PatternResult(
            name="三阳不过阴",
            name_en="Three Yang Not Over Yin",
            type=PatternType.BEARISH,
            index=index,
            date=k3.get("date") or k3.get("time", ""),
            confidence=0.8,
            description="长阴后3阳未破阴顶，空方主导，暴跌信号",
            price=k0_high,
            importance="high",
        )

    return None


def detect_three_yin_not_over_yang(
    klines: List[Dict], index: int
) -> Optional[PatternResult]:
    """
    识别三阴不过阳形态
    特征：一根长阳线后，连续3根阴线未能跌破阳线最低点
    """
    if index < 3:
        return None

    k0 = klines[index - 3]  # 长阳线
    k1 = klines[index - 2]  # 第1根阴线
    k2 = klines[index - 1]  # 第2根阴线
    k3 = klines[index]  # 第3根阴线

    k0_open = float(k0.get("open", 0))
    k0_close = float(k0.get("close", 0))
    k0_low = float(k0.get("low", 0))

    if k0_close <= k0_open:  # 不是阳线
        return None

    # 判断后3根是否都是阴线
    for k in [k1, k2, k3]:
        if float(k.get("close", 0)) >= float(k.get("open", 0)):
            return None

    k1_low = float(k1.get("low", 0))
    k2_low = float(k2.get("low", 0))
    k3_low = float(k3.get("low", 0))

    if k1_low > k0_low and k2_low > k0_low and k3_low > k0_low:
        return PatternResult(
            name="三阴不过阳",
            name_en="Three Yin Not Over Yang",
            type=PatternType.BULLISH,
            index=index,
            date=k3.get("date") or k3.get("time", ""),
            confidence=0.8,
            description="长阳后3阴未破阳底，多方主导，暴涨信号",
            price=k0_low,
            importance="high",
        )

    return None


def detect_rising_resistance(klines: List[Dict], index: int) -> Optional[PatternResult]:
    """
    识别上升受阻形态
    特征：阳线实体缩小 + 长上影线
    """
    if index < 2:
        return None

    curr = klines[index]
    prev = klines[index - 1]

    curr_open = float(curr.get("open", 0))
    curr_close = float(curr.get("close", 0))
    curr_high = float(curr.get("high", 0))
    prev_open = float(prev.get("open", 0))
    prev_close = float(prev.get("close", 0))

    # 当前是阳线
    if curr_close <= curr_open:
        return None

    curr_body = curr_close - curr_open
    prev_body = abs(prev_close - prev_open)
    curr_upper_shadow = curr_high - curr_close

    # 实体缩小且有长上影线
    if curr_body < prev_body * 0.7 and curr_upper_shadow > curr_body:
        return PatternResult(
            name="上升受阻",
            name_en="Rising Resistance",
            type=PatternType.BEARISH,
            index=index,
            date=curr.get("date") or curr.get("time", ""),
            confidence=0.6,
            description="阳线实体缩小+长上影，趋势动能衰减，可能回调",
            price=curr_high,
            importance="medium",
        )

    return None


def detect_falling_support(klines: List[Dict], index: int) -> Optional[PatternResult]:
    """
    识别下跌受阻形态
    特征：阴线实体缩小 + 长下影线
    """
    if index < 2:
        return None

    curr = klines[index]
    prev = klines[index - 1]

    curr_open = float(curr.get("open", 0))
    curr_close = float(curr.get("close", 0))
    curr_low = float(curr.get("low", 0))
    prev_open = float(prev.get("open", 0))
    prev_close = float(prev.get("close", 0))

    # 当前是阴线
    if curr_close >= curr_open:
        return None

    curr_body = curr_open - curr_close
    prev_body = abs(prev_close - prev_open)
    curr_lower_shadow = curr_close - curr_low

    if curr_body < prev_body * 0.7 and curr_lower_shadow > curr_body:
        return PatternResult(
            name="下跌受阻",
            name_en="Falling Support",
            type=PatternType.BULLISH,
            index=index,
            date=curr.get("date") or curr.get("time", ""),
            confidence=0.6,
            description="阴线实体缩小+长下影，趋势动能衰减，可能反弹",
            price=curr_low,
            importance="medium",
        )

    return None


# ==================== 图表形态识别 ====================


def detect_head_and_shoulders_top(
    klines: List[Dict], window: int = 20
) -> List[PatternResult]:
    """
    识别头肩顶形态
    特征：左肩-头-右肩，头部最高，颈线为关键支撑

    Args:
        klines: K线数据列表
        window: 检测窗口大小
    """
    results = []

    if len(klines) < window:
        return results

    for i in range(window, len(klines)):
        # 在窗口内寻找三个高点
        window_data = klines[i - window : i]
        highs = [float(k.get("high", 0)) for k in window_data]

        # 找到最高点（头部）
        head_idx = highs.index(max(highs))
        head_price = highs[head_idx]

        # 头部不能在边缘
        if head_idx < 3 or head_idx > window - 4:
            continue

        # 在头部左侧找左肩
        left_highs = highs[:head_idx]
        if not left_highs:
            continue
        left_shoulder_idx = left_highs.index(max(left_highs))
        left_shoulder_price = left_highs[left_shoulder_idx]

        # 在头部右侧找右肩
        right_highs = highs[head_idx + 1 :]
        if not right_highs:
            continue
        right_shoulder_idx = head_idx + 1 + right_highs.index(max(right_highs))
        right_shoulder_price = right_highs[right_highs.index(max(right_highs))]

        # 验证头肩顶条件
        # 1. 头部高于两肩
        # 2. 两肩高度接近
        if (
            head_price > left_shoulder_price
            and head_price > right_shoulder_price
            and abs(left_shoulder_price - right_shoulder_price) / head_price < 0.05
        ):
            # 计算颈线
            left_low = min(highs[left_shoulder_idx:head_idx])
            right_low = min(highs[head_idx : right_shoulder_idx + 1])
            neckline = (left_low + right_low) / 2

            results.append(
                PatternResult(
                    name="头肩顶",
                    name_en="Head and Shoulders Top",
                    type=PatternType.BEARISH,
                    index=i - 1,
                    date=klines[i - 1].get("date") or klines[i - 1].get("time", ""),
                    confidence=0.8,
                    description=f"头肩顶形态，颈线位置约{neckline:.2f}，跌破颈线确认反转",
                    price=neckline,
                    importance="high",
                )
            )

    return results


def detect_head_and_shoulders_bottom(
    klines: List[Dict], window: int = 20
) -> List[PatternResult]:
    """
    识别头肩底形态
    特征：左肩-头-右肩，头部最低，颈线为关键压力
    """
    results = []

    if len(klines) < window:
        return results

    for i in range(window, len(klines)):
        window_data = klines[i - window : i]
        lows = [float(k.get("low", 0)) for k in window_data]

        # 找到最低点（头部）
        head_idx = lows.index(min(lows))
        head_price = lows[head_idx]

        if head_idx < 3 or head_idx > window - 4:
            continue

        # 找左肩和右肩
        left_lows = lows[:head_idx]
        if not left_lows:
            continue
        left_shoulder_idx = left_lows.index(min(left_lows))
        left_shoulder_price = left_lows[left_shoulder_idx]

        right_lows = lows[head_idx + 1 :]
        if not right_lows:
            continue
        right_shoulder_idx = head_idx + 1 + right_lows.index(min(right_lows))
        right_shoulder_price = right_lows[right_lows.index(min(right_lows))]

        if (
            head_price < left_shoulder_price
            and head_price < right_shoulder_price
            and abs(left_shoulder_price - right_shoulder_price) / max(head_price, 0.01)
            < 0.05
        ):
            left_high = max(lows[left_shoulder_idx:head_idx])
            right_high = max(lows[head_idx : right_shoulder_idx + 1])
            neckline = (left_high + right_high) / 2

            results.append(
                PatternResult(
                    name="头肩底",
                    name_en="Head and Shoulders Bottom",
                    type=PatternType.BULLISH,
                    index=i - 1,
                    date=klines[i - 1].get("date") or klines[i - 1].get("time", ""),
                    confidence=0.8,
                    description=f"头肩底形态，颈线位置约{neckline:.2f}，突破颈线确认反转",
                    price=neckline,
                    importance="high",
                )
            )

    return results


# ==================== 单K线形态检测 ====================


def detect_doji(klines: List[Dict], index: int) -> Optional[PatternResult]:
    """检测十字星"""
    if index < 0 or index >= len(klines):
        return None

    k = klines[index]
    open_p = float(k.get("open", 0))
    high = float(k.get("high", 0))
    low = float(k.get("low", 0))
    close = float(k.get("close", 0))

    if is_doji(open_p, high, low, close):
        return PatternResult(
            name="十字星",
            name_en="Doji",
            type=PatternType.NEUTRAL,
            index=index,
            date=k.get("date") or k.get("time", ""),
            confidence=0.5,
            description="开盘价≈收盘价，多空分歧大，需结合位置判断",
            price=close,
            importance="low",
        )

    return None


def detect_hammer_or_hanging(
    klines: List[Dict], index: int, lookback: int = 10
) -> Optional[PatternResult]:
    """检测锤子线或吊线"""
    if index < lookback:
        return None

    k = klines[index]
    open_p = float(k.get("open", 0))
    high = float(k.get("high", 0))
    low = float(k.get("low", 0))
    close = float(k.get("close", 0))

    if not is_hammer(open_p, high, low, close):
        return None

    # 判断是高位还是低位
    recent_closes = [
        float(klines[i].get("close", 0)) for i in range(index - lookback, index)
    ]
    avg_close = sum(recent_closes) / len(recent_closes)

    if close > avg_close * 1.05:  # 高位
        return PatternResult(
            name="高位吊线",
            name_en="Hanging Man",
            type=PatternType.BEARISH,
            index=index,
            date=k.get("date") or k.get("time", ""),
            confidence=0.6,
            description="高位小实体+长下影，上涨底气不足",
            price=close,
            importance="medium",
        )
    elif close < avg_close * 0.95:  # 低位
        return PatternResult(
            name="低位锤线",
            name_en="Hammer",
            type=PatternType.BULLISH,
            index=index,
            date=k.get("date") or k.get("time", ""),
            confidence=0.6,
            description="低位小实体+长下影，下跌动能衰竭",
            price=close,
            importance="medium",
        )

    return None


# ==================== 综合形态识别 ====================


def detect_all_patterns(klines: List[Dict]) -> List[PatternResult]:
    """
    识别所有K线形态

    Args:
        klines: K线数据列表

    Returns:
        识别到的所有形态列表
    """
    results = []

    if not klines or len(klines) < 5:
        return results

    # 遍历每根K线检测形态
    for i in range(len(klines)):
        # 单K线形态
        doji = detect_doji(klines, i)
        if doji:
            results.append(doji)

        hammer = detect_hammer_or_hanging(klines, i)
        if hammer:
            results.append(hammer)

        # 组合K线形态
        double_top = detect_double_needle_top(klines, i)
        if double_top:
            results.append(double_top)

        double_bottom = detect_double_needle_bottom(klines, i)
        if double_bottom:
            results.append(double_bottom)

        three_yang = detect_three_yang_not_over_yin(klines, i)
        if three_yang:
            results.append(three_yang)

        three_yin = detect_three_yin_not_over_yang(klines, i)
        if three_yin:
            results.append(three_yin)

        rising_res = detect_rising_resistance(klines, i)
        if rising_res:
            results.append(rising_res)

        falling_sup = detect_falling_support(klines, i)
        if falling_sup:
            results.append(falling_sup)

    # 图表形态（需要更多数据）
    if len(klines) >= 20:
        hs_tops = detect_head_and_shoulders_top(klines)
        results.extend(hs_tops)

        hs_bottoms = detect_head_and_shoulders_bottom(klines)
        results.extend(hs_bottoms)

    # 按索引排序
    results.sort(key=lambda x: x.index)

    return results


def get_recent_patterns(klines: List[Dict], lookback: int = 5) -> List[PatternResult]:
    """
    获取最近N根K线的形态

    Args:
        klines: K线数据列表
        lookback: 回看K线数量

    Returns:
        最近的形态列表
    """
    all_patterns = detect_all_patterns(klines)

    if not all_patterns:
        return []

    # 只返回最近lookback根K线内的形态
    min_index = len(klines) - lookback
    return [p for p in all_patterns if p.index >= min_index]
