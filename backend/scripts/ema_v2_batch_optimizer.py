#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2 参数优化批量执行脚本
- 处理剩余59只股票
- 测试多种参数组合
- 自动更新进度文件
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import akshare as ak
import time
import os
import random

# 设置akshare请求间隔
ak.stock_zh_a_hist.__wrapped__ if hasattr(ak.stock_zh_a_hist, '__wrapped__') else None

# 东方财富是国内网站，不需要代理
# 如果需要代理可取消下面注释
# os.environ['HTTP_PROXY'] = 'http://127.0.0.1:7890'
# os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:7890'
# 确保清除可能存在的代理设置
if 'HTTP_PROXY' in os.environ:
    del os.environ['HTTP_PROXY']
if 'HTTPS_PROXY' in os.environ:
    del os.environ['HTTPS_PROXY']
if 'http_proxy' in os.environ:
    del os.environ['http_proxy']
if 'https_proxy' in os.environ:
    del os.environ['https_proxy']

# 添加项目路径
project_root = Path("/data/workspace-investmindpro/InvestMindPro")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

# 配置
RESULTS_DIR = project_root / "results/individual_ema_v2"
PROGRESS_FILE = project_root / "results/ema_v2_optimization_progress.json"
INITIAL_CAPITAL = 100000.0

# 所有82只股票
ALL_STOCKS = [
    '000001', '000002', '000063', '000100', '000333', '000538', '000568', '000651', '000725', '000768',
    '000786', '000858', '000895', '002001', '002007', '002024', '002027', '002049', '002120', '002142',
    '002230', '002236', '002271', '002304', '002352', '002415', '002460', '002475', '002594', '002714',
    '300003', '300014', '300015', '300033', '300059', '300124', '300274', '300408', '300433', '300750',
    '600000', '600009', '600016', '600028', '600030', '600031', '600036', '600048', '600104', '600276',
    '600309', '600406', '600436', '600438', '600519', '600585', '600660', '600690', '600745', '600809',
    '600837', '600887', '600900', '601012', '601066', '601088', '601100', '601138', '601211', '601288',
    '601318', '601398', '601601', '601628', '601668', '601688', '601857', '601888', '601899', '603288',
    '603501', '603986'
]

