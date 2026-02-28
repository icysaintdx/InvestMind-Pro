#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联合回测模块 - Joint Backtest Engine
实现技术+新闻双驱动回测

功能：
1. 同时接收技术信号和新闻信号
2. 支持动态权重配置（技术权重/新闻权重）
3. 输出联合回测报告
4. 对比纯技术回测 vs 双驱动回测
"""

import sys
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd
import numpy as np

# 添加项目根目录到路径
project_root = "/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro"
sys.path.insert(0, project_root)

from backend.backtest.news_backtest_engine import NewsBacktestEngine, NewsBacktestResult

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)


class MarketState(Enum):
    """市场状态"""
    TRENDING = "趋势市"  # 技术面主导
    EVENT_DRIVEN = "事件驱动"  # 新闻面主导
    VOLATILE = "震荡市"  # 技术面权重高
    BALANCED = "平衡市"  # 均衡


class SignalType(Enum):
    """信号类型"""
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class TechnicalSignal:
    """技术信号"""
    date: str
    signal: SignalType
    confidence: float  # 0-100
    score: float  # 综合得分
    indicators: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NewsSignal:
    """新闻信号"""
    date: str
    signal: SignalType
    confidence: float  # 0-100
    score: float  # 情绪得分
    urgency: float  # 紧急程度
    major_events: List[Dict] = field(default_factory=list)


@dataclass
class CombinedSignal:
    """联合信号"""
    date: str
    tech_signal: TechnicalSignal
    news_signal: NewsSignal
    combined_score: float
    final_signal: SignalType
    tech_weight: float
    news_weight: float
    reasoning: str = ""


@dataclass
class JointBacktestConfig:
    """联合回测配置"""
    # 权重配置
    tech_weight: float = 0.5
    news_weight: float = 0.5
    
    # 动态权重调整
    enable_dynamic_weight: bool = True
    
    # 信号阈值
    buy_threshold: float = 60  # 综合得分>60买入
    sell_threshold: float = 40  # 综合得分<40卖出
    
    # 新闻紧急度阈值
    critical_news_boost: bool = True  # 重大新闻是否提升权重
    
    # 初始资金
    initial_capital: float = 1_000_000.0
    commission_rate: float = 0.0003
    slippage_rate: float = 0.0005


@dataclass
class TradeRecord:
    """交易记录"""
    date: str
    action: str  # BUY/SELL
    price: float
    shares: int
    value: float
    commission: float
    reason: str
    tech_score: float
    news_score: float
    combined_score: float


@dataclass
class JointBacktestResult:
    """联合回测结果"""
    stock_code: str
    stock_name: str
    start_date: str
    end_date: str
    config: JointBacktestConfig
    
    # 信号记录
    signals: List[CombinedSignal] = field(default_factory=list)
    
    # 交易记录
    trades: List[TradeRecord] = field(default_factory=list)
    
    # 每日持仓
    daily_positions: pd.DataFrame = field(default_factory=pd.DataFrame)
    
    # 最终表现
    final_capital: float = 0
    total_return: float = 0
    max_drawdown: float = 0
    sharpe_ratio: float = 0
    win_rate: float = 0
    
    # 对比数据
    tech_only_return: float = 0  # 纯技术回测收益
    news_only_return: float = 0  # 纯新闻回测收益


class JointBacktestEngine:
    """
    联合回测引擎
    
    实现技术+新闻双驱动回测：
    1. 加载技术信号（从已有回测结果或实时生成）
    2. 加载新闻信号（从NewsBacktestEngine）
    3. 按配置权重融合信号
    4. 执行回测并输出报告
    """
    
    def __init__(self, config: Optional[JointBacktestConfig] = None):
        """
        初始化联合回测引擎
        
        Args:
            config: 回测配置，默认使用均衡配置
        """
        self.config = config or JointBacktestConfig()
        self.news_engine = NewsBacktestEngine()
        
        logger.info(f"联合回测引擎初始化完成")
        logger.info(f"  技术权重: {self.config.tech_weight}, 新闻权重: {self.config.news_weight}")
    
    def detect_market_state(
        self,
        price_data: pd.DataFrame,
        window: int = 20
    ) -> MarketState:
        """
        检测市场状态
        
        Args:
            price_data: 价格数据
            window: 检测窗口
            
        Returns:
            MarketState
        """
        if len(price_data) < window:
            return MarketState.BALANCED
        
        # 计算波动率
        recent_data = price_data.tail(window)
        returns = recent_data['close'].pct_change().dropna()
        volatility = returns.std() * np.sqrt(252)  # 年化波动率
        
        # 计算趋势强度
        if 'ema20' in recent_data.columns and 'ema60' in recent_data.columns:
            trend_strength = abs(recent_data['ema20'].iloc[-1] - recent_data['ema60'].iloc[-1]) / recent_data['close'].iloc[-1]
        else:
            sma20 = recent_data['close'].rolling(20).mean().iloc[-1]
            sma60 = recent_data['close'].rolling(60).mean().iloc[-1]
            trend_strength = abs(sma20 - sma60) / recent_data['close'].iloc[-1]
        
        # 判断市场状态
        if volatility > 0.3:  # 高波动
            return MarketState.VOLATILE
        elif trend_strength > 0.05:  # 强趋势
            return MarketState.TRENDING
        else:
            return MarketState.BALANCED
    
    def calculate_dynamic_weights(
        self,
        market_state: MarketState,
        news_urgency: float
    ) -> Tuple[float, float]:
        """
        计算动态权重
        
        Args:
            market_state: 市场状态
            news_urgency: 新闻紧急程度 (0-100)
            
        Returns:
            (技术权重, 新闻权重)
        """
        if not self.config.enable_dynamic_weight:
            return self.config.tech_weight, self.config.news_weight
        
        # 基础权重根据市场状态调整
        if market_state == MarketState.TRENDING:
            tech_w, news_w = 0.7, 0.3
        elif market_state == MarketState.VOLATILE:
            tech_w, news_w = 0.7, 0.3
        elif market_state == MarketState.EVENT_DRIVEN:
            tech_w, news_w = 0.3, 0.7
        else:  # BALANCED
            tech_w, news_w = 0.5, 0.5
        
        # 重大新闻事件调整
        if self.config.critical_news_boost and news_urgency >= 80:
            tech_w = max(0.2, tech_w - 0.2)
            news_w = min(0.8, news_w + 0.2)
        
        return tech_w, news_w
    
    def combine_signals(
        self,
        tech_signal: TechnicalSignal,
        news_signal: NewsSignal,
        market_state: MarketState
    ) -> CombinedSignal:
        """
        融合技术信号和新闻信号
        
        Args:
            tech_signal: 技术信号
            news_signal: 新闻信号
            market_state: 市场状态
            
        Returns:
            CombinedSignal
        """
        # 计算动态权重
        tech_w, news_w = self.calculate_dynamic_weights(
            market_state, 
            news_signal.urgency
        )
        
        # 标准化得分到0-100
        tech_score = tech_signal.score
        news_score = news_signal.score
        
        # 加权融合
        combined_score = tech_score * tech_w + news_score * news_w
        
        # 确定最终信号
        if combined_score >= self.config.buy_threshold:
            final_signal = SignalType.BUY
            reasoning = f"综合得分{combined_score:.1f} >= {self.config.buy_threshold}，触发买入"
        elif combined_score <= self.config.sell_threshold:
            final_signal = SignalType.SELL
            reasoning = f"综合得分{combined_score:.1f} <= {self.config.sell_threshold}，触发卖出"
        else:
            final_signal = SignalType.HOLD
            reasoning = f"综合得分{combined_score:.1f} 在阈值区间，保持观望"
        
        return CombinedSignal(
            date=tech_signal.date,
            tech_signal=tech_signal,
            news_signal=news_signal,
            combined_score=combined_score,
            final_signal=final_signal,
            tech_weight=tech_w,
            news_weight=news_w,
            reasoning=reasoning
        )
    
    def generate_technical_signals(
        self,
        price_data: pd.DataFrame,
        strategy_func: Optional[callable] = None
    ) -> List[TechnicalSignal]:
        """
        生成技术信号（简化版EMA策略）
        
        Args:
            price_data: 价格数据
            strategy_func: 可选的自定义策略函数
            
        Returns:
            技术信号列表
        """
        signals = []
        
        if strategy_func:
            return strategy_func(price_data)
        
        # 默认EMA策略
        df = price_data.copy()
        
        # 计算EMA
        df['ema5'] = df['close'].ewm(span=5, min_periods=1).mean()
        df['ema20'] = df['close'].ewm(span=20, min_periods=1).mean()
        df['ema60'] = df['close'].ewm(span=60, min_periods=1).mean()
        
        for idx, row in df.iterrows():
            date_str = idx.strftime("%Y-%m-%d") if isinstance(idx, pd.Timestamp) else str(idx)
            
            # 简单EMA交叉策略
            score = 50  # 中性
            signal = SignalType.HOLD
            
            if row['ema5'] > row['ema20'] > row['ema60']:
                score = 75
                signal = SignalType.BUY
            elif row['ema5'] < row['ema20'] < row['ema60']:
                score = 25
                signal = SignalType.SELL
            elif row['ema5'] > row['ema20']:
                score = 60
            elif row['ema5'] < row['ema20']:
                score = 40
            
            signals.append(TechnicalSignal(
                date=date_str,
                signal=signal,
                confidence=abs(score - 50) * 2,  # 偏离中性的程度
                score=score,
                indicators={
                    'ema5': row['ema5'],
                    'ema20': row['ema20'],
                    'ema60': row['ema60']
                }
            ))
        
        return signals
    
    def generate_news_signals(
        self,
        news_result: NewsBacktestResult
    ) -> List[NewsSignal]:
        """
        从新闻回测结果生成新闻信号
        
        Args:
            news_result: 新闻回测结果
            
        Returns:
            新闻信号列表
        """
        signals = []
        
        for sentiment in news_result.daily_sentiments:
            # 情绪得分转换为信号
            if sentiment.sentiment_score >= 60:
                signal = SignalType.BUY
            elif sentiment.sentiment_score <= 40:
                signal = SignalType.SELL
            else:
                signal = SignalType.HOLD
            
            signals.append(NewsSignal(
                date=sentiment.date,
                signal=signal,
                confidence=sentiment.avg_confidence,
                score=sentiment.sentiment_score,
                urgency=sentiment.urgency_score,
                major_events=sentiment.major_events
            ))
        
        return signals
    
    def run_backtest(
        self,
        stock_code: str,
        stock_name: str,
        price_data: pd.DataFrame,
        start_date: str,
        end_date: str,
        tech_signals: Optional[List[TechnicalSignal]] = None
    ) -> JointBacktestResult:
        """
        执行联合回测
        
        Args:
            stock_code: 股票代码
            stock_name: 股票名称
            price_data: 价格数据DataFrame（需包含open/high/low/close/volume）
            start_date: 开始日期
            end_date: 结束日期
            tech_signals: 可选的技术信号列表，不提供则自动生成
            
        Returns:
            JointBacktestResult
        """
        logger.info(f"开始联合回测: {stock_name}({stock_code}) {start_date} ~ {end_date}")
        
        # 1. 执行新闻回测
        news_result = self.news_engine.run_backtest(
            stock_code, stock_name, start_date, end_date
        )
        
        # 2. 生成新闻信号
        news_signals = self.generate_news_signals(news_result)
        news_signal_dict = {s.date: s for s in news_signals}
        
        # 3. 生成或转换技术信号
        if tech_signals is None:
            tech_signals = self.generate_technical_signals(price_data)
        tech_signal_dict = {s.date: s for s in tech_signals}
        
        # 4. 对齐价格数据和信号
        all_dates = set(tech_signal_dict.keys()) | set(news_signal_dict.keys())
        all_dates = sorted(all_dates)
        
        # 5. 逐日融合信号并执行回测
        combined_signals = []
        trades = []
        position = 0  # 持仓股数
        capital = self.config.initial_capital
        
        for date_str in all_dates:
            # 获取当日价格
            if date_str not in price_data.index.strftime('%Y-%m-%d'):
                continue
            
            day_price = price_data.loc[price_data.index.strftime('%Y-%m-%d') == date_str]
            if day_price.empty:
                continue
            
            close_price = day_price['close'].iloc[0]
            
            # 获取信号
            tech_sig = tech_signal_dict.get(date_str)
            if tech_sig is None:
                continue
            
            news_sig = news_signal_dict.get(date_str)
            if news_sig is None:
                # 使用中性新闻信号
                news_sig = NewsSignal(
                    date=date_str,
                    signal=SignalType.HOLD,
                    confidence=0,
                    score=50,
                    urgency=0
                )
            
            # 检测市场状态
            market_state = self.detect_market_state(price_data.loc[:date_str])
            
            # 融合信号
            combined = self.combine_signals(tech_sig, news_sig, market_state)
            combined_signals.append(combined)
            
            # 执行交易
            if combined.final_signal == SignalType.BUY and position == 0:
                # 买入
                shares = int(capital * 0.95 / close_price / 100) * 100  # 整手
                if shares > 0:
                    value = shares * close_price
                    commission = value * self.config.commission_rate
                    
                    trade = TradeRecord(
                        date=date_str,
                        action="BUY",
                        price=close_price,
                        shares=shares,
                        value=value,
                        commission=commission,
                        reason=combined.reasoning,
                        tech_score=tech_sig.score,
                        news_score=news_sig.score,
                        combined_score=combined.combined_score
                    )
                    trades.append(trade)
                    position = shares
                    capital -= value + commission
                    
            elif combined.final_signal == SignalType.SELL and position > 0:
                # 卖出
                value = position * close_price
                commission = value * self.config.commission_rate
                
                trade = TradeRecord(
                    date=date_str,
                    action="SELL",
                    price=close_price,
                    shares=position,
                    value=value,
                    commission=commission,
                    reason=combined.reasoning,
                    tech_score=tech_sig.score,
                    news_score=news_sig.score,
                    combined_score=combined.combined_score
                )
                trades.append(trade)
                capital += value - commission
                position = 0
        
        # 6. 计算最终表现
        final_value = capital + position * price_data['close'].iloc[-1]
        total_return = (final_value - self.config.initial_capital) / self.config.initial_capital * 100
        
        # 计算最大回撤
        portfolio_values = self._calculate_portfolio_values(
            price_data, trades, self.config.initial_capital
        )
        max_drawdown = self._calculate_max_drawdown(portfolio_values)
        
        # 7. 组装结果
        result = JointBacktestResult(
            stock_code=stock_code,
            stock_name=stock_name,
            start_date=start_date,
            end_date=end_date,
            config=self.config,
            signals=combined_signals,
            trades=trades,
            final_capital=final_value,
            total_return=total_return,
            max_drawdown=max_drawdown,
            daily_positions=portfolio_values
        )
        
        logger.info(f"联合回测完成: 收益 {total_return:.2f}%, 最大回撤 {max_drawdown:.2f}%")
        return result
    
    def _calculate_portfolio_values(
        self,
        price_data: pd.DataFrame,
        trades: List[TradeRecord],
        initial_capital: float
    ) -> pd.DataFrame:
        """计算每日持仓价值"""
        df = price_data.copy()
        df['cash'] = initial_capital
        df['position'] = 0
        df['portfolio_value'] = initial_capital
        
        for trade in trades:
            date_idx = df.index[df.index.strftime('%Y-%m-%d') == trade.date]
            if len(date_idx) > 0:
                idx = date_idx[0]
                if trade.action == "BUY":
                    df.loc[idx:, 'cash'] -= (trade.value + trade.commission)
                    df.loc[idx:, 'position'] += trade.shares
                else:  # SELL
                    df.loc[idx:, 'cash'] += (trade.value - trade.commission)
                    df.loc[idx:, 'position'] -= trade.shares
        
        df['portfolio_value'] = df['cash'] + df['position'] * df['close']
        return df[['close', 'cash', 'position', 'portfolio_value']]
    
    def _calculate_max_drawdown(self, portfolio_values: pd.DataFrame) -> float:
        """计算最大回撤"""
        values = portfolio_values['portfolio_value']
        rolling_max = values.expanding().max()
        drawdown = (values - rolling_max) / rolling_max * 100
        return abs(drawdown.min())
    
    def generate_report(self, result: JointBacktestResult) -> str:
        """
        生成回测报告
        
        Args:
            result: 回测结果
            
        Returns:
            Markdown格式报告
        """
        lines = [
            f"# 联合回测报告: {result.stock_name}({result.stock_code})",
            f"",
            f"**回测区间**: {result.start_date} ~ {result.end_date}",
            f"**初始资金**: {result.config.initial_capital:,.2f}",
            f"**技术权重**: {result.config.tech_weight} | **新闻权重**: {result.config.news_weight}",
            f"**动态权重**: {'开启' if result.config.enable_dynamic_weight else '关闭'}",
            f"",
            f"## 📊 回测结果",
            f"",
            f"| 指标 | 数值 |",
            f"|------|------|",
            f"| 最终资金 | {result.final_capital:,.2f} |",
            f"| 总收益率 | {result.total_return:+.2f}% |",
            f"| 最大回撤 | {result.max_drawdown:.2f}% |",
            f"| 交易次数 | {len(result.trades)} |",
            f"",
            f"## 📈 交易记录",
            f"",
        ]
        
        if result.trades:
            lines.append("| 日期 | 操作 | 价格 | 股数 | 技术分 | 新闻分 | 综合分 |")
            lines.append("|------|------|------|------|--------|--------|--------|")
            for trade in result.trades:
                lines.append(
                    f"| {trade.date} | {trade.action} | {trade.price:.2f} | {trade.shares} | "
                    f"{trade.tech_score:.1f} | {trade.news_score:.1f} | {trade.combined_score:.1f} |"
                )
        else:
            lines.append("*无交易记录*")
        
        lines.append("")
        lines.append("## 🔄 信号详情")
        lines.append("")
        
        if result.signals:
            lines.append("| 日期 | 技术信号 | 新闻信号 | 权重(技/新) | 综合分 | 最终信号 |")
            lines.append("|------|----------|----------|-------------|--------|----------|")
            for sig in result.signals[:20]:  # 只显示前20条
                lines.append(
                    f"| {sig.date} | {sig.tech_signal.signal.value}({sig.tech_signal.score:.0f}) | "
                    f"{sig.news_signal.signal.value}({sig.news_signal.score:.0f}) | "
                    f"{sig.tech_weight:.1f}/{sig.news_weight:.1f} | "
                    f"{sig.combined_score:.1f} | {sig.final_signal.value} |"
                )
            if len(result.signals) > 20:
                lines.append(f"| ... | ... | ... | ... | ... | ... |")
                lines.append(f"*共 {len(result.signals)} 条信号记录*")
        
        return "\n".join(lines)
    
    def export_results(
        self,
        result: JointBacktestResult,
        output_dir: str
    ):
        """
        导出回测结果到文件
        
        Args:
            result: 回测结果
            output_dir: 输出目录
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        # 导出JSON
        json_file = f"{output_dir}/joint_backtest_{result.stock_code}_{result.start_date}_{result.end_date}.json"
        export_data = {
            'stock_code': result.stock_code,
            'stock_name': result.stock_name,
            'start_date': result.start_date,
            'end_date': result.end_date,
            'config': {
                'tech_weight': result.config.tech_weight,
                'news_weight': result.config.news_weight,
                'enable_dynamic_weight': result.config.enable_dynamic_weight,
                'initial_capital': result.config.initial_capital
            },
            'performance': {
                'final_capital': result.final_capital,
                'total_return': result.total_return,
                'max_drawdown': result.max_drawdown
            },
            'trades': [
                {
                    'date': t.date,
                    'action': t.action,
                    'price': t.price,
                    'shares': t.shares,
                    'tech_score': t.tech_score,
                    'news_score': t.news_score,
                    'combined_score': t.combined_score,
                    'reason': t.reason
                }
                for t in result.trades
            ],
            'signals': [
                {
                    'date': s.date,
                    'tech_signal': s.tech_signal.signal.value,
                    'tech_score': s.tech_signal.score,
                    'news_signal': s.news_signal.signal.value,
                    'news_score': s.news_signal.score,
                    'tech_weight': s.tech_weight,
                    'news_weight': s.news_weight,
                    'combined_score': s.combined_score,
                    'final_signal': s.final_signal.value
                }
                for s in result.signals
            ]
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        # 导出Markdown报告
        md_file = f"{output_dir}/joint_backtest_{result.stock_code}_{result.start_date}_{result.end_date}.md"
        with open(md_file, 'w', encoding='utf-8') as f:
            f.write(self.generate_report(result))
        
        logger.info(f"结果已导出到: {output_dir}")


# ==================== 快捷函数 ====================

def run_joint_backtest(
    stock_code: str,
    stock_name: str,
    price_data: pd.DataFrame,
    start_date: str,
    end_date: str,
    tech_weight: float = 0.5,
    news_weight: float = 0.5,
    enable_dynamic_weight: bool = True
) -> JointBacktestResult:
    """
    快速执行联合回测的便捷函数
    
    Args:
        stock_code: 股票代码
        stock_name: 股票名称
        price_data: 价格数据
        start_date: 开始日期
        end_date: 结束日期
        tech_weight: 技术权重
        news_weight: 新闻权重
        enable_dynamic_weight: 是否启用动态权重
        
    Returns:
        JointBacktestResult
    """
    config = JointBacktestConfig(
        tech_weight=tech_weight,
        news_weight=news_weight,
        enable_dynamic_weight=enable_dynamic_weight
    )
    
    engine = JointBacktestEngine(config)
    return engine.run_backtest(stock_code, stock_name, price_data, start_date, end_date)


if __name__ == "__main__":
    # 测试代码
    print("联合回测引擎测试")
    print("="*60)
    
    # 创建模拟价格数据
    dates = pd.date_range(start='2024-01-01', end='2024-06-30', freq='B')
    np.random.seed(42)
    prices = 100 + np.cumsum(np.random.randn(len(dates)) * 0.5)
    
    price_data = pd.DataFrame({
        'open': prices * (1 + np.random.randn(len(dates)) * 0.01),
        'high': prices * (1 + abs(np.random.randn(len(dates))) * 0.02),
        'low': prices * (1 - abs(np.random.randn(len(dates))) * 0.02),
        'close': prices,
        'volume': np.random.randint(1000000, 10000000, len(dates))
    }, index=dates)
    
    # 执行联合回测
    result = run_joint_backtest(
        stock_code="000001",
        stock_name="平安银行",
        price_data=price_data,
        start_date="2024-01-01",
        end_date="2024-06-30",
        tech_weight=0.6,
        news_weight=0.4
    )
    
    print(f"\n回测结果:")
    print(f"  总收益率: {result.total_return:+.2f}%")
    print(f"  最大回撤: {result.max_drawdown:.2f}%")
    print(f"  交易次数: {len(result.trades)}")
