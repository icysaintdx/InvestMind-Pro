"""
技术指标分析API
提供技术指标计算、K线形态识别、交易信号检测等功能
"""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
from pydantic import BaseModel, ConfigDict
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.utils.logging_config import get_logger
from backend.utils.technical_indicators import (
    calculate_all_indicators,
    calculate_ma,
    calculate_macd,
    calculate_rsi,
    calculate_kdj,
    calculate_boll,
    calculate_mtm_ma,
    calculate_lwr,
    calculate_obv,
    calculate_bbi,
    calculate_six_pulse_indicator,
)
from backend.utils.pattern_recognition import (
    detect_all_patterns,
    get_recent_patterns,
    PatternResult,
)
from backend.utils.signal_detection import (
    detect_all_signals,
    get_recent_signals,
    get_signal_summary,
    SignalResult,
)

logger = get_logger("api.indicators")
router = APIRouter(prefix="/api/indicators", tags=["Technical Indicators"])


# ==================== 请求/响应模型 ====================


class KlineItem(BaseModel):
    """K线数据项"""

    model_config = ConfigDict(protected_namespaces=())

    date: Optional[str] = None
    time: Optional[str] = None
    open: float
    high: float
    low: float
    close: float
    volume: float
    amount: Optional[float] = 0


class IndicatorRequest(BaseModel):
    """指标计算请求"""

    model_config = ConfigDict(protected_namespaces=())

    klines: List[KlineItem]
    indicators: Optional[List[str]] = None  # 指定要计算的指标，None表示全部


class PatternRequest(BaseModel):
    """形态识别请求"""

    model_config = ConfigDict(protected_namespaces=())

    klines: List[KlineItem]
    lookback: Optional[int] = 5  # 回看K线数量


class SignalRequest(BaseModel):
    """信号检测请求"""

    model_config = ConfigDict(protected_namespaces=())

    klines: List[KlineItem]
    lookback: Optional[int] = 10  # 回看K线数量


class AnalysisRequest(BaseModel):
    """综合分析请求"""

    model_config = ConfigDict(protected_namespaces=())

    klines: List[KlineItem]
    include_indicators: Optional[bool] = True
    include_patterns: Optional[bool] = True
    include_signals: Optional[bool] = True
    lookback: Optional[int] = 10


# ==================== API端点 ====================


