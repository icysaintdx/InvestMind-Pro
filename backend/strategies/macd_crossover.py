"""
MACD交叉策略
经典的MACD金叉死叉策略，结合成交量确认
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .base import BaseStrategy, StrategySignal, SignalType, StrategyConfig, register_strategy

# 兼容旧代码
Signal = StrategySignal


@register_strategy("macd_crossover")
class MACDCrossoverStrategy(BaseStrategy):
    """
    MACD交叉策略
    
    信号规则：
    1. 金叉（MACD线上穿信号线）：买入信号
    2. 死叉（MACD线下穿信号线）：卖出信号
    3. 结合成交量确认：放量突破更可靠
    4. 结合零轴位置：零轴上方金叉更强
    """
    
    # 添加策略描述属性
    description = "经典的MACD金叉死叉策略，结合成交量确认，适合趋势性股票"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "MACD金叉死叉策略"
        self.category = "技术分析"
        
        # 策略参数
        self.params = {
            "fast_period": 12,
            "slow_period": 26,
            "signal_period": 9,
            "volume_ma_period": 20,
            "volume_threshold": 1.2,  # 成交量放大倍数
            "use_volume_confirm": True,
            "use_zero_line": True  # 是否考虑零轴位置
        }
        
        # 风险参数
        self.risk_params = {
            "max_position_pct": 0.40,
            "stop_loss_pct": 0.04,
            "take_profit_pct": 0.10,
            "max_drawdown_pct": 0.12
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        # MACD指标
        ema_fast = df['close'].ewm(span=self.params['fast_period']).mean()
        ema_slow = df['close'].ewm(span=self.params['slow_period']).mean()
        
        df['macd'] = ema_fast - ema_slow
        df['macd_signal'] = df['macd'].ewm(span=self.params['signal_period']).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 成交量指标
        df['volume_ma'] = df['volume'].rolling(window=self.params['volume_ma_period']).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # 识别金叉和死叉
        df['macd_cross'] = 0
        df.loc[(df['macd'] > df['macd_signal']) & 
               (df['macd'].shift(1) <= df['macd_signal'].shift(1)), 'macd_cross'] = 1  # 金叉
        df.loc[(df['macd'] < df['macd_signal']) & 
               (df['macd'].shift(1) >= df['macd_signal'].shift(1)), 'macd_cross'] = -1  # 死叉
        
        # MACD与零轴的关系
        df['macd_above_zero'] = (df['macd'] > 0).astype(int)
        
        return df
    
    def initialize(self, data: pd.DataFrame) -> None:
        """初始化策略"""
        self._initialized = True
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> StrategySignal:
        """生成交易信号（新接口）"""
        df = self.calculate_indicators(data)
        
        if len(df) < self.params['slow_period'] + self.params['signal_period']:
            return StrategySignal(
                signal_type=SignalType.HOLD,
                confidence=0.0,
                strength=0.0,
                reasons=["数据不足"],
                strategy_id="macd_crossover",
                strategy_name=self.name
            )
        
        row = df.iloc[-1]
        prev_row = df.iloc[-2]
        price = row['close']
        
        signal_type = SignalType.HOLD
        confidence = 0.5
        reasons = []
        
        # MACD金叉
        macd_cross_up = (row['macd'] > row['macd_signal']) and (prev_row['macd'] <= prev_row['macd_signal'])
        # MACD死叉
        macd_cross_down = (row['macd'] < row['macd_signal']) and (prev_row['macd'] >= prev_row['macd_signal'])
        
        if macd_cross_up:
            # 金叉
            on_zero_line = row['macd'] > 0 if self.params['use_zero_line'] else True
            volume_confirmed = row.get('volume_ratio', 0) > self.params['volume_threshold']
            
            if on_zero_line:
                signal_type = SignalType.STRONG_BUY if volume_confirmed else SignalType.BUY
                confidence = 0.85 if volume_confirmed else 0.7
                reasons = [
                    "MACD金叉信号",
                    f"MACD在零轴{'u4e0a' if row['macd'] > 0 else 'u4e0b'}方",
                    f"成交量放大" if volume_confirmed else "金叉确认"
                ]
            else:
                signal_type = SignalType.BUY
                confidence = 0.6
                reasons = ["MACD金叉，但在零轴下方"]
        
        elif macd_cross_down:
            # 死叉
            signal_type = SignalType.SELL
            confidence = 0.75
            reasons = [
                "MACD死叉信号",
                f"MACD: {row['macd']:.4f}",
                f"Signal: {row['macd_signal']:.4f}"
            ]
        
        return StrategySignal(
            signal_type=signal_type,
            confidence=confidence,
            strength=min(abs(row.get('macd', 0)) / 0.1, 1.0),
            price=price,
            stop_loss=price * 0.96 if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else None,
            target_price=price * 1.10 if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else None,
            position_size=0.40 if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else 0,
            reasons=reasons[:5],
            strategy_id="macd_crossover",
            strategy_name=self.name
        )
    
    def _generate_signals_legacy(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信号"""
        df = self.calculate_indicators(data)
        signals = []
        
        for i in range(len(df)):
            if i < self.params['slow_period']:  # 确保指标已计算
                continue
            
            row = df.iloc[i]
            
            # 买入信号：金叉
            if row['macd_cross'] == 1:
                # 成交量确认
                volume_confirmed = True
                if self.params['use_volume_confirm']:
                    volume_confirmed = row['volume_ratio'] >= self.params['volume_threshold']
                
                # 零轴位置加分
                above_zero = row['macd_above_zero'] == 1
                
                # 计算信号强度
                strength = 0.7
                if above_zero:
                    strength += 0.2  # 零轴上方金叉更强
                if volume_confirmed:
                    strength += 0.1  # 放量确认加分
                
                # 计算置信度
                confidence = self._calculate_confidence(row, volume_confirmed, above_zero)
                
                # 计算目标价和止损价
                current_price = row['close']
                hist_abs = abs(row['macd_hist'])
                
                target_price = current_price * (1 + self.risk_params['take_profit_pct'])
                stop_loss = current_price * (1 - self.risk_params['stop_loss_pct'])
                
                # 计算仓位大小
                position_size = self._calculate_position_size(confidence)
                
                # 生成信号原因
                reasons = self._generate_buy_reasons(row, volume_confirmed, above_zero)
                
                signal = Signal(
                    strategy_id="macd_crossover",
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
            
            # 卖出信号：死叉
            elif row['macd_cross'] == -1:
                # 成交量确认
                volume_confirmed = True
                if self.params['use_volume_confirm']:
                    volume_confirmed = row['volume_ratio'] >= self.params['volume_threshold']
                
                strength = 0.8 if volume_confirmed else 0.6
                confidence = 0.75 if volume_confirmed else 0.6
                
                reasons = self._generate_sell_reasons(row, volume_confirmed)
                
                signal = Signal(
                    strategy_id="macd_crossover",
                    strategy_name=self.name,
                    signal_type=SignalType.SELL,
                    strength=strength,
                    confidence=confidence,
                    reasons=reasons,
                    timestamp=df.index[i]
                )
                
                signals.append(signal)
        
        return signals
    
    def _calculate_confidence(
        self,
        row: pd.Series,
        volume_confirmed: bool,
        above_zero: bool
    ) -> float:
        """计算信号置信度"""
        confidence = 0.6  # 基础置信度
        
        # 零轴上方加分
        if above_zero:
            confidence += 0.15
        
        # 成交量确认加分
        if volume_confirmed:
            confidence += 0.10
        
        # MACD柱状图强度加分
        if abs(row['macd_hist']) > 0.5:
            confidence += 0.10
        
        return min(confidence, 0.95)
    
    def _calculate_position_size(self, confidence: float) -> float:
        """计算仓位大小"""
        # 基于置信度调整仓位
        base_position = self.risk_params['max_position_pct']
        return base_position * confidence
    
    def _generate_buy_reasons(
        self,
        row: pd.Series,
        volume_confirmed: bool,
        above_zero: bool
    ) -> List[str]:
        """生成买入信号原因"""
        reasons = []
        
        reasons.append(f"✓ MACD金叉：MACD线({row['macd']:.3f})上穿信号线({row['macd_signal']:.3f})")
        
        if above_zero:
            reasons.append("✓ 零轴上方金叉，趋势强劲")
        else:
            reasons.append("⚠ 零轴下方金叉，谨慎看待")
        
        if volume_confirmed:
            reasons.append(f"✓ 成交量放大{row['volume_ratio']:.1f}倍，突破有效")
        else:
            reasons.append("⚠ 成交量未明显放大")
        
        reasons.append(f"MACD柱状图：{row['macd_hist']:.3f}")
        
        return reasons
    
    def _generate_sell_reasons(
        self,
        row: pd.Series,
        volume_confirmed: bool
    ) -> List[str]:
        """生成卖出信号原因"""
        reasons = []
        
        reasons.append(f"✗ MACD死叉：MACD线({row['macd']:.3f})下穿信号线({row['macd_signal']:.3f})")
        
        if volume_confirmed:
            reasons.append(f"✗ 成交量放大{row['volume_ratio']:.1f}倍，下跌压力大")
        
        reasons.append(f"MACD柱状图：{row['macd_hist']:.3f}")
        
        return reasons
    
    def get_required_indicators(self) -> List[str]:
        """获取所需的技术指标"""
        return [
            'macd',
            'macd_signal',
            'macd_hist',
            'macd_cross',
            'macd_above_zero',
            'volume_ma',
            'volume_ratio'
        ]