# 参数组合
PARAM_COMBINATIONS = [
    # 短线组合
    {"ema_fast": 3, "ema_slow": 20, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 3, "ema_slow": 20, "atr_period": 14, "atr_multiplier": 2.0, "market_filter": True},
    {"ema_fast": 3, "ema_slow": 20, "atr_period": 14, "atr_multiplier": 2.5, "market_filter": True},
    {"ema_fast": 5, "ema_slow": 25, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 5, "ema_slow": 25, "atr_period": 14, "atr_multiplier": 2.0, "market_filter": True},
    {"ema_fast": 5, "ema_slow": 25, "atr_period": 14, "atr_multiplier": 2.5, "market_filter": True},
    # 中线组合
    {"ema_fast": 7, "ema_slow": 20, "atr_period": 14, "atr_multiplier": 1.0, "market_filter": True},
    {"ema_fast": 7, "ema_slow": 20, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 7, "ema_slow": 25, "atr_period": 14, "atr_multiplier": 2.0, "market_filter": True},
    {"ema_fast": 7, "ema_slow": 30, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 8, "ema_slow": 20, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 8, "ema_slow": 25, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 8, "ema_slow": 30, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 8, "ema_slow": 35, "atr_period": 14, "atr_multiplier": 2.0, "market_filter": True},
    {"ema_fast": 10, "ema_slow": 18, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 10, "ema_slow": 18, "atr_period": 14, "atr_multiplier": 2.0, "market_filter": True},
    {"ema_fast": 10, "ema_slow": 30, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 10, "ema_slow": 35, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    # 长线组合
    {"ema_fast": 12, "ema_slow": 15, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 12, "ema_slow": 15, "atr_period": 14, "atr_multiplier": 2.0, "market_filter": True},
    {"ema_fast": 12, "ema_slow": 15, "atr_period": 14, "atr_multiplier": 2.5, "market_filter": True},
    {"ema_fast": 12, "ema_slow": 20, "atr_period": 14, "atr_multiplier": 1.0, "market_filter": True},
    {"ema_fast": 12, "ema_slow": 25, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 12, "ema_slow": 30, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 15, "ema_slow": 40, "atr_period": 14, "atr_multiplier": 1.5, "market_filter": True},
    {"ema_fast": 15, "ema_slow": 40, "atr_period": 14, "atr_multiplier": 2.0, "market_filter": True},
    {"ema_fast": 15, "ema_slow": 40, "atr_period": 14, "atr_multiplier": 2.5, "market_filter": True},
    {"ema_fast": 15, "ema_slow": 40, "atr_period": 14, "atr_multiplier": 3.0, "market_filter": True},
    {"ema_fast": 15, "ema_slow": 40, "atr_period": 14, "atr_multiplier": 4.0, "market_filter": True},
]


class SignalType(Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


@dataclass
class StrategySignal:
    signal_type: SignalType
    confidence: float
    price: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    position_size: float = 0.2
    reason: str = ""
    strategy_id: str = ""
    timestamp: Any = None
    metadata: Dict = field(default_factory=dict)


@dataclass
class StrategyConfig:
    strategy_id: str
    name: str
    parameters: Dict = field(default_factory=dict)
    enabled: bool = True


class EMABreakoutV2Strategy:
    """EMA突破策略 V2.0 - 内联版"""
    
    description = "EMA突破 + ATR动态止损"
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = config.name
        self.parameters = config.parameters
        
        self.ema_fast = self.parameters.get('ema_fast', 8)
        self.ema_slow = self.parameters.get('ema_slow', 25)
        self.atr_period = self.parameters.get('atr_period', 14)
        self.atr_multiplier = self.parameters.get('atr_multiplier', 2.0)
        self.market_filter = self.parameters.get('market_filter', True)
        
        self._data = None
        self._market_data = None
        self._initialized = False
        self.trade_history = []
    
    def initialize(self, data: pd.DataFrame, market_data: pd.DataFrame = None):
        """计算指标"""
        df = data.copy()
        
        # EMA
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow).mean()
        
        # ATR
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df['atr'] = tr.ewm(span=self.atr_period).mean()
        
        # RSI辅助
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(span=14).mean()
        loss = (-delta.clip(upper=0)).ewm(span=14).mean()
        df['rsi'] = 100 - 100 / (1 + gain / (loss + 0.001))
        
        self._data = df
        
        # 大盘数据
        if market_data is not None and self.market_filter:
            mdf = market_data.copy()
            mdf['ema50'] = mdf['close'].ewm(span=50).mean()
            mdf['market_bull'] = mdf['close'] > mdf['ema50']
            self._market_data = mdf
        
        self._initialized = True
    
    def generate_signals(self, data: pd.DataFrame, market_data: pd.DataFrame = None) -> List[StrategySignal]:
        """生成所有交易信号"""
        if not self._initialized:
            self.initialize(data, market_data)
        
        signals = []
        
        for idx in range(1, len(self._data)):
            row = self._data.iloc[idx]
            prev_row = self._data.iloc[idx-1]
            
            if pd.isna(row.get('ema_fast')) or pd.isna(row.get('atr')):
                continue
            
            # 大盘过滤
            if self.market_filter and self._market_data is not None:
                market_idx = min(idx, len(self._market_data) - 1)
                if not self._market_data.iloc[market_idx].get('market_bull', True):
                    continue
            
            price = float(row['close'])
            timestamp = self._data.index[idx]
            
            # 金叉/死叉判断
            golden_cross = (row['ema_fast'] > row['ema_slow']) and (prev_row['ema_fast'] <= prev_row['ema_slow'])
            death_cross = (row['ema_fast'] < row['ema_slow']) and (prev_row['ema_fast'] >= prev_row['ema_slow'])
            trend_up = row['ema_fast'] > row['ema_slow']
            rsi = row.get('rsi', 50)
            atr = row['atr']
            
            if golden_cross and trend_up and rsi < 70:
                stop_loss = price - self.atr_multiplier * atr
                take_profit = price + 2 * (price - stop_loss)
                
                signals.append(StrategySignal(
                    signal_type=SignalType.BUY,
                    confidence=0.75,
                    price=price,
                    stop_loss=round(stop_loss, 2),
                    take_profit=round(take_profit, 2),
                    position_size=0.2,
                    reason=f"EMA金叉买入",
                    strategy_id=self.config.strategy_id,
                    timestamp=timestamp
                ))
            elif death_cross:
                signals.append(StrategySignal(
                    signal_type=SignalType.SELL,
                    confidence=0.8,
                    price=price,
                    reason="EMA死叉卖出",
                    strategy_id=self.config.strategy_id,
                    timestamp=timestamp
                ))
        
        return signals


class StrategyBacktester:
    """简化版策略回测引擎"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
    
    def _reset(self):
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
    
    def run_backtest(self, strategy, data: pd.DataFrame, market_data: pd.DataFrame = None,
                     start_date=None, end_date=None) -> Dict[str, Any]:
        self._reset()
        
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        if len(data) < 50:
            return {"success": False, "error": "数据不足，至少需要50个交易日"}
        
        try:
            signals = strategy.generate_signals(data, market_data)
        except Exception as e:
            return {"success": False, "error": f"生成信号失败: {str(e)}"}
        
        for signal in signals:
            self._execute_signal(signal, data)
        
        performance = self._calculate_performance(data)
        
        return {
            "success": True,
            "strategy_name": strategy.name,
            "backtest_period": {
                "start": str(data.index[0]),
                "end": str(data.index[-1]),
                "days": len(data)
            },
            "performance": performance,
            "trades": self.trades
        }
    
    def _execute_signal(self, signal, data: pd.DataFrame):
        signal_date = signal.timestamp
        
        if signal_date not in data.index:
            return
        
        signal_idx = data.index.get_loc(signal_date)
        if signal_idx + 1 >= len(data):
            return
        
        next_day = data.index[signal_idx + 1]
        execution_price = data.loc[next_day, 'open']
        
        if signal.signal_type == SignalType.BUY:
            self._execute_buy(signal, execution_price, next_day)
        elif signal.signal_type == SignalType.SELL:
            self._execute_sell(signal, execution_price, next_day)
    
    def _execute_buy(self, signal, price: float, date):
        position_value = self.current_capital * signal.position_size
        shares = int(position_value / price / 100) * 100
        
        if shares < 100:
            return
        
        cost = shares * price
        commission = cost * 0.0003
        total_cost = cost + commission
        
        if total_cost > self.current_capital:
            return
        
        if signal.strategy_id not in self.positions:
            self.positions[signal.strategy_id] = {"shares": 0, "cost": 0}
        
        position = self.positions[signal.strategy_id]
        position["shares"] += shares
        position["cost"] += total_cost
        self.current_capital -= total_cost
        
        self.trades.append({
            "date": str(date),
            "action": "BUY",
            "price": price,
            "shares": shares,
            "cost": total_cost,
            "capital_after": self.current_capital
        })
    
    def _execute_sell(self, signal, price: float, date):
        if signal.strategy_id not in self.positions:
            return
        
        position = self.positions[signal.strategy_id]
        if position["shares"] == 0:
            return
        
        shares = position["shares"]
        revenue = shares * price
        commission = revenue * 0.0003
        stamp_tax = revenue * 0.001
        total_revenue = revenue - commission - stamp_tax
        
        profit = total_revenue - position["cost"]
        profit_pct = profit / position["cost"] if position["cost"] > 0 else 0
        
        self.current_capital += total_revenue
        
        self.trades.append({
            "date": str(date),
            "action": "SELL",
            "price": price,
            "shares": shares,
            "revenue": total_revenue,
            "profit": profit,
            "profit_pct": profit_pct,
            "capital_after": self.current_capital
        })
        
        position["shares"] = 0
        position["cost"] = 0
    
    def _calculate_max_drawdown(self, equity_curve):
        if not equity_curve:
            return 0
        peak = equity_curve[0]
        max_dd = 0
        for value in equity_curve:
            if value > peak:
                peak = value
            dd = (peak - value) / peak
            if dd > max_dd:
                max_dd = dd
        return max_dd
    
    def _calculate_performance(self, data: pd.DataFrame) -> Dict[str, Any]:
        if not self.trades:
            return {
                "total_return": 0,
                "total_return_pct": 0,
                "win_rate": 0,
                "total_trades": 0
            }
        
        total_return = self.current_capital - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        
        sell_trades = [t for t in self.trades if t.get("action") == "SELL"]
        profitable_trades = [t for t in sell_trades if t.get("profit", 0) > 0]
        win_rate = len(profitable_trades) / len(sell_trades) if sell_trades else 0
        
        profits = [t["profit"] for t in sell_trades if "profit" in t]
        avg_profit = np.mean(profits) if profits else 0
        
        profit_pcts = [t["profit_pct"] for t in sell_trades if "profit_pct" in t]
        avg_profit_pct = np.mean(profit_pcts) if profit_pcts else 0
        
        # 计算资金曲线和最大回撤
        equity_curve = [self.initial_capital]
        for trade in self.trades:
            if "capital_after" in trade:
                equity_curve.append(trade["capital_after"])
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        # 简化夏普比率
        if len(profit_pcts) > 1:
            returns = np.array(profit_pcts)
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        else:
            sharpe = 0
        
        return {
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "final_capital": self.current_capital,
            "win_rate": win_rate,
            "total_trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t["action"] == "BUY"]),
            "sell_trades": len(sell_trades),
            "profitable_trades": len(profitable_trades),
            "avg_profit": avg_profit,
            "avg_profit_pct": avg_profit_pct,
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe
        }


def fetch_stock_data(symbol: str, start_date: str = "20200101", end_date: str = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """获取个股和大盘数据（使用TDX Native Provider）"""
    from backend.dataflows.providers.tdx_native_provider import get_tdx_native_provider
    
    provider = get_tdx_native_provider()
    
    if not provider.ensure_available_with_retry(max_retries=3):
        raise Exception("TDX Provider不可用")
    
    try:
        # 获取个股数据 - 使用日K线类型9
        stock_data = provider.get_kline(symbol, kline_type=9, count=800)
        
        if not stock_data or len(stock_data) < 50:
            raise Exception(f"股票{symbol}数据不足: {len(stock_data) if stock_data else 0}条")
        
        df_stock = pd.DataFrame(stock_data)
        # TDX返回的date字段格式为 "2026-02-25 15:00"，但可能有无效数据
        # 使用errors='coerce'跳过无效日期
        df_stock['date'] = pd.to_datetime(df_stock['date'], format='%Y-%m-%d %H:%M', errors='coerce')
        # 删除无效日期的行
        df_stock = df_stock.dropna(subset=['date'])
        df_stock = df_stock.sort_values('date').reset_index(drop=True)
        df_stock.set_index('date', inplace=True)
        
        # 重命名列以匹配原有格式
        df_stock = df_stock.rename(columns={
            'open': 'open',
            'close': 'close', 
            'high': 'high',
            'low': 'low',
            'volume': 'volume',
            'amount': 'amount'
        })
        
        # 计算涨跌幅等字段
        df_stock['pct_change'] = df_stock['close'].pct_change() * 100
        df_stock['change'] = df_stock['close'].diff()
        df_stock['amplitude'] = ((df_stock['high'] - df_stock['low']) / df_stock['close'].shift(1)) * 100
        df_stock['turnover'] = 0  # TDX不直接提供换手率
        
        # 获取沪深300数据 (TDX中使用399300代码)
        market_data = provider.get_kline('399300', kline_type=9, count=800)
        
        if not market_data or len(market_data) < 50:
            raise Exception(f"沪深300数据不足: {len(market_data) if market_data else 0}条")
        
        df_market = pd.DataFrame(market_data)
        # TDX返回的date字段格式为 "2026-02-25 15:00"，但可能有无效数据
        df_market['date'] = pd.to_datetime(df_market['date'], format='%Y-%m-%d %H:%M', errors='coerce')
        # 删除无效日期的行
        df_market = df_market.dropna(subset=['date'])
        df_market = df_market.sort_values('date').reset_index(drop=True)
        df_market.set_index('date', inplace=True)
        
        df_market = df_market.rename(columns={
            'open': 'open',
            'close': 'close',
            'high': 'high', 
            'low': 'low',
            'volume': 'volume',
            'amount': 'amount'
        })
        
        df_market['pct_change'] = df_market['close'].pct_change() * 100
        df_market['change'] = df_market['close'].diff()
        df_market['amplitude'] = ((df_market['high'] - df_market['low']) / df_market['close'].shift(1)) * 100
        df_market['turnover'] = 0
        
        return df_stock, df_market
        
    except Exception as e:
        raise Exception(f"获取数据失败: {e}")


def run_single_optimization(symbol: str, params: Dict) -> Dict:
    """运行单个参数组合优化"""
    try:
        df_stock, df_market = fetch_stock_data(symbol)
        
        config = StrategyConfig(
            strategy_id=f"ema_v2_{symbol}",
            name=f"EMA V2 ({params['ema_fast']}/{params['ema_slow']})",
            parameters=params
        )
        
        strategy = EMABreakoutV2Strategy(config)
        backtester = StrategyBacktester(initial_capital=INITIAL_CAPITAL)
        result = backtester.run_backtest(strategy, df_stock, df_market)
        
        if result["success"]:
            perf = result["performance"]
            # 计算综合得分
            return_score = max(0, perf.get("total_return_pct", 0) * 100)  # 收益得分
            sharpe_score = max(0, perf.get("sharpe_ratio", 0) * 20)  # 夏普得分
            dd_penalty = abs(perf.get("max_drawdown", 0)) * 50  # 回撤惩罚
            
            score = return_score + sharpe_score - dd_penalty
            
            return {
                "success": True,
                "params": params,
                "return": perf.get("total_return_pct", 0) * 100,
                "win_rate": perf.get("win_rate", 0) * 100,
                "trades": perf.get("total_trades", 0),
                "max_dd": perf.get("max_drawdown", 0) * 100,
                "sharpe": perf.get("sharpe_ratio", 0),
                "score": score
            }
        else:
            return {"success": False, "error": result.get("error", "未知错误")}
    except Exception as e:
        return {"success": False, "error": str(e)}


def optimize_stock(symbol: str) -> Dict:
    """优化单个股票的所有参数组合"""
    print(f"\n{'='*60}")
    print(f"📊 开始优化股票: {symbol}")
    print(f"{'='*60}")
    
    results = []
    for i, params in enumerate(PARAM_COMBINATIONS):
        param_desc = f"EMA{params['ema_fast']}/{params['ema_slow']}, ATRx{params['atr_multiplier']}"
        print(f"  [{i+1}/{len(PARAM_COMBINATIONS)}] 测试 {param_desc}...", end=" ")
        
        result = run_single_optimization(symbol, params)
        results.append(result)
        
        if result["success"]:
            print(f"✅ 收益={result['return']:.2f}%, 胜率={result['win_rate']:.1f}%, 夏普={result['sharpe']:.2f}")
        else:
            print(f"❌ 失败: {result.get('error', '未知错误')}")
    
    # 找出最佳参数（按得分排序）
    successful = [r for r in results if r["success"]]
    if successful:
        # 按得分排序
        sorted_results = sorted(successful, key=lambda x: x["score"], reverse=True)
        best = sorted_results[0]
        
        return {
            "symbol": symbol,
            "success": True,
            "best_params": best["params"],
            "best_result": {
                "return": best["return"],
                "win_rate": best["win_rate"],
                "trades": best["trades"],
                "max_drawdown": best["max_dd"],
                "sharpe": best["sharpe"]
            },
            "all_results": [
                {
                    "params": r["params"],
                    "return": r["return"],
                    "win_rate": r["win_rate"],
                    "trades": r["trades"],
                    "max_dd": r["max_dd"],
                    "sharpe": r["sharpe"],
                    "score": r["score"]
                }
                for r in sorted_results[:20]  # 保存前20个结果
            ],
            "tested_combinations": len(PARAM_COMBINATIONS)
        }
    else:
        return {
            "symbol": symbol,
            "success": False,
            "error": "所有参数组合均失败"
        }


def load_progress() -> Dict:
    """加载进度文件"""
    if PROGRESS_FILE.exists():
        with open(PROGRESS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "completed_count": 0,
        "completed_symbols": [],
        "results": {}
    }


def save_progress(progress: Dict):
    """保存进度文件"""
    progress["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(PROGRESS_FILE, 'w', encoding='utf-8') as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def save_individual_result(symbol: str, result: Dict):
    """保存单个股票结果"""
    result_file = RESULTS_DIR / f"{symbol}.json"
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)


def get_remaining_stocks() -> List[str]:
    """获取剩余待优化的股票列表"""
    progress = load_progress()
    completed = set(progress.get("completed_symbols", []))
    return [s for s in ALL_STOCKS if s not in completed]


def batch_optimize(batch_size: int = 5, max_stocks: int = None):
    """批量优化股票"""
    remaining = get_remaining_stocks()
    
    if max_stocks:
        remaining = remaining[:max_stocks]
    
    total = len(remaining)
    print(f"\n{'='*70}")
    print(f"🚀 EMA V2 批量参数优化")
    print(f"{'='*70}")
    print(f"📊 剩余待优化: {total} 只股票")
    print(f"📦 批次大小: {batch_size}")
    print(f"🔧 参数组合: {len(PARAM_COMBINATIONS)} 种")
    print(f"{'='*70}\n")
    
    progress = load_progress()
    completed = 0
    failed = []
    
    for i, symbol in enumerate(remaining, 1):
        print(f"\n[{i}/{total}] 处理: {symbol}")
        
        try:
            result = optimize_stock(symbol)
            
            if result["success"]:
                # 保存单个结果
                save_individual_result(symbol, result)
                
                # 更新进度
                progress["completed_symbols"].append(symbol)
                progress["completed_count"] = len(progress["completed_symbols"])
                progress["results"][symbol] = {
                    "best_params": result["best_params"],
                    "best_result": result["best_result"]
                }
                save_progress(progress)
                
                completed += 1
                print(f"✅ 完成: {symbol} - 收益={result['best_result']['return']:.2f}%")
            else:
                failed.append((symbol, result.get("error", "未知错误")))
                print(f"❌ 失败: {symbol} - {result.get('error', '未知错误')}")
        except Exception as e:
            failed.append((symbol, str(e)))
            print(f"❌ 异常: {symbol} - {str(e)}")
        
        # 批次报告
        if i % batch_size == 0:
            print(f"\n{'='*70}")
            print(f"📊 进度报告 [{i}/{total}]")
            print(f"✅ 成功: {completed} | ❌ 失败: {len(failed)}")
            print(f"{'='*70}\n")
    
    # 最终报告
    print(f"\n{'='*70}")
    print(f"🎉 批量优化完成!")
    print(f"{'='*70}")
    print(f"✅ 成功: {completed} 只")
    print(f"❌ 失败: {len(failed)} 只")
    if failed:
        print(f"失败列表: {[f[0] for f in failed]}")
    print(f"{'='*70}")
    
    return completed, failed


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="EMA V2 批量参数优化")
    parser.add_argument("--batch-size", type=int, default=5, help="每批处理股票数")
    parser.add_argument("--max-stocks", type=int, default=None, help="最大处理股票数")
    parser.add_argument("--single", type=str, default=None, help="单只股票代码")
    
    args = parser.parse_args()
    
    if args.single:
        # 单只股票模式
        result = optimize_stock(args.single)
        save_individual_result(args.single, result)
        print(f"\n结果已保存: {RESULTS_DIR / args.single}.json")
    else:
        # 批量模式
        batch_optimize(batch_size=args.batch_size, max_stocks=args.max_stocks)
