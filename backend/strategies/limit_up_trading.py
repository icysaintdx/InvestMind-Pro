"""
涨停板战法 (Limit Up Trading)
A股特色策略 - 首板涨停 T+1

核心理念：
1. 捕捉首板涨停（非一字板）
2. T+1开盘竞价买入
3. 快进快出，控制风险
4. 关注成交量和封单强度
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, List, Optional
from .base import BaseStrategy, StrategySignal, SignalType, StrategyConfig, register_strategy

# 兼容旧代码
Signal = StrategySignal


@register_strategy("limit_up_trading")
class LimitUpTradingStrategy(BaseStrategy):
    """
    涨停板战法
    
    入场条件：
    1. 前一日涨停（非一字板）
    2. 涨停时间早（最好10:30前）
    3. 封单强度大（封单量/流通盘>5%）
    4. 成交量放大（量比>2）
    5. 板块有热度
    
    出场条件：
    1. T+1开盘冲高回落
    2. 盈儩3-5%止盈
    3. 跌破开盘价止损
    """
    
    # 添加策略描述属性
    description = "A股特色的涨停板战法，捕捉首板涨停 T+1的短线机会"
        
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        self.name = "涨停板战法"
        self.category = "民间策略"
        
        # 策略参数
        self.params = {
            # 涨停板识别
            "limit_up_pct": 0.10,           # A股涨停幅度10%（ST为5%）
            "limit_up_tolerance": 0.001,    # 涨停容差0.1%
            
            # 封单强度
            "seal_strength_min": 0.05,      # 最小封单强度5%
            "volume_ratio_min": 2.0,        # 最小量比2倍
            
            # 时间要求
            "limit_up_time_max": 1030,      # 涨停时间最晚10:30
            
            # 板块要求
            "sector_heat_min": 0.6,         # 板块热度最低60%
            
            # T+1交易参数
            "open_premium_max": 0.03,       # 开盘溢价最大3%
            "take_profit_pct": 0.05,        # 止盈5%
            "stop_loss_pct": 0.03,          # 止损3%
        }
        
        # 风险参数
        self.risk_params = {
            "max_position_pct": 0.20,       # 最大仓位20%（高风险）
            "stop_loss_pct": 0.03,
            "take_profit_pct": 0.05,
            "max_drawdown_pct": 0.08
        }
    
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """计算技术指标"""
        df = data.copy()
        
        # 涨跌幅
        df['pct_change'] = df['close'].pct_change()
        
        # 识别涨停板
        df['is_limit_up'] = (
            (df['pct_change'] >= self.params['limit_up_pct'] - self.params['limit_up_tolerance']) &
            (df['pct_change'] <= self.params['limit_up_pct'] + self.params['limit_up_tolerance'])
        )
        
        # 识别一字板（开盘就涨停）
        df['is_one_word_board'] = (
            df['is_limit_up'] &
            (df['open'] >= df['close'] * 0.999)  # 开盘价接近收盘价
        )
        
        # 识别首板（非一字板的涨停）
        df['is_first_board'] = df['is_limit_up'] & ~df['is_one_word_board']
        
        # 成交量比率
        df['volume_ma5'] = df['volume'].rolling(window=5).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma5']
        
        # 换手率（需要流通股本数据，这里用成交量/总市值估算）
        # 实际使用时需要接入真实的换手率数据
        df['turnover_rate'] = (df['volume'] * df['close']) / (df['volume'].rolling(20).mean() * df['close'].rolling(20).mean())
        
        return df
    
    def check_limit_up_quality(
        self,
        row: pd.Series,
        limit_up_time: Optional[int] = None,
        seal_orders: Optional[float] = None,
        sector_heat: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        检查涨停板质量
        
        Args:
            row: 当前K线数据
            limit_up_time: 涨停时间（HHMM格式，如1030表示10:30）
            seal_orders: 封单量（手）
            sector_heat: 板块热度（0-1）
            
        Returns:
            质量评分和详细信息
        """
        score = 0
        max_score = 5
        details = []
        
        # 1. 检查是否首板（非一字板）
        if row['is_first_board']:
            score += 1
            details.append("✓ 首板涨停（非一字板）")
        else:
            details.append("✗ 不是首板或为一字板")
            return {"score": 0, "max_score": max_score, "details": details, "qualified": False}
        
        # 2. 检查涨停时间
        if limit_up_time is not None:
            if limit_up_time <= self.params['limit_up_time_max']:
                score += 1
                details.append(f"✓ 涨停时间早（{limit_up_time//100:02d}:{limit_up_time%100:02d}）")
            else:
                details.append(f"✗ 涨停时间晚（{limit_up_time//100:02d}:{limit_up_time%100:02d}）")
        
        # 3. 检查成交量
        if row['volume_ratio'] >= self.params['volume_ratio_min']:
            score += 1
            details.append(f"✓ 成交量放大（量比{row['volume_ratio']:.1f}）")
        else:
            details.append(f"✗ 成交量不足（量比{row['volume_ratio']:.1f}）")
        
        # 4. 检查封单强度
        if seal_orders is not None:
            # 封单强度 = 封单量 / 流通盘
            # 这里简化处理，实际需要真实的流通盘数据
            seal_strength = seal_orders / (row['volume'] * 10)  # 估算
            if seal_strength >= self.params['seal_strength_min']:
                score += 1
                details.append(f"✓ 封单强度大（{seal_strength:.1%}）")
            else:
                details.append(f"✗ 封单强度弱（{seal_strength:.1%}）")
        
        # 5. 检查板块热度
        if sector_heat is not None:
            if sector_heat >= self.params['sector_heat_min']:
                score += 1
                details.append(f"✓ 板块有热度（{sector_heat:.1%}）")
            else:
                details.append(f"✗ 板块热度不足（{sector_heat:.1%}）")
        
        # 判断是否合格（至少3分）
        qualified = score >= 3
        
        return {
            "score": score,
            "max_score": max_score,
            "details": details,
            "qualified": qualified
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
                strategy_id="limit_up_trading",
                strategy_name=self.name
            )
        
        row = df.iloc[-1]
        prev_row = df.iloc[-2]
        price = row['close']
        
        signal_type = SignalType.HOLD
        confidence = 0.5
        reasons = []
        
        # 检测前一日是否涨停
        prev_change = (prev_row['close'] - prev_row['open']) / prev_row['open']
        is_limit_up = prev_change >= (self.params['limit_up_pct'] - self.params['limit_up_tolerance'])
        
        if is_limit_up:
            # 前一日涨停，T+1开盘买入机会
            volume_ratio = row.get('volume_ratio', 0)
            
            if volume_ratio >= self.params['volume_ratio_min']:
                signal_type = SignalType.BUY
                confidence = 0.7
                reasons = [
                    f"前日涨停: {prev_change*100:.2f}%",
                    f"量比: {volume_ratio:.2f}",
                    "T+1首板战法"
                ]
        
        # 已持仓，检查出场条件
        elif current_position > 0:
            # 简单的止盈止损逻辑
            change = (price - prev_row['close']) / prev_row['close']
            if change >= 0.05:  # 5%止盈
                signal_type = SignalType.SELL
                confidence = 0.8
                reasons = [f"达到目标盈利: {change*100:.1f}%"]
            elif change <= -0.03:  # -3%止损
                signal_type = SignalType.SELL
                confidence = 0.9
                reasons = [f"触发止损: {change*100:.1f}%"]
        
        return StrategySignal(
            signal_type=signal_type,
            confidence=confidence,
            strength=0.7,
            price=price,
            stop_loss=price * 0.97 if signal_type == SignalType.BUY else None,
            target_price=price * 1.05 if signal_type == SignalType.BUY else None,
            position_size=0.3 if signal_type == SignalType.BUY else 0,
            reasons=reasons[:5],
            strategy_id="limit_up_trading",
            strategy_name=self.name
        )
    
    def _generate_signals_legacy(
        self,
        data: pd.DataFrame,
        limit_up_info: Optional[Dict[str, Any]] = None
    ) -> List[Signal]:
        """
        生成交易信号
        
        Args:
            data: 价格数据
            limit_up_info: 涨停板详细信息（时间、封单量、板块热度等）
        """
        df = self.calculate_indicators(data)
        signals = []
        
        for i in range(1, len(df)):
            prev_row = df.iloc[i-1]
            curr_row = df.iloc[i]
            
            # T日：检测到涨停板
            if prev_row['is_first_board']:
                
                # 提取涨停板信息
                limit_up_time = limit_up_info.get('time') if limit_up_info else None
                seal_orders = limit_up_info.get('seal_orders') if limit_up_info else None
                sector_heat = limit_up_info.get('sector_heat') if limit_up_info else None
                
                # 检查涨停板质量
                quality = self.check_limit_up_quality(
                    prev_row,
                    limit_up_time,
                    seal_orders,
                    sector_heat
                )
                
                if not quality['qualified']:
                    continue
                
                # T+1日：生成买入信号
                # 检查开盘溢价
                open_premium = (curr_row['open'] - prev_row['close']) / prev_row['close']
                
                if open_premium > self.params['open_premium_max']:
                    # 开盘溢价过高，放弃
                    continue
                
                # 计算目标价和止损价
                entry_price = curr_row['open']
                target_price = entry_price * (1 + self.params['take_profit_pct'])
                stop_loss = entry_price * (1 - self.params['stop_loss_pct'])
                
                # 根据质量评分调整仓位
                quality_ratio = quality['score'] / quality['max_score']
                position_size = self.risk_params['max_position_pct'] * quality_ratio
                
                # 生成买入信号
                reasons = self._generate_buy_reasons(
                    prev_row, curr_row, quality, open_premium
                )
                
                signal = Signal(
                    strategy_id="limit_up_trading",
                    strategy_name=self.name,
                    signal_type=SignalType.BUY,
                    strength=quality_ratio,
                    confidence=quality_ratio * 0.8,  # 涨停板策略风险较高
                    target_price=target_price,
                    stop_loss=stop_loss,
                    position_size=position_size,
                    reasons=reasons,
                    timestamp=df.index[i]
                )
                
                signals.append(signal)
            
            # 检查是否需要卖出
            # 这里简化处理，实际需要跟踪持仓状态
            if i >= 2:
                prev_prev_row = df.iloc[i-2]
                if prev_prev_row['is_first_board']:
                    # 检查是否达到止盈或止损条件
                    entry_price = prev_row['open']
                    current_price = curr_row['close']
                    
                    profit = (current_price - entry_price) / entry_price
                    
                    if profit >= self.params['take_profit_pct']:
                        # 止盈
                        reasons = [
                            f"✓ 达到止盈目标（{profit:.1%}）",
                            f"入场价：{entry_price:.2f}",
                            f"当前价：{current_price:.2f}",
                            "涨停板战法：快进快出，落袋为安"
                        ]
                        
                        signal = Signal(
                            strategy_id="limit_up_trading",
                            strategy_name=self.name,
                            signal_type=SignalType.SELL,
                            strength=0.9,
                            confidence=0.8,
                            reasons=reasons,
                            timestamp=df.index[i]
                        )
                        
                        signals.append(signal)
                    
                    elif current_price < entry_price * (1 - self.params['stop_loss_pct']):
                        # 止损
                        reasons = [
                            f"✗ 触发止损（{profit:.1%}）",
                            f"入场价：{entry_price:.2f}",
                            f"当前价：{current_price:.2f}",
                            "涨停板战法：严格止损，控制风险"
                        ]
                        
                        signal = Signal(
                            strategy_id="limit_up_trading",
                            strategy_name=self.name,
                            signal_type=SignalType.SELL,
                            strength=1.0,
                            confidence=0.9,
                            reasons=reasons,
                            timestamp=df.index[i]
                        )
                        
                        signals.append(signal)
        
        return signals
    
    def _generate_buy_reasons(
        self,
        limit_up_row: pd.Series,
        entry_row: pd.Series,
        quality: Dict[str, Any],
        open_premium: float
    ) -> List[str]:
        """生成买入信号原因"""
        reasons = []
        
        reasons.append(f"✓ T日涨停板（质量{quality['score']}/{quality['max_score']}分）")
        
        # 添加质量详情
        for detail in quality['details']:
            if detail.startswith("✓"):
                reasons.append(f"  {detail}")
        
        reasons.append(f"T+1开盘溢价：{open_premium:.1%}")
        reasons.append(f"入场价：{entry_row['open']:.2f}")
        reasons.append(f"止盈目标：{entry_row['open'] * (1 + self.params['take_profit_pct']):.2f}")
        reasons.append("涨停板战法：快进快出，控制风险")
        
        return reasons
    
    def get_required_indicators(self) -> List[str]:
        """获取所需的技术指标"""
        return [
            'pct_change',
            'is_limit_up',
            'is_one_word_board',
            'is_first_board',
            'volume_ma5',
            'volume_ratio',
            'turnover_rate'
        ]
