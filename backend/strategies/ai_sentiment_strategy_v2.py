"""
AI情绪驱动策略 - LLM增强版 (AI Sentiment Strategy v2)
=====================================================

核心改进:
    1. 真正使用LLM做最终交易决策
    2. 规则计算作为特征输入LLM
    3. LLM输出决策理由，增强可解释性
    4. 支持情绪趋势分析

Author: 自主执行代理
Date: 2026-02-28
"""

import os
import json
import asyncio
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import logging

import pandas as pd
import numpy as np

from backend.strategies.base import (
    BaseStrategy, StrategySignal, SignalType,
    StrategyConfig, StrategyCategory, register_strategy
)
from backend.strategies.ai_sentiment_strategy import (
    AISentimentStrategy, load_sentiment_from_db, merge_sentiment_into_ohlcv
)

logger = logging.getLogger(__name__)


@register_strategy("ai_sentiment_v2")
class AISentimentStrategyV2(AISentimentStrategy):
    """
    AI情绪驱动策略 V2 - LLM增强版
    
    相比V1的改进:
        - V1: 规则组合 (技术+情绪+资金加权)
        - V2: LLM做最终决策，规则作为输入特征
    
    决策流程:
        1. 计算技术指标特征 (RSI, MACD, 布林带, 均线)
        2. 加载情绪数据特征 (sent_smooth, sent_momentum, sent_trend)
        3. 计算资金流向特征 (量比, 价量背离)
        4. 构建LLM提示词 (包含上述特征+近期新闻摘要)
        5. LLM分析并输出决策 (BUY/SELL/HOLD + 理由)
        6. 解析LLM响应，生成StrategySignal
    
    特征工程:
        - 情绪趋势: 7日/30日情绪MA + 情绪MACD
        - 技术共振: 多指标共振强度
        - 异常检测: 情绪突变、成交量异常
    """

    description = "AI情绪驱动策略V2: LLM增强版，真正使用AI做交易决策"

    def __init__(self, config: Optional[StrategyConfig] = None):
        super().__init__(config)
        self.name = "AI情绪驱动策略V2"
        self.version = "2.0.0"
        
        # LLM配置
        self._llm_client = None
        self._init_llm()
        
        # V2新参数
        self.sentiment_ma_short = 7   # 7日情绪MA
        self.sentiment_ma_long = 30   # 30日情绪MA
        self.use_llm_for_decision = True  # 是否使用LLM决策
        self.llm_fallback_to_rules = True  # LLM失败时回退到规则
        
    def _init_llm(self):
        """初始化LLM客户端"""
        try:
            from backend.services.llm.llm_service import get_llm_service
            self._llm_client = get_llm_service()
            logger.info("[AISentimentV2] LLM client initialized")
        except Exception as e:
            logger.warning(f"[AISentimentV2] Failed to init LLM: {e}")
            self._llm_client = None

    def _ensure_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """确保所有指标已计算（V2增强版）"""
        df = super()._ensure_indicators(data)
        
        # 添加情绪趋势指标
        if 'sent_smooth' in df.columns:
            # 7日/30日情绪MA
            df['sent_ma7'] = df['sent_smooth'].rolling(window=7, min_periods=1).mean()
            df['sent_ma30'] = df['sent_smooth'].rolling(window=30, min_periods=1).mean()
            
            # 情绪MACD (类似价格MACD)
            df['sent_macd'] = df['sent_ma7'] - df['sent_ma30']
            df['sent_macd_signal'] = df['sent_macd'].ewm(span=9, min_periods=1).mean()
            df['sent_macd_hist'] = df['sent_macd'] - df['sent_macd_signal']
            
            # 情绪趋势方向
            df['sent_trend'] = np.where(
                df['sent_macd'] > 0, 'up',
                np.where(df['sent_macd'] < 0, 'down', 'neutral')
            )
            
            # 情绪异常标记 (单日情绪变化>0.5)
            df['sent_spike'] = abs(df['sent_smooth'].diff()) > 0.5
        
        return df

    def generate_signal(
        self,
        data: pd.DataFrame,
        current_position: int = 0,
        **kwargs,
    ) -> StrategySignal:
        """生成交易信号 - V2 LLM增强版"""
        df = self._ensure_indicators(data)
        
        if len(df) < 60:
            return self._hold_signal("数据不足(<60天)")
        
        # 获取特征数据
        features = self._extract_features(df)
        
        # 如果使用LLM且客户端可用
        if self.use_llm_for_decision and self._llm_client:
            try:
                signal = self._llm_decision(features, df, current_position)
                if signal:
                    return signal
            except Exception as e:
                logger.error(f"[AISentimentV2] LLM决策失败: {e}")
                if not self.llm_fallback_to_rules:
                    return self._hold_signal(f"LLM错误: {str(e)[:50]}")
        
        # 回退到V1规则决策
        logger.debug("[AISentimentV2] 使用规则回退")
        return super().generate_signal(data, current_position, **kwargs)

    def _extract_features(self, df: pd.DataFrame) -> Dict[str, Any]:
        """提取特征数据用于LLM决策"""
        row = df.iloc[-1]
        prev = df.iloc[-2] if len(df) > 1 else row
        
        # 基础价格信息
        price = float(row['close'])
        price_change = (price / float(prev['close']) - 1) * 100 if prev['close'] != 0 else 0
        
        # 技术指标特征
        tech_features = {
            'rsi': round(float(row.get('rsi', 50)), 2),
            'macd': round(float(row.get('macd_hist', 0)), 4),
            'bb_position': self._calc_bb_position(row),
            'ma_trend': self._calc_ma_trend(df),
            'price_vs_ma20': round((price / float(row.get('ma_20', price)) - 1) * 100, 2),
        }
        
        # 情绪特征
        sent_features = {
            'sent_current': round(float(row.get('sent_smooth', 0)), 3),
            'sent_ma7': round(float(row.get('sent_ma7', 0)), 3),
            'sent_ma30': round(float(row.get('sent_ma30', 0)), 3),
            'sent_macd': round(float(row.get('sent_macd_hist', 0)), 4),
            'sent_trend': str(row.get('sent_trend', 'neutral')),
            'sent_spike': bool(row.get('sent_spike', False)),
            'sent_momentum': round(float(row.get('sent_momentum', 0)), 3),
        }
        
        # 资金特征
        fund_features = {
            'volume_ratio': round(float(row.get('volume_ratio', 1.0)), 2),
            'volume_trend': self._calc_volume_trend(df),
        }
        
        # 近期价格走势 (近5日)
        recent_prices = df['close'].tail(5).tolist()
        price_trend = []
        for i in range(1, len(recent_prices)):
            change = (recent_prices[i] / recent_prices[i-1] - 1) * 100
            price_trend.append(round(change, 2))
        
        return {
            'price': round(price, 2),
            'price_change_pct': round(price_change, 2),
            'date': str(df.index[-1]),
            'technical': tech_features,
            'sentiment': sent_features,
            'fund_flow': fund_features,
            'price_trend_5d': price_trend,
            'has_sentiment_data': bool(row.get('has_sentiment', False)),
        }

    def _llm_decision(
        self, 
        features: Dict[str, Any], 
        df: pd.DataFrame,
        current_position: int
    ) -> Optional[StrategySignal]:
        """调用LLM做交易决策"""
        
        prompt = self._build_llm_prompt(features, current_position)
        
        try:
            # 调用LLM
            loop = asyncio.get_event_loop()
            response = loop.run_until_complete(
                self._call_llm_async(prompt)
            )
            
            if not response:
                return None
            
            # 解析LLM响应
            decision = self._parse_llm_response(response)
            if not decision:
                return None
            
            # 构建StrategySignal
            return self._build_signal_from_llm(decision, features, df)
            
        except Exception as e:
            logger.error(f"[AISentimentV2] LLM调用失败: {e}")
            return None

    async def _call_llm_async(self, prompt: str) -> Optional[str]:
        """异步调用LLM"""
        if not self._llm_client:
            return None
        
        try:
            if hasattr(self._llm_client, 'generate'):
                return await self._llm_client.generate(prompt)
            
            # 直接调用OpenAI格式
            import asyncio
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None,
                lambda: self._llm_client.chat.completions.create(
                    model="kimi-k2.5",
                    messages=[
                        {"role": "system", "content": "你是一位专业的量化交易AI助手。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=800,
                )
            )
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"[AISentimentV2] LLM调用错误: {e}")
            return None

    def _build_llm_prompt(self, features: Dict[str, Any], current_position: int) -> str:
        """构建LLM决策提示词"""
        
        pos_str = {0: "空仓", 1: "持仓", -1: "持空"}.get(current_position, "未知")
        
        prompt = f"""作为量化交易AI，请基于以下多维度数据做出交易决策。

## 当前市场数据

**价格信息**:
- 当前价格: {features['price']}
- 今日涨跌: {features['price_change_pct']}%
- 近期5日涨跌: {features['price_trend_5d']}

**技术指标**:
- RSI(14): {features['technical']['rsi']} (30以下超卖, 70以上超买)
- MACD柱状图: {features['technical']['macd']} (正值看涨, 负值看跌)
- 布林带位置: {features['technical']['bb_position']}
- 均线趋势: {features['technical']['ma_trend']}
- 价格vs20日均线: {features['technical']['price_vs_ma20']}%

**情绪指标** (新闻舆情):
- 当前情绪分: {features['sentiment']['sent_current']} (-1极负, +1极正)
- 7日情绪MA: {features['sentiment']['sent_ma7']}
- 30日情绪MA: {features['sentiment']['sent_ma30']}
- 情绪MACD: {features['sentiment']['sent_macd']} (情绪动量)
- 情绪趋势: {features['sentiment']['sent_trend']}
- 情绪动量(3日): {features['sentiment']['sent_momentum']}
- 是否有情绪数据: {features['has_sentiment_data']}

**资金流向**:
- 量比: {features['fund_flow']['volume_ratio']} (大于1放量, 小于1缩量)
- 量能趋势: {features['fund_flow']['volume_trend']}

**当前持仓状态**: {pos_str}

## 决策要求

请分析上述数据，输出JSON格式的交易决策:

```json
{{
    "decision": "BUY/SELL/HOLD",
    "confidence": 0.0-1.0,
    "position_size": 0.0-1.0,
    "reasoning": "详细分析理由，包括: 1)技术信号解读 2)情绪信号解读 3)风险因素",
    "risk_factors": ["风险1", "风险2"],
    "key_signals": ["关键看涨信号1", "关键看跌信号1"]
}}
```

决策规则:
1. BUY: 技术+情绪+资金三维度共振看涨，或技术面突破+情绪配合
2. SELL: 出现明显卖出信号(如情绪急转直下+技术破位)，或止损触发
3. HOLD: 信号不明显，或趋势不明朗时观望
4. confidence应反映你的确定程度
5. position_size建议仓位比例 (0.1-0.5为宜)

请只输出JSON，不要其他内容。"""
        
        return prompt

    def _parse_llm_response(self, response: str) -> Optional[Dict[str, Any]]:
        """解析LLM响应"""
        try:
            # 提取JSON部分
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start == -1 or json_end == 0:
                return None
            
            json_str = response[json_start:json_end]
            decision = json.loads(json_str)
            
            # 验证必要字段
            required = ['decision', 'confidence', 'reasoning']
            for field in required:
                if field not in decision:
                    logger.warning(f"[AISentimentV2] LLM响应缺少字段: {field}")
                    return None
            
            return decision
            
        except json.JSONDecodeError as e:
            logger.error(f"[AISentimentV2] JSON解析失败: {e}")
            return None

    def _build_signal_from_llm(
        self, 
        decision: Dict[str, Any], 
        features: Dict[str, Any],
        df: pd.DataFrame
    ) -> StrategySignal:
        """从LLM决策构建StrategySignal"""
        
        row = df.iloc[-1]
        price = float(row['close'])
        
        # 映射决策到SignalType
        decision_map = {
            'BUY': SignalType.BUY,
            'STRONG_BUY': SignalType.STRONG_BUY,
            'SELL': SignalType.SELL,
            'STRONG_SELL': SignalType.STRONG_SELL,
            'HOLD': SignalType.HOLD,
        }
        sig_type = decision_map.get(decision['decision'].upper(), SignalType.HOLD)
        
        # 计算止损止盈
        is_buy = sig_type in (SignalType.BUY, SignalType.STRONG_BUY)
        stop_loss = round(price * (1 - self.risk_params['stop_loss_pct']), 2) if is_buy else 0
        target_price = round(price * (1 + self.risk_params['take_profit_pct']), 2) if is_buy else 0
        
        # 仓位大小
        position_size = min(decision.get('position_size', 0.2), self.risk_params['max_position_pct'])
        
        # 置信度
        confidence = min(decision.get('confidence', 0.5), 0.95)
        
        # 构建理由
        reasons = [
            f"🤖 AI决策: {decision['decision']}",
        ]
        
        # 添加关键信号
        key_signals = decision.get('key_signals', [])
        if key_signals:
            reasons.extend(key_signals[:2])
        
        # 添加风险因素
        risk_factors = decision.get('risk_factors', [])
        if risk_factors:
            reasons.append(f"⚠️ 风险: {risk_factors[0]}")
        
        # 添加AI推理摘要
        reasoning = decision.get('reasoning', '')
        if len(reasoning) > 100:
            reasoning = reasoning[:100] + "..."
        reasons.append(f"💡 AI分析: {reasoning}")
        
        return StrategySignal(
            signal_type=sig_type,
            confidence=round(confidence, 3),
            strength=round(position_size * 2, 3),  # 仓位*2作为强度
            price=round(price, 2),
            stop_loss=stop_loss,
            target_price=target_price,
            position_size=position_size if is_buy else 0,
            reasons=reasons[:6],
            strategy_id="ai_sentiment_v2",
            strategy_name=self.name,
            metadata={
                'llm_decision': decision['decision'],
                'llm_confidence': confidence,
                'features': features,
            }
        )

    # ------------------------------------------------------------------
    # 辅助计算方法
    # ------------------------------------------------------------------

    def _calc_bb_position(self, row: pd.Series) -> str:
        """计算布林带位置"""
        close = float(row.get('close', 0))
        upper = float(row.get('bb_upper', close))
        lower = float(row.get('bb_lower', close))
        middle = float(row.get('bb_middle', close))
        
        if close >= upper:
            return "上轨(超买)"
        elif close <= lower:
            return "下轨(超卖)"
        elif close > middle:
            return "上半轨"
        else:
            return "下半轨"

    def _calc_ma_trend(self, df: pd.DataFrame) -> str:
        """计算均线趋势"""
        if len(df) < 2:
            return "unknown"
        
        row = df.iloc[-1]
        ma5 = row.get('ma_5', 0)
        ma20 = row.get('ma_20', 0)
        ma60 = row.get('ma_60', 0)
        
        if ma5 > ma20 > ma60:
            return "多头排列"
        elif ma5 < ma20 < ma60:
            return "空头排列"
        elif ma5 > ma20:
            return "短期走强"
        else:
            return "短期走弱"

    def _calc_volume_trend(self, df: pd.DataFrame) -> str:
        """计算量能趋势"""
        if len(df) < 5:
            return "unknown"
        
        recent_vol = df['volume'].tail(5).mean()
        prev_vol = df['volume'].tail(10).head(5).mean()
        
        ratio = recent_vol / prev_vol if prev_vol > 0 else 1
        
        if ratio > 1.5:
            return "明显放量"
        elif ratio > 1.2:
            return "温和放量"
        elif ratio < 0.8:
            return "缩量"
        else:
            return "量平"

    def _hold_signal(self, reason: str) -> StrategySignal:
        """生成HOLD信号"""
        return StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.5,
            strength=0.0,
            price=0.0,
            stop_loss=0.0,
            target_price=0.0,
            position_size=0.0,
            reasons=[f"观望: {reason}"],
            strategy_id="ai_sentiment_v2",
            strategy_name=self.name,
        )
