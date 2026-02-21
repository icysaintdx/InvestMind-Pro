"""
情绪共振策略 (Sentiment Resonance Strategy)
AI合成策略 - 结合新闻情绪、技术指标、资金流向三维度

核心理念：
当新闻情绪、技术信号、资金流向三者产生共振时，产生高置信度的交易信号
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import BaseStrategy, StrategySignal, SignalType, StrategyConfig, register_strategy

# 兼容旧代码
Signal = StrategySignal


@register_strategy("sentiment_resonance")
class SentimentResonanceStrategy(BaseStrategy):
    """
    情绪共振策略
    
    三维度共振：
    1. 新闻维度：新闻情绪指数（-1到1）
    2. 技术维度：技术分析得分（0到100）
    3. 资金维度：资金流向强度（-1到1）
    
    只有三个维度同时共振（同向且强度足够）时才发出信号
    """
    
    # 添加策略描述属性
    description = "AI合成策略，结合新闻情绪、技术指标和资金流向三维度共振"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "情绪共振AI策略"
        self.category = "AI合成"
        
        # 策略参数
        self.params = {
            # 共振阈值
            "news_threshold": 0.3,          # 新闻情绪阈值（绝对值）
            "technical_threshold": 60,       # 技术得分阈值
            "fund_threshold": 0.2,           # 资金流向阈值（绝对值）
            "resonance_score_min": 2.5,      # 最低共振得分（满分3）
            
            # 技术指标参数
            "rsi_period": 14,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            
            # 时间窗口
            "news_window": 3,                # 新闻情绪统计窗口（天）
            "fund_window": 5,                # 资金流向统计窗口（天）
        }
        
        # 风险参数
        self.risk_params = {
            "max_position_pct": 0.40,
            "stop_loss_pct": 0.04,
            "take_profit_pct": 0.12,
            "max_drawdown_pct": 0.10
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.params['rsi_period']).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.params['rsi_period']).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # MACD
        ema_fast = df['close'].ewm(span=self.params['macd_fast']).mean()
        ema_slow = df['close'].ewm(span=self.params['macd_slow']).mean()
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=self.params['macd_signal']).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 价格动量
        df['price_momentum'] = df['close'].pct_change(5)
        
        # 成交量动量
        df['volume_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        return df
    
    def analyze_with_agents(
        self,
        stock_code: str,
        agent_results: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        使用智能体分析结果
        
        Args:
            stock_code: 股票代码
            agent_results: 智能体分析结果（如果提供）
            
        Returns:
            三维度得分字典
        """
        if agent_results is None:
            # 如果没有提供智能体结果，使用默认值
            return {
                "news_sentiment": 0.0,
                "technical_score": 50.0,
                "fund_flow": 0.0
            }
        
        # 提取新闻情绪（news_analyst智能体）
        news_sentiment = self._extract_news_sentiment(agent_results)
        
        # 提取技术得分（technical智能体）
        technical_score = self._extract_technical_score(agent_results)
        
        # 提取资金流向（funds智能体）
        fund_flow = self._extract_fund_flow(agent_results)
        
        return {
            "news_sentiment": news_sentiment,
            "technical_score": technical_score,
            "fund_flow": fund_flow
        }
    
    def _extract_news_sentiment(self, agent_results: Dict[str, Any]) -> float:
        """提取新闻情绪指数"""
        try:
            # 从news_analyst智能体结果中提取
            if "news_analyst" in agent_results:
                news_data = agent_results["news_analyst"]
                # 假设返回格式包含sentiment字段
                if isinstance(news_data, dict) and "sentiment" in news_data:
                    return float(news_data["sentiment"])
                # 或者从文本中解析情绪
                if isinstance(news_data, str):
                    return self._parse_sentiment_from_text(news_data)
            
            # 默认中性
            return 0.0
        except Exception as e:
            return 0.0
    
    def _extract_technical_score(self, agent_results: Dict[str, Any]) -> float:
        """提取技术分析得分"""
        try:
            # 从technical智能体结果中提取
            if "technical" in agent_results:
                tech_data = agent_results["technical"]
                if isinstance(tech_data, dict) and "score" in tech_data:
                    return float(tech_data["score"])
                # 或者从文本中解析得分
                if isinstance(tech_data, str):
                    return self._parse_score_from_text(tech_data)
            
            # 默认中性得分
            return 50.0
        except Exception as e:
            return 50.0
    
    def _extract_fund_flow(self, agent_results: Dict[str, Any]) -> float:
        """提取资金流向强度"""
        try:
            # 从funds智能体结果中提取
            if "funds" in agent_results:
                fund_data = agent_results["funds"]
                if isinstance(fund_data, dict) and "flow_strength" in fund_data:
                    return float(fund_data["flow_strength"])
                # 或者从文本中解析
                if isinstance(fund_data, str):
                    return self._parse_fund_flow_from_text(fund_data)
            
            # 默认中性
            return 0.0
        except Exception as e:
            return 0.0
    
    def _parse_sentiment_from_text(self, text: str) -> float:
        """从文本中解析情绪（简单实现）"""
        text = text.lower()
        positive_words = ["利好", "看涨", "积极", "乐观", "上涨", "买入"]
        negative_words = ["利空", "看跌", "消极", "悲观", "下跌", "卖出"]
        
        pos_count = sum(1 for word in positive_words if word in text)
        neg_count = sum(1 for word in negative_words if word in text)
        
        if pos_count + neg_count == 0:
            return 0.0
        
        return (pos_count - neg_count) / (pos_count + neg_count)
    
    def _parse_score_from_text(self, text: str) -> float:
        """从文本中解析得分"""
        # 简单实现：查找数字
        import re
        numbers = re.findall(r'\d+', text)
        if numbers:
            score = float(numbers[0])
            return min(max(score, 0), 100)  # 限制在0-100
        return 50.0
    
    def _parse_fund_flow_from_text(self, text: str) -> float:
        """从文本中解析资金流向"""
        text = text.lower()
        inflow_words = ["流入", "净流入", "买入", "增持"]
        outflow_words = ["流出", "净流出", "卖出", "减持"]
        
        in_count = sum(1 for word in inflow_words if word in text)
        out_count = sum(1 for word in outflow_words if word in text)
        
        if in_count + out_count == 0:
            return 0.0
        
        return (in_count - out_count) / (in_count + out_count)
    
    def calculate_resonance_score(
        self,
        news_sentiment: float,
        technical_score: float,
        fund_flow: float
    ) -> Dict[str, Any]:
        """
        计算共振得分
        
        Returns:
            包含共振得分、方向、强度的字典
        """
        # 标准化各维度得分到[-1, 1]
        news_norm = news_sentiment  # 已经是[-1, 1]
        tech_norm = (technical_score - 50) / 50  # 转换到[-1, 1]
        fund_norm = fund_flow  # 已经是[-1, 1]
        
        # 判断方向
        direction = 0
        if news_norm > 0 and tech_norm > 0 and fund_norm > 0:
            direction = 1  # 多头共振
        elif news_norm < 0 and tech_norm < 0 and fund_norm < 0:
            direction = -1  # 空头共振
        
        # 计算共振强度（三个维度的平均绝对值）
        resonance_strength = (abs(news_norm) + abs(tech_norm) + abs(fund_norm)) / 3
        
        # 计算共振得分（0-3分）
        score = 0
        if abs(news_norm) >= self.params['news_threshold'] / 1.0:
            score += abs(news_norm)
        if abs(tech_norm) >= (self.params['technical_threshold'] - 50) / 50:
            score += abs(tech_norm)
        if abs(fund_norm) >= self.params['fund_threshold'] / 1.0:
            score += abs(fund_norm)
        
        return {
            "score": score,
            "direction": direction,
            "strength": resonance_strength,
            "news_norm": news_norm,
            "tech_norm": tech_norm,
            "fund_norm": fund_norm
        }
    
    def initialize(self, data: pd.DataFrame) -> None:
        """初始化策略"""
        self._initialized = True
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0,
                        sentiment_data: Optional[Dict[str, Any]] = None) -> StrategySignal:
        """
        生成交易信号 - 真正融合情绪数据 + 技术指标
        
        Args:
            data: K线数据
            current_position: 当前持仓
            sentiment_data: 情绪摘要，来自 SentimentTrendService.get_stock_sentiment_summary()
                {
                    "score": float,           # -1~1
                    "direction": str,         # bullish/bearish/neutral
                    "momentum": float,        # 情绪动量
                    "confidence": float,      # 数据置信度
                    "recent_negative_spike": bool,
                    "trend_reversal": bool,
                    "signal_strength": float,
                }
        """
        df = self.calculate_indicators(data)
        
        if len(df) < 20:
            return StrategySignal(
                signal_type=SignalType.HOLD,
                confidence=0.0,
                strength=0.0,
                reasons=["数据不足"],
                strategy_id="sentiment_resonance",
                strategy_name=self.name
            )
        
        row = df.iloc[-1]
        price = row['close']
        rsi = row.get('rsi', 50)
        macd = row.get('macd', 0)
        macd_hist = row.get('macd_hist', 0)
        vol_ratio = row.get('volume_ratio', 1.0)
        
        # === 情绪维度 ===
        sent = sentiment_data or {}
        sent_score = sent.get("score", 0.0)
        sent_direction = sent.get("direction", "neutral")
        sent_momentum = sent.get("momentum", 0.0)
        sent_confidence = sent.get("confidence", 0.0)
        negative_spike = sent.get("recent_negative_spike", False)
        trend_reversal = sent.get("trend_reversal", False)
        
        # === 技术维度得分 (-1 ~ 1) ===
        tech_score = 0.0
        tech_reasons = []
        
        if rsi < 30:
            tech_score += 0.6
            tech_reasons.append(f"RSI超卖({rsi:.1f})")
        elif rsi < 45:
            tech_score += 0.3
            tech_reasons.append(f"RSI偏低({rsi:.1f})")
        elif rsi > 70:
            tech_score -= 0.6
            tech_reasons.append(f"RSI超买({rsi:.1f})")
        elif rsi > 55:
            tech_score -= 0.3
            tech_reasons.append(f"RSI偏高({rsi:.1f})")
        
        if macd > 0 and macd_hist > 0:
            tech_score += 0.4
            tech_reasons.append("MACD金叉放大")
        elif macd > 0:
            tech_score += 0.2
            tech_reasons.append("MACD为正")
        elif macd < 0 and macd_hist < 0:
            tech_score -= 0.4
            tech_reasons.append("MACD死叉放大")
        elif macd < 0:
            tech_score -= 0.2
            tech_reasons.append("MACD为负")
        
        tech_score = max(-1.0, min(1.0, tech_score))
        
        # === 资金维度（量比） ===
        fund_score = 0.0
        if vol_ratio > 2.0:
            fund_score = 0.4
        elif vol_ratio > 1.3:
            fund_score = 0.2
        elif vol_ratio < 0.5:
            fund_score = -0.3
        elif vol_ratio < 0.8:
            fund_score = -0.1
        
        # === 三维度共振计算 ===
        # 情绪权重40% + 技术权重35% + 资金权重25%
        sentiment_weight = 0.40 if sent_confidence > 0.3 else 0.15
        tech_weight = 0.35 if sent_confidence > 0.3 else 0.55
        fund_weight = 0.25 if sent_confidence > 0.3 else 0.30
        
        composite_score = (
            sent_score * sentiment_weight +
            tech_score * tech_weight +
            fund_score * fund_weight
        )
        
        # === 特殊情况处理 ===
        reasons = []
        
        if negative_spike:
            composite_score -= 0.3
            reasons.append("⚠️ 负面情绪突增")
        
        if trend_reversal:
            composite_score *= 0.7
            reasons.append("⚠️ 情绪趋势反转")
        
        # === 信号生成 ===
        if composite_score > 0.5:
            signal_type = SignalType.STRONG_BUY
            confidence = min(0.6 + abs(composite_score) * 0.3, 0.95)
        elif composite_score > 0.2:
            signal_type = SignalType.BUY
            confidence = min(0.5 + abs(composite_score) * 0.3, 0.85)
        elif composite_score < -0.5:
            signal_type = SignalType.STRONG_SELL
            confidence = min(0.6 + abs(composite_score) * 0.3, 0.95)
        elif composite_score < -0.2:
            signal_type = SignalType.SELL
            confidence = min(0.5 + abs(composite_score) * 0.3, 0.85)
        else:
            signal_type = SignalType.HOLD
            confidence = 0.4
        
        # 构建原因列表
        if sent_confidence > 0.1:
            reasons.append(f"📰 情绪: {sent_direction}({sent_score:+.2f}, 动量{sent_momentum:+.2f})")
        else:
            reasons.append("📰 情绪: 数据不足")
        reasons.extend([f"📊 {r}" for r in tech_reasons[:2]])
        if fund_score != 0:
            reasons.append(f"💰 量比: {vol_ratio:.2f}")
        reasons.append(f"共振得分: {composite_score:+.3f}")
        
        strength = min(abs(composite_score), 1.0)
        
        return StrategySignal(
            signal_type=signal_type,
            confidence=round(confidence, 3),
            strength=round(strength, 3),
            price=price,
            stop_loss=price * (1 - self.risk_params['stop_loss_pct']) if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else None,
            target_price=price * (1 + self.risk_params['take_profit_pct']) if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else None,
            position_size=self.risk_params['max_position_pct'] * strength if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else 0,
            reasons=reasons[:5],
            strategy_id="sentiment_resonance",
            strategy_name=self.name
        )
    
    # _generate_signals_legacy removed - was dead code using only RSI+MACD without sentiment
    
    def _generate_buy_reasons(
        self,
        resonance: Dict[str, Any],
        agent_scores: Dict[str, float],
        row: pd.Series
    ) -> List[str]:
        """生成买入信号原因"""
        reasons = []
        
        reasons.append(f"✓ 三维度多头共振（得分{resonance['score']:.2f}/3.00）")
        
        if resonance["news_norm"] > 0:
            reasons.append(f"  📰 新闻情绪：{agent_scores['news_sentiment']:.2f}（正面）")
        
        if resonance["tech_norm"] > 0:
            reasons.append(f"  📊 技术得分：{agent_scores['technical_score']:.1f}/100（看涨）")
        
        if resonance["fund_norm"] > 0:
            reasons.append(f"  💰 资金流向：{agent_scores['fund_flow']:.2f}（净流入）")
        
        reasons.append(f"共振强度：{resonance['strength']:.1%}")
        reasons.append(f"RSI：{row['rsi']:.1f}，MACD柱：{row['macd_hist']:.3f}")
        
        return reasons
    
    def _generate_sell_reasons(
        self,
        resonance: Dict[str, Any],
        agent_scores: Dict[str, float],
        row: pd.Series
    ) -> List[str]:
        """生成卖出信号原因"""
        reasons = []
        
        reasons.append(f"✗ 三维度空头共振（得分{resonance['score']:.2f}/3.00）")
        
        if resonance["news_norm"] < 0:
            reasons.append(f"  📰 新闻情绪：{agent_scores['news_sentiment']:.2f}（负面）")
        
        if resonance["tech_norm"] < 0:
            reasons.append(f"  📊 技术得分：{agent_scores['technical_score']:.1f}/100（看跌）")
        
        if resonance["fund_norm"] < 0:
            reasons.append(f"  💰 资金流向：{agent_scores['fund_flow']:.2f}（净流出）")
        
        reasons.append(f"共振强度：{resonance['strength']:.1%}")
        
        return reasons
    
    def get_required_indicators(self) -> List[str]:
        """获取所需的技术指标"""
        return [
            'rsi',
            'macd',
            'macd_signal',
            'macd_hist',
            'price_momentum',
            'volume_ma',
            'volume_ratio'
        ]
