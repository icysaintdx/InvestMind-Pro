"""
布林带突破策略
基于布林带的突破和回归策略
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .base import BaseStrategy, StrategySignal, SignalType, StrategyConfig, register_strategy

# 兼容旧代码：将Signal指向StrategySignal
Signal = StrategySignal


@register_strategy("bollinger_breakout")
class BollingerBreakoutStrategy(BaseStrategy):
    """
    布林带突破策略
    
    信号规则：
    1. 价格突破上轨：强势突破，买入信号
    2. 价格跌破下轨：超跌反弹，买入信号
    3. 价格从上轨回落：卖出信号
    4. 带宽收窄后突破：更可靠的信号
    """
    
    # 添加策略描述属性
    description = "基于布林带的突破和回归策略，适合波动市场"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "布林带突破策略"
        self.category = "技术分析"
        
        # 策略参数
        self.params = {
            "bb_period": 20,
            "bb_std": 2.0,
            "squeeze_threshold": 0.05,  # 带宽收窄阈值
            "volume_ma_period": 20,
            "volume_threshold": 1.3,
            "use_volume_confirm": True
        }
        
        # 风险参数
        self.risk_params = {
            "max_position_pct": 0.35,
            "stop_loss_pct": 0.05,
            "take_profit_pct": 0.12,
            "max_drawdown_pct": 0.10
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        # 布林带
        df['bb_mid'] = df['close'].rolling(window=self.params['bb_period']).mean()
        df['bb_std'] = df['close'].rolling(window=self.params['bb_period']).std()
        df['bb_upper'] = df['bb_mid'] + (df['bb_std'] * self.params['bb_std'])
        df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * self.params['bb_std'])
        
        # 布林带宽度（标准化）
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        
        # 价格在布林带中的位置（%B指标）
        df['bb_position'] = (df['close'] - df['bb_lower']) / (df['bb_upper'] - df['bb_lower'])
        
        # 带宽收窄（Squeeze）
        df['bb_squeeze'] = df['bb_width'] < self.params['squeeze_threshold']
        
        # 成交量
        df['volume_ma'] = df['volume'].rolling(window=self.params['volume_ma_period']).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # 识别突破
        df['upper_breakout'] = (df['close'] > df['bb_upper']) & (df['close'].shift(1) <= df['bb_upper'].shift(1))
        df['lower_breakout'] = (df['close'] < df['bb_lower']) & (df['close'].shift(1) >= df['bb_lower'].shift(1))
        
        return df
    
    def initialize(self, data: pd.DataFrame) -> None:
        """初始化策略"""
        self._initialized = True
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> StrategySignal:
        """生成交易信号（新接口）"""
        df = self.calculate_indicators(data)
        
        if len(df) < self.params['bb_period']:
            return StrategySignal(
                signal_type=SignalType.HOLD,
                confidence=0.0,
                strength=0.0,
                reasons=["数据不足"],
                strategy_id="bollinger_breakout",
                strategy_name=self.name
            )
        
        row = df.iloc[-1]
        price = row['close']
        
        # 布林带突破策略
        signal_type = SignalType.HOLD
        confidence = 0.5
        reasons = []
        
        # 上轨突破（强势）
        if row.get('upper_breakout', False):
            volume_confirmed = row.get('volume_ratio', 0) > self.params['volume_threshold']
            if volume_confirmed or not self.params['use_volume_confirm']:
                signal_type = SignalType.STRONG_BUY if volume_confirmed else SignalType.BUY
                confidence = 0.8 if volume_confirmed else 0.6
                reasons = [
                    f"价格突破上轨: {price:.2f} > {row['bb_upper']:.2f}",
                    f"成交量放大: {row.get('volume_ratio', 0):.2f}x" if volume_confirmed else "突破确认"
                ]
        # 下轨突破（超跌反弹）
        elif row.get('lower_breakout', False):
            signal_type = SignalType.BUY
            confidence = 0.65
            reasons = [
                f"价格跌破下轨: {price:.2f} < {row['bb_lower']:.2f}",
                "超跌反弹机会"
            ]
        # 价格从上轨回落
        elif row.get('bb_position', 0.5) > 0.9 and current_position > 0:
            signal_type = SignalType.SELL
            confidence = 0.7
            reasons = [
                f"价格达到上轨附近，回落风险",
                f"布林带位置: {row.get('bb_position', 0)*100:.1f}%"
            ]
        
        return StrategySignal(
            signal_type=signal_type,
            confidence=confidence,
            strength=min(abs(row.get('bb_position', 0.5) - 0.5) * 2, 1.0),
            price=price,
            stop_loss=price * 0.95 if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else None,
            target_price=price * 1.12 if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else None,
            position_size=0.35 if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else 0,
            reasons=reasons[:5],
            strategy_id="bollinger_breakout",
            strategy_name=self.name
        )
    
    def _generate_signals_legacy(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信号"""
        df = self.calculate_indicators(data)
        signals = []
        
        for i in range(len(df)):
            if i < self.params['bb_period']:
                continue
            
            row = df.iloc[i]
            prev_row = df.iloc[i-1] if i > 0 else None
            
            # 买入信号1：突破上轨（强势突破）
            if row['upper_breakout']:
                volume_confirmed = True
                if self.params['use_volume_confirm']:
                    volume_confirmed = row['volume_ratio'] >= self.params['volume_threshold']
                
                # 检查是否有带宽收窄
                squeeze = prev_row['bb_squeeze'] if prev_row is not None else False
                
                strength = 0.8
                if squeeze:
                    strength += 0.15  # 收窄后突破更强
                if volume_confirmed:
                    strength += 0.05
                
                confidence = self._calculate_confidence(row, volume_confirmed, squeeze, "upper")
                
                current_price = row['close']
                bb_width_price = row['bb_upper'] - row['bb_lower']
                
                target_price = current_price + bb_width_price * 0.5
                stop_loss = row['bb_mid']
                
                position_size = self._calculate_position_size(confidence)
                
                reasons = self._generate_upper_breakout_reasons(row, volume_confirmed, squeeze)
                
                signal = Signal(
                    strategy_id="bollinger_breakout",
                    strategy_name=self.name,
                    signal_type=SignalType.BUY,
                    strength=min(strength, 1.0),
                    confidence=confidence,
                    target_price=target_price,
                    stop_loss=stop_loss,
                    position_size=position_size,
                    reasons=reasons,
                    timestamp=df.index[i]
                )
                
                signals.append(signal)
            
            # 买入信号2：跌破下轨（超跌反弹）
            elif row['lower_breakout']:
                volume_confirmed = True
                if self.params['use_volume_confirm']:
                    volume_confirmed = row['volume_ratio'] >= self.params['volume_threshold']
                
                strength = 0.7
                confidence = self._calculate_confidence(row, volume_confirmed, False, "lower")
                
                current_price = row['close']
                
                target_price = row['bb_mid']
                stop_loss = current_price * (1 - self.risk_params['stop_loss_pct'])
                
                position_size = self._calculate_position_size(confidence) * 0.8  # 超跌反弹仓位略小
                
                reasons = self._generate_lower_breakout_reasons(row, volume_confirmed)
                
                signal = Signal(
                    strategy_id="bollinger_breakout",
                    strategy_name=self.name,
                    signal_type=SignalType.BUY,
                    strength=strength,
                    confidence=confidence,
                    target_price=target_price,
                    stop_loss=stop_loss,
                    position_size=position_size,
                    reasons=reasons,
                    timestamp=df.index[i]
                )
                
                signals.append(signal)
            
            # 卖出信号：价格从上轨回落
            elif prev_row is not None and prev_row['bb_position'] > 0.9 and row['bb_position'] < 0.9:
                reasons = [
                    f"✗ 价格从上轨回落，当前位置{row['bb_position']:.1%}",
                    f"布林带宽度：{row['bb_width']:.2%}",
                    "建议止盈或减仓"
                ]
                
                signal = Signal(
                    strategy_id="bollinger_breakout",
                    strategy_name=self.name,
                    signal_type=SignalType.SELL,
                    strength=0.7,
                    confidence=0.7,
                    reasons=reasons,
                    timestamp=df.index[i]
                )
                
                signals.append(signal)
        
        return signals
    
    def _calculate_confidence(
        self,
        row: pd.Series,
        volume_confirmed: bool,
        squeeze: bool,
        breakout_type: str
    ) -> float:
        """计算信号置信度"""
        confidence = 0.6
        
        if breakout_type == "upper":
            # 上轨突破
            if squeeze:
                confidence += 0.15  # 收窄后突破
            if volume_confirmed:
                confidence += 0.10
            if row['bb_width'] > 0.08:
                confidence += 0.05  # 带宽较宽，空间大
        else:
            # 下轨突破（超跌）
            if volume_confirmed:
                confidence += 0.10
            if row['bb_position'] < 0.1:
                confidence += 0.10  # 严重超跌
        
        return min(confidence, 0.90)
    
    def _calculate_position_size(self, confidence: float) -> float:
        """计算仓位大小"""
        base_position = self.risk_params['max_position_pct']
        return base_position * confidence
    
    def _generate_upper_breakout_reasons(
        self,
        row: pd.Series,
        volume_confirmed: bool,
        squeeze: bool
    ) -> List[str]:
        """生成上轨突破信号原因"""
        reasons = []
        
        reasons.append(f"✓ 突破上轨：价格{row['close']:.2f} > 上轨{row['bb_upper']:.2f}")
        
        if squeeze:
            reasons.append("✓ 带宽收窄后突破，信号更可靠")
        
        if volume_confirmed:
            reasons.append(f"✓ 成交量放大{row['volume_ratio']:.1f}倍")
        
        reasons.append(f"布林带位置：{row['bb_position']:.1%}")
        reasons.append(f"带宽：{row['bb_width']:.2%}")
        
        return reasons
    
    def _generate_lower_breakout_reasons(
        self,
        row: pd.Series,
        volume_confirmed: bool
    ) -> List[str]:
        """生成下轨突破信号原因"""
        reasons = []
        
        reasons.append(f"✓ 跌破下轨：价格{row['close']:.2f} < 下轨{row['bb_lower']:.2f}")
        reasons.append("超跌反弹机会")
        
        if volume_confirmed:
            reasons.append(f"✓ 恐慌性抛售，成交量{row['volume_ratio']:.1f}倍")
        
        reasons.append(f"布林带位置：{row['bb_position']:.1%}")
        reasons.append(f"目标：回归中轨{row['bb_mid']:.2f}")
        
        return reasons
    
    def get_required_indicators(self) -> List[str]:
        """获取所需的技术指标"""
        return [
            'bb_upper',
            'bb_mid',
            'bb_lower',
            'bb_width',
            'bb_position',
            'bb_squeeze',
            'volume_ma',
            'volume_ratio',
            'upper_breakout',
            'lower_breakout'
        ]
