"""
海龟交易法则 (Turtle Trading Rules)
经典的趋势跟踪策略 - ATR金字塔加仓

核心理念：
1. 唐奇安通道突破入场
2. ATR动态止损
3. 金字塔式加仓
4. 严格的资金管理
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .base import BaseStrategy, StrategySignal, SignalType, StrategyConfig, register_strategy

# 兼容旧代码
Signal = StrategySignal


@register_strategy("turtle_trading")
class TurtleTradingStrategy(BaseStrategy):
    """
    海龟交易法则
    
    入场规则：
    - System 1: 20日突破（短期系统）
    - System 2: 55日突破（长期系统）
    
    加仓规则：
    - 每次价格向有利方向移动0.5个ATR时加仓
    - 最多加仓4次
    
    止损规则：
    - 初始止损：2个ATR
    - 加仓后调整止损
    """
    
    # 添加策略描述属性
    description = "经典的海龟交易法则，趋势跟踪策略，适合长线交易"
    
    def __init__(self, config: StrategyConfig, system: int = 2):
        super().__init__(config)
        self.name = "海龟交易法则"
        self.category = "技术分析"
        
        # 系统选择：1=短期(20日)，2=长期(55日)
        self.system = system
        
        # 策略参数
        self.params = {
            # 唐奇安通道周期
            "entry_period": 55 if system == 2 else 20,
            "exit_period": 20 if system == 2 else 10,
            
            # ATR参数
            "atr_period": 20,
            "stop_loss_atr": 2.0,      # 止损：2个ATR
            "add_position_atr": 0.5,    # 加仓：0.5个ATR
            
            # 金字塔加仓
            "max_units": 4,             # 最多4个单位
            "unit_size": 0.01,          # 每单位占账户的1%
            
            # 风险参数
            "account_risk": 0.02,       # 每次交易风险2%
        }
        
        # 风险参数
        self.risk_params = {
            "max_position_pct": 0.40,   # 最大总仓位40%（4单位×10%）
            "stop_loss_pct": 0.08,      # 初始止损约8%（2个ATR）
            "take_profit_pct": 0.20,    # 目标止盈20%
            "max_drawdown_pct": 0.15
        }
        
        # 持仓状态（用于跟踪加仓）
        self.position_units = 0
        self.entry_prices = []
        self.current_stop_loss = None
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        # 唐奇安通道（入场）
        df['donchian_high'] = df['high'].rolling(
            window=self.params['entry_period']
        ).max()
        df['donchian_low'] = df['low'].rolling(
            window=self.params['entry_period']
        ).min()
        
        # 唐奇安通道（出场）
        df['exit_high'] = df['high'].rolling(
            window=self.params['exit_period']
        ).max()
        df['exit_low'] = df['low'].rolling(
            window=self.params['exit_period']
        ).min()
        
        # ATR（真实波动幅度）
        df['tr'] = self._calculate_true_range(df)
        df['atr'] = df['tr'].rolling(window=self.params['atr_period']).mean()
        
        # 突破信号
        df['breakout_high'] = (df['close'] > df['donchian_high'].shift(1))
        df['breakout_low'] = (df['close'] < df['donchian_low'].shift(1))
        
        # 出场信号
        df['exit_signal_long'] = (df['close'] < df['exit_low'].shift(1))
        df['exit_signal_short'] = (df['close'] > df['exit_high'].shift(1))
        
        return df
    
    def _calculate_true_range(self, df: pd.DataFrame) -> pd.Series:
        """计算真实波动幅度（True Range）"""
        high_low = df['high'] - df['low']
        high_close = abs(df['high'] - df['close'].shift(1))
        low_close = abs(df['low'] - df['close'].shift(1))
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr
    
    def calculate_position_size(
        self,
        account_value: float,
        atr: float,
        price: float
    ) -> Dict[str, Any]:
        """
        计算仓位大小（海龟交易法则的核心）
        
        Args:
            account_value: 账户总价值
            atr: 当前ATR值
            price: 当前价格
            
        Returns:
            包含单位数量、金额、风险的字典
        """
        # 计算每个单位的风险金额
        dollar_volatility = atr * 1  # 1股的波动金额
        
        # 计算单位大小（账户的1%风险）
        unit_size = (account_value * self.params['unit_size']) / dollar_volatility
        
        # 计算可以买入的股数
        shares = int(unit_size)
        
        # 计算需要的资金
        required_capital = shares * price
        
        # 计算风险金额（2个ATR的止损）
        risk_amount = shares * atr * self.params['stop_loss_atr']
        
        return {
            "shares": shares,
            "capital": required_capital,
            "risk": risk_amount,
            "risk_pct": risk_amount / account_value if account_value > 0 else 0
        }
    
    def initialize(self, data: pd.DataFrame) -> None:
        """初始化策略"""
        self._initialized = True
        self.position_units = 0
        self.entry_prices = []
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> StrategySignal:
        """生成交易信号（新接口）"""
        df = self.calculate_indicators(data)
        
        min_period = max(self.params['entry_period'], self.params['atr_period'])
        if len(df) < min_period:
            return StrategySignal(
                signal_type=SignalType.HOLD,
                confidence=0.0,
                strength=0.0,
                reasons=["数据不足"],
                strategy_id="turtle_trading",
                strategy_name=self.name
            )
        
        row = df.iloc[-1]
        price = row['close']
        atr = row.get('atr', price * 0.02)
        
        signal_type = SignalType.HOLD
        confidence = 0.5
        reasons = []
        
        # 唐奇安通道突破
        if price >= row.get('donchian_high', price):
            signal_type = SignalType.BUY
            confidence = 0.75
            reasons = [
                f"价格突破{self.params['entry_period']}日高点",
                f"唐奇安通道上轨: {row.get('donchian_high', 0):.2f}",
                f"ATR: {atr:.2f}"
            ]
        elif price <= row.get('donchian_low', price) and current_position > 0:
            signal_type = SignalType.SELL
            confidence = 0.75
            reasons = [
                f"价格跌破{self.params['exit_period']}日低点",
                f"唐奇安通道下轨: {row.get('donchian_low', 0):.2f}"
            ]
        
        # ATR动态止损
        stop_loss = price - (atr * self.params['stop_loss_atr']) if signal_type == SignalType.BUY else None
        
        return StrategySignal(
            signal_type=signal_type,
            confidence=confidence,
            strength=0.75,
            price=price,
            stop_loss=stop_loss,
            target_price=None,  # 海龟策略不设目标价
            position_size=0.25 if signal_type == SignalType.BUY else 0,
            reasons=reasons[:5],
            strategy_id="turtle_trading",
            strategy_name=self.name
        )
    
    def _generate_signals_legacy(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信号"""
        df = self.calculate_indicators(data)
        signals = []
        
        # 重置持仓状态
        self.position_units = 0
        self.entry_prices = []
        self.current_stop_loss = None
        
        for i in range(len(df)):
            if i < self.params['entry_period']:
                continue
            
            row = df.iloc[i]
            
            # 做多突破信号
            if row['breakout_high'] and self.position_units == 0:
                current_price = row['close']
                atr = row['atr']
                
                # 计算初始止损
                stop_loss = current_price - (atr * self.params['stop_loss_atr'])
                
                # 计算目标价（基于ATR的倍数）
                target_price = current_price + (atr * 4)  # 4个ATR的目标
                
                # 初始仓位（1个单位）
                position_size = self.risk_params['max_position_pct'] / self.params['max_units']
                
                reasons = self._generate_entry_reasons(row, "long", 1)
                
                signal = Signal(
                    strategy_id="turtle_trading",
                    strategy_name=self.name,
                    signal_type=SignalType.BUY,
                    strength=0.8,
                    confidence=0.75,
                    target_price=target_price,
                    stop_loss=stop_loss,
                    position_size=position_size,
                    reasons=reasons,
                    timestamp=df.index[i]
                )
                
                signals.append(signal)
                
                # 更新持仓状态
                self.position_units = 1
                self.entry_prices = [current_price]
                self.current_stop_loss = stop_loss
            
            # 加仓信号（金字塔式）
            elif self.position_units > 0 and self.position_units < self.params['max_units']:
                current_price = row['close']
                atr = row['atr']
                
                # 检查是否达到加仓条件（价格上涨0.5个ATR）
                last_entry = self.entry_prices[-1]
                if current_price >= last_entry + (atr * self.params['add_position_atr']):
                    
                    # 计算新的止损（提高到上一个入场价下方2个ATR）
                    new_stop_loss = last_entry - (atr * self.params['stop_loss_atr'])
                    
                    # 加仓
                    unit_number = self.position_units + 1
                    position_size = self.risk_params['max_position_pct'] / self.params['max_units']
                    
                    reasons = self._generate_add_position_reasons(
                        row, unit_number, last_entry, current_price
                    )
                    
                    signal = Signal(
                        strategy_id="turtle_trading",
                        strategy_name=self.name,
                        signal_type=SignalType.BUY,
                        strength=0.7,
                        confidence=0.7,
                        stop_loss=new_stop_loss,
                        position_size=position_size,
                        reasons=reasons,
                        timestamp=df.index[i]
                    )
                    
                    signals.append(signal)
                    
                    # 更新持仓状态
                    self.position_units += 1
                    self.entry_prices.append(current_price)
                    self.current_stop_loss = new_stop_loss
            
            # 出场信号
            if self.position_units > 0 and row['exit_signal_long']:
                reasons = [
                    f"✗ 跌破{self.params['exit_period']}日低点",
                    f"当前持有{self.position_units}个单位",
                    f"平均成本：{np.mean(self.entry_prices):.2f}",
                    "海龟交易法则：趋势结束，全部平仓"
                ]
                
                signal = Signal(
                    strategy_id="turtle_trading",
                    strategy_name=self.name,
                    signal_type=SignalType.SELL,
                    strength=0.9,
                    confidence=0.8,
                    reasons=reasons,
                    timestamp=df.index[i]
                )
                
                signals.append(signal)
                
                # 重置持仓状态
                self.position_units = 0
                self.entry_prices = []
                self.current_stop_loss = None
        
        return signals
    
    def _generate_entry_reasons(
        self,
        row: pd.Series,
        direction: str,
        unit_number: int
    ) -> List[str]:
        """生成入场信号原因"""
        reasons = []
        
        if direction == "long":
            reasons.append(f"✓ 突破{self.params['entry_period']}日高点")
            reasons.append(f"  入场价：{row['close']:.2f}")
            reasons.append(f"  ATR：{row['atr']:.2f}")
            reasons.append(f"  止损：{row['close'] - row['atr'] * self.params['stop_loss_atr']:.2f}")
            reasons.append(f"海龟交易法则 System {self.system}")
            reasons.append(f"初始建仓：第{unit_number}个单位（共{self.params['max_units']}个）")
        
        return reasons
    
    def _generate_add_position_reasons(
        self,
        row: pd.Series,
        unit_number: int,
        last_entry: float,
        current_price: float
    ) -> List[str]:
        """生成加仓信号原因"""
        reasons = []
        
        gain = (current_price - last_entry) / last_entry
        
        reasons.append(f"✓ 金字塔加仓：第{unit_number}个单位")
        reasons.append(f"  上次入场：{last_entry:.2f}")
        reasons.append(f"  当前价格：{current_price:.2f}")
        reasons.append(f"  盈利：{gain:.1%}")
        reasons.append(f"  ATR：{row['atr']:.2f}")
        reasons.append(f"海龟交易法则：趋势确认，继续加仓")
        
        return reasons
    
    def get_required_indicators(self) -> List[str]:
        """获取所需的技术指标"""
        return [
            'donchian_high',
            'donchian_low',
            'exit_high',
            'exit_low',
            'atr',
            'tr',
            'breakout_high',
            'breakout_low',
            'exit_signal_long',
            'exit_signal_short'
        ]
