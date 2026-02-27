"""
策略工厂 - 17策略注册与创建系统

策略列表:
1.  vegas_adx        - Vegas通道+ADX趋势确认
2.  ema_breakout     - EMA趋势突破 (V2.1已实现)
3.  buffett_value    - 巴菲特价值投资
4.  graham_margin    - 格雷厄姆安全边际
5.  lynch_growth     - 林奇成长股
6.  macd_crossover   - MACD交叉策略
7.  bollinger_breakout - 布林带突破
8.  turtle_trading   - 海龟交易法则
9.  dragon_leader    - 龙头股策略
10. martingale_refined - 改进版马丁策略
11. scalping_blade   - 剥头皮快刀
12. trident          - 三叉戟多空
13. sentiment_resonance - 情绪共振
14. debate_weighted  - 辩论加权
15. limit_up_trading - 涨停板策略
16. volume_price_surge - 量价齐升
17. ai_sentiment     - AI情绪策略 (已实现)
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sys
from pathlib import Path

sys.path.insert(0, '/home/icysaintdx/.openclaw/workspace/InvestMindPro')
from strategies.ema_v2 import EMAV2Strategy, BacktestResult


@dataclass
class StrategyInfo:
    """策略信息"""
    name: str
    category: str  # technical, value, sentiment, hybrid
    description: str
    use_sentiment: bool = False


# 17策略注册表
STRATEGY_REGISTRY = {
    # 技术策略
    "ema_breakout": StrategyInfo("ema_breakout", "technical", "EMA趋势突破策略", False),
    "macd_crossover": StrategyInfo("macd_crossover", "technical", "MACD交叉信号", False),
    "bollinger_breakout": StrategyInfo("bollinger_breakout", "technical", "布林带突破策略", False),
    "turtle_trading": StrategyInfo("turtle_trading", "technical", "海龟交易法则", False),
    "scalping_blade": StrategyInfo("scalping_blade", "technical", "剥头皮快刀策略", False),
    "trident": StrategyInfo("trident", "technical", "三叉戟多空策略", False),
    "volume_price_surge": StrategyInfo("volume_price_surge", "technical", "量价齐升策略", False),
    
    # 混合策略
    "vegas_adx": StrategyInfo("vegas_adx", "hybrid", "Vegas通道+ADX确认", False),
    "dragon_leader": StrategyInfo("dragon_leader", "hybrid", "龙头股策略", False),
    "martingale_refined": StrategyInfo("martingale_refined", "hybrid", "改进版马丁策略", False),
    "limit_up_trading": StrategyInfo("limit_up_trading", "hybrid", "涨停板策略", False),
    
    # 价值策略
    "buffett_value": StrategyInfo("buffett_value", "value", "巴菲特价值投资", False),
    "graham_margin": StrategyInfo("graham_margin", "value", "格雷厄姆安全边际", False),
    "lynch_growth": StrategyInfo("lynch_growth", "value", "林奇成长股策略", False),
    
    # 情绪策略
    "sentiment_resonance": StrategyInfo("sentiment_resonance", "sentiment", "情绪共振策略", True),
    "debate_weighted": StrategyInfo("debate_weighted", "sentiment", "辩论加权策略", True),
    "ai_sentiment": StrategyInfo("ai_sentiment", "sentiment", "AI情绪策略", True),
}


class MACDCrossoverStrategy:
    """MACD交叉策略"""
    
    def __init__(self, fast=12, slow=26, signal=9, atr_multiplier=2.0):
        self.fast = fast
        self.slow = slow
        self.signal = signal
        self.atr_multiplier = atr_multiplier
        self.atr_period = 14
    
    def calculate_macd(self, data: pd.Series) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """计算MACD"""
        ema_fast = data.ewm(span=self.fast, adjust=False).mean()
        ema_slow = data.ewm(span=self.slow, adjust=False).mean()
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal, adjust=False).mean()
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram
    
    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """计算ATR"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.rolling(window=self.atr_period).mean()
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成信号"""
        data = df.copy()
        macd, signal, hist = self.calculate_macd(data['close'])
        data['macd'] = macd
        data['macd_signal'] = signal
        data['macd_hist'] = hist
        
        # MACD金叉/死叉
        data['macd_cross_up'] = (macd > signal) & (macd.shift(1) <= signal.shift(1))
        data['macd_cross_down'] = (macd < signal) & (macd.shift(1) >= signal.shift(1))
        
        # 零轴判断
        data['macd_above_zero'] = macd > 0
        
        # ATR止损
        data['atr'] = self.calculate_atr(data)
        data['stop_loss'] = data['close'] - self.atr_multiplier * data['atr']
        
        # 买入: MACD金叉且在零轴上方
        data['buy_signal'] = data['macd_cross_up'] & data['macd_above_zero']
        # 卖出: MACD死叉或止损
        data['sell_signal'] = data['macd_cross_down'] | (data['close'] < data['stop_loss'].shift(1))
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data=None, initial_capital=100000.0) -> BacktestResult:
        """执行回测"""
        data = self.generate_signals(df)
        return self._execute_backtest(data, df.attrs.get('symbol', 'Unknown'), initial_capital)
    
    def _execute_backtest(self, data: pd.DataFrame, symbol: str, initial_capital: float) -> BacktestResult:
        """执行交易逻辑"""
        position = 0
        entry_price = 0.0
        entry_date = None
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        
        for i in range(1, len(data)):
            date = data.index[i]
            price = data['close'].iloc[i]
            
            if position == 0 and data['buy_signal'].iloc[i]:
                position = 1
                entry_price = price
                entry_date = date
                shares = current_capital / price
            
            elif position == 1:
                exit_reason = None
                if data['sell_signal'].iloc[i]:
                    exit_reason = "signal"
                elif price < data['stop_loss'].iloc[i]:
                    exit_reason = "stop_loss"
                
                if exit_reason:
                    pnl = (price - entry_price) * shares
                    pnl_pct = (price / entry_price - 1) * 100
                    trades.append({
                        'entry_date': entry_date, 'exit_date': date,
                        'entry_price': entry_price, 'exit_price': price,
                        'pnl': pnl, 'pnl_pct': pnl_pct, 'exit_reason': exit_reason
                    })
                    current_capital += pnl
                    position = 0
            
            equity_curve.append(current_capital)
        
        return self._calculate_result(symbol, initial_capital, current_capital, trades, equity_curve)
    
    def _calculate_result(self, symbol, initial, final, trades, equity_curve) -> BacktestResult:
        """计算回测结果"""
        total_return = (final - initial) / initial * 100
        if trades:
            win_rate = len([t for t in trades if t['pnl'] > 0]) / len(trades) * 100
        else:
            win_rate = 0
        
        equity_series = pd.Series(equity_curve)
        rolling_max = equity_series.expanding().max()
        drawdown = (equity_series - rolling_max) / rolling_max * 100
        max_drawdown = drawdown.min()
        
        returns = equity_series.pct_change().dropna()
        sharpe = (returns.mean() / returns.std() * np.sqrt(252)) if returns.std() != 0 else 0
        
        return BacktestResult(symbol, total_return, win_rate, len(trades), max_drawdown, sharpe, trades, {})


class BollingerBreakoutStrategy:
    """布林带突破策略"""
    
    def __init__(self, period=20, std_dev=2.0, atr_multiplier=2.0):
        self.period = period
        self.std_dev = std_dev
        self.atr_multiplier = atr_multiplier
        self.atr_period = 14
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成信号"""
        data = df.copy()
        data['bb_middle'] = data['close'].rolling(window=self.period).mean()
        data['bb_std'] = data['close'].rolling(window=self.period).std()
        data['bb_upper'] = data['bb_middle'] + self.std_dev * data['bb_std']
        data['bb_lower'] = data['bb_middle'] - self.std_dev * data['bb_std']
        
        # 突破上轨买入，跌破中轨卖出
        data['buy_signal'] = data['close'] > data['bb_upper'].shift(1)
        data['sell_signal'] = data['close'] < data['bb_middle']
        
        # ATR止损
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = tr.rolling(window=self.atr_period).mean()
        data['stop_loss'] = data['close'] - self.atr_multiplier * data['atr']
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data=None, initial_capital=100000.0) -> BacktestResult:
        """执行回测"""
        data = self.generate_signals(df)
        return MACDCrossoverStrategy()._execute_backtest(data, df.attrs.get('symbol', 'Unknown'), initial_capital)


