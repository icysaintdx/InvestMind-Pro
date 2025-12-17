"""
量价齐升战法 (Volume-Price Surge Strategy)
短期交易策略 - 捕捉量价配合的短期机会

核心理念：
1. 价格上涨 + 成交量放大
2. 量价配合度高
3. 短期持有3-5天
4. 快进快出
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .base import BaseStrategy, StrategySignal, SignalType, StrategyConfig, register_strategy

# 兼容旧代码
Signal = StrategySignal


@register_strategy("volume_price_surge")
class VolumePriceSurgeStrategy(BaseStrategy):
    """
    量价齐升战法
    
    入场条件：
    1. 价格连续上涨（2-3天）
    2. 成交量连续放大（量比>1.5）
    3. 量价配合度高（>0.8）
    4. 突破前期平台
    
    出场条件：
    1. 持有3-5天
    2. 量价背离（价涨量缩）
    3. 盈利5-8%止盈
    4. 跌破5日均线止损
    """
    
    # 添加策略描述属性
    description = "捕捉量价齐升的短期交易机会，快进快出"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "量价齐升策略"
        self.category = "民间策略"
        
        # 策略参数
        self.params = {
            # 价格要求
            "price_rise_days": 2,           # 连续上涨天数
            "price_rise_min": 0.03,         # 最小涨幅3%
            
            # 成交量要求
            "volume_ratio_min": 1.5,        # 最小量比1.5倍
            "volume_surge_days": 2,         # 连续放量天数
            
            # 量价配合度
            "vp_correlation_min": 0.8,      # 最小量价相关性0.8
            "vp_window": 5,                 # 量价相关性计算窗口
            
            # 持有周期
            "hold_days_min": 3,             # 最短持有3天
            "hold_days_max": 5,             # 最长持有5天
            
            # 止盈止损
            "take_profit_pct": 0.08,        # 止盈8%
            "stop_loss_pct": 0.04,          # 止损4%
        }
        
        # 风险参数
        self.risk_params = {
            "max_position_pct": 0.30,
            "stop_loss_pct": 0.04,
            "take_profit_pct": 0.08,
            "max_drawdown_pct": 0.10
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        # 价格变化
        df['pct_change'] = df['close'].pct_change()
        df['price_up'] = df['pct_change'] > 0
        
        # 连续上涨天数
        df['consecutive_up'] = df['price_up'].astype(int).groupby(
            (df['price_up'] != df['price_up'].shift()).cumsum()
        ).cumsum()
        df.loc[~df['price_up'], 'consecutive_up'] = 0
        
        # 成交量指标
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ma10'] = df['volume'].rolling(window=10).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma5']
        
        # 连续放量天数
        df['volume_surge'] = df['volume_ratio'] > self.params['volume_ratio_min']
        df['consecutive_surge'] = df['volume_surge'].astype(int).groupby(
            (df['volume_surge'] != df['volume_surge'].shift()).cumsum()
        ).cumsum()
        df.loc[~df['volume_surge'], 'consecutive_surge'] = 0
        
        # 量价配合度（相关性）
        df['vp_correlation'] = df['close'].rolling(
            window=self.params['vp_window']
        ).corr(df['volume'])
        
        # 均线
        df['ma5'] = df['close'].rolling(window=5).mean()
        df['ma10'] = df['close'].rolling(window=10).mean()
        df['ma20'] = df['close'].rolling(window=20).mean()
        
        # 价格相对位置
        df['price_position'] = (df['close'] - df['ma20']) / df['ma20']
        
        # 突破信号
        df['breakout'] = (
            (df['close'] > df['ma10']) &
            (df['close'].shift(1) <= df['ma10'].shift(1))
        )
        
        return df
    
    def check_volume_price_surge(self, row: pd.Series, prev_rows: pd.DataFrame) -> Dict[str, Any]:
        """
        检查量价齐升条件
        
        Returns:
            包含是否满足条件和详细信息的字典
        """
        conditions_met = []
        conditions_failed = []
        score = 0
        max_score = 4
        
        # 1. 检查连续上涨
        if row['consecutive_up'] >= self.params['price_rise_days']:
            score += 1
            conditions_met.append(f"✓ 连续上涨{int(row['consecutive_up'])}天")
        else:
            conditions_failed.append(f"✗ 连续上涨不足（{int(row['consecutive_up'])}天）")
        
        # 2. 检查涨幅
        recent_gain = (row['close'] - prev_rows.iloc[-self.params['price_rise_days']]['close']) / \
                     prev_rows.iloc[-self.params['price_rise_days']]['close']
        if recent_gain >= self.params['price_rise_min']:
            score += 1
            conditions_met.append(f"✓ 涨幅达标（{recent_gain:.1%}）")
        else:
            conditions_failed.append(f"✗ 涨幅不足（{recent_gain:.1%}）")
        
        # 3. 检查连续放量
        if row['consecutive_surge'] >= self.params['volume_surge_days']:
            score += 1
            conditions_met.append(f"✓ 连续放量{int(row['consecutive_surge'])}天（量比{row['volume_ratio']:.1f}）")
        else:
            conditions_failed.append(f"✗ 放量不足（{int(row['consecutive_surge'])}天）")
        
        # 4. 检查量价配合度
        if row['vp_correlation'] >= self.params['vp_correlation_min']:
            score += 1
            conditions_met.append(f"✓ 量价配合度高（{row['vp_correlation']:.2f}）")
        else:
            conditions_failed.append(f"✗ 量价配合度低（{row['vp_correlation']:.2f}）")
        
        # 判断是否满足条件（至少3分）
        qualified = score >= 3
        
        return {
            "qualified": qualified,
            "score": score,
            "max_score": max_score,
            "conditions_met": conditions_met,
            "conditions_failed": conditions_failed,
            "recent_gain": recent_gain
        }
    
    def check_exit_conditions(
        self,
        entry_row: pd.Series,
        current_row: pd.Series,
        hold_days: int
    ) -> Dict[str, Any]:
        """
        检查出场条件
        
        Returns:
            是否应该出场及原因
        """
        entry_price = entry_row['close']
        current_price = current_row['close']
        profit = (current_price - entry_price) / entry_price
        
        should_exit = False
        exit_reason = []
        
        # 1. 止盈
        if profit >= self.params['take_profit_pct']:
            should_exit = True
            exit_reason.append(f"✓ 达到止盈目标（{profit:.1%}）")
        
        # 2. 止损
        if current_price < current_row['ma5']:
            should_exit = True
            exit_reason.append(f"✗ 跌破5日均线（{profit:.1%}）")
        
        # 3. 持有时间
        if hold_days >= self.params['hold_days_max']:
            should_exit = True
            exit_reason.append(f"⏰ 达到最长持有期（{hold_days}天）")
        
        # 4. 量价背离
        if current_row['pct_change'] > 0 and current_row['volume_ratio'] < 1.0:
            should_exit = True
            exit_reason.append(f"⚠ 量价背离（价涨量缩）")
        
        return {
            "should_exit": should_exit,
            "exit_reason": exit_reason,
            "profit": profit,
            "hold_days": hold_days
        }
    
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
                strategy_id="volume_price_surge",
                strategy_name=self.name
            )
        
        row = df.iloc[-1]
        price = row['close']
        
        signal_type = SignalType.HOLD
        confidence = 0.5
        reasons = []
        
        # 量价齐升检测
        price_surge = row.get('price_surge', False)
        volume_surge = row.get('volume_surge', False)
        vp_sync = row.get('vp_sync', 0)
        
        if price_surge and volume_surge and vp_sync >= 0.8:
            signal_type = SignalType.BUY
            confidence = 0.75
            reasons = [
                "量价齐升信号",
                f"量价配合度: {vp_sync:.2f}",
                f"量比: {row.get('volume_ratio', 0):.2f}"
            ]
        elif current_position > 0:
            # 量价背离检测
            vp_divergence = row.get('vp_divergence', False)
            if vp_divergence:
                signal_type = SignalType.SELL
                confidence = 0.7
                reasons = ["量价背离，价涨量缩"]
        
        return StrategySignal(
            signal_type=signal_type,
            confidence=confidence,
            strength=min(vp_sync, 1.0) if vp_sync else 0.5,
            price=price,
            stop_loss=price * 0.95 if signal_type == SignalType.BUY else None,
            target_price=price * 1.08 if signal_type == SignalType.BUY else None,
            position_size=0.3 if signal_type == SignalType.BUY else 0,
            reasons=reasons[:5],
            strategy_id="volume_price_surge",
            strategy_name=self.name
        )
    
    def _generate_signals_legacy(self, data: pd.DataFrame) -> List[Signal]:
        """生成交易信号"""
        df = self.calculate_indicators(data)
        signals = []
        
        # 持仓状态跟踪
        in_position = False
        entry_index = None
        entry_price = None
        
        for i in range(self.params['vp_window'], len(df)):
            row = df.iloc[i]
            prev_rows = df.iloc[max(0, i-10):i]
            
            # 检查入场条件
            if not in_position:
                surge_check = self.check_volume_price_surge(row, prev_rows)
                
                if surge_check['qualified']:
                    # 生成买入信号
                    current_price = row['close']
                    target_price = current_price * (1 + self.params['take_profit_pct'])
                    stop_loss = row['ma5']  # 5日均线作为止损
                    
                    # 根据得分调整仓位
                    quality_ratio = surge_check['score'] / surge_check['max_score']
                    position_size = self.risk_params['max_position_pct'] * quality_ratio
                    
                    reasons = self._generate_buy_reasons(row, surge_check)
                    
                    signal = Signal(
                        strategy_id="volume_price_surge",
                        strategy_name=self.name,
                        signal_type=SignalType.BUY,
                        strength=quality_ratio,
                        confidence=quality_ratio * 0.85,
                        target_price=target_price,
                        stop_loss=stop_loss,
                        position_size=position_size,
                        reasons=reasons,
                        timestamp=df.index[i]
                    )
                    
                    signals.append(signal)
                    
                    # 更新持仓状态
                    in_position = True
                    entry_index = i
                    entry_price = current_price
            
            # 检查出场条件
            else:
                entry_row = df.iloc[entry_index]
                hold_days = i - entry_index
                
                exit_check = self.check_exit_conditions(entry_row, row, hold_days)
                
                if exit_check['should_exit']:
                    # 生成卖出信号
                    reasons = self._generate_sell_reasons(row, exit_check)
                    
                    signal = Signal(
                        strategy_id="volume_price_surge",
                        strategy_name=self.name,
                        signal_type=SignalType.SELL,
                        strength=0.9,
                        confidence=0.85,
                        reasons=reasons,
                        timestamp=df.index[i]
                    )
                    
                    signals.append(signal)
                    
                    # 重置持仓状态
                    in_position = False
                    entry_index = None
                    entry_price = None
        
        return signals
    
    def _generate_buy_reasons(
        self,
        row: pd.Series,
        surge_check: Dict[str, Any]
    ) -> List[str]:
        """生成买入信号原因"""
        reasons = []
        
        reasons.append(f"✓ 量价齐升（得分{surge_check['score']}/{surge_check['max_score']}）")
        
        # 添加满足的条件
        for condition in surge_check['conditions_met']:
            reasons.append(f"  {condition}")
        
        reasons.append(f"当前价：{row['close']:.2f}")
        reasons.append(f"5日均线：{row['ma5']:.2f}")
        reasons.append("量价齐升战法：短期持有3-5天")
        
        return reasons
    
    def _generate_sell_reasons(
        self,
        row: pd.Series,
        exit_check: Dict[str, Any]
    ) -> List[str]:
        """生成卖出信号原因"""
        reasons = []
        
        reasons.append(f"出场信号（持有{exit_check['hold_days']}天，盈亏{exit_check['profit']:.1%}）")
        
        for reason in exit_check['exit_reason']:
            reasons.append(f"  {reason}")
        
        reasons.append(f"当前价：{row['close']:.2f}")
        reasons.append("量价齐升战法：快进快出，落袋为安")
        
        return reasons
    
    def get_required_indicators(self) -> List[str]:
        """获取所需的技术指标"""
        return [
            'pct_change',
            'price_up',
            'consecutive_up',
            'volume_ma5',
            'volume_ma10',
            'volume_ratio',
            'volume_surge',
            'consecutive_surge',
            'vp_correlation',
            'ma5',
            'ma10',
            'ma20',
            'price_position',
            'breakout'
        ]
