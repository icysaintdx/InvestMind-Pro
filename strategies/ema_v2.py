"""
EMA V2.1 趋势跟踪策略 - 核心模块

核心特性:
1. 双EMA交叉信号 (快EMA上穿慢EMA买入，下穿卖出)
2. 动态ATR止损 (根据股票波动率调整止损位置)
3. 大盘趋势过滤 (使用沪深300判断市场环境，避免逆势交易)
4. 按波动率分类参数优化 (高/中/低波动率股票采用不同参数)

使用示例:
    >>> from strategies.ema_v2 import EMAV2Strategy
    >>> 
    >>> # 使用默认参数
    >>> strategy = EMAV2Strategy(volatility_type="high_volatility")
    >>> 
    >>> # 使用自定义参数
    >>> params = {"fast_ema": 10, "slow_ema": 30, "atr_multiplier": 2.5}
    >>> strategy = EMAV2Strategy(params=params)
    >>> 
    >>> # 执行回测
    >>> result = strategy.run_backtest(stock_data, market_data)
    >>> print(f"收益率: {result.total_return:.2f}%")

作者: InvestMindPro Team
版本: 2.1.0
日期: 2026-02-27
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum


class MarketRegime(Enum):
    """
    市场环境分类枚举
    
    基于沪深300指数的50日/200日均线判断:
    - BULL: 50日均线 > 200日均线 (牛市，允许交易)
    - BEAR: 50日均线 < 200日均线 (熊市，暂停交易)
    - OSCILLATION: 均线缠绕 (震荡市，谨慎交易)
    """
    BULL = "bull"      # 牛市
    BEAR = "bear"      # 熊市
    OSCILLATION = "oscillation"  # 震荡


@dataclass
class BacktestResult:
    """
    回测结果数据类
    
    Attributes:
        symbol: 股票代码
        total_return: 总收益率 (%)
        win_rate: 胜率 (%)
        total_trades: 总交易次数
        max_drawdown: 最大回撤 (%)
        sharpe_ratio: 夏普比率
        trades: 交易记录列表
        params: 使用的参数配置
    """
    symbol: str
    total_return: float
    win_rate: float
    total_trades: int
    max_drawdown: float
    sharpe_ratio: float
    trades: List[Dict]
    params: Dict


class EMAV2Strategy:
    """
    EMA V2.1 策略实现类
    
    策略逻辑:
    1. 买入信号: 快EMA上穿慢EMA (金叉) + 市场环境允许
    2. 卖出信号: 快EMA下穿慢EMA (死叉) 或 价格跌破ATR止损线
    3. 止损机制: 动态ATR止损，根据股票波动率自动调整
    4. 大盘过滤: 熊市环境下暂停新开仓
    
    参数说明:
        fast_ema (int): 快EMA周期，范围3-15
        slow_ema (int): 慢EMA周期，范围15-50
        atr_period (int): ATR计算周期，默认14
        atr_multiplier (float): ATR倍数(止损用)，范围1.0-3.0
        market_filter (bool): 是否启用大盘过滤
    
    示例:
        >>> strategy = EMAV2Strategy(volatility_type="medium_volatility")
        >>> result = strategy.run_backtest(df, market_df)
        >>> print(f"收益: {result.total_return:.2f}%")
    """
    
    # 按波动率分类的默认参数
    DEFAULT_PARAMS = {
        "high_volatility": {    # 高波动股票 (如新能源、科技)
            "fast_ema": 10,
            "slow_ema": 30,
            "atr_period": 14,
            "atr_multiplier": 3.0,
            "market_filter": True
        },
        "medium_volatility": {  # 中波动股票 (如消费、医药)
            "fast_ema": 8,
            "slow_ema": 25,
            "atr_period": 14,
            "atr_multiplier": 2.0,
            "market_filter": True
        },
        "low_volatility": {     # 低波动股票 (如银行、白酒)
            "fast_ema": 5,
            "slow_ema": 20,
            "atr_period": 14,
            "atr_multiplier": 1.5,
            "market_filter": True
        }
    }
    
    def __init__(self, params: Optional[Dict] = None, volatility_type: str = "medium_volatility"):
        """
        初始化策略
        
        Args:
            params: 自定义参数，为None时使用默认参数
            volatility_type: 波动率类型 (high_volatility/medium_volatility/low_volatility)
        """
        if params is None:
            self.params = self.DEFAULT_PARAMS.get(volatility_type, self.DEFAULT_PARAMS["medium_volatility"])
        else:
            self.params = params
            
        self.fast_ema = self.params["fast_ema"]
        self.slow_ema = self.params["slow_ema"]
        self.atr_period = self.params["atr_period"]
        self.atr_multiplier = self.params["atr_multiplier"]
        self.market_filter = self.params.get("market_filter", True)
        
    def calculate_ema(self, data: pd.Series, period: int) -> pd.Series:
        """计算EMA"""
        return data.ewm(span=period, adjust=False).mean()
    
    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """计算ATR (Average True Range)"""
        high_low = df['high'] - df['low']
        high_close = np.abs(df['high'] - df['close'].shift())
        low_close = np.abs(df['low'] - df['close'].shift())
        
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        atr = tr.rolling(window=self.atr_period).mean()
        return atr
    
    def calculate_market_regime(self, market_data: pd.DataFrame) -> pd.Series:
        """
        计算市场环境 (基于沪深300指数)
        使用50/200日均线判断牛熊
        """
        if market_data is None or not self.market_filter:
            return pd.Series([MarketRegime.BULL] * len(market_data), index=market_data.index)
        
        ma50 = market_data['close'].rolling(window=50).mean()
        ma200 = market_data['close'].rolling(window=200).mean()
        
        regime = pd.Series(index=market_data.index, dtype=object)
        
        # 牛市: 50日均线 > 200日均线
        # 熊市: 50日均线 < 200日均线
        for i in range(len(market_data)):
            if pd.isna(ma50.iloc[i]) or pd.isna(ma200.iloc[i]):
                regime.iloc[i] = MarketRegime.OSCILLATION
            elif ma50.iloc[i] > ma200.iloc[i]:
                regime.iloc[i] = MarketRegime.BULL
            else:
                regime.iloc[i] = MarketRegime.BEAR
                
        return regime
    
    def generate_signals(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        生成交易信号
        
        Args:
            df: 股票数据 (需包含 open, high, low, close, volume 列)
            market_data: 大盘数据 (沪深300)，用于市场过滤
            
        Returns:
            DataFrame 包含信号列
        """
        data = df.copy()
        
        # 计算EMA
        data['ema_fast'] = self.calculate_ema(data['close'], self.fast_ema)
        data['ema_slow'] = self.calculate_ema(data['close'], self.slow_ema)
        
        # 计算ATR和动态止损
        data['atr'] = self.calculate_atr(data)
        data['stop_loss'] = data['close'] - self.atr_multiplier * data['atr']
        
        # EMA交叉信号
        data['ema_cross_up'] = (data['ema_fast'] > data['ema_slow']) & (data['ema_fast'].shift(1) <= data['ema_slow'].shift(1))
        data['ema_cross_down'] = (data['ema_fast'] < data['ema_slow']) & (data['ema_fast'].shift(1) >= data['ema_slow'].shift(1))
        
        # 市场环境
        if market_data is not None and self.market_filter:
            data['market_regime'] = self.calculate_market_regime(market_data)
            # 只在牛市和震荡市做多，熊市不交易
            data['market_valid'] = data['market_regime'] != MarketRegime.BEAR
        else:
            data['market_valid'] = True
        
        # 买入信号: EMA金叉 + 市场环境允许
        data['buy_signal'] = data['ema_cross_up'] & data['market_valid']
        
        # 卖出信号: EMA死叉 或 价格跌破动态止损
        data['sell_signal'] = data['ema_cross_down'] | (data['close'] < data['stop_loss'].shift(1))
        
        return data
    
    def run_backtest(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None, 
                     initial_capital: float = 100000.0) -> BacktestResult:
        """
        执行回测
        
        Args:
            df: 股票数据
            market_data: 大盘数据
            initial_capital: 初始资金
            
        Returns:
            BacktestResult 包含回测结果
        """
        data = self.generate_signals(df, market_data)
        
        position = 0  # 0: 空仓, 1: 持仓
        entry_price = 0.0
        entry_date = None
        trades = []
        equity_curve = [initial_capital]
        current_capital = initial_capital
        
        for i in range(1, len(data)):
            date = data.index[i]
            price = data['close'].iloc[i]
            
            if position == 0:  # 空仓
                if data['buy_signal'].iloc[i]:
                    # 买入
                    position = 1
                    entry_price = price
                    entry_date = date
                    shares = current_capital / price
                    
            elif position == 1:  # 持仓
                # 检查止损
                stop_price = data['stop_loss'].iloc[i]
                exit_reason = None
                
                if data['sell_signal'].iloc[i]:
                    exit_reason = "signal"
                elif price < stop_price:
                    exit_reason = "stop_loss"
                
                if exit_reason:
                    # 卖出
                    exit_price = price
                    pnl = (exit_price - entry_price) * shares
                    pnl_pct = (exit_price / entry_price - 1) * 100
                    
                    trades.append({
                        'entry_date': entry_date,
                        'exit_date': date,
                        'entry_price': entry_price,
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
        
        # 计算指标
        total_return = (current_capital - initial_capital) / initial_capital * 100
        
        if len(trades) > 0:
            winning_trades = [t for t in trades if t['pnl'] > 0]
            win_rate = len(winning_trades) / len(trades) * 100
            
            # 计算最大回撤
            equity_series = pd.Series(equity_curve)
            rolling_max = equity_series.expanding().max()
            drawdown = (equity_series - rolling_max) / rolling_max * 100
            max_drawdown = drawdown.min()
            
            # 计算Sharpe比率 (简化版)
            returns = pd.Series(equity_curve).pct_change().dropna()
            if returns.std() != 0:
                sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)
            else:
                sharpe_ratio = 0
        else:
            win_rate = 0
            max_drawdown = 0
            sharpe_ratio = 0
        
        return BacktestResult(
            symbol=df.attrs.get('symbol', 'Unknown'),
            total_return=total_return,
            win_rate=win_rate,
            total_trades=len(trades),
            max_drawdown=max_drawdown,
            sharpe_ratio=sharpe_ratio,
            trades=trades,
            params=self.params
        )
    
    def optimize_params(self, df: pd.DataFrame, market_data: Optional[pd.DataFrame] = None,
                       fast_ema_range: List[int] = [5, 8, 10, 12],
                       slow_ema_range: List[int] = [15, 20, 25, 30],
                       atr_mult_range: List[float] = [1.5, 2.0, 2.5, 3.0]) -> Dict:
        """
        参数优化 (网格搜索)
        
        Args:
            df: 股票数据
            market_data: 大盘数据
            fast_ema_range: 快EMA周期范围
            slow_ema_range: 慢EMA周期范围
            atr_mult_range: ATR倍数范围
            
        Returns:
            最优参数和结果
        """
        best_result = None
        best_score = -float('inf')
        best_params = None
        
        for fast in fast_ema_range:
            for slow in slow_ema_range:
                if fast >= slow:
                    continue
                for atr_mult in atr_mult_range:
                    params = {
                        "fast_ema": fast,
                        "slow_ema": slow,
                        "atr_period": 14,
                        "atr_multiplier": atr_mult,
                        "market_filter": True
                    }
                    
                    strategy = EMAV2Strategy(params)
                    result = strategy.run_backtest(df, market_data)
                    
                    # 评分: 收益 + 0.5*胜率 - 最大回撤
                    score = result.total_return + 0.5 * result.win_rate - abs(result.max_drawdown)
                    
                    if score > best_score:
                        best_score = score
                        best_result = result
                        best_params = params
        
        return {
            'best_params': best_params,
            'best_result': best_result,
            'best_score': best_score
        }