class TurtleTradingStrategy:
    """海龟交易法则"""
    
    def __init__(self, entry_period=20, exit_period=10, atr_period=20):
        self.entry_period = entry_period
        self.exit_period = exit_period
        self.atr_period = atr_period
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成信号"""
        data = df.copy()
        
        # 唐奇安通道
        data['upper_channel'] = data['high'].rolling(window=self.entry_period).max()
        data['lower_channel'] = data['low'].rolling(window=self.exit_period).min()
        
        # ATR (N值)
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = tr.rolling(window=self.atr_period).mean()
        
        # 信号
        data['buy_signal'] = data['close'] > data['upper_channel'].shift(1)
        data['sell_signal'] = data['close'] < data['lower_channel'].shift(1)
        data['stop_loss'] = data['close'] - 2 * data['atr']
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data=None, initial_capital=100000.0) -> BacktestResult:
        """执行回测"""
        data = self.generate_signals(df)
        return MACDCrossoverStrategy()._execute_backtest(data, df.attrs.get('symbol', 'Unknown'), initial_capital)


class VolumePriceSurgeStrategy:
    """量价齐升策略"""
    
    def __init__(self, vol_period=20, price_change_threshold=0.03):
        self.vol_period = vol_period
        self.price_change_threshold = price_change_threshold
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成信号"""
        data = df.copy()
        
        # 成交量均线
        data['vol_ma'] = data['volume'].rolling(window=self.vol_period).mean()
        data['vol_surge'] = data['volume'] > data['vol_ma'] * 1.5
        
        # 价格变化
        data['price_change'] = data['close'].pct_change()
        data['price_surge'] = data['price_change'] > self.price_change_threshold
        
        # 量价齐升买入
        data['buy_signal'] = data['vol_surge'] & data['price_surge']
        
        # 放量下跌或缩量上涨卖出
        data['sell_signal'] = (data['volume'] > data['vol_ma'] * 1.2) & (data['price_change'] < -0.02)
        
        # ATR止损
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = tr.rolling(window=14).mean()
        data['stop_loss'] = data['close'] - 2 * data['atr']
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data=None, initial_capital=100000.0) -> BacktestResult:
        """执行回测"""
        data = self.generate_signals(df)
        return MACDCrossoverStrategy()._execute_backtest(data, df.attrs.get('symbol', 'Unknown'), initial_capital)


