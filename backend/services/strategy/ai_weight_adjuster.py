# -*- coding: utf-8 -*-
"""
AI策略权重调节器
根据情绪趋势动态调整策略权重

核心逻辑：
- 情绪看多 → 提升进攻型策略权重（动量/趋势/涨停）
- 情绪看空 → 提升防守型策略权重（价值/均值回归）
- 情绪中性 → 使用基准权重
- 负面突增 → 大幅降低进攻型，提升防守型
- 趋势反转 → 降低所有策略置信度

Author: AI升级
Date: 2026-02-22
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


# 策略分类：进攻型 vs 防守型
OFFENSIVE_STRATEGIES = {
    "ema_breakout", "macd_crossover", "dragon_leader",
    "scalping_blade", "limit_up_trading", "volume_price_surge",
    "sentiment_resonance"
}

DEFENSIVE_STRATEGIES = {
    "buffett_value", "lynch_growth", "graham_margin",
    "turtle_trading"
}

NEUTRAL_STRATEGIES = {
    "vegas_adx", "bollinger_breakout", "trident",
    "martingale_refined", "debate_weighted"
}


class AIWeightAdjuster:
    """
    AI策略权重调节器
    
    输入：情绪摘要（来自 SentimentTrendService）
    输出：调整后的策略权重字典
    """
    
    def __init__(self):
        # 基准权重（从 manager.py 默认值）
        self.base_weights = {
            "vegas_adx": 0.8,
            "ema_breakout": 0.7,
            "macd_crossover": 0.7,
            "bollinger_breakout": 0.7,
            "turtle_trading": 0.8,
            "trident": 0.6,
            "buffett_value": 0.9,
            "lynch_growth": 0.85,
            "graham_margin": 0.85,
            "martingale_refined": 0.5,
            "dragon_leader": 0.6,
            "scalping_blade": 0.5,
            "limit_up_trading": 0.6,
            "volume_price_surge": 0.6,
            "sentiment_resonance": 0.75,
            "debate_weighted": 0.8,
        }
        
        # 调整幅度参数
        self.max_boost = 0.25       # 最大加成
        self.max_penalty = 0.30     # 最大惩罚
        self.spike_penalty = 0.40   # 负面突增惩罚
        
        logger.info("AIWeightAdjuster initialized")
    
    def adjust_weights(
        self,
        sentiment_summary: Dict[str, Any],
        current_weights: Optional[Dict[str, float]] = None
    ) -> Dict[str, float]:
        """
        根据情绪摘要调整策略权重
        
        Args:
            sentiment_summary: 来自 SentimentTrendService.get_stock_sentiment_summary()
                {
                    "score": float,
                    "direction": str,
                    "momentum": float,
                    "confidence": float,
                    "recent_negative_spike": bool,
                    "trend_reversal": bool,
                    "signal_strength": float,
                }
            current_weights: 当前权重（None则使用基准）
            
        Returns:
            调整后的权重字典
        """
        weights = dict(current_weights or self.base_weights)
        
        direction = sentiment_summary.get("direction", "neutral")
        momentum = sentiment_summary.get("momentum", 0.0)
        confidence = sentiment_summary.get("confidence", 0.0)
        signal_strength = sentiment_summary.get("signal_strength", 0.0)
        negative_spike = sentiment_summary.get("recent_negative_spike", False)
        trend_reversal = sentiment_summary.get("trend_reversal", False)
        
        # 调整因子 = 动量 * 置信度（低置信度时调整幅度小）
        adjust_factor = momentum * confidence
        
        # === 1. 基于方向的调整 ===
        if direction == "bullish":
            for sid in OFFENSIVE_STRATEGIES:
                if sid in weights:
                    boost = min(adjust_factor * self.max_boost, self.max_boost)
                    weights[sid] = min(weights[sid] + boost, 1.0)
            for sid in DEFENSIVE_STRATEGIES:
                if sid in weights:
                    penalty = min(abs(adjust_factor) * self.max_penalty * 0.5, self.max_penalty * 0.5)
                    weights[sid] = max(weights[sid] - penalty, 0.1)
                    
        elif direction == "bearish":
            for sid in DEFENSIVE_STRATEGIES:
                if sid in weights:
                    boost = min(abs(adjust_factor) * self.max_boost, self.max_boost)
                    weights[sid] = min(weights[sid] + boost, 1.0)
            for sid in OFFENSIVE_STRATEGIES:
                if sid in weights:
                    penalty = min(abs(adjust_factor) * self.max_penalty, self.max_penalty)
                    weights[sid] = max(weights[sid] - penalty, 0.1)
        
        # === 2. 负面突增：紧急降低进攻型 ===
        if negative_spike:
            logger.warning("Negative sentiment spike detected! Reducing offensive weights.")
            for sid in OFFENSIVE_STRATEGIES:
                if sid in weights:
                    weights[sid] = max(weights[sid] - self.spike_penalty, 0.1)
            # 提升防守型
            for sid in DEFENSIVE_STRATEGIES:
                if sid in weights:
                    weights[sid] = min(weights[sid] + self.spike_penalty * 0.5, 1.0)
        
        # === 3. 趋势反转：降低所有策略置信度 ===
        if trend_reversal:
            logger.info("Sentiment trend reversal detected. Reducing all weights by 15%.")
            for sid in weights:
                weights[sid] = max(weights[sid] * 0.85, 0.1)
        
        # === 4. 情绪共振策略特殊处理：信号强时大幅提升 ===
        if "sentiment_resonance" in weights and signal_strength > 0.5:
            weights["sentiment_resonance"] = min(
                weights["sentiment_resonance"] + signal_strength * 0.2, 1.0
            )
        
        # 四舍五入
        weights = {k: round(v, 3) for k, v in weights.items()}
        
        logger.info(
            f"Weights adjusted: direction={direction}, momentum={momentum:.3f}, "
            f"confidence={confidence:.2f}, spike={negative_spike}, reversal={trend_reversal}"
        )
        
        return weights
    
    def get_adjustment_report(
        self,
        sentiment_summary: Dict[str, Any],
        old_weights: Dict[str, float],
        new_weights: Dict[str, float]
    ) -> Dict[str, Any]:
        """生成权重调整报告"""
        changes = {}
        for sid in new_weights:
            old = old_weights.get(sid, 0)
            new = new_weights[sid]
            if abs(new - old) > 0.001:
                changes[sid] = {
                    "old": old,
                    "new": new,
                    "delta": round(new - old, 3),
                    "category": (
                        "offensive" if sid in OFFENSIVE_STRATEGIES
                        else "defensive" if sid in DEFENSIVE_STRATEGIES
                        else "neutral"
                    )
                }
        
        return {
            "sentiment_direction": sentiment_summary.get("direction", "neutral"),
            "sentiment_momentum": sentiment_summary.get("momentum", 0),
            "negative_spike": sentiment_summary.get("recent_negative_spike", False),
            "trend_reversal": sentiment_summary.get("trend_reversal", False),
            "changes": changes,
            "total_changed": len(changes),
            "adjusted_at": datetime.now().isoformat()
        }


# 全局实例
_adjuster = None

def get_ai_weight_adjuster() -> AIWeightAdjuster:
    """获取AI权重调节器实例（单例）"""
    global _adjuster
    if _adjuster is None:
        _adjuster = AIWeightAdjuster()
    return _adjuster