@router.post("/calculate")
async def calculate_indicators(request: IndicatorRequest):
    """
    计算技术指标

    支持的指标:
    - MA5, MA10, MA20, MA60: 移动平均线
    - MACD: DIF, DEA, MACD柱
    - RSI: 相对强弱指标
    - KDJ: K, D, J随机指标
    - BOLL: 布林带上轨、中轨、下轨
    - MTM: 动量指标及其均线
    - LWR: 威廉指标变体
    - OBV: 能量潮
    - BBI: 多空均线
    - SIX_PULSE: 六脉神剑综合指标
    """
    try:
        if not request.klines:
            raise HTTPException(status_code=400, detail="K线数据不能为空")

        # 转换为字典列表
        klines = [k.model_dump() for k in request.klines]

        # 计算所有指标
        indicators = calculate_all_indicators(klines)

        # 如果指定了特定指标，只返回这些指标
        if request.indicators:
            filtered = {"dates": indicators.get("dates", [])}
            for ind in request.indicators:
                if ind.upper() in indicators:
                    filtered[ind.upper()] = indicators[ind.upper()]
            indicators = filtered

        logger.info(f"计算技术指标成功，K线数量: {len(klines)}")

        return {"success": True, "count": len(klines), "indicators": indicators}

    except Exception as e:
        logger.error(f"计算技术指标失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"计算失败: {str(e)}")


@router.post("/patterns")
async def detect_patterns(request: PatternRequest):
    """
    识别K线形态

    支持的形态:
    - 高关键度: 双针探顶/探底、三阳不过阴/三阴不过阳、头肩顶/底
    - 中关键度: 上升受阻、下跌受阻、高位吊线、低位锤线
    - 低关键度: 十字星
    """
    try:
        if not request.klines:
            raise HTTPException(status_code=400, detail="K线数据不能为空")

        klines = [k.model_dump() for k in request.klines]

        # 识别形态
        if request.lookback and request.lookback > 0:
            patterns = get_recent_patterns(klines, request.lookback)
        else:
            patterns = detect_all_patterns(klines)

        # 转换为可序列化格式
        pattern_list = []
        for p in patterns:
            pattern_list.append(
                {
                    "name": p.name,
                    "name_en": p.name_en,
                    "type": p.type.value,
                    "index": p.index,
                    "date": p.date,
                    "confidence": p.confidence,
                    "description": p.description,
                    "price": p.price,
                    "importance": p.importance,
                }
            )

        # 按重要性分组
        high_importance = [p for p in pattern_list if p["importance"] == "high"]
        medium_importance = [p for p in pattern_list if p["importance"] == "medium"]
        low_importance = [p for p in pattern_list if p["importance"] == "low"]

        logger.info(f"识别K线形态成功，发现 {len(patterns)} 个形态")

        return {
            "success": True,
            "count": len(patterns),
            "patterns": pattern_list,
            "summary": {
                "high": len(high_importance),
                "medium": len(medium_importance),
                "low": len(low_importance),
                "high_patterns": high_importance,
            },
        }

    except Exception as e:
        logger.error(f"识别K线形态失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"识别失败: {str(e)}")


@router.post("/signals")
async def detect_trading_signals(request: SignalRequest):
    """
    检测交易信号

    支持的信号:
    - 均线金叉/死叉 (MA5/MA10, MA5/MA20, MA10/MA60)
    - MACD金叉/死叉
    - KDJ金叉/死叉、超买超卖
    - RSI超买超卖
    - LWR超买超卖
    - MTM突破/跌破均线
    - BBI价格穿越
    - 量价关系 (量价齐升/齐跌/背离)
    """
    try:
        if not request.klines:
            raise HTTPException(status_code=400, detail="K线数据不能为空")

        klines = [k.model_dump() for k in request.klines]

        # 先计算指标
        indicators = calculate_all_indicators(klines)

        # 检测信号
        if request.lookback and request.lookback > 0:
            signals = get_recent_signals(klines, indicators, request.lookback)
        else:
            signals = detect_all_signals(klines, indicators)

        # 转换为可序列化格式
        signal_list = []
        for s in signals:
            signal_list.append(
                {
                    "name": s.name,
                    "name_en": s.name_en,
                    "signal_type": s.signal_type.value,
                    "direction": s.direction,
                    "index": s.index,
                    "date": s.date,
                    "confidence": s.confidence,
                    "description": s.description,
                    "price": s.price,
                    "importance": s.importance,
                    "indicator": s.indicator,
                }
            )

        # 获取信号汇总
        summary = get_signal_summary(signals)

        logger.info(f"检测交易信号成功，发现 {len(signals)} 个信号")

        return {
            "success": True,
            "count": len(signals),
            "signals": signal_list,
            "summary": summary,
        }

    except Exception as e:
        logger.error(f"检测交易信号失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


@router.post("/analyze")
async def comprehensive_analysis(request: AnalysisRequest):
    """
    综合技术分析

    一次性返回:
    - 所有技术指标
    - K线形态识别结果
    - 交易信号检测结果
    - 六脉神剑综合评分
    - 操作建议
    """
    try:
        if not request.klines:
            raise HTTPException(status_code=400, detail="K线数据不能为空")

        klines = [k.model_dump() for k in request.klines]
        result = {"success": True, "count": len(klines)}

        # 计算指标
        indicators = None
        if request.include_indicators:
            indicators = calculate_all_indicators(klines)
            result["indicators"] = indicators

        # 识别形态
        if request.include_patterns:
            patterns = get_recent_patterns(klines, request.lookback or 10)
            pattern_list = []
            for p in patterns:
                pattern_list.append(
                    {
                        "name": p.name,
                        "name_en": p.name_en,
                        "type": p.type.value,
                        "index": p.index,
                        "date": p.date,
                        "confidence": p.confidence,
                        "description": p.description,
                        "price": p.price,
                        "importance": p.importance,
                    }
                )
            result["patterns"] = pattern_list

        # 检测信号
        if request.include_signals:
            if indicators is None:
                indicators = calculate_all_indicators(klines)

            signals = get_recent_signals(klines, indicators, request.lookback or 10)
            signal_list = []
            for s in signals:
                signal_list.append(
                    {
                        "name": s.name,
                        "name_en": s.name_en,
                        "signal_type": s.signal_type.value,
                        "direction": s.direction,
                        "index": s.index,
                        "date": s.date,
                        "confidence": s.confidence,
                        "description": s.description,
                        "price": s.price,
                        "importance": s.importance,
                        "indicator": s.indicator,
                    }
                )
            result["signals"] = signal_list
            result["signal_summary"] = get_signal_summary(signals)

        # 六脉神剑综合评分
        if indicators and "SIX_PULSE" in indicators:
            six_pulse = indicators["SIX_PULSE"]
            if six_pulse.get("signals") and len(six_pulse["signals"]) > 0:
                latest_signal = six_pulse["signals"][-1]
                result["six_pulse_score"] = {
                    "bullish": latest_signal["bullish"],
                    "bearish": latest_signal["bearish"],
                    "signal": latest_signal["signal"],
                    "description": f"六脉神剑: {latest_signal['bullish']}个看涨信号, {latest_signal['bearish']}个看跌信号",
                }

        # 生成操作建议
        recommendation = generate_recommendation(result)
        result["recommendation"] = recommendation

        logger.info(f"综合技术分析成功，K线数量: {len(klines)}")

        return result

    except Exception as e:
        logger.error(f"综合技术分析失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"分析失败: {str(e)}")


@router.get("/six-pulse")
async def get_six_pulse_indicator(
    symbol: str = Query(..., description="股票代码"),
    period: str = Query("daily", description="周期"),
    limit: int = Query(100, description="K线数量"),
):
    """
    获取六脉神剑综合指标

    六脉神剑融合6个经典指标:
    - MACD: 趋势方向
    - KDJ: 超买超卖
    - RSI: 强弱程度
    - LWR: 相对位置
    - BBI: 多空趋势
    - MTM: 动量速度

    返回综合信号: BUY(4+看涨) / SELL(4+看跌) / HOLD(其他)
    """
    try:
        # 获取K线数据
        from backend.api.kline_api import get_kline_data

        kline_result = await get_kline_data(
            symbol=symbol, period=period, adjust="qfq", source="auto", limit=limit
        )

        if not kline_result.get("success") or not kline_result.get("data"):
            raise HTTPException(status_code=404, detail="获取K线数据失败")

        klines = kline_result["data"]

        # 提取数据
        closes = [float(k.get("close", 0)) for k in klines]
        highs = [float(k.get("high", 0)) for k in klines]
        lows = [float(k.get("low", 0)) for k in klines]
        volumes = [float(k.get("volume", 0)) for k in klines]
        dates = [k.get("time") or k.get("date", "") for k in klines]

        # 计算六脉神剑
        six_pulse = calculate_six_pulse_indicator(closes, highs, lows, volumes)

        # 获取最新信号
        latest_idx = len(closes) - 1
        latest_signal = (
            six_pulse["signals"][latest_idx] if six_pulse["signals"] else None
        )

        # 构建详细指标状态
        indicator_status = []
        if latest_idx >= 0:
            # MACD状态
            macd = six_pulse["MACD"]
            if (
                macd["DIF"][latest_idx] is not None
                and macd["DEA"][latest_idx] is not None
            ):
                macd_bullish = macd["DIF"][latest_idx] > macd["DEA"][latest_idx]
                indicator_status.append(
                    {
                        "name": "MACD",
                        "status": "bullish" if macd_bullish else "bearish",
                        "value": f"DIF={macd['DIF'][latest_idx]:.3f}, DEA={macd['DEA'][latest_idx]:.3f}",
                        "description": "DIF>DEA 多头"
                        if macd_bullish
                        else "DIF<DEA 空头",
                    }
                )

            # KDJ状态
            kdj = six_pulse["KDJ"]
            if kdj["K"][latest_idx] is not None and kdj["D"][latest_idx] is not None:
                kdj_bullish = kdj["K"][latest_idx] > kdj["D"][latest_idx]
                indicator_status.append(
                    {
                        "name": "KDJ",
                        "status": "bullish" if kdj_bullish else "bearish",
                        "value": f"K={kdj['K'][latest_idx]:.1f}, D={kdj['D'][latest_idx]:.1f}, J={kdj['J'][latest_idx]:.1f}",
                        "description": "K>D 多头" if kdj_bullish else "K<D 空头",
                    }
                )

            # RSI状态
            rsi = six_pulse["RSI"]
            if rsi[latest_idx] is not None:
                rsi_bullish = rsi[latest_idx] > 50
                indicator_status.append(
                    {
                        "name": "RSI",
                        "status": "bullish" if rsi_bullish else "bearish",
                        "value": f"{rsi[latest_idx]:.1f}",
                        "description": "RSI>50 偏强" if rsi_bullish else "RSI<50 偏弱",
                    }
                )

            # LWR状态
            lwr = six_pulse["LWR"]
            if lwr["LWR2"][latest_idx] is not None:
                lwr_bullish = lwr["LWR2"][latest_idx] < 50
                indicator_status.append(
                    {
                        "name": "LWR",
                        "status": "bullish" if lwr_bullish else "bearish",
                        "value": f"{lwr['LWR2'][latest_idx]:.1f}",
                        "description": "LWR<50 偏强" if lwr_bullish else "LWR>50 偏弱",
                    }
                )

            # BBI状态
            bbi = six_pulse["BBI"]
            if bbi[latest_idx] is not None:
                bbi_bullish = closes[latest_idx] > bbi[latest_idx]
                indicator_status.append(
                    {
                        "name": "BBI",
                        "status": "bullish" if bbi_bullish else "bearish",
                        "value": f"{bbi[latest_idx]:.2f}",
                        "description": "价格>BBI 多头"
                        if bbi_bullish
                        else "价格<BBI 空头",
                    }
                )

            # MTM状态
            mtm = six_pulse["MTM"]
            if mtm["MTM"][latest_idx] is not None:
                mtm_bullish = mtm["MTM"][latest_idx] > 0
                indicator_status.append(
                    {
                        "name": "MTM",
                        "status": "bullish" if mtm_bullish else "bearish",
                        "value": f"{mtm['MTM'][latest_idx]:.3f}",
                        "description": "MTM>0 动量向上"
                        if mtm_bullish
                        else "MTM<0 动量向下",
                    }
                )

        return {
            "success": True,
            "symbol": symbol,
            "period": period,
            "date": dates[-1] if dates else "",
            "price": closes[-1] if closes else 0,
            "signal": latest_signal["signal"] if latest_signal else "HOLD",
            "bullish_count": latest_signal["bullish"] if latest_signal else 0,
            "bearish_count": latest_signal["bearish"] if latest_signal else 0,
            "indicators": indicator_status,
            "description": f"六脉神剑综合评分: {latest_signal['bullish'] if latest_signal else 0}个看涨, {latest_signal['bearish'] if latest_signal else 0}个看跌",
            "recommendation": get_six_pulse_recommendation(latest_signal)
            if latest_signal
            else "数据不足，无法判断",
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取六脉神剑指标失败: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取失败: {str(e)}")


# ==================== 辅助函数 ====================


def generate_recommendation(analysis_result: dict) -> dict:
    """生成操作建议"""
    bullish_factors = []
    bearish_factors = []

    # 分析形态
    patterns = analysis_result.get("patterns", [])
    for p in patterns:
        if p["importance"] == "high":
            if p["type"] == "bullish":
                bullish_factors.append(f"形态: {p['name']}")
            elif p["type"] == "bearish":
                bearish_factors.append(f"形态: {p['name']}")

    # 分析信号
    signal_summary = analysis_result.get("signal_summary", {})
    if signal_summary.get("bullish", 0) > signal_summary.get("bearish", 0):
        bullish_factors.append(
            f"信号: {signal_summary['bullish']}个看涨 vs {signal_summary['bearish']}个看跌"
        )
    elif signal_summary.get("bearish", 0) > signal_summary.get("bullish", 0):
        bearish_factors.append(
            f"信号: {signal_summary['bearish']}个看跌 vs {signal_summary['bullish']}个看涨"
        )

    # 分析六脉神剑
    six_pulse = analysis_result.get("six_pulse_score", {})
    if six_pulse.get("signal") == "BUY":
        bullish_factors.append(f"六脉神剑: {six_pulse['bullish']}个看涨信号")
    elif six_pulse.get("signal") == "SELL":
        bearish_factors.append(f"六脉神剑: {six_pulse['bearish']}个看跌信号")

    # 生成建议
    if len(bullish_factors) > len(bearish_factors) + 1:
        action = "BUY"
        confidence = min(0.9, 0.5 + len(bullish_factors) * 0.1)
        reason = "多个看涨因素共振"
    elif len(bearish_factors) > len(bullish_factors) + 1:
        action = "SELL"
        confidence = min(0.9, 0.5 + len(bearish_factors) * 0.1)
        reason = "多个看跌因素共振"
    else:
        action = "HOLD"
        confidence = 0.5
        reason = "多空因素均衡，建议观望"

    return {
        "action": action,
        "confidence": confidence,
        "reason": reason,
        "bullish_factors": bullish_factors,
        "bearish_factors": bearish_factors,
    }


def get_six_pulse_recommendation(signal: dict) -> str:
    """获取六脉神剑操作建议"""
    bullish = signal.get("bullish", 0)
    bearish = signal.get("bearish", 0)

    if bullish >= 5:
        return "强烈看涨，5个以上指标同时发出多头信号，可考虑积极做多"
    elif bullish >= 4:
        return "看涨，4个指标发出多头信号，可考虑逢低买入"
    elif bearish >= 5:
        return "强烈看跌，5个以上指标同时发出空头信号，建议减仓或观望"
    elif bearish >= 4:
        return "看跌，4个指标发出空头信号，建议谨慎操作"
    elif bullish == 3 and bearish == 3:
        return "多空均衡，市场分歧较大，建议观望等待明确信号"
    elif bullish > bearish:
        return f"偏多，{bullish}个看涨vs{bearish}个看跌，可轻仓参与"
    elif bearish > bullish:
        return f"偏空，{bearish}个看跌vs{bullish}个看涨，建议谨慎"
    else:
        return "中性，建议观望"
