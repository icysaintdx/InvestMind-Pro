"""
三叉戟策略 (Trident Strategy)
结合趋势、动量和波动率的综合策略
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .base import BaseStrategy, StrategySignal, SignalType, StrategyConfig, register_strategy


@register_strategy("trident")
class TridentStrategy(BaseStrategy):
    """
    三叉戟策略
    
    三个维度：
    1. 趋势叉（Trend Fork）：使用EMA判断趋势方向
    2. 动量叉（Momentum Fork）：使用RSI和MACD判断动量
    3. 波动叉（Volatility Fork）：使用ATR和布林带判断波动
    
    只有三个维度都确认时才发出信号
    """
    
    # 添加策略描述属性
    description = "结合趋势、动量和波动率的综合策略，三个维度共振时发出信号"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "三叉戟综合策略"
        self.category = "综合"
        
        # 策略参数
        self.params = {
            # 趋势参数
            "ema_fast": 12,
            "ema_slow": 26,
            # 动量参数
            "rsi_period": 14,
            "rsi_overbought": 70,
            "rsi_oversold": 30,
            "macd_fast": 12,
            "macd_slow": 26,
            "macd_signal": 9,
            # 波动参数
            "atr_period": 14,
            "bb_period": 20,
            "bb_std": 2.0,
            # 确认参数
            "min_forks": 3,  # 最少需要几个叉确认
        }
        
        # 风险参数
        self.risk_params = {
            "max_position_pct": 0.35,
            "stop_loss_pct": 0.04,
            "take_profit_pct": 0.12,
            "max_drawdown_pct": 0.10
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        # 1. 趋势指标
        df['ema_fast'] = df['close'].ewm(span=self.params['ema_fast']).mean()
        df['ema_slow'] = df['close'].ewm(span=self.params['ema_slow']).mean()
        df['trend_fork'] = (df['ema_fast'] > df['ema_slow']).astype(int)  # 1=上升趋势, 0=下降趋势
        
        # 2. 动量指标
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
        
        # 动量叉：RSI不在超买超卖区 且 MACD柱状图为正
        df['momentum_fork'] = (
            (df['rsi'] > self.params['rsi_oversold']) &
            (df['rsi'] < self.params['rsi_overbought']) &
            (df['macd_hist'] > 0)
        ).astype(int)
        
        # 3. 波动指标
        # ATR
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        ranges = pd.concat([high_low, high_close, low_close], axis=1)
        true_range = ranges.max(axis=1)
        df['atr'] = true_range.rolling(window=self.params['atr_period']).mean()
        
        # 布林带
        df['bb_mid'] = df['close'].rolling(window=self.params['bb_period']).mean()
        df['bb_std'] = df['close'].rolling(window=self.params['bb_period']).std()
        df['bb_upper'] = df['bb_mid'] + (df['bb_std'] * self.params['bb_std'])
        df['bb_lower'] = df['bb_mid'] - (df['bb_std'] * self.params['bb_std'])
        df['bb_width'] = (df['bb_upper'] - df['bb_lower']) / df['bb_mid']
        
        # 波动叉：价格在布林带中轨附近 且 带宽适中
        df['volatility_fork'] = (
            (df['close'] > df['bb_lower']) &
            (df['close'] < df['bb_upper']) &
            (df['bb_width'] > 0.02) &  # 带宽不能太窄
            (df['bb_width'] < 0.15)    # 带宽不能太宽
        ).astype(int)
        
        # 三叉戟总分
        df['trident_score'] = df['trend_fork'] + df['momentum_fork'] + df['volatility_fork']
        
        return df
    
    def initialize(self, data: pd.DataFrame) -> None:
        """初始化策略（计算指标等）"""
        self._initialized = True
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> StrategySignal:
        """生成交易信号（新接口）"""
        # 计算指标
        df = self.calculate_indicators(data)
        
        if len(df) < self.params.get('bb_period', 20):
            return StrategySignal(
                signal_type=SignalType.HOLD,
                confidence=0.0,
                strength=0.0,
                reasons=["数据不足"]
            )
        
        # 获取最后一行
        row = df.iloc[-1]
        price = row['close']
        
        # 计算三叉戟得分
        trident_score = row.get('trident_score', 0)
        
        # 根据得分生成信号
        if trident_score >= 2.5:  # 三个维度共振买入
            signal_type = SignalType.STRONG_BUY if trident_score >= 2.8 else SignalType.BUY
            confidence = min(trident_score / 3.0, 1.0)
            reasons = [
                f"三叉戟共振得分: {trident_score:.2f}",
                f"趋势得分: {row.get('trend_fork', 0):.2f}",
                f"动量得分: {row.get('momentum_fork', 0):.2f}",
                f"波动率得分: {row.get('volatility_fork', 0):.2f}"
            ]
        elif trident_score <= -2.5:  # 三个维度共振卖出
            signal_type = SignalType.STRONG_SELL if trident_score <= -2.8 else SignalType.SELL
            confidence = min(abs(trident_score) / 3.0, 1.0)
            reasons = [
                f"三叉戟反向得分: {trident_score:.2f}",
                "趋势、动量、波动率共振看空"
            ]
        else:
            signal_type = SignalType.HOLD
            confidence = 0.5
            reasons = [f"三叉戟得分未达门槛: {trident_score:.2f}"]
        
        return StrategySignal(
            signal_type=signal_type,
            confidence=confidence,
            strength=min(abs(trident_score) / 3.0, 1.0),
            price=price,
            stop_loss=price * 0.95 if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else None,
            target_price=price * 1.10 if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else None,
            position_size=0.3 if signal_type in [SignalType.BUY, SignalType.STRONG_BUY] else 0,
            reasons=reasons[:5],
            strategy_id="trident",
            strategy_name=self.name
        )
    
    def _generate_signals_legacy(self, data: pd.DataFrame) -> List[StrategySignal]:
        """生成交易信号"""
        df = self.calculate_indicators(data)
        signals = []
        
        for i in range(len(df)):
            if i < self.params['bb_period']:  # 确保指标已计算
                continue
            
            row = df.iloc[i]
            prev_row = df.iloc[i-1] if i > 0 else None
            
            # 买入信号：三叉戟得分达到最低要求
            if row['trident_score'] >= self.params['min_forks']:
                # 检查是否是新信号（前一根K线得分不足）
                if prev_row is None or prev_row['trident_score'] < self.params['min_forks']:
                    # 计算信号强度（基于三叉戟得分）
                    strength = row['trident_score'] / 3.0
                    
                    # 计算置信度
                    confidence = self._calculate_confidence(row)
                    
                    # 计算目标价和止损价
                    current_price = row['close']
                    atr = row['atr']
                    
                    target_price = current_price + (atr * 3)  # 3倍ATR作为目标
                    stop_loss = current_price - (atr * 1.5)   # 1.5倍ATR作为止损
                    
                    # 计算仓位大小
                    position_size = self._calculate_position_size(
                        current_price,
                        stop_loss,
                        confidence
                    )
                    
                    # 生成信号原因
                    reasons = self._generate_reasons(row)
                    
                    signal = Signal(
                        strategy_id="trident",
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
            
            # 卖出信号：三叉戟得分低于阈值
            elif row['trident_score'] < 2:
                if prev_row is not None and prev_row['trident_score'] >= 2:
                    signal = Signal(
                        strategy_id="trident",
                        strategy_name=self.name,
                        signal_type=SignalType.SELL,
                        strength=0.8,
                        confidence=0.7,
                        reasons=["三叉戟信号减弱，建议减仓或止盈"],
                        timestamp=df.index[i]
                    )
                    
                    signals.append(signal)
        
        return signals
    
    def _calculate_confidence(self, row: pd.Series) -> float:
        """计算信号置信度"""
        confidence = 0.5  # 基础置信度
        
        # 趋势叉加分
        if row['trend_fork'] == 1:
            confidence += 0.15
        
        # 动量叉加分
        if row['momentum_fork'] == 1:
            confidence += 0.15
        
        # 波动叉加分
        if row['volatility_fork'] == 1:
            confidence += 0.15
        
        # RSI位置加分
        if 40 < row['rsi'] < 60:
            confidence += 0.05
        
        return min(confidence, 0.95)
    
    def _calculate_position_size(
        self,
        current_price: float,
        stop_loss: float,
        confidence: float
    ) -> float:
        """计算仓位大小"""
        # 基于风险和置信度计算仓位
        risk_per_trade = 0.02  # 每次交易风险2%
        price_risk = (current_price - stop_loss) / current_price
        
        if price_risk <= 0:
            return 0.0
        
        position = (risk_per_trade / price_risk) * confidence
        
        # 限制最大仓位
        max_position = self.risk_params['max_position_pct']
        return min(position, max_position)
    
    def _generate_reasons(self, row: pd.Series) -> List[str]:
        """生成信号原因"""
        reasons = []
        
        if row['trend_fork'] == 1:
            reasons.append(f"✓ 趋势叉：快线({row['ema_fast']:.2f})高于慢线({row['ema_slow']:.2f})，上升趋势确认")
        
        if row['momentum_fork'] == 1:
            reasons.append(f"✓ 动量叉：RSI={row['rsi']:.1f}，MACD柱状图为正，动量良好")
        
        if row['volatility_fork'] == 1:
            reasons.append(f"✓ 波动叉：价格在布林带内，波动率适中（带宽={row['bb_width']:.2%}）")
        
        reasons.append(f"三叉戟得分：{row['trident_score']}/3")
        
        return reasons
    
    def get_required_indicators(self) -> List[str]:
        """获取所需的技术指标"""
        return [
            'ema_fast', 'ema_slow',
            'rsi', 'macd', 'macd_signal', 'macd_hist',
            'atr', 'bb_upper', 'bb_mid', 'bb_lower',
            'trend_fork', 'momentum_fork', 'volatility_fork',
            'trident_score'
        ]
