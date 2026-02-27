"""
AI情绪策略 V2 - 基于LLM的交易决策系统

核心特性:
1. 使用LLM分析市场技术形态和情绪
2. 多维度分析: 趋势、波动率、成交量、支撑阻力
3. 回退机制: LLM调用失败时自动切换到EMA策略
4. 可解释性: LLM提供交易决策理由

使用示例:
    >>> from strategies.ai_sentiment_v2 import AISentimentV2Strategy
    >>> 
    >>> # 使用默认配置
    >>> strategy = AISentimentV2Strategy()
    >>> 
    >>> # 执行回测
    >>> result = strategy.run_backtest(stock_data, market_data)
    >>> print(f"收益率: {result.total_return:.2f}%")
    >>> print(f"决策理由: {result.reasoning}")

作者: InvestMindPro Team
版本: 2.0.0
日期: 2026-02-28
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
import sys
from pathlib import Path

sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace/InvestMindPro')
from strategies.ema_v2 import EMAV2Strategy, BacktestResult


@dataclass
class AIAnalysisResult:
    """AI分析结果数据类"""
    decision: str  # 'buy', 'sell', 'hold'
    confidence: float  # 0-1
    reasoning: str  # 决策理由
    key_factors: List[str]  # 关键因素
    risk_level: str  # 'low', 'medium', 'high'


@dataclass
class AIBacktestResult(BacktestResult):
    """AI策略回测结果扩展"""
    ai_decisions: List[Dict] = field(default_factory=list)  # AI决策记录
    fallback_used: bool = False  # 是否使用了回退策略
    fallback_count: int = 0  # 回退次数


class LLMClient:
    """
    LLM客户端 - 模拟LLM调用
    
    注意: 在实际部署中，这里应该调用真实的LLM API
    为了回测的可重复性和性能，我们使用基于规则的模拟
    """
    
    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.call_count = 0
        self.error_count = 0
    
    def analyze_market(self, market_context: Dict) -> AIAnalysisResult:
        """
        分析市场数据并返回交易决策
        
        模拟LLM分析过程，基于技术指标做出决策
        """
        self.call_count += 1
        
        try:
            if self.use_mock:
                return self._mock_analyze(market_context)
            else:
                # 这里可以接入真实LLM API
                return self._mock_analyze(market_context)
        except Exception as e:
            self.error_count += 1
            raise Exception(f"LLM分析失败: {e}")
    
    def _mock_analyze(self, ctx: Dict) -> AIAnalysisResult:
        """
        模拟LLM分析
        
        基于多维度技术指标综合判断:
        1. 趋势方向 (EMA状态)
        2. 动量强度 (RSI)
        3. 波动率 (ATR)
        4. 成交量确认
        5. 市场环境
        """
        signals = []
        confidence = 0.5
        factors = []
        
        # 1. EMA趋势分析
        if ctx.get('ema_fast') > ctx.get('ema_slow'):
            signals.append(1)  # 上升趋势
            factors.append("EMA金叉状态，短期趋势向上")
            confidence += 0.15
        else:
            signals.append(-1)  # 下降趋势
            factors.append("EMA死叉状态，短期趋势向下")
            confidence -= 0.15
        
        # 2. RSI动量分析
        rsi = ctx.get('rsi', 50)
        if 40 <= rsi <= 60:
            signals.append(0)  # 中性
            factors.append(f"RSI({rsi:.1f})处于中性区域，无极端情绪")
        elif rsi > 60:
            signals.append(1)  # 偏强
            factors.append(f"RSI({rsi:.1f})显示一定强势，但需警惕超买")
            confidence += 0.1
        else:
            signals.append(-1)  # 偏弱
            factors.append(f"RSI({rsi:.1f})处于弱势区域，可能存在超卖")
            confidence -= 0.1
        
        # 3. 成交量分析
        vol_ratio = ctx.get('volume_ratio', 1.0)
        if vol_ratio > 1.5:
            if ctx.get('price_change', 0) > 0:
                signals.append(1)
                factors.append(f"成交量放大({vol_ratio:.1f}x)，上涨有资金配合")
                confidence += 0.1
            else:
                signals.append(-1)
                factors.append(f"放量下跌({vol_ratio:.1f}x)，资金出逃迹象")
                confidence -= 0.15
        elif vol_ratio < 0.7:
            factors.append(f"成交量萎缩({vol_ratio:.1f}x)，市场观望情绪浓")
        
        # 4. 市场环境
        if ctx.get('market_bull', True):
            signals.append(1)
            factors.append("大盘处于牛市环境，支持做多")
            confidence += 0.1
        else:
            signals.append(-1)
            factors.append("大盘处于熊市环境，需保持谨慎")
            confidence -= 0.1
        
        # 5. 波动率评估
        atr_pct = ctx.get('atr_pct', 2.0)
        if atr_pct > 4:
            factors.append(f"高波动环境(ATR:{atr_pct:.1f}%)，建议收紧止损")
        elif atr_pct < 1.5:
            factors.append(f"低波动环境(ATR:{atr_pct:.1f}%)，趋势可能持续")
        
        # 综合决策
        signal_sum = sum(signals)
        
        if signal_sum >= 2 and confidence > 0.6:
            decision = 'buy'
            confidence = min(confidence, 0.95)
            reasoning = f"多个技术指标共振看涨，建议买入。关键因子: {'; '.join(factors[:3])}"
            risk_level = 'medium' if atr_pct > 3 else 'low'
        elif signal_sum <= -2 or confidence < 0.4:
            decision = 'sell'
            confidence = min(1 - confidence, 0.95)
            reasoning = f"技术指标显示下跌风险，建议卖出。关键因子: {'; '.join(factors[:3])}"
            risk_level = 'medium'
        else:
            decision = 'hold'
            confidence = 0.5
            reasoning = f"信号混杂，建议观望。关键因子: {'; '.join(factors[:2])}"
            risk_level = 'low'
        
        return AIAnalysisResult(
            decision=decision,
            confidence=confidence,
            reasoning=reasoning,
            key_factors=factors,
            risk_level=risk_level
        )


class AISentimentV2Strategy:
    """
    AI情绪策略 V2 实现类
    
    策略逻辑:
    1. 使用LLM分析当前市场技术形态
    2. LLM基于多维度指标给出交易决策 (buy/sell/hold)
    3. 结合ATR动态止损
    4. LLM失败时自动回退到EMA V2.1策略
    
    与规则策略的区别:
    - 规则策略: 固定阈值触发 (如RSI<30买入)
    - AI策略: LLM综合判断，考虑多个因子的相互关系
    
    参数说明:
        confidence_threshold (float): AI置信度阈值 (默认0.6)
        use_fallback (bool): 是否启用EMA回退机制 (默认True)
        fallback_after_errors (int): 连续错误多少次后切换回退 (默认3)
    """
    
    def __init__(self, 
                 confidence_threshold: float = 0.6,
                 use_fallback: bool = True,
                 fallback_after_errors: int = 3,
                 ema_params: Optional[Dict] = None):
        """
        初始化AI情绪策略
        
        Args:
            confidence_threshold: AI决策置信度阈值
            use_fallback: 是否启用EMA回退机制
            fallback_after_errors: 连续错误多少次后切换回退
            ema_params: EMA回退策略参数
        """
        self.confidence_threshold = confidence_threshold
        self.use_fallback = use_fallback
        self.fallback_after_errors = fallback_after_errors
        
        # 初始化LLM客户端
        self.llm = LLMClient(use_mock=True)
        
        # 初始化EMA回退策略
        if ema_params is None:
            ema_params = {
                "fast_ema": 8,
                "slow_ema": 25,
                "atr_period": 14,
                "atr_multiplier": 2.0,
                "market_filter": True
            }
        self.fallback_strategy = EMAV2Strategy(ema_params)
        
        # 状态追踪
        self.consecutive_errors = 0
        self.in_fallback_mode = False
        
    def calculate_rsi(self, prices: pd.Series, period: int = 14) -> pd.Series:
        """计算RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    def calculate_atr(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """计算ATR"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=period).mean()
        return atr
    
    def prepare_market_context(self, df: pd.DataFrame, 
                               market_data: Optional[pd.DataFrame],
                               idx: int) -> Dict:
        """
        准备市场上下文数据供LLM分析
        """
        data = df.iloc[:idx+1]
        
        # 计算技术指标
        ema_fast = data['close'].ewm(span=8, adjust=False).mean().iloc[-1]
        ema_slow = data['close'].ewm(span=25, adjust=False).mean().iloc[-1]
        rsi = self.calculate_rsi(data['close']).iloc[-1]
        atr = self.calculate_atr(data).iloc[-1]
        
        # 成交量分析
        vol_current = data['volume'].iloc[-1]
        vol_ma20 = data['volume'].rolling(20).mean().iloc[-1]
        vol_ratio = vol_current / vol_ma20 if vol_ma20 > 0 else 1.0
        
        # 价格变化
        price_change = data['pct_change'].iloc[-1] if 'pct_change' in data.columns else 0
        
        # 市场环境
        market_bull = True
        if market_data is not None and len(market_data) > 200:
            market_ma50 = market_data['close'].rolling(50).mean().iloc[-1]
            market_ma200 = market_data['close'].rolling(200).mean().iloc[-1]
            market_bull = market_ma50 > market_ma200
        
        # 近期波动率
        atr_pct = (atr / data['close'].iloc[-1]) * 100 if data['close'].iloc[-1] > 0 else 0
        
        # 近期价格走势
        recent_returns = data['close'].pct_change(5).iloc[-1] * 100 if len(data) > 5 else 0
        
        return {
            'date': str(data.index[-1]),
            'price': float(data['close'].iloc[-1]),
            'ema_fast': float(ema_fast),
            'ema_slow': float(ema_slow),
            'rsi': float(rsi) if not pd.isna(rsi) else 50,
            'atr': float(atr) if not pd.isna(atr) else 0,
            'atr_pct': float(atr_pct),
            'volume_ratio': float(vol_ratio),
            'price_change': float(price_change),
            'recent_5d_return': float(recent_returns),
            'market_bull': market_bull,
            'high_20d': float(data['high'].rolling(20).max().iloc[-1]),
            'low_20d': float(data['low'].rolling(20).min().iloc[-1]),
        }
    
    def generate_signals(self, df: pd.DataFrame, 
                        market_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        生成交易信号 (AI决策)
        """
        data = df.copy()
        data['ai_buy_signal'] = False
        data['ai_sell_signal'] = False
        data['ai_confidence'] = 0.0
        data['ai_reasoning'] = ''
        data['ai_fallback'] = False
        
        # 预计算ATR止损
        data['atr'] = self.calculate_atr(data)
        data['stop_loss'] = data['close'] - 2.0 * data['atr']
        
        # 从第50天开始分析 (确保有足够的历史数据)
        for i in range(50, len(data)):
            try:
                if self.in_fallback_mode:
                    # 使用EMA回退策略
                    ema_signals = self.fallback_strategy.generate_signals(
                        data.iloc[:i+1], market_data
                    )
                    data.loc[data.index[i], 'ai_buy_signal'] = ema_signals['buy_signal'].iloc[-1]
                    data.loc[data.index[i], 'ai_sell_signal'] = ema_signals['sell_signal'].iloc[-1]
                    data.loc[data.index[i], 'ai_fallback'] = True
                    continue
                
                # 准备市场上下文
                ctx = self.prepare_market_context(data, market_data, i)
                
                # 调用LLM分析
                ai_result = self.llm.analyze_market(ctx)
                
                # 重置错误计数
                self.consecutive_errors = 0
                
                # 应用AI决策 (需要满足置信度阈值)
                if ai_result.decision == 'buy' and ai_result.confidence >= self.confidence_threshold:
                    data.loc[data.index[i], 'ai_buy_signal'] = True
                elif ai_result.decision == 'sell':
                    data.loc[data.index[i], 'ai_sell_signal'] = True
                
                data.loc[data.index[i], 'ai_confidence'] = ai_result.confidence
                data.loc[data.index[i], 'ai_reasoning'] = ai_result.reasoning[:100]  # 截短存储
                
            except Exception as e:
                self.consecutive_errors += 1
                
                # 检查是否需要切换回退模式
                if self.consecutive_errors >= self.fallback_after_errors and self.use_fallback:
                    self.in_fallback_mode = True
                    print(f"  LLM连续{self.consecutive_errors}次错误，切换到EMA回退模式")
                
                # 继续使用EMA信号
                ema_signals = self.fallback_strategy.generate_signals(
                    data.iloc[:i+1], market_data
                )
                data.loc[data.index[i], 'ai_buy_signal'] = ema_signals['buy_signal'].iloc[-1]
                data.loc[data.index[i], 'ai_sell_signal'] = ema_signals['sell_signal'].iloc[-1]
                data.loc[data.index[i], 'ai_fallback'] = True
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, 
                     market_data: Optional[pd.DataFrame] = None,
                     initial_capital: float = 100000.0) -> AIBacktestResult:
        """
        执行AI策略回测
        """
        symbol = df.attrs.get('symbol', 'Unknown')
        
        print(f"  AI策略分析 {symbol}...")
        data = self.generate_signals(df, market_data)
        
        position = 0
        entry_price = 0.0
        entry_date = None
        trades = []
        ai_decisions = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        fallback_count = 0
        
        for i in range(50, len(data)):  # 从第50天开始
            date = data.index[i]
            price = data['close'].iloc[i]
            
            # 记录AI决策
            if data['ai_buy_signal'].iloc[i] or data['ai_sell_signal'].iloc[i] or data['ai_confidence'].iloc[i] > 0:
                ai_decisions.append({
                    'date': str(date),
                    'buy': bool(data['ai_buy_signal'].iloc[i]),
                    'sell': bool(data['ai_sell_signal'].iloc[i]),
                    'confidence': float(data['ai_confidence'].iloc[i]),
                    'fallback': bool(data['ai_fallback'].iloc[i]),
                    'reasoning': str(data['ai_reasoning'].iloc[i])[:50]
                })
                
                if data['ai_fallback'].iloc[i]:
                    fallback_count += 1
            
            if position == 0:  # 空仓
                if data['ai_buy_signal'].iloc[i]:
                    position = 1
                    entry_price = price
                    entry_date = date
                    shares = current_capital / price
                    
            elif position == 1:  # 持仓
                exit_reason = None
                exit_price = price
                
                if data['ai_sell_signal'].iloc[i]:
                    exit_reason = "ai_signal"
                
                # ATR止损
                stop_price = data['stop_loss'].iloc[i]
                if price < stop_price:
                    exit_reason = "stop_loss"
                    exit_price = stop_price
                
                if exit_reason:
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    
                    trades.append({
                        'entry_date': entry_date,
                        'entry_price': entry_price,
                        'exit_date': date,
                        'exit_price': exit_price,
                        'pnl': pnl,
                        'pnl_pct': pnl_pct,
                        'exit_reason': exit_reason
                    })
                    
                    current_capital += pnl
                    position = 0
                    entry_price = 0.0
                    entry_date = None
            
            equity_curve.append(current_capital)
        
        # 计算绩效指标
        total_return = (current_capital - initial_capital) / initial_capital * 100
        
        if len(trades) > 0:
            winning_trades = [t for t in trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(trades) * 100
            
            equity_series = pd.Series(equity_curve)
            rolling_max = equity_series.expanding().max()
            drawdown = (equity_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdown.min()
            
            returns = pd.Series(equity_curve).pct_change().dropna()
            if returns.std() != 0:
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            win_rate = 0
            max_drawdown = 0
            sharpe_ratio = 0
        
        return AIBacktestResult(
            symbol=symbol,
            total_return=total_return,
            win_rate=win_rate,
            total_trades=len(trades),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=trades,
            params={
                'confidence_threshold': self.confidence_threshold,
                'use_fallback': self.use_fallback,
                'ema_params': self.fallback_strategy.params
            },
            ai_decisions=ai_decisions,
            fallback_used=self.in_fallback_mode or fallback_count > 0,
            fallback_count=fallback_count
        )


if __name__ == '__main__':
    print("AI情绪策略 V2 已加载")
    print("策略特点:")
    print("- 使用LLM模拟分析市场技术形态")
    print("- 多维度决策: 趋势+动量+成交量+市场环境")
    print("- 失败时自动回退到EMA V2.1策略")
    print("- 提供可解释的交易决策理由")
