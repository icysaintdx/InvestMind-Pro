#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
EMA V2 回测引擎修复版 - 添加止损执行逻辑

修复内容:
1. 记录买入时的止损价格
2. 每日检查是否触及止损
3. 触及止损时立即卖出
"""

import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

# 添加项目路径
project_root = Path("/home/icysaintdx/.openclaw/workspace-investmindpro/InvestMindPro")
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend"))

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
    """EMA突破策略 V2.0 - 修复版"""
    
    description = "EMA突破 + ATR动态止损"
    
    def __init__(self, config: StrategyConfig):
        self.config = config
        self.name = config.name
        self.parameters = config.parameters
        
        self.ema_fast = self.parameters.get('ema_fast', 8)
        self.ema_slow = self.parameters.get('ema_slow', 25)
        self.atr_period = self.parameters.get('atr_period', 14)
        self.atr_multiplier = self.parameters.get('atr_multiplier', 2.0)
        
        self._data = None
        self._initialized = False
    
    def initialize(self, data: pd.DataFrame):
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
        
        # RSI
        delta = df['close'].diff()
        gain = delta.clip(lower=0).ewm(span=14).mean()
        loss = (-delta.clip(upper=0)).ewm(span=14).mean()
        df['rsi'] = 100 - 100 / (1 + gain / (loss + 0.001))
        
        self._data = df
        self._initialized = True
    
    def generate_signals(self, data: pd.DataFrame) -> List[StrategySignal]:
        """生成所有交易信号"""
        if not self._initialized:
            self.initialize(data)
        
        signals = []
        
        for idx in range(1, len(self._data)):
            row = self._data.iloc[idx]
            prev_row = self._data.iloc[idx-1]
            
            if pd.isna(row.get('ema_fast')) or pd.isna(row.get('atr')):
                continue
            
            price = float(row['close'])
            timestamp = self._data.index[idx]
            
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
                    reason=f"EMA金叉买入 | 止损={stop_loss:.2f}",
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

class StrategyBacktesterWithStopLoss:
    """回测引擎 - 修复版：添加止损执行"""
    
    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.positions = {}  # 持仓信息，包含止损价
        self.trades = []
        self.equity_curve = []
        self.stop_loss_hits = 0  # 统计止损次数
    
    def _reset(self):
        self.current_capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.stop_loss_hits = 0
    
    def run_backtest(self, strategy, data: pd.DataFrame, start_date=None, end_date=None) -> Dict[str, Any]:
        """运行回测 - 逐日检查止损"""
        self._reset()
        
        if start_date:
            data = data[data.index >= start_date]
        if end_date:
            data = data[data.index <= end_date]
        
        if len(data) < 50:
            return {"success": False, "error": "数据不足"}
        
        try:
            signals = strategy.generate_signals(data)
            signal_map = {s.timestamp: s for s in signals}
        except Exception as e:
            return {"success": False, "error": f"生成信号失败: {str(e)}"}
        
        # 逐日遍历
        for idx in range(len(data)):
            current_date = data.index[idx]
            current_bar = data.iloc[idx]
            
            # 1. 先检查止损（开盘价优先）
            self._check_stop_loss(current_date, current_bar)
            
            # 2. 处理信号（T+1，使用第二天开盘价）
            if current_date in signal_map:
                signal = signal_map[current_date]
                # 使用下一天的开盘价执行
                if idx + 1 < len(data):
                    next_date = data.index[idx + 1]
                    next_open = data.iloc[idx + 1]['open']
                    self._execute_signal(signal, next_date, next_open)
        
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
            "trades": self.trades,
            "stop_loss_hits": self.stop_loss_hits
        }
    
    def _check_stop_loss(self, date, bar):
        """检查是否触及止损 - 修复核心"""
        for strategy_id, position in self.positions.items():
            if position.get("shares", 0) == 0:
                continue
            
            stop_loss_price = position.get("stop_loss")
            if stop_loss_price is None:
                continue
            
            # 检查当天最低价是否触及止损
            low_price = bar['low']
            if low_price <= stop_loss_price:
                # 止损卖出 - 按止损价执行
                self._execute_stop_loss(strategy_id, date, stop_loss_price)
    
    def _execute_stop_loss(self, strategy_id, date, stop_price):
        """执行止损卖出"""
        position = self.positions.get(strategy_id)
        if not position or position.get("shares", 0) == 0:
            return
        
        shares = position["shares"]
        revenue = shares * stop_price
        commission = revenue * 0.0003
        stamp_tax = revenue * 0.001
        total_revenue = revenue - commission - stamp_tax
        
        profit = total_revenue - position["cost"]
        profit_pct = profit / position["cost"] if position["cost"] > 0 else 0
        
        self.current_capital += total_revenue
        self.stop_loss_hits += 1
        
        self.trades.append({
            "date": str(date),
            "action": "SELL",
            "type": "STOP_LOSS",
            "price": stop_price,
            "shares": shares,
            "revenue": total_revenue,
            "profit": profit,
            "profit_pct": profit_pct,
            "capital_after": self.current_capital,
            "reason": f"触及止损价 {stop_price}"
        })
        
        position["shares"] = 0
        position["cost"] = 0
        position["stop_loss"] = None
    
    def _execute_signal(self, signal, date, execution_price):
        """执行交易信号"""
        if signal.signal_type == SignalType.BUY:
            self._execute_buy(signal, execution_price, date)
        elif signal.signal_type == SignalType.SELL:
            self._execute_sell(signal, execution_price, date)
    
    def _execute_buy(self, signal, price: float, date):
        """执行买入 - 记录止损价"""
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
            self.positions[signal.strategy_id] = {"shares": 0, "cost": 0, "stop_loss": None}
        
        position = self.positions[signal.strategy_id]
        position["shares"] += shares
        position["cost"] += total_cost
        position["stop_loss"] = signal.stop_loss  # 记录止损价！
        
        self.current_capital -= total_cost
        
        self.trades.append({
            "date": str(date),
            "action": "BUY",
            "type": "SIGNAL",
            "price": price,
            "shares": shares,
            "cost": total_cost,
            "stop_loss": signal.stop_loss,
            "capital_after": self.current_capital
        })
    
    def _execute_sell(self, signal, price: float, date):
        """执行卖出信号"""
        position = self.positions.get(signal.strategy_id)
        if not position or position.get("shares", 0) == 0:
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
            "type": "SIGNAL",
            "price": price,
            "shares": shares,
            "revenue": total_revenue,
            "profit": profit,
            "profit_pct": profit_pct,
            "capital_after": self.current_capital,
            "reason": signal.reason
        })
        
        position["shares"] = 0
        position["cost"] = 0
        position["stop_loss"] = None
    
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
            return {"total_return": 0, "total_return_pct": 0, "win_rate": 0, "total_trades": 0}
        
        total_return = self.current_capital - self.initial_capital
        total_return_pct = total_return / self.initial_capital
        
        sell_trades = [t for t in self.trades if t.get("action") == "SELL"]
        profitable_trades = [t for t in sell_trades if t.get("profit", 0) > 0]
        win_rate = len(profitable_trades) / len(sell_trades) if sell_trades else 0
        
        # 统计止损次数
        stop_loss_trades = [t for t in sell_trades if t.get("type") == "STOP_LOSS"]
        
        equity_curve = [self.initial_capital]
        for trade in self.trades:
            if "capital_after" in trade:
                equity_curve.append(trade["capital_after"])
        
        max_drawdown = self._calculate_max_drawdown(equity_curve)
        
        profit_pcts = [t["profit_pct"] for t in sell_trades if "profit_pct" in t]
        sharpe = 0
        if len(profit_pcts) > 1:
            returns = np.array(profit_pcts)
            sharpe = np.mean(returns) / np.std(returns) * np.sqrt(252) if np.std(returns) > 0 else 0
        
        return {
            "total_return": total_return,
            "total_return_pct": total_return_pct,
            "final_capital": self.current_capital,
            "win_rate": win_rate,
            "total_trades": len(self.trades),
            "buy_trades": len([t for t in self.trades if t["action"] == "BUY"]),
            "sell_trades": len(sell_trades),
            "profitable_trades": len(profitable_trades),
            "stop_loss_trades": len(stop_loss_trades),
            "max_drawdown": max_drawdown,
            "sharpe_ratio": sharpe
        }

# 主执行函数
def main():
    """测试修复后的回测引擎"""
    print("="*60)
    print("EMA V2 回测引擎修复版 - 带止损执行")
    print("="*60)
    
    DATA_DIR = project_root / "backend/data/backtest_cache"
    
    # 测试股票
    test_stock = "000858_20200101_20241231.csv"  # 五粮液
    stock_code = test_stock.split("_")[0]
    
    # 加载数据
    df = pd.read_csv(DATA_DIR / test_stock)
    df['date'] = pd.to_datetime(df['date'])
    df.set_index('date', inplace=True)
    df.sort_index(inplace=True)
    
    print(f"\n📊 测试股票: {stock_code}")
    print(f"📅 数据范围: {df.index[0]} ~ {df.index[-1]}")
    print(f"📈 数据条数: {len(df)}")
    
    # 测试参数
    params = {"ema_fast": 5, "ema_slow": 30, "atr_multiplier": 2.0}
    
    config = StrategyConfig(
        strategy_id=f"ema_v2_test",
        name=f"EMA V2 ({params['ema_fast']}/{params['ema_slow']})",
        parameters=params
    )
    
    strategy = EMABreakoutV2Strategy(config)
    backtester = StrategyBacktesterWithStopLoss(initial_capital=100000.0)
    
    result = backtester.run_backtest(strategy, df)
    
    if result["success"]:
        perf = result["performance"]
        print(f"\n✅ 回测成功!")
        print(f"💰 总收益: {perf['total_return_pct']:.2%}")
        print(f"📊 最终资金: ¥{perf['final_capital']:,.0f}")
        print(f"🎯 胜率: {perf['win_rate']:.1%}")
        print(f"📉 最大回撤: {perf['max_drawdown']:.2%}")
        print(f"📈 夏普比率: {perf['sharpe_ratio']:.2f}")
        print(f"🔄 交易次数: {perf['total_trades']}")
        print(f"🛑 止损次数: {perf.get('stop_loss_trades', 0)}")
        
        # 显示交易明细
        print(f"\n📋 交易记录 (前5笔):")
        for trade in result["trades"][:5]:
            print(f"  {trade['date'][:10]} | {trade['action']:4} | {trade.get('type', 'N/A'):10} | "
                  f"¥{trade['price']:.2f} | {trade.get('reason', 'N/A')[:20]}")
    else:
        print(f"\n❌ 回测失败: {result.get('error', '未知错误')}")

if __name__ == "__main__":
    main()