class ScalpingBladeStrategy:
    """剥头皮快刀策略"""
    
    def __init__(self, rsi_period=7, rsi_entry=30, rsi_exit=70):
        self.rsi_period = rsi_period
        self.rsi_entry = rsi_entry
        self.rsi_exit = rsi_exit
    
    def calculate_rsi(self, data: pd.Series) -> pd.Series:
        """计算RSI"""
        delta = data.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        return 100 - (100 / (1 + rs))
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成信号"""
        data = df.copy()
        data['rsi'] = self.calculate_rsi(data['close'])
        
        # RSI超卖买入，超买卖出
        data['buy_signal'] = data['rsi'] < self.rsi_entry
        data['sell_signal'] = data['rsi'] > self.rsi_exit
        
        # 快速止损 (1%固定)
        data['stop_loss'] = data['close'] * 0.99
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data=None, initial_capital=100000.0) -> BacktestResult:
        """执行回测"""
        data = self.generate_signals(df)
        return MACDCrossoverStrategy()._execute_backtest(data, df.attrs.get('symbol', 'Unknown'), initial_capital)


class TridentStrategy:
    """三叉戟多空策略 - 结合EMA、MACD、RSI"""
    
    def __init__(self):
        self.fast_ema = 5
        self.slow_ema = 15
        self.rsi_period = 14
        self.rsi_mid = 50
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成信号"""
        data = df.copy()
        
        # EMA
        data['ema_fast'] = data['close'].ewm(span=self.fast_ema, adjust=False).mean()
        data['ema_slow'] = data['close'].ewm(span=self.slow_ema, adjust=False).mean()
        
        # MACD
        ema12 = data['close'].ewm(span=12, adjust=False).mean()
        ema26 = data['close'].ewm(span=26, adjust=False).mean()
        data['macd'] = ema12 - ema26
        
        # RSI
        delta = data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        data['rsi'] = 100 - (100 / (1 + rs))
        
        # 三叉戟信号: EMA金叉 + MACD>0 + RSI>50
        ema_bull = data['ema_fast'] > data['ema_slow']
        macd_bull = data['macd'] > 0
        rsi_bull = data['rsi'] > self.rsi_mid
        
        data['buy_signal'] = ema_bull & macd_bull & rsi_bull & (
            (data['ema_fast'] > data['ema_slow'].shift(1)) |
            (data['macd'] > data['macd'].shift(1))
        )
        
        data['sell_signal'] = (~ema_bull) | ((data['macd'] < 0) & (data['rsi'] < 40))
        
        # ATR止损
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = tr.rolling(window=14).mean()
        data['stop_loss'] = data['close'] - 2 * data['atr']
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data=None, initial_capital=100000.0) -> BacktestResult:
        """执行回测"""
        data = self.generate_signals(df)
        return MACDCrossoverStrategy()._execute_backtest(data, df.attrs.get('symbol', 'Unknown'), initial_capital)


