"""
多空辩论加权策略 (Debate Weighted Strategy)
AI合成策略 - 利用21智能体的多空辩论结果进行加权决策

核心理念：
将21个智能体的分析结果按照优先级和可信度进行加权，
通过多空辩论的方式得出最终的投资建议
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from datetime import datetime
from .base import BaseStrategy, StrategySignal, SignalType, StrategyConfig, register_strategy

# 兼容旧代码
Signal = StrategySignal


@register_strategy("debate_weighted")
class DebateWeightedStrategy(BaseStrategy):
    """
    多空辩论加权策略
    
    智能体分级：
    - 核心必须(9个): 权重1.5
    - 重要增强(6个): 权重1.2
    - 可选补充(6个): 权重1.0
    
    决策流程：
    1. 收集21个智能体的观点和得分
    2. 按照优先级进行加权
    3. 计算多空双方的总得分
    4. 根据得分差异和置信度生成信号
    """
    
    # 添加策略描述属性
    description = "AI合成策略，通过21个智能体的多空辩论进行加权决策"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "辩论加权AI策略"
        self.category = "AI合成"
        
        # 智能体权重配置
        self.agent_weights = {
            # 核心必需(9个) - 权重1.5
            "news_analyst": 1.5,
            "fundamental": 1.5,
            "technical": 1.5,
            "bull_researcher": 1.5,
            "bear_researcher": 1.5,
            "research_manager": 1.5,
            "risk_manager": 1.5,
            "gm": 1.5,
            "trader": 1.5,
            
            # 重要增强(6个) - 权重1.2
            "macro": 1.2,
            "industry": 1.2,
            "funds": 1.2,
            "manager_fundamental": 1.2,
            "risk_aggressive": 1.2,
            "risk_conservative": 1.2,
            
            # 可选补充(6个) - 权重1.0
            "china_market": 1.0,
            "social_analyst": 1.0,
            "manager_momentum": 1.0,
            "risk_system": 1.0,
            "risk_portfolio": 1.0,
            "interpreter": 1.0,
        }
        
        # 策略参数
        self.params = {
            "score_threshold": 10.0,         # 最低得分阈值
            "confidence_threshold": 0.6,     # 最低置信度阈值
            "debate_gap_min": 5.0,           # 多空得分差距最小值
            "consensus_bonus": 1.2,          # 一致性加成系数
            "use_risk_adjustment": True,     # 是否使用风险调整
        }
        
        # 风险参数
        self.risk_params = {
            "max_position_pct": 0.35,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.15,
            "max_drawdown_pct": 0.12
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算基础技术指标（用于辅助判断）"""
        df = data.copy()
        
        # 简单移动平均
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_50'] = df['close'].rolling(window=50).mean()
        
        # 价格相对位置
        df['price_position'] = (df['close'] - df['sma_20']) / df['sma_20']
        
        return df
    
    def analyze_agent_results(
        self,
        agent_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        分析所有智能体的结果
        
        Returns:
            包含多空得分、置信度、一致性等信息的字典
        """
        bull_score = 0.0  # 多方总得分
        bear_score = 0.0  # 空方总得分
        total_weight = 0.0  # 总权重
        
        agent_opinions = []  # 记录每个智能体的观点
        
        # 遍历所有智能体结果
        for agent_name, weight in self.agent_weights.items():
            if agent_name not in agent_results:
                continue
            
            agent_data = agent_results[agent_name]
            
            # 提取智能体的观点和得分
            opinion = self._extract_agent_opinion(agent_name, agent_data)
            
            if opinion:
                agent_opinions.append(opinion)
                
                # 根据观点方向累加得分
                if opinion["direction"] == "bull":
                    bull_score += opinion["score"] * weight
                elif opinion["direction"] == "bear":
                    bear_score += opinion["score"] * weight
                
                total_weight += weight
        
        # 计算最终得分
        if total_weight > 0:
            bull_score_normalized = bull_score / total_weight * 100
            bear_score_normalized = bear_score / total_weight * 100
        else:
            bull_score_normalized = 50.0
            bear_score_normalized = 50.0
        
        # 计算一致性（观点集中度）
        consensus = self._calculate_consensus(agent_opinions)
        
        # 计算置信度
        score_gap = abs(bull_score_normalized - bear_score_normalized)
        confidence = min(score_gap / 100.0 * consensus, 1.0)
        
        # 确定最终方向
        if bull_score_normalized > bear_score_normalized:
            direction = "bull"
            final_score = bull_score_normalized
        elif bear_score_normalized > bull_score_normalized:
            direction = "bear"
            final_score = bear_score_normalized
        else:
            direction = "neutral"
            final_score = 50.0
        
        return {
            "direction": direction,
            "final_score": final_score,
            "bull_score": bull_score_normalized,
            "bear_score": bear_score_normalized,
            "score_gap": score_gap,
            "consensus": consensus,
            "confidence": confidence,
            "agent_opinions": agent_opinions,
            "total_agents": len(agent_opinions)
        }
    
    def _extract_agent_opinion(
        self,
        agent_name: str,
        agent_data: Any
    ) -> Optional[Dict[str, Any]]:
        """
        提取单个智能体的观点
        
        Returns:
            包含方向、得分、理由的字典
        """
        try:
            # 如果是字典格式
            if isinstance(agent_data, dict):
                direction = agent_data.get("direction", "neutral")
                score = float(agent_data.get("score", 50))
                reason = agent_data.get("reason", "")
                
                return {
                    "agent": agent_name,
                    "direction": direction,
                    "score": score,
                    "reason": reason
                }
            
            # 如果是文本格式，需要解析
            if isinstance(agent_data, str):
                return self._parse_opinion_from_text(agent_name, agent_data)
            
            return None
            
        except Exception as e:
            return None
    
    def _parse_opinion_from_text(
        self,
        agent_name: str,
        text: str
    ) -> Optional[Dict[str, Any]]:
        """从文本中解析观点"""
        text_lower = text.lower()
        
        # 判断方向
        bull_keywords = ["看涨", "买入", "增持", "利好", "上涨", "积极", "乐观"]
        bear_keywords = ["看跌", "卖出", "减持", "利空", "下跌", "消极", "悲观"]
        
        bull_count = sum(1 for kw in bull_keywords if kw in text)
        bear_count = sum(1 for kw in bear_keywords if kw in text)
        
        if bull_count > bear_count:
            direction = "bull"
            score = min(50 + (bull_count - bear_count) * 10, 100)
        elif bear_count > bull_count:
            direction = "bear"
            score = min(50 + (bear_count - bull_count) * 10, 100)
        else:
            direction = "neutral"
            score = 50
        
        return {
            "agent": agent_name,
            "direction": direction,
            "score": score,
            "reason": text[:100]  # 截取前100字符
        }
    
    def _calculate_consensus(self, agent_opinions: List[Dict[str, Any]]) -> float:
        """
        计算观点一致性
        
        Returns:
            一致性得分（0-1）
        """
        if len(agent_opinions) < 2:
            return 0.5
        
        # 统计各方向的数量
        bull_count = sum(1 for op in agent_opinions if op["direction"] == "bull")
        bear_count = sum(1 for op in agent_opinions if op["direction"] == "bear")
        neutral_count = len(agent_opinions) - bull_count - bear_count
        
        # 计算最大一致性比例
        max_count = max(bull_count, bear_count, neutral_count)
        consensus = max_count / len(agent_opinions)
        
        return consensus
    
    def initialize(self, data: pd.DataFrame) -> None:
        """初始化策略"""
        self._initialized = True
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> StrategySignal:
        """生成交易信号（新接口）"""
        df = self.calculate_indicators(data)

        if len(df) < 20:
            return StrategySignal(
                signal_type=SignalType.HOLD,
                confidence=0.0,
                strength=0.0,
                reasons=["数据不足"],
                strategy_id="debate_weighted",
                strategy_name=self.name
            )

        row = df.iloc[-1]
        prev_row = df.iloc[-2] if len(df) > 1 else row
        price = row['close']

        signal_type = SignalType.HOLD
        confidence = 0.5
        reasons = []

        # 基于技术分析的多空判断
        sma_20 = row.get('sma_20', price)
        sma_50 = row.get('sma_50', price)
        price_position = row.get('price_position', 0)

        # 多方信号：价格在均线上方且趋势向上
        bull_signals = 0
        bear_signals = 0

        # 1. 价格位置
        if price > sma_20:
            bull_signals += 1
            reasons.append("价格高于MA20")
        else:
            bear_signals += 1

        # 2. 均线排列
        if sma_20 > sma_50:
            bull_signals += 1
            reasons.append("MA20 > MA50 多头排列")
        else:
            bear_signals += 1

        # 3. 价格动量
        if price > prev_row['close']:
            bull_signals += 1
            reasons.append("价格上涨")
        else:
            bear_signals += 1

        # 4. 相对位置
        if price_position > 0.02:
            bull_signals += 1
            reasons.append(f"价格偏离MA20: {price_position:.1%}")
        elif price_position < -0.02:
            bear_signals += 1

        # 生成信号
        if bull_signals >= 3 and current_position == 0:
            signal_type = SignalType.BUY
            confidence = 0.6 + bull_signals * 0.05
            reasons.insert(0, "多空辩论：多方占优")
        elif bear_signals >= 3 and current_position > 0:
            signal_type = SignalType.SELL
            confidence = 0.6 + bear_signals * 0.05
            reasons = ["多空辩论：空方占优"]

        return StrategySignal(
            signal_type=signal_type,
            confidence=min(confidence, 0.85),
            strength=0.6,
            price=price,
            stop_loss=price * 0.95 if signal_type == SignalType.BUY else None,
            target_price=price * 1.10 if signal_type == SignalType.BUY else None,
            position_size=0.3 if signal_type == SignalType.BUY else 0,
            reasons=reasons[:5],
            strategy_id="debate_weighted",
            strategy_name=self.name
        )
    
    def _generate_signals_legacy(
        self,
        data: pd.DataFrame,
        agent_results: Optional[Dict[str, Any]] = None
    ) -> List[Signal]:
        """
        生成交易信号
        
        Args:
            data: 价格数据
            agent_results: 21个智能体的分析结果
        """
        if agent_results is None:
            return []
        
        df = self.calculate_indicators(data)
        signals = []
        
        # 分析智能体结果
        debate_result = self.analyze_agent_results(agent_results)
        
        # 检查是否满足信号条件
        if (debate_result["final_score"] < self.params["score_threshold"] or
            debate_result["confidence"] < self.params["confidence_threshold"] or
            debate_result["score_gap"] < self.params["debate_gap_min"]):
            return signals
        
        # 只在最后一根K线生成信号
        if len(df) < 2:
            return signals
        
        row = df.iloc[-1]
        
        # 多头信号
        if debate_result["direction"] == "bull":
            current_price = row['close']
            
            # 根据一致性调整仓位
            position_multiplier = 1.0
            if debate_result["consensus"] > 0.8:
                position_multiplier = self.params["consensus_bonus"]
            
            # 计算目标价和止损价
            target_price = current_price * (1 + self.risk_params['take_profit_pct'])
            stop_loss = current_price * (1 - self.risk_params['stop_loss_pct'])
            
            # 计算仓位
            position_size = (self.risk_params['max_position_pct'] * 
                           debate_result["confidence"] * 
                           position_multiplier)
            position_size = min(position_size, self.risk_params['max_position_pct'])
            
            # 生成信号原因
            reasons = self._generate_bull_reasons(debate_result)
            
            signal = Signal(
                strategy_id="debate_weighted",
                strategy_name=self.name,
                signal_type=SignalType.BUY,
                strength=debate_result["confidence"],
                confidence=debate_result["confidence"],
                target_price=target_price,
                stop_loss=stop_loss,
                position_size=position_size,
                reasons=reasons,
                timestamp=df.index[-1]
            )
            
            signals.append(signal)
        
        # 空头信号
        elif debate_result["direction"] == "bear":
            reasons = self._generate_bear_reasons(debate_result)
            
            signal = Signal(
                strategy_id="debate_weighted",
                strategy_name=self.name,
                signal_type=SignalType.SELL,
                strength=debate_result["confidence"],
                confidence=debate_result["confidence"],
                reasons=reasons,
                timestamp=df.index[-1]
            )
            
            signals.append(signal)
        
        return signals
    
    def _generate_bull_reasons(self, debate_result: Dict[str, Any]) -> List[str]:
        """生成多头信号原因"""
        reasons = []
        
        reasons.append(f"🐂 多方辩论胜出（{debate_result['total_agents']}个智能体参与）")
        reasons.append(f"  多方得分：{debate_result['bull_score']:.1f}/100")
        reasons.append(f"  空方得分：{debate_result['bear_score']:.1f}/100")
        reasons.append(f"  得分差距：{debate_result['score_gap']:.1f}")
        reasons.append(f"  观点一致性：{debate_result['consensus']:.1%}")
        reasons.append(f"  综合置信度：{debate_result['confidence']:.1%}")
        
        # 添加主要支持观点
        bull_opinions = [op for op in debate_result["agent_opinions"] 
                        if op["direction"] == "bull"]
        if bull_opinions:
            reasons.append(f"\n主要多方观点：")
            for op in bull_opinions[:3]:  # 最多显示3个
                reasons.append(f"  • {op['agent']}: {op['reason'][:50]}...")
        
        return reasons
    
    def _generate_bear_reasons(self, debate_result: Dict[str, Any]) -> List[str]:
        """生成空头信号原因"""
        reasons = []
        
        reasons.append(f"🐻 空方辩论胜出（{debate_result['total_agents']}个智能体参与）")
        reasons.append(f"  空方得分：{debate_result['bear_score']:.1f}/100")
        reasons.append(f"  多方得分：{debate_result['bull_score']:.1f}/100")
        reasons.append(f"  得分差距：{debate_result['score_gap']:.1f}")
        reasons.append(f"  观点一致性：{debate_result['consensus']:.1%}")
        reasons.append(f"  综合置信度：{debate_result['confidence']:.1%}")
        
        # 添加主要支持观点
        bear_opinions = [op for op in debate_result["agent_opinions"] 
                        if op["direction"] == "bear"]
        if bear_opinions:
            reasons.append(f"\n主要空方观点：")
            for op in bear_opinions[:3]:
                reasons.append(f"  • {op['agent']}: {op['reason'][:50]}...")
        
        return reasons
    
    def get_required_indicators(self) -> List[str]:
        """获取所需的技术指标"""
        return ['sma_20', 'sma_50', 'price_position']
