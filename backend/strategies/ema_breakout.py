"""
均线突破策略
三均线或四均线系统，适合强势股
"""

import pandas as pd
import numpy as np
from typing import Optional
from .base import (
    BaseStrategy,
    StrategySignal,
    SignalType,
    StrategyConfig,
    register_strategy
)


@register_strategy("ema_breakout")
class EMABreakoutStrategy(BaseStrategy):
    """
    均线突破策略
    
    交易逻辑：
    1. 短中长期均线多头排列
    2. 价格突破短期均线买入
    3. 成交量确认（放量突破）
    4. 均线支撑位止损
    
    参数：
    - ema_short: 短期均线（默认5）
    - ema_mid1: 中期均线1（默认9）
    - ema_mid2: 中期均线2（默认13）
    - ema_long: 长期均线（默认21）
    - volume_multiplier: 成交量倍数（默认1.5）
    """
    
        
    # 策略描述属性
    description = "基于EMA均线突破的短期交易策略，适合波动较大的股票"
        
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
            
        # 设置中文名称
        self.name = "EMA均线突破策略"
        self.category = "技术分析"
        
        # 策略参数
        self.ema_short = self.parameters.get('ema_short', 5)
        self.ema_mid1 = self.parameters.get('ema_mid1', 9)
        self.ema_mid2 = self.parameters.get('ema_mid2', 13)
        self.ema_long = self.parameters.get('ema_long', 21)
        self.volume_multiplier = self.parameters.get('volume_multiplier', 1.5)
        self.use_volume_confirm = self.parameters.get('use_volume_confirm', True)
        
        # 内部状态
        self._last_signal = None
        self._entry_price = 0

    def initialize(self, data: pd.DataFrame) -> None:
        """初始化策略，计算所需指标"""
        if not self.validate_data(data):
            raise ValueError("数据格式不正确")
        
        # 计算 EMA
        data[f'ema_{self.ema_short}'] = data['close'].ewm(span=self.ema_short).mean()
        data[f'ema_{self.ema_mid1}'] = data['close'].ewm(span=self.ema_mid1).mean()
        data[f'ema_{self.ema_mid2}'] = data['close'].ewm(span=self.ema_mid2).mean()
        data[f'ema_{self.ema_long}'] = data['close'].ewm(span=self.ema_long).mean()
        
        # 计算成交量移动平均
        data['volume_ma'] = data['volume'].rolling(window=20).mean()
        data['volume_ratio'] = data['volume'] / data['volume_ma']
        
        # 计算均线排列强度
        data['ema_alignment'] = self._calculate_alignment(data)
        
        # 计算RSI（辅助指标）
        data['rsi'] = self._calculate_rsi(data['close'], 14)
        
        self._initialized = True

    def generate_signal(
        self,
        data: pd.DataFrame,
        current_position: int = 0
    ) -> StrategySignal:
        """生成交易信号"""
        if not self._initialized:
            self.initialize(data)
        
        # 获取最新数据
        latest = data.iloc[-1]
        prev = data.iloc[-2] if len(data) > 1 else latest
        
        price = latest['close']
        ema_s = latest[f'ema_{self.ema_short}']
        ema_m1 = latest[f'ema_{self.ema_mid1}']
        ema_m2 = latest[f'ema_{self.ema_mid2}']
        ema_l = latest[f'ema_{self.ema_long}']
        volume_ratio = latest['volume_ratio']
        rsi = latest['rsi']
        alignment = latest['ema_alignment']
        
        # 默认信号
        signal = StrategySignal(
            signal_type=SignalType.HOLD,
            price=price,
            confidence=0.3
        )
        
        # 成交量确认
        volume_confirm = volume_ratio > self.volume_multiplier if self.use_volume_confirm else True
        
        # 买入信号
        if current_position <= 0:
            # 条件1：完美多头排列
            bullish_alignment = (ema_s > ema_m1 > ema_m2 > ema_l)
            
            # 条件2：价格突破短期均线
            price_breakout = (price > ema_s and prev['close'] <= prev[f'ema_{self.ema_short}'])
            
            # 条件3：短期均线向上穿越中期均线
            ema_crossover = (ema_s > ema_m1 and 
                            prev[f'ema_{self.ema_short}'] <= prev[f'ema_{self.ema_mid1}'])
            
            # 条件4：RSI不超买
            rsi_not_overbought = rsi < 75
            
            # 综合判断
            if bullish_alignment and (price_breakout or ema_crossover) and rsi_not_overbought:
                if volume_confirm:
                    signal.signal_type = SignalType.STRONG_BUY
                    signal.confidence = min(0.9, 0.6 + alignment / 10)
                    signal.reason = f"均线多头排列突破买入，成交量放大{volume_ratio:.1f}倍"
                else:
                    signal.signal_type = SignalType.BUY
                    signal.confidence = min(0.7, 0.5 + alignment / 10)
                    signal.reason = "均线多头排列突破买入"
                
                signal.stop_loss = max(ema_m1, ema_m2) * 0.98  # 中期均线下方2%止损
                signal.take_profit = price * 1.08  # 8%止盈
                self._entry_price = price
        
        # 卖出信号
        elif current_position > 0:
            # 条件1：跌破短期均线
            below_short = price < ema_s
            
            # 条件2：跌破中期均线
            below_mid = price < min(ema_m1, ema_m2)
            
            # 条件3：均线死叉
            bearish_cross = (ema_s < ema_m1 and 
                            prev[f'ema_{self.ema_short}'] >= prev[f'ema_{self.ema_mid1}'])
            
            # 条件4：RSI超买
            rsi_overbought = rsi > 80
            
            # 条件5：均线空头排列
            bearish_alignment = (ema_s < ema_m1 < ema_m2 < ema_l)
            
            # 综合判断
            if bearish_alignment or bearish_cross or below_mid:
                signal.signal_type = SignalType.STRONG_SELL
                signal.confidence = 0.8
                signal.reason = "均线系统转空，立即止损"
            elif below_short or rsi_overbought:
                signal.signal_type = SignalType.SELL
                signal.confidence = 0.6
                signal.reason = "短期调整信号，减仓"
            
            # 动态止盈止损
            if self._entry_price > 0:
                profit_pct = (price - self._entry_price) / self._entry_price
                
                # 盈利超过5%，提高止损位到成本线
                if profit_pct > 0.05:
                    signal.stop_loss = self._entry_price * 1.01
                
                # 盈利超过10%，提高止损位到5%盈利
                if profit_pct > 0.10:
                    signal.stop_loss = self._entry_price * 1.05
        
        # 记录额外信息
        signal.metadata = {
            "ema_short": round(ema_s, 2),
            "ema_mid1": round(ema_m1, 2),
            "ema_mid2": round(ema_m2, 2),
            "ema_long": round(ema_l, 2),
            "volume_ratio": round(volume_ratio, 2),
            "rsi": round(rsi, 1),
            "alignment_score": round(alignment, 2),
            "bullish_alignment": ema_s > ema_m1 > ema_m2 > ema_l
        }
        
        self._last_signal = signal
        return signal

    def get_required_indicators(self) -> list:
        """获取策略所需的技术指标"""
        return [
            f'ema_{self.ema_short}',
            f'ema_{self.ema_mid1}',
            f'ema_{self.ema_mid2}',
            f'ema_{self.ema_long}',
            'volume_ma',
            'volume_ratio',
            'ema_alignment',
            'rsi'
        ]

    def _calculate_alignment(self, data: pd.DataFrame) -> pd.Series:
        """计算均线排列强度（0-10分）"""
        scores = []
        
        for idx in range(len(data)):
            score = 0
            row = data.iloc[idx]
            
            # 检查各均线关系
            if row[f'ema_{self.ema_short}'] > row[f'ema_{self.ema_mid1}']:
                score += 2.5
            if row[f'ema_{self.ema_mid1}'] > row[f'ema_{self.ema_mid2}']:
                score += 2.5
            if row[f'ema_{self.ema_mid2}'] > row[f'ema_{self.ema_long}']:
                score += 2.5
            if row['close'] > row[f'ema_{self.ema_short}']:
                score += 2.5
            
            scores.append(score)
        
        return pd.Series(scores, index=data.index)

    def _calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算 RSI 指标"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / (loss + 0.001)  # 避免除零
        rsi = 100 - (100 / (1 + rs))
        
        return rsi


# 创建预配置的策略实例
def create_ema_breakout_strategy() -> EMABreakoutStrategy:
    """创建均线突破策略实例"""
    config = StrategyConfig(
        name="EMA Breakout",
        version="1.0.0", 
        category="trend",
        description="基于多重EMA均线系统的突破策略，适合强势股票",
        author="InvestMind Team",
        parameters={
            "ema_short": 5,
            "ema_mid1": 9,
            "ema_mid2": 13,
            "ema_long": 21,
            "volume_multiplier": 1.5,
            "use_volume_confirm": True
        },
        risk_params={
            "max_position_pct": 0.4,
            "stop_loss_pct": 0.03,
            "take_profit_pct": 0.08,
            "max_drawdown_pct": 0.08
        }
    )
    return EMABreakoutStrategy(config)
