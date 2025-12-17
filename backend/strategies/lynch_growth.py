"""
彼得林奇成长股策略 (Peter Lynch Growth Strategy)
寻找PEG<1的成长股，合理价格买入成长

核心理念：
1. PEG估值法：PEG = PE / 增长率
2. PEG<1是最佳买入时机
3. 寻找细分市场龙头
4. 关注成长性和财务质量

投资标准：
- 成长性指标：营收增长率>20%、净利润增长率>25%、连续3年增长
- PEG估值：PEG<1（最佳）、PEG<1.5（可接受）
- 行业地位：细分市场龙头、市场份额增长、竞争优势明显
- 财务质量：现金流正向、应收账款合理、存货周转快

持有策略：
- 中期持有（1-2年）
- PEG>2时卖出
- 增长放缓时卖出
- 行业地位下降时卖出
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


@register_strategy("lynch_growth")
class LynchGrowthStrategy(BaseStrategy):
    """
    彼得林奇成长股策略
    
    选股标准：
    1. PEG<1（最佳）或PEG<1.5（可接受）
    2. 营收和利润持续高增长
    3. 细分市场龙头地位
    4. 财务质量优秀
    
    持有策略：
    - 中期持有（1-2年）
    - PEG>2或增长放缓时卖出
    """
    
    # 策略描述属性
    description = "PEG<1的成长股，在合理价格买入高成长企业"
    
    def __init__(self, config: StrategyConfig):
        super().__init__(config)
        
        # 设置中文名称和分类
        self.name = "彼得林奇成长股"
        self.category = "价值投资"
        
        # PEG估值标准
        self.best_peg = self.parameters.get('best_peg', 1.0)  # 最佳PEG
        self.acceptable_peg = self.parameters.get('acceptable_peg', 1.5)  # 可接受PEG
        self.sell_peg = self.parameters.get('sell_peg', 2.0)  # 卖出PEG阈值
        
        # 成长性标准
        self.min_revenue_growth = self.parameters.get('min_revenue_growth', 0.20)  # 最低营收增长 20%
        self.min_profit_growth = self.parameters.get('min_profit_growth', 0.25)  # 最低利润增长 25%
        self.growth_consistency_years = self.parameters.get('growth_consistency_years', 3)  # 增长持续年数
        
        # 行业地位标准
        self.min_market_share_growth = self.parameters.get('min_market_share_growth', 0.05)  # 市场份额增长
        
        # 财务质量标准
        self.min_cash_flow_ratio = self.parameters.get('min_cash_flow_ratio', 0.10)  # 现金流比率
        self.max_receivables_ratio = self.parameters.get('max_receivables_ratio', 0.30)  # 应收账款比率
        
        # 持有策略
        self.min_holding_days = self.parameters.get('min_holding_days', 180)  # 最短持有天数（6个月）
        self.max_holding_days = self.parameters.get('max_holding_days', 730)  # 最长持有天数（2年）
        
        # 风险参数
        self.max_position = self.parameters.get('max_position', 0.35)  # 最大仓位 35%
        self.stop_loss_pct = self.parameters.get('stop_loss', 0.25)  # 止损 -25%
        self.take_profit_pct = self.parameters.get('take_profit', 1.50)  # 止盈 +150%
        
        # 内部状态
        self.holding_position = None
        self.entry_date = None
        self.entry_price = 0
        self.entry_peg = 0
        
    def initialize(self, data: pd.DataFrame):
        """初始化策略"""
        self._initialized = True
    
    def get_required_indicators(self) -> List[str]:
        """返回策略所需指标"""
        return [
            "revenue_growth",
            "earnings_growth",
            "pe_ratio",
            "peg_ratio",
            "roe"
        ]
        
    def calculate_indicators(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        计算技术指标和成长性指标
        
        注：实际应用中需要接入财报数据API
        这里使用技术指标模拟成长性指标
        """
        df = data.copy()
        
        # 技术指标
        df['sma_20'] = df['close'].rolling(window=20).mean()
        df['sma_60'] = df['close'].rolling(window=60).mean()
        df['sma_120'] = df['close'].rolling(window=120).mean()
        
        # 模拟成长性指标（实际应从财报数据获取）
        
        # 模拟营收增长率（使用价格上涨速度）
        df['price_growth_60d'] = df['close'].pct_change(60)
        df['price_growth_120d'] = df['close'].pct_change(120)
        df['simulated_revenue_growth'] = (df['price_growth_60d'] + df['price_growth_120d']) / 2
        
        # 模拟利润增长率（使用成交量增长）
        df['volume_growth_60d'] = df['volume'].pct_change(60)
        df['volume_growth_120d'] = df['volume'].pct_change(120)
        df['simulated_profit_growth'] = (df['volume_growth_60d'] + df['volume_growth_120d']) / 2
        
        # 模拟PE（使用价格相对位置）
        df['price_percentile'] = df['close'].rolling(window=250).apply(
            lambda x: (x.iloc[-1] - x.min()) / (x.max() - x.min()) if (x.max() - x.min()) > 0 else 0.5
        )
        df['simulated_pe'] = 15 + df['price_percentile'] * 25  # PE在15-40之间
        
        # 计算PEG（PE / 增长率）
        # 增长率使用百分比形式
        df['growth_rate_pct'] = df['simulated_revenue_growth'] * 100
        df['simulated_peg'] = df['simulated_pe'] / df['growth_rate_pct'].abs()
        df['simulated_peg'] = df['simulated_peg'].replace([np.inf, -np.inf], 10)  # 处理无穷大
        df['simulated_peg'] = df['simulated_peg'].clip(0, 10)  # 限制在0-10之间
        
        # 模拟市场份额增长（使用相对强度）
        df['relative_strength'] = df['close'] / df['sma_120']
        df['simulated_market_share_growth'] = (df['relative_strength'] - 1) * 0.5
        
        # 模拟现金流（使用成交量稳定性）
        df['volume_std'] = df['volume'].rolling(window=60).std()
        df['volume_mean'] = df['volume'].rolling(window=60).mean()
        df['simulated_cash_flow_ratio'] = 0.15 * (1 - df['volume_std'] / df['volume_mean'])
        
        # 模拟应收账款比率（使用价格波动率）
        df['returns'] = df['close'].pct_change()
        df['volatility'] = df['returns'].rolling(window=60).std()
        df['simulated_receivables_ratio'] = df['volatility'] * 5
        
        # 增长一致性（使用价格趋势稳定性）
        df['trend_consistency'] = df['close'].rolling(window=90).apply(
            lambda x: 1 if (x.iloc[-1] > x.iloc[0] and all(x.diff().dropna() > -x.mean() * 0.05)) else 0
        )
        
        return df
    
    def calculate_peg(self, data: pd.DataFrame, current_idx: int) -> Dict[str, Any]:
        """
        计算PEG及相关指标
        
        Returns:
            PEG分析结果
        """
        current_data = data.iloc[:current_idx+1]
        
        # 获取当前PEG
        current_peg = current_data['simulated_peg'].iloc[-1]
        
        # 获取PE和增长率
        current_pe = current_data['simulated_pe'].iloc[-1]
        revenue_growth = current_data['simulated_revenue_growth'].iloc[-1]
        profit_growth = current_data['simulated_profit_growth'].iloc[-1]
        
        # 平均增长率
        avg_growth = (revenue_growth + profit_growth) / 2
        
        # PEG评分
        if current_peg < self.best_peg:
            peg_score = 1.0
            peg_rating = "优秀"
        elif current_peg < self.acceptable_peg:
            peg_score = 0.7
            peg_rating = "良好"
        elif current_peg < self.sell_peg:
            peg_score = 0.4
            peg_rating = "一般"
        else:
            peg_score = 0.0
            peg_rating = "偏高"
        
        return {
            "peg": current_peg,
            "peg_score": peg_score,
            "peg_rating": peg_rating,
            "pe": current_pe,
            "revenue_growth": revenue_growth,
            "profit_growth": profit_growth,
            "avg_growth": avg_growth,
            "is_attractive": current_peg < self.acceptable_peg
        }
    
    def check_growth_quality(self, data: pd.DataFrame, current_idx: int) -> Dict[str, Any]:
        """
        检查成长质量
        
        Returns:
            成长质量分析结果
        """
        current_data = data.iloc[:current_idx+1]
        
        # 营收增长
        revenue_growth = current_data['simulated_revenue_growth'].iloc[-1]
        revenue_score = 1.0 if revenue_growth > self.min_revenue_growth else 0.0
        
        # 利润增长
        profit_growth = current_data['simulated_profit_growth'].iloc[-1]
        profit_score = 1.0 if profit_growth > self.min_profit_growth else 0.0
        
        # 增长一致性（检查过去90天）
        recent_consistency = current_data['trend_consistency'].iloc[-90:].mean()
        consistency_score = 1.0 if recent_consistency > 0.7 else 0.0
        
        # 增长加速度（增长率是否在提升）
        growth_60d = current_data['price_growth_60d'].iloc[-1]
        growth_120d = current_data['price_growth_120d'].iloc[-1]
        is_accelerating = growth_60d > growth_120d
        acceleration_score = 1.0 if is_accelerating else 0.5
        
        growth_score = (revenue_score + profit_score + consistency_score + acceleration_score) / 4
        
        return {
            "growth_score": growth_score,
            "revenue_growth": revenue_growth,
            "profit_growth": profit_growth,
            "consistency": recent_consistency,
            "is_accelerating": is_accelerating,
            "is_high_quality": growth_score > 0.6
        }
    
    def check_market_position(self, data: pd.DataFrame, current_idx: int) -> Dict[str, Any]:
        """
        检查市场地位
        
        Returns:
            市场地位分析结果
        """
        current_data = data.iloc[:current_idx+1]
        
        # 市场份额增长
        market_share_growth = current_data['simulated_market_share_growth'].iloc[-1]
        share_score = 1.0 if market_share_growth > self.min_market_share_growth else 0.0
        
        # 相对强度（vs市场）
        relative_strength = current_data['relative_strength'].iloc[-1]
        strength_score = 1.0 if relative_strength > 1.1 else 0.5
        
        # 趋势强度
        is_uptrend = (current_data['close'].iloc[-1] > current_data['sma_20'].iloc[-1] and
                      current_data['sma_20'].iloc[-1] > current_data['sma_60'].iloc[-1] and
                      current_data['sma_60'].iloc[-1] > current_data['sma_120'].iloc[-1])
        trend_score = 1.0 if is_uptrend else 0.0
        
        position_score = (share_score + strength_score + trend_score) / 3
        
        return {
            "position_score": position_score,
            "market_share_growth": market_share_growth,
            "relative_strength": relative_strength,
            "is_uptrend": is_uptrend,
            "is_leader": position_score > 0.6
        }
    
    def check_financial_quality(self, data: pd.DataFrame, current_idx: int) -> Dict[str, Any]:
        """
        检查财务质量
        
        Returns:
            财务质量分析结果
        """
        current_data = data.iloc[:current_idx+1]
        
        # 现金流
        cash_flow_ratio = current_data['simulated_cash_flow_ratio'].iloc[-1]
        cash_score = 1.0 if cash_flow_ratio > self.min_cash_flow_ratio else 0.0
        
        # 应收账款
        receivables_ratio = current_data['simulated_receivables_ratio'].iloc[-1]
        receivables_score = 1.0 if receivables_ratio < self.max_receivables_ratio else 0.0
        
        # 波动率（财务稳定性）
        volatility = current_data['volatility'].iloc[-1]
        stability_score = 1.0 if volatility < 0.03 else 0.5
        
        quality_score = (cash_score + receivables_score + stability_score) / 3
        
        return {
            "quality_score": quality_score,
            "cash_flow_ratio": cash_flow_ratio,
            "receivables_ratio": receivables_ratio,
            "volatility": volatility,
            "is_high_quality": quality_score > 0.6
        }
    
    def generate_signal(self, data: pd.DataFrame, current_position: int = 0) -> Optional[StrategySignal]:
        """
        生成交易信号
        
        买入条件：
        1. PEG<1.5
        2. 成长质量高
        3. 市场地位领先
        4. 财务质量优秀
        5. 当前无持仓
        
        卖出条件：
        1. 持有时间>最短持有期 且 (PEG>2 或 增长放缓 或 市场地位下降)
        2. 持有时间>最长持有期
        3. 达到止损/止盈
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
        peg_analysis = self.calculate_peg(data, current_idx)
        growth_analysis = self.check_growth_quality(data, current_idx)
        position_analysis = self.check_market_position(data, current_idx)
        quality_analysis = self.check_financial_quality(data, current_idx)
        
        # 买入逻辑
        if self.holding_position is None:
            # 检查是否满足买入条件
            if (peg_analysis['is_attractive'] and
                growth_analysis['is_high_quality'] and
                position_analysis['is_leader'] and
                quality_analysis['is_high_quality']):
                
                # 计算综合得分
                total_score = (
                    peg_analysis['peg_score'] * 0.35 +
                    growth_analysis['growth_score'] * 0.30 +
                    position_analysis['position_score'] * 0.20 +
                    quality_analysis['quality_score'] * 0.15
                )
                
                confidence = min(total_score, 0.95)
                position_size = self.max_position * confidence
                
                # 生成买入信号
                reasons = [
                    f"PEG估值: {peg_analysis['peg']:.2f} ({peg_analysis['peg_rating']})",
                    f"PE: {peg_analysis['pe']:.1f}, 增长率: {peg_analysis['avg_growth']:.2%}",
                    f"成长质量: {growth_analysis['growth_score']:.2f} (营收增长: {growth_analysis['revenue_growth']:.2%})",
                    f"市场地位: {position_analysis['position_score']:.2f} (相对强度: {position_analysis['relative_strength']:.2f})",
                    f"财务质量: {quality_analysis['quality_score']:.2f}",
                    f"综合得分: {total_score:.2f}"
                ]
                
                # 更新持仓状态
                self.holding_position = True
                self.entry_date = current_date
                self.entry_price = current_price
                self.entry_peg = peg_analysis['peg']
                
                return StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=confidence,
                    price=current_price,
                    stop_loss=current_price * (1 - self.stop_loss_pct),
                    take_profit=current_price * (1 + self.take_profit_pct),
                    reason="\n".join(reasons),
                    timestamp=current_date,
                    metadata={
                        "peg_analysis": peg_analysis,
                        "growth_analysis": growth_analysis,
                        "position_analysis": position_analysis,
                        "quality_analysis": quality_analysis,
                        "position_size": position_size
                    }
                )
        
        # 卖出逻辑
        else:
            holding_days = (current_date - self.entry_date).days
            profit_pct = (current_price - self.entry_price) / self.entry_price
            
            should_sell = False
            sell_reasons = []
            
            # 检查持有时间
            if holding_days >= self.max_holding_days:
                should_sell = True
                sell_reasons.append(f"达到最长持有期（{holding_days}天）")
            
            # 检查各项指标（需要持有超过最短期限）
            if holding_days >= self.min_holding_days:
                # PEG过高
                if peg_analysis['peg'] > self.sell_peg:
                    should_sell = True
                    sell_reasons.append(f"PEG过高（{peg_analysis['peg']:.2f} > {self.sell_peg}）")
                
                # 增长放缓
                if not growth_analysis['is_high_quality']:
                    should_sell = True
                    sell_reasons.append(f"增长放缓（得分: {growth_analysis['growth_score']:.2f}）")
                
                # 市场地位下降
                if not position_analysis['is_leader']:
                    should_sell = True
                    sell_reasons.append(f"市场地位下降（得分: {position_analysis['position_score']:.2f}）")
            
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
                self.entry_peg = 0
                
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
                        "entry_peg": self.entry_peg,
                        "exit_peg": peg_analysis['peg']
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