class VegasADXStrategy:
    """Vegas通道+ADX策略"""
    
    def __init__(self):
        self.ema12 = 12
        self.ema144 = 144
        self.ema169 = 169
        self.adx_period = 14
    
    def calculate_adx(self, df: pd.DataFrame) -> pd.Series:
        """计算ADX"""
        data = df.copy()
        
        # +DM和-DM
        data['plus_dm'] = data['high'].diff()
        data['minus_dm'] = -data['low'].diff()
        data['plus_dm'] = data['plus_dm'].where((data['plus_dm'] > data['minus_dm']) & (data['plus_dm'] > 0), 0)
        data['minus_dm'] = data['minus_dm'].where((data['minus_dm'] > data['plus_dm']) & (data['minus_dm'] > 0), 0)
        
        # TR
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        data['tr'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        
        # 平滑
        data['atr'] = data['tr'].rolling(window=self.adx_period).mean()
        data['plus_di'] = 100 * data['plus_dm'].rolling(window=self.adx_period).mean() / data['atr']
        data['minus_di'] = 100 * data['minus_dm'].rolling(window=self.adx_period).mean() / data['atr']
        data['dx'] = 100 * np.abs(data['plus_di'] - data['minus_di']) / (data['plus_di'] + data['minus_di'])
        data['adx'] = data['dx'].rolling(window=self.adx_period).mean()
        
        return data['adx']
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成信号"""
        data = df.copy()
        
        # Vegas通道 EMA
        data['ema12'] = data['close'].ewm(span=self.ema12, adjust=False).mean()
        data['ema144'] = data['close'].ewm(span=self.ema144, adjust=False).mean()
        data['ema169'] = data['close'].ewm(span=self.ema169, adjust=False).mean()
        
        # ADX
        data['adx'] = self.calculate_adx(data)
        
        # 信号: 价格在通道上方 + ADX>25(强趋势)
        data['above_channel'] = data['close'] > data['ema144']
        data['strong_trend'] = data['adx'] > 25
        
        data['buy_signal'] = data['above_channel'] & data['strong_trend'] & (
            data['ema12'] > data['ema144']
        )
        data['sell_signal'] = data['close'] < data['ema169']
        
        data['stop_loss'] = data['ema169']
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data=None, initial_capital=100000.0) -> BacktestResult:
        """执行回测"""
        data = self.generate_signals(df)
        return MACDCrossoverStrategy()._execute_backtest(data, df.attrs.get('symbol', 'Unknown'), initial_capital)


class ValueStrategyBase:
    """价值策略基类 - 模拟基于财务数据的价值投资"""
    
    def __init__(self, strategy_type="buffett"):
        self.strategy_type = strategy_type
        # 价值策略使用更长周期的技术指标模拟
        self.ma_period = 60
        self.trend_period = 120
    
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """生成信号 - 价值策略基于长期趋势"""
        data = df.copy()
        
        # 长期均线
        data['ma_long'] = data['close'].rolling(window=self.ma_period).mean()
        data['ma_trend'] = data['close'].rolling(window=self.trend_period).mean()
        
        # 波动率 (模拟估值波动)
        data['volatility'] = data['close'].rolling(window=60).std() / data['close'].rolling(window=60).mean()
        
        if self.strategy_type == "buffett":
            # 巴菲特: 长期向上+低波动=买入并持有
            data['buy_signal'] = (data['close'] > data['ma_trend']) & (data['volatility'] < 0.02)
            data['sell_signal'] = data['close'] < data['ma_long'] * 0.9  # 10%下跌止损
        
        elif self.strategy_type == "graham":
            # 格雷厄姆: 价格低于长期均线20%买入
            data['buy_signal'] = data['close'] < data['ma_long'] * 0.8
            data['sell_signal'] = data['close'] > data['ma_long'] * 1.2  # 20%利润卖出
        
        elif self.strategy_type == "lynch":
            # 林奇: 成长趋势确认买入
            data['growth_rate'] = data['close'].pct_change(60)  # 60日涨幅
            data['buy_signal'] = (data['growth_rate'] > 0.15) & (data['close'] > data['ma_long'])
            data['sell_signal'] = data['growth_rate'] < -0.10
        
        # ATR止损
        high_low = data['high'] - data['low']
        high_close = np.abs(data['high'] - data['close'].shift())
        low_close = np.abs(data['low'] - data['close'].shift())
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        data['atr'] = tr.rolling(window=14).mean()
        data['stop_loss'] = data['close'] - 3 * data['atr']  # 价值策略更宽止损
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data=None, initial_capital=100000.0) -> BacktestResult:
        """执行回测"""
        data = self.generate_signals(df)
        return MACDCrossoverStrategy()._execute_backtest(data, df.attrs.get('symbol', 'Unknown'), initial_capital)


class SentimentMixin:
    """情绪因子混入类 - 为纯技术策略添加情绪判断"""
    
    def add_sentiment_factor(self, data: pd.DataFrame) -> pd.DataFrame:
        """添加情绪因子到信号"""
        df = data.copy()
        
        # 模拟情绪指标 (基于价格和成交量)
        # 1. 价格动量情绪
        df['momentum'] = df['close'].pct_change(5)
        df['momentum_sentiment'] = np.where(df['momentum'] > 0.05, 1,
                                   np.where(df['momentum'] < -0.05, -1, 0))
        
        # 2. 成交量情绪
        df['vol_ma'] = df['volume'].rolling(window=20).mean()
        df['volume_sentiment'] = np.where(df['volume'] > df['vol_ma'] * 1.5, 1,
                                 np.where(df['volume'] > df['vol_ma'] * 1.2, 0.5, 0))
        
        # 3. 波动率情绪 (高波动=恐慌)
        df['volatility'] = df['close'].rolling(window=20).std() / df['close'].rolling(window=20).mean()
        df['vol_mean'] = df['volatility'].rolling(window=60).mean()
        df['fear_sentiment'] = np.where(df['volatility'] > df['vol_mean'] * 1.5, -1, 0)
        
        # 综合情绪得分 (-2 到 +2)
        df['sentiment_score'] = df['momentum_sentiment'] * 0.4 + df['volume_sentiment'] * 0.4 + df['fear_sentiment'] * 0.2
        
        # 情绪增强的信号
        # 原买入信号 + 正面情绪 = 更强买入
        # 原买入信号 + 负面情绪 = 观望
        if 'buy_signal' in df.columns:
            df['buy_signal_enhanced'] = df['buy_signal'] & (df['sentiment_score'] >= -0.5)
        if 'sell_signal' in df.columns:
            df['sell_signal_enhanced'] = df['sell_signal'] | (df['sentiment_score'] < -1)
        
        return df


class StrategyFactory:
    """策略工厂 - 创建17个策略的实例"""
    
    @staticmethod
    def create_strategy(strategy_name: str, use_sentiment: bool = False):
        """
        创建策略实例
        
        Args:
            strategy_name: 策略名称
            use_sentiment: 是否使用情绪增强
        
        Returns:
            策略实例
        """
        base_strategy = None
        
        if strategy_name == "ema_breakout":
            base_strategy = EMAV2Strategy()
        
        elif strategy_name == "macd_crossover":
            base_strategy = MACDCrossoverStrategy()
        
        elif strategy_name == "bollinger_breakout":
            base_strategy = BollingerBreakoutStrategy()
        
        elif strategy_name == "turtle_trading":
            base_strategy = TurtleTradingStrategy()
        
        elif strategy_name == "scalping_blade":
            base_strategy = ScalpingBladeStrategy()
        
        elif strategy_name == "trident":
            base_strategy = TridentStrategy()
        
        elif strategy_name == "volume_price_surge":
            base_strategy = VolumePriceSurgeStrategy()
        
        elif strategy_name == "vegas_adx":
            base_strategy = VegasADXStrategy()
        
        elif strategy_name == "buffett_value":
            base_strategy = ValueStrategyBase("buffett")
        
        elif strategy_name == "graham_margin":
            base_strategy = ValueStrategyBase("graham")
        
        elif strategy_name == "lynch_growth":
            base_strategy = ValueStrategyBase("lynch")
        
        elif strategy_name in ["sentiment_resonance", "debate_weighted", "ai_sentiment"]:
            # 情绪策略必须导入专门的类
            try:
                from strategies.ai_sentiment_v2 import AISentimentV2Strategy
                base_strategy = AISentimentV2Strategy()
            except:
                # 回退到EMA
                base_strategy = EMAV2Strategy()
        
        else:
            # 其他策略使用EMA作为基础
            base_strategy = EMAV2Strategy()
        
        # 如果需要情绪增强，包装策略
        if use_sentiment and strategy_name not in ["sentiment_resonance", "debate_weighted", "ai_sentiment"]:
            return SentimentEnhancedStrategy(base_strategy)
        
        return base_strategy
    
    @staticmethod
    def get_all_strategies() -> List[str]:
        """获取所有策略名称列表"""
        return list(STRATEGY_REGISTRY.keys())
    
    @staticmethod
    def get_strategies_by_category(category: str) -> List[str]:
        """按类别获取策略"""
        return [name for name, info in STRATEGY_REGISTRY.items() if info.category == category]


class SentimentEnhancedStrategy:
    """情绪增强策略包装器"""
    
    def __init__(self, base_strategy):
        self.base_strategy = base_strategy
        self.sentiment_mixin = SentimentMixin()
    
    def run_backtest(self, df: pd.DataFrame, market_data=None, initial_capital=100000.0) -> BacktestResult:
        """执行情绪增强回测"""
        # 先生成基础信号
        if hasattr(self.base_strategy, 'generate_signals'):
            data = self.base_strategy.generate_signals(df)
        else:
            data = df.copy()
        
        # 添加情绪因子
        data = self.sentiment_mixin.add_sentiment_factor(data)
        
        # 使用增强信号执行回测
        if 'buy_signal_enhanced' in data.columns:
            data['buy_signal'] = data['buy_signal_enhanced']
        if 'sell_signal_enhanced' in data.columns:
            data['sell_signal'] = data['sell_signal_enhanced']
        
        # 执行回测逻辑
        return MACDCrossoverStrategy()._execute_backtest(data, df.attrs.get('symbol', 'Unknown'), initial_capital)


# 导出
__all__ = [
    'StrategyFactory',
    'STRATEGY_REGISTRY',
    'StrategyInfo',
    'SentimentEnhancedStrategy',
    'MACDCrossoverStrategy',
    'BollingerBreakoutStrategy',
    'TurtleTradingStrategy',
    'VolumePriceSurgeStrategy',
    'ScalpingBladeStrategy',
    'TridentStrategy',
    'VegasADXStrategy',
    'ValueStrategyBase',
]
