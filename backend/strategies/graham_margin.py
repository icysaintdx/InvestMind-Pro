"""
格雷厄姆安全边际策略 (Graham Margin of Safety Strategy)
以低于内在价值的价格买入，安全边际保护

核心理念：
1. 安全边际：以显著低于内在价值的价格买入
2. 防御性投资：重视财务稳健性
3. 价值回归：等待市场认识到真实价值
4. 纪律性：严格遵守估值标准

投资标准：
- 估值指标：PE<10、PB<1.5、股价<净资产×1.5
- 安全边际：内在价值/股价>1.5、清算价值>市值
- 财务稳健：流动比率>2、速动比率>1、负债率<40%
- 盈利能力：连续5年盈利、ROE>10%、股息率>3%

持有策略：
- 价值回归后卖出
- 达到内在价值卖出
- 基本面恶化卖出
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .base import (
    BaseStrategy,
    StrategySignal,
    SignalType,
    StrategyConfig,
    register_strategy
)


@register_strategy("graham_margin")
class GrahamMarginStrategy(BaseStrategy):
    """
    格雷厄姆安全边际策略
    
    选股标准：
    1. 极低估值（PE<10, PB<1.5）
    2. 充足安全边际（>50%）
    3. 财务稳健（高流动性、低负债）
    4. 持续盈利能力
    
    持有策略：
    - 价值回归后卖出
    - 基本面恶化时卖出
    """
    
    # 策略描述属性
    description = "低于内在价值买入，充足的安全边际保护"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # 设置中文名称和分类
        self.name = "格雷厄姆安全边际"
        self.category = "价值投资"
        
        # 估值标准（非常严格）
        self.max_pe = self.parameters.get('max_pe', 10)  # 最大PE 10
        self.max_pb = self.parameters.get('max_pb', 1.5)  # 最大PB 1.5
        self.max_price_to_net_asset = self.parameters.get('max_price_to_net_asset', 1.5)  # 价格/净资产
        
        # 安全边际标准
        self.min_margin_of_safety = self.parameters.get('min_margin_of_safety', 0.50)  # 最低安全边际 50%
        self.min_intrinsic_value_ratio = self.parameters.get('min_intrinsic_value_ratio', 1.5)  # 内在价值/股价
        
        # 财务稳健标准
        self.min_current_ratio = self.parameters.get('min_current_ratio', 2.0)  # 最低流动比率 2.0
        self.min_quick_ratio = self.parameters.get('min_quick_ratio', 1.0)  # 最低速动比率 1.0
        self.max_debt_ratio = self.parameters.get('max_debt_ratio', 0.40)  # 最大负债率 40%
        
        # 盈利能力标准
        self.min_roe = self.parameters.get('min_roe', 0.10)  # 最低ROE 10%
        self.min_dividend_yield = self.parameters.get('min_dividend_yield', 0.03)  # 最低股息率 3%
        self.profit_years = self.parameters.get('profit_years', 5)  # 连续盈利年数
        
        # 持有策略
        self.target_return = self.parameters.get('target_return', 0.50)  # 目标回报 50%
        self.max_holding_days = self.parameters.get('max_holding_days', 1095)  # 最长持有天数（3年）
        
        # 风险参数
        self.max_position = self.parameters.get('max_position', 0.25)  # 最大仓位 25%（保守）
        self.stop_loss_pct = self.parameters.get('stop_loss', 0.15)  # 止损 -15%
        self.take_profit_pct = self.parameters.get('take_profit', 0.80)  # 止盈 +80%
        
        # 内部状态
        self.holding_position = None
        self.entry_date = None
        self.entry_price = 0
        self.intrinsic_value = 0
        
    def initialize(self, data: pd.DataFrame):
        """初始化策略"""
        self._initialized = True
    
    def get_required_indicators(self) -> List[str]:
        """返回策略所需指标"""
        return [
            "pe_ratio",
            "pb_ratio",
            "current_ratio",
            "debt_ratio",
            "dividend_yield",
            "earnings_stability"
        ]
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标和价值指标
        
        注：实际应用中需要接入财报数据API
        这里使用技术指标模拟价值指标
        """
        df = data.copy()
        
        # 技术指标
        df['sma_50'] = df['close'].rolling(window=50).mean()
        df['sma_200'] = df['close'].rolling(window=200).mean()
        
        # 价格波动率
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=60).std()
        
        # 模拟估值指标（实际应从财报数据获取）
        
        # 模拟PE（使用价格相对位置，低位=低PE）
        df['price_percentile'] = df['close'].rolling(window=250).apply(
            lambda x: (x.iloc[-1] - x.min()) / (x.max() - x.min()) if (x.max() - x.min()) > 0 else 0.5
        )
        df['simulated_pe'] = 5 + df['price_percentile'] * 20  # PE在5-25之间
        
        # 模拟PB（使用价格趋势）
        df['price_trend'] = (df['close'] - df['sma_200']) / df['sma_200']
        df['simulated_pb'] = 0.8 + df['price_trend'] * 1.5  # PB在0.3-2.3之间
        df['simulated_pb'] = df['simulated_pb'].clip(0.3, 3.0)
        
        # 模拟净资产（假设为当前价格的某个倍数）
        df['simulated_net_asset'] = df['close'] / df['simulated_pb']
        
        # 模拟流动比率（使用成交量稳定性）
        df['volume_std'] = df['volume'].rolling(window=60).std()
        df['volume_mean'] = df['volume'].rolling(window=60).mean()
        df['volume_stability'] = 1 - (df['volume_std'] / df['volume_mean']).clip(0, 1)
        df['simulated_current_ratio'] = 1.0 + df['volume_stability'] * 2.0  # 1.0-3.0
        
        # 模拟速动比率（略低于流动比率）
        df['simulated_quick_ratio'] = df['simulated_current_ratio'] * 0.7
        
        # 模拟负债率（使用波动率）
        df['simulated_debt_ratio'] = df['volatility'] * 8  # 波动率越高，负债率越高
        df['simulated_debt_ratio'] = df['simulated_debt_ratio'].clip(0, 0.8)
        
        # 模拟ROE（使用价格稳定性）
        df['price_std'] = df['close'].rolling(window=250).std()
        df['price_mean'] = df['close'].rolling(window=250).mean()
        df['price_stability'] = 1 - (df['price_std'] / df['price_mean']).clip(0, 1)
        df['simulated_roe'] = 0.05 + df['price_stability'] * 0.20  # 5%-25%
        
        # 模拟股息率（使用低波动率）
        df['simulated_dividend_yield'] = 0.05 * (1 - df['volatility'] * 10)
        df['simulated_dividend_yield'] = df['simulated_dividend_yield'].clip(0, 0.08)
        
        # 模拟盈利持续性（使用趋势稳定性）
        df['profit_consistency'] = df['close'].rolling(window=250).apply(
            lambda x: 1 if len(x[x > 0]) == len(x) else 0
        )
        
        # 计算内在价值（格雷厄姆公式简化版）
        # 内在价值 = 净资产 × (1 + ROE)
        df['simulated_intrinsic_value'] = df['simulated_net_asset'] * (1 + df['simulated_roe'])
        
        # 计算安全边际
        df['margin_of_safety'] = (df['simulated_intrinsic_value'] - df['close']) / df['close']
        df['margin_of_safety'] = df['margin_of_safety'].clip(-1, 2)
        
        return df
    
    def check_valuation(self, data: pd.DataFrame, current_idx: int) -> Dict[str, Any]:
        """
        检查估值水平
        
        Returns:
            估值分析结果
        """
        current_data = data.iloc[:current_idx+1]
        
        # PE估值
        pe = current_data['simulated_pe'].iloc[-1]
        pe_score = 1.0 if pe < self.max_pe else 0.0
        
        # PB估值
        pb = current_data['simulated_pb'].iloc[-1]
        pb_score = 1.0 if pb < self.max_pb else 0.0
        
        # 价格/净资产
        current_price = current_data['close'].iloc[-1]
        net_asset = current_data['simulated_net_asset'].iloc[-1]
        price_to_net_asset = current_price / net_asset if net_asset > 0 else 10
        pna_score = 1.0 if price_to_net_asset < self.max_price_to_net_asset else 0.0
        
        valuation_score = (pe_score + pb_score + pna_score) / 3
        
        return {
            "valuation_score": valuation_score,
            "pe": pe,
            "pb": pb,
            "price_to_net_asset": price_to_net_asset,
            "net_asset": net_asset,
            "is_undervalued": valuation_score > 0.6
        }
    
    def check_margin_of_safety(self, data: pd.DataFrame, current_idx: int) -> Dict[str, Any]:
        """
        检查安全边际
        
        Returns:
            安全边际分析结果
        """
        current_data = data.iloc[:current_idx+1]
        
        # 安全边际
        margin = current_data['margin_of_safety'].iloc[-1]
        margin_score = 1.0 if margin > self.min_margin_of_safety else 0.0
        
        # 内在价值比率
        current_price = current_data['close'].iloc[-1]
        intrinsic_value = current_data['simulated_intrinsic_value'].iloc[-1]
        iv_ratio = intrinsic_value / current_price if current_price > 0 else 0
        iv_score = 1.0 if iv_ratio > self.min_intrinsic_value_ratio else 0.0
        
        safety_score = (margin_score + iv_score) / 2
        
        return {
            "safety_score": safety_score,
            "margin_of_safety": margin,
            "intrinsic_value": intrinsic_value,
            "intrinsic_value_ratio": iv_ratio,
            "current_price": current_price,
            "has_safety_margin": safety_score > 0.5
        }
    
    def check_financial_strength(self, data: pd.DataFrame, current_idx: int) -> Dict[str, Any]:
        """
        检查财务实力
        
        Returns:
            财务实力分析结果
        """
        current_data = data.iloc[:current_idx+1]
        
        # 流动比率
        current_ratio = current_data['simulated_current_ratio'].iloc[-1]
        current_score = 1.0 if current_ratio > self.min_current_ratio else 0.0
        
        # 速动比率
        quick_ratio = current_data['simulated_quick_ratio'].iloc[-1]
        quick_score = 1.0 if quick_ratio > self.min_quick_ratio else 0.0
        
        # 负债率
        debt_ratio = current_data['simulated_debt_ratio'].iloc[-1]
        debt_score = 1.0 if debt_ratio < self.max_debt_ratio else 0.0
        
        strength_score = (current_score + quick_score + debt_score) / 3
        
        return {
            "strength_score": strength_score,
            "current_ratio": current_ratio,
            "quick_ratio": quick_ratio,
            "debt_ratio": debt_ratio,
            "is_strong": strength_score > 0.6
        }
    
    def check_profitability(self, data: pd.DataFrame, current_idx: int) -> Dict[str, Any]:
        """
        检查盈利能力
        
        Returns:
            盈利能力分析结果
        """
        current_data = data.iloc[:current_idx+1]
        
        # ROE
        roe = current_data['simulated_roe'].iloc[-1]
        roe_score = 1.0 if roe > self.min_roe else 0.0
        
        # 股息率
        dividend_yield = current_data['simulated_dividend_yield'].iloc[-1]
        dividend_score = 1.0 if dividend_yield > self.min_dividend_yield else 0.0
        
        # 盈利持续性
        profit_consistency = current_data['profit_consistency'].iloc[-250:].mean()
        consistency_score = 1.0 if profit_consistency > 0.8 else 0.0
        
        profitability_score = (roe_score + dividend_score + consistency_score) / 3
        
        return {
            "profitability_score": profitability_score,
            "roe": roe,
            "dividend_yield": dividend_yield,
            "profit_consistency": profit_consistency,
            "is_profitable": profitability_score > 0.6
        }
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> Optional[StrategySignal]:
        """
        生成交易信号
        
        买入条件：
        1. 极低估值
        2. 充足安全边际
        3. 财务稳健
        4. 持续盈利
        5. 当前无持仓
        
        卖出条件：
        1. 价格接近或超过内在价值
        2. 基本面恶化
        3. 持有时间过长
        4. 达到止损/止盈
        """
        # 使用数据长度作为索引
        current_idx = len(data) - 1
        
        if current_idx < 250:  # 需要足够的历史数据
            return StrategySignal(
                signal_type=SignalType.HOLD,
                confidence=0.0,
                reason="数据不足，需要至少250个交易日"
            )
        
        current_data = data.iloc[:current_idx+1]
        current_price = current_data['close'].iloc[-1]
        current_date = current_data.index[-1]
        
        # 分析各项指标
        valuation = self.check_valuation(data, current_idx)
        safety = self.check_margin_of_safety(data, current_idx)
        strength = self.check_financial_strength(data, current_idx)
        profitability = self.check_profitability(data, current_idx)
        
        # 买入逻辑
        if self.holding_position is None:
            # 检查是否满足买入条件（格雷厄姆标准非常严格）
            if (valuation['is_undervalued'] and
                safety['has_safety_margin'] and
                strength['is_strong'] and
                profitability['is_profitable']):
                
                # 计算综合得分
                total_score = (
                    valuation['valuation_score'] * 0.30 +
                    safety['safety_score'] * 0.35 +
                    strength['strength_score'] * 0.20 +
                    profitability['profitability_score'] * 0.15
                )
                
                confidence = min(total_score, 0.95)
                position_size = self.max_position * confidence
                
                # 生成买入信号
                reasons = [
                    f"估值水平: PE={valuation['pe']:.1f}, PB={valuation['pb']:.2f}",
                    f"安全边际: {safety['margin_of_safety']:.2%}",
                    f"内在价值: ¥{safety['intrinsic_value']:.2f} vs 当前价格: ¥{current_price:.2f}",
                    f"内在价值比率: {safety['intrinsic_value_ratio']:.2f}x",
                    f"财务实力: 流动比率={strength['current_ratio']:.2f}, 负债率={strength['debt_ratio']:.2%}",
                    f"盈利能力: ROE={profitability['roe']:.2%}, 股息率={profitability['dividend_yield']:.2%}",
                    f"综合得分: {total_score:.2f}"
                ]
                
                # 更新持仓状态
                self.holding_position = True
                self.entry_date = current_date
                self.entry_price = current_price
                self.intrinsic_value = safety['intrinsic_value']
                
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=confidence,
                    price=current_price,
                    stop_loss=current_price * (1 - self.stop_loss_pct),
                    take_profit=current_price * (1 + self.take_profit_pct),
                    reason="\n".join(reasons),
                    timestamp=current_date,
                    metadata={
                        "valuation": valuation,
                        "safety": safety,
                        "strength": strength,
                        "profitability": profitability,
                        "position_size": position_size
                    }
                )
        
        # 卖出逻辑
        else:
            holding_days = (current_date - self.entry_date).days
            profit_pct = (current_price - self.entry_price) / self.entry_price
            
            should_sell = False
            sell_reasons = []
            
            # 检查价值回归
            if current_price >= self.intrinsic_value * 0.95:  # 接近内在价值
                should_sell = True
                sell_reasons.append(f"价格接近内在价值（¥{current_price:.2f} vs ¥{self.intrinsic_value:.2f}）")
            
            # 检查目标回报
            if profit_pct >= self.target_return:
                should_sell = True
                sell_reasons.append(f"达到目标回报（{profit_pct:.2%}）")
            
            # 检查基本面恶化
            if not strength['is_strong']:
                should_sell = True
                sell_reasons.append(f"财务实力下降（得分: {strength['strength_score']:.2f}）")
            
            if not profitability['is_profitable']:
                should_sell = True
                sell_reasons.append(f"盈利能力下降（得分: {profitability['profitability_score']:.2f}）")
            
            # 检查持有时间
            if holding_days >= self.max_holding_days:
                should_sell = True
                sell_reasons.append(f"达到最长持有期（{holding_days}天）")
            
            # 检查止损止盈
            if profit_pct <= -self.stop_loss_pct:
                should_sell = True
                sell_reasons.append(f"触发止损（亏损: {profit_pct:.2%}）")
            
            if profit_pct >= self.take_profit_pct:
                should_sell = True
                sell_reasons.append(f"触发止盈（盈利: {profit_pct:.2%}）")
            
            if should_sell:
                # 重置持仓状态
                self.holding_position = None
                self.entry_date = None
                self.entry_price = 0
                self.intrinsic_value = 0
                
                return StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.90,
                    price=current_price,
                    reason="\n".join(sell_reasons),
                    timestamp=current_date,
                    metadata={
                        "holding_days": holding_days,
                        "profit_pct": profit_pct,
                        "entry_price": self.entry_price,
                        "entry_intrinsic_value": self.intrinsic_value,
                        "exit_intrinsic_value": safety['intrinsic_value']
                    }
                )
        
        # 默认持有，不操作
        return StrategySignal(
            signal_type=SignalType.HOLD,
            confidence=0.5,
            price=current_data['close'].iloc[-1],
            reason="持续持有或暂无交易机会",
            timestamp=current_data.index[-1]
        )
    
    def generate_signals(self, data: pd.DataFrame) -> List[StrategySignal]:
        """
        生成所有交易信号
        
        Args:
            data: 历史数据
            
        Returns:
            信号列表
        """
        # 计算指标
        data_with_indicators = self.calculate_indicators(data)
        
        signals = []
        
        # 遍历数据生成信号
        for i in range(250, len(data_with_indicators)):
            signal = self.generate_signal(data_with_indicators, i)
            if signal:
                signals.append(signal)
        
        return signals
